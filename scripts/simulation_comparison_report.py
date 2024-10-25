#!/usr/bin/env python3

### Author: Hélène Genet, modified by Ruth Rutter
### Contact: hgenet@alaska.edu
### Institution: Institute of Arctic Biology, University of Alaska Fairbanks
### Script purpose: branch comparison.
### When a topic branch is ready to be submitted as a pull request, this
### script should be used to produce comparison plots to evaluate
### the effect of the code changes on model outputs.
### The product of this script is a file named result.pdf This should be
### provided with the pull request.


import os
import sys
import glob
import argparse
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mplc
import xarray as xr
from pypdf import PdfWriter
from PIL import Image

from cftime import datetime




### Flags

parser = argparse.ArgumentParser()
parser.add_argument('--POD', nargs='+')
parser.add_argument('--PODlist', nargs='+')
parser.add_argument('--scenariolist', nargs='+')
parser.add_argument('--colorlist', nargs='+')
parser.add_argument('--widthlist', nargs='+')
args = parser.parse_args()


# path to the directory with the various simulations to compare
# example: POD='/Users/helene/Helene/TEM/DVMDOSTEM/dvmdostem_workflows/fire_fix/'
POD = str(args.POD[0])

# list of the subdirectories containing single simulations
# example: PODlist = ['master_nofire','master_fire','fix1','fix2','fix3']
PODlist = args.PODlist

# title for each simulations
# example: scenariolist = ['0. master_nofire','1. master_fire','2. black_carbon_fix','3. root_dist_fix','4. root_dist_removal']
scenariolist = args.scenariolist

# color and width of plot lines for each scenartio
# example: colorlist = ['black', 'brown', 'cyan','green','blue']
# example: widthlist = [4, 3.2, 2.4, 1.6, 0.8]
colorlist = args.colorlist
widthlist = args.widthlist

# color of plot bars for each PFT
pftcolorlist = ['darkgreen','limegreen','mediumaquamarine','teal','slateblue','orchid','crimson','lightcoral','peachpuff','sandybrown','darkorange']


def load_reduced_dataframe(filepath, xidx=0, yidx=0):
  ds = xr.open_dataset(filepath)
  ds = ds.to_dataframe()

  #Add 0-based index column
  ds.reset_index(inplace=True)

  #Restrict to a single cell
  ds = ds[(ds['x'] == xidx)]
  ds = ds[(ds['y'] == yidx)]

  #x,y unnecessary because of single cell reduction
  ds = ds.drop(columns=['y','x','albers_conical_equal_area'])

  #Construct separated time columns
  #A time type of int indicates stages PR, EQ, or SP
  if isinstance(ds['time'][0], np.int64):
    if 'monthly' in filepath:
      ds['month'] = (ds['time'] % 12 + 1).astype('int')
      ds['year'] = (ds['time'] / 12).astype('int')
    elif 'yearly' in filepath:
      ds['year'] = ds['time'].astype('int')

  #A time type of cftime.datetime indicates stages TR or SC
  elif isinstance(ds['time'][0], datetime):
    ds['string_time'] = ds['time'].astype(pd.StringDtype())
    ds['year'] = ds['string_time'].str.split('-').str[0].astype('int')
    ds['month'] = ds['string_time'].str.split('-').str[1].astype('int')
    ds = ds.drop(columns=['string_time'])
  else:
    print("Incoming time column is of unhandled type " + str(type(ds['time'][0])))
    exit()

  return ds


### Define all plot functions

def ts_flux(simpath,simlist,vlist,sclist,clist,wlist,oname,ttl,stage):
  '''
  Produces flux yearly timeseries plots
  '''
  ncols = int(min(np.ceil(len(vlist)**0.5),3))
  nrows = int(np.ceil(len(vlist)/ncols))
  plt.figure(figsize=(12, int(0.8*12*(nrows/ncols))))

  for i in range(0,len(vlist)):
    ax = plt.subplot(nrows, ncols, i + 1)
    VAR=vlist[i]
#    print(VAR)
    dt = pd.DataFrame()
    for j in range(len(simlist)):
      simlist[j]
      PODout = (os.path.join(simpath,simlist[j],'output'))
#      print(PODout)
      fileglob = glob.glob(PODout + '/' + VAR + "_*_" + stage + ".nc")
      if len(fileglob) > 0:
        filepath = fileglob[0]

        ds = load_reduced_dataframe(filepath, xidx=0, yidx=0)

        out = pd.DataFrame(ds.groupby('year')[VAR].sum())
        out.reset_index(inplace=True)
        out['scenario'] = sclist[j]
        out['color'] = clist[j]
        out['width'] = wlist[j]

        dt = pd.concat([dt,out],axis=0)
    grouped = dt.groupby('scenario')
    group_dict = dict(list(grouped))
    for group in group_dict.keys():
      y= group_dict[group][VAR]
      x= group_dict[group]['year']
      ax.plot(x, y, label=group_dict[group]['scenario'][0], c=group_dict[group]['color'][0], linewidth=group_dict[group]['width'][0])
    ax.set_xlabel("Time (yrs)", fontsize=12)
    ax.set_ylabel(str(VAR), fontsize=12)

  if len(vlist) % ncols == 0:
    anchor = (1.2, 1)
    rs = 0.75
  else:
    anchor = (1.2, 0.2)
    rs = 0.9

  plt.subplots_adjust(left=0.1,bottom=0.1, right=rs, top=0.9,wspace=0.5,hspace=0.3)
  handles, labels = ax.get_legend_handles_labels()
  plt.legend(handles[0:len(sclist)], labels[0:len(sclist)], bbox_to_anchor=anchor, loc='center left', borderaxespad=0.1, fontsize=11)
  plt.suptitle(str(ttl), fontsize=20)
  plt.savefig(os.path.join(simpath,'results','Flux_' + oname + '.png'), dpi=300, transparent=False)
  plt.close()



