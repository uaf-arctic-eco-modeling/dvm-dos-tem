### Author: Helene Genet
### Institution: UAF, IAB
### Contact: hgenet@alaska.edu
### Description: This script will add new community to the parameter files, 
### and update existing parameters for communities newly calibrated.
### New calibrations should be stored in a specific parameter folder where
### each file have a single community listed.


from google.cloud import storage
import os
from pathlib import Path
import subprocess
from git import Repo
import shutil
import re
import pandas as pd


### PATH TO THE DIRECTORY FOR COMBINING PARAMETERIZATIONS

local_path = '/Users/helenegenet/Helene/TEM/DVMDOSTEM/calibration/parameters'  



### DOWNLOAD PARAMETER FILES FOR INDIVIDUAL COMMUNITIES

bucket_path = 'vb-tem/Calibration/calibration_files/calibrated'
subprocess.run(['gcloud', 'auth', 'application-default', 'login'], check=True) 
subprocess.run(['gcloud', 'storage', 'cp', '--recursive', 'gs://'+ bucket_path, local_path], check=True) 




### DOWNLOAD PARAMETER FILES FROM MASTER

os.makedirs(os.path.join(local_path,'master'), exist_ok=True)
url = 'https://github.com/uaf-arctic-eco-modeling/dvm-dos-tem.git'
Repo.clone_from(url, os.path.join(local_path,'master'))
for item in os.listdir(os.path.join(local_path,'master')):
  if os.path.isdir(os.path.join(local_path,'master',item)):
    if item != 'parameters' and item != 'calibration':
      shutil.rmtree(os.path.join(local_path,'master',item))
  else:
    os.remove(os.path.join(local_path,'master',item))
#list all parameter files
lpf = os.listdir(os.path.join(local_path,'master','parameters'))
lpf




### LIST AVAILABLE COMMUNITIES

## List the CMT that are calibrated
cmtlist_calib = []
for pardir in os.listdir(os.path.join(local_path,'calibrated')):
  if os.path.isdir(os.path.join(local_path,'calibrated',pardir)):
    print(pardir)
    file_path = os.path.join(local_path,'calibrated',pardir, 'cmt_calparbgc.txt')
    if os.path.isfile(file_path):
      with open(file_path, 'r') as f:
        b = f.read()
        CMT = [item for item in re.split("\n",b) if "CMT" in item][0].replace(" ", "").split('//')[1]
        print(CMT)
        cmtlist_calib.append(CMT)

## List the CMT that are in master
cmtlist_master = []
if os.path.isdir(os.path.join(local_path,'master','parameters')):
  file_path = os.path.join(local_path,'master','parameters', 'cmt_calparbgc.txt')
  if os.path.isfile(file_path):
    with open(file_path, 'r') as f:
      b = f.read()
      c = re.split("\n//========",b)
    for block in c:
      if "cmax" in block:
        print("yes")
        print(block)
        CMT = [item for item in re.split("\n",block) if "CMT" in item][0].replace(" ", "").split('//')[1]
        print(CMT) 
        cmtlist_master.append(CMT)

cmtlist = sorted(list(set(cmtlist_master + cmtlist_calib)))
cmtlist



### COMBINE THE PARAMETERIZATIONS

parfile='cmt_calparbgc.txt'
parfile = 'cmt_bgcsoil.txt'
cmt='CMT71'

