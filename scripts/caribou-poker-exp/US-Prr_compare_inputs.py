#!/usr/bin/env python
# coding: utf-8

import netCDF4 as nc
import numpy as np
from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
from datetime import datetime as dt
import xarray as xr


def calc_rmse(column_a, column_b):
    return np.power(np.nanmean(((column_a - column_b) ** 2)), .5)


path_to_comparison_data = '/data/comparison_data/US-Prr-monthly.csv'
cell_x_coord = 1
cell_y_coord = 0


comparison_data=pd.read_csv(path_to_comparison_data)
comparison_data = comparison_data.replace(-9999.0, np.nan)
comparison_data['date'] = pd.to_datetime(comparison_data['m_y'])
comparison_data['year'] = comparison_data['date'].dt.year


comparison_data_co2 = comparison_data.groupby(by=['year']).mean().reset_index()[['year','CO2']]
comparison_data_co2


comparison_data['month'] = pd.DatetimeIndex(comparison_data['date']).month
comparison_data_pr = comparison_data.groupby(by=['year', 'month']).sum().reset_index()['Precip (mm)']
comparison_data = comparison_data.groupby(by=['year', 'month']).mean().reset_index().drop(columns=['Unnamed: 0'])
comparison_data_pr[(comparison_data['month']<10)&(comparison_data['year']==2010)]=np.nan
comparison_data['Precip (mm)'] = comparison_data_pr
comparison_data['m_y'] = pd.to_datetime(comparison_data['month'].astype(str) + '-'+ comparison_data['year'].astype(str), format='%m-%Y')
comparison_data.dtypes








# !ls /data/input-catalog/caribou-poker/

ds = nc.Dataset('/data/input-catalog/cpcrw_towers_upscaled/poker_flats_tower_tem.nc')
ds.variables


tair = ds.variables['tair'][:,0,0]
nirr = ds.variables['nirr'][:,0,0]
vapor_press = ds.variables['vapor_press'][:,0,0]
precip = ds.variables['precip'][:,0,0]

starting_date = pd.to_datetime('1901-1-1 0:0:0')
timedeltas=[0 + i for i in range(0, np.shape(ds.variables['tair'])[0])]
#dates = [starting_date + pd.Timedelta(t, 'd') for t in timedeltas]
dates = [starting_date + pd.Timedelta(t, 'd') for t in ds.variables['time'][:]]
len(dates)


tem_output_df = pd.DataFrame({'date':dates, 'tair':tair, 'nirr': nirr, 'precip': precip, 'vapor_press': vapor_press})
tem_output_df['month'] = pd.DatetimeIndex(tem_output_df['date']).month
tem_output_df['year'] = pd.DatetimeIndex(tem_output_df['date']).year


#tem_output_df = tem_output_df.groupby(by=['year', 'month']).mean().reset_index()
#tem_output_df['m_y'] = pd.to_datetime(tem_output_df['month'].astype(str) + '-'+ tem_output_df['year'].astype(str), format='%m-%Y')
tem_output_df.dtypes


comparison_data.columns


fig, ax = plt.subplots()
dt_comp = pd.to_datetime('2010-01-01')
sns.lineplot(data = tem_output_df[tem_output_df['date']>=dt_comp], x='date', y='tair', label = 'downscaled input')
sns.scatterplot(data = comparison_data[comparison_data['m_y']>=dt_comp], x = 'm_y', y= 'TA', label='station data', color='orange')
plt.ylabel('Air Temperature ($^\circ$C)')
plt.xlabel('Date')
rmse = np.around(calc_rmse(tem_output_df['tair'], comparison_data['TA']), decimals=1)
ax.legend(title='rmse: {} $^\circ$C'.format(rmse), title_fontsize=10)


fig, ax = plt.subplots()
dt_comp = pd.to_datetime('2010-01-01')
sns.lineplot(data = tem_output_df[tem_output_df['date']>=dt_comp], x='date', y='precip', label = 'downscaled input')
sns.scatterplot(data = comparison_data[comparison_data['m_y']>=dt_comp], x = 'm_y', y= 'Precip (mm)', label='station data', color='orange')
plt.ylabel('Precipitation (mm)')
plt.xlabel('Date')
rmse=np.around(calc_rmse(tem_output_df['precip'], comparison_data['Precip (mm)']), decimals=1)
ax.legend(title='rmse: {} mm'.format(rmse), title_fontsize=10)


fig, ax = plt.subplots()
dt_comp = pd.to_datetime('2010-01-01')
sns.lineplot(data = tem_output_df[tem_output_df['date']>=dt_comp], x='date', y='nirr', label = 'downscaled input')
sns.scatterplot(data = comparison_data[comparison_data['m_y']>=dt_comp], x = 'm_y', y= 'SW_IN', label='station data', color='orange')
plt.ylabel('Incoming Shortwave ($W/m^2$)')
plt.xlabel('Date')
rmse=np.around(calc_rmse(tem_output_df['nirr'], comparison_data['SW_IN']), decimals=1)
ax.legend(title='rmse: {} $W/m^2$'.format(rmse), title_fontsize=10)


comparison_data['RH']


fig, ax = plt.subplots()
dt_comp = pd.to_datetime('2010-01-01')
t_kelvin = comparison_data['TA'] + 273.15
sat_vap_press = (611*np.exp((17.27*comparison_data['TA'])/t_kelvin))/100
vap_press = ((comparison_data['RH']/100) * sat_vap_press)
sns.lineplot(data = tem_output_df[tem_output_df['date']>=dt_comp], x='date', y='vapor_press', label = 'downscaled input')
sns.scatterplot(data = comparison_data[comparison_data['m_y']>=dt_comp], x = 'm_y', y= vap_press*100, label='station data', color='orange')
plt.ylabel('Water Vapor Pressure (hPA)')
plt.xlabel('Date')
rmse=np.around(calc_rmse(tem_output_df['vapor_press'], vap_press), decimals=1)
ax.legend(title='rmse: {} hPA'.format(rmse), title_fontsize=10)


tem_co2 = nc.Dataset('/data/input-catalog/cpcrw_towers_upscaled/co2_all.nc')


tem_co2


tem_co2.variables['year'][:]


tem_co2_df = pd.DataFrame({'year': tem_co2.variables['year'][:], 'co2': tem_co2.variables['co2'][:]})
tem_co2_df


fig, ax = plt.subplots()
sns.lineplot(data = tem_co2_df[tem_co2_df['year']>=2010], x='year', y='co2', label = 'downscaled input')
sns.scatterplot(data = comparison_data_co2[comparison_data_co2['year']>=2010], x = 'year', y= 'CO2', label='station data', color='orange')
plt.ylabel('$CO_{2}$ (ppm)')
plt.xlabel('Year')
rmse=np.around(calc_rmse(tem_co2_df['co2'], comparison_data_co2['CO2']), decimals=1)
ax.legend(title='rmse: {} ppm'.format(rmse), title_fontsize=10)




