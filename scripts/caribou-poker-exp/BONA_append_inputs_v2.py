#!/usr/bin/env python
# coding: utf-8

import xarray as xr
import cftime
import seaborn as sns
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt


ds = xr.open_dataset('/data/input-catalog/cpcrw_towers_downscaled/historic-climate_Pa.nc')

# Create the new time index using the same calendar (noleap/365_day)
new_time = xr.cftime_range(
    start='1901-01-01', 
    end='2022-12-01', 
    freq='MS',  # Month start
    calendar='noleap'  # or '365_day' - they're equivalent
)

# Replace the time coordinate in your dataset
ds_new = ds.assign_coords(time=new_time)

trimmed_time = xr.cftime_range(
    start='1901-01-01', 
    end='2020-12-01', 
    freq='MS',  # Month start
    calendar='noleap'  # or '365_day' - they're equivalent
)
ds_new = ds_new.reindex(time=trimmed_time)


ds_new


obs_data = pd.read_csv('/data/comparison_data/BONA/BONA_EC_monthly_final.csv', parse_dates=['MM_YY'])
obs_data = obs_data.loc[(obs_data['MM_YY']>=pd.to_datetime('2021-01-01')) & (obs_data['MM_YY']<=pd.to_datetime('2024-12-01'))]


obs_ds = ds_new.copy()
extended_time = xr.cftime_range(
    start='2021-01-01', 
    end='2024-12-01', 
    freq='MS',  # Month start
    calendar='noleap'  # or '365_day' - they're equivalent
)
obs_ds = obs_ds.reindex(time=extended_time)
obs_ds['vapor_press'].values[:,0,0] = obs_data['VP'].values
obs_ds['tair'].values[:,0,0] = obs_data['TA_F'].values
obs_ds['nirr'].values[:,0,0] = obs_data['SW_IN_F'].values
obs_ds['precip'].values[:,0,0] = obs_data['P_F'].values


obs_ds


out_ds = xr.concat([ds_new,obs_ds], dim='time')
out_ds['y'] = out_ds['y'].isel(time=0)
out_ds['x'] = out_ds['x'].isel(time=0)
out_ds['lat'] = out_ds['lat'].isel(time=0)
out_ds['lon'] = out_ds['lon'].isel(time=0)


print("y dimensions:", ds['y'].dims)
print("x dimensions:", ds['x'].dims)
print("lat dimensions:", ds['lat'].dims)
print("lon dimensions:", ds['lon'].dims)


ds_data = ds_new.sel(X=0, Y=0)
ds_data_out = out_ds.sel(X=0, Y=0)
fig, axes=plt.subplots(4,1,figsize=(8,5), sharex=True)

sns.lineplot(x=obs_data['MM_YY'], y=obs_data['VP'], ax=axes[0])
sns.lineplot(x=ds_data.indexes['time'].to_datetimeindex(), y=ds_data['vapor_press'], ax=axes[0])
sns.lineplot(x=ds_data_out.indexes['time'].to_datetimeindex(), y=ds_data_out['vapor_press'], ax=axes[0], linestyle=':', color='red')

sns.lineplot(x=obs_data['MM_YY'], y=obs_data['TA_F'], ax=axes[1])
sns.lineplot(x=ds_data.indexes['time'].to_datetimeindex(), y=ds_data['tair'], ax=axes[1])
sns.lineplot(x=ds_data_out.indexes['time'].to_datetimeindex(), y=ds_data_out['tair'], ax=axes[1], linestyle=':', color='red')

sns.lineplot(x=obs_data['MM_YY'], y=obs_data['SW_IN_F'], ax=axes[2])
sns.lineplot(x=ds_data.indexes['time'].to_datetimeindex(), y=ds_data['nirr'], ax=axes[2])
sns.lineplot(x=ds_data_out.indexes['time'].to_datetimeindex(), y=ds_data_out['nirr'], ax=axes[2], linestyle=':', color='red')

sns.lineplot(x=obs_data['MM_YY'], y=obs_data['P_F'], ax=axes[3])
sns.lineplot(x=ds_data.indexes['time'].to_datetimeindex(), y=ds_data['precip'], ax=axes[3])
sns.lineplot(x=ds_data_out.indexes['time'].to_datetimeindex(), y=ds_data_out['precip'], ax=axes[3], linestyle=':', color='red')

axes[3].set_xlim(pd.to_datetime('2018-01-01'), pd.to_datetime('2025-01-01'))


out_ds.to_netcdf('/data/input-catalog/cpcrw_towers_downscaled/historic-climate_time_fixed.nc')


hist_years_cf = xr.cftime_range(
    start='1901-01-01', 
    end='2022-01-01', 
    freq='YS',  # Year start
    calendar='noleap'  # or '365_day' - they're equivalent
)

future_years_cf = xr.cftime_range(
    start='2025-01-01', 
    end='2100-01-01', 
    freq='YS',  # Year start
    calendar='noleap'  # or '365_day' - they're equivalent
)


hist_years_cf


import cftime
hist_co2 = xr.open_dataset("/data/input-catalog/cpcrw_towers_downscaled/co2.nc")
proj_co2 = xr.open_dataset("/data/input-catalog/cpcrw_towers_downscaled/projected_co2_CC_CCSM4_85.nc")

