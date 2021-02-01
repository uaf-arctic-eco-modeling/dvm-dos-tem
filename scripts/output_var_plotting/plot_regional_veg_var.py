#! /usr/bin/env python

#This script will plot the historical, mri, and ncar outputs
# for a single vegetation variable from a regional run. Each specified
# PFT will have a subplot, and the standard deviation will be displayed as
# a translucent range around the average (mean) line.

import subprocess
import netCDF4 as nc
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma

matplotlib.use('TkAgg')


#In theory the historical output files should be the same between the mri
# and ncar runs. However, the output directories are separate. This
# script uses the historical and vegetation files from the mri directory.

# Set the values in the following section
#################################################
#################################################
var_name = "NPP"

#The data filenames will be generated automatically, so just
# put the directory here. The trailing slash is necessary.
mri_directory = "YKD/mri/"
ncar_directory = "YKD/ncar/"
#The vegetation file needs to be specified in full (not just
# the directory)
veg_filename = "YKD/mri/vegetation.nc"

#Set these based on the data:
byPFT = False
byPFTCompartment = False
Monthly = True
Yearly = False
hist_years = 115
proj_years = 85

#Specify which CMTs you want plotted. If they do not appear in the
# data set they will be skipped.
CMTs_to_plot = [4,5,6] 

#################################################
#################################################
# Everything below here should be left as-is

#Setting timestep to the right string so we can open the appropriate file
if Monthly:
  timestep = "monthly"
elif Yearly:
  timestep = "yearly"

#Construct data filenames
hist_filename = mri_directory + var_name + "_" + timestep + "_tr.nc"
mri_filename = mri_directory + var_name + "_" + timestep + "_sc.nc"
ncar_filename = ncar_directory + var_name + "_" + timestep + "_sc.nc"

print(f'Vegetation file: {veg_filename}')
print(f'Transient file: {hist_filename}')
print(f'mri file: {mri_filename}')
print(f'ncar file: {ncar_filename}')

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

#Remove specified CMTs that do not appear in the data set
for cmt in CMTs_to_plot:
  if not cmt in valid_CMTs:
    print(f'Specified CMT {cmt} not found, removing from list')
    CMTs_to_plot.remove(cmt) 
    continue

#Load data from output files
with nc.Dataset(hist_filename, 'r') as ncFile:
  data_hist = np.array(ncFile.variables[var_name][:])
  try:
    data_units = ncFile.variables[var_name].getncattr('units') 
  except KeyError:
    print("No units variable attribute found")

with nc.Dataset(mri_filename, 'r') as ncFile:
  data_mri = np.array(ncFile.variables[var_name][:])

with nc.Dataset(ncar_filename, 'r') as ncFile:
  data_ncar = np.array(ncFile.variables[var_name][:])

#The following sum calls assume the following order of dimensions:
# time, pftpart, pft, y, x
# This should be assured by dvmdostem's output

#If output is by PFT compartment, sum to by PFT or total
if byPFTCompartment:
  data_hist = np.ma.sum(data_hist, axis=1)
  data_mri = np.ma.sum(data_mri, axis=1)
  data_ncar = np.ma.sum(data_ncar, axis=1)

#If output is by PFT, sum to total
if byPFT:
  data_hist = np.ma.sum(data_hist, axis=1)
  data_mri = np.ma.sum(data_mri, axis=1)
  data_ncar = np.ma.sum(data_ncar, axis=1)

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


#Length of data sets (for length of x axis when plotting)
hist_len = len(data_hist)
proj_len = len(data_mri)


#One sub plot per selected CMT
#All sub plots will share a y axis scale
#Each sub plot will have three lines: transient, mri, and ncar, each
# with a shaded envelope around them +- standard deviation

fig = plt.figure()
fig.canvas.set_window_title(var_name)
num_rows = len(CMTs_to_plot)
num_columns = 1

#x ticks will be every 10 x units, starting from 0 and running to
# the length of transient and scenario plus ten 
#The associated labels will be the year value for each tick, starting
# at 1900 and ending ten years after the length of both transient
# and scenario stages (to force another tick for clarity)
xticks = np.arange(0, hist_len+proj_len+10, 10)
xticklabels = np.arange(1900, 1900+hist_len+proj_len+10, 10)

