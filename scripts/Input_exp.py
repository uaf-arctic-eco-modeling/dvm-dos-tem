# Author: Helene Genet, UAF
# Creation date: Dec. 9 2021
# Purpose: this script generates modified input files for DVM-DOS-TEM simulations, following three options (see bellow comments for details)


import os
from os.path import exists
import netCDF4 as nc
import pandas as pd
import numpy as np
import xarray as xr
import argparse

def make_fake_testing_csv():
  # Generate fake sample input to test with 
  tr = pd.date_range('2004-01-01','2006-01-01',freq='M')
  fake_data = np.random.normal(0,10,len(tr))
  data = pd.DataFrame(dict(year=[i.year for i in tr],month=[i.month for i in tr], value=fake_data))
  data.to_csv('test.csv', header=True, columns=['year','month','value'], index=False)


def main():
	#### INFORMATION REQUIRED

	### PATH TO ORIGINAL INPUT DIRECTORY
	inpath = "/Users/helene/Helene/TEM/DVMDOSTEM/dvmdostem-input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_CALM_Betty_Pingo_MNT_10x10/"

	### NAME OF THE INPUT FILE
	orgin = "historic-climate.nc"

	### NAME OF THE MODIFIED INPUT FILE
	modin = "historic-climate-mod.nc"

	### VARIABLE OF INTEREST
	vmod = "tair"

	### PIXEL OF INTEREST
	xmod = 0
	ymod = 0


	### SELECT THE MODIFICATION OPTION (1,2,3): 1- YOU HAVE AN OBSERVED TIME SERIES TO REPLACE FROM ORIGINAL DATA, 2- YOU WANT TO INCREASE/DECREASE MONTHLY VALUES BY ABSOLUTE CHANGE, 3- YOU WANT TO INCREASE/DECREASE MONTHLY VALUES BY RELATIVE CHANGE (IN PERCENT)
	option = 2

	## First month (1=january ...) and year of the modified time series
	start_month = 1
	start_year = 2004
	## Last month (1=january ...) and year of the modified time series
	end_month = 12
	end_year = 2005


	if option == 1:
		# path to the modified time series: a csv file with the following headers - year, month, value. Year and month will not be used but are helpful to the user to prepare, read and check the data.
		modts = "/Users/helene/Helene/QCF/test.csv"
	elif option == 2:
		# monthly values of absolute change
		series = [0,0,0,0,0,0,900,0,0,0,0,0]
	elif option == 3:
		# monthly values of relative change (in precent)
		series = [0,0,0,0,0,50,0,0,0,0,0,0]



	#### CHECKS ON THE INFORMATION


	### Check the directory and original input file exist:

	while exists(inpath) != True:
		print ("Input directory not found")
		break

	while exists(os.path.join(inpath + orgin)) != True:
		print ("Original input file not found")
		break

	### Check the time ranges for modification fit within the time series of the input file
	if "historic" in orgin:
		while start_year > 2015 or start_year < 1901:
			print ("Correction needed: the starting year is outside the range of the historical time series")
			break

	if "projected" in orgin:
		while start_year > 2100 or start_year < 2015:
			print ("Correction needed: the starting year is outside the range of the projected time series")
			break

	if "historic" in orgin:
		while end_year > 2015 or end_year < 1901:
			print ("Correction needed: the ending year is outside the range of the historical time series")
			break

	if "projected" in orgin:
		while end_year > 2100 or end_year < 2015:
			print ("Correction needed: the ending year is outside the range of the projected time series")
			break



	#### GET START AND END YEARS OF THE ENTIRE ORIGINAL TIME SERIES 

	if "historic" in orgin:
		start_org = 1901
		end_org = 2015

	if "projected" in orgin:
		start_org = 2016
		end_org = 2100



	#### IMPORT & EXPLORE ORIGINAL DATA

	### Import the input datafile
	#org = nc.Dataset(os.path.join(inpath + orgin))
	org=xr.open_dataset(os.path.join(inpath + orgin))

	### Explore the input datafile dimensions and variables
	#for dim in org.dimensions.values():
	#	print(dim)
	#
	#for var in org.variables.values():
	#	print(var)

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
		ds=xr.open_dataset(os.path.join(inpath + orgin))
		ds[vmod][:, ymod, xmod]=result['final']
		### test the changes
		#ds[vmod][start+2, ymod, xmod]
		#ds[vmod][start-2, ymod, xmod]
		#ds[vmod][start+2, ymod+1, xmod]
		### export
		ds.to_netcdf(os.path.join(inpath + modin)) 






	#======================== OPTION 2 ========================#

	if option == 2:
		### Read the original input data
		ds=xr.open_dataset(os.path.join(inpath + orgin))
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
		ds.to_netcdf(os.path.join(inpath + modin)) 






	#======================== OPTION 3 ========================#

	if option == 3:
		### Read the original input data
		ds=xr.open_dataset(os.path.join(inpath + orgin))
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
		ds.to_netcdf(os.path.join(inpath + modin)) 

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

  main()