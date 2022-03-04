#!/usr/bin/env python

# Author: Helene Genet, UAF
# Creation date: Dec. 9 2021
# Purpose: this script generates modified input files for DVM-DOS-TEM simulations, following three options (see bellow comments for details)


import os
from os.path import exists
import netCDF4 as nc
import pandas as pd
import numpy as np
import json
import xarray as xr
import argparse
import matplotlib.pyplot as plt
import datetime


# Some constants...
### NAME OF THE INPUT FILE
ORGIN = "historic-climate.nc"

### NAME OF THE MODIFIED INPUT FILE
MODIN = "historic-climate-mod.nc"

def plot_outputs(outpath):
  '''
  Hack together a quick plot. Bunch of hard-coded stuff:
  variables to plot time slices, etc.

  But is shold work as a proof of concept. Makes one plot for
  each modificaton case (1, 2, 3), one plot for the "base case"
  and one plot that shows them all together.
  '''
  print('junk')
  os.chdir(outpath)

  plt.close()
  fig, axes = plt.subplots(5)

  VAR = 'NPP'
  START = 500

  for ax in axes[0:4]:
    ax.sharex(axes[4])

  runcases = os.listdir('.')
  runcases = sorted([x for x in runcases if '.DS' not in x])
  #runcases = 'basecase,modopt1,modopt2,modopt3'.split(',')
  for i, (CASE, color) in enumerate(zip(runcases,'red,black,green,orange'.split(','))):
      data = nc.Dataset('{}/output/{}_monthly_tr.nc'.format(CASE, VAR))
      times = nc.num2date(data.variables['time'], data.variables['time'].units)
      t2 = [datetime.datetime.fromisoformat(x.isoformat()) for x in times]
      axes[4].set_ylabel('{} {}'.format(VAR, data.variables[VAR].units))
      axes[4].plot(t2[START:], data.variables[VAR][START:,0,0], color=color, label=CASE)
      axes[i].plot(t2[START:], data.variables[VAR][START:,0,0], color=color, label=CASE)

  for ax in axes:
    ax.legend(loc='upper right', fontsize='x-small')
  
  plt.show(block=True)

def plot_inputs(inpath, outpath, ORGIN, MODIN):
  original = nc.Dataset(os.path.join(inpath, ORGIN))
  modified = nc.Dataset(os.path.join(outpath, MODIN))
  print(original.variables['tair'])
  print(modified.variables['tair'])
  plt.plot(original.variables['tair'][:,0,0], label='original',marker='o',alpha=.5)
  plt.plot(modified.variables['tair'][:,0,0], label='modified',marker='^',alpha=.5)
  plt.legend()
  
  #plt.show(block=True)
  print(outpath)
  #Save figure plotting original vs modified csv to be saved in workshop-lab2/modopt1/ path
  newfilename=os.path.join(outpath,'orig_vs_mod.png')
  plt.savefig(newfilename)

def make_fake_testing_csv():
  # Generate fake sample input to test with 
  tr = pd.date_range('2004-01-01','2006-01-01',freq='M')
  fake_data = np.random.normal(0,10,len(tr))
  data = pd.DataFrame(dict(year=[i.year for i in tr],month=[i.month for i in tr], value=fake_data))
  data.to_csv('test.csv', header=True, columns=['year','month','value'], index=False)


def fix_config(workdir, modified_file_name):
  '''Changes config path to be relative so as to use the modified file.'''
  cfgfile = os.path.join(workdir, 'config/config.js')
  if not os.path.exists(cfgfile):
    print("No config file to adjust. Nothing to do.")
    return None
  else:
    with open(cfgfile) as f:
      jd = json.load(f)
    jd['IO']['hist_climate_file'] = modified_file_name
    with open(cfgfile, 'w') as f:
      json.dump(jd, f, indent=2)



