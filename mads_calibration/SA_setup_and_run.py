#!/usr/bin/env python

# Sensitivity adapted for the calibration type output
# uses calibration configuration file as an input
# Example: python3 run_mads_sensitivity.py /work/mads_calibration/config-step1-md1.yaml
# Author: Elchin Jafarov 
# Date: 03/27/2023

import os
import yaml
import numpy as np
import argparse
import pathlib
import textwrap

import drivers.Sensitivity 

def config_file_validator(arg_config_file):
  '''Make sure that the file exists'''
  try:
    files = os.path.isfile(arg_config_file)
  except OSError as e:
    msg = "Can't find file: {}".format(e)
    raise argparse.ArgumentTypeError(msg)
  return arg_config_file

def get_parser():

  parser = argparse.ArgumentParser(
    formatter_class = argparse.RawDescriptionHelpFormatter,
      description=textwrap.dedent('''\
        This script runs a special Sensitivity Analysis that is used as
        as the initial part of a the calibration process. This is the left 
        (orange) half of the diagram in the MADS Assisted Calibration section.    
        '''.format("")),
  )

  parser.add_argument("configfile", type=config_file_validator,
      help=textwrap.dedent('''The config file to use.'''))

  parser.add_argument("--custom-seed",
                      help=textwrap.dedent('''\ 
                        A user specified location for the seed path. The seed
                        path is the folder where parameter values are sourced
                        when setting up runs. The bulk (all) of the parameters
                        for each run will be set from the seed path. Then the
                        Sensitivity driver will modify some of the parameters in
                        place in each run directory.
                      '''))

  parser.add_argument('--N', type=int, default=10,
      help=textwrap.dedent('''The number of samples that should be run.'''))

  parser.add_argument('--sampling-method', default='uniform',
      choices=['uniform','lhc'],
      help=textwrap.dedent('''\
          Which sampling method to use for drawing parameter sets. 'lhc' offers
          better coverage, but is slower.'''))

  parser.add_argument('--dry-run', action='store_true',
      help=textwrap.dedent('''If passed, only do the setup, don't actually 
        launch the runs.'''))

  parser.add_argument('-f', '--force', action='store_true', 
      help=textwrap.dedent('''Clean the working directory without warning.'''))

  return parser

if __name__ == '__main__':
  
  parser = get_parser()

  args = parser.parse_args()
  
  config_file_name = args.configfile

  print(f"The filename you provided is: {config_file_name}")

  with open(config_file_name, 'r') as config_data:
    config = yaml.safe_load(config_data)

  # Make an instance of the driver object
  driver = drivers.Sensitivity.Sensitivity()

  # Set the "seed" path. This is the directory where initial parameter values
  # will be read from.
  driver.set_seed_path('/work/parameters/')
  if args.custom_seed:
    # should validate it is a proper director first?
    driver.set_seed_path(args.custom_seed)

  # Set the working directory. This is the folder where all the individual runs
  # will be carried out. Each individual run directory will be setup using
  # parameter values from the seed path, and then parameter values in the
  # run directories will be adjusted as part of the sensitivity analysis.
  driver.set_work_dir(config['work_dir'])

  # Bug in some circumstances with directory not existing yet...
  pathlib.Path(driver.work_dir).mkdir(parents=True, exist_ok=True)

  if args.force:
    driver.clean()

  # Use this function to further configure the sensitivitry analysis. 
  # Note that the percent_diffs (aka "perturbations") array allows you to set the
  # ranges that the sampling method will use to choose parameter values. The default
  # perturbation is initial values (from seed path) +/-10%. Here we choose
  # set the perturbations to initial value +/-90%.
  perturbations = 0.9 * np.ones(len(config['pftnums']))
  driver.design_experiment(Nsamples=args.N, 
                          cmtnum=config['cmtnum'], 
                          params=config['params'], 
                          pftnums=config['pftnums'], 
                          percent_diffs=list(perturbations),
                          sampling_method=args.sampling_method)

  # Load up the target (aka observation) data.
  driver.load_target_data('/work/calibration/')

  driver.opt_run_setup = config['opt_run_setup']

  # Build the outputs dict for the driver object, based on what is specified by
  # the user in the config file for targets. Idea is that for each target you are
  # interested in looking at you need to make sure the appropriate netCDf output
  # is enabled.
  #
  # This is so far only designed to work for outputs that have a corresponding 
  # target. If more outputs are needed, we will need to add more functionality
  # to the setup_outputs function, or add another function.
  driver.setup_outputs(config['target_names'])

  driver.module_stage_settings=config['calib_mode']

  try:
    # add param calib  (a boolean, turns off dsl)
    driver.setup_multi() 
  except ValueError:
    print("Oops!  setup_multi failed.  Check the setup...")

  if args.dry_run:
    print(f"Dry Run. Stopping here so you can")
    print(f"confirm everything is setup correctly in {driver.work_dir}")
    exit(0)

  try:
    driver.run_all_samples()
  except ValueError:
    print("Oops!  run_all_samples failed.  Check the sample folders...")

  # Gather up all the results into one place.
  driver.collate_results()

  # Make the targets file in the work dir too. This API needs to change slightly
  # as it required using the private _ssrf_names() function inorder to make
  # the targets csv file...
  d0 = driver.summarize_ssrf(os.path.join(driver._ssrf_names()[0], 'output'))
  driver.ssrf_targets2csv(d0, os.path.join(driver.work_dir, 'targets.csv'))

  # TODO: keep working on implementing the dsl on/off toggle correctly. This
  # existed in the mads_sensitivity.py, but I don't think it was doing anything.
  # (no evidence of ever calling dvmdostem with --cal-mode, so calibration
  # directives file was likely never being read or executed.)

