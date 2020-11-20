#! /usr/bin/env python

import subprocess
import netCDF4 as nc
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma

matplotlib.use('TkAgg')


#Timeseries of average annual NPP
#Sum monthly fluxes to years
#Produce graph from 1901-2100
#Historical to 2015, then two scenario lines to 2100
#x is time
#y is average annual NPP, gC/m2/year
#"envelope" of +- stand deviation based on pixels



#load three files:
# transient from one of the runs
# scenario from mri
# scenario from ncar
#./??/NPP_monthly_tr.nc
#./mri/NPP_monthly_sc.nc
#./ncar/NPP_monthly_sc.nc

var_name = "NPP"

mri_directory = "mri/"
ncar_directory = "ncar/"

#Example:
byPFT = False
byPFTCompartment = False
Monthly = True
Yearly = False

CMTs_to_plot = [5,6] 

#Setting timestep to the right string so we can open the appropriate file
if Monthly:
  timestep = "monthly"
elif Yearly:
  timestep = "yearly"

hist_filename = "mri/NPP_monthly_tr.nc"
mri_filename = "mri/NPP_monthly_sc.nc"
ncar_filename = "ncar/NPP_monthly_sc.nc"
veg_filename = "vegetation-mri.nc"

#hist_filename = "toolik/NPP_monthly_tr.nc"
#veg_filename = "toolik/vegetation.nc"

#Load vegtype data for masking
with nc.Dataset(veg_filename, 'r') as ncFile:
  vegtype = np.array(ncFile.variables['veg_class'][:])

#Load data from output files
#with nc.Dataset("mri/yearly_NPP_tr.nc", 'r') as ncFile:
with nc.Dataset(hist_filename, 'r') as ncFile:
  NPP_hist = np.array(ncFile.variables[var_name][:])

with nc.Dataset(mri_filename, 'r') as ncFile:
  NPP_mri = np.array(ncFile.variables[var_name][:])

with nc.Dataset(ncar_filename, 'r') as ncFile:
  NPP_ncar = np.array(ncFile.variables[var_name][:])


#If monthly, sum across time to make it yearly
if Monthly:
  months_per_year = 12

  #Split the array with a stride of 12, to isolate each year's
  # monthly values
  yearly_index = np.arange(12,1380,months_per_year)
  yearly_split = np.array(np.split(NPP_hist, yearly_index, axis=0))
#  print(yearly_split.shape)

  #Sum along axis index 1, to end up with a 3D array with dimensions
  # years, x, and y
  NPP_hist = np.ma.sum(yearly_split, axis=1)

  #Repeat the process for projected data
  yearly_index = np.arange(12,1020,months_per_year)
  #mri
  yearly_split = np.array(np.split(NPP_mri, yearly_index, axis=0))
  NPP_mri = np.ma.sum(yearly_split, axis=1)
  #ncar
  yearly_split = np.array(np.split(NPP_ncar, yearly_index, axis=0))
  NPP_ncar = np.ma.sum(yearly_split, axis=1)


#Masking out values less than -5000 
# (mostly to catch the fill value from the nc file)
NPP_hist = ma.masked_less(NPP_hist, -5000)
NPP_mri = ma.masked_less(NPP_mri, -5000)
NPP_ncar = ma.masked_less(NPP_ncar, -5000)


#One plot (historic, mri, ncar) per selected CMT
# Same y range
#all_CMTs,CMT_cell_count = np.unique(vegtype, return_counts=True)
#all_CMTs = list(zip(all_CMTs, CMT_cell_count))

#CMTs_to_plot = np.array([cmt for cmt in all_CMTs if cmt[0] != 0])
#print(CMTs_to_plot)


#Length of data sets (for plotting)
hist_len = len(NPP_hist)
proj_len = len(NPP_mri)



#Make a masked array per CMT plot wanted
#This does a single CMT for experimentation

CMT_count = len(CMTs_to_plot)
#fig, axes = plt.subplots(nrows=CMT_count, ncols=1)
fig = plt.figure()

for cmt in CMTs_to_plot:
  print("Plotting cmt: " + str(cmt))
  num_columns = 1
  ax = fig.add_subplot(CMT_count, num_columns, cmt-4, label=cmt, title=str(cmt))

  cmt_masked = ma.masked_where(vegtype != cmt, vegtype)
  broadcast_cmt_mask = np.broadcast_to(cmt_masked.mask, NPP_hist.shape)
  NPP_hist_cmt_masked = np.ma.array(NPP_hist, mask=broadcast_cmt_mask)
  #Repeat for mri and ncar
  broadcast_cmt_mask = np.broadcast_to(cmt_masked.mask, NPP_mri.shape)
  NPP_mri_cmt_masked = np.ma.array(NPP_mri, mask=broadcast_cmt_mask)
  NPP_ncar_cmt_masked = np.ma.array(NPP_ncar, mask=broadcast_cmt_mask)

  #Calculate the mean per year
  NPP_hist_avg = np.ma.mean(NPP_hist_cmt_masked, axis=(1,2))
  #print("NPP_hist_avg sample: ")
  #print(NPP_hist_avg[0:4])
  NPP_mri_avg = np.mean(NPP_mri_cmt_masked, axis=(1,2))
  NPP_ncar_avg = np.mean(NPP_ncar_cmt_masked, axis=(1,2))

  #Calculate standard deviation per timestep
  NPP_hist_stddev = np.ma.std(NPP_hist_cmt_masked, axis=(1,2))
  #print("NPP_hist_stddev: ")
  #print(NPP_hist_stddev[0:4])
  #print(NPP_hist.mask)
  NPP_mri_stddev = np.ma.std(NPP_mri_cmt_masked, axis=(1,2))
  NPP_ncar_stddev = np.ma.std(NPP_ncar_cmt_masked, axis=(1,2))


  #Calculating the upper and lower bounds for the standard deviation
  # "envelope" around the plotted line
  hist_lower_bound = [a_i - b_i for a_i, b_i in zip(NPP_hist_avg, NPP_hist_stddev)]
  hist_upper_bound = [a_i + b_i for a_i, b_i in zip(NPP_hist_avg, NPP_hist_stddev)]

  #Plot the average line
  ax.plot(range(hist_len), NPP_hist_avg)

  #Plot the "envelope" plus and minus standard deviation
  ax.fill_between(range(hist_len), hist_lower_bound, hist_upper_bound, alpha=0.5)


  #Repeating for mri
  mri_low_bound = [a_i - b_i for a_i, b_i in zip(NPP_mri_avg, NPP_mri_stddev)]
  mri_up_bound = [a_i + b_i for a_i, b_i in zip(NPP_mri_avg, NPP_mri_stddev)]

  ax.plot(range(hist_len, hist_len+proj_len), NPP_mri_avg)
  ax.fill_between(range(hist_len, hist_len+proj_len), mri_up_bound, mri_low_bound, alpha=0.3)


  #Repeating for ncar
  ncar_low_bound = [a_i - b_i for a_i, b_i in zip(NPP_ncar_avg, NPP_ncar_stddev)]
  ncar_up_bound = [a_i + b_i for a_i, b_i in zip(NPP_ncar_avg, NPP_ncar_stddev)]

  ax.plot(range(hist_len, hist_len+proj_len), NPP_ncar_avg)
  ax.fill_between(range(hist_len, hist_len+proj_len), ncar_up_bound, ncar_low_bound, alpha=0.3)


#Display the plot
plt.show()


exit()