hist_fire = xr.open_dataset("/data/input-catalog/cpcrw_towers_downscaled/historic-explicit-fire.nc")
proj_fire = xr.open_dataset("/data/input-catalog/cpcrw_towers_downscaled/projected_explicit_fire_CC_CCSM4_85.nc")

hist_years = np.arange(1901, 2025, dtype=np.int64)
future_years = np.arange(2025, 2101, dtype=np.int64)

hist_co2 = hist_co2.reindex(year=hist_years)
hist_co2['co2'].loc[dict(year=slice(2023, 2024))] = proj_co2.sel(year=slice(2023, 2024))['co2']
proj_co2 = proj_co2.reindex(year=future_years)

year_start = cftime.DatetimeNoLeap(2023, 1, 1, 0, 0, 0, 0, has_year_zero=True)
year_end = cftime.DatetimeNoLeap(2024, 1, 1, 0, 0, 0, 0, has_year_zero=True)
hist_fire = hist_fire.reindex(year=hist_years_cf)

hist_fire['exp_burn_mask'].loc[dict(time=slice(year_start, year_end))] = hist_fire.sel(time=slice(year_start, year_end))['exp_burn_mask']
hist_fire['exp_jday_of_burn'].loc[dict(time=slice(year_start, year_end))] = hist_fire.sel(time=slice(year_start, year_end))['exp_jday_of_burn']
hist_fire['exp_fire_severity'].loc[dict(time=slice(year_start, year_end))] = hist_fire.sel(time=slice(year_start, year_end))['exp_fire_severity']
hist_fire['exp_area_of_burn'].loc[dict(time=slice(year_start, year_end))] = hist_fire.sel(time=slice(year_start, year_end))['exp_area_of_burn']
proj_fire = proj_fire.reindex(year=future_years_cf)


hist_co2.to_netcdf('/data/input-catalog/cpcrw_towers_downscaled/co2_time_fixed.nc')
proj_co2.to_netcdf('/data/input-catalog/cpcrw_towers_downscaled/projected_co2_CC_CCSM4_85_time_fixed.nc')
hist_fire.to_netcdf('/data/input-catalog/cpcrw_towers_downscaled/historic-explicit-fire_time_fixed.nc')
proj_fire.to_netcdf('/data/input-catalog/cpcrw_towers_downscaled/projected_explicit_fire_CC_CCSM4_85_time_fixed.nc')


future_time = xr.cftime_range(
    start='2025-01-01', 
    end='2100-12-01', 
    freq='MS',  # Month start
    calendar='noleap'  # or '365_day' - they're equivalent
)

hist_time = xr.cftime_range(
    start='1901-01-01', 
    end='2024-12-01', 
    freq='MS',  # Month start
    calendar='noleap'  # or '365_day' - they're equivalent
)


future_ds = xr.open_dataset('/data/input-catalog/cpcrw_towers_downscaled/projected-climate_CC_CCSM4_85_Pa.nc')

future_ds = future_ds.reindex(time=future_time)



future_ds.to_netcdf('/data/input-catalog/cpcrw_towers_downscaled/projected-climate_CC_CCSM4_85_Pa_time_fixed.nc')


future_ds


def calc_vpd(tair_c, vapor_press_pa):
    """
    Calculate Vapor Pressure Deficit (VPD).
    
    Parameters:
    -----------
    tair_c : float
        Air temperature in degrees Celsius
    vapor_press_pa : float
        Actual vapor pressure in Pascals
    
    Returns:
    --------
    float
        Vapor Pressure Deficit in Pascals
    """
    # Calculate saturation vapor pressure using Tetens formula
    # SVP in Pascals
    svp = 610.78 * (10 ** ((7.5 * tair_c) / (tair_c + 237.3)))
    
    # Actual vapor pressure (already in Pascals)
    vp = vapor_press_pa
    
    # Calculate VPD
    vpd = svp - vp
    
    return vpd


hist = out_ds[['vapor_press', 'tair', 'nirr', 'precip']].squeeze().to_pandas().reset_index()
future = future_ds[['vapor_press', 'tair', 'nirr', 'precip']].squeeze().to_pandas().reset_index()

cru_jra = pd.concat([hist, future])
cru_jra['vpd_pa'] = calc_vpd(cru_jra['tair'], cru_jra['vapor_press'])

cru_jra = cru_jra.rename(columns={'vapor_press':'vapor_pressure_pa',
                                  'tair':'air_temperature_celsius',
                                  'nirr':'shortwave_radiation_wm2',
                                  'precip':'precipitation_mm'})
cru_jra['time'] = cru_jra['time'].apply(lambda x: pd.Timestamp(x.year, x.month, x.day) 
                                         if hasattr(x, 'year') else x)
cru_jra['year'] = cru_jra['time'].dt.year
cru_jra['month'] = cru_jra['time'].dt.month

cru_jra[['time','year', 'month','air_temperature_celsius', 'precipitation_mm', 
         'shortwave_radiation_wm2', 'vapor_pressure_pa', 'vpd_pa']].to_csv('cru_jra_cpcrw.csv', index=False)


df = pd.read_csv('ERA5_climate_timeseries_1950_present_cpcrw.csv')
df['vpd_pa'] = calc_vpd(df['air_temperature_celsius'], df['vapor_pressure_pa'])

df[['time','year', 'month','air_temperature_celsius', 'precipitation_mm', 
         'shortwave_radiation_wm2', 'vapor_pressure_pa', 'vpd_pa']].to_csv('ERA5_climate_cpcrw.csv', index=False)




