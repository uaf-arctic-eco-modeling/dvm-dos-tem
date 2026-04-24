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


tem_inputs = xr.open_dataset('/data/input-catalog/cpcrw_towers_downscaled/historic-climate_time_fixed.nc')
tem_inputs = tem_inputs.squeeze()
tem_inputs = tem_inputs.convert_calendar('standard', use_cftime=True, align_on='date')

tem_inputs = tem_inputs.to_pandas().reset_index()

tem_inputs['time'] = tem_inputs['time'].astype(str)

# Convert the string column to datetime using pd.to_datetime
tem_inputs['time'] = pd.to_datetime(tem_inputs['time'])
tem_inputs_yearly = tem_inputs.groupby(tem_inputs['time'].dt.year).agg({
    'vapor_press': ['mean', 'std'],
    'tair': ['mean','std'],
    'nirr': ['mean', 'std'],
    'precip':'sum'
})
tem_inputs_yearly.columns = ['_'.join(col).strip() for col in tem_inputs_yearly.columns.values]
tem_inputs_yearly = tem_inputs_yearly.reset_index()
#tem_inputs_yearly['time'] = pd.to_datetime({'year': tem_inputs_yearly['time'], 'month': 1, 'day': 1})


obs_data = pd.read_csv('/data/comparison_data/BONA/BONA_EC_monthly_final.csv', parse_dates=['MM_YY'])
obs_data = obs_data.loc[(obs_data['MM_YY']>=pd.to_datetime('2019-01-01')) & (obs_data['MM_YY']<=pd.to_datetime('2024-12-01'))]

obs_data = obs_data[['MM_YY', 'VP','VPD_F', 'TA_F', 'SW_IN_F', 'P_F','SWC_F_MDS_1','TS_F_MDS_1']]
obs_data=obs_data.rename(columns={'MM_YY':'time','VP':'vapor_press', 'VPD_F': 'vpd', 
                                  'TA_F':'tair','SW_IN_F':'nirr','P_F':'precip',
                                 'SWC_F_MDS_1':'swc','TS_F_MDS_1':'ts'})

obs_data_yearly = obs_data.groupby(obs_data['time'].dt.year).agg({
    'vapor_press': ['mean', 'std'],
    'vpd': ['mean', 'std'],
    'tair': ['mean','std'],
    'nirr': ['mean', 'std'],
    'swc': ['mean', 'std'],
    'ts': ['mean', 'std'],
    'precip':'sum'
})
obs_data_yearly.columns = ['_'.join(col).strip() for col in obs_data_yearly.columns.values]
obs_data_yearly = obs_data_yearly.reset_index()


palette = sns.color_palette(['#4B519B','#2E2427','#3E7274','#416114','#82710D','#114131','#1E7256', '#30B589','#266797'])


cell_y_coord=0
cell_x_coord=0


birch_dir='/data/workflows/BONA-birch/output/'
black_spruce_dir='/data/workflows/BONA-black-spruce/output/'

gpp_tr='GPP_monthly_tr.nc'
gpp_sc='GPP_monthly_sc.nc'

ingpp_tr='INGPP_monthly_tr.nc'

npp_tr='NPP_monthly_tr.nc'
npp_sc='NPP_monthly_sc.nc'

rm_tr='RM_monthly_tr.nc'
rm_sc='RM_monthly_sc.nc'

rg_tr='RG_monthly_tr.nc'
rg_sc='RG_monthly_sc.nc'

rh_tr='RH_monthly_tr.nc'
rh_sc='RH_monthly_sc.nc'

ald_eq='ALD_yearly_eq.nc'
ald_tr='ALD_yearly_tr.nc'
ald_sc='ALD_yearly_sc.nc'

lwclayer_tr = 'LWCLAYER_monthly_tr.nc'
lwclayer_sc = 'LWCLAYER_monthly_sc.nc'

tlayer_tr = 'TLAYER_monthly_tr.nc'
tlayer_sc = 'TLAYER_monthly_sc.nc'

vegc_tr = 'VEGC_monthly_tr.nc'
vegc_sc = 'VEGC_monthly_sc.nc'
vegc_eq = 'VEGC_monthly_eq.nc'

vegn_tr = 'VEGN_monthly_tr.nc'

lai_tr = 'LAI_monthly_tr.nc'

transpiration_tr = 'TRANSPIRATION_monthly_tr.nc'
eet_tr = 'EET_monthly_tr.nc'
pet_tr = 'PET_monthly_tr.nc'

ltrfalc_tr = 'LTRFALC_monthly_tr.nc'
shlwc_tr = 'SHLWC_monthly_tr.nc'
shlwc_eq = 'SHLWC_monthly_eq.nc'
deepc_eq = 'DEEPC_yearly_eq.nc'
minec_eq= 'MINEC_yearly_eq.nc'

burnveg_tr = 'BURNVEG2AIRC_monthly_tr.nc'


#GPP
gpp_bs_tr = xr.open_dataset(black_spruce_dir+gpp_tr)
tr_dates = gpp_bs_tr.indexes['time'].to_datetimeindex()
gpp_bs_tr = gpp_bs_tr.convert_calendar('standard', use_cftime=True, align_on='date')
gpp_bs_tr = gpp_bs_tr['GPP'][:, cell_y_coord, cell_x_coord]

#INGPP
ingpp_bs_tr = xr.open_dataset(black_spruce_dir+ingpp_tr)
tr_dates = ingpp_bs_tr.indexes['time'].to_datetimeindex()
ingpp_bs_tr = ingpp_bs_tr.convert_calendar('standard', use_cftime=True, align_on='date')
ingpp_bs_tr = ingpp_bs_tr.variables['INGPP'][:, cell_y_coord, cell_x_coord]

#Burn
burn_bs_tr = xr.open_dataset(black_spruce_dir+burnveg_tr)
burn_bs_tr = burn_bs_tr.convert_calendar('standard', use_cftime=True, align_on='date')
burn_bs_tr = burn_bs_tr.variables['BURNVEG2AIRC'][:, cell_y_coord, cell_x_coord]

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

#ALD
ald_bs_tr = xr.open_dataset(black_spruce_dir+ald_tr)
ald_bs_tr = ald_bs_tr.convert_calendar('standard', use_cftime=True, align_on='date')
ald_bs_tr = ald_bs_tr.variables['ALD'][:, cell_y_coord, cell_x_coord]

#ald_bs_sc = xr.open_dataset(black_spruce_dir+ald_sc)
#ald_bs_sc = ald_bs_sc.convert_calendar('standard', use_cftime=True, align_on='date')
#ald_bs_sc = ald_bs_sc.variables['ALD'][:, cell_y_coord, cell_x_coord]

#RM
rm_bs_tr = xr.open_dataset(black_spruce_dir+rm_tr)
rm_bs_tr = rm_bs_tr.convert_calendar('standard', use_cftime=True, align_on='date')
rm_bs_tr = rm_bs_tr.variables['RM'][:, :, :5, cell_y_coord, cell_x_coord]

rm_bs_sc = xr.open_dataset(black_spruce_dir+rm_sc)
rm_bs_sc = rm_bs_sc.convert_calendar('standard', use_cftime=True, align_on='date')
rm_bs_sc = rm_bs_sc.variables['RM'][:, :, :5, cell_y_coord, cell_x_coord]

#RG
rg_bs_tr = xr.open_dataset(black_spruce_dir+rg_tr)
rg_bs_tr = rg_bs_tr.convert_calendar('standard', use_cftime=True, align_on='date')
rg_bs_tr = rg_bs_tr.variables['RG'][:, :, :5, cell_y_coord, cell_x_coord]

rg_bs_sc = xr.open_dataset(black_spruce_dir+rg_sc)
rg_bs_sc = rg_bs_sc.convert_calendar('standard', use_cftime=True, align_on='date')
rg_bs_sc = rg_bs_sc.variables['RG'][:, :, :5, cell_y_coord, cell_x_coord]

#RH
rh_bs_tr_layer = xr.open_dataset(black_spruce_dir+rh_tr)
rh_bs_tr_layer = rh_bs_tr_layer.convert_calendar('standard', use_cftime=True, align_on='date')
rh_bs_tr_layer = rh_bs_tr_layer.variables['RH'][:, :, cell_y_coord, cell_x_coord]
rh_bs_tr = rh_bs_tr_layer.sum(axis=1)

rh_bs_sc_layer = xr.open_dataset(black_spruce_dir+rh_sc)
rh_bs_sc_layer = rh_bs_sc_layer.convert_calendar('standard', use_cftime=True, align_on='date')
rh_bs_sc_layer = rh_bs_sc_layer.variables['RH'][:, :, cell_y_coord, cell_x_coord]
rh_bs_sc = rh_bs_sc_layer.sum(axis=1)

#LWCLAYER
lwclayer_bs_tr = xr.open_dataset(black_spruce_dir+lwclayer_tr)
lwclayer_bs_tr = lwclayer_bs_tr.convert_calendar('standard', use_cftime=True, align_on='date')
lwclayer_bs_tr = lwclayer_bs_tr.variables['LWCLAYER'][:,:, cell_y_coord, cell_x_coord]

#lwclayer_bs_sc = xr.open_dataset(black_spruce_dir+lwclayer_sc)
#lwclayer_bs_sc = lwclayer_bs_sc.convert_calendar('standard', use_cftime=True, align_on='date')
#lwclayer_bs_sc = lwclayer_bs_sc.variables['LWCLAYER'][:,:, cell_y_coord, cell_x_coord]

#TLAYER
tlayer_bs_tr = xr.open_dataset(black_spruce_dir+tlayer_tr)
tlayer_bs_tr = tlayer_bs_tr.convert_calendar('standard', use_cftime=True, align_on='date')
tlayer_bs_tr = tlayer_bs_tr.variables['TLAYER'][:,:,cell_y_coord, cell_x_coord]

#tlayer_bs_sc = xr.open_dataset(black_spruce_dir+tlayer_sc)
#tlayer_bs_sc = tlayer_bs_sc.convert_calendar('standard', use_cftime=True, align_on='date')
#tlayer_bs_sc = tlayer_bs_sc.variables['TLAYER'][:,:,cell_y_coord, cell_x_coord]

#VEGC
vegc_bs_eq = xr.open_dataset(black_spruce_dir+vegc_eq)
vegc_bs_eq = vegc_bs_eq.to_dataframe().reset_index()
vegc_bs_eq = vegc_bs_eq.loc[(vegc_bs_eq['y']==cell_y_coord) & (vegc_bs_eq['x']==cell_x_coord) & (vegc_bs_eq['pft']<5)]

vegc_bs_tr = xr.open_dataset(black_spruce_dir+vegc_tr)
vegc_bs_tr = vegc_bs_tr.convert_calendar('standard', use_cftime=False, align_on='date')
vegc_bs_tr = vegc_bs_tr.to_dataframe().reset_index()
vegc_bs_tr = vegc_bs_tr.loc[(vegc_bs_tr['y']==cell_y_coord) & (vegc_bs_tr['x']==cell_x_coord) & (vegc_bs_tr['pft']<5)]

#VEGN
vegn_bs_tr = xr.open_dataset(black_spruce_dir+vegn_tr)
vegn_bs_tr = vegn_bs_tr.convert_calendar('standard', use_cftime=False, align_on='date')
vegn_bs_tr = vegn_bs_tr.to_dataframe().reset_index()
vegn_bs_tr = vegn_bs_tr.loc[(vegn_bs_tr['y']==cell_y_coord) & (vegn_bs_tr['x']==cell_x_coord) & (vegn_bs_tr['pft']<5)]

#LAI
lai_bs_tr = xr.open_dataset(black_spruce_dir+lai_tr)
lai_bs_tr = lai_bs_tr.convert_calendar('standard', use_cftime=True, align_on='date')
lai_bs_tr = lai_bs_tr.variables['LAI'][:, :5, cell_y_coord, cell_x_coord]
lai_bs_tr_sum = lai_bs_tr.sum(axis=1)

#TRANSPIRATION
transpiration_bs_tr = xr.open_dataset(black_spruce_dir+transpiration_tr)
transpiration_bs_tr = transpiration_bs_tr.convert_calendar('standard', use_cftime=False, align_on='date')
transpiration_bs_tr = transpiration_bs_tr.variables['TRANSPIRATION'][:, cell_y_coord, cell_x_coord]

#EET
eet_bs_tr = xr.open_dataset(black_spruce_dir+eet_tr)
eet_bs_tr = eet_bs_tr.convert_calendar('standard', use_cftime=False, align_on='date')
eet_bs_tr = eet_bs_tr.variables['EET'][:, cell_y_coord, cell_x_coord]

#PET
pet_bs_tr = xr.open_dataset(black_spruce_dir+pet_tr)
pet_bs_tr = pet_bs_tr.convert_calendar('standard', use_cftime=False, align_on='date')
pet_bs_tr = pet_bs_tr.variables['PET'][:, cell_y_coord, cell_x_coord]

#LTRFALC
ltrfalc_bs_tr = xr.open_dataset(black_spruce_dir+ltrfalc_tr)
ltrfalc_bs_tr = ltrfalc_bs_tr.convert_calendar('standard', use_cftime=False, align_on='date')
ltrfalc_bs_tr = ltrfalc_bs_tr.to_dataframe().reset_index()
ltrfalc_bs_tr = ltrfalc_bs_tr.loc[(ltrfalc_bs_tr['y']==cell_y_coord) & (ltrfalc_bs_tr['x']==cell_x_coord)]

#SHLWC
shlwc_bs_tr = xr.open_dataset(black_spruce_dir+shlwc_tr)
shlwc_bs_tr = shlwc_bs_tr.convert_calendar('standard', use_cftime=False, align_on='date')
shlwc_bs_tr = shlwc_bs_tr.to_dataframe().reset_index()
shlwc_bs_tr = shlwc_bs_tr.loc[(shlwc_bs_tr['y']==cell_y_coord) & (shlwc_bs_tr['x']==cell_x_coord)]

shlwc_bs_eq = xr.open_dataset(black_spruce_dir+shlwc_eq)
shlwc_bs_eq = shlwc_bs_eq.to_dataframe().reset_index()
shlwc_bs_eq = shlwc_bs_eq.loc[(shlwc_bs_eq['y']==cell_y_coord) & (shlwc_bs_eq['x']==cell_x_coord)]

#DEEPC
deepc_bs_eq = xr.open_dataset(black_spruce_dir+deepc_eq)
deepc_bs_eq = deepc_bs_eq.to_dataframe().reset_index()
deepc_bs_eq = deepc_bs_eq.loc[(deepc_bs_eq['y']==cell_y_coord) & (deepc_bs_eq['x']==cell_x_coord)]

#MINEC
minec_bs_eq = xr.open_dataset(black_spruce_dir+minec_eq)
minec_bs_eq = minec_bs_eq.to_dataframe().reset_index()
minec_bs_eq = minec_bs_eq.loc[(minec_bs_eq['y']==cell_y_coord) & (minec_bs_eq['x']==cell_x_coord)]

#ALD
ald_bs_eq = xr.open_dataset(black_spruce_dir+ald_eq)
ald_bs_eq = ald_bs_eq.to_dataframe().reset_index()
ald_bs_eq = ald_bs_eq.loc[(ald_bs_eq['y']==cell_y_coord) & (ald_bs_eq['x']==cell_x_coord)]








rm_bs_tr_root = rm_bs_tr[:, 2, :].sum(axis=1)
rm_bs_tr = rm_bs_tr.sum(axis=2).sum(axis=1)

rm_bs_sc_root = rm_bs_sc[:, 2, :].sum(axis=1)
rm_bs_sc = rm_bs_sc.sum(axis=2).sum(axis=1)

rg_bs_tr_root = rg_bs_tr[:, 2, :].sum(axis=1)
rg_bs_tr = rg_bs_tr.sum(axis=2).sum(axis=1)

rg_bs_sc_root = rg_bs_sc[:, 2, :].sum(axis=1)
rg_bs_sc = rg_bs_sc.sum(axis=2).sum(axis=1)


rh_bs_tr


