#!/usr/bin/env python

#  June 2023
# H. Genet - initial framework 
# T. Carman - adjustments for slightly  different plots, re-usable, 
# consistent formatting

import xarray as xr
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

# Concept is that there will be a main directory for the test with a
# subdirectory for the master (base) branch to check against and a sub directory
# for the branch being tested. inside each of these will be two directories: one
# for the restart run and one for the continuous run.
#
#  test_PR593/
#      | plot_1.png
#      | plot_2.png
#      | etc....
#      |
#      | - base/
#      |     | - continuous/
#      |     | - restart/
#      |
#      |  - fix/
#            | - continuous/
#            | - restart/


WORKDIR = '/data/workflows/test_PR593'
SAVE_FIGS_LOCATION = WORKDIR
PSDlist = ['fix/continuous','fix/restart']
BASElist = ['base/continuous','base/restart']


# Make one massive dataframe that has columns for each "test case" and rows for 
# every variable. If you enable ALL variables at monthly, pft and layer
# resolution, this comes out to ~1.2million rows! The rows are setup such that
# each variable is represented in its full timeseries, then the next variable
tr = pd.DataFrame(columns=['time','pft','pftpart','layer','variable'])
for test_dir in PSDlist + BASElist:
  PSDout = os.path.join(WORKDIR, test_dir, 'output')
  print(PSDout)
  VARlist = os.listdir(PSDout)
  VARlist = [f for f in VARlist if os.path.isfile(os.path.join(PSDout, f))] 
  VARlist = [f for f in VARlist if '_tr.nc' in f] 
  VARlist = [f.split("_",1)[0] for f in VARlist]
  print(VARlist)
  dt = pd.DataFrame()
  for VAR in VARlist:
    print(VAR)
    ds = xr.open_dataset(glob.glob(PSDout + '/' + VAR + "_*_tr.nc")[0])
    ds = ds.to_dataframe()
    ds.reset_index(inplace=True)
    ds = ds[(ds['x'] == 0)]
    ds = ds[(ds['y'] == 0)]
    #ds = ds[(ds['time'] == 0)]
    ds = ds.rename(columns={VAR: test_dir})
    ds['variable'] = VAR
    ds = ds.drop(columns=['y','x','albers_conical_equal_area'])
    dt = pd.concat([dt,ds],axis=0)
  tr = pd.merge(tr,dt,on=['time','pft','pftpart','layer','variable'], how='outer')

tr['time'] = tr['time'].astype(pd.StringDtype()).astype('|datetime64[ns]')
tr['year'] = tr['time'].dt.year
tr['month'] = tr['time'].dt.month

#from IPython import embed; embed()


# Make columns that try to summarize the "percent diff" between the 
# run w/ restart and w/o restart. Do this for the "base case" (master branch)
# and the "fix case" (fix_restart branch)
tr['diff_pct_fix'] = 100 * abs(tr['fix/restart'] - tr['fix/restart']) / tr['fix/continuous']
tr['diff_pct_base'] = 100 * abs(tr['base/restart'] - tr['base/continuous']) / tr['base/continuous']

tr[tr['diff_pct_fix'] > 0.1]
tr[(tr['year']==1901) & (tr['variable'] == 'VEGC')]

from IPython import embed; embed()
Save this monster dataframe so we don't have to re-create it every time...
pd.to_pickle(tr, os.path.join(SAVE_FIGS_LOCATION, 'data.pkl'))

tr = pd.read_pickle(os.path.join(SAVE_FIGS_LOCATION, 'data.pkl'))
### Plotting the outputs by groups of variables
VARlist1 = ['GPP','RH','NETNMIN','EET','PET','LTRFALC','LTRFALN','RM','RG','INGPP']
VARlist2 = ['ALD','VEGC','VEGN','WATERTAB','SHLWC','DEEPC','MINEC','AVLN','ORGN']
VARlist3 = ['LAYERTYPE','LAYERDEPTH','LAYERDZ','TLAYER']
VARlist4 = ['VEGC','VEGN']

for VAR in VARlist1:
   ds = tr[tr['variable']==VAR][0:10]
   print(ds)

out1 = pd.DataFrame()
for VAR in VARlist1:
  print(VAR)
  ds = tr[tr['variable'] == VAR].groupby(
    ['year','variable']
  ).agg(    
    fix_restart=('fix/restart','sum'),
    fix_cont=('fix/continuous','sum'),
    base_restart=('base/restart', 'sum'),
    base_cont=('base/continuous', 'sum'),
  ).reset_index()
  out1 = pd.concat([out1,ds], axis=0)

out2 = pd.DataFrame()
for VAR in VARlist2:
  print(VAR)
  ds = tr[(tr['variable'] == VAR) & (tr['month'] == 1)].groupby(
    ['year','variable']
  ).agg(
    fix_restart=('fix/restart','sum'),
    fix_cont=('fix/continuous','sum'),
    base_restart=('base/restart', 'sum'),
    base_cont=('base/continuous', 'sum'),
  ).reset_index()
  out2 = pd.concat([out2,ds],axis=0)

out3 = pd.DataFrame()
for VAR in VARlist3:
  print(VAR)
  ds = tr[(tr['variable'] == VAR) & (tr['year'] == 1901)].groupby(
    ['layer','variable']
  ).agg(
    fix_restart=('fix/restart','sum'),
    fix_cont=('fix/continuous','sum'),
    base_restart=('base/restart', 'sum'),
    base_cont=('base/continuous', 'sum'),
  ).reset_index()
  out3 = pd.concat([out3,ds],axis=0)

