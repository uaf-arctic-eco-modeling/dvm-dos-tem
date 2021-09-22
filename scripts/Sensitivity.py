#!/usr/bin/env python

import numpy as np
import netCDF4 as nc
import pandas as pd
import multiprocessing

import json
import os
import shutil
import subprocess
from contextlib import contextmanager

import param_util as pu
import output_utils as ou


@contextmanager
def log_wrapper(message,tag=''):
  print('[SA:{}] {}'.format(tag, message))
  try:
    yield
  finally:
    print()


class SensitivityDriver(object):
  '''
  Sensitivity Analysis Driver class.

  Driver class for conducting dvmdostem SensitivityAnalysis.
  Methods for cleaning, setup, running model, collecting outputs.

  Parameters
  ----------
  param_specs : list of dicts describing parameters to use
    Each of the dicts is assumed to have the following keys: 
    'name','cmtnum','pftnum','bounds','enabled'
  sample_N : int
    The number of samples to generate for the `self.sample_matrix`.
    Also controls how many runs there will be (one per sample row).

  See Also
  --------

  Examples
  --------
  Parameter specification:
  >>> param_specs = [
  {'name':'cmax', 'cmtnum':4, 'pftnum':3, 'bounds':[100,700],'enabled':True },
  {'name':'rhq10', 'cmtnum':4, 'pftnum':None, 'bounds':[0.1,5],'enabled':True },
  {'name':'micbnup', 'cmtnum':4, 'pftnum':None, 'bounds':[0.1,10],'enabled':True }]

  SensitivityDriver:
  >>> sd = SensitivityDriver(param_specs, sample_N=3)
  >>> sd.pftnum()
  3
  >>> sd.sample_matrix
      cmax  rhq10  micbnup
  0  100.0   0.10     0.10
  1  400.0   2.55     5.05
  2  700.0   5.00    10.00
  '''
  def __init__(self, param_specs, sample_N=10):
    '''Constructor'''
    self.params = param_specs
    self.sample_matrix = self.generate_sample_matrix(N=sample_N)

    self.work_dir = '/data/workflows/sensitivity_analysis'
    self.site = '/data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_CALM_Toolik_LTER_10x10/'
    self.PXx = 0
    self.PXy = 0
    self.outputs = [
      { 'name': 'GPP', 'type': 'flux',},
      { 'name': 'VEGC','type': 'pool',},
    ]

  def clean(self):
    ''''''
    shutil.rmtree(self.work_dir, ignore_errors=True)

  def setup_single(self):
    '''
    Conduct all runs in one directory by modifying the params,
    running, and saving the outputs to a csv file.'''
    pass

  def generate_sample_matrix(self, N, method='uniform'):
    '''
    One row for each sample, one column for each parameter.
    Assumes parameter names match those found in dvmdostem
    parameter files.
    '''
    if not method == 'uniform':
      raise RuntimeError("Not implemented yet!")

    sample_matrix = {}
    for i, p in enumerate(filter(lambda x: x['enabled'], self.params)):
      samples = np.linspace(p['bounds'][0], p['bounds'][1], N)
      sample_matrix[p['name']] = samples

    self.sample_matrix = sample_matrix
    return pd.DataFrame(sample_matrix)

  def core_setup(self, row, idx):
    '''...'''
    print("PROC:{}  ".format(multiprocessing.current_process()), row)
    sample_specific_folder = os.path.join(self.work_dir, 'sample_{:09d}'.format(idx))

    program = '/work/scripts/setup_working_directory.py'
    opt_str = '--input-data-path {} {}'.format(self.site, sample_specific_folder)
    cmdline = program + ' ' + opt_str
    with log_wrapper(cmdline, tag='setup') as lw:
        comp_proc = subprocess.run(cmdline, shell=True, check=True, capture_output=True) 

    program = '/work/scripts/runmask-util.py'
    opt_str = '--reset --yx {} {} {}/run-mask.nc'.format(self.PXy, self.PXx, sample_specific_folder)
    cmdline = program + ' ' + opt_str 
    with log_wrapper(cmdline, tag='setup') as lw:
      comp_proc = subprocess.run(cmdline, shell=True, check=True, capture_output=True)

    for output_spec in self.outputs:
      program = '/work/scripts/outspec_utils.py'
      opt_str = '{}/config/output_spec.csv --on {} m p'.format(sample_specific_folder, output_spec['name'])
      cmdline = program + ' ' + opt_str
      with log_wrapper(cmdline, tag='setup') as lw:
        comp_proc = subprocess.run(cmdline, shell=True, capture_output=True, check=True)

    program = '/work/scripts/outspec_utils.py'
    opt_str = '{}/config/output_spec.csv --on CMTNUM y'.format(sample_specific_folder)
    cmdline = program + ' ' + opt_str
    with log_wrapper(cmdline, tag='setup') as lw:
      comp_proc = subprocess.run(cmdline, shell=True, capture_output=True, check=True)

    CONFIG_FILE = os.path.join(sample_specific_folder, 'config/config.js')
    # Read the existing data into memory
    with open(CONFIG_FILE, 'r') as f:
      config = json.load(f)
    
    config['IO']['output_nc_eq'] = 1 # Modify value...

    # Write it back..
    with open(CONFIG_FILE, 'w') as f:
      json.dump(config, f, indent=2)

    # modify parameters according to sample_matrix (param values)
    # and the  param_spec (cmtnum, pftnum)
    # Iterating over sample_matrix, which is a pandas.DataFrame, we use
    # itertuples() which coughs up a named tuple. So here we get the
    # name, and the sample value outof the named tuple for use in 
    # calling param_utils update function.
    for pname, pval in row.items():
    #for pname, pval in zip(row._fields[1:], row[1:]):
      pdict = list(filter(lambda x: x['name'] == pname, self.params))[0]
      pu.update_inplace(
          pval, os.path.join(sample_specific_folder, 'parameters'), 
          pname, pdict['cmtnum'], pdict['pftnum']
      )

  def setup_multi(self):
    '''
    One directory for each run (row in sample matrix) plus
    one for the initial conditions.
    '''
    # Start fresh...
    self.clean()

    with multiprocessing.Pool(processes=(os.cpu_count()-1)) as pool:
      results = pool.starmap(self.core_setup, zip(self.sample_matrix.to_dict(orient='records'),range(0,len(self.sample_matrix))))
    print(results)

    # Still need to make a directory for default case

  def cmtnum(self):
    '''
    Enforces that there is only one cmtnum specified
    amongst all the param specificaitons in `self.params`.

    Returns
    -------
    cmtnum : int 
      The cmtnum specified.
    
    Raises
    ------
    RuntimeError - if there in valid specification of
    cmtnum in the params list.
    '''
    c = set([x['cmtnum'] for x in self.params])
    if not (len(c) == 1):
      raise RuntimeError("Problem with cmt specification in param_spec!")
    return c.pop()
  
  def pftnum(self):
    '''
    NOTE! Not really sure how this should work long term.
    For now assume that all parameters must have the 
    same pftnum (or None for non-pft params).

    So this ensures that all the parameters are set to the same
    PFT (for pft params). If there are no PFT params, then 
    we return None, and if there is a problem (i.e. params 
    set for different PFTs), then we raise an exception.

    This is only a problem for processing the outputs. Presumably
    if we are adjusting PFT 3 we want to look at outputs for PFT 3.
    Not sure how to handle a case where we have parameters adjusted 
    for several PFTs??? What outputs would we want??
    '''
    pftnums = set([x['pftnum'] for x in self.params])
    pftnums.discard(None)
    if len(pftnums) == 1:
      return pftnums.pop()
    elif len(pftnums) == 0:
      return None
    else:
      # For now 
      raise RuntimeError("Invalid pftnum specificaiton in params dictionary!")

  def ssrf_name(self, idx):
    '''generate the Sample Specific Run Folder name.'''
    return os.path.join(self.work_dir, 'sample_{:09d}'.format(idx))

  def ssrf_names(self):
    return [self.ssrf_name(i) for i in range(0,len(self.sample_matrix))]

  def run_all_samples(self):

    folders = self.ssrf_names()

    with multiprocessing.Pool(processes=(os.cpu_count()-1)) as pool:
      results = pool.map(self.run_model, folders)
    print()

  def run_model(self, rundirectory):
    program = '/work/dvmdostem'
    ctrl_file = os.path.join(rundirectory, 'config','config.js')
    opt_str = '-p 5 -e 5 -s 5 -t 5 -n 5 -l err --force-cmt {} --ctrl-file {}'.format(self.cmtnum(), ctrl_file)
    cmdline = program + ' ' + opt_str
    with log_wrapper(cmdline, tag='run') as lw:
      completed_process = subprocess.run(
        cmdline,             # The program + options 
        shell=True,          # must be used if passing options as str and not list
        check=True,          # raise CalledProcessError on failure
        capture_output=True, # collect stdout and stderr
        cwd=rundirectory)   # control context
      if not completed_process.returncode == 0:
        print(completed_process.stdout)
        print(completed_process.stderr)

  def collect_outputs(self, posthoc=True, multi=True):
    
    for row in self.sample_matrix.itertuples():
      sample_specific_folder = os.path.join(self.work_dir, 'sample_{:09d}'.format(row.Index))
      sensitivity_outfile = os.path.join(sample_specific_folder, 'sensitivity.csv')

      # Not sure if this is how we want to set things up...
      # Seems like each of these files will have only one row, but the 
      # advantage of having a sensitivity file per sample directory is that
      # we can leverage the same parallelism for running collect_outputs
      # Then we'll need another step to collect all the csv files into one
      # at the end.
      pstr = ','.join(['p_{}'.format(p['name']) for p in self.params]) 
      ostr = ','.join(['o_{}'.format(o['name']) for o in self.outputs])
      hdrline = pstr + ',' + ostr + '\n'
      with open(sensitivity_outfile, 'w') as f:
        f.write(hdrline)
      
      # Now do the parameters and output values...
      pstr = ','.join(['{:2.3f}'.format(x) for x in self.sample_matrix.iloc[row.Index]])
      ostr = ''

      for output in self.outputs:
        ds = nc.Dataset(sample_specific_folder + '/output/' + '{}_monthly_eq.nc'.format(output['name']))
        data_m = ds.variables[output['name']][:]
        if output['type'] == 'pool':
          data_y = ou.average_monthly_pool_to_yearly(data_m)
        elif output['type'] == 'flux':
          data_y = ou.sum_monthly_flux_to_yearly(data_m)

        # TODO: Need to handle non-PFT outputs!
        ostr += '{:2.3f},'.format(data_y[-1,self.pftnum(),self.PXy,self.PXx])

      ostr = ostr.rstrip(',') # remove trailing comma...
 
      with open(sensitivity_outfile, 'a') as f:
        f.write(pstr + ',' + ostr + '\n')