df_bs_tr = pd.DataFrame({'date': tr_dates, 'INGPP': ingpp_bs_tr, 'GPP': gpp_bs_tr, 'NPP': npp_bs_tr, 'RG': rg_bs_tr, 'RG_root': rg_bs_tr_root, 'RH': rh_bs_tr, 'RM': rm_bs_tr, 'RM_root': rm_bs_tr_root, 'LWC_top': lwclayer_bs_tr[:,1], 'TLAYER_top': tlayer_bs_tr[:,1], 'EET': eet_bs_tr,'PET': pet_bs_tr, 'TRANSPIRATION': transpiration_bs_tr, 'LAI': lai_bs_tr_sum, 'BURN': burn_bs_tr})
df_bs_sc = pd.DataFrame({'date': sc_dates, 'GPP': gpp_bs_sc, 'NPP': npp_bs_sc, 'RG': rg_bs_sc, 'RH': rh_bs_sc, 'RM': rm_bs_sc})
df_bs = pd.concat([df_bs_tr, df_bs_sc])
df_bs['RECO'] = df_bs['RG'] + df_bs['RM'] + df_bs['RH']
df_bs['NEE'] = df_bs['RECO'] - df_bs['GPP']
df_bs['year'] = df_bs['date'].dt.year
df_bs_yearly = df_bs.groupby(by=['year']).sum()


df_bs_sc


cell_y_coord=0
cell_x_coord=0


#GPP
gpp_br_tr = xr.open_dataset(birch_dir+gpp_tr)
tr_dates = gpp_br_tr.indexes['time'].to_datetimeindex()
gpp_br_tr = gpp_br_tr.convert_calendar('standard', use_cftime=True, align_on='date')
gpp_br_tr = gpp_br_tr.variables['GPP'][:, cell_y_coord, cell_x_coord]

#INGPP
ingpp_br_tr = xr.open_dataset(birch_dir+ingpp_tr)
tr_dates = ingpp_br_tr.indexes['time'].to_datetimeindex()
ingpp_br_tr = ingpp_br_tr.convert_calendar('standard', use_cftime=True, align_on='date')
ingpp_br_tr = ingpp_br_tr.variables['INGPP'][:, cell_y_coord, cell_x_coord]

#Burn
burn_br_tr = xr.open_dataset(birch_dir+burnveg_tr)
burn_br_tr = burn_br_tr.convert_calendar('standard', use_cftime=True, align_on='date')
burn_br_tr = burn_br_tr.variables['BURNVEG2AIRC'][:, cell_y_coord, cell_x_coord]

gpp_br_sc = xr.open_dataset(birch_dir+gpp_sc)
sc_dates = gpp_br_sc.indexes['time'].to_datetimeindex()
gpp_br_sc = gpp_br_sc.convert_calendar('standard', use_cftime=True, align_on='date')
gpp_br_sc = gpp_br_sc.variables['GPP'][:, cell_y_coord, cell_x_coord]

#NPP
npp_br_tr = xr.open_dataset(birch_dir+npp_tr)
npp_br_tr = npp_br_tr.convert_calendar('standard', use_cftime=True, align_on='date')
npp_br_tr = npp_br_tr.variables['NPP'][:, cell_y_coord, cell_x_coord]

npp_br_sc = xr.open_dataset(birch_dir+npp_sc)
npp_br_sc = npp_br_sc.convert_calendar('standard', use_cftime=True, align_on='date')
npp_br_sc = npp_br_sc.variables['NPP'][:, cell_y_coord, cell_x_coord]

#ALD
ald_br_tr = xr.open_dataset(birch_dir+ald_tr)
ald_br_tr = ald_br_tr.convert_calendar('standard', use_cftime=True, align_on='date')
ald_br_tr = ald_br_tr.variables['ALD'][:, cell_y_coord, cell_x_coord]

#ald_br_sc = xr.open_dataset(birch_dir+ald_sc)
#ald_br_sc = ald_br_sc.convert_calendar('standard', use_cftime=True, align_on='date')
#ald_br_sc = ald_br_sc.variables['ALD'][:, cell_y_coord, cell_x_coord]

#RM
rm_br_tr = xr.open_dataset(birch_dir+rm_tr)
rm_br_tr = rm_br_tr.convert_calendar('standard', use_cftime=True, align_on='date')
rm_br_tr = rm_br_tr.variables['RM'][:, :, :, cell_y_coord, cell_x_coord]

rm_br_sc = xr.open_dataset(birch_dir+rm_sc)
rm_br_sc = rm_br_sc.convert_calendar('standard', use_cftime=True, align_on='date')
rm_br_sc = rm_br_sc.variables['RM'][:, :, :, cell_y_coord, cell_x_coord]

#RG
rg_br_tr = xr.open_dataset(birch_dir+rg_tr)
rg_br_tr = rg_br_tr.convert_calendar('standard', use_cftime=True, align_on='date')
rg_br_tr = rg_br_tr.variables['RG'][:, :, :, cell_y_coord, cell_x_coord]

rg_br_sc = xr.open_dataset(birch_dir+rg_sc)
rg_br_sc = rg_br_sc.convert_calendar('standard', use_cftime=True, align_on='date')
rg_br_sc = rg_br_sc.variables['RG'][:, :, :, cell_y_coord, cell_x_coord]

#RH
rh_br_tr_layer = xr.open_dataset(birch_dir+rh_tr)
rh_br_tr_layer = rh_br_tr_layer.convert_calendar('standard', use_cftime=True, align_on='date')
rh_br_tr_layer = rh_br_tr_layer.variables['RH'][:,:,cell_y_coord, cell_x_coord]
rh_br_tr = rh_br_tr_layer.sum(axis=1)

rh_br_sc_layer = xr.open_dataset(birch_dir+rh_sc)
rh_br_sc_layer = rh_br_sc_layer.convert_calendar('standard', use_cftime=True, align_on='date')
rh_br_sc_layer = rh_br_sc_layer.variables['RH'][:,:,cell_y_coord, cell_x_coord]
rh_br_sc = rh_br_sc_layer.sum(axis=1)

#LWCLAYER
lwclayer_br_tr = xr.open_dataset(birch_dir+lwclayer_tr)
lwclayer_br_tr = lwclayer_br_tr.convert_calendar('standard', use_cftime=True, align_on='date')
lwclayer_br_tr = lwclayer_br_tr.variables['LWCLAYER'][:,:,cell_y_coord, cell_x_coord]

#lwclayer_br_sc = xr.open_dataset(birch_dir+lwclayer_sc)
#lwclayer_br_sc = lwclayer_br_sc.convert_calendar('standard', use_cftime=True, align_on='date')
#lwclayer_br_sc = lwclayer_br_sc.variables['LWCLAYER'][:,:,cell_y_coord, cell_x_coord]

#TLAYER
tlayer_br_tr = xr.open_dataset(birch_dir+tlayer_tr)
tlayer_br_tr = tlayer_br_tr.convert_calendar('standard', use_cftime=True, align_on='date')
tlayer_br_tr = tlayer_br_tr.variables['TLAYER'][:,:,cell_y_coord, cell_x_coord]

#tlayer_br_sc = xr.open_dataset(birch_dir+tlayer_sc)
#tlayer_br_sc = tlayer_br_sc.convert_calendar('standard', use_cftime=True, align_on='date')
#tlayer_br_sc = tlayer_br_sc.variables['TLAYER'][:,:,cell_y_coord, cell_x_coord]

#VEGC
vegc_br_eq = xr.open_dataset(birch_dir+vegc_eq)
vegc_br_eq = vegc_br_eq.to_dataframe().reset_index()
vegc_br_eq = vegc_br_eq.loc[(vegc_br_eq['y']==cell_y_coord) & (vegc_br_eq['x']==cell_x_coord) & (vegc_br_eq['pft']<5)]

vegc_br_tr = xr.open_dataset(birch_dir+vegc_tr)
vegc_br_tr = vegc_br_tr.convert_calendar('standard', use_cftime=False, align_on='date')
vegc_br_tr = vegc_br_tr.to_dataframe().reset_index()
vegc_br_tr = vegc_br_tr.loc[(vegc_br_tr['y']==cell_y_coord) & (vegc_br_tr['x']==cell_x_coord) & (vegc_br_tr['pft']<5)]

#VEGN
vegn_br_tr = xr.open_dataset(birch_dir+vegn_tr)
vegn_br_tr = vegn_br_tr.convert_calendar('standard', use_cftime=False, align_on='date')
vegn_br_tr = vegn_br_tr.to_dataframe().reset_index()
vegn_br_tr = vegn_br_tr.loc[(vegn_br_tr['y']==cell_y_coord) & (vegn_br_tr['x']==cell_x_coord) & (vegn_br_tr['pft']<5)]

#LAI
lai_br_tr = xr.open_dataset(birch_dir+lai_tr)
lai_br_tr = lai_br_tr.convert_calendar('standard', use_cftime=True, align_on='date')
lai_br_tr = lai_br_tr.variables['LAI'][:, :5, cell_y_coord, cell_x_coord]
lai_br_tr_sum = lai_br_tr.sum(axis=1)

#TRANSPIRATION
transpiration_br_tr = xr.open_dataset(birch_dir+transpiration_tr)
transpiration_br_tr = transpiration_br_tr.convert_calendar('standard', use_cftime=False, align_on='date')
transpiration_br_tr = transpiration_br_tr.variables['TRANSPIRATION'][:, cell_y_coord, cell_x_coord]

#EET
eet_br_tr = xr.open_dataset(birch_dir+eet_tr)
eet_br_tr = eet_br_tr.convert_calendar('standard', use_cftime=False, align_on='date')
eet_br_tr = eet_br_tr.variables['EET'][:, cell_y_coord, cell_x_coord]

#PET
pet_br_tr = xr.open_dataset(birch_dir+pet_tr)
pet_br_tr = pet_br_tr.convert_calendar('standard', use_cftime=False, align_on='date')
pet_br_tr = pet_br_tr.variables['PET'][:, cell_y_coord, cell_x_coord]

#SHLWC
shlwc_br_tr = xr.open_dataset(birch_dir+shlwc_tr)
shlwc_br_tr = shlwc_br_tr.convert_calendar('standard', use_cftime=True, align_on='date')
shlwc_br_tr = shlwc_br_tr.to_dataframe().reset_index()
shlwc_br_tr = shlwc_br_tr.loc[(shlwc_br_tr['y']==cell_y_coord) & (shlwc_br_tr['x']==cell_x_coord)]

#SHLWC
shlwc_br_eq = xr.open_dataset(birch_dir+shlwc_eq)
shlwc_br_eq = shlwc_br_eq.to_dataframe().reset_index()
shlwc_br_eq = shlwc_br_eq.loc[(shlwc_br_eq['y']==cell_y_coord) & (shlwc_br_eq['x']==cell_x_coord)]

#DEEPC
deepc_br_eq = xr.open_dataset(birch_dir+deepc_eq)
deepc_br_eq = deepc_br_eq.to_dataframe().reset_index()
deepc_br_eq = deepc_br_eq.loc[(deepc_br_eq['y']==cell_y_coord) & (deepc_br_eq['x']==cell_x_coord)]

#MINEC
minec_br_eq = xr.open_dataset(birch_dir+minec_eq)
minec_br_eq = minec_br_eq.to_dataframe().reset_index()
minec_br_eq = minec_br_eq.loc[(minec_br_eq['y']==cell_y_coord) & (minec_br_eq['x']==cell_x_coord)]

#ALD
ald_br_eq = xr.open_dataset(birch_dir+ald_eq)
ald_br_eq = ald_br_eq.to_dataframe().reset_index()
ald_br_eq = ald_br_eq.loc[(ald_br_eq['y']==cell_y_coord) & (ald_br_eq['x']==cell_x_coord)]


rm_br_tr_root = rm_br_tr[:, 2, :].sum(axis=1)
rm_br_tr = rm_br_tr.sum(axis=2).sum(axis=1)

rm_br_sc_root = rm_br_sc[:, 2, :].sum(axis=1)
rm_br_sc = rm_br_sc.sum(axis=2).sum(axis=1)

rg_br_tr_root = rg_br_tr[:, 2, :].sum(axis=1)
rg_br_tr = rg_br_tr.sum(axis=2).sum(axis=1)

rg_br_sc_root = rg_br_sc[:, 2, :].sum(axis=1)
rg_br_sc = rg_br_sc.sum(axis=2).sum(axis=1)


df_br_tr = pd.DataFrame({'date': tr_dates, 'INGPP': ingpp_br_tr, 'GPP': gpp_br_tr, 'NPP': npp_br_tr, 'RG': rg_br_tr, 'RG_root': rg_br_tr_root, 'RH': rh_br_tr, 'RM': rm_br_tr, 'RM_root': rm_br_tr_root, 'LWC_top': lwclayer_br_tr[:,1], 'TLAYER_top': tlayer_br_tr[:,1], 'EET': eet_br_tr,'PET': pet_br_tr, 'TRANSPIRATION': transpiration_br_tr, 'LAI': lai_br_tr_sum, 'BURN': burn_br_tr})
df_br_sc = pd.DataFrame({'date': sc_dates, 'GPP': gpp_br_sc, 'NPP': npp_br_sc, 'RG': rg_br_sc, 'RH': rh_br_sc, 'RM': rm_br_sc})
df_br = pd.concat([df_br_tr, df_br_sc])
df_br['RECO'] = df_br['RG'] + df_br['RM'] + df_br['RH']
df_br['NEE'] = df_br['RECO'] - df_br['GPP']
df_br['year'] = df_br['date'].dt.year
df_br_yearly = df_br.groupby(by=['year']).sum()


df_bs_yearly['CMT'] = 'Black Spruce'
df_br_yearly['CMT'] = 'Deciduous'
#df_bs_yearly['ALD'] = ald_bs_tr
#df_br_yearly['ALD'] = ald_br_tr

df_yearly=pd.concat([df_bs_yearly, df_br_yearly]).reset_index()


vegc_bs_eq


vegc_bs_eq.loc[vegc_bs_eq['pft']==0]


sns.lineplot(data = vegc_bs_eq.loc[vegc_bs_eq['pft']==0], x='time', y='VEGC', hue='pftpart')


#fig, ax=plt.subplots(figsize=(8,5))
#sns.lineplot(results[target_vars].T, legend=False, alpha=0.6)
#sns.lineplot(results[target_vars].iloc[first].T, legend=False, alpha=0.6)
#sns.scatterplot(targets.T, color='red')
#plt.xticks(rotation=83)
#plt.yscale('log')
#plt.ylabel('Value')

#fig.tight_layout()
#plt.savefig('BONA_Black_Spruce_SA_ex.jpg', dpi=300)


# ## Compare vegetation carbon stocks

vegc_bs_eq_tem = vegc_bs_eq.loc[vegc_bs_eq['time']==2100]
vegc_bs_eq_tem['type'] = 'Modeled (TEM)'

vegc_bs_tr_tem = vegc_bs_tr.loc[vegc_bs_tr['time']==pd.to_datetime('2021-08-01')]
vegc_bs_tr_tem['type'] = 'Modeled (TEM)'

vegc_bs_tr_field = vegc_bs_eq_tem.copy()
vegc_bs_tr_field['type'] = 'Field Obs.'
vegc_bs_tr_field['VEGC'] = [287.19, 17.392, 5.525, 192.10, 29.933,
                            1694.1, 21.767, 12.30, 0.0, 0.0,
                            383.38, 3.054, 4.456, 0.0, 0.0]

vegc_bs_tr_rs = vegc_bs_eq_tem.copy()
vegc_bs_tr_rs['type'] = 'Remotely Sensed'
vegc_bs_tr_rs['VEGC'] = [337.38, np.nan, np.nan, np.nan, np.nan,
                            1990.0, np.nan, np.nan, np.nan, np.nan,
                            450.44, np.nan, np.nan, np.nan, np.nan]


vegc_bs_comp=pd.concat([vegc_bs_tr_tem, vegc_bs_tr_field, vegc_bs_tr_rs]).groupby(by=['pft', 'type']).sum().reset_index()


