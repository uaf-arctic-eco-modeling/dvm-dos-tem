#!/usr/bin/env python
# coding: utf-8

import xarray as xr
import seaborn as sns
import pandas as pd
from matplotlib import pyplot as plt


rh_cumulative_layer_path = '/data/workflows/BONA-black-spruce-fire-1930-RH_cumulative/output/RH_monthly_tr.nc'
rh_layer_cumulative = xr.open_dataset(rh_cumulative_layer_path)
rh_layer_cumulative['time'] = rh_layer_cumulative.indexes['time'].to_datetimeindex()
rh_layer_cumulative = rh_layer_cumulative.to_dataframe().reset_index().drop(columns=['x', 'y'])
rh_layer_cumulative['time'] = pd.to_datetime(rh_layer_cumulative['time'])
rh_layer_cumulative['year'] = rh_layer_cumulative['time'].dt.year
rh_layer_cumulative = rh_layer_cumulative.groupby(by=['year']).sum().reset_index()


deadc_path = '/data/workflows/BONA-black-spruce-fire-1930/output/DEADC_yearly_tr.nc'
deadc = xr.open_dataset(deadc_path)
deadc['time'] = deadc.indexes['time'].to_datetimeindex()
deadc = deadc.to_dataframe().reset_index().drop(columns=['x', 'y'])
deadc['time'] = pd.to_datetime(deadc['time'])
deadc['year'] = deadc['time'].dt.year
deadc = deadc.groupby(by=['year']).sum().reset_index()


dwdc_path = '/data/workflows/BONA-black-spruce-fire-1930/output/DWDC_yearly_tr.nc'
dwdc = xr.open_dataset(dwdc_path)
dwdc['time'] = dwdc.indexes['time'].to_datetimeindex()
dwdc = dwdc.to_dataframe().reset_index().drop(columns=['x', 'y'])
dwdc['time'] = pd.to_datetime(dwdc['time'])
dwdc['year'] = dwdc['time'].dt.year
dwdc = dwdc.groupby(by=['year']).sum().reset_index()


#rh_layer_path = '/data/workflows/BONA-black-spruce-fire-1930/output/RH_monthly_tr.nc'
#rh_layer = xr.open_dataset(rh_layer_path)
#rh_layer['time'] = rh_layer.indexes['time'].to_datetimeindex()
#rh_layer = rh_layer.to_dataframe().reset_index().drop(columns=['x', 'y'])
#rh_layer['time'] = pd.to_datetime(rh_layer['time'])
#rh_layer['year'] = rh_layer['time'].dt.year
#rh_layer_yearly = rh_layer.groupby(by=['year', 'layer']).sum().reset_index()
#rh_layer_yearly_sum = rh_layer.groupby(by=['year']).sum().reset_index()


lwc_layer_path = '/data/workflows/BONA-black-spruce-fire-1930/output/LWCLAYER_yearly_tr.nc'
lwc_layer = xr.open_dataset(lwc_layer_path)
lwc_layer['time'] = lwc_layer.indexes['time'].to_datetimeindex()
lwc_layer = lwc_layer.to_dataframe().reset_index().drop(columns=['x', 'y'])
lwc_layer['time'] = pd.to_datetime(lwc_layer['time'])
lwc_layer['year'] = lwc_layer['time'].dt.year
lwc_layer_yearly = lwc_layer.groupby(by=['year', 'layer']).mean().reset_index()


t_layer_path = '/data/workflows/BONA-black-spruce-fire-1930/output/TLAYER_yearly_tr.nc'
t_layer = xr.open_dataset(t_layer_path)
t_layer['time'] = t_layer.indexes['time'].to_datetimeindex()
t_layer = t_layer.to_dataframe().reset_index().drop(columns=['x', 'y'])
t_layer['time'] = pd.to_datetime(t_layer['time'])
t_layer['year'] = t_layer['time'].dt.year
t_layer_yearly = t_layer.groupby(by=['year', 'layer']).mean().reset_index()


npp


npp_path = '/data/workflows/BONA-black-spruce-fire-1930/output/NPP_monthly_tr.nc'
npp = xr.open_dataset(npp_path)
npp['time'] = npp.indexes['time'].to_datetimeindex()
npp = npp.to_dataframe().reset_index().drop(columns=['x', 'y'])
npp['time'] = pd.to_datetime(npp['time'])
npp['year'] = npp['time'].dt.year
npp_yearly = npp.loc[npp['pft']==4].groupby(by=['year', 'pftpart']).sum().reset_index()
npp_yearly_sum = npp.groupby(by=['year']).sum().reset_index()


inpp_path = '/data/workflows/BONA-birch-fire-1930/output/INNPP_monthly_tr.nc'
inpp = xr.open_dataset(inpp_path)
inpp['time'] = inpp.indexes['time'].to_datetimeindex()
inpp = inpp.to_dataframe().reset_index().drop(columns=['x', 'y'])
inpp['time'] = pd.to_datetime(inpp['time'])
inpp['year'] = inpp['time'].dt.year
inpp_yearly_sum = inpp.groupby(by=['year']).sum().reset_index()


vegc_path = '/data/workflows/BONA-birch-fire-1930/output/VEGC_monthly_tr.nc'
vegc = xr.open_dataset(vegc_path)
vegc['time'] = vegc.indexes['time'].to_datetimeindex()
vegc = vegc.to_dataframe().reset_index().drop(columns=['x', 'y'])
vegc['time'] = pd.to_datetime(vegc['time'])
vegc['year'] = vegc['time'].dt.year
vegc_yearly = vegc.loc[vegc['pft']==4].groupby(by=['year', 'pftpart']).mean().reset_index()
vegc_yearly_sum = vegc.groupby(by=['year', 'pftpart']).sum().reset_index().groupby(by=['year']).mean().reset_index()


#black spruce
fig, axes = plt.subplots(2,1)
sns.lineplot(data=npp_yearly, x='year', y='NPP', hue='pftpart', ax=axes[0])
sns.lineplot(data=vegc_yearly, x='year', y='VEGC', hue='pftpart', ax=axes[1])


#birch
fig, axes = plt.subplots(2,1)
sns.lineplot(data=npp_yearly, x='year', y='NPP', hue='pftpart', ax=axes[0])
sns.lineplot(data=vegc_yearly, x='year', y='VEGC', hue='pftpart', ax=axes[1])


fig, axes = plt.subplots(2,1)
sns.lineplot(data=npp_yearly_sum, x='year', y='NPP', ax=axes[0], label='NPP')
sns.lineplot(data=inpp_yearly_sum, x='year', y='INNPP', ax=axes[0], label='INPP')


fig, axes = plt.subplots(2,1)
sns.lineplot(data=deadc, x='year', y='DEADC', ax=axes[0], label='DEADC')
sns.lineplot(data=dwdc, x='year', y='DWDC', ax=axes[1], label='DWDC')










