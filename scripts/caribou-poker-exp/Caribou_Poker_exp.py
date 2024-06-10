#!/usr/bin/env python
# coding: utf-8

import netCDF4 as nc
import numpy as np
from matplotlib import pyplot as plt
import os
import json
import pandas as pd
import seaborn as sns


os.environ["PYTHONPATH"] = "/work/scripts"


get_ipython().system('pwd')


get_ipython().system('ls output')


os.environ['HDF5_USE_FILE_LOCKING']='FALSE'


run_name='poker_flats_merged_data'


#define coordiantes of stations
station_lat = 65.12332 #poker flats
station_lon = -147.48722 #poker flats

#station_lat = 65.15401 #caribou creek
#station_lon = -147.50258 #caribou creek


#get netcdf coordinates from runmask
runmask = nc.Dataset('/data/workflows/poker_flats_merged_data/run-mask.nc')
lats=runmask.variables['lat'][:]
lons=runmask.variables['lon'][:]


#get distance between station and each cell
ydist = lats-station_lat
xdist = lons-station_lon
euc_dist = (ydist**2 + xdist**2)**.5


y_x = np.unravel_index(np.argmin(euc_dist),np.shape(lats))
print('y coordinate: {}'.format(y_x[0]))
print('x coordinate: {}'.format(y_x[1]))


get_ipython().run_line_magic('cd', '/work')


get_ipython().system('echo $PYTHONPATH')


#!make clean
#!make


# Cleanup:
get_ipython().system('rm -r /data/workflows/poker_flats_merged_data')


#set working directory
get_ipython().system('/work/scripts/util/setup_working_directory.py  --input-data-path /data/input-catalog/caribou-poker_merged/  /data/workflows/poker_flats_merged_data/')


# Adjust the config file
CONFIG_FILE = os.path.join('/data/workflows/poker_flats_merged_data/', 'config/config.js')
# Read the existing data into memory
with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)
    
    config['IO']['output_nc_eq'] = 1 # Modify value...

# Write it back..
with open(CONFIG_FILE, 'w') as f:
    json.dump(config, f, indent=2)


get_ipython().system('ls ../data/input-catalog/caribou-poker_merged/')


get_ipython().system('ls ../data/workflows/poker_flats_merged_data/')


#poker flats: 0, 1
#caribou creek: 3, 0
# setup runmask
get_ipython().system('/work/scripts/util/runmask.py --reset  --yx 0 1  --show  /data/workflows/poker_flats_merged_data/run-mask.nc')


get_ipython().system('dvmdostem --help')


path_to_drainage_input='/data/input-catalog/caribou-poker_merged/drainage.nc'
drainage = nc.Dataset(path_to_drainage_input, 'r+')

drainage['drainage_class'][0,1]=1

drainage.close()


drainage = nc.Dataset(path_to_drainage_input)
print(drainage)


# poorly drained: 1, or well drained: 0
drainage['drainage_class'][:]


path_to_soil_input='/data/input-catalog/caribou-poker/soil-texture.nc'
soil_dataset = nc.Dataset(path_to_soil_input)
print(soil_dataset)
print('target cell is {}% clay, {}% sand, and {}% silt'.format(soil_dataset['pct_clay'][y_x[0], y_x[1]], 
                                                               soil_dataset['pct_sand'][y_x[0], y_x[1]], 
                                                               soil_dataset['pct_silt'][y_x[0], y_x[1]]))
soil_dataset.close()


soil_dataset = nc.Dataset(path_to_soil_input, 'r+')
soil_dataset['pct_clay'][y_x[0], y_x[1]] = 10 # originally 4.70958137512207
soil_dataset['pct_sand'][y_x[0], y_x[1]] = 27 # originally 55.84833908081055
soil_dataset['pct_silt'][y_x[0], y_x[1]] = 63 # origially 39.44207763671875
print('target cell is {}% clay, {}% sand, and {}% silt'.format(soil_dataset['pct_clay'][y_x[0], y_x[1]], 
                                                               soil_dataset['pct_sand'][y_x[0], y_x[1]], 
                                                               soil_dataset['pct_silt'][y_x[0], y_x[1]]))
drainage.close()


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --empty')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on CMTNUM yearly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on GPP monthly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on SNOWTHICK monthly')


#!scripts/outspec_utils.py ../data/workflows/poker_flats_test/config/output_spec.csv --on TLAYER daily


#!scripts/outspec_utils.py ../data/workflows/poker_flats_test/config/output_spec.csv --on TLAYER daily


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on RG monthly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on RH monthly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on RM monthly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on NPP monthly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on EET monthly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on PET monthly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on RAINFALL monthly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on SWE monthly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on ALD monthly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on TRANSPIRATION monthly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on VWCLAYER monthly layer')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on WATERTAB monthly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on LWCLAYER monthly layer')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on TLAYER monthly layer')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on LAYERDEPTH monthly layer')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on LAYERTYPE monthly layer')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on LAYERDZ monthly layer')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on MOSSDZ monthly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on LAI monthly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on DEEPDZ monthly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on SHLWDZ monthly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on DEEPC yearly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on MINEC yearly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on SHLWC yearly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on LTRFALC yearly')


