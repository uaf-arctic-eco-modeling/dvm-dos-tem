#!/usr/bin/env python

# Hannah 01.27.2021 

#import sys
#import subprocess
#import json
#import numpy as np
#import os 
#import pandas as pd
import matplotlib.pyplot as plt
#import cartopy.crs as ccrs
import xarray as xr
#import glob
#import netCDF4 as nc
import argparse
#import scipy.stats as ss
#from pandas import ExcelWriter


def basic_time_series_plot(runfolders=None):
  #runfolders = os.listdir('/home/hannah/dvmdostem-workflows2')
  #print(runfolders)

  GPP = xr.Dataset()
  for i, folder in enumerate(runfolders):
    ds = xr.open_dataset('%s/output/GPP_yearly_sp.nc'%folder)
    GPP= xr.concat([GPP, ds], dim='folder')

  GPP['folder'] = runfolders # here assigning the name of the runfolder for identification 
  print(GPP)

  fig = plt.figure()
  GPP.folder[1].where((GPP.x==1)&(GPP.y==1)).plot(fig=fig)
  fig.savefig('foo.png')



if __name__ == '__main__':

  parser = argparse.ArgumentParser(
      description='''Plotting for ensembles of dvmdostem runs.''')

  parser.add_argument('--data',
    help=textwrap.dedent('''\
      Path to folder of data, assumes folder has subfolders,
      ens_*, one subfolder for each ensemble member'''))

  parser.add_argument('--var',
    help=textwrap.dedent('''\
      Which variable to plot.'''))

  args = parser.parse_args()
  print(args)

  basic_time_series_plot(runfolders=args.data)

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