def ts_stock(simpath,simlist,vlist,sclist,clist,wlist,oname,ttl,stage):
  '''
  Produces stock yearly timeseries plots
  '''
  ncols = int(min(np.ceil(len(vlist)**0.5),3))
  nrows = int(np.ceil(len(vlist)/ncols))
  plt.figure(figsize=(12, int(0.8*12*(nrows/ncols))))

  for i in range(0,len(vlist)):
    ax = plt.subplot(nrows, ncols, i + 1)
    VAR=vlist[i]
#    print(VAR)
    dt = pd.DataFrame()
    for j in range(len(simlist)):
      simlist[j]
      PODout = (os.path.join(simpath,simlist[j],'output'))
#      print(PODout)
      fileglob = glob.glob(PODout + '/' + VAR + "_*_" + stage + ".nc")
      if len(fileglob) > 0:
        filepath = fileglob[0]

        ds = load_reduced_dataframe(filepath, xidx=0, yidx=0)

        out = pd.DataFrame(ds[ds['month']==12].groupby('year')[VAR].sum())
        out.reset_index(inplace=True)
        out['scenario'] = sclist[j]
        out['color'] = clist[j]
        out['width'] = wlist[j]

        dt = pd.concat([dt,out],axis=0)
    years = dt['year'].drop_duplicates()
    grouped = dt.groupby('scenario')
    group_dict = dict(list(grouped))
    for group in group_dict.keys():
      y= group_dict[group][VAR]
      x= group_dict[group]['year']
      plt.plot(x, y, label=group_dict[group]['scenario'][0], c=group_dict[group]['color'][0], linewidth=group_dict[group]['width'][0])
    ax.set_xlabel("Time (yrs)", fontsize=12)
    ax.set_ylabel(str(VAR), fontsize=12)

  if len(vlist) % ncols == 0:
    anchor = (1.2, 1)
    rs = 0.75
  else:
    anchor = (1.2, 0.2)
    rs = 0.9

  plt.subplots_adjust(left=0.1,bottom=0.1, right=rs, top=0.9,wspace=0.5,hspace=0.3)
  handles, labels = ax.get_legend_handles_labels()
  plt.legend(handles[0:len(sclist)], labels[0:len(sclist)], bbox_to_anchor=anchor, loc='center left', borderaxespad=0.1, fontsize=11)
  plt.suptitle(str(ttl), fontsize=20)
  plt.savefig(os.path.join(simpath,'results','Stock_' + oname + '.png'), dpi=300, transparent=False)
  plt.close()


def seasonality(simpath, simlist, vlist, sclist, clist, oname, stage):
  '''
  Produces decadal seasonal pattern plots for the given variables.

  Assumes cell [0,0], and that there are 11 or more years of
    output data for the stage.
  '''
  for VAR in vlist:
    dt = pd.DataFrame()

    #For each simulation subdirectory
    for i in range(len(simlist)):
      simlist[i]
      PODout = (os.path.join(simpath,simlist[i],'output'))

      fileglob = glob.glob(PODout + '/' + VAR + "_*_" + stage + ".nc")
      if len(fileglob) > 0:
        filepath = fileglob[0]

        ds = load_reduced_dataframe(filepath, xidx=0, yidx=0)

        #Sample every 10 years, excluding year 0 to avoid the
        # volatility at stage change.
        #If the stage has <11 years of data, quietly produces empty plots
        ds = ds[(ds['year'] % 10 == 0) & (ds['year'] > 0)]

        out = pd.DataFrame(ds.groupby(['year','month'])[VAR].sum())
        out.reset_index(inplace=True)
        out['scenario'] = sclist[i]
        out['color'] = clist[i]

        dt = pd.concat([dt,out],axis=0)

    ncols = int(min(np.ceil(len(sclist)**0.5),3))
    nrows = int(np.ceil(len(sclist)/ncols))
    plt.figure(figsize=(12, int(0.8*12*(nrows/ncols))))

    for i in range(0,len(sclist)):
      scname=sclist[i]
#      print(scname)
      ax = plt.subplot(nrows, ncols, i + 1)
      grouped = dt[dt['scenario']==scname].groupby('year')
      group_dict = dict(list(grouped))
      colors = plt.cm.jet(np.linspace(0,1,len(group_dict.keys())))
      norm = mpl.colors.Normalize(vmin=dt[dt['scenario']==scname]['year'].min(), vmax=dt[dt['scenario']==scname]['year'].max())
      cmap = plt.cm.ScalarMappable(norm=norm,cmap=plt.cm.jet)
      cmap.set_array([])

      for j in range(len(group_dict.keys())):
        group = list(group_dict.keys())[j]
        group_dict[group].reset_index(inplace=True)
        y = group_dict[group][VAR]
        x = group_dict[group]['month']
        ax.plot(x, y, label=group_dict[group]['year'][0], c=colors[j])
      ax.set_xlabel("Month", fontsize=12)
      ax.set_ylabel(str(VAR), fontsize=12)
      ax.set_title(str(scname), fontsize=12)
    plt.subplots_adjust(left=0.1,bottom=0.1, right=0.8, top=0.9,wspace=0.5,hspace=0.3)
    cax = plt.axes([0.85, 0.1, 0.025, 0.8])
    plt.colorbar(cmap,cax=cax).set_label(label='year',rotation = 270, fontsize=12, labelpad=25)
    plt.suptitle(str(VAR) + ' Seasonal Pattern', fontsize=20)
    plt.savefig(os.path.join(simpath,'results','Seasonality_' + VAR + '.png'), bbox_inches='tight',dpi=300, transparent=False)
    plt.close()


