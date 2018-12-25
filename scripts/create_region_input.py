#!/usr/bin/env python


from subprocess import call
from subprocess import check_call
import subprocess

import shutil

import multiprocessing as mp

import configobj
import argparse
import textwrap
import os

import netCDF4

import datetime as dt
import numpy as np

import glob


# for now, keep to a rectangular requirement?
# Select y,x or lat,lon bounding box coordinates for use?


# Data should be in a rectangular (grid) layout, NetCDF format.
# Should aim to conforms to CF & COARDS standards
# Geospatial information must be with the file. Each file should have 
# variables for Lat and Lon each defined in terms of the dimensions of (y,x) 
# where (y,x) are the rectangular grid coordinates.
#  --> Since extracting the Lat/Long info seems to be one of the slowest parts
#      of the process, and because keeping it in every file would result in 
#      a lot of redundant info, for now we are only storing spatial info
#      with the climate files.


def source_attr_string(ys='', xs='', yo='', xo='', msg=''):
  '''
  Returns a string to be included as a netCDF global attribute named "source".

  The string will start with the filename and function name responsible for
  creating the (new) input file, and if provided, will include values for size
  and offset. The size attributes are relatively self-explanatory (by looking
  at the size of the resulting file), and so can generally be ignored. The
  offset arguments are much more important to include.

  Parameters
  ----------
  ys, xs : str
    Strings denoting the spatial size of the domain.
  yo, xo : str
    Strings denoting the pixel offsets used by gdal_translate to create the
    input dataset.
  msg : str
    An additional message string to be included.

  Returns
  -------
  s : str
    A string something like:
    "./create_region_input.py::fill_veg_file --xoff 915 --yoff 292"
  '''
  import inspect
  cf = inspect.currentframe().f_back # <-- gotta look up one frame.

  # Start with the file name and function name
  s = "{}::{}".format(cf.f_code.co_filename, cf.f_code.co_name,)

  # add other info if present.
  for t, val in zip(['--xsize','--ysize','--xoff','--yoff',''],[xs,ys,xo,yo,msg]):
    if val != '':
      s += " {} {}".format(t, val)

  return s


def make_run_mask(filename, sizey=10, sizex=10, setpx='', match2veg=False):
  '''Generate a file representing the run mask'''

  print "Creating a run_mask file, %s by %s pixels." % (sizey, sizex)
  ncfile = netCDF4.Dataset(filename, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)
  run = ncfile.createVariable('run', np.int, ('Y', 'X',))

  if setpx != '':
    y, x = setpx.split(",")
    print " --> NOTE: Turning off all pixels except (y,x): %s,%s." % (y, x)
    run[:] = np.zeros((sizey, sizex))
    run[y,x] = 1
    
  if match2veg:
    guess_vegfile = os.path.join(os.path.split(filename)[0], 'vegetation.nc')
    print "--> NOTE: Attempting to read: {:}".format(guess_vegfile)
    print "          and set runmask true where veg_class > 0."

    with netCDF4.Dataset(guess_vegfile ,'r') as vegFile:
      vd = vegFile.variables['veg_class'][:]

    run[:] = np.where(vd>0, 1, 0)


  ncfile.source = source_attr_string()
  ncfile.close()


def make_co2_file(filename):
  '''Generates a co2 file for dvmdostem from the old sample data'''

  print "Creating a co2 file..."
  new_ncfile = netCDF4.Dataset(filename, mode='w', format='NETCDF4')

  # Dimensions
  yearD = new_ncfile.createDimension('year', None) # append along time axis
    
  # Coordinate Variable
  yearV = new_ncfile.createVariable('year', np.int, ('year',))
    
  # Data Variables
  co2 = new_ncfile.createVariable('co2', np.float32, ('year',))


  print " --> NOTE: Hard-coding the values that were just ncdumped from the old file..."
  print " --> NOTE: Adding new values for 2010-2017. Using data from here:"
  print "           https://www.esrl.noaa.gov/gmd/ccgg/trends/data.html"
  print "           direct ftp link:"
  print "           ftp://aftp.cmdl.noaa.gov/products/trends/co2/co2_annmean_mlo.txt"
  co2[:] = [ 296.311, 296.661, 297.04, 297.441, 297.86, 298.29, 298.726, 299.163,
    299.595, 300.016, 300.421, 300.804, 301.162, 301.501, 301.829, 302.154, 
    302.48, 302.808, 303.142, 303.482, 303.833, 304.195, 304.573, 304.966, 
    305.378, 305.806, 306.247, 306.698, 307.154, 307.614, 308.074, 308.531, 
    308.979, 309.401, 309.781, 310.107, 310.369, 310.559, 310.667, 310.697, 
    310.664, 310.594, 310.51, 310.438, 310.401, 310.41, 310.475, 310.605, 
    310.807, 311.077, 311.41, 311.802, 312.245, 312.736, 313.27, 313.842, 
    314.448, 315.084, 315.665, 316.535, 317.195, 317.885, 318.495, 318.935, 
    319.58, 320.895, 321.56, 322.34, 323.7, 324.835, 325.555, 326.55, 
    328.455, 329.215, 330.165, 331.215, 332.79, 334.44, 335.78, 337.655, 
    338.925, 340.065, 341.79, 343.33, 344.67, 346.075, 347.845, 350.055, 
    351.52, 352.785, 354.21, 355.225, 356.055, 357.55, 359.62, 361.69, 
    363.76, 365.83, 367.9, 368, 370.1, 372.2, 373.6943, 375.3507, 377.0071, 
    378.6636, 380.5236, 382.3536, 384.1336, 389.90, 391.65, 393.85, 396.52,
    398.65, 400.83, 404.24, 406.55 ]

  yearV[:] = [ 1901, 1902, 1903, 1904, 1905, 1906, 1907, 1908, 1909, 1910, 1911,
    1912, 1913, 1914, 1915, 1916, 1917, 1918, 1919, 1920, 1921, 1922, 1923, 
    1924, 1925, 1926, 1927, 1928, 1929, 1930, 1931, 1932, 1933, 1934, 1935, 
    1936, 1937, 1938, 1939, 1940, 1941, 1942, 1943, 1944, 1945, 1946, 1947, 
    1948, 1949, 1950, 1951, 1952, 1953, 1954, 1955, 1956, 1957, 1958, 1959, 
    1960, 1961, 1962, 1963, 1964, 1965, 1966, 1967, 1968, 1969, 1970, 1971, 
    1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980, 1981, 1982, 1983, 
    1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994, 1995, 
    1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 
    2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017 ]

  new_ncfile.source = source_attr_string()
  new_ncfile.close()

def create_template_topo_file(fname, sizey=10, sizex=10):
  '''Generate a template file for drainage classification.'''
  print "Creating an empty topography  file, %s by %s pixels. (%s)" % (sizey, sizex, os.path.basename(fname))
  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)

  # Spatial Ref. variables
  lat = ncfile.createVariable('lat', np.float32, ('Y', 'X',))
  lon = ncfile.createVariable('lon', np.float32, ('Y', 'X',))

  slope = ncfile.createVariable('slope', np.double, ('Y', 'X',))
  aspect = ncfile.createVariable('aspect', np.double, ('Y', 'X',))
  elevation = ncfile.createVariable('elevation', np.double, ('Y', 'X',))

  ncfile.source = source_attr_string()
  ncfile.close()


def create_template_drainage_file(fname, sizey=10, sizex=10):
  '''Generate a template file for drainage classification.'''
  print "Creating an empty drainage classification file, %s by %s pixels. (%s)" % (sizey, sizex, os.path.basename(fname))
  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)

  # Spatial Ref. variables
  lat = ncfile.createVariable('lat', np.float32, ('Y', 'X',))
  lon = ncfile.createVariable('lon', np.float32, ('Y', 'X',))

  drainage_class = ncfile.createVariable('drainage_class', np.int, ('Y', 'X',))

  ncfile.source = source_attr_string()
  ncfile.close()


