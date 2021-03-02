#!/usr/bin/env python

# Hannah 01.27.2021 

#import sys
#import subprocess
#import json
#import numpy as np
import os
#import pandas as pd
import matplotlib.pyplot as plt
#import cartopy.crs as ccrs
import xarray as xr
#import glob
#import netCDF4 as nc
import argparse
import textwrap
#import scipy.stats as ss
#from pandas import ExcelWriter


def basic_time_series_plot(runfolders=None, var=None):
  runfolders = os.listdir(runfolders)
  #print(runfolders)
  runfolders = [i for i in runfolders if ".DS_Store" not in i]

  fig, ax = plt.subplots(figsize=(10, 7))

  for folder in runfolders:
    ds = xr.open_dataset('{}/output/{}_yearly_sp.nc'.format(folder, var)) # X array dataset
    dataV = ds.variables[var]
    ax.plot(ds.time, dataV[:,0,0], label='%s'%folder)

  ax.legend()
  ax.set_xlabel('Time after equilibrium [years]')
  ax.set_ylabel('{} [g/m$^2$]'.format(var))
  ax.set_title('GPP variation over time at Kougarok site for varying envcanopy')
  ax.set_xlim(left=0)
  fig.savefig('plot.png', dpi=300, bbox_inches='tight')



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

  args = parser.parse_args()
  print(args)

  datafolder = os.path.abspath(args.data)
  print(datafolder)
  basic_time_series_plot(runfolders=datafolder, var=args.var)

# Ideas for command line interface

# $ ./ensemble_visualizer.py --data /path/to/folder/of/ens/runs --var GPP --yx --stage sp

#GPP.folder[1].plot.scatter(time, )
#GPP.folder[1].
#plt.savefig('foo.png')

#for i, folder in enumerate(runfolders):
#  globals()["GPP_"+str(folder)]= xr.open_dataset('%s/output/GPP_yearly_sp.nc'%folder)

#print(GPP_ens_000001)

#GPP_ens_000001.
#plt.savefig('foo.png')


