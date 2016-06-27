#!/usr/bin/env python

import os
import glob
import json
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

import sys
if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO


def analyze(cjd, pjd):
  '''Extract every ounce of knowledge from a pair of json data objects.

  Returns a dict with all the data.
  '''

  vasc = [0,1,2,3,4]
  nonvasc = [5,6,7]

  results = {}

  results['C veg err'] = bal_C_veg(cjd, pjd).err
  results['C veg del'] = bal_C_veg(cjd, pjd).delta
  results['C veg vasc err'] = bal_C_veg(cjd, pjd, pftlist=vasc).err
  results['C veg vasc del'] = bal_C_veg(cjd, pjd, pftlist=vasc).delta
  results['C veg nonvasc err'] = bal_C_veg(cjd, pjd, pftlist=nonvasc).err
  results['C veg nonvasc del'] = bal_C_veg(cjd, pjd, pftlist=nonvasc).delta

  results['C soil err'] = bal_C_soil(cjd, pjd).err
  results['C soil del'] = bal_C_soil(cjd, pjd).delta

  results['N veg err tot'] = bal_N_veg_tot(cjd, pjd).err
  results['N veg err str'] = bal_N_veg_str(cjd, pjd).err
  results['N veg err lab'] = bal_N_veg_lab(cjd, pjd).err
  results['N soil err org'] = bal_N_soil_org(cjd, pjd).err
  results['N soil err avl'] = bal_N_soil_avl(cjd, pjd).err

  results['N veg vasc err tot'] = bal_N_veg_tot(cjd, pjd, pftlist=vasc).err
  results['N veg vasc err str'] = bal_N_veg_str(cjd, pjd, pftlist=vasc).err
  results['N veg vasc err lab'] = bal_N_veg_lab(cjd, pjd, pftlist=vasc).err

  results['N veg nonvasc err tot'] = bal_N_veg_tot(cjd, pjd, pftlist=nonvasc).err
  results['N veg nonvasc err str'] = bal_N_veg_str(cjd, pjd, pftlist=nonvasc).err
  results['N veg nonvasc err lab'] = bal_N_veg_lab(cjd, pjd, pftlist=nonvasc).err

  return results

def file_loader(**kwargs):
  '''Returns a list of files to open'''
  if 'fileslice' in kwargs:
      slice_string = kwargs['fileslice']
      # parse string into slice object
      # https://stackoverflow.com/questions/680826/python-create-slice-object-from-string/681949#681949
      custom_slice = slice(*map(lambda x: int(x.strip()) if x.strip() else None, slice_string.split(':')))
  else:
      custom_slice = slice(None,None,None)

  jfiles = glob.glob("/tmp/dvmdostem/calibration/monthly/*.json")

  print "Custom file slice:", custom_slice
  jfiles = jfiles[custom_slice]

  return jfiles

