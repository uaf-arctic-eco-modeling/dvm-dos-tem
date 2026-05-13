#!/usr/bin/env python

# T. Carman June 2019

import os
import sys
import errno
import shutil
import pathlib

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

def pick_input_file(search_dir, criteria_groups, default_filename, description):
  '''
  Scan search_dir for .nc files whose lowercased names contain all tokens in
  at least one criteria group (list of tuples). Returns the first match. If
  multiple matches are found, a warning is printed. If no match is found, a
  warning is printed and the default filename is used.
  '''
  matches = []
  for candidate in sorted(pathlib.Path(search_dir).iterdir()):
    if not candidate.is_file() or candidate.suffix.lower() != '.nc':
      continue
    name_lower = candidate.name.lower()
    for tokens in criteria_groups:
      if all(t in name_lower for t in tokens):
        matches.append(candidate.name)
        break

  if len(matches) > 1:
    print(
      f"WARNING: Multiple {description} files found in {search_dir}: "
      f"{matches}. Using first match: {matches[0]}",
      file=sys.stderr,
    )
  if len(matches) == 0:
    print(
      f"WARNING: No {description} file found in {search_dir}. "
      f"Defaulting to: {default_filename}",
      file=sys.stderr,
    )
    return os.path.join(search_dir, default_filename)

  return os.path.join(search_dir, matches[0])


def cmdline_parse(argv=None):
  '''
  Define command line interface and parse incoming arguments.
  When argv is None, parses sys.argv[1:], otherwise parses argv.
  '''
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

  parser.add_argument('--force', action='store_true',
      help=textwrap.dedent("""Force create new directory, overwriting existing 
        data."""))

  parser.add_argument('--input-data-path', default="<placeholder>",
      help=textwrap.dedent("""Path to the input data"""))

  parser.add_argument('--seed-parameters',
      help=textwrap.dedent('''The path that should be searched for the
        parameters that will be copied into your new workspace.'''))

  parser.add_argument('--seed-targets',
      help=textwrap.dedent('''The path that should be searched for the
        calibration_targets.py that will be copied into your new workspace.'''))

  parser.add_argument('--copy-inputs', action='store_true',
      help=textwrap.dedent("""Copy the inputs from the location specified 
        in --input-data-path to the new working directory that is being setup.
        If this option is present, then the paths in the config file will be
        set to use the copied inputs."""))

  parser.add_argument('--no-cal-targets', action='store_true',
      help=textwrap.dedent("""Do NOT copy the calibration_targets.py file into
        the new working directory."""))

  args = parser.parse_args(argv) # uses sys.argv[1:] when argv is None

  # various argument validation...
  if args.seed_targets:
    if not os.path.exists(args.seed_targets):
      parser.error("Must be a valid path to an existing targets file.")

    # hmm, not sure if this is the best here...
    if 'calibration_targets.py' not in os.path.basename(args.seed_targets):
      parser.error("Must pass full path to calibration_targets.py file")

  if args.no_cal_targets and args.seed_targets:
    parser.error("It does not make sense use --seed-targets and --no-cal-targets at the same time.")

  return args


