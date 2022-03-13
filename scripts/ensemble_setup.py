#!/usr/bin/env python

# T. Carman, Jan 20 2021 (Biden inauguration!)

# A quick stab at setting up an ensemble of runs.

import os
import argparse
import textwrap
import sys
import subprocess
import json
import numpy as np
import netCDF4 as nc

def setup_for_driver_adjust(exe_path, input_data_path, N=5):
  '''
  Work in progress...
  '''
  # Build the ensemble member directories
  for i in range(N):
    run_dir = 'ens_{:06d}'.format(i)

    # Note the --copy-inputs argument! Might want to verify that it is
    # single site inputs or space consumption might be a problem...
    # If space is a problem, could get fancier and only copy the input file
    # that is going to be modified....
    s = "{}/setup_working_directory.py --copy-inputs --input-data-path {} {}".format(exe_path, input_data_path, run_dir)
    result = subprocess.run(s.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE) #capture_output=True)
    if len(result.stderr) > 0:
      print(result)


  # Now loop over the directories and modify the driver(s) in each
  for i in range(N):
    run_dir = 'ens_{:06d}'.format(i)
    #ds = nc.Dataset('{}/inputs/{}/historic-climate.nc'.format(run_dir, os.path.basename(input_data_path)))
    ds = nc.Dataset('{}/inputs/{}/historic-climate.nc'.format(run_dir, os.path.basename(input_data_path)), 'a')
    air_temp_timeseries = ds.variables['tair'][:,0,0]
    print(type(air_temp_timeseries))
    d=1
    variation = np.random.normal(0, d, len(air_temp_timeseries))
    air_temp_mod = (air_temp_timeseries + variation)
    print(type(air_temp_mod))
    ds.variables['tair'][:,0,0] = air_temp_mod 

    # Now add some variation here....
    #air_temp_mod = ?????
    #
    # This sorta works but would be horribly inefficient...
    #   for i, value in enumerate(air_temp_timeseries):
    #     variation = np.random.normal(value, .1, 1)[0]
    #     print(i, value, variation, value + variation)
    #
    # And write it back to the file here...
    #ds.variables['tair'][:,0,0] = air_temp_mod
    ds.close()


def setup_for_parameter_adjust_ensemble(exe_path, input_data_path, PFT='pft0', N=5, PARAM='albvisnir'):
  '''
  Work in progress...bunch of hard coded stuff, not very flexible at the moment.

  Parameters
  ----------
  exe_path : str, the path to the directory where this (ensemble_setup.py) script is.
    Assumes that other dvmdostem supporting scripts are in the same directory as this
    script.
  N : integer, number of members of the ensemble.
  PARAM : str, which parameter to adjust, must exist in one of the parameter files.
  PFT : str, which pft to adjust parameter for, e.g. 'pft0'
  '''

  # draw samples from distribution
  PARAM_VALS = np.random.normal(loc=.5,scale=.1,size=N)

  # see what the samples look like
  #import matplotlib.pyplot as plt
  #plt.scatter(np.arange(0,N),np.random.normal(loc=.5,scale=.1,size=N))
  #plt.show()

  for i, pv in enumerate(PARAM_VALS):

    # add leading zeros, so like this: ens_000000, ens_000001, etc
    run_dir = 'ens_{:06d}'.format(i)

    # 1. Setup the run directory
    s = "{}/setup_working_directory.py --input-data-path {} {}".format(exe_path, input_data_path, run_dir)
    result = subprocess.run(s.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE) #capture_output=True)
    if len(result.stderr) > 0:
      print(result)
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
    s = "{}/param_util.py --dump-block-to-json {}/parameters/cmt_envcanopy.txt 4".format(exe_path, run_dir)
    result = subprocess.run(s.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE) #, capture_output=True)
    if len(result.stderr) > 0:
      print(result)
    jd = json.loads(result.stdout.decode('utf-8'))
    jd[PFT][PARAM] = pv
    with open('/tmp/data.json', 'w') as f:
      f.write(json.dumps(jd))
    s = "{}/param_util.py --fmt-block-from-json /tmp/data.json {}/parameters/cmt_envcanopy.txt".format(exe_path, run_dir)
    result = subprocess.run(s.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE) #, capture_output=True)
    with open("{}/parameters/cmt_envcanopy.txt".format(run_dir), 'w') as f:
      f.write(result.stdout.decode('utf-8'))

if __name__ == '__main__':

  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
      description=textwrap.dedent('''\
        Helper script for setting up an ensemble of dvmdostem runs.

        Work in progress. For now assumes that the working directory
        from which you run this script will be where you want your 
        ensemble sub folders to be built. So you frequently will 
        end up running this script with a relative path, i.e.:
        ../dvm-dos-tem/scripts/ensemble_setup.py --param-adjust --input-data ../some/path
        '''),
      epilog=textwrap.dedent('''\
        epilog text...''')
  )

  parser.add_argument('--param-adjust', action='store_true',
    help=textwrap.dedent('''\
      Setup for a series of runs where parameter(s) are adjusted between runs.
    '''))

  parser.add_argument('--input-data',
      help="Path to the driving data (i.e. something in the input data catalog...")

  parser.add_argument('--driver-adjust', action='store_true',
    help=textwrap.dedent('''\
      Setup for a series of runs where the drivers are adjusted between runs.
    '''))

  args = parser.parse_args()

  exe_path = os.path.dirname(os.path.abspath(sys.argv[0]))

  if args.param_adjust:
    print("setup for parameter adjust")
    setup_for_parameter_adjust_ensemble(exe_path, args.input_data)
    sys.exit(0)
  
  if args.driver_adjust:
    print("setup for driver adjust")
    setup_for_driver_adjust(exe_path, input_data_path=args.input_data)
    sys.exit(0)
  
  if not (args.driver_adjust or args.param_adjust):
    print("Error: must provide one of the options.")
    parser.print_help()
    