def error_image(**kwargs):
  '''Returns an array with dimensions (yrs,months) for the error variable.'''

  if "plotlist" not in kwargs:
    plotlist = ['C veg err', 'C soil err', 'N veg err tot', 'N veg err str', 'N veg err lab', 'N soil err org', 'N soil err avl']
  else:
    plotlist = kwargs["plotlist"]


  from mpl_toolkits.axes_grid1 import make_axes_locatable
  from matplotlib.colors import LogNorm
  from matplotlib.ticker import MultipleLocator
  from matplotlib.ticker import MaxNLocator
  import matplotlib.ticker as mtkr

  jfiles = file_loader(**kwargs)

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
  imgarrays = [np.copy(empty) for i in plotlist]

  # Run over all the files, calculating all the derived 
  # diagnostics.
  pjd = None
  for idx, jfile in enumerate(jfiles):
    with open(jfile, 'r') as f:
        jdata = json.load(f)

    diagnostics = analyze(jdata, pjd)

    for pltnum, key in enumerate(plotlist):
      imgarrays[pltnum][idx+m1] = diagnostics[key]

    pjd = jdata


  # undertake the plotting of the now full arrays..
  fig, axar = plt.subplots(1, len(imgarrays), sharex=True, sharey=True)
  for axidx, data in enumerate(imgarrays):

    # We are going to use a divergent color scheme centered around zero,
    # so we need to find largest absolute value of the data and use that
    # as the endpoints for the color-scaling.
    xval = np.nanmax(np.abs(data))
    print "Color map range for ax[%s]: %s" % (axidx, xval)

    # It is also handy to mask out the values that are zero (no error)
    # or riduculously close to zero (effectively zero)
    print "before mask: ", np.count_nonzero(~np.isnan(data))
    data = np.ma.masked_equal(data, 0)
    maskclose = np.isclose(data, np.zeros(data.shape))
    data = np.ma.masked_array(data, mask=maskclose)
    data = np.ma.masked_invalid(data)
    print "after mask: ", data.count()

    im = axar[axidx].imshow(
          data.reshape(len(data)/12, 12),
          interpolation="nearest",
          cmap="coolwarm", vmin=-xval, vmax=xval,
          aspect='auto' # helps with non-square images...
        )
    axar[axidx].grid(False, axis='both')

    #axar[axidx].yaxis.set_visible(False)
    #axar[axidx].yaxis.set_major_locator(mtkr.MultipleLocator(5))
    #axar[axidx].tick_params(axis='y', direction='in', length=3, width=.5, colors='k', labelleft='off', labelright='off')

    axar[axidx].set_xlabel("Month")
    axar[axidx].xaxis.set_major_locator(mtkr.MaxNLocator(5, integer=True)) # 5 seems to be magic number; works with zooming.
    axar[axidx].tick_params(axis='x', direction='in', length=3, width=.5, colors='k')

    divider = make_axes_locatable(axar[axidx])
    cwm = plt.cm.coolwarm
    cwm.set_bad('white',1.0)
    cwm.set_over('yellow',1.0) # <- nothing should be ouside the colormap range...
    cwm.set_under('orange',1.0)
    colax = divider.append_axes("bottom", size="3%", pad="10%")
    cbar = plt.colorbar(im, cax=colax, orientation='horizontal', format="%0.8f", ticks=mtkr.MaxNLocator(6, prune=None))
    plt.setp(colax.xaxis.get_majorticklabels(), rotation=90)

  # Turn the y axis on for the leftmost plot
  axar[0].yaxis.set_visible(True)
  axar[0].set_ylabel("Year")
  #axar[0].tick_params(axis='y', direction='out', length=4, width=1, colors='k', labelleft='on', labelright='off')


  # set the titles for the subplots
  for x in zip(axar, plotlist):
    x[0].set_title(x[1])

  plt.tight_layout()
  plt.show(block=True)

def plot_tests(test_list, **kwargs):
  #title =  "------  %s  ------" % t
  for t in test_list:
    data = compile_table_by_year(t, **kwargs)

    np.loadtxt(StringIO(data), skiprows=1)
    filter(None,data.split("\n")[0].split(" "))
    df = pd.DataFrame(
            np.loadtxt(StringIO(data), skiprows=1),
            columns=filter(None,data.split("\n")[0].split(" "))
        )

    # fails to read some columns with many zeros - whole
    # column ends up NaN. May need to update pandas version
    #df = pd.read_csv(StringIO(data), header=0, delim_whitespace=True, na_values='NULL')

    print "plotting dataframe..."
    dfp = df.plot(subplots=True)#, grid=False)

    #from IPython import embed; embed()

    print "using matplotlib show..."
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

        print "clearing output file: ", outfile
        with open(outfile, 'w') as f:
            f.write("")


    for t in test_list:
        title =  "------  %s  ------" % t
        data = compile_table_by_year(t, **kwargs)

        # print to console (p2c)
        if 'p2c' in kwargs and kwargs['p2c'] == True:
            print title
            print data
        if outfile != None:
            with open(outfile, 'a') as f:
                print "appending to file: ", outfile
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

def eco_total(key, jdata, **kwargs):
  total = np.nan

  if jdata != None:
    if 'pftlist' in kwargs:
      pftlist = kwargs['pftlist']
    else:
      pftlist = range(0,10)
    total = 0
    for pft in ['PFT%i'%i for i in pftlist]:
      if ( type(jdata[pft][key]) == dict ): # sniff out compartment variables
        if len(jdata[pft][key]) == 3:
          total += jdata[pft][key]["Leaf"] + jdata[pft][key]["Stem"] + jdata[pft][key]["Root"]
        else:
          print "Error?: incorrect number of compartments..."
      else:
        total += jdata[pft][key]

  return total

def ecosystem_sum_soilC(jdata):
  total = np.nan
  if jdata != None:
    total = 0
    total += jdata["CarbonMineralSum"]
    total += jdata["CarbonDeep"]
    total += jdata["CarbonShallow"]
    total += jdata["DeadMossCarbon"]
  return total

class DeltaError(object):
  '''Simply used to allow convenient access to data via . operator.'''
  def __init__(self, _d, _e):
    self.delta = _d
    self.err = _e

