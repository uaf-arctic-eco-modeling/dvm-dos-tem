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


comparison_data['TA_1_1_1_int'] = comparison_data['TA_1_1_1'].interpolate(method='linear')


temp_gaps = pd.DatetimeIndex(comparison_data[np.isnan(comparison_data['TA_1_1_1'])]['date'])
interpolated = comparison_data[np.isnan(comparison_data['TA_1_1_1'])]['TA_1_1_1_int']
#first_temp_date = comparison_data[~np.isnan(comparison_data['TA_1_1_1'])]['date'].min()
#first_temp_date


fig, axes = plt.subplots(3,1)
sns.scatterplot(data=comparison_data, x='date', y = 'TA_1_1_1', s=1, ax=axes[0])
sns.scatterplot(x=temp_gaps, y = np.zeros(len(temp_gaps)), s=10, ax=axes[0], color='red')

sns.scatterplot(data=comparison_data[comparison_data['year']==2021], x='date', y = 'TA_1_1_1', s=1, ax=axes[1])
sns.scatterplot(x=temp_gaps[temp_gaps.year==2021], y = np.zeros(len(temp_gaps[temp_gaps.year==2021])), s=10, ax=axes[1], color='red')

sns.scatterplot(data=comparison_data[(comparison_data['year']==2021) & (comparison_data['month']==7)], x='date', y = 'TA_1_1_1', s=3, ax=axes[2])
sns.scatterplot(x=temp_gaps[(temp_gaps.year==2021)&(temp_gaps.month==7)], y = np.zeros(len(interpolated[(temp_gaps.year==2021)&(temp_gaps.month==7)])), s=10, ax=axes[2], color='red')
sns.scatterplot(x=temp_gaps[(temp_gaps.year==2021)&(temp_gaps.month==7)], y = interpolated[(temp_gaps.year==2021)&(temp_gaps.month==7)], s=10, ax=axes[2], color='green')
fig.tight_layout()


precip_gaps = comparison_data[np.isnan(comparison_data['P'])]['date']


comparison_data.columns.to_list()


precip_gaps


comparison_data.head()


comparison_data_pr = comparison_data.groupby(by=['year', 'month']).sum().reset_index()['P']
comparison_data = comparison_data.groupby(by=['year', 'month']).mean().reset_index()
comparison_data['ppt (mm)'] = comparison_data_pr
comparison_data['m_y'] = pd.to_datetime(comparison_data['month'].astype(str) + '-'+ comparison_data['year'].astype(str), format='%m-%Y')
comparison_data.dtypes


comparison_data.head(50)


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
sns.lineplot(data = comparison_data[comparison_data['m_y']>=dt_comp], x = 'm_y', y= 'TA_1_1_1_int', label='BONA Tower', color='orange')

plt.ylabel('Air Temperature ($^\circ$C)')
plt.xlabel('Date')
rmse = np.around(calc_rmse(tem_output_df['tair'], comparison_data['TA_1_1_1_int']), decimals=1)
ax.legend(title='rmse: {} $^\circ$C'.format(rmse), title_fontsize=10)





fig, ax = plt.subplots()
dt_comp = pd.to_datetime('2010-01-01')
sns.lineplot(data = tem_output_df[tem_output_df['date']>=dt_comp], x='date', y='precip', label = 'SNAP input')
sns.lineplot(data = comparison_data[comparison_data['m_y']>=dt_comp], x = 'm_y', y= 'ppt (mm)', label='station data', color='orange')
sns.scatterplot(x=precip_gaps, y=np.zeros(len(precip_gaps)), color='red', linewidth=0, s=3)
plt.ylabel('Precipitation (mm)')
plt.xlabel('Date')
#plt.xlim(pd.to_datetime('2020-01-01'), pd.to_datetime('2022-05-01'))
rmse=np.around(calc_rmse(tem_output_df['precip'], comparison_data['ppt (mm)']), decimals=1)
ax.legend(title='rmse: {} mm'.format(rmse), title_fontsize=10)


fig, ax = plt.subplots()
dt_comp = pd.to_datetime('2010-01-01')
sns.lineplot(data = tem_output_df[tem_output_df['date']>=dt_comp], x='date', y='nirr', label = 'SNAP input')
sns.lineplot(data = comparison_data[comparison_data['m_y']>=dt_comp], x = 'm_y', y= 'SW_IN_1_1_2', label='station data', color='orange')
plt.ylabel('Incoming Shortwave ($W/m^2$)')
plt.xlabel('Date')
rmse=np.around(calc_rmse(tem_output_df['nirr'], comparison_data['SW_IN_1_1_2']), decimals=1)
ax.legend(title='rmse: {} $W/m^2$'.format(rmse), title_fontsize=10)


fig, ax = plt.subplots()

dt_comp = pd.to_datetime('2010-01-01')

t_kelvin = comparison_data['TA_1_1_1'] + 273.15 #convert from deg. C to K
sat_vap_press = (611*np.exp((17.27*comparison_data['TA_1_1_1'])/t_kelvin))/100 #calculate saturation vapor pressure (hPA)
vap_press = ((comparison_data['RH']/100) * sat_vap_press) #calculate vapor pressure based on RH and saturation vapor pressure (hPA)
vap_press2 = sat_vap_press - comparison_data['VPD_PI'] #calculate vapor pressure based on vapor pressure defecit and saturation vapor pressure (hPA)

sns.lineplot(data = tem_output_df[tem_output_df['date']>=dt_comp], x='date', y='vapor_press', label = 'SNAP input')
sns.lineplot(data = comparison_data[comparison_data['m_y']>=dt_comp], x = 'm_y', y= vap_press, label='station (RH method)', color='orange')
sns.lineplot(data = comparison_data[comparison_data['m_y']>=dt_comp], x = 'm_y', y= vap_press2, label='station (VPD method)', color='red')

plt.ylabel('Water Vapor Pressure (hPA)')
plt.xlabel('Date')
rmse=np.around(calc_rmse(tem_output_df['vapor_press'], vap_press), decimals=1)
ax.legend(title='rmse: {} hPA'.format(rmse), title_fontsize=10)


#time diff between SNAP end and BONA beginning
SNAP_end = tem_output_df['date'].max()
BONA_begin = comparison_data['m_y'].min()

print(SNAP_end)
print(BONA_begin)


tem_co2 = nc.Dataset('/data/input-catalog/caribou-poker/co2.nc')


tem_co2_df = pd.DataFrame({'year': tem_co2.variables['year'][:], 'co2': tem_co2.variables['co2'][:]})


fig, ax = plt.subplots()
sns.lineplot(data = tem_co2_df[tem_co2_df['year']>=2010], x='year', y='co2', label = 'SNAP input')
sns.lineplot(data = comparison_data[comparison_data['year']>=2010], x = 'year', y= 'CO2_1_1_1', label='station data', color='orange')
plt.ylabel('$CO_{2}$ (ppm)')
plt.xlabel('Year')
rmse=np.around(calc_rmse(tem_co2_df['co2'], comparison_data['CO2_1_1_1']), decimals=1)
ax.legend(title='rmse: {} ppm'.format(rmse), title_fontsize=10)




