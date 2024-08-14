#!/usr/bin/env python
# coding: utf-8

import xarray as xr
import seaborn as sns
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np


historic_climate_pa = '/data/input-catalog/cpcrw_towers_downscaled/historic-climate_Pa.nc'
historic_climate_pa = xr.open_dataset(historic_climate_pa).sel(X=0,Y=0)
historic_climate_pa['time'] = historic_climate_pa.indexes['time'].to_datetimeindex()


historic_climate = '/data/input-catalog/cpcrw_towers_downscaled/historic-climate_hPa.nc'
historic_climate = xr.open_dataset(historic_climate).sel(X=0,Y=0)
historic_climate['time'] = historic_climate.indexes['time'].to_datetimeindex()


future_climate = '/data/input-catalog/cpcrw_towers_downscaled/projected-climate_CC_CCSM4_85_hPa.nc'
future_climate = xr.open_dataset(future_climate).sel(X=0, Y=0)
future_climate['time'] = future_climate.indexes['time'].to_datetimeindex()


future_climate['year'] = future_climate['time'].dt.year
historic_climate['year'] = historic_climate['time'].dt.year
historic_climate_yearly=historic_climate.to_pandas().groupby(by='year').agg({'precip':'sum',
                                                                 'tair': 'mean'}).reset_index()
future_climate_yearly=future_climate.to_pandas().groupby(by='year').agg({'precip':'sum',
                                                                 'tair': 'mean'}).reset_index()
climate_yearly= pd.concat([historic_climate_yearly,future_climate_yearly])


fig, axes = plt.subplots(4,1, sharex=True)

sns.lineplot(x=historic_climate['time'], y=historic_climate['nirr'], ax=axes[0])
sns.lineplot(x=future_climate['time'], y=future_climate['nirr'], ax=axes[0])
#axes[0].set_xlim(pd.to_datetime('2022-01-01'), pd.to_datetime('2024-01-01'))

sns.lineplot(x=historic_climate['time'], y=historic_climate['precip'], ax=axes[1])
sns.lineplot(x=future_climate['time'], y=future_climate['precip'], ax=axes[1])
#axes[1].set_xlim(pd.to_datetime('2022-01-01'), pd.to_datetime('2024-01-01'))

sns.lineplot(x=historic_climate['time'], y=historic_climate['tair'], ax=axes[2])
sns.lineplot(x=future_climate['time'], y=future_climate['tair'], ax=axes[2])
#axes[2].set_xlim(pd.to_datetime('2022-01-01'), pd.to_datetime('2024-01-01'))

sns.lineplot(x=historic_climate['time'], y=historic_climate['vapor_press'], ax=axes[3])
sns.lineplot(x=future_climate['time'], y=future_climate['vapor_press'], ax=axes[3])
#axes[3].set_xlim(pd.to_datetime('2022-01-01'), pd.to_datetime('2026-01-01'))

fig.autofmt_xdate()


fig, axes = plt.subplots(2,1, sharex=True)

sns.lineplot(x=climate_yearly['year'], y=climate_yearly['precip'], ax=axes[0])


sns.lineplot(x=climate_yearly['year'], y=climate_yearly['tair'], ax=axes[1])
axes[0].set_ylabel('Precip. (cm)')
axes[1].set_ylabel('T air (C)')


fig.autofmt_xdate()

plt.savefig('driving_vars.jpg', dpi=300)


fig, axes = plt.subplots(2,1, sharex=True)

sns.lineplot(x=historic_climate['time'], y=historic_climate['vapor_press'], ax=axes[0])
sns.lineplot(x=historic_climate_pa['time'], y=historic_climate_pa['vapor_press'], ax=axes[1])

axes[0].set_ylabel('vapor_press (old)')
axes[1].set_ylabel('vapor_press (new)')


dwdc = xr.open_dataset('/data/workflows/BONA-black-spruce-fire-1930/output/DWDC_yearly_tr.nc').sel(x=0,y=0)
dwdc['time'] = dwdc.indexes['time'].to_datetimeindex()

deadc = xr.open_dataset('/data/workflows/BONA-black-spruce-fire-1930/output/DEADC_yearly_tr.nc').sel(x=0,y=0)
deadc['time'] = deadc.indexes['time'].to_datetimeindex()


fig, axes = plt.subplots(2,1, sharex=True)

sns.lineplot(x=deadc['time'], y=deadc['DEADC'], ax=axes[0])
sns.lineplot(x=dwdc['time'], y=dwdc['DWDC'], ax=axes[1])
#axes[0].set_xlim(pd.to_datetime('2022-01-01'), pd.to_datetime('2024-01-01'))


def create_explicit_fire(inpath, outpath, dates, jdays, severities, areas):
    
    fire_vars = ['exp_burn_mask', 'exp_jday_of_burn', 'exp_fire_severity', 'exp_area_of_burn']
    fire_file = xr.open_dataset(inpath)
    
    #reset mask
    fire_file[fire_vars] = fire_file[fire_vars].where(fire_file['exp_burn_mask']==0, 0)
    
    if dates == []:
        fire_file.to_netcdf(outpath)
        return fire_file
    
    for i, date in enumerate(dates):

        fire_file[fire_vars[0]] = fire_file['exp_burn_mask'].where(fire_file['time']!=date, 1)
        fire_file[fire_vars[1]] = fire_file[fire_vars[1]].where(fire_file['time']!=date, jdays[i])
        fire_file[fire_vars[2]] = fire_file[fire_vars[2]].where(fire_file['time']!=date, severities[i])
        fire_file[fire_vars[3]] = fire_file[fire_vars[3]].where(fire_file['time']!=date, areas[i])
        
    fire_file.to_netcdf(outpath)
    
    return fire_file


future_co2 = xr.open_dataset('/data/input-catalog/cpcrw_towers_downscaled/projected_co2_CC_CCSM4_85.nc').to_dataframe()


hist_co2 = xr.open_dataset('/data/input-catalog/cpcrw_towers_downscaled/co2.nc').to_dataframe()


sns.lineplot(data=hist_co2, x=hist_co2.index, y='co2')
sns.lineplot(data=future_co2, x=future_co2.index, y='co2')


ltrfalc = xr.open_dataset('/data/workflows/BONA-black-spruce-fire-1930/output/LTRFALC_monthly_sc.nc').sel(x=0,y=0)
ltrfalc['time'] = ltrfalc.indexes['time'].to_datetimeindex()


root_black_spruce = ltrfalc.where((ltrfalc['pft']==0))
root_black_spruce = root_black_spruce.to_dataframe().reset_index().dropna()


root_black_spruce['LTRFALC'].min()


sns.lineplot(data=root_black_spruce, x='time', y='LTRFALC', hue='pftpart')




