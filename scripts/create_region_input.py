#!/usr/bin/env python


from subprocess import call

import argparse
import textwrap

import netCDF4
import numpy as np

from osgeo import gdal

#some description of what region wanted
#for now, keep to a rectangular requirement?
#Maintain CF and COARDS standards

#Select y,x or lat,lon bounding box coordinates for use


#Data should be in a rectangular (grid) layout
#NetCDF
#Conforms to CF & COARDS standards
#Geospatial information must be with the file. Each file should have variables for Lat and Lon each defined in terms of the dimensions of (y,x) where (y,x) are the rectangular grid coordinates.


#(0,0) pixel is hardcoded to the exact values from Toolik for testing.


def make_fire_dataset(fname, sizey=10, sizex=10):
  '''Generate a file representing fire information'''

  print "Creating a fire classification file, %s by %s pixels." % (sizey, sizex)
  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)
  fri = ncfile.createVariable('fri', np.int, ('Y','X',))
  fire_year_vector = ncfile.createVLType(np.int, 'fire_year_vector')
  fire_years = ncfile.createVariable('fire_years', fire_year_vector, ('Y','X'))
  fire_sizes = ncfile.createVariable('fire_sizes', fire_year_vector, ('Y','X'))

  print " --> NOTE: Filling FRI with random data!"
  fri[:] = np.random.uniform(low=1, high=7, size=(10, 10))

  print " --> NOTE: Setting FRI for pixel 0,0 to 1000!"
  fri[0,0] = 1000

  print " --> NOTE: Filling the fire_year and fire_sizes with random data!"
  yr_data = np.empty(sizey * sizex, object)
  sz_data = np.empty(sizey * sizex, object)
  for n in range(sizey * sizex):
    yr_data[n] = np.array(sorted(np.random.randint(1900, 2006, np.random.randint(0,10,1))), dtype=np.int)
    sz_data[n] = np.random.randint(0,100,len(yr_data[n]))
    #numpy.arange(random.randint(1,10),dtype='int32')+1
    
  yr_data = np.reshape(yr_data,(sizey,sizex))
  sz_data = np.reshape(sz_data,(sizey,sizex))

  print " --> NOTE: Check on a few pixels?"
  print "  (0,0)", yr_data[0,0], "-->", sz_data[0,0]
  print "  (0,1)", yr_data[0,1], "-->", sz_data[0,1]
  print "  (9,9)", yr_data[9,9], "-->", sz_data[9,9]
    
  fire_years[:] = yr_data
  fire_sizes[:] = sz_data

  ncfile.close()   


def make_veg_classification(fname, sizey=10, sizex=10):
  '''Generate a file representing veg classification.'''

  print "Creating a vegetation classification file, %s by %s pixels." % (sizey, sizex)
  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)
  veg_class = ncfile.createVariable('veg_class', np.int, ('Y', 'X',))

  print " --> NOTE: Filling with random data!"
  veg_class[:] = np.random.uniform(low=1, high=7, size=(10,10))

  print " --> NOTE: Setting pixel 0,0 to 4"
  veg_class[0,0] = 4
    
  ncfile.close()


def make_drainage_classification(fname, sizey=10, sizex=10):
  '''Generate a file representing drainage classification.'''
  print "Creating a drainage classification file, %s by %s pixels." % (sizey, sizex)
  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)
  drainage_class = ncfile.createVariable('drainage_class', np.int, ('Y', 'X',))

  print " --> NOTE: Filling with random data!"
  drainage_class[:] = np.random.uniform(low=1, high=7, size=(10,10))

  print " --> NOTE: Setting 0,0 pixel to zero!"
  drainage_class[0,0] = 0

  ncfile.close()


def make_run_mask(filename, sizey=10, sizex=10):
  '''Generate a file representing the run mask'''

  print "Creating a run_mask file, %s by %s pixels." % (sizey, sizex)
  ncfile = netCDF4.Dataset(filename, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)
  run = ncfile.createVariable('run', np.int, ('Y', 'X',))

  print " --> NOTE: Turning off all pixels except 0,0."
  run[:] = np.zeros((10,10))
  run[0,0] = 1
    
  ncfile.close()


