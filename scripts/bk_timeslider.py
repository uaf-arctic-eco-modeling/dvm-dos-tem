#!/usr/bin/env python

# T. Carman, 2022 Nov

import numpy as np
import netCDF4 as nc
import xarray as xr

import functools

import bokeh
import bokeh.io as bkio
import bokeh.models as bkm
import bokeh.plotting as bkp
import bokeh.layouts as bkl


# atlas
#ff = "input-staging-area/cru-ts40_ar5_rcp85_gfdl-cm3_moose_basin_v2022_11_17_29x36/historic-explicit-fire.nc"

# MacOS
# scp -r atlas:/home/UA/tcarman2/dvm-dos-tem/input-staging-area/cru-ts40_ar5_rcp85_gfdl-cm3_moose_basin_v2022_11_17_29x36/ ~/Downloads 
ff = '/Users/tobeycarman/Downloads/cru-ts40_ar5_rcp85_gfdl-cm3_moose_basin_v2022_11_17_29x36/historic-explicit-fire.nc'

#ff = "input-staging-area/cru-ts40_ar5_rcp85_mri-cgcm3_GoodP_basin_74x93/historic-explicit-fire.nc"
#ff = 'demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/historic-explicit-fire.nc'
#ff = 'input-staging-area/cru-ts40_ar5_rcp85_ncar-ccsm4_Chat_basin_104x150/historic-explicit-fire.nc'

ds = nc.Dataset(ff)
xds = xr.open_dataset(ff, decode_cf=False)

exp_burn_mask = xds.exp_burn_mask
exp_aob = xds.exp_area_of_burn
exp_jdob = xds.exp_jday_of_burn
exp_sev = xds.exp_fire_severity

# two ways to do the same thing
F = np.count_nonzero(exp_burn_mask, axis=0)
G = np.count_nonzero(ds.variables['exp_burn_mask'][:], axis=0)


DW = exp_burn_mask.shape[2]
DH = exp_burn_mask.shape[1]


# Setup all the color maps and ranges
mask_cm = bkm.LinearColorMapper(palette="Greys9", low=0, high=1, 
                           low_color="darkgrey", high_color="red")
mask_cb = bkm.ColorBar(color_mapper=mask_cm, padding=5)

aob_cm = bkm.LogColorMapper(palette="Viridis256", low=1, high=float(exp_aob.max()),
                            low_color='lightgrey', high_color='darkgrey')
aob_cb = bkm.ColorBar(color_mapper=aob_cm, padding=5)

sev_cm = bkm.LinearColorMapper(palette="Inferno5", low=0, high=5,
                           low_color="pink", high_color="blue", nan_color="lightgrey")
sev_cb = bkm.ColorBar(color_mapper=sev_cm, padding=5)

jdob_cm = bkm.LinearColorMapper(palette="Viridis256", low=0, high=365,
                           low_color="lightgrey", high_color="darkgrey", nan_color="green")
jdob_cb = bkm.ColorBar(color_mapper=jdob_cm, padding=5)

count_cm = bkm.LinearColorMapper(palette=bokeh.palettes.viridis(F.max()+1), low=0, high=F.max(), 
                          low_color="darkgrey", high_color="red")
count_cb = bkm.ColorBar(color_mapper=count_cm, padding=5)

TOOLTIPS = [
    ("(x,y)", "($x, $y)"),
    ("timeidx", "@timeidx"),
    ("Mask", "@mask"),
    ("AOB", "@aob"),
    ("Sev", "@sev"),
    ("JDOB","@jdob"),
    ("# yrs burned","@count_time_axis"),
]

#bkio.output_file("SAMPLE.html")

# Crosshairs
width_span = bkm.Span(dimension="width", line_dash="dotted", line_width=1, line_color='red')
height_span = bkm.Span(dimension="height", line_dash="dotted", line_width=1, line_color='red')

# Image plots
yr_count = bkp.figure(title="# yrs burned", width=400, height=400, tools='hover', toolbar_location='left', tooltips=TOOLTIPS)
yr_count.x_range.range_padding = yr_count.y_range.range_padding = 0
yr_count.add_tools(bkm.CrosshairTool(overlay=[width_span, height_span]))
yr_count.add_layout(count_cb, 'above')

