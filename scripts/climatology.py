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
import sys
import subprocess
import glob
import pickle
import multiprocessing

import datetime as dt

from osgeo import gdal

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('pdf')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as ticker


TMP_DATA = 'climatology-intermediate-data'


def timeseries_summary_stats_and_plots(base_path, secondary_path_list):
  '''
  '''
  # Decades for projected, truncated first
  fx_periods = [
    (2006,2010),(2010,2020),(2020,2030),(2030,2040),(2040,2050),
    (2050,2060),(2060,2070),(2070,2080),(2080,2090),(2090,2100)
  ]

  # Decades for historic, truncated at end
  hist_periods = [
    (1901,1911),(1911,1921),(1921,1931),(1931,1941),(1941,1951),
    (1951,1961),(1961,1971),(1971,1981),(1981,1991),(1991,2001),
    (2001,2011),(2011,2015)
  ]

  procs = []
  for i in secondary_path_list:
    if 'pr_total' in i.lower():
      units = 'mm month-1'
    elif 'tas_mean' in i.lower():
      units = 'degrees C'
    elif 'vap_mean' in i.lower():
      units = 'hPa'
    elif 'rsds_mean' in i.lower():
      units = 'MJ-m2-d1'
    elif 'hurs_mean' in i.lower():
      units = 'percent'
    else:
      print("ERROR! hmmm can't find variable in {}".format(i))


    if '_cru' in i.lower():
      periods = hist_periods
    elif '_mri' in i.lower():
      periods = fx_periods
    elif '_ncar' in i.lower():
      periods = fx_periods

    secondary_path = i

    print("MAIN PROCESS! [{}] Starting worker...".format(os.getpid()))
    p = multiprocessing.Process(target=worker_func, args=(base_path, secondary_path, units, periods))
    procs.append(p)
    p.start()

  print("Done starting processes. Looping to set join on each process...")
  for p in procs:
    p.join()
  print("DONE! Plots should be saved...")

def worker_func(base_path, secondary_path, units, periods):
  '''
  '''
  print("worker function! pid:{}".format(os.getpid()))
  print("  [{}] {}".format(os.getpid(), base_path))
  print("  [{}] {}".format(os.getpid(), secondary_path))
  print("  [{}] {}".format(os.getpid(), units))
  monthlies_figure = get_monthlies_figure(
      base_path, secondary_path, 
      title='\n'.join((base_path, secondary_path)),
      units=units,
      src='fresh',
      save_intermediates=False,
      madata=None
  )

  overveiw_figure, period_averages = get_overview_figure(
      periods,
      base_path, secondary_path,
      title='\n'.join((base_path, secondary_path)),
      units=units,
      src='fresh', # can be: fresh, pickle, or passed
      save_intermediates=False,
      padata=None
  )

  individual_figs, _ = get_period_avg_figures(
      periods,
      base_path, secondary_path,
      title=os.path.dirname(secondary_path),
      units=units,
      src='passed',
      padata=period_averages
  )

  # Create multi-page pdf document
  import matplotlib.backends.backend_pdf
  ofname = "climatology_{}.pdf".format(secondary_path.split("/")[0])
  print("Building PDF with many images: {}".format(ofname))
  pdf = matplotlib.backends.backend_pdf.PdfPages(ofname)
  pdf.savefig(monthlies_figure)
  pdf.savefig(overveiw_figure)
  for f in individual_figs:
    pdf.savefig(f)
  pdf.close()
  print("Done saving pdf: {}".format(ofname))