def create_template_restart_nc_file(filename, sizex=10, sizey=10):
  '''Creates an empty restart file that can be used as a template?'''
  print "Creating an empty restart file: ", filename
  ncfile = netCDF4.Dataset(filename, mode='w', format='NETCDF4')

  print textwrap.dedent('''\
  %%%%%   NOTE   %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  Please note, this functionality may no longer be necessary, as functions have
  been added to the dvmdostem model that will allow it to create its own empty 
  restart files.
  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  ''')

  # Dimensions for the file.
  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)

  pft        = ncfile.createDimension('pft', 10)
  pftpart    = ncfile.createDimension('pftpart', 3)
  snowlayer  = ncfile.createDimension('snowlayer', 6)
  rootlayer  = ncfile.createDimension('rootlayer', 10)
  soillayer  = ncfile.createDimension('soillayer', 23)
  rocklayer  = ncfile.createDimension('rocklayer', 5)
  fronts     = ncfile.createDimension('fronts', 10)
  prevten    = ncfile.createDimension('prevten', 10)
  prevtwelve = ncfile.createDimension('prevtwelve', 12)

  # Create variables...
  for v in ['dsr', 'numsnwl', 'numsl', 'rtfrozendays', 'rtunfrozendays', 'yrsdist']:
    ncfile.createVariable(v, np.int, ('Y', 'X'))

  for v in ['firea2sorgn', 'snwextramass', 'monthsfrozen', 'watertab', 'wdebrisc', 'wdebrisn', 'dmossc', 'dmossn']:
    ncfile.createVariable(v, np.double, ('Y', 'X'))

  for v in ['ifwoody', 'ifdeciwoody', 'ifperenial', 'nonvascular', 'vegage']:
    ncfile.createVariable(v, np.int, ('Y','X','pft'))

  for v in ['vegcov', 'lai', 'vegwater', 'vegsnow', 'labn', 'deadc', 'deadn', 'topt', 'eetmx', 'unnormleafmx', 'growingttime', 'foliagemx']:
    ncfile.createVariable(v, np.double, ('Y','X','pft'))

  for v in ['vegc', 'strn']:
    ncfile.createVariable(v, np.double, ('Y','X','pftpart', 'pft'))

  for v in ['TEXTUREsoil', 'FROZENsoil', 'TYPEsoil', 'AGEsoil',]:
    ncfile.createVariable(v, np.int, ('Y','X','soillayer'))

  for v in ['TSsoil', 'DZsoil', 'LIQsoil', 'ICEsoil', 'FROZENFRACsoil', 'rawc', 'soma', 'sompr', 'somcr', 'orgn', 'avln']:
    ncfile.createVariable(v, np.double, ('Y','X','soillayer'))

  for v in ['TSsnow', 'DZsnow', 'LIQsnow', 'RHOsnow', 'ICEsnow', 'AGEsnow']:
    ncfile.createVariable(v, np.double, ('Y','X','soillayer'))

  for v in ['TSrock', 'DZrock']:
    ncfile.createVariable(v, np.double, ('Y','X', 'rocklayer'))


  ncfile.createVariable('frontFT', np.int, ('Y','X', 'fronts'))
  ncfile.createVariable('frontZ', np.double, ('Y','X', 'fronts'))

  ncfile.createVariable('rootfrac', np.double, ('Y','X','rootlayer','pft'))

  for v in ['toptA','eetmxA','unnormleafmxA','growingttimeA']:
    ncfile.createVariable(v, np.double, ('Y','X','prevten','pft'))

  for v in ['prvltrfcnA']:
    ncfile.createVariable(v, np.double, ('Y','X','prevtwelve','pft'))

  ncfile.source = source_attr_string()
  ncfile.close()

def create_template_climate_nc_file(filename, sizey=10, sizex=10):
  '''Creates an empty climate file for dvmdostem; y,x grid, time unlimited.'''

  print "Creating an empty climate file..."
  ncfile = netCDF4.Dataset(filename, mode="w", format='NETCDF4')

  # Dimensions for the file.
  time_dim = ncfile.createDimension('time', None) # append along time axis
  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)

  # Coordinate Variables
  Y = ncfile.createVariable('Y', np.int, ('Y',))
  X = ncfile.createVariable('X', np.int, ('X',))
  Y[:] = np.arange(0, sizey)
  X[:] = np.arange(0, sizex)

  # 'Spatial Refefence' variables (?)
  lat = ncfile.createVariable('lat', np.float32, ('Y', 'X',))
  lon = ncfile.createVariable('lon', np.float32, ('Y', 'X',))

  # Create data variables
  #co2 = ncfile.createVariable('co2', np.float32, ('time')) # actually year
  temp_air = ncfile.createVariable('tair', np.float32, ('time', 'Y', 'X',))
  precip = ncfile.createVariable('precip', np.float32, ('time', 'Y', 'X',))
  nirr = ncfile.createVariable('nirr', np.float32, ('time', 'Y', 'X',))
  vapor_press = ncfile.createVariable('vapor_press', np.float32, ('time', 'Y', 'X',))

  ncfile.source = source_attr_string()
  ncfile.close()


def create_template_fri_fire_file(fname, sizey=10, sizex=10, rand=None):
  print "Creating an FRI fire file, %s by %s pixels. Fill with random data?: %s" % (sizey, sizex, rand)
  print "Opening/Creating file: ", fname

  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)

  # Do we need time dimension??

  # Spatial Ref. variables
  lat = ncfile.createVariable('lat', np.float32, ('Y', 'X',))
  lon = ncfile.createVariable('lon', np.float32, ('Y', 'X',))

  fri = ncfile.createVariable('fri', np.int32, ('Y','X',))
  sev = ncfile.createVariable('fri_severity', np.int32, ('Y','X'))
  dob = ncfile.createVariable('fri_jday_of_burn', np.int32, ('Y','X'))
  aob = ncfile.createVariable('fri_area_of_burn', np.int32, ('Y','X'))

  if rand:
    print "Fill FRI fire file with random data NOT IMPLEMENTED YET! See fill function."

  ncfile.source = source_attr_string()
  ncfile.close()


def create_template_explicit_fire_file(fname, sizey=10, sizex=10, rand=None):
  print "Creating a fire file, %s by %s pixels. Fill with random data?: %s" % (sizey, sizex, rand)
  print "Opening/Creating file: ", fname

  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)
  time = ncfile.createDimension('time', None)

  # Spatial Ref. variables
  lat = ncfile.createVariable('lat', np.float32, ('Y', 'X',))
  lon = ncfile.createVariable('lon', np.float32, ('Y', 'X',))

  exp_bm = ncfile.createVariable('exp_burn_mask', np.int32, ('time', 'Y', 'X',))
  exp_dob = ncfile.createVariable('exp_jday_of_burn', np.int32, ('time', 'Y', 'X',))
  exp_sev = ncfile.createVariable('exp_fire_severity', np.int32, ('time', 'Y','X'))
  exp_aob = ncfile.createVariable('exp_area_of_burn', np.int32, ('time', 'Y','X'))

  if rand:
    print "Fill EXPLICIT fire file with random data NOT IMPLEMENTED HERE! See fill function."

  ncfile.source = source_attr_string()
  ncfile.close()


def create_template_veg_nc_file(fname, sizey=10, sizex=10, rand=None):
  print "Creating a vegetation classification file, %s by %s pixels. Fill with random data?: %s" % (sizey, sizex, rand)

  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)

  # Spatial Ref. variables
  lat = ncfile.createVariable('lat', np.float32, ('Y', 'X',))
  lon = ncfile.createVariable('lon', np.float32, ('Y', 'X',))

  veg_class = ncfile.createVariable('veg_class', np.int, ('Y', 'X',))

  if (rand):
    print " --> NOTE: Filling with random data!"
    veg_class[:] = np.random.uniform(low=1, high=7, size=(sizey,sizex))

  ncfile.source = source_attr_string()
  ncfile.close()

def create_template_soil_texture_nc_file(fname, sizey=10, sizex=10):
  print "Creating a soil texture classification file, %s by %s pixels." % (sizey, sizex)

  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)

  # Spatial Ref. variables
  lat = ncfile.createVariable('lat', np.float32, ('Y', 'X',))
  lon = ncfile.createVariable('lon', np.float32, ('Y', 'X',))

  pct_sand = ncfile.createVariable('pct_sand', np.float32, ('Y','X'))
  pct_silt = ncfile.createVariable('pct_silt', np.float32, ('Y','X'))
  pct_clay = ncfile.createVariable('pct_clay', np.float32, ('Y','X'))

  ncfile.source = source_attr_string()
  ncfile.close()


def convert_and_subset(in_file, master_output, xo, yo, xs, ys, yridx, midx, variablename):
  '''
  Convert a .tif to .nc file and subset it using pixel offsets.

  This is indended to be called as a independant multiprocessing.Process.

  Parameters
  ----------
  in_file : str (path)
    The tif file (from SNAP) with data in it
  master_output : str (path)
    The (per variable) master file that should get appended to.
  xo, yo : int
    The X and Y pixel offsets (lower left corner?)
  xs, ys : int
    The X and Y sizes (in pixels)
  yridx : int
    The year index for this in_file.
  midx : int
    The month index for this in_file
  variablename : str
    The variable we are working on. I.e. tair, precip, etc.

  Returns
  -------
  None
  '''
  cpn = mp.current_process().name

  tmpfile1 = '/tmp/script-temporary_%s.nc' % variablename
  tmpfile2 = '/tmp/script-temporary_%s-2.nc' % variablename

  print "{:}: infile: {} master_output: {} vname: {}".format(
      cpn, in_file, master_output, variablename)

  print "{:}: Converting tif --> netcdf...".format(cpn)
  check_call(['gdal_translate', '-of', 'netCDF', in_file, tmpfile1])

  print "{:}: Subsetting...".format(cpn)
  check_call(['gdal_translate', '-of', 'netCDF',
              '-srcwin', str(xo), str(yo), str(xs), str(ys),
              tmpfile1, tmpfile2])

  print "{:}: Writing subset's data to new file...".format(cpn)

  new_climatedataset = netCDF4.Dataset(master_output, mode='a')
  t2 = netCDF4.Dataset(tmpfile2, mode='r')

  theVariable = new_climatedataset.variables[variablename]
  theVariable[yridx*12+midx] = t2.variables['Band1'][:]

  new_climatedataset.close()
  t2.close()

  print "{:}: Done appending.".format(cpn)

def fill_topo_file(inSlope, inAspect, inElev, xo, yo, xs, ys, out_dir, of_name):
  '''Read subset of data from various tifs into single netcdf file for dvmdostem'''

  create_template_topo_file(of_name, sizey=ys, sizex=xs)

  # get a string for use as a file handle for each input file
  tmpSlope = '/tmp/cri-{:}'.format(os.path.basename(inSlope))
  tmpAspect = '/tmp/cri-{:}'.format(os.path.basename(inAspect))
  tmpElev = '/tmp/cri-{:}'.format(os.path.basename(inElev))

  for inFile, tmpFile in zip([inSlope, inAspect, inElev], [tmpSlope, tmpAspect, tmpElev]):
    subprocess.call(['gdal_translate', '-of', 'netcdf',
                     '-co', 'WRITE_LONLAT=YES',
                      '-srcwin', str(xo), str(yo), str(xs), str(ys),
                      inFile, tmpFile])

  with netCDF4.Dataset(of_name, mode='a') as new_topodataset:
    for ncvar, tmpFileName in zip(['slope','aspect','elevation'],[tmpSlope,tmpAspect,tmpElev]):
      with netCDF4.Dataset(tmpFileName, 'r') as TF:
        V = new_topodataset.variables[ncvar]
        V[:] = TF.variables['Band1'][:]

  with netCDF4.Dataset(of_name, mode='a') as new_topodataset:
    with netCDF4.Dataset(tmpSlope, 'r') as TF:
        new_topodataset.variables['lat'][:] = TF.variables['lat'][:]
        new_topodataset.variables['lon'][:] = TF.variables['lon'][:]

