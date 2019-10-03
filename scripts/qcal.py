#!/usr/bin/env python

# T Carman May 2019

import os
import glob
import sys
import json
import numpy as np

# Add dvm-dos-tem directory to path so that we can import various scripts, 
# classes from the calibration directory, and the calibration targets.
# Assumes that this script, (qcal.py) is living in the dvm-dos-tem/scripts/
# directory
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import scripts.output_utils as ou
import scripts.param_util as pu

from calibration.calibration_targets import calibration_targets as ct
from calibration.InputHelper import InputHelper

# Paste this into IPython to see log output
# import logging
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)
# logging.debug("test")

# Re-shape the wat the calibration targets dict is structured (keyed)
caltargets = {'CMT{:02d}'.format(v['cmtnumber']):v for k, v in ct.iteritems()}


def qcal_rank(truth, value):
  ''' Deviation from truth, expressed as percent, with sign.''' 
  #assert(truth > 0)
  return(value/(truth*1.0)-1.0 )

def qcal_rank2(truth, value):
  '''Deviation from truth, expressed as distance squared (no sign).'''
  return (truth - value)**2


def measure_calibration_quality_nc(output_directory_path):

  #print "************* WORKING WITH NETCDF FILES ***********"
  #print ""
  #print "WARNING !!! WARNING !!! WARNING !!! HARDCODED CMT NUMBER!!"
  cmtkey = 'CMT05'

  #print "CMT:", cmtkey

  qcr = 0.0
  qcr_2 = 0.0
  w_qcr = 0.0
  w_qcr_2 = 0.0

  caltarget_to_ncname_map = [
    ('GPPAllIgnoringNitrogen','INGPP'),
    ('NPPAllIgnoringNitrogen','INNPP'),
    ('NPPAll','NPP'),
    #('Nuptake','NUPTAKE'), # ??? There are snuptake, lnuptake and innuptake... and TotNitrogentUptake is the sum of sn and ln...
    ('VegCarbon','VEGC'),
    ('VegStructuralNitrogen','VEGN'),
    ('MossDeathC','MOSSDEATHC'),
    ('CarbonShallow','SHLWC'),
    ('CarbonDeep','DEEPC'),
    ('CarbonMineralSum','MINEC'),
    ('OrganicNitrogenSum','ORGN'),
    ('AvailableNitrogenSum','AVLN'),
  ]

  final_data = []
  #print "variable value target rank(abs)"
  for ctname, ncname in caltarget_to_ncname_map:

    
    data, dims = ou.get_last_n_eq(ncname, 'yearly', output_directory_path)
    dsizes, dnames = zip(*dims)

    #print ctname, output_directory_path, ncname, dims, dnames, dsizes

    if dnames == ('time','y','x'):
      pec = pu.percent_ecosys_contribution(cmtkey, ctname)
      truth = caltargets[cmtkey][ctname]
      value = data[:,0,0].mean()
      #print ctname, value, truth, np.abs(qcal_rank(truth, value))

      # Unweighted Rank
      qcr += np.abs(qcal_rank(truth, value))
      qcr_2 += qcal_rank2(truth, value)

      # Weighted Rank
      w_qcr += np.abs(qcal_rank(truth, value)) * pec
      w_qcr_2 += qcal_rank2(truth, value) * pec

      d = dict(cmt=cmtkey, ctname=ctname,value=value,truth=truth,qcr=np.abs(qcal_rank(truth, value)), qcr_w=np.abs(qcal_rank(truth, value)) * pec)
      final_data.append(d)



    elif dnames == ('time','y','x','pft'):
      for pft in range(0,10):
        if pu.is_ecosys_contributor(cmtkey, pft):
          pec = pu.percent_ecosys_contribution(cmtkey, ctname, pftnum=pft)
          truth = caltargets[cmtkey][ctname][pft]
          value = data[:,pft,0,0].mean()

          # Unweighted Rank
          qcr += np.abs(qcal_rank(truth, value))
          qcr_2 += qcal_rank2(truth, value)

          # Weighted Rank
          w_qcr += np.abs(qcal_rank(truth, value)) * pec
          w_qcr_2 += qcal_rank2(truth, value) * pec

          d = dict(cmt=cmtkey, ctname=ctname,value=value,truth=truth,pft=pft,pec=pec,qcr=np.abs(qcal_rank(truth, value)),qcr_w=np.abs(qcal_rank(truth, value)) * pec)
          final_data.append(d)

        else:
          pass
          #print "  -> Failed" # contributor test! Ignoring pft:{}, caltarget:{}, output:{}".format(pft, ctname, ncname)

    elif dnames == ('time','y','x','pft','pftpart'):
      for pft in range(0,10):
        clu = {0:'Leaf', 1:'Stem', 2:'Root'}
        for cmprt in range(0,3):
          #print "analyzing... ctname {} (nc output: {}) for pft {} compartment {}".format(ctname, ncname, pft, cmprt),
          if pu.is_ecosys_contributor(cmtkey, pft, clu[cmprt]):
            pec = pu.percent_ecosys_contribution(cmtkey, ctname, pftnum=pft, compartment=clu[cmprt])
            truth = caltargets[cmtkey][ctname][clu[cmprt]][pft]
            value = data[:,cmprt,pft,0,0].mean()
            # Unweighted Rank
            qcr += np.abs(qcal_rank(truth, value))
            qcr_2 += qcal_rank2(truth, value)

            # Weighted Rank
            w_qcr += np.abs(qcal_rank(truth, value)) * pec
            w_qcr_2 += qcal_rank2(truth, value) * pec

            d = dict(cmt=cmtkey, ctname=ctname,value=value,truth=truth,pft=pft,compartment=clu[cmprt],pec=pec,qcr=np.abs(qcal_rank(truth, value)),qcr_w=np.abs(qcal_rank(truth, value)) * pec)
            final_data.append(d)

          else:
            pass
            #print "  -> Failed! "#contributor test! Ignoring pft:{}, compartment:{}, caltarget:{}, output:{}".format(pft, cmprt, ctname, ofname)

    else:
      raise RuntimeError("SOMETHING IS WRONG?")

  #print ""
  #print ""
  #print "qcr: {}  qcr_2: {}".format(qcr, qcr_2)
  #print "w_qcr: {}  w_qcr_2: {}".format(w_qcr, w_qcr_2)
  #pu.get_ecosystem_total_C('CMT04')

  return data

