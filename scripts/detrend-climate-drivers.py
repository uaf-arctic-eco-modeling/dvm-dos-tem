#!/usr/bin/env python

# Tobey Carman
# Feb 2015
# Spatial Ecology Lab, UAF

'''
RUNNING ON ATLAS LIKE SO:

    tcarman2@atlas ~ $ sbatch --array 7-12 --exclusive -p main test-driver.sh

Here is test-driver.sh:

    tcarman2@atlas ~ $ cat test-driver.sh 
    #!/bin/bash

    # partition - grouping of nodes
    # job - allocation of resources assigned to user for specific time 
    #       AND
    # job step(s) - sets of (possibly parallel) tasks w/in a job

    #SBATCH -o detrend_%a.txt
    #SBATCH -e detrend_%a.txt


    echo "sajid: $SLURM_ARRAY_JOB_ID satid: $SLURM_ARRAY_TASK_ID"

    MONTH="$SLURM_ARRAY_TASK_ID"
    INDIR="/big_scratch/tem/snap_aiem_research_data/tas_mean_C_iem_cccma_cgcm3_1_sresa1b"
    OUTDIR="/big_scratch/tem/snap_aiem_research_data"

    # This is a job step...
    #  -u    unbuffered output from stdout, stderr
    #  -l    tag lines in stdout and err with step id? can't be used with -u
    srun -u --nodes=1 python dvm-dos-tem/scripts/detrend-climate-drivers.py "$MONTH" "$INDIR" "$OUTDIR"
'''

import argparse
import textwrap   
import glob
import os
import resource    # for checking available memory?
import psutil
import subprocess  # for calling various GDAL command line tools 

import rasterio
import numpy as np
import scipy.signal

def print_mask_report(data):
  '''Print some info about a masked array'''
  shape = data.shape
  sz = data.size
  mv = np.count_nonzero(data.mask)
  pcnt = 100.0 * mv/sz
  print "Shape: %s Total size: %s Masked values: %s. Percent Masked: %0.7f" % (str(shape), sz, mv, pcnt)


def guess_from_filename(f):
  '''Tokenizes a SNAP file name, returns fields chosen from input filename'''

  f = os.path.basename(f)
  f_extension = os.path.splitext(f)[1]
  f_name = os.path.splitext(f)[0]

  # Split into tokens
  # e.g.: 'tas_mean_C_iem_cccma_cgcm3_1_sresa1b_02_2001.tif'
  # e.g.: ['tas', 'mean', 'C', 'iem', 'cccma', 'cgcm3', '1', 'sresa1b', '02', '2001']
  
  # SNAP's general naming pattern they strive for:
  # [variable][metric][units][format][assessmentReport][group][model][scenario][timeFrame].[fileFormat]
  tokens = f_name.split('_')

  variable = tokens[0]
  metric = tokens[1]
  # units =   # variable number of '_' separated fields.
  # group =   # not sure how to choose these yet??
  # model = 
  scenario = [-3]
  year = tokens[-1]
  month = tokens[-2]

  # Like this: 'tas_mean_C_iem_cccma_cgcm3_1_sresa1b'
  bname = "_".join(tokens[0:-2]) # everything except the date fields.

  return (bname, variable, metric, scenario, month, year)

def setup_output_directory(orig_file_list):
  '''Makes a place to put outputs...'''

  if not os.path.exists("detrended_data"):
    os.makedirs(test)

  #  - mkdir -p detrended_output directory
  #  - clear any files in detrended_output that match glob (file list)
  #      * that way other months are preserved but this month can't end up with 
  #        a mixture of recent and old files if for some reason
  #        there are some older ones laying around (maybe from a test run 
  #        or something)
  # 
  #  - discover the "basename" for the file - everything but the date fields.


  # clear any output

  # vap_mean_hPa_iem_cccma_cgcm3_1_sresa1b_2001_2100.zip
  # rsds_mean_MJ-m2-d1_iem_cccma_cgcm3_1_sresa1b_2001_2100.zip
  # pr_total_mm_iem_cccma_cgcm3_1_sresa1b_2001_2100.zip
  # tas_mean_C_iem_mpi_echam5_sresa1b_2001_2100.zip

def print_memory_report():
  print "Currently Available Memory (GB) ", psutil.virtual_memory().available/1024.0/1024.0/1024.0
  print "Peak memory usage by this program(GB):", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024.0/1024.0/1024.0


