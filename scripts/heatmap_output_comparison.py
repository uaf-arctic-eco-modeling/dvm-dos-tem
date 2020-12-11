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


def diff_files(outdir, filename, data_name, prefix_A, prefix_B):
  
  print(data_name + ": diffing")
  diff_filename = outdir + "/diff_" + filename 
  fileA = outdir + "/" + prefix_A + filename
  fileB = outdir + "/" + prefix_B + filename

  #Diff files  
  process = subprocess.run(['ncdiff', fileA, fileB, diff_filename],
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
  
  
def percent_diff(outdir, filename, data_name, comp_prefix, diff_prefix):

  print(data_name + ": calculating percent diff")

  #diffed file and comparison file, respectively
  diff_file = outdir + '/' + diff_prefix + filename
  comp_file = outdir + '/' + comp_prefix + filename

  #Rename the variables in the diff files so the append works
  #It appears to rename any variable that contains 'data_var',
  # and if called multiple times will prepend 'diff_' as many
  # times as called.
  names_string = data_name + ",diff_" + data_name
  subprocess.run(['ncrename', '-v', names_string, diff_file],
                 stdout=subprocess.PIPE)


  #Concatenate the diffed values onto the copy of the original file
  subprocess.run(['ncks', '-A', diff_file, comp_file],
                 stdout=subprocess.PIPE)


  #Calculate ratio between diff values and original values
  #ncap -O -h -s 'reldiff = 100 * (diff/value)'
  reldiff_filename = outdir + '/rel_diff_' + filename 
  reldiff_str = data_name + '_rel_diff=100*(diff_' + data_name + '/' + data_name + ')'
  subprocess.run(['ncap2', '-O', '-h', '-s', reldiff_str,
                  comp_file, reldiff_filename],
                 stdout=subprocess.PIPE)

  #Delete the copy of the original file to save space 
#  subprocess.run(['rm', data_file_copy],
#                 stdout=subprocess.PIPE)
 


def average_file(outdir, filename, data_name, input_prefix, output_prefix):

  filecopy = outdir + '/' + input_prefix + filename

  with nc.Dataset(filecopy) as ncFile:
    nc_dims = [dim for dim in ncFile.dimensions]

  by_pft = by_pftpart = by_layer = False
  
  if "pft" in nc_dims:
    by_pft = True
  if "pftpart" in nc_dims:
    by_pftpart = True
  if "layer" in nc_dims:
    by_layer = True
  
  if "monthly" in filecopy:
    #sum across time
    print(data_name + ": summing monthly diffs")
    subprocess.run(['ncks', '-O', '-h', '--mk_rec_dmn', 'time',
                    filecopy, filecopy],
                   stdout=subprocess.PIPE)
  
    subprocess.run(['ncra', '--mro', '-O', '-d', 'time,0,,12,12', '-y',
                    'avg', '-v', data_name,
                    filecopy, filecopy],
                   stdout=subprocess.PIPE) 
  

  #Default to the main filename, unless the file requires
  # summing across dimensions below, in which case the
  # name will be overwritten
  file_to_average = filecopy 
  avg_filename = outdir + '/' + output_prefix + input_prefix + filename
  
  if by_layer:
    print(data_name + ": averaging across layers")
    subprocess.run(['ncwa', '-O', '-h', '-v', data_name,
                    '-a', 'layer', '-y', 'avg',
                    filecopy, avg_filename],
                   stdout=subprocess.PIPE)
    file_to_average = avg_filename
  
  elif by_pft and not by_pftpart:
    print(data_name + ": averaging across PFTs")
    subprocess.run(['ncwa', '-O', '-h', '-v', data_name,
                    '-a', 'pft', '-y', 'avg',
                    filecopy, avg_filename],
                   stdout=subprocess.PIPE)
    file_to_average = avg_filename
 
  elif by_pft and by_pftpart:
    print(data_name + ": averaging across PFT and PFT parts")
    subprocess.run(['ncwa', '-O', '-h', '-v', data_name,
                    '-a', 'pftpart,pft', '-y', 'avg',
                    filecopy, avg_filename],
                   stdout=subprocess.PIPE)
    file_to_average = avg_filename
  
  
  #Average across cells
  print(data_name + ": averaging across cells")

  subprocess.run(['ncwa', '-O', '-h', '-v', data_name, '-a', 'x,y',
                  '-y', 'avg', file_to_average, avg_filename],
                 stdout=subprocess.PIPE)


def produce_heatmap_plot(outdir, reldiff_prefix):

  glob_descriptor = f"/{reldiff_prefix}*"

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
        if reldiff_prefix in var:
          data_var = var

      var_data = avg_ncFile.variables[data_var][:]

      if len(var_data) <= 100:
        sc_var_names.append(data_var)
        sc_plot_data.append(var_data)
      elif len(var_data) > 100:
        tr_var_names.append(data_var)
        tr_plot_data.append(var_data)

    #Print min/max percentage diffs, for quick reference when
    # a small number of variables are skewing the color scale
    #print(data_var + "percent diff min, max: {0:1.4g}, {1:1.4g}".format(min(var_data), max(var_data)) )
    min_data = min(var_data)
    max_data = max(var_data)
    #print(f"{data_var} percent diff min, max: {min_data}, {max_data}" )


  plot_data_np_tr = np.array(tr_plot_data)
  plot_data_np_tr = np.ma.masked_invalid(plot_data_np_tr)
  plot_data_np_tr = np.ma.masked_less(plot_data_np_tr, -1000)
  plot_data_np_tr = np.ma.masked_greater(plot_data_np_tr, 1000)

  plot_data_np_sc = np.array(sc_plot_data)
  plot_data_np_sc = np.ma.masked_invalid(plot_data_np_sc)
  plot_data_np_sc = np.ma.masked_less(plot_data_np_sc, -1000)
  plot_data_np_sc = np.ma.masked_greater(plot_data_np_sc, 1000)

  fig, axes = plt.subplots(nrows=2, ncols=1)
  cm1 = plt.cm.coolwarm

  #Set up TR plot
  TR_data_len = len(plot_data_np_tr[0])
  axes[0].set_title('Transient (TR)')
  axes[0].set_yticks(np.arange(len(plot_data_np_tr)))
  axes[0].set_yticklabels(tr_var_names)
  axes[0].set_xticks(np.arange(0,TR_data_len,10))
  axes[0].set_xticklabels(np.arange(0,TR_data_len,10))

  im = axes[0].imshow(plot_data_np_tr, cmap=cm1,
                 vmin=-np.nanmax(np.abs(plot_data_np_tr)),
                 vmax=np.nanmax(np.abs(plot_data_np_tr)))

  cbar = plt.colorbar(im, ax=axes[0], orientation='vertical')
  im.set_clim(-100, 100)

  #Set up SC plot
  SC_data_len = len(plot_data_np_sc[0])
  axes[1].set_title('Scenario (SC)')
  axes[1].set_yticks(np.arange(len(sc_plot_data)))
  axes[1].set_yticklabels(sc_var_names)
  axes[1].set_xticks(np.arange(0,SC_data_len,10))
  axes[1].set_xticklabels(np.arange(0,SC_data_len,10))

  im = axes[1].imshow(plot_data_np_sc, cmap=cm1,
                 vmin=-np.nanmax(np.abs(plot_data_np_sc)),
                 vmax=np.nanmax(np.abs(plot_data_np_sc)))

  cbar = plt.colorbar(im, ax=axes[1], orientation='vertical')
  im.set_clim(-100, 100)

  fig.tight_layout()
  plt.show()


def delete_file(filename):
  subprocess.run(['rm', filename],
                 stdout=subprocess.PIPE)
 


if __name__ == '__main__':

  parser = argparse.ArgumentParser(
    formatter_class = argparse.RawDescriptionHelpFormatter,
      description=textwrap.dedent('''This compares two sets of regional output data and presents the results as a pair of heatmap plots, one for transient and one for scenario. If the sets have already been compared, it can be used just to produce the plots.'''.format()),

      epilog=textwrap.dedent(''''''),
  )

  parser.add_argument('--dirA',
      help=textwrap.dedent("""The first directory to compare"""))

  parser.add_argument('--dirB',
      help=textwrap.dedent("""The second directory to compare"""))

  parser.add_argument('--outdir',
      help=textwrap.dedent("""Working/output directory"""))

  parser.add_argument('--plot-only', action="store_true",
      help=textwrap.dedent("""Only generate the plots. Assumes that
        files to plot already exist."""))

  args = parser.parse_args()

  dirA = args.dirA
  dirB = args.dirB
  outdir = args.outdir

  if not args.plot_only:

    if not os.path.exists(outdir):
      print("Creating output directory: " + outdir)
      os.mkdir(outdir)
    else:
      print("Output directory exists. Exiting")
      exit()


    for filename in os.listdir(dirA):

      if 'restart' in filename or 'status' in filename:
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
          print("Processing " + data_name)


      #copy original files to working directory
      filename_A = dirA + '/' + filename
      filename_B = dirB + '/' + filename

      filecopy_A = outdir + '/A_' + filename
      filecopy_B = outdir + '/B_' + filename

      subprocess.run(['cp', filename_A, filecopy_A],
                   stdout=subprocess.PIPE)
      subprocess.run(['cp', filename_B, filecopy_B],
                   stdout=subprocess.PIPE)

      #Average the files across layer, pft, pftpart, and space
      avg_prefix = "avg_"
      average_file(outdir, filename, data_name, "A_", avg_prefix)
      average_file(outdir, filename, data_name, "B_", avg_prefix)

      #Diff the averaged files
      avg_A_prefix = "avg_A_"
      avg_B_prefix = "avg_B_"
      diff_files(outdir, filename, data_name, avg_A_prefix, avg_B_prefix)

      #Compare the diffed files with one set of the original files
      comp_prefix = "avg_A_"
      diff_prefix = "diff_"
      percent_diff(outdir, filename, data_name, comp_prefix, diff_prefix)

      #Delete the intermediate files to save space 
      delete_file(filecopy_A)
      delete_file(filecopy_B)
      delete_file(f"{outdir}/{avg_A_prefix}{filename}")
      delete_file(f"{outdir}/{avg_B_prefix}{filename}")
      delete_file(f"{outdir}/{diff_prefix}{filename}")

  produce_heatmap_plot(outdir, "rel_diff")
 

