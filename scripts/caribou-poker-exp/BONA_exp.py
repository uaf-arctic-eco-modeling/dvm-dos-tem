#!/usr/bin/env python
# coding: utf-8

import netCDF4 as nc
import numpy as np
from matplotlib import pyplot as plt
import os
import json
import pandas as pd
import seaborn as sns
import xarray as xr


from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = "all"


get_ipython().system('pwd')


os.environ['HDF5_USE_FILE_LOCKING']='FALSE'


#establish site coordinates

run_name='BONA-birch'

station_lat = 65.15401 #caribou creek
station_lon = -147.50258 #caribou creek

#get netcdf coordinates from runmask
#runmask = nc.Dataset('/data/workflows/BONA-birch/run-mask.nc') #original climate dataset
runmask = nc.Dataset('/data/input-catalog/cpcrw_towers_downscaled/run-mask.nc') #downscaled climate dataset
lats=runmask.variables['lat'][:]
lons=runmask.variables['lon'][:]

#get distance between station and each cell
ydist = lats-station_lat
xdist = lons-station_lon
euc_dist = (ydist**2 + xdist**2)**.5

y_x = np.unravel_index(np.argmin(euc_dist),np.shape(lats))
print('y coordinate: {}'.format(y_x[0]))
print('x coordinate: {}'.format(y_x[1]))


# # BONA Birch

get_ipython().system('rm -r /data/workflows/BONA-birch/')


get_ipython().run_line_magic('cd', '/work')


#set working directory, original input
#!scripts/setup_working_directory.py \
#--input-data-path /data/input-catalog/caribou-poker_merged/ \
#/data/workflows/BONA-birch/


#set working directory, downscaled input
get_ipython().system('scripts/util/setup_working_directory.py  --input-data-path /data/input-catalog/cpcrw_towers_downscaled/  /data/workflows/BONA-birch/')


# Adjust the config file
CONFIG_FILE = os.path.join('/data/workflows/BONA-birch/', 'config/config.js')
# Read the existing data into memory
with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)
    
    config['IO']['output_nc_eq'] = 1 # Modify value...

# Write it back..
with open(CONFIG_FILE, 'w') as f:
    json.dump(config, f, indent=2)


#poker flats: 0, 1
#caribou creek: 3, 0 # original climate
#caribou creek: 0, 0, #downscaled climate
# setup runmask
get_ipython().system('runmask.py --reset  --yx 0 0  --show  /data/workflows/BONA-birch/run-mask.nc')


path_to_soil_input='/data/input-catalog/cpcrw_towers_downscaled/soil-texture.nc'
soil_dataset = nc.Dataset(path_to_soil_input)
print(soil_dataset)
print('target cell is {}% clay, {}% sand, and {}% silt'.format(soil_dataset['pct_clay'][y_x[0], y_x[1]], 
                                                               soil_dataset['pct_sand'][y_x[0], y_x[1]], 
                                                               soil_dataset['pct_silt'][y_x[0], y_x[1]]))
soil_dataset.close()


#soil_dataset = nc.Dataset(path_to_soil_input, 'r+')
#soil_dataset['pct_clay'][y_x[0], y_x[1]] = 10 # originally 8.81557846069336
#soil_dataset['pct_sand'][y_x[0], y_x[1]] = 27 # originally 42.533843994140625
#soil_dataset['pct_silt'][y_x[0], y_x[1]] = 63 # origially 48.650577545166016
#print('target cell is {}% clay, {}% sand, and {}% silt'.format(soil_dataset['pct_clay'][y_x[0], y_x[1]], 
#                                                               soil_dataset['pct_sand'][y_x[0], y_x[1]], 
#                                                               soil_dataset['pct_silt'][y_x[0], y_x[1]]))
#drainage.close()


get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --empty')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on CMTNUM yearly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on GPP monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on RG monthly compartment')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on RH monthly layer')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on RM monthly compartment')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on NPP monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on ALD yearly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on SHLWC yearly monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on DEEPC yearly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on MINEC yearly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on ORGN yearly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on AVLN yearly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on LTRFALC monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on LWCLAYER monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on TLAYER monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on LAYERDEPTH monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on LAYERDZ monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on EET monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on TRANSPIRATION monthly PFT')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on LAI monthly PFT')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on VEGC monthly PFT compartment')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-birch/config/output_spec.csv --on BURNVEG2AIRC monthly')