def bal_C_soil(curr_jd, prev_jd):
  delta = np.nan
  if prev_jd != None:
    delta = ecosystem_sum_soilC(curr_jd) - ecosystem_sum_soilC(prev_jd)
  err = delta - (eco_total("LitterfallCarbonAll", curr_jd) + eco_total("MossDeathC", curr_jd) - curr_jd["RH"])
  return DeltaError(delta, err)

def bal_C_veg(curr_jd, pjd, **kwargs):
  delta = np.nan
  if pjd != None:
    delta = eco_total("VegCarbon", curr_jd, **kwargs) - eco_total("VegCarbon", pjd, **kwargs)
  err = delta - (eco_total("NPPAll", curr_jd, **kwargs) - eco_total("LitterfallCarbonAll", curr_jd, **kwargs) - eco_total("MossDeathC", curr_jd, **kwargs))
  return DeltaError(delta, err)

def bal_N_soil_org(jd, pjd):
  delta = np.nan
  if pjd != None:
    delta = jd["OrganicNitrogenSum"] - pjd["OrganicNitrogenSum"]
  err = delta - ( (eco_total("LitterfallNitrogenPFT", jd) + jd["MossdeathNitrogen"]) + jd["NetNMin"] )
  return DeltaError(delta, err)

def bal_N_soil_avl(jd, pjd):
  delta = np.nan
  if pjd != None:
    delta = jd["AvailableNitrogenSum"] - pjd["AvailableNitrogenSum"]
  err = delta - ( (jd["NetNMin"] + jd["AvlNInput"]) + (eco_total("TotNitrogenUptake", jd) + jd["AvlNLost"]) )
  return DeltaError(delta, err)

def bal_N_veg_tot(jd, pjd, **kwargs):
  delta = np.nan
  if pjd != None:
    delta = eco_total("NAll", jd, **kwargs) - eco_total("NAll", pjd, **kwargs)
  err = delta - eco_total("TotNitrogenUptake", jd, **kwargs) + (eco_total("LitterfallNitrogenPFT", jd, **kwargs) + jd["MossdeathNitrogen"])
  return DeltaError(delta, err)

def bal_N_veg_str(jd, pjd, **kwargs):
  delta = np.nan
  if pjd != None:
    delta = eco_total("VegStructuralNitrogen", jd, **kwargs) - eco_total("VegStructuralNitrogen", pjd, **kwargs) # <-- will sum compartments
  err = delta - (eco_total("StNitrogenUptake", jd, **kwargs) + eco_total("NMobil", jd, **kwargs)) + (eco_total("LitterfallNitrogenPFT", jd, **kwargs) + jd["MossdeathNitrogen"] + eco_total("NResorb", jd, **kwargs))
  return DeltaError(delta, err)

def bal_N_veg_lab(jd, pjd, **kwargs):
  delta = np.nan
  if pjd != None:
    delta = eco_total("VegLabileNitrogen", jd, **kwargs) - eco_total("VegLabileNitrogen", pjd, **kwargs)
  err = delta - (eco_total("LabNitrogenUptake", jd, **kwargs) + eco_total("NResorb", jd, **kwargs)) + eco_total("NMobil", jd, **kwargs)
  return DeltaError(delta, err)

def Check_N_cycle_veg_balance(idx, header=False, jd=None, pjd=None):
    '''Checking....?'''
    if header:
        return "{:<4} {:>6} {:>2} {:>10} {:>10} {:>10} {:>10} {:>10} {:>10} {:>10} {:>10} {:>10}\n".format(
                "idx", "yr", "m", "errT", "errS", "errL", "deltaN", "delNStr", "delNLab", "sumFlxT","sumFlxS", "sumFlxL"
        )
    else:

        sum_str_N_flux = jd["StNitrogenUptakeAll"] - (eco_total("LitterfallNitrogenPFT", jd) + jd["MossdeathNitrogen"]) + eco_total("NMobil", jd) -  eco_total("NResorb", jd)
        sum_lab_N_flux = eco_total("LabNitrogenUptake", jd) + eco_total("NResorb", jd) - eco_total("NMobil", jd) 

        return  "{:<4} {:>6} {:>2} {:>10.4f} {:>10.4f} {:>10.3f} {:>10.4f} {:>10.4f} {:>10.3f} {:>10.4f} {:>10.4f} {:>10.3f}\n".format(
                idx,
                jd["Year"],
                jd["Month"],
                bal_N_veg_tot(jd, pjd).err,
                bal_N_veg_str(jd, pjd).err,
                bal_N_veg_lab(jd, pjd).err,

                bal_N_veg_tot(jd, pjd).delta,
                bal_N_veg_str(jd, pjd).delta,
                bal_N_veg_lab(jd, pjd).delta,

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
              eco_total("LitterfallCarbonAll", jd)  + eco_total("MossDeathC", jd) - jd["RH"],
              ecosystem_sum_soilC(jd),
              eco_total("LitterfallCarbonAll", jd) ,
              eco_total("MossDeathC", jd),
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
                eco_total("LitterfallCarbonAll", jd) + jd['MossdeathCarbon'],
                jd['RawCSum'],
                jd['SomaSum'],
                jd['SomprSum'],
                jd['SomcrSum'],
                jd['DeadMossCarbon'],

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
                bal_C_veg(jd, pjd).err,
                bal_C_veg(jd, pjd).delta,

                eco_total("NPPAll", jd)  - eco_total("LitterfallCarbonAll", jd)  - eco_total("MossDeathC", jd),
                eco_total("MossDeathC", jd),
                eco_total("VegCarbon", jd), 
                eco_total("NPPAll", jd) ,
                eco_total("LitterfallCarbonAll", jd) ,
            )