vegc_bs_tr_field


vegc_br_eq_tem = vegc_br_eq.loc[vegc_br_eq['time']==2100]
vegc_br_eq_tem['type'] = 'Modeled (TEM)'

vegc_br_tr_tem = vegc_br_tr.loc[vegc_br_tr['time']==pd.to_datetime('2021-08-01')]
vegc_br_tr_tem['type'] = 'Modeled (TEM)'

vegc_br_tr_field = vegc_br_eq_tem.copy()
vegc_br_tr_field['type'] = 'Field Obs.'
vegc_br_tr_field['VEGC'] = [.106,         10.300,       85.13,      15.831,   2.70,
                            .509,         11.200,       2131.64,     0.0,      12.3,
                            0.043,         2.800,        289.71,     0.0,      2.00]

vegc_br_tr_rs = vegc_br_eq_tem.copy()
vegc_br_tr_rs['type'] = 'Remotely Sensed'
vegc_br_tr_rs['VEGC'] = [np.nan, np.nan, 62.14, np.nan, np.nan,
                            np.nan, np.nan, 2580.17, np.nan, np.nan,
                            np.nan, np.nan, 345.38, np.nan, np.nan]


vegc_br_comp=pd.concat([vegc_br_tr_tem, vegc_br_tr_field, vegc_br_tr_rs]).groupby(by=['pft', 'type']).sum().reset_index()
vegc_br_comp['order'] = [4, 4, 4, 1, 1, 1, 0, 0, 0, 3, 3, 3, 2, 2, 2]
vegc_br_comp = vegc_br_comp.sort_values(by='order')


vegc_bs_comp


#TODO: propagate Error
fig, axes = plt.subplots(2, 1, figsize = (8,5), sharex=True)
sns.barplot(data = vegc_bs_comp, x='VEGC', y='pft', hue='type', orient='h', ax=axes[0], palette=palette)
sns.despine(left=True, bottom=True)

axes[0].set_facecolor('#d9d9d9')
axes[0].set_yticklabels(('Black Spruce', 'Deciduous Shrub', 'Evergreen Shrub', 'Moss', 'Lichen'), fontsize=18)
axes[0].set_ylabel('Black Spruce', fontweight='bold', fontsize=14)
axes[0].set_xlabel('')
axes[0].xaxis.set_ticks_position('none')
axes[0].yaxis.set_label_position('right')
axes[0].get_legend().remove()

#TODO: propagate Error
sns.barplot(data = vegc_br_comp.loc[vegc_br_comp['pft']!=0], x='VEGC', y='order', hue='type', orient='h', ax=axes[1], palette=palette)
sns.despine(left=True, bottom=True)

axes[1].set_yticklabels(('Birch', 'Deciduous Shrub', 'Evergreen Shrub', 'Moss'), fontsize=18)
plt.xticks(fontsize= 18)
axes[1].set_ylabel('Deciduous', fontweight='bold', fontsize=14)
axes[1].yaxis.set_label_position('right')
axes[1].set_xlabel('gC/$m^2$', fontsize=14)
axes[1].legend(title='', fontsize=14)

fig.tight_layout()
plt.savefig('output_figs/BONA/equillibrium_vegC.jpg', dpi=300)



vegc_br_comp


fig, axes = plt.subplots(5,1, figsize=(8,10))
#palette=sns.color_palette(['#336600', '#662200', '#ff9966'])
sns.lineplot(data=vegc_bs_tr.loc[vegc_bs_tr['pft']==0], x='time', y='VEGC', hue='pftpart', ax=axes[0], legend=False, palette=palette)
sns.lineplot(data=vegc_bs_tr.loc[(vegc_bs_tr['pft']==1)], x='time', y='VEGC', hue='pftpart', ax=axes[1], legend=False, palette=palette)
sns.lineplot(data=vegc_bs_tr.loc[vegc_bs_tr['pft']==2], x='time', y='VEGC', hue='pftpart', ax=axes[2], legend=False, palette=palette)
sns.lineplot(data=vegc_bs_tr.loc[vegc_bs_tr['pft']==3], x='time', y='VEGC', hue='pftpart', ax=axes[3], legend=False, palette=palette)
sns.lineplot(data=vegc_bs_tr.loc[vegc_bs_tr['pft']==4], x='time', y='VEGC', hue='pftpart', ax=axes[4], legend=False, palette=palette)
fig.tight_layout()


fig, axes = plt.subplots(5,1, figsize=(8,10))
#palette=sns.color_palette(['#336600', '#662200', '#ff9966'])
sns.lineplot(data=vegc_br_tr.loc[vegc_br_tr['pft']==0], x='time', y='VEGC', hue='pftpart', ax=axes[0], legend=False, palette=palette)
sns.lineplot(data=vegc_br_tr.loc[(vegc_br_tr['pft']==1)], x='time', y='VEGC', hue='pftpart', ax=axes[1], legend=False, palette=palette)
sns.lineplot(data=vegc_br_tr.loc[vegc_br_tr['pft']==2], x='time', y='VEGC', hue='pftpart', ax=axes[2], legend=False, palette=palette)
sns.lineplot(data=vegc_br_tr.loc[vegc_br_tr['pft']==3], x='time', y='VEGC', hue='pftpart', ax=axes[3], legend=False, palette=palette)
sns.lineplot(data=vegc_br_tr.loc[vegc_br_tr['pft']==4], x='time', y='VEGC', hue='pftpart', ax=axes[4], legend=False, palette=palette)
fig.tight_layout()


fig, axes = plt.subplots(2,1, figsize=(8,10))
#palette=sns.color_palette(['#336600', '#662200', '#ff9966'])
sns.lineplot(data=df_bs_tr, x='date', y='BURN', ax=axes[0], legend=False, palette=palette)
sns.lineplot(data=df_br_tr, x='date', y='BURN', ax=axes[1], legend=False, palette=palette)

axes[0].set_ylabel('Burn VegC to Air')
axes[1].set_ylabel('Burn VegC to Air')

fig.tight_layout()


# ## Compare soil carbon stocks

sns.lineplot(data=deepc_bs_eq, x='time', y='DEEPC')


sns.lineplot(data=minec_bs_eq, x='time', y='MINEC')


sns.lineplot(data=ald_bs_eq, x='time', y='ALD')


sns.lineplot(data=ald_br_eq, x='time', y='ALD')


#shlwc_bs_modeled = shlwc_bs_eq.loc[shlwc_bs_eq['time']==999]['SHLWC'].values[0]
#deepc_bs_modeled = deepc_bs_eq.loc[deepc_bs_eq['time']==999]['DEEPC'].values[0]
#shlwc_br_modeled = shlwc_br_eq.loc[shlwc_br_eq['time']==999]['SHLWC'].values[0]
#deepc_br_modeled = deepc_br_eq.loc[deepc_br_eq['time']==999]['DEEPC'].values[0]

shlwc_bs_modeled = shlwc_bs_eq.loc[shlwc_bs_eq['time']==299]['SHLWC'].values[0]
deepc_bs_modeled = deepc_bs_eq.loc[deepc_bs_eq['time']==299]['DEEPC'].values[0]
shlwc_br_modeled = shlwc_br_eq.loc[shlwc_br_eq['time']==299]['SHLWC'].values[0]
deepc_br_modeled = deepc_br_eq.loc[deepc_br_eq['time']==299]['DEEPC'].values[0]

# black spruce MD1
# 782.73    #  shlwc, 0.185
# 3448.46    #  deepc, 0.815

# black spruce obs. 
# 12 (cm) * 0.2 (g/cm3) * 0.426 * 10000 (cm2/m2) = 10224
# shlwc: 10,224 * 0.185 = 1891
# deepc: 10,224 * 0.815 = 8332.56

# deciduous MD1
# 528.17,    #  shlwc, 0.242
# 1653.50    #  deepc, 0.758

# birch obs. 
# 5.5 (cm) * 0.1 (g/cm3) * 0.475 * 10000 (cm2/m2) = 2612.5
# shlwc: 2612.5 * 0.242 = 632.225
# deepc: 2612.5 * 0.758 = 1980.275

shlwc_bs_field = 1891
deepc_bs_field = 8332.56
shlwc_br_field = 632.225
deepc_br_field = 1980.275


#minec_bs_eq.loc[minec_bs_eq['time']==1499]['MINEC'].values[0]


deepc_br_modeled


shlwc_br_modeled


deepc_br_modeled


df_org_c = pd.DataFrame({'stand': ['Black Spruce', 'Black Spruce', 'Deciduous', 'Deciduous',
                                   'Black Spruce', 'Black Spruce', 'Deciduous', 'Deciduous'],
                         'carbon_stock': ['Fibric', 'Humic', 'Fibric', 'Humic',
                                          'Fibric', 'Humic', 'Fibric', 'Humic'], 
                         'value': [shlwc_bs_field, deepc_bs_field, shlwc_br_field, deepc_br_field,
                                   shlwc_bs_modeled, deepc_bs_modeled, shlwc_br_modeled, deepc_br_modeled], 
                         'type': ['Field Obs.', 'Field Obs.', 'Field Obs.', 'Field Obs.',
                                  'Modeled (TEM)', 'Modeled (TEM)', 'Modeled (TEM)', 'Modeled (TEM)']})


fig, axes = plt.subplots(2, 1, figsize = (8,4), sharex=True)

sns.barplot(data = df_org_c.loc[df_org_c['stand']=='Black Spruce'], x='value', y='carbon_stock', hue='type', orient='h', palette='colorblind', ax=axes[0])
sns.barplot(data = df_org_c.loc[df_org_c['stand']=='Deciduous'], x='value', y='carbon_stock', hue='type', orient='h', palette='colorblind', ax=axes[1])

axes[0].set_facecolor('#d9d9d9')
axes[0].set_yticklabels(('Fibric', 'Humic'), fontsize=18)
axes[0].set_xlabel('')
axes[0].xaxis.set_ticks_position('none')
axes[0].set_ylabel('Black Spruce', fontweight='bold', fontsize=14)
axes[0].yaxis.set_label_position('right')
axes[0].get_legend().remove()

axes[1].set_yticklabels(('Fibric', 'Humic'), fontsize=18)
axes[1].set_ylabel('Deciduous', fontweight='bold', fontsize=14)
axes[1].yaxis.set_label_position('right')
plt.xticks(fontsize= 18)
axes[1].set_xlabel('gC/$m^2$', fontsize=14)
plt.legend(title='', fontsize=14)
sns.despine(left=True, bottom=True)
fig.tight_layout()
plt.savefig('output_figs/BONA/equillibrium_soilC.jpg', dpi=300)


# # Combined soil

#TODO: propagate Error
fig, axes = plt.subplots(2, 2, figsize = (16,5))
sns.barplot(data = vegc_bs_comp, x='VEGC', y='pft', hue='type', orient='h', ax=axes[0,0], palette=palette)
sns.despine(left=True, bottom=True)

axes[0,0].set_facecolor('#d9d9d9')
axes[0,0].set_yticklabels(('Black Spruce', 'Deciduous Shrub', 'Evergreen Shrub', 'Moss', 'Lichen'), fontsize=18)
axes[0,0].set_ylabel('')
axes[0,0].set_xlabel('')
axes[0,0].xaxis.set_ticks_position('none')
axes[0,0].set_ylabel('Black Spruce\nStands', fontweight='bold', fontsize=14)
axes[0,0].yaxis.set_label_position('right')
axes[0,0].get_legend().remove()
axes[0,0].set_title('Vegetation Carbon Stocks', fontsize=20)
axes[0,0].text(-.35, 1.15, '(a)', horizontalalignment='left', verticalalignment='top', transform=axes[0,0].transAxes, fontsize=18, fontweight='bold')

#TODO: propagate Error
sns.barplot(data = vegc_br_comp.loc[vegc_br_comp['pft']!=0], x='VEGC', y='order', hue='type', orient='h', ax=axes[1,0], palette=palette)
sns.despine(left=True, bottom=True)

axes[1,0].set_yticklabels(('Birch', 'Deciduous Shrub', 'Evergreen Shrub', 'Moss'), fontsize=18)
axes[1,0].tick_params(axis='x', labelsize=18)
axes[1,0].set_ylabel('Deciduous Stands', fontweight='bold', fontsize=14)
axes[1,0].yaxis.set_label_position('right')
axes[1,0].set_xlabel('gC $m^{-2}$', fontsize=14)
axes[1,0].legend(title='', fontsize=14)
axes[1,0].sharex(axes[0,0])



sns.barplot(data = df_org_c.loc[df_org_c['stand']=='Black Spruce'], x='value', y='carbon_stock', hue='type', orient='h', palette=palette, ax=axes[0,1])
sns.barplot(data = df_org_c.loc[df_org_c['stand']=='Deciduous'], x='value', y='carbon_stock', hue='type', orient='h', palette=palette, ax=axes[1,1])

axes[0,1].set_title('Soil Carbon Stocks', fontsize=20)
axes[0,1].set_facecolor('#d9d9d9')
axes[0,1].set_yticklabels(('Fibric', 'Humic'), fontsize=18)
axes[0,1].set_xlabel('')
axes[0,1].xaxis.set_ticks_position('none')
axes[0,1].set_ylabel('Black Spruce\nStands', fontweight='bold', fontsize=14)
axes[0,1].yaxis.set_label_position('right')
axes[0,1].get_legend().remove()
axes[0,1].text(-.05, 1.15, '(b)', horizontalalignment='left', verticalalignment='top', transform=axes[0,1].transAxes, fontsize=18, fontweight='bold')

axes[1,1].set_yticklabels(('Fibric', 'Humic'), fontsize=18)
axes[1,1].set_ylabel('Deciduous Stands', fontweight='bold', fontsize=14)
axes[1,1].yaxis.set_label_position('right')
axes[1,1].tick_params(axis='x', labelsize=18)
axes[1,1].set_xlabel('gC $m^{-2}$', fontsize=14)
axes[1,1].get_legend().remove()
sns.despine(left=True, bottom=True)
axes[1,1].sharex(axes[0,1])

fig.tight_layout()
plt.savefig('output_figs/BONA/C_stocks_combined.jpg', dpi=300)


# # Fluxes

BONA_EC_monthly = pd.read_csv('/data/comparison_data/BONA_monthly_fluxes.csv', parse_dates=['MM_YY'])
BONA_EC_monthly_v2 = pd.read_csv('/data/comparison_data/BONA/AMF_US-xBN_FLUXNET_SUBSET_MM_2019-2024_4-7.csv')
BONA_EC_monthly_v2['MM_YY'] = pd.to_datetime(BONA_EC_monthly_v2['TIMESTAMP'], format='%Y%m')
BONA_EC_monthly_v2['daysinmonth'] = BONA_EC_monthly_v2['MM_YY'].dt.daysinmonth


BONA_EC_monthly_v3= pd.read_csv('/data/comparison_data/BONA/BONA_EC_monthly_final.csv', parse_dates=['MM_YY'])


BONA_EC_RF= pd.read_csv('/data/comparison_data/BONA/BONA_monthly_RF.csv', parse_dates=['MM_YY'])


BONA_EC_ABC = pd.read_csv('/data/comparison_data/BONA/ABCFlux_V2_CPRCWsub.csv')
BONA_EC_ABC = BONA_EC_ABC.replace(-9999, np.nan)


BONA_EC_ABC['MM_YY'] = pd.to_datetime({'year': BONA_EC_ABC['year'], 
                                      'month': BONA_EC_ABC['month'], 
                                      'day': 1})


SIF_BS = pd.read_csv('/data/comparison_data/SIF/BlackSpruce_YII.csv', parse_dates=['Date'])
SIF_BR = pd.read_csv('/data/comparison_data/SIF/Deciduous_SIF.csv', parse_dates=['Date'])

SIF_BS_daily = SIF_BS[['Date','Y.II.']].groupby(by='Date').mean().reset_index()
SIF_BR_daily = SIF_BR[['Date','SIF760_Wide']].groupby(by='Date').mean().reset_index()


decid_color = '#6CB36B'
ever_color = '#1F6B39'


tem_inputs


