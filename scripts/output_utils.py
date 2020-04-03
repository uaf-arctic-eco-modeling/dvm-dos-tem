#!/usr/bin/env python

# Tobey Carman
# Dec 2017

# A set of functions for plotting dvmdostem ouputs.

import os
import glob
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import netCDF4 as nc
import collections


def get_last_n_eq(var, timeres='yearly', fileprefix='', n=10):
  '''
  Work in progress for getting the last few year of equlibrium stage for calibration.
  '''
  fname = os.path.join(fileprefix, '{}_{}_eq.nc'.format(var.upper(), timeres.lower()))

  if not os.path.exists(fname):
    raise RuntimeError("Can't find file: {}".format(fname))

  with nc.Dataset(fname) as ds:
    data = ds.variables[var.upper()][-n:]
    info = list(zip(data.shape, list(ds.dimensions.keys())))
    #info = [(name, dim.size) for name, dim in ds.dimensions.iteritems()]

  return data, info




def sum_monthly_flux_to_yearly(data):
  '''
  Expects `data` to be at least a 1D array, with the first axis being time.
  Also assumes that the time axis starts and stops on Jan 1 and Dec 31. In 
  otherwords, if you had a 2 years of monthly data that ran from Aug 1 thru
  July 31, this function would NOT work!  
  '''
  if (data.shape[0] % 12) != 0:
    raise RuntimeError('data size for dimension 0 (time) must be an even multiple of 12')

  newshape = [data.shape[0]/12]
  for i in data.shape[1:]:
    newshape.append(i)

  yearly_data = np.zeros((newshape)) * np.nan

  for i in range(0, newshape[0]):
    yr_start = (i * 12)
    yr_end = (i * 12) + 12
    yearly_data[i] = np.sum(data[yr_start:yr_end], axis=0)

  return yearly_data


def sum_across_compartments(data):
  '''
  Expects `data` to be a 5D numpy array with dimensions 
  `(time, pftpart, pft, y, x)`.

  Returns a 4D array that has been summed over the `pftpart` dimension,
  effectively creating a new array with totals for a PFT instead of having
  values split by compartment.
  '''
  if len(data.shape) != 5:
    raise RuntimeError('data input parameter must have 5 dimensions')
  return np.sum(data, axis=1)


def sum_across_pfts(data):
  '''
  Expects `data` to be a 4D numpy array with dimensions
  `(time, pft, y, x)`.

  Returns a 3D array that has been summed over the `pft` dimension, effectively
  creating a new array with totals for an entire gridcell/pixel instead of
  having the totals broken out by PFT.
  '''
  if len(data.shape) != 4:
    raise RuntimeError('data input parameter must have 4 dimensions')
  return np.sum(data, axis=1)


def sum_across_layers(data):
  '''
  Expects `data` to be a 4D numpy array with dimensions
  `(time, layers, y, x)`.

  Returns a 3D array that has been summed over the `layer` dimension, 
  effectively creating a new array with totals for an entire gridcell/pixel 
  instead of having the totals broken out by layer.
  '''
  if len(data.shape) != 4:
    raise RuntimeError('data input parameter must have 4 dimensions')
  return np.sum(data, axis=1)


def average_monthly_pool_to_yearly(data):
  '''
  Expects `data` to be a 3D, 4D, or 5D numpy MASKED array with dimensions
  `(time, layers, y, x)`, `(time, pft, y, x)`  or `(time, pftpart, pft, y, x)`
  and the size of the time dimension to be an even multiple of 12. The calling 
  client is expected to set up the mask correctly, i.e. if data is read from a 
  netcdf file, then using the _FillValue for the mask. 

  The function will compute the average of the input array along the time 
  dimension in strides of 12.

  Returns a 3D, 4D, or 5D numpy array with dimensions e.g. `(time, layers, y, x)`, 
  (same as input), but the length of the returned time dimension will be 
  1/12th of the length of the input array.

  Note: this function contains a loop and could probably be vectorized somehow
  with some fancy numpy indexing.

  Examples:
      Load a monthly file with soil layer data and convert it to yearly.

      >>> import numpy as np
      >>> import netCDF4 as nc
      >>> import scripts.output_utils as ou
      >>>
      >>> soc = nc.Dataset('all-merged/SOC_monthly_tr.nc')
      >>> a = np.ma.masked_values(soc.variables['SOC'][:], soc.variables['SOC']._FillValue)
      >>> a = np.ma.masked_values(a, -99999)
      >>> 
      >>> b = average_monthly_pool_to_yearly(a)
      >>> print a.shape, b.shape
      (1308, 22, 10, 10) (109, 22, 10, 10)

  '''
  if len(data.shape) != 4:
    raise RuntimeError('data input parameter must have 4 dimensions.')
  if data.shape[0] % 12 > 0:
    raise RuntimeError('data input parameter first dimension (time) must be evenly divisible by 12')
  if not isinstance(data, np.ma.core.MaskedArray):
    raise RuntimeError('data input parameter must be a numpy masked array!')

  original_dims = list(data.shape)
  new_time = original_dims[0] / 12
  new_dims = original_dims
  new_dims[0] = new_time

  output = np.ones(new_dims) * np.nan
  for i in range(0, new_time):
    yr_start = i * 12
    yr_end = i*12 + 12

    output[i] = data[yr_start:yr_end].mean(axis=0)

  return output


