#!/usr/bin/env python


from subprocess import call
from subprocess import check_call
import subprocess

import shutil

import multiprocessing as mp

import argparse
import textwrap
import os

import netCDF4

import numpy as np

from osgeo import gdal

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

# (0,0) pixel is hardcoded to the exact values from Toolik for testing.

def tunnel_fast(latvar,lonvar,lat0,lon0):
  '''
  Find closest point in a set of (lat,lon) points to specified point
  latvar - 2D latitude variable from an open netCDF dataset
  lonvar - 2D longitude variable from an open netCDF dataset
  lat0,lon0 - query point
  Returns iy,ix such that the square of the tunnel distance
  between (latval[it,ix],lonval[iy,ix]) and (lat0,lon0)
  is minimum.
  Code from Unidata's Python Workshop:
  https://github.com/Unidata/unidata-python-workshop
  '''
  rad_factor = np.pi/180.0 # for trignometry, need angles in radians
  # Read latitude and longitude from file into numpy arrays
  latvals = latvar[:] * rad_factor
  lonvals = lonvar[:] * rad_factor
  ny,nx = latvals.shape
  lat0_rad = lat0 * rad_factor
  lon0_rad = lon0 * rad_factor
  # Compute numpy arrays for all values, no loops
  clat,clon = np.cos(latvals), np.cos(lonvals)
  slat,slon = np.sin(latvals), np.sin(lonvals)
  delX = np.cos(lat0_rad)*np.cos(lon0_rad) - clat*clon
  delY = np.cos(lat0_rad)*np.sin(lon0_rad) - clat*slon
  delZ = np.sin(lat0_rad) - slat;
  dist_sq = delX**2 + delY**2 + delZ**2
  minindex_1d = dist_sq.argmin()  # 1D index of minimum element
  iy_min,ix_min = np.unravel_index(minindex_1d, latvals.shape)
  return iy_min,ix_min

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
    378.6636, 380.5236, 382.3536, 384.1336 ]

  yearV[:] = [ 1901, 1902, 1903, 1904, 1905, 1906, 1907, 1908, 1909, 1910, 1911,
    1912, 1913, 1914, 1915, 1916, 1917, 1918, 1919, 1920, 1921, 1922, 1923, 
    1924, 1925, 1926, 1927, 1928, 1929, 1930, 1931, 1932, 1933, 1934, 1935, 
    1936, 1937, 1938, 1939, 1940, 1941, 1942, 1943, 1944, 1945, 1946, 1947, 
    1948, 1949, 1950, 1951, 1952, 1953, 1954, 1955, 1956, 1957, 1958, 1959, 
    1960, 1961, 1962, 1963, 1964, 1965, 1966, 1967, 1968, 1969, 1970, 1971, 
    1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980, 1981, 1982, 1983, 
    1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994, 1995, 
    1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 
    2008, 2009 ]

  new_ncfile.source = source_attr_string()
  new_ncfile.close()

def create_template_topo_file(fname, sizey=10, sizex=10):
  '''Generate a template file for drainage classification.'''
  print "Creating an empty topography  file, %s by %s pixels. (%s)" % (sizey, sizex, os.path.basename(fname))
  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)
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
                      '-srcwin', str(xo), str(yo), str(xs), str(ys),
                      inFile, tmpFile])

  with netCDF4.Dataset(of_name, mode='a') as new_topodataset:
    for ncvar, tmpFileName in zip(['slope','aspect','elevation'],[tmpSlope,tmpAspect,tmpElev]):
      with netCDF4.Dataset(tmpFileName, 'r') as TF:
        V = new_topodataset.variables[ncvar]
        V[:] = TF.variables['Band1'][:]


def fill_veg_file(if_name, xo, yo, xs, ys, out_dir, of_name):
  '''Read subset of data from .tif into netcdf file for dvmdostem. '''

  of_stripped = os.path.basename(of_name);

  # Create place for data
  create_template_veg_nc_file(of_name, sizey=ys, sizex=xs, rand=None)

  # Translate and subset to temporary location
  temporary = os.path.join('/tmp', of_stripped)

  if not os.path.exists( os.path.dirname(temporary) ):
    os.makedirs(os.path.dirname(temporary))

  subprocess.call(['gdal_translate', '-of', 'netcdf',
                   '-srcwin', str(xo), str(yo), str(xs), str(ys),
                   if_name, temporary])

  # Copy from temporary location to into the placeholder file we just created
  with netCDF4.Dataset(temporary) as t1, netCDF4.Dataset(of_name, mode='a') as new_vegdataset:
    veg_class = new_vegdataset.variables['veg_class']

    new_vegdataset.source = source_attr_string(xo=xo, yo=yo)

    veg_class[:] = t1.variables['Band1'][:].data 
    # For some reason, some rows of the temporary file are numpy masked arrays
    # and if we don't directly access the data, then we get strange results '
    # (i.e. stuff that should be ocean shows up as CMT02??)
    # If we use the .data method, then the ocean ends up filled with '-1' and 
    # lakes end up as CMT00, which is what we want. Alternatively, could use the
    # .filled(-1) method.


