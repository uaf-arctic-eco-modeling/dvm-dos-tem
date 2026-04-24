#!/usr/bin/env python
# coding: utf-8

import xarray as xr
import rioxarray as rxr
import numpy as np
import pandas as pd
import cftime


def generate_cftime_list(start_year, end_year):

    cftime_list = []
    for year in range(start_year, end_year + 1):
        dt = cftime.DatetimeNoLeap(year, 1, 1, 0, 0, 0, 0, has_year_zero=True)
        cftime_list.append(dt)
    return cftime_list


start_year = 1901
end_year = 2024

dates = generate_cftime_list(start_year, end_year)


start_year_sc = 2025
end_year_sc = 2100

dates_sc = generate_cftime_list(start_year_sc, end_year_sc)


get_ipython().system("ls '/data/input-catalog/cpcrw_towers_downscaled/'")


# transient


burn_year = 1990
infile = xr.open_dataset(f'/data/input-catalog/cpcrw_towers_downscaled/historic-explicit-fire_{burn_year}.nc')

outfile = infile.copy().assign(
    time=dates,
    exp_burn_mask=(('time', 'Y', 'X'), np.zeros((len(dates),1, 1))),
    exp_jday_of_burn=(('time', 'Y', 'X'), np.zeros((len(dates), 1, 1))),
    exp_fire_severity=(('time', 'Y', 'X'), np.zeros((len(dates), 1, 1))),
    exp_area_of_burn=(('time', 'Y', 'X'), np.zeros((len(dates), 1, 1)))
)

# Method 2: Set multiple variables at once using a dictionary
values_to_set = {
    'exp_burn_mask': 1.0,
    'exp_jday_of_burn': 212,
    'exp_fire_severity': 3,
    'exp_area_of_burn': 1e3
}

target_date = cftime.DatetimeNoLeap(burn_year, 1, 1, 0, 0, 0, 0, has_year_zero=True)
for var_name, value in values_to_set.items():
    outfile[var_name].loc[{'time': target_date}] = value
    outfile[var_name] = outfile[var_name].astype(np.int32)
    
for var_name in outfile.data_vars:
    if var_name in infile.data_vars:
        outfile[var_name].attrs = infile[var_name].attrs
outfile.time.attrs = infile.time.attrs
    
outfile.to_netcdf(f'/data/input-catalog/cpcrw_towers_downscaled/historic-explicit-fire_{burn_year}_time_fixed.nc')


infile = xr.open_dataset(f'/data/input-catalog/cpcrw_towers_downscaled/historic-explicit-nofire.nc')

outfile = infile.copy().assign(
    time=dates,
    exp_burn_mask=(('time', 'Y', 'X'), np.zeros((len(dates),1, 1))),
    exp_jday_of_burn=(('time', 'Y', 'X'), np.zeros((len(dates), 1, 1))),
    exp_fire_severity=(('time', 'Y', 'X'), np.zeros((len(dates), 1, 1))),
    exp_area_of_burn=(('time', 'Y', 'X'), np.zeros((len(dates), 1, 1)))
)

for var_name, value in values_to_set.items():
    outfile[var_name] = outfile[var_name].astype(np.int32)
    
outfile.to_netcdf(f'/data/input-catalog/cpcrw_towers_downscaled/historic-explicit-nofire_time_fixed.nc')


# scenario


burn_year = 2030

infile=xr.open_dataset(f'/data/input-catalog/cpcrw_towers_downscaled/projected_explicit_fire_CC_CCSM4_85.nc')

outfile = infile.copy().assign(
    time=dates_sc,
    exp_burn_mask=(('time', 'Y', 'X'), np.zeros((len(dates_sc),1, 1))),
    exp_jday_of_burn=(('time', 'Y', 'X'), np.zeros((len(dates_sc), 1, 1))),
    exp_fire_severity=(('time', 'Y', 'X'), np.zeros((len(dates_sc), 1, 1))),
    exp_area_of_burn=(('time', 'Y', 'X'), np.zeros((len(dates_sc), 1, 1)))
)
outfile['exp_burn_mask'].attrs
# Method 2: Set multiple variables at once using a dictionary
values_to_set = {
    'exp_burn_mask': 1.0,
    'exp_jday_of_burn': 212,
    'exp_fire_severity': 3,
    'exp_area_of_burn': 1e3
}

target_date = cftime.DatetimeNoLeap(burn_year, 1, 1, 0, 0, 0, 0, has_year_zero=True)
for var_name, value in values_to_set.items():
    outfile[var_name].loc[{'time': target_date}] = value
    outfile[var_name] = outfile[var_name].astype(np.int32)
    
for var_name in outfile.data_vars:
    if var_name in infile.data_vars:
        outfile[var_name].attrs = infile[var_name].attrs
    
outfile.to_netcdf(f'/data/input-catalog/cpcrw_towers_downscaled/projected_explicit_fire_CC_CCSM4_85_time_fixed.nc')


infile = xr.open_dataset(f'/data/input-catalog/cpcrw_towers_downscaled/projected_explicit_fire_CC_CCSM4_85_nofire.nc')

outfile = infile.copy().assign(
    time=dates_sc,
    exp_burn_mask=(('time', 'Y', 'X'), np.zeros((len(dates_sc),1, 1))),
    exp_jday_of_burn=(('time', 'Y', 'X'), np.zeros((len(dates_sc), 1, 1))),
    exp_fire_severity=(('time', 'Y', 'X'), np.zeros((len(dates_sc), 1, 1))),
    exp_area_of_burn=(('time', 'Y', 'X'), np.zeros((len(dates_sc), 1, 1)))
)

for var_name, value in values_to_set.items():
    outfile[var_name] = outfile[var_name].astype(np.int32)
    
for var_name in outfile.data_vars:
    if var_name in infile.data_vars:
        outfile[var_name].attrs = infile[var_name].attrs
        
outfile.to_netcdf(f'/data/input-catalog/cpcrw_towers_downscaled/projected_explicit_fire_CC_CCSM4_85_nofire_time_fixed.nc')