def stitch_stages(var, timestep, stages, fileprefix=''):
  '''
  Expects `var` to be one the dvmdostem output variable names. `timestep` must
  be one of "yearly" or "monthly", and stages is a (ordered) list containing 
  one or more of "pr","eq","sp","tr","sc". `fileprefix` is an optional path
  that will be pre-pended to the filenames for opening files in a different
  directory.

  Outputs from dvmdostem assume one variable per file and the following 
  file-naming pattern: 
  
      `var`_`timestep`_`stage`.nc
  
  This function makes the following additional assumptions about the files:
    - All files for different timesteps have the same dimensions
    - The file's variable name is the same as the variable name in the filename.
    - There is a units attribute?

  Returns a tuple (`data`, `units`), where `data` is a multi-dimensional numpy 
  array that is the concatenation of the input arrays along the time axis and 
  `units` is the unit string that is found in the input netcdf files.
  '''

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


def check_files(fnames):
  '''
  A work in progress for verifying assumptions about input files, `fnames`.

  Prints messages to stdout.

  Returns `None`.
  '''

  def get_dims(afile):
    '''
    Attempts to open `afile` as a netCDF file and read dimensions.
    
    Prints message for RuntimeErrors resulting from opening and reading file.

    Returns a list of dimensions in the file.
    '''
    try:
      with nc.Dataset(afile, 'r') as f:
        dims = f.variables[var].dimensions
    except RuntimeError as e:
      print("RuntimeError! Problem opening/reading: {} message: {}".format(afile, e.message))
      dims = None

    return dims

  dims_for_each_file = [get_dims(f) for f in fnames]

  if len(set(dims_for_each_file)) > 1:
    print("Warning! Not all files have the same dims!")

  if set(dims_for_each_file).pop() is None:
    print("Warning! At least one file doesn't even have dimensions!")

  if len(set(dims_for_each_file).pop()) > 0:
    first_item = set(dims_for_each_file).pop()
    if first_item[0].lower() != 'time':
      print("Warning! It appears that the first dimension is not time!")  
  else: 
    print("Warning! No dimensions, can't check for time as first dimension!")


def mask_by_cmt(data, cmtnum, vegmap_filepath):
  '''
  Expects `data` to be at least a 2D array with the last two dimensions being
  (y, x). `cmtnum` is the community type number that will remain unmasked
  in the final data. `vegmap_filepath` should be the path to dvmdostem input 
  vegetation map file, which has dimensions (y,x) and an integer specifying 
  the CMT number for each pixel, under the variable 'veg_class'.

  Returns a numpy  masked array with the same dimensions as `data`. In the
  returned array, data for pixels in `vegmap_filepath` equal to `cmtnum` will
  unmasked.

  Example:

    # An nd veg mask
    # Assumed that the shape of data is either 
    # 3D (time, y, x), 
    # 4D (time, pft, y, x) or (time, layer, y, x) or 
    # 5D (time, pftpart, pft, y, x),
    # and that in any case, the last two dimensions are y and x

    # For example:
    In [142]: ba = np.random.randint(0,100,(2,3,4,5,5))

    In [143]: np.broadcast_to(np.random.randint(0,2,(5,5)), ba.shape).shape
    Out[143]: (2, 3, 4, 5, 5)

  '''
  vegmap = nc.Dataset(vegmap_filepath, 'r')

  vegmask = np.ma.masked_not_equal(vegmap.variables['veg_class'][:], cmtnum)

  vmnd_mask = np.broadcast_to(vegmask.mask, data.shape)

  # Full data, masked by veg type
  vmnd_all = np.ma.masked_array(data, vmnd_mask)

  return vmnd_all

def mask_by_failed_run_status(data, run_status_filepath="run_status.nc"):
  '''
  Masks out any data for which the run status is < 0 in the `run_status_filepath`.

  `data`: (numpy.ndarray) must have at least 2 dimensions (y, x) and they must
   be the last dimensions.

  `run_status_file`: (str) path to a dvmdostem run_status.nc file that has
  dimensions (y,x) and single variable run_status(y,x) that has positive values
  for successfully run pixels and negative values for failed pixels.

  Returns a numpy masked array the same shape as `data` with all the data for
  failed pixels masked out.

  Example: see mask_by_cmt(...)
  '''
  runstat = nc.Dataset(run_status_filepath)

  runstatmask = np.ma.masked_less(runstat.variables['run_status'][:], 0)

  rsnd_mask = np.broadcast_to(runstatmask.mask, data.shape)

  rsnd_all = np.ma.masked_array(data, rsnd_mask)

  return rsnd_all

def plot_comp_sst():

  ROWS=4; COLS=4 

  gs = gridspec.GridSpec(ROWS, COLS)

  for i, cmt in enumerate([4,5,6,7]):
    ax = plt.subplot(gs[i,:])
    plot_spatial_summary_timeseries('VEGC', 'yearly', cmt, 'tr sc'.split(' '), "vegetation.nc", "run_status.nc", ax=ax)

  plt.tight_layout()
  plt.show(block=True)



def plot_basic_timeseries(vars2plot, spatial_y, spatial_x, time_resolution, stages, folder):
  '''
  Make a basic timeseries plot, one subplot per variable.

  Not sure yet how should handle summarizing over layers, pfts, etc.
  '''

  ROWS = len(vars2plot)
  COLS = 1
  gs = gridspec.GridSpec(ROWS, COLS)

  for i, var in enumerate(vars2plot):
    ax = plt.subplot(gs[i,:])
    data, units = stitch_stages(var, time_resolution, stages, folder)
    print(data.shape)
    ax.plot(data[:,spatial_y, spatial_x], label=var)
    ax.set_ylabel = units

  plt.show()