def main(inpath, outpath, option,usercsv=''):
  #### INFORMATION REQUIRED

  ### SELECT THE MODIFICATION OPTION (1,2,3): 
  # 1- YOU HAVE AN OBSERVED TIME SERIES TO REPLACE FROM ORIGINAL DATA, 
  # 2- YOU WANT TO INCREASE/DECREASE MONTHLY VALUES BY ABSOLUTE CHANGE, 
  # 3- YOU WANT TO INCREASE/DECREASE MONTHLY VALUES BY RELATIVE CHANGE (IN PERCENT)
  

  ### VARIABLE OF INTEREST
  vmod = "tair"

  ### PIXEL OF INTEREST
  xmod = 0
  ymod = 0



  ## First month (1=january ...) and year of the modified time series
  start_month = 1
  start_year = 2004
  ## Last month (1=january ...) and year of the modified time series
  end_month = 12
  end_year = 2015


  if option == 1:
    if usercsv == '':
    # path to the modified time series: a csv file with the following headers - year, month, value. Year and month will not be used but are helpful to the user to prepare, read and check the data.
       modts = "test.csv"
    else:
       modts = usercsv
  elif option == 2:
    # monthly values of absolute change
    series = [0,0,0,0,0,0,0,0,0,0,0,0]
  elif option == 3:
    # monthly values of relative change (in precent)
    series = [0,0,0,0,0,0,0,0,0,0,0,0]



  #### CHECKS ON THE INFORMATION


  ### Check the directory and original input file exist:

  while exists(inpath) != True:
    print ("Input directory not found")
    break

  while exists(os.path.join(inpath, ORGIN)) != True:
    print ("Original input file not found")
    break

  ### Check the time ranges for modification fit within the time series of the input file
  if "historic" in ORGIN:
    while start_year > 2015 or start_year < 1901:
      print ("Correction needed: the starting year is outside the range of the historical time series")
      break

  if "projected" in ORGIN:
    while start_year > 2100 or start_year < 2015:
      print ("Correction needed: the starting year is outside the range of the projected time series")
      break

  if "historic" in ORGIN:
    while end_year > 2015 or end_year < 1901:
      print ("Correction needed: the ending year is outside the range of the historical time series")
      break

  if "projected" in ORGIN:
    while end_year > 2100 or end_year < 2015:
      print ("Correction needed: the ending year is outside the range of the projected time series")
      break



  #### GET START AND END YEARS OF THE ENTIRE ORIGINAL TIME SERIES 

  if "historic" in ORGIN:
    start_org = 1901
    end_org = 2015

  if "projected" in ORGIN:
    start_org = 2016
    end_org = 2100



  #### IMPORT & EXPLORE ORIGINAL DATA

  ### Import the input datafile
  #org = nc.Dataset(os.path.join(inpath, ORGIN))
  org=xr.open_dataset(os.path.join(inpath, ORGIN))

  ### Explore the input datafile dimensions and variables
  #for dim in org.dimensions.values():
  #  print(dim)
  #
  #for var in org.variables.values():
  #  print(var)

  ### Compute the portion of the time series that needs modification
  start = (start_year-start_org)*12+start_month-1
  end = (end_year-start_org)*12+end_month-1

  ### Access the original data for the variable of interest
  var_org = pd.DataFrame(org[vmod][:, ymod, xmod])
  var_org['idx'] = np.arange(len(var_org))
  var_org = var_org.rename(columns={var_org.columns[0]: 'value_org', var_org.columns[1]: "idx"})




  #======================== OPTION 1 ========================#


  #### IMPORT & EXPLORE MODIFIED TIME SERIES AND CHECK FOR GAPS

  if option == 1:
    #read the modified time series ( again, should be a csv with year, month and values in that order of headers)
    # NOTE there may be a bug with reading the last year of the modified data
    ts = pd.read_csv(modts)
    # rename the headeers to make sure they match the format used below
    ts = ts.rename(columns={ts.columns[0]: "year", ts.columns[1]: "month", ts.columns[2]: "value"})
    # order the time series
    ts = ts.sort_values(by=['year', 'month'])
    # check for gaps
    ts['time'] = ts['year'] + ts['month']/12
    ts['delta'] = ts['time'].diff()[1:]
    ts['gap'] = np.where( (np.isclose(ts['delta'],1/12,atol=1e-08)) | (ts['delta'].isnull()), 0, 1)
    while ts['gap'].sum() > 0:
      print ("there are/is ", ts['gap'].sum()," gaps in your time series, please correct.")
      break
    #### PRODUCE THE FINAL TIME SERIES, INTEGRATE IT TO THE NETCDF FILE AND EXPORT IT.
    ### Produce the final time series
    ts['idx'] = np.arange(len(ts)) + start
    ts = ts.drop(['gap','delta','time','year','month'],axis=1)
    result = pd.merge(var_org, ts, on="idx", how='outer')
    result['final'] = np.where(result['value'].isnull(), result['value_org'], result['value'])
    ## test the merging
    #result.loc[[start+2]]
    #result.loc[[start-2]]
    #### INTEGRATE THE OBSERVED DATA IN THE INPUT FILE
    ### re-read and replace
    ds=xr.open_dataset(os.path.join(inpath, ORGIN))
    ds[vmod][:, ymod, xmod]=result['final']
    ### test the changes
    #ds[vmod][start+2, ymod, xmod]
    #ds[vmod][start-2, ymod, xmod]
    #ds[vmod][start+2, ymod+1, xmod]
    ### export
    ds.to_netcdf(os.path.join(outpath, MODIN)) 






  #======================== OPTION 2 ========================#

  if option == 2:
    ### Read the original input data
    ds=xr.open_dataset(os.path.join(inpath, ORGIN))
    ### Loop through the twelve months and check that change is required, if not, then pass
    for i in range(0,12):
      if series[i] ==0 :
        print ('month',i+1,': no change for this month, pass!')
      ## if change is required, only change the data for the time period of choice
      else :
        print ('month',i + 1,': change =', series[i])
        for j in range(i,len(org['time'][:]),12):
          if j >= start and j <= end:
            print (j)
            ds[vmod][j, ymod, xmod]= ds[vmod][j, ymod, xmod] + series[i]
    ### test
    #ds[vmod][1242, ymod, xmod]
    #ds[vmod][1254, ymod, xmod]
    ### export the new modified data
    ds.to_netcdf(os.path.join(outpath, MODIN)) 






  #======================== OPTION 3 ========================#

  if option == 3:
    ### Read the original input data
    ds=xr.open_dataset(os.path.join(inpath, ORGIN))
    ### Loop through the twelve months and check that change is required, if not, then pass
    for i in range(0,12):
      if series[i] ==0 :
        print ('month',i+1,': no change for this month, pass!')
      ## if change is required, only change the data for the time period of choice
      else :
        print ('month',i + 1,': change =', series[i],'%')
        for j in range(i,len(org['time'][:]),12):
          if j >= start and j <= end:
            print (j)
            ds[vmod][j, ymod, xmod]= ds[vmod][j, ymod, xmod] * (1+0.01*series[i])
    ### test
    #ds[vmod][1242, ymod, xmod]
    #ds[vmod][1254, ymod, xmod]
    ### export the new modified data
    ds.to_netcdf(os.path.join(outpath, MODIN)) 

  # Done with modifications (whatever option user chose), so 
  # now adjust the config file for the model run to point to the 
  # modified file.
  # >> NOTE this is assumes that you have already setup your 
  # working directory (i.e. using setup_working_directory.py) 
  # and that you have a config.js file to modify. If you are 
  # using the Input_exp_driver.sh, then this is the case, but
  # is is possible to use this script w/o a config file. So this
  # fix config function tries to be smart and just won't do 
  # anything if there is not config.js file to be found in outpath.
  fix_config(outpath, MODIN)

