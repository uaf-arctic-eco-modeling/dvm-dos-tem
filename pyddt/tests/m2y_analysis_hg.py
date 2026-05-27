#!/usr/bin/env python

#### Run command
### 1. Prepare the output_spec.csv files for four scenarios (yearly/ecosystem, monthly/ecosystem, monthly/pft/layer, monthly/pft/part)
### 2. cd /data/workflows/TILE_testing/
### 3. cp ./run-mask.nc ./run-mask_original.nc
### 4. ncap2 -O -h -s'run(:,:) = 0' ./run-mask.nc ./run-mask.nc
### 5. ncap2 -O -h -s'run(0,0) = 1' ./run-mask.nc ./run-mask.nc
### 6. cp output_spec_scenario.csv output_spec.csv
### 7. /work/dvmdostem -l err -f ./config/config.js -p 100 -e 200 -s 10 -t 3
### 8. mv -r ./output ./output_scenario
### 9. mkdir ./output

#### Analysis of the results

import os
import xarray as xr
import pandas as pd

tolerance = 0.000001
outdir = 'temp_outputs/reco_output_debugging/3_outputs_for_analysis/'
sc_list = ('y', 'm', 'm_pft_layer', 'm_pft_part')






### Month to year test


varlist = ('AVLN','DEEPC','EET','GPP','HKDEEP','LAI','LFVC','LFVN','MINEC','NETNMIN','NIMMOB','NPP','NRESORB','NUPTAKELAB','NUPTAKEST','ORGN','PET','QDRAINAGE','QINFILTRATION','QRUNOFF','RAINFALL','RG','RHSOM','RM','SHLWC','SNOWFALL','SNOWTHICK','SOMA','SOMCR','SOMPR','SOMRAWC','SWE','TCDEEP','TDEEP','TRANSPIRATION','TSHLW','VEGC','VEGNSTR','VWCDEEP','WATERTAB')
statlist = ('stock','stock','flux','flux','mean','mean','flux','flux','stock','flux','flux','flux','flux','flux','flux','stock','flux','flux','flux','flux','flux','flux','flux','flux','stock','flux','stock','stock','stock','stock','stock','mean','mean','mean','flux','mean','stock','stock','mean','mean')

sc = 'y'
yearly = pd.DataFrame(columns = ['year'])
for i, var in enumerate(varlist):
  print(var)
  dd = xr.open_dataset(os.path.join(outdir,'output_'+str(sc), var + '_yearly_tr.nc')).isel(x=0, y=0)
  dd['time'] = dd.indexes['time'].to_datetimeindex()
  dd = dd.to_dataframe()
  dd.reset_index(inplace=True)
  dd['year'] = dd['time'].dt.year
  dd = dd.drop(columns=['time'])
  dd = dd.drop(columns=['albers_conical_equal_area'])
  yearly = pd.merge(yearly, dd, on=['year'], how='outer')


sc = 'm'
monthly = pd.DataFrame(columns = ['year','month'])
m2y = pd.DataFrame(columns = ['year'])
for i, var in enumerate(varlist):
  dd = xr.open_dataset(os.path.join(outdir,'output_'+str(sc), var + '_monthly_tr.nc')).isel(x=0, y=0)
  dd['time'] = dd.indexes['time'].to_datetimeindex()
  dd = dd.to_dataframe()
  dd.reset_index(inplace=True)
  dd['year'] = dd['time'].dt.year
  dd['month'] = dd['time'].dt.month
  dd = dd.drop(columns=['time'])
  dd = dd.drop(columns=['albers_conical_equal_area'])
  monthly = pd.merge(monthly, dd, on=['year','month'], how='outer')
  if statlist[i] == 'flux':
    dy = pd.DataFrame(dd.groupby('year')[var].sum())
  if statlist[i] == 'mean':
    dy = pd.DataFrame(dd.groupby('year')[var].mean())
  if statlist[i] == 'stock':
    dy = dd[dd['month'] == 12]
    dy = dy.drop(columns=['month'])
  dy.reset_index(inplace=True)
  if 'index' in dy.columns:
    dy = dy.drop(columns=['index'])
#  dy = dy.rename(columns={var: var + '_m2y'}) 
  m2y = pd.merge(m2y, dy, on=['year'], how='outer')


test = pd.DataFrame((m2y-yearly).mean())
test.reset_index(inplace=True)
test = test.rename(columns={'index': 'varname', 0:'diffmean'}) 

