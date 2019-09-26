#!/usr/bin/env python

# T.Carman June 2019
# Experimenting with keeping grid mapping with input files and plotting.

import csv
import os
import subprocess
import netCDF4 as nc
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.colors
from mpl_toolkits.basemap import Basemap

import rasterio
import pyproj

import input_util as iu

def pretty_print_crs(crs):
  print crs.is_projected
  print crs.data
  print crs.to_proj4()
  print crs.to_wkt()
  print "-->", tif_crs.to_epsg()
  print crs.keys()
  print crs.is_projected
  print crs.values()
  print meta


sites = []
with open("/home/vagrant/RegionalSoilValidation_SiteCoordinates_NorthSlope.csv") as myfile:
    reader = csv.DictReader(myfile)
    for r in reader:
        sites.append(r)
        
#### THE MAIN INPUT VEG FILE ####
veg_tiff = '/home/vagrant/atlas_original_snap_data/ancillary/land_cover/v_0_4/iem_vegetation_model_input_v0_4.tif'
veg_nc = os.path.splitext(veg_tiff)[0]+'.nc'

# Read the tif and collect the tif_metadata
with rasterio.open(veg_tiff) as src:
  tif_meta = src.meta
  tif_data = src.read(1, masked=True)
  tif_colormap = src.colormap(1)

# Convert tif to netcdf
if os.path.exists(veg_nc):
    print "NOTE: Overwriting ", veg_nc
subprocess.call([ 'gdal_translate', '-of','netcdf','-co','WRITE_LONLAT=YES', veg_tiff, veg_nc])


# Open netcdf data. 2 ways to do this:
#  1. rasterio - advantage is that the geo ref info will come in the same way as the tif
#  2. netCDF4 - advantage is that we get normal access to the netcdf file (variables, attributes, dimensions, etc)
with rasterio.open('netcdf:{}:Band1'.format(veg_nc)) as nc_rds:
  nc_meta = nc_rds.meta
  nc_data = nc_rds.read()

# Open netcdf
with nc.Dataset(veg_nc, 'r') as ds:
  nc_latv = ds.variables['lat'][:]
  nc_lonv = ds.variables['lon'][:]

tif_crs = tif_meta['crs']
nc_crs = nc_meta['crs']

#pretty_print_crs(tif_crs)
#pretty_print_crs(nc_crs)  


# Extract shape/extent of the raster from its crs
map_width = tif_meta['width'] * tif_meta['transform'][0]
map_height = tif_meta['height'] * tif_meta['transform'][0]
xmin = tif_meta['transform'][2]
xmax = xmin + map_width
ymax = tif_meta['transform'][5]
ymin = ymax - map_height
llproj = (xmin, ymin)
urproj = (xmax, ymax)
extent = [xmin, xmax, ymin, ymax] # [left, right, bottom, top]
print llproj


# Instantiate projection class and compute longlat coordinates of
# the raster's ll and ur corners
tif_crs = tif_meta['crs']
p = pyproj.Proj(**tif_crs)
llll = p(*llproj, inverse=True)
urll = p(*urproj, inverse=True)


# Set up the color map...
print tif_colormap
a = np.array([v for k, v in tif_colormap.iteritems()])
print a.shape, a.max(), a.min()
a = a/255.0
cm = matplotlib.colors.ListedColormap(a[0:13])#

#color_map = plt.cm.get_cmap('tab20', 12)
#cm.colors



# From SNAP website, tif_metadata
CMTs = [
  (0, 'Not Modeled'),
  (1 ,'Black Spruce Forest'),
  (2 ,'White Spruce Forest'),
  (3 ,'Deciduous Forest'),
  (4 ,'Shrub Tundra'),
  (5 ,'Graminoid Tundra'),
  (6 ,'Wetland Tundra'),
  (7 ,'Barren lichen-moss'),
  (8 ,'Heath'),
  (9 ,'Maritime Upland Forest'),
  (10,'Maritime Forested Wetland'),
  (11,'Maritime Fen'),
  (12,'Maritime Alder Shrubland')
]


