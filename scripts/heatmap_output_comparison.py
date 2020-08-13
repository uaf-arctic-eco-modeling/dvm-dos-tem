#!/usr/bin/env python3

import subprocess
import os
import netCDF4 as nc
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import glob
import argparse
import textwrap

matplotlib.use('TkAgg')


def diff_files(dirA, dirB, filename, data_name, outdir):
  
      print(data_name + ": diffing")
      diff_filename = outdir + "/diff_" + filename 
      fileA = dirA + "/" + filename
      fileB = dirB + "/" + filename

      #Diff files  
      process = subprocess.run(['ncdiff', fileA, fileB, diff_filename],
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
  
  
def percent_diff(dirA, outdir, filename, data_name):

  print(data_name + ": calculating percent diff")

  diff_file = outdir + '/diff_' + filename

  #Copy the original output files, since the append would modify them 
  subprocess.run(['cp', dirA + '/' + filename, outdir],
                 stdout=subprocess.PIPE)
  data_file_copy = outdir + '/' + filename


  #Rename the variables in the diff files so the append works
  #It appears to rename any variable that contains 'data_var',
  # and if called multiple times will prepend 'diff_' as many
  # times as called.
  names_string = data_name + ",diff_" + data_name
  subprocess.run(['ncrename', '-v', names_string, diff_file],
                 stdout=subprocess.PIPE)


  #Concatenate the diffed values onto the copy of the original file
  subprocess.run(['ncks', '-A', diff_file, data_file_copy],
                 stdout=subprocess.PIPE)


  #Calculate ratio between diff values and original values
  #ncap -O -h -s 'reldiff = 100 * (diff/value)'
  reldiff_filename = outdir + '/rel_diff_' + filename 
  reldiff_str = data_name + '_reldiff=100*(diff_' + data_name + '/' + data_name + ')'
  subprocess.run(['ncap2', '-O', '-h', '-s', reldiff_str,
                  data_file_copy, reldiff_filename],
                 stdout=subprocess.PIPE)

  #Delete the copy of the original file to save space 
  subprocess.run(['rm', data_file_copy],
                 stdout=subprocess.PIPE)
 


def average_file(outdir, filename, data_name, input_prefix, output_prefix):

#  diff_files = glob.glob(outdir + glob_descriptor)

  var_to_avg = data_name + "_reldiff"

  diff_filename = outdir + '/' + input_prefix + filename 

  with nc.Dataset(diff_filename) as diff_ncFile:
    nc_dims = [dim for dim in diff_ncFile.dimensions]

  by_pft = by_pftpart = by_layer = False
  
  if "pft" in nc_dims:
    by_pft = True
  if "pftpart" in nc_dims:
    by_pftpart = True
  if "layer" in nc_dims:
    by_layer = True
  
  if "monthly" in diff_filename:
    #sum across time
    print(data_name + ": summing monthly diffs")
    subprocess.run(['ncks', '-O', '-h', '--mk_rec_dmn', 'time',
                    diff_filename, diff_filename],
                   stdout=subprocess.PIPE)
  
    subprocess.run(['ncra', '--mro', '-O', '-d', 'time,0,,12,12', '-y',
                    'avg', '-v', var_to_avg,
                    diff_filename, diff_filename],
                   stdout=subprocess.PIPE) 
  

  #Default to the diff filename, unless the file requires
  # summing across dimensions below, in which case the
  # name will be overwritten
  file_to_average = diff_filename
  avg_filename = outdir + '/' + output_prefix + filename
  
  if by_layer:
    print(data_name + ": averaging across layers")
    subprocess.run(['ncwa', '-O', '-h', '-v', var_to_avg,
                    '-a', 'layer', '-y', 'avg',
                    diff_filename, avg_filename],
                   stdout=subprocess.PIPE)
    file_to_average = avg_filename
  
  elif by_pft and not by_pftpart:
    print(data_name + ": averaging across PFTs")
    subprocess.run(['ncwa', '-O', '-h', '-v', var_to_avg,
                    '-a', 'pft', '-y', 'avg',
                    diff_filename, avg_filename],
                   stdout=subprocess.PIPE)
    file_to_average = avg_filename
 
  elif by_pft and by_pftpart:
    print(data_name + ": averaging across PFT and PFT parts")
    subprocess.run(['ncwa', '-O', '-h', '-v', var_to_avg,
                    '-a', 'pftpart,pft', '-y', 'avg',
                    diff_filename, avg_filename],
                   stdout=subprocess.PIPE)
    file_to_average = avg_filename
  
  
  #Average across cells
  print(data_name + ": averaging across cells")

  subprocess.run(['ncwa', '-O', '-h', '-v', var_to_avg, '-a', 'x,y',
                  '-y', 'avg', file_to_average, avg_filename],
                 stdout=subprocess.PIPE)


def produce_heatmap_plot(outdir, glob_descriptor):

  avg_files = glob.glob(outdir + glob_descriptor)
  avg_files.sort()

  tr_var_names = []
  sc_var_names = []
  sc_plot_data = []
  tr_plot_data = []


  for avg_filename in avg_files:
#    print(avg_filename)

    #Load data from the averaged diff files for plotting
    with nc.Dataset(avg_filename) as avg_ncFile:

      nc_vars = [var for var in avg_ncFile.variables]
      #Get variable name
      for var in nc_vars:
        if var == 'time' or var == 'albers_conical_equal_area':
          continue
        else:
          data_var = var

#      var_names.append(data_var)
      var_data = avg_ncFile.variables[data_var][:]
#      print(len(var_data))

      if len(var_data) <= 100:
        sc_var_names.append(data_var)
        sc_plot_data.append(avg_ncFile.variables[data_var][:])
      elif len(var_data) > 100:
        tr_var_names.append(data_var)
        tr_plot_data.append(avg_ncFile.variables[data_var][:])


  plot_data_np = np.array(sc_plot_data)

#  xval = np.nanmax(np.abs(plot_data_np))

  plot_data_np = np.ma.masked_invalid(plot_data_np)
  plot_data_np = np.ma.masked_less(plot_data_np, -1000)
  plot_data_np = np.ma.masked_greater(plot_data_np, 1000)


  fig, ax = plt.subplots()

  ax.set_yticks(np.arange(len(sc_plot_data)))

  ax.set_yticklabels(sc_var_names)
  ax.set_xticklabels(np.arange(0,len(sc_plot_data),10))


  cm1 = plt.cm.coolwarm

  im = ax.imshow(plot_data_np, cmap=cm1,
                 vmin=-np.nanmax(np.abs(plot_data_np)),
                 vmax=np.nanmax(np.abs(plot_data_np)))

#  cbar = ax.figure.colorbar(im, ax=ax, cmap="YlGn")
#  cbar.ax.set_ylabel("Difference", rotation=-90, va="bottom")

  cbar = plt.colorbar(im, ax=ax, orientation='vertical')

  fig.tight_layout()
  plt.show()


if __name__ == '__main__':


  dirA = "/home/rarutter/development/ddt_F30/5_cell_old_mri/"
  dirB = "/home/rarutter/development/ddt_F30/202006_mri/"
  outdir = "heatmapping_diffs"


#  os.mkdir(outdir)


  for filename in os.listdir(dirA):

    if 'restart' in filename or 'status' in filename:
      continue

#    if 'ALD' not in filename:
#      continue

    if 'yearly' not in filename:
      continue

    with nc.Dataset(dirA + filename) as ncFile:
      nc_dims = [dim for dim in ncFile.dimensions]
      nc_vars = [var for var in ncFile.variables]

  
    #Get variable name
    for var in nc_vars:
      if var == 'time' or var == 'albers_conical_equal_area':
        continue
      else:
        data_name = var
#        print("Processing " + data_name)


#    diff_files(dirA, dirB, filename, data_name, outdir)

#    percent_diff(dirA, outdir, filename, data_name)

#    average_file(outdir, filename, data_name, "rel_diff_", "avg_rel_diff_")


# "/avg_diff*"
  produce_heatmap_plot(outdir, "/avg_rel_diff*")
 