def main(args):

  ''' ??? Need to write this....'''

  # Make a list with paths to all the correct input files.
  # In this case, one month, all years.
  print "Listing and sorting all files for a month from the input directory..."
  monthfiles = sorted(glob.glob("%s/*_%02d_*.tif" % (args.infiledir, args.month)))
  
  TMP_MONTHLISTFILE = 'month-%02d-file-list.txt' % args.month
  VRTFILE = 'month-%02d.vrt' % args.month
  
  # Write the list to a file...
  with open(TMP_MONTHLISTFILE, 'w') as f:
    for i in monthfiles:
      f.write(i)
      f.write("\n")

  # Call gdalbuildvrt with the list file...
  print "Build a .vrt file with a band for each timestep in the %s file..." % TMP_MONTHLISTFILE
  rc = subprocess.call([
      'gdalbuildvrt',
      '-separate',
      '-b', '1',
      '-input_file_list', TMP_MONTHLISTFILE,
      VRTFILE
    ], stderr=subprocess.STDOUT)

  print "Return code from subprocess:", rc
  if rc != 0:
    print "Warning! There was an error in calling gdalbuildvrt!"
    if rc == -6:
      print "We think it may be safe to continue..."
    else:
      print "Not sure what is going on. Stopping."
      exit()  

  print "Cleaning up temporary month list file..."
  os.remove(TMP_MONTHLISTFILE)

  # NOTE: should we check for enough memory?? 
  print_memory_report()

  print "Opening %s file..." % VRTFILE
  monthdatafile = rasterio.open(VRTFILE)
  print "File has %s bands." % (monthdatafile.count)

  # NOTE: one based indexing...seems to be a rasterio thing?
  # or gdalvrt numbers bands starting at 1? Not sure....
  # Also, when not debugging, we want to read all the bands
  # (by not passing any arguments to the read() function. BUT 
  # this can result in a whole lot of memory usage!
  print "Reading the vrt file into memory..."
  if args.ss != None:
    ss = [int(v) for v in args.ss.split(':')]
    # should really verify/validate this elsewhere..
    if len(ss) != 2:
      print "Error with --ss argument!: %s" % args.ss
      exit(-1)
    print "Reading bands (start, stop): %s" % (str(ss))
    data = monthdatafile.read(range(ss[0],ss[1]))
  else:
    print "Reading all bands...."
    data = monthdatafile.read() #<-- empty to read all bands 

  # Make sure the mask is set 
  # NOTE: actually not even important for detrending, only
  #       for displaying. The detrend function seems to run 
  #       over all the masked points too. But the mask
  #       is key for displaying the data and having the auto-
  #       scaling work correctly...
  print "Masking extreme data..."
  data = np.ma.masked_outside(data, -100, 100, copy=False)
  print_mask_report(data)

  # Detrend for each pixel over the time axis.
  # For some reason, the detrend function seems to operate on
  # masked values. This will result in a RunTime overflow error
  # when operating on the fill values which are usually very
  # large or very small. These large or small numbers get squared
  # in the detrending fuction and we end up with overflow errors. 
  print "Detrend along time axis..."
  detrended_data = scipy.signal.detrend(data, axis=0)

  # Now make sure to add the offset back into the data
  print "Add offset to data..."
  detrended_data[:,:,:] += (data[0,:,:] - detrended_data[0,:,:])

  print "Mask extreme values..."
  print "(apparently previous mask not respected by scipy.signal.detrend and the '+=' operator)"
  detrended_data = np.ma.masked_outside(detrended_data, -100, 100)
  print_mask_report(detrended_data)

  # Apply the most aggressive mask to every timeslice.
  print "Apply the the 'any mask' from along time axis to each timestep/image..."
  for i, img in enumerate(data[:]):
      detrended_data.mask[i,:,:] = detrended_data.mask.any(0)

  print_mask_report(detrended_data)

  # NOTE: Really, here I should be writing out a netcdf file as 
  # that would prevent having to run thru gdal_translate later
  # to convert the tif to netcdf...
  # looks like 

  # Write out the data to a new series of .tif files
  print "Setup for file writing..."
  with rasterio.drivers(CPL_DEBUG=True):

    # See here for driver info
    # http://www.gdal.org/frmt_netcdf.html
    # Maybe we can set more options??
    # https://github.com/mapbox/rasterio/blob/master/docs/options.rst

    # Copy the metadata from the input vrt file
    kwargs = monthdatafile.meta

    # Change a few things about the metadata...
    kwargs.update(
      count=1,            # only one band
      #compress='',     # not sure if this is actually helping?
      driver='netCDF'      # we want .tifs, not .vrts
    )




    # guess some things about the data from the naming of the first
    # input file...
    (bname, variable, metric, scenario, month, year) = guess_from_filename(monthfiles[0])

    outputdir = os.path.join(args.outfiledir, "detrended_data", bname)

    # Make sure there is a location for outputs
    if not os.path.exists(outputdir):
      os.makedirs(outputdir)

    existing_file_list = sorted(glob.glob("%s/*_%02d_*.nc" % (outputdir, args.month)))
    print "Clean up %i existing output files for this month..." % len(existing_file_list)
    for f in existing_file_list:
      print "removing %s" % f
      os.remove(f)

    print "Write each timestep out to its own file in %s" % outputdir
    for i, timestep in enumerate(detrended_data[:]):
      # tag each file name with the timestep info (month and year)
      newfname = bname + ("_%02d_%04d.nc" % (args.month, int(year)+i)) 
      with rasterio.open( os.path.join(outputdir, newfname), 'w', **kwargs) as dst:
        dst.write_band(1, timestep.astype(rasterio.float32))

  print "Done writing timesteps to files."
  print_memory_report()




def merge_tifs_to_single_timeseries_netcdf(dir): # path to directory of files...?
  pass
  # use the first file in the list to create a empty nc file (time, lon, lat)
  # dimensions and one record variable


if __name__ == '__main__':
	
  parser = argparse.ArgumentParser(description=textwrap.dedent('''
    De-trend climate data. Takes an input file directory selects 
    a single month's files for all years. Removes trend along time
    axis, and writes a new set of netcdf files in the same "shape",
    (but with slightly different nomenclature: the netcdf file will
    have dimensions (time, y, x), while the tifs are 2D raster images
    files, with a single "band" for the variable).
  '''))

  parser.add_argument('--ss', 
    help=textwrap.dedent('''A 'start:stop' string used to generate a range of 
      bands to read. 1 based! Bands in this case are timesteps, so years, because
      the list of files should be about 100 (years) long for a single month.'''))

  parser.add_argument('month', choices=range(1,13), type=int, 
    help="Which month to process"
  )

  parser.add_argument('infiledir', 
    help="path to directory of input files"
  )

  parser.add_argument('outfiledir', 
    help="path to a directory for the output tree (which will be stored in a directory 'detrended_data/')"
  )

  args = parser.parse_args()
  #print args

  main(args)





