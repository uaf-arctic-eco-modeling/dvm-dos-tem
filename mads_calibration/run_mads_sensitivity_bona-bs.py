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
sample_size=16
driver.design_experiment(sample_size, driver.cmtnum,
  params=driver.paramnames,
  pftnums=driver.pftnums,
  percent_diffs=list(0.1*np.ones(len(driver.pftnums))),
  sampling_method='uniform')


#individual PFT
#Soil
#new_bounds = [[1.5, 2.2],[0.6, 0.8],[0.4, 0.6],[0.025, 0.03],[1e-8, 1e-5]]

#PFT2
new_bounds = [[0.35,0.45], [-3.5, -3.], [-6.0, -5.0], [-6.0, -5.0], [0.04, 0.06], [0.0002, 0.0008], [0.0002, 0.0008],
              [0.0001,0.005], [0.0001, 0.005], [0.0001, 0.005]]

#PFT1
#new_bounds = [[0.5,1.5], [-3.6, -3.1], [-7.2, -6], [-7.5, -7], [0.04, 0.06], [0.0006, 0.001], [0.0006, 0.001],
#               [0.0001,0.001], [0.0001, 0.001], [0.0001, 0.001]]

#PFT4
#new_bounds = [[0.1, 10], [-5.5, -4.5], [-6, -2.5], [-6, -1.5], [0.0065, 0.014], [0.004, 0.015], [0.0007, 0.0075],
#              [0.0001,0.001], [0.001, 0.002], [0.00001, 0.0005]]

#PFT3
#new_bounds = [[0.1, 10], [-5.0, -4.0], [-6, -2.5], [-6, -1.5], [0.01, 0.03], [0.004, 0.015], [0.0007, 0.0075],
#              [0.0001,0.001], [0.001, 0.002], [0.00001, 0.0005]]

#PFT0
#new_bounds = [[1, 5], [-3.5, -2.5], [-7., -6.0], [-7.0, -6.0], [0.05, 0.1], [0.00001, 0.00005], [0.0001, 0.001],
#              [0.0001,0.001], [0.0001, 0.001], [0.0001, 0.001]]

#GPP
#new_bounds=[[400, 430], [267, 270], [173,178], [960, 970], [97, 100]]
#new_bounds=[[650, 720], [55, 62], [30, 40], [120, 150], [20, 25]]


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