def soilcnprofile(simpath,simlist,sclist,stage):
  VARlist = ['LAYERDEPTH','LAYERDZ','LAYERTYPE','SOMRAWC','SOMA','SOMPR','SOMCR','ORGN','AVLN']
  data = pd.DataFrame(columns=['scenario','year','layer'])
  for VAR in VARlist:
#    print(VAR)
    dt = pd.DataFrame()
    for i in range(len(simlist)):
      simlist[i]
      PODout = (os.path.join(simpath,simlist[i],'output'))
#      print(PODout)

      fileglob = glob.glob(PODout + '/' + VAR + "_*_" + stage + ".nc")
      if len(fileglob) > 0:
        filepath = fileglob[0]

        ds = load_reduced_dataframe(filepath, xidx=0, yidx=0)

        ds['scenario'] = sclist[i]
        ds = ds[ds['month'] == 12]
        ds = ds.drop(columns=['month','time'])

        dt = pd.concat([dt,ds],axis=0)  
    data = pd.merge(data,dt,on=['scenario','year','layer'], how='outer')
  
  ald = pd.DataFrame()
  for i in range(len(simlist)):
    simlist[i]
    PODout = (os.path.join(simpath,simlist[i],'output'))
#    print(PODout)
    fileglob = glob.glob(PODout + "/ALD_*_" + stage + ".nc")
    if len(fileglob) > 0:
      filepath = fileglob[0]

      ds = load_reduced_dataframe(filepath, xidx=0, yidx=0)

      ds['scenario'] = sclist[i]
      ds = ds.drop(columns=['time'])

    ald = pd.concat([ald,ds],axis=0)
  
  data['SOILC_DENS'] = 0.001*(data['SOMRAWC'].fillna(0) + data['SOMA'].fillna(0) + data['SOMPR'].fillna(0) + data['SOMCR'].fillna(0)) / data['LAYERDZ']
  data['ORGN_DENS'] = data['ORGN'].fillna(0) / data['LAYERDZ']
  data['AVLN_DENS'] = data['AVLN'].fillna(0) / data['LAYERDZ']
  #data = data.drop(columns=['SOMRAWC','SOMA','SOMPR','SOMCR'])
  data.loc[data['LAYERDZ'] < 0.01, 'tmp'] = 1
  data.loc[data['LAYERDZ'] >= 0.01, 'tmp'] = 0
  probs = data[data['tmp'] == 1]['scenario'].drop_duplicates().tolist()
  
  data = data[(data['LAYERDEPTH']>=0) & (data['LAYERDZ'] > 0.01)]
  olt = pd.DataFrame(data[data['LAYERTYPE']==3].groupby(['scenario','year'])['LAYERDEPTH'].min())
  olt.reset_index(inplace=True)
  olt = olt.rename(columns={"LAYERDEPTH": "OLT"})
  oltl = pd.DataFrame(data[data['LAYERTYPE']==3].groupby(['scenario','year'])['layer'].min())
  oltl.reset_index(inplace=True)
  oltl['OLT_nl'] = oltl['layer']-1
  oltl = oltl.drop(columns=['layer'])
  data = pd.merge(data,olt,on=['scenario','year'], how='outer')
  data = pd.merge(data,oltl,on=['scenario','year'], how='outer')
  data['depth'] = data['LAYERDEPTH'] - data['OLT']
  ald = pd.merge(ald,olt,on=['scenario','year'], how='outer')
  ald['ald_depth'] = ald['ALD'] - ald['OLT']
  data.loc[data['layer'] <= data['OLT_nl'], 'layer2'] = data['OLT_nl'] - data['layer']
  data.loc[data['layer'] > data['OLT_nl'], 'layer2'] = data['layer'] - (data['OLT_nl'] + 1)
  data.loc[data['layer'] <= data['OLT_nl'], 'dz2'] = data['LAYERDZ'] 
  data.loc[data['layer'] > data['OLT_nl'], 'dz2'] = -data['LAYERDZ']
  data['layer2'] = data['layer2'].astype(int)
#  print('plt1')
  norm = plt.Normalize(data['SOILC_DENS'].min(), data['SOILC_DENS'].max())
  cmap = plt.cm.ScalarMappable(norm=norm,cmap=plt.get_cmap('viridis'))
  cmap.set_array([])
  colors = pd.DataFrame(plt.get_cmap('viridis')(norm(data['SOILC_DENS'])))
  result = pd.concat([data, colors], axis=1)
  result1=result
  result1.loc[result1['SOILC_DENS'] == 0, 3] = 0
  result1 = result1[result1['depth']<2]
  #result1[(result1['scenario'] == '1. master_fire') & (result1['year'] > 198) & (result1['year'] < 202)]
  ncols = int(min(np.ceil(len(sclist)**0.5),6))
  nrows = int(np.ceil(len(sclist)/ncols))
  plt.figure(figsize=(12, int(0.8*12*(nrows/ncols))))
  for i in range(0,len(sclist)):
    scname=sclist[i]