def overlay_subregion(fpath, map_inst):

  #fpath="/home/vagrant/small_region.nc"

  with rasterio.open('netcdf:{}:Band1'.format(fpath)) as nc_rds:
    meta = nc_rds.meta
    data = nc_rds.read(1)

  print data.shape
  with nc.Dataset(fpath, 'r') as ds:
    latv = ds.variables['lat'][:]
    lonv = ds.variables['lon'][:]
    # netcdf shape will be something like (1, rows, cols), or (1, height, width)

  # Figure out the shape and extent of the raster from the CRS
  map_width = meta['width'] * meta['transform'][0]
  map_height = meta['height'] * meta['transform'][0]
  xmin = meta['transform'][2]
  xmax = xmin + map_width
  ymax = tif_meta['transform'][5]
  ymin = ymax - map_height
  llproj = (xmin, ymin)
  urproj = (xmax, ymax)
  extent = [xmin, xmax, ymin, ymax] # [left, right, bottom, top]

  print map_width,map_height
  print xmin, xmax
  print ymin, ymax
  print llproj
  print urproj
  print extent

  # Instantiate projection class and compute longlat coordinates of
  # the raster's ll and ur corners
  crs = meta['crs']
  p = pyproj.Proj(**crs)
  llll = p(*llproj, inverse=True)
  urll = p(*urproj, inverse=True)
  print "sro ll: ", llll
  print "sro ur:", urll

  xi,yi = map_inst(lonv,latv)
  sro = map_inst.scatter(xi,yi[::-1], zorder=5001, c=data, cmap=cm, alpha=1.0)  ### <---- ?????? reversing the y coords makes it all look right??
  #sro = map_inst.imshow(data, origin='upper', extent=OE, zorder=5000, alpha=1, cmap=plt.cm.get_cmap('tab20', 12))

#gdal_translate -of netcdf -srcwin 361 2023 25 25 -co WRITE_LONLAT=YES ../atlas_original_snap_data/ancillary/land_cover/v_0_4/iem_vegetation_model_input_v0_4.nc ~/small_region.nc

#((2363-2023)-25)+1
#gdal_translate -of netcdf -srcwin 361 316 25 25 -co WRITE_LONLAT=YES ../atlas_original_snap_data/ancillary/land_cover/v_0_4/iem_vegetation_model_input_v0_4.nc ~/small_region.nc

#361 316
#m.plot(*(m(nc_lonv[2210,1097], nc_latv[2210,1097])), marker='^', markersize=50,zorder=3000,color='red')




#import ipywidgets
#debug_view = ipywidgets.Output(layout={'border': '1px solid black'})


# Start plotting....
fig = plt.figure(figsize=(6,6), dpi=80, facecolor='w', edgecolor='k')
ax1 = plt.subplot(111)

# Instantiate Basemap class
m = Basemap(llcrnrlon=llll[0], llcrnrlat=llll[1], urcrnrlon=urll[0], urcrnrlat=urll[1],
            #projection=tif_crs.to_proj4(),
            epsg=tif_crs.to_epsg(),
            resolution='l', 
            #lat_0=tif_crs['lat_0'], lon_0=tif_crs['lon_0']
            width=2800000, lon_0=-145, lat_0=63, ax=ax1)
            # There might be other parameters to set depending on your crs


print "Lower left (ll) = ????", m(llproj, urproj, inverse=True) # Get lat, lon in decimal degrees from projected coords

# Get the sites in projected coords from the lon/lat in decimal degrees
#sitex_projmapcoords, sitey_projmapcoords = m([float(d['lon']) for d in sites], [float(d['lat']) for d in sites])


# Projected map coordinates
sitex_projmapcoords, sitey_projmapcoords = m([float(d['lon']) for d in sites], [float(d['lat']) for d in sites])

# From the csv file (user supplied)
site_lon, site_lat = [float(d['lon']) for d in sites], [float(d['lat']) for d in sites]

# Round trip: csv file to Basemap instance (projected coords), back to lat/lon
sitey_lon_rt, sitex_lat_rt = m(sitex_projmapcoords, sitey_projmapcoords, inverse=True) 

# pixel offsets to be (understood) and passed to gdal_translate
#sitex_ix, sitey_iy           

# matplotib figure coordinates from corner of page?
#sitex_figx, sitey_figy       


# draw coasts and fill continents.
m.drawmapboundary(fill_color=None)
m.drawcoastlines(linewidth=0.5, zorder=999)
#m.fillcontinents(color='purple',lake_color='aqua')

# PLot raster
iem_vegclass_img = m.imshow(tif_data, origin='upper', extent=extent, cmap=cm, zorder=100, alpha=1.0)
cbar = m.colorbar(iem_vegclass_img)

tick_locs = (np.arange(len(CMTs)) + 0.5)*(len(CMTs)-1)/len(CMTs)
cbar.set_ticks(tick_locs)
cbar.set_ticklabels(zip(*CMTs)[1])