def Check_C_cycle_veg_vascular_balance(idx, header=False, jd=None, pjd=None):
    '''Should duplicate Vegetation_Bgc::deltastate()'''

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

                bal_C_veg(jd, pjd, pftlist=vascular).err,
                bal_C_veg(jd, pjd, pftlist=vascular).delta,

                eco_total("NPPAll", jd, pftlist=vascular)  - eco_total("LitterfallCarbonAll", jd, pftlist=vascular)  - eco_total("MossDeathC",jd,pftlist=vascular),

                eco_total("MossDeathC",jd, pftlist=vascular),
                eco_total("VegCarbon", jd, pftlist=vascular), 
                eco_total("NPPAll", jd, pftlist=vascular),
                eco_total("LitterfallCarbonAll", jd, pftlist=vascular)
            )

def Check_C_cycle_veg_nonvascular_balance(idx, header=False, jd=None, pjd=None):
    '''Should duplicate Vegetation_Bgc::deltastate()'''

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

                bal_C_veg(jd, pjd, pftlist=non_vasc).err,
                bal_C_veg(jd, pjd, pftlist=non_vasc).delta,

                eco_total("NPPAll", jd, pftlist=non_vasc)  - eco_total("LitterfallCarbonAll", jd, pftlist=non_vasc)  - eco_total("MossDeathC", jd, pftlist=non_vasc),
                eco_total("MossDeathC", jd, pftlist=non_vasc),
                eco_total("VegCarbon", jd, pftlist=non_vasc), 
                eco_total("NPPAll", jd, pftlist=non_vasc) ,
                eco_total("LitterfallCarbonAll", jd, pftlist=non_vasc) ,
            )

if __name__ == '__main__':

  slstr = ':6000:'

  slstr = ':500:'

  #plot_tests(['C_soil_balance'], fileslice=slstr)

  '''
  run_tests(
    [
      'N_soil_balance',
      'N_veg_balance',
      'C_soil_balance',
      'C_veg_balance',
      'C_veg_vascular_balance',
      'C_veg_nonvascular_balance',
      'report_soil_C'
    ],
    w2f="tabular-reports-500-months.txt", 
    fileslice=slstr
  )
  '''

  print "Running the imaging...."
  error_image(
    plotlist=[
      'C veg err',
      'C veg vasc err',
      'C veg nonvasc err',
      'N soil err org',
      'N soil err avl',
      'N veg err tot',
      'N veg err str',
      'N veg err lab',
      # 'N veg vasc err tot',
      # 'N veg vasc err str',
      # 'N veg vasc err lab',
      # 'N veg nonvasc err tot',
      # 'N veg nonvasc err str',
      # 'N veg nonvasc err lab',
    ],
    fileslice=slstr
  )

  error_image(
    plotlist=[
      'N veg vasc err tot',
      'N veg vasc err str',
      'N veg vasc err lab',
      'N veg nonvasc err tot',
      'N veg nonvasc err str',
      'N veg nonvasc err lab',
    ],
    fileslice=slstr
  )
  error_image(
    plotlist=[
      'C veg err',
      'C veg vasc err',
      'C veg nonvasc err',
      'N soil err org',
      'N soil err avl',
      'N veg err tot',
      'N veg err str',
      'N veg err lab',
    ],
    fileslice=slstr
  )