get_ipython().run_line_magic('cd', '/data/workflows/BONA-birch')


get_ipython().system("dvmdostem --force-cmt=14 --log-level='err' --eq-yrs=1000 --sp-yrs=300 --tr-yrs=122 --sc-yrs=0")


get_ipython().system('ls /data/workflows/BONA-birch/output/')


# # BONA Black Spruce

get_ipython().run_line_magic('cd', '/work')


get_ipython().system('rm -r /data/workflows/BONA-black-spruce/')


#set working directory
#!scripts/util/setup_working_directory.py \
#--input-data-path /data/input-catalog/caribou-poker_merged/ \
#/data/workflows/BONA-black-spruce/


#set working directory, downscaled input
get_ipython().system('scripts/util/setup_working_directory.py  --input-data-path /data/input-catalog/cpcrw_towers_downscaled/  /data/workflows/BONA-black-spruce/')


# Adjust the config file
CONFIG_FILE = os.path.join('/data/workflows/BONA-black-spruce/', 'config/config.js')
# Read the existing data into memory
with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)
    
    config['IO']['output_nc_eq'] = 1 # Modify value...

# Write it back..
with open(CONFIG_FILE, 'w') as f:
    json.dump(config, f, indent=2)


#poker flats: 0, 1
#caribou creek: 3, 0
#caribou creek downscaled: 0, 0
# setup runmask
get_ipython().system('/work/scripts/util/runmask.py --reset  --yx 0 0  --show  /data/workflows/BONA-black-spruce/run-mask.nc')


get_ipython().system('pwd')


get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --empty')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on CMTNUM yearly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on GPP monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on RG monthly compartment')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on RH monthly layer')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on RM monthly compartment')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on NPP monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on ALD yearly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on SHLWC yearly monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on DEEPC yearly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on MINEC yearly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on ORGN yearly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on AVLN yearly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on LTRFALC monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on LWCLAYER monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on TLAYER monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on LAYERDEPTH monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on LAYERDZ monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on EET monthly')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on TRANSPIRATION monthly PFT')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on LAI monthly PFT')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on VEGC monthly PFT compartment')
get_ipython().system('scripts/util/outspec.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on BURNVEG2AIRC monthly')


get_ipython().run_line_magic('cd', '/data/workflows/BONA-black-spruce')


#!dvmdostem --force-cmt=15 --log-level='err' --eq-yrs=1000 --sp-yrs=300 --tr-yrs=115 --sc-yrs=10
get_ipython().system("dvmdostem --force-cmt=15 --log-level='err' --eq-yrs=1500 --sp-yrs=300 --tr-yrs=122 --sc-yrs=0")
#!dvmdostem --force-cmt=15 --log-level='err' --eq-yrs=300 --sp-yrs=0 --tr-yrs=0 --sc-yrs=0


get_ipython().system('ls /data/workflows/BONA-black-spruce/output/')


#ALD
ald_bs_eq = xr.open_dataset('/data/workflows/BONA-black-spruce/output/ALD_yearly_eq.nc')
ald_bs_eq = ald_bs_eq.to_dataframe().reset_index()
ald_bs_eq = ald_bs_eq.loc[(ald_bs_eq['y']==0) & (ald_bs_eq['x']==0)]

#SHLWC
shlwc_bs_eq = xr.open_dataset('/data/workflows/BONA-black-spruce/output/SHLWC_monthly_eq.nc')
shlwc_bs_eq = shlwc_bs_eq.to_dataframe().reset_index()
shlwc_bs_eq = shlwc_bs_eq.loc[(shlwc_bs_eq['y']==0) & (shlwc_bs_eq['x']==0)]


ald_bs_eq


#CMT1 with shlwc, nfactor_s from CMT13
sns.lineplot(data=ald_bs_eq, x='time', y='ALD')


#CMT1 with shlwc, nfactor_s from CMT13
sns.lineplot(data=shlwc_bs_eq, x='time', y='SHLWC')


#CMT1
sns.lineplot(data=ald_bs_eq, x='time', y='ALD')


#CMT1
sns.lineplot(data=shlwc_bs_eq, x='time', y='SHLWC')
















