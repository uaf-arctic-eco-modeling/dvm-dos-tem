#!/usr/bin/env python
'''
Tobey Carman October 2018

Scripts for looking at and evaluating input data files for dvmdostem.
Generally data has been prepared by M. Lindgren of SNAP for the IEM project and
consists of directories of well labled .tif images, with one image for each
timestep.

This script has (or will have) a variety of routines for summarizing the data
and displaying plots that will let us look for problems, missing data, or 
anomolies.
'''

import os
import subprocess
import glob

#import multiprocessing as mp

from osgeo import gdal

import numpy as np
import matplotlib.pyplot as plt


def create_vrt(filelist, ofname):
  '''
  Creates a GDAL vrt (virtual file format) for a series of input files.
  Expects the each of the files in the filelist to be a single band GeoTiff.
  The files will be combined into a .vrt file which may then be further 
  manipulated with GDAL
  
  Parameters
  ----------
  filelist : list of strings (paths) to files that will be combined
  ofname : string for a filename that will be written
  
  Returns
  -------
  None

  Use Cases, Examples
  -------------------
   - Create a monthly or decadal summary file for a set of images representing
   a timeseries (e.g. tifs that will be pre-processed and turned to netcdf files
   for dvmdostem runs).
  '''

  basename = os.path.basename(ofname)
  basename_noext, ext =  os.path.splitext(basename)
  temporary_filelist_file = os.path.join("/tmp/", "filelist-{}.txt".format(basename_noext))

  with open(temporary_filelist_file, 'w') as f:
    f.write("\n".join(filelist))

  result = subprocess.check_call([
    'gdalbuildvrt', 
    '-separate',
    ofname,
    '-input_file_list', temporary_filelist_file
  ])

  os.remove(temporary_filelist_file)

def average_over_bands(ifname, bands='all'):
  '''
  Given an input file (`ifname`), this function computes the average over all
  the bands and returns the result.
  
  Parameters
  ----------
  ifname : A multi-band file that can be opened and read with GDAL. Expects
  that all bands have data and are the same spatial extents. Ignored data less
  than -9999.
  
  Returns
  -------
  avg : numpy masked array which is the same shape as an individual band in the
  input file, and with each pixel being the average of the pixel values in all
  of the input file's bands.
  '''
  ds = gdal.Open(ifname)
  print " [ DESCRIPTION ]: ", ds.GetDescription()

  print " [ RASTER BAND COUNT ]: ", ds.RasterCount
  print " [ RASTER Y SIZE ]: ", ds.RasterYSize
  print " [ RASTER X SIZE ]: ", ds.RasterXSize

  if bands == 'all':
    band_range = range(1, ds.RasterCount+1)
  elif bands == 'first10':
    band_range = range(1, 10+1)
  elif bands == 'first3':
    band_range = range(1, 3+1)

  print " [ AVERAGE OVER BANDS ]: {}".format(len(band_range))
  print " [ START BAND ]: {}".format(band_range[0])
  print " [ END BAND ]: {}".format(band_range[-1])

  # allocate a storage location
  running_sum = np.ma.masked_less_equal(np.zeros((ds.RasterYSize, ds.RasterXSize)), -9999)

  for band in band_range:
    dsb = ds.GetRasterBand(band)
    if dsb is None:
      print "huh??"
      # continue (? as per example here: https://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.html)
    
    masked_data = np.ma.masked_less_equal(dsb.ReadAsArray(), -9999)

    running_sum += masked_data
    print "adding band: {} band min/max: {}/{} running_sum min/max: {}/{}".format(
        band,
        masked_data.min(), masked_data.max(),
        running_sum.min(), running_sum.max()
    )

  # Compute average
  avg = running_sum / float(len(band_range)+1)
  
  # Close gdal file
  ds = None

  return avg


