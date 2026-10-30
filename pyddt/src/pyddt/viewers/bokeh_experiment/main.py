#!/usr/bin/env python

# T Carman, May 2019

# adapted from bokeh docs, Stocks example

try:
    from functools import lru_cache
except ImportError:
  # Python 2 does stdlib does not have lru_cache so let's just
  # create a dummy decorator to avoid crashing
  print ("WARNING: Cache for this example is available on Python 3 only.")
  def lru_cache():
    def dec(f):
      def _(*args, **kws):
        return f(*args, **kws)
      return _
    return dec

from os.path import dirname, join

import pandas as pd
import netCDF4 as nc

from bokeh.io import curdoc
from bokeh.layouts import row, column
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import PreText, Select, CheckboxGroup, MultiSelect, RadioButtonGroup, Dropdown
from bokeh.plotting import figure

import os
import glob
import sys
sys.path.insert(0,"/Users/tobeycarman/sandbox/dvm-dos-tem/")
import util.output

DATA_DIR ="/Users/tobeycarman/sandbox/better-gl_c/output"

def list_available_variables():
  a = os.listdir(DATA_DIR)

  # three fields (variable name, timeres, stage)
  # separated by underscore
  a = [x for x in a if len(x.split("_")) == 3]


#########################
  expected_file_names = ["{}_{}_{}.nc".format(var, timestep, stg) for stg in stages]
  expected_file_names = [os.path.join(fileprefix, i) for i in expected_file_names]

  full_ds = np.array([])
  units_str = ''
  for i, exp_file in enumerate(expected_file_names):
    print("Trying to open: ", exp_file)
    with nc.Dataset(exp_file, 'r') as f:
      #print f.variables[var].units
      if i == 0:
        full_ds = f.variables[var][:]
        units_str = f.variables[var].units
      else:
        full_ds = np.concatenate( (full_ds, f.variables[var][:]), axis=0 )
        if f.variables[var].units != units_str:
          raise RuntimeError("Something is wrong with your input files! Units don't match!")

  return (full_ds, units_str)


#########################


def get_data(variable="", stages=['eq','sp','tr','sc'], timeres='yearly', pixel=(0,0)):
  y, x = pixel

  d, units = util.output.stitch_stages(variable, timeres, stages, fileprefix=DATA_DIR)
  if len(d.shape) == 5:
    d = util.output.sum_across_compartments(d)
  else:
    pass
  d = d[:,y,x]

  # with nc.Dataset(DATA_DIR + '/{}_{}_{}.nc'.format(variable, timeres, stage)) as ds:
  #   print ds
  #   if all(i in ds.dimensions.keys() for i in ['time','y','x','pft','pftpart']):
  #     d = ds.variables[variable]
  #     d = util.output.sum_across_compartments(d)
  #     d = d[:,y,x]
  #   else:
  #     d = ds.variables[variable][:,y,x]
  #     #from IPython import embed; embed()

  span = pd.period_range(start='1901-01-01', freq='Y', periods=d.shape[0])

  dd = {}
  for i in range(d.shape[1]): # loop over pft dimensions
    dd['pft{}'.format(i)] = d[:,i]
  dd['date'] = [i.year for i in span]
  #dd['date'] = [i.to_timestamp() for i in span]
  #from IPython import embed; embed()
  data = pd.DataFrame(dd)
  return data

def DD():
  pass


def get_variable_info(vname):
  files = glob.glob(os.path.join(DATA_DIR, '{}_*_*.nc'.format(vname.upper())))
  for f in files:
    with nc.Dataset(f) as ds:
      if 'time' in ds.variables:

        # See this repo:
        #https://github.com/SciTools/nc-time-axis
        start = nc.num2date(ds.variables['time'][0], ds.variables['time'].units, ds.variables['time'].calendar) 
        end = nc.num2date(ds.variables['time'][-1], ds.variables['time'].units, ds.variables['time'].calendar) 
        #dti = pd.
        # Not done yet...


def update(attr, old, new, selected=None):
  print("attr, old, new, selected: ", attr, old, new, selected)
  # Maybe loop over all widgets, collecting state values?
  #for widget in widget_collection:

  #vinfo = get_variable_info(new)

  # if 'pft' in vinfo['dimensions']:
  #   # add pft selector widget
  #   if 'compartment' in vinfo['dimensions']:
  #     # add cmpt select widget
  # elif 'layer' in vinfo['dimensions']
  #   # add layer selector widget

  # get/build time axis??
  # build one that spans from beginning of first available stage, to end of last available stage

  # then get each file's data and put it in the right spot in the full index...

  
  # Then get the data
  data = get_data(variable=variable_dropdown.value, stages=['tr', 'sc'])
  variable_dropdown.label = variable_dropdown.value



  # Then set the source DF to have different numbers.
  source.data = source.from_df(data[['date','pft0']]) # pass in dataframe of data created above
  source_static.data = source.data
  


menu = [x for x in os.listdir(DATA_DIR) if len(x.split("_")) == 3]
menu = set([(i.split("_")[0], i.split("_")[0]) for i in menu]) # get rid of duplicates that come from different stages, (i.e. NPP_monthly_eq.nc NPP_monthly_sp.nc)
menu = [i for i in menu] # Make sure its a list


#menu = [("NPP", "NPP"), ("VEGC", "VEGC"), ("INGPP", "INGPP")]
#from IPython import embed; embed()
variable_dropdown = Dropdown(label="Choose Variable", button_type="warning", menu=menu, default_value='NPP') #, value="NPP")

variable_dropdown.on_change('value', update)
# Set up widgets
# variable_multiselect = MultiSelect(
#   title="Choose varibales", 
#   value=['VEGC'],                            # The keys that are chosen 
#   options=[('NPP','NPP'),('VEGC','VEGC')])   # The key value pairs of what is available. Keys are shown to the user.

#stage_checkboxgroup = CheckboxGroup(labels=["pr","eq","sp","tr","sc"], active=[])  # <- Code to determine available stages?
#timeres_radiobuttongroup = RadioButtonGroup(labels=["daily", "monthly", "yearly"], active=0) # <- code to determine available time rez?



# Setup data: one structure for ALL the data (static), the other for the selected data
source = ColumnDataSource(data=dict(date=[], pft0=[]))
source_static = ColumnDataSource(data=dict(date=[], pft0=[]))

# Setup plot
fig = figure(plot_width=900, plot_height=200) #,  x_axis_type='datetime', active_drag='xbox_select')
fig.line('date','pft0',source=source_static)
fig.circle('date', 'pft0', size=1, source=source, color=None, selection_color='orange')




# Setup callbacks

# Layout


# Show (serve) it
#update('value','NPP','NPP','NPP')

widgets = row(variable_dropdown)
main_row = row(fig)
layout = column(widgets, main_row)
curdoc().add_root(layout)