burn_mask = bkp.figure(title="Mask", width=400, height=400, tools='hover', toolbar_location='left', tooltips=TOOLTIPS )
burn_mask.x_range.range_padding = burn_mask.y_range.range_padding = 0
burn_mask.add_tools(bkm.CrosshairTool(overlay=[width_span, height_span]))
burn_mask.add_layout(mask_cb, 'right')

aob = bkp.figure(title="AOB", width=400, height=400, tools='hover', toolbar_location='left', tooltips=TOOLTIPS)
aob.x_range.range_padding = aob.y_range.range_padding = 0
aob.add_tools(bkm.CrosshairTool(overlay=[width_span, height_span]))
aob.add_layout(aob_cb, 'right')

fire_sev = bkp.figure(title="Severity", width=400, height=400, tools='hover', toolbar_location='left', tooltips=TOOLTIPS)
fire_sev.x_range.range_padding = fire_sev.y_range.range_padding = 0
fire_sev.add_tools(bkm.CrosshairTool(overlay=[width_span, height_span]))
fire_sev.add_layout(sev_cb, 'right')

jdob = bkp.figure(title="JDOB", width=400, height=400, tools='hover', toolbar_location='left', tooltips=TOOLTIPS)
jdob.x_range.range_padding = jdob.y_range.range_padding = 0
jdob.add_tools(bkm.CrosshairTool(overlay=[width_span, height_span]))
jdob.add_layout(jdob_cb, 'right')

# File input
#file_input = bkm.FileInput(accept=".nc")


# Time Controls
#time_slider = bkm.Slider(start=0, end=exp_burn_mask.time.shape[0], step=1, title='time axis idx')
#time_slider = bkm.DateSlider(start=exp_burn_mask.time.values[0], end=exp_burn_mask.time.values[-1], value=exp_burn_mask.time[0], step=1, title="time axis index")
time_slider = bkm.Slider(start=0, end=115, value=0, step=1, title='time axis idx')
time_spinner = bkm.Spinner(title='time axis idx', low=0, high=115, step=1, value=0, width=100)

# data table
columns = [
        bkm.TableColumn(field="xy", title="(x,y)"),
        bkm.TableColumn(field="count_time_axis", title="# yrs burned"),
        bkm.TableColumn(field="mask", title="Mask", ),
        bkm.TableColumn(field="aob", title="AOB"),
        bkm.TableColumn(field="sev", title="Sev"),
        bkm.TableColumn(field="jdob", title="JDOB"),
    ]
data_table = bkm.DataTable(columns=columns, width=400, height=50)

# columns = [
#         bkm.TableColumn(field="var", title="var"),
#         bkm.TableColumn(field="min", title="min"),
#         bkm.TableColumn(field="max", title="max"),
#         bkm.TableColumn(field="med", title="median"),
#         bkm.TableColumn(field="std", title="std"),
# ]
# summary_table = bkm.DataTable(columns=columns, width=400, height=200)
# data = dict(
#     var='mask,aob,mask,sev,jdob,count'.split(','),
#     #min=[np.min(D) for D in [exp_burn_mask, exp_aob, exp_sev, exp_jdob, F]], 
#     #max=[np.max(D).data for D in [exp_burn_mask, exp_aob, exp_sev, exp_jdob, F]],
#     #med=[np.median(D).data for D in [exp_burn_mask, exp_aob, exp_sev, exp_jdob, F]],
#     #std=[np.std(D).data for D in [exp_burn_mask, exp_aob, exp_sev, exp_jdob, F]],
# )
# for k, v in data.items():
#   print(k, v)
# summary_table.source.data = data

# text_summary = bkm.PreText(text=f"""
# Global Stats Summary
# ====================
# exp_aob.min: {exp_aob.min().values}
# exp_aob.max: {exp_aob.max().values}
# exp_aob.std: {exp_aob.std().values}
# """, width=400, height=200)