#    print(scname)
    ax = plt.subplot(nrows, ncols, i + 1)
    bottom = np.zeros(len(result1['year'].drop_duplicates()))
    if scname in probs:
      ax.text(0.5, -2, 'layer(s) < 1cm thick')
    for j in range(result1[result1['LAYERTYPE'] < 3]['layer2'].min()+1,result1[result1['LAYERTYPE'] < 3]['layer2'].max()+1):
      tmp = result1[(result1['LAYERTYPE'] < 3) & (result1['scenario']==scname) & (result1['layer2']==j)]
      tmp = pd.merge(tmp,result1['year'].drop_duplicates(),on=['year'], how='outer')
      ax.bar(tmp['year'], tmp['dz2'], color=tmp[[0, 1, 2, 3]].to_numpy(), width=1.0, bottom=bottom)
      bottom += tmp['dz2']
    bottom = np.zeros(len(result1['year'].drop_duplicates()))
    for j in range(result1[result1['LAYERTYPE'] >= 3]['layer2'].min()+1,result1[result1['LAYERTYPE'] >= 3]['layer2'].max()+1):
      tmp = result1[(result1['LAYERTYPE'] >= 3) & (result1['scenario']==scname) & (result1['layer2']==j)]
      tmp = pd.merge(tmp,result1['year'].drop_duplicates(),on=['year'], how='outer')
      ax.bar(tmp['year'], tmp['dz2'], color=tmp[[0, 1, 2, 3]].to_numpy(), width=1.0, bottom=bottom)
      bottom += tmp['dz2']
    ax.set_xlabel('year', fontsize=12)
    ax.set_ylabel('depth (m)', fontsize=12)
    ax.set_title(str(scname), fontsize=12)
    ax.plot(ald[ald['scenario']==scname]['year'], -ald[ald['scenario']==scname]['ald_depth'], c='black', linewidth=1.5,linestyle='dashed')
  plt.subplots_adjust(left=0.1,bottom=0.1, right=0.8, top=0.9,wspace=0.5,hspace=0.5)
  cax = plt.axes([0.85, 0.1, 0.025, 0.8])
  plt.colorbar(cmap,cax=cax).set_label(label='Soil C density (kg/m3)',rotation = 270, fontsize=12, labelpad=25)
  plt.suptitle('Total Soil Carbon Profile', fontsize=20)
  plt.savefig(os.path.join(simpath,'results','Profile_SOILC_density.png'), bbox_inches='tight',dpi=300 ,transparent=False)
  plt.close()
    
  norm = plt.Normalize(data['ORGN_DENS'].min(), data['ORGN_DENS'].max())
  cmap = plt.cm.ScalarMappable(norm=norm,cmap=plt.get_cmap('viridis'))
  cmap.set_array([])
  colors = pd.DataFrame(plt.get_cmap('viridis')(norm(data['ORGN_DENS'])))
  result = pd.concat([data, colors], axis=1)
  result1=result
  result1.loc[result1['ORGN_DENS'] == 0, 3] = 0
  result1 = result1[result1['depth']<2]
  ncols = int(min(np.ceil(len(sclist)**0.5),6))
  nrows = int(np.ceil(len(sclist)/ncols))
  plt.figure(figsize=(12, int(0.8*12*(nrows/ncols))))
  for i in range(0,len(sclist)):
    scname=sclist[i]
#    print(scname)
    ax = plt.subplot(nrows, ncols, i + 1)
    bottom = np.zeros(len(result1['year'].drop_duplicates()))
    for j in range(result1[result1['LAYERTYPE'] < 3]['layer2'].min()+1,result1[result1['LAYERTYPE'] < 3]['layer2'].max()+1):
      tmp = result1[(result1['LAYERTYPE'] < 3) & (result1['scenario']==scname) & (result1['layer2']==j)]
      tmp = pd.merge(tmp,result1['year'].drop_duplicates(),on=['year'], how='outer')
      ax.bar(tmp['year'], tmp['dz2'], color=tmp[[0, 1, 2, 3]].to_numpy(), width=1.0, bottom=bottom)
      bottom += tmp['dz2']
    bottom = np.zeros(len(result1['year'].drop_duplicates()))
    for j in range(result1[result1['LAYERTYPE'] >= 3]['layer2'].min()+1,result1[result1['LAYERTYPE'] >= 3]['layer2'].max()+1):
      tmp = result1[(result1['LAYERTYPE'] >= 3) & (result1['scenario']==scname) & (result1['layer2']==j)]
      tmp = pd.merge(tmp,result1['year'].drop_duplicates(),on=['year'], how='outer')
      ax.bar(tmp['year'], tmp['dz2'], color=tmp[[0, 1, 2, 3]].to_numpy(), width=1.0, bottom=bottom)
      bottom += tmp['dz2']
    ax.set_xlabel('year', fontsize=12)
    ax.set_ylabel('depth (m)', fontsize=12)
    ax.set_title(str(scname), fontsize=12)
    ax.plot(ald[ald['scenario']==scname]['year'], -ald[ald['scenario']==scname]['ald_depth'], c='black', linewidth=1.5,linestyle='dashed')
  
  plt.subplots_adjust(left=0.1,bottom=0.1, right=0.8, top=0.9,wspace=0.5,hspace=0.5)
  cax = plt.axes([0.85, 0.1, 0.025, 0.8])
  plt.colorbar(cmap,cax=cax).set_label(label='Organic N density (g/m3)',rotation = 270, fontsize=12, labelpad=25)
  plt.suptitle('Organic N Soil Profile', fontsize=20)
  plt.savefig(os.path.join(simpath,'results','Profile_ORGN_density.png'), bbox_inches='tight',dpi=300, transparent=False)
  plt.close()

  norm = plt.Normalize(data['AVLN_DENS'].min(), data['AVLN_DENS'].max())
  cmap = plt.cm.ScalarMappable(norm=norm,cmap=plt.get_cmap('viridis'))
  cmap.set_array([])
  colors = pd.DataFrame(plt.get_cmap('viridis')(norm(data['AVLN_DENS'])))
  result = pd.concat([data, colors], axis=1)
  result1=result
  result1.loc[result1['AVLN_DENS'] == 0, 3] = 0
  result1 = result1[result1['depth']<2]
  ncols = int(min(np.ceil(len(sclist)**0.5),6))
  nrows = int(np.ceil(len(sclist)/ncols))
  plt.figure(figsize=(12, int(0.8*12*(nrows/ncols))))
  for i in range(0,len(sclist)):
    scname=sclist[i]
