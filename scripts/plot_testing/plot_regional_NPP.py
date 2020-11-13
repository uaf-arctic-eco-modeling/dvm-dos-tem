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

#Setting timestep to the right string so we can open the appropriate file
if Monthly:
  timestep = "monthly"
elif Yearly:
  timestep = "yearly"

hist_filename = "mri/NPP_monthly_tr.nc"
mri_filename = "mri/NPP_monthly_sc.nc"
ncar_filename = "ncar/NPP_monthly_sc.nc"
veg_filename = "vegetation-mri.nc"

#Load vegtype data for masking
with nc.Dataset(veg_filename, 'r') as ncFile:
  vegtype = np.array(ncFile.variables['veg_class'][:])

#Load data from output files
#with nc.Dataset("mri/yearly_NPP_tr.nc", 'r') as ncFile:
with nc.Dataset("mri/NPP_monthly_tr.nc", 'r') as ncFile:
  NPP_hist = np.array(ncFile.variables[var_name][:])

with nc.Dataset(mri_filename, 'r') as ncFile:
  NPP_mri = np.array(ncFile.variables[var_name][:])

with nc.Dataset(ncar_filename, 'r') as ncFile:
  NPP_ncar = np.array(ncFile.variables[var_name][:])


#Masking out values less than -5000 (mostly the fill value from the nc file)
NPP_hist = ma.masked_less(NPP_hist, -5000)
NPP_mri = ma.masked_less(NPP_mri, -5000)
NPP_ncar = ma.masked_less(NPP_ncar, -5000)


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
  NPP_hist = yearly_split.sum(axis=1)

  #temp_array = NPP_hist.reshape(??, months_per_year, NPP_hist.shape[???])


#One plot (historic, mri, ncar) per selected CMT
# Same y range
all_CMTs,CMT_cell_count = np.unique(vegtype, return_counts=True)
all_CMTs = list(zip(all_CMTs, CMT_cell_count))

CMTs_to_plot = np.array([cmt for cmt in all_CMTs if cmt[0] != 0])
print(CMTs_to_plot)


#Make a masked array per CMT plot wanted
#This does a single CMT for experimentation
cmt_masked = ma.masked_where(vegtype != 5, vegtype)
print(cmt_masked)
broadcast_cmt_mask = np.broadcast_to(cmt_masked.mask, NPP_hist.shape)
NPP_hist = np.ma.array(NPP_hist, mask=broadcast_cmt_mask)
print("NPP_hist shape: " + str(NPP_hist.shape))
print(NPP_hist[0])

#Calculate the mean per year
NPP_hist_avg = np.ma.mean(NPP_hist, axis=(1,2))
print("NPP_hist_avg[0]: ")
print(NPP_hist_avg[0])

NPP_mri_avg = np.mean(NPP_mri, axis=(1,2))
NPP_ncar_avg = np.mean(NPP_ncar, axis=(1,2))

#Calculate standard deviation per timestep
NPP_hist_stddev = np.ma.std(NPP_hist, axis=(1,2))
print("NPP_hist_stddev: ")
print(NPP_hist_stddev)
#print(NPP_hist.mask)

NPP_mri_stddev = np.std(NPP_mri, axis=(1,2))
NPP_ncar_stddev = np.std(NPP_ncar, axis=(1,2))

#Length of data set (for plotting)
hist_len = len(NPP_hist)
print(hist_len)


#Calculating the upper and lower bounds for the standard deviation
# "envelope" around the plotted line
hist_lower_bound = [a_i - b_i for a_i, b_i in zip(NPP_hist_avg, NPP_hist_stddev)]
hist_upper_bound = [a_i + b_i for a_i, b_i in zip(NPP_hist_avg, NPP_hist_stddev)]

#Plot the average line
plt.plot(range(hist_len), NPP_hist_avg)

#Plot the "envelope" plus and minus standard deviation
plt.fill_between(range(hist_len), hist_lower_bound, hist_upper_bound, alpha=0.5)


plt.show()


exit()



with nc.Dataset("mri/yearly_NPP_tr.nc", 'r') as ncFile:
  NPP_yearly = ncFile.variables[var_name][:]

NPP_yearly = np.array(NPP_yearly)
print(NPP_yearly)
print(NPP_yearly.shape)

#Masking out very small values (fill value from the nc file)
NPP_valid_values = ma.masked_less(NPP_yearly, -5000)

#Length of data set (for plotting)
hist_len = len(NPP_avg)
#print(hist_len)




