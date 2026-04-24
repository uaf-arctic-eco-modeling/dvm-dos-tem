#!/usr/bin/env python
# coding: utf-8

import sys
# caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(1, '/work/scripts/util')
from output import load_trsc_dataframe, build_full_datetimeindex


import netCDF4 as nc
import numpy as np
from matplotlib import pyplot as plt
import os
import json
import pandas as pd
import seaborn as sns
import xarray as xr
from output import load_trsc_dataframe
import seaborn as sns


palette = sns.color_palette(['#4B519B','#2E2427','#3E7274','#416114','#82710D','#114131','#1E7256', '#30B589','#266797'])


cell_y_coord=0
cell_x_coord=0


#model run level information

data_paths=['/data/workflows/BONA-black-spruce-fire-control/output/',
            '/data/workflows/BONA-black-spruce-fire-1930/output/',
            '/data/workflows/BONA-black-spruce-fire-1960/output/',
            '/data/workflows/BONA-black-spruce-fire-1990/output/',
            '/data/workflows/BONA-black-spruce-fire-2030/output/',
            '/data/workflows/BONA-birch-fire-control/output/',
            '/data/workflows/BONA-birch-fire-1930/output/',
            '/data/workflows/BONA-birch-fire-1960/output/',
            '/data/workflows/BONA-birch-fire-1990/output/',
            '/data/workflows/BONA-birch-fire-2030/output/'
           ]

#data_paths=['/data/workflows/BONA-black-spruce-fire-control-nfix/output/',
#            '/data/workflows/BONA-black-spruce-fire-1930-nfix/output/',
#            '/data/workflows/BONA-black-spruce-fire-1960-nfix/output/',
#            '/data/workflows/BONA-black-spruce-fire-1990-nfix/output/',
#            '/data/workflows/BONA-birch-fire-control-nfix/output/',
#            '/data/workflows/BONA-birch-fire-1930-nfix/output/',
#            '/data/workflows/BONA-birch-fire-1960-nfix/output/',
#            '/data/workflows/BONA-birch-fire-1990-nfix/output/'
#           ]

#data_paths=['/data/workflows/BONA-black-spruce-fire-control-rhmoist/output/',
#            '/data/workflows/BONA-black-spruce-fire-1930-rhmoist/output/',
#            '/data/workflows/BONA-black-spruce-fire-1960-rhmoist/output/',
#            '/data/workflows/BONA-black-spruce-fire-1990-rhmoist/output/',
#            '/data/workflows/BONA-birch-fire-control-rhmoist/output/',
#            '/data/workflows/BONA-birch-fire-1930-rhmoist/output/',
#           '/data/workflows/BONA-birch-fire-1960-rhmoist/output/',
#            '/data/workflows/BONA-birch-fire-1990-rhmoist/output/'
#           ]

exp = ['control', 
       'burn_1930', 
       'burn_1960', 
       'burn_1990',
       'burn_2030',
       'control', 
       'burn_1930', 
       'burn_1960', 
       'burn_1990',
       'burn_2030']

cmt = ['black_spruce', 
       'black_spruce', 
       'black_spruce', 
       'black_spruce',
       'black_spruce',
       'birch', 
       'birch', 
       'birch', 
       'birch',
       'birch']

pfts = {'black_spruce': ['Black Spruce', 'Decid. Shrub', 'Evr. Shrub', 'Moss', 'Lichen'],
        'birch': ['White Spruce', 'Decid. Shrub', 'Birch', 'Moss', 'Evr. Shrub']}

burn_year = [1900, 
             1930, 
             1960, 
             1990,
             2030,
             1900, 
             1930, 
             1960, 
             1990,
             2030]

#variable-level information, assuming same outputs from each model run
var_list = ['GPP', 
            'NPP', 
            'RH', 
            'RG', 
            'RM',
            'LTRFALC',
            'SHLWC',
            'VEGC',
            'DEEPC',
            'MINEC',
            'AVLN',
            'ORGN',
            'ALD',
            'SHLWDZ',
            'DEEPDZ',
            'WATERTAB',
            'EET',
            'PET',
            'SOMA',
            'SOMCR',
            'SOMPR',
            'SOMRAWC',
            'BURNVEG2AIRC',
            'BURNSOIC',
            'GROWSTART',
            'GROWEND',
            'YSD'
           ]

timeres = ['monthly', 
           'monthly', 
           'monthly', 
           'monthly',
           'monthly', 
           'monthly',
           'monthly',
           'monthly',
           'yearly',
           'yearly',
           'yearly',
           'yearly',
           'yearly',
           'yearly',
           'yearly',
           'yearly',
           'yearly',
           'yearly',
           'yearly',
           'yearly',
           'yearly',
           'yearly',
           'yearly',
           'yearly',
           'yearly',
           'yearly',
           'yearly'
            ]

year_agg = ['sum', 
               'sum', 
               'sum', 
               'sum', 
               'sum',
               'sum',
               'mean',
               'mean',
               'mean',
               'mean',
               'mean',
               'mean',
               'mean',
               'mean',
               'mean',
               'mean',
               'mean',
               'mean',
               'mean',
               'mean',
               'mean',
               'mean',
               'sum', 
               'sum',
               'sum', 
               'sum',
               'sum'
                ]

detail = ['cmt', 
          'cmt', 
          'cmt', 
          'cmt', 
          'cmt',
          'cmt',
          'cmt',
          'pft',
          'cmt',
          'cmt',
          'cmt',
          'cmt',
          'cmt',
          'cmt',
          'cmt',
          'cmt',
          'cmt',
          'cmt',
          'cmt',
          'cmt',
          'cmt',
          'cmt',
          'cmt',
          'cmt',
          'cmt',
          'cmt',
          'cmt'
         ]


def get_monthly_data(data_path, var, cell_y_coord=0, cell_x_coord=0, year_agg='mean'):
    
    df_monthly = load_trsc_dataframe(var=var, timeres='monthly', px_y=cell_y_coord, px_x=cell_x_coord, fileprefix=data_path, stages=['tr', 'sc'])[0].reset_index()
    df_monthly.columns = ['time', var]
    df_monthly['time'] = pd.to_datetime(df_monthly['time'])
    df_monthly['year'] = df_monthly['time'].dt.year

    if year_agg == 'mean':
        df_yearly = df_monthly[['year', var]].groupby(by='year').mean()
        
    if year_agg == 'sum':
        df_yearly = df_monthly[['year', var]].groupby(by='year').sum()
    
    return df_monthly, df_yearly


def get_yearly_data(data_path, var, cell_y_coord=0, cell_x_coord=0):
    
    df_yearly = load_trsc_dataframe(var=var, timeres='yearly', px_y=cell_y_coord, px_x=cell_x_coord, fileprefix=data_path, stages=['tr', 'sc'])[0].reset_index()
    df_yearly.columns = ['time', var]
    df_yearly['time'] = pd.to_datetime(df_yearly['time'])
    df_yearly['year'] = df_yearly['time'].dt.year
    
    return df_yearly


def get_monthly_data_part(data_path, var, pfts, cell_y_coord=0, cell_x_coord=0, year_agg='mean'):
    
    #df_monthly = xr.open_dataset(data_path+var+'_monthly_tr.nc')
    #df_monthly = df_monthly.convert_calendar('standard', use_cftime=False, align_on='date')
    #df_monthly = df_monthly.to_dataframe().reset_index()
    
    df_monthly = load_trsc_dataframe(var=var, timeres='monthly', px_y=cell_y_coord, px_x=cell_x_coord, fileprefix=data_path, stages=['tr', 'sc'])[0].reset_index()
    #df_monthly = df_monthly.loc[(df_monthly['y']==cell_y_coord) & (df_monthly['x']==cell_x_coord) & (df_monthly['pft']<5)]
    print(df_monthly)
    df_monthly = df_monthly[['index', 0, 1, 2, 3, 4]]
    df_monthly = df_monthly[['time','pft', 'pftpart', var]]
    df_monthly['year'] = df_monthly['time'].dt.year
    
    
    
    if year_agg== 'mean':
        df_yearly = df_monthly.groupby(by=['year', 'pft', 'pftpart']).mean().reset_index()
    
    if year_agg== 'sum':
        df_yearly = df_monthly.groupby(by=['year', 'pft', 'pftpart']).sum().reset_index()

    return df_monthly, df_yearly


def get_monthly_data_pft(data_path, var, pfts, cell_y_coord=0, cell_x_coord=0, year_agg='mean'):
    
    df_monthly = load_trsc_dataframe(var=var, timeres='monthly', px_y=cell_y_coord, px_x=cell_x_coord, fileprefix=data_path, stages=['tr', 'sc'])[0].reset_index()
    
    df_monthly = df_monthly[['index', 0, 1, 2, 3, 4]]
    df_monthly.columns = ['time']+pfts
    df_monthly['time'] = pd.to_datetime(df_monthly['time'])
    df_monthly['year'] = df_monthly['time'].dt.year
    
    if year_agg== 'mean':
        df_yearly = df_monthly[['year']+pfts].groupby(by='year').mean().reset_index()
    
    if year_agg== 'sum':
        df_yearly = df_monthly[['year']+pfts].groupby(by='year').sum().reset_index()

    return df_monthly, df_yearly


depthlist = [0.08, 0.1, 0.2, 0.3, 0.4, 0.5]