#    print(scname)
    ax = plt.subplot(nrows, ncols, i + 1)
    bottom = np.zeros(len(result1['year'].drop_duplicates()))
    for j in range(result1[result1['LAYERTYPE'] < 3]['layer2'].min()+1,result1[result1['LAYERTYPE'] < 3]['layer2'].max()+1):
      tmp = result1[(result1['LAYERTYPE'] < 3) & (result1['scenario']==scname) & (result1['layer2']==j)]
      tmp = pd.merge(tmp,result1['year'].drop_duplicates(),on=['year'], how='outer')
      ax.bar(tmp['year'], tmp['dz2'], color=tmp[[0, 1, 2, 3]].to_numpy(), width=1.0, bottom=bottom)
      bottom += tmp['dz2']
    bottom = np.zeros(len(result1['year'].drop_duplicates()))
    for j in range(result1[result1['LAYERTYPE'] >= 3]['layer2'].min()+1,result1[result1['LAYERTYPE'] >= 3]['layer2'].max()+1):
      tmp = result1[(result1['LAYERTYPE'] >= 3) & (result1['scenario']==scname) & (result1['layer2']==j)]
      tmp = pd.merge(tmp,result1['year'].drop_duplicates(),on=['year'], how='outer')
      ax.bar(tmp['year'], tmp['dz2'], color=tmp[[0, 1, 2, 3]].to_numpy(), width=1.0, bottom=bottom)
      bottom += tmp['dz2']
    ax.set_xlabel('year', fontsize=12)
    ax.set_ylabel('depth (m)', fontsize=12)
    ax.set_title(str(scname), fontsize=12)
    ax.plot(ald[ald['scenario']==scname]['year'], -ald[ald['scenario']==scname]['ald_depth'], c='black', linewidth=1.5,linestyle='dashed')
  plt.subplots_adjust(left=0.1,bottom=0.1, right=0.8, top=0.9,wspace=0.5,hspace=0.3)
  cax = plt.axes([0.85, 0.1, 0.025, 0.8])
  plt.colorbar(cmap,cax=cax).set_label(label='Available N density (g/m3)',rotation = 270, fontsize=12, labelpad=25)
  plt.suptitle('Available N Soil Profile', fontsize=20)
  plt.savefig(os.path.join(simpath,'results','Profile_AVLN_density.png'), bbox_inches='tight',dpi=300, transparent=False)
  plt.close()


def soilenvprofile(simpath,simlist,vlist,sclist,oname,stage):
  STVARlist = ['LAYERDEPTH','LAYERDZ','LAYERTYPE']
  soilstruc = pd.DataFrame(columns=['scenario','year','time','layer'])
  for VAR in STVARlist:
#    print(VAR)
    dt = pd.DataFrame()
    for i in range(len(simlist)):
      simlist[i]
      PODout = (os.path.join(POD,simlist[i],'output'))
#      print(PODout)

    #   if len(glob.glob(PODout + '/' + VAR + "_*_eq.nc")) > 0:
    #     filepath = glob.glob(PODout + '/' + VAR + "_*_eq.nc")[0]

      fileglob = glob.glob(PODout + '/' + VAR + "_*_" + stage + ".nc")
      if len(fileglob) > 0:
        filepath = fileglob[0]

        ds = load_reduced_dataframe(filepath, xidx=0, yidx=0)

        ds['scenario'] = sclist[i]
        ds = ds[ds['month'] == 12]
        ds = ds.drop(columns=['month'])
        dt = pd.concat([dt,ds],axis=0)  

    soilstruc = pd.merge(soilstruc,dt,on=['scenario','year','time','layer'], how='outer')
  soilstruc['LAYERDEPTHBOT'] = soilstruc['LAYERDEPTH'] + soilstruc['LAYERDZ']
#  print('soil structure done')
  
  for v in vlist:
#    print(v)
    dt = pd.DataFrame()
    dt2 = pd.DataFrame()
    for i in range(len(simlist)):
      simlist[i]
      PODout = (os.path.join(simpath,simlist[i],'output'))
#      print(PODout)

      fileglob = glob.glob(PODout + '/' + str(v) + "_*_" + stage + ".nc")
      if len(fileglob) > 0:
        filepath = fileglob[0]

        ds = load_reduced_dataframe(filepath, xidx=0, yidx=0)
        ds['scenario'] = sclist[i]

        out = pd.DataFrame(ds.groupby(['year', 'layer'])[v].mean())
        out.reset_index(inplace=True)
        out['scenario'] = sclist[i]
        dt = pd.concat([dt,ds],axis=0)
        dt2 = pd.concat([dt2,out],axis=0)
    seas10 = pd.merge(soilstruc[['scenario','year','layer','LAYERDZ','LAYERDEPTH','LAYERDEPTHBOT']],dt,on=['scenario','year','layer'], how='outer')
    #Reducing to the last ten years, and non-surface layers?
    seas10 = seas10[(seas10['LAYERDEPTH']>=0) & (seas10['year']>seas10['year'].max()-10)]
    #Reduce to these columns, remove entries that match for all columns
    ts = seas10[['scenario','year','month','time']].drop_duplicates()