def cmdline_run(args):
  '''
  The work of setting up a new working directory.
  '''
    # Make the new main working directory
  mkdir_p(args.new_directory)

  if args.force:
    shutil.rmtree(args.new_directory)

  # Figure out the path of the dvm-dos-tem repo that is being used
  # to run this script. This is presumably where the user would 
  # like the config and parameters to come from.
  # Alternatively: os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
  # Hmmm kinda unwieldly...added a few more layers to get out of the pyhon package layout...
  # This data really should be passed or stored in some kind of config data structure
  #                           pyddt         src             pyddt            util
  ddt_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))))
  #import sys; sys.exit()

  if args.no_cal_targets:
    pass
  else:
    mkdir_p(os.path.join(args.new_directory, 'calibration'))
    if args.seed_targets:
      shutil.copy(args.seed_targets,
                  os.path.join(args.new_directory, 'calibration'))
    else:
      shutil.copy(os.path.join(ddt_dir,'pyddt','src','pyddt', 'calibration', 'calibration_targets.py'),
                  os.path.join(args.new_directory, 'calibration'))

  if args.seed_parameters:
    shutil.copytree(args.seed_parameters,
                    os.path.join(args.new_directory, 'parameters'))
  else:
    shutil.copytree(os.path.join(ddt_dir, 'parameters'),
                    os.path.join(args.new_directory, 'parameters'))


  # Copy over the config and parameters directories
  shutil.copytree(os.path.join(ddt_dir, 'config'), os.path.join(args.new_directory, 'config'))

  if args.copy_inputs:
    shutil.copytree(args.input_data_path, os.path.join(args.new_directory, 'inputs', os.path.basename(args.input_data_path)))
  else:
    # Copy the run mask from the source data directory into the new working directory
    shutil.copy(os.path.join(args.input_data_path, 'run-mask.nc'), os.path.join(args.new_directory, 'run-mask.nc'))

  # Make sure an output directory exists
  mkdir_p(os.path.join(args.new_directory, 'output'))

  # Open the new config file
  with open(os.path.join(args.new_directory, 'config/config.js'), encoding='utf-8') as fp:
    config = commentjson.load(fp)

  ####  Set up the new config file appropriately... ####

  # Make sure parameters and output are relative to the current working directory
  config['IO']['parameter_dir'] = 'parameters/'  # <-- trailing slash is important!!
  config['IO']['output_dir']    = 'output/'      # <-- trailing slash is important!!
  config['IO']['restart_from']  = ''             # defaults to blank; not a restart run,
  config['IO']['runmask_file']  = 'run-mask.nc'

  if args.copy_inputs:
    input_data_path = os.path.join('inputs', os.path.basename(args.input_data_path))
    # leave run mask where it is, set path
    config['IO']['runmask_file']  = os.path.join(input_data_path,'run-mask.nc')

  else:
    input_data_path = os.path.join(os.path.abspath(args.input_data_path))
    if not pathlib.Path(input_data_path).is_dir():
      raise ValueError(f"Input data path {input_data_path} is not a valid directory.")

  # Check the input data path and look for the appropriate files. Allow for some
  # variation, i.e. veg, vegetation, veg_class, VegClass, etc. Same for soil
  # texture, climate, climate, topo, fire and co2 files. This is to allow for
  # some flexibility in the input data naming conventions, and to avoid having
  # to rename files just to get them to work with the default config file. If
  # there are multiple files that match the criteria, then the first one found
  # will be used, and a warning will be printed to the user. If no files are
  # found that match the criteria, then the path in the config file will be set
  # to the default filename, which will likely cause the run to fail, but at
  # least the user will get a clear error message about what file is missing.
  
  config['IO']['hist_climate_file'] = pick_input_file(
    input_data_path,
    [('historic', 'climate'), ('hist', 'climate')],
    'historic-climate.nc',
    'historic climate',
  )

  config['IO']['proj_climate_file'] = pick_input_file(
    input_data_path,
    [('projected', 'climate'), ('proj', 'climate')],
    'projected-climate.nc',
    'projected climate',
  )

  config['IO']['veg_class_file'] = pick_input_file(
    input_data_path,
    [('vegetation',), ('veg_class',), ('vegclass',), ('veg',)],
    'vegetation.nc',
    'vegetation',
  )

  config['IO']['drainage_file'] = pick_input_file(
    input_data_path,
    [('drainage',), ('drain',)],
    'drainage.nc',
    'drainage',
  )

  config['IO']['soil_texture_file'] = pick_input_file(
    input_data_path,
    [('soil', 'texture'), ('soil_texture',), ('soiltex',)],
    'soil-texture.nc',
    'soil texture',
  )

  config['IO']['co2_file'] = pick_input_file(
    input_data_path,
    [('historic', 'co2'), ('hist', 'co2'), ('co2',)],
    'co2.nc',
    'historic CO2',
  )

  config['IO']['proj_co2_file'] = pick_input_file(
    input_data_path,
    [('projected', 'co2'), ('proj', 'co2')],
    'projected-co2.nc',
    'projected CO2',
  )

  config['IO']['topo_file'] = pick_input_file(
    input_data_path,
    [('topo',), ('topography',)],
    'topo.nc',
    'topography',
  )

  config['IO']['fri_fire_file'] = pick_input_file(
    input_data_path,
    [('fri', 'fire'), ('fri-fire',), ('frifire',)],
    'fri-fire.nc',
    'FRI fire',
  )

  config['IO']['hist_exp_fire_file'] = pick_input_file(
    input_data_path,
    [('historic', 'explicit', 'fire'), ('hist', 'exp', 'fire')],
    'historic-explicit-fire.nc',
    'historic explicit fire',
  )

  config['IO']['proj_exp_fire_file'] = pick_input_file(
    input_data_path,
    [('projected', 'explicit', 'fire'), ('proj', 'exp', 'fire')],
    'projected-explicit-fire.nc',
    'projected explicit fire',
  )

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
    "restart_from",
    "output_spec_file",
    "output_monthly",
    "output_nc_eq",
    "output_nc_sp",
    "output_nc_tr",
    "output_nc_sc",
    "output_interval",
  ] 

  # Sort the keys in the IO section.
  config['IO'] = collections.OrderedDict(sorted(iter(config['IO'].items()), key=lambda k_v: sort_order.index(k_v[0])))

  with open(os.path.join(args.new_directory, 'config/config.js'), 'w', encoding='utf-8') as fp:
    commentjson.dump(config, fp, indent=2, sort_keys=False) # sorting messes up previous sorting!


def cmdline_entry(argv=None):
  '''
  Wrapper allowing for easier testing of the cmdline run and parse functions.
  '''
  args = cmdline_parse(argv)
  return cmdline_run(args)

# adding this allows the script to be run standalone when installed with pip
def main(argv=None):
  return cmdline_entry(argv=argv)

if __name__ == '__main__':
  sys.exit(cmdline_entry())
  




