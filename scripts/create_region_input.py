#!/usr/bin/env python


from subprocess import call
from subprocess import check_call
import subprocess

import argparse
import textwrap
import os

import netCDF4
import numpy as np

from osgeo import gdal

import glob

#some description of what region wanted
#for now, keep to a rectangular requirement?
#Maintain CF and COARDS standards

#Select y,x or lat,lon bounding box coordinates for use


#Data should be in a rectangular (grid) layout
#NetCDF
#Conforms to CF & COARDS standards
#Geospatial information must be with the file. Each file should have variables for Lat and Lon each defined in terms of the dimensions of (y,x) where (y,x) are the rectangular grid coordinates.


#(0,0) pixel is hardcoded to the exact values from Toolik for testing.

def make_run_mask(filename, sizey=10, sizex=10):
  '''Generate a file representing the run mask'''

  print "Creating a run_mask file, %s by %s pixels." % (sizey, sizex)
  ncfile = netCDF4.Dataset(filename, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)
  run = ncfile.createVariable('run', np.int, ('Y', 'X',))

  print " --> NOTE: Turning off all pixels except 0,0."
  run[:] = np.zeros((sizey, sizex))
  run[0,0] = 1
    
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

  new_ncfile.close()


def create_template_drainage_file(fname, sizey=10, sizex=10):
  '''Generate a template file for drainage classification.'''
  print "Creating an empty drainage classification file, %s by %s pixels. (%s)" % (sizey, sizex, os.path.basename(fname))
  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)
  drainage_class = ncfile.createVariable('drainage_class', np.int, ('Y', 'X',))

  ncfile.close()


def create_template_restart_nc_file(filename, sizex=10, sizey=10):
  '''Creates an empty restart file that can be used as a template?'''
  print "Creating an empty restart file: ", filename
  ncfile = netCDF4.Dataset(filename, mode='w', format='NETCDF4')

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

  ncfile.close()

def create_template_fri_fire_file(fname, sizey=10, sizex=10, rand=None):
  print "Creating an FRI fire file, %s by %s pixels. Fill with random data?: %s" % (sizey, sizex, rand)
  print "Opening/Creating file: ", fname

  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)

  severity = ncfile.createVariable('severity', np.int32, ('Y','X'))
  fri = ncfile.createVariable('fri', np.int32, ('Y','X',))

  # not sure if we need these...
  #fri_day = ncfile.createVariable('fri_day_of_burn', np.int, ('Y','X'))
  #fri_area = ncfile.createVariable('fri_area_of_burn', np.float32, ('Y','X'))

  ncfile.close()


def create_template_explicit_fire_file(fname, sizey=10, sizex=10, rand=None):
  print "Creating a fire file, %s by %s pixels. Fill with random data?: %s" % (sizey, sizex, rand)
  print "Opening/Creating file: ", fname

  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)
  time = ncfile.createDimension('time', None)

  explicit_fire_year = ncfile.createVariable('explicit_fire_year', np.int, ('time', 'Y', 'X',))

  severity = ncfile.createVariable('severity', np.int32, ('time', 'Y','X'))

  # not sure if we need these yet...
  #f_day = ncfile.createVariable('day_of_burn', np.int, ('time', 'Y', 'X'))
  #f_area = ncfile.createVariable('area_of_burn', np.float32, ('time', 'Y', 'X'))

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

  ncfile.close()

def create_template_soil_texture_nc_file(fname, sizey=10, sizex=10):
  print "Creating a soil texture classification file, %s by %s pixels." % (sizey, sizex)

  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)
  pct_sand = ncfile.createVariable('pct_sand', np.float32, ('Y','X'))
  pct_silt = ncfile.createVariable('pct_silt', np.float32, ('Y','X'))
  pct_clay = ncfile.createVariable('pct_clay', np.float32, ('Y','X'))

  ncfile.close()



def fill_veg_file(if_name, xo, yo, xs, ys, out_dir, of_name):
  '''Read subset of data from .tif into netcdf file for dvmdostem. '''

  of_stripped = os.path.basename(of_name);

  # Create place for data
  create_template_veg_nc_file(of_name, sizey=ys, sizex=xs, rand=None)

  # Translate and subset to temporary location
  temporary = os.path.join('/tmp', of_stripped)

  if not os.path.exists( os.path.dirname(temporary) ):
    os.makedirs(os.path.dirname(temporary))

  subprocess.call(['gdal_translate', '-of', 'netcdf', '-srcwin', str(xo), str(yo), str(xs), str(ys), if_name, temporary])

  # Copy from temporary location to into the placeholde file we just created
  with netCDF4.Dataset(temporary) as t1, netCDF4.Dataset(of_name, mode='a') as new_vegdataset:
    veg_class = new_vegdataset.variables['veg_class']
    veg_class[:] = t1.variables['Band1'][:]