def plot_monthly_averages(base_path, secondary_path, title, units):
  '''
  Creates a single figure with 12 subplots, each showing the average for that
  month across the timeseries.
  '''
  months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

  for im, MONTH in enumerate(months[0:]):
    final_secondary_path = secondary_path.format("{:02d}", "*").format(im+1)
    filelist = sorted(glob.glob(os.path.join(base_path, final_secondary_path)))
    create_vrt(filelist, "month-{:02d}.vrt".format(im+1))

  # pool = mp.Pool(processes=len(months))
  # monthly_averages = pool.map(average_over_bands, 
  # 
  # procs = []
  # for im, MONTH in enumerate(months[0:])
  #   proc = mp.Process(target=average_over_bands, args=("month-{:02d}.vrt".format(im+1), bands='all'))
  #   procs.append(proc)
  #   proc.start()
  # for proc in procs.join()
    
  monthly_averages = [average_over_bands("month-{:02d}.vrt".format(im+1), bands='all') for im, MONTH in enumerate(months[0:])]

  vmax = np.max([avg.max() for avg in monthly_averages])
  vmin = np.min([avg.min() for avg in monthly_averages])
  print "vmax: {}  vmin: {}".format(vmax, vmin)
  fig, axes = plt.subplots(nrows=3, ncols=4, sharex=True, sharey=True)
  imgs = []
  for ax, avg, month in zip(axes.flat, monthly_averages, months):
    im = ax.imshow(avg, vmin=vmin, vmax=vmax)
    imgs.append(im)
    ax.set_title(month)

  cbar = fig.colorbar(imgs[0], ax=axes.ravel().tolist())
  #cbar.set_ticks(cbarlabels)
  #cbar.set_ticklabels(cbarlabels)
  cbar.set_label(units)
  fig.suptitle(title)

  plt.show(block=True)


def plot_period_averages(periods, base_path, secondary_path, title=""):
  '''
  Creates plots of averages over the given periods. Creates a multi-page pdf
  document with one plot for each of the periods specified in the input args.
  Along the way a number of GDAL VRT files are created in your working directory
  that summarize the periods to be averaged.
  
  periods : list of tuples with start and end year (not inclusive of end) to average over
  '''
  for i, (start, end) in enumerate(periods):
    print i, start, end, range(start, end)
    filelist = []
    for year in range(start, end):
      final_secondary_path = secondary_path.format("*", "{:04d}")
      #print os.path.join(base_path, final_secondary_path.format(year))
      single_year_filelist = sorted(glob.glob(os.path.join(base_path, final_secondary_path.format(year))))
      #print single_year_filelist
      filelist += single_year_filelist
    #print len(filelist)
    create_vrt(filelist, "period-{}-{}.vrt".format(start, end))
  
  period_averages = []
  for i, (start, end) in enumerate(periods):
    period_averages.append(average_over_bands("period-{}-{}.vrt".format(start, end), bands='all'))

  import matplotlib.backends.backend_pdf
  pdf = matplotlib.backends.backend_pdf.PdfPages("output.pdf")
  for i, ((start,end), periodavg) in enumerate(zip(periods, period_averages)):
    fig = plt.figure()
    fig.suptitle("\n".join([title, "Period Average {} to {}".format(start, end)]), fontsize=8)
    plt.imshow(periodavg)
    plt.colorbar()
    pdf.savefig(fig)
  pdf.close()



if __name__ == '__main__':

  base_path = '/atlas_scratch/ALFRESCO/ALFRESCO_Master_Dataset_v2_1/ALFRESCO_Model_Input_Datasets/IEM_for_TEM_inputs/'

  #secondary_path = 'rsds_mean_MJ-m2-d1_MRI-CGCM3_rcp85_2006_2100_fix/rsds/rsds_mean_MJ-m2-d1_iem_ar5_MRI-CGCM3_rcp85_{}_{}.tif'
  secondary_path = 'vap_mean_hPa_MRI-CGCM3_rcp85_2006_2100_fix/vap/vap_mean_hPa_iem_ar5_MRI-CGCM3_rcp85_{}_{}.tif'

  #plot_monthly_averages(base_path, secondary_path, 'rsds_mean_MJ-m2-d1_MRI-CGCM3_rcp85_2006_2100 monthly averages', 'MJ-m2-d1')

  periods = [
    (2006,2010),(2010,2020),(2020,2030),(2030,2040),(2040,2050),
    (2050,2060),(2060,2070),(2070,2080),(2080,2090),(2090,2100)
  ]
  plot_period_averages(periods, base_path, secondary_path, title="\n".join([base_path,secondary_path]))
  


  
  
  
  