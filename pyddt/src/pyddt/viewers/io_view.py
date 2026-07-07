#!/usr/bin/env python

# For more development, consider the following:
# docker compose exec dvmdostem-mapping-support bokeh serve --port 7003 scripts/io_view.py --dev scripts/io_view.py
# pip install nest_asyncio
# pip install --upgrade bokeh==3.0.3

from osgeo import gdal
# Don't import rasterio too - they compete for some 
# underlying GDAL.so global objects!
from osgeo import osr

import os

import shapely

import geojson
import json
import glob

import bokeh
import bokeh.io as bkio
import bokeh.events as bke
import bokeh.models as bkm
import bokeh.plotting as bkp
import bokeh.layouts as bkl

import bokeh.tile_providers

import geopandas

# handy for embed debugging...
#import nest_asyncio
#nest_asyncio.apply()


def get_corner_coords(file_path):
  '''
  Given a file path to a vegetation.nc dvmdostem input file, this function
  figures out the corner coordinates in WGS84. Assumes that the vegetation.nc
  file is projected and has all the spatial reference info.
  Returns coordinate pairs for lr, ll, ul, ur.
  '''
  ds = gdal.Open("NETCDF:{}:veg_class".format(file_path))
  ulx, xres, xskew, uly, yskew, yres = ds.GetGeoTransform()

  lrx = ulx + ds.RasterXSize * xres
  lry = uly + ds.RasterYSize * yres

  llx = ulx
  lly = uly + ds.RasterYSize * yres

  urx = ulx + ds.RasterXSize * xres
  ury = uly

  targetSR = osr.SpatialReference()
  targetSR.ImportFromEPSG(4326) # WGS84
  sourceSR = osr.SpatialReference(wkt=ds.GetProjectionRef())
  print(ds.GetProjectionRef())
  coordTrans = osr.CoordinateTransformation(sourceSR,targetSR)

  # For some reason this seems to return (Y/lat, X/lon) instead of X,Y.
  # I don't understand quite what is going on....
  return [coordTrans.TransformPoint(X, Y) for X,Y in zip((lrx,llx,ulx,urx),(lry,lly,uly,ury))]


def transform(x, y, srs='EPSG:3857', trs='EPSG:4326'):
  '''
  Wrapper around osr.CoordinateTransformation
  
  Confusion abounds with regards to the ordering of x and y.
  It seems that the transformation functions wants them supplied like 
  (y, x) but then returns (x, y). Go figure.

  EPSG:3857 - Web Mercator
  EPSG:3338 - Alaska Albers
  EPSG:4326 - WGS84

  '''
  sourceSR = osr.SpatialReference()
  sourceSR.SetFromUserInput(srs)

  targetSR = osr.SpatialReference()
  targetSR.SetFromUserInput(trs)

  coordTrans = osr.CoordinateTransformation(sourceSR, targetSR)
  x, y, _ = coordTrans.TransformPoint(y, x)
  return (x, y)

def build_feature_collection(folder_list):
  '''
  Builds a GeoJSON feature collection with a polygon for every site in the
  `folder_list`.

  Parameters
  ----------
  `folder_list` : list of folders 
    Each folder is expected to be a folder of `dvmdostem` input data, and should
    have a vegetation.nc file within it.

  Returns
  -------
  geosjon_obj : a GeoJSON object
  '''
  geojson_obj = dict(type="FeatureCollection",features=[])

  if len(folder_list) < 1:
    # make an empty structure; seems to be very sensitive to having all
    # fields, especially the coordinates in the right shape!
    geojson_obj['features'].append(
      dict(
        type="Feature",
        geometry=dict(
          type="Polygon",
          coordinates=[[[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]]],
        ),
        properties=dict(name=''),
      )
    )
  for folder in folder_list:
    
    f = os.path.join(folder, 'vegetation.nc')

    if not os.path.exists(f):
      print("ERROR! Can't find file: {}".format(f))
    else:


      lr,ll,ul,ur = get_corner_coords(f)
      if "Koug" in folder:
        print(lr,ll,ul,ur, "    ",folder)

      # CAUTION: For some reason get_corner_coords(..) is returning
      # (Y,X) instead of (X,Y). Doesn't make sense to me with regards
      # to the documentation for osr.CoordinateTransformation.TransformPoint(..)
      # So here, we swap the order of the coordinates, and things seem to work
      # downstream for plotting....
      lr,ll,ul,ur = [(x[1],x[0],x[2]) for x in (lr,ll,ul,ur)]

      geojson_obj['features'].append(
        dict(
          type="Feature", 
          geometry=dict(
            type="Polygon", 
            # must be list of lists so as to accomodate holes
            coordinates=[[list(lr),list(ur),list(ul),list(ll),list(lr)]]  # CCW for exterior rings
            #coordinates=[[list(lr),list(ll),list(ul),list(ur),list(lr)]]
            
          ), 
          properties=dict(
            name=f
          )
        )
      )

  return geojson_obj


