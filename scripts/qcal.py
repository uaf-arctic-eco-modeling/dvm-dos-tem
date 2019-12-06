#!/usr/bin/env python

# T Carman May 2019

import os
import glob
import shutil
import sys
import json
import errno
import numpy as np

# Add dvm-dos-tem directory to path so that we can import various scripts, 
# classes from the calibration directory, and the calibration targets.
# Assumes that this script, (qcal.py) is living in the dvm-dos-tem/scripts/
# directory
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import scripts.output_utils as ou
import scripts.param_util as pu

from calibration.InputHelper import InputHelper

# Paste this into IPython to see log output
# import logging
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)
# logging.debug("test")


def mkdir_p(path):
  '''poached from: https://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python'''
  try:
    os.makedirs(path)
  except OSError as exc:  # Python >2.5
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else:
      raise



def qcal_rank(truth, value):
  ''' Deviation from truth, expressed as percent, with sign.''' 
  #assert(truth > 0)
  return(value/(truth*1.0)-1.0 )

def qcal_rank2(truth, value):
  '''Deviation from truth, expressed as distance squared (no sign).'''
  return (truth - value)**2


def measure_calibration_quality_nc(output_directory_path, ref_targets_dir, ref_param_file):

  print "************* WORKING WITH NETCDF FILES ***********"
  print ""
  print "WARNING !!! WARNING !!! WARNING !!! HARDCODED CMT NUMBER!!"
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
      pec = pu.percent_ecosys_contribution(cmtkey, ctname, ref_param_file=ref_param_file)
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
          pec = pu.percent_ecosys_contribution(cmtkey, ctname, pftnum=pft, ref_params_dir=ref_params_dir)
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
            pec = pu.percent_ecosys_contribution(cmtkey, ctname, pftnum=pft, compartment=clu[cmprt], ref_params_dir=ref_params_dir)
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
  def __init__(self,jsondata_path="", ncdata_path="", ref_targets_dir="", ref_params_dir=""):
    #self.cmtkey = ?? # it is possible to lookup the CMT number in the json file, but not the netcdf file!

    # This is basically a complicated mechanism to make sure that importing 
    # the targets file is possible, even in the case where the user is specifying
    # that the reference targets file is in a directory that does not have
    # an __init__.py. In the case that the calibration targets file is in a 
    # different folder from this script and we are using python <3.3 I think, 
    # then there must be an __init__.py file so that the containing folder is
    # treated as a package and the calibration_targets.py module is importable.
    # Basically if we can't find __init__.py, then we copy to /tmp where
    # we can make the __init__.py file, then we import and clean up after ourselves.
    # Hopefully this implentation will work on multiuser systems and allow for
    # importing targets from another user's directory. This is probably some 
    # awful gaping security hole, but we are going to ignore that for now...
    if not os.path.isfile(os.path.join(ref_targets_dir,  'calibration_targets.py')):
      print "ERROR: Can't find calibration_targets.py in {}".format(ref_targets_dir)
      sys.exit(-1)
    else:
      if not os.path.isfile(os.path.join(ref_targets_dir, '__init__.py')):
        print "WARNING: No __init__.py python package file present. Copying targets to a temporary location for facilitate import"
        mkdir_p(os.path.join('/tmp/', 'dvmdostem-user-{}-tmp-cal'.format(os.getuid())))
        shutil.copy(os.path.join(ref_targets_dir, 'calibration_targets.py'), os.path.join('/tmp/', 'dvmdostem-user-{}-tmp-cal'.format(os.getuid())))
        with open(os.path.join('/tmp/','dvmdostem-user-{}-tmp-cal'.format(os.getuid()),'__init__.py'), 'w') as f:
          f.writelines(["# nothing to see here..."]) 

        old_path = sys.path
        sys.path = [os.path.join('/tmp/','dvmdostem-user-{}-tmp-cal'.format(os.getuid()))]
        print "Loading calibration_targets from : {}".format(sys.path)
        import calibration_targets as ct
        caltargets = {'CMT{:02d}'.format(v['cmtnumber']):v for k, v in ct.calibration_targets.iteritems()}
        del ct

        print "Cleaning up temporary targets and __init__.py file used for import..."
        shutil.rmtree(os.path.join('/tmp/','dvmdostem-user-{}-tmp-cal'.format(os.getuid())))
        print "Resetting path..."
        sys.path = old_path

      else:
        old_path = sys.path
        sys.path = [os.path.join(ref_targets_dir, 'calibration')]
        print "Loading calibration_targets from : {}".format(sys.path)
        import calibration_targets as ct
        caltargets = {'CMT{:02d}'.format(v['cmtnumber']):v for k, v in ct.calibration_targets.iteritems()}
        del ct
        print "Resetting path..."
        sys.path = old_path


    self.targets = caltargets
    self.targets_dir = ref_targets_dir
    self.params_dir = ref_params_dir

    self.jsondata_path = jsondata_path
    self.ncdata_path = ncdata_path


  def json_qcal(self):
    ih = InputHelper(self.jsondata_path)
    assert(os.path.splitext(ih.files()[0])[1] == ".json")
    result_list = measure_calibration_quality_json(ih.files()[-10:], ref_targets=self.targets, ref_params_dir=self.params_dir)
    return result_list


  def nc_qcal(self):
    assert(os.path.splitext(os.listdir(self.ncdata_path)[0])[1] == ".nc")
    result_list = measure_calibration_quality_nc(self.ncdata_path)
    return result_list


  def report(self, which):
    if which == 'json':
      r = self.json_qcal()
    elif which == 'nc':
      r = self.nc_qcal()
    else:
      raise RuntimeError("You must specify which data source to use with the 'which' parameter")

    cmt = set([i['cmt'] for i in r])
    if len(cmt) != 1:
      raise RuntimeError("Problem with QCal results! More than one CMT detected!! {}".format(cmt))

    s = '''\
        modeled data: {}
        targets file: {}
     parameter files: {}
                 CMT: {}
                 QCR: {}
        Weighted QCR: {}
    '''.format(self.jsondata_path, self.targets_dir, self.params_dir, cmt, np.sum([i['qcr'] for i in r]), np.sum([i['qcr_w'] for i in r]) )

    return s



