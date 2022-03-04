#!/usr/bin/python 
# A sample of the sensitivity run script
# Author: Elchin Jafarov
# date: 12.02.2021

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import Sensitivity
import param_util as pu

driver = Sensitivity.SensitivityDriver()
# change workdir and site here
#driver.work_dir='/data/workflows/sensitivity_analysis_EML'
driver.site='/data/input-catalog/cru-ts40_ar5_rcp85_mri-cgcm3_EML_study_area_10x10'
driver.opt_run_setup = '-p 5 -e 5 -s 5 -t 5 -n 5'

# setup parameters: 
# Nsamples: number of sample points in the parameter interval
# cmtnum: community type number (site specific)
# params: list of parameter names
# pftnums: list, pft numbers marked by 0 and non pfts by None
# percent_diffs: the difference from the initial value (i.e. initial_value +- initial_value*percent)
# sampling_method: currently only two: lhs and uniform
driver.design_experiment(Nsamples=10, cmtnum=4, params=['cmax','rhq10','nmax'], 
                         pftnums=[0,None,0], percent_diffs=[.25, .25, 0.25],
                         sampling_method='lhc')
print(driver.info())

#setup outputs, these will change depending on what the user wants to ouput
print('Setting up the outputs...')
driver.outputs.append({'name': 'ALD', 'type': 'xxx'})
print(driver.outputs)

try:
    driver.setup_multi()
except ValueError:
    print("Oops!  setup_multi failed.  Check the setup...")

try:
    driver.run_all_samples()
except ValueError:
    print("Oops!  run_all_samples failed.  Check the sample folders...")

#save the sample matrix in the same folder
driver.save_experiment(driver.work_dir+'/')

print('RUN IS SUCCESSFUL!!!')