def get_lwclayer_tlayer(depthlist, run_dir, var):
    
    reference_date_2016 = pd.Timestamp('2016-01-01')
    reference_date_2022 = pd.Timestamp('2022-01-01')
    delta = (reference_date_2022 - reference_date_2016)
    
    ### read the netcdf output files and compute year from the time dimension
    data = xr.open_dataset(f'{run_dir}/output/{var}_yearly_tr.nc')
    data = data.to_dataframe()
    data = data.reset_index()
    
    data_sc=xr.open_dataset(f'{run_dir}/output/{var}_yearly_sc.nc')
    data_sc = data_sc.to_dataframe()
    data_sc = data_sc.reset_index()
    data_sc['time'] = data_sc['time'] + delta
    data=pd.concat([data, data_sc], axis=0)
    
    
    
    data = data.reset_index(drop=True)

    data.dtypes
    data['time'] = data['time'].astype('|S80')
    data['time'] = data['time'].astype('|datetime64[ns]')
    data['month'] = data['time'].dt.month
    data['year'] = data['time'].dt.year
    data = data.sort_values(['time','x','y','layer'])


    ### read the netcdf output files on soil structure and compute year from the time dimension
    dz = xr.open_dataset(f'{run_dir}/output/LAYERDZ_yearly_tr.nc')
    dz = dz.to_dataframe()
    dz= dz.reset_index()
    
    dz_sc = xr.open_dataset(f'{run_dir}/output/LAYERDZ_yearly_sc.nc')
    dz_sc = dz_sc.to_dataframe()
    dz_sc= dz_sc.reset_index()
    dz_sc['time'] = dz_sc['time'] + delta
    
    dz=pd.concat([dz, dz_sc])

    # Assign the new time coordinate back to the dataset
    dz = dz.reset_index()
    
    dz.reset_index(inplace=True)
    dz.dtypes
    dz['time'] = dz['time'].astype('|S80')
    dz['time'] = dz['time'].astype('|datetime64[ns]')
    dz['month'] = dz['time'].dt.month
    dz['year'] = dz['time'].dt.year
    dz = dz.sort_values(['time','x','y','layer'])

    ### read the netcdf output files on soil structure and compute year from the time dimension
    lt = xr.open_dataset(f'{run_dir}/output/LAYERTYPE_yearly_tr.nc')
    lt = lt.to_dataframe()
    lt = lt.reset_index()
    
    lt_sc = xr.open_dataset(f'{run_dir}/output/LAYERTYPE_yearly_sc.nc')
    lt_sc = lt_sc.to_dataframe()
    lt_sc = lt_sc.reset_index()
    lt_sc['time'] = lt_sc['time'] + delta
    
    lt=pd.concat([lt, lt_sc], axis=0)
    
    
    lt = lt.reset_index(drop=True)
    
    lt.reset_index(inplace=True)
    lt.dtypes
    lt['time'] = lt['time'].astype('|S80')
    lt['time'] = lt['time'].astype('|datetime64[ns]')
    #lt['month'] = lt['time'].dt.month
    lt['year'] = lt['time'].dt.year
    lt = lt.sort_values(['time','x','y','layer'])
    dz=pd.merge(dz, lt[['LAYERTYPE', 'time', 'x', 'y', 'layer']], on=['time','x','y','layer'])


    ### compute the depth of the bottom of every layers
    dz['z'] = dz.groupby(['time','x','y'])['LAYERDZ'].cumsum(axis=0)
    
    ### loop through the list of depths of reference to compute the soil variable at that depth via linear interpolation
    stdz = []
    for i in range(len(depthlist)):
        dpth = depthlist[i]
        print("depth:", dpth,"m")
        # extract the top and bottom layers the closest to the depth of reference
        dz['diff'] = dz['z']-float(dpth)
        top = dz.loc[dz[(dz['diff'] <= 0)].groupby(['time','x','y'])['diff'].idxmax()]
        bot = dz.loc[dz[(dz['diff'] >= 0)].groupby(['time','x','y'])['diff'].idxmin()]
        # select the variable value for each of these top and bottom layers
        datatop = pd.merge(data, top[['year','month', 'x','y','layer','LAYERDZ','LAYERTYPE','z']], how="left", on=['layer','year','month', 'x','y'])
        datatop = datatop[datatop['z'].notna()]
        datatop = datatop.rename(columns={"layer": "layertop", var: var+"top", "LAYERDZ": "dztop", "z": "ztop", "LAYERTYPE": "typetop"})
        databot = pd.merge(data, bot[['year', 'month', 'x','y','layer','LAYERDZ','LAYERTYPE','z']], how="left", on=['layer','year','month' , 'x','y'])
        databot = databot[databot['z'].notna()]
        databot = databot.rename(columns={"layer": "layerbot", var: var+"bot", "LAYERDZ": "dzbot", "z": "zbot", "LAYERTYPE": "typebot"})
        # merge the data to do the linear interpolation
        datastdz = pd.merge(datatop, databot, how="outer", on=['time','year', 'month', 'x','y'])
        datastdz['a'] = (datastdz[var+"top"] - datastdz[var+"bot"]) / (datastdz['ztop'] - datastdz['zbot'])
        datastdz['b'] = datastdz[var+"top"] - (datastdz['a'] * datastdz['ztop'])
        datastdz[var] = (datastdz['a'] * float(dpth)) + datastdz['b']
        datastdz[var+'_top'] = datastdz[var+"top"]
        datastdz[var+'_bot'] = datastdz[var+"bot"]
        datastdz['z'] = float(dpth)
        datastdz['layer'] = i
        datastdz['type'] = datastdz['typebot']
        datastdz = datastdz[['time','year', 'x','y','layer','z','type',var, var+'_top', var+'_bot']]
        stdz.append(datastdz)

    stdz = pd.concat(stdz)
    
    return stdz


lwc_layers = []
t_layers = []

for i, d in enumerate(data_paths):
    if 'GPP_monthly_tr.nc' in os.listdir(d):
        d='/'.join(d.split('/')[:-2])
        print(d)

        TLAYER = load_trsc_dataframe(var ='TLAYER', timeres='yearly', px_y=cell_y_coord, px_x=cell_x_coord, fileprefix=f'{d}/output/', stages=['tr', 'sc'])[0]
        LAYERDEPTH = load_trsc_dataframe(var ='LAYERDEPTH', timeres='yearly', px_y=cell_y_coord, px_x=cell_x_coord, fileprefix=f'{d}/output/', stages=['tr', 'sc'])[0]
        LAYERDZ = load_trsc_dataframe(var ='LAYERDZ', timeres='yearly', px_y=cell_y_coord, px_x=cell_x_coord, fileprefix=f'{d}/output/', stages=['tr', 'sc'])[0]
        
        LWCLAYER = get_lwclayer_tlayer(depthlist, d, 'VWCLAYER')
        LWCLAYER['exp'] = exp[i]
        LWCLAYER['cmt'] = cmt[i]
        lwc_layers.append(LWCLAYER)
        
        TLAYER = get_lwclayer_tlayer(depthlist, d, 'TLAYER')
        TLAYER['exp'] = exp[i]
        TLAYER['cmt'] = cmt[i]
        t_layers.append(TLAYER)
        
lwc_layers=pd.concat(lwc_layers)
t_layers=pd.concat(t_layers)


t_layer_lwc_layer = lwc_layers[['cmt', 'exp', 'time','z','VWCLAYER']].merge(t_layers[['cmt', 'exp', 'time','z','TLAYER']], on = ['cmt','exp','time','z'])


t_layer_lwc_layer.to_csv('output_files/soil_moisture_temperature_TEM.csv', index=False)
t_layer_lwc_layer.loc[t_layer_lwc_layer['cmt']=='black_spruce'].to_csv('output_files/soil_moisture_temperature_TEM_outputs_black_spruce.csv', index=False)
t_layer_lwc_layer.loc[t_layer_lwc_layer['cmt']=='birch'].to_csv('output_files/soil_moisture_temperature_TEM_outputs_birch.csv', index=False)


def create_df_for_var(data_paths, exps, cmts, burn_year, var, timeres, detail, year_agg=None, pfts=None):
    
    dfs_monthly=[]
    dfs_yearly=[]
    
    for i, data_path in enumerate(data_paths):
        if timeres=='monthly':
            
            if detail=='pft':
                df_monthly, df_yearly = get_monthly_data_pft(data_path, var, pfts[cmts[i]], 
                                                             cell_y_coord=0, cell_x_coord=0, year_agg=year_agg)
                
                df_monthly = df_monthly.melt(id_vars=['time', 'year'])
                df_monthly.columns = ['time', 'year', 'pft', var]
                
                df_yearly = df_yearly.melt(id_vars=['year'])
                df_yearly.columns = ['year', 'pft', var]
                
            if detail=='part':
                df_monthly, df_yearly = get_monthly_data_part(data_path, var, pfts[cmts[i]], 
                                                             cell_y_coord=0, cell_x_coord=0, year_agg=year_agg)
                
                #print(df_monthly.head())
                #df_monthly = df_monthly.melt(id_vars=['time', 'year'])
                #print(df_monthly.head())
                #df_monthly.columns = ['time', 'year', 'pft', 'pftpart', var]
                
                #df_yearly = df_yearly.melt(id_vars=['year'])
                #df_yearly.columns = ['year', 'pft', 'pftpart', var]
                
            if detail=='cmt':
                df_monthly, df_yearly = get_monthly_data(data_path, var, year_agg=year_agg)
        
            df_monthly['exp'] = exps[i]
            df_monthly['cmt'] = cmts[i]
            df_monthly['burn_year'] = burn_year[i]
        
        if timeres=='yearly':
            df_yearly=get_yearly_data(data_path, var)
            df_monthly=pd.DataFrame(columns = ['time', 'year', 'pft', var, 'exp', 'cmt', 'burn_year'])
            
        df_yearly['exp'] = exps[i]
        df_yearly['cmt'] = cmts[i]
        df_yearly['burn_year'] = burn_year[i]

        dfs_monthly.append(df_monthly)
        dfs_yearly.append(df_yearly)
            
    dfs_monthly = pd.concat(dfs_monthly)
    dfs_yearly = pd.concat(dfs_yearly)
    
    return dfs_monthly, dfs_yearly


#get monthly data, not defined by pft

results_monthly = pd.DataFrame()
results_yearly = pd.DataFrame()

results_monthly_pft = pd.DataFrame()
results_yearly_pft = pd.DataFrame()

results_monthly_part = pd.DataFrame()
results_yearly_part = pd.DataFrame()

for i, var in enumerate(var_list):
    print(var)
    print(detail[i])
    var_monthly, var_yearly = create_df_for_var(data_paths, exp, cmt, burn_year, var, timeres[i], detail[i], year_agg[i], pfts)
        
    if (detail[i] == 'pft'):
        
        if len(results_monthly_pft)==0:

            results_monthly_pft = var_monthly
            results_yearly_pft = var_yearly
            
        else:
            if len(var_monthly)>0:
                results_monthly_pft = pd.merge(results_monthly_pft, var_monthly, on=['time', 'year', 'exp', 'cmt', 'burn_year', 'pft'])
            results_yearly_pft = pd.merge(results_yearly_pft, var_yearly, on=['year', 'exp', 'cmt', 'burn_year', 'pft'])
            
    if (detail[i] == 'part'):
         
        if len(results_monthly_part)==0:

            results_monthly_part = var_monthly
            results_yearly_part = var_yearly
               
        else:
            if len(var_monthly)>0:
                results_monthly_part = pd.merge(results_monthly_part, var_monthly, on=['time', 'year', 'exp', 'cmt', 'burn_year', 'pft', 'pftpart'])
            results_yearly_part = pd.merge(results_yearly_part, var_yearly, on=['year', 'exp', 'cmt', 'burn_year', 'pft', 'pftpart'])
         
    if (detail[i] == 'cmt'):
        
        if len(results_monthly)==0:

            results_monthly = var_monthly
            results_yearly = var_yearly
            
        else:
            if len(var_monthly)>0:
                results_monthly = pd.merge(results_monthly, var_monthly, on=['time', 'year', 'exp', 'cmt', 'burn_year'])
            results_yearly = pd.merge(results_yearly, var_yearly, on=['year', 'exp', 'cmt', 'burn_year'])
            
