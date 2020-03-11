#!/usr/bin/env python

#
# T. Carman Spring/Summer 2016
#

import os                         # general path manipulations
import shutil                     # cleaning up files
import glob                       # listing/finding data files
import json                       # reading data files
import signal                     # for exiting gracefully
import itertools
import tarfile                    # opening archived data
import argparse                   # command line interface
import textwrap                   # help formatting
import numpy as np                # general maths
import pandas as pd               # for timeseries plots
import matplotlib.pyplot as plt   # general plotting

import sys
if sys.version_info[0] < 3:
    from io import StringIO
else:
    from io import StringIO


def exit_gracefully(signum, frame):
  '''A function for quitting w/o leaving a stacktrace on the users console.'''
  print("Caught signal='%s', frame='%s'. Quitting - gracefully." % (signum, frame))
  sys.exit(1)

# Generator function for extracting specific files from a tar archive
def monthly_files(tarfileobj):
  '''Get the */monthly/*.json files...'''
  for tarinfo in tarfileobj:
    if 'monthly' in tarinfo.name:
      yield tarinfo

def analyze(cjd, pjd):
  '''
  Extract every ounce of knowledge from a pair of json data objects.

  Parameters
  ----------
  cjd : json?
    The 'current' json data object.
  pjd : json?
    The previous json data object.

  Returns a dict with all the data (calculated values).
  '''

  # The vascular/non-vascular split (i.e. which pfts should be considered
  # vascular or non) is done in the sum_across function from a lookup table.

  results = {}

  results['C_veg'] = bal_C_veg(cjd, pjd, xsec='all')
  results['C_veg_vasc'] = bal_C_veg(cjd, pjd, xsec='vasc')
  results['C_veg_nonvasc'] = bal_C_veg(cjd, pjd, xsec='nonvasc')

  results['C_soil'] = bal_C_soil(cjd, pjd)

  results['C_standing_dead'] = bal_C_standing_dead(cjd, pjd)
  results['N_standing_dead'] = bal_N_standing_dead(cjd, pjd)

  results['C_woody_debris'] = bal_C_woody_debris(cjd, pjd)
  results['N_woody_debris'] = bal_N_woody_debris(cjd, pjd)

  results['N_veg_tot'] = bal_N_veg_tot(cjd, pjd, xsec='all')
  results['N_veg_str'] = bal_N_veg_str(cjd, pjd, xsec='all')
  results['N_veg_lab'] = bal_N_veg_lab(cjd, pjd, xsec='all')
  results['N_soil_org'] = bal_N_soil_org(cjd, pjd)
  results['N_soil_avl'] = bal_N_soil_avl(cjd, pjd)

  results['N_veg_vasc_tot'] = bal_N_veg_tot(cjd, pjd, xsec='vasc')
  results['N_veg_vasc_str'] = bal_N_veg_str(cjd, pjd, xsec='vasc')
  results['N_veg_vasc_lab'] = bal_N_veg_lab(cjd, pjd, xsec='vasc')

  results['N_veg_nonvasc_tot'] = bal_N_veg_tot(cjd, pjd, xsec='nonvasc')
  results['N_veg_nonvasc_str'] = bal_N_veg_str(cjd, pjd, xsec='nonvasc')
  results['N_veg_nonvasc_lab'] = bal_N_veg_lab(cjd, pjd, xsec='nonvasc')

  return results


def file_loader(**kwargs):
  '''
  Build a list of files to open.

  Parameters
  ----------
  fileslice : str, optional
    A string of the form 'start:end'

  fromarchive : str, optional
    A path to a .tar.gz archive to read from.

  Returns
  -------
  jfiles : list of str
    A list of .json file paths.
  '''
  if 'fileslice' in kwargs:
      slice_string = kwargs['fileslice']
      # parse string into slice object
      # https://stackoverflow.com/questions/680826/python-create-slice-object-from-string/681949#681949
      custom_slice = slice(*[int(x.strip()) if x.strip() else None for x in slice_string.split(':')])
  else:
      custom_slice = slice(None,None,None)

  if "fromarchive" in kwargs:
    tf = tarfile.open(kwargs['fromarchive'])

    # might be able to use tar checksum (crc) to implement some kind of caching...
    TMP_EXTRACT_LOCATION = '/tmp/com.iab.dvmdostem.diagnostics.23f23f2' # <-- could be a checksum of the tar?

    if ( os.path.isdir(TMP_EXTRACT_LOCATION) or os.path.isfile(TMP_EXTRACT_LOCATION) ):
      print("Cleaning up the temporary location: ", TMP_EXTRACT_LOCATION)
      shutil.rmtree(TMP_EXTRACT_LOCATION)
    tf.extractall(TMP_EXTRACT_LOCATION, members=monthly_files(tf))
    full_glob = os.path.join(TMP_EXTRACT_LOCATION, "tmp/dvmdostem/calibration/monthly/*.json")
    print("Matching this pattern: ", full_glob)
    jfiles = glob.glob(full_glob)
  else:
    pattern_string = "/tmp/dvmdostem/calibration/monthly/*.json"
    print("Looking for json files matching pattern:", pattern_string)
    jfiles = glob.glob(pattern_string)

  print("Custom file slice:", custom_slice)
  jfiles = jfiles[custom_slice]

  return jfiles

