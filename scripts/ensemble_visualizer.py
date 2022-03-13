#!/usr/bin/env python

# Hannah 01.27.2021 

import pathlib
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
  stage = 'sp' # For future...

  # Make a list of all the output data files to plot
  files = sorted(pathlib.Path(data_directory).rglob("{}_yearly_{}.nc".format(var, stage)))

  assert len(files) > 0 , "Error! Can't find any data files! Check that you are providing the correct path to the directory containing your ensemble runs!"

  # Open all the files as xarray Datasets.
  member_datasets = [xr.open_dataset(f) for f in files]

  # This combines all the xrarray.Datasets into one Dataset that has 
  # an new dimension, 'ens'.
  data = xr.concat([m[dict(time=slice(None,None),x=0,y=0)] for m in member_datasets], dim='ens')

  # Print some basic stats
  print("Ensemble Mean:     ", data.mean('ens'))
  print("Std Dev.:          ", data.std('ens'))

  # Now get down to some plotting...
  fig, ax = plt.subplots(figsize=(10, 7))

  # Shade an area +/- one std deviation...
  # plt.fill_between(
  #     data['time'], 
  #     data.median('ens')[var]+data.std('ens')[var], 
  #     data.median('ens')[var]-data.std('ens')[var],
  #     alpha=0.5, color='gray', linewidth=0,
  # )

  # Shade area between 2.5% and 97.5% quantiles...
  plt.fill_between(
      data['time'],
      data[var].quantile(.025, dim='ens'),
      data[var].quantile(.975, dim='ens'),
      alpha=0.25, color='gray', linewidth=0,
  )

  # Plot one line for each ensemble member...
  for i, vdata in enumerate(data[var]):
    plt.plot(vdata, label='ens_{}'.format(i), linewidth=.5, alpha=.5)

  # Make a fat median line...
  plt.plot(data.median('ens')[var], linewidth=1.5, color='red')

  #ax.legend()
  ax.set_xlabel('Time {} years'.format(stage))
  ax.set_ylabel('{} {}'.format(var, data[var].units))
  # ax.set_title('{} variation over time at Kougarok site for varying envcanopy'.format(var))
  ax.set_xlim(left=0)
  fig.savefig('plot.png', dpi=300, bbox_inches='tight')

def utility_verify_adjusted_drivers(workflows_dir):
  '''
  Might want a plotting function to be able to check on what the adjusted drivers look like...
  Really rough stab here with a bunch of hard coded assumptions...
  '''

  filelist = sorted(pathlib.Path(workflows_dir).rglob('*historic-climate.nc'))
  #print("filelist:",  filelist)

  fig, ax = plt.subplots(1,1,figsize=(10,7))

  for i, historic_climate in enumerate(filelist):
    ds = xr.open_dataset(historic_climate)
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
      Assumes that the each ensemble member directory has an historic-climate.nc
      file in it.
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