def fill_climate_file(start_yr, yrs, xo, yo, xs, ys, out_dir, of_name, sp_ref_file, in_tair_base, in_prec_base, in_rsds_base, in_vapo_base):
  # TRANSLATE TO NETCDF
  #Create empty file to copy data into
  create_template_climate_nc_file(os.path.join(out_dir, of_name), sizey=ys, sizex=xs)

  tmpfile = '/tmp/temporary-file-with-spatial-info.nc'
  smaller_tmpfile = '/tmp/smaller-temporary-file-with-spatial-info.nc'
  print "Creating a temporary file with LAT and LON variables: ", tmpfile
  check_call([
      'gdal_translate', '-of', 'netCDF', '-co', 'WRITE_LONLAT=YES',
      sp_ref_file,
      tmpfile
    ])
  print "Finished creating temporary file with spatial info."

  #from IPython import embed; embed()
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
  new_climatedataset = netCDF4.Dataset(os.path.join(out_dir, of_name), mode='a')

  # Insert lat/lon from temp file into the new file
  lat = new_climatedataset.variables['lat']
  lon = new_climatedataset.variables['lon']
  lat[:] = temp_subset_with_lonlat.variables['lat']
  lon[:] = temp_subset_with_lonlat.variables['lon']

  new_climatedataset.close()
  temp_subset_with_lonlat.close()
  print "Done copying LON/LAT."

  #Populate input file with data from TIFs
  with netCDF4.Dataset(os.path.join(out_dir, of_name), mode='a') as new_climatedataset:

    for yridx, year in enumerate( range(start_yr, start_yr + yrs)) : ## ??? How is args in scope here???

      for midx, month in enumerate(range(1,13)): # Note 1 based month!

        print year, month

        in_tair = in_tair_base + "_%02d_%04d.tif" % (month, year)
        in_prec = in_prec_base + "_%02d_%04d.tif" % (month, year)
        in_rsds = in_rsds_base + "_%02d_%04d.tif" % (month, year)
        in_vapo = in_rsds_base + "_%02d_%04d.tif" % (month, year)

        # TRANSLATE TO NETCDF
        print "Converting tif --> netcdf..."
        check_call(['gdal_translate', '-of', 'netCDF',
              in_tair,
              '/tmp/script-temporary_tair.nc'])

        check_call(['gdal_translate', '-of', 'netCDF',
              in_rsds,
              '/tmp/script-temporary_rsds.nc'])

        check_call(['gdal_translate', '-of', 'netCDF',
              in_prec,
              '/tmp/script-temporary_pr.nc'])

        check_call(['gdal_translate', '-of', 'netCDF',
              in_vapo,
              '/tmp/script-temporary_vapo.nc'])

        print "Subsetting...."
        check_call(['gdal_translate', '-of', 'netCDF', '-srcwin',
              str(xo), str(yo), str(xs), str(ys),
              '/tmp/script-temporary_tair.nc', '/tmp/script-temporary_tair2.nc'])

        check_call(['gdal_translate', '-of', 'netCDF', '-srcwin',
              str(xo), str(yo), str(xs), str(ys),
              '/tmp/script-temporary_rsds.nc', '/tmp/script-temporary_rsds2.nc'])

        check_call(['gdal_translate', '-of', 'netCDF', '-srcwin',
              str(xo), str(yo), str(xs), str(ys),
              '/tmp/script-temporary_pr.nc', '/tmp/script-temporary_pr2.nc'])

        check_call(['gdal_translate', '-of', 'netCDF', '-srcwin',
              str(xo), str(yo), str(xs), str(ys),
              '/tmp/script-temporary_vapo.nc', '/tmp/script-temporary_vapo2.nc'])


        print "Writing subset's data to new files..."
        with netCDF4.Dataset('/tmp/script-temporary_tair2.nc', mode='r') as t2:
          tair = new_climatedataset.variables['tair']
          tair[yridx*12+midx] = t2.variables['Band1'][:]

        with netCDF4.Dataset('/tmp/script-temporary_rsds2.nc', mode='r') as t2:
          nirr = new_climatedataset.variables['nirr']
          nirr[yridx*12+midx] = t2.variables['Band1'][:]

        with netCDF4.Dataset('/tmp/script-temporary_pr2.nc', mode='r') as t2:
          prec = new_climatedataset.variables['precip']
          prec[yridx*12+midx] = t2.variables['Band1'][:]

        with netCDF4.Dataset('/tmp/script-temporary_vapo2.nc', mode='r') as t2:
          vapo = new_climatedataset.variables['vapor_press']
          vapo[yridx*12+midx] = t2.variables['Band1'][:]

        print "Done appending. Closing the new file"

    print "Done with year loop."

  print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
  print "%% NOTE! Converting rsds (nirr) from MJ/m^2/day to W/m^2!"
  print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
  with netCDF4.Dataset(os.path.join(out_dir, of_name), mode='a') as new_climatedataset:
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