#    print('ald')
    ald = pd.DataFrame()
    for i in range(len(PODlist)):
      PODlist[i]
      PODout = (os.path.join(POD,PODlist[i],'output'))
#      print(PODout)

      fileglob = glob.glob(PODout + "/ALD_*_" + stage + ".nc")
      if len(fileglob) > 0:
        filepath = fileglob[0]

        ds = load_reduced_dataframe(filepath, xidx=0, yidx=0)
        ds['scenario'] = sclist[i]
        ds = ds.drop(columns=['time'])

      ald = pd.concat([ald,ds],axis=0)

    #Merge the last 10 years of ald with ts (time/sc dataframe)
    ald_seas = pd.merge(ald[ald['year']>ald['year'].max()-10],ts,on=['scenario','year'], how='outer')
#    print('wtd')
    wt = pd.DataFrame()
    wt2 = pd.DataFrame()
    for i in range(len(simlist)):
      simlist[i]
      PODout = (os.path.join(simpath,simlist[i],'output'))
#      print(PODout)

      fileglob = glob.glob(PODout + "/WATERTAB_*_" + stage + ".nc")
      if len(fileglob) > 0:
        filepath = fileglob[0]

        ds = load_reduced_dataframe(filepath, xidx=0, yidx=0)
        ds['scenario'] = sclist[i]

        out = pd.DataFrame(ds.groupby(['year'])['WATERTAB'].mean())
        out.reset_index(inplace=True)
        out['scenario'] = sclist[i]
        wt = pd.concat([wt,ds],axis=0)
        wt2 = pd.concat([wt2,out],axis=0)
    wt10 = wt[wt['year']>wt['year'].max()-10]
#    print('olt')
    olt = pd.DataFrame(soilstruc[soilstruc['LAYERTYPE']==3].groupby(['scenario','year'])['LAYERDEPTH'].min())
    olt.reset_index(inplace=True)
    olt = olt.rename(columns={"LAYERDEPTH": "OLT"})
    olt_seas = pd.merge(olt[olt['year']>olt['year'].max()-10],ts,on=['scenario','year'], how='outer')
#    print('plt1')
    plt.set_cmap('bwr')

    if seas10[v].min() > 0:
      norm = mplc.TwoSlopeNorm(vmin=seas10[v].min(), vcenter=1.00001*seas10[v].min(), vmax=seas10[v].max())
    else:
      norm = mplc.TwoSlopeNorm(vmin=seas10[v].min(), vcenter=0, vmax=seas10[v].max())
    cmap = plt.cm.ScalarMappable(norm=norm,cmap=plt.set_cmap('bwr'))
    cmap.set_array([])
    clrs = pd.DataFrame(plt.get_cmap('bwr')(norm(seas10[v])))
    seas10.reset_index(drop=True, inplace=True)
    clrs.reset_index(drop=True, inplace=True)

    result = pd.concat([seas10, clrs], axis=1)
    result = result[result['layer'] >=0] 
    result.reset_index(drop=True, inplace=True)

    ncols = int(min(np.ceil(len(sclist)**0.5),6))
    nrows = int(np.ceil(len(sclist)/ncols))
    plt.figure(figsize=(12, int(0.8*12*(nrows/ncols))))

    #Producing a fake time index since the various plotting calls do
    # not work well with the datetime values in 'time' for tr and sc
    month_count = int(len(ald_seas['time']) / len(sclist))
    #print("month count: " + str(month_count))
    ald_seas['faketime'] = list(range(0, month_count)) + list(range(0, month_count))
    olt_seas['faketime'] = list(range(0, month_count)) + list(range(0, month_count))
    wt10['faketime'] = list(range(0, month_count)) + list(range(0, month_count))

    for i in range(0,len(sclist)):
      scname=sclist[i]
#      print(scname)
      ax = plt.subplot(nrows, ncols, i + 1)
      bottom = np.zeros(len(result['time'].drop_duplicates()))

      #For each layer in the current "scenario"
      for j in range(result['layer'].astype('int').min(),result['layer'].astype('int').max()+1):
        #tmp is result for the current layer in the current "scenario"
        tmp = result[(result['scenario']==scname) & (result['layer']==j)]
        #Merge tmp with... the time column from result with duplicates removed
        tmp = pd.merge(tmp,result['time'].drop_duplicates(),on=['time'], how='outer')

        tmp['faketime'] = range(0, len(tmp['time']))
        ax.bar(tmp['faketime'], -tmp['LAYERDZ'], color=tmp[[0, 1, 2, 3]].to_numpy(), width=1.0, bottom=bottom)

        bottom -= tmp['LAYERDZ']

      ax.set_xlabel('time (month)', fontsize=12)
      ax.set_ylabel('depth (m)', fontsize=12)
      ax.set_title(str(scname), fontsize=12)

      ax.plot(ald_seas[ald_seas['scenario']==scname]['faketime'], -ald_seas[ald_seas['scenario']==scname]['ALD'], c='blue', linewidth=1.5,linestyle='dashed')

      ax.plot(olt_seas[olt_seas['scenario']==scname]['faketime'], -olt_seas[olt_seas['scenario']==scname]['OLT'], c='black', linewidth=1.5,linestyle='dashed')

      ax.plot(wt10[wt10['scenario']==scname]['faketime'], -wt10[wt10['scenario']==scname]['WATERTAB'], c='cyan', linewidth=1.5,linestyle='dashed')

    plt.subplots_adjust(left=0.1,bottom=0.1, right=0.8, top=0.85,wspace=0.4,hspace=0.4)
    cax = plt.axes([0.85, 0.1, 0.025, 0.8])
    #plt.colorbar(cax=cax).set_label(label='Soil temp (oC))',rotation = 270, fontsize=12, labelpad=25)
    plt.colorbar(cmap,cax=cax).set_label(label=str(v),rotation = 270, fontsize=12, labelpad=25)
    plt.suptitle('Environmental Seasonal Profile - past 10 yrs', fontsize=20)
    plt.savefig(os.path.join(simpath,'results',oname + '_' + str(v) + '_seasonal.png'), bbox_inches='tight',dpi=300, transparent=False)
    plt.close()
    