def onclick(event):
  if event.xdata != None and event.ydata != None:
    i_edy = np.rint(event.ydata) # rint - convert to integer with rounding
    i_edx = np.rint(event.xdata)
    cax = event.inaxes
    caximg = cax.images[0]
    print("Axes: %s" % (cax.get_title().replace("\n", " ")))
    print("Data coordinates (y, x): ", "(%s,%s)"%(event.ydata, event.xdata))
    print("Data coords as int: ", "(%s,%s)"%(i_edy, i_edx))
    print("Data at[%s, %s]: %s" % (i_edy, i_edx, caximg.get_array()[i_edy, i_edx]))
    print()

  if event.key == 'ctrl+c':
    print("Captured Ctrl-C. Quit nicely.")
    exit_gracefully(event.key, None) # <-- need to pass something for frame ??


def error_image(save_plots=False, save_format="pdf", **kwargs):
  '''
  Generates "Error Image Plots", that are shown, and or saved.

  Parameters
  ----------
  plotlist : list of str
    Which plots to create (i.e. 'C soil' 'N veg', etc)
  save_plots : bool
    Whether or not to save the plots to files.
  save_format : str
    Which file format to use for saving image.
  savetag : str
    A tag to insertin the midst of the output file name.

  --> various kwargs, passed to file loader

  Returns
  -------
  None
  '''

  if "plotlist" not in kwargs:
    plotlist = ['C veg', 'C soil', 'N veg tot', 'N veg str', 'N veg lab', 'N soil org', 'N soil avl']
  else:
    plotlist = kwargs["plotlist"]

  jfiles = sorted(file_loader(**kwargs))


  # Figure out the month and year for the first and last
  # data files. Assumes that the datafiles are contiguous.
  with open(jfiles[0], 'r') as f:
    jdata = json.load(f)
    m1 = int(jdata["Month"])
    y1 = (jdata["Year"])

  with open(jfiles[-1], 'r') as f:
    jdata = json.load(f)
    mlast = (jdata["Month"])
    yrlast = (jdata["Year"])

  # Pad out the array so it fills an even 
  # number of months/years. So if the slice
  # lands on month 3 and end on month 10, 
  # add 3 empty months at the beginning
  # and 1 at the end. Helps for displaying as an image...
  empty = np.empty(len(jfiles) + m1 + (11-mlast)) * np.nan

  # Make room for a lot of data
  imgarrays_err = np.array([np.copy(empty) for i in plotlist])
  imgarrays_delta = np.array([np.copy(empty) for i in plotlist])

  # Run over all the files, calculating all the derived 
  # diagnostics.
  pjd = None
  for idx, jfile in enumerate(jfiles):
    with open(jfile, 'r') as f:
      jdata = json.load(f)

    diagnostics = analyze(jdata, pjd)

    for pltnum, key in enumerate(plotlist):
      imgarrays_err[pltnum][idx+m1] = diagnostics[key].err
      imgarrays_delta[pltnum][idx+m1] = diagnostics[key].delta

    pjd = jdata

  # Old method - resulted in 2 or more plots per panel (i.e. 'C soil', 
  # 'C veg', etc), and then one figure for each error, delta, and error/delta.
  # No titles, kind of hard to interpert.
  # image_plot(imgarrays_err, plotlist)
  # image_plot(imgarrays_delta, plotlist)
  # image_plot(imgarrays_err/imgarrays_delta, plotlist)

  # New method - shows one figure of for each item in plot list (i.e. 'C soil' 
  # 'N veg', etc), and each figure has error, delta, and error/delta on it.
  for idx, p in enumerate(plotlist):
    new_list = np.array((imgarrays_err[idx], imgarrays_delta[idx], imgarrays_err[idx]/imgarrays_delta[idx]))
    image_plot(new_list,
               ['error','delta','err/delta'], # list of titles for subplots
               title=p,                       # figure title
               save=save_plots,               # pass-thru whether or not to save
               savetag=savetag,               # pass-thru - a string to put in the filename
               format=save_format)            # pass-thru saving format