if __name__ == '__main__':

  parser = argparse.ArgumentParser(
    description='''workshop, lab 2''',
    epilog='''epilog text...'''
  )

  parser.add_argument('--opt', type=int, choices=[1,2,3], 
    help='''which modification scheme to pursue''')

  parser.add_argument('--inpath', 
    help='''path to the input folder, i.e. /data/input-catalog/cru_...''')

  parser.add_argument('--outpath', 
    help='''path where you want your modified file written to, i.e. /data/workflows/workshop-lab2/modified-opt-1''')

  parser.add_argument('--plot-inputs', action='store_true',
    help='''plot the modified data vs original data''')

  parser.add_argument('--plot-outputs', action='store_true',
    help='''plot the data after the runs. --outpath in this case should be to the directory containing all the "modified cases"''')
    
  parser.add_argument('--usercsv',
    help='''path to users modified observational data, if left blank defaults to fake test data''')
    
  args = parser.parse_args()

  if args.opt == 1:
    make_fake_testing_csv()


  if args.plot_inputs:
    plot_inputs(args.inpath, args.outpath, ORGIN, MODIN)
    exit()

  if args.plot_outputs:
    plot_outputs(args.outpath)
    exit()

  else:
    main(inpath=args.inpath, outpath=args.outpath, option=args.opt,usercsv=args.usercsv)

