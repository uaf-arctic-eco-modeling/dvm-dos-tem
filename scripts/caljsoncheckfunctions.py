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

def bal_C_veg(curr_jd, pjd):
  delta = np.nan
  if pjd != None:
    delta = calc_delta(eco_total("VegCarbon", curr_jd), eco_total("VegCarbon", pjd))
  err = delta - (eco_total("NPPAll", curr_jd) - eco_total("LitterfallCarbonAll", curr_jd)  - eco_total("MossDeathC", curr_jd))
  return DeltaError(delta, err)

def bal_N_soil_org(jd, pjd):
  delta = np.nan
  if pjd != None:
    delta = jd["OrganicNitrogenSum"] - jd["OrganicNitrogenSum"]
  err = delta - ( (eco_total("LitterfallNitrogenPFT", jd) + jd["MossdeathNitrogen"]) + jd["NetNMin"] )
  return DeltaError(delta, err)

def bal_N_soil_avl(jd, pjd):
  delta = np.nan
  if pjd != None:
    delta = jd["AvailableNitrogenSum"] - pjd["AvailableNitrogenSum"]
  err = delta - ( (jd["NetNMin"] + jd["AvlNInput"]) + (eco_total("TotNitrogenUptake", jd) + jd["AvlNLost"]) )
  return DeltaError(delta, err)

def bal_N_veg_tot(jd, pjd):
  delta = np.nan
  if pjd != None:
    delta = eco_total("NAll", jd)  - eco_total("NAll", pjd) 
  err = delta - eco_total("TotNitrogenUptake", jd) + (eco_total("LitterfallNitrogenPFT", jd) + jd["MossdeathNitrogen"])
  return DeltaError(delta, err)

def bal_N_veg_str(jd, pjd):
  delta = np.nan
  if pjd != None:
    delta = eco_total("VegStructuralNitrogen", jd) - eco_total("VegStructuralNitrogen", pjd) # <-- will sum compartments
  err = delta - (eco_total("StNitrogenUptake", jd) + eco_total("NMobil", jd)) + (eco_total("LitterfallNitrogenPFT", jd) + jd["MossdeathNitrogen"] + eco_total("NResorb", jd))
  return DeltaError(delta, err)

def bal_N_veg_lab(jd, pjd):
  delta = np.nan
  if pjd != None:
    delta = eco_total("VegLabileNitrogen", jd) - eco_total("VegLabileNitrogen", pjd)
  err = delta - (eco_total("LabNitrogenUptake", jd) + eco_total("NResorb", jd)) + eco_total("NMobil", jd)
  return DeltaError(delta, err)