fig, axes=plt.subplots(4,1,figsize=(8,4), sharex=True)

#Black Spruce modeled
sns.lineplot(data=df_bs.loc[(df_bs['date']>'2010-01-01') & (df_bs['date']<'2025-01-01')], 
             x='date', y='GPP', label = 'TEM Black Spruce', ax=axes[0], alpha=0.8, color=palette[5], linewidth=0.8)
sns.lineplot(data=df_bs.loc[(df_bs['date']>'2010-01-01') & (df_bs['date']<'2025-01-01')], 
             x='date', y='RECO', label = 'Black Spruce', ax=axes[1], legend=False, alpha=0.8, color=palette[5], linewidth=0.8)
sns.lineplot(data=df_bs.loc[(df_bs['date']>'2010-01-01') & (df_bs['date']<'2025-01-01')], 
             x='date', y='NEE', ax=axes[2], legend=False, alpha=0.8, color=palette[5], linewidth=0.8)

#Birch modeled
sns.lineplot(data=df_br.loc[(df_br['date']>'2010-01-01') & (df_br['date']<'2025-01-01')], 
             x='date', y='GPP', label = 'TEM Deciduous', ax=axes[0], alpha=0.8, color=palette[7], linewidth=0.8)
sns.lineplot(data=df_br.loc[(df_br['date']>'2010-01-01') & (df_br['date']<'2025-01-01')], 
             x='date', y='RECO', label = 'Deciduous', ax=axes[1], legend=False, alpha=0.8, color=palette[7], linewidth=0.8)
sns.lineplot(data=df_br.loc[(df_br['date']>'2010-01-01') & (df_br['date']<'2025-01-01')], 
             x='date', y='NEE', ax=axes[2], legend=False, alpha=0.8, color=palette[7], linewidth=0.8)

#GPP observed
sns.scatterplot(data=BONA_EC_monthly_v3, x='MM_YY', 
                y=BONA_EC_monthly_v3['GPP_NT_VUT_50'], 
                ax=axes[0], label='Obs. - OneFlux', 
                s=8, facecolors='none', edgecolors=palette[1],linewidths=0.8, alpha=0.6)

#sns.scatterplot(data=BONA_EC_RF, x='MM_YY', 
#                y=BONA_EC_RF['GPP_f'], 
#                ax=axes[0], label='Obs. - RF',
#                s=8, facecolors='none', edgecolors='brown',linewidths=0.8, alpha=0.6)

#RECO observed
sns.scatterplot(data=BONA_EC_monthly_v3, x='MM_YY', 
                y=BONA_EC_monthly_v3['RECO_NT_VUT_50'], ax=axes[1], legend=False, 
                s=8, facecolors='none', edgecolors=palette[1],linewidths=0.8, alpha=0.6)

#sns.scatterplot(data=BONA_EC_RF, x='MM_YY', 
#                y=BONA_EC_RF['Reco'], ax=axes[1],
#                s=8, facecolors='none', edgecolors='brown',linewidths=0.8, alpha=0.6)

#NEE observed
sns.scatterplot(data=BONA_EC_monthly_v3, x='MM_YY', 
                y=BONA_EC_monthly_v3['NEE_VUT_50'], 
                ax=axes[2], legend=False,
                s=8, facecolors='none', edgecolors=palette[1],linewidths=0.8, alpha=0.6)
sns.scatterplot(data=BONA_EC_RF, x='MM_YY', 
                y=BONA_EC_RF['NEE_f'], 
                ax=axes[2], legend=False,label='Obs. - RF',
                s=8, facecolors='none', edgecolors='brown',linewidths=0.8, alpha=0.6)


sns.lineplot(data=tem_inputs.loc[(tem_inputs['time']>'2019-01-01') & (tem_inputs['time']<'2025-01-01')], 
             x='time', y='tair', label = r'$\mathrm{T}_{\mathrm{air}}$', ax=axes[3], alpha=0.8, color=palette[1], linewidth=0.8)

ax2=axes[3].twinx()
filtered_data = tem_inputs.loc[(tem_inputs['time']>'2019-01-01') & (tem_inputs['time']<'2025-01-01')]

# Ensure 'time' is datetime
filtered_data['time'] = pd.to_datetime(filtered_data['time'])

# Calculate appropriate bar width based on your data frequency
time_delta = (filtered_data['time'].max() - filtered_data['time'].min()) / len(filtered_data)
width = time_delta.days * 0.5  # 50% of the time interval

ax2.bar(filtered_data['time'], filtered_data['precip'], width=width, alpha=0.7, color=palette[8], label='precip')
ax2.set_ylabel('Precip. (mm)')

axes[3].set_ylabel(r'$\mathrm{T}_{\mathrm{air}}$ (°C)')

axes[0].spines['top'].set_visible(False)
axes[0].spines['right'].set_visible(False)
axes[1].spines['top'].set_visible(False)
axes[1].spines['right'].set_visible(False)
axes[2].spines['top'].set_visible(False)
axes[2].spines['right'].set_visible(False)

axes[2].axhline(0, linestyle='--', color='black', alpha=0.4,linewidth=1)
axes[3].set_xlabel('')
axes[3].set_ylim(-27,40)

axes[0].set_ylabel('GPP\n(gC$m^{-2}$)')
axes[1].set_ylabel('RECO\n(gC$m^{-2}$)')
axes[2].set_ylabel('NEE\n(gC$m^{-2}$)')

# Combine legends from axes[0] and axes[2]
handles0, labels0 = axes[0].get_legend_handles_labels()
handles2, labels2 = axes[2].get_legend_handles_labels()
axes[0].legend(handles0 + handles2, labels0 + labels2, ncol=4, frameon=False, loc=(0.0,1))

#axes[0].legend(ncol=4, frameon=False, loc=(0.02,1))
#axes[2].legend(ncol=1, frameon=False, loc=(0.32,1))
axes[1].legend().remove()
axes[3].legend(frameon=False, loc=(0.1,.6))
ax2.legend(frameon=False, loc=(0.25,.6))

axes[2].set_xlim(pd.to_datetime('2019-01-01'), pd.to_datetime('2025-01-01'))

fig.tight_layout()
plt.savefig('output_figs/BONA/flux_hist.jpg', dpi=300)


fig, axes=plt.subplots(4,1,figsize=(8,4), sharex=True)

#Black Spruce modeled
sns.lineplot(data=df_bs.loc[(df_bs['date']>'2010-01-01') & (df_bs['date']<'2025-01-01')], 
             x='date', y='GPP', label = 'TEM Black Spruce', ax=axes[0], alpha=0.8, color=palette[5], linewidth=0.8)
sns.lineplot(data=df_bs.loc[(df_bs['date']>'2010-01-01') & (df_bs['date']<'2025-01-01')], 
             x='date', y='RECO', label = 'Black Spruce', ax=axes[1], legend=False, alpha=0.8, color=palette[5], linewidth=0.8)
sns.lineplot(data=df_bs.loc[(df_bs['date']>'2010-01-01') & (df_bs['date']<'2025-01-01')], 
             x='date', y='NEE', ax=axes[2], legend=False, alpha=0.8, color=palette[5], linewidth=0.8)

#Birch modeled
sns.lineplot(data=df_br.loc[(df_br['date']>'2010-01-01') & (df_br['date']<'2025-01-01')], 
             x='date', y='GPP', label = 'TEM Birch', ax=axes[0], alpha=0.8, color=palette[7], linewidth=0.8)
sns.lineplot(data=df_br.loc[(df_br['date']>'2010-01-01') & (df_br['date']<'2025-01-01')], 
             x='date', y='RECO', label = 'Deciduous', ax=axes[1], legend=False, alpha=0.8, color=palette[7], linewidth=0.8)
sns.lineplot(data=df_br.loc[(df_br['date']>'2010-01-01') & (df_br['date']<'2025-01-01')], 
             x='date', y='NEE', ax=axes[2], legend=False, alpha=0.8, color=palette[7], linewidth=0.8)

#GPP observed
sns.scatterplot(data=BONA_EC_monthly_v3, x='MM_YY', 
                y=BONA_EC_monthly_v3['GPP_NT_VUT_50'], 
                ax=axes[0], label='Observed', 
                s=8, facecolors='none', edgecolors=palette[1],linewidths=0.8, alpha=0.6)

#sns.scatterplot(data=BONA_EC_RF, x='MM_YY', 
#                y=BONA_EC_RF['GPP_f'], 
#                ax=axes[0], label='Obs. - RF',
#                s=8, facecolors='none', edgecolors='brown',linewidths=0.8, alpha=0.6)

#RECO observed
sns.scatterplot(data=BONA_EC_monthly_v3, x='MM_YY', 
                y=BONA_EC_monthly_v3['RECO_NT_VUT_50'], ax=axes[1], legend=False, 
                s=8, facecolors='none', edgecolors=palette[1],linewidths=0.8, alpha=0.6)

#sns.scatterplot(data=BONA_EC_RF, x='MM_YY', 
#                y=BONA_EC_RF['Reco'], ax=axes[1],
#                s=8, facecolors='none', edgecolors='brown',linewidths=0.8, alpha=0.6)

#NEE observed
#sns.scatterplot(data=BONA_EC_monthly_v3, x='MM_YY', 
#                y=BONA_EC_monthly_v3['NEE_VUT_50'], 
#                ax=axes[2], legend=False,
#                s=8, facecolors='none', edgecolors=palette[1],linewidths=0.8, alpha=0.6)
sns.scatterplot(data=BONA_EC_RF, x='MM_YY', 
                y=BONA_EC_RF['NEE_f'], 
                ax=axes[2], legend=False,
                s=8, facecolors='none', edgecolors=palette[1], linewidths=0.8, alpha=0.6)


sns.lineplot(data=tem_inputs.loc[(tem_inputs['time']>'2019-01-01') & (tem_inputs['time']<'2025-01-01')], 
             x='time', y='tair', label = r'$\mathrm{T}_{\mathrm{air}}$', ax=axes[3], alpha=0.8, color=palette[1], linewidth=0.8)

ax2=axes[3].twinx()
filtered_data = tem_inputs.loc[(tem_inputs['time']>'2019-01-01') & (tem_inputs['time']<'2025-01-01')]

# Ensure 'time' is datetime
filtered_data['time'] = pd.to_datetime(filtered_data['time'])

# Calculate appropriate bar width based on your data frequency
time_delta = (filtered_data['time'].max() - filtered_data['time'].min()) / len(filtered_data)
width = time_delta.days * 0.5  # 50% of the time interval

ax2.bar(filtered_data['time'], filtered_data['precip'], width=width, alpha=0.7, color=palette[8], label='precip')
ax2.set_ylabel('Precip. (mm)')

axes[3].set_ylabel(r'$\mathrm{T}_{\mathrm{air}}$ (°C)')

axes[0].spines['top'].set_visible(False)
axes[0].spines['right'].set_visible(False)
axes[1].spines['top'].set_visible(False)
axes[1].spines['right'].set_visible(False)
axes[2].spines['top'].set_visible(False)
axes[2].spines['right'].set_visible(False)

axes[2].axhline(0, linestyle='--', color='black', alpha=0.4,linewidth=1)
axes[3].set_xlabel('')
axes[3].set_ylim(-27,40)

axes[0].set_ylabel('GPP\n(gC$m^{-2}$)')
axes[1].set_ylabel('RECO\n(gC$m^{-2}$)')
axes[2].set_ylabel('NEE\n(gC$m^{-2}$)')

# Combine legends from axes[0] and axes[2]
handles0, labels0 = axes[0].get_legend_handles_labels()
handles2, labels2 = axes[2].get_legend_handles_labels()
axes[0].legend(handles0 + handles2, labels0 + labels2, ncol=4, frameon=False, loc=(0.0,1))

#axes[0].legend(ncol=4, frameon=False, loc=(0.02,1))
#axes[2].legend(ncol=1, frameon=False, loc=(0.32,1))
axes[1].legend().remove()
axes[3].legend(frameon=False, loc=(0.1,.6))
ax2.legend(frameon=False, loc=(0.25,.6))

axes[2].set_xlim(pd.to_datetime('2019-01-01'), pd.to_datetime('2025-01-01'))

fig.tight_layout()
plt.savefig('output_figs/BONA/flux_hist_obs.jpg', dpi=300)


BONA_EC_RF.columns


from sklearn.metrics import r2_score, mean_squared_error
import numpy as np
months = [1,2,3,4,5,6,7,8,9,10,11,12]
date_min = pd.to_datetime('2019-01-01')
date_max = pd.to_datetime('2025-01-01')

# Get the data
observed_gpp = BONA_EC_monthly_v3.loc[(BONA_EC_monthly_v3['MM_YY']>date_min) & 
                                      (BONA_EC_monthly_v3['MM_YY']<date_max) &
                                      (BONA_EC_monthly_v3['MM_YY'].dt.month.isin(months)), 'GPP_NT_VUT_50'].values
modeled_gpp = df_bs.loc[(df_bs['date']>date_min) & (df_bs['date']<date_max) &
                        (df_bs['date'].dt.month.isin(months)), 'GPP'].values

observed_reco = BONA_EC_monthly_v3.loc[(BONA_EC_monthly_v3['MM_YY']>date_min) & 
                                       (BONA_EC_monthly_v3['MM_YY']<date_max) &
                                       (BONA_EC_monthly_v3['MM_YY'].dt.month.isin(months)), 'RECO_NT_VUT_50'].values
modeled_reco = df_bs.loc[(df_bs['date']>date_min) & (df_bs['date']<date_max) &
                         (df_bs['date'].dt.month.isin(months)), 'RECO'].values

observed_nee = BONA_EC_RF.loc[(BONA_EC_RF['MM_YY']>date_min) & 
                              (BONA_EC_RF['MM_YY']<date_max) &
                              (BONA_EC_RF['MM_YY'].dt.month.isin(months)), 'NEE_f'].values

modeled_nee = df_bs.loc[(df_bs['date']>date_min) & (df_bs['date']<date_max)&
                        (df_bs['date'].dt.month.isin(months)), 'NEE'].values

# Calculate metrics
r2_gpp = r2_score(observed_gpp, modeled_gpp)
bias_gpp = np.mean(modeled_gpp - observed_gpp)
rmse_gpp = np.sqrt(mean_squared_error(observed_gpp, modeled_gpp))

r2_reco = r2_score(observed_reco, modeled_reco)
bias_reco = np.mean(modeled_reco - observed_reco)
rmse_reco = np.sqrt(mean_squared_error(observed_reco, modeled_reco))

r2_nee = r2_score(observed_nee, modeled_nee)
bias_nee = np.mean(modeled_nee - observed_nee)
rmse_nee = np.sqrt(mean_squared_error(observed_nee, modeled_nee))

print('Black Spruce')
print('###################')
print('GPP')
print('-------------------')
print(f"R² = {r2_gpp:.4f}")
print(f"Bias = {bias_gpp:.4f}")
print(f"RMSE = {rmse_gpp:.4f}")
print('###################')
print('RECO')
print('-------------------')
print(f"R² = {r2_reco:.4f}")
print(f"Bias = {bias_reco:.4f}")
print(f"RMSE = {rmse_reco:.4f}")
print('###################')
print('NEE')
print('-------------------')
print(f"R² = {r2_nee:.4f}")
print(f"Bias = {bias_nee:.4f}")
print(f"RMSE = {rmse_nee:.4f}")
print()
print()



from sklearn.metrics import r2_score, mean_squared_error
import numpy as np

date_min = pd.to_datetime('2019-01-01')
date_max = pd.to_datetime('2025-01-01')

# Get the data
observed_gpp = BONA_EC_monthly_v3.loc[(BONA_EC_monthly_v3['MM_YY']>date_min) & (BONA_EC_monthly_v3['MM_YY']<date_max), 'GPP_NT_VUT_50'].values
modeled_gpp = df_br.loc[(df_bs['date']>date_min) & (df_br['date']<date_max), 'GPP'].values