#    print('plt2')
    ty = pd.merge(soilstruc[['scenario','year','layer','LAYERDZ','LAYERDEPTH','LAYERDEPTHBOT']],dt2,on=['scenario','year','layer'], how='outer')
    ty = ty[ty['LAYERDEPTH']>=0]
    plt.set_cmap('bwr')
    if seas10[v].min() > 0:
      norm = mplc.TwoSlopeNorm(vmin=seas10[v].min(), vcenter=1.00001*seas10[v].min(), vmax=seas10[v].max())
    else:
      norm = mplc.TwoSlopeNorm(vmin=seas10[v].min(), vcenter=0, vmax=seas10[v].max())
    cmap = plt.cm.ScalarMappable(norm=norm,cmap=plt.set_cmap('bwr'))
    cmap.set_array([])
    clrs = pd.DataFrame(plt.get_cmap('bwr')(norm(ty[v])))
    ty.reset_index(drop=True, inplace=True)
    clrs.reset_index(drop=True, inplace=True)
    result = pd.concat([ty, clrs], axis=1)
    result = result[result['layer'] >=0] 
    result.reset_index(drop=True, inplace=True)
    ncols = int(min(np.ceil(len(sclist)**0.5),6))
    nrows = int(np.ceil(len(sclist)/ncols))
    plt.figure(figsize=(12, int(0.8*12*(nrows/ncols))))
    for i in range(0,len(sclist)):
      scname=sclist[i]
#      print(scname)
      ax = plt.subplot(nrows, ncols, i + 1)
      bottom = np.zeros(len(result['year'].drop_duplicates()))

      #For each layer in the current "scenario"
      for j in range(result['layer'].astype('int').min(),result['layer'].astype('int').max()+1):
        tmp = result[(result['scenario']==scname) & (result['layer']==j)]
        tmp = pd.merge(tmp,result['year'].drop_duplicates(),on=['year'], how='outer')
        ax.bar(tmp['year'], -tmp['LAYERDZ'], color=tmp[[0, 1, 2, 3]].to_numpy(), width=1.0, bottom=bottom)
        bottom -= tmp['LAYERDZ']
      ax.set_xlabel('year', fontsize=12)
      ax.set_ylabel('depth (m)', fontsize=12)
      ax.set_title(str(scname), fontsize=12)
      ax.plot(ald[ald['scenario']==scname]['year'], -ald[ald['scenario']==scname]['ALD'], c='blue', linewidth=1.5,linestyle='dashed')
      ax.plot(olt[olt['scenario']==scname]['year'], -olt[olt['scenario']==scname]['OLT'], c='black', linewidth=1.5,linestyle='dashed')
      ax.plot(olt[olt['scenario']==scname]['year'], -olt[olt['scenario']==scname]['OLT'], c='black', linewidth=1.5,linestyle='dashed')
    plt.subplots_adjust(left=0.1,bottom=0.1, right=0.8, top=0.85,wspace=0.4,hspace=0.4)
    cax = plt.axes([0.85, 0.1, 0.025, 0.8])
    #plt.colorbar(cax=cax).set_label(label='Soil temp (oC))',rotation = 270, fontsize=12, labelpad=25)
    plt.colorbar(cmap,cax=cax).set_label(label=str(v),rotation = 270, fontsize=12, labelpad=25)
    plt.suptitle('Environmental Annual Profile', fontsize=20)
    plt.savefig(os.path.join(simpath,'results',oname + '_' + str(v) + '_annual.png'), bbox_inches='tight',dpi=300, transparent=False)
    plt.close()
  


def vegdynamic(simpath,simlist,vlist,sclist,oname,stage):
  for v in vlist:
#    print(v)
    data = pd.DataFrame()
    for i in range(len(simlist)):
      simlist[i]
      PODout = (os.path.join(simpath,simlist[i],'output'))
#      print(PODout)
      fileglob = glob.glob(PODout + '/' + str(v) + "_*_" + stage + ".nc")
      if len(fileglob) > 0:
        filepath = fileglob[0]

        ds = load_reduced_dataframe(filepath, xidx=0, yidx=0)

        if 'pftpart' in ds.columns.values.tolist():
          ds = pd.DataFrame(ds.groupby(['year','month','pft'])[v].sum())

        out = pd.DataFrame(ds.groupby(['year','pft'])[v].max())
        out.reset_index(inplace=True)
        out['scenario'] = sclist[i]
        data = pd.concat([data,out],axis=0)

    ncols = int(min(np.ceil(len(sclist)**0.5),6))
    nrows = int(np.ceil(len(sclist)/ncols))
    plt.figure(figsize=(12, int(0.8*12*(nrows/ncols))))
    for i in range(0,len(sclist)):
      scname=sclist[i]
