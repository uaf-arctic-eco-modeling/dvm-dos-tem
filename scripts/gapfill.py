#!/usr/bin/env python

# June 2017
# Tobey Carman, 
# Institute of Arctic Biology

import os
import argparse
import textwrap

import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt


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

def plot_mask_count_along_timeseries(dataset):
  img = plt.imshow(
        np.ma.masked_greater_equal(
            np.apply_along_axis(np.count_nonzero, 0, dataset.mask),
            len(dataset)),
        interpolation='none',
        vmin=0,
        vmax=len(dataset))

  plt.colorbar(img)

  plt.tight_layout()
  plt.show()

def print_mask_count_along_timeseries(dataset):
  print "Masked items: {}".format(np.ma.count_masked(dataset))
  print "----------------"
  print np.apply_along_axis(np.count_nonzero, 0, np.ma.getmaskarray(dataset))

def gapfill_along_timeseries(data, plot=False):
  '''
  Parameters
  ----------
  data : a 3D numpy array of data with dimensions (time, y, x)
    Will be converted to a masked array, and then have values modifed by
    the interpolation scheme.
  plot : bool
    Whether or not to generate images using matplotlib showing which pixels
    get masked

  Returns
  -------
  data : a 3D numpy masked array with dimension (time, y, x)
    Some data will be hidden (masked)

  '''
  datam = np.ma.MaskedArray(data)

  #datam = np.ma.MaskedArray(pc.variables['precip'][:])

  print_mask_count_along_timeseries(datam)

  #fig, (ax0, ax1, ax2) = plt.subplots(1,3)

  #plot_mask_count_along_timeseries(datam)

  coords_to_process = zip(*np.nonzero(np.invert(np.ma.getmaskarray(datam[0]))))

  for i, px in enumerate( coords_to_process ):
    yc, xc = px
    timeseries = datam[:,yc,xc]

    # list of arrays, one array for each dimension,
    # so we unzip into a single list
    bad_points = zip(*np.nonzero(timeseries.mask))
    if len(bad_points) > 0:
      pass
      #print "Got some bad data for px ({},{}): bad_points={}".format(yc, xc, bad_points)

    for j, bp in enumerate(bad_points):
      tidx = bp[0]
      print "datam[{},{},{}] is {} ({})".format(tidx, yc, xc, datam[tidx, yc, xc], datam[tidx, yc, xc].data)

      # Don't bother with the ends of the timeseries
      if tidx >= 0 and tidx < len(timeseries):
        prevp = timeseries[tidx-1]
        nextp = timeseries[tidx+1]
        new_value = (prevp + nextp)/2.0
        #print "Setting datam[{},{},{}] = {}".format(tidx, yc, xc, new_value)
        datam[tidx, yc, xc] = new_value
      else:
        print "Cant' operating on ends of timeseries! Passing..."

  print_mask_count_along_timeseries(datam)

  return datam


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

      within the input %(metavar)s. Both files will have their missing values
      filled and the files will be over-written with the new interpolated
      data. Additionally an attribute will be written to each file indicating
      the file has been modifed by this script.
      '''.format(', '.join(CLIMATE_FILES), ', '.join(VARS)))
  )

  parser.add_argument('--input-folder', metavar=('FOLDER'),
      help=textwrap.dedent('''The input folder to operate in.'''))

  parser.add_argument('--dry-run', action='store_true',
      help=textwrap.dedent('''Read-only - don't overwrite the existing file.'''))

  args = parser.parse_args()



for climate_file in CLIMATE_FILES:

    file_path = os.path.join(args.input_folder, climate_file)

    with nc.Dataset(file_path, 'r+') as myFile:

      for v in VARS:

        print "Generating fill data"
        filled = gapfill_along_timeseries(myFile[v][:])

        print myFile.source
        print myFile.ncattrs()

        if not (args.dry_run):
          print "Overwriting file...."
          myFile.variables[v][:] = filled

          myFile.variables[v].setncattr('modified', modified_attribute_string("Basic single point interpolation"))




#from IPython import embed; embed()