class QCal(object):
  def __init__(self,jsondata_path="", ncdata_path="", targets_file="calibration/calibration_targets.py"):
    #self.cmtkey = ?? # it is possible to lookup the CMT number in the json file, but not the netcdf file!
    self.targets = caltargets # use the CMT to lookup the targets
    self.jsondata_path = jsondata_path
    self.ncdata_path = ncdata_path


  def json_qcal(self):
    ih = InputHelper(self.jsondata_path)
    assert(os.path.splitext(ih.files()[0])[1] == ".json")
    measure_calibration_quality_json(ih.files()[-10:])

  def nc_qcal(self):
    assert(os.path.splitext(os.listdir(self.ncdata_path)[0])[1] == ".nc")
    measure_calibration_quality_nc(self.ncdata_path)





def measure_calibration_quality_json(file_list):

  #print "************* WORKING WITH JSON FILES ***********"
  # Figure out which community type was run by looking at the first json file
  # in the list. Assume that ALL json files have the same CMT!
  with open(file_list[0]) as f1:
    f1_data = json.load(f1)
    cmtkey = f1_data['CMT']

  data = []
  #print "CMT: ", cmtkey
  qcr_t = 0.0 # A variable for accumulating the total.

  # First process all the non-PFT variables
  for v in 'MossDeathC,CarbonShallow,CarbonDeep,CarbonMineralSum,OrganicNitrogenSum,AvailableNitrogenSum'.split(','):
    pec = pu.percent_ecosys_contribution(cmtkey, v)
    d = 0.0
    for f in file_list:
      with open(f) as fh:
        jdata = json.load(fh)
      d += jdata[v]/float(len(file_list))
    qcr = np.abs(qcal_rank(caltargets[cmtkey][v], d))
    qcr_w = qcr * pec
    qcr_t += qcr
    #print v, d, caltargets[cmtkey][v], qcr
    #print "{:>25s} {:>5s} {:>8s} {:0.6f} {:0.3f}".format(v, '', '', pec, qcr)
    d = dict(cmt=cmtkey, ctname=v, value=d, truth=caltargets[cmtkey][v], pec=pec, qcr=qcr, qcr_w=qcr_w)
    data.append(d)

  # Now process all the PFT variables
  for ipft, pft in enumerate(['PFT{}'.format(i) for i in range(0,10)]):
    if pu.is_ecosys_contributor(cmtkey, ipft):
      for v in ['GPPAllIgnoringNitrogen','NPPAllIgnoringNitrogen','NPPAll']:
        pec = pu.percent_ecosys_contribution(cmtkey, v, pftnum=ipft)
        d = 0.0
        for f in file_list:
          with open(f) as fh:
            jdata = json.load(fh)
          d += jdata[pft][v]/float(len(file_list))
        qcr = np.abs(qcal_rank(caltargets[cmtkey][v][ipft], d))
        qcr_w = qcr * pec
        qcr_t += qcr
        #print "{:>25s} {:>5d} {:>8s} {:0.6f} {:0.3f}".format(v, ipft, '', pec, qcr)
        d = dict(cmt=cmtkey, ctname=v, pft=ipft, value=d, truth=caltargets[cmtkey][v][ipft], pec=pec, qcr=qcr, qcr_w=qcr_w)
        data.append(d)
    else:
      pass #print "{:>25s} {:>5d}     --".format(v, ipft)

    # And process all the PFT/Compartment variables
    for cmprt in ['Leaf','Stem','Root']:
      if pu.is_ecosys_contributor(cmtkey, ipft, cmprt):
        for v in ['VegCarbon', 'VegStructuralNitrogen']:
          pec = pu.percent_ecosys_contribution(cmtkey, v, pftnum=ipft, compartment=cmprt)
          d = 0.0
          for f in file_list:
            with open(f) as fh:
              jdata = json.load(fh)
            d += jdata[pft][v][cmprt]/float(len(file_list))
          truth = caltargets[cmtkey][v][cmprt][ipft],
          qcr = np.abs(qcal_rank(caltargets[cmtkey][v][cmprt][ipft], d))
          qcr_t += qcr
          qcr_w = qcr * pec
          #print "{:>25s} {:>5d} {:>8s} {:0.6f} {:0.3f}".format(v, ipft, cmprt, pec, qcr)
          d = dict(cmt=cmtkey, ctname=v, pft=ipft, compartment=cmprt, value=d,  truth=truth, pec=pec, qcr=qcr, qcr_w=qcr_w)
          data.append(d)

      else:
        pass #print "{:>25s} {:>5d} {:>8s} {} {}     --".format(v, ipft, cmprt, '','')
        #print "dict(v='{}',ipft={},cmprt='{}',qcr='{}',pec='{}'')".format(v, ipft,cmprt,"--","--")

  #print "Total QCR: {}".format(qcr_t)

  return data