from contextlib import contextmanager

@contextmanager
def custom_netcdf_attr_bug_wrapper(ncid):
  # Maybe a bug? https://github.com/Unidata/netcdf4-python/issues/110
  ncid.setncattr('junkattr', 'somejunk')
  yield ncid
  del ncid.junkattr

def fill_veg_file(if_name, xo, yo, xs, ys, out_dir, of_name):
  '''Read subset of data from .tif into netcdf file for dvmdostem. '''

  of_stripped = os.path.basename(of_name)

  # Create place for data
  create_template_veg_nc_file(of_name, sizey=ys, sizex=xs, rand=None)

  # Translate and subset to temporary location
  temporary = os.path.join('/tmp', of_stripped)

  if not os.path.exists( os.path.dirname(temporary) ):
    os.makedirs(os.path.dirname(temporary))

  subprocess.call(['gdal_translate', '-of', 'netcdf',
                   '-co', 'WRITE_LONLAT=YES',
                   '-srcwin', str(xo), str(yo), str(xs), str(ys),
                   if_name, temporary])

  # Copy from temporary location to into the placeholder file we just created
  with netCDF4.Dataset(temporary) as t1, netCDF4.Dataset(of_name, mode='a') as new_vegdataset:
    veg_class = new_vegdataset.variables['veg_class']
    lat = new_vegdataset.variables['lat']
    lon = new_vegdataset.variables['lon']

    with custom_netcdf_attr_bug_wrapper(new_vegdataset) as f:
      f.source = source_attr_string(xo=xo, yo=yo)

    veg_class[:] = t1.variables['Band1'][:].data 
    lat[:] = t1.variables['lat'][:]
    lon[:] = t1.variables['lon'][:]
    # For some reason, some rows of the temporary file are numpy masked arrays
    # and if we don't directly access the data, then we get strange results '
    # (i.e. stuff that should be ocean shows up as CMT02??)
    # If we use the .data method, then the ocean ends up filled with '-1' and 
    # lakes end up as CMT00, which is what we want. Alternatively, could use the
    # .filled(-1) method.


def fill_climate_file(start_yr, yrs, xo, yo, xs, ys,
                      out_dir, of_name, sp_ref_file,
                      in_tair_base, in_prec_base, in_rsds_base, in_vapo_base,
                      time_coord_var, model='', scen='', cleanup_tmpfiles=True):

  # create short handle for output file
  masterOutFile = os.path.join(out_dir, of_name)

  dataVarList = ['tair', 'precip', 'nirr', 'vapor_press']

  # Create empty file with all the correct dimensions. At the end data will
  # be copied into this file.
  create_template_climate_nc_file(masterOutFile, sizey=ys, sizex=xs)

  # Start with setting up the spatial info (copying from input file)
  # Best do to this before the data so that we can catch bugs before waiting 
  # for all the data to copy.
  tmpfile = '/tmp/temporary-file-with-spatial-info.nc'
  smaller_tmpfile = '/tmp/smaller-temporary-file-with-spatial-info.nc'
  print "Creating a temporary file with LAT and LON variables: ", tmpfile
  print "------------------------"
  print type(sp_ref_file), type(tmpfile)
  print sp_ref_file, tmpfile
  print "------------------------"
  if type(sp_ref_file) == tuple:
    sp_ref_file = sp_ref_file[0]
  elif type(sp_ref_file) == str:
    pass # nothing to do...

  check_call([
      'gdal_translate', '-of', 'netCDF', '-co', 'WRITE_LONLAT=YES',
      sp_ref_file,
      tmpfile
    ])
  print "Finished creating temporary file with spatial info."

  print "Make a subset of the temporary file with LAT and LON variables: ", smaller_tmpfile
  check_call(['gdal_translate', '-of', 'netCDF',
      '-co', 'WRITE_LONLAT=YES',
      '-srcwin', str(xo), str(yo), str(xs), str(ys),
      'NETCDF:"{}":Band1'.format(tmpfile), smaller_tmpfile
    ])
  print "Finished creating the temporary subset...(cropping to our domain)"

  print "Copy the LAT/LON variables from the temporary file into our new dataset..."
  # Open the temporary dataset
  temp_subset_with_lonlat = netCDF4.Dataset(smaller_tmpfile, mode='r')

  # Open the new file for appending
  new_climatedataset = netCDF4.Dataset(masterOutFile, mode='a')

  # Insert lat/lon from temp file into the new file
  lat = new_climatedataset.variables['lat']
  lon = new_climatedataset.variables['lon']
  lat[:] = temp_subset_with_lonlat.variables['lat'][:]
  lon[:] = temp_subset_with_lonlat.variables['lon'][:]
  print "Done copying LON/LAT."

  with custom_netcdf_attr_bug_wrapper(new_climatedataset) as f:

    print "Write attribute with pixel offsets to file..."
    f.source = source_attr_string(xo=xo, yo=yo)

    print "Write attributes for model and scenario..."
    f.model = model
    f.scenario = scen

    print "Write attributes for each variable"
    f.variables['lat'].standard_name = 'latitude'
    f.variables['lat'].units = 'degree_north'

    f.variables['lon'].standard_name = 'longitude'
    f.variables['lon'].units = 'degree_east'

    print "Double check that we picked the right CF name for nirr!"
    f.variables['nirr'].standard_name = 'downwelling_shortwave_flux_in_air'
    f.variables['nirr'].units = 'W m-2'

    f.variables['precip'].standard_name = 'precipitation_amount'
    f.variables['precip'].units = 'mm month-1'

    f.variables['tair'].standard_name = 'air_temperature'
    f.variables['tair'].units = 'celsius'

    f.variables['vapor_press'].standard_name = 'water_vapor_pressure'
    f.variables['vapor_press'].units = 'hPa'


  print "Closing new dataset and temporary file."
  print "masterOutFile time dimension size: {}".format(new_climatedataset.dimensions['time'].size)
  new_climatedataset.close()
  temp_subset_with_lonlat.close()

  if cleanup_tmpfiles:
    print "Cleaning up temporary files: {} and {}".format(tmpfile, smaller_tmpfile)
    os.remove(smaller_tmpfile)
    os.remove(tmpfile)


  # Copy the master into a separate file for each variable
  for v in dataVarList:
    shutil.copyfile(masterOutFile, os.path.join(out_dir, 'TEMP-{}-{}'.format(v, of_name)))

  # Now we have to loop over all the .tif files - there is one file for each
  # month of each year for each variable - and extract the data so we can
  # save it in our new NetCDF file.
  print "Working to prepare climate data for years %s to %s" % (start_yr, start_yr + yrs)
  for yridx, year in enumerate(range(start_yr, start_yr + yrs)):

    for midx, month in enumerate(range(1,13)): # Note 1 based month!

      print year, month

      basePathList = [in_tair_base, in_prec_base, in_rsds_base, in_vapo_base]
      baseFiles = [basePath + "{:02d}_{:04d}.tif".format(month, year) for basePath in basePathList]
      tmpFiles = [os.path.join(out_dir, 'TEMP-{}-{}'.format(v, of_name)) for v in dataVarList]
      procs = []
      for tiffimage, tmpFileName, vName in zip(baseFiles, tmpFiles , dataVarList):
        proc = mp.Process(target=convert_and_subset, args=(tiffimage, tmpFileName, xo, yo, xs, ys, yridx, midx, vName))
        procs.append(proc)
        proc.start()

      for proc in procs:
        proc.join()

  print "Done with year loop."

  with netCDF4.Dataset(masterOutFile, 'r') as ds:
    print "===> masterOutFile.dimensions: {}".format(ds.dimensions)

  print "Copy data from temporary per-variable files into master"
  tmpFiles = [os.path.join(out_dir, 'TEMP-{}-{}'.format(v, of_name)) for v in dataVarList]
  for tFile, var in zip(tmpFiles, dataVarList):
    # Need to make a list of variables to exclude from the
    # ncks append operation (all except the current variable)
    masked_list = [i for i in dataVarList if var not in i]

    opt_str = "lat,lon," + ",".join(masked_list)
    check_call(['ncks', '--append', '-x','-v', opt_str, tFile, masterOutFile])

    os.remove(tFile)

    # This fails. Looks to me like a bug in nco as it expand the option string
    # import nco as NCO
    #nco = NCO.Nco()
    #opt_str = "--append -x -v lat,lon," + ",".join(masked_list)
    #nco.ncks(input=tFile, output=masterOutFile, options=opt_str)
    ''' Error from console:
    Copy data from temporary per-variable files into master /tmp/smaller-temporary-file-with-spatial-info.nc
    Error in calling operator ncks with:
    >>> /usr/local/bin/ncks - - a p p e n d - x - v p r e c i p , n i r r , v a p o r _ p r e s s --overwrite --output=some-dvmdostem-inputs/SouthBarrow_10x10/historic-climate.nc some-dvmdostem-inputs/SouthBarrow_10x10/TEMP-tair-historic-climate.nc <<<
    Inputs: some-dvmdostem-inputs/SouthBarrow_10x10/TEMP-tair-historic-climate.nc
    '''

  with netCDF4.Dataset(masterOutFile, mode='a') as new_climatedataset:

    print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
    print "%% NOTE! Converting rsds (nirr) from MJ/m^2/day to W/m^2!"
    print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"

    nirr = new_climatedataset.variables['nirr']
    nirr[:] = (1000000 / (60*60*24)) * nirr[:]

    if time_coord_var:
      print "Write time coordinate variable attribute for time axis..."
      with custom_netcdf_attr_bug_wrapper(new_climatedataset) as f:
        tcV = f.createVariable("time", np.double, ('time'))
        tcV.setncatts({
          'long_name': 'time',
          'units': 'days since {}-1-1 0:0:0'.format(start_yr),
          'calendar': '365_day'
        })

        # Build up a vector of datetime stamps for the first day of each month
        try:
          num_months = f.dimensions['time'].size # only available in netCDF4 >1.2.2
        except AttributeError as e:
          num_months = len(f.dimensions['time'])

        # Gives an array of numpy datetime64 objects, which are monthly resolution
        assert start_yr+num_months/12 == start_yr+yrs, "Date/time indexing bug!"
        month_starts = np.arange('{}-01-01'.format(start_yr), '{}-01-01'.format(start_yr+yrs), dtype='datetime64[M]')

        print "length of month_starts array: {}".format(len(month_starts))

        # Using .tolist() to convert from numpy.datetime64 objects to python
        # standard library datetime.datetime objects only works for some 
        # of the available numpy.datetime units options! See here:
        # https://stackoverflow.com/questions/46921593#46921593
        assert month_starts[0].dtype == np.dtype('<M8[M]'), "Invalid type!"

        # Convert to python datetime.date objects
        month_starts_dateobjs = month_starts.tolist() 

        # Convert to python datetime.datetime objects with time set at 0
        month_starts_datetimeobjs = [dt.datetime.combine(i, dt.time()) for i in month_starts_dateobjs]
        print "length of month_starts_datetimeobjs: {}".format(len(month_starts_datetimeobjs))

        # Convert to numeric offset using netCDF utility function, the units,
        # and calendar.
        tcV_vals = netCDF4.date2num(month_starts_datetimeobjs, 
            units="days since {}-01-01".format(start_yr),
            calendar="365_day"
        )

        # Set the values for the time coordinate variable, using the
        # values from the helper function that computed the proper offsets
        tcV[:] = tcV_vals