def create_vrt(filelist, ofname):
  '''
  Creates a GDAL vrt (virtual file format) for a series of input files.
  Expects the each of the files in the filelist to be a single band GeoTiff.
  The files will be combined into a single .vrt file with one Band for each
  of the input files. The single VRT file may then be further manipulated with
  GDAL (i.e take the average over all the bands).
  
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
  temporary_filelist_file = os.path.join("/tmp/", "filelist-pid-{}-{}.txt".format(os.getpid(), basename_noext))

  with open(temporary_filelist_file, 'w') as f:
    f.write("\n".join(filelist))

  result = subprocess.check_call([
    'gdalbuildvrt',
    '-overwrite', 
    '-separate',
    ofname,
    '-input_file_list', temporary_filelist_file
  ])

  os.remove(temporary_filelist_file)


def average_over_bands(ifname, bands='all'):
  '''
  Given an input file (`ifname`), this function computes the average over all
  the bands and returns the result. Assumes the bands are named Band1, Band2,
  etc.
  
  Parameters
  ----------
  ifname : str
    A multi-band file that can be opened and read with GDAL. Expects that all 
    bands have data and are the same spatial extents. Ignored data less 
    than -9999.

  bands : str
    One of 'all', 'first10', or 'first3'. Selects a subset of bands for faster
    processing for testing and development.
  
  Returns
  -------
  avg : numpy masked array
     Returned array is the same shape as an individual band in the input file,
     and with each pixel being the average of the pixel values in all of the
     input file's bands.
  '''
  ds = gdal.Open(ifname)
  print(" [ DESCRIPTION ]: ", ds.GetDescription())

  print(" [ RASTER BAND COUNT ]: ", ds.RasterCount)
  print(" [ RASTER Y SIZE ]: ", ds.RasterYSize)
  print(" [ RASTER X SIZE ]: ", ds.RasterXSize)

  if bands == 'all':
    band_range = list(range(1, ds.RasterCount+1))
  elif bands == 'first10':
    band_range = list(range(1, 10+1))
  elif bands == 'first3':
    band_range = list(range(1, 3+1))

  print(" [ AVERAGE OVER BANDS ]: {}".format(len(band_range)))
  print(" [ START BAND ]: {}".format(band_range[0]))
  print(" [ END BAND ]: {}".format(band_range[-1]))

  # allocate a storage location
  running_sum = np.ma.masked_less_equal(np.zeros((ds.RasterYSize, ds.RasterXSize)), -9999)

  for band in band_range:
    dsb = ds.GetRasterBand(band)
    if dsb is None:
      print("huh??")
      # continue (? as per example here: https://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.html)
    
    masked_data = np.ma.masked_less_equal(dsb.ReadAsArray(), -9999)

    running_sum += masked_data
    print("adding band: {} band min/max: {}/{} running_sum min/max: {}/{}".format(
        band,
        masked_data.min(), masked_data.max(),
        running_sum.min(), running_sum.max()
    ))

  # Compute average
  avg = running_sum / float(len(band_range)+1)
  
  # Close gdal file
  ds = None

  return avg


def read_period_averages(periods):
  '''
  Reads pickled period average data from the TMP_DATA directory. Expects files
  to be in a further sub-directory, period-averages, and have names
  like: "pa-{start}-{end}.pickle".

  Parameters
  ----------
  periods : list of tuples
    Each tuple should have values (start, end) that are used to define the
    period.

  Returns
  -------
  period_averages : list
    A list of (masked) numpy arrays that have been un-pickled from the TMP_DATA
    directory. The pickles are expected to be the period averages built using
    other routines in this script.
  '''
  print("Reading period average pickles into list...")
  period_averages = []
  for i, (start, end) in enumerate(periods):

    path = os.path.join(TMP_DATA, 'period-averages-pid{}'.format(os.getpid()), 'pa-{}-{}.pickle'.format(start, end))
    pa = pickle.load(file(path))
    period_averages.append(pa)

  print("Done reading period average pickles into list.")
  return period_averages


def read_monthly_pickles(months=list(range(1,13))):

  print("reading monthly pickle files for months {}...".format(months))
  mavgs = []
  for m in months:
    path = os.path.join(
        TMP_DATA,
        'month-averages-pid{}'.format(os.getpid()),
        'month-{:02d}.pickle'.format(m)
    )
    ma = pickle.load(file(path))
    mavgs.append(ma)
  print("Returning monthly averages list..")
  return mavgs


def calculate_period_averages(periods, base_path, secondary_path, save_intermediates=False):
  '''Given a stack of tif files, one file for each month, this routine will
  calculate the averages for the supplied periods. Periods are expected to be
  selections of years, i.e. 1901 to 1911.
  
  Parameters
  ----------
  periods : list of tuples
    each tuple has a start and end year for the period

  base_path : str
    path on the file system where files are located

  secondary_path : str
    remainder of path on file system where files will be found. The secondary
    path string is expected to be somethign like this:
        "ar5_MRI-CGCM3_rcp85_{month:}_{year:}.tif" 
    with the one set of braces for the month one set of braces for the year.
    This function will fill the braces to match any month and the years
    specified in the periods tuples

  save_intermediates : bool
    when true, period average array will be pickled for each period. Will be 
    saved like so 'climatology/period-averages/pa-{}-{}.pickle'

  Returns
  -------
  list of 2D masked numpy arrays
  '''
  # Ensure there is a place to put the vrt files 
  path = os.path.join(TMP_DATA, 'period-averages-pid{}'.format(os.getpid()))
  try: 
    os.makedirs(path)
  except OSError:
    if not os.path.isdir(path):
      raise
  # Make the VRTs for the periods
  for i, (start, end) in enumerate(periods):
    print("[ period {} ] Making vrt for period {} to {} (range {})".format(i, start, end, list(range(start, end))))
    filelist = []
    for year in range(start, end):
      final_secondary_path = secondary_path.format(month="*", year="{:04d}")
      #print os.path.join(base_path, final_secondary_path.format(year))
      single_year_filelist = sorted(glob.glob(os.path.join(base_path, final_secondary_path.format(year))))
      #print "Length of single year filelist {}".format(len(single_year_filelist))
      filelist += single_year_filelist
    print("Length of full filelist: {} ".format(len(filelist)))
    vrtp = os.path.join(TMP_DATA, 'period-averages-pid{}'.format(os.getpid()), "period-{}-{}.vrt".format(start, end))
    create_vrt(filelist, vrtp)

  # Calculate the period averages from the VRT files
  period_averages = []
  for i, (start, end) in enumerate(periods):
  
    # Find the average over the selected range
    vrtp = os.path.join(TMP_DATA, 'period-averages-pid{}'.format(os.getpid()), "period-{}-{}.vrt".format(start, end))
    pa = average_over_bands(vrtp, bands='all')
    period_averages.append(pa)

    if save_intermediates:
      # Make sure there is a place to put our pickles 
      path = os.path.join(TMP_DATA, 'period-averages-pid{}'.format(os.getpid()))
      try: 
        os.makedirs(path)
      except OSError:
        if not os.path.isdir(path):
          raise
      print("Dumping pickle for period {} to {}".format(start, end))
      pickle.dump(pa, file(os.path.join(path, "pa-{}-{}.pickle".format(start, end)), 'wb'))
  
  # Clean up any intermediate files.
  if not save_intermediates:
    papath = os.path.join(TMP_DATA, 'period-averages-pid{}'.format(os.getpid()))
    for f in os.listdir(papath):
      os.remove(os.path.join(papath, f))
    os.rmdir(papath)

  print("Returning period averages list...")
  return period_averages


def calculate_monthly_averages(months, base_path, secondary_path, save_intermediates=False):
  '''
  '''
  # Make sure there is a place to put our pickles and vrt files
  intermediates_path = os.path.join(TMP_DATA, 'month-averages-pid{}'.format(os.getpid()))
  try: 
    os.makedirs(intermediates_path)
  except OSError:
    if not os.path.isdir(intermediates_path):
      raise

  # Build the vrt files
  print("Creating monthly VRT files...")
  for im, MONTH in enumerate(months[:]):
    final_secondary_path = secondary_path.format(month="{:02d}", year="*").format(im+1)
    filelist = sorted(glob.glob(os.path.join(base_path, final_secondary_path)))
    if len(filelist) < 1:
      print("ERROR! No files found in {}".format( os.path.join(base_path, final_secondary_path) ))

    vrt_path = os.path.join(intermediates_path,"month-{:02d}.vrt".format(im+1))
    create_vrt(filelist, vrt_path)

  print("Computing monthly averages from monthly VRT files...")
  # make list of expected input vrt paths
  ivp_list = [os.path.join(intermediates_path,"month-{:02d}.vrt".format(im)) for im in range(1, len(months)+1)]
  monthly_averages = [average_over_bands(ivp, bands='all') for ivp in ivp_list]

  if save_intermediates:
    print("Saving pickles...")
    for im, ma in enumerate(monthly_averages):
      pp = os.path.join(intermediates_path, "month-{:02d}.pickle".format(im+1))
      pickle.dump(ma, file(pp, 'wb'))
    print("Done saving pickles...")

  # Clean up any intermediate files.
  if not save_intermediates:
    mapath = os.path.join(TMP_DATA, 'month-averages-pid{}'.format(os.getpid())) 
    for f in os.listdir(mapath):
      os.remove(os.path.join(mapath, f))
    os.rmdir(mapath)

  print("Returning monthly_averages list...")
  return monthly_averages


def get_monthlies_figure(base_path, secondary_path, title, units, 
    src='fresh', save_intermediates=True, madata=None ):
  '''
  Creates a single figure with 12 subplots, each showing the average for that
  month across the timeseries.
  '''
  months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

  if src == 'fresh':
    monthly_averages = calculate_monthly_averages(months, base_path, secondary_path, save_intermediates=save_intermediates)

  elif src == 'pickle':
    monthly_averages = read_monthly_pickles(months=list(range(1,13)))

  elif src == 'passed':
    monthly_averages = madata 

  else:
    print("Invalid argument for src! '{}'".format(src))

  vmax = np.max([avg.max() for avg in monthly_averages])
  vmin = np.min([avg.min() for avg in monthly_averages])
  print("vmax: {}  vmin: {}".format(vmax, vmin))

  print("Creating monthlies figure...")
  fig, axes = plt.subplots(figsize=(11,8.5), nrows=3, ncols=4, sharex=True, sharey=True)
  imgs = []
  for ax, avg, month in zip(axes.flat, monthly_averages, months):
    im = ax.imshow(avg, vmin=vmin, vmax=vmax, cmap='gist_ncar')
    imgs.append(im)
    ax.set_title(month)

  cbar = fig.colorbar(imgs[0], ax=axes.ravel().tolist())
  cbar.set_label(units)
  fig.suptitle(title)

  print("Done creating monthlies figure.") 
  return fig


def get_overview_figure(periods, base_path, secondary_path, title='', 
    units='', src='fresh', save_intermediates=True, padata=None):
  '''
  Creates and returns a matplotlib figure that has ??
  
  Parameters
  ----------
  
  Returns
  -------
  fig : matplotlib figure instance
  '''
  if src == 'fresh':
    period_averages = calculate_period_averages(periods, base_path, secondary_path, save_intermediates=save_intermediates)
  elif src == 'pickle':
    period_averages = read_period_averages(periods)
  elif src == 'passed':
    period_averages = padata 
  else:
    print("Invalid argument for src! '{}'".format(src))
    
  print("Converting to stacked masked array...")
  pa2 = np.ma.stack(period_averages)
  vmax = pa2.max()
  vmin = pa2.min()  
  print("vmax: {}  vmin: {}".format(vmax, vmin))

  NCOLS = 4     # fixed number of cols, may add more rows
  NROWS = len(period_averages)/NCOLS
  if (len(period_averages) % NCOLS) > 0:
    NROWS += 1

  if len(period_averages) < NCOLS:
    NCOLS = len(period_averages)
    NROWS = 1

  overview_fig, axes = plt.subplots(nrows=NROWS, ncols=NCOLS, sharex=True, sharey=True)
  overview_fig.set_size_inches((11, 8.5), forward=True)

  imgs = []  # in case we need to manipulate the images all at once
  for ax, avg, period in zip(axes.flat, period_averages, periods):
    print("plotting image for period:", period)

    # Setting vmax and vmin normalized the colorbars across all images
    im = ax.imshow(avg, vmin=vmin, vmax=vmax, cmap='gist_ncar')
    ax.set_title('{} to {}'.format(period[0], period[1]))
    imgs.append(im)
  
  # set a colorbar on the first axes
  cbar = overview_fig.colorbar(imgs[0], ax=axes.ravel().tolist())
  cbar.set_label(units)
  overview_fig.suptitle(title) 

  return overview_fig, period_averages
  

def get_period_avg_figures(periods, base_path, secondary_path,
    title='', units='', src='fresh', save_intermediates=True, padata=None):
  '''

  Parameters
  ----------

  Returns
  -------
  '''
  if src == 'fresh':
    period_averages = calculate_period_averages(periods, base_path, secondary_path, save_intermediates=save_intermediates)
  elif src == 'pickle':
    period_averages = read_period_averages(periods)
  elif src == 'passed':
    period_averages = padata 
  else:
    print("Invalid argument for src! '{}'".format(src))

  print("Converting to stacked masked array...")
  pa2 = np.ma.stack(period_averages)
  vmax = pa2.max()
  vmin = pa2.min()  
  print("vmax: {}  vmin: {}".format(vmax, vmin))

  ind_figures = []
  for i, ((start,end), periodavg) in enumerate(zip(periods, pa2)):
    fig = plt.figure()
    fig.suptitle(title) #fontsize=8
    im = plt.imshow(periodavg, vmin=vmin, vmax=vmax, cmap='gist_ncar')
    ax = fig.axes[0]
    ax.set_title('Average, {} to {}'.format(start, end))
    cbar = plt.colorbar()
    cbar.set_label(units)

    ind_figures.append(fig)
  
  return ind_figures, padata


def worker_func2(f):
  if f == 'file3':
    time.sleep(1)
  if f == 'file7':
    time.sleep(5)
  print("will open, read, average {}".format(f))
  return f

def worker_func3(in_file_path):
  '''
  '''
  # Deduce month and year from file name
  bname = os.path.basename(in_file_path)
  n, ext = os.path.splitext(bname)
  parts = n.split('_')
  month, year = [int(p) for p in parts[-2:]]
  date = dt.date(year=year, month=month, day=1)

  # Open the file, get some stats
  ds = gdal.Open(in_file_path)
  ds_array = ds.ReadAsArray()
  ds_m = np.ma.masked_less_equal(ds_array, -9999)

  data_dict = dict(
      fname=bname, 
      date=date, 
      statewide_mean=ds_m.mean(), 
      statewide_min=ds_m.min(), 
      statewide_max=ds_m.max(), 
      statewide_std=ds_m.std()
  )

  return data_dict



def generate_spatial_summary_stats(base_path, secondary_path):
  '''
  '''
  # This produces a bunch of csv files with statewide averages
  for sec_path in secondary_path_list[0:]:

    files = sorted(glob.glob(os.path.join(base_path, sec_path.format(month='*', year='*'))))

    p = multiprocessing.Pool()
    results = p.map(worker_func3, files[0:])
    p.close()
    p.join()

    s_results = sorted(results, key=lambda k: k['date'])

    stats_path = "SPATIAL_SUMMARY_STATS_{}.csv".format(sec_path.split('/')[0])

    import pandas as pd
    df = pd.DataFrame(s_results)
    df.to_csv(stats_path)

def plot_timeseries_of_spatial_summary_stats():
  '''
  '''
  # Build this automatically:
  #   - look for SPATIAL_SUMMARY_STATS_*
  ss_file_list = [
    'SPATIAL_SUMMARY_STATS_hurs_mean_pct_ar5_MRI-CGCM3_rcp85_2006_2100_fix.csv',
    'SPATIAL_SUMMARY_STATS_hurs_mean_pct_ar5_NCAR-CCSM4_rcp85_2006_2100_fix.csv',
    'SPATIAL_SUMMARY_STATS_hurs_mean_pct_iem_CRU-TS40_historical_1901_2015_fix.csv',

    'SPATIAL_SUMMARY_STATS_pr_total_mm_ar5_MRI-CGCM3_rcp85_2006_2100.csv',
    'SPATIAL_SUMMARY_STATS_pr_total_mm_ar5_NCAR-CCSM4_rcp85_2006_2100.csv',
    'SPATIAL_SUMMARY_STATS_pr_total_mm_iem_cru_TS40_1901_2015.csv',

    'SPATIAL_SUMMARY_STATS_rsds_mean_MJ-m2-d1_ar5_MRI-CGCM3_rcp85_2006_2100_fix.csv',
    'SPATIAL_SUMMARY_STATS_rsds_mean_MJ-m2-d1_ar5_NCAR-CCSM4_rcp85_2006_2100_fix.csv',
    'SPATIAL_SUMMARY_STATS_rsds_mean_MJ-m2-d1_iem_CRU-TS40_historical_1901_2015_fix.csv',

    'SPATIAL_SUMMARY_STATS_tas_mean_C_ar5_MRI-CGCM3_rcp85_2006_2100.csv',
    'SPATIAL_SUMMARY_STATS_tas_mean_C_ar5_NCAR-CCSM4_rcp85_2006_2100.csv',
    'SPATIAL_SUMMARY_STATS_tas_mean_C_iem_cru_TS40_1901_2015.csv',

    'SPATIAL_SUMMARY_STATS_vap_mean_hPa_ar5_MRI-CGCM3_rcp85_2006_2100_fix.csv',
    'SPATIAL_SUMMARY_STATS_vap_mean_hPa_ar5_NCAR-CCSM4_rcp85_2006_2100_fix.csv',
    'SPATIAL_SUMMARY_STATS_vap_mean_hPa_iem_CRU-TS40_historical_1901_2015_fix.csv',
  ]

  # Create multi-page pdf document
  import matplotlib.backends.backend_pdf
  ofname = "climatology_statewide_averages.pdf".format()
  print("Saving PDF: {}".format(ofname))
  pdf = matplotlib.backends.backend_pdf.PdfPages(ofname)

  var_list = ['tas_mean','pr_total','rsds_mean','vap_mean','hurs_mean']
  unit_list = ['celsius', 'mm month-1', 'MJ-m2-d1','hPa', 'percent']
  for var, units in zip(var_list, unit_list):

    # Figure out the right files to work on
    var_files = [x for x in ss_file_list if var in x.lower()]
    print(var_files)
    print()
    h_file = [x for x in var_files if 'cru' in x.lower()]
    pmri_file = [x for x in var_files if 'mri' in x.lower()]
    pncar_file = [x for x in var_files if 'ncar' in x.lower()]

    # Filtering above should result in single item lists, unpack for convenience.
    h_file = h_file[0]
    pmri_file = pmri_file[0]
    pncar_file = pncar_file[0]

    print("var: ", var)
    print("hfile: ", h_file)
    print("pmri_file: ", pmri_file)
    print("pncar_file: ", pncar_file)
    print()

    # Read data into DataFrames
    hdf = pd.read_csv( h_file )
    hdf.set_index( pd.to_datetime(hdf['date']), inplace=True )

    pmri_df = pd.read_csv( pmri_file )
    pmri_df.set_index( pd.to_datetime(pmri_df['date']), inplace=True )

    pncar_df = pd.read_csv( pncar_file )
    pncar_df.set_index( pd.to_datetime(pncar_df['date']), inplace=True )

    # build an index for the whole range, historic & projected
    full_index = pd.DatetimeIndex(start=hdf.index[0], end=pncar_df.index[-1], freq="MS")

    hdf_f = hdf.reindex(full_index)
    pmri_df_f = pmri_df.reindex(full_index)
    pncar_df_f = pncar_df.reindex(full_index)

    rsmpl_mean_h = hdf_f.resample('A').mean()
    rsmpl_std_h = hdf_f.resample('A').std()
    rsmpl_sum_h = hdf_f.resample('A').sum()

    rsmpl_mean_pncar = pncar_df_f.resample('A').mean()
    rsmpl_std_pncar = pncar_df_f.resample('A').std()
    rsmpl_sum_pncar = pncar_df_f.resample('A').sum()

    rsmpl_mean_pmri = pmri_df_f.resample('A').mean()
    rsmpl_std_pmri = pmri_df_f.resample('A').std()
    rsmpl_sum_pmri = pmri_df_f.resample('A').sum()

    fig = plt.figure(figsize=(11,8.5))
    fig.suptitle( "\n".join((h_file, pmri_file, pncar_file)) )

    plt.ylabel(units)

    if var == 'pr_total':

      # For precip, make sure to sum over the year instead of taking the mean.
      # Also take care when plotting the standard deviation too as it is
      # confusing which DataFrame and column to use.

      plt.ylabel(units.replace('month', 'year'))

      from IPython import embed; embed()

      # Confusing here, but the following masks the zero sums...
      plt.plot(rsmpl_sum_h['statewide_mean'][rsmpl_sum_h.statewide_mean>0], label='cru-ts40 +/-1 stdv')
      plt.fill_between(
          rsmpl_sum_h.index,
          rsmpl_sum_h['statewide_mean']+rsmpl_mean_h['statewide_std'],
          rsmpl_sum_h['statewide_mean']-rsmpl_mean_h['statewide_std'],
          alpha=0.25
      )

      plt.plot(rsmpl_sum_pncar['statewide_mean'][rsmpl_sum_pncar.statewide_mean>0], label='ncar-ccsm4 +/-1 stdv')
      plt.fill_between(
          rsmpl_sum_pncar.index,
          rsmpl_sum_pncar['statewide_mean']+rsmpl_mean_pncar['statewide_std'],
          rsmpl_sum_pncar['statewide_mean']-rsmpl_mean_pncar['statewide_std'],
          alpha=0.25
      )

      plt.plot(rsmpl_sum_pmri['statewide_mean'][rsmpl_sum_pmri.statewide_mean>0], label='mri-cgcm3 +/-1 stdv')
      plt.fill_between(
          rsmpl_sum_pmri.index,
          rsmpl_sum_pmri['statewide_mean']+rsmpl_mean_pmri['statewide_std'],
          rsmpl_sum_pmri['statewide_mean']-rsmpl_mean_pmri['statewide_std'],
          alpha=0.25
      )


    else:
      plt.plot(rsmpl_mean_h['statewide_mean'], label='cru-ts40 +/-1 stdv')
      plt.fill_between(
          rsmpl_mean_h.index,
          rsmpl_mean_h['statewide_mean']+rsmpl_mean_h['statewide_std'],
          rsmpl_mean_h['statewide_mean']-rsmpl_mean_h['statewide_std'],
          alpha=0.25
      )

      plt.plot(rsmpl_mean_pncar['statewide_mean'], label='ncar-ccsm4 +/-1 stdv')
      plt.fill_between(
          rsmpl_mean_pncar.index,
          rsmpl_mean_pncar['statewide_mean']+rsmpl_mean_pncar['statewide_std'],
          rsmpl_mean_pncar['statewide_mean']-rsmpl_mean_pncar['statewide_std'],
          alpha=0.25
      )

      plt.plot(rsmpl_mean_pmri['statewide_mean'], label='mri-cgcm3 +/-1 stdv')
      plt.fill_between(
          rsmpl_mean_pmri.index,
          rsmpl_mean_pmri['statewide_mean']+rsmpl_mean_pmri['statewide_std'],
          rsmpl_mean_pmri['statewide_mean']-rsmpl_mean_pmri['statewide_std'],
          alpha=0.25
      )

    plt.legend()
    #plt.show(block=True)    

    print("Saving fig to pdf for {}".format(var))
    pdf.savefig(fig)

  print("Closing PDF: {}".format(ofname))
  pdf.close()



if __name__ == '__main__':

  if len(sys.argv) > 1:
    if '-h' in sys.argv or '--help' in sys.argv:
      print("There is not a proper command line interface built for this script.")
      print("Read the code to figure out what it does!")

  print("PID: {}".format(os.getpid()))
  print("Temporary file storage: {}".format(TMP_DATA))

  print("For use with slurm (generating and saving multi-page pdfs) you have ")
  print("to import matplotlib and then set the backend explicitly, or you ")
  print("have issues with related to the DISPLAY environment variable. ")
  print("For interactive development use, comment those import lines out at ")
  print("the top of the file and use plt.show(block=True) instead of savefig() ")
  print("in the code.")
  

  base_path = '/atlas_scratch/ALFRESCO/ALFRESCO_Master_Dataset_v2_1/ALFRESCO_Model_Input_Datasets/IEM_for_TEM_inputs/'

  secondary_path_list = [
    'pr_total_mm_iem_cru_TS40_1901_2015/pr_total_mm_CRU_TS40_historical_{month:}_{year:}.tif',
    'pr_total_mm_ar5_MRI-CGCM3_rcp85_2006_2100/pr/pr_total_mm_iem_ar5_MRI-CGCM3_rcp85_{month:}_{year:}.tif',
    'pr_total_mm_ar5_NCAR-CCSM4_rcp85_2006_2100/pr/pr_total_mm_iem_ar5_NCAR-CCSM4_rcp85_{month:}_{year:}.tif',

    'tas_mean_C_iem_cru_TS40_1901_2015/tas/tas_mean_C_CRU_TS40_historical_{month:}_{year:}.tif',
    'tas_mean_C_ar5_MRI-CGCM3_rcp85_2006_2100/tas/tas_mean_C_iem_ar5_MRI-CGCM3_rcp85_{month:}_{year:}.tif',
    'tas_mean_C_ar5_NCAR-CCSM4_rcp85_2006_2100/tas/tas_mean_C_iem_ar5_NCAR-CCSM4_rcp85_{month:}_{year:}.tif',

    'hurs_mean_pct_iem_CRU-TS40_historical_1901_2015_fix/hurs/hurs_mean_pct_iem_CRU-TS40_historical_{month:}_{year:}.tif',
    'hurs_mean_pct_ar5_MRI-CGCM3_rcp85_2006_2100_fix/hurs/hurs_mean_pct_iem_ar5_MRI-CGCM3_rcp85_{month:}_{year:}.tif',
    'hurs_mean_pct_ar5_NCAR-CCSM4_rcp85_2006_2100_fix/hurs/hurs_mean_pct_iem_ar5_NCAR-CCSM4_rcp85_{month:}_{year:}.tif',

    'rsds_mean_MJ-m2-d1_iem_CRU-TS40_historical_1901_2015_fix/rsds/rsds_mean_MJ-m2-d1_iem_CRU-TS40_historical_{month:}_{year:}.tif',
    'rsds_mean_MJ-m2-d1_ar5_MRI-CGCM3_rcp85_2006_2100_fix/rsds/rsds_mean_MJ-m2-d1_iem_ar5_MRI-CGCM3_rcp85_{month:}_{year:}.tif',
    'rsds_mean_MJ-m2-d1_ar5_NCAR-CCSM4_rcp85_2006_2100_fix/rsds/rsds_mean_MJ-m2-d1_iem_ar5_NCAR-CCSM4_rcp85_{month:}_{year:}.tif',

    'vap_mean_hPa_iem_CRU-TS40_historical_1901_2015_fix/vap/vap_mean_hPa_iem_CRU-TS40_historical_{month:}_{year:}.tif',
    'vap_mean_hPa_ar5_MRI-CGCM3_rcp85_2006_2100_fix/vap/vap_mean_hPa_iem_ar5_MRI-CGCM3_rcp85_{month:}_{year:}.tif',
    'vap_mean_hPa_ar5_NCAR-CCSM4_rcp85_2006_2100_fix/vap/vap_mean_hPa_iem_ar5_NCAR-CCSM4_rcp85_{month:}_{year:}.tif',
  ]

  print("{} CPU Count: {}".format(os.getpid(), multiprocessing.cpu_count()))
  

  # Builds maps and figures (multi-page pdfs) of monthly averages and or 
  # decadal averages (or arbitrary time range).
  # Uses multiprocessing.Process to get parallelism over each set of files
  # (one of the items in the secondary_path_list) 
  # Takes ~12 minutes on atlas
  #timeseries_summary_stats_and_plots(base_path, secondary_path_list)

  # Generate csv files with mean and other summary stats that are taken over
  # the entire spatial domain (statewide). Uses multiprocessing.Pool to get 
  # parallelism over all the individual files - could benefit from up to 1000
  # cores (one for each file in the timeseries)
  # Takes ~6 minutes on atlas
  generate_spatial_summary_stats(base_path, secondary_path_list)


  # Make plots of the summary stats file created in the previous function.
  # Runs fast...
  plot_timeseries_of_spatial_summary_stats()


# Decades for historic period - works nicely, truncated at end
#   FREQ = 10; START = 1901; END = 2015
#   srange = range(START, END, FREQ)
#   erange = range(START+FREQ, END, FREQ)
#   periods = zip(srange, erange)
#   periods.append( (erange[-1], END ) )