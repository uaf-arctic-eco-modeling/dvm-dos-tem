# Sensitivity adapted for the calibration type output
# uses calibration configuration file as an input
# Author: Elchin Jafarov 
# Date: 03/27/2023

import os
import json
import numpy as np
import pandas as pd
import mads_sensitivity as Sensitivity
import TEM

config_file_name='config-step1-md1.yaml'
driver = Sensitivity.SensitivityDriver(config_file=config_file_name)
driver.clean()
sample_size=10
driver.design_experiment(sample_size, driver.cmtnum,
  params=driver.paramnames,
  pftnums=driver.pftnums,
  percent_diffs=list(0.5*np.ones(len(driver.pftnums))),
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