observed_reco = BONA_EC_monthly_v3.loc[(BONA_EC_monthly_v3['MM_YY']>date_min) & (BONA_EC_monthly_v3['MM_YY']<date_max), 'RECO_NT_VUT_50'].values
modeled_reco = df_br.loc[(df_bs['date']>date_min) & (df_br['date']<date_max), 'RECO'].values

observed_nee = BONA_EC_RF.loc[(BONA_EC_RF['MM_YY']>date_min) & (BONA_EC_RF['MM_YY']<date_max), 'NEE_f'].values
modeled_nee = df_br.loc[(df_bs['date']>date_min) & (df_br['date']<date_max), 'NEE'].values

# Calculate metrics
r2_gpp = r2_score(observed_gpp, modeled_gpp)
bias_gpp = np.mean(modeled_gpp - observed_gpp)
rmse_gpp = np.sqrt(mean_squared_error(observed_gpp, modeled_gpp))

r2_reco = r2_score(observed_reco, modeled_reco)
bias_reco = np.mean(modeled_reco - observed_reco)
rmse_reco = np.sqrt(mean_squared_error(observed_reco, modeled_reco))

r2_nee = r2_score(observed_nee, modeled_nee)
bias_nee = np.mean(modeled_nee - observed_nee)
rmse_nee = np.sqrt(mean_squared_error(observed_nee, modeled_nee))

print('Birch')
print('###################')
print('GPP')
print('-------------------')
print(f"R² = {r2_gpp:.4f}")
print(f"Bias = {bias_gpp:.4f}")
print(f"RMSE = {rmse_gpp:.4f}")
print('###################')
print('RECO')
print('-------------------')
print(f"R² = {r2_reco:.4f}")
print(f"Bias = {bias_reco:.4f}")
print(f"RMSE = {rmse_reco:.4f}")
print('###################')
print('NEE')
print('-------------------')
print(f"R² = {r2_nee:.4f}")
print(f"Bias = {bias_nee:.4f}")
print(f"RMSE = {rmse_nee:.4f}")
print()
print()

# Define seasons
summer_months = [6, 7, 8]  # June, July, August
shoulder_months = [4, 5, 9, 10]  # April, May, September, October
winter_months = [11, 12, 1, 2, 3]  # November - March


import pandas as pd
import numpy as np
from sklearn.metrics import r2_score, mean_squared_error

date_min = pd.to_datetime("2019-01-01")
date_max = pd.to_datetime("2025-01-01")

def metrics(obs, mod):
    return {
        "r2": r2_score(obs, mod),
        "bias": np.mean(mod - obs),
        "rmse": np.sqrt(mean_squared_error(obs, mod))
    }

def annual_stats(obs_df, mod_df, obs_col, mod_col, flux):
    df = (
        obs_df[['MM_YY', obs_col]]
        .rename(columns={'MM_YY': 'date', obs_col: 'obs'})
        .merge(
            mod_df[['date', mod_col]].rename(columns={mod_col: 'mod'}),
            on='date',
            how='inner'
        )
    )
    df = df[(df['date'] > date_min) & (df['date'] < date_max)].dropna()
    df['year'] = df['date'].dt.year

    rows = []
    for y, g in df.groupby('year'):
        if len(g) > 1:  # r2 requires >=2 samples
            rows.append({
                "year": y,
                "flux": flux,
                **metrics(g['obs'].values, g['mod'].values)
            })
    return pd.DataFrame(rows)

annual_metrics = pd.concat([
    annual_stats(BONA_EC_monthly_v3, df_br, "GPP_NT_VUT_50", "GPP",  "GPP"),
    annual_stats(BONA_EC_monthly_v3, df_br, "RECO_NT_VUT_50", "RECO", "RECO"),
    annual_stats(BONA_EC_RF,         df_br, "NEE_f",          "NEE",  "NEE"),
], ignore_index=True)

annual_wide = (
    annual_metrics
    .pivot(index="year", columns="flux", values=["r2", "bias", "rmse"])
    .swaplevel(0, 1, axis=1)
    .sort_index(axis=1)
)

annual_wide


import pandas as pd
import numpy as np
from sklearn.metrics import r2_score, mean_squared_error

date_min = pd.to_datetime("2019-01-01")
date_max = pd.to_datetime("2025-01-01")

def metrics(obs, mod):
    return {
        "r2": r2_score(obs, mod),
        "bias": np.mean(mod - obs),
        "rmse": np.sqrt(mean_squared_error(obs, mod))
    }

def annual_stats(obs_df, mod_df, obs_col, mod_col, flux):
    df = (
        obs_df[['MM_YY', obs_col]]
        .rename(columns={'MM_YY': 'date', obs_col: 'obs'})
        .merge(
            mod_df[['date', mod_col]].rename(columns={mod_col: 'mod'}),
            on='date',
            how='inner'
        )
    )
    df = df[(df['date'] > date_min) & (df['date'] < date_max)].dropna()
    df['year'] = df['date'].dt.year

    rows = []
    for y, g in df.groupby('year'):
        if len(g) > 1:  # r2 requires >=2 samples
            rows.append({
                "year": y,
                "flux": flux,
                **metrics(g['obs'].values, g['mod'].values)
            })
    return pd.DataFrame(rows)

annual_metrics = pd.concat([
    annual_stats(BONA_EC_monthly_v3, df_bs, "GPP_NT_VUT_50", "GPP",  "GPP"),
    annual_stats(BONA_EC_monthly_v3, df_bs, "RECO_NT_VUT_50", "RECO", "RECO"),
    annual_stats(BONA_EC_RF,         df_bs, "NEE_f",          "NEE",  "NEE"),
], ignore_index=True)

annual_metrics = annual_metrics.round(2)

annual_wide = (
    annual_metrics
    .pivot(index="year", columns="flux", values=["r2", "bias", "rmse"])
    .swaplevel(0, 1, axis=1)
    .sort_index(axis=1)
)

annual_wide


df_br_comp = df_br.loc[(df_br['date']>=date_min) & (df_br['date']<date_max)]
df_br_comp = df_br_comp.groupby(by=df_br_comp.date.dt.year).aggregate({
    'GPP': 'sum',
    'RECO': 'sum',
    'NEE': 'sum'
}).reset_index()

df_br_comp


df_bs_comp = df_bs.loc[(df_br['date']>=date_min) & (df_bs['date']<date_max)]
df_bs_comp = df_bs_comp.groupby(by=df_bs_comp.date.dt.year).aggregate({
    'GPP': 'sum',
    'RECO': 'sum',
    'NEE': 'sum'
}).reset_index()

df_bs_comp


df_oneflux_comp = BONA_EC_monthly_v3.loc[(BONA_EC_monthly_v3['MM_YY']>=date_min) & (BONA_EC_monthly_v3['MM_YY']<date_max)]
df_oneflux_comp = df_oneflux_comp.groupby(by=df_oneflux_comp.MM_YY.dt.year).aggregate({
    'GPP_NT_VUT_50': 'sum',
    'RECO_NT_VUT_50': 'sum'
}).reset_index()

df_oneflux_comp.columns = ['date', 'GPP', 'RECO']

df_rf_comp = BONA_EC_RF.loc[(BONA_EC_RF['MM_YY']>=date_min) & (BONA_EC_RF['MM_YY']<date_max)]
df_rf_comp = df_rf_comp.groupby(by=df_rf_comp.MM_YY.dt.year).aggregate({
    'NEE_f': 'sum'
}).reset_index()

df_rf_comp.columns = ['date', 'NEE']

df_ec_comp = df_oneflux_comp.merge(df_rf_comp, on='date')
df_ec_comp


r2_gpp_bs = r2_score(df_ec_comp['GPP'], df_bs_comp['GPP'])
bias_gpp_bs = np.mean(df_bs_comp['GPP'] - df_ec_comp['GPP'])
rmse_gpp_bs = np.sqrt(mean_squared_error(df_ec_comp['GPP'], df_bs_comp['GPP']))

r2_gpp_br = r2_score(df_ec_comp['GPP'], df_br_comp['GPP'])
bias_gpp_br = np.mean(df_br_comp['GPP'] - df_ec_comp['GPP'])
rmse_gpp_br = np.sqrt(mean_squared_error(df_ec_comp['GPP'], df_br_comp['GPP']))

r2_reco_bs = r2_score(df_ec_comp['RECO'], df_bs_comp['RECO'])
bias_reco_bs = np.mean(df_bs_comp['RECO'] - df_ec_comp['RECO'])
rmse_reco_bs = np.sqrt(mean_squared_error(df_ec_comp['RECO'], df_bs_comp['RECO']))

r2_reco_br = r2_score(df_ec_comp['RECO'], df_br_comp['RECO'])
bias_reco_br = np.mean(df_br_comp['RECO'] - df_ec_comp['RECO'])
rmse_reco_br = np.sqrt(mean_squared_error(df_ec_comp['RECO'], df_br_comp['RECO']))

r2_nee_bs = r2_score(df_ec_comp['NEE'], df_bs_comp['NEE'])
bias_nee_bs = np.mean(df_bs_comp['NEE'] - df_ec_comp['NEE'])
rmse_nee_bs = np.sqrt(mean_squared_error(df_ec_comp['NEE'], df_bs_comp['NEE']))

r2_nee_br = r2_score(df_ec_comp['NEE'], df_br_comp['NEE'])
bias_nee_br = np.mean(df_br_comp['NEE'] - df_ec_comp['NEE'])
rmse_nee_br = np.sqrt(mean_squared_error(df_ec_comp['NEE'], df_br_comp['NEE']))

# Create the comparison table
metrics_data = {
    'Variable': ['GPP', 'GPP', 'RECO', 'RECO', 'NEE', 'NEE'],
    'Model': ['BS', 'BR', 'BS', 'BR', 'BS', 'BR'],
    'R²': [r2_gpp_bs, r2_gpp_br, r2_reco_bs, r2_reco_br, r2_nee_bs, r2_nee_br],
    'Bias': [bias_gpp_bs, bias_gpp_br, bias_reco_bs, bias_reco_br, bias_nee_bs, bias_nee_br],
    'RMSE': [rmse_gpp_bs, rmse_gpp_br, rmse_reco_bs, rmse_reco_br, rmse_nee_bs, rmse_nee_br]
}

# Create DataFrame
results_df = pd.DataFrame(metrics_data)
print(results_df.to_string(index=False))


fig, axes=plt.subplots(3,1,figsize=(10,4), sharex=True)

#transient
sns.lineplot(data=df_bs.loc[(df_bs['date']>'2010-01-01') & (df_bs['date']<'2025-01-01')], 
             x='date', y='GPP', label = 'Black Spruce', ax=axes[0], alpha=0.8, color='#2A788EFF')
sns.lineplot(data=df_bs.loc[(df_bs['date']>'2010-01-01') & (df_bs['date']<'2025-01-01')], 
             x='date', y='RECO', ax=axes[1], legend=False, alpha=0.7, color='#2A788EFF')
sns.lineplot(data=df_bs.loc[(df_bs['date']>'2010-01-01') & (df_bs['date']<'2025-01-01')], 
             x='date', y='NEE', label = 'Black Spruce', ax=axes[2], legend=False, alpha=0.7, color='#2A788EFF')
#sns.lineplot(data=df_bs.loc[(df_bs['date']>'2010-01-01') & (df_bs['date']<'2025-01-01')], 
#             x='date', y='RH', label = 'Black Spruce', ax=axes[1], legend=False, alpha=0.7, color='red')

sns.lineplot(data=df_br.loc[(df_br['date']>'2010-01-01') & (df_br['date']<'2025-01-01')], 
             x='date', y='GPP', label = 'Deciduous', ax=axes[0], alpha=0.8, color='#35B779FF')
sns.lineplot(data=df_br.loc[(df_br['date']>'2010-01-01') & (df_br['date']<'2025-01-01')], 
             x='date', y='RECO', ax=axes[1], legend=False, alpha=0.7, color='#35B779FF')
sns.lineplot(data=df_br.loc[(df_br['date']>'2010-01-01') & (df_br['date']<'2025-01-01')], 
             x='date', y='NEE', label = 'Deciduous', ax=axes[2], legend=False, alpha=0.7, color='#35B779FF')

sns.scatterplot(data=BONA_EC_monthly_v3, x='MM_YY', 
                y=BONA_EC_monthly_v3['GPP_NT_VUT_50'], 
                ax=axes[0], label='Obs. - OneFlux', color='black', s=8, alpha=0.7)

sns.scatterplot(data=BONA_EC_RF, x='MM_YY', 
                y=BONA_EC_RF['GPP_f'], 
                ax=axes[0], label='Obs. - RF', s=8, alpha=0.7)
sns.scatterplot(data=BONA_EC_ABC, x='MM_YY', 
                y=BONA_EC_ABC['gpp'], 
                ax=axes[0], label='Obs. - ABC', s=8, alpha=0.7)
ax2=axes[0].twinx()
sns.lineplot(data = SIF_BS_daily, x='Date', y='Y.II.', ax=ax2, color='#2A788EFF', linestyle='--', linewidth=1, alpha=0.7)
sns.lineplot(data = SIF_BR_daily, x='Date', y='SIF760_Wide', ax=ax2, color='#35B779FF', linestyle='--', linewidth=1, alpha=0.7)
ax2.set_ylim(0,1)

#RECO_NT_VUT_REF
sns.scatterplot(data=BONA_EC_monthly_v3, x='MM_YY', 
                y=BONA_EC_monthly_v3['RECO_NT_VUT_50'], 
                ax=axes[1], legend=False, color='black', s=4)
sns.scatterplot(data=BONA_EC_RF, x='MM_YY', 
                y=BONA_EC_RF['Reco'], 
                ax=axes[1], s=5, alpha=0.5)
sns.scatterplot(data=BONA_EC_ABC, x='MM_YY', 
                y=BONA_EC_ABC['reco'], 
                ax=axes[1], s=5, alpha=0.5)
sns.scatterplot(x=BONA_EC_monthly_v3['MM_YY'], 
                y=BONA_EC_monthly_v3['GPP_NT_VUT_50'] - BONA_EC_RF['NEE_f'], 
                ax=axes[1], s=8, alpha=0.7, color='red', label='Oneflux GPP - RF NEE')
#sns.scatterplot(data=BONA_EC_monthly_v2, x='MM_YY', 
#                y=BONA_EC_monthly_v2['RECO_NT_VUT_50'] * BONA_EC_monthly_v2['daysinmonth'], 
#                ax=axes[1], legend=False, color='red', s=5, alpha=0.5)
#sns.scatterplot(data=BONA_EC_monthly, x='MM_YY', 
#                y=BONA_EC_monthly['NEE_gCm-2'] + BONA_EC_monthly['GPP_gCm-2'], 
#                ax=axes[1], legend=False, color='blue', s=5, alpha=0.5)


sns.scatterplot(data=BONA_EC_monthly_v3, x='MM_YY', 
                y=BONA_EC_monthly_v3['NEE_VUT_50'], 
                ax=axes[2], legend=False, color='black', s=4)
sns.scatterplot(data=BONA_EC_RF, x='MM_YY', 
                y=BONA_EC_RF['NEE_f'], 
                ax=axes[2], legend=False, s=4)
sns.scatterplot(data=BONA_EC_ABC, x='MM_YY', 
                y=BONA_EC_ABC['nee'], 
                ax=axes[2], legend=False, s=4)

#sns.scatterplot(data=BONA_EC_monthly_v2, x='MM_YY', 
#                y=BONA_EC_monthly_v2['NEE_VUT_50'] * BONA_EC_monthly_v2['daysinmonth'], 
#                ax=axes[2], legend=False, color='red', s=5, alpha=0.5)

#sns.scatterplot(data=BONA_EC_monthly, x='MM_YY', 
#                y=BONA_EC_monthly['NEE_gCm-2'], 
#                ax=axes[2], legend=False, color='blue', s=5, alpha=0.5)


axes[2].axhline(0, linestyle='--')
plt.xlabel('')

axes[0].set_ylabel('GPP (gC$m^{-2}$)')
axes[1].set_ylabel('Reco (gC$m^{-2}$)')
axes[2].set_ylabel('NEE (gC$m^{-2}$)')

