#!/usr/bin/env python
# coding: utf-8

import netCDF4 as nc
import numpy as np
from matplotlib import pyplot as plt
import os
import json
import pandas as pd
import seaborn as sns
import xarray as xr


cell_y_coord=3
cell_x_coord=0


birch_dir='/data/workflows/BONA-birch/output/'
black_spruce_dir='/data/workflows/BONA-black-spruce/output/'

gpp_tr='GPP_monthly_tr.nc'
gpp_sc='GPP_monthly_sc.nc'

npp_tr='NPP_monthly_tr.nc'
npp_sc='NPP_monthly_sc.nc'

rm_tr='RM_monthly_tr.nc'
rm_sc='RM_monthly_sc.nc'

rg_tr='RG_monthly_tr.nc'
rg_sc='RG_monthly_sc.nc'

rh_tr='RH_monthly_tr.nc'
rh_sc='RH_monthly_sc.nc'


#GPP
gpp_bs_tr = xr.open_dataset(black_spruce_dir+gpp_tr)
tr_dates = gpp_bs_tr.indexes['time'].to_datetimeindex()
gpp_bs_tr = gpp_bs_tr.convert_calendar('standard', use_cftime=True, align_on='date')
gpp_bs_tr = gpp_bs_tr.variables['GPP'][:, cell_y_coord, cell_x_coord]

gpp_bs_sc = xr.open_dataset(black_spruce_dir+gpp_sc)
sc_dates = gpp_bs_sc.indexes['time'].to_datetimeindex()
gpp_bs_sc = gpp_bs_sc.convert_calendar('standard', use_cftime=True, align_on='date')
gpp_bs_sc = gpp_bs_sc.variables['GPP'][:, cell_y_coord, cell_x_coord]

#NPP
npp_bs_tr = xr.open_dataset(black_spruce_dir+npp_tr)
npp_bs_tr = npp_bs_tr.convert_calendar('standard', use_cftime=True, align_on='date')
npp_bs_tr = npp_bs_tr.variables['NPP'][:, cell_y_coord, cell_x_coord]

npp_bs_sc = xr.open_dataset(black_spruce_dir+npp_sc)
npp_bs_sc = npp_bs_sc.convert_calendar('standard', use_cftime=True, align_on='date')
npp_bs_sc = npp_bs_sc.variables['NPP'][:, cell_y_coord, cell_x_coord]

#RM
rm_bs_tr = xr.open_dataset(black_spruce_dir+rm_tr)
rm_bs_tr = rm_bs_tr.convert_calendar('standard', use_cftime=True, align_on='date')
rm_bs_tr = rm_bs_tr.variables['RM'][:, cell_y_coord, cell_x_coord]

rm_bs_sc = xr.open_dataset(black_spruce_dir+rm_sc)
rm_bs_sc = rm_bs_sc.convert_calendar('standard', use_cftime=True, align_on='date')
rm_bs_sc = rm_bs_sc.variables['RM'][:, cell_y_coord, cell_x_coord]

#RG
rg_bs_tr = xr.open_dataset(black_spruce_dir+rg_tr)
rg_bs_tr = rg_bs_tr.convert_calendar('standard', use_cftime=True, align_on='date')
rg_bs_tr = rg_bs_tr.variables['RG'][:, cell_y_coord, cell_x_coord]

rg_bs_sc = xr.open_dataset(black_spruce_dir+rg_sc)
rg_bs_sc = rg_bs_sc.convert_calendar('standard', use_cftime=True, align_on='date')
rg_bs_sc = rg_bs_sc.variables['RG'][:, cell_y_coord, cell_x_coord]

#RH
rh_bs_tr = xr.open_dataset(black_spruce_dir+rh_tr)
rh_bs_tr = rh_bs_tr.convert_calendar('standard', use_cftime=True, align_on='date')
rh_bs_tr = rh_bs_tr.variables['RH'][:, cell_y_coord, cell_x_coord]

rh_bs_sc = xr.open_dataset(black_spruce_dir+rh_sc)
rh_bs_sc = rh_bs_sc.convert_calendar('standard', use_cftime=True, align_on='date')
rh_bs_sc = rh_bs_sc.variables['RH'][:, cell_y_coord, cell_x_coord]


