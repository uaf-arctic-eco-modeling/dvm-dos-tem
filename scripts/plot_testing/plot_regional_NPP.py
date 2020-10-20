#! /usr/bin/env python

import subprocess
import netCDF4 as nc
import matplotlib
import matplotlib.pyplot as plt

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
hist_filename = "mri/NPP_monthly_tr.nc"
mri_filename = "mri/NPP_monthly_sc.nc"
ncar_filename = "ncar/NPP_monthly_sc.nc"

#Example:
byPFT = True
byPFTCompartment = False
Monthly = True

#Make 'time' a record dimension
#subprocess.run(['ncks', '-O', '-h', '--mk_rec_dmn', 'time',
#                ??_filename, ??_filename],
#               stdout=subprocess.PIPE)
#
##Sum across time
#subprocess.run(['ncra', '--mro', '-O', '-d', 'time,0,,12,12', '-y',
#                'ttl', '-v', var_name, ??_filename, ??_filename],
#               stdout=subprocess.PIPE)
#
#
#
##calculate spatial mean
#subprocess.run(['ncwa', '-O', '-v', var_name, '-a', 'y,x', in.nc, out.nc],
#               stdout=subprocess.PIPE)
# Add '-y' option to make sure it does what is correct (avg)
##Ex: ncwa -O -v NPP -a y,x yearly_NPP_sc.nc spatial_mean_NPP_yearly_sc.nc
#

#Need to be able to do this for a specific veg type, which isn't
# simple in NCOs. One plot per specified veg type
# Same y range

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




