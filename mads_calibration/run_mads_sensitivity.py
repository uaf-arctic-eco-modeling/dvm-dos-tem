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

import drivers.Sensitivity 

def config_file_validator(arg_config_file):
  '''Make sure that the file exists'''
  try:
    files = os.path.isfile(arg_config_file)
  except OSError as e:
    msg = "Can't find file: {}".format(e)
    raise argparse.ArgumentTypeError(msg)
  return arg_config_file

if __name__ == '__main__':
  
  import argparse
  import textwrap

  parser = argparse.ArgumentParser(
    formatter_class = argparse.RawDescriptionHelpFormatter,
      description=textwrap.dedent('''\
        This script runs a special Sensitivity Analysis that is used as
        as the initial part of a the calibration process. This is the left 
        (orange) half of the diagram.     
        '''.format("")),
  )

  parser.add_argument("configfile", type=config_file_validator,
      help=textwrap.dedent('''The config file to use.'''))

  parser.add_argument('-f', '--force', action='store_true', 
      help=textwrap.dedent('''Clean the working directory without warning.'''))

  args = parser.parse_args()
  

config_file_name = args.configfile

print(f"The filename you provided is: {config_file_name}")

with open(config_file_name, 'r') as config_data:
    config = yaml.safe_load(config_data)

# Make an instance of the driver object
driver = drivers.Sensitivity.SensitivityDriver()

# Set the "seed" path. This is the directory where initial parameter values
# will be read from.
driver.set_seed_path('/work/parameters/')

# Set the working directory. This is the folder where all the individual runs
# will be carried out. Each individual run directory will be setup using
# parameter values from the seed path, and then parameter values in the
# run directories will be adjusted as part of the sensitivity analysis.
driver.set_work_dir(os.path.join(os.path.dirname(os.path.abspath(config_file_name)), 'SA'))

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
driver.design_experiment(Nsamples=10, 
                         cmtnum=config['cmtnum'], 
                         params=config['params'], 
                         pftnums=config['pftnums'], 
                         percent_diffs=list(perturbations),
                         sampling_method='uniform')

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
#define the SA setup
driver = Sensitivity.SensitivityDriver(config_file=config_file_name)
driver.clean()
sample_size=10
driver.design_experiment(sample_size, driver.cmtnum,
  params=driver.paramnames,
  pftnums=driver.pftnums,
  percent_diffs=list(0.1*np.ones(len(driver.pftnums))),
  sampling_method='uniform')

#getting initial parameters from config file
initial=config['mads_initial_guess']

perturbation=0.9
for i in range(len(driver.params)):
    driver.params[i]['initial']=initial[i]
    driver.params[i]['bounds']=[initial[i] - (initial[i]*perturbation), initial[i] + (initial[i]*perturbation)]

print('params:',driver.params)

#customize bounds
#new_bounds=[[1, 5], [1, 5], [1, 5], [1, 5], \
#        [-20, -0.1],[-20, -0.1],[-20, -0.1],[-20, -0.1],[-20, -0.1], \
#        [-20, -0.1],[-20, -0.1],[-20, -0.1],[-20, -0.1],[-20, -0.1] \
#        ]

#for i in range(len(driver.params)):
#    driver.params[i]['bounds']=new_bounds[i]

#driver.generate_lhc(sample_size)
driver.generate_uniform(sample_size)
#print(driver.info())

d2 = drivers.Sensitivity.SensitivityDriver()
print(d2.info())
d2.set_work_dir(config['work_dir'])
d2.set_seed_path('/work/parameters/')
d2.design_experiment(10, config['cmtnum'], config['params'], config['pftnums'], list(0.1*np.ones(len(config['pftnums']))), sampling_method='uniform')
d2.setup_multi()
d2.get_initial_params_dir()
# d2.info()

from IPython import embed; embed()


#setup folders based on a sample size  
try:
    driver.setup_multi(calib=True)
except ValueError:
    print("Oops!  setup_multi failed.  Check the setup...")

#run themads_sensitivity in parallel
try:
    driver.run_all_samples()
except ValueError:
    print("Oops!  run_all_samples failed.  Check the sample folders...")

#save results in the work_dir results.txt
#NOTE, that the last row in the results.txt is targets/observations
driver.save_results()

