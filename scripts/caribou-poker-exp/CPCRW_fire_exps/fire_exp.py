#!/usr/bin/env python
# coding: utf-8

import xarray as xr
import rioxarray as rxr
import numpy as np
import pandas as pd
import cftime


get_ipython().system("ls '/data/input-catalog/cpcrw_towers_downscaled/'")


def create_explicit_fire(inpath, outpath, dates, jdays, severities, areas):
    
    fire_vars = ['exp_burn_mask', 'exp_jday_of_burn', 'exp_fire_severity', 'exp_area_of_burn']
    fire_file = xr.open_dataset(inpath)
    
    #reset mask
    fire_file[fire_vars] = fire_file[fire_vars].where(fire_file['exp_burn_mask']==0, 0)

    for i, date in enumerate(dates):

        fire_file[fire_vars[0]] = fire_file['exp_burn_mask'].where(fire_file['time']!=date, 1)
        fire_file[fire_vars[1]] = fire_file[fire_vars[1]].where(fire_file['time']!=date, jdays[i])
        fire_file[fire_vars[2]] = fire_file[fire_vars[2]].where(fire_file['time']!=date, severities[i])
        fire_file[fire_vars[3]] = fire_file[fire_vars[3]].where(fire_file['time']!=date, areas[i])
        
    fire_file.to_netcdf(outpath)
    
    return fire_file


# # 1930 fire

fire_1930 = xr.open_dataset('/data/input-catalog/cpcrw_towers_downscaled/historic-explicit-fire_1930.nc')
#fire = xr.open_dataset('/data/input-catalog/cpcrw_towers_downscaled/fri-fire.nc')
fire_1930.where(fire_1930['exp_burn_mask']==1).dropna(dim='time')


fire_1930


inpath='/data/input-catalog/cpcrw_towers_downscaled/caribou_creek_historic-explicit-fire_1930.nc'
outpath='/data/input-catalog/cpcrw_towers_downscaled/caribou_creek_historic-explicit-fire_193007.nc'
dates=[cftime.DatetimeNoLeap(1930, 7, 15, 0, 0, 0, 0, has_year_zero=True)]
jdays=[196]
severities=[5]
areas=[1e3]

fire_1930 = create_explicit_fire(inpath, outpath, dates, jdays, severities, areas)
fire_1930.where(fire_1930['exp_burn_mask']==1).dropna(dim='time')


# # 1960 fire

fire_1960 = xr.open_dataset('/data/input-catalog/cpcrw_towers_downscaled/historic-explicit-fire_1960.nc')
#fire = xr.open_dataset('/data/input-catalog/cpcrw_towers_downscaled/fri-fire.nc')
fire_1960.where(fire_1960['exp_burn_mask']==1).dropna(dim='time')


fire_1960


inpath='/data/input-catalog/cpcrw_towers_downscaled/caribou_creek_historic-explicit-fire_1960.nc'
outpath='/data/input-catalog/cpcrw_towers_downscaled/caribou_creek_historic-explicit-fire_196007.nc'
dates=[cftime.DatetimeNoLeap(1960, 7, 31, 0, 0, 0, 0, has_year_zero=True)]
jdays=[212]
severities=[5]
areas=[1e3]

fire_1960 = create_explicit_fire(inpath, outpath, dates, jdays, severities, areas)
fire_1960.where(fire_1960['exp_burn_mask']==1).dropna(dim='time')


# # 1990 fire

fire_1990 = xr.open_dataset('/data/input-catalog/cpcrw_towers_downscaled/caribou_creek_historic-explicit-fire_1990.nc')
#fire = xr.open_dataset('/data/input-catalog/cpcrw_towers_downscaled/fri-fire.nc')
fire_1990.where(fire_1990['exp_burn_mask']==1).dropna(dim='time')


inpath='/data/input-catalog/cpcrw_towers_downscaled/caribou_creek_historic-explicit-fire_1990.nc'
outpath='/data/input-catalog/cpcrw_towers_downscaled/caribou_creek_historic-explicit-fire_199007.nc'
dates=[cftime.DatetimeNoLeap(1990, 7, 15, 0, 0, 0, 0, has_year_zero=True)]
jdays=[196]
severities=[3]
areas=[1e3]

fire_1990 = create_explicit_fire(inpath, outpath, dates, jdays, severities, areas)
fire_1990.where(fire_1990['exp_burn_mask']==1).dropna(dim='time')


# # No fire

inpath='/data/input-catalog/cpcrw_towers_downscaled/caribou_creek_historic-explicit-fire_1990.nc'
outpath='/data/input-catalog/cpcrw_towers_downscaled/caribou_creek_historic-explicit-fire_nofire.nc'
dates=[]
jdays=[]
severities=[]
areas=[]

no_fire = create_explicit_fire(inpath, outpath, dates, jdays, severities, areas)
no_fire.where(no_fire['exp_burn_mask']==1).dropna(dim='time')


#for time in fire_1930['time'].values:
#    print(time)


test_fire= '/data/input-catalog/cru-ts40_ar5_rcp85_mri-cgcm3_EML_study_area_10x10/historic-explicit-fire.nc'
test_fire = xr.open_dataset(test_fire)
test_fire.where(test_fire['exp_burn_mask']==0).dropna(dim='time')