def image_plot(imgarrays, plotlist, title='', save=False, format='pdf', savetag=''):
  '''
  Carry out the rendering of several "image plots" side by side:
  Setup grid, layout, colorbar, render data, set titles, axes labels, etc.
  '''
  from mpl_toolkits.axes_grid1 import make_axes_locatable
  from matplotlib.colors import LogNorm
  from matplotlib.ticker import MultipleLocator
  from matplotlib.ticker import MaxNLocator
  import matplotlib.ticker as mtkr

  # One set of data for each plot
  assert len(imgarrays) == len(plotlist)

  # One row, with a column for each item in the imagearrays list
  fig, axar = plt.subplots(1, len(imgarrays), sharex=True, sharey=True)

  #fig.set_tight_layout(True)
  print("Making room for title...")
  plt.subplots_adjust(top=0.9, bottom=0.16)
  fig.suptitle(title, fontsize=16)

  # setup the callback
  cid = fig.canvas.mpl_connect('button_press_event', onclick)

  for axidx, (ax, data, plotname) in enumerate(zip(axar, imgarrays, plotlist)):

    print("%s plot. axar[%s] '%s' data shape: %s" % (title, axidx, plotname, data.shape))
    print("---------------------------------------------------------------")
    # We are going to use a divergent color scheme centered around zero,
    # so we need to find largest absolute value of the data and use that
    # as the endpoints for the color-scaling.
    print("min/max ignoring nans: %s %s" % (np.nanmin(data), np.nanmax(data)))
    xval = np.nanmax(np.abs(data))
    print("Color map range for ax[%s]: %s" % (axidx, xval))

    # It is also handy to mask out the values that are zero (no error)
    # or riduculously close to zero (effectively zero)
    print("Number of non nan values: ", np.count_nonzero(~np.isnan(data)))

    data = np.ma.masked_equal(data, 0)
    print("Number of values after masking values equal to zero:", data.count())

    maskclose = np.isclose(data, np.zeros(data.shape))
    data = np.ma.masked_array(data, mask=maskclose)
    print("Number of values after masking values close to zero:", data.count())

    data = np.ma.masked_invalid(data)
    print("Remaining data after masking invalid data: ", data.count())

    print("min/max values in data array:", data.min(), data.max())

    # Transform data to 2D shape for showing as an image
    data = data.reshape(len(data)/12, 12)

    # Not totally sure how this part works, but it seems to help make room
    # for the colorbar axes
    divider = make_axes_locatable(ax)
    colax = divider.append_axes("bottom", size="3%", pad="10%")

    # Use this colormap for the error and delta plots
    cm1 = plt.cm.coolwarm
    cm1.set_bad('white',1.0)
    cm1.set_over('yellow') # <- nothing should be ouside the colormap range...
    cm1.set_under('orange')

    # Display the data as an image
    im = ax.imshow(
          data,
          interpolation="nearest",
          cmap=cm1, vmin=-np.nanmax(np.abs(data)), vmax=np.nanmax(np.abs(data)),
          aspect='auto' # helps with non-square images...
        )

    # Set some tick mark stuff
    loc = MultipleLocator(base=1.0) # this locator puts ticks at regular intervals
    ax.xaxis.set_major_locator(loc)
    ax.grid(True, axis='both')

    cbar = plt.colorbar(im, cax=colax, orientation='horizontal', format="%0.8f", ticks=mtkr.MaxNLocator(6, prune=None))

    # use the other colormap for the error divided by delta plot
    # and adjust the tick labels

    # For the (error/delta) plot it is nice to have a different colormap
    # and slightly different colorbar settings
    cm2 = plt.cm.RdYlGn_r
    cm2.set_bad('white',1.0)
    cm2.set_over('pink') # <- nothing should be ouside the colormap range...
    cm2.set_under('green')

    if plotname == 'err/delta':
      im.cmap = cm2
      cbar = plt.colorbar(im, cax=colax, orientation='horizontal', format="%0.2f", ticks=mtkr.MaxNLocator(6, prune=None))

    plt.setp(colax.xaxis.get_majorticklabels(), rotation=90)

    #axar[axidx].yaxis.set_visible(False)
    #axar[axidx].yaxis.set_major_locator(mtkr.MultipleLocator(5))
    #axar[axidx].tick_params(axis='y', direction='in', length=3, width=.5, colors='k', labelleft='off', labelright='off')

    ax.set_xlabel("Month")
    ax.xaxis.set_major_locator(mtkr.MaxNLocator(5, integer=True)) # 5 seems to be magic number; works with zooming.
    ax.tick_params(axis='x', direction='in', length=3, width=.5, colors='k')

    # end of loop over axes/images
    print("")

  # Turn the y axis on for the leftmost plot
  axar[0].yaxis.set_visible(True)
  axar[0].set_ylabel("Year")
  #axar[0].tick_params(axis='y', direction='out', length=4, width=1, colors='k', labelleft='on', labelright='off')


  # set the titles for the subplots - rudimentady line-wrapping for long titles
  assert len(axar) == len(plotlist) # zip silently trucates longer list
  for x in zip(axar, plotlist):
    if len(x[1].split(' ')) > 3:
      print(x[1].split(' '))
      l1 = ' '.join(x[1].split(' ')[0:3])
      l2 = ' '.join(x[1].split(' ')[3:])
      newX1 = "\n".join([l1, l2])
      x[0].set_title(newX1)
    else:
      x[0].set_title(x[1])

  if save:
    file_name = os.path.join(SAVE_DIR, title + "_" + savetag + "_diagnostic." + format)
    print("saving file: %s" % file_name)
    plt.savefig(file_name)
  else:
    plt.show(block=True)


def plot_tests(test_list, **kwargs):
  #title =  "------  %s  ------" % t
  for t in test_list:
    data = compile_table_by_year(t, **kwargs)

    np.loadtxt(StringIO(data), skiprows=1)
    [_f for _f in data.split("\n")[0].split(" ") if _f]
    df = pd.DataFrame(
            np.loadtxt(StringIO(data), skiprows=1),
            columns=[_f for _f in data.split("\n")[0].split(" ") if _f]
        )

    # fails to read some columns with many zeros - whole
    # column ends up NaN. May need to update pandas version
    #df = pd.read_csv(StringIO(data), header=0, delim_whitespace=True, na_values='NULL')

    print("plotting dataframe...")
    dfp = df.plot(subplots=True)#, grid=False)

    print("using matplotlib show...")
    plt.show(block=True)

def run_tests(test_list, **kwargs):

    # write to file (w2f)
    if 'w2f' in kwargs:
        outfile = kwargs['w2f']
    else:
        outfile = None

    if outfile:
        folder, fname = os.path.split(outfile)
        if folder != '':

            try:
                os.makedirs(folder) # keyword argument 'exists_ok=True' is for python 3.4+
            except OSError:
                if not os.path.isdir(folder):
                    raise

        print("clearing output file: ", outfile)
        with open(outfile, 'w') as f:
            f.write("")


    for t in test_list:
        title =  "------  %s  ------" % t
        data = compile_table_by_year(t, **kwargs)

        # print to console (p2c)
        if 'p2c' in kwargs and kwargs['p2c'] == True:
            print(title)
            print(data)
        if outfile != None:
            with open(outfile, 'a') as f:
                print("appending to file: ", outfile)
                f.write(title); f.write("\n")
                f.write(data)

