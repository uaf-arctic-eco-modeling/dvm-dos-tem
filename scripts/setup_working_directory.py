#!/usr/bin/env python

# T. Carman June 2019

import os
import sys
import errno
import shutil
#import json
import commentjson # need because we keep comments in our config file
import collections
import argparse
import textwrap

def mkdir_p(path):
  '''Emulates the shell's `mkdir -p`.'''
  try:
    os.makedirs(path)
  except OSError as exc:  # Python >2.5
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else:
      raise


if __name__ == '__main__':
  
  parser = argparse.ArgumentParser(
    formatter_class = argparse.RawDescriptionHelpFormatter,

      description=textwrap.dedent('''\
        This script will create a working directory for conducting a dvmdostem
        run. The working directory will have the parameters, and configuration
        files necessary for the run. In addition the config.js file will be
        at least partially filled out so that the run will look for parameters
        in your new working directory, and will write outputs in the new working 
        directory. If you specify the --input-data-path then the paths will be
        set in the config/config.js file too. Otherwise you will need to 
        modify the config/config.js file to include the correct paths to your 
        input files.'''.format()),

      epilog=textwrap.dedent(''''''),
  )
  
  parser.add_argument('new_directory',
      help=textwrap.dedent("""The new working directory to setup."""))

  parser.add_argument('--input-data-path', default="<placeholder>",
      help=textwrap.dedent("""Path to the input data"""))

  parser.add_argument('--copy-inputs', action='store_true',
      help=textwrap.dedent("""Copy the inputs from the location specified 
        in --input-data-path to the new working directory that is being setup.
        If this option is present, then the paths in the config file will be
        set to use the copied inputs."""))

  parser.add_argument('--no-cal-targets', action='store_true',
      help=textwrap.dedent("""Do NOT copy the calibration_targets.py file into
        the new working directory."""))

  args = parser.parse_args()
  print(args)

  # Make the new main working directory
  mkdir_p(args.new_directory)

  # Figure out the path of the dvm-dos-tem repo that is being used
  # to run this script. This is presumably where the user would 
  # like the config and parameters to come from.
  # Alternatively: os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
  ddt_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

  if args.no_cal_targets:
    pass
  else:
    mkdir_p(os.path.join(args.new_directory, 'calibration'))
    shutil.copy( os.path.join(ddt_dir, 'calibration', 'calibration_targets.py'), 
                 os.path.join(args.new_directory, 'calibration'))


  # Copy over the config and parameters directories
  shutil.copytree(os.path.join(ddt_dir, 'config'), os.path.join(args.new_directory, 'config'))
  shutil.copytree(os.path.join(ddt_dir, 'parameters'), os.path.join(args.new_directory, 'parameters'))

  if args.copy_inputs:
    shutil.copytree(args.input_data_path, os.path.join(args.new_directory, 'inputs', os.path.basename(args.input_data_path)))
  else:
    # Copy the run mask from the source data directory into the new working directory
    shutil.copy(os.path.join(args.input_data_path, 'run-mask.nc'), os.path.join(args.new_directory, 'run-mask.nc'))

  # Make sure an output directory exists
  mkdir_p(os.path.join(args.new_directory, 'output'))

  # Open the new config file
  with open(os.path.join(args.new_directory, 'config/config.js')) as fp:
    config = commentjson.load(fp)

  ####  Set up the new config file appropriately... ####

  # Make sure parameters and output are relative to the current working directory
  config['IO']['parameter_dir'] = 'parameters/'  # <-- trailing slash is important!!
  config['IO']['output_dir']    = 'output/'      # <-- trailing slash is important!!
  config['IO']['runmask_file']  = 'run-mask.nc'

  if args.copy_inputs:
    input_data_path = os.path.join('inputs', os.path.basename(args.input_data_path))
    # leave run mask where it is, set path
    config['IO']['runmask_file']  = os.path.join(input_data_path,'run-mask.nc')

  else:
    input_data_path = os.path.join(os.path.abspath(args.input_data_path))
 
  # Set up the paths to the input data...
  config['IO']['hist_climate_file']    = os.path.join(input_data_path, 'historic-climate.nc')
  config['IO']['proj_climate_file']    = os.path.join(input_data_path, 'projected-climate.nc')
  config['IO']['veg_class_file']       = os.path.join(input_data_path, 'vegetation.nc')
  config['IO']['drainage_file']        = os.path.join(input_data_path, 'drainage.nc')
  config['IO']['soil_texture_file']    = os.path.join(input_data_path, 'soil-texture.nc')
  config['IO']['co2_file']             = os.path.join(input_data_path, 'co2.nc')
  config['IO']['proj_co2_file']        = os.path.join(input_data_path, 'projected-co2.nc')
  config['IO']['topo_file']            = os.path.join(input_data_path, 'topo.nc')
  config['IO']['fri_fire_file']        = os.path.join(input_data_path, 'fri-fire.nc')
  config['IO']['hist_exp_fire_file']   = os.path.join(input_data_path, 'historic-explicit-fire.nc')
  config['IO']['proj_exp_fire_file']   = os.path.join(input_data_path, 'projected-explicit-fire.nc')

  # Make sure calibration data ends up in a directory that is named the same
  # as your new working directory.
  # NOTE: Seems like when the user runs the calibration-viewer.py and specifies
  # --data-path, they for some reason have to include dvmdostem, like this:
  # --data-path /tmp/args.new_directory/dvmdostem
  config['calibration-IO']['caldata_tree_loc'] = os.path.join('/tmp', os.path.basename(os.path.abspath(args.new_directory)))

  # Match the default config file shipped with the code, except we move runmask
  # to the end of the file listings
  sort_order = [
    "parameter_dir",

    "hist_climate_file",
    "proj_climate_file",
    "veg_class_file",
    "drainage_file",
    "soil_texture_file",
    "co2_file",
    "proj_co2_file",
    "topo_file",
    "fri_fire_file",
    "hist_exp_fire_file",
    "proj_exp_fire_file",
    "topo_file",
    "runmask_file",

    "output_dir",
    "output_spec_file",
    "output_monthly",
    "output_nc_eq",
    "output_nc_sp",
    "output_nc_tr",
    "output_nc_sc"
  ] 

  # Sort the keys in the IO section.
  config['IO'] = collections.OrderedDict(sorted(iter(config['IO'].items()), key=lambda k_v: sort_order.index(k_v[0])))

  with open(os.path.join(args.new_directory, 'config/config.js'), 'w') as fp:
    commentjson.dump(config, fp, indent=2, sort_keys=False) # sorting messes up previous sorting!




