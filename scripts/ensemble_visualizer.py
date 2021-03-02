#!/usr/bin/env python

# Hannah 01.27.2021 

import sys
import os
import matplotlib.pyplot as plt
import xarray as xr
import argparse
import textwrap


def basic_time_series_plot(data_directory=None, var=None):
  '''
  Outputs/saves a basic time series plot of one dvmdostem output variable.

  Parameters
  ----------
  data_directory : str
    Path to a folder containing one subfolder for each ensemble member.
  var : str
    The variable to plot.

  Returns
  -------
  None
  '''
  runfolders = os.listdir(data_directory)
  runfolders = [i for i in runfolders if ".DS_Store" not in i]
  # Filter out non directories.
  runfolders = [i for i in filter(os.path.isdir, runfolders)]

  # Open the first file so we can grab some metadata and check a few things
  ds = xr.open_dataset('{}/output/{}_yearly_sp.nc'.format(runfolders[0], var))

  # Make a few assertions, sanity checking the data...the idea here
  # is that this will fail when we try to read a file with more 
  # dimensions, i.e. something output by layer or by PFT. When this
  # happens, we can add some more code here to deal with it...
  assert len(ds.variables[var].dims) == 3, "Incorrect number of dimensions for variable in file!"
  assert 'units' in ds.variables[var].attrs, "Can't find units attribute in file!"

  # Grab units from first file, assume all the rest are the same...
  unit_str = ds.variables[var].attrs['units']

  # Now get down to some plotting...
  fig, ax = plt.subplots(figsize=(10, 7))

  for folder in runfolders:
    ds = xr.open_dataset('{}/output/{}_yearly_sp.nc'.format(folder, var)) # X array dataset
    dataV = ds.variables[var]
    ax.plot(ds.time, dataV[:,0,0], label='%s'%folder)

  ax.legend()
  ax.set_xlabel('Time after equilibrium [years]')
  ax.set_ylabel('{} {}'.format(var, unit_str))
  ax.set_title('{} variation over time at Kougarok site for varying envcanopy'.format(var))
  ax.set_xlim(left=0)
  fig.savefig('plot.png', dpi=300, bbox_inches='tight')

def utility_verify_adjusted_drivers(run_dir):
  '''
  Might want a plotting funciton to be able to check on what the adjusted drivers look like...
  Really rough stab here with a bunch of hard coded assumptions...
  '''
  runfolders = os.listdir(run_dir)
  runfolders = [i for i in runfolders if ".DS_Store" not in i]
  # Filter out non directories.
  runfolders = [i for i in filter(os.path.isdir, runfolders)]

  fig, ax = plt.subplots(1,1,figsize=(10,7))

  for i, folder in enumerate(runfolders):
    ds = xr.open_dataset('{}/inputs/SITE_cru-ts40_ar5_rcp85__MRI-CGCM3/historic-climate.nc'.format(folder))
    ax.plot(ds.variables['tair'][:,0,0])

  fig.savefig('driverplot.png')


if __name__ == '__main__':

  parser = argparse.ArgumentParser(
      description='''Plotting for ensembles of dvmdostem runs.''')

  parser.add_argument('--data', required=True,
    help=textwrap.dedent('''\
      Path to folder of data, assumes folder has subfolders,
      ens_*, one subfolder for each ensemble member'''))

  parser.add_argument('--var',
    help=textwrap.dedent('''\
      Which variable to plot.'''))

  parser.add_argument('--view-drivers', action='store_true',
    help=textwrap.dedent('''\
      A helper function for viewing what the adjusted drivers look like...
    '''))


  args = parser.parse_args()
  print(args)

  if args.view_drivers:
    utility_verify_adjusted_drivers(args.data)
    sys.exit(0)


  datafolder = os.path.abspath(args.data)
  print(datafolder)
  basic_time_series_plot(data_directory=datafolder, var=args.var)

# Ideas for command line interface

# $ ./ensemble_visualizer.py --data /path/to/folder/of/ens/runs --var GPP --yx 0 0 --stage sp