def plot_spatial_summary_timeseries(var, timestep, cmtnum, stages, ref_veg_map, ref_run_status, ax=None):
  '''
  Plots a single line with min/max shading representing the `var` averaged over
  the spatial dimension, considering only pixels for `cmtnum`. Stitches together
  data for the specified `stages`.

  `var`: (string) must be one of the dvmdostem output variables (upper case).

  `timesteps`: (string) must be one of "monthly" or "yearly".

  `cmtnum`: (int) must be a number found in the veg map, see `mask_by_cmt(..)`.

  `stages`: (list) must contain one or more of "pr","eq","sp","tr","sc".

  `ref_veg_map`: (str) must be a file path to a dvmdostem vegetation input map
  with dimensions (y, x) and a single variable veg_class(y,x) with a number for
  representing the community type for that pixel.
  
  `ref_run_status`: (str) must be a file path to a dvmdostem run_status.nc map
  with dimensions (y,x) and a single variable run_status(y, with a number for 
  how the pixel completed its run.

  `ax`: (matplotlib.axes._subplots.AxesSubplot instance) will plot line(s) on
  this axes instance. If ax in None, then will create (and show) a new figure
  and plot.

  Attempts to find the requsite files for `var`, `timestep` and `stages`.
  Plots a timeseries of variable `var` after averaging over the spatial
  dimensions. If the data found in the input files is higher dimensionality
  than (time, y, x), for example (time, pft, y, x), then the data is 
  summed across PFTs before plotting.

  Returns `None`
  '''
  data, units = stitch_stages(var, timestep, stages)
  print("data size:", data.size)

  data = mask_by_cmt(data, cmtnum, ref_veg_map)
  print("data count after masking cmt:", data.count())

  data = mask_by_failed_run_status(data, ref_run_status)
  print("data count after masking run status:", data.count())

  if len(data.shape) == 5: # assume (time, pftpart, pft, y, x)
    data = sum_across_compartments(data)

  if len(data.shape) == 4: # assume (time, pft, y, x) or (time, layer, y, x)
    data = sum_across_pfts(data) # alternatively, use sum_across_layers(..)

  if len(data.shape) == 3: # assume (time, y, x)
    pass # all set...

  workhorse_spatial_summary_plot(data, cmtnum, units, var, stages, ax=ax)


def workhorse_spatial_summary_plot(data, cmtnum, yunits, varname, stages, ax=None):
  '''
  Worker function, plots a line for average along time axis (axis 0), 
  with shading for min and max.

  `data`: (numpy.ndarray) must have dimensions (time, y, x).

  `cmtnum`: (int)  used for the plot title.

  `varname`: (str) used for the plot title

  `stages`: (list) used for the plot title, must contain one or 
            more of "pr","eq","sp","tr","sc".

  `ax`: (matplotlib.axes._subplots.AxesSubplot instance) will plot line(s) on
  this axes instance. If ax in None, then will create (and show) a new figure
  and plot.

  Returns `None`
  '''
  if ax is not None:
    print("Plotting on existing ax instance...")
    ax.plot(np.ma.average(data, axis=(1,2)), linewidth=0.5, label="CMT {}".format(cmtnum))
    ax.fill_between(
        np.arange(0, len(data)),
        np.ma.min(data, axis=(1,2)), 
        np.ma.max(data, axis=(1,2)), 
        color='gray', alpha=0.25
    )
    ax.set_ylabel(yunits)
    ax.set_title("{} for CMT {} averaged spatially for stages {}".format(varname, cmtnum, stages))
    #plt.show(block=True)

  else:
    print("Plotting on new ax, figure...")
    plt.plot(np.ma.average(data, axis=(1,2)), linewidth=0.5, label="CMT {}".format(cmtnum))
    plt.fill_between(
        np.arange(0, len(data)),
        np.ma.min(data, axis=(1,2)), 
        np.ma.max(data, axis=(1,2)), 
        color='gray', alpha=0.25
    )
    plt.ylabel(yunits)
    plt.title("{} for CMT {} averaged spatially for stages {}".format(varname, cmtnum, stages))
    plt.show(block=True)


def plot_inputs(cmtnum, hist_fname, proj_fname, ref_veg_map):
  '''
  Plots the historic and projected climate inputs, averaging over the spatial
  dimensions and with shading for min/max.

  `cmtnum`: (int) CMT to work with, must be in the veg map, see mask_by_cmt(..).

  `hist_fname`: (str) path to a dvmdostem historic input file.

  `proj_fname`: (str) path to a dvmdostem projected input file.

  The historic and projected input files are assumed to be have the variables
  tair, precip, vapor_press, and nirr all with the dimensions (time, y, x). 
  The files are assumed to be monthly resolution.

  Returns `None`.
  '''
  with nc.Dataset(hist_fname) as f:
    htair = f.variables['tair'][:]
    hprecip = f.variables['precip'][:]
    hvp = f.variables['vapor_press'][:]
    hnirr = f.variables['nirr'][:]

  with nc.Dataset(proj_fname) as f:
    ptair = f.variables['tair'][:]
    pprecip = f.variables['precip'][:]
    pvp = f.variables['vapor_press'][:]
    pnirr = f.variables['nirr'][:]

  tair = np.concatenate((htair, ptair), axis=0)
  precip = np.concatenate((hprecip, pprecip), axis=0)
  vp = np.concatenate((hvp, pvp), axis=0)
  nirr = np.concatenate((hnirr, pnirr), axis=0)

  tair = mask_by_cmt(tair, cmtnum, ref_veg_map)
  precip = mask_by_cmt(precip, cmtnum, ref_veg_map)
  vp = mask_by_cmt(vp, cmtnum, ref_veg_map)
  nirr = mask_by_cmt(nirr, cmtnum, ref_veg_map)

  #fig, (tair_ax, precip_ax, vp_ax, nirr_ax) = plt.subplots()

  tair_ax = plt.subplot(411)
  precip_ax = plt.subplot(412, sharex=tair_ax)
  vp_ax = plt.subplot(413, sharex=tair_ax)
  nirr_ax = plt.subplot(414, sharex=tair_ax)

  for pax, data, vname in zip([tair_ax, precip_ax, vp_ax, nirr_ax], [tair, precip, vp, nirr], ['tair','precip','vapor_press','nirr']):

    pax.plot(np.ma.average(data, axis=(1,2)), linewidth=0.5, label="{}".format(vname))
    pax.fill_between(
        np.arange(0, len(data)),
        np.ma.min(data, axis=(1,2)), 
        np.ma.max(data, axis=(1,2)), 
        color='gray', alpha=0.25
    )

    # add a line marking the transition from historic to projected
    pax.vlines(htair.shape[0], *pax.yaxis.get_view_interval(), color='red')

    pax.set_title("{} averaged spatially for historic and projected masked to cmt{}".format(vname, cmtnum))

  plt.tight_layout()
  plt.show(block=True)
  