out4 = pd.DataFrame()
for VAR in VARlist4:
  print(VAR)
  ds = tr[(tr['variable'] == VAR) & (tr['year'] == 1901)].groupby(
    ['pft','variable']
  ).agg(
    fix_restart=('fix/restart','sum'),
    fix_cont=('fix/continuous','sum'),
    base_restart=('base/restart', 'sum'),
    base_cont=('base/continuous', 'sum'),
  ).reset_index()
  out4 = pd.concat([out4,ds],axis=0)

#from IPython import embed; embed()
base_cont_props = dict(linewidth=4, zorder=1, color='black', linestyle='solid', label='base cont')
base_restart_props = dict(linewidth=3, zorder=2, color='blue', linestyle='dotted', label='base rest')
fix_cont_props = dict(linewidth=2, zorder=3, color='orange', linestyle='solid', label='fix cont')
fix_restart_props = dict(linewidth=1, zorder=4, color='red', linestyle='dashed', label='fix rest')

plt.figure(figsize=(10, 10))
plt.subplots_adjust(hspace=0.3)
ncols = 2
nrows = 5
for i in range(0,len(VARlist1)):
    ax = plt.subplot(nrows, ncols, i + 1)
    VAR = VARlist1[i]
    x = out1[out1['variable'] == VAR]['year'][0:10]
    ax.plot(x, out1[out1['variable'] == VAR]['fix_restart'][0:10], **fix_restart_props )
    ax.plot(x, out1[out1['variable'] == VAR]['fix_cont'][0:10], **fix_cont_props)
    ax.plot(x, out1[out1['variable'] == VAR]['base_restart'][0:10], **base_restart_props)
    ax.plot(x, out1[out1['variable'] == VAR]['fix_cont'][0:10], **base_cont_props)
    ax.set_title(str(VAR), fontsize=7)
    ax.tick_params(labelsize=6)

plt.tight_layout()
plt.savefig(os.path.join(SAVE_FIGS_LOCATION,'TS_flux.png'), format="png", bbox_inches="tight")
#plt.show()

plt.figure(figsize=(6, 6))
plt.subplots_adjust(hspace=0.3)
ncols = 2
nrows = 5
for i in range(0,len(VARlist2)):
    ax = plt.subplot(nrows, ncols, i + 1)
    VAR = VARlist2[i]
    x = out2[out2['variable'] == VAR]['year'][0:20]
    ax.plot(x, out2[out2['variable'] == VAR]['fix_restart'][0:20], **fix_restart_props)
    ax.plot(x, out2[out2['variable'] == VAR]['fix_cont'][0:20], **fix_cont_props)
    ax.plot(x, out2[out2['variable'] == VAR]['base_restart'][0:20], **base_restart_props)
    ax.plot(x, out2[out2['variable'] == VAR]['base_cont'][0:20], **base_cont_props)
    ax.set_title(str(VAR), fontsize=7)
    ax.tick_params(labelsize=6)

plt.tight_layout()
plt.savefig(os.path.join(SAVE_FIGS_LOCATION, 'TS_perm_stock_first20.png'), format="png", bbox_inches="tight")
#plt.show()

plt.figure(figsize=(6, 6))
plt.subplots_adjust(hspace=0.3)
ncols = 2
nrows = 5
for i in range(0,len(VARlist3)):
    ax = plt.subplot(nrows, ncols, i + 1)
    VAR = VARlist3[i]
    x = out3[out3['variable'] == VAR]['layer']
    ax.plot(x, out3[out3['variable'] == VAR]['fix_restart'], **fix_restart_props)
    ax.plot(x, out3[out3['variable'] == VAR]['fix_cont'], **fix_cont_props)
    ax.plot(x, out3[out3['variable'] == VAR]['base_restart'], **base_restart_props)
    ax.plot(x, out3[out3['variable'] == VAR]['base_cont'], **base_cont_props)
    ax.set_title(str(VAR), fontsize=7)
    ax.tick_params(labelsize=6)

plt.tight_layout()
plt.savefig(os.path.join(SAVE_FIGS_LOCATION, 'Soil_profile.png'), format="png", bbox_inches="tight")
#plt.show()

plt.figure(figsize=(6, 6))
plt.subplots_adjust(hspace=0.3)
ncols = 1
nrows = 2
for i in range(0,len(VARlist4)):
    ax = plt.subplot(nrows, ncols, i + 1)
    VAR = VARlist4[i]
    x = out4[out4['variable'] == VAR]['pft']
    ax.plot(x, out4[out4['variable'] == VAR]['fix_restart'], **fix_restart_props)
    ax.plot(x, out4[out4['variable'] == VAR]['fix_cont'], **fix_cont_props)
    ax.plot(x, out4[out4['variable'] == VAR]['base_restart'], **base_restart_props)
    ax.plot(x, out4[out4['variable'] == VAR]['base_cont'], **base_cont_props)
    ax.set_title(str(VAR), fontsize=7)
    #ax.get_legend().remove()
    ax.tick_params(labelsize=6)

plt.tight_layout()
plt.savefig(os.path.join(SAVE_FIGS_LOCATION, 'Veg_dist.png'), format="png", bbox_inches="tight")
#plt.show()


# Experimental...
# x3 = tr[tr['variable']=='GPP'].groupby(['time','pft']).agg(
#    fix_restart=('fix/restart', 'sum'), 
#    base_restart=('base/restart', 'sum'),
#    fix_cont=('fix/continuous','sum'),
#    base_cont=('base/continuous','sum')
# ).groupby('time').agg(
#     fix_restart=('fix_restart', 'sum'),
#     base_restart=('base_restart', 'sum'),
#     fix_cont=('fix_cont','sum'),
#     base_cont=('base_cont','sum'),
# )