def fill_soil_texture_file(if_sand_name, if_silt_name, if_clay_name, xo, yo, xs, ys, out_dir, of_name, rand=True):
  
  create_template_soil_texture_nc_file(of_name, sizey=ys, sizex=xs)

  with netCDF4.Dataset(of_name, mode='a') as soil_tex:
    p_sand = soil_tex.variables['pct_sand']
    p_silt = soil_tex.variables['pct_silt']
    p_clay = soil_tex.variables['pct_clay']
    
    if (rand):
      print "Filling file with random data."
      psand = np.random.uniform(low=0, high=100, size=(ys,xs))
      psilt = np.random.uniform(low=0, high=100, size=(ys,xs))
      pclay = np.random.uniform(low=0, high=100, size=(ys,xs))

      bigsum = psand + psilt + pclay

      p_sand[:] = np.round(psand/bigsum*100)
      p_silt[:] = np.round(psilt/bigsum*100)
      p_clay[:] = np.round(pclay/bigsum*100)

      print "WARNING: the random data is not perfect - due to rounding error, adding the percent sand/silt/clay does not always sum to exactly 100"

    else:
      print "Filling with real data..."

      print "Subsetting TIF to netCDF"
      subprocess.check_call(['gdal_translate','-of','netCDF',
                             '-co', 'WRITE_LONLAT=YES',
                             '-srcwin', str(xo), str(yo), str(xs), str(ys),
                             if_sand_name,
                             '/tmp/create_region_input_script_sand_texture.nc'])

      subprocess.check_call(['gdal_translate','-of','netCDF',
                             '-co', 'WRITE_LONLAT=YES',
                             '-srcwin', str(xo), str(yo), str(xs), str(ys),
                             if_silt_name,
                             '/tmp/create_region_input_script_silt_texture.nc'])

      subprocess.check_call(['gdal_translate','-of','netCDF',
                             '-co', 'WRITE_LONLAT=YES',
                             '-srcwin', str(xo), str(yo), str(xs), str(ys),
                             if_clay_name,
                             '/tmp/create_region_input_script_clay_texture.nc'])

      print "Writing subset's data to new files..."
      with netCDF4.Dataset('/tmp/create_region_input_script_sand_texture.nc', mode='r') as f:
        p_sand[:] = f.variables['Band1'][:]
      with netCDF4.Dataset('/tmp/create_region_input_script_silt_texture.nc', mode='r') as f:
        p_silt[:] = f.variables['Band1'][:]
      with netCDF4.Dataset('/tmp/create_region_input_script_clay_texture.nc', mode='r') as f:
        p_clay[:] = f.variables['Band1'][:]

    # While we went to the trouble of writing lat/lon to all the temporary
    # files, we are only going to use one of those files to get the 
    # data into the final file...

    with netCDF4.Dataset('/tmp/create_region_input_script_sand_texture.nc', mode='r') as f:
      soil_tex.variables['lat'][:] = f.variables['lat'][:]
      soil_tex.variables['lon'][:] = f.variables['lon'][:]

    with custom_netcdf_attr_bug_wrapper(soil_tex) as f:
      f.source =  source_attr_string(xo=xo, yo=yo)


def fill_drainage_file(if_name, xo, yo, xs, ys, out_dir, of_name, rand=False):
  create_template_drainage_file(of_name, sizey=ys, sizex=xs)

  with netCDF4.Dataset(of_name, mode='a') as drainage_class:

    '''Fill drainage template file'''
    if rand:
      print " --> NOTE: Filling with random data!"
      drain = drainage_class.variables['drainage_class']
      drain[:] = np.random.randint(low=0, high=2, size=(ys, xs))

      #Hard-coding a Toolik value to try and stabilize plots
      print " --> NOTE: Setting 0,0 pixel to 1! (poorly drained?)"
      drain[0,0] = 1

    else:
      print "Filling with real data"

      print "Subsetting TIF to netCDF..."
      check_call(['gdal_translate', '-of', 'netCDF',
                  '-co', 'WRITE_LONLAT=YES',
                  '-srcwin', str(xo), str(yo), str(xs), str(ys),
                  if_name,
                  '/tmp/script-temp_drainage_subset.nc'])

      with netCDF4.Dataset('/tmp/script-temp_drainage_subset.nc', mode='r') as temp_drainage:
        drain = drainage_class.variables['drainage_class']

        print "Thresholding: set data <= 200 to 0; set data > 200 to 1."
        data = temp_drainage.variables['Band1'][:]
        data[data <= 200] = 0
        data[data > 200] = 1

        print "Writing subset data to new file"
        drain[:] = data

        print "Writing lat/lon data to new file..."
        drainage_class.variables['lat'][:] = temp_drainage.variables['lat'][:]
        drainage_class.variables['lon'][:] = temp_drainage.variables['lon'][:]

    with custom_netcdf_attr_bug_wrapper(drainage_class) as f:
      f.source = source_attr_string(xo=xo, yo=yo)