def boxplot_monthlies(var, stages, cmtnum, ref_veg_map, ref_run_status, facecolor='blue'):
  '''
  Makes a boxplot showing distribution of values for `var` for each month,
  averaged over spatial dimensions, and only considering `cmtnum`. If multiple
  stages are specified, the stages will be stitched together along the time 
  dimension before the distributions are calculated.

  `var`: (str) one of the dvmdostem output variables.
  `stages`: (list) must contain one or more of "pr","eq","sp","tr","sc".
  `cmtnum`: (int) which CMT to work with.
  `ref_veg_map`: (str) path to a vegetation map to use for masking cmts
  `ref_run_status`: (str) path to run status map to use for masking failed cells
  `facecolor`: (str) color to use for the box.

  Returns `None`
  '''

  data, units = stitch_stages(var, 'monthly', stages)
  print("data size:", data.size)

  data = mask_by_cmt(data, cmtnum, ref_veg_map)
  print("data count after masking cmt:", data.count())

  data = mask_by_failed_run_status(data, ref_run_status)
  print("data count after masking run status:", data.count())


  # list of months
  months = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(' ')
  
  # empty dictionary
  monthstr2data = collections.OrderedDict()

  # fill dict with data for each month
  for i, m in enumerate(months):
      b0 = data[i::12,:,:]
      monthstr2data[m] = data[i::12,:,:]

  data2 = [np.ma.average(i, axis=(1,2)) for i in list(monthstr2data.values())]

  bp = plt.boxplot(
      data2,
      labels=list(monthstr2data.keys()),
      #notch=True,
      whis='range', # force whiskers to min/max range instead of quartiles
      showfliers=False,
      patch_artist=True,
      boxprops=dict(facecolor=facecolor, alpha=.25),
      whiskerprops=dict(color=facecolor),
      capprops=dict(color=facecolor)
  )
  plt.ylabel(units)
  plt.title("{} for CMT {}, averaged spatially ".format(var, cmtnum))
  plt.show(block=True)


def boxplot_by_pft(var, timestep, cmtnum, stages, ref_veg_map, ref_run_status):
  '''
  Work in progress...
  '''

  data, units = stitch_stages(var, timestep, stages)
  print("data size:", data.size)
  print(data.shape)

  d2 = data
  # d2 = sum_across_compartments(data)
  # print "data size after summing compartments:", d2.size

  d3 = mask_by_cmt(d2, cmtnum, ref_veg_map)
  print("data size after masking cmt:", d3.count())

  d3 = mask_by_failed_run_status(d3, ref_run_status)
  print("data count after masking run status:", d3.count())

  pft0avg = np.ma.average(d3, axis=(2,3))
  #plt.plot(pft0avg) # Line plot
  plt.boxplot(
      pft0avg,
      labels = ["PFT {}".format(i) for i in range(0, 10)],
      whis='range',
      showfliers=False,
      patch_artist=True,
      boxprops=dict(color='blue', alpha=0.25),
      whiskerprops=dict(color='red'),
      capprops=dict(color='blue'),
  )
  plt.ylabel(units)
  plt.show(block=True)


def plot_soil_layers():
  '''
  WORK IN PROGRESS! 
  
  Attempts to display an intuitive representation of the soil column using
  a horizontal bar chart. 
   - bar width is set by the value of the variable under investigation
   - bar color is set by the LAYERTYPE
   - bar height (thickness?) is controlled by the LAYERDZ

  The y axis is depth (cumulative sum of LAYERDZ)
  
  '''
  with nc.Dataset("all-merged/SOC_monthly_tr.nc") as f:
    soc = np.ma.masked_values(f.variables['SOC'][:], f.variables['SOC']._FillValue)

  soc = np.ma.masked_values(soc, -99999)
  soc = average_monthly_pool_to_yearly(soc)
    
  with nc.Dataset("all-merged/LAYERDZ_yearly_tr.nc") as dzf:
    dz = dzf.variables['LAYERDZ'][:]

  with nc.Dataset("all-merged/LAYERTYPE_yearly_tr.nc") as ltf:
    lt = ltf.variables['LAYERTYPE'][:]
  
  Y = 0
  X = 0
  time = 78

  def cmapper(x):
    #    moss     shallow  deep     mineral  undefined 
    c = ['green', 'red',   'black', 'gray',  'y']

    if isinstance(x, np.ma.core.MaskedConstant):
      return c[-1]
    else:
      return c[int(x)]

  colors = list(map(cmapper, lt[time,:,Y,X]))
  bottoms = np.cumsum(dz[time,:,Y,X]) * -1  # <-- reverses y axis!
  widths = soc[time,:,Y,X]
  heights =  dz[time,:,Y,X]
  plt.barh(bottoms, widths, heights, color=colors)