def fill_climate_file(start_yr, yrs, xo, yo, xs, ys,
                      out_dir, of_name, sp_ref_file,
                      in_tair_base, in_prec_base, in_rsds_base, in_vapo_base):

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
      tmpfile, smaller_tmpfile
    ])
  print "Finished creating the temporary subset...(cropping to our domain)"

  print "Copy the LAT/LON variables from the temporary file into our new dataset..."
  # Open the 'temporary' dataset
  temp_subset_with_lonlat = netCDF4.Dataset(smaller_tmpfile, mode='r')

  # Open the new file for appending
  new_climatedataset = netCDF4.Dataset(masterOutFile, mode='a')

  # Insert lat/lon from temp file into the new file
  lat = new_climatedataset.variables['lat']
  lon = new_climatedataset.variables['lon']
  lat[:] = temp_subset_with_lonlat.variables['lat'][:]
  lon[:] = temp_subset_with_lonlat.variables['lon'][:]

  print "Write attribute with pixel offsets to file..."
  new_climatedataset.source = source_attr_string(xo=xo, yo=yo)

  print "Done copying LON/LAT."

  print "Closing new dataset and temporary file."
  new_climatedataset.close()
  temp_subset_with_lonlat.close()

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
      baseFiles = [basePath + "_{:02d}_{:04d}.tif".format(month, year) for basePath in basePathList]
      tmpFiles = [os.path.join(out_dir, 'TEMP-{}-{}'.format(v, of_name)) for v in dataVarList]

      procs = []
      for tiffimage, tmpFileName, vName in zip(baseFiles, tmpFiles , dataVarList):
        proc = mp.Process(target=convert_and_subset, args=(tiffimage, tmpFileName, xo, yo, xs, ys, yridx,midx,vName))
        procs.append(proc)
        proc.start()

      for proc in procs:
        proc.join()

  print "Done with year loop."

  print "Copy data from temporary per-variable files into master"
  for tFile, var in zip(tmpFiles, dataVarList):
    # Need to make a list of variables to exclude from the
    # ncks append operation (all except the current variable)
    masked_list = [i for i in dataVarList if var not in i]

    opt_str = "lat,lon," + ",".join(masked_list)
    check_call(['ncks', '--append', '-x','-v',opt_str, tFile, masterOutFile])

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

  print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
  print "%% NOTE! Converting rsds (nirr) from MJ/m^2/day to W/m^2!"
  print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
  with netCDF4.Dataset(masterOutFile, mode='a') as new_climatedataset:
    nirr = new_climatedataset.variables['nirr']
    nirr[:] = (1000000 / (60*60*24)) * nirr[:]


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
      subprocess.check_call(['gdal_translate','-of','netCDF','-srcwin',
                             str(xo), str(yo), str(xs), str(ys),
                             if_sand_name,
                             '/tmp/create_region_input_script_sand_texture.nc'])

      subprocess.check_call(['gdal_translate','-of','netCDF','-srcwin',
                             str(xo), str(yo), str(xs), str(ys),
                             if_silt_name,
                             '/tmp/create_region_input_script_silt_texture.nc'])

      subprocess.check_call(['gdal_translate','-of','netCDF','-srcwin',
                             str(xo), str(yo), str(xs), str(ys),
                             if_clay_name,
                             '/tmp/create_region_input_script_clay_texture.nc'])

      print "Writing subset's data to new files..."
      with netCDF4.Dataset('/tmp/create_region_input_script_sand_texture.nc', mode='r') as f:
        p_sand[:] = f.variables['Band1'][:]
      with netCDF4.Dataset('/tmp/create_region_input_script_silt_texture.nc', mode='r') as f:
        p_silt[:] = f.variables['Band1'][:]
      with netCDF4.Dataset('/tmp/create_region_input_script_clay_texture.nc', mode='r') as f:
        p_clay[:] = f.variables['Band1'][:]

    soil_tex.source =  source_attr_string(xo=xo, yo=yo)


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
      check_call(['gdal_translate', '-of', 'netCDF', '-srcwin',
                  str(xo), str(yo), str(xs), str(ys),
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

      drainage_class.source = source_attr_string(xo=xo, yo=yo)

def fill_fri_fire_file(if_name, xo, yo, xs, ys, out_dir, of_name):
  create_template_fri_fire_file(of_name, sizey=ys, sizex=xs, rand=False)

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

    print "==> write global :source attribute to FRI fire file..."
    nfd.source = source_attr_string(xo=xo, yo=yo)


def fill_explicit_fire_file(if_name, yrs, xo, yo, xs, ys, out_dir, of_name):
  create_template_explicit_fire_file(of_name, sizey=ys, sizex=xs, rand=False)

  print "%%%%%%  WARNING  %%%%%%%%%%%%%%%%%"
  print "GENERATING FAKE DATA!"
  print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"

  never_burn = ([9],[9])
  print "--> Never burn pixels: {}".format(zip(*never_burn))

  # guess_vegfile = os.path.join(os.path.split(of_name)[0], 'vegetation.nc')
  # print "--> NOTE: Attempting to read: {:}".format(guess_vegfile)
  # print "    and set fire properties based on community type..."
  # with netCDF4.Dataset(guess_vegfile ,'r') as vegFile:
  #   vd = vegFile.variables['veg_class'][:]

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

  print "Setting :source attribute on new explicit fire file..."
  with netCDF4.Dataset(of_name, mode='a') as nfd:
    nfd.source = source_attr_string(xo=xo, yo=yo)



def main(start_year, years, xo, yo, xs, ys, tif_dir, out_dir, files=[]):

  #
  # Make the veg file first, then run-mask, then climate, then fire.
  #
  # The fire files require the presence of the veg map, and climate!
  #
  if 'vegetation' in files:
    of_name = os.path.join(out_dir, "vegetation.nc")
    fill_veg_file(os.path.join(tif_dir,  "iem_ancillary_data/Landcover/LandCover_iem_TEM_2005.tif"), xo, yo, xs, ys, out_dir, of_name)

  if 'drainage' in files:
    of_name = os.path.join(out_dir, "drainage.nc")
    fill_drainage_file(os.path.join(tif_dir,  "iem_ancillary_data/soil_and_drainage/Lowland_1km.tif"), xo, yo, xs, ys, out_dir, of_name)

  if 'soil-texture' in files:
    of_name = os.path.join(out_dir, "soil-texture.nc")
    in_sand_base = os.path.join(tif_dir,  "iem_ancillary_data/soil_and_drainage/iem_domain_hayes_igbp_pct_sand.tif")
    in_silt_base = os.path.join(tif_dir,  "iem_ancillary_data/soil_and_drainage/iem_domain_hayes_igbp_pct_silt.tif")
    in_clay_base = os.path.join(tif_dir,  "iem_ancillary_data/soil_and_drainage/iem_domain_hayes_igbp_pct_clay.tif")

    fill_soil_texture_file(in_sand_base, in_silt_base, in_clay_base, xo, yo, xs, ys, out_dir, of_name, rand=False)

  if 'topo' in files:
    of_name = os.path.join(out_dir, "topo.nc")
    in_slope = os.path.join(tif_dir,  "iem_ancillary_data/Elevation/ALF_AK_CAN_prism_slope_1km.tif")
    in_aspect = os.path.join(tif_dir,  "iem_ancillary_data/Elevation/ALF_AK_CAN_prism_aspect_1km.tif")
    in_elev = os.path.join(tif_dir,  "iem_ancillary_data/Elevation/ALF_AK_CAN_prism_dem_1km.tif")
    fill_topo_file(in_slope, in_aspect, in_elev, xo,yo,xs,ys,out_dir, of_name)

  if 'run-mask' in files:
    make_run_mask(os.path.join(out_dir, "run-mask.nc"), sizey=ys, sizex=xs, match2veg=True) #setpx='1,1')

  if 'co2' in files:
    make_co2_file(os.path.join(out_dir, "co2.nc"))

  if 'historic-climate' in files:
    of_name = "historic-climate.nc"
    sp_ref_file  = os.path.join(tif_dir,  "tas_mean_C_iem_cru_TS31_1901_2009/tas_mean_C_iem_cru_TS31_%02d_%04d.tif" % (1, 1901))
    in_tair_base = os.path.join(tif_dir,  "tas_mean_C_iem_cru_TS31_1901_2009/tas_mean_C_iem_cru_TS31")
    in_prec_base = os.path.join(tif_dir,  "pr_total_mm_iem_cru_TS31_1901_2009/pr_total_mm_iem_cru_TS31")
    in_rsds_base = os.path.join(tif_dir,  "rsds_mean_MJ-m2-d1_iem_cru_TS31_1901_2009/rsds_mean_MJ-m2-d1_iem_cru_TS31")
    in_vapo_base = os.path.join(tif_dir,  "vap_mean_hPa_iem_cru_TS31_1901_2009/vap_mean_hPa_iem_cru_TS31")

    # Calculates number of years for running all. Values are different
    # for historic versus projected.
    hc_years = 0
    if years == -1:
      filecount = len(glob.glob(os.path.join(tif_dir,  "tas_mean_C_iem_cru_TS31_1901_2009/*.tif")))
      print "Found %s files..." % filecount
      hc_years = filecount/12 
    else:
      hc_years = years

    fill_climate_file(1901+start_year, hc_years, xo, yo, xs, ys, out_dir, of_name, sp_ref_file, in_tair_base, in_prec_base, in_rsds_base, in_vapo_base)


  if 'projected-climate' in files:
    of_name = "projected-climate.nc"
    sp_ref_file  = os.path.join(tif_dir,  "tas_mean_C_iem_cccma_cgcm3_1_sresa1b_2001_2100/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_%02d_%04d.tif" % (1, 2001))
    in_tair_base = os.path.join(tif_dir,  "tas_mean_C_iem_cccma_cgcm3_1_sresa1b_2001_2100/tas_mean_C_iem_cccma_cgcm3_1_sresa1b")
    in_prec_base = os.path.join(tif_dir,  "pr_total_mm_iem_cccma_cgcm3_1_sresa1b_2001_2100/pr_total_mm_iem_cccma_cgcm3_1_sresa1b")
    in_rsds_base = os.path.join(tif_dir,  "rsds_mean_MJ-m2-d1_iem_cccma_cgcm3_1_sresa1b_2001_2100/rsds_mean_MJ-m2-d1_iem_cccma_cgcm3_1_sresa1b")
    in_vapo_base = os.path.join(tif_dir,  "vap_mean_hPa_iem_cccma_cgcm3_1_sresa1b_2001_2100/vap_mean_hPa_iem_cccma_cgcm3_1_sresa1b")

    # Calculates number of years for running all. Values are different
    # for historic versus projected.
    pc_years = 0;
    if years == -1:
      filecount = len(glob.glob(os.path.join(tif_dir, "tas_mean_C_iem_cccma_cgcm3_1_sresa1b_2001_2100/*.tif")))
      print "Found %s files..." % filecount
      pc_years = filecount/12
    else:
      pc_years = years

    fill_climate_file(2001+start_year, pc_years, xo, yo, xs, ys, out_dir, of_name, sp_ref_file, in_tair_base, in_prec_base, in_rsds_base, in_vapo_base)


  if 'fri-fire' in files:
    of_name = os.path.join(out_dir, "fri-fire.nc")
    fill_fri_fire_file(tif_dir + "iem_ancillary_data/Fire/", xo, yo, xs, ys, out_dir, of_name)

  if 'historic-explicit-fire' in files:
    of_name = os.path.join(out_dir, "historic-explicit-fire.nc")

    climate = os.path.join(os.path.split(of_name)[0], 'historic-climate.nc')
    print "--> NOTE: Guessing length of time dimension from: {:}".format(climate)
    with netCDF4.Dataset(climate, 'r') as climate_dataset:
      years = len(climate_dataset.dimensions['time']) / 12

    fill_explicit_fire_file(tif_dir + "iem_ancillary_data/Fire/", years, xo, yo, xs, ys, out_dir, of_name)

  if 'projected-explicit-fire' in files:
    of_name = os.path.join(out_dir, "projected-explicit-fire.nc")

    climate = os.path.join(os.path.split(of_name)[0], 'projected-climate.nc')
    print "--> NOTE: Guessing length of time dimension from: {:}".format(climate)
    with netCDF4.Dataset(climate, 'r') as climate_dataset:
      years = len(climate_dataset.dimensions['time']) / 12

    fill_explicit_fire_file(tif_dir + "iem_ancillary_data/Fire/", years, xo, yo, xs, ys, out_dir, of_name)

  print "DONE"






if __name__ == '__main__':

  fileChoices = ['run-mask', 'co2', 'vegetation', 'drainage', 'soil-texture', 'topo',
                 'fri-fire', 'historic-explicit-fire', 'projected-explicit-fire',
                 'historic-climate', 'projected-climate']

  parser = argparse.ArgumentParser(
    formatter_class = argparse.RawDescriptionHelpFormatter,

      description=textwrap.dedent('''\
        Creates a set of input files for dvmdostem.

        <OUTDIR>/<TAG>_<YSIZE>x<XSIZE>/
                {0}

        <OUTDIR>/<TAG>_<YSIZE>x<XSIZE>/output/restart-eq.nc

        Assumes a certain layout for the source files. At this point, the 
        source files are generally .tifs that have been created for the IEM
        project.
        '''.format("\n                ".join([i+'.nc' for i in fileChoices]))),

      epilog=textwrap.dedent(''''''),
  )
  
  parser.add_argument('--crtf-only', action="store_true",
                      help="Only create the restart template file. Deprecated in favor of the built in capability in dvmdostem.")

  parser.add_argument('--tifs', default="../snap-data",
                      help="Directory containing input TIF directories.")

  parser.add_argument('--outdir', default="input-staging-area",
                      help="Directory for netCDF output files. (default: %(default)s)")

  parser.add_argument('--tag', default="Toolik",
                      help="A name for the dataset, used to name output directory. (default: %(default)s)")

  parser.add_argument('--years', default=10, type=int, 
                      help="The number of years of the climate data to process. (default: %(default)s). -1 to run for all input TIFs")
  parser.add_argument('--start-year', default=0, type=int,
                      help="An offset to use for making a climate dataset that doesn't start at the beginning of the historic (1901) or projected (2001) datasets.")

  parser.add_argument('--xoff', default=915,
                      help="source window offset for x axis (default: %(default)s)")
  parser.add_argument('--yoff', default=292,
                      help="source window offset for y axis (default: %(default)s)")

  parser.add_argument('--xsize', default=5, type=int,
                      help="source window x size (default: %(default)s)")
  parser.add_argument('--ysize', default=5, type=int,
                      help="source window y size (default: %(default)s)")

  parser.add_argument('--which', default=['all'], nargs='+',
                      choices=fileChoices+['all'],
                      metavar='FILE',
                      help=textwrap.dedent('''\
                        Space separated list of which files to create. 
                        Allowed values: {:}. (default: %(default)s)
                        '''.format(', '.join(fileChoices+['all'])))
                      )



  parser.add_argument('--iyix-from-latlon', default=None, nargs=2, type=float,
                      help="Find closest pixel to provided lat and lon arguments.")

  print "Parsing command line arguments";
  args = parser.parse_args()
  print "args: ", args


  if args.iyix_from_latlon:
    ncfile = netCDF4.Dataset("../snap-data/temporary-veg-from-LandCover_iem_ALFRESCO_2005tif.nc", 'r')
    latvar = ncfile.variables['lat']
    lonvar = ncfile.variables['lon']

    #toolik = {'lat':68.626480, 'lon':-149.594995}
    #bnza_lter = {'lat':64.70138, 'lon':-148.31034}
    #target = bnza_lter
    target = {'lat':args.iyix_from_latlon[0], 'lon':args.iyix_from_latlon[1]}
    iy,ix = tunnel_fast(latvar, lonvar, target['lat'], target['lon'])
    print('Target lat, lon:', target['lat'], target['lon'])
    print('Delta with target lat, lon:', target['lat'] - latvar[iy,ix], target['lon'] - lonvar[iy,ix])
    print('lat, lon of closest match:', latvar[iy,ix], lonvar[iy,ix])
    print('indices of closest match iy, ix (from LOWER left):', iy, ix)
    print('indices of closest match iy, ix (from UPPER left):', len(ncfile.dimensions['y'])-iy, ix)
    ncfile.close()
    exit()

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


  which_files = args.which

  if 'all' in which_files:
    print "Will generate ALL input files."
    which_files = fileChoices

  main(start_year, years, xo, yo, xs, ys, tif_dir, out_dir, files=which_files)



