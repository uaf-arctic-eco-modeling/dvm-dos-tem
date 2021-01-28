#!/usr/bin/env python

# T. Carman, Jan 20 2021 (Biden inauguration!)

# A quick stab at setting up an ensemble of runs.

import argparse
import textwrap
import sys
import subprocess
import json
import numpy as np

# number of runs in ensemble
N = 5

# draw samples from distribution
PARAM_VALS = np.random.normal(loc=.5,scale=.1,size=N)

# see what the samples look like
#import matplotlib.pyplot as plt
#plt.scatter(np.arange(0,N),np.random.normal(loc=.5,scale=.1,size=N))
#plt.show()

PARAM = 'albvisnir'
PFT = 'pft0'

for i, pv in enumerate(PARAM_VALS):

  # add leading zeros, so like this: ens_000000, ens_000001, etc
  run_dir = 'ens_{:06d}'.format(i)


  # 1. Setup the run directory
  s = "../dvm-dos-tem/scripts/setup_working_directory.py --input-data-path ../dvmdostem-input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_CALM_Kougarok_10x10/ {}".format(run_dir)
  result = subprocess.run(s.split(' '), capture_output=True)
  # Note that we could avoid the subprocess by importing the setup-working-directory.py into 
  # this script and using the appropriate functions...

  # 2. Modify the appropriate value in the parameter files. This is somewhat
  #  obtuse, these are the steps: 
  #    a) convert "block" of parameter data to json (using param_util.py)
  #    b) modify value in json datastructure
  #    c) write json data structure to temporary file
  #    d) convert json file to "block" of data formatted as required for 
  #       our parameter files, again using param_util.py
  #    e) capture output of previous step and overwrite the parameter file
  s = "../dvm-dos-tem/scripts/param_util.py --dump-block-to-json {}/parameters/cmt_envcanopy.txt 4".format(run_dir)
  result = subprocess.run(s.split(' '), capture_output=True)
  jd = json.loads(result.stdout.decode('utf-8'))
  jd[PFT][PARAM] = pv
  with open('/tmp/data.json', 'w') as f:
    f.write(json.dumps(jd))
  s = "../dvm-dos-tem/scripts/param_util.py --fmt-block-from-json /tmp/data.json {}/parameters/cmt_envcanopy.txt".format(run_dir)
  result = subprocess.run(s.split(' '), capture_output=True)
  with open("{}/parameters/cmt_envcanopy.txt".format(run_dir), 'w') as f:
    f.write(result.stdout.decode('utf-8'))

if __name__ == '__main__':

  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
      description=textwrap.dedent('''\
        Helper script for setting up an ensemble of dvmdostem runs.
        '''),
      epilog=textwrap.dedent('''\
        epilog text...''')
  )

  parser.add_argument('--param-adjust', action='store_true',
    help=textwrap.dedent('''\
      Setup for a series of runs where parameter(s) are adjusted between runs.
    '''))

  parser.add_argument('--driver-adjust', action='store_true',
    help=textwrap.dedent('''\
      Setup for a series of runs where the drivers are adjusted between runs.
    '''))

  args = parser.parse_args()

  if args.param_adjust:
    print("setup for parameter adjust")
    sys.exit(0)
  
  if args.driver_adjust:
    print("setup for driver adjust")
    sys.exit(0)
    