# Plot the sites of interest
# not sure abotue this one? # m.plot(sitex_projmapcoords, sitey_projmapcoords, color='black')
#for x, y in zip(sitex_projmapcoords, sitey_projmapcoords):
#    m.plot(x, y, color='black', zorder=1000, picker=20, alpha=.7, marker='o')
sites_coll = m.scatter(sitex_projmapcoords, sitey_projmapcoords, color=[(0,0,0) for i in sitex_projmapcoords], zorder=1000, picker=10, alpha=.70)

# draw parallels and meridians.
parallels = np.arange(0.,81,5.)
meridians = np.arange(10.,351.,5.)
# labels = [left,right,top,bottom]
m.drawparallels(parallels,labels=[True,False,False,False], zorder=1000)
m.drawmeridians(meridians,labels=[False,False,False,True], zorder=1000)






#gdal_translate -of netcdf -srcwin 361 2023 25 25 -co WRITE_LONLAT=YES ../atlas_original_snap_data/ancillary/land_cover/v_0_4/iem_vegetation_model_input_v0_4.nc ~/small_region.nc

#((2363-2023)-25)+1
#gdal_translate -of netcdf -srcwin 361 316 25 25 -co WRITE_LONLAT=YES ../atlas_original_snap_data/ancillary/land_cover/v_0_4/iem_vegetation_model_input_v0_4.nc ~/small_region.nc

#361 316
#m.plot(*(m(nc_lonv[2210,1097], nc_latv[2210,1097])), marker='^', markersize=50,zorder=3000,color='red')



#@debug_view.capture(clear_output=True)
def onpick0(event):
  print event
  print vars(event)

  if len(event.ind) > 1:
    print "YOU HIT MORE THAN ONE POINT!!"

  SIZE = 25

  print "{:>10s} {:>7s} {:>9s} {:>7s} {:>7s}   {:>7s} {:>7s}".format('event.ind', 'lat', 'lon', 'iy' , 'ix', 'iy_alt', 'ix')
  for (ei, lat, lon) in zip(event.ind, np.array(site_lat)[event.ind], np.array(site_lon)[event.ind]):

    iy, ix = iu.tunnel_fast(nc_latv, nc_lonv, lat, lon)

    iy_alt = (nc_meta['height'] - iy) - SIZE

    print "{:>10d} {:>2.4f} {:>4.4f} {:>7d} {:>7d}   {:>7d} {:>7d}".format(ei, lat,lon, iy,ix, iy_alt,ix)

  print ""


  #from IPython import embed; embed()

  iu.cropper(ix, iy_alt, SIZE, SIZE, 
          input_file='../atlas_original_snap_data/ancillary/land_cover/v_0_4/iem_vegetation_model_input_v0_4.tif',
          output_file='/home/vagrant/small_region.nc')
 
  overlay_subregion("/home/vagrant/small_region.nc", m)

  artist = event.artist

  # set everythign black
  sites_coll._facecolors[:] = (254,254,254,.7)

  # set only the picked artists to something bright
  sites_coll._facecolors[event.ind] = (254,34,1,1)



    

pid = fig.canvas.mpl_connect('pick_event', onpick0)
plt.show()
#plt.savefig('figure_name.png',dpi=100, transparent=True)


  '''
      fig_coords    map_proj_coords      lonlat
  x:         235      45334534534.3      -147.2
  y:         123      43534534511.5      63.2

  '''

  '''
                     X       Y
       fig_coords   235
  map_proj_coords  
      data_coords
    lonlat_coords
  '''


  '''
  site,lon,lat,mpcoords_x,mpcoords_y,figcoords_x,figcoords_y,


  '''
  #from IPython import embed; embed()

  # header = "{:>10}{:>6}{:>6}{:>14}{:>14}{:>14}{:>14}".format(*('site,lon,lat,mpcoords_x,mpcoords_y,figcoords_x,figcoords_y'.split(',')))

  # #zip( np.array(site_lon)[event.ind], np.array(site_lat)[event.ind], np.array(sitex_projmapcoords)[event.ind], np.array(sitey_projmapcoords)[event.ind])

  # #zip(np.array(sitex_projmapcoor))

  # #np.array(sitex_projmapcoords)[event.ind]

  # # for l in ax1.lines:
  # #     l.set_color('black')
  # # artist.set_color('red')

  # x,y = event.mouseevent.x, event.mouseevent.y                           # in pixel coords from axes/figure
  # xd, yd = event.mouseevent.xdata, event.mouseevent.ydata                # data coords (map projections)
  # lonpt, latpt = m(xd,yd,inverse=True)             # lat and lon of click
  # #iy, ix = kdtree_fast(lats, lons, latpt, lonpt)   # nearest px offsets?
  # print '''x:{}, y:{}
  # xdata:{}, ydata={}
  # lonpt:{}, latpt:{}
  # '''.format(x,y,xd,yd, lonpt, latpt)
  # print ""
  # plt.draw()
  # from IPython import embed; embed()    
  #artist.set_color('red')