def plot_fronts(args):
  '''
  Makes a timeseries plot of all the fronts that are output. The X axis is time,
  the Y axis is depth from surface (0 at the top of the plot). Each front will
  have a line on the plot. 

  Blue dots are used for FREEZING fronts (frozen above, warm below, values > 0)
  Red is used for THAWING fronts (warm above, frozen below, value < 0)

  # NOTE:
  # In the model, there are two places that fronts info is stored: 
  # a pair of deques and a pair of arrays. The arrays are set to have a max
  # size of 10 (MAX_FRONTS or something like that) As the model runs, the
  # values are written periodically from the dequees into the arrays. The 
  # arrays are the structures that are output to the netcdf files. Our output
  # netcdf files and output_spec files are not setup to deal with a "fronts" 
  # dimension. So for now, since we know there will only be 
  # 10 fronts, we'll store the stuff in files with a layer dimension, using the
  # first 10 slots. After a little testing it looks like there are rarely more
  # than 2 fronts, so this setup is not space efficient.
  '''

  time = args.timestep
  Y, X = args.yx
  od = args.outfolder
  timeres = (args.timeres).lower()
  stage = (args.stage).lower()

  ftype, ftype_units = pull_data_wrapper(args, variable='FRONTSTYPE', required_dims=['time','layer','y','x'])
  fdepth, fdepth_units = pull_data_wrapper(args, variable='FRONTSDEPTH', required_dims=['time','layer','y','x'])

  if fdepth_units == '':
    print("WARNING! Missing depth units! Assumed to be meters.")
    depthunits = 'm'
  if ftype_units == '':
    print("WARNING! Missing front type units! Assumed to be categorical.")
    dzunits = 'categorical'

  # Setup the plotting
  ROWS=1; COLS=1
  gs = gridspec.GridSpec(ROWS, COLS)

  fig = plt.figure()
  ax0 = plt.subplot(gs[:])
  ax0.set_ylabel("Depth ({})".format(fdepth_units))
  ax0.set_xlabel("Time")
  ax0.set_title("{}".format(od))

  x = np.arange(0, fdepth.shape[0])

  for fnt_idx in range(0,10):
    front_thaw = ax0.scatter(x, np.ma.masked_where(ftype[:,fnt_idx,Y,X] > 0, fdepth[:,fnt_idx,Y,X]), color='orange', marker='o')
    front_thaw_line = ax0.plot(np.ma.masked_where(ftype[:,fnt_idx,Y,X] > 0, fdepth[:,fnt_idx,Y,X]), label='thaw front {}'.format(fnt_idx), color='orange', alpha=0.5)

    front_freeze = ax0.scatter(x ,np.ma.masked_where(ftype[:,fnt_idx,Y,X] < 0, fdepth[:,fnt_idx,Y,X]), color='blue', marker='o')
    front_freeze_line = ax0.plot(np.ma.masked_where(ftype[:,fnt_idx,Y,X] < 0, fdepth[:,fnt_idx,Y,X]), label='freeze front {}'.format(fnt_idx), color='blue', alpha=0.5)

  if args.show_layers:
    layerdepth, layerdepth_units = pull_data_wrapper(args, variable="LAYERDEPTH", required_dims=['time','layer','y','x'])
    layer_lines = []
    for lidx in range(0,layerdepth.shape[1]):
      layerline = ax0.plot(layerdepth[:,lidx,Y,X], color='gray', alpha=0.5, linewidth=0.5, marker='o', markersize=.75)
      layer_lines.append(layerline)

  if args.layer_colors:
    ltype, ltype_units = pull_data_wrapper(args, "LAYERTYPE")
    for il, l in enumerate(layer_lines):
      if il == 0:
        pass
      else:
        currl = l[0]
        prevl = layer_lines[il-1][0]

        # Make sure to grab the previous layer (il-1) for the layer type condition!
        ax0.fill_between(x, currl.get_ydata(), prevl.get_ydata(), ltype[:,il-1,Y,X] == 0, color='xkcd:green', alpha=.5)
        ax0.fill_between(x, currl.get_ydata(), prevl.get_ydata(), ltype[:,il-1,Y,X] == 1, color='xkcd:sand', alpha=.5)
        ax0.fill_between(x, currl.get_ydata(), prevl.get_ydata(), ltype[:,il-1,Y,X] == 2, color='xkcd:coffee', alpha=.5)
        ax0.fill_between(x, currl.get_ydata(), prevl.get_ydata(), ltype[:,il-1,Y,X] == 3, color='xkcd:silver', alpha=.5)


  # This is super cluttered in the default view if there are many layers or if
  # the time axis is long, but looks good when you zoom in.
  ax0.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(12))
  ax0.xaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(6))
  ax0.invert_yaxis()

  plt.show(block=True)


