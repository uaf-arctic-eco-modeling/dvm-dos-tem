#!/usr/bin/env python


import os
import shutil #For non-empty directory tree deletion
import subprocess
import netCDF4 as nc


def compare_nc_with_nco(fileA, fileB, varname, file_cleanup):
  '''
  Compares a single variable from two dvmdostem netCDF output
    files using ncdiff and ncap2.

  Assumes that the files have matching dimensions and variables.

  Uses a subdirectory in /tmp to store the intermediate files
    that NCOs produce.
  '''

  #directory for storage of temporary diff files
  tmp_dir = "/tmp/ncdiffing/"
  os.makedirs(tmp_dir)
  diff_file = tmp_dir + varname + "_diff.nc"
  sum_diff_file = tmp_dir + varname + "_sum_diff.nc"

  #ncdiff to produce the difference of each entry
  subprocess.run(["ncdiff", fileA, fileB, diff_file])

  #ncap2 to calculate total difference
  ncap_script = "total_diff={}.total($time,$y,$x)".format(varname)
  subprocess.run(["ncap2", "-O", "-s",
        ncap_script, diff_file, sum_diff_file])

  #Check total error value
  files_match = False
  with nc.Dataset(sum_diff_file, 'r') as totalDiffFile:
    total_diff = totalDiffFile["total_diff"][0]

    if total_diff > 0.0:
      #Files differ
      files_match = False
    else:
      #Files are identical
      files_match = True

  if file_cleanup:
    shutil.rmtree(tmp_dir)

  return files_match


def compare_nc_with_python(fileA, fileB, varname):
  '''
  UNWRITTEN
  Compares a single variable from two dvmdostem netCDF output files
    without using NCOs, avoiding the creation of the temporary
    files that NCOs require.
  '''
  return