df_bs_tr = pd.DataFrame({'date': tr_dates, 'GPP': gpp_bs_tr, 'NPP': npp_bs_tr, 'RG': rg_bs_tr, 'RH': rh_bs_tr, 'RM': rm_bs_tr})
df_bs_sc = pd.DataFrame({'date': sc_dates, 'GPP': gpp_bs_sc, 'NPP': npp_bs_sc, 'RG': rg_bs_sc, 'RH': rh_bs_sc, 'RM': rm_bs_sc})
df_bs = pd.concat([df_bs_tr,df_bs_sc])
df_bs['RECO'] = df_bs['RG'] + df_bs['RM'] + df_bs['RH']
df_bs['NEE'] = df_bs['RECO'] - df_bs['GPP']
df_bs['year'] = df_bs['date'].dt.year


df_bs


df_bs_yearly = df_bs.groupby(by=['year']).sum()
df_bs_yearly


#GPP
gpp_br_tr = xr.open_dataset(birch_dir+gpp_tr)
gpp_br_tr = gpp_br_tr.convert_calendar('standard', use_cftime=True, align_on='date')
gpp_br_tr = gpp_br_tr.variables['GPP'][:, cell_y_coord, cell_x_coord]

gpp_br_sc = xr.open_dataset(birch_dir+gpp_sc)
gpp_br_sc = gpp_br_sc.convert_calendar('standard', use_cftime=True, align_on='date')
gpp_br_sc = gpp_br_sc.variables['GPP'][:, cell_y_coord, cell_x_coord]

#NPP
npp_br_tr = xr.open_dataset(birch_dir+npp_tr)
npp_br_tr = npp_br_tr.convert_calendar('standard', use_cftime=True, align_on='date')
npp_br_tr = npp_br_tr.variables['NPP'][:, cell_y_coord, cell_x_coord]

npp_br_sc = xr.open_dataset(birch_dir+npp_sc)
npp_br_sc = npp_br_sc.convert_calendar('standard', use_cftime=True, align_on='date')
npp_br_sc = npp_br_sc.variables['NPP'][:, cell_y_coord, cell_x_coord]

#RM
rm_br_tr = xr.open_dataset(birch_dir+rm_tr)
rm_br_tr = rm_br_tr.convert_calendar('standard', use_cftime=True, align_on='date')
rm_br_tr = rm_br_tr.variables['RM'][:, cell_y_coord, cell_x_coord]

rm_br_sc = xr.open_dataset(birch_dir+rm_sc)
rm_br_sc = rm_br_sc.convert_calendar('standard', use_cftime=True, align_on='date')
rm_br_sc = rm_br_sc.variables['RM'][:, cell_y_coord, cell_x_coord]

#RG
rg_br_tr = xr.open_dataset(birch_dir+rg_tr)
rg_br_tr = rg_br_tr.convert_calendar('standard', use_cftime=True, align_on='date')
rg_br_tr = rg_br_tr.variables['RG'][:, cell_y_coord, cell_x_coord]

rg_br_sc = xr.open_dataset(birch_dir+rg_sc)
rg_br_sc = rg_br_sc.convert_calendar('standard', use_cftime=True, align_on='date')
rg_br_sc = rg_br_sc.variables['RG'][:, cell_y_coord, cell_x_coord]

#RH
rh_br_tr = xr.open_dataset(birch_dir+rh_tr)
rh_br_tr = rh_br_tr.convert_calendar('standard', use_cftime=True, align_on='date')
rh_br_tr = rh_br_tr.variables['RH'][:, cell_y_coord, cell_x_coord]

rh_br_sc = xr.open_dataset(birch_dir+rh_sc)
rh_br_sc = rh_br_sc.convert_calendar('standard', use_cftime=True, align_on='date')
rh_br_sc = rh_br_sc.variables['RH'][:, cell_y_coord, cell_x_coord]