def pull_data_wrapper(args, variable=None, required_dims=None):
  '''
  Extracts data from an netcdf file.

  `args` must be a dict with settings for outfolder, timeres, and stage.
  `variable` must be a string with the variable name that is expected to be in
  the netcdf file. The file is expected to be names like this:
  "VARIABLE_TIMERES_STAGE.nc" and is expected to be present in the
  args.outfolder.

  If required_dims is passed, then the dimensions of the variable to extract
  are checked against the list and a RuntimeError is thrown if there is a
  a problem.

  Returns a tuple (data, units), where data is a numpy array or masked array
  and units is a string that is extracted from the attributs of the netcdf file.

  '''

  od = args.outfolder
  timeres = (args.timeres).lower()
  stage = (args.stage).lower()

  def pull_data(the_var, required_dims):
    '''Pulls data out of an nc file'''
    fglob = os.path.join(od, "{}_{}_{}.nc".format(the_var, timeres, stage))
    the_file = glob.glob(fglob)

    if len(the_file) < 1:
      raise RuntimeError("Can't find file for variable '{}' here: {}".format(the_var, fglob))
    if len(the_file) > 1:
      raise RuntimeError("Appears to be more than one file matching glob?: {}".format(fglob))

    the_file = the_file[0]
    print("Pulling data from ", the_file)
    with nc.Dataset(the_file, 'r') as ds:
      if required_dims != None:
        for rd in required_dims:
          if rd not in list(ds.dimensions.keys()):
            raise RuntimeError("'{}' is a required dimension for this operation. File: {}".format(rd, the_file))

      data = ds.variables[the_var][:]
      units = ds.variables[the_var].units
    return data, units

  data, units = pull_data(variable, required_dims)

  return data, units

def plot_soil_layers2(args):
  '''
  Makes plots of soil profile variables. Generates one plot/axis for each 
  variable specified. Y axis is the depth, X axis is the value of the variable.
  Plots include horizontal lines marking layer boundaries. 

  Calling code must supply`args` which must be a dictionary with the following
  keys set:
  `outfolder`: (string) a path to a folder containing dvmdostem output files.
  `time`: (int) index along time axis to plot 
  `yx`: (tuple) the pixel coordinates to source for the plot(s)
  `timeres`: (string) either 'monthly', 'yearly', or 'daily' (daily is untested)
  `stage`: (string) the run stage to plot from
  `vars`: a list of variables names to plot, e.g. ['TLAYER', 'SOC', 'ORGN']

  The function will look in `outfolder` for the appropriate dvmdostem output
  files basedon variable name, stage, and time resolution. 

  NOTE: The LAYERDZ and LAYERDEPTH files must be present in `outfolder` for 
  the speficied `stage` and `timeres`!
  '''

  od = args.outfolder
  time = args.timestep
  Y, X = args.yx
  timeres = (args.timeres).lower()
  stage = (args.stage).lower()

  # Need to specify units in output_spec files!!
  depth, depthunits = pull_data_wrapper(args, 'LAYERDEPTH', required_dims=['time','layer','y','x'])
  dz, dzunits = pull_data_wrapper(args, 'LAYERDZ', required_dims=['time','layer','y','x',])

  if depthunits == '':
    print("WARNING! Missing depth units! Assumed to be meters.")
    depthunits = 'm'
  if dzunits == '':
    print("WARNING! Missing dz units! Assumed to be meters.")
    dzunits = 'm'
  if dzunits != depthunits:
    print("WARNING! depthunits ({}) and dzunits ({}) are not the same!".format(depthunits, dzunits)) 

  # Setup the plotting
  ROWS=1; COLS=len([v.upper() for v in args.vars])
  gs = gridspec.GridSpec(ROWS, COLS)

  fig = plt.figure()
  ax0 = plt.subplot(gs[:,0])
  ax0.set_ylabel("Depth ({})".format(depthunits))

  for i, v in enumerate([v.upper() for v in args.vars]):
    if i == 0:
      ax0.set_title(v)
      ax0.invert_yaxis()
    else:
      ax = plt.subplot(gs[:,i], sharey=ax0)
      ax.set_title(v)

  for ax in fig.axes:

    vardata, units = pull_data_wrapper(args, ax.get_title())

    # Line plot, offset so markers are at the midpoint of layer.'''
    ax.plot(
      vardata[time,:,Y,X],
      depth[time,:,Y,X] + (0.5 * dz[time,:,Y,X]),
      #color='red',
      marker='o',
      markeredgecolor='gray',
      #markerfacecolor='red',
      alpha=0.85,
    )

    if ax.get_title() == 'TLAYER':
      ymin, ymax = ax.yaxis.get_view_interval()
      ax.vlines(0, ymin, ymax, linestyles='solid', color='red')

    # First attempt was to use horizontal bars to display variables that
    # represent mass or volume (e.g. SOC). This worked for versions of
    # matplotlib < 2.x, but in the more recent versions there is some
    # issue and the y scale gets really messed up when plotting bars.
    #
    # if ax.get_title().upper() in ['SOC','VWC']:
    #   ''' For volume/mass stuff, use bars'''
    #   ax.barh(
    #     depth[time,:,Y,X],       # bottom
    #     vardata[time,:,Y,X],     # width
    #     dz[time,:,Y,X],          # height
    #   )
    # else:
    #   '''Line plot, offset so markers are at the midpoint of layer.'''
    #   ax.plot(
    #     vardata[time,:,Y,X],
    #     depth[time,:,Y,X] + (0.5 * dz[time,:,Y,X]),
    #     marker='o',
    #   )

    # Label the X axis
    ax.set_xlabel(units)

    # Put in the layer markers.
    xmin, xmax = ax.xaxis.get_view_interval()
    ax.hlines(
      depth[time,:,Y,X],         # y positions
      xmin, xmax,                # x min and max
      linestyles='dashed', color='orange'
    )

    ax.grid(False, which='both', axis='both')

  # Turn off y axis labels for all but the left one (first axes instance)
  for ax in fig.axes[1:]:
    ax.yaxis.set_visible(False)

  fig.suptitle("Soil Profile stage: {} {}, timestep: {}".format(stage, timeres, time))

  plt.show(block=True)


