# Sensitivity adapted for the calibration type output
# uses calibration configuration file as an input
# Example: python3 run_mads_sensitivity.py /work/mads_calibration/config-step1-md1.yaml
# Author: Elchin Jafarov 
# Date: 03/27/2023

import os,sys
import json
import numpy as np
import pandas as pd
import mads_sensitivity as Sensitivity

#read the config yaml file and 
if len(sys.argv) != 2:
    print("Usage: python run_mads_sensitivity.py <path/configfilename>")
    sys.exit(1)

config_file_name = sys.argv[1]
print(f"The filename you provided is: {config_file_name}")

#define the SA setup
driver = Sensitivity.SensitivityDriver(config_file=config_file_name)
driver.clean()
sample_size=50
driver.design_experiment(sample_size, driver.cmtnum,
  params=driver.paramnames,
  pftnums=driver.pftnums,
  percent_diffs=list(0.1*np.ones(len(driver.pftnums))),
  sampling_method='uniform')


#individual PFT
#Soil
new_bounds = [[0.1, 0.5],[0.6, 0.8],[0.4, 0.6],[0.008, 0.015],[1e-8, 1e-5]]

#PFT2
#new_bounds = [[3.5,4.5], [-7.8, -6], [-5.0, -3], [-7.0, -4.5], [0.009, 0.013], [0.008, 0.02], [0.008, 0.02],
#              [0.0001,0.005], [0.0001, 0.005], [0.0001, 0.005]]

#PFT1
#new_bounds = [[1,5], [-6, -2], [-8, -5], [-6, -4], [0.007, 0.08], [0.008, 0.02], [0.002, 0.018],
#               [0.001,0.005], [0.001, 0.005], [0.001, 0.004]]

#PFT4
#new_bounds = [[0.1, 10], [-5.5, -4.5], [-6, -2.5], [-6, -1.5], [0.0065, 0.014], [0.004, 0.015], [0.0007, 0.0075],
#              [0.0001,0.001], [0.001, 0.002], [0.00001, 0.0005]]

#PFT3
#new_bounds = [[0.1, 10], [-4.4, -3.6], [-6, -2.5], [-6, -1.5], [0.0125, 0.02], [0.004, 0.015], [0.0007, 0.0075],
#              [0.0001,0.001], [0.001, 0.002], [0.00001, 0.0005]]

#PFT0
#new_bounds = [[15, 30], [-6.0, -2.5], [-10.0, -8.0], [-10.0, -8.0], [0.01, 0.02], [0.006, 0.008], [0.0025, 0.008],
#              [0.003,0.01], [0.001, 0.01], [0.001, 0.01]]

#GPP
#new_bounds=[[400, 430], [267, 270], [173,178], [960, 970], [97, 100]]


for i in range(len(driver.params)):
    driver.params[i]['bounds']=new_bounds[i]

driver.generate_uniform(sample_size)
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