def update_imgs(time_idx):
  '''Build a ColumnDataSource for a specific time_idx and plot all images.'''
  # While it works to plot directly w/o CDS, e.g:
  # burn_mask.image(image=[exp_burn_mask[time_idx].values], x=0, y=0, dw=DW, dh=DH, )
  # doing so prevents accessing data from other images in HoverTool...

  data = bkm.ColumnDataSource(
      data=dict(
        mask=[exp_burn_mask[time_idx].values],
        aob=[exp_aob[time_idx].values],
        sev=[exp_sev[time_idx].values],
        jdob=[exp_jdob[time_idx].values],
        timeidx=[time_idx],
        honky_tonk=["jibberish"],
        count_time_axis=[F],
      )
  )
  yr_count.image(source=data,   image='count_time_axis', x=0, y=0, dw=DW, dh=DH, color_mapper=count_cm)
  burn_mask.image(source=data,  image='mask',            x=0, y=0, dw=DW, dh=DH, color_mapper=mask_cm)
  aob.image(source=data,        image='aob',             x=0, y=0, dh=DH, dw=DW, color_mapper=aob_cm)
  fire_sev.image(source=data,   image='sev',             x=0, y=0, dh=DH, dw=DW, color_mapper=sev_cm) 
  jdob.image(source=data,       image='jdob',            x=0, y=0, dh=DH, dw=DW, color_mapper=jdob_cm)


def update_table(time_idx, y=None, x=None):
  
  # This allows update_table to be called before any points have been 
  # clicked, i.e. when x and y are None.
  if y and x:
    Y = int(y)
    X = int(x)
    data = dict(
        xy=[(X,Y)], # <---- Note order is for display, NOT for indexing!
        mask=[exp_burn_mask[time_idx,Y,X].values],
        aob=[exp_aob[time_idx,Y,X].values],
        sev=[exp_sev[time_idx,Y,X].values],
        jdob=[exp_jdob[time_idx,Y,X].values],
        timeidx=[time_idx],
        count_time_axis=[F[Y,X]],
    )

    data_table.source.data = data

# Run the update functions to get everything setup
update_imgs(0)
update_table(0)

# Define all the callback functions...
def load_file(attr, old, new, foo):
  print(f'attr={attr}, old={old}, new={new}, foo={foo}')
  print("DUMMY FUNCTION! Need to work in loading files!")
  # looks like file_input.value is the **actual** data (base 64 encoded contents of file!)
  # filename is just the os.path.basename() of what the user selected - no path info...

def time_spinner_handler(attr, old, new, foo):
  print(attr, old, new)
  print(foo)
  time_slider.value = new 
  update_imgs(new) 
  update_table(new)

def time_slider_handler(attr, old, new, foo):
  print(attr, old, new)
  print(foo)
  time_spinner.value = new
  update_imgs(new)
  update_table(new)

def tap_callback(event):
    print('User clicked', event)
    print(event.x, event.y)
    update_table(0, y=event.y, x=event.x)

### Register events and callbacks ###

# Tap event on plots - update data table
burn_mask.on_event(bokeh.events.Tap, tap_callback)
aob.on_event(bokeh.events.Tap, tap_callback)
fire_sev.on_event(bokeh.events.Tap, tap_callback)
jdob.on_event(bokeh.events.Tap, tap_callback)
yr_count.on_event(bokeh.events.Tap, tap_callback)

# update control events
time_spinner.on_change("value_throttled", functools.partial(time_spinner_handler, foo="sample"))
time_slider.on_change("value_throttled", functools.partial(time_slider_handler, foo="test!"))
#file_input.on_change("filename", functools.partial(load_file, foo="extra args..."))

# Put everything in a layout
layout = bkl.layout(
    children=[
      [ burn_mask, aob, [time_slider, time_spinner, data_table] ],
      [ fire_sev, jdob, yr_count],
    ],
    sizing_mode='fixed'
)


bkio.curdoc().add_root(layout)   # updates server doc
#bkio.show(layout)                # opens browser
#bkio.save(layout)                # saves html file to disk
