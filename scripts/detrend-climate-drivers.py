#!/usr/bin/env python

# Tobey Carman
# Feb 2015
# Spatial Ecology Lab, UAF

# Example usage:
# ./detrend-climate-data.py jan 10 "../snap-data/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_2001_2100/"

import argparse
import glob
import os
import resource
import subprocess
import textwrap

import rasterio
import numpy as np
import scipy.signal


def process_data(args):

  # Make a list with paths to all the right files...
  monthfiles = glob.glob("%s/*_%02d_*.tif" % (args.infiledir, args.month))
  
  TMP_MONTHLISTFILE = 'month-file-list.txt'
  VRTFILE = 'month-%02d.vrt' % args.month

  # Write the list to a file...
  with open(TMP_MONTHLISTFILE, 'w') as f:
    for i in sorted(monthfiles):
      f.write(i)
      f.write("\n")

  # Then call gdalbuildvrt with the list file...
  rc = subprocess.call([
    'gdalbuildvrt',
    '-separate',
    '-b', '1',
    '-input_file_list', TMP_MONTHLISTFILE,
    VRTFILE
  ])

  if rc != 0:
    print "Warning: gdalbuildvrt did not exit cleanly..."

  # cleanup the file with months listed
  os.remove(TMP_MONTHLISTFILE)

  # Open and read the vrt
  monthdatafile = rasterio.open(VRTFILE)

  # NOTE: should we check for enough memory?? 
  print resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

  from IPython import embed; embed()
  data = monthdatafile.read(range(1,11))

  # Make sure the mask is set 
  # NOTE: actually not even important for detrending, only
  #       for displaying. The detrend function seems to run 
  #       over all the masked points too. But the mask
  #       is key for displaying the data and having the auto-
  #       scaling work correctly...
  data = np.ma.masked_outside(data, -500, 500, copy=False)

  # Detrend for each pixel over the time axis.
  # For some reason, the detrend function seems to operate on
  # masked values. This will result in a RunTime overflow error
  # when operating on the fill values which are usually very
  # large or very small. These large or small numbers get squared
  # in the detrending fuction and we end up with overflow errors. 
  detrended_data = scipy.signal.detrend(data, axis=0)

  # Now make sure to add the offset back into the data
  detrended_data[:,:,:] += (data[0,:,:] - detrended_data[0,:,:])

  # Write out the data to a new series of .tif files
  with rasterio.drivers(CPL_DEBUG=True):
    
    # Copy the metadata from the input vrt file
    kwargs = monthdatafile.meta

    # Change a few things about the metadata...
    kwargs.update(
      count=1,            # only one band
      compress='lzw',     # not sure if this is actually helping?
      driver='GTiff'      # we want .tifs, not .vrts
    )

    # Write each timestep out to its own file...
    for i, timestep in enumerate(detrended_data[:]): 
      with rasterio.open('month-%02d-%04d.tif' % (args.month, i), 'w', **kwargs) as dst:
        dst.write_band(1, timestep.astype(rasterio.float32))



if __name__ == '__main__':
	
  parser = argparse.ArgumentParser(description=textwrap.dedent('''
    De-trend climate data.
  '''))

  parser.add_argument('month', choices=range(1,13), type=int, 
    help="Which month to process"
  )

  parser.add_argument('infiledir', 
    help="path to directory of input files"
  )

  args = parser.parse_args()
  print args

  process_data(args)