def compile_table_by_year(test_case, **kwargs):

    jfiles = file_loader(**kwargs)

    # map 'test case' strings to various test and 
    # reporting functions we have written in the module.
    function_dict = {
        'N_soil_balance':             Check_N_cycle_soil_balance,
        'N_veg_balance':              Check_N_cycle_veg_balance,
        'C_soil_balance':             Check_C_cycle_soil_balance,
        'C_veg_balance':              Check_C_cycle_veg_balance,
        'C_veg_vascular_balance':     Check_C_cycle_veg_vascular_balance,
        'C_veg_nonvascular_balance':  Check_C_cycle_veg_nonvascular_balance,
        'report_soil_C':              Report_Soil_C
    }

    check_func = function_dict[test_case]

    header = check_func(0, header=True)

    table_data = ""
    for idx, jfile in enumerate(jfiles):
        with open(jfile, 'r') as f:
            jdata = json.load(f)

        prev_jdata = None
        if idx > 0:
            with open(jfiles[idx-1], 'r') as prev_jf:
                prev_jdata = json.load(prev_jf)

        row = check_func(idx, jd=jdata, pjd=prev_jdata, header=False)

        table_data = table_data + row

    full_report = header + table_data

    return full_report

def sum_across(key, jdata, xsec):
  '''
  Parameters
  ----------
  key : str
    The key to lookup in the json data object.
  jdata : json object
    A json data object (output from dvmdostem)
  xsec : str
    A string, ('all', 'vasc', 'nonvasc') specifying which PFTs to sum over.

  Returns
  -------
  total : float
    The sum of the values for 'key' across the cross-section specified by 'xsec'.
  '''
  # Setup a dict for mapping community type numbers
  # to differnet combos of PFTs for vascular/non-vascular
  # We should really build this programatically based on the parameter files
  # or something! Bound to get out of whack if we try to maintain manually!
  CMTLU = {
    1: { # Black spruce - split guesses by looking at parameters/cmt_calparbgc.txt
      'all'      : [0,1,2,3,4,5,6,7,8,9],
      'vasc'     : [0,1,2,3,4,5,6],
      'nonvasc'  : [7, 8]
    },
    4: {
      'all'      : [0,1,2,3,4,5,6,7,8,9], # <- ?? need to include 9 ??
      'vasc'     : [0,1,2,3,4,5,6],
      'nonvasc'  : [7,8]
    },
    5: {
      'all'      : [0,1,2,3,4,5,6,7,8,9],
      'vasc'     : [0,1,2,3,4],
      'nonvasc'  : [5,6,7]
    },
    6: {}
  }

  CMT = int(jdata['CMT'].lstrip('CMT')) # reduce from string like 'CMT01'
  if CMT not in list(CMTLU.keys()):
    print("%% ERROR! {:%>65s}".format('%'))
    print(" YOU MIGHT BE THE FIRST TO WORK WITH THIS COMMUNITY TYPE!")
    print(" ADD THE VASCULAR/NON-VASCULAR SPLIT TO THE LOOKUP TABLE")
    print(" IN THE sum_across() FUNCTION.")
    print("%%%%%%%%%%{:%>65s}".format('%'))
    sys.exit(-1)

  pfts = CMTLU[CMT][xsec]
  total = np.nan
  if jdata != None:
    total = 0
    for pft in ['PFT%i'%i for i in pfts]:
      if ( type(jdata[pft][key]) == dict ): # sniff out compartment variables
        if len(jdata[pft][key]) == 3:
          total += jdata[pft][key]["Leaf"] + jdata[pft][key]["Stem"] + jdata[pft][key]["Root"]
        else:
          print("Error?: incorrect number of compartments...")
      else:
        total += jdata[pft][key]

  return total

def ecosystem_sum_soilC(jdata):
  total = np.nan
  if jdata != None:
    total = 0
    total += jdata["RawCSum"]
    total += jdata["SomaSum"]
    total += jdata["SomcrSum"]
    total += jdata["SomprSum"]
#    total += jdata["CarbonMineralSum"]
#    total += jdata["CarbonDeep"]
#    total += jdata["CarbonShallow"]
    total += jdata["WoodyDebrisC"]
  return total

class DeltaError(object):
  '''Simply used to allow convenient access to data via . operator.'''
  def __init__(self, _d, _e):
    self.delta = _d
    self.err = _e

def bal_C_standing_dead(cjd, pjd):
  delta = np.nan
  if pjd != None:
    delta = cjd["StandingDeadC"] - pjd["StandingDeadC"]
  sum_of_fluxes = cjd["BurnAbvVeg2DeadC"] - cjd["D2WoodyDebrisC"]
  err = delta - sum_of_fluxes
  return DeltaError(delta, err)

def bal_N_standing_dead(cjd, pjd):
  delta = np.nan
  if pjd != None:
    delta = cjd["StandingDeadN"] - pjd["StandingDeadN"]
  sum_of_fluxes = cjd["BurnAbvVeg2DeadN"] - cjd["D2WoodyDebrisN"]
  err = delta - sum_of_fluxes
  return DeltaError(delta, err)

def bal_C_woody_debris(cjd, pjd):
  delta = np.nan
  if pjd != None:
    delta = cjd["WoodyDebrisC"] - pjd["WoodyDebrisC"]
  sum_of_fluxes = cjd["D2WoodyDebrisC"] - cjd["RHwdeb"]
  err = delta - sum_of_fluxes
  return DeltaError(delta, err)

def bal_N_woody_debris(cjd, pjd):
  delta = np.nan
  if pjd != None:
    delta = cjd["WoodyDebrisN"] - pjd["WoodyDebrisN"]

  # Avoid divide by zero problem - assume no RH if there is no WoodyDebrisC
  if cjd["WoodyDebrisC"] != 0:
    sum_of_fluxes = cjd["D2WoodyDebrisN"] - (cjd["RHwdeb"] * cjd["WoodyDebrisN"]/cjd["WoodyDebrisC"])
  else:
    sum_of_fluxes = cjd["D2WoodyDebrisN"]

  err = delta - sum_of_fluxes
  return DeltaError(delta, err)

