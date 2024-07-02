#!/usr/bin/env python
# coding: utf-8

import sys
# caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(1, '/work/scripts/util')
from output import load_trsc_dataframe
import os
import output as ou
import pandas as pd
import xarray as xr
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt
from sklearn.metrics import r2_score


SA_path = '/data/workflows/BONA_black_spruce_SWC_SA/'
#SA_path = '/data/workflows/BONA_birch_SWC_SA/'
run_dirs=[os.path.join(SA_path, f) for f in os.listdir(SA_path) if ('sample' in f) and not ('.' in f)]

varlist = ['LAYERDEPTH', 'LAYERDZ', 'LAYERTYPE', 'TLAYER', 'LWCLAYER']
cell_x_coord = 0
cell_y_coord = 0

# WTT2, WTT3, DF2 - birch

# WTT1 - black spruce


depthlist = [0.15,0.4]

def get_lwclayer_tlayer(depthlist, run_dir, var):
    
    ### read the netcdf output files and compute year from the time dimension
    data = xr.open_dataset(f'{run_dir}/output/{var}_monthly_tr.nc')
    data = data.to_dataframe()
    data.reset_index(inplace=True)
    data.dtypes
    data['time'] = data['time'].astype('|S80')
    data['time'] = data['time'].astype('|datetime64[ns]')
    data['month'] = data['time'].dt.month
    data['year'] = data['time'].dt.year
    data = data.sort_values(['time','x','y','layer'])


    ### read the netcdf output files on soil structure and compute year from the time dimension
    dz = xr.open_dataset(f'{run_dir}/output/LAYERDZ_monthly_tr.nc')
    dz = dz.to_dataframe()
    dz.reset_index(inplace=True)
    dz.dtypes
    dz['time'] = dz['time'].astype('|S80')
    dz['time'] = dz['time'].astype('|datetime64[ns]')
    dz['month'] = dz['time'].dt.month
    dz['year'] = dz['time'].dt.year
    dz = dz.sort_values(['time','x','y','layer'])

    ### read the netcdf output files on soil structure and compute year from the time dimension
    lt = xr.open_dataset(f'{run_dir}/output/LAYERTYPE_monthly_tr.nc')
    lt = lt.to_dataframe()
    lt.reset_index(inplace=True)
    lt.dtypes
    lt['time'] = lt['time'].astype('|S80')
    lt['time'] = lt['time'].astype('|datetime64[ns]')
    lt['month'] = lt['time'].dt.month
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
        datastdz = datastdz[['time','x','y','layer','z','type',var, var+'_top', var+'_bot']]
        stdz.append(datastdz)

    stdz = pd.concat(stdz)
    
    return stdz


lwc_layers = []
t_layers = []
sample_dfs=[]
for d in run_dirs:
    if 'GPP_monthly_tr.nc' in os.listdir(os.path.join(d, 'output')):
        sample = int(d.split('/')[-1].split('_')[-1])
        TLAYER = ou.load_trsc_dataframe(var ='TLAYER', timeres='monthly', px_y=cell_y_coord, px_x=cell_x_coord, fileprefix=f'{d}/output/')[0]
        LAYERDEPTH = ou.load_trsc_dataframe(var ='LAYERDEPTH', timeres='monthly', px_y=cell_y_coord, px_x=cell_x_coord, fileprefix=f'{d}/output/')[0]
        LAYERDZ = ou.load_trsc_dataframe(var ='LAYERDZ', timeres='monthly', px_y=cell_y_coord, px_x=cell_x_coord, fileprefix=f'{d}/output/')[0]
        GPP = ou.load_trsc_dataframe(var ='GPP', timeres='monthly', px_y=cell_y_coord, px_x=cell_x_coord, fileprefix=f'{d}/output/')[0][0]
        ALD = ou.load_trsc_dataframe(var ='ALD', timeres='yearly', px_y=cell_y_coord, px_x=cell_x_coord, fileprefix=f'{d}/output/')[0][0]
        RH = ou.load_trsc_dataframe(var ='RH', timeres='monthly', px_y=cell_y_coord, px_x=cell_x_coord, fileprefix=f'{d}/output/')[0][0]
        ALD.columns=['ALD']
        sample_df = pd.DataFrame({'date': GPP.index, 'sample': [sample]*len(GPP), #'LWCLAYER': LWCLAYER, 'TLAYER': TLAYER, 'LAYERDEPTH': LAYERDEPTH, 'LAYERDZ': LAYERDZ,
                                  'GPP': GPP, 'RH':RH})
        sample_df = pd.merge(sample_df, ALD, how='left', left_on='date', right_index=True)
        sample_dfs.append(sample_df)
        
        LWCLAYER = get_lwclayer_tlayer(depthlist, d, 'LWCLAYER')
        LWCLAYER['sample'] = sample
        lwc_layers.append(LWCLAYER)
        
        TLAYER = get_lwclayer_tlayer(depthlist, d, 'TLAYER')
        TLAYER['sample'] = sample
        t_layers.append(TLAYER)
        