print(f'Plotting CMTs: {CMTs_to_plot}')
for cmt in CMTs_to_plot:
  #Finding an index so that we can identify different subplots
  CMT_index = CMTs_to_plot.index(cmt)
  #The index() function above returns a 0-based index, but the subplot
  # system uses a 1-based indexing scheme so we increment by 1.
  subplot_index = CMT_index + 1

  #Add a subplot for the current CMT, using the subplot_index to move
  # to the new subplot
  ax = fig.add_subplot(num_rows, num_columns, subplot_index, label=cmt, title="CMT "+str(cmt))

  #Setting x ticks and labels to the values defined above
  ax.set_xticks(xticks)
  ax.set_xticklabels(xticklabels)

  #Set each subplot to use the same y axis as the first subplot
  allaxes = fig.get_axes()
  allaxes[0].get_shared_y_axes().join(allaxes[0], allaxes[CMT_index])

  #Create a mask based on the current CMT - mask out all cells
  # where the vegtype does not match.
  cmt_masked = ma.masked_where(vegtype != cmt, vegtype)
  broadcast_cmt_mask = np.broadcast_to(cmt_masked.mask, data_hist.shape)
  data_hist_cmt_masked = np.ma.array(data_hist, mask=broadcast_cmt_mask)
  #Repeat for mri and ncar
  broadcast_cmt_mask = np.broadcast_to(cmt_masked.mask, data_mri.shape)
  data_mri_cmt_masked = np.ma.array(data_mri, mask=broadcast_cmt_mask)
  data_ncar_cmt_masked = np.ma.array(data_ncar, mask=broadcast_cmt_mask)

  #Calculate the mean per year
  data_hist_avg = np.ma.mean(data_hist_cmt_masked, axis=(1,2))
  data_mri_avg = np.mean(data_mri_cmt_masked, axis=(1,2))
  data_ncar_avg = np.mean(data_ncar_cmt_masked, axis=(1,2))

  #Calculate standard deviation per timestep
  data_hist_stddev = np.ma.std(data_hist_cmt_masked, axis=(1,2))
  data_mri_stddev = np.ma.std(data_mri_cmt_masked, axis=(1,2))
  data_ncar_stddev = np.ma.std(data_ncar_cmt_masked, axis=(1,2))


  #Calculating the upper and lower bounds for the standard deviation
  # "envelope" around the plotted line
  hist_lower_bound = [a_i - b_i for a_i, b_i in zip(data_hist_avg, data_hist_stddev)]
  hist_upper_bound = [a_i + b_i for a_i, b_i in zip(data_hist_avg, data_hist_stddev)]

  #Plot the average line
  ax.plot(range(hist_len), data_hist_avg, label='Transient')

  #Plot the "envelope" plus and minus standard deviation
  ax.fill_between(range(hist_len), hist_lower_bound, hist_upper_bound, alpha=0.5)


  #Repeating for mri
  mri_low_bound = [a_i - b_i for a_i, b_i in zip(data_mri_avg, data_mri_stddev)]
  mri_up_bound = [a_i + b_i for a_i, b_i in zip(data_mri_avg, data_mri_stddev)]

  ax.plot(range(hist_len, hist_len+proj_len), data_mri_avg, label='mri')
  ax.fill_between(range(hist_len, hist_len+proj_len), mri_up_bound, mri_low_bound, alpha=0.3)

  #Repeating for ncar
  ncar_low_bound = [a_i - b_i for a_i, b_i in zip(data_ncar_avg, data_ncar_stddev)]
  ncar_up_bound = [a_i + b_i for a_i, b_i in zip(data_ncar_avg, data_ncar_stddev)]

  ax.plot(range(hist_len, hist_len+proj_len), data_ncar_avg, label='ncar')
  ax.fill_between(range(hist_len, hist_len+proj_len), ncar_up_bound, ncar_low_bound, alpha=0.3)

  ax.legend()

x_label = 'Year'
y_label = f'{data_units} (if monthly summed to yearly)'

fig.text(0.5, 0.04, x_label, ha='center', va='center', fontsize=18)
fig.text(0.06, 0.5, y_label, ha='center', va='center', fontsize=18, rotation='vertical')


#Display the plot
plt.show()


exit()