def bal_C_soil(curr_jd, prev_jd):
  delta = np.nan
  if prev_jd != None:
    delta = ecosystem_sum_soilC(curr_jd) - ecosystem_sum_soilC(prev_jd)

  sum_of_fluxes = sum_across("LitterfallCarbonAll", curr_jd, 'all') \
                  + sum_across("MossDeathC", curr_jd, 'all') \
                  + curr_jd["BurnVeg2SoiAbvVegC"] \
                  + curr_jd["BurnVeg2SoiBlwVegC"] \
                  + curr_jd["D2WoodyDebrisC"] \
                  - curr_jd["RH"] \
                  - curr_jd["BurnSoi2AirC"]

  err = delta - sum_of_fluxes
  return DeltaError(delta, err)

def bal_C_veg(curr_jd, pjd, xsec='all'):
  '''
  Parameters
  ----------
  curr_jd : json data
    Current month.
  pjd : json data
    Previous month.
  xsec : str
    A string specifying the "cross section" of pfts to look. One of:
    'all', 'vasc', 'nonvasc'.

  Returns
  -------
  d : DeltaError
    A DeltaError object.
  '''

  delta = np.nan
  if pjd != None:
    delta = sum_across("VegCarbon", curr_jd, xsec) - sum_across("VegCarbon", pjd, xsec)

  if xsec == 'all':
    burn_flux = curr_jd["BurnVeg2AirC"] \
                + curr_jd["BurnVeg2SoiAbvVegC"] \
                + curr_jd["BurnVeg2SoiBlwVegC"] \
                + curr_jd["BurnAbvVeg2DeadC"]

    sum_of_fluxes = sum_across("NPPAll", curr_jd, xsec) \
                    - sum_across("LitterfallCarbonAll", curr_jd, xsec) \
                    - sum_across("MossDeathC", curr_jd, xsec) \
                    - burn_flux
  if xsec == 'vasc':
    sum_of_fluxes = sum_across("NPPAll", curr_jd, xsec) \
                    - sum_across("LitterfallCarbonAll", curr_jd, xsec)

  if xsec == 'nonvasc':
    sum_of_fluxes = sum_across("NPPAll", curr_jd, xsec) \
                    - sum_across("LitterfallCarbonAll", curr_jd, xsec) \
                    - sum_across("MossDeathC", curr_jd, xsec)

  err = delta - sum_of_fluxes
  return DeltaError(delta, err)

def bal_N_soil_org(jd, pjd):
  delta = np.nan
  if pjd != None:
    delta = jd["OrganicNitrogenSum"] - pjd["OrganicNitrogenSum"]

  sum_of_fluxes = sum_across("LitterfallNitrogenPFT", jd, 'all') \
                  + jd["MossdeathNitrogen"] \
                  + jd["BurnVeg2SoiAbvVegN"] \
                  + jd["BurnVeg2SoiBlwVegN"] \
                  - jd["NetNMin"] \
                  - jd["BurnSoi2AirN"]

  err = delta - sum_of_fluxes
  return DeltaError(delta, err)

def bal_N_soil_avl(jd, pjd):
  delta = np.nan
  if pjd != None:
    delta = jd["AvailableNitrogenSum"] - pjd["AvailableNitrogenSum"]
  sum_of_fluxes = (jd["NetNMin"] + jd["AvlNInput"]) - (jd["NExtract"] + jd["AvlNLost"])
  err = delta - sum_of_fluxes
  return DeltaError(delta, err)

def bal_N_veg_tot(jd, pjd, xsec='all'):

  delta = np.nan
  if pjd != None:
    delta = sum_across("NAll", jd, xsec) - sum_across("NAll", pjd, xsec)

  if xsec == 'all':
    burn_flux = jd["BurnVeg2AirN"] \
                + jd["BurnVeg2SoiAbvVegN"] \
                + jd["BurnVeg2SoiBlwVegN"] \
                + jd["BurnAbvVeg2DeadN"]

    sum_of_fluxes = sum_across("TotNitrogenUptake", jd, xsec) \
                    - sum_across("LitterfallNitrogenPFT", jd, xsec) \
                    - jd["MossdeathNitrogen"] \
                    - burn_flux

  if xsec == 'vasc':
    sum_of_fluxes = sum_across("TotNitrogenUptake", jd, xsec) \
                    - sum_across("LitterfallNitrogenPFT", jd, xsec)

  if xsec == 'nonvasc':
    sum_of_fluxes = sum_across("TotNitrogenUptake", jd, xsec) \
                    - sum_across("LitterfallNitrogenPFT", jd, xsec) \
                    - jd["MossdeathNitrogen"] 

  err = delta - sum_of_fluxes

  return DeltaError(delta, err)