sample_dfs=pd.concat(sample_dfs)
lwc_layers=pd.concat(lwc_layers)
t_layers=pd.concat(t_layers)


sample_dfs['year'] = sample_dfs['date'].dt.year
sample_dfs['month'] = sample_dfs['date'].dt.month
sample_dfs = sample_dfs.loc[sample_dfs['year']>=2017]
sample_dfs.columns = ['date', 'sample', 'GPP', 'RH', 'ALD', 'year', 'month']

lwc_layers['year'] = lwc_layers['time'].dt.year
lwc_layers['month'] = lwc_layers['time'].dt.month
lwc_layers = lwc_layers.loc[lwc_layers['year']>=2017]

t_layers['year'] = t_layers['time'].dt.year
t_layers['month'] = t_layers['time'].dt.month
t_layers = t_layers.loc[t_layers['year']>=2017]


lwc_layers


path_to_tripod_data = '/data/comparison_data/BONA_Tripod_SM_TSoil.xlsx'


tripod_data = pd.read_excel(path_to_tripod_data, sheet_name='Long', parse_dates = ['Date'])
tripod_data = tripod_data.replace('NAN', np.nan)


tripod_data['month'] = tripod_data['Date'].dt.month
tripod_data['year'] = tripod_data['Date'].dt.year
tripod_data_monthly = tripod_data.groupby(by=['Location', 'year', 'month']).mean().reset_index()
tripod_data_monthly['day'] = 1
tripod_data_monthly['m_y'] = pd.to_datetime(tripod_data_monthly[['year', 'month', 'day']])


fig, axes = plt.subplots(2, 1, sharex=True)

#sns.lineplot(data=lwc_layers[lwc_layers['z']==.15], x='time', y='LWCLAYER', hue='sample', legend=False, ax=axes[0], alpha=0.3)
sns.lineplot(data=lwc_layers[(lwc_layers['z']==.15) & (lwc_layers['sample']==0)], x='time', y='LWCLAYER', color='red', ax=axes[0])

#sns.scatterplot(tripod_data_monthly[tripod_data_monthly['Location']=='WTT3'], label='WTT3', 
#             x='m_y', y = 'soil_moisture_15cm(%)', ax=axes[0])
#sns.scatterplot(tripod_data_monthly[tripod_data_monthly['Location']=='WTT2'], label='WTT2', 
#             x='m_y', y = 'soil_moisture_15cm(%)', ax=axes[0])
sns.scatterplot(tripod_data_monthly[tripod_data_monthly['Location']=='WTT1'], label='WTT2', 
             x='m_y', y = 'soil_moisture_15cm(%)', ax=axes[0])


#sns.lineplot(data=lwc_layers[lwc_layers['z']==.4], x='time', y='LWCLAYER', hue='sample', legend=False, ax=axes[1], alpha=0.3)
sns.lineplot(data=lwc_layers[(lwc_layers['z']==.4) & (lwc_layers['sample']==0)], x='time', y='LWCLAYER', color='red', ax=axes[1])


#sns.scatterplot(tripod_data_monthly[tripod_data_monthly['Location']=='WTT3'], 
#             x='m_y', y = 'soil_moisture_40cm(%)', ax=axes[1])
#sns.scatterplot(tripod_data_monthly[tripod_data_monthly['Location']=='WTT2'], 
#             x='m_y', y = 'soil_moisture_40cm(%)', ax=axes[1])
sns.scatterplot(tripod_data_monthly[tripod_data_monthly['Location']=='WTT1'], 
             x='m_y', y = 'soil_moisture_40cm(%)', ax=axes[1])

plt.xticks(rotation=70)

plt.xlabel('')
axes[0].set_ylabel('soil moisture 15 cm (C)')
axes[1].set_ylabel('soil moisture 40 cm (C)')

plt.xticks(rotation=70)


fig.tight_layout()

plt.savefig('BONA_SWC_SA_LWC_soil.jpg', dpi=300)


fig, axes = plt.subplots(2, 1, sharex=True)

#sns.lineplot(data=t_layers[t_layers['z']==.15], x='time', y='TLAYER', hue='sample', legend=False, alpha = 0.3, ax=axes[0])
sns.lineplot(data=t_layers[(t_layers['z']==.15) & (t_layers['sample']==42)], x='time', y='TLAYER', color='red', ax=axes[0])