def print_report(jdata, caltargets):

  cmtkey = jdata['CMT']

  for v in 'MossDeathC,CarbonShallow,CarbonDeep,CarbonMineralSum,OrganicNitrogenSum,AvailableNitrogenSum'.split(','):
    pec = pu.percent_ecosys_contribution(cmtkey, v)
    qcr = qcal_rank(caltargets[cmtkey][v], jdata[v])
    print "{} {}".format(pec, qcr)

  for ipft, pft in enumerate(['PFT{}'.format(i) for i in range(0,10)]):
    if pu.is_ecosys_contributor(cmtkey, ipft):
      for v in ['GPPAllIgnoringNitrogen','NPPAllIgnoringNitrogen','NPPAll']:
        pec = pu.percent_ecosys_contribution(cmtkey, v, pftnum=ipft)
        qcr = qcal_rank(caltargets[cmtkey][v][ipft], jdata[pft][v])

        print "{} {}".format(pec, qcr)

    for cmprt in ['Leaf','Stem','Root']:

      if pu.is_ecosys_contributor(cmtkey, ipft, cmprt):
        for v in ['VegCarbon', 'VegStructuralNitrogen']:

          pec = pu.percent_ecosys_contribution(cmtkey, v, pftnum=ipft, compartment=cmprt)
          qcr = qcal_rank(caltargets[cmtkey][v][cmprt][ipft], jdata[pft][v][cmprt])
    
        print "{} {}".format(pec, qcr)

      else:
        print "--"


# NOTE, TODO, need to figure out how to find CMT type!!









def cal_folder_validator(arg_calfolder):
  try:
    files = os.listdir(arg_calfolder)
  except OSError as e:
    msg = "Invalid folder for calibration data! {}".format(e)
    raise argparse.ArgumentTypeError(msg)
  return arg_calfolder



if __name__ == '__main__':
  
  import argparse
  import textwrap

  parser = argparse.ArgumentParser(
    formatter_class = argparse.RawDescriptionHelpFormatter,

      description=textwrap.dedent('''\
        Still working on this...
        '''.format("")),

      epilog=textwrap.dedent(''''''),
  )

  parser.add_argument("calfolder", type=cal_folder_validator, 
      help=textwrap.dedent('''The folder where the program should look for calibration outputs from dvm-dos-tem'''))

  args = parser.parse_args()
  
  qcal = QCal(jsondata_path=os.path.join(args.calfolder, "eq-data.tar.gz")) #, ncdata_path="/home/jclein/Desktop/cal-kougo-treelineWS/output/")

  qcal.json_qcal()
  #qcal.nc_qcal()



