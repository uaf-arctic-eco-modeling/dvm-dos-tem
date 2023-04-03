#post-processing script 
#1. processes all the finalresults files for a given step
#2. saves optimal parameter values into a list 
#3. removes all duplicates from the list and save them into the csv file
#4. runs the dmvdostem for all elements of the list and save them into another csv file
#Example: python3 post_runs.py /work/mads_calibration/config-step1-md1.yaml
#Author: Elchin Jafarov
#Date: 03/2023

import utils as ut
import numpy as np
import sys,os
sys.path.append(os.path.join('/work','mads_calibration'))
import TEM
import sys

if len(sys.argv) != 2:
    print("Usage: python3 post_runs.py <path/configfilename>")
    sys.exit(1)

config_file_name = sys.argv[1]
print(f"The filename you provided is: {config_file_name}")

def get_cofig_file(config_file_name):
    dvmdostem=TEM.TEM_model(config_file_name)
    dvmdostem.set_params(dvmdostem.cmtnum, dvmdostem.paramnames, dvmdostem.pftnums)
    return dvmdostem

def save_file(filename,data):
    np.savetxt(filename,data,delimiter =", ",fmt ='% s')
    return

fl=['../scripts/AC3-STEP1-MD1-1-R-EJ.finalresults',  
'../scripts/AC3-STEP1-MD1-R-EJ-new.finalresults', 
'../scripts/AC3-STEP1-MD1-EJ.finalresults', 
'../scripts/AC3-STEP1-MD1-R-EJ.finalresults']

#get the list of initial conditions from the finalresults file
a=ut.get_optimal_sets_of_params(fl[0]) 
for i in fl[1:]:
    a = ut.merge_parameter(a, ut.get_optimal_sets_of_params(i))

d=list(a.keys())
ic_list= [[val[i] for key, val in a.items()] for i in range(len(a[d[0]]))]
print(ic_list)

tem=get_cofig_file(config_file_name)

new_list = []
u_set = set()
for item in ic_list:
    if item[2] not in u_set:
        u_set.add(item[2])
        new_list.append(item)
    else:
        pass

save_file('param.csv',new_list)
y=[tem.run_TEM(ig) for ig in new_list] 
y.append(tem.get_targets(1))
print(y)
save_file('out.csv',y)