axes[0].legend(ncol=3, frameon=False, loc=(0.1,1))
axes[1].legend(frameon=False, loc=(0.6,.9))

axes[2].set_xlim(pd.to_datetime('2022-01-01'), pd.to_datetime('2025-01-01'))

fig.tight_layout()
#plt.savefig('output_figs/BONA/flux_hist.jpg', dpi=300)


BONA_EC_RF


BONA_EC_RF['month'] = BONA_EC_RF['MM_YY'].dt.month
BONA_EC_RF['year'] = BONA_EC_RF['MM_YY'].dt.year
sns.barplot(data=BONA_EC_RF, x='month', y='NEE_f', hue='year')


# Calculate cumulative NEE for each year
BONA_EC_RF['cumulative_NEE'] = BONA_EC_RF.groupby('year')['NEE_f'].cumsum()

# Plot
sns.lineplot(data=BONA_EC_RF, x='month', y='cumulative_NEE', hue='year', marker='o')
plt.ylabel('Cumulative NEE')
plt.xlabel('Month')


from matplotlib import ticker
from operator import itemgetter

years = ['2021', '2022', '2023', '2024']
tem_inputs['year'] = tem_inputs['time'].dt.year
obs_data['year'] = obs_data['time'].dt.year
obs_data['season'] = 'winter'
obs_data['month'] = obs_data['time'].dt.month
obs_data['water_year'] = obs_data['time'].dt.year
obs_data.loc[obs_data['month'] >= 10, 'water_year'] = obs_data.loc[obs_data['month'] >= 10, 'water_year'] + 1
obs_data.loc[(obs_data['month']>=7) & (obs_data['month']<=8), 'season'] = 'summer'
obs_data.loc[(obs_data['month']>=4) & (obs_data['month']<=6), 'season'] = 'spring'
obs_data.loc[(obs_data['month']>=9) & (obs_data['month']<=10), 'season'] = 'fall'

obs_data = obs_data.loc[obs_data['water_year'] <2025]

annual_fluxes_bs_mod = df_bs.loc[(df_bs['date']>='2019-01-01') & (df_bs['date']<'2025-01-01')][['date', 'RECO', 'GPP', 'NEE']]
annual_fluxes_bs_mod=annual_fluxes_bs_mod.groupby(by=annual_fluxes_bs_mod['date'].dt.year).sum().reset_index()
annual_fluxes_bs_mod['desc'] = 'black spruce modeled'

annual_fluxes_br_mod = df_br.loc[(df_br['date']>='2019-01-01') & (df_br['date']<'2025-01-01')][['date', 'RECO', 'GPP', 'NEE']]
annual_fluxes_br_mod=annual_fluxes_br_mod.groupby(by=annual_fluxes_br_mod['date'].dt.year).sum().reset_index()
annual_fluxes_br_mod['desc'] = 'birch modeled'

annual_fluxes_rf = BONA_EC_RF.loc[(BONA_EC_RF['MM_YY']>='2019-01-01') & (BONA_EC_RF['MM_YY']<'2025-01-01')][['MM_YY', 'GPP_f', 'Reco', 'NEE_f']]
annual_fluxes_rf = annual_fluxes_rf.groupby(by=annual_fluxes_rf['MM_YY'].dt.year).sum().reset_index()
annual_fluxes_rf['desc'] = 'observed'
annual_fluxes_rf = annual_fluxes_rf.rename(columns={'MM_YY': 'date', 'GPP_f': 'GPP', 
                                                      'Reco':'RECO', 'NEE_f':'NEE'})

annual_fluxes_oneflux = BONA_EC_monthly_v3.loc[(BONA_EC_monthly_v3['MM_YY']>='2019-01-01') & (BONA_EC_monthly_v3['MM_YY']<'2025-01-01')][['MM_YY', 'GPP_NT_VUT_50', 'RECO_NT_VUT_50', 'NEE_VUT_50']]
annual_fluxes_oneflux = annual_fluxes_oneflux.groupby(by=annual_fluxes_oneflux['MM_YY'].dt.year).sum().reset_index()
annual_fluxes_oneflux['desc'] = 'observed - oneflux'
annual_fluxes_oneflux = annual_fluxes_oneflux.rename(columns={'MM_YY': 'date', 'GPP_NT_VUT_50': 'GPP', 
                                                      'RECO_NT_VUT_50':'RECO', 'NEE_VUT_50':'NEE'})

annual_flux_comp = pd.concat([annual_fluxes_bs_mod, annual_fluxes_br_mod, annual_fluxes_rf])

fig, axes=plt.subplots(5,1, figsize=(8,4.5), sharex=True)

sns.barplot(data = annual_flux_comp, x=annual_flux_comp['date'], y='NEE', hue='desc', palette=list(itemgetter(5, 7, 3)(palette)), ax=axes[0])
sns.boxplot(data=obs_data.loc[obs_data['water_year']>=2019], x='year', y='tair', ax=axes[1], hue='season',legend=False)
sns.barplot(data=obs_data.loc[obs_data['water_year']>=2019], x='water_year', y='precip', ax=axes[2], hue='season',legend=False, zorder=3)
#sns.boxplot(data=obs_data.loc[obs_data['water_year']>=2019], x='water_year', y='vpd', ax=axes[3], hue='season',legend=False)
sns.boxplot(data=obs_data.loc[obs_data['water_year']>=2019], x='year', y='vpd', ax=axes[3], hue='season',legend=False)
sns.boxplot(data=obs_data.loc[obs_data['water_year']>=2019], x='year', y='nirr', ax=axes[4], hue='season',legend=False)

minor_locator1 = ticker.MultipleLocator(10)
axes[1].yaxis.set_minor_locator(minor_locator1)
axes[1].grid(which='minor', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6)
axes[1].grid(which='major', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6)

minor_locator2 = ticker.MultipleLocator(25)
axes[2].yaxis.set_minor_locator(minor_locator2)
axes[2].grid(which='minor', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6)
axes[2].grid(which='major', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6)

minor_locator3 = ticker.MultipleLocator(2)
#axes[3].yaxis.set_minor_locator(minor_locator3)
#axes[3].grid(which='minor', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6)
#axes[3].grid(which='major', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6)


axes[0].legend(frameon=False, ncol=3, loc=(0.1,1))

plt.savefig('annual_cumulative_flux_comp.jpg', dpi=300)


# Prepare each dataframe with renamed columns using desc as suffix
monthly_fluxes_bs_mod = df_bs.loc[(df_bs['date']>='2019-01-01') & (df_bs['date']<'2025-01-01')][['date', 'RECO', 'GPP', 'NEE']]
monthly_fluxes_bs_mod = monthly_fluxes_bs_mod.rename(columns={
    'RECO': 'RECO_black_spruce_modeled',
    'GPP': 'GPP_black_spruce_modeled',
    'NEE': 'NEE_black_spruce_modeled'
})

monthly_fluxes_br_mod = df_br.loc[(df_br['date']>='2019-01-01') & (df_br['date']<'2025-01-01')][['date', 'RECO', 'GPP', 'NEE']]
monthly_fluxes_br_mod = monthly_fluxes_br_mod.rename(columns={
    'RECO': 'RECO_birch_modeled',
    'GPP': 'GPP_birch_modeled',
    'NEE': 'NEE_birch_modeled'
})

monthly_fluxes_rf = BONA_EC_RF.loc[(BONA_EC_RF['MM_YY']>='2019-01-01') & (BONA_EC_RF['MM_YY']<'2025-01-01')][['MM_YY', 'GPP_f', 'Reco', 'NEE_f']]
monthly_fluxes_rf = monthly_fluxes_rf.rename(columns={
    'MM_YY': 'date',
    'GPP_f': 'GPP_observed_RF',
    'Reco': 'RECO_observed_RF',
    'NEE_f': 'NEE_observed_RF'
})

monthly_fluxes_oneflux = BONA_EC_monthly_v3.loc[(BONA_EC_monthly_v3['MM_YY']>='2019-01-01') & (BONA_EC_monthly_v3['MM_YY']<'2025-01-01')][['MM_YY', 'GPP_NT_VUT_50', 'RECO_NT_VUT_50', 'NEE_VUT_50']]
monthly_fluxes_oneflux = monthly_fluxes_oneflux.rename(columns={
    'MM_YY': 'date',
    'GPP_NT_VUT_50': 'GPP_observed_oneflux',
    'RECO_NT_VUT_50': 'RECO_observed_oneflux',
    'NEE_VUT_50': 'NEE_observed_oneflux'
})

monthly_obs_data = tem_inputs.loc[(tem_inputs['time']>='2019-01-01') & (tem_inputs['time']<'2025-01-01')][['time','tair','nirr','precip']]
monthly_obs_data = monthly_obs_data.rename(columns={'time': 'date'})

# Merge all dataframes on 'date'
monthly_flux_comp = monthly_fluxes_bs_mod.merge(monthly_fluxes_br_mod, on='date', how='inner')
monthly_flux_comp = monthly_flux_comp.merge(monthly_fluxes_rf, on='date', how='inner')
monthly_flux_comp = monthly_flux_comp.merge(monthly_fluxes_oneflux, on='date', how='inner')
monthly_flux_comp = monthly_flux_comp.merge(monthly_obs_data, on='date', how='inner')

monthly_flux_comp.to_csv('monthly_flux_table.csv', index=False)       


tem_inputs


from matplotlib import ticker
from operator import itemgetter

years = ['2021', '2022', '2023', '2024']
tem_inputs['year'] = tem_inputs['time'].dt.year
obs_data['year'] = obs_data['time'].dt.year
obs_data['season'] = 'winter'
obs_data['month'] = obs_data['time'].dt.month
obs_data['water_year'] = obs_data['time'].dt.year
obs_data.loc[obs_data['month'] >= 10, 'water_year'] = obs_data.loc[obs_data['month'] >= 10, 'water_year'] + 1
obs_data.loc[(obs_data['month']>=7) & (obs_data['month']<=8), 'season'] = 'summer'
obs_data.loc[(obs_data['month']>=4) & (obs_data['month']<=6), 'season'] = 'spring'
obs_data.loc[(obs_data['month']>=9) & (obs_data['month']<=10), 'season'] = 'fall'

obs_data = obs_data.loc[obs_data['water_year'] <2025]

annual_fluxes_bs_mod = df_bs.loc[(df_bs['date']>='2019-01-01') & (df_bs['date']<'2025-01-01')][['date', 'RECO', 'GPP', 'NEE']]
annual_fluxes_bs_mod=annual_fluxes_bs_mod.groupby(by=annual_fluxes_bs_mod['date'].dt.year).sum().reset_index()
annual_fluxes_bs_mod['desc'] = 'black spruce modeled'

annual_fluxes_br_mod = df_br.loc[(df_br['date']>='2019-01-01') & (df_br['date']<'2025-01-01')][['date', 'RECO', 'GPP', 'NEE']]
annual_fluxes_br_mod=annual_fluxes_br_mod.groupby(by=annual_fluxes_br_mod['date'].dt.year).sum().reset_index()
annual_fluxes_br_mod['desc'] = 'birch modeled'

annual_fluxes_rf = BONA_EC_RF.loc[(BONA_EC_RF['MM_YY']>='2019-01-01') & (BONA_EC_RF['MM_YY']<'2025-01-01')][['MM_YY', 'GPP_f', 'Reco', 'NEE_f']]
annual_fluxes_rf = annual_fluxes_rf.groupby(by=annual_fluxes_rf['MM_YY'].dt.year).sum().reset_index()
annual_fluxes_rf['desc'] = 'observed'
annual_fluxes_rf = annual_fluxes_rf.rename(columns={'MM_YY': 'date', 'GPP_f': 'GPP', 
                                                      'Reco':'RECO', 'NEE_f':'NEE'})

annual_flux_comp = pd.concat([annual_fluxes_bs_mod, annual_fluxes_br_mod, annual_fluxes_rf])

fig, axes=plt.subplots(5,1, figsize=(8,7), sharex=True)

sns.barplot(data = annual_flux_comp, x=annual_flux_comp['date'], y='NEE', hue='desc', palette=list(itemgetter(5, 7, 3)(palette)), ax=axes[0],zorder=3)
axes[0].axhline(0,linestyle='--',linewidth=0.8, alpha=0.6, color='black')
sns.barplot(data=obs_data_yearly.loc[obs_data_yearly['time']>=2019], 
            x='time', y='precip_sum', ax=axes[1], 
            legend=False, zorder=3, fill=False, linewidth=1, color=palette[1], width=0.4)

sns.boxplot(data=obs_data.loc[obs_data['water_year']>=2019], x='year', y='tair', 
            ax=axes[2],legend=False, color=palette[1], fill=False, linewidth=1, 
            width=0.4,medianprops={"color": "r", "linewidth": 1.5})

sns.boxplot(data=obs_data.loc[obs_data['water_year']>=2019], x='year', y='vpd', ax=axes[3],legend=False, 
            color=palette[1], fill=False, linewidth=1, width=0.4,medianprops={"color": "r", "linewidth": 1.5})

sns.boxplot(data=obs_data.loc[obs_data['water_year']>=2019], x='year', y='nirr', ax=axes[4],legend=False,
            color=palette[1], fill=False, linewidth=1, width=0.4,medianprops={"color": "r", "linewidth": 1.5})

minor_locator1 = ticker.MultipleLocator(100)
axes[1].yaxis.set_minor_locator(minor_locator1)
axes[1].grid(which='minor', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6)
axes[1].grid(which='major', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6)

minor_locator2 = ticker.MultipleLocator(10)
axes[2].yaxis.set_minor_locator(minor_locator2)
axes[2].grid(which='minor', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6)
axes[2].grid(which='major', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6)

minor_locator3 = ticker.MultipleLocator(2)
axes[3].yaxis.set_minor_locator(minor_locator3)
axes[3].grid(which='minor', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6)
axes[3].grid(which='major', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6)

minor_locator4 = ticker.MultipleLocator(50)
axes[4].yaxis.set_minor_locator(minor_locator4)
axes[4].grid(which='minor', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6)
axes[4].grid(which='major', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6)

axes[0].set_ylabel('NEE (gC $m^{-2}$)')
axes[2].set_ylabel(r'$\mathrm{T}_{\mathrm{air}}$ (°C)')
axes[1].set_ylabel('precip. (mm)')
axes[3].set_ylabel('VPD (Pa)')
axes[4].set_ylabel('$SW_{in}$ (W $m^{-2}$)')
axes[4].set_xlabel('')


axes[0].legend(frameon=False, ncol=3, loc=(0.1,1))

plt.savefig('annual_cumulative_flux_comp.jpg', dpi=300)


from matplotlib import ticker
from operator import itemgetter

years = ['2021', '2022', '2023', '2024']
tem_inputs['year'] = tem_inputs['time'].dt.year
obs_data['year'] = obs_data['time'].dt.year
obs_data['season'] = 'winter'
obs_data['month'] = obs_data['time'].dt.month
obs_data['water_year'] = obs_data['time'].dt.year
obs_data.loc[obs_data['month'] >= 10, 'water_year'] = obs_data.loc[obs_data['month'] >= 10, 'water_year'] + 1
obs_data.loc[(obs_data['month']>=7) & (obs_data['month']<=8), 'season'] = 'summer'
obs_data.loc[(obs_data['month']>=4) & (obs_data['month']<=6), 'season'] = 'spring'
obs_data.loc[(obs_data['month']>=9) & (obs_data['month']<=10), 'season'] = 'fall'

obs_data = obs_data.loc[obs_data['water_year'] <2025]

annual_fluxes_bs_mod = df_bs.loc[(df_bs['date']>='2019-01-01') & (df_bs['date']<'2025-01-01')][['date', 'RECO', 'GPP', 'NEE']]
annual_fluxes_bs_mod=annual_fluxes_bs_mod.groupby(by=annual_fluxes_bs_mod['date'].dt.year).sum().reset_index()
annual_fluxes_bs_mod['desc'] = 'black spruce modeled'