#####################
with open("FYEAH.csv", 'w') as myfile:
    myfile.write('''site,lat,lon,d_lat,d_lon,info
CALM_56_Mile,69.6969,-148.6821,-0.000396142578126,-0.00746315917968,target@ LL of cropped region iy_fUL=(179-YSIZE)+1  ix=947
CALM_Atqasuk,70.45,-157.4,0.00441284179688,0.00699768066406,target@ LL of cropped region iy_fUL=(102-YSIZE)+1  ix=608
CALM_Awuna,69.166667,-158.016667,0.00113202685547,0.00780809765624,target@ LL of cropped region iy_fUL=(241-YSIZE)+1  ix=576
CALM_Barrow,71.316667,-156.6,-0.00330980664063,0.0122741699219,target@ LL of cropped region iy_fUL=(8-YSIZE)+1  ix=642
CALM_Barrow_CRREL_Plots,71.316667,-156.583333,-0.0036683881836,0.00168897265624,target@ LL of cropped region iy_fUL=(8-YSIZE)+1  ix=643
CALM_Betty_Pingo_1_km_grid,70.283333,-148.866667,-0.00407392138672,-0.0138227617188,target@ LL of cropped region iy_fUL=(115-YSIZE)+1  ix=935
CALM_Betty_Pingo_MNT,70.2835,-148.8928,0.00449304199219,-0.0119558837891,target@ LL of cropped region iy_fUL=(116-YSIZE)+1  ix=934
CALM_Betty_Pingo_WET,70.275,-148.919,0.00438537597657,-0.0101865234375,target@ LL of cropped region iy_fUL=(117-YSIZE)+1  ix=933
CALM_Chandalar_Shelf,68.066667,-149.583333,-0.000723441894536,0.00704480761718,target@ LL of cropped region iy_fUL=(361-YSIZE)+1  ix=923
CALM_Deadhorse,70.166667,-148.466667,0.000147834960941,-0.00342542285156,target@ LL of cropped region iy_fUL=(127-YSIZE)+1  ix=951
CALM_Drew_Point,70.866667,-153.916667,-0.00273302441406,-0.00358106249999,target@ LL of cropped region iy_fUL=(59-YSIZE)+1  ix=741
CALM_East_Teshekpuk,70.566667,-152.966667,0.00204602832031,-0.00223523730469,target@ LL of cropped region iy_fUL=(92-YSIZE)+1  ix=777
CALM_Fish_Creek,70.333333,-152.05,0.00424669628906,0.0106536865234,target@ LL of cropped region iy_fUL=(117-YSIZE)+1  ix=812
CALM_Franklin_Bluff,69.683333,-148.716667,0.00272997265625,0.0126878583984,target@ LL of cropped region iy_fUL=(181-YSIZE)+1  ix=945
CALM_Galbraith_Lake,68.483333,-149.5,0.00143755322266,-0.00755310058594,target@ LL of cropped region iy_fUL=(315-YSIZE)+1  ix=924
CALM_Happy_Valley,69.166667,-148.833333,0.0025053178711,0.00834180468749,target@ LL of cropped region iy_fUL=(238-YSIZE)+1  ix=945
CALM_Happy_Valley_1_km_grid,69.1,-148.5,0.000299072265619,0.00709533691406,target@ LL of cropped region iy_fUL=(244-YSIZE)+1  ix=959
CALM_Imnavait_Creek_1_km_grid,68.5,-149.5,3.81469726562e-05,-0.0108337402344,target@ LL of cropped region iy_fUL=(313-YSIZE)+1  ix=924
CALM_Imnavait_Creek_MAT,68.611,-149.30933,-0.00199133300781,-0.0113868847656,target@ LL of cropped region iy_fUL=(300-YSIZE)+1  ix=931
CALM_Imnavait_Creek_WET,68.611,-149.3145,-0.0026245727539,0.00768933105468,target@ LL of cropped region iy_fUL=(300-YSIZE)+1  ix=930
CALM_Inigok,70.0,-153.1,0.000755310058594,-0.00769958496093,target@ LL of cropped region iy_fUL=(154-YSIZE)+1  ix=773
CALM_Ivotuk_1_km_grid,68.483333,-155.733333,-0.00206433886719,0.00221692675782,target@ LL of cropped region iy_fUL=(320-YSIZE)+1  ix=666
CALM_Lupine_Hill,69.12883,-148.5928,-0.000976518554694,0.00711455078124,target@ LL of cropped region iy_fUL=(241-YSIZE)+1  ix=955
CALM_Marsh_Creek,69.783333,-144.8,-0.000236335937501,0.00436706542968,target@ LL of cropped region iy_fUL=(153-YSIZE)+1  ix=1097
CALM_Niguanak,69.883333,-142.983333,-0.00295850390626,-0.00826586132811,target@ LL of cropped region iy_fUL=(131-YSIZE)+1  ix=1166
CALM_Piksiksak,70.033333,-157.083333,0.00259416943359,0.0053663408203,target@ LL of cropped region iy_fUL=(148-YSIZE)+1  ix=618
CALM_Red_Sheep_Creek,68.683333,-144.833333,-0.000916877929683,-0.0116166914063,target@ LL of cropped region iy_fUL=(273-YSIZE)+1  ix=1113
CALM_Sagwon_Hills_MAT,69.401,-148.8056,0.000708557128902,0.0104705566406,target@ LL of cropped region iy_fUL=(212-YSIZE)+1  ix=944
CALM_Sagwon_Hills_MNT,69.441,-148.67033,-0.00100134277343,0.0105629443359,target@ LL of cropped region iy_fUL=(207-YSIZE)+1  ix=949
CALM_South_Meade,70.633333,-156.833333,0.00438097363281,-0.00827501660157,target@ LL of cropped region iy_fUL=(83-YSIZE)+1  ix=631
CALM_Toolik_1_km_grid,68.616667,-149.6,-0.00377825146484,-0.0109649658203,target@ LL of cropped region iy_fUL=(300-YSIZE)+1  ix=919
CALM_Toolik_LTER,68.616667,-149.6,-0.00377825146484,-0.0109649658203,target@ LL of cropped region iy_fUL=(300-YSIZE)+1  ix=919
CALM_Toolik_MAT,68.624,-149.61817,0.00295965576171,-0.00487349121093,target@ LL of cropped region iy_fUL=(300-YSIZE)+1  ix=918
CALM_Tunalik,70.2,-160.066667,0.00437469482422,0.0113359296875,target@ LL of cropped region iy_fUL=(122-YSIZE)+1  ix=504
CALM_Umiat,69.4,-152.15,-0.000665283203119,0.0105224609375,target@ LL of cropped region iy_fUL=(219-YSIZE)+1  ix=811
CALM_West_Dock_1_ha_grid,70.366667,-148.55,-0.00374773388671,-0.00433044433595,target@ LL of cropped region iy_fUL=(105-YSIZE)+1  ix=946
CALM_West_Dock_1_km_grid,70.366667,-148.566667,-0.00449541455077,0.00507982617188,target@ LL of cropped region iy_fUL=(105-YSIZE)+1  ix=945
SCAN_IkalukrokCreek,68.08,-163.0,-0.00182525634766,-0.00601196289062,target@ LL of cropped region iy_fUL=(340-YSIZE)+1  ix=361
SNOTEL_ATIGUNPASS,68.13,-149.48,0.00191009521484,0.00414611816407,target@ LL of cropped region iy_fUL=(354-YSIZE)+1  ix=927
SNOTEL_IMNAVIATCREEK,68.62,-149.3,-0.00202453613281,-0.0037811279297,target@ LL of cropped region iy_fUL=(299-YSIZE)+1  ix=931''')

# Trying to figure out how many bins the colormap needs.
# src = rasterio.open(veg_tiff)
# src.colormap(1)
# def gen_valid(d):
#     for k, v in d:
#         if sum(v)>255:
#             yield k, v
# cmts = gen_valid(src.colormap(1).iteritems())
# CMTS = [i for i in cmts]
# print len(CMTS)
# #for k, v in src.colormap(1).iteritems():
# #    if sum(v) > 255:
# #        print (k, v)
# #src.close()