test[abs(test['diffmean']) > tolerance]

print("Monthly to yearly")
print(varlist)
print(test)


###  pft to ecosystem test

varlist = ('EET','GPP','LAI','LFVC','LFVN','NPP','NRESORB','NUPTAKELAB','NUPTAKEST','PET','RG','RM','VEGC','VEGNSTR')

sc = 'm_pft_layer'
pft = pd.DataFrame(columns = ['year','month','pft'])
for i, var in enumerate(varlist):
  dd = xr.open_dataset(os.path.join(outdir,'output_'+str(sc), var + '_monthly_tr.nc')).isel(x=0, y=0)
  dd['time'] = dd.indexes['time'].to_datetimeindex()
  dd = dd.to_dataframe()
  dd.reset_index(inplace=True)
  dd['year'] = dd['time'].dt.year
  dd['month'] = dd['time'].dt.month
  dd = dd.drop(columns=['time'])
  dd = dd.drop(columns=['albers_conical_equal_area'])
  pft = pd.merge(pft, dd, on=['year','month','pft'], how='outer')

pft2eco = pft.groupby(['year','month']).sum()
pft2eco.reset_index(inplace=True)
pft2eco = pft2eco.drop(columns=['pft'])

test = pd.DataFrame((pft2eco-monthly).mean())
test.reset_index(inplace=True)
test = test.rename(columns={'index': 'varname', 0:'diffmean'}) 

test[abs(test['diffmean']) > tolerance]

#breakpoint()

print("PFT to Ecosystem")
print(varlist)
print(test)




###  part to pft test

varlist = ('GPP','LFVC','LFVN','NPP','NRESORB','NUPTAKEST','RG','RM','VEGC','VEGNSTR')

sc = 'm_pft_part'
part = pd.DataFrame(columns = ['year','month','pft','pftpart'])
for i, var in enumerate(varlist):
  dd = xr.open_dataset(os.path.join(outdir,'output_'+str(sc), var + '_monthly_tr.nc')).isel(x=0, y=0)
  dd['time'] = dd.indexes['time'].to_datetimeindex()
  dd = dd.to_dataframe()
  dd.reset_index(inplace=True)
  dd['year'] = dd['time'].dt.year
  dd['month'] = dd['time'].dt.month
  dd = dd.drop(columns=['time'])
  dd = dd.drop(columns=['albers_conical_equal_area'])
  part = pd.merge(part, dd, on=['year','month','pft','pftpart'], how='outer')

part2pft = part.groupby(['year','month','pft']).sum()
part2pft.reset_index(inplace=True)
part2pft = part2pft.drop(columns=['pftpart'])

test = pd.DataFrame((part2pft-pft).mean())
test.reset_index(inplace=True)
test = test.rename(columns={'index': 'varname', 0:'diffmean'}) 

test[abs(test['diffmean']) > tolerance]

#breakpoint()
print("Compartment to PFT")
print(varlist)
print(test)



###  layer to column test

varlist = ('AVLN','NETNMIN','NIMMOB','ORGN','RHSOM','SOMA','SOMCR','SOMPR','SOMRAWC')

sc = 'm_pft_layer'
layer = pd.DataFrame(columns = ['year','month','layer'])
for i, var in enumerate(varlist):
  dd = xr.open_dataset(os.path.join(outdir,'output_'+str(sc), var + '_monthly_tr.nc')).isel(x=0, y=0)
  dd['time'] = dd.indexes['time'].to_datetimeindex()
  dd = dd.to_dataframe()
  dd.reset_index(inplace=True)
  dd['year'] = dd['time'].dt.year
  dd['month'] = dd['time'].dt.month
  dd = dd.drop(columns=['time'])
  dd = dd.drop(columns=['albers_conical_equal_area'])
  layer = pd.merge(layer, dd, on=['year','month','layer'], how='outer')

layer2column = layer.groupby(['year','month']).sum()
layer2column.reset_index(inplace=True)
layer2column = layer2column.drop(columns=['layer'])

test = pd.DataFrame((layer2column-monthly).mean())
test.reset_index(inplace=True)
test = test.rename(columns={'index': 'varname', 0:'diffmean'}) 

test[abs(test['diffmean']) > tolerance]

#breakpoint()
print("Layer to Ecosystem")
print(varlist)
print(test)