def print_soil_table(outdir, stage, timeres, Y, X, timestep):
  '''
  Prints a table to stdout with all the soil info.

  Looks in the `outdir` for any .nc file with 'layer' in the dimension list,
  and `stage` and `timeres` in the name, e.g. "SOC_monthly_tr.nc". Each
  appropriate file found will get a column in the printed table. The printed
  table will be for the pixel specified by `Y` and `X` and for the specified
  `timestep`

  Prints a very wide table if there are many by-layer outputs available. A neat
  addition to this function would be a better way to control the width.
  '''

  def get_var_name(fpath):
    '''Extract variable name from full path'''
    return os.path.basename(fpath).split("_")[0]

  allncfiles = glob.glob(os.path.join(outdir, "*_{}_{}.nc".format(timeres, stage)))
  soilfiles = []
  soillayerdimlengths = []
  for f in allncfiles:
    with nc.Dataset(f) as ds:
      if 'layer' in ds.dimensions:
        try:
          numlayers = ds.dimensions['layer'].size # attribute only available in netCDF4 > 1.2.2
        except AttributeError as e:
          numlayers = len(ds.dimensions['layer'])
        soilfiles.append(f)
        soillayerdimlengths.append(numlayers)

  soillayerdimlengths = set(soillayerdimlengths)
  if len(soillayerdimlengths) > 1:
    raise RuntimeError("Not all files/variables have the same lenght of layer dimensions")

  header_fmt = "{:>15s} " * len(soilfiles)
  row_fmt = "{:>15.3f} " * len(soilfiles)

  varlist = [get_var_name(f) for f in soilfiles]
  print("---- Soil Profile ----")
  print("  output directory: {}".format(outdir))
  print("  {} files stage: {} pixel(y,x): ({},{}) timestep: {}".format(timeres.upper(), stage.upper(), Y, X, timestep))
  print(header_fmt.format(*varlist))

  # This is probably not very effecient.
  for il in range(0, soillayerdimlengths.pop()):

    data = []
    for v, f in zip(varlist, soilfiles):
      with nc.Dataset(f) as ds:
        if type(ds.variables[v][timestep,il,Y,X]) == 'str':
          data.append(np.nan)
        if ds.variables[v][timestep,il,Y,X] is np.ma.masked: # works in recent numpy versions
          data.append(np.nan)
        if np.ma.is_masked(ds.variables[v][timestep, il, Y,X]): # works numpy 1.11.1
          data.append(np.nan)
        else:
          data.append(ds.variables[v][timestep,il,Y,X])

    print(row_fmt.format(*data))


