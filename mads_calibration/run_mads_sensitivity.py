# Sensitivity adapted for the calibration type output
# uses calibration configuration file as an input
# Example: python3 run_mads_sensitivity.py /work/mads_calibration/config-step1-md1.yaml
# Author: Elchin Jafarov 
# Date: 03/27/2023

import os,sys
import json
import yaml
import numpy as np
import pandas as pd
import mads_sensitivity as Sensitivity

#read the config yaml file and 
if len(sys.argv) != 2:
    print("Usage: python run_mads_sensitivity.py <path/configfilename>")
    sys.exit(1)

config_file_name = sys.argv[1]
print(f"The filename you provided is: {config_file_name}")

with open(config_file_name, 'r') as config_data:
    config = yaml.safe_load(config_data)

#define the SA setup
driver = Sensitivity.SensitivityDriver(config_file=config_file_name)
driver.clean()
sample_size=1000
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

driver.generate_lhc(sample_size)
#print(driver.info())

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