def fill_fri_fire_file(xo, yo, xs, ys, out_dir, of_name, datasrc='', if_name=None):
  '''
  Parameters:
  -----------
  datasrc : str describing how and where to get the numbers used to fill the file
    'random' will create files filled with random data
    'no-fires' will create files such that no fires occur
    'genet-greaves' will create files using H.Genet's and H.Greaves process   
  '''

  create_template_fri_fire_file(of_name, sizey=ys, sizex=xs, rand=False)

  if datasrc == 'random':
    print "%%%%%%  WARNING  %%%%%%%%%%%%%%%%%"
    print "GENERATING FAKE DATA!"
    print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
    cmt2fireprops = {
      -1: {'fri':   -1, 'sev': -1, 'jdob':  -1, 'aob':  -1 }, # No data?
      0: {'fri':   -1, 'sev': -1, 'jdob':  -1, 'aob':  -1 }, # rock/snow/water
      1: {'fri':  100, 'sev':  3, 'jdob': 165, 'aob': 100 }, # black spruce
      2: {'fri':  105, 'sev':  2, 'jdob': 175, 'aob': 225 }, # white spruce
      3: {'fri':  400, 'sev':  3, 'jdob': 194, 'aob': 104 }, # boreal deciduous
      4: {'fri': 2000, 'sev':  2, 'jdob': 200, 'aob': 350 }, # shrub tundra
      5: {'fri': 2222, 'sev':  3, 'jdob': 187, 'aob': 210 }, # tussock tundra
      6: {'fri': 1500, 'sev':  1, 'jdob': 203, 'aob': 130 }, # wet sedge tundra
      7: {'fri': 1225, 'sev':  4, 'jdob': 174, 'aob': 250 }, # heath tundra
      8: {'fri':  759, 'sev':  3, 'jdob': 182, 'aob': 156 }, # maritime forest
    }
    guess_vegfile = os.path.join(os.path.split(of_name)[0], 'vegetation.nc')
    print "--> NOTE: Attempting to read: {:} and set fire properties based on community type...".format(guess_vegfile)

    with netCDF4.Dataset(guess_vegfile ,'r') as vegFile:
      vd = vegFile.variables['veg_class'][:]
      fri = np.array([cmt2fireprops[i]['fri'] for i in vd.flatten()]).reshape(vd.shape)
      sev = np.array([cmt2fireprops[i]['sev'] for i in vd.flatten()]).reshape(vd.shape)
      jdob = np.array([cmt2fireprops[i]['jdob'] for i in vd.flatten()]).reshape(vd.shape)
      aob = np.array([cmt2fireprops[i]['aob'] for i in vd.flatten()]).reshape(vd.shape)

    with netCDF4.Dataset(of_name, mode='a') as nfd:
      print "==> write data to new FRI based fire file..."
      nfd.variables['fri'][:,:] = fri
      nfd.variables['fri_severity'][:,:] = sev
      nfd.variables['fri_jday_of_burn'][:,:] = jdob
      nfd.variables['fri_area_of_burn'][:,:] = aob

  elif datasrc == 'no-fires':
    print "%%%%%%  WARNING  %%%%%%%%%%%%%%%%%"
    print "GENERATING FRI FILE WITH NO FIRES!"
    print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"

    with netCDF4.Dataset(of_name, mode='a') as nfd:
      print "==> write zeros to FRI file..."
      zeros = np.zeros((ys,xs))
      nfd.variables['fri'][:,:] = zeros
      nfd.variables['fri_severity'][:,:] = zeros
      nfd.variables['fri_jday_of_burn'][:,:] = zeros
      nfd.variables['fri_area_of_burn'][:,:] = zeros

  elif datasrc == 'fri-from-file': # other variables fixed/hardcoded below
    if not os.path.exists(if_name):
      print "ERROR! Can't find file specified for FRI input!: {}".format(if_name) 
      
    # Translate and subset to temporary location
    temporary = os.path.join('/tmp/', os.path.basename(of_name))

    if not os.path.exists( os.path.dirname(temporary) ):
      os.makedirs(os.path.dirname(temporary))

    subprocess.call(['gdal_translate', '-of', 'netcdf',
                     '-co', 'WRITE_LONLAT=YES',
                     '-srcwin', str(xo), str(yo), str(xs), str(ys),
                     if_name, temporary])

    with netCDF4.Dataset(temporary, mode='r') as temp_fri, netCDF4.Dataset(of_name, mode='a') as new_fri:
      print "--> Copying data from temporary subset file into new file..."
      new_fri.variables['fri'][:] = temp_fri.variables['Band1'][:]
      new_fri.variables['fri_severity'][:] = 2
      new_fri.variables['fri_jday_of_burn'][:] = 156
      new_fri.variables['fri_jday_of_burn'].setncatts({
          'long_name': 'julian day of burn'
        })
      new_fri.variables['fri_area_of_burn'][:] = 4.06283e+08 # square meters
      new_fri.variables['fri_area_of_burn'].setncatts({
          'long_name': 'area of burn',
          'units': 'm2',
          'note': "mean area of fire scar computed from statewide fire records 1950 to 1980"
        })

  else:
    print "ERROR! Unrecognized value for 'datasrc' in function fill_fri_file(..)"
     

  # Now that primary data has been written, take care of some generic 
  # stuff: lat, lon, atrributes, etc.
  guess_vegfile = os.path.join(os.path.split(of_name)[0], 'vegetation.nc')
  print "--> NOTE: Attempting to read: {:} to get lat/lon info".format(guess_vegfile)

  with netCDF4.Dataset(guess_vegfile ,'r') as vegFile:
    latv = vegFile.variables['lat'][:]
    lonv = vegFile.variables['lon'][:]


  with netCDF4.Dataset(of_name, mode='a') as nfd:
    print "Writing lat/lon from veg file..."
    nfd.variables['lat'][:] = latv
    nfd.variables['lon'][:] = lonv

    with custom_netcdf_attr_bug_wrapper(nfd) as f:
      print "==> write global :source attribute to FRI fire file..."
      f.source = source_attr_string(xo=xo, yo=yo)






def fill_explicit_fire_file(yrs, xo, yo, xs, ys, out_dir, of_name, datasrc='', if_name=None):

  create_template_explicit_fire_file(of_name, sizey=ys, sizex=xs, rand=False)

  if datasrc =='no-fires':
    print "%%%%%%  WARNING  %%%%%%%%%%%%%%%%%%%%%%%%%%%"
    print "GENERATING EXPLICIT FIRE FILE WITH NO FIRES!"
    print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"

    with netCDF4.Dataset(of_name, mode='a') as nfd:

        zeros = np.zeros((yrs,ys,xs))
        nfd.variables['exp_burn_mask'][:] = zeros
        nfd.variables['exp_jday_of_burn'][:] = zeros
        nfd.variables['exp_fire_severity'][:] = zeros
        nfd.variables['exp_area_of_burn'][:] = zeros

  elif datasrc == 'random':

    print "%%%%%%  WARNING  %%%%%%%%%%%%%%%%%"
    print "GENERATING FAKE DATA!"
    print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"

    never_burn = ([9],[9])
    print "--> Never burn pixels: {}".format(zip(*never_burn))

    with netCDF4.Dataset(of_name, mode='a') as nfd:

      for yr in range(0, yrs):

        # Future: lookup from snap/alfresco .tif files...

        # Generate indices a few random pixels to burn
        flat_burn_indices = np.random.randint(0, (ys*xs), (ys*xs)*0.3)
        burn_indices = np.unravel_index(flat_burn_indices, (ys,xs))

        #print burn_indices
        # Now set the other variables, but only for the burning pixels...
        exp_bm = np.zeros((ys,xs))
        exp_jdob = np.zeros((ys,xs))
        exp_sev = np.zeros((ys,xs))
        exp_aob = np.zeros((ys,xs))

        exp_bm[burn_indices] = 1
        exp_jdob[burn_indices] = np.random.randint(152, 244, len(flat_burn_indices))
        exp_sev[burn_indices] = np.random.randint(0, 5, len(flat_burn_indices))
        exp_aob[burn_indices] = np.random.randint(1, 20000, len(flat_burn_indices))

        # Make sure far corner pixel never burns:
        exp_bm[never_burn] = 0

        nfd.variables['exp_burn_mask'][yr,:,:] = exp_bm
        nfd.variables['exp_jday_of_burn'][yr,:,:] = exp_jdob
        nfd.variables['exp_fire_severity'][yr,:,:] = exp_sev
        nfd.variables['exp_area_of_burn'][yr,:,:] = exp_aob

      print "Done filling out fire years..."

  else:
    print "ERROR! Unrecognized value for 'datasrc' in function fill_explicit_file(..)"

  # Now that the primary data is taken care of, fill out all some other general 
  # info for the file, lat, lon, attributes, etc

  def figure_out_time_size(of_name, yrs):
    guess_hcf = os.path.join(os.path.split(of_name)[0], 'historic-climate.nc')
    guess_pcf = os.path.join(os.path.split(of_name)[0], 'projected-climate.nc')

    starting_date_str = ''
    with netCDF4.Dataset(guess_hcf, 'r') as ds:
      if ds.variables['time'].size / 12 == yrs:
        starting_date_str = (ds.variables['time'].units).replace('days', 'years')
        end_date = netCDF4.num2date(ds.variables['time'][-1], ds.variables['time'].units, ds.variables['time'].calendar)

    with netCDF4.Dataset(guess_pcf, 'r') as ds:
      if ds.variables['time'].size / 12 == yrs:
        starting_date_str = (ds.variables['time'].units).replace('days', 'years')
        end_date = netCDF4.num2date(ds.variables['time'][-1], ds.variables['time'].units, ds.variables['time'].calendar)

    # Convert from the funky netcdf time object to python datetime object
    end_date = dt.datetime.strptime(end_date.strftime(), "%Y-%m-%d %H:%M:%S")

    return starting_date_str, end_date 


  guess_starting_date_string, end_date = figure_out_time_size(of_name, yrs)

  with netCDF4.Dataset(of_name, mode='a') as nfd:
    print "Write time coordinate variable attribute for time axis..."
    with custom_netcdf_attr_bug_wrapper(nfd) as f:
      tcV = f.createVariable("time", np.double, ('time'))
      start_date = dt.datetime.strptime('T'.join(guess_starting_date_string.split(' ')[-2:]), '%Y-%m-%dT%H:%M:%S')
      tcV[:] = np.arange( 0, (end_date.year+1 - start_date.year) )
      tcV.setncatts({
        'long_name': 'time',
        'units': '{}'.format(guess_starting_date_string),
        'calendar': '365_day'
      })


  guess_vegfile = os.path.join(os.path.split(of_name)[0], 'vegetation.nc')
  print "--> NOTE: Attempting to read: {:} to get lat/lon info".format(guess_vegfile)

  with netCDF4.Dataset(of_name, mode='a') as nfd:

    print "Writing lat/lon from veg file..."
    with netCDF4.Dataset(guess_vegfile ,'r') as vegFile:
      nfd.variables['lat'][:] = vegFile.variables['lat'][:]
      nfd.variables['lon'][:] = vegFile.variables['lon'][:]

      print "Setting :source attribute on new explicit fire file..."
      with custom_netcdf_attr_bug_wrapper(nfd) as f:
        f.source = source_attr_string(xo=xo, yo=yo)