def build_areas_df(folders):
  '''
  '''
  print("Looking in the following folders for datasets to map:")
  if len(folders) > 10:
    for x in folders[0:3]:
      print("    {}".format(x))
    print("    ... {} total folders ...".format(len(folders)))  
    for x in folders[-3:]:
      print("    {}".format(x))
  else:
    print(folders)

  # hand built dict trying to be valid geojson
  feature_collection = build_feature_collection(folders)
  print(f"feature_collection: {type(feature_collection)}")

  # GEOJson is assumed to be un-projected, WGS84
  vgj = geojson.loads(geojson.dumps(feature_collection))

  # Have to explicitly extract the geometries so the column can be set 
  # for the geopandas GeoDataFrame
  geoms = [shapely.geometry.shape(i['geometry']) for i in vgj['features']]
  geodf = geopandas.GeoDataFrame(vgj, geometry=geoms)

  # tell geopandas what the CRS is for the data
  geodf = geodf.set_crs(epsg=4326) # WGS84
  print("feature collecton bounds in wgs84: ", geodf.total_bounds)

  # now re-project to web mercator (used by tiling service)
  geodf = geodf.to_crs(epsg=3857) # web mercator.
  print("feature collection bounds in web mercator: ", geodf.total_bounds)

  # Add a name column...
  geodf['name'] = [os.path.dirname(i['properties']['name']).split('/')[-1] for i in vgj.features]

  return geodf


def get_io_folder_listing(starting_path, pattern="*"):
  '''Get list of folders using the starting path and matching the pattern.'''
  folder_list = glob.glob(os.path.join(starting_path, pattern))
  folder_list = [i for i in folder_list if ".tar.gz" not in i]
  folder_list = [i for i in folder_list if os.path.isdir(i)]
  folder_list = [i for i in folder_list if i.split('/')[-1].startswith('cru')]

  return folder_list


def update_map(attr, old, new):
  print(f'update_map(...): attr={attr}, old={old}, new={new}')
  

def update_points(event):

  print(f"Event is: {event}")

  try:
    lat = float(points_input_lat.value)
    lon = float(points_input_lon.value)
  except:
    print('Problem with value in points inputs. Nothing to do.')

  lon, lat = transform(lon, lat, srs='EPSG:4326',trs='EPSG:3857')

  point_data_source.data = dict(lon=[lon], lat=[lat])



def update_areas(attr, old, new):
  print(f'update_areas(...): attr={attr}, old={old}, new={new}')

  folders = get_io_folder_listing(folder_input.value)

  if len(folders) < 1:
    print("Invalid folder path. No input folders found. Reverting to previous display.")
    folder_input.value = old # this triggers the change event again...
  else:

    areas_df = build_areas_df(folders)

    # Update the global datasource that backs all the patches..
    data_table_source.data = dict(name=areas_df['name'])
    geosource.geojson = areas_df.to_json()

    print(data_table_source)
    print(data_table_source.data)
    # if you call map_figure.patches(...) here, then it draws new patches
    # each time and they eventually overlay obsucring the alpha setting.
    print("Done updating areas.")

# Figure out some bounds that zoom default view to Alaska. Transform from 
# WGS84 to web mercator
xmin, ymin = transform(-179, 45, srs='EPSG:4326',trs='EPSG:3857')
xmax, ymax = transform(-130, 75, srs='EPSG:4326',trs='EPSG:3857')

## Main Map Plot ##
map_figure = bkp.figure(
    # Comment out bounds to show blank map (nothing) if no data is loaded, or
    # zoom to extent of whatever data is loaded.
    x_range = (xmin, xmax), y_range=(ymin, ymax),
    #x_range=(-20039764, 19965065), y_range=(-20112178, 15268115), # approx full globe
    x_axis_type="mercator", y_axis_type="mercator"
)

