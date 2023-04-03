# Sensitivity adapted for the calibration type output
# uses calibration configuration file as an input
# Example: python3 run_mads_sensitivity.py /work/mads_calibration/config-step1-md1.yaml
# Author: Elchin Jafarov 
# Date: 03/27/2023

import os
import json
import numpy as np
import pandas as pd
import mads_sensitivity as Sensitivity
import TEM
import sys

if len(sys.argv) != 2:
    print("Usage: python3 run_mads_sensitivity.py <path/configfilename>")
    sys.exit(1)

config_file_name = sys.argv[1]
print(f"The filename you provided is: {config_file_name}")

# config_file_name='../scripts/config-step1-md3.yaml'
driver = Sensitivity.SensitivityDriver(config_file=config_file_name)
driver.clean()
sample_size=1000
driver.design_experiment(sample_size, driver.cmtnum,
  params=driver.paramnames,
  pftnums=driver.pftnums,
  percent_diffs=list(0.8*np.ones(len(driver.pftnums))),
  sampling_method='uniform')

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

#once complete, run the following in the terminal to copy results from workdir to SA folder
# cp -r /data/workflows/STEP2-MD3-CR_4/results.txt /work/mads_calibration/SA/results_STEP2-MD3-CR_1.txt
# cp -r /data/workflows/STEP2-MD3-CR_4/sample_matrix.csv /work/mads_calibration/SA/sample_matrix_STEP2-MD3-CR_1.csv