get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on AVLN yearly')
get_ipython().system('/work/scripts/util/outspec.py ../data/workflows/poker_flats_merged_data/config/output_spec.csv --on ORGN yearly')


#force input data to site obs: --force-cmt {#}  black spruce = 1, deciduous = 3
#!scripts/outspec_utils.py --help
get_ipython().system('/work/scripts/util/outspec.py --list-vars ../data/workflows/poker_flats_merged_data/config/output_spec.csv')
#!scripts/outspec_utils.py --on LAI yearly ../data/workflows/poker_flats_test/config/output_spec.csv
#!scripts/outspec_utils.py --summary ../data/workflows/poker_flats_test/config/output_spec.csv



#also force drainage (poorly drained: 1, or well drained: 0), 


get_ipython().run_line_magic('cd', '/data/workflows/poker_flats_merged_data')


get_ipython().system("dvmdostem --force-cmt=13 --log-level='err' --tr-yrs=121 --sp-yrs=300 --eq-yrs=500")
#!dvmdostem --force-cmt=13 --log-level='err' --tr-yrs=0 --sp-yrs=0 --eq-yrs=1000


get_ipython().system('ls /data/workflows/poker_flats_merged_data/output/')


gpp_ds = nc.Dataset('/data/workflows/poker_flats_merged_data/output/GPP_monthly_eq.nc')
gpp = gpp_ds.variables['GPP'][:, y_x[0], y_x[1]]

rh_ds = nc.Dataset('/data/workflows/poker_flats_merged_data/output/RH_monthly_eq.nc')
rh = rh_ds.variables['RH'][:, y_x[0], y_x[1]]

lwc_ds = nc.Dataset('/data/workflows/poker_flats_merged_data/output/LWCLAYER_monthly_eq.nc')
lwc = lwc_ds.variables['LWCLAYER'][:,3,y_x[0], y_x[1]]*100


year=np.array([np.floor(i/12) for i in range(0, len(gpp))]).astype(np.uint16)
month=[1,2,3,4,5,6,7,8,9,10,11,12]*(len(gpp)//12)
tem_output_df = pd.DataFrame({'year': year, 'month': month, 'GPP': gpp, 'RH': rh, 'LWC':lwc})
yearly_gpp = tem_output_df.groupby('year').sum().reset_index()


len(gpp)//12


# 

sns.scatterplot(data=yearly_gpp, x='year', y='GPP')


sns.scatterplot(data=yearly_gpp, x='year', y='RH')


deepc_ds = nc.Dataset('/data/workflows/poker_flats_merged_data/output/DEEPC_yearly_eq.nc')
deepc = deepc_ds.variables['DEEPC'][:, y_x[0], y_x[1]]
year=np.array([i for i in range(0, len(deepc))]).astype(np.uint16)
deepc_df = pd.DataFrame({'year': year, 'DEEPC': deepc})


shlwc_ds = nc.Dataset('/data/workflows/poker_flats_merged_data/output/SHLWC_yearly_eq.nc')
shlwc = shlwc_ds.variables['SHLWC'][:, y_x[0], y_x[1]]
year=np.array([i for i in range(0, len(deepc))]).astype(np.uint16)
shlwc_df = pd.DataFrame({'year': year, 'SHLWC': shlwc})


sns.scatterplot(data=deepc_df, x='year', y='DEEPC')
sns.scatterplot(data=shlwc_df, x='year', y='SHLWC')


ltrfalc_ds = nc.Dataset('/data/workflows/poker_flats_merged_data/output/LTRFALC_yearly_eq.nc')
ltrfalc = ltrfalc_ds.variables['LTRFALC'][:, y_x[0], y_x[1]]
year=np.array([i for i in range(0, len(ltrfalc))]).astype(np.uint16)
ltrfalc_df = pd.DataFrame({'year': year, 'LTRFALC': ltrfalc})


sns.scatterplot(data=ltrfalc_df, x='year', y='LTRFALC')


avln_ds = nc.Dataset('/data/workflows/poker_flats_merged_data/output/AVLN_yearly_eq.nc')
avln = avln_ds.variables['AVLN'][:, y_x[0], y_x[1]]
year=np.array([i for i in range(0, len(ltrfalc))]).astype(np.uint16)
avln_df = pd.DataFrame({'year': year, 'AVLN': avln})

orgn_ds = nc.Dataset('/data/workflows/poker_flats_merged_data/output/ORGN_yearly_eq.nc')
orgn = orgn_ds.variables['ORGN'][:, y_x[0], y_x[1]]
year=np.array([i for i in range(0, len(ltrfalc))]).astype(np.uint16)
orgn_df = pd.DataFrame({'year': year, 'ORGN': orgn})


sns.scatterplot(data=avln_df, x='year', y='AVLN')


sns.scatterplot(data=orgn_df, x='year', y='ORGN')


sns.scatterplot(data=yearly_gpp, x='year', y='LWC')


minec_ds = nc.Dataset('/data/workflows/poker_flats_merged_data/output/MINEC_yearly_eq.nc')
minec = minec_ds.variables['MINEC'][:, y_x[0], y_x[1]]
year=np.array([i for i in range(0, len(minec))]).astype(np.uint16)
minec_df = pd.DataFrame({'year': year, 'MINEC': minec})


sns.scatterplot(data=minec_df, x='year', y='MINEC')