def bal_N_veg_str(jd, pjd, xsec='all'):

  delta = np.nan
  if pjd != None:
    delta = sum_across("VegStructuralNitrogen", jd, xsec) - sum_across("VegStructuralNitrogen", pjd, xsec) # <-- will sum compartments

  if xsec == 'all':
    burn_flux = jd["BurnVeg2AirN"] \
                + jd["BurnVeg2SoiAbvVegN"] \
                + jd["BurnVeg2SoiBlwVegN"] \
                + jd["BurnAbvVeg2DeadN"]

    sum_of_fluxes = sum_across("StNitrogenUptake", jd, xsec) \
                    + sum_across("NMobil", jd, xsec) \
                    - sum_across("LitterfallNitrogenPFT", jd, xsec) \
                    - jd["MossdeathNitrogen"] \
                    - sum_across("NResorb", jd, xsec) \
                    - burn_flux

  if xsec == 'vasc':
    sum_of_fluxes = sum_across("StNitrogenUptake", jd, xsec) \
                    + sum_across("NMobil", jd, xsec) \
                    - sum_across("LitterfallNitrogenPFT", jd, xsec) \
                    - sum_across("NResorb", jd, xsec)


  if xsec == 'nonvasc':
    sum_of_fluxes = sum_across("StNitrogenUptake", jd, xsec) + \
                    sum_across("NMobil", jd, xsec) - \
                    jd["MossdeathNitrogen"] - \
                    sum_across("NResorb", jd, xsec)

  err = delta - sum_of_fluxes
  return DeltaError(delta, err)

def bal_N_veg_lab(jd, pjd, xsec='all'):

  delta = np.nan
  if pjd != None:
    delta = sum_across("VegLabileNitrogen", jd, xsec) - sum_across("VegLabileNitrogen", pjd, xsec)

  if xsec=='all' or xsec == 'vasc' or xsec == 'nonvasc':
    sum_of_fluxes = sum_across("LabNitrogenUptake", jd, xsec) \
                    + sum_across("NResorb", jd, xsec) \
                    - sum_across("NMobil", jd, xsec)

  err = delta - sum_of_fluxes
  return DeltaError(delta, err)


def Check_N_cycle_veg_balance(idx, header=False, jd=None, pjd=None):
    '''Checking....?'''
    if header:
        return "{:<4} {:>6} {:>2} {:>10} {:>10} {:>10} {:>10} {:>10} {:>10} {:>10} {:>10} {:>10}\n".format(
                "idx", "yr", "m", "errT", "errS", "errL", "deltaN", "delNStr", "delNLab", "sumFlxT","sumFlxS", "sumFlxL"
        )
    else:

        sum_str_N_flux = jd["StNitrogenUptakeAll"] - (sum_across("LitterfallNitrogenPFT", jd, 'all') + jd["MossdeathNitrogen"]) + sum_across("NMobil", jd, 'all') -  sum_across("NResorb", jd, 'all')
        sum_lab_N_flux = sum_across("LabNitrogenUptake", jd, 'all') + sum_across("NResorb", jd, 'all') - sum_across("NMobil", jd, 'all') 

        return  "{:<4} {:>6} {:>2} {:>10.4f} {:>10.4f} {:>10.3f} {:>10.4f} {:>10.4f} {:>10.3f} {:>10.4f} {:>10.4f} {:>10.3f}\n".format(
                idx,
                jd["Year"],
                jd["Month"],
                bal_N_veg_tot(jd, pjd, xsec='all').err,
                bal_N_veg_str(jd, pjd, xsec='all').err,
                bal_N_veg_lab(jd, pjd, xsec='all').err,

                bal_N_veg_tot(jd, pjd, xsec='all').delta,
                bal_N_veg_str(jd, pjd, xsec='all').delta,
                bal_N_veg_lab(jd, pjd, xsec='all').delta,

                sum_str_N_flux + sum_lab_N_flux,
                sum_str_N_flux,
                sum_lab_N_flux,
        )

def Check_N_cycle_soil_balance(idx, header=False, jd=None, pjd=None):

    if header:
      return "{:<6} {:<6} {:<2} {:>10} {:>10} {:>10} {:>10}\n".format("idx","yr","m","errORGN","delORGN","errAVL","delAVL" )

    return "{:<6} {:<6} {:<2} {:>10.4f} {:>10.4f} {:>10.4f} {:>10.4f}\n".format(
        idx,
        jd["Year"],
        jd["Month"],
        bal_N_soil_org(jd, pjd).err,
        bal_N_soil_org(jd, pjd).delta,
        bal_N_soil_avl(jd, pjd).err,
        bal_N_soil_avl(jd, pjd).delta
    )

def Check_C_cycle_soil_balance(idx, header=False, jd=None, pjd=None):
    if header:
        return '{:<4} {:>2} {:>4} {:>8} {:>10} {:>10}     {:>10} {:>10} {:>10} {:>10} {:>10}\n'.format(
               'idx', 'm', 'yr', 'err', 'deltaC', 'lfmdcrh', 'sumsoilC', 'ltrfal', 'mossdeathc', 'RH', 'checksum'
        )
    else:
      return "{:<4} {:>2} {:>4} {:>8.2f} {:>10.2f} {:>10.2f}     {:>10.2f} {:>10.2f} {:>10.2f} {:>10.2f} {:>10.2f}\n".format(
              idx,
              jd["Month"],
              jd["Year"],
              bal_C_soil(jd, pjd).err,
              bal_C_soil(jd, pjd).delta,
              sum_across("LitterfallCarbonAll", jd, 'all')  + sum_across("MossDeathC", jd, 'all') - jd["RH"],
              ecosystem_sum_soilC(jd),
              sum_across("LitterfallCarbonAll", jd, 'all') ,
              sum_across("MossDeathC", jd, 'all'),
              jd['RH'], 
              (jd['RHsomcr']+jd['RHsompr']+jd['RHsoma']+jd['RHraw']+jd['RHmossc']+jd['RHwdeb']),
          )