#sns.scatterplot(tripod_data_monthly[tripod_data_monthly['Location']=='WTT3'], label='WTT3', 
#             x='m_y', y = 'soil_temp_15cm(°C)', ax=axes[0])
#sns.scatterplot(tripod_data_monthly[tripod_data_monthly['Location']=='WTT2'], label='WTT2',
#             x='m_y', y = 'soil_temp_15cm(°C)', ax=axes[0])
sns.scatterplot(tripod_data_monthly[tripod_data_monthly['Location']=='WTT1'], label='WTT2',
             x='m_y', y = 'soil_temp_15cm(°C)', ax=axes[0])


#sns.lineplot(data=t_layers[t_layers['z']==.4], x='time', y='TLAYER', hue='sample', alpha=0.3, ax=axes[1], legend=False)
sns.lineplot(data=t_layers[(t_layers['z']==.4) & (t_layers['sample']==42)], x='time', y='TLAYER', color='red', ax=axes[1])
#sns.lineplot(data=t_layers[(t_layers['z']==.4) & (t_layers['sample']==20)], x='time', y='TLAYER_top', color='red', ax=axes[1])
#sns.lineplot(data=t_layers[(t_layers['z']==.4) & (t_layers['sample']==20)], x='time', y='TLAYER_bot', color='red', ax=axes[1])

#sns.scatterplot(tripod_data_monthly[tripod_data_monthly['Location']=='WTT3'], 
#             x='m_y', y = 'soil_temp_40cm(°C)', ax=axes[1])
#sns.scatterplot(tripod_data_monthly[tripod_data_monthly['Location']=='WTT2'], 
#             x='m_y', y = 'soil_temp_40cm(°C)', ax=axes[1])
sns.scatterplot(tripod_data_monthly[tripod_data_monthly['Location']=='WTT1'], 
             x='m_y', y = 'soil_temp_40cm(°C)', ax=axes[1])


plt.xlabel('')
axes[0].set_ylabel('soil temp 15 cm (C)')
axes[1].set_ylabel('soil temp 40 cm (C)')

plt.xticks(rotation=70)


fig.tight_layout()

plt.savefig('BONA_SWC_SA_T_soil.jpg', dpi=300)


sns.scatterplot(data=sample_dfs.loc[sample_dfs['sample']==0], x='year', y='ALD', hue='sample')


sample_dfs


sample_matrix=pd.read_csv(os.path.join(SA_path, 'sample_matrix.csv'))
sample_matrix.iloc[42]


sample_matrix.iloc[35]


sample_summary_s = sample_dfs.loc[(sample_dfs['month']>7) & (sample_dfs['month']<9), ['sample', 'GPP', 'RH', 'ALD']].groupby(by='sample').mean()
t_layers_summary_s = t_layers.loc[(t_layers['month']>7) & (t_layers['month']<9), ['sample', 'z', 'type', 'TLAYER']].groupby(by=['sample', 'z']).mean().reset_index()
lwc_layers_summary_s = lwc_layers.loc[(lwc_layers['month']>7) & (lwc_layers['month']<9), ['sample', 'z', 'type', 'LWCLAYER']].groupby(by=['sample', 'z']).mean().reset_index()

sample_summary_s = sample_summary_s.merge(sample_matrix, left_index=True, right_index=True)
sample_summary_s = sample_summary_s.merge(t_layers_summary_s, left_index=True, right_on='sample', how='right')
sample_summary_s = sample_summary_s.merge(lwc_layers_summary_s, on=['sample', 'z'])

sample_summary_w = sample_dfs.loc[(sample_dfs['month']<6) | (sample_dfs['month']>=10), ['sample', 'GPP', 'RH', 'ALD']].groupby(by='sample').mean()
t_layers_summary_w = t_layers.loc[(t_layers['month']<6) | (t_layers['month']>=10), ['sample', 'z', 'type', 'TLAYER']].groupby(by=['sample', 'z']).mean().reset_index()
lwc_layers_summary_w = lwc_layers.loc[(lwc_layers['month']<6) | (lwc_layers['month']>=10), ['sample', 'z', 'type', 'LWCLAYER']].groupby(by=['sample', 'z']).mean().reset_index()

sample_summary_w = sample_summary_w.merge(sample_matrix, left_index=True, right_index=True)
sample_summary_w = sample_summary_w.merge(t_layers_summary_w, left_index=True, right_on='sample', how='right')
sample_summary_w = sample_summary_w.merge(lwc_layers_summary_w, on=['sample', 'z'])