def fill_fri_fire_file(if_name, xo, yo, xs, ys, out_dir, of_name):
  create_template_fri_fire_file(of_name, sizey=ys, sizex=xs, rand=False)

  print "FILLING FRI FIRE FILE WITH 'REAL' DATA IS NOT IMPLEMENTED YET!"

  with netCDF4.Dataset(of_name, mode='a') as nfd:

    print "==> fill with random severity..."
    nfd.variables['severity'][:,:] = np.random.randint(0,5,(ys,xs))

    print "==> set arbitrary fri values (same for all pixels; for easy testing)..."
    nfd.variables['fri'][:,:] = 5

def fill_explicit_fire_file(if_name, xo, yo, xs, ys, out_dir, of_name):
  create_template_explicit_fire_file(of_name, sizey=ys, sizex=xs, rand=False)

  print "FILLING EXPLICIT FIRE FILE WITH 'REAL' DATA IS NOT IMPLEMENTED YET!"

  with netCDF4.Dataset(of_name, mode='a') as nfd:

    print "==> fill with random fire years...";
    nfd.variables['explicit_fire_year'][:,:,:] = np.random.randint(0, 2, (100,ys,xs))

    print "==> fill with random severity..."
    nfd.variables['severity'][:,:,:] = np.random.randint(0, 5, (100,ys,xs))

    print "NOTE: with this arrangement, it is possible to have a year ",
    print " that is tagged for fire (explicit_fire_year==1) but a severity of 0!"


def main(start_year, years, xo, yo, xs, ys, tif_dir, out_dir, files=[]):

  if 'fri_fire' in files:
    of_name = os.path.join(out_dir, "fri_fire.nc")
    fill_fri_fire_file(tif_dir + "iem_ancillary_data/Fire/", xo, yo, xs, ys, out_dir, of_name)

  if 'explicit_fire' in files:
    of_name = os.path.join(out_dir, "explicit_fire.nc")
    fill_explicit_fire_file(tif_dir + "iem_ancillary_data/Fire/", xo, yo, xs, ys, out_dir, of_name)

  if 'veg' in files:
    of_name = os.path.join(out_dir, "vegetation.nc")
    fill_veg_file(os.path.join(tif_dir,  "iem_ancillary_data/Landcover/LandCover_iem_TEM_2005.tif"), xo, yo, xs, ys, out_dir, of_name)

  if 'drain' in files:
    of_name = os.path.join(out_dir, "drainage.nc")
    fill_drainage_file(os.path.join(tif_dir,  "iem_ancillary_data/soil_and_drainage/Lowland_1km.tif"), xo, yo, xs, ys, out_dir, of_name)

  if 'soil_texture' in files:
    of_name = os.path.join(out_dir, "soil_texture.nc")
    in_sand_base = os.path.join(tif_dir,  "iem_ancillary_data/soil_and_drainage/iem_domain_hayes_igbp_pct_sand.tif")
    in_silt_base = os.path.join(tif_dir,  "iem_ancillary_data/soil_and_drainage/iem_domain_hayes_igbp_pct_silt.tif")
    in_clay_base = os.path.join(tif_dir,  "iem_ancillary_data/soil_and_drainage/iem_domain_hayes_igbp_pct_clay.tif")


    fill_soil_texture_file(in_sand_base, in_silt_base, in_clay_base, xo, yo, xs, ys, out_dir, of_name, rand=False)

  if 'run_mask' in files:
    make_run_mask(os.path.join(out_dir, "run-mask.nc"), sizey=ys, sizex=xs)

  if 'co2' in files:
    make_co2_file(os.path.join(out_dir, "co2.nc"))

  if 'hist_climate' in files:
    of_name = "historic-climate.nc"
    sp_ref_file  = os.path.join(tif_dir,  "tas_mean_C_iem_cru_TS31_1901_2009/tas_mean_C_iem_cru_TS31_%02d_%04d.tif" % (1, 1901))
    in_tair_base = os.path.join(tif_dir,  "tas_mean_C_iem_cru_TS31_1901_2009/tas_mean_C_iem_cru_TS31")
    in_prec_base = os.path.join(tif_dir,  "pr_total_mm_iem_cru_TS31_1901_2009/pr_total_mm_iem_cru_TS31")
    in_rsds_base = os.path.join(tif_dir,  "rsds_mean_MJ-m2-d1_iem_cru_TS31_1901_2009/rsds_mean_MJ-m2-d1_iem_cru_TS31")
    in_vapo_base = os.path.join(tif_dir,  "vap_mean_hPa_iem_cru_TS31_1901_2009/vap_mean_hPa_iem_cru_TS31")

    #Calculates number of years for running all. Values are different
    #  for historic versus projected.
    hc_years = 0
    if years == -1:
      filecount = len(glob.glob(os.path.join(tif_dir,  "/tas_mean_C_iem_cru_TS31_1901_2009/*.tif")))
      hc_years = filecount/12 
    else:
      hc_years = years

    fill_climate_file(1901+start_year, hc_years, xo, yo, xs, ys, out_dir, of_name, sp_ref_file, in_tair_base, in_prec_base, in_rsds_base, in_vapo_base)


  if 'proj_climate' in files:
    of_name = "projected-climate.nc"
    sp_ref_file  = os.path.join(tif_dir,  "tas_mean_C_iem_cccma_cgcm3_1_sresa1b_2001_2100/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_%02d_%04d.tif" % (1, 2001))
    in_tair_base = os.path.join(tif_dir,  "tas_mean_C_iem_cccma_cgcm3_1_sresa1b_2001_2100/tas_mean_C_iem_cccma_cgcm3_1_sresa1b")
    in_prec_base = os.path.join(tif_dir,  "pr_total_mm_iem_cccma_cgcm3_1_sresa1b_2001_2100/pr_total_mm_iem_cccma_cgcm3_1_sresa1b")
    in_rsds_base = os.path.join(tif_dir,  "rsds_mean_MJ-m2-d1_iem_cccma_cgcm3_1_sresa1b_2001_2100/rsds_mean_MJ-m2-d1_iem_cccma_cgcm3_1_sresa1b")
    in_vapo_base = os.path.join(tif_dir,  "vap_mean_hPa_iem_cccma_cgcm3_1_sresa1b_2001_2100/vap_mean_hPa_iem_cccma_cgcm3_1_sresa1b")

    #Calculates number of years for running all. Values are different
    #  for historic versus projected.
    pc_years = 0;
    if years == -1:
      filecount = len(glob.glob(tif_dir + "/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_2001_2100/*.tif"))
      pc_years = filecount/12
    else:
      pc_years = years

    fill_climate_file(2001+start_year, pc_years, xo, yo, xs, ys, out_dir, of_name, sp_ref_file, in_tair_base, in_prec_base, in_rsds_base, in_vapo_base)

  if 'hist_fire' in files:
    of_name = "historic-fire.nc"
    in_fire_base = os.path.join(tif_dir, "iem_ancillary_data/Fire/")

    print "Filling with RANDOM DATA!!"
    fill_fire_file2(1900, years, xo, yo, xs,ys, out_dir, of_name, rand=True)

  if 'proj_fire' in files:
    of_name = "projected-fire.nc"
    in_fire_base = os.path.join(tif_dir, "iem_ancillary_data/Fire/")

    print "Filling with RANDOM DATA!!"
    fill_fire_file2(2001, years, xo, yo, xs,ys, out_dir, of_name, rand=True)

  print "DONE"