os.makedirs(os.path.join(local_path,'combined'), exist_ok=True)
blockdelimiter = "\n//==========================================================="
for parfile in lpf:
  print('Combining parameterizations for', parfile)
  allblocks = ""
  with open(os.path.join(local_path,'master','parameters','cmt_bgcsoil.txt'), 'r') as f:
    b = f.read()
  c = re.split("\n//========",b)
  allblocks = allblocks + c[0] + blockdelimiter + "\n"
  for cmt in cmtlist:
    if cmt in cmtlist_calib:
      print(cmt,'parameter values from new calibrations')
      for pardir in os.listdir(os.path.join(local_path,'calibrated')):
        if cmt in os.path.basename(pardir):
          path = os.path.join(local_path,'calibrated',pardir,parfile)
          with open(path, 'r') as f:
            b = f.read()
          c = re.split("\n//========",b)
          d = re.split("\n",[item for item in c if  cmt in item][0])
          block = "\n".join([item for item in d if "=====" not in item])
          # Check that all parameters are present
          e = (re.sub(r'^//.*\n?', '', block, flags=re.MULTILINE))
          f = pd.DataFrame(re.split("\n",e))
          g = f[0].str.split('//', expand=True)
          if (parfile == 'cmt_bgcsoil.txt') and (not g[1].str.contains('rhmoistfrozen', case=False).any()) :
            g = pd.concat([g.iloc[:1], pd.DataFrame([{0: '0.0', 1: 'rhmoistfrozen:'}]) , g.iloc[1:]], ignore_index=True)
          if (parfile == 'cmt_calparbgc.txt') and (not g[1].str.contains('s2dfraction', case=False).any()) :
            g = pd.concat([g.iloc[:18], pd.DataFrame([{0: '1.0', 1: 's2dfraction:'}]) , g.iloc[18:]], ignore_index=True)
          if (parfile == 'cmt_calparbgc.txt') and (not g[1].str.contains('d2mfraction', case=False).any()) :
            g = pd.concat([g.iloc[:19], pd.DataFrame([{0: '1.0', 1: 'd2mfraction:'}]) , g.iloc[19:]], ignore_index=True)
#          g[0] = g[0].str.replace(' ', '')
          g[1] = g[1].str.replace(' ', '')
          g = g[g[0] != '']
          h = "\n".join(g.apply(lambda row: '//'.join(row.astype(str)), axis=1))
          header = [item for item in [i for i in re.split("\n",block) if i.startswith('//')] if 'CMT' in item or 'PFT' in item or 'name:' in item or 'names:' in item or 'pftnames:' in item]
          i = header + re.split("\n",h)
          block_final = '\n'.join(i)
          #if block.endswith("\n"):
          #  block = block[:-len("\n")]
    else:
      print(cmt,'parameter values from master')
      path = os.path.join(local_path,'master','parameters',parfile)
      if os.path.isfile(path):
        with open(path, 'r') as f:
          b = f.read()
        c = re.split("\n//========",b)
        d = re.split("\n",[item for item in c if  cmt in item][0])
        block = "\n".join([item for item in d if "=====" not in item])
      # Check that all parameters are present
      e = (re.sub(r'^//.*\n?', '', block, flags=re.MULTILINE))
      f = pd.DataFrame(re.split("\n",e))
      g = f[0].str.split('//', expand=True)
      if (parfile == 'cmt_bgcsoil.txt') and (not g[1].str.contains('rhmoistfrozen', case=False).any()) :
        g = pd.concat([g.iloc[:1], pd.DataFrame([{0: '0.0', 1: 'rhmoistfrozen:'}]) , g.iloc[1:]], ignore_index=True)
      if (parfile == 'cmt_calparbgc.txt') and (not g[1].str.contains('s2dfraction', case=False).any()) :
        g = pd.concat([g.iloc[:18], pd.DataFrame([{0: '1.0', 1: 's2dfraction:'}]) , g.iloc[18:]], ignore_index=True)
      if (parfile == 'cmt_calparbgc.txt') and (not g[1].str.contains('d2mfraction', case=False).any()) :
        g = pd.concat([g.iloc[:19], pd.DataFrame([{0: '1.0', 1: 'd2mfraction:'}]) , g.iloc[19:]], ignore_index=True)
#      g[0] = g[0].str.replace(' ', '')
      g[1] = g[1].str.replace(' ', '')
      g = g[g[0] != '']
      h = "\n".join(g.apply(lambda row: '//'.join(row.astype(str)), axis=1))
      header = [item for item in [i for i in re.split("\n",block) if i.startswith('//')] if 'CMT' in item or 'PFT' in item or 'name:' in item or 'names:' in item or 'pftnames:' in item]
      i = header + re.split("\n",h)
      block_final = '\n'.join(i)
    allblocks = allblocks + block_final + blockdelimiter + "\n"
    #allblocks = "\n".join([line for line in allblocks.splitlines() if line.strip()])
  with open(os.path.join(local_path,'combined',parfile), "a") as file:
    file.write(allblocks)
  