sns.pairplot(data=sample_summary_s, x_vars=['hksat(m)','hksat(f)','hksat(h)',
          'tcsolid(m)', 'tcsolid(f)', 'tcsolid(h)'], y_vars= ['GPP', 'RH', 'TLAYER', 'LWCLAYER'], hue='z', kind='reg')


sns.pairplot(data=sample_summary_s, x_vars=['porosity(m)', 'porosity(f)', 'porosity(h)', 'nfactor(s)', 'nfactor(w)', 'rhq10'], 
             y_vars= ['GPP', 'RH', 'TLAYER', 'LWCLAYER'], hue='z', kind='reg')


sns.pairplot(data=sample_summary_w, x_vars=['hksat(m)','hksat(f)','hksat(h)',
          'tcsolid(m)', 'tcsolid(f)', 'tcsolid(h)'], y_vars= ['ALD', 'GPP', 'RH', 'TLAYER', 'LWCLAYER'], hue='z', kind='reg')


sns.pairplot(data=sample_summary_w, x_vars=['porosity(m)', 'porosity(f)', 'porosity(h)', 'nfactor(s)', 'nfactor(w)', 'rhq10'], 
             y_vars= ['ALD', 'GPP', 'RH', 'TLAYER', 'LWCLAYER'], hue='z', kind='reg')


sample_summary_s


tripod_data_monthly


tlayer_merged = t_layers[['time', 'z', 'TLAYER', 'sample']].merge(tripod_data_monthly[['m_y', 'soil_temp_15cm(°C)', 'soil_temp_40cm(°C)']], left_on = ['time'], right_on=['m_y'], how='left')
tlayer_merged= tlayer_merged.loc[~tlayer_merged['soil_temp_15cm(°C)'].isna() & ~tlayer_merged['soil_temp_40cm(°C)'].isna() & ~tlayer_merged['TLAYER'].isna()]

lwclayer_merged = lwc_layers[['time', 'z', 'LWCLAYER', 'sample']].merge(tripod_data_monthly[['m_y', 'soil_moisture_15cm(%)', 'soil_moisture_40cm(%)']], left_on = ['time'], right_on=['m_y'], how='left')
lwclayer_merged= lwclayer_merged.loc[~lwclayer_merged['soil_moisture_15cm(%)'].isna() & ~lwclayer_merged['soil_moisture_40cm(%)'].isna() & ~lwclayer_merged['LWCLAYER'].isna()]


r2s_15cm = []
r2s_40cm = []

samples = []

for sample in tlayer_merged['sample'].unique():
    
    tlayer_sample = tlayer_merged.loc[tlayer_merged['sample']==sample]
    if len(tlayer_sample.loc[tlayer_sample['z']==0.15])>0:
        r2_15cm = r2_score(tlayer_sample.loc[tlayer_sample['z']==0.15, 'soil_temp_15cm(°C)'], tlayer_sample.loc[tlayer_sample['z']==0.15, 'TLAYER'])
        r2_40cm = r2_score(tlayer_sample.loc[tlayer_sample['z']==0.4, 'soil_temp_40cm(°C)'], tlayer_sample.loc[tlayer_sample['z']==0.4, 'TLAYER'])

        samples.append(sample)
        r2s_15cm.append(r2_15cm)
        r2s_40cm.append(r2_40cm)
    
df_tlayer = pd.DataFrame({'sample': samples, 'r2_15cm': r2s_15cm, 'r2_40cm': r2s_40cm})


lwclayer_r2s_15cm = []
lwclayer_r2s_40cm = []

samples = []
for sample in tlayer_merged['sample'].unique():
    lwclayer_sample = lwclayer_merged.loc[lwclayer_merged['sample']==sample]
    if len(lwclayer_sample.loc[lwclayer_sample['z']==0.15])>0:
        r2_15cm = r2_score(lwclayer_sample.loc[lwclayer_sample['z']==0.15, 'soil_moisture_15cm(%)'], lwclayer_sample.loc[lwclayer_sample['z']==0.15, 'LWCLAYER'])
        r2_40cm = r2_score(lwclayer_sample.loc[lwclayer_sample['z']==0.4, 'soil_moisture_40cm(%)'], lwclayer_sample.loc[lwclayer_sample['z']==0.4, 'LWCLAYER'])

        samples.append(sample)
        lwclayer_r2s_15cm.append(r2_15cm)
        lwclayer_r2s_40cm.append(r2_40cm)
    
df_lwclayer = pd.DataFrame({'sample': samples, 'r2_15cm': lwclayer_r2s_15cm, 'r2_40cm': lwclayer_r2s_40cm})


df_tlayer.sort_values('r2_15cm', ascending=False).head(20)


df_lwclayer.sort_values('r2_15cm', ascending=False).head(20)










