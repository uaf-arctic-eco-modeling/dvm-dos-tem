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

CMTs_to_plot = [2,5,7] 
hist_years = 115
proj_years = 85

#Setting timestep to the right string so we can open the appropriate file
if Monthly:
  timestep = "monthly"
elif Yearly:
  timestep = "yearly"

hist_filename = "mri/NPP_monthly_tr.nc"
mri_filename = "mri/NPP_monthly_sc.nc"
ncar_filename = "ncar/NPP_monthly_sc.nc"
veg_filename = "vegetation-mri.nc"


#Load vegtype data for masking by CMT
with nc.Dataset(veg_filename, 'r') as ncFile:
  vegtype = np.array(ncFile.variables['veg_class'][:])
#CMT types and counts from the data set
all_CMTs,CMT_cell_count = np.unique(vegtype, return_counts=True)
#Merge types and counts into a single list
all_CMTs = list(zip(all_CMTs, CMT_cell_count))
#Exclude CMT '0' because it's not real
valid_CMTs = np.array([cmt for cmt in all_CMTs if cmt[0] != 0])
print(valid_CMTs)

#Compare specified CMTs to the CMTS that actually appear in the
# data set and remove the ones that do not
for cmt in CMTs_to_plot:
  if not cmt in valid_CMTs:
    print(f'Specified CMT {cmt} not found, removing from list')
    CMTs_to_plot.remove(cmt) 
    continue

#Load data from output files
with nc.Dataset(hist_filename, 'r') as ncFile:
  data_hist = np.array(ncFile.variables[var_name][:])

with nc.Dataset(mri_filename, 'r') as ncFile:
  data_mri = np.array(ncFile.variables[var_name][:])

with nc.Dataset(ncar_filename, 'r') as ncFile:
  data_ncar = np.array(ncFile.variables[var_name][:])


#If monthly, sum across time to make it yearly
if Monthly:
  months_per_year = 12
  hist_months = hist_years * 12
  proj_months = proj_years * 12

  #Split the array with a stride of 12, to isolate each year's
  # monthly values
  yearly_index = np.arange(12, hist_months, months_per_year)
  yearly_split = np.array(np.split(data_hist, yearly_index, axis=0))

  #Sum along axis index 1, to end up with a 3D array with dimensions
  # years, x, and y
  data_hist = np.ma.sum(yearly_split, axis=1)

  #Repeat the process for projected data
  yearly_index = np.arange(12, proj_months, months_per_year)
  #mri
  yearly_split = np.array(np.split(data_mri, yearly_index, axis=0))
  data_mri = np.ma.sum(yearly_split, axis=1)
  #ncar
  yearly_split = np.array(np.split(data_ncar, yearly_index, axis=0))
  data_ncar = np.ma.sum(yearly_split, axis=1)


#Masking out values less than -5000 
# (mostly to catch the fill value from the nc file)
data_hist = ma.masked_less(data_hist, -5000)
data_mri = ma.masked_less(data_mri, -5000)
data_ncar = ma.masked_less(data_ncar, -5000)


#Length of data sets (for plotting)
hist_len = len(data_hist)
proj_len = len(data_mri)


#One plot (historic, mri, ncar) per selected CMT
# Same y range

fig = plt.figure()
num_rows = len(CMTs_to_plot)
num_columns = 1

print(CMTs_to_plot)
for cmt in CMTs_to_plot:
  print("Plotting cmt: " + str(cmt))
  CMT_index = CMTs_to_plot.index(cmt)
  subplot_index = CMT_index + 1
  ax = fig.add_subplot(num_rows, num_columns, subplot_index, label=cmt, title="CMT "+str(cmt))

  allaxes = fig.get_axes()
  allaxes[0].get_shared_y_axes().join(allaxes[0], allaxes[CMT_index])

  cmt_masked = ma.masked_where(vegtype != cmt, vegtype)
  broadcast_cmt_mask = np.broadcast_to(cmt_masked.mask, data_hist.shape)
  data_hist_cmt_masked = np.ma.array(data_hist, mask=broadcast_cmt_mask)
  #Repeat for mri and ncar
  broadcast_cmt_mask = np.broadcast_to(cmt_masked.mask, data_mri.shape)
  data_mri_cmt_masked = np.ma.array(data_mri, mask=broadcast_cmt_mask)
  data_ncar_cmt_masked = np.ma.array(data_ncar, mask=broadcast_cmt_mask)

  #Calculate the mean per year
  data_hist_avg = np.ma.mean(data_hist_cmt_masked, axis=(1,2))
  #print("data_hist_avg sample: ")
  #print(data_hist_avg[0:4])
  data_mri_avg = np.mean(data_mri_cmt_masked, axis=(1,2))
  data_ncar_avg = np.mean(data_ncar_cmt_masked, axis=(1,2))

  #Calculate standard deviation per timestep
  data_hist_stddev = np.ma.std(data_hist_cmt_masked, axis=(1,2))
  #print("data_hist_stddev: ")
  #print(data_hist_stddev[0:4])
  #print(data_hist.mask)
  data_mri_stddev = np.ma.std(data_mri_cmt_masked, axis=(1,2))
  data_ncar_stddev = np.ma.std(data_ncar_cmt_masked, axis=(1,2))


  #Calculating the upper and lower bounds for the standard deviation
  # "envelope" around the plotted line
  hist_lower_bound = [a_i - b_i for a_i, b_i in zip(data_hist_avg, data_hist_stddev)]
  hist_upper_bound = [a_i + b_i for a_i, b_i in zip(data_hist_avg, data_hist_stddev)]

  #Plot the average line
  ax.plot(range(hist_len), data_hist_avg)

  #Plot the "envelope" plus and minus standard deviation
  ax.fill_between(range(hist_len), hist_lower_bound, hist_upper_bound, alpha=0.5)


  #Repeating for mri
  mri_low_bound = [a_i - b_i for a_i, b_i in zip(data_mri_avg, data_mri_stddev)]
  mri_up_bound = [a_i + b_i for a_i, b_i in zip(data_mri_avg, data_mri_stddev)]

  ax.plot(range(hist_len, hist_len+proj_len), data_mri_avg)
  ax.fill_between(range(hist_len, hist_len+proj_len), mri_up_bound, mri_low_bound, alpha=0.3)


  #Repeating for ncar
  ncar_low_bound = [a_i - b_i for a_i, b_i in zip(data_ncar_avg, data_ncar_stddev)]
  ncar_up_bound = [a_i + b_i for a_i, b_i in zip(data_ncar_avg, data_ncar_stddev)]

  ax.plot(range(hist_len, hist_len+proj_len), data_ncar_avg)
  ax.fill_between(range(hist_len, hist_len+proj_len), ncar_up_bound, ncar_low_bound, alpha=0.3)


#Display the plot
plt.show()


exit()