def verify_paths_in_config_dict(tif_dir, config):

  def pretty_print_test_path(test_path, k):
    if os.path.exists(test_path):
      print "key {} is OK!".format(k)
    else:
      print "ERROR! Can't find config path!! key:{} test_path: {}".format(k, test_path)

  for k, v in config.iteritems():

    if 'src' in k:

      if 'soil' in k:
        required_for = ['soil']
      if 'drainage' in k:
        required_for = ['drainage']
      if 'top' in k:
        required_for = ['topo']
      if 'veg' in k:
        required_for = ['vegetation']

      # Check the climate stuff
      if 'clim' in k:
        if 'h clim' in k:
          required_for = ['historic-climate']
          fy = config['h clim first yr']
        elif 'p clim' in k:
          required_for = ['projected-climate']
          fy = config['p clim first yr']
        else:
          pass #??

        test_path = os.path.join(tif_dir,"{}01_{}.tif".format(v, fy))
        pretty_print_test_path(test_path, k)

      # Check the fire stuff
      elif 'fire fri' in k:
        test_path = os.path.join(tif_dir, v)
        pretty_print_test_path(test_path, k)

      # Check all the other src files...
      else:
        test_path = os.path.join(tif_dir, v)
        pretty_print_test_path(test_path, k)


def main(start_year, years, xo, yo, xs, ys, tif_dir, out_dir, 
         files=[], config={}, time_coord_var=False, clip_projected2match_historic=False):

  #
  # Make the veg file first, then run-mask, then climate, then fire.
  #
  # The fire files require the presence of the veg map, and climate!
  #
  if 'vegetation' in files:
    of_name = os.path.join(out_dir, "vegetation.nc")
    #fill_veg_file(os.path.join(tif_dir,  "ancillary/land_cover/v_0_4/iem_vegetation_model_input_v0_4.tif"), xo, yo, xs, ys, out_dir, of_name)
    fill_veg_file(os.path.join(tif_dir, config['veg src']), xo, yo, xs, ys, out_dir, of_name)

  if 'drainage' in files:
    of_name = os.path.join(out_dir, "drainage.nc")
    fill_drainage_file(os.path.join(tif_dir,  config['drainage src']), xo, yo, xs, ys, out_dir, of_name)

  if 'soil-texture' in files:
    of_name = os.path.join(out_dir, "soil-texture.nc")

    in_clay_base = os.path.join(tif_dir, config['soil clay src'])
    in_sand_base = os.path.join(tif_dir, config['soil sand src'])
    in_silt_base = os.path.join(tif_dir, config['soil silt src'])

    fill_soil_texture_file(in_sand_base, in_silt_base, in_clay_base, xo, yo, xs, ys, out_dir, of_name, rand=False)

  if 'topo' in files:
    of_name = os.path.join(out_dir, "topo.nc")

    in_slope = os.path.join(tif_dir, config['topo slope src'])
    in_aspect = os.path.join(tif_dir, config['topo aspect src'])
    in_elev = os.path.join(tif_dir, config['topo elev src'])

    fill_topo_file(in_slope, in_aspect, in_elev, xo,yo,xs,ys,out_dir, of_name)

  if 'run-mask' in files:
    make_run_mask(os.path.join(out_dir, "run-mask.nc"), sizey=ys, sizex=xs, match2veg=True) #setpx='1,1')

  if 'co2' in files:
    make_co2_file(os.path.join(out_dir, "co2.nc"))

  if 'historic-climate' in files:
    of_name = "historic-climate.nc"
    # Tried parsing this stuff automatically from the above paths,
    # but the paths, names, directory structures, etc were not standardized
    # enough to be worth it.
    first_avail_year    = int(config['h clim first yr'])
    last_avail_year     = int(config['h clim last yr'])
    origin_institute    = config['h clim orig inst']
    version             = config['h clim ver']
    in_tair_base = os.path.join(tif_dir, config['h clim tair src'])
    in_prec_base = os.path.join(tif_dir, config['h clim prec src'])
    in_rsds_base = os.path.join(tif_dir, config['h clim rsds src'])
    in_vapo_base = os.path.join(tif_dir, config['h clim vapo src'])

    # Use the the January file for the first year requested as a spatial reference
    sp_ref_file  = "{}{month:02d}_{starty:04d}.tif".format(in_tair_base, month=1, starty=first_avail_year),

    # Calculates number of years for running all. Values are different
    # for historic versus projected.
    hc_years = 0
    if years == -1:
      filecount = len(glob.glob(in_tair_base + "*.tif"))
      print "Found %s files..." % filecount
      hc_years = (filecount/12) - start_year
    else:
      hc_years = years

    #print "filecount: {}".format(filecount)
    print "hc_years: {}".format(hc_years)
    fill_climate_file(first_avail_year+start_year, hc_years,
                      xo, yo, xs, ys,
                      out_dir, of_name, sp_ref_file,
                      in_tair_base, in_prec_base, in_rsds_base, in_vapo_base,
                      time_coord_var, model=origin_institute, scen=version)


  if 'projected-climate' in files:
    of_name = "projected-climate.nc"

    # Tried parsing this stuff automatically from the above paths,
    # but the paths, names, directory structures, etc were not standardized
    # enough to be worth it.
    first_avail_year    = int(config['p clim first yr'])
    last_avail_year     = int(config['p clim last yr'])
    origin_institute    = config['p clim orig inst']
    version             = config['p clim ver']
    in_tair_base = os.path.join(tif_dir, config['p clim tair src'])
    in_prec_base = os.path.join(tif_dir, config['p clim prec src'])
    in_rsds_base = os.path.join(tif_dir, config['p clim rsds src'])
    in_vapo_base = os.path.join(tif_dir, config['p clim vapo src'])

    # Pick the starting year of the projected file to immediately follow the 
    # last year in the historic file.
    if ('projected-climate' in files) and ('historic-climate' in files):
      if clip_projected2match_historic:

        # Look up the last year that is in the historic data
        # assumes that the historic file was just created, and so exists and 
        # is reliable...
        with netCDF4.Dataset(os.path.join(out_dir, 'historic-climate.nc'), 'r') as hds:
          end_hist = netCDF4.num2date(hds.variables['time'][-1], hds.variables['time'].units, calendar=hds.variables['time'].calendar)
        print "The historic dataset ends at {}".format(end_hist)

        if (first_avail_year > end_hist.year+1):
          print """==> WARNING! There will be a gap between the historic and 
          projected climate files!! Ignoring --start-year offset and will 
          start building at the beginning of the projected period ({})
          """.format(first_avail_year)
          start_year = 0
        else:
          # Override start_year
          start_year = (end_hist.year - first_avail_year) + 1 
          print """Setting start year for projected data to be immediately 
          following the historic data. 
          End historic: {} 
          Beginning projected: {}
          start_year offset: {}""".format(end_hist.year, first_avail_year + start_year, start_year)

    # Set the spatial reference file. Use the first month of the starting year
    sp_ref_file  = "{}{month:02d}_{starty:04d}.tif".format(in_tair_base, month=1, starty=first_avail_year),

    # Calculates number of years for running all. Values are different
    # for historic versus projected.
    pc_years = 0;
    if years == -1:
      filecount = len(glob.glob(in_tair_base + "*.tif"))
      print "Found %s files..." % filecount
      pc_years = (filecount/12) - start_year
    else:
      pc_years = years

    #print "filecount: {}".format(filecount)
    print "pc_years: {}".format(pc_years)
    fill_climate_file(first_avail_year + start_year, pc_years,
                      xo, yo, xs, ys, out_dir, of_name, sp_ref_file,
                      in_tair_base, in_prec_base, in_rsds_base, in_vapo_base,
                      time_coord_var, model=origin_institute, scen=version)



  if 'fri-fire' in files:
    of_name = os.path.join(out_dir, "fri-fire.nc")
    fill_fri_fire_file(
        xo, yo, xs, ys, out_dir, of_name, 
        datasrc='no-fires', 
        if_name=None,
    )

  if 'historic-explicit-fire' in files:
    of_name = os.path.join(out_dir, "historic-explicit-fire.nc")

    climate = os.path.join(os.path.split(of_name)[0], 'historic-climate.nc')
    print "--> NOTE: Guessing length of time dimension from: {:}".format(climate)
    with netCDF4.Dataset(climate, 'r') as climate_dataset:
      years = len(climate_dataset.dimensions['time']) / 12

    fill_explicit_fire_file(
        years, xo, yo, xs, ys, out_dir, of_name,
        datasrc='no-fires',
        if_name=None
    )

  if 'projected-explicit-fire' in files:
    of_name = os.path.join(out_dir, "projected-explicit-fire.nc")

    climate = os.path.join(os.path.split(of_name)[0], 'projected-climate.nc')
    print "--> NOTE: Guessing length of time dimension from: {:}".format(climate)
    with netCDF4.Dataset(climate, 'r') as climate_dataset:
      years = len(climate_dataset.dimensions['time']) / 12

    fill_explicit_fire_file(
        years, xo, yo, xs, ys, out_dir, of_name,
        datasrc='no-fires',
        if_name=None
    )

  print(textwrap.dedent('''\

      ----> CAVEATS:
       * The input file series are from SNAP, use CRU-TS40 for historic climate
         and AR5 for the projected climate.
  '''))

  print "DONE"