# Add tiles
map_figure.add_tile("CartoDB Positron", retina=True)

# Crosshairs
width_span = bkm.Span(dimension="width", line_dash="dotted", line_width=1, line_color='red')
height_span = bkm.Span(dimension="height", line_dash="dotted", line_width=1, line_color='red')
map_figure.add_tools(bkm.CrosshairTool(overlay=[width_span, height_span]))

## Widgets ##
folder_input = bkm.TextInput(title="Path to folders", value='', placeholder='FOLDER PATH', width=600)
folder_input.on_change('value', update_areas)

points_input_lat = bkm.TextInput(title='Lat', value='', placeholder='LAT')
points_input_lon = bkm.TextInput(title='Lon', value='', placeholder='LON')

point_mark_button = bkm.Button(label="Mark Point")
point_mark_button.on_click(update_points)

mouse_lat, mouse_lon = [0,0]
mouse_lat_wgs84, mouse_lon_wgs84 = transform(mouse_lat, mouse_lon, srs='EPSG:3338', trs='EPSG:4326')

parag_cur_wgs84 = bkm.Paragraph(text=f"Cursor WGS84 ({mouse_lon_wgs84:0.6f}, {mouse_lat_wgs84:0.6f})")
parag_cur_webmerc = bkm.Paragraph(text=f"Cursor Web Mercator ({mouse_lon:0.6f}, {mouse_lat:0.6f})")

x, y = transform(-157, 64, srs='EPSG:4326', trs='EPSG:3857')
point_data_source = bkm.ColumnDataSource(dict(lon=[x], lat=[y]))

map_figure.circle(x='lon', y='lat', source=point_data_source, size=20, color="navy", alpha=0.5)

# Start with an empty geo data source
geodf = build_areas_df(get_io_folder_listing(''))

#geodf = build_areas_df(get_io_folder_listing('demo-data'))
geosource = bkm.sources.GeoJSONDataSource(geojson=geodf.to_json())
area_patches = map_figure.patches('xs','ys', source=geosource, fill_color='red', line_color='gray', line_width=0.25, fill_alpha=.3)

taptool = bkm.TapTool(renderers = [area_patches])
hovertool = bkm.HoverTool(renderers = [area_patches],
                          tooltips = [
                            ('Site','@name')
                          ])
columns = [
  bkm.TableColumn(field="name", title="Name"),
  #bkm.TableColumn(field="", title=""),
]
data_table_source = bkm.ColumnDataSource( dict(name=geodf['name']) ) 
data_table = bkm.DataTable(source=data_table_source, columns=columns, width=600)#, height=200)
# The above works, but we need to somehow synchronize the geosource and the non-
# geo version of the dataframe...

map_figure.add_tools(taptool, hovertool)

## Event callbacks ##
def update_cursor_printout(event):
  #print(event.y, event.x,)
  parag_cur_webmerc.text = f"Cursor Web Mercator ({event.x:0.6f}, {event.y:0.6f})"
  mouse_lat_wgs84, mouse_lon_wgs84 = transform(event.y, event.x, srs='EPSG:3857', trs='EPSG:4326')
  parag_cur_wgs84.text = f"Cursor WGS84 ({mouse_lon_wgs84:0.6f}, {mouse_lat_wgs84:0.6f})"

def tapselect_handler(attr, old, new):
  # value of new seems to be the indices in the data source that are selected.
  print("attr:{}   old:{}    new:{}".format(attr, old, new))
  print("Somewhere to stop!")

  #data_table_source.selected.indices = new

  for i in data_table_source.data['name'][new]:
    print(i)


# Register callbacks
map_figure.on_event(bke.MouseMove, update_cursor_printout)
geosource.selected.on_change('indices', tapselect_handler)

selected_patches = bkm.Patches(fill_color="yellow", fill_alpha=.3, line_width=1, line_color="green")
area_patches.selection_glyph = selected_patches

## Layout ##
layout = bkl.layout(
    children=[
      [map_figure, [folder_input, [points_input_lat, points_input_lon, point_mark_button], data_table]],
      [parag_cur_webmerc],
      [parag_cur_wgs84]
    ],
    sizing_mode='fixed'
)


## Render it... ##
bkio.curdoc().add_root(layout)