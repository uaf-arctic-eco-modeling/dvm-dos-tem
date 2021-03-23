#!/usr/bin/env python

# Hannah 01.27.2021 

import sys
import subprocess
import json
import numpy as np
import os 
import pathlib

def adjust_mask(workflows_dir, exe_path):

  # build a list of all the run masks to adjust
  filelist = sorted(pathlib.Path(workflows_dir).rglob('*run-mask.nc'))

  # loop over the list adjusting masks. 
  for i, mask_file in enumerate(filelist):
    print("Changing runmask for {}".format(mask_file))
    s = "{}/runmask-util.py --reset --yx 0 0 {}".format(exe_path, mask_file) 
    result = subprocess.run(s.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE) #, capture_output=True)
    if len(result.stderr) > 0:
      print(result)


def adjust_outvars(ens_folder_list, exe_path):
  ''' add code here to use the outspec_utils.py script '''
  pass

def run(ens_folder_list, exe_path):
  print(ens_folder_list)
  for i, folder in enumerate(ens_folder_list):
    print(i, folder)
    os.chdir(folder)
    print("Current working directory: ", os.getcwd())
    s = "{}/dvmdostem -p 5 -e 10 -s 15 -f config/config.js --force-cmt 4 -l err".format(os.path.dirname(exe_path))
    print("Run command: ", s)
    print(s.split(' '))
    result = subprocess.run(s.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE) #, capture_output=True)
    with open('stdout.txt', 'w') as f:
      f.write(result.stdout.decode('utf-8'))
    with open('stderr.txt', 'w') as f:
      f.write(result.stderr.decode('utf-8'))
    os.chdir("../")

def adjust_drivers():
  '''Psuedo code:
    - copy drivers into current working directory
  '''
  pass
  

if __name__ == '__main__':

  exe_path = os.path.dirname(os.path.abspath(sys.argv[0]))

  #WORKFLOWS_DIR = os.listdir('/home/hannah/dvmdostem-workflows')
  #WORKFLOWS_DIR = os.listdir('/Users/tobeycarman/Documents/SEL/dvmdostem-workflows')
  #WORKFLOWS_DIR = os.listdir('/home/UA/tcarman2/dvmdostem-workflows')
  WORKFLOWS_DIR = '/data/workflows'

  adjust_mask(WORKFLOWS_DIR, exe_path)

  run(runfolders, exe_path)
































