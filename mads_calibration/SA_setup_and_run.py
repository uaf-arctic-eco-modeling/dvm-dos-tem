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

        Most of the settings should be set in the config file, but some of them
        can be overridden with command line arguments to this script.
        '''.format("")),
  )

  parser.add_argument("configfile", type=config_file_validator,
      help=textwrap.dedent('''The config file to use.'''))

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

  # If user provides stuff on comand line, then we need to open the config file
  # overwrite the appropriate keys and then save the file before passing it to
  # the Sensitivity ctor!

  # Make an instance of the driver object based on the config file...
  driver = drivers.Sensitivity.Sensitivity.fromfilename(config_file_name)

  # Bug in some circumstances with directory not existing yet...
  pathlib.Path(driver.work_dir).mkdir(parents=True, exist_ok=True)

  if args.force:
    driver.clean()

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

