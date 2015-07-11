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
  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)

  fri = ncfile.createVariable('fri', np.int, ('Y','X',))
  fri[:] = np.random.uniform(low=1, high=7, size=(10, 10))
  fri[0,0] = 1000
    
  fire_year_vector = ncfile.createVLType(np.int, 'fire_year_vector')
  fire_years = ncfile.createVariable('fire_years', fire_year_vector, ('Y','X'))

  fire_sizes = ncfile.createVariable('fire_sizes', fire_year_vector, ('Y','X'))

  yr_data = np.empty(sizey * sizex, object)
  sz_data = np.empty(sizey * sizex, object)
  for n in range(sizey * sizex):
    yr_data[n] = np.array(sorted(np.random.randint(1900, 2006, np.random.randint(0,10,1))), dtype=np.int)
    sz_data[n] = np.random.randint(0,100,len(yr_data[n]))
    #numpy.arange(random.randint(1,10),dtype='int32')+1
    
  yr_data = np.reshape(yr_data,(sizey,sizex))
  sz_data = np.reshape(sz_data,(sizey,sizex))

  print yr_data[0,0], "-->", sz_data[0,0] 
  print yr_data[0,1], "-->", sz_data[0,1]
  print yr_data[9,9], "-->", sz_data[9,9]
    
  fire_years[:] = yr_data
  fire_sizes[:] = sz_data

  ncfile.close()   

#end make_fire_dataset

def make_veg_classification(fname, sizey=10, sizex=10):
  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)

  veg_class = ncfile.createVariable('veg_class', np.int, ('Y', 'X',))
  veg_class[:] = np.random.uniform(low=1, high=7, size=(10,10))
  veg_class[0,0] = 4
    
  ncfile.close()

#end make_veg_classification

def make_drainage_classification(fname, sizey=10, sizex=10):
  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)

  drainage_class = ncfile.createVariable('drainage_class', np.int, ('Y', 'X',))
  drainage_class[:] = np.random.uniform(low=1, high=7, size=(10,10))
  drainage_class[0,0] = 0
  ncfile.close()
#end make_drainage_classification


def make_run_mask(filename, sizey=10, sizex=10):
  ncfile = netCDF4.Dataset(filename, mode='w', format='NETCDF4')
  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)

  run = ncfile.createVariable('run', np.int, ('Y', 'X',))
  run[:] = np.zeros((10,10))
  run[0,0] = 1
    
  ncfile.close()
#end make_run_mask


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
#end copy_co2_to_new_style

def create_empty_climate_nc_file(filename, sizey=10, sizex=10):
    '''Creates an empty climate file for dvmdostem; y,x grid, time unlimited.'''
    
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
#end create_empty_climate_nc_file




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

  parser.add_argument('--dir', default="/vagrant/",
                      help="Directory containing input TIFs")

  print "Parsing command line arguments";
  args = parser.parse_args()
  print args

#Pick bounding box coordinates to use with gdal_translate for subsetting the AIEM domain data files from SNAP. Current files from SNAP are Alaska Albers, 1km pixel size

#Specifying the "creation option" means that special variables will be written to the new netcdf file mapping row/column coordinates to lat/lon

#  "../../snap-data/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_2001_2100/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_01_2001.tif"

#The following has the complete path.
#  call(["gdal_translate", " -of netCDF", " -co \"WRITE_LONLAT=YES\"", \
#        "../../snap-data/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_2001_2100/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_01_2001.tif", \
#        "sc_temporary_with_lonlat.nc"]);

#  call(["gdal_translate", " -of netCDF", " -co \"WRITE_LONLAT=YES\"", \
#        "tas_mean_C_iem_cccma_cgcm3_1_sresa1b_01_2001.tif", \
#        "sc_temporary_with_lonlat.nc"]);


#  src_data = gdal.open("tas_mean_C_iem_cccma_cgcm3_1_sresa1b_01_2001.tif")
#  driver = gdal.GetDriverByName("netCDF")
#  dst_data = driver.CreateCopy("sc_temp.nc", src_data, 0)

#  call("gdal_translate -of netCDF -co \"WRITE_LONLAT=YES\" ../../snap-data/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_2001_2100/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_01_2001.tif sc_temporary_with_lonlat.nc");



#  gdal_translate -of netCDF -co "WRITE_LONLAT=YES" \
#    -co GDAL_NETCDF_BOTTOMUP=YES -srcwin 915 292 10 10 \
#    temporary_with_lonlat.nc temp_subset_with_lonlat.nc

  x_dim = args.dim;
  y_dim = args.dim;

  make_fire_dataset("sc-new-fire-dataset.nc", sizey=y_dim, sizex=x_dim);

  make_veg_classification("sc-new-veg-dataset.nc", sizey=y_dim, sizex=x_dim);

  make_drainage_classification("sc-new-drainage-dataset.nc", sizey=y_dim, sizex=x_dim);

  make_run_mask("sc-run-mask.nc", sizey=y_dim, sizex=x_dim);

  #Copy CO2 data to a new file that follows proper standards/formatting
  copy_co2_to_new_style("sc-new-co2-dataset.nc");

  #Create empty file to copy data into
  create_empty_climate_nc_file("sc-new-climate-dataset.nc", sizey=y_dim, sizex=x_dim);