results_yearly = results_yearly.reset_index()


xr.open_dataset('/data/workflows/BONA-black-spruce-fire-control/output/GPP_monthly_tr.nc')





results_monthly.columns


results_monthly['RECO'] = results_monthly['RH'] + results_monthly['RG'] + results_monthly['RM']
results_monthly['NEE'] = results_monthly['RECO'] - results_monthly['GPP']
results_monthly_out = results_monthly[['cmt','exp','time','GPP','RECO','NEE','NPP','RH','RG','RM','LTRFALC','SHLWC']]
results_monthly_out.to_csv('output_files/monthly_TEM_outputs.csv', index=False)
results_monthly_out.loc[results_monthly_out['cmt']=='black_spruce'].to_csv('output_files/monthly_TEM_outputs_black_spruce.csv', index=False)
results_monthly_out.loc[results_monthly_out['cmt']=='birch'].to_csv('output_files/monthly_TEM_outputs_birch.csv', index=False)





if len(results_yearly_part>0):
    results_yearly_pft = results_yearly_part.groupby(by=['burn_year', 'cmt', 'exp', 'year', 'pft']).sum().reset_index()
results_yearly_pft['pft'] = results_yearly_pft['pft'].apply(str)
results_yearly_pft





hist_inputs = xr.open_dataset('/data/input-catalog/cpcrw_towers_downscaled/historic-climate_time_fixed.nc').squeeze()
proj_inputs = xr.open_dataset('/data/input-catalog/cpcrw_towers_downscaled/projected-climate_CC_CCSM4_85_Pa_time_fixed.nc').squeeze()

hist_inputs.squeeze()
hist_inputs = hist_inputs.convert_calendar('standard', use_cftime=True, align_on='date')
hist_inputs = hist_inputs.to_pandas().reset_index()
hist_inputs['time'] = hist_inputs['time'].astype(str)
hist_inputs['time'] = pd.to_datetime(hist_inputs['time'])
hist_inputs_annual = hist_inputs.groupby(by=hist_inputs['time'].dt.year).agg({'tair':['mean','std'],
                                                                                    'nirr': ['mean','std'],
                                                                                    'precip': 'sum',
                                                                                    'vapor_press': ['mean','std']}).reset_index()
proj_inputs.squeeze()
proj_inputs = proj_inputs.convert_calendar('standard', use_cftime=True, align_on='date')
proj_inputs = proj_inputs.to_pandas().reset_index()
proj_inputs['time'] = proj_inputs['time'].astype(str)
proj_inputs['time'] = pd.to_datetime(proj_inputs['time'])
proj_inputs_annual = proj_inputs.groupby(by=proj_inputs['time'].dt.year).agg({'tair':['mean','std'],
                                                                                    'nirr': ['mean','std'],
                                                                                    'precip': 'sum',
                                                                                    'vapor_press': ['mean','std']}).reset_index()


hist_inputs_annual.columns = ['year','tair_mean', 'tair_std', 'nirr_mean', 'nirr_std', 
                              'precip_sum', 'vapor_press_mean', 'vapor_press_std']

proj_inputs_annual.columns = ['year','tair_mean', 'tair_std', 'nirr_mean', 'nirr_std', 
                              'precip_sum', 'vapor_press_mean', 'vapor_press_std']


tem_inputs = pd.concat([hist_inputs_annual, proj_inputs_annual])
tem_inputs.to_csv('TEM_inputs_hist_proj_RCP8-5.csv')


results_yearly['RECO'] = results_yearly['RG'] + results_yearly['RM'] + results_yearly['RH']
results_yearly['NEE'] = results_yearly['RECO'] - results_yearly['GPP']
results_yearly['years_since_fire'] = results_yearly['year'] - results_yearly['burn_year']
#results_yearly = results_yearly.loc[(results_yearly['exp']=='burn_1930') | (results_yearly['exp']=='control')]


fig, axes = plt.subplots(3,2, figsize=(8,8), sharex=True)


sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], x='year', y='GPP', hue='exp', ax=axes[0][0], alpha=0.7)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], x='year', y='RH', hue='exp', ax=axes[1][0], legend=False, alpha=0.7)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], x='year', y='NEE', hue='exp', ax=axes[2][0], legend=False, alpha=0.7)

axes[0][0].set_title('Black Spruce')
axes[0][0].set_ylabel('GPP (gC/m2/yr)')

new_labels = ['control', '1930', '1960', '1990', '2030']
legend=axes[0,0].legend(title='Scenario', frameon=True, title_fontproperties={'weight':'bold'}, fontsize=10)
for text, new_label in zip(legend.get_texts(), new_labels):
    text.set_text(new_label)
    
axes[1][0].set_ylabel('RH (gC/m2/yr)')
axes[2][0].set_ylabel('NEE (gC/m2/yr)')

sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], x='year', y='GPP', hue='exp', ax=axes[0][1], legend=False, alpha=0.7)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], x='year', y='RH', hue='exp', ax=axes[1][1], legend=False, alpha=0.7)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], x='year', y='NEE', hue='exp', ax=axes[2][1], legend=False, alpha=0.7)

axes[0][1].set_ylabel('')
axes[1][1].set_ylabel('')
axes[2][1].set_ylabel('')

axes[0][1].set_title('Birch')


fig.tight_layout()

plt.savefig('C_Fluxes_fire_exps.jpg', dpi=300)


bin_interval=10
results_yearly['bin_lower_bound'] = np.floor(results_yearly['year']/bin_interval)
results_yearly['bin_lower_bound_year'] = results_yearly['bin_lower_bound']*bin_interval


results_yearly['bin_lower_bound_year']





fig, axes=plt.subplots(3,1,figsize=(8,5), sharex=True)

#sns.set_palette(sns.color_palette(['#708891', '#E0DAD0']))
sns.boxplot(data=results_yearly.loc[results_yearly['exp']=='control'], x = 'bin_lower_bound', y = 'GPP', hue='cmt', ax=axes[0],
           palette=[palette[5],palette[7]],medianprops={"color": "r", "linewidth": 0.7})
handles, labels = axes[0].get_legend_handles_labels()
axes[0].legend(handles=handles[:], labels=labels[:])
axes[0].set_xticklabels(results_yearly['bin_lower_bound_year'].unique().astype(int))
plt.xticks(rotation = 45)
axes[0].set_ylabel('GPP\n(g C $m^{-2}$ $y^{-1}$)')
axes[0].set_xlabel('')

sns.boxplot(data=results_yearly.loc[results_yearly['exp']=='control'], x = 'bin_lower_bound', y = 'RECO', hue='cmt', ax=axes[1],
           palette=[palette[5],palette[7]],medianprops={"color": "r", "linewidth": 0.7})
handles, labels = axes[1].get_legend_handles_labels()
axes[1].legend().remove()
axes[1].set_xticklabels(results_yearly['bin_lower_bound_year'].unique().astype(int))
plt.xticks(rotation = 45)
axes[1].set_ylabel('RECO\n(g C $m^{-2}$ $y^{-1}$)')
axes[1].set_xlabel('')

sns.boxplot(data=results_yearly.loc[results_yearly['exp']=='control'], x = 'bin_lower_bound', y = 'NEE', 
            hue='cmt', ax=axes[2], zorder=3,palette=[palette[5],palette[7]],medianprops={"color": "r", "linewidth": 0.7})
handles, labels = axes[2].get_legend_handles_labels()
axes[2].legend().remove()
axes[2].set_xticklabels(results_yearly['bin_lower_bound_year'].unique().astype(int))
plt.xticks(rotation = 45)
axes[2].set_ylabel('NEE\n(g C $m^{-2}$ $y^{-1}$)')
axes[2].set_xlabel('')

axes[2].axhline(0,linestyle='--', color='grey', linewidth=0.8)

# Get handles and labels, then modify
handles, labels = axes[0].get_legend_handles_labels()

# Replace labels
new_labels = ['black spruce', 'birch']
axes[0].legend(loc=(0.2,0.6), title=False, frameon=False, handles=handles, labels=new_labels)

axes[0].text(0.01, 0.83, '(a)', transform=axes[0].transAxes, fontsize=13)
axes[1].text(0.01, 0.83, '(b)', transform=axes[1].transAxes, fontsize=13)
axes[2].text(0.01, 0.83, '(c)', transform=axes[2].transAxes, fontsize=13)

fig.tight_layout()
plt.savefig('control_flux_history.jpg', dpi=300)
plt.show()


results_yearly['exp'].unique()


fig, axes = plt.subplots(2, 2, figsize=(8, 4), sharex=True, sharey='row')

# Plot boxplot first (this sets the categorical x-axis)
sns.boxplot(data=results_yearly.loc[results_yearly['exp']=='control'], 
            x='bin_lower_bound', y='RH', hue='cmt', ax=axes[1,0],
            palette=[palette[5], palette[7]], 
            medianprops={"color": "r", "linewidth": 0.7})

# Plot boxplot first (this sets the categorical x-axis)
sns.boxplot(data=results_yearly.loc[results_yearly['exp']=='burn_2030'], 
            x='bin_lower_bound', y='RH', hue='cmt', ax=axes[1,1],
            palette=[palette[5], palette[7]], 
            medianprops={"color": "r", "linewidth": 0.7}, legend=False)

# Get the x positions from the boxplot for the lineplot
x_positions = range(len(results_yearly['bin_lower_bound'].unique()))
bin_to_pos = {bin_val: pos for pos, bin_val in enumerate(sorted(results_yearly['bin_lower_bound'].unique()))}

# Get the unique cmt values in the same order as the boxplot hue
cmt_values = results_yearly.loc[results_yearly['exp']=='control', 'cmt'].unique()
color_map = dict(zip(cmt_values, [palette[5], palette[7]]))

# Manually plot lines with min/max shading on axes[0]
for cmt_val in cmt_values:
    color = color_map[cmt_val]
    data_subset = results_yearly.loc[(results_yearly['exp']=='control') & (results_yearly['cmt']==cmt_val)]
    
    # Group by bin_lower_bound and calculate mean, min, and max
    grouped = data_subset.groupby('bin_lower_bound')['ALD'].agg(['mean', 'min', 'max'])
    grouped = grouped.reindex(sorted(results_yearly['bin_lower_bound'].unique()))
    
    x_vals = [bin_to_pos[val] for val in grouped.index]
    y_mean = grouped['mean'].values
    y_min = grouped['min'].values
    y_max = grouped['max'].values
    
    # Plot line
    axes[0,0].plot(x_vals, y_mean, linewidth=2, color=color, label=cmt_val)
    
    # Add shaded region from min to max
    axes[0,0].fill_between(x_vals, y_min, y_max, alpha=0.2, color=color)