def Check_N_cycle_veg_balance(idx, header=False, jd=None, pjd=None):
    '''Checking....?'''
    if header:
        return "{:<4} {:>6} {:>10} {:>10} {:>10} {:>10} {:>10} {:>10} {:>10} {:>10} {:>10}\n".format(
                "idx", "yr", "errT", "errS", "errL", "deltaN", "delNStr", "delNLab", "sumFlxT","sumFlxS", "sumFlxL"
        )
    else:
        deltaN = np.nan
        deltaN_str = np.nan
        deltaN_lab = np.nan

        if pjd != None:
          deltaN = eco_total("NAll", jd)  - eco_total("NAll", pjd) 
          deltaN_str = eco_total("VegStructuralNitrogen", jd) - eco_total("VegStructuralNitrogen", pjd) # <-- will sum compartments
          deltaN_lab = eco_total("VegLabileNitrogen", jd) - eco_total("VegLabileNitrogen", pjd)
            
        sum_str_N_flux = jd["StNitrogenUptakeAll"] - (eco_total("LitterfallNitrogenPFT", jd) + jd["MossdeathNitrogen"]) + eco_total("NMobil", jd) -  eco_total("NResorb", jd)
        sum_lab_N_flux = eco_total("LabNitrogenUptake", jd) + eco_total("NResorb", jd) - eco_total("NMobil", jd) 


        return  "{:<4} {:>6} {:>10.4f} {:>10.4f} {:>10.3f} {:>10.4f} {:>10.4f} {:>10.3f} {:>10.4f} {:>10.4f} {:>10.3f}\n".format(
                idx,
                jd["Year"],

                deltaN - eco_total("TotNitrogenUptake", jd) + (eco_total("LitterfallNitrogenPFT", jd) + jd["MossdeathNitrogen"]),
                deltaN_str - (eco_total("StNitrogenUptake", jd) + eco_total("NMobil", jd)) + (eco_total("LitterfallNitrogenPFT", jd) + jd["MossdeathNitrogen"] + eco_total("NResorb", jd)),
                deltaN_lab - (eco_total("LabNitrogenUptake", jd) + eco_total("NResorb", jd)) + eco_total("NMobil", jd),

                deltaN,
                deltaN_str,
                deltaN_lab,

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
        deltaC = np.nan

        # If we are beyond the first year, load the previous year
        if pjd != None:
            deltaC = ecosystem_sum_soilC(jd) - ecosystem_sum_soilC(pjd)


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
        return '{:<4} {:>4} {:>10} {:>10} {:>15}     {:>10} {:>15} {:>15} {:>15}\n'.format(
               'idx', 'yr', 'err', 'deltaC', 'NPP-LFallC-mdc', 'mdc', 'VegC', 'NPP', 'LFallC' )
    else:
        deltaC = np.nan

        # If we are beyond the first year, load the previous year
        if pjd != None:
            deltaC = eco_total("VegCarbon", jd) - eco_total("VegCarbon", pjd)

        # FIll in the table with data...
        return '{:<4d} {:>4} {:>10.3f} {:>10.3f} {:>15.3f}     {:>10.3f} {:>15.3f} {:>15.3f} {:>15.3f}\n'.format(
                idx,
                jd['Year'],
                (eco_total("NPPAll", jd)  - eco_total("LitterfallCarbonAll", jd)  - eco_total("MossDeathC", jd)) - deltaC,
                deltaC,
                eco_total("NPPAll", jd)  - eco_total("LitterfallCarbonAll", jd)  - eco_total("MossDeathC", jd),

                eco_total("MossDeathC", jd),
                eco_total("VegCarbon", jd), 
                eco_total("NPPAll", jd) ,
                eco_total("LitterfallCarbonAll", jd) ,
            )

def Check_C_cycle_veg_vascular_balance(idx, header=False, jd=None, pjd=None):
    '''Should duplicate Vegetation_Bgc::deltastate()'''

    # vascular PFT list (CMT05)
    pl = [0,1,2,3,4]

    if header:
        return '{:<4} {:>4} {:>10} {:>10} {:>15}     {:>10} {:>15} {:>15} {:>15}\n'.format(
               'idx', 'yr', 'err', 'deltaC', 'NPP-LFallC-mdc', 'mdc', 'VegC', 'NPP', 'LFallC' )
    else:
        deltaC = np.nan

        # If we are beyond the first year, load the previous year
        if pjd != None:
            deltaC = eco_total("VegCarbon", jd, pftlist=pl) - eco_total("VegCarbon", pjd, pftlist=pl)

        # FIll in the table with data...
        return '{:<4d} {:>4} {:>10.3f} {:>10.3f} {:>15.3f}     {:>10.3f} {:>15.3f} {:>15.3f} {:>15.3f}\n'.format(
                idx,
                jd['Year'],
                (eco_total("NPPAll", jd, pftlist=pl)  - eco_total("LitterfallCarbonAll", jd, pftlist=pl)  - eco_total("MossDeathC",jd,pftlist=pl)) - deltaC,
                deltaC,
                eco_total("NPPAll", jd, pftlist=pl)  - eco_total("LitterfallCarbonAll", jd, pftlist=pl)  - eco_total("MossDeathC",jd,pftlist=pl),

                eco_total("MossDeathC",jd, pftlist=pl),
                eco_total("VegCarbon", jd, pftlist=pl), 
                eco_total("NPPAll", jd, pftlist=pl) ,
                eco_total("LitterfallCarbonAll", jd, pftlist=pl) ,
            )

def Check_C_cycle_veg_nonvascular_balance(idx, header=False, jd=None, pjd=None):
    '''Should duplicate Vegetation_Bgc::deltastate()'''

    # non-vascular PFT list (CMT05)
    pl = [5,6,7]

    if header:
        return '{:<4} {:>4} {:>10} {:>10} {:>15}     {:>10} {:>15} {:>15} {:>15}\n'.format(
               'idx', 'yr', 'err', 'deltaC', 'NPP-LFallC-mdc', 'mdc', 'VegC', 'NPP', 'LFallC' )
    else:
        deltaC = np.nan

        # If we are beyond the first year, load the previous year
        if pjd != None:
            deltaC = eco_total("VegCarbon", jd, pftlist=pl) - eco_total("VegCarbon", pjd, pftlist=pl)

        # FIll in the table with data...
        return '{:<4d} {:>4} {:>10.3f} {:>10.3f} {:>15.3f}     {:>10.3f} {:>15.3f} {:>15.3f} {:>15.3f}\n'.format(
                idx,
                jd['Year'],
                (eco_total("NPPAll", jd, pftlist=pl)  - eco_total("LitterfallCarbonAll", jd, pftlist=pl)  - eco_total("MossDeathC", jd, pftlist=pl)) - deltaC,
                deltaC,
                eco_total("NPPAll", jd, pftlist=pl)  - eco_total("LitterfallCarbonAll", jd, pftlist=pl)  - eco_total("MossDeathC", jd, pftlist=pl),

                eco_total("MossDeathC", jd, pftlist=pl),
                eco_total("VegCarbon", jd, pftlist=pl), 
                eco_total("NPPAll", jd, pftlist=pl) ,
                eco_total("LitterfallCarbonAll", jd, pftlist=pl) ,
            )

if __name__ == '__main__':
  slstr = ':1000:'
  slstr = ':500:'

  plot_tests(['C_soil_balance'], fileslice=slstr)

  run_tests([
    'N_soil_balance',
    'N_veg_balance',
    'C_soil_balance',
    'C_veg_balance',
    'C_veg_vascular_balance',
    'C_veg_nonvascular_balance',
    'report_soil_C'
    ], p2c=True, fileslice=slstr)



  run_tests(['C_soil_balance', 'N_veg_balance'], fileslice=slstr, p2c=True)