def get_slurm_wrapper_string():
  '''
  When running this program (create_region_input.py) on atlas, it is best to
  run under the control of the queue manager (slurm). This function is a place
  to store a wrapper script that can be submitted to slurm.

  Returns string with text for slurm script.
  '''
  s = textwrap.dedent('''\
    #!/bin/bash

    #SBATCH --cpus-per-task=4
    #SABTCH --ntasks=1
    #SBATCH -p main
    ##SBATCH --reservation=snap_8  # Not needed anymore

    # Offsets for new ar5/rcp85 datasets found in:
    TIFDIR="/atlas_scratch/ALFRESCO/ALFRESCO_Master_Dataset_v2_1/ALFRESCO_Model_Input_Datasets/IEM_for_TEM_inputs/"

    #PCLIM="mri-cgcm3"
    PCLIM="ncar-ccsm4"

    ###################
    # 10x10 sites
    ###################
    #XSIZE=10
    #YSIZE=10

    #site=cru-ts40_ar5_rcp85_"$PCLIM"_Toolik; yoff=298; xoff=918
    #site=cru-ts40_ar5_rcp85_"$PCLIM"_SouthBarrow; yoff=28; xoff=620 
    #site=cru-ts40_ar5_rcp85_"$PCLIM"_SewardPeninsula; yoff=643; xoff=231 
    #site=cru-ts40_ar5_rcp85_"$PCLIM"_Kougarok; yoff=649; xoff=233;

    # Dalton Highway Sites with site at LOWER LEFT corner
    #site=cru-ts40_ar5_rcp85_"$PCLIM"_dh_site_1; yoff=470 ; xoff=900
    #site=cru-ts40_ar5_rcp85_"$PCLIM"_dh_site_2; yoff=429 ; xoff=906
    #site=cru-ts40_ar5_rcp85_"$PCLIM"_dh_site_3; yoff=379 ; xoff=915
    #site=cru-ts40_ar5_rcp85_"$PCLIM"_dh_site_4; yoff=246 ; xoff=947
    #site=cru-ts40_ar5_rcp85_"$PCLIM"_dh_site_5; yoff=210 ; xoff=948

    ####################
    # 50x50 sites
    ####################
    XSIZE=50
    YSIZE=50

    site=cru-ts40_ar5_rcp85_"$PCLIM"_Toolik; yoff=250; xoff=919



    # USE this to put the desired pixel at the center of the grid.
    #echo "Original x and y offsets: $xoff $yoff"
    #yoff=$(( $yoff + $(( $YSIZE / 2 )) ))
    #xoff=$(( $xoff - $(( $XSIZE / 2 )) ))
    #echo "New x and y offsets: $xoff $yoff"

    echo $site

    srun ./scripts/create_region_input.py \
      --tifs $TIFDIR \
      --tag $site \
      --years -1 \
      --buildout-time-coord \
      --yoff $yoff --xoff $xoff --xsize $XSIZE --ysize $YSIZE \
      --which all \
      --projected-climate-config "$PCLIM" \
      --clip-projected2match-historic

    # Handle cropping if needed...
    #mkdir -p input-staging-area/"$site"_"$YSIZE"x"$XSIZE"/output
    #srun ./scripts/input_util.py crop --yx 0 0 --ysize 1 --xsize 1 input-staging-area/"$site"_"$YSIZE"x"$XSIZE"/

    # Generate plots for double checking data... (Should this be submitted with srun too??)
    #./scripts/input_util.py climate-ts-plot --type annual-summary --yx 0 0 input-staging-area/

    # REMEMBER TO CHECK FOR GAPFILLING NEEDS!!!
    srun ./scripts/gapfill.py --dry-run --input-folder input-staging-area/"$site"_"$YSIZE"x"$XSIZE"/
    #srun ./scripts/gapfill.py --dry-run --input-folder input-staging-area/"$site"_1x1/

    # Run script to swap all CMT 8 pixels to CMT 7
    srun ./scripts/fix_vegetation_file_cmt08_to_cmt07.py input-staging-area/"$site"_"$YSIZE"x"$XSIZE"/vegetation.nc
    #srun ./scripts/fix_vegetation_file_cmt08_to_cmt07.py input-staging-area/"$site"_1x1/vegetation.nc


    # Old stuff...
    #srun ./scripts/create_region_input.py --tifs /atlas_scratch/tem/snap-data/ --tag Kougarok --years -1 --start-year 9  --buildout-time-coord --xoff 230 --yoff 641 --xsize 10 --ysize 10 --which projected-climate
    #srun ./scripts/create_region_input.py --tifs /atlas_scratch/tem/snap-data/ --tag Toolik --years -1 --start-year 9 --buildout-time-coord --xoff 1137 --yoff 239 --xsize 50 --ysize 50 --which projected-climate 

    # Dalton Highway Sites for Ceci, 2018 summer REU work
    # Offsets for ar4 (old) data in /atlas_scratch/tem/snap-data
    #site=site_1; yoff=472; xoff=898
    #site=site_2; yoff=431; xoff=903
    #site=site_3; yoff=381; xoff=912
    #site=site_4; yoff=248; xoff=944
    #site=site_5; yoff=211; xoff=945

  ''')
  return s


def get_empty_config_object():
  '''
  Returns a configuration object with all the required keys, but no values.
  '''
  empty_config_string = textwrap.dedent('''\
      veg src = ''

      drainage src = ''

      soil clay src = ''
      soil sand src = ''
      soil silt src = ''

      topo slope src = ''
      topo aspect src = ''
      topo elev src = ''

      h clim first yr = ''
      h clim last yr = ''
      h clim orig inst = ''
      h clim ver = ''
      h clim tair src = ''
      h clim prec src = ''
      h clim rsds src = ''
      h clim vapo src = ''

      p clim first yr = ''
      p clim last yr = ''
      p clim ver = ''
      p clim orig inst = ''
      p clim tair src = ''
      p clim prec src = ''
      p clim rsds src = ''
      p clim vapo src = ''

      fire fri src = ''
    ''')
  return configobj.ConfigObj(empty_config_string.split("\n"))