# Manually plot lines with min/max shading on axes[0]
for cmt_val in cmt_values:
    color = color_map[cmt_val]
    data_subset = results_yearly.loc[(results_yearly['exp']=='burn_2030') & (results_yearly['cmt']==cmt_val)]
    
    # Group by bin_lower_bound and calculate mean, min, and max
    grouped = data_subset.groupby('bin_lower_bound')['ALD'].agg(['mean', 'min', 'max'])
    grouped = grouped.reindex(sorted(results_yearly['bin_lower_bound'].unique()))
    
    x_vals = [bin_to_pos[val] for val in grouped.index]
    y_mean = grouped['mean'].values
    y_min = grouped['min'].values
    y_max = grouped['max'].values
    
    # Plot line
    axes[0,1].plot(x_vals, y_mean, linewidth=2, color=color, label=cmt_val)
    
    # Add shaded region from min to max
    axes[0,1].fill_between(x_vals, y_min, y_max, alpha=0.2, color=color)
    
# Set labels and formatting
axes[1,0].set_xticklabels(results_yearly['bin_lower_bound_year'].unique().astype(int), rotation=90)
axes[1,1].set_xticklabels(results_yearly['bin_lower_bound_year'].unique().astype(int), rotation=90)
axes[0,0].set_ylabel('ALD (m)')
axes[1,0].set_ylabel('RH\n(g C $m^{-2}$ $y^{-1}$)')
axes[1,0].set_xlabel('')
axes[1,1].set_xlabel('')
axes[0,0].set_xlabel('')

# Handle legends
handles, labels = axes[1,0].get_legend_handles_labels()
new_labels = ['black spruce', 'birch']
axes[1,0].legend(loc=(0.1, 0.6), title=False, frameon=False, handles=handles, labels=new_labels)
axes[0,0].legend().remove()

axes[0,0].text(0.01, 0.83, '(a)', transform=axes[0,0].transAxes, fontsize=13)
axes[1,0].text(0.01, 0.83, '(c)', transform=axes[1,0].transAxes, fontsize=13)
axes[0,1].text(0.01, 0.83, '(b)', transform=axes[0,1].transAxes, fontsize=13)
axes[1,1].text(0.01, 0.83, '(d)', transform=axes[1,1].transAxes, fontsize=13)

axes[0,0].set_title('Control', fontsize=13)
axes[0,1].set_title('2030 Burn', fontsize=13)

fig.tight_layout()
plt.savefig('RH_ALD.jpg', dpi=300)
plt.show()


lwc_layers['bin_lower_bound'] = np.floor(lwc_layers['year']/bin_interval)
lwc_layers['bin_lower_bound_year'] = lwc_layers['bin_lower_bound']*bin_interval

tem_inputs['bin_lower_bound'] = np.floor(tem_inputs['year']/bin_interval)
tem_inputs['bin_lower_bound_year'] = tem_inputs['bin_lower_bound']*bin_interval


tem_inputs['bin_lower_bound']


results_yearly['bin_lower_bound'] = results_yearly['bin_lower_bound'].astype(int)


tem_inputs['bin_lower_bound'] = tem_inputs['bin_lower_bound'].astype(int)


results_yearly = results_yearly.loc[results_yearly['bin_lower_bound']<210.0]
tem_inputs = tem_inputs.loc[tem_inputs['bin_lower_bound']<210.0]
lwc_layers = lwc_layers.loc[lwc_layers['bin_lower_bound']<210.0]


fig, axes=plt.subplots(4,1,figsize=(8,5), sharex=True)

# Get the common bin categories from results_yearly
bin_categories = results_yearly['bin_lower_bound'].unique()

sns.boxplot(data=results_yearly.loc[results_yearly['exp']=='control'], x = 'bin_lower_bound', y = 'NEE', hue='cmt', ax=axes[0],
           palette=[palette[5],palette[7]],medianprops={"color": "r", "linewidth": 0.7})
handles, labels = axes[0].get_legend_handles_labels()
axes[0].legend(handles=handles[:], labels=labels[:])
axes[0].set_xticklabels(results_yearly['bin_lower_bound_year'].unique().astype(int))
plt.xticks(rotation = 45)
axes[0].set_ylabel('NEE\n(g C $m^{-2}$ $y^{-1}$)')
axes[0].set_xlabel('')

sns.boxplot(data=results_yearly.loc[results_yearly['exp']=='control'], x = 'bin_lower_bound', y = 'ALD', hue='cmt', ax=axes[1],
           palette=[palette[5],palette[7]],medianprops={"color": "r", "linewidth": 0.7})
handles, labels = axes[1].get_legend_handles_labels()
axes[1].legend().remove()
axes[1].set_xticklabels(results_yearly['bin_lower_bound_year'].unique().astype(int))
plt.xticks(rotation = 45)
axes[1].set_ylabel('ALD\n(m)')
axes[1].set_xlabel('')
#axes[1].set_yscale('log')

# Force lwc_layers to use the same categories
lwc_subset = lwc_layers.loc[(lwc_layers['exp']=='control') & (lwc_layers['z']==0.2)].copy()
lwc_subset['bin_lower_bound'] = pd.Categorical(lwc_subset['bin_lower_bound'], 
                                                 categories=bin_categories, 
                                                 ordered=True)

sns.boxplot(data=lwc_subset, x = 'bin_lower_bound', y = 'VWCLAYER', 
            hue='cmt', ax=axes[2], zorder=3,palette=[palette[5],palette[7]],medianprops={"color": "r", "linewidth": 0.7})
handles, labels = axes[2].get_legend_handles_labels()
axes[2].legend().remove()
axes[2].set_xticklabels(results_yearly['bin_lower_bound_year'].unique().astype(int))
plt.xticks(rotation = 45)
axes[2].set_ylabel('20 cm Soil Moist.\n(%)')
axes[2].set_xlabel('')

# Convert bin_lower_bound to categorical to match boxplot x-axis positions
tem_inputs_copy = tem_inputs.copy()
tem_inputs_copy['bin_lower_bound_cat'] = pd.Categorical(tem_inputs_copy['bin_lower_bound'], 
                                                     categories=bin_categories,
                                                     ordered=True)
# Map categories to integer positions
tem_inputs_copy['x_pos'] = tem_inputs_copy['bin_lower_bound_cat'].cat.codes

# Calculate mean and std for shading
grouped = tem_inputs_copy.groupby('x_pos')['tair_mean'].agg(['mean', 'std']).reset_index()

# Plot line with shaded error
axes[3].plot(grouped['x_pos'], grouped['mean'], 
             label=r'$\mathrm{T}_{\mathrm{air}}$', alpha=0.8, color=palette[1], linewidth=0.8)
axes[3].fill_between(grouped['x_pos'], 
                      grouped['mean'] - grouped['std'], 
                      grouped['mean'] + grouped['std'],
                      alpha=0.3, color=palette[1])
axes[3].set_ylabel('$\mathrm{T}_{\mathrm{air}}$\n(°C)')

ax2=axes[3].twinx()
# Add bar plot for precipitation
precip_grouped = tem_inputs_copy.groupby('x_pos')['precip_sum'].mean().reset_index()
ax2.bar(precip_grouped['x_pos'], precip_grouped['precip_sum'], width=0.6, alpha=0.7, color=palette[8], label='precip')
ax2.set_ylabel('Precip.\n(mm)')

# Get handles and labels, then modify
handles, labels = axes[0].get_legend_handles_labels()
# Replace labels
new_labels = ['black spruce', 'birch']
axes[0].legend(loc=(0.2,0.6), title=False, frameon=False, handles=handles, labels=new_labels)
axes[0].text(0.01, 0.8, '(a)', transform=axes[0].transAxes, fontsize=13)
axes[1].text(0.01, 0.8, '(b)', transform=axes[1].transAxes, fontsize=13)
axes[2].text(0.01, 0.8, '(c)', transform=axes[2].transAxes, fontsize=13)
axes[3].text(0.01, 0.8, '(d)', transform=axes[3].transAxes, fontsize=13)

axes[0].legend(frameon=False, loc=(0.1,1), ncol=2)
axes[3].legend(frameon=False, loc=(0.05,0.7))
ax2.legend(frameon=False, loc=(0.18,0.7))

axes[3].set_xlim(9.5,20)

ax2.set_ylim(0,800)

fig.tight_layout()
plt.savefig('proj_change.jpg', dpi=300)
plt.show()


lwc_layers.loc[(lwc_layers['exp']=='control') & (lwc_layers['z']==0.2)]


results_yearly.columns


results_yearly.loc[(results_yearly['exp']=='control') & (results_yearly['year']>=2019)& (results_yearly['year']<=2024)][['cmt', 'year', 'NEE']].groupby(by='cmt').std()


fig, axes=plt.subplots(3,1,figsize=(8,5), sharex=True)

#sns.set_palette(sns.color_palette(['#708891', '#E0DAD0']))
sns.boxplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], x = 'bin_lower_bound', y = 'GPP', hue='exp', ax=axes[0])
handles, labels = axes[0].get_legend_handles_labels()
axes[0].legend(handles=handles[:], labels=labels[:])
axes[0].set_xticklabels(results_yearly['bin_lower_bound_year'].unique().astype(int))
plt.xticks(rotation = 45)
axes[0].set_ylabel('GPP\n(g C $m^{-2}$ $y^{-1}$)')
axes[0].set_xlabel('')

sns.boxplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
            x = 'bin_lower_bound', y = 'RECO', hue='exp', ax=axes[1], legend=False)
handles, labels = axes[1].get_legend_handles_labels()
axes[1].legend(handles=handles[:], labels=labels[:])
axes[1].set_xticklabels(results_yearly['bin_lower_bound_year'].unique().astype(int))
plt.xticks(rotation = 45)
axes[1].set_ylabel('RECO\n(g C $m^{-2}$ $y^{-1}$)')
axes[1].set_xlabel('')

sns.boxplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
            x = 'bin_lower_bound', y = 'NEE', hue='exp', ax=axes[2], legend=False)
handles, labels = axes[2].get_legend_handles_labels()
axes[2].legend(handles=handles[:], labels=labels[:])
axes[2].set_xticklabels(results_yearly['bin_lower_bound_year'].unique().astype(int))
plt.xticks(rotation = 45)
axes[2].set_ylabel('NEE\n(g C $m^{-2}$ $y^{-1}$)')
axes[2].set_xlabel('')

fig.tight_layout()

plt.show()


fig, axes=plt.subplots(3,1,figsize=(8,5), sharex=True)

#sns.set_palette(sns.color_palette(['#708891', '#E0DAD0']))
sns.boxplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], x = 'bin_lower_bound', y = 'GPP', hue='exp', ax=axes[0])
handles, labels = axes[0].get_legend_handles_labels()
axes[0].legend(handles=handles[:], labels=['control', '1930', '1960', '1990', '2030'], loc='upper left')
axes[0].set_xticklabels(results_yearly['bin_lower_bound_year'].unique().astype(int))
plt.xticks(rotation = 45)
axes[0].set_ylabel('GPP\n(g C $m^{-2}$ $y^{-1}$)')
axes[0].set_xlabel('')

sns.boxplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
            x = 'bin_lower_bound', y = 'RECO', hue='exp', ax=axes[1], legend=False)
handles, labels = axes[1].get_legend_handles_labels()
#axes[1].legend(handles=handles[:], labels=labels[:])
axes[1].set_xticklabels(results_yearly['bin_lower_bound_year'].unique().astype(int))
plt.xticks(rotation = 45)
axes[1].set_ylabel('RECO\n(g C $m^{-2}$ $y^{-1}$)')
axes[1].set_xlabel('')

sns.boxplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
            x = 'bin_lower_bound', y = 'NEE', hue='exp', ax=axes[2], legend=False)
handles, labels = axes[2].get_legend_handles_labels()
#axes[2].legend(handles=handles[:], labels=labels[:])
axes[2].set_xticklabels(results_yearly['bin_lower_bound_year'].unique().astype(int))
plt.xticks(rotation = 45)
axes[2].set_ylabel('NEE\n(g C $m^{-2}$ $y^{-1}$)')
axes[2].set_xlabel('')

fig.tight_layout()

plt.show()


fig, axes = plt.subplots(4,2, figsize=(8,6), sharex=True)


sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], x='year', y='SHLWC', hue='exp', ax=axes[0][0])
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], x='year', y='DEEPC', hue='exp', ax=axes[1][0], legend=False)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], x='year', y='MINEC', hue='exp', ax=axes[2][0], legend=False)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], x='year', y='AVLN', hue='exp', ax=axes[3][0], legend=False)


axes[0][0].set_title('Black Spruce')
axes[0][0].set_ylabel('SHLWC\n(gC/m2)')

new_labels = ['control', '1930', '1960', '1990', '2030']
legend=axes[0,0].legend(title='Scenario', frameon=True, title_fontproperties={'weight':'bold'}, fontsize=10)
for text, new_label in zip(legend.get_texts(), new_labels):
    text.set_text(new_label)
    
axes[1][0].set_ylabel('DEEPC\n(gC/m2)')
axes[2][0].set_ylabel('MINEC\n(gC/m2)')
axes[3][0].set_ylabel('AVLN\n(gN/m2)')

sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], x='year', y='SHLWC', hue='exp', ax=axes[0][1], legend=False)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], x='year', y='DEEPC', hue='exp', ax=axes[1][1], legend=False)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], x='year', y='MINEC', hue='exp', ax=axes[2][1], legend=False)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], x='year', y='AVLN', hue='exp', ax=axes[3][1], legend=False)


axes[0][1].set_ylabel('')
axes[1][1].set_ylabel('')
axes[2][1].set_ylabel('')

axes[0][1].set_title('Birch')

fig.legend(ncol=5, frameon=False, loc='upper left', bbox_to_anchor=(0.15,0.0))
axes[0][0].legend().remove()

axes[3,0].set_xlabel('')
axes[3,1].set_xlabel('')

fig.tight_layout()
plt.savefig('Soil_C_fire_exps.jpg', dpi=300, bbox_inches='tight',)


fig, axes = plt.subplots(5,2, figsize=(8,8), sharex=True)


sns.lineplot(data=results_yearly_pft.loc[(results_yearly_pft['cmt']=='black_spruce') & (results_yearly_pft['exp']=='control')], 
             x='year', y='VEGC', hue='pft', ax=axes[0][0])
sns.lineplot(data=results_yearly_pft.loc[(results_yearly_pft['cmt']=='black_spruce') & (results_yearly_pft['exp']=='burn_1930')], 
             x='year', y='VEGC', hue='pft', ax=axes[1][0], legend=False)
sns.lineplot(data=results_yearly_pft.loc[(results_yearly_pft['cmt']=='black_spruce') & (results_yearly_pft['exp']=='burn_1960')], 
             x='year', y='VEGC', hue='pft', ax=axes[2][0], legend=False)
sns.lineplot(data=results_yearly_pft.loc[(results_yearly_pft['cmt']=='black_spruce') & (results_yearly_pft['exp']=='burn_1990')], 
             x='year', y='VEGC', hue='pft', ax=axes[3][0], legend=False)
sns.lineplot(data=results_yearly_pft.loc[(results_yearly_pft['cmt']=='black_spruce') & (results_yearly_pft['exp']=='burn_2030')], 
             x='year', y='VEGC', hue='pft', ax=axes[4][0], legend=False)

axes[0][0].set_title('Black Spruce')
axes[0][0].set_ylabel('Control')
axes[0][0].legend(title=False)

    
axes[1][0].set_ylabel('1930 burn')
axes[2][0].set_ylabel('1960 burn')
axes[3][0].set_ylabel('1990 burn')
axes[4][0].set_ylabel('2030 burn')

sns.lineplot(data=results_yearly_pft.loc[(results_yearly_pft['cmt']=='birch') & (results_yearly_pft['exp']=='control')], 
             x='year', y='VEGC', hue='pft', ax=axes[0][1])
sns.lineplot(data=results_yearly_pft.loc[(results_yearly_pft['cmt']=='birch') & (results_yearly_pft['exp']=='burn_1930')], 
             x='year', y='VEGC', hue='pft', ax=axes[1][1], legend=False)
sns.lineplot(data=results_yearly_pft.loc[(results_yearly_pft['cmt']=='birch') & (results_yearly_pft['exp']=='burn_1960')], 
             x='year', y='VEGC', hue='pft', ax=axes[2][1], legend=False)
sns.lineplot(data=results_yearly_pft.loc[(results_yearly_pft['cmt']=='birch') & (results_yearly_pft['exp']=='burn_1990')], 
             x='year', y='VEGC', hue='pft', ax=axes[3][1], legend=False)
sns.lineplot(data=results_yearly_pft.loc[(results_yearly_pft['cmt']=='birch') & (results_yearly_pft['exp']=='burn_2030')], 
             x='year', y='VEGC', hue='pft', ax=axes[4][1], legend=False)

axes[0][1].set_ylabel('')
axes[1][1].set_ylabel('')
axes[2][1].set_ylabel('')
axes[3][1].set_ylabel('')
axes[4][1].set_ylabel('')

axes[0][1].set_title('Birch')
axes[0][1].legend(title=False)

fig.supylabel('VEGC')
fig.tight_layout()

plt.savefig('VEGC_fire_exps.jpg', dpi=300)


results_yearly_part


if len(results_yearly_part>0):
    fig, axes = plt.subplots(4,2, figsize=(8,8), sharex=True)


    sns.lineplot(data=results_yearly_part.loc[(results_yearly_part['cmt']=='black_spruce') & 
                                              (results_yearly_part['exp']=='control') &
                                              (results_yearly_part['pft']==0)], 
                 x='year', y='VEGC', hue='pftpart', ax=axes[0][0])
    sns.lineplot(data=results_yearly_part.loc[(results_yearly_part['cmt']=='black_spruce') & (results_yearly_part['exp']=='burn_1930')&
                                              (results_yearly_part['pft']==0)], 
                 x='year', y='VEGC', hue='pftpart', ax=axes[1][0], legend=False)
    sns.lineplot(data=results_yearly_part.loc[(results_yearly_part['cmt']=='black_spruce') & (results_yearly_part['exp']=='burn_1960')&
                                              (results_yearly_part['pft']==0)], 
                 x='year', y='VEGC', hue='pftpart', ax=axes[2][0], legend=False)
    sns.lineplot(data=results_yearly_part.loc[(results_yearly_part['cmt']=='black_spruce') & (results_yearly_part['exp']=='burn_1990')&
                                              (results_yearly_part['pft']==0)], 
                 x='year', y='VEGC', hue='pftpart', ax=axes[3][0], legend=False)

    axes[0][0].set_title('Black Spruce')
    axes[0][0].set_ylabel('Control')


    axes[1][0].set_ylabel('1930 burn')

    #axes[1][0].set_ylim(0,200)

    axes[2][0].set_ylabel('1960 burn')
    axes[3][0].set_ylabel('1990 burn')

    sns.lineplot(data=results_yearly_part.loc[(results_yearly_part['cmt']=='birch') & (results_yearly_part['exp']=='control')&
                                              (results_yearly_part['pft']==2)], 
                 x='year', y='VEGC', hue='pftpart', ax=axes[0][1])
    sns.lineplot(data=results_yearly_part.loc[(results_yearly_part['cmt']=='birch') & (results_yearly_part['exp']=='burn_1930')&
                                              (results_yearly_part['pft']==2)], 
                 x='year', y='VEGC', hue='pftpart', ax=axes[1][1], legend=False)
    sns.lineplot(data=results_yearly_part.loc[(results_yearly_part['cmt']=='birch') & (results_yearly_part['exp']=='burn_1960')&
                                              (results_yearly_part['pft']==2)], 
                 x='year', y='VEGC', hue='pftpart', ax=axes[2][1], legend=False)
    sns.lineplot(data=results_yearly_part.loc[(results_yearly_part['cmt']=='birch') & (results_yearly_part['exp']=='burn_1990')&
                                              (results_yearly_part['pft']==2)], 
                 x='year', y='VEGC', hue='pftpart', ax=axes[3][1], legend=False)

    axes[0][1].set_ylabel('')
    axes[1][1].set_ylabel('')
    axes[2][1].set_ylabel('')

    axes[0][1].set_title('Birch')

    fig.supylabel('VEGC')
    fig.tight_layout()

    plt.savefig('VEGC_tree_fire_exps.jpg', dpi=300)


if len(results_yearly_part>0):
    results_yearly_part.loc[(results_yearly_part['cmt']=='black_spruce') & (results_yearly_part['exp']=='burn_1930')&
                                              (results_yearly_part['pft']==0)
                                               & (results_yearly_part['pftpart']==0)]


pal=sns.color_palette(['#5d5e5e', '#faae34', '#ba6714', '#752f00'])


fig, axes=plt.subplots(2,1, figsize=(8,3), sharex=True)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
             x='year', y='ALD', hue='exp', palette=sns.color_palette(), alpha=0.6, ax=axes[0])

sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
             x='year', y='RH', hue='exp', palette=sns.color_palette(), alpha=0.6, ax=axes[1], legend=False)

axes[0].legend(loc=(0.0,1), ncol=5, title='', frameon=False)



plt.savefig('ALD-black_spruce.jpg', dpi=300)


fig, axes=plt.subplots(2,1, figsize=(8,3), sharex=True)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y='ALD', hue='exp', palette=sns.color_palette(), alpha=0.6, ax=axes[0])

sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y='RH', hue='exp', palette=sns.color_palette(), alpha=0.6, ax=axes[1], legend=False)

axes[0].legend(loc=(0.0,1), ncol=5, title='', frameon=False)
plt.savefig('ALD-birch.jpg', dpi=300)


fig, axes = plt.subplots(4,2, figsize=(8,8), sharex=True)


sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
             x='year', y='ALD', hue='exp', ax=axes[0][0], palette=sns.color_palette(), alpha=0.6)
#sns.lineplot(data=t_layers.loc[(t_layers['cmt']=='black_spruce') & (t_layers['z']==0.08)], 
#             x='year', y='TLAYER', hue='exp', ax=axes[1][0], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=t_layers.loc[(t_layers['cmt']=='black_spruce') & (t_layers['z']==0.2)], 
             x='year', y='TLAYER', hue='exp', ax=axes[2][0], legend=False, palette=sns.color_palette(), alpha=0.6)
sns.lineplot(data=t_layers.loc[(t_layers['cmt']=='black_spruce') & (t_layers['z']==0.3)], 
             x='year', y='TLAYER', hue='exp', ax=axes[3][0], legend=False, palette=sns.color_palette(), alpha=0.6)

axes[0][0].set_title('Black Spruce')
axes[0][0].set_ylabel('ALD (m)')

new_labels = ['control', '1930', '1960', '1990']
legend=axes[0,0].legend(title='Scenario', frameon=True, title_fontproperties={'weight':'bold'}, fontsize=10)
for text, new_label in zip(legend.get_texts(), new_labels):
    text.set_text(new_label)
    
axes[1][0].set_ylabel('TLAYER (8cm) (C)')
axes[2][0].set_ylabel('TLAYER (20cm) (C)')
axes[3][0].set_ylabel('TLAYER (30cm) (C)')

sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y='ALD', hue='exp', ax=axes[0][1], legend=False, palette=sns.color_palette(), alpha=0.6)
sns.lineplot(data=t_layers.loc[(t_layers['cmt']=='birch') & (t_layers['z']==0.08)], 
             x='year', y='TLAYER', hue='exp', ax=axes[1][1], legend=False, palette=sns.color_palette(), alpha=0.6)
sns.lineplot(data=t_layers.loc[(t_layers['cmt']=='birch') & (t_layers['z']==0.2)], 
             x='year', y='TLAYER', hue='exp', ax=axes[2][1], legend=False, palette=sns.color_palette(), alpha=0.6)
sns.lineplot(data=t_layers.loc[(t_layers['cmt']=='birch') & (t_layers['z']==0.3)], 
             x='year', y='TLAYER', hue='exp', ax=axes[3][1], legend=False, palette=sns.color_palette(), alpha=0.6)

axes[0][1].set_ylabel('')
axes[1][1].set_ylabel('')
axes[2][1].set_ylabel('')
axes[3][1].set_ylabel('')

axes[0][1].set_title('Birch')


fig.tight_layout()
plt.savefig('ALD_tlayer_fire_exps.jpg', dpi=300)


fig, axes = plt.subplots(5,2, figsize=(8,8), sharex=True)


sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
             x='year', y='ALD', hue='exp', ax=axes[0][0], palette=pal, alpha=0.6)
sns.lineplot(data=lwc_layers.loc[(lwc_layers['cmt']=='black_spruce') & (lwc_layers['z']==0.08)], 
             x='year', y='VWCLAYER', hue='exp', ax=axes[1][0], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=lwc_layers.loc[(lwc_layers['cmt']=='black_spruce') & (lwc_layers['z']==0.2)], 
             x='year', y='VWCLAYER', hue='exp', ax=axes[2][0], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=lwc_layers.loc[(lwc_layers['cmt']=='black_spruce') & (lwc_layers['z']==0.3)], 
             x='year', y='VWCLAYER', hue='exp', ax=axes[3][0], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=lwc_layers.loc[(lwc_layers['cmt']=='black_spruce') & (lwc_layers['z']==0.5)], 
             x='year', y='VWCLAYER', hue='exp', ax=axes[4][0], legend=False, palette=pal, alpha=0.6)

axes[0][0].set_title('Black Spruce')
axes[0][0].set_ylabel('ALD (m)')

new_labels = ['control', '1930', '1960', '1990']
legend=axes[0,0].legend(title='Scenario', frameon=True, title_fontproperties={'weight':'bold'}, fontsize=10)
for text, new_label in zip(legend.get_texts(), new_labels):
    text.set_text(new_label)
    
axes[1][0].set_ylabel('VWCLAYER (8cm) (C)')
axes[2][0].set_ylabel('VWCLAYER (20cm) (C)')
axes[3][0].set_ylabel('VWCLAYER (30cm) (C)')
axes[4][0].set_ylabel('VWCLAYER (50cm) (C)')

sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y='ALD', hue='exp', ax=axes[0][1], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=lwc_layers.loc[(lwc_layers['cmt']=='birch') & (lwc_layers['z']==0.08)], 
             x='year', y='VWCLAYER', hue='exp', ax=axes[1][1], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=lwc_layers.loc[(lwc_layers['cmt']=='birch') & (lwc_layers['z']==0.2)], 
             x='year', y='VWCLAYER', hue='exp', ax=axes[2][1], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=lwc_layers.loc[(lwc_layers['cmt']=='birch') & (lwc_layers['z']==0.3)], 
             x='year', y='VWCLAYER', hue='exp', ax=axes[3][1], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=lwc_layers.loc[(lwc_layers['cmt']=='birch') & (lwc_layers['z']==0.5)], 
             x='year', y='VWCLAYER', hue='exp', ax=axes[4][1], legend=False, palette=pal, alpha=0.6)

axes[0][1].set_ylabel('')
axes[1][1].set_ylabel('')
axes[2][1].set_ylabel('')
axes[3][1].set_ylabel('')

axes[0][1].set_title('Birch')


fig.tight_layout()
plt.savefig('ALD_lwclayer_fire_exps.jpg', dpi=300)


fig, axes = plt.subplots(4,2, figsize=(8,8), sharex=True)


sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
             x='year', y='ALD', hue='exp', ax=axes[0][0], palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
             x='year', y='WATERTAB', hue='exp', ax=axes[1][0], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
             x='year', y='SHLWDZ', hue='exp', ax=axes[2][0], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
             x='year', y='DEEPDZ', hue='exp', ax=axes[3][0], legend=False, palette=pal, alpha=0.6)

axes[0][0].set_title('Black Spruce')
axes[0][0].set_ylabel('ALD (m)')

new_labels = ['control', '1930', '1960', '1990']
legend=axes[0,0].legend(title='Scenario', frameon=True, title_fontproperties={'weight':'bold'}, fontsize=10)
for text, new_label in zip(legend.get_texts(), new_labels):
    text.set_text(new_label)
    
axes[1][0].set_ylabel('WATERTAB (m)')
axes[2][0].set_ylabel('SHLWDZ (m)')
axes[3][0].set_ylabel('DEEPDZ (m)')

sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y='ALD', hue='exp', ax=axes[0][1], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y='WATERTAB', hue='exp', ax=axes[1][1], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y='SHLWDZ', hue='exp', ax=axes[2][1], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y='DEEPDZ', hue='exp', ax=axes[3][1], legend=False, palette=pal, alpha=0.6)

axes[0][1].set_ylabel('')
axes[1][1].set_ylabel('')
axes[2][1].set_ylabel('')
axes[3][1].set_ylabel('')

axes[0][1].set_title('Birch')


fig.tight_layout()
plt.savefig('WATERTAB_DZ_fire_exps.jpg', dpi=300)


# fig, axes = plt.subplots(3,2, figsize=(8,8), sharex=True)
# 
# 
# sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
#              x='year', y='PET', hue='exp', ax=axes[0][0], palette=pal, alpha=0.6)
# sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
#              x='year', y='EET', hue='exp', ax=axes[1][0], legend=False, palette=pal, alpha=0.6)
# sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
#              x='year', y='WATERTAB', hue='exp', ax=axes[2][0], legend=False, palette=pal, alpha=0.6)
# 
# axes[0][0].set_title('Black Spruce')
# axes[0][0].set_ylabel('PET')
# 
# new_labels = ['control', '1930', '1960', '1990']
# legend=axes[0,0].legend(title='Scenario', frameon=True, title_fontproperties={'weight':'bold'}, fontsize=10)
# for text, new_label in zip(legend.get_texts(), new_labels):
#     text.set_text(new_label)
#     
# axes[1][0].set_ylabel('EET')
# axes[2][0].set_ylabel('WATERTAB (m)')
# 
# 
# sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
#              x='year', y='PET', hue='exp', ax=axes[0][1], legend=False, palette=pal, alpha=0.6)
# sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
#              x='year', y='EET', hue='exp', ax=axes[1][1], legend=False, palette=pal, alpha=0.6)
# sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
#              x='year', y='WATERTAB', hue='exp', ax=axes[2][1], legend=False, palette=pal, alpha=0.6)
# 
# 
# axes[0][1].set_ylabel('')
# axes[1][1].set_ylabel('')
# axes[2][1].set_ylabel('')
# 
# axes[0][1].set_title('Birch')
# 
# 
# fig.tight_layout()
# plt.savefig('ET_fire_exps.jpg', dpi=300)

fig, axes = plt.subplots(7,2, figsize=(8,10), sharex=True)


sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
             x='year', y='LTRFALC', hue='exp', ax=axes[0][0], palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
             x='year', y='SOMRAWC', hue='exp', ax=axes[1][0], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
             x='year', y='SOMA', hue='exp', ax=axes[2][0], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
             x='year', y='SOMPR', hue='exp', ax=axes[3][0], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
             x='year', y='SOMCR', hue='exp', ax=axes[4][0], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
             x='year', y='AVLN', hue='exp', ax=axes[5][0], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
             x='year', y='ORGN', hue='exp', ax=axes[6][0], legend=False, palette=pal, alpha=0.6)

axes[0][0].set_title('Black Spruce')
axes[0][0].set_ylabel('LTRFALC (gC/m2)')

new_labels = ['control', '1930', '1960', '1990']
legend=axes[0,0].legend(title='Scenario', frameon=True, title_fontproperties={'weight':'bold'}, fontsize=10)
for text, new_label in zip(legend.get_texts(), new_labels):
    text.set_text(new_label)
    
axes[1][0].set_ylabel('SOMRAWC (gC/m2)')
axes[2][0].set_ylabel('SOMA (gC/m2)')
axes[3][0].set_ylabel('SOMPR (gC/m2)')
axes[4][0].set_ylabel('SOMCR (gC/m2)')
axes[5][0].set_ylabel('AVLN (gC/m2)')

#axes[5][0].set_ylim(1.64,1.645)

sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y='LTRFALC', hue='exp', ax=axes[0][1], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y='SOMRAWC', hue='exp', ax=axes[1][1], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y='SOMA', hue='exp', ax=axes[2][1], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y='SOMPR', hue='exp', ax=axes[3][1], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y='SOMCR', hue='exp', ax=axes[4][1], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y='AVLN', hue='exp', ax=axes[5][1], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y='ORGN', hue='exp', ax=axes[6][1], legend=False, palette=pal, alpha=0.6)

#axes[6,0].set_ylim(2100,2300)

axes[0][1].set_ylabel('')
axes[1][1].set_ylabel('')
axes[2][1].set_ylabel('')
axes[3][1].set_ylabel('')
axes[4][1].set_ylabel('')
axes[5][1].set_ylabel('')

axes[0][1].set_title('Birch')


fig.tight_layout()
plt.savefig('Pools_fire_exps.jpg', dpi=300)


fig, axes=plt.subplots(2,1, sharex=True)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
             x='year', y='AVLN', hue='exp', ax=axes[0], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
             x='year', y='ORGN', hue='exp', ax=axes[1], legend=False, palette=pal, alpha=0.6)
plt.xlim(2035, 2040)


fig, axes=plt.subplots(2,1, sharex=True)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y='AVLN', hue='exp', ax=axes[0], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y='ORGN', hue='exp', ax=axes[1], legend=False, palette=pal, alpha=0.6)
plt.xlim(2035, 2040)


results_yearly.loc[(results_yearly['cmt']=='black_spruce') & (results_yearly['exp']=='control')][['year', 'AVLN']]


results_yearly.loc[(results_yearly['cmt']=='black_spruce') & (results_yearly['exp']=='control')][['year', 'ORGN']]


results_yearly.columns


fig, axes = plt.subplots(3,2, figsize=(8,8), sharex=True)


sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
             x='year', y='GPP', hue='exp', ax=axes[0][0], palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
             x='year', y='NPP', hue='exp', ax=axes[1][0], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='black_spruce'], 
             x='year', y='LTRFALC', hue='exp', ax=axes[2][0], legend=False, palette=pal, alpha=0.6)

axes[0][0].set_title('Black Spruce')
axes[0][0].set_ylabel('GPP')

new_labels = ['control', '1930', '1960', '1990']
legend=axes[0,0].legend(title='Scenario', frameon=True, title_fontproperties={'weight':'bold'}, fontsize=10)
for text, new_label in zip(legend.get_texts(), new_labels):
    text.set_text(new_label)
    
axes[1][0].set_ylabel('NPP')
axes[2][0].set_ylabel('LTRFALC')


sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y='GPP', hue='exp', ax=axes[0][1], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y='NPP', hue='exp', ax=axes[1][1], legend=False, palette=pal, alpha=0.6)
sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y='LTRFALC', hue='exp', ax=axes[2][1], legend=False, palette=pal, alpha=0.6)


axes[0][1].set_ylabel('')
axes[1][1].set_ylabel('')
axes[2][1].set_ylabel('')

axes[0][1].set_title('Birch')


fig.tight_layout()
plt.savefig('ET_fire_exps.jpg', dpi=300)


vegc_yearly = results_yearly_pft.groupby(by=['burn_year', 'cmt', 'exp', 'year']).sum().reset_index()
vegc_yearly['VEGC_diff'] = vegc_yearly['VEGC'].diff()
vegc_yearly = vegc_yearly.merge(results_yearly[['burn_year', 'cmt', 'exp', 'year', 'NPP', 'LTRFALC']], on = ['burn_year', 'cmt', 'exp', 'year'])
vegc_yearly['balance'] = vegc_yearly['VEGC_diff'] - (vegc_yearly['NPP'] - vegc_yearly['LTRFALC'])
vegc_yearly


sns.lineplot(data = vegc_yearly.loc[(vegc_yearly['cmt']=='black_spruce') & (vegc_yearly['exp']=='burn_1930')], x='year', y = 'balance', hue = 'exp')


sns.lineplot(data=results_yearly.loc[results_yearly['cmt']=='birch'], 
             x='year', y=results_yearly.loc[results_yearly['cmt']=='birch','EET']/results_yearly.loc[results_yearly['cmt']=='birch','PET'], 
             hue='exp', palette=pal, alpha=0.6)


emissions = results_yearly[['year', 'exp', 'cmt', 'burn_year', 'BURNSOIC', 'BURNVEG2AIRC']].groupby(by=['exp', 'cmt', 'burn_year']).sum().reset_index()
emissions['total'] = emissions['BURNSOIC'] + emissions['BURNVEG2AIRC']


fig, axes=plt.subplots(1,2, figsize=(8,3), sharex=True)
sns.barplot(data=emissions.loc[emissions['exp']!='control'], x='burn_year', y='BURNSOIC', hue='cmt', ax=axes[0])
sns.barplot(data=emissions.loc[emissions['exp']!='control'], x='burn_year', y='BURNVEG2AIRC', hue='cmt', ax=axes[1], legend=False)

axes[0].set_xlabel('Burn Year')
axes[1].set_xlabel('Burn Year')
axes[0].set_ylabel('Soil Emissions (gC/m2)')
axes[1].set_ylabel('Vegetation Emissions (gC/m2)')

axes[0].legend(title=False, loc='upper left')
plt.suptitle('Burn Emissions')
fig.tight_layout()
plt.savefig('burn_emissions.jpg', dpi=300)


results_yearly['growing_days'] = results_yearly['GROWEND'] - results_yearly['GROWSTART']


fig, axes=plt.subplots(2, 1, figsize=(8,5), sharex=True)

sns.lineplot(data=results_yearly.loc[results_yearly['exp']=='control'], x='year', y='GROWSTART', 
             label='growing start', ax=axes[0])

sns.lineplot(data=results_yearly.loc[results_yearly['exp']=='control'], x='year', y='GROWEND', 
             label='growing end', ax=axes[0])
axes[0].set_ylabel('Day of Year')
axes[0].set_xlabel('')

sns.lineplot(data=results_yearly.loc[results_yearly['exp']=='control'], x='year', y='growing_days', 
             label='growing days', ax=axes[1])

axes[1].set_ylabel('Days')

fig.tight_layout()
plt.savefig('growing_days.jpg', dpi=300)


carbon_summary = results_yearly_pft.groupby(by=['year', 'cmt', 'exp', 'burn_year']).sum().reset_index()


results_yearly=results_yearly.merge(carbon_summary, on=['year', 'cmt', 'exp', 'burn_year'])


results_yearly_pft = results_yearly_pft.merge(results_yearly[['year', 'YSD']], on='year', how='left')


results_yearly_pft['years_since_fire'] = results_yearly_pft['year'] - results_yearly_pft['burn_year']


year_before_fire_pft = []

pre_fire_pft = results_yearly_pft.loc[(results_yearly_pft['years_since_fire'] == 0)].groupby(by=['exp', 'cmt', 'pft','burn_year'])

for name, group in pre_fire_pft:
    year_before_fire_pft.append(group.loc[group.index==group['year'].idxmax()])
    
year_before_fire_pft = pd.concat(year_before_fire_pft)


year_before_fire_pft


results_yearly_pft.columns


year_before_fire = []

pre_fire = results_yearly.loc[(results_yearly['years_since_fire'] == 0)].groupby(by=['exp', 'cmt', 'burn_year'])

for name, group in pre_fire:
    year_before_fire.append(group)
    
year_before_fire = pd.concat(year_before_fire)


pd.set_option('display.max_rows', None) 


ysd_pft = results_yearly_pft.loc[(results_yearly_pft['YSD'] < 500)]

ysd_pft = ysd_pft.merge(year_before_fire_pft, on = ['exp', 'cmt','pft', 'burn_year'], suffixes=['', '_prefire'])


ysd_pft.head()


#ysd = results_yearly.loc[(results_yearly['years_since_fire'] != 0)]
ysd = results_yearly.loc[(results_yearly['YSD'] < 500)]

ysd = ysd.merge(year_before_fire, on = ['exp', 'cmt', 'burn_year'], suffixes=['', '_prefire'])


fig, axes=plt.subplots(2, 1, figsize = (8,5), sharey=True, sharex=True)

sns.lineplot(data=ysd.loc[ysd['cmt'] == 'black_spruce'], x='YSD', 
             y=ysd['VEGC'] - ysd['VEGC_prefire'], hue='exp', ax=axes[0])

sns.lineplot(data=ysd.loc[ysd['cmt'] == 'birch'], x='YSD', 
             y=ysd['VEGC'] - ysd['VEGC_prefire'], hue='exp', ax=axes[1], legend=False)

axes[0].axhline(y = 0, color = 'grey', linestyle = '--')
axes[1].axhline(y = 0, color = 'grey', linestyle = '--') 

axes[0].set_ylabel('Black Spruce VegC (gC/m2)')
axes[1].set_ylabel('Birch VegC (gC/m2)')
axes[1].set_xlabel('Years Since Disturbance')
fig.tight_layout()
plt.savefig('VegC_recovery.jpg', dpi=300)


fig, axes=plt.subplots(2,1, sharex=True)

sns.lineplot(data=ysd.loc[ysd['cmt']=='black_spruce'], x='YSD', y=(ysd['DEEPC']+ysd['SHLWC']+ysd['MINEC']) - (ysd['DEEPC_prefire']+ysd['SHLWC_prefire']+ysd['MINEC_prefire']), 
             hue='exp', ax=axes[0])
sns.lineplot(data=ysd.loc[ysd['cmt']=='birch'], x='YSD', y=(ysd['DEEPC']+ysd['SHLWC']+ysd['MINEC']) - (ysd['DEEPC_prefire']+ysd['SHLWC_prefire']+ysd['MINEC_prefire']), 
             hue='exp', ax=axes[1], legend=False)

axes[0].axhline(y = 0, color = 'grey', linestyle = '--')
axes[1].axhline(y = 0, color = 'grey', linestyle = '--')

axes[0].set_ylabel('Black Spruce SOC (gC/m2)')
axes[1].set_ylabel('Birch SOC (gC/m2)')
axes[1].set_xlabel('Years Since Disturbance')
fig.tight_layout()

plt.savefig('SoilC_recovery.jpg', dpi=300)


fig, axes=plt.subplots(2,1, figsize=(8,5), sharex=True)
sns.lineplot(data=ysd.loc[ysd['cmt']=='black_spruce'], x='YSD', y=ysd['GPP'] - ysd['GPP_prefire'], hue='exp', ax=axes[0])
sns.lineplot(data=ysd.loc[ysd['cmt']=='black_spruce'], x='YSD', y=ysd['RECO'] - ysd['RECO_prefire'], hue='exp', ax=axes[1], legend=False)

