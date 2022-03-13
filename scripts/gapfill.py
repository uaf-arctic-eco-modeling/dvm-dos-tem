#!/usr/bin/env python

# June 2017
# Tobey Carman, 
# Institute of Arctic Biology

import os
import sys
import argparse
import textwrap

import netCDF4 as nc
import numpy as np


def modified_attribute_string(msg=''):
  '''
  Returns a string to be included as a netCDF attribute named "modified".

  The string will contain the filename and function name responsible for
  modifying the file.

  Parameters
  ----------
  msg : str
    An additional message string to be included.

  Returns
  -------
  s : str
    A string something like:
    "gapfill.py::gapfill_along_timeseries"
  '''
  import inspect
  cf = inspect.currentframe().f_back # <-- gotta look up one frame.

  # Start with the file name and function name
  s = "{}::{} {}".format(cf.f_code.co_filename, cf.f_code.co_name, msg)

  return s

def print_mask_count_along_timeseries(dataset, title='', nonewline=False):
  '''Counts masked items along a time axis and prints value for each pixel.'''
  pass
  print("Masked items: {}".format(np.ma.count_masked(dataset)))
  print("-- {} --".format(title))
  print("{}".format(np.apply_along_axis(np.count_nonzero, 0, np.ma.getmaskarray(dataset))))
  print("")

def gapfill_along_timeseries(data, dataTag):
  '''
  Parameters
  ----------
  data : a 3D numpy array of data with dimensions (time, y, x)
    Will be converted to a masked array, and then have values modifed by
    the interpolation scheme.

  Returns
  -------
  data : a 3D numpy masked array with dimension (time, y, x)
    Some data will be hidden (masked)

  '''
  datam = np.ma.MaskedArray(data)

  print_mask_count_along_timeseries(datam, title='{} (before)'.format(dataTag))

  coords_to_process = list(zip(*np.nonzero(np.invert(np.ma.getmaskarray(datam[0])))))

  bad_points = None

  for i, px in enumerate( coords_to_process ):
    yc, xc = px
    timeseries = datam[:,yc,xc]

    # list of arrays, one array for each dimension,
    # so we unzip into a single list
    bad_points = list(zip(*np.nonzero(timeseries.mask)))
    if len(bad_points) > 0:
      pass
      #print "Got some bad data for px ({},{}): bad_points={}".format(yc, xc, bad_points)

    for j, bp in enumerate(bad_points):
      tidx = bp[0]
      #print "datam[{},{},{}] is {} ({})".format(tidx, yc, xc, datam[tidx, yc, xc], datam[tidx, yc, xc].data)

      # Don't bother with the ends of the timeseries
      if tidx >= 0 and tidx < len(timeseries):
        prevp = timeseries[tidx-1]
        nextp = timeseries[tidx+1]
        new_value = (prevp + nextp)/2.0
        #print "Setting datam[{},{},{}] = {}".format(tidx, yc, xc, new_value)
        datam[tidx, yc, xc] = new_value
      else:
        print("Can't operate on ends of timeseries! Passing...")

  print_mask_count_along_timeseries(datam, title='{} (after)'.format(dataTag))

  return (datam, bad_points)


if __name__ == '__main__':

  CLIMATE_FILES = ['historic-climate.nc', 'projected-climate.nc']
  VARS = ['tair', 'precip', 'nirr', 'vapor_press']

  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''
      Script for filling in (interpolating) missing data in dvmdostem input
      files.

      Currently the script does linear interpolation over single point gaps
      along the time dimension of the dvmdostem climate files.

      The script will look for the following files:

        {}

      and the following variables:

        {}

      within the input folder. Both files will have their missing values
      filled and the files will be over-written with the new interpolated
      data. Additionally an attribute will be written to each file indicating
      the file has been modifed by this script.
      '''.format(', '.join(CLIMATE_FILES), ', '.join(VARS)))
  )

  parser.add_argument('--input-folder', metavar=('FOLDER'),
      help=textwrap.dedent('''The input folder to operate in.'''))

  parser.add_argument('--dry-run', action='store_true',
      help=textwrap.dedent('''Read-only - don't overwrite the existing file.'''))

  parser.add_argument('--fix-ar5-rcp85-nirr', action='store_true', help="need to write this...")

  args = parser.parse_args()

  if args.fix_ar5_rcp85_nirr:
    file_path = os.path.join(args.input_folder, 'historic-climate.nc')

    with nc.Dataset(file_path, 'r') as histFile:
      nirrV = histFile.variables['nirr']
      nirrD = histFile.variables['nirr'][:]

      from IPython import embed; embed()

      T, Y, X = nirrD.shape

      nirrD_i = nirrD * -1.0

      peaks, _ = np.apply_along_axis(scipy.signal.find_peaks, 0, nirrD_i)

      # Maybe this will work. Should be vectorized if it does...
      for y in np.arange(0,Y):
        for x in np.arange(0,X):
          px_ts = nirrD_i[:,y,x]
          for peakidx in peaks:
            print(peakidx) # this is the coordinate along time axis
            if peakidx == 0 or peakidx == T-1:
              pass # Can't operate on ends!!
            else:
              peak_data = px_ts[peakidx]
              prev = px_ts[peakidx-1]
              next = px_ts[peakidx+1]
              estimated_value = (prev + next) / 2.0
              estimated_value = estimated_value * -1.0
              nirrD[peakidx,y,x] = estimated_value

    sys.exit(0)



  for climate_file in CLIMATE_FILES:

    file_path = os.path.join(args.input_folder, climate_file)

    print("Looking for path as src dataset:", file_path)
    with nc.Dataset(file_path, 'r+') as myFile:

      for v in VARS:

        print("Generating fill data for {}".format(file_path))
        filled, bad_points = gapfill_along_timeseries(myFile.variables[v][:], dataTag='{}'.format(v))

        print("Source: {}".format(myFile.source))
        print("ncattrs: {}".format(myFile.ncattrs()))

        if len(bad_points) < 1:
          print("VARIABLE {} ALL OK! NOTHING TO GAPFILL!".format(v))
        else:
          if not (args.dry_run):
            print("Overwriting file....")
            myFile.variables[v][:] = filled

            myFile.variables[v].setncattr('modified', modified_attribute_string("Basic single point interpolation"))