def measure_calibration_quality_json(file_list, ref_params_dir=None, ref_targets={}):

  assert(type(ref_targets == dict))
  assert(len(ref_targets.keys()) > 0)


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
    pec = pu.percent_ecosys_contribution(cmtkey, v, ref_params_dir=ref_params_dir)
    d = 0.0
    for f in file_list:
      with open(f) as fh:
        jdata = json.load(fh)
      d += jdata[v]/float(len(file_list))

    if np.isclose(ref_targets[cmtkey][v], 0.0):
      print "WARNING! Target value for {} is zero! Is this a problem???".format(v)
      qcr = np.abs(0.0 + d)
    else:
      qcr = np.abs(qcal_rank(ref_targets[cmtkey][v], d))

    qcr_w = qcr * pec
    qcr_t += qcr
    #print v, d, ref_targets[cmtkey][v], qcr
    #print "{:>25s} {:>5s} {:>8s} {:0.6f} {:0.3f}".format(v, '', '', pec, qcr)
    d = dict(cmt=cmtkey, ctname=v, value=d, truth=ref_targets[cmtkey][v], pec=pec, qcr=qcr, qcr_w=qcr_w)
    data.append(d)

  # Now process all the PFT variables
  for ipft, pft in enumerate(['PFT{}'.format(i) for i in range(0,10)]):
    if pu.is_ecosys_contributor(cmtkey, ipft, ref_params_dir=ref_params_dir):
      for v in ['GPPAllIgnoringNitrogen','NPPAllIgnoringNitrogen','NPPAll']:
        pec = pu.percent_ecosys_contribution(cmtkey, v, pftnum=ipft, ref_params_dir=ref_params_dir)
        d = 0.0
        for f in file_list:
          with open(f) as fh:
            jdata = json.load(fh)
          d += jdata[pft][v]/float(len(file_list))
        qcr = np.abs(qcal_rank(ref_targets[cmtkey][v][ipft], d))
        qcr_w = qcr * pec
        qcr_t += qcr
        #print "{:>25s} {:>5d} {:>8s} {:0.6f} {:0.3f}".format(v, ipft, '', pec, qcr)
        d = dict(cmt=cmtkey, ctname=v, pft=ipft, value=d, truth=ref_targets[cmtkey][v][ipft], pec=pec, qcr=qcr, qcr_w=qcr_w)
        data.append(d)
    else:
      pass #print "{:>25s} {:>5d}     --".format(v, ipft)

    # And process all the PFT/Compartment variables
    for cmprt in ['Leaf','Stem','Root']:
      if pu.is_ecosys_contributor(cmtkey, ipft, cmprt, ref_params_dir=ref_params_dir):
        for v in ['VegCarbon', 'VegStructuralNitrogen']:
          pec = pu.percent_ecosys_contribution(cmtkey, v, pftnum=ipft, compartment=cmprt, ref_params_dir=ref_params_dir)
          d = 0.0
          for f in file_list:
            with open(f) as fh:
              jdata = json.load(fh)
            d += jdata[pft][v][cmprt]/float(len(file_list))
          truth = ref_targets[cmtkey][v][cmprt][ipft],
          qcr = np.abs(qcal_rank(ref_targets[cmtkey][v][cmprt][ipft], d))
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
    pec = pu.percent_ecosys_contribution(cmtkey, v, ref_params_dir=ref_params_dir)
    qcr = qcal_rank(caltargets[cmtkey][v], jdata[v])
    print "{} {}".format(pec, qcr)

  for ipft, pft in enumerate(['PFT{}'.format(i) for i in range(0,10)]):
    if pu.is_ecosys_contributor(cmtkey, ipft):
      for v in ['GPPAllIgnoringNitrogen','NPPAllIgnoringNitrogen','NPPAll']:
        pec = pu.percent_ecosys_contribution(cmtkey, v, pftnum=ipft, ref_params_dir=ref_params_dir)
        qcr = qcal_rank(caltargets[cmtkey][v][ipft], jdata[pft][v])

        print "{} {}".format(pec, qcr)

    for cmprt in ['Leaf','Stem','Root']:

      if pu.is_ecosys_contributor(cmtkey, ipft, cmprt):
        for v in ['VegCarbon', 'VegStructuralNitrogen']:

          pec = pu.percent_ecosys_contribution(cmtkey, v, pftnum=ipft, compartment=cmprt, ref_params_dir=ref_params_dir)
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