if __name__ == '__main__':

  parser = argparse.ArgumentParser(
    formatter_class = argparse.RawDescriptionHelpFormatter,

      description=textwrap.dedent('''\
        Creates a set of files for dvm-dos-tem.

        <OUTDIR>/<TAG>_<YSIZE>x<XSIZE>/fire.nc
                                  ... /vegetation.nc
                                  ... /drainage.nc
                                  ... /historic-climate.nc
                                  ... /projected-climate.nc
                                  ... /co2.nc
                                  ... /historic-fire.nc
                                  ... /run-mask.nc

        <OUTDIR>/<TAG>_<YSIZE>x<XSIZE>/output/restart-eq.nc

        Assumes a certain layout for the source files. At this point, the 
        source files are generally .tifs that have been created for the IEM
        project.
        '''),

      epilog=textwrap.dedent(''''''),
  )
  
  parser.add_argument('--crtf-only', action="store_true",
                      help="Only create the restart template file.")

  parser.add_argument('--tifs', default="../../snap-data",
                      help="Directory containing input TIF directories.")

  parser.add_argument('--outdir', default="some-dvmdostem-inputs",
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

  parser.add_argument('--which', default=['all'],
                      help="which files to create (default: %(default)s)", choices=['all', 'veg', 'fri_fire', 'explicit_fire', 'drain', 'soil_texture', 'run_mask', 'co2', 'hist_climate', 'proj_climate',])

  print "Parsing command line arguments";
  args = parser.parse_args()
  print "args: ", args

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
    which_files = ['veg', 'fri_fire', 'explicit_fire', 'drain', 'soil_texture', 'run_mask', 'co2', 'hist_climate', 'proj_climate']

  main(start_year, years, xo, yo, xs, ys, tif_dir, out_dir, files=which_files)