def Report_Soil_C(idx, header=False, jd=None, pjd=None):
    '''Create a table/report for Soil Carbon'''
    if header:
        return '{:<4} {:>4} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9}\n'.format(
               'idx', 'yr', 'RHtot', 'RHrawc', 'RHsomac', 'RHsomprc','RHsomcrc','RHmossc','RHwdeb','Lfc+dmsc','rawc','soma','sompr','somcr','dmossc'
            )
    else:
        # FIll in the table with data...
        return "{:<4} {:>4} {:>9.2f} {:>9.2f} {:>9.2f} {:>9.2f} {:>9.2f} {:>9.2f} {:>9.2f} {:>9.2f} {:>9.2f} {:>9.2f} {:>9.2f} {:>9.2f} {:>9.2f}\n".format(
                idx,
                jd['Year'],
                jd['RH'],
                jd['RHraw'],
                jd['RHsoma'],
                jd['RHsompr'],
                jd['RHsomcr'],
                jd['RHmossc'],
                jd['RHwdeb'],
                sum_across("LitterfallCarbonAll", jd, 'all') + jd['MossDeathC'],
                jd['RawCSum'],
                jd['SomaSum'],
                jd['SomprSum'],
                jd['SomcrSum'],

            )

def Check_C_cycle_veg_balance(idx, header=False, jd=None, pjd=None):
    '''Should duplicate Vegetation_Bgc::deltastate()'''
    if header:
        return '{:<4} {:>2} {:>4} {:>10} {:>10} {:>15}     {:>10} {:>15} {:>15} {:>15}\n'.format(
               'idx', 'm', 'yr', 'err', 'deltaC', 'NPP-LFallC-mdc', 'mdc', 'VegC', 'NPP', 'LFallC' )
    else:
        # FIll in the table with data...
        return '{:<4d} {:>2} {:>4} {:>10.3f} {:>10.3f} {:>15.3f}     {:>10.3f} {:>15.3f} {:>15.3f} {:>15.3f}\n'.format(
                idx,
                jd['Month'],
                jd['Year'],
                bal_C_veg(jd, pjd, xsec='all').err,
                bal_C_veg(jd, pjd, xsec='all').delta,

                sum_across("NPPAll", jd, 'all')  - sum_across("LitterfallCarbonAll", jd, 'all')  - sum_across("MossDeathC", jd, 'all'),
                sum_across("MossDeathC", jd, 'all'),
                sum_across("VegCarbon", jd, 'all'), 
                sum_across("NPPAll", jd, 'all') ,
                sum_across("LitterfallCarbonAll", jd, 'all') ,
            )

def Check_C_cycle_veg_vascular_balance(idx, header=False, jd=None, pjd=None):
    '''Should duplicate Vegetation_Bgc::deltastate()'''

    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    print("DEPRECATED! Proof-read before trusting!")
    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")

    # vascular PFT list (CMT05)
    vascular = [0,1,2,3,4]

    if header:
        return '{:<4} {:>2} {:>4} {:>10} {:>10} {:>15} {:>10} {:>15} {:>15} {:>15}\n'.format(
               'idx', 'm', 'yr', 'err', 'deltaC', 'NPP-LFallC-mdc', 'mdc', 'VegC', 'NPP', 'LFallC' )
    else:
        return '{:<4d} {:>2} {:>4} {:>10.3f} {:>10.3f} {:>15.3f} {:>10.3f} {:>15.3f} {:>15.3f} {:>15.3f}\n'.format(
                idx,
                jd['Month'],
                jd['Year'],

                bal_C_veg(jd, pjd, xsec='vasc').err,
                bal_C_veg(jd, pjd, xsec='vasc').delta,

                sum_across("NPPAll", jd, 'vasc')  - sum_across("LitterfallCarbonAll", jd, 'vasc')  - sum_across("MossDeathC",jd,'vasc'),

                sum_across("MossDeathC",jd, 'vasc'),
                sum_across("VegCarbon", jd, 'vasc'), 
                sum_across("NPPAll", jd, 'vasc'),
                sum_across("LitterfallCarbonAll", jd, 'vasc')
            )

def Check_C_cycle_veg_nonvascular_balance(idx, header=False, jd=None, pjd=None):
    '''Should duplicate Vegetation_Bgc::deltastate()'''

    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    print("DEPRECATED! Proof-read before trusting!")
    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")

    # non-vascular PFT list (CMT05)
    non_vasc = [5,6,7]

    if header:
        return '{:<4} {:>2} {:>4} {:>10} {:>10} {:>15} {:>10} {:>15} {:>15} {:>15}\n'.format(
               'idx', 'm', 'yr', 'err', 'deltaC', 'NPP-LFallC-mdc', 'mdc', 'VegC', 'NPP', 'LFallC' )
    else:

        # FIll in the table with data...
        return '{:<4d} {:>2} {:>4} {:>10.3f} {:>10.3f} {:>15.3f} {:>10.3f} {:>15.3f} {:>15.3f} {:>15.3f}\n'.format(
                idx,
                jd['Month'],
                jd['Year'],

                bal_C_veg(jd, pjd, xsec='nonvasc').err,
                bal_C_veg(jd, pjd, xsec='nonvasc').delta,

                sum_across("NPPAll", jd, 'nonvasc')  - sum_across("LitterfallCarbonAll", jd, 'nonvasc')  - sum_across("MossDeathC", jd, 'nonvasc'),
                sum_across("MossDeathC", jd, 'nonvasc'),
                sum_across("VegCarbon", jd, 'nonvasc'), 
                sum_across("NPPAll", jd, 'nonvasc') ,
                sum_across("LitterfallCarbonAll", jd, 'nonvasc') ,
            )

