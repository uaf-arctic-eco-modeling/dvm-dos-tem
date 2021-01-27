#!/usr/bin/env python

# Hannah 01.27.2021 



import subprocess
import json
import numpy as np
import os 

runfolders=os.listdir('/home/hannah/dvmdostem-workflows')

print(runfolders)
for i, folder in enumerate(runfolders):
  s = "../dvm-dos-tem/scripts/runmask-util.py --reset --yx 0 0 {}/run-mask.nc".format(folder)
  result = subprocess.run(s.split(' '), capture_output=True)
  os.chdir(folder)
  s = "../../dvm-dos-tem/dvmdostem -p 5 -e 5 -s 5 -f config/config.js --force-cmt 4 -l err"
  result = subprocess.run(s.split(' '), capture_output=True) 
  #print(result.stderr)
  os.chdir('../')
  
































