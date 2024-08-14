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


#path_to_comparison_data = '/data/comparison_data/BONA_ltr_massdata.csv'
path_to_comparison_data = '/data/comparison_data/AMF_US-xBN_BASE_HH_6-5_cleaned.csv'
cell_x_coord = 0
cell_y_coord = 3


comparison_data=pd.read_csv(path_to_comparison_data)
comparison_data = comparison_data.replace(-9999.0, np.nan)
comparison_data['date'] = pd.to_datetime(comparison_data['date'])


comparison_data.head()


comparison_data['month'] = pd.DatetimeIndex(comparison_data['date']).month
comparison_data['year'] = pd.DatetimeIndex(comparison_data['date']).year
comparison_data_pr = comparison_data.groupby(by=['year', 'month']).sum().reset_index()['P']
comparison_data = comparison_data.groupby(by=['year', 'month']).mean().reset_index()
comparison_data['ppt (mm)'] = comparison_data_pr
comparison_data['m_y'] = pd.to_datetime(comparison_data['month'].astype(str) + '-'+ comparison_data['year'].astype(str), format='%m-%Y')
comparison_data.dtypes


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


tem_output_df = pd.DataFrame({'date':dates, 'tair':tair, 'nirr': nirr, 'precip': precip, 'vapor_press': vapor_press})
tem_output_df['month'] = pd.DatetimeIndex(tem_output_df['date']).month
tem_output_df['year'] = pd.DatetimeIndex(tem_output_df['date']).year


tem_output_df.dtypes


fig, ax = plt.subplots()
dt_comp = pd.to_datetime('2010-01-01')
sns.lineplot(data = tem_output_df[tem_output_df['date']>=dt_comp], x='date', y='tair', label = 'SNAP input')
sns.lineplot(data = comparison_data[comparison_data['m_y']>=dt_comp], x = 'm_y', y= 'TA_1_1_1', label='BONA Tower', color='orange')
plt.ylabel('Air Temperature ($^\circ$C)')
plt.xlabel('Date')
rmse = np.around(calc_rmse(tem_output_df['tair'], comparison_data['TA_1_1_1']), decimals=1)
ax.legend(title='rmse: {} $^\circ$C'.format(rmse), title_fontsize=10)


#time diff between SNAP end and BONA beginning
SNAP_end = tem_output_df['date'].max()
BONA_begin = comparison_data['m_y'].min()

print(SNAP_end)
print(BONA_begin)


tem_co2 = nc.Dataset('/data/input-catalog/caribou-poker/co2.nc')


tem_co2_df = pd.DataFrame({'year': tem_co2.variables['year'][:], 'co2': tem_co2.variables['co2'][:]})


fig, ax = plt.subplots()
sns.lineplot(data = tem_co2_df[tem_co2_df['year']>=2010], x='year', y='co2', label = 'SNAP input')
sns.scatterplot(data = comparison_data_co2[comparison_data_co2['year']>=2010], x = 'year', y= 'co2_mean', label='station data', color='orange')
plt.ylabel('$CO_{2}$ (ppm)')
plt.xlabel('Year')
rmse=np.around(calc_rmse(tem_co2_df['co2'], comparison_data_co2['co2_mean']), decimals=1)
ax.legend(title='rmse: {} ppm'.format(rmse), title_fontsize=10)