def copy_co2_to_new_style(filename):
  '''Creates an co2 file for dvmdostem from the old sample data'''
  old_ncfile = netCDF4.Dataset("../DATA/test_single_site/dataregion/co2.nc", mode='r')
  new_ncfile = netCDF4.Dataset(filename, mode='w', format='NETCDF4')

  # Dimensions
  yearD = new_ncfile.createDimension('year', None) # append along time axis
    
  # Coordinate Variable
  yearV = new_ncfile.createVariable('year', np.int, ('year',))
    
  # Data Variables
  co2 = new_ncfile.createVariable('co2', np.float32, ('year',))
    
  yearV[:] = old_ncfile.variables['YEAR'][:]
  co2[:] = old_ncfile.variables['CO2'][:]
    
  old_ncfile.close()
  new_ncfile.close()


def create_empty_climate_nc_file(filename, sizey=10, sizex=10):
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



if __name__ == '__main__':

  parser = argparse.ArgumentParser(
    formatter_class = argparse.RawDescriptionHelpFormatter,

      description=textwrap.dedent('''\
        stuff
        '''),

      epilog=textwrap.dedent('''\
        '''),
  )

  parser.add_argument('--dim', default=10, type=int,
                      help="Width and height of square selection")

  parser.add_argument('--tifs', default="../../snap-data",
                      help="Directory containing input TIF directories")

  parser.add_argument('--outdir', default=".",
                      help="Directory for netCDF output files")

  parser.add_argument('--loc', default="Toolik",
                      help="Location of data set (for dir naming)")

  print "Parsing command line arguments";
  args = parser.parse_args()
  print args


  x_dim = args.dim;
  y_dim = args.dim;

  tif_dir = args.tifs;

  out_dir = args.outdir + '/' + args.loc + '_' + str(x_dim) + 'x' + str(y_dim);

#Pick bounding box coordinates to use with gdal_translate for subsetting the AIEM domain data files from SNAP. Current files from SNAP are Alaska Albers, 1km pixel size

#Specifying the "creation option" means that special variables will be written to the new netcdf file mapping row/column coordinates to lat/lon

#The following two calls must still be done manually

  lonlat_settings = '\"WRITE_LONLAT=YES\"'
  print lonlat_settings
 
#  call(['gdal_translate', '-of', 'netCDF', '-co', lonlat_settings,
#        tif_dir + '/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_2001_2100/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_01_2001.tif',
#        'sc_temporary_with_lonlat.nc']);

#  call(['gdal_translate', '-of', 'netCDF', '-co', '\"WRITE_LONLAT=YES\"',
#        'tas_mean_C_iem_cccma_cgcm3_1_sresa1b_01_2001.tif',
#        'sc_temporary_with_lonlat.nc']);

#  gdal_translate -of netCDF -co "WRITE_LONLAT=YES" \
#    -co GDAL_NETCDF_BOTTOMUP=YES -srcwin 915 292 10 10 \
#    temporary_with_lonlat.nc temp_subset_with_lonlat.nc



  call(['mkdir', out_dir]);


  make_fire_dataset(out_dir + "/script-new-fire-dataset.nc", sizey=y_dim, sizex=x_dim);

  make_veg_classification(out_dir + "/script-new-veg-dataset.nc", sizey=y_dim, sizex=x_dim);

  make_drainage_classification(out_dir + "/script-new-drainage-dataset.nc", sizey=y_dim, sizex=x_dim);

  make_run_mask(out_dir + "/script-run-mask.nc", sizey=y_dim, sizex=x_dim);

  #Copy CO2 data to a new file that follows proper standards/formatting
  copy_co2_to_new_style(out_dir + "/script-new-co2-dataset.nc");

  #Create empty file to copy data into
  create_empty_climate_nc_file(out_dir + "/script-projected-climate-dataset.nc", sizey=y_dim, sizex=x_dim);