df_br_tr = pd.DataFrame({'date': tr_dates, 'GPP': gpp_br_tr, 'NPP': npp_br_tr, 'RG': rg_br_tr, 'RH': rh_br_tr, 'RM': rm_br_tr})
df_br_sc = pd.DataFrame({'date': sc_dates, 'GPP': gpp_br_sc, 'NPP': npp_br_sc, 'RG': rg_br_sc, 'RH': rh_br_sc, 'RM': rm_br_sc})
df_br = pd.concat([df_br_tr,df_br_sc])
df_br['RECO'] = df_br['RG'] + df_br['RM'] + df_br['RH']
df_br['NEE'] = df_br['RECO'] - df_br['GPP']
df_br['year'] = df_br['date'].dt.year


df_br_yearly = df_br.groupby(by=['year']).sum()
df_br_yearly


#sns.set_palette(sns.color_palette("Greys",2))
fig, axes=plt.subplots(3,1,figsize=(8,5))
sns.lineplot(data=df_bs_yearly, x='year', y='GPP', ax=axes[0], label = 'Black Spruce', color='#708891')
sns.lineplot(data=df_br_yearly, x='year', y='GPP', ax=axes[0], label = 'Deciduous', color='#E0DAD0')
sns.lineplot(data=df_bs_yearly, x='year', y='RECO', ax=axes[1], color='#708891')
sns.lineplot(data=df_br_yearly, x='year', y='RECO', ax=axes[1], color='#E0DAD0')
sns.lineplot(data=df_bs_yearly, x='year', y='NEE', ax=axes[2], color='#708891')
sns.lineplot(data=df_br_yearly, x='year', y='NEE', ax=axes[2], color='#E0DAD0')

axes[0].xaxis.set_tick_params(labelbottom=False)
axes[1].xaxis.set_tick_params(labelbottom=False)
axes[0].set_xlabel('')
axes[1].set_xlabel('')
axes[0].set_ylabel('GPP\n(g C $m^{-2}$ $y^{-1}$)')
axes[1].set_ylabel('RECO\n(g C $m^{-2}$ $y^{-1}$)')
axes[2].set_ylabel('NEE\n(g C $m^{-2}$ $y^{-1}$)')
plt.xlabel('Year')
plt.savefig('BONA_carbon_a.jpg', dpi=300)


bins=['2000-2009', '2010-2019', '2020-2029', '2030-2039', '2040-2049', 
      '2050-2059', '2060-2069', '2070-2079', '2080-2089', '2090-2100']
df_bs_recent=df_bs_yearly.loc[df_bs_yearly.index>=2000]
df_br_recent=df_br_yearly.loc[df_br_yearly.index>=2000]

df_bs_recent['bin_index']= ((df_bs_recent.index.astype(int)-2000)/10).astype(int).to_list()
df_br_recent['bin_index']= ((df_br_recent.index.astype(int)-2000)/10).astype(int).to_list()

df_bs_recent.loc[df_bs_recent.index==2100, 'bin_index']=9
df_br_recent.loc[df_bs_recent.index==2100, 'bin_index']=9


df_bs_recent['stand'] = 'Black Spruce'
df_br_recent['stand'] = 'Birch'
df_recent=pd.concat([df_bs_recent, df_br_recent])


fig, ax=plt.subplots(figsize=(8,5))
sns.set_palette(sns.color_palette(['#708891', '#E0DAD0']))
sns.boxplot(data=df_recent, x = 'bin_index', y = 'NEE', hue='stand')
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles=handles[:], labels=labels[:])
ax.set_xticklabels(bins)
plt.xticks(rotation = 45)
ax.set_ylabel('NEE\n(g C $m^{-2}$ $y^{-1}$)')
ax.set_xlabel('')
fig.tight_layout()
plt.savefig('BONA_carbon_b.jpg', dpi=300)
plt.show()


sns.lineplot(data=df_bs_yearly[(df_bs_yearly.index>2010) & (df_bs_yearly.index<2020)], x='year', y='GPP')
sns.lineplot(data=df_br_yearly[(df_br_yearly.index>2010) & (df_br_yearly.index<2020)], x='year', y='GPP')
sns.lineplot(data=df_bs_yearly[(df_bs_yearly.index>2010) & (df_bs_yearly.index<2020)], x='year', y='RH')
sns.lineplot(data=df_br_yearly[(df_br_yearly.index>2010) & (df_br_yearly.index<2020)], x='year', y='RH')