if __name__ == '__main__':

  # Callback for SIGINT. Allows exit w/o printing stacktrace to users screen
  original_sigint = signal.getsignal(signal.SIGINT)
  signal.signal(signal.SIGINT, exit_gracefully)

  error_image_choices = [
    'C_soil',
    'N_soil_org', 'N_soil_avl',
    'C_veg', 'C_veg_vasc', 'C_veg_nonvasc',
    'N_veg_tot', 'N_veg_str', 'N_veg_lab',
    'N_veg_vasc_tot', 'N_veg_vasc_str', 'N_veg_vasc_lab',
    'N_veg_nonvasc_tot', 'N_veg_nonvasc_str', 'N_veg_nonvasc_lab',
    'C_standing_dead', 'C_woody_debris',
    'N_standing_dead', 'N_woody_debris'
  ]

  tab_reports_and_timeseries_choices = [
    'N_soil_balance',
    'N_veg_balance',
    'C_soil_balance',
    'C_veg_balance',
    'C_veg_vascular_balance',
    'C_veg_nonvascular_balance',
    'report_soil_C'
  ]

  # Make a table listing options for the help text
  t = itertools.zip_longest(error_image_choices, tab_reports_and_timeseries_choices)
  option_table = "\n".join(["{:>30} {:>30}".format(r[0], r[1]) for r in t])
  option_table = "\n" + option_table

  #
  # Setup the command line interface...
  #
  parser = argparse.ArgumentParser(

    formatter_class=argparse.RawDescriptionHelpFormatter,

      description=textwrap.dedent('''\
        Diagnostics plots for dvmdostem in calibration mode. 

        In general this program is designed to check that the sum of the fluxes
        computed and recorded by dvmdostem is comensurate with the changes in 
        pool values computed and recorded by dvmdostem. We have been calling 
        this an a-posteriori check of the C and N balance closure.

        This program provides two ways to look at this diagnostic information:
          - Error Image Plots
          - Tabular Reports

        This program can assess data over the entire duration of a model run or
        a user-specified slice. The Error Image Plots are better for looking at
        the big picture, while the tabular reports are better for analyzing a
        smaller slice of the timeseries.

        The Error Image Plot uses the y axis for simulation year and x axis for
        simulation month, creating a 2D image for the timeseries. Each pixel 
        in the images is colored based on the error value for that point in 
        time. To compute the error value, the program first computes a delta
        value for a given pool:

          delta = (current pool value) - (previous pool value)

        Then to compute the error value, the program substracts the sum of
        fluxes that should affect a give pool from the delta value for the pool:

          error = (delta) - (sum of fluxes)

        Ideally the error is zero. For each Error Image Plot this program also 
        generates a plot showing the pool deltas, and a plot showing the error
        values divided by the delta values.

        NOTE: 
          When there is fire, the str and lab N plots are kind of useless
          because the flux recorded in the json files is the total flux and
          the fluxes on the str and lab N pools is some proportion of the total.

        NOTE:

        NOTE:
          You must run dvmdostem such that it creates monthly json files!


        Error image and tabular report options
        %s
        ''' % (option_table)),
      epilog=textwrap.dedent('''\
        epilog text...''')
    )

  parser.add_argument('-s', '--slice', default='', type=str,
      help="A custom file slice string")

  parser.add_argument('-a', '--from-archive', default=False,
      help=textwrap.dedent('''Generate plots from an archive of json files, 
          instead of the normal /tmp directory.'''))

  parser.add_argument('-i', '--error-image', default=False, nargs='+',
      choices=error_image_choices+['all'], metavar="P",
      help=textwrap.dedent('''Generate at 2D image plot of the error''')
  )

  parser.add_argument('-p', '--plot-timeseries', default=False, nargs='+',
      choices=tab_reports_and_timeseries_choices, metavar="P",
      help=textwrap.dedent('''Generate timeseries''')
  )

  parser.add_argument('-c', '--tab-reports', default=False, nargs='+',
      choices=tab_reports_and_timeseries_choices, metavar="P",
      help=textwrap.dedent('''Generate tabular reports''')
  )

  parser.add_argument('--save-plots', action='store_true', default=False,
      help=textwrap.dedent('''\
        Saves plots to 'diagnostics-plots/' subdirectory instead of displaying
        them in a pop-up interactive window.. Overwrites any existing plots.'''))

  parser.add_argument('--save-tag', default='',
      help=textwrap.dedent('''\
        A tag to add to the output file's name, e.g.: "C_soil-<TAG>-diagnostics.png"'''))

  parser.add_argument('--save-format', default="pdf",
      choices=['pdf', 'png', 'jpg'],
      help="Choose a file format to use for saving plots.")

  print("Parsing command line arguments...")
  args = parser.parse_args()
  print("Command line argument settings:")
  for k, v in vars(args).items():
    print("  %s = %s" % (k, v))

  slstr = args.slice
  archive = args.from_archive
  save = args.save_plots
  imgformat = args.save_format
  savetag = args.save_tag

  SAVE_DIR = "diagnostics-plots"

  if args.error_image == ['all']:
    errimgs = error_image_choices
  else:
    errimgs = args.error_image

  if save:
    # Clean up old plots,
    if os.path.isdir(SAVE_DIR) or os.path.isfile(SAVE_DIR):
      print("Cleaning up existing plots (in %s)..." % SAVE_DIR)
      shutil.rmtree(SAVE_DIR)

    print("Making an empty directory to save plots in...")
    os.makedirs(SAVE_DIR)


  if args.error_image:
    print("Creating error image plots...")
    error_image(plotlist=errimgs, fileslice=slstr, save_plots=save, save_format=imgformat, fromarchive=archive, savetag=savetag)

  if args.plot_timeseries:
    print("Creating timeseries plots...")
    plot_tests(args.plot_timeseries, fileslice=slstr)

  if args.tab_reports:
    print("Creating tabular reports...")
    run_tests(args.tab_reports, fileslice=slstr, p2c=True)