####
  #Open the 'temporary' dataset
  temp_subset_with_lonlat = netCDF4.Dataset("temp_subset_with_lonlat.nc", mode='r')

  #Open the new file for appending
  new_climatedataset = netCDF4.Dataset(out_dir + "/script-projected-climate-dataset.nc", mode='a');

  #Insert lat/lon from temp file into the new file
  lat = new_climatedataset.variables['lat']
  lon = new_climatedataset.variables['lon']
  lat[:] = temp_subset_with_lonlat.variables['lat'][:]
  lon[:] = temp_subset_with_lonlat.variables['lon'][:]

  new_climatedataset.close()
  temp_subset_with_lonlat.close()
####

####
  YEARS=99
  #Populate input file with data from TIFs
  with netCDF4.Dataset(out_dir + '/script-projected-climate-dataset.nc', mode='a') as new_climatedataset:

    for yridx, year in enumerate(range(2001, 2001+YEARS)):
      for midx, month in enumerate(range (1,13)): # Note 1 based month!
        print year, month
        # TRANSLATE TO NETCDF
        # The curly braces are needed to run the shell command from w/in
        # ipython and have the variable exansion with year and month
        # work out alright
        print "Converting tif --> netcdf..."
        call(['gdal_translate', '-of', 'netCDF',
              tif_dir + '/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_2001_2100/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_%02d_%04d.tif' % (month,year),
              'script-temporary_tair.nc'])


        call(['gdal_translate', '-of', 'netCDF',
              tif_dir + '/rsds_mean_MJ-m2-d1_iem_cccma_cgcm3_1_sresa1b_2001_2100/rsds_mean_MJ-m2-d1_iem_cccma_cgcm3_1_sresa1b_%02d_%04d.tif' % (month, year),
              'script-temporary_rsds.nc'])

        call(['gdal_translate', '-of', 'netCDF',
              tif_dir + '/pr_total_mm_iem_cccma_cgcm3_1_sresa1b_2001_2100/pr_total_mm_iem_cccma_cgcm3_1_sresa1b_%02d_%04d.tif' % (month, year),
              'script-temporary_pr.nc'])

        call(['gdal_translate', '-of', 'netCDF',
              tif_dir + '/vap_mean_hPa_iem_cccma_cgcm3_1_sresa1b_2001_2100/vap_mean_hPa_iem_cccma_cgcm3_1_sresa1b_%02d_%04d.tif' % (month, year),
              'script-temporary_vapo.nc'])


        print "Subsetting...."
        call(['gdal_translate', '-of', 'netCDF', '-srcwin',
              '915', '292', '10', '10',
              'script-temporary_tair.nc', 'script-temporary_tair2.nc']);

        call(['gdal_translate', '-of', 'netCDF', '-srcwin',
              '915', '292', '10', '10',
              'script-temporary_rsds.nc', 'script-temporary_rsds2.nc']);

        call(['gdal_translate', '-of', 'netCDF', '-srcwin',
              '915', '292', '10', '10',
              'script-temporary_pr.nc', 'script-temporary_pr2.nc']);

        call(['gdal_translate', '-of', 'netCDF', '-srcwin',
              '915', '292', '10', '10',
              'script-temporary_vapo.nc', 'script-temporary_vapo2.nc']);


        print "Writing subset's data to new files..."
        with netCDF4.Dataset('script-temporary_tair2.nc', mode='r') as t2:
          # Grab the lat and lon from the temporary file
          tair = new_climatedataset.variables['tair']
          tair[yridx*12+midx] = t2.variables['Band1'][:]

        with netCDF4.Dataset('script-temporary_rsds2.nc', mode='r') as t2:
          # Grab the lat and lon from the temporary file
          nirr = new_climatedataset.variables['nirr']
          nirr[yridx*12+midx] = t2.variables['Band1'][:]
                
        with netCDF4.Dataset('script-temporary_pr2.nc', mode='r') as t2:
          # Grab the lat and lon from the temporary file
          prec = new_climatedataset.variables['precip']
          prec[yridx*12+midx] = t2.variables['Band1'][:]

        with netCDF4.Dataset('script-temporary_vapo2.nc', mode='r') as t2:
          # Grab the lat and lon from the temporary file
          vapo = new_climatedataset.variables['vapor_press']
          vapo[yridx*12+midx] = t2.variables['Band1'][:]
                
  print "Done appending. Closing the new file"
####

#end Main