#      print(scname)
      ax = plt.subplot(nrows, ncols, i + 1)
      bottom = np.zeros(len(data['year'].drop_duplicates()))
      for j in range(data['pft'].astype('int').min(),data['pft'].astype('int').max()+1):
        tmp = data[(data['scenario']==scname) & (data['pft']==j)]
        tmp = pd.merge(tmp,data['year'].drop_duplicates(),on=['year'], how='outer')
        pftname = 'PFT' + str(j)
        ax.bar(tmp['year'], tmp[v], color=pftcolorlist[j], label=pftname, width=1.0, bottom=bottom)
        bottom += tmp[v]
      ax.set_xlabel('time', fontsize=12)
      ax.set_ylabel(str(v), fontsize=12)
      ax.set_title(str(scname), fontsize=12)

    if len(sclist) % ncols == 0:
      anchor = (1.2, 1)
      rs = 0.75
    else:
      anchor = (1.2, 0.2)
      rs = 0.9

    plt.subplots_adjust(left=0.1,bottom=0.1, right=rs, top=0.9,wspace=0.5,hspace=0.5)
    handles, labels = ax.get_legend_handles_labels()
    plt.legend(handles[0:len(sclist)], labels[0:len(sclist)], bbox_to_anchor=anchor, loc='center left', borderaxespad=0.1, fontsize=11)
    plt.suptitle('Vegetation dynamic (seasonal maximum)', fontsize=20)
    plt.savefig(os.path.join(simpath,'results',oname + '_' + str(v) + '_seasonal.png'), bbox_inches='tight',dpi=300, transparent=False)
    plt.close()






### Create all plots
print("Generating single plots...")

os.mkdir(os.path.join(POD,'results'))

print("Generating timeseries flux plots...")
VARlist=['RHSOM','GPP','NPP','LTRFALC','RG','RM']
ts_flux(POD,PODlist,VARlist,scenariolist,colorlist,widthlist,'carbon','Yearly Carbon Flux Time Series','eq')

VARlist=['NUPTAKEST','NUPTAKELAB','NRESORB','NIMMOB','NETNMIN','LTRFALN']
ts_flux(POD,PODlist,VARlist,scenariolist,colorlist,widthlist,'nitrogen','Yearly Nitrogen Flux Time Series', 'eq')

VARlist=['BURNSOIL2AIRC','BURNVEG2AIRC','BURNVEG2DEADC','RHDWD', 'BURNAIR2SOILN','BURNSOIL2AIRN','BURNVEG2AIRN','BURNVEG2DEADN']
ts_flux(POD,PODlist,VARlist,scenariolist,colorlist,widthlist, 'fire', 'Yearly Wildfire Flux Time Series', 'eq')

print("Generating ts stock plots...")
VARlist=['SHLWC','DEEPC','MINEC','SOMRAWC','SOMA','SOMPR','SOMCR','VEGC']
ts_stock(POD,PODlist,VARlist,scenariolist,colorlist,widthlist, 'carbon','Yearly Carbon Stock Time Series', 'eq')

VARlist=['AVLN','ORGN','VEGN','NETNMIN','LTRFALN']
ts_stock(POD,PODlist,VARlist,scenariolist,colorlist,widthlist,'nitrogen','Yearly Nitrogen Stock Time Series','eq')

VARlist=['DEADC','DWDC','DEADN','DWDN']
ts_stock(POD,PODlist,VARlist,scenariolist,colorlist,widthlist,'wildfire','Yearly Burned C, N Stock in Time series', 'eq')

print("Generating seasonality plots...")
VARlist=['GPP','RHSOM','LAI']
seasonality(POD,PODlist,VARlist,scenariolist,colorlist,'Seas_Bio','eq')

VARlist=['SNOWTHICK','EET','PET','TRANSPIRATION','WATERTAB']
seasonality(POD,PODlist,VARlist,scenariolist,colorlist,'Seas_Env', 'eq')

print("Generating soil CN plots...")
soilcnprofile(POD,PODlist,scenariolist,'eq')

print("Generating soil env plots...")
VARlist=['TLAYER','VWCLAYER']
soilenvprofile(POD,PODlist,VARlist,scenariolist,'Profile','eq')

print("Generating vegetation dynamic plots...")
VARlist=['VEGC','VEGN']
vegdynamic(POD,PODlist,VARlist,scenariolist,'Veg_Dyn','eq')





### Merge all plots to a pdf report

print("Generating final report...")

listpng = os.listdir(os.path.join(POD,'results'))
listpng2 = [ x for x in listpng if '.png' in x ]

for png in listpng2:
  image_1 = Image.open(os.path.join(POD,'results',png))
  im_1 = image_1.convert('RGB')
  im_1.save(os.path.join(POD,'results',png.replace(".png", "") + '.pdf'))
#  os.remove(os.path.join(POD,'results',png))

if os.path.isfile(os.path.join(POD,'result.pdf')):   
  os.remove(os.path.join(POD,'result.pdf'))

listpdf = os.listdir(os.path.join(POD,'results'))
listpdf2 = [ x for x in listpdf if '.pdf' in x ]

writer = PdfWriter()
for pdf in sorted(listpdf2):
  writer.append(os.path.join(POD,'results',pdf))
  os.remove(os.path.join(POD,'results',pdf))

writer.write(os.path.join(POD,'result.pdf'))

print("Done")


