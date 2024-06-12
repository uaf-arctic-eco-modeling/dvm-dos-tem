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


#path_to_comparison_data = '/data/comparison_data/poker_flats_2010-2016_daily.csv'
#cell_x_coord = 1
#cell_y_coord = 0

path_to_comparison_data = '/data/comparison_data/BONA_ltr_massdata.csv'
cell_x_coord = 0
cell_y_coord = 3


comparison_data=pd.read_csv(path_to_comparison_data)
comparison_data = comparison_data.replace(-9999.0, np.nan)
comparison_data['date'] = pd.to_datetime(comparison_data['date'])


comparison_data_co2 = comparison_data.groupby(by=['year']).mean().reset_index()[['year','CO2_1_1_1', 'CO2_1_2_1']]
comparison_data_co2['co2_mean'] = np.nanmean([comparison_data_co2['CO2_1_1_1'], comparison_data_co2['CO2_1_2_1']], axis=0)
comparison_data_co2


comparison_data['month'] = pd.DatetimeIndex(comparison_data['date']).month
comparison_data_pr = comparison_data.groupby(by=['year', 'month']).sum().reset_index()['P_RAIN']
comparison_data = comparison_data.groupby(by=['year', 'month']).mean().reset_index().drop(columns=['Unnamed: 0', 'DOY', 'X'])
comparison_data_pr[(comparison_data['month']<10)&(comparison_data['year']==2010)]=np.nan
comparison_data['P_RAIN'] = comparison_data_pr
comparison_data['m_y'] = pd.to_datetime(comparison_data['month'].astype(str) + '-'+ comparison_data['year'].astype(str), format='%m-%Y')
comparison_data.dtypes


# !ls /data/input-catalog/caribou-poker/

ds = nc.Dataset('/data/input-catalog/caribou-poker/historic-climate.nc')
ds.variables


tair = ds.variables['tair'][:,cell_y_coord,cell_x_coord]
nirr = ds.variables['nirr'][:,cell_y_coord,cell_x_coord]
vapor_press = ds.variables['vapor_press'][:,cell_y_coord,cell_x_coord]
precip = ds.variables['precip'][:,cell_y_coord,cell_x_coord]

starting_date = pd.to_datetime('1901-1-1 0:0:0')
timedeltas=[0 + i for i in range(0, np.shape(ds.variables['tair'])[0])]
#dates = [starting_date + pd.Timedelta(t, 'd') for t in timedeltas]
dates = [starting_date + pd.Timedelta(t, 'd') for t in ds.variables['time'][:]]
len(dates)


ds = xr.open_dataset('/data/input-catalog/caribou-poker/historic-climate.nc')
dates=ds.indexes['time'].to_datetimeindex()
dates





tem_output_df = pd.DataFrame({'date':dates, 'tair':tair, 'nirr': nirr, 'precip': precip, 'vapor_press': vapor_press})
tem_output_df['month'] = pd.DatetimeIndex(tem_output_df['date']).month
tem_output_df['year'] = pd.DatetimeIndex(tem_output_df['date']).year


#tem_output_df = tem_output_df.groupby(by=['year', 'month']).mean().reset_index()
#tem_output_df['m_y'] = pd.to_datetime(tem_output_df['month'].astype(str) + '-'+ tem_output_df['year'].astype(str), format='%m-%Y')
tem_output_df.dtypes


temp_measurements = ['TA_1_1_1', 'TA_1_2_1', 'TA_1_3_1', 'TA_1_4_1', 'TA_1_5_1', 'TA_1_6_1', 'TA_1_7_1', 'TA_1_8_1', 'TA_1_9_1']


fig, ax = plt.subplots()
dt_comp = pd.to_datetime('2010-01-01')
sns.lineplot(data = tem_output_df[tem_output_df['date']>=dt_comp], x='date', y='tair', label = 'SNAP input')
sns.scatterplot(data = comparison_data[comparison_data['m_y']>=dt_comp], x = 'm_y', y= 'TA_1_1_1', label='station data', color='orange')
plt.ylabel('Air Temperature ($^\circ$C)')
plt.xlabel('Date')
rmse = np.around(calc_rmse(tem_output_df['tair'], comparison_data['TA_1_1_1']), decimals=1)
ax.legend(title='rmse: {} $^\circ$C'.format(rmse), title_fontsize=10)


fig, ax = plt.subplots()
dt_comp = pd.to_datetime('2010-01-01')
sns.lineplot(data = tem_output_df[tem_output_df['date']>=dt_comp], x='date', y='precip', label = 'SNAP input')
sns.scatterplot(data = comparison_data[comparison_data['m_y']>=dt_comp], x = 'm_y', y= 'P_RAIN', label='station data', color='orange')
plt.ylabel('Precipitation (mm)')
plt.xlabel('Date')
rmse=np.around(calc_rmse(tem_output_df['precip'], comparison_data['P_RAIN']), decimals=1)
ax.legend(title='rmse: {} mm'.format(rmse), title_fontsize=10)


fig, ax = plt.subplots()
dt_comp = pd.to_datetime('2010-01-01')
sns.lineplot(data = tem_output_df[tem_output_df['date']>=dt_comp], x='date', y='nirr', label = 'SNAP input')
sns.scatterplot(data = comparison_data[comparison_data['m_y']>=dt_comp], x = 'm_y', y= 'SW_IN', label='station data', color='orange')
plt.ylabel('Incoming Shortwave ($W/m^2$)')
plt.xlabel('Date')
rmse=np.around(calc_rmse(tem_output_df['nirr'], comparison_data['SW_IN']), decimals=1)
ax.legend(title='rmse: {} $W/m^2$'.format(rmse), title_fontsize=10)


fig, ax = plt.subplots()
dt_comp = pd.to_datetime('2010-01-01')
t_kelvin = comparison_data['TA_1_1_1'] + 273.15
sat_vap_press = (611*np.exp((17.27*comparison_data['TA_1_1_1'])/t_kelvin))/100
vap_press = ((comparison_data['RH_1_1_1']/100) * sat_vap_press)
sns.lineplot(data = tem_output_df[tem_output_df['date']>=dt_comp], x='date', y='vapor_press', label = 'SNAP input')
sns.scatterplot(data = comparison_data[comparison_data['m_y']>=dt_comp], x = 'm_y', y= vap_press, label='station data', color='orange')
plt.ylabel('Water Vapor Pressure (hPA)')
plt.xlabel('Date')
rmse=np.around(calc_rmse(tem_output_df['vapor_press'], vap_press), decimals=1)
ax.legend(title='rmse: {} hPA'.format(rmse), title_fontsize=10)


tem_co2 = nc.Dataset('/data/input-catalog/caribou-poker/co2.nc')


tem_co2


tem_co2.variables['year'][:]


tem_co2_df = pd.DataFrame({'year': tem_co2.variables['year'][:], 'co2': tem_co2.variables['co2'][:]})
tem_co2_df


fig, ax = plt.subplots()
sns.lineplot(data = tem_co2_df[tem_co2_df['year']>=2010], x='year', y='co2', label = 'SNAP input')
sns.scatterplot(data = comparison_data_co2[comparison_data_co2['year']>=2010], x = 'year', y= 'co2_mean', label='station data', color='orange')
plt.ylabel('$CO_{2}$ (ppm)')
plt.xlabel('Year')
rmse=np.around(calc_rmse(tem_co2_df['co2'], comparison_data_co2['co2_mean']), decimals=1)
ax.legend(title='rmse: {} ppm'.format(rmse), title_fontsize=10)



