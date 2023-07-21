#!/usr/bin/env python
# coding: utf-8

import netCDF4 as nc
import numpy as np
from matplotlib import pyplot as plt
import os
import json
import pandas as pd
import seaborn as sns


get_ipython().system('pwd')


os.environ['HDF5_USE_FILE_LOCKING']='FALSE'


run_name='BONA-black-spruce'


station_lat = 65.15401 #caribou creek
station_lon = -147.50258 #caribou creek


#get netcdf coordinates from runmask
runmask = nc.Dataset('/data/workflows/BONA-black-spruce/run-mask.nc')
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


#set working directory
get_ipython().system('scripts/setup_working_directory.py  --input-data-path /data/input-catalog/caribou-poker/  /data/workflows/BONA-black-spruce/')


# Adjust the config file
CONFIG_FILE = os.path.join('/data/workflows/BONA-black-spruce/', 'config/config.js')
# Read the existing data into memory
with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)
    
    config['IO']['output_nc_eq'] = 0 # Modify value...

# Write it back..
with open(CONFIG_FILE, 'w') as f:
    json.dump(config, f, indent=2)


get_ipython().system('ls ../data/input-catalog/caribou-poker/')


get_ipython().system('ls ../data/workflows/BONA-black-spruce/')


#poker flats: 0, 1
#caribou creek: 3, 0
# setup runmask
get_ipython().system('runmask-util.py --reset  --yx 3 0  --show  /data/workflows/BONA-black-spruce/run-mask.nc')


get_ipython().system('scripts/outspec_utils.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --empty')


get_ipython().system('scripts/outspec_utils.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on CMTNUM yearly')


get_ipython().system('scripts/outspec_utils.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on GPP monthly')


get_ipython().system('scripts/outspec_utils.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on RG monthly')


get_ipython().system('scripts/outspec_utils.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on RH monthly')


get_ipython().system('scripts/outspec_utils.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on RM monthly')


get_ipython().system('scripts/outspec_utils.py ../data/workflows/BONA-black-spruce/config/output_spec.csv --on NPP monthly')


get_ipython().run_line_magic('cd', '/data/workflows/BONA-black-spruce')


get_ipython().system("dvmdostem --force-cmt=13 --log-level='err' --tr-yrs=115 --sp-yrs=300 --eq-yrs=2000 --sc-yrs=85")


get_ipython().system('ls /data/workflows/BONA-black-spruce/output/')


deepc_ds = nc.Dataset('/data/workflows/BONA-black-spruce/output/DEEPC_yearly_eq.nc')
deepc = deepc_ds.variables['DEEPC'][:, y_x[0], y_x[1]]
year=np.array([i for i in range(0, len(deepc))]).astype(np.uint16)
deepc_df = pd.DataFrame({'year': year, 'DEEPC': deepc})


sns.scatterplot(data=deepc_df, x='year', y='DEEPC')