####
  #Open the 'temporary' dataset
  temp_subset_with_lonlat = netCDF4.Dataset("temp_subset_with_lonlat.nc", mode='r')

  #Open the new file for appending
  new_climatedataset = netCDF4.Dataset("sc-new-climate-dataset.nc", mode='a');

  #Insert lat/lon from temp file into the new file
  lat = new_climatedataset.variables['lat']
  lon = new_climatedataset.variables['lon']
  lat[:] = temp_subset_with_lonlat.variables['lat'][:]
  lon[:] = temp_subset_with_lonlat.variables['lon'][:]

  new_climatedataset.close()
  temp_subset_with_lonlat.close()
####

####
  #Populate new data file with data (for now, random)
  with netCDF4.Dataset("sc-new-climate-dataset.nc", mode='a') as new_climatedataset:
    YEARS = 10
    TIMESTEPS = YEARS*12

    #Write random junk data to the climate file
    sx = new_climatedataset.variables['X'].size
    sy = new_climatedataset.variables['Y'].size

    junkA = np.random.uniform(low=0.0, high=10, size=(TIMESTEPS*sy*sx)).reshape(TIMESTEPS, sy, sx)
    junkB = np.random.uniform(low=0.0, high=1300, size=(TIMESTEPS*sy*sx)).reshape(TIMESTEPS, sy, sx)
    junkC = np.random.uniform(low=0.0, high=20, size=(TIMESTEPS*sy*sx)).reshape(TIMESTEPS, sy, sx)

    new_climatedataset.variables['precip'][:] = junkA
    new_climatedataset.variables['nirr'][:] = junkB
    new_climatedataset.variables['vapor_press'][:] = junkC

####

####
  #Populate input file with data from TIFs
  with netCDF4.Dataset('new-climate-dataset.nc', mode='a') as new_climatedataset:

    for yridx, year in enumerate(range(2010, 2010+YEARS)):
      for midx, month in enumerate(range (1,13)): # Note 1 based month!
        print year, month
        # TRANSLATE TO NETCDF
        # The curly braces are needed to run the shell command from w/in
        # ipython and have the variable exansion with year and month
        # work out alright
        print "Converting tif --> netcdf..."
        print('gdal_translate -of netCDF /vagrant/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_2001_2100/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_' + str(month) + '_' + str(year) + '.tif sc-temporary_tair.nc')
        #call('gdal_translate -of netCDF /vagrant/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_2001_2100/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_' + str(month) + '_' + str(year) + '.tif sc-temporary_tair.nc')
        call("gdal_translate -of netCDF /vagrant/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_2001_2100/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_01_2010.tif sc-temporary_tair.nc")
        #gdal_translate -of netCDF {"/vagrant/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_2001_2100/tas_mean_C_iem_cccma_cgcm3_1_sresa1b_%02d_%04d.tif" % (month, year)} temporary_tair.nc

        #gdal_translate -of netCDF {"/vagrant/rsds_mean_MJ-m2-d1_iem_cccma_cgcm3_1_sresa1b_2001_2100/rsds_mean_MJ-m2-d1_iem_cccma_cgcm3_1_sresa1b_%02d_%04d.tif" % (month, year)} temporary_rsds.nc

        #gdal_translate -of netCDF {"/vagrant/pr_total_mm_iem_cccma_cgcm3_1_sresa1b_2001_2100/pr_total_mm_iem_cccma_cgcm3_1_sresa1b_%02d_%04d.tif" % (month, year)} temporary_pr.nc

        #gdal_translate -of netCDF {"/vagrant/vap_mean_hPa_iem_cccma_cgcm3_1_sresa1b_2001_2100/vap_mean_hPa_iem_cccma_cgcm3_1_sresa1b_%02d_%04d.tif" % (month, year)} temporary_vapo.nc


        print "Subsetting...."
        call('gdal_translate -of netCDF -srcwin 915 292 10 10 temporary_tair.nc sc-temporary_tair2.nc');
        #gdal_translate -of netCDF -srcwin 915 292 10 10 temporary_rsds.nc temporary_rsds2.nc
        #gdal_translate -of netCDF -srcwin 915 292 10 10 temporary_pr.nc temporary_pr2.nc
        #gdal_translate -of netCDF -srcwin 915 292 10 10 temporary_vapo.nc temporary_vapo2.nc

        print "Writing subset's data to new files..."
        with netCDF4.Dataset('temporary_tair2.nc', mode='r') as t2:
          # Grab the lat and lon from the temporary file
          tair = new_climatedataset.variables['tair']
          tair[yridx*12+midx] = t2.variables['Band1'][:]

        with netCDF4.Dataset('temporary_rsds2.nc', mode='r') as t2:
          # Grab the lat and lon from the temporary file
          nirr = new_climatedataset.variables['nirr']
          nirr[yridx*12+midx] = t2.variables['Band1'][:]
                
        with netCDF4.Dataset('temporary_pr2.nc', mode='r') as t2:
          # Grab the lat and lon from the temporary file
          prec = new_climatedataset.variables['precip']
          prec[yridx*12+midx] = t2.variables['Band1'][:]

        with netCDF4.Dataset('temporary_vapo2.nc', mode='r') as t2:
          # Grab the lat and lon from the temporary file
          vapo = new_climatedataset.variables['vapor_press']
          vapo[yridx*12+midx] = t2.variables['Band1'][:]
                
  print "Done appending. Closing the new file"
####

#end Main





