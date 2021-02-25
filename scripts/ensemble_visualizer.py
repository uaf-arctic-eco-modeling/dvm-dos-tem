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
#import scipy.stats as ss
#from pandas import ExcelWriter


runfolders= os.listdir('/home/hannah/dvmdostem-workflows2')
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




#GPP.folder[1].plot.scatter(time, )
#GPP.folder[1].
#plt.savefig('foo.png')





#for i, folder in enumerate(runfolders):
#  globals()["GPP_"+str(folder)]= xr.open_dataset('%s/output/GPP_yearly_sp.nc'%folder)

#print(GPP_ens_000001)


#GPP_ens_000001.
#plt.savefig('foo.png')


































