annual_fluxes_br_mod = df_br.loc[(df_br['date']>='2019-01-01') & (df_br['date']<'2025-01-01')][['date', 'RECO', 'GPP', 'NEE']]
annual_fluxes_br_mod=annual_fluxes_br_mod.groupby(by=annual_fluxes_br_mod['date'].dt.year).sum().reset_index()
annual_fluxes_br_mod['desc'] = 'birch modeled'

annual_fluxes_rf = BONA_EC_RF.loc[(BONA_EC_RF['MM_YY']>='2019-01-01') & (BONA_EC_RF['MM_YY']<'2025-01-01')][['MM_YY', 'GPP_f', 'Reco', 'NEE_f']]
annual_fluxes_rf = annual_fluxes_rf.groupby(by=annual_fluxes_rf['MM_YY'].dt.year).sum().reset_index()
annual_fluxes_rf['desc'] = 'observed'
annual_fluxes_rf = annual_fluxes_rf.rename(columns={'MM_YY': 'date', 'GPP_f': 'GPP', 
                                                      'Reco':'RECO', 'NEE_f':'NEE'})

annual_flux_comp = pd.concat([annual_fluxes_bs_mod, annual_fluxes_br_mod, annual_fluxes_rf])

fig, axes=plt.subplots(5,1, figsize=(8,7), sharex=True)

sns.barplot(data = annual_flux_comp, x=annual_flux_comp['date'], y='NEE', hue='desc', palette=list(itemgetter(5, 7, 3)(palette)), ax=axes[0],zorder=3)
axes[0].axhline(0,linestyle='--',linewidth=0.8, alpha=0.6, color='black')
sns.barplot(data = annual_flux_comp, x=annual_flux_comp['date'], y='GPP', hue='desc', 
            palette=list(itemgetter(5, 7, 3)(palette)), ax=axes[1],zorder=3, legend=False)
sns.barplot(data = annual_flux_comp, x=annual_flux_comp['date'], y='RECO', hue='desc', 
            palette=list(itemgetter(5, 7, 3)(palette)), ax=axes[2],zorder=3, legend=False)

sns.barplot(data=obs_data_yearly.loc[obs_data_yearly['time']>=2019], 
            x='time', y='precip_sum', ax=axes[3], 
            legend=False, zorder=3, fill=False, linewidth=1, color=palette[1], width=0.4)

sns.boxplot(data=obs_data.loc[obs_data['water_year']>=2019], x='year', y='tair', 
            ax=axes[4],legend=False, color=palette[1], fill=False, linewidth=1, 
            width=0.4,medianprops={"color": "r", "linewidth": 1.5})

minor_locator1 = ticker.MultipleLocator(100)
axes[3].yaxis.set_minor_locator(minor_locator1)
axes[3].grid(which='minor', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6)
axes[3].grid(which='major', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6)

minor_locator2 = ticker.MultipleLocator(10)
axes[4].yaxis.set_minor_locator(minor_locator2)
axes[4].grid(which='minor', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6)
axes[4].grid(which='major', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6)

axes[1].set_ylim(0,750)
axes[2].set_ylim(0,750)

axes[0].set_ylabel('NEE (gC $m^{-2}$)')
axes[1].set_ylabel('GPP (gC $m^{-2}$)')
axes[2].set_ylabel('RECO (gC $m^{-2}$)')
axes[3].set_ylabel('Precip (mm)')
axes[4].set_ylabel(r'$\mathrm{T}_{\mathrm{air}}$ (°C)')
axes[4].set_xlabel('')


axes[0].legend(frameon=False, ncol=3, loc=(0.1,1))

plt.savefig('annual_cumulative_flux_comp.jpg', dpi=300)


from matplotlib import ticker
from operator import itemgetter
import numpy as np

years = ['2021', '2022', '2023', '2024']
tem_inputs['year'] = tem_inputs['time'].dt.year
obs_data['year'] = obs_data['time'].dt.year
obs_data['season'] = 'winter'
obs_data['month'] = obs_data['time'].dt.month
obs_data['water_year'] = obs_data['time'].dt.year
obs_data.loc[obs_data['month'] >= 10, 'water_year'] = obs_data.loc[obs_data['month'] >= 10, 'water_year'] + 1
obs_data.loc[(obs_data['month']>=7) & (obs_data['month']<=8), 'season'] = 'summer'
obs_data.loc[(obs_data['month']>=4) & (obs_data['month']<=6), 'season'] = 'spring'
obs_data.loc[(obs_data['month']>=9) & (obs_data['month']<=10), 'season'] = 'fall'
obs_data = obs_data.loc[obs_data['water_year'] <2025]

annual_fluxes_bs_mod = df_bs.loc[(df_bs['date']>='2019-01-01') & (df_bs['date']<'2025-01-01')][['date', 'RECO', 'GPP', 'NEE']]
annual_fluxes_bs_mod=annual_fluxes_bs_mod.groupby(by=annual_fluxes_bs_mod['date'].dt.year).sum().reset_index()
annual_fluxes_bs_mod['desc'] = 'black spruce modeled'

annual_fluxes_br_mod = df_br.loc[(df_br['date']>='2019-01-01') & (df_br['date']<'2025-01-01')][['date', 'RECO', 'GPP', 'NEE']]
annual_fluxes_br_mod=annual_fluxes_br_mod.groupby(by=annual_fluxes_br_mod['date'].dt.year).sum().reset_index()
annual_fluxes_br_mod['desc'] = 'birch modeled'

annual_fluxes_rf = BONA_EC_RF.loc[(BONA_EC_RF['MM_YY']>='2019-01-01') & (BONA_EC_RF['MM_YY']<'2025-01-01')][['MM_YY', 'GPP_f', 'Reco', 'NEE_f']]
annual_fluxes_rf = annual_fluxes_rf.groupby(by=annual_fluxes_rf['MM_YY'].dt.year).sum().reset_index()
annual_fluxes_rf['desc'] = 'observed'
annual_fluxes_rf = annual_fluxes_rf.rename(columns={'MM_YY': 'date', 'GPP_f': 'GPP', 
                                                      'Reco':'RECO', 'NEE_f':'NEE'})

annual_flux_comp = pd.concat([annual_fluxes_bs_mod, annual_fluxes_br_mod, annual_fluxes_rf])

# Calculate temperature statistics by year
tair_stats = obs_data.loc[obs_data['water_year']>=2019].groupby('year')['tair'].agg([
    ('mean', 'mean'),
    ('min', 'min'),
    ('max', 'max'),
    ('q25', lambda x: x.quantile(0.25)),
    ('q75', lambda x: x.quantile(0.75))
]).reset_index()

fig, axes=plt.subplots(4,1, figsize=(8,6.5), sharex=True)

sns.barplot(data = annual_flux_comp, x=annual_flux_comp['date'], y='NEE', hue='desc', 
            palette=list(itemgetter(5, 7, 3)(palette)), ax=axes[0],zorder=3, width=0.6, gap=0.2)
axes[0].axhline(0,linestyle='--',linewidth=0.8, alpha=0.6, color='black')

sns.barplot(data = annual_flux_comp, x=annual_flux_comp['date'], y='GPP', hue='desc', 
            palette=list(itemgetter(5, 7, 3)(palette)), ax=axes[1],zorder=3, legend=False, width=0.6, gap=0.2)

sns.barplot(data = annual_flux_comp, x=annual_flux_comp['date'], y='RECO', hue='desc', 
            palette=list(itemgetter(5, 7, 3)(palette)), ax=axes[2],zorder=3, legend=False, width=0.6, gap=0.2)

# Combined precipitation and temperature plot
ax_tair = axes[3]
ax_precip = ax_tair.twinx()

# Get categorical positions
precip_data = obs_data_yearly.loc[obs_data_yearly['time']>=2019]
x_positions = np.arange(len(tair_stats))

# Plot temperature with error bars on primary axis using categorical positions
temp_line = ax_tair.errorbar(x_positions, tair_stats['mean'], 
                 yerr=[tair_stats['mean']-tair_stats['min'], tair_stats['max']-tair_stats['mean']],
                 fmt='o-', color=palette[0], linewidth=1.5, markersize=5, 
                 capsize=3, capthick=1.5, zorder=3, label=r'$\mathrm{T}_{\mathrm{air}}$')

# Plot precipitation as bars on secondary axis with semi-transparent blue
precip_bars = sns.barplot(data=precip_data, 
            x='time', y='precip_sum', ax=ax_precip, 
            legend=False, zorder=2, color='#3a619e', alpha=0.3, 
            edgecolor='#3a619e', linewidth=1, width=0.4)

# Set labels and styling (no colored text)
ax_tair.set_ylabel(r'$\mathrm{T}_{\mathrm{air}}$ (°C)')
ax_precip.set_ylabel('Precip (mm)')

# Grid for tair axis
minor_locator2 = ticker.MultipleLocator(10)
ax_tair.yaxis.set_minor_locator(minor_locator2)
ax_tair.grid(which='minor', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6, zorder=1)
ax_tair.grid(which='major', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6, zorder=1)

axes[0].grid(which='major', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6, zorder=1)
axes[1].grid(which='major', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6, zorder=1)
axes[2].grid(which='major', linestyle='--', linewidth='0.6', color='lightgray', alpha=0.6, zorder=1)

# Create legend
from matplotlib.patches import Patch
legend_elements = [
    temp_line,
    Patch(facecolor='#3a619e', edgecolor='#3a619e', alpha=0.3, label='Precip')
]
ax_tair.legend(handles=legend_elements, frameon=False, loc=(0.35,0.78), ncol=2)

axes[1].set_ylim(0,750)
axes[2].set_ylim(0,750)
axes[3].set_ylim(-27,30)
ax_precip.set_ylim(0,650)
axes[0].set_ylabel('NEE (gC $m^{-2}$)')
axes[1].set_ylabel('GPP (gC $m^{-2}$)')
axes[2].set_ylabel('RECO (gC $m^{-2}$)')
axes[3].set_xlabel('')
axes[0].legend(frameon=False, ncol=3, loc=(0.1,1))

plt.tight_layout()
plt.savefig('annual_cumulative_flux_comp.jpg', dpi=300)


#sum over period
annual_flux_comp.groupby(by='desc').sum()


annual_flux_comp_all = pd.concat([annual_flux_comp, annual_fluxes_oneflux])

# Melt to long format, then pivot
annual_flux_long = annual_flux_comp_all.melt(
    id_vars=['desc', 'date'], 
    value_vars=['GPP', 'RECO', 'NEE'],
    var_name='variable',
    value_name='value'
)

# Then pivot with multi-index
result = annual_flux_long.pivot(
    index=['desc', 'variable'], 
    columns='date', 
    values='value'
)
result.round(2)


black_spruce_sum_RECO_modeled = df_bs.loc[(df_bs['date']>='2021-01-01') & (df_bs['date']<'2025-01-01'), 'RECO'].sum()
birch_sum_RECO_modeled = df_br.loc[(df_br['date']>='2021-01-01') & (df_br['date']<'2025-01-01'), 'RECO'].sum()

sum_RECO_obs = BONA_EC_monthly_v3.loc[(BONA_EC_monthly_v3['MM_YY']>='2021-01-01') & 
                                     (BONA_EC_monthly_v3['MM_YY']<'2025-01-01'), 'RECO_NT_VUT_50'].sum()

print(f'black spruce modeled RECO {black_spruce_sum_RECO_modeled}')
print(f'birch modeled RECO {birch_sum_RECO_modeled}')
print(f'EC RECO {sum_RECO_obs}')


black_spruce_sum_GPP_modeled = df_bs.loc[(df_bs['date']>='2021-01-01') & (df_bs['date']<'2025-01-01'), 'GPP'].sum()
birch_sum_GPP_modeled = df_br.loc[(df_br['date']>='2021-01-01') & (df_br['date']<'2025-01-01'), 'GPP'].sum()

sum_GPP_obs = BONA_EC_monthly_v3.loc[(BONA_EC_monthly_v3['MM_YY']>='2021-01-01') & 
                                     (BONA_EC_monthly_v3['MM_YY']<'2025-01-01'), 'GPP_NT_VUT_50'].sum()

print(f'black spruce modeled GPP {black_spruce_sum_GPP_modeled}')
print(f'birch modeled GPP {birch_sum_GPP_modeled}')
print(f'EC GPP {sum_GPP_obs}')


print('cumulative NEE 2021-2024 (gC/m2)\n-------------------------------')

black_spruce_sum_NEE_modeled = df_bs.loc[(df_bs['date']>='2021-01-01') & (df_bs['date']<'2025-01-01'), 'NEE'].sum()
birch_sum_NEE_modeled = df_br.loc[(df_br['date']>='2021-01-01') & (df_br['date']<'2025-01-01'), 'NEE'].sum()

sum_NEE_obs = BONA_EC_monthly_v3.loc[(BONA_EC_monthly_v3['MM_YY']>='2021-01-01') & 
                                     (BONA_EC_monthly_v3['MM_YY']<'2023-01-01'), 'NEE_VUT_50'].sum()

sum_NEE_obs_orig = BONA_EC_monthly_v2.loc[(BONA_EC_monthly_v2['MM_YY']>='2021-01-01') & 
                                     (BONA_EC_monthly_v2['MM_YY']<'2023-01-01'), 'NEE_VUT_50'] *\
                    BONA_EC_monthly_v2.loc[(BONA_EC_monthly_v2['MM_YY']>='2021-01-01') & 
                                     (BONA_EC_monthly_v2['MM_YY']<'2023-01-01'), 'daysinmonth']
sum_NEE_obs_orig = sum_NEE_obs_orig.sum()

print(f'black spruce modeled NEE {black_spruce_sum_NEE_modeled}')
print(f'birch modeled NEE {birch_sum_NEE_modeled}')
print(f'EC NEE v1 {sum_NEE_obs_orig}')
print(f'EC NEE v2 {sum_NEE_obs}')


sum_NEE_obs_v1 = BONA_EC_monthly.loc[(BONA_EC_monthly['MM_YY']>='2021-01-01') & 
                                     (BONA_EC_monthly['MM_YY']<'2023-01-01'), 'NEE_gCm-2']
sum_NEE_obs_v1 = sum_NEE_obs_v1.sum()
print(f'EC NEE original {sum_NEE_obs_v1}')


BONA_EC_monthly


BONA_EC_monthly_v2[['MM_YY', 'NEE_VUT_REF']]


BONA_soil_flux = pd.read_csv('/data/comparison_data/BONA_daily_averaged_soil_flux.csv', parse_dates=['MM_YY', 'Date'])


BONA_soil_flux.head()


fig, axes=plt.subplots(figsize=(8,3))
bs_soil_resp = df_bs.loc[(df_bs['date']>'2019-01-01') & (df_bs['date']<'2025-01-01')]
br_soil_resp = df_br.loc[(df_br['date']>'2019-01-01') & (df_br['date']<'2025-01-01')]
sns.lineplot(data=bs_soil_resp, x='date', y=bs_soil_resp['RH']+bs_soil_resp['RM_root']+bs_soil_resp['RG_root'], label = 'Black Spruce', legend=False, alpha=0.8, color=ever_color)
sns.lineplot(data=br_soil_resp, x='date', y=br_soil_resp['RH']+br_soil_resp['RM_root']+br_soil_resp['RG_root'], label = 'Birch', legend=False, alpha=0.8, color=decid_color)
sns.scatterplot(data=BONA_soil_flux.loc[(BONA_soil_flux['year']==2021) & (BONA_soil_flux['stand']=='black_spruce')], x='Date', y='Flux (gC m2 m-1)', color=ever_color)
sns.scatterplot(data=BONA_soil_flux.loc[(BONA_soil_flux['year']==2021) & (BONA_soil_flux['stand']=='deciduous')], x='Date', y='Flux (gC m2 m-1)', color=decid_color)
sns.scatterplot(data=BONA_soil_flux.loc[BONA_soil_flux['year']==2021], x='Date', y='Flux (gC m2 m-1)', hue='stand')