if __name__ == '__main__':

  base_ar5_rcp85_config = textwrap.dedent('''\
    veg src = 'ancillary/land_cover/v_0_4/iem_vegetation_model_input_v0_4.tif'

    drainage src = 'ancillary/drainage/Lowland_1km.tif'

    soil clay src = 'ancillary/BLISS_IEM/mu_claytotal_r_pct_0_25mineral_2_AK_CAN.img'
    soil sand src = 'ancillary/BLISS_IEM/mu_sandtotal_r_pct_0_25mineral_2_AK_CAN.img'
    soil silt src = 'ancillary/BLISS_IEM/mu_silttotal_r_pct_0_25mineral_2_AK_CAN.img'

    topo slope src = 'ancillary/slope/iem_prism_slope_1km.tif'
    topo aspect src = 'ancillary/aspect/iem_prism_aspect_1km.tif'
    topo elev src = 'ancillary/elevation/iem_prism_dem_1km.tif'

    h clim first yr = 1901
    h clim last yr = 2015
    h clim orig inst = 'CRU'
    h clim ver = 'TS40'
    h clim tair src = 'tas_mean_C_iem_cru_TS40_1901_2015/tas/tas_mean_C_CRU_TS40_historical_'
    h clim prec src = 'pr_total_mm_iem_cru_TS40_1901_2015/pr_total_mm_CRU_TS40_historical_'
    h clim rsds src = 'rsds_mean_MJ-m2-d1_iem_CRU-TS40_historical_1901_2015_fix/rsds/rsds_mean_MJ-m2-d1_iem_CRU-TS40_historical_'
    h clim vapo src = 'vap_mean_hPa_iem_CRU-TS40_historical_1901_2015_fix/vap/vap_mean_hPa_iem_CRU-TS40_historical_'

    fire fri src = 'iem_ancillary_data/Fire/FRI.tif'
  ''')

  mri_cgcm3_ar5_rcp85_config = textwrap.dedent('''\
    p clim first yr = 2006
    p clim last yr = 2100
    p clim ver = 'rcp85'

    p clim orig inst = 'MRI-CGCM3'
    p clim tair src = 'tas_mean_C_ar5_MRI-CGCM3_rcp85_2006_2100/tas/tas_mean_C_iem_ar5_MRI-CGCM3_rcp85_'
    p clim prec src = 'pr_total_mm_ar5_MRI-CGCM3_rcp85_2006_2100/pr/pr_total_mm_iem_ar5_MRI-CGCM3_rcp85_'
    p clim rsds src = 'rsds_mean_MJ-m2-d1_ar5_MRI-CGCM3_rcp85_2006_2100_fix/rsds/rsds_mean_MJ-m2-d1_iem_ar5_MRI-CGCM3_rcp85_'
    p clim vapo src = 'vap_mean_hPa_ar5_MRI-CGCM3_rcp85_2006_2100_fix/vap/vap_mean_hPa_iem_ar5_MRI-CGCM3_rcp85_'
  ''')

  ncar_ccsm4_ar5_rcp85_config = textwrap.dedent('''\
    p clim first yr = 2006
    p clim last yr = 2100
    p clim ver = 'rcp85'

    p clim orig inst = 'NCAR-CCSM4'
    p clim tair src = 'tas_mean_C_ar5_NCAR-CCSM4_rcp85_2006_2100/tas/tas_mean_C_iem_ar5_NCAR-CCSM4_rcp85_'
    p clim prec src = 'pr_total_mm_ar5_NCAR-CCSM4_rcp85_2006_2100/pr/pr_total_mm_iem_ar5_NCAR-CCSM4_rcp85_'
    p clim rsds src = 'rsds_mean_MJ-m2-d1_ar5_NCAR-CCSM4_rcp85_2006_2100_fix/rsds/rsds_mean_MJ-m2-d1_iem_ar5_NCAR-CCSM4_rcp85_'
    p clim vapo src = 'vap_mean_hPa_ar5_NCAR-CCSM4_rcp85_2006_2100_fix/vap/vap_mean_hPa_iem_ar5_NCAR-CCSM4_rcp85_'
  ''')



  fileChoices = ['run-mask', 'co2', 'vegetation', 'drainage', 'soil-texture', 'topo',
                 'fri-fire', 'historic-explicit-fire', 'projected-explicit-fire',
                 'historic-climate', 'projected-climate']

  # maintain subsets of the file choices to ease argument combo verification  
  temporal_file_choices = [
    'co2',
    'historic-explicit-fire','projected-explicit-fire',
    'historic-climate','projected-climate'
  ]
  spatial_file_choices = [f for f in filter(lambda x: x not in ['co2'], fileChoices)]


  parser = argparse.ArgumentParser(
    formatter_class = argparse.RawDescriptionHelpFormatter,

      description=textwrap.dedent('''\
        Creates a set of input files for dvmdostem.

        <OUTDIR>/<TAG>_<YSIZE>x<XSIZE>/
                {0}

        <OUTDIR>/<TAG>_<YSIZE>x<XSIZE>/output/restart-eq.nc

        Assumes a certain layout for the source files. At this point, the 
        source files are generally .tifs that have been created for the IEM
        project. As of Oct 2018 the is desgined to work with the data on 
        the atlas server:

        atlas:/atlas_scratch/ALFRESCO/ALFRESCO_Master_Dataset_v2_1/ALFRESCO_Model_Input_Datasets/IEM_for_TEM_inputs/

        **THE PATHS IN THIS SCIRPT MUST BE EDITED BY HAND IF IT IS TO BE RUN ON
        A DIFFERENT COMPUTER OR IF THE DIRECTORY LAYOUT ON ATLAS CHANGES!**

        Running this script on atlas under Slurm it takes about 15 minutes to
        create a complete input dataset for all historic and projected years.

        There is a command line option to print an example slurm script.
        '''.format("\n                ".join([i+'.nc' for i in fileChoices]))),

      epilog=textwrap.dedent(''''''),
  )
  
  parser.add_argument('--crtf-only', action="store_true",
      help=textwrap.dedent("""(DEPRECATED - now built into dvmdostem) Only 
        create the restart template file."""))

  parser.add_argument('--tifs', default="", required=True,
      help=textwrap.dedent("""Directory containing input TIF directories. This
        is used as a "base path", and it is assumed that all the requsite input
        files exist somewhere within the directory specified by this option.
        Using '/' as the --tifs argument allows absolute path specification in
        the config object in cases where required input files are not all
        contained within one directory. 
        (default: '%(default)s')"""))

  parser.add_argument('--outdir', default="input-staging-area",
      help=textwrap.dedent("""Directory for netCDF output files. 
        (default: '%(default)s')"""))

  parser.add_argument('--tag', required=True,
      help=textwrap.dedent("""A name for the dataset, used to name output 
        directory. (default: '%(default)s')"""))

  parser.add_argument('--years', type=int,
      help=textwrap.dedent("""The number of years of the climate data to 
        process. Use -1 to run for all TIFs found in input directory. 
        (default: %(default)s)"""))

  parser.add_argument('--start-year', default=0, type=int,
      help=textwrap.dedent("""An offset to use for making a climate dataset 
        that doesn't start at the beginning of the historic (1901) or projected
        (2001) datasets. Mostly deprecated in favor of --clip-projected2match-historic"""))

  parser.add_argument('--buildout-time-coord', action='store_true',
      help=textwrap.dedent('''Add a time coordinate variable to the *-climate.nc 
        files. Also populates the coordinate variable attributes.'''))

  parser.add_argument('--xoff', type=int,
      help="source window offset for x axis (default: %(default)s)")
  parser.add_argument('--yoff', type=int,
      help="source window offset for y axis (default: %(default)s)")

  parser.add_argument('--xsize', type=int,
      help="source window x size (default: %(default)s)")
  parser.add_argument('--ysize', type=int,
      help="source window y size (default: %(default)s)")

  parser.add_argument('--which', default=['all'], nargs='+',
      choices=fileChoices+['all'], metavar='FILE',
      help=textwrap.dedent('''Space separated list of which files to create. 
        Allowed values: {:}. (default: %(default)s)'''.format(', '.join(fileChoices+['all']))))

  parser.add_argument('--clip-projected2match-historic', action='store_true',
    help=textwrap.dedent('''Instead of building the entire projected dataset, 
      start building it where the historic 
      data leaves off.'''))

  parser.add_argument('--generate-slurm-wrapper', action='store_true',
      help=textwrap.dedent('''Writes the file "CRI_slurm_wrapper.sh" and exits.
        Submit CRI_slurm_wrapper.sh to slurm using sbatch. Expected workflow
        is that you will generate the slurm wrapper script and then edit the
        script as needed (uncommenting the lines for the desired site and post
        processing steps that you want).'''))

  parser.add_argument('--dump-empty-config', action='store_true',
      help=textwrap.dedent('''Write out an empty config file with all the keys
        that need to be filled in to make a functioning config object.'''))

  parser.add_argument('--projected-climate-config', nargs=1, choices=['ncar-ccsm4', 'mri-cgcm3'],
      help=textwrap.dedent('''Choose a configuration to use for the projected 
        climate data.'''))

  print "Parsing command line arguments..."
  args = parser.parse_args()
  print "args: ", args

  print "Reading config file..."
  config = configobj.ConfigObj(base_ar5_rcp85_config.split("\n"))


  if args.generate_slurm_wrapper:
    ofname = 'CRI_slurm_wrapper.sh'
    print "Writing wrapper file: {}".format(ofname)
    print "Submit using sbatch."
    with open(ofname, 'w') as f:
      f.write(get_slurm_wrapper_string())
    exit(0)

  if args.dump_empty_config:
    ofname = "EMPTY_CONFIG_create_region_input.txt"
    print "Writing empty config file: {}".format(ofname)
    ec = get_empty_config_object()
    ec.filename = ofname
    ec.write()
    exit(0)



  # Verify argument combinations: time coordinate variables and files
  if args.clip_projected2match_historic:
    if ('historic-climate' in args.which) and ('projected-climate' in args.which):
      pass # everything ok...
    elif 'all' in args.which:
      pass # everything ok...
    else:
      print "ERROR!: Can't clip the projected climate to start where the "
      print "        historic data leaves off unless creating both historic "
      print "        and projected files!"
      exit(-1)
    if (args.buildout_time_coord):
      pass # everything ok...
    else:
      print "ERROR!: You MUST specify to the --buildout-time-coord option if you want to match historic and projected files!"
      exit(-1)
    if args.start_year > 0:
      print "WARNING! The --start-year offset will be ignored for projected climate file!"


  # Verify argument combinations: spatial and time dims, required paths 
  # for source datafiles...
  which_files = args.which
  if 'all' in which_files:
    print "Will generate ALL input files."
    which_files = fileChoices

  if any( [f in temporal_file_choices for f in which_files] ):
    if not all([x is not None for x in [args.years, args.start_year]]):
      print args
      print args.which
      print which_files
      parser.error("Argument ERROR!: Must specify years and start year for temporal files!")

  if any( [f in spatial_file_choices for f in which_files] ):
    if not all([x is not None for x in [args.xoff, args.yoff, args.xsize, args.ysize]]):
      print args
      print args.which
      print which_files
      parser.error("Argument ERROR!: Must specify ALL sizes and offsets for spatial files!")

  if any(f for f in which_files if f != 'co2'):
    verify_paths_in_config_dict(args.tifs, config)

  # Verify argument combos: project climate configuration specified when 
  # asking to generate projected climate
  if 'projected-climate' in which_files:
    if args.projected_climate_config is not None:
      pass # All ok - value is set and the choices are constrained above
    else:
      parser.error("Argument ERROR! Must specify a projecte climate configuration for the projected-climate file!")


  # Pick up the user's config option for which projected climate to use 
  # overwrite the section in the config object.
  cmdline_config = configobj.ConfigObj()
  if 'projected-climate' in which_files:
    if 'ncar-ccsm4' in args.projected_climate_config:
      cmdline_config = configobj.ConfigObj(ncar_ccsm4_ar5_rcp85_config.split("\n"))
    elif 'mri-cgcm3' in args.projected_climate_config:
      cmdline_config = configobj.ConfigObj(mri_cgcm3_ar5_rcp85_config.split("\n"))

  config.merge(cmdline_config)

  print "\n".join(config.write())

  years = args.years
  start_year = args.start_year
  
  xo = args.xoff
  yo = args.yoff
  xs = args.xsize
  ys = args.ysize

  tif_dir = args.tifs;
  print "Will be looking for files in:      ", tif_dir

  # Like this: somedirectory/sometag_NxM
  out_dir = os.path.join(args.outdir, "%s_%sx%s" % (args.tag, ys, xs))
  print "Will be (over)writing files to:    ", out_dir
  if not os.path.exists(out_dir):
    os.makedirs(out_dir)

  # All we are doing is creating a restart template file, then quitting.
  if args.crtf_only:
    if not os.path.exists( os.path.join(out_dir, "output") ):
      os.mkdir(os.path.join(out_dir, "output"))

    create_template_restart_nc_file(os.path.join(out_dir, "output/restart-eq.nc"), sizey=ys, sizex=xs)
    create_template_restart_nc_file(os.path.join(out_dir, "output/restart-sp.nc"), sizey=ys, sizex=xs)
    create_template_restart_nc_file(os.path.join(out_dir, "output/restart-tr.nc"), sizey=ys, sizex=xs)
    create_template_restart_nc_file(os.path.join(out_dir, "output/restart-sc.nc"), sizey=ys, sizex=xs)
    exit()



  print type(start_year), type(years)
  main(start_year, years, xo, yo, xs, ys, tif_dir, out_dir,
       files=which_files,
       config=config,
       time_coord_var=args.buildout_time_coord, 
       clip_projected2match_historic=args.clip_projected2match_historic)