if __name__ == '__main__':

  import argparse
  import textwrap

  parser = argparse.ArgumentParser(
    formatter_class = argparse.RawDescriptionHelpFormatter,

      description=textwrap.dedent('''\
        Command line interface for utility functions that work on 
        dvmdostem outputs. This script may also be imported and used
        from other scripts (if you wish to import functions without 
        using this command line interface).

        The command line interface contains (or will in the future)
        different sub-commands for different types of operations.
        '''.format("")),

      epilog=textwrap.dedent(''''''),
  )

  # Arguments that may apply to all sub commands
  parser.add_argument("--yx", nargs=2, type=int, default=[0, 0],
      help=textwrap.dedent('''The (Y,X) pixel coordinates to plot'''))

  parser.add_argument("--timestep", type=int, default=0, 
      help=textwrap.dedent('''The timestep for which to make the profile'''))

  #parser.add_argument("--timeslice" ... ) # <-- might be handy in the future...

  parser.add_argument('--timeres', type=str, default="monthly",
      choices=['yearly', 'monthly', 'daily'],
      help='The time resolution: monthly or yearly')

  parser.add_argument('--stage', default="tr", 
      choices=['pr', 'eq','sp','tr','sc'], help="The stage to plot")


  subparsers = parser.add_subparsers(help='sub commands', dest='command')

  # EXAMPLES
  # ./input_utils.py soil-profiles /some/path/to/some/outputs/

  # sp for 'soil profile'
  sp_parser = subparsers.add_parser('soil-profiles', 
      help=textwrap.dedent('''\
        Make plots of soil profiles variables (i.e. outputs that are specified 
        to be by layer). NOTE: you must have outputs for the variables
        LAYERDZ and LAYERTYPE in addition to the variables you'd like to
        plot for these panles to work!'''))
  sp_parser.add_argument('--vars', nargs='*', default=['SOC'], help='The soil layer variables to plot')
  sp_parser.add_argument('--print-full-table', action='store_true', help="Prints a full table of all soil/layer variables to the console.")
  sp_parser.add_argument('outfolder', help="Path to a folder containing a set of dvmdostem outputs")


  fronts_parser = subparsers.add_parser('fronts',
    help=textwrap.dedent('''\
      Make a plot of the fronts. Y axis depth with 0 at the surface, X axis is
      time (tested with monthly data).
      '''))
  fronts_parser.add_argument('--show-layers', action='store_true',
    help=textwrap.dedent('''Plot the layers. Assumes that file for LAYERDEPTH 
      is available in the outfolder.'''))
  fronts_parser.add_argument('--layer-colors', action='store_true',
    help=textwrap.dedent('''Try to color the layers based on the LAYERTYPE.
      Green for moss, sand for shallow soil, dark brown for deep soil, and gray
      for mineral.'''))
  fronts_parser.add_argument('outfolder', help=textwrap.dedent('''\
    "Path to a folder containing a set of dvmdostem outputs, presumably with
    files for FRONTSDEPTH and FRONTSTYPE'''))

  # sc for 'site compare'
  # ./output_util.py --stage tr --yx 0 0 --timeres monthly site-compare --save-name some/path/to/somefile.pdf /path/to/inputA /path/to/inputB /pathto.inpuC
  sc_parser = subparsers.add_parser('site-compare',
      help=textwrap.dedent('''\
        Make time-series plots of various variables, with a line for each site.
        Note that the different "sites" don't have to be geographic sites, but 
        could be the same site, but differnet model runs with outputs stored
        in different folders. Basically each positional argument supplied
        is treated as a "site". This command may result in many plots which 
        will be saved in a single pdf, with the name (and path) specified by the 
        --savename option.
        '''))
  sc_parser.add_argument('--vars', nargs="*")
  sc_parser.add_argument('--savename', default="dvmdostem-outpututils-sitecompare.pdf")
  sc_parser.add_argument('output_folder', nargs='+', metavar="FOLDER",
      help=textwrap.dedent('''\
        Path to a folder containing dvmdostem outputs.
        '''))

  # E.G.: ./output_util.py basic-ts --stitch eq,sp,tr,sc --yx 0 0 --vars VEGC,SOC,GPP --savename test.pdf /data/tcarman/ngee_dhs_runs/dhs_1_cmt04/out/2000121081/
  bts_parser = subparsers.add_parser('basic-ts',
      help=textwrap.dedent('''\
          Make time-series of one or more various variables. Each variable gets
          its own subplot. X axes will be linked.
          '''))
  bts_parser.add_argument('--stitch', nargs="+", help="comma separated list of stages to attempt to stitch together")
  bts_parser.add_argument('--yx', nargs=2, type=int, default=[0, 0], help='The (Y,X) pixel coordinates to plot')
  bts_parser.add_argument('--vars', nargs="+", help="comma or space separated list or variable names")
  bts_parser.add_argument('--savename', default="dvmdostem-outpututils-basicts.pdf")
  bts_parser.add_argument('output_folder', nargs='+', metavar="FOLDER",
      help=textwrap.dedent('''\
        Path to a folder containing dvmdostem outputs.
        '''))


  # ss for 'spatial summary'
  ss_parser = subparsers.add_parser('spatial-summaries',
      help=textwrap.dedent('''\
      Make plots that are summaries over the spatial dimensions.'''))

  #ss_parser.add_argument()

  args = parser.parse_args()
  print(args)

  if args.command == 'fronts':
    plot_fronts(args)

  if args.command == 'soil-profiles':
    if args.print_full_table:
      print_soil_table(args.outfolder, args.stage, args.timeres, args.yx[0], args.yx[1], args.timestep)
    plot_soil_layers2(args)

  if args.command == 'spatial-summaries':
    print("Not implemented yet. Or rather, the command line interface is not ")
    print("implemented yet - many of the plot functions are done!")

  if args.command == 'site-compare':
    print("Not implemented yet...")
    print("Warn about conflicting arguments? Or about ignoring --yx argument??")

  if args.command == 'basic-ts':

    # just seeing if the right files are around.
    for var in args.vars[0].split(','):
      for stage in args.stitch:
        ep = os.path.join(args.output_folder[0], "{}_{}_{}.nc".format(var, args.timeres, stage))
        print("Looking for file: ", ep)
        if not os.path.exists(ep):
          raise RuntimeError("Missing file!: {}".format(ep))
        else:
          data = nc.Dataset(ep)

    # Make the plots...
    plot_basic_timeseries(args.vars[0].split(','), args.yx[0], args.yx[1], args.timeres, args.stitch, args.output_folder[0]) 








'''
a = np.zeros((3,2,2))
b = np.ones((2,2,2))
np.concatenate((a,b), axis=0)
'''




'''
# Make a 3x3 array of random data (2D)
>>> m = np.random.randint(0, 100, (3,3))
array([[90, 49, 44],
       [99, 43, 28],
       [65, 50, 26]])


# Mask off some arbitrary part of it
>>> m2 = np.ma.masked_inside(m, 40,60)
masked_array(data =
 [[90 -- --]
 [99 -- 28]
 [65 -- 26]],
             mask =
 [[False  True  True]
 [False  True False]
 [False  True False]],
       fill_value = 999999)

# Make a 3D array of random data
>>> d = np.random.randint(2, 100, (4,3,3,))
array([[[44, 79, 17],
        [36, 91, 68],
        [95, 41, 28]],

       [[97, 35, 41],
        [39, 28, 19],
        [60, 61,  5]],

       [[62, 64, 59],
        [81, 33, 79],
        [45, 76, 85]],

       [[18,  6, 30],
        [23, 81, 46],
        [28, 56, 27]]])

# Broadcast my 2D mask out to the 3rd dimension
>>> m3 = np.broadcast_to(m2.mask, d.shape)
array([[[False,  True,  True],
        [False,  True, False],
        [False,  True, False]],

       [[False,  True,  True],
        [False,  True, False],
        [False,  True, False]],

       [[False,  True,  True],
        [False,  True, False],
        [False,  True, False]],

       [[False,  True,  True],
        [False,  True, False],
        [False,  True, False]]], dtype=bool)

# Make a big 'ol masked array
>>> dm3 = np.ma.masked_array(d, m3)
masked_array(data =
 [[[44 -- --]
  [36 -- 68]
  [95 -- 28]]

 [[97 -- --]
  [39 -- 19]
  [60 -- 5]]

 [[62 -- --]
  [81 -- 79]
  [45 -- 85]]

 [[18 -- --]
  [23 -- 46]
  [28 -- 27]]],
             mask =
 [[[False  True  True]
  [False  True False]
  [False  True False]]

 [[False  True  True]
  [False  True False]
  [False  True False]]

 [[False  True  True]
  [False  True False]
  [False  True False]]

 [[False  True  True]
  [False  True False]
  [False  True False]]],
       fill_value = 999999)

'''