fig, axes=plt.subplots(figsize=(8,3))
bs_soil_resp = df_bs.loc[(df_bs['date']>'2019-01-01') & (df_bs['date']<'2025-01-01')]
br_soil_resp = df_br.loc[(df_br['date']>'2019-01-01') & (df_br['date']<'2025-01-01')]
sns.lineplot(data=bs_soil_resp, x='date', y=bs_soil_resp['RH'], label = 'Black Spruce', legend=False, alpha=0.8, color=ever_color)
sns.lineplot(data=br_soil_resp, x='date', y=br_soil_resp['RH'], label = 'Birch', legend=False, alpha=0.8, color=decid_color)
sns.scatterplot(data=BONA_soil_flux.loc[(BONA_soil_flux['year']==2021) & (BONA_soil_flux['stand']=='black_spruce')], x='Date', y='Flux (gC m2 m-1)', color=ever_color)
sns.scatterplot(data=BONA_soil_flux.loc[(BONA_soil_flux['year']==2021) & (BONA_soil_flux['stand']=='deciduous')], x='Date', y='Flux (gC m2 m-1)', color=decid_color)
sns.scatterplot(data=BONA_soil_flux.loc[BONA_soil_flux['year']==2021], x='Date', y='Flux (gC m2 m-1)', hue='stand')


rh_br_tr_layer


fig, ax = plt.subplots()

sns.lineplot(data=df_br.loc[(df_br['date']>'2010-01-01') & (df_br['date']<'2024-01-01')], x='date', y='TLAYER_top', label = 'Birch', ax=ax)
sns.lineplot(data=df_bs.loc[(df_bs['date']>'2010-01-01') & (df_bs['date']<'2024-01-01')], x='date', y='TLAYER_top', label = 'Black Spruce', ax=ax)


fig, ax = plt.subplots()

sns.lineplot(data=df_br.loc[(df_br['date']>'2010-01-01') & (df_br['date']<'2025-01-01')], x='date', y='LWC_top', label = 'Birch', ax=ax)
sns.lineplot(data=df_bs.loc[(df_bs['date']>'2010-01-01') & (df_bs['date']<'2025-01-01')], x='date', y='LWC_top', label = 'Black Spruce', ax=ax)


tlayer_bs_tr_df = pd.DataFrame(tlayer_bs_tr)
lwclayer_bs_tr_df = pd.DataFrame(lwclayer_bs_tr)
lwclayer_br_tr_df = pd.DataFrame(lwclayer_br_tr)


sns.lineplot(x=lwclayer_bs_tr_df[1300:].index, y=lwclayer_bs_tr_df[1300:][6])
sns.lineplot(x=lwclayer_bs_tr_df[1300:].index, y=lwclayer_br_tr_df[1300:][6])
#sns.lineplot(x=lwclayer_bs_tr_df[1200:].index, y=lwclayer_bs_tr_df[1200:][1])
#sns.lineplot(x=lwclayer_bs_tr_df[1200:].index, y=lwclayer_b_tr_df[1200:][2])
#sns.lineplot(x=lwclayer_bs_tr_df[1200:].index, y=lwclayer_bs_tr_df[1200:][3])
#sns.lineplot(x=lwclayer_bs_tr_df[1200:].index, y=lwclayer_bs_tr_df[1200:][4])
#sns.lineplot(x=lwclayer_bs_tr_df[1200:].index, y=lwclayer_bs_tr_df[1200:][5])


sns.lineplot(x=tlayer_bs_tr_df[1200:].index, y=tlayer_bs_tr_df[1200:][0])
sns.lineplot(x=tlayer_bs_tr_df[1200:].index, y=tlayer_bs_tr_df[1200:][1])
sns.lineplot(x=tlayer_bs_tr_df[1200:].index, y=tlayer_bs_tr_df[1200:][2])
sns.lineplot(x=tlayer_bs_tr_df[1200:].index, y=tlayer_bs_tr_df[1200:][3])
sns.lineplot(x=tlayer_bs_tr_df[1200:].index, y=tlayer_bs_tr_df[1200:][4])
sns.lineplot(x=tlayer_bs_tr_df[1200:].index, y=tlayer_bs_tr_df[1200:][5])


bs_soil_resp


#AET/PET
et_df = bs_soil_resp[['date','EET','PET', 'RH', 'TRANSPIRATION']]
et_df['cmt'] = 'black spruce'
et_df_br = br_soil_resp[['date','EET','PET', 'RH', 'TRANSPIRATION']]
et_df_br['cmt'] = 'birch'
et_df = pd.concat([et_df,et_df_br])
et_df['ratio'] = et_df['EET']/et_df['PET']

et_df = et_df.merge(obs_data, left_on='date', right_on='time', how='left')

#                                                            


et_df['date_int'] = et_df['date'].astype(int)
et_df['year'] = et_df['date'].dt.year
et_df['month'] = et_df['date'].dt.month


fig, axes=plt.subplots(1,2, figsize=(8,4))

sns.scatterplot(data = et_df, x=et_df['PET']/et_df['precip'],
                y=et_df['EET']/et_df['precip'], 
                style='cmt', legend=False,ax=axes[0],hue='year')

sns.scatterplot(data = et_df, x=et_df['PET']/et_df['precip'],
                y=et_df['EET']/et_df['precip'], 
                style='cmt', legend=False,ax=axes[1], hue='year')

axes[0].set_ylim(0,1.4)
axes[0].set_xlim(0,2)
axes[0].set_ylabel('')
axes[0].set_xlabel('')

axes[1].set_ylim(0,0.2)
axes[1].set_xlim(0,0.75)
axes[1].set_ylabel('')
axes[1].set_xlabel('')

fig.tight_layout()


fig, axes = plt.subplots(2,1, sharex=True)
sns.lineplot(data = et_df, x='month',y=et_df['PET']/et_df['precip'],
                style='cmt', legend=False, hue='year', ax=axes[0])

sns.scatterplot(data = et_df, x='month',y=et_df['PET']/et_df['precip'],
                style='cmt', legend=False, hue='year', ax=axes[0])

axes[0].set_yscale('log')

sns.lineplot(data = et_df, x='month',y=et_df['EET']/et_df['precip'],
                style='cmt', legend=False, hue='year', ax=axes[1])

sns.scatterplot(data = et_df, x='month',y=et_df['EET']/et_df['precip'],
                style='cmt', legend=False, hue='year', ax=axes[1])

axes[1].set_yscale('log')
#plt.ylim(0,2)


et_df=et_df.groupby(by=['cmt', et_df['date'].dt.year]).agg({'RH': 'sum',
                                                            'EET':'sum',
                                                            'PET':'sum',
                                                            'TRANSPIRATION':'sum',
                                                        'precip':'sum'}).reset_index()
annual_flux_comp['cmt'] = ''
annual_flux_comp.loc[annual_flux_comp['desc']=='black spruce modeled', 'cmt'] = 'black spruce'
annual_flux_comp.loc[annual_flux_comp['desc']=='birch modeled', 'cmt'] = 'birch'

et_df=et_df.merge(annual_flux_comp, on = ['date','cmt'], how='left')


et_df


fig, ax = plt.subplots(figsize=(8,4))
sns.scatterplot(data=et_df, x=et_df['PET']/et_df['precip'],
                y=et_df['EET']/et_df['precip'], 
                style='cmt', hue='date', size='NEE')
ax.set_ylabel('AET/P')
ax.set_xlabel('PET/P')

# Get handles and labels
handles, labels = ax.get_legend_handles_labels()

# Find indices where each group starts
date_start = labels.index('date')
nee_start = labels.index('NEE')
cmt_start = labels.index('cmt')

# Extract each group
date_h = handles[date_start:nee_start]
date_l = labels[date_start:nee_start]

nee_h = handles[nee_start:cmt_start]
nee_l = labels[nee_start:cmt_start]

cmt_h = handles[cmt_start:]
cmt_l = labels[cmt_start:]

# Pad to same length
from matplotlib.patches import Rectangle
empty = Rectangle((0,0), 0, 0, alpha=0)
max_len = max(len(date_l), len(nee_l), len(cmt_l))

date_h += [empty] * (max_len - len(date_h))
date_l += [''] * (max_len - len(date_l))

nee_h += [empty] * (max_len - len(nee_h))
nee_l += [''] * (max_len - len(nee_l))

cmt_h += [empty] * (max_len - len(cmt_h))
cmt_l += [''] * (max_len - len(cmt_l))

# Stack groups vertically: all of date, then all of nee, then all of cmt
new_handles = date_h + nee_h + cmt_h
new_labels = date_l + nee_l + cmt_l

# Use ncol=3 and it will fill row-wise, creating 3 columns
ax.legend(new_handles, new_labels, frameon=False, loc=(1,0.5), ncol=3, columnspacing=1.5)

fig.tight_layout()
plt.savefig('buddyko_by_year.jpg', dpi=300)


#fig, axes = plt.subplots(3,1,figsize=(5,3), sharex=True)#

#sns.barplot(data=et_df, x='date', y=et_df['ratio'], legend=True, 
#            alpha=0.8, ax = axes[0], hue='cmt')

#sns.barplot(data=et_df, x='date', y=et_df['RH'], legend=False, 
#            alpha=0.8, ax = axes[1], hue='cmt')

#sns.barplot(data=et_df, x='date', y=et_df['TRANSPIRATION'], legend=False, 
#            alpha=0.8, ax = axes[2], hue='cmt')

#axes[1].set_xlabel('')
#axes[0].legend(ncol=2, frameon=False, loc=(0.1,1))





fig, ax = plt.subplots()
ax2=ax.twinx()
sns.lineplot(data=bs_soil_resp, x='date', y=bs_soil_resp['TRANSPIRATION'], label = 'Trans', legend=False, alpha=0.8, color=decid_color, ax = ax)
sns.lineplot(data=bs_soil_resp, x='date', y=bs_soil_resp['LAI'], label = 'LAI', alpha=0.8, ax = ax2)


sns.lineplot(data=df_bs, x='date', y=df_bs['LAI'], label = 'LAI', alpha=0.8)
plt.xlim(pd.to_datetime('2010-01-01'), pd.to_datetime('2025-01-01'))


sns.lineplot(x=np.arange(len(lai_bs_tr)), y=lai_bs_tr[:,3])


fig, ax = plt.subplots(figsize=(10,5))
ax2=ax.twinx()
sns.lineplot(data=bs_soil_resp, x='date', y=bs_soil_resp['RH'], label = 'RH', legend=False, alpha=0.8, color=decid_color, ax = ax)
sns.lineplot(data=bs_soil_resp, x='date', y=bs_soil_resp['EET'], label = 'EET', alpha=0.8, ax = ax2)
plt.xticks(rotation = 90)


fig, ax = plt.subplots()
ax2=ax.twinx()
sns.lineplot(data=bs_soil_resp, x='date', y=bs_soil_resp['RH'], label = 'RH', legend=False, alpha=0.8, color=decid_color, ax = ax)
sns.lineplot(data=ltrfalc_bs_tr.loc[ltrfalc_bs_tr['time']>'1990-01-01'], x='time', y='LTRFALC', ax=ax2, label='litter')


fig, ax = plt.subplots()
ax2=ax.twinx()
sns.lineplot(data=bs_soil_resp, x='date', y=bs_soil_resp['RH'], label = 'RH', alpha=0.8, color=decid_color, ax = ax)
sns.lineplot(data=shlwc_bs_tr.loc[shlwc_bs_tr['time']>'2021-01-01'], x='time', y='SHLWC', ax=ax2, label='SHLWC')


sns.lineplot(data=df_br.loc[(df_br['date']>'2010-01-01') & (df_br['date']<'2024-01-01')], x='date', y='RH')
sns.scatterplot(data=df_br.loc[(df_br['date']>'2010-01-01') & (df_br['date']<'2024-01-01')], x='date', y='RH', hue = 'LWC_top')


sns.scatterplot(data=df_br.loc[(df_br['date']>'2010-01-01') & (df_br['date']<'2024-01-01')], x='LWC_top', y='RH', label = 'Birch', hue='TLAYER_top')


sns.scatterplot(data=df_bs.loc[(df_bs['date']>'2010-01-01') & (df_bs['date']<'2024-01-01')], x='TLAYER_top', y='RH', label = 'Birch', hue='LWC_top')


sns.scatterplot(data=df_br.loc[(df_br['date']>'2010-01-01') & (df_br['date']<'2024-01-01')], x='LWC_top', y='RH', label = 'Birch', color='#708891')


df_yearly_melt = df_yearly[['year', 'GPP', 'RECO', 'NEE', 'CMT']].melt(id_vars=['year', 'CMT'], value_vars=['GPP', 'RECO', 'NEE', 'CMT'])
df_yearly_melt.loc[df_yearly_melt['variable']=='RECO', 'variable'] = 'Reco'
df_yearly_melt['order'] = 0
df_yearly_melt.loc[df_yearly_melt['variable']=='Reco', 'order'] = 1
df_yearly_melt.loc[df_yearly_melt['variable']=='NEE', 'order'] = 2
df_yearly_melt = df_yearly_melt.sort_values(by='order')


df_yearly_melt.head()


pal = sns.color_palette(['#35B779FF', '#2A788EFF'])

fig, ax = plt.subplots()
sns.boxplot(data = df_yearly_melt.loc[df_yearly_melt['year']>=2010], x='variable', y='value', hue='CMT', palette = pal)

ax.set_ylabel('Flux (gC$m^{-2}$$y^{-1}$)', fontsize=18)
ax.set_xlabel('')
ax.tick_params(axis='x', labelsize=18)
ax.tick_params(axis='y', labelsize=18)
ax.legend(title='', fontsize=14, frameon=False)
fig.tight_layout()
plt.savefig('output_figs/BONA/flux_boxplot.jpg', dpi=300)


df_yearly_melt.groupby(by=['CMT', 'variable']).mean()


df_yearly_melt.groupby(by=['CMT', 'variable']).std()


#sns.set_palette(sns.color_palette("Greys",2))
fig, axes=plt.subplots(3,1,figsize=(8,5))
sns.lineplot(data=df_bs_yearly, x='year', y='GPP', ax=axes[0], label = 'Black Spruce', color=ever_color)
sns.lineplot(data=df_br_yearly, x='year', y='GPP', ax=axes[0], label = 'Deciduous', color=decid_color)
sns.lineplot(data=df_bs_yearly, x='year', y='RECO', ax=axes[1], color=ever_color)
sns.lineplot(data=df_br_yearly, x='year', y='RECO', ax=axes[1], color=decid_color)
sns.lineplot(data=df_bs_yearly, x='year', y='NEE', ax=axes[2], color=ever_color)
sns.lineplot(data=df_br_yearly, x='year', y='NEE', ax=axes[2], color=decid_color)

axes[0].xaxis.set_tick_params(labelbottom=False)
axes[1].xaxis.set_tick_params(labelbottom=False)
axes[0].set_xlabel('')
axes[1].set_xlabel('')
axes[0].set_ylabel('GPP\n(g C $m^{-2}$ $y^{-1}$)')
axes[1].set_ylabel('RECO\n(g C $m^{-2}$ $y^{-1}$)')
axes[2].set_ylabel('NEE\n(g C $m^{-2}$ $y^{-1}$)')
plt.xlabel('')
fig.tight_layout()
plt.savefig('output_figs/BONA/yearly_fluxes.jpg', dpi=300)


df_yearly.columns


sns.lineplot(data=df_yearly, x='year', y='ALD', hue='CMT')
#plt.ylim(0,1)


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
#sns.set_palette(sns.color_palette(['#708891', '#E0DAD0']))
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


fig, ax=plt.subplots(figsize=(8,5))
#sns.set_palette(sns.color_palette(['#708891', '#E0DAD0']))
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


a = 'sdaf/adfadsfa/asdfa/fs.tif'
b = '/'.join(a.split('/')[:-1]) + '/fused_landcover.tif'
b


df_bs[['date', 'GPP', 'NPP', 'RH', 'RECO', 'NEE']].to_csv('BONA_Black_Spruce_flux_hist.csv')


df_br[['date', 'GPP', 'NPP', 'RH', 'RECO', 'NEE']].to_csv('BONA_Birch_flux_hist.csv')
















