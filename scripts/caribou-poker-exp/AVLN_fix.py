#!/usr/bin/env python
# coding: utf-8

import netCDF4 as nc
import numpy as np
from matplotlib import pyplot as plt
import os
import json
import pandas as pd
import seaborn as sns


y_x = [0,1]


gpp_ds_pre = nc.Dataset('/data/workflows/poker_flats_merged_data_pre_fix/output/GPP_monthly_eq.nc')
gpp_pre = gpp_ds_pre.variables['GPP'][:, y_x[0], y_x[1]]

rh_ds_pre = nc.Dataset('/data/workflows/poker_flats_merged_data_pre_fix/output/RH_monthly_eq.nc')
rh_pre = rh_ds_pre.variables['RH'][:, y_x[0], y_x[1]]

lwc_ds_pre = nc.Dataset('/data/workflows/poker_flats_merged_data_pre_fix/output/LWCLAYER_monthly_eq.nc')
lwc_pre = lwc_ds_pre.variables['LWCLAYER'][:,3,y_x[0], y_x[1]]*100


year=np.array([np.floor(i/12) for i in range(0, len(gpp_pre))]).astype(np.uint16)
month=[1,2,3,4,5,6,7,8,9,10,11,12]*(len(gpp_pre)//12)
tem_output_df = pd.DataFrame({'year': year, 'month': month, 'GPP': gpp_pre, 'RH': rh_pre, 'LWC':lwc_pre})
yearly_gpp_pre = tem_output_df.groupby('year').sum().reset_index()


gpp_ds_post = nc.Dataset('/data/workflows/poker_flats_merged_data/output/GPP_monthly_eq.nc')
gpp_post = gpp_ds_post.variables['GPP'][:, y_x[0], y_x[1]]

rh_ds_post = nc.Dataset('/data/workflows/poker_flats_merged_data/output/RH_monthly_eq.nc')
rh_post = rh_ds_post.variables['RH'][:, y_x[0], y_x[1]]

lwc_ds_post = nc.Dataset('/data/workflows/poker_flats_merged_data/output/LWCLAYER_monthly_eq.nc')
lwc_post = lwc_ds_post.variables['LWCLAYER'][:,3,y_x[0], y_x[1]]*100


year=np.array([np.floor(i/12) for i in range(0, len(gpp_post))]).astype(np.uint16)
month=[1,2,3,4,5,6,7,8,9,10,11,12]*(len(gpp_post)//12)
tem_output_df = pd.DataFrame({'year': year, 'month': month, 'GPP': gpp_post, 'RH': rh_post, 'LWC':lwc_post})
yearly_gpp_post = tem_output_df.groupby('year').sum().reset_index()


sns.scatterplot(data=yearly_gpp_pre, x='year', y='GPP', label = 'pre fix')
sns.scatterplot(data=yearly_gpp_post, x='year', y='GPP', label='post fix')


sns.scatterplot(data=yearly_gpp_pre, x='year', y='RH', label = 'pre fix')
sns.scatterplot(data=yearly_gpp_post, x='year', y='RH', label='post fix')


sns.scatterplot(data=yearly_gpp_pre, x='year', y='LWC', label = 'pre fix')
sns.scatterplot(data=yearly_gpp_post, x='year', y='LWC', label='post fix')


deepc_ds_pre = nc.Dataset('/data/workflows/poker_flats_merged_data_pre_fix/output/DEEPC_yearly_eq.nc')
deepc_pre = deepc_ds_pre.variables['DEEPC'][:, y_x[0], y_x[1]]
year=np.array([i for i in range(0, len(deepc_pre))]).astype(np.uint16)
deepc_df_pre = pd.DataFrame({'year': year, 'DEEPC': deepc_pre})

deepc_ds_post = nc.Dataset('/data/workflows/poker_flats_merged_data/output/DEEPC_yearly_eq.nc')
deepc_post = deepc_ds_post.variables['DEEPC'][:, y_x[0], y_x[1]]
year=np.array([i for i in range(0, len(deepc_post))]).astype(np.uint16)
deepc_df_post = pd.DataFrame({'year': year, 'DEEPC': deepc_post})


shlwc_ds_pre = nc.Dataset('/data/workflows/poker_flats_merged_data_pre_fix/output/SHLWC_yearly_eq.nc')
shlwc_pre = shlwc_ds_pre.variables['SHLWC'][:, y_x[0], y_x[1]]
year=np.array([i for i in range(0, len(shlwc_pre))]).astype(np.uint16)
shlwc_df_pre = pd.DataFrame({'year': year, 'SHLWC': shlwc_pre})

shlwc_ds_post = nc.Dataset('/data/workflows/poker_flats_merged_data/output/SHLWC_yearly_eq.nc')
shlwc_post = shlwc_ds_post.variables['SHLWC'][:, y_x[0], y_x[1]]
year=np.array([i for i in range(0, len(shlwc_post))]).astype(np.uint16)
shlwc_df_post = pd.DataFrame({'year': year, 'SHLWC': shlwc_post})


ltrfalc_ds_pre = nc.Dataset('/data/workflows/poker_flats_merged_data_pre_fix/output/LTRFALC_yearly_eq.nc')
ltrfalc_pre = ltrfalc_ds_pre.variables['LTRFALC'][:, y_x[0], y_x[1]]
year=np.array([i for i in range(0, len(ltrfalc_pre))]).astype(np.uint16)
ltrfalc_df_pre = pd.DataFrame({'year': year, 'LTRFALC': ltrfalc_pre})

ltrfalc_ds_post = nc.Dataset('/data/workflows/poker_flats_merged_data/output/LTRFALC_yearly_eq.nc')
ltrfalc_post = ltrfalc_ds_post.variables['LTRFALC'][:, y_x[0], y_x[1]]
year=np.array([i for i in range(0, len(ltrfalc_post))]).astype(np.uint16)
ltrfalc_df_post = pd.DataFrame({'year': year, 'LTRFALC': ltrfalc_post})


avln_ds_pre = nc.Dataset('/data/workflows/poker_flats_merged_data_pre_fix/output/AVLN_yearly_eq.nc')
avln_pre = avln_ds_pre.variables['AVLN'][:, y_x[0], y_x[1]]
year=np.array([i for i in range(0, len(ltrfalc_pre))]).astype(np.uint16)
avln_df_pre = pd.DataFrame({'year': year, 'AVLN': avln_pre})

avln_ds_post = nc.Dataset('/data/workflows/poker_flats_merged_data/output/AVLN_yearly_eq.nc')
avln_post = avln_ds_post.variables['AVLN'][:, y_x[0], y_x[1]]
year=np.array([i for i in range(0, len(ltrfalc_post))]).astype(np.uint16)
avln_df_post = pd.DataFrame({'year': year, 'AVLN': avln_post})

orgn_ds_pre = nc.Dataset('/data/workflows/poker_flats_merged_data_pre_fix/output/ORGN_yearly_eq.nc')
orgn_pre = orgn_ds_pre.variables['ORGN'][:, y_x[0], y_x[1]]
year=np.array([i for i in range(0, len(ltrfalc_pre))]).astype(np.uint16)
orgn_df_pre = pd.DataFrame({'year': year, 'ORGN': orgn_pre})

orgn_ds_post = nc.Dataset('/data/workflows/poker_flats_merged_data/output/ORGN_yearly_eq.nc')
orgn_post = orgn_ds_post.variables['ORGN'][:, y_x[0], y_x[1]]
year=np.array([i for i in range(0, len(ltrfalc_post))]).astype(np.uint16)
orgn_df_post = pd.DataFrame({'year': year, 'ORGN': orgn_post})


sns.scatterplot(data=shlwc_df_pre, x='year', y='SHLWC', label = 'pre fix')
sns.scatterplot(data=shlwc_df_post, x='year', y='SHLWC', label = 'post fix')


sns.scatterplot(data=deepc_df_pre, x='year', y='DEEPC', label = 'pre fix')
sns.scatterplot(data=deepc_df_post, x='year', y='DEEPC', label = 'post fix')


sns.scatterplot(data=ltrfalc_df_pre, x='year', y='LTRFALC', label = 'pre fix')
sns.scatterplot(data=ltrfalc_df_post, x='year', y='LTRFALC', label = 'post fix')


sns.scatterplot(data=orgn_df_pre, x='year', y='ORGN', label = 'pre fix')
sns.scatterplot(data=orgn_df_post, x='year', y='ORGN', label = 'post fix')


sns.scatterplot(data=avln_df_pre, x='year', y='AVLN', label = 'pre fix')
sns.scatterplot(data=avln_df_post, x='year', y='AVLN', label = 'post fix')


sns.scatterplot(data=avln_df_pre, x='year', y='AVLN', label = 'pre fix')
sns.scatterplot(data=avln_df_post, x='year', y='AVLN', label = 'post fix')
plt.ylim(0,10)