##calculate spatial mean
#subprocess.run(['ncwa', '-O', '-v', var_name, '-a', 'y,x', in.nc, out.nc],
#               stdout=subprocess.PIPE)
# Add '-y' option to make sure it does what is correct (avg)
##Ex: ncwa -O -v NPP -a y,x yearly_NPP_sc.nc spatial_mean_NPP_yearly_sc.nc
#

##Calculate the deviations wrt the mean
#subprocess.run(['ncbo', '-O', '-v', var_name, in.nc, out.nc, out.nc],
#               stdout=subprocess.PIPE)

##this produces a file that is fully x by y by time. Check this.
##Ex: ncbo -O -v NPP yearly_NPP_tr.nc spatial_mean_NPP_yearly_tr.nc std_dev_NPP_yearly_tr.nc
#
#subprocess.run(['ncwa', '-O', '-y', 'rmssdn', '-v', var_name,
#                '-a', 'y,x', out.nc, out.nc],
#               stdout=subprocess.PIPE)
#

base_dir = "/home/rarutter/development/dvm-dos-tem/scripts/plot_testing"

with nc.Dataset(base_dir + "/mri/spatial_mean_NPP_yearly_tr.nc") as hist_file:
#  hist_dims = [dim for dim in hist_file.dimensions]
#  hist_vars = [var for var in hist_file.variables]
  hist_data = hist_file[var_name][:]

with nc.Dataset(base_dir + "/mri/std_dev_NPP_yearly_tr.nc") as hist_std_dev_file:
  hist_std_dev = hist_std_dev_file[var_name][:]

with nc.Dataset(base_dir + "/mri/spatial_mean_NPP_yearly_sc.nc") as mri_file:
  mri_data = mri_file[var_name][:]

with nc.Dataset(base_dir + "/mri/std_dev_NPP_yearly_sc.nc") as mri_std_dev_file:
  mri_std_dev = mri_std_dev_file[var_name][:]

with nc.Dataset(base_dir + "/ncar/spatial_mean_NPP_yearly_sc.nc") as ncar_file:
  ncar_data = ncar_file[var_name][:]

with nc.Dataset(base_dir + "/ncar/std_dev_NPP_yearly_sc.nc") as ncar_std_dev_file:
  ncar_std_dev = ncar_std_dev_file[var_name][:]


hist_len = len(hist_data)
print(hist_len)
proj_len = len(mri_data)


hist_lower_bound = [a_i - b_i for a_i, b_i in zip(hist_data, hist_std_dev)]
hist_upper_bound = [a_i + b_i for a_i, b_i in zip(hist_data, hist_std_dev)]

plt.plot(range(hist_len), hist_data)
plt.fill_between(range(hist_len), hist_lower_bound, hist_upper_bound, alpha=0.5)


mri_low_bound = [a_i - b_i for a_i, b_i in zip(mri_data, mri_std_dev)]
mri_up_bound = [a_i + b_i for a_i, b_i in zip(mri_data, mri_std_dev)]

plt.plot(range(hist_len, hist_len+proj_len), mri_data)
plt.fill_between(range(hist_len, hist_len+proj_len), mri_up_bound, mri_low_bound, alpha=0.3)

ncar_low_bound = [a_i - b_i for a_i, b_i in zip(ncar_data, ncar_std_dev)]
ncar_up_bound = [a_i + b_i for a_i, b_i in zip(ncar_data, ncar_std_dev)]

plt.plot(range(hist_len, hist_len+proj_len), ncar_data)
plt.fill_between(range(hist_len, hist_len+proj_len), ncar_up_bound, ncar_low_bound, alpha=0.3)





plt.show()


#Sum the square of the deviations, divide by (N-1) and take the square root
#ncra -O -y rmssdn out.nc out.nc

#with nc.Dataset("mri/NPP_monthly_sc.nc") as mri_file:
#  mri_data = mri_file.variables[var_name][:]
#
#with nc.Dataset("ncar/NPP_monthly_sc.nc") as ncar_file:
#  ncar_data = ncar_file.variables[var_name][:]


### *******IF the summed-to-yearly file does not exist:
#if Monthly:

#  for filename in NPP_filenames:
    #Make 'time' a record dimension
#    subprocess.run(['ncks', '-O', '-h', '--mk_rec_dmn', 'time',
#                   filename, ??_filename],
#                 stdout=subprocess.PIPE)


    #Sum across time
#    subprocess.run(['ncra', '--mro', '-O', '-d', 'time,0,,12,12', '-y',
#                    'ttl', '-v', var_name, ??_filename, ??_filename],
#                   stdout=subprocess.PIPE)