axes[0].axhline(y = 0, color = 'grey', linestyle = '--')
axes[1].axhline(y = 0, color = 'grey', linestyle = '--')

axes[0].set_ylabel('Black Spruce GPP (gC/m2/yr)')
axes[1].set_ylabel('Black Spruce RECO (gC/m2/yr)')
axes[0].set_xlabel('Years Since Disturbance')
axes[1].set_xlabel('Years Since Disturbance')

fig.tight_layout()
plt.savefig('Black_Spruce_Flux_recovery.jpg', dpi=300)


fig, axes=plt.subplots(2,1, figsize=(8,5), sharex=True)
sns.lineplot(data=ysd.loc[ysd['cmt']=='birch'], x='YSD', y=ysd['GPP'] - ysd['GPP_prefire'], hue='exp', ax=axes[0])
sns.lineplot(data=ysd.loc[ysd['cmt']=='birch'], x='YSD', y=ysd['RECO'] - ysd['RECO_prefire'], hue='exp', ax=axes[1], legend=False)

axes[0].axhline(y = 0, color = 'grey', linestyle = '--')
axes[1].axhline(y = 0, color = 'grey', linestyle = '--')

axes[0].set_ylabel('Birch GPP (gC/m2/yr)')
axes[1].set_ylabel('Birch RECO (gC/m2/yr)')
axes[0].set_xlabel('Years Since Disturbance')
axes[1].set_xlabel('Years Since Disturbance')

fig.tight_layout()
plt.savefig('Birch_Flux_recovery.jpg', dpi=300)


emissions = results_yearly[['year', 'exp', 'cmt', 'burn_year', 'BURNSOIC', 'BURNVEG2AIRC']].groupby(by=['exp', 'cmt', 'burn_year']).sum().reset_index()
emissions['total'] = emissions['BURNSOIC'] + emissions['BURNVEG2AIRC']

flux_sum = results_yearly[['year', 'exp', 'cmt', 'burn_year', 'NEE']].groupby(by=['exp', 'cmt', 'burn_year']).sum().reset_index()
flux_sum['burn_year'] = flux_sum['burn_year'].astype(int)


fig, axes=plt.subplots(1,3,figsize=(10,3))

sns.barplot(data=emissions, x='burn_year', 
            y='total', hue='cmt', ax=axes[0],palette=[palette[7],palette[5]])

sns.barplot(data=flux_sum, x='burn_year', 
            y='NEE', hue='cmt', ax=axes[1], legend=False,palette=[palette[7],palette[5]])

sns.barplot(data=flux_sum, x='burn_year', 
            y=flux_sum['NEE'] + emissions['total'], 
            hue='cmt', ax=axes[2], legend=False,palette=[palette[7],palette[5]])

axes[0].set_xlabel('Burn Year')
#axes[0].set_ylim(1000,5000)
axes[0].set_xticklabels(['no burn', '1930', '1960', '1990', '2030'])
axes[0].set_ylabel('Burn emissions (gC m$^{-2}$)')
axes[0].tick_params(axis='x', labelrotation=90)
axes[1].set_xlabel('Burn Year')
axes[1].set_ylabel('NEE (gC m$^{-2}$)')
axes[1].set_xticklabels(['no burn', '1930', '1960', '1990', '2030'])
axes[1].tick_params(axis='x', labelrotation=90)
axes[2].set_xlabel('Burn Year')
axes[2].set_ylabel('NEE + emissions (gC m$^{-2}$)')
axes[2].set_xticklabels(['no burn', '1930', '1960', '1990', '2030'])
axes[2].tick_params(axis='x', labelrotation=90)

axes[0].text(-0.15, 1.1, '(a)', transform=axes[0].transAxes, fontsize=13)
axes[1].text(-0.15, 1.1, '(b)', transform=axes[1].transAxes, fontsize=13)
axes[2].text(-0.15, 1.1, '(c)', transform=axes[2].transAxes, fontsize=13)

# Remove frame (spines)
for ax in axes.flatten():
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    #ax.spines['bottom'].set_visible(False)
    #ax.spines['left'].set_visible(False)

    # Rotate x tick labels
    ax.tick_params(axis='x', rotation=45)

    # Remove tick markers
    ax.tick_params(axis='both', which='both', length=0)
    
    #ax.minorticks_on()
    #ax.grid(axis='y', which='both', linestyle='--', alpha=0.3)
    ax.grid(axis='y', which='major', linestyle='--', alpha=0.7, linewidth=0.5)
    ax.set_axisbelow(True)

plt.suptitle('Net Carbon Balance 1901 - 2100 (RCP8.5)')


# Get handles and labels, then modify
handles, labels = axes[0].get_legend_handles_labels()

# Replace labels
new_labels = ['birch', 'black spruce']
axes[0].legend(title=False, loc=(0,1), ncol=2, frameon=False, handles=handles, labels=new_labels)

fig.tight_layout()

plt.savefig('net_carbon_balance.jpg', dpi=300)


emissions_2025 = results_yearly.loc[results_yearly['year']>=2025][['year', 'exp', 'cmt', 'burn_year', 'BURNSOIC', 'BURNVEG2AIRC']].groupby(by=['exp', 'cmt', 'burn_year']).sum().reset_index()
emissions_2025['total'] = emissions_2025['BURNSOIC'] + emissions_2025['BURNVEG2AIRC']

flux_sum_2025 = results_yearly.loc[results_yearly['year']>=2025][['year', 'exp', 'cmt', 'burn_year', 'NEE']].groupby(by=['exp', 'cmt', 'burn_year']).sum().reset_index()
flux_sum_2025['burn_year'] = flux_sum_2025['burn_year'].astype(int)


fig, axes=plt.subplots(1,3,figsize=(10,3))

sns.barplot(data=emissions_2025, x='burn_year', 
            y='total', hue='cmt', ax=axes[0],palette=[palette[7],palette[5]])

sns.barplot(data=flux_sum_2025, x='burn_year', 
            y='NEE', hue='cmt', ax=axes[1], legend=False,palette=[palette[7],palette[5]])

sns.barplot(data=flux_sum_2025, x='burn_year', 
            y=flux_sum_2025['NEE'] + emissions_2025['total'], 
            hue='cmt', ax=axes[2], legend=False,palette=[palette[7],palette[5]])

axes[0].set_xlabel('Burn Year')
#axes[0].set_ylim(1000,5000)
axes[0].set_xticklabels(['no burn', '1930', '1960', '1990', '2030'])
axes[0].set_ylabel(r'Burn emissions (gC m$^{-2}$)')
axes[0].tick_params(axis='x', labelrotation=90)
axes[1].set_xlabel('Burn Year')
axes[1].set_ylabel(r'NEE (gC m$^{-2}$)')
axes[1].set_xticklabels(['no burn', '1930', '1960', '1990', '2030'])
axes[1].tick_params(axis='x', labelrotation=90)
axes[2].set_xlabel('Burn Year')
axes[2].set_ylabel(r'NEE + emissions (gC m$^{-2}$)')
axes[2].set_xticklabels(['no burn', '1930', '1960', '1990', '2030'])
axes[2].tick_params(axis='x', labelrotation=90)

axes[0].text(-0.15, 1.1, '(a)', transform=axes[0].transAxes, fontsize=13)
axes[1].text(-0.15, 1.1, '(b)', transform=axes[1].transAxes, fontsize=13)
axes[2].text(-0.15, 1.1, '(c)', transform=axes[2].transAxes, fontsize=13)
# Get handles and labels, then modify
handles, labels = axes[0].get_legend_handles_labels()


# Remove frame (spines)
for ax in axes.flatten():
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    #ax.spines['bottom'].set_visible(False)
    #ax.spines['left'].set_visible(False)

    # Rotate x tick labels
    ax.tick_params(axis='x', rotation=45)

    # Remove tick markers
    ax.tick_params(axis='both', which='both', length=0)
    
    #ax.minorticks_on()
    #ax.grid(axis='y', which='both', linestyle='--', alpha=0.3)
    ax.grid(axis='y', which='major', linestyle='--', alpha=0.7, linewidth=0.5)
    ax.set_axisbelow(True)
    
    
# Replace labels
new_labels = ['birch', 'black spruce']
axes[0].legend(title=False, loc=(0,1), ncol=2, frameon=False, handles=handles, labels=new_labels)

plt.suptitle('Net Carbon Balance 2025 - 2100 (RCP8.5)')
fig.tight_layout()


plt.savefig('net_carbon_balance_2025.jpg', dpi=300)


results_yearly.columns


ysd_pft.columns


fig, axes=plt.subplots(2, 1, figsize = (8,5), sharey=True, sharex=True)

sns.lineplot(data=ysd_pft.loc[(ysd_pft['cmt'] == 'black_spruce')& (ysd_pft['exp'] == 'burn_1930')], x='YSD', 
             y=ysd['VEGC'] - ysd['VEGC_prefire'], hue='pft', ax=axes[0])

sns.lineplot(data=ysd_pft.loc[(ysd_pft['cmt'] == 'birch')& (ysd_pft['exp'] == 'burn_1930')], x='YSD', 
             y=ysd_pft['VEGC'] - ysd_pft['VEGC_prefire'], hue='pft', ax=axes[1], legend=False)

axes[0].axhline(y = 0, color = 'grey', linestyle = '--')
axes[1].axhline(y = 0, color = 'grey', linestyle = '--') 

axes[0].set_ylabel('Black Spruce VegC (gC/m2)')
axes[1].set_ylabel('Birch VegC (gC/m2)')
axes[1].set_xlabel('Years Since Disturbance')
fig.tight_layout()
plt.savefig('VegC_recovery_pft.jpg', dpi=300)


#compare outputs with target data


results_yearly['total_burn_emissions'] = results_yearly['BURNVEG2AIRC'] + results_yearly['BURNSOIC']
results_yearly['total_soil_carbon'] = results_yearly['SHLWC'] + results_yearly['DEEPC'] + results_yearly['MINEC']


results_yearly.columns


results_yearly_output = results_yearly[['cmt','exp','year','burn_year','GPP','RECO','NEE','NPP','RH',
                                        'RG','RM','VEGC','LTRFALC','SHLWC','DEEPC','MINEC','total_soil_carbon',
                                        'ALD', 'BURNVEG2AIRC','BURNSOIC','total_burn_emissions','years_since_fire']]


results_yearly_output.loc[results_yearly_output['cmt']=='black_spruce'].to_csv('output_files/yearly_TEM_outputs_black_spruce.csv', index=False)
results_yearly_output.loc[results_yearly_output['cmt']=='birch'].to_csv('output_files/yearly_TEM_outputs_birch.csv', index=False)




