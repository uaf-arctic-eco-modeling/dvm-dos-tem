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

#new_bounds = [[0.4, 2.0],[0.7, 0.9],[0.4, 0.7],[0.00001, 0.2],[1e-18, 1e-4]]

#PFT2
#new_bounds = [[1,30], [-12.5, -7.2], [-6, -2.5], [-6.0, -1.5], [0.14, 0.20], [0.0007, 0.007], [0.0007, 0.0045],
#              [0.0001,0.001], [0.001, 0.002], [0.00001, 0.0005]]

#PFT1
#new_bounds = [[1,10], [-7.4, -7.2], [-3.2, -2], [-5, -0.1], [0.00008, 0.0001], [0.035, 0.045], [0.04, 0.044445],
#               [0.000005,0.00001], [0.001, 0.005], [0.001, 0.004]]

#PFT4
#new_bounds = [[1, 10], [-11, -7], [-5, -4.1], [-3.9, -2.7], [0.00003, 0.00015], [0.009, 0.014], [0.006, 0.015],
#              [0.0005,0.001], [0.0005, 0.003], [0.0005, 0.004]]

#PFT3
#new_bounds = [[0.1, 5], [-4.6, -4.0], [-7, -6], [-6, -5], [0.0065, 0.008], [0.0002, 0.02], [0.002, 0.01],
#              [0.0001,0.0005], [0.0006, 0.002], [0.0006, 0.002]]

#PFT0
#new_bounds = [[5.5, 6.5], [-4, -2], [-7.5, -6.5], [-6, -5], [0.03, 0.046], [0.00008, 0.001], [0.00005, 0.0001],
#              [0.0001,0.0008], [0.0006, 0.002], [0.0006, 0.002]]

#customize bounds
#STEP 1
new_bounds=[[3.8, 4.0], [396, 398], [750,780], [54, 55], [131, 133]]

#STEP 2

#new_bounds=[[0.1, 5],[0.1, 10],[10, 100],[0.1, 3],[0.1, 3], \
#        [-8, -3],[-6, -2],[-20, -0.1],[-6, -4.5],[-4, -0.5], \
#        [-6, -4],[-6, -2],[-20, -0.1],[-20, -0.1], \
#        [-8, -3],[-8, -3],[-20, -0.1],[-20, -0.1] 
#        ]

#STEP 2 Vegc
#new_bounds = [[-9, -7.5], [-.8, -0.01], [-22.0, -18], [-6, -4.5], [-4, -1.5], \
#[-8.0, -5.0], [-6, -1], [-20, -15], [-12, -8], \
#[-8, -3.0], [-8, -3.0], [-20, -10], [-20, -15], \
#[0.008, 0.013], [0.24, 0.40], [0.01, 0.025], [0.006, 0.009], [0.01, 0.09], \
#[0.0001, 0.001], [0.0000005, 0.0005], [0.004, 0.008], [0.00001, 0.001], \
#[0.0001, 0.005], [0.000005, 0.0005], [0.004, 0.008], [0.000008, 0.001]]

#new_bounds = [[-9.73071531,-7.54176053],\
#[-4.51078194,-0.09138272],\
#[-24.49503541,-19.35870093],\
#[-5.42646185,-4.77267974],\
#[-2.07256013,-0.55864136],\
#[-6.77947821,-5.37297737],\
#[-7.74069131,-1.00633668],\
#[-16.76136371,-15.30096147],\
#[-10.31137062,-8.43732268],\
#[-4.04181913,-2.72608684],\
#[-7.69646878,-5.42135743],\
#[-18.75501584,-14.06969049],\
#[-18.18412644,-17.67168402],\
#[0.00801676,0.01311396],\
#[0.15833982,0.29753398],\
#[0.01663628,0.01721222],\
#[0.00612458,0.00899989],\
#[0.04937073,0.06488356],\
#[0.00014636,0.00046547],\
#[7.2e-07,0.08462146],\
#[0.00454931,0.00534691],\
#[1.089e-05,0.00194012],\
#[0.00191249,0.00478204],\
#[3.576e-05,0.10529057],\
#[0.00417741,0.0066826],\
#[3.001e-05,0.00471857]]

#STEP 3 Vegc Vegn
#new_bounds=[[0.001, 0.015],[0.2, 0.4],[0.001, 0.02],[0.007, 0.009],[0.0001, 0.07], \
#        [0.00005, 0.01],[0.03, 0.1],[0.002, 0.006],[0.0001, 0.005], \
#        [0.0005, 0.01],[0.03, 0.1],[0.001, 0.006],[0.0001, 0.005], \
#        [0.001, 0.05],[0.001, 0.05],[0.001, 0.05],[0.001, 0.05],[0.001, 0.05], \
#        [0.001, 0.05],[0.001, 0.05],[0.001, 0.05],[0.001, 0.05], \
#        [0.001, 0.05],[0.001, 0.05],[0.001, 0.05],[0.001, 0.05]
#        ]


#STEP 3
#new_bounds=[[3, 4],[4.5, 5.5],[1, 2],[3.8, 4.9],[9, 10], \
#        [-5.3, -4.3],[-4.3, -3.3],[-2.2, -1.2],[-6.5, -5.5],[-6, -5], \
#        [-14, -12],[-5, -4], \
#        [-8.3, -7.2],[-1.6, -0.6],[-3.9, -2.9], \
#        [0.002, 0.006], [0.02, 0.06], [0.1, 0.2], [0.00003, 0.00008], [0.05, 0.09], \
#        [0.002, 0.005], [0.05, 0.09], \
#        [0.002, 0.007], [0.03, 0.09], [0.01, 0.05], \
#        [9e-5, 3e-5], [5e-6, 5e-5], [5e-8, 5e-7], [2e-7, 9e-7], [2e-7, 8e-7], \
#        [0.03, 0.09], [2e-5, 9e-5], \
#        [0.002, 0.008], [0.02, 0.08], [0.007, 0.04] \
#        ]


#STEP 4
#new_bounds=[[1e-2, 3],[1e-2, 1.5],[5e-3, 0.8],[1e-4, 0.25],[1e-10, 1e-4]]

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

