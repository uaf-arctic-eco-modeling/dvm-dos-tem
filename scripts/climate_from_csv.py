#!/usr/bin/env python

# Tobey Carman, Dec 2023
#
# Goal is to convert csv file into netCDF that can be used to drive dvmdostem
#
#
# The csv should look like this:
#
#     vapor_press	tair	nirr	precip	date	lat	lon	Y	X	y	x
#     48.36000324	-28.20003042	14.52500576	24.91308591	1901-01-01	61.3079	-121.2992	0	0	1679770.112	1676087.57
#     58.85211786	-23.49998046	47.51192864	18.99999681	1901-02-01	61.3079	-121.2992	0	0	1679770.112	1676087.57
#     107.8089398	-14.39999188	110.9967167	14.14599608	1901-03-01	61.3079	-121.2992	0	0	1679770.112	1676087.57
#     272.872255	-3.499951151	185.5182044	13.00000194	1901-04-01	61.3079	-121.2992	0	0	1679770.112	1676087.57
#
# In shell:
#  - copy downloaded csv file to /data/workflows/climate-prep
#  - copy arbitrary historic file that we can use to grab attributes, etc
#    
#    $ cp /data/input-catalog/cru-ts40_ar5_rcp85_mri-cgcm3_MurphyDome_10x10/historic-climate.nc /data/workflows/climate-prep/
#
#    Alternatively could use the create_region_input.py to create an empty 
#    template file, but this doesn't appear to have all the attributes...
#
#    >>> import create_region_input
#    >>> create_region_input.create_template_climate_nc_file(
#        "/data/workflows/junk.nc", sizey=1, sizex=1, withlatlon=True
#    )

import netCDF4 as nc
import pandas as pd

ds = nc.Dataset('/data/workflows/climate-prep/historic-climate.nc', 'r')
df = pd.read_csv('/data/workflows/climate-prep/scotty_creek_tem.csv')

ds2 = nc.Dataset('/data/workflows/climate-prep/NEW-historic-climate.nc', 'w')

ds2.createDimension('time', )  
ds2.createDimension('Y', size=1)
ds2.createDimension('X', size=1)

for v in 'lat lon tair precip nirr vapor_press time'.split(' '):
  name = ds.variables[v].name
  datatype = ds.variables[v].datatype
  dims = ds.variables[v].dimensions
  ds2.createVariable(name, datatype, dims) 

for v in 'lat lon tair precip nirr vapor_press'.split(' '):
  # make a dict of attributes for each variable from the other file
  d = { att: ds.variables[v].getncattr(att) for att in ['standard_name', 'units']}
  ds2.variables[v].setncatts(d)

# Copy over all the time series stuff...
for v in 'tair precip nirr vapor_press'.split(' '):
  ds2.variables[v][:,0,0] = df[v][:]

# copy the geospatial
for v in 'lat lon'.split(' '):
  ds2.variables[v][:] = df[v][0] # FIX this

# Setup for time
ds2.variables['time'].setncattr('units', 'days since 1901-1-1 0:0:0')
ds2.variables['time'].setncattr('calendar', '365_day')
ds2.variables['time'].setncattr('long_name', 'time')

# Make the time data
date_objs = [pd.to_datetime(i) for  i in df['date']]
time_data = nc.date2num(date_objs, 
                        ds2.variables['time'].units, 
                        ds2.variables['time'].calendar)

# Assign the time data
ds2.variables['time'][:] = time_data

# Work on attributes
ds2.Conventions = 'CF-1.5'
ds2.source = 'Uhh, homemade, by hand. Fill this out before more serious use.'
ds2.model = 'CRU'
ds2.scenario = '??'
hist_string = """Testing methods to make new datasets from ERA5 climates."""
ds2.history = hist_string
ds2.NCO = '??'

ds2.close()
ds.close()

