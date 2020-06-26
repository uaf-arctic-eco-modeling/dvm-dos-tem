#!/usr/bin/env python3

import subprocess
import os
import netCDF4 as nc
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

import argparse
import textwrap

dirA = "/vagrant/5_cell_old_mri/"
dirB = "/vagrant/202006_mri/"
outdir = "heatmapping_diffs"

file1 = "/vagrant/5_cell_old_mri/ALD_yearly_sc.nc"
file2 = "/vagrant/202006_mri/ALD_yearly_sc.nc"

outfile = outdir + "/ALD_diff.nc"
avgfile = outdir + "/ALD_diff_avg.nc"

os.mkdir(outdir)

var_names = []
plot_data = []

for filename in os.listdir(dirA):

  if 'restart' in filename or 'status' in filename:
    continue

  if 'ALD' not in filename:
    continue

  #Get variable name
  with nc.Dataset(dirA + filename) as ncFile:
    nc_dims = [dim for dim in ncFile.dimensions]
    nc_vars = [var for var in ncFile.variables]

    by_pft = by_pftpart = by_layer = False

    if "pft" in nc_dims:
      by_pft = True
    if "pftpart" in nc_dims:
      by_pftpart = True
    if "layer" in nc_dims:
      by_layer = True

    for var in nc_vars:
      if var == 'time' or var == 'albers_conical_equal_area':
        continue
      else:
        data_var = var
        print("Processing " + data_var)

    print(data_var + ": diffing")
    diff_filename = outdir + "/diff_" + filename 
    fileA = dirA + "/" + filename
    fileB = dirB + "/" + filename

    process = subprocess.run(['ncdiff', fileA, fileB, diff_filename],
                             stdout=subprocess.PIPE,
                             universal_newlines=True)


    if "monthly" in filename:
      #sum across time
      print(data_var + ": summing monthly diffs")
      subprocess.run(['ncks', '-O', '-h', '--mk_rec_dmn', 'time',
                      diff_filename, diff_filename],
                     stdout=subprocess.PIPE)

      subprocess.run(['ncra', '--mro', '-O', '-d', 'time,0,,12,12', '-y',
                      'avg', '-v', data_var,
                      diff_filename, diff_filename],
                     stdout=subprocess.PIPE) 


    file_to_average = diff_filename
    avg_filename = outdir + "/avg_diff_" + filename

    if by_layer:
      print(data_var + ": averaging across layers")
      subprocess.run(['ncwa', '-O', '-h', '-v', data_var,
                      '-a', 'layer', '-y', 'avg',
                      diff_filename, avg_filename],
                     stdout=subprocess.PIPE)
      file_to_average = avg_filename

    elif by_pft and not by_pftpart:
      print(data_var + ": averaging across PFTs")
      subprocess.run(['ncwa', '-O', '-h', '-v', data_var,
                      '-a', 'pft', '-y', 'avg',
                      diff_filename, avg_filename],
                     stdout=subprocess.PIPE)
      file_to_average = avg_filename

    elif by_pft and by_pftpart:
      print(data_var + ": averaging across PFT and PFT parts")
      subprocess.run(['ncwa', '-O', '-h', '-v', data_var,
                      '-a', 'pftpart,pft', '-y', 'avg',
                      diff_filename, avg_filename],
                     stdout=subprocess.PIPE)
      file_to_average = avg_filename


    #Average across cells
    print(data_var + ": averaging across cells")

    subprocess.run(['ncwa', '-O', '-h', '-v', data_var, '-a', 'x,y',
                    '-y', 'avg', file_to_average, avg_filename],
                   stdout=subprocess.PIPE)



    #Load data from the averaged diff files for plotting
    with nc.Dataset(avg_filename) as avg_ncFile:
      var_names.append(data_var)
      var_data = avg_ncFile.variables[data_var][:]
      print(len(var_data))
      plot_data.append(avg_ncFile.variables[data_var][:])

#      print(var_names)
#      print(len(plot_data))

plot_data_np = np.array(plot_data)

fig, ax = plt.subplots()
im = ax.imshow(plot_data_np)

fig.tight_layout()
plt.show()

#print("diffing ALD")
#process = subprocess.run(['ncdiff', file1, file2, outfile],
#               stdout=subprocess.PIPE,
#               universal_newlines=True)

#print(process.stdout)

#print("Averaging across cells")

#subprocess.run(['ncwa', '-O', '-h', '-v', 'ALD', '-a', 'x,y', '-y', 'avg', outfile, avgfile],
#               stdout=subprocess.PIPE)



#with nc.Dataset(avgfile) as ncFile:
#  nc_vars = [var for var in ncFile.variables]

#  for var in nc_vars:
#    if var == 'time' or var == 'albers_conical_equal_area':
#      continue
#    else:
#      data_var = var

#  data = ncFile.variables[data_var][:]


 