def ref_targets_validator(arg_ref_targets_path):
  return arg_ref_targets_path

def ref_params_validator(arg_ref_params_path):
  return arg_ref_params_path



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

  parser.add_argument("--ref-targets", type=ref_targets_validator, default=os.path.join('calibration/'),
      help=textwrap.dedent('''Path to a folder containing a calibration_targets.py file.'''))

  parser.add_argument("--ref-params", type=ref_params_validator, default=os.path.join('parameters/'),
      help=textwrap.dedent('''Path to a folder of parameter files. (cmt_*.txt)'''))

  parser.add_argument("calfolder", type=cal_folder_validator, 
      help=textwrap.dedent('''The folder where the program should look for calibration outputs from dvm-dos-tem'''))

  args = parser.parse_args()
  

  # Setup the parameters

  if 'eq-data.tar.gz' not in os.listdir(args.calfolder):
    print "Can't find enough json data to measure calibration quality!"

  qcal = QCal(
      jsondata_path=os.path.join(args.calfolder, "eq-data.tar.gz"),
      #ncdata_path="/home/jclein/Desktop/cal-kougo-treelineWS/output/",
      ref_targets_dir=args.ref_targets,
      ref_params_dir=args.ref_params
  )

  print qcal.report(which='json')

  #qcal.nc_qcal()



