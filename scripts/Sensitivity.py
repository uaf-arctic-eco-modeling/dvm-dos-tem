#!/usr/bin/env python

import pathlib
import numpy as np
import netCDF4 as nc
import pandas as pd
import multiprocessing
import textwrap
import matplotlib.pyplot as plt

import lhsmdu
import glob
import json
import os
import ast
import shutil
import subprocess
from contextlib import contextmanager

import param_util as pu
import output_utils as ou

import setup_working_directory
import importlib
runmask_util = importlib.import_module("runmask-util")
import outspec_utils

@contextmanager
def log_wrapper(message,tag=''):
  '''
  Likely will abandon or repurpose this function.
  Not super helpful as a log printer.'''
  print('[SA:{}] {}'.format(tag, message))
  try:
    yield
  finally:
    print()

def generate_uniform(N, param_props):
  '''
  Generate sample matrix using uniform method.

  Sample matrix will have one row for each "sample" of the
  parameters. There will be one column for each parameter in
  the `param_props` list.

  For example:
    >>> generate_uniform(3,
    ...   [ {"name": "rhq10", "bounds": [0, 5]},
    ...     {"name": "cmax", "bounds": [10, 20]} ])
          rhq10       cmax
    0  2.513395  10.514788
    1  1.393232  19.082659
    2  1.197809  11.448949


  Parameters
  ----------
  N : int
    number of samples (rows) to create

  param_props : list of dicts
    Each item in `param_props` list will be a dictionary
    with at least the following:
    >>> param_props = {
    ...   'name': 'rhq10',        # name in dvmdostem parameter file (cmt_*.txt)
    ...   'bounds': [5.2, 6.4],   # the min and max values the parameter can have
    ... }

  Returns
  -------
  df : pandas.DataFrame, shape (N, len(param_props))
    There will be one column for each parameter in the
    `param_props` list and N rows (samples).
  '''
  #print(param_props)
  l = np.random.uniform(size=(N, len(param_props)))

  # Generate bounds, based on specification in params list
  lows = np.array([p['bounds'][0] for p in param_props])
  highs = np.array([p['bounds'][1] for p in param_props])

  # Figure out the spread, or difference between bounds
  spreads = highs - lows

  sm = l * spreads + lows

  return pd.DataFrame(sm, columns=[p['name'] for p in param_props])


def generate_lhc(N, param_props):
  '''
  Generate sample matrix using Latin Hyper Cube method.

  Sample matrix will have one row for each "sample" of the
  parameters. There will be one column for each parameter in
  the `param_props` list.

  For example:
    >>> generate_lhc(3, 
    ...   [ {"name": "rhq10", "bounds": [0, 5]},
    ...     {"name": "cmax", "bounds": [10, 20]} ])
          rhq10       cmax
    0  0.419637  10.949468
    1  4.162081  13.456290
    2  2.168131  18.698548

  Parameters
  ----------
  N : int
    number of samples (rows) to create

  param_props : list of dicts
    Each item in `param_props` list will be a dictionary
    with at least the following:
    >>> param_props = {
    ...   'name': 'cmax',               # name in dvmdostem parameter file (cmt_*.txt)
    ...   'bounds': [100.1, 105.1],     # the min and max values the parameter can have
    ... }

  Returns
  -------
  df : pandas.DataFrame, shape (N, len(param_props))
    There will be one column for each parameter in the
    `param_props` list and N rows (samples).
  '''

  # Generate bounds, based on specification in params list
  lo_bounds = np.array([p['bounds'][0] for p in param_props])
  hi_bounds = np.array([p['bounds'][1] for p in param_props])

  # Figure out the spread, or difference between bounds
  spreads = hi_bounds - lo_bounds

  # ??
  l = lhsmdu.sample(len(param_props), N)
  
  # ??
  l = lhsmdu.resample().T

  # ??
  mat_diff = np.diag(spreads)

  # ??
  sample_matrix = l * mat_diff + lo_bounds

  def make_col_name(pdict):
    '''Given a parameter, returns a column name like 'rhq10' or 'cmax_1', 
    depending on whether the parameter is specified by PFT or not...'''
    s = f"{pdict['name']}"
    if 'pftnum' in pdict.keys():
      s+= f"_pft{pdict['pftnum']}"
    return s


  return pd.DataFrame(sample_matrix, columns=[make_col_name(p) for p in param_props])


def params_from_seed(seedpath, params, pftnums, percent_diffs, cmtnum):
  '''
  Builds a list of "param specifications" from the data in the `seedpath` and
  for params specified in `params` for the pfts specified in `pftnums` and the
  Community specified in `cmtnum`. Sets bounds based on the intial values
  found in the `seedpath` and according to the percent_diffs.
  '''

  assert len(params) == len(pftnums), "params list and pftnums list must be same length!"
  assert len(params) == len(percent_diffs), "params list and percent_diffs list must be same length"

  final = []
  plu = pu.build_param_lookup(seedpath)

  for pname, pftnum, perturbation in zip(params, pftnums, percent_diffs):
    original_pdata_file = pu.which_file(seedpath, pname, lookup_struct=plu)

    p_db = pu.get_CMT_datablock(original_pdata_file, cmtnum)
    p_dd = pu.cmtdatablock2dict(p_db)

    if pname in p_dd.keys():
      p_initial = p_dd[pname]
      p_bounds = [p_initial - (p_initial*perturbation), p_initial + (p_initial*perturbation)]
      final.append(dict(name=pname, bounds=p_bounds, initial=p_initial, cmtnum=cmtnum, pftnum=None))
    else:
      if pftnum == 'all':
        for pftidx in range(0,10):
          p_initial = p_dd['pft{}'.format(pftidx)][pname]
          p_bounds = [p_initial - (p_initial*perturbation), p_initial + (p_initial*perturbation)]
          final.append(dict(name=pname, bounds=p_bounds, initial=p_initial, cmtnum=cmtnum, pftnum=pftidx))
      elif type(pftnum) is list:
        for pftidx in pftnum:
          p_initial = p_dd['pft{}'.format(pftidx)][pname]
          p_bounds = [p_initial - (p_initial*perturbation), p_initial + (p_initial*perturbation)]
          final.append(dict(name=pname, bounds=p_bounds, initial=p_initial, cmtnum=cmtnum, pftnum=pftidx))
      elif type(pftnum) is int:
        p_initial = p_dd['pft{}'.format(pftnum)][pname]
        p_bounds = [p_initial - (p_initial*perturbation), p_initial + (p_initial*perturbation)]
        final.append(dict(name=pname, bounds=p_bounds, initial=p_initial, cmtnum=cmtnum, pftnum=pftnum))

  return final
  


class SensitivityDriver(object):
  '''
  Sensitivity Analysis Driver class.

  Driver class for conducting ``dvmdostem`` SensitivityAnalysis. Methods for
  cleaning, setup, running model, collecting outputs.

  Basic overview of use is like this:

    1. Instantiate driver object.
    2. Setup/design the experiment (working directory, seed path, parameters to
       use, number of samples, etc)
    3. Use driver object to setup the run folders.
    4. Use driver object to carry out model runs.
    5. Use driver object to summarize/collect outputs.
    6. Use driver object to make plots, do analysis.

  Parameters
  ----------
  work_dir : str, optional
    The working directory path of the driver object.

  sampling_method : { None, 'lhc', 'uniform' }
    Method that should be used to draw samples from the specified ranges in
    order to construct the sample matrix. `lhc` will use the Latin Hyper Cube
    sampling method and `uniform` will draw from a uniform distribution. The
    default `None` is simply a placeholder.

  clean : bool, default=False
    CAREFUL! - this will forecfully remove the entrire tree rooted at
    `work_dir`.

  Examples
  --------
  Instantiate object, sets pixel, outputs, working directory, site selection
  (input data path)

      >>> driver = SensitivityDriver()

  Set the working directory for the driver (using something temporary for this
  test case).

      >>> driver.work_dir = '/tmp/Sensitivity-inline-test'

  Show info about the driver object:

      >>> driver.design_experiment(5, 4, params=['cmax','rhq10','nfall(1)'], pftnums=[2,None,2])
      >>> driver.sample_matrix
              cmax     rhq10  nfall(1)
      0  63.536594  1.919504  0.000162
      1  62.528847  2.161819  0.000159
      2  67.606747  1.834203  0.000145
      3  59.671967  2.042034  0.000171
      4  57.711999  1.968631  0.000155
  '''
  def __init__(self, work_dir=None, sampling_method=None, clean=False,opt_run_setup=None):
    '''Create a SensitivityDriver object.'''

    self.__seedpath = None

    self.set_work_dir(work_dir)

    self.site = '/work/demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10'
    self.PXx = 0
    self.PXy = 0
    self.outputs = [
      { 'name': 'GPP', 'type': 'flux',},
      { 'name': 'VEGC','type': 'pool',},
    ]
    self.opt_run_setup = opt_run_setup
    self.sampling_method = sampling_method
    if self.work_dir is not None:
      if not os.path.isdir(self.work_dir):
        os.mkdir(self.work_dir)

    if clean and work_dir is not None:
      self.clean()

  def set_work_dir(self, path):
    '''Sets the working directory for the object. Assumes that the working
    directory will have an ``initial_params_rundir`` directory that will have
    the initial parameter values.'''
    if path:
      self.work_dir = path
      self.__initial_params_rundir = os.path.join(self.work_dir, 'initial_params_run_dir')
    else:
      self.work_dir = None
      self.__initial_params_rundir = None

  def set_seed_path(self, path):
    self.__seedpath = path


  def get_initial_params_dir(self):
    '''Read only accessor to private member variable.'''
    return self.__initial_params_rundir

  def design_experiment(self, Nsamples, cmtnum, params, pftnums, 
      percent_diffs=None, sampling_method='lhc'):
    '''
    Builds bounds based on initial values found in dvmdostem parameter files
    (cmt_*.txt files) and the `percent_diffs` array. The `percent_diffs` array
    gets used to figure out how far the bounds should be from the initial value.
    Defaults to initial value +/-10%.

    Sets instance values for `self.params` and `self.sample_matrix`.

    Parameters
    ----------
    Nsamples : int
      How many samples to draw. One sample equates to one run to be done with
      the parameter values in the sample.
    
    cmtnum : int
      Which community type number to use for initial parameter values, for doing
      runs and analyzing outputs.
    
    params : list of strings
      List of parameter names to use in the experiment. Each name must be in one
      of the dvmdostem parameter files (cmt_*.txt).
    
    pftnums : list, same length as params list
      Each item in the items may be one of: 

       1. int 
       2. the string 'all' 
       3. list of ints 
       4. None

      If the list item is an int, then that is the PFT number to be used for the
      corresponding parameter. If the list item is the string 'all' then ALL 10
      PFTs are enabled for this parameter. If the list item is a list of ints,
      then the corresponding parameter will be setup for each PFT in the list.
      If the list item is None, then the parameter is assumed to be a soil
      parameter and no PFT info is set or needed.
    
    percent_diffs : list of floats
      List values, one for each parameter in `params`. The value is used to the
      bounds with respect to the intial parameter value. I.e. passing a value in
      the percent_diff array of .3 would mean that bounds should be +/-30% of
      the initial value of the parameter.
    
    sampling_method : str
      A string indicating which sampling method to use for getting values for
      the sample matrix. Currently the options are 'lhc' or 'uniform'. 

    Returns
    -------
    None
    '''
    self.sampling_method = sampling_method

    if os.path.isdir(self.work_dir):
      if len(os.listdir(self.work_dir)) > 0:
        raise RuntimeError("SensitivityDriver.work_dir is not empty! You must run SensitivityDriver.clean() before designing an experiment.")

    if not percent_diffs:
      percent_diffs = np.ones(len(params)) * 0.1 # use 10% for default perturbation

    self.params = params_from_seed(seedpath=self.__seedpath, params=params, 
        pftnums=pftnums, percent_diffs=percent_diffs, cmtnum=cmtnum)

    if self.sampling_method == 'lhc':
      self.sample_matrix = generate_lhc(Nsamples, self.params)
    elif sampling_method == 'uniform':
      self.sample_matrix = self.generate_uniform(Nsamples, self.params)
    else:
      raise RuntimeError(f"{self.sampling_method} is not implemented as a sampling method.")

  def save_experiment(self, name=''):
    '''Write the parameter properties and sensitivity matrix to files.'''
    if name == '':
      sm_fname = os.path.join(self.work_dir, 'sample_matrix.csv')
      pp_fname = os.path.join(self.work_dir, 'param_props.csv')
      info_fname = os.path.join(self.work_dir, 'info.txt')
    else:
      sm_fname = "{}_sample_matrix.csv".format(name) 
      pp_fname = '{}_param_props.csv'.format(name)
      info_fname = '{}_info.txt'.format(name)

    for p in [sm_fname, pp_fname, info_fname]:
      if not os.path.exists(os.path.dirname(p)):
        pathlib.Path(os.path.dirname(p)).mkdir(parents=True, exist_ok=True)

    self.sample_matrix.to_csv(sm_fname, index=False)
    pd.DataFrame(self.params).to_csv(pp_fname, index=False)
    with open(info_fname, 'w') as f:
      f.writelines("sampling_method: {}\n".format(self.sampling_method))
      f.writelines("initial_params_seedpath: {}\n".format(self.__seedpath))

  def load_experiment(self, param_props_path, sample_matrix_path, info_path):
    '''Load parameter properties and sample matrix from files.'''

    with open(info_path) as f:
      data = f.readlines()

    for l in data:
      if 'sampling_method' in l:
        self.sampling_method = l.split(':')[1].strip()
      if 'initial_params_seedpath' in l:
        self.__seedpath = l.split(':')[1].strip()

    self.sample_matrix = pd.read_csv(sample_matrix_path)
    self.params = pd.read_csv(param_props_path, 
        dtype={'name':'S10','cmtnum':np.int32,}, 
        converters={'bounds': ast.literal_eval}
    )

    self.params = self.params.to_dict(orient='records')

    # nan to None so that self.pftnum() function works later 
    for x in self.params:
      if 'name' in x.keys():
        x['name'] = x['name'].decode('utf-8')
      if 'pftnum' in x.keys():
        if pd.isna(x['pftnum']): # could try np.isnan
          x['pftnum'] = None
        else:
          x['pftnum'] = int(x['pftnum'])


  def clean(self):
    '''
    Remove the entire tree at `self.work_dir`.
    
    This function is NOT CAREFUL, so be careful using it!
    '''
    shutil.rmtree(self.work_dir, ignore_errors=True)
    os.makedirs(self.work_dir)

  def get_sensitivity_csvs(self):
    '''
    Looks for all the sensitivity.csv files that are present in
    the run directories. The sensitivity.csv files are created
    using the extract_data_for_sensitivity_analysis(..) funciton.

    Returns
    -------
    file_list : list of strings
      list of paths to sensitivity.csv files, one for each file run folder
    '''
    pattern = '{}/*/sensitivity.csv'.format(self.work_dir)
    file_list = sorted(glob.glob(pattern, recursive=True))
    return file_list

  def info(self):
    '''
    Print some summary info about the SensitivityDriver object.

    Not sure how to best handle the summary of outputs yet. Maybe
    a separate method. The problem is that existing outputs may 
    be leftover from prior runs and thus may not match the existing
    params and sample_matrix data. But I don't want to be too
    aggressive in cleaning up old outputs incase they are expensive 
    to re-create.

    Returns
    -------
    None
    '''

    def lookup_pft_verbose_name(row):
      if row.pftnum >= 0 and row.pftnum < 10:
        pft_verbose_name = pu.get_pft_verbose_name(
          cmtnum=self.cmtnum(), pftnum=row.pftnum, 
          lookup_path=self.get_initial_params_dir()
        )
      else:
        pft_verbose_name = None
      return pft_verbose_name

    # Not all class attributes might be initialized, so if an 
    # attribute is not set, then print empty string.
    try:
      # DataFrame prints nicely
      df = pd.DataFrame(self.params)
      # prevents printing nan
      # Might want to make this more specific to PFT column, 
      # in case there somehow ends up being bad data in one of the 
      # number columns that buggers things farther along?
      df['PFT Name'] = df.apply(lookup_pft_verbose_name, axis=1)
      df = df.where(df.notna(), '')
      ps = df.to_string()
    except AttributeError:
      ps = "[not set]"

    try:
      #sms = self.sample_matrix.head()
      sms = self.sample_matrix.shape
    except AttributeError:
      sms = "[not set]"    

    info_str = textwrap.dedent('''\
      --- Setup ---
      work_dir: {workdir}
      site: {site}
      pixel(y,x): ({pxY},{pxX})
      cmtnum: {cmtnum}
      sampling_method: {sampmeth}

      '''.format(
        workdir=self.work_dir, site=self.site, 
        pxY=self.PXy, pxX=self.PXx, cmtnum=self.cmtnum(),
        sampmeth=self.sampling_method))

    info_str += textwrap.dedent('''\
      --- Parameters ---
      '''.format())
    info_str += '{}\n\n'.format(ps)


    info_str += textwrap.dedent('''\
      --- Sample Matrix ---
      sample_matrix shape: {}

      '''.format(sms))

    info_str += textwrap.dedent('''\
      --- Outputs ---
      > NOTE - these may be leftover from a prior run!
      found {} existing sensitivity csv files.

      '''.format(len(self.get_sensitivity_csvs())))



    return info_str

  def core_setup(self, row, idx, initial=False):
    '''Sets up a sample run folder for the given ``idx`` and ``row``.

    The following things are assumed:

     - you have called set_working_directory()
     - you have called set_seed_path()
     - you have called designe experiment - OR you at least have:
     - you have a sample_matrix
     - you have a list of param specs

    Do all the work to setup and configure a model run.
    Uses the `row` parameter (one row of the sample matrix) to
    set the parameter values for the run.

    Currently relies on command line API for various ``dvmdostem``
    helper scripts. Would be nice to transition to using a Python
    API for all these helper scripts (modules).

    Parameters
    ----------
    row : dict
      One row of the sample matrix, in dict form. So like this:
      `{'cmax': 108.2, 'rhq10': 34.24}` with one key for each parameter name.

    idx : int
      The row index of the `sample_matrix` being worked on. Gets
      used to set the run specific folder name, i.e. sample_000001.

    Returns
    -------
    None
    '''
    #print("PROC:{}  ".format(multiprocessing.current_process()), row)

    def rowkey2pdict(key):
      '''
      Examples
      =========
      >>> rowkey2pdict('cmax_pft3')
      ('cmax', '3') 
      >>> rowkey2pdict('rhq10')
      (rhq10, None)
      '''
      pname, *p = key.split('_pft')
      if len(p) > 0:
        pftnum = p[0]
      else:
        pftnum = None
      return pname, pftnum

    def pdict2rowkey(pdict):
      '''Takes a parameter dict and returns something like cmax_1
      
      Examples
      ========
      >>> pdict2rowkey({'name': 'cmax','bounds': [117.0, 143.0], 'initial': 130.0,'cmtnum': 5, 'pftnum': 0})
      'cmax_pft0'
      '''
      if 'pftnum' in pdict.keys():
        key = "{}_pft{}".format(pdict['name'], pdict['pftnum'] )
      else:
        key = pdict['name']
      return key

    if initial:
      #print("Ignoring idx, it is not really relevant here.")
      #print("Ignoring row dict, not really relevant here.")
      # Build our own row dict, based on initial values in params
      row = {pdict2rowkey(pd): pd['initial'] for pd in self.params}
      sample_specific_folder = os.path.join(self.work_dir, self.get_initial_params_dir())
      if os.path.isdir(sample_specific_folder):
        shutil.rmtree(sample_specific_folder)
    else:
      sample_specific_folder = self._ssrf_name(idx)

    # Make the working directory
    setup_working_directory.cmdline_entry([
      '--input-data-path', self.site, 
      sample_specific_folder
    ])

    # Adjust run mask for appropriate pixel
    runmask_util.cmdline_entry([
      '--reset',
      '--yx',self.PXy, self.PXx,
      '{}/run-mask.nc'.format(sample_specific_folder)
    ])

    # Enable outputs as specified
    for output_spec in self.outputs:
      outspec_utils.cmdline_entry([
        '{}/config/output_spec.csv'.format(sample_specific_folder),
        '--on', output_spec['name'], 'month'
      ])

    # Make sure CMTNUM output is on
    outspec_utils.cmdline_entry([
      '{}/config/output_spec.csv'.format(sample_specific_folder),
      '--on','CMTNUM','y'
    ])

    # Adjust the config file
    CONFIG_FILE = os.path.join(sample_specific_folder, 'config/config.js')
    # Read the existing data into memory
    with open(CONFIG_FILE, 'r') as f:
      config = json.load(f)
    
    config['IO']['output_nc_eq'] = 1 # Modify value...

    # Write it back..
    with open(CONFIG_FILE, 'w') as f:
      json.dump(config, f, indent=2)

    # modify parameters according to sample_matrix (param values)

    # row is something like {'cmax_pft1':2344, 'cmax_pft2':2344, 'rhq10':45} 
    # 
    # iterate over the items in row, we need to find the parameter dict (out of
    # the self.params list) that matches the item in the row. The problem is
    # that in the parameter dict, pft is encoded with a key, where as in the
    # row, it is an item in the row...so we can look up the 
    for rowkey, pval in row.items():
      pname, pft = rowkey2pdict(rowkey)
      for pdict in self.params:
        if pname == pdict['name']:
          if not pft and 'pftnum' not in pdict.keys():
            #print("GOT ONE!", rowkey, pval, pname, pft, pdict, flush=True)
            pu.update_inplace(
              pval, os.path.join(sample_specific_folder, 'parameters'), 
              pdict['name'], pdict['cmtnum'], pft
            )
          if pft and 'pftnum' in pdict.keys():
            if pdict['pftnum'] is not None:
              if int(pft) == int(pdict['pftnum']):
                #print("GOT ONE!", rowkey, pval, pname, pft, pdict, flush=True)
                pu.update_inplace(
                  pval, os.path.join(sample_specific_folder, 'parameters'), 
                  pdict['name'], pdict['cmtnum'], pft
                )
            else:
              pass # pftnum key is set, but value is None, so not a PFT parameter...
          else:
            pass # might be same param name, different pft
        else:
          pass # wrong parameter dict





  def setup_multi(self, force=False):
    '''
    Makes one run directory for each row in sample matrix.

    This is essentially a wrapper around `core_setup(..)` 
    that allows for parallelization.
    
    Returns
    -------
    None
    '''
    if not force:
      if any(os.scandir(self.work_dir)):
        raise RuntimeError('''SensitivityDriver.work_dir is not empty! You must run SensitivityDriver.clean() before designing an experiment.''')

    # Start fresh...
    self.clean()

    # Save the metadata type stuff
    self.save_experiment()

    # Make a special directory for the "initial values" run.
    # row and idx args are ignored when setting up initial value run. 
    self.core_setup(row={'ignore this and idx':None}, idx=324234, initial=True)

    # Make the individial sample directories
    args = list(zip(self.sample_matrix.to_dict(orient='records'),
               range(0,len(self.sample_matrix)), 
               np.zeros(len(self.sample_matrix), dtype=bool)))

    with multiprocessing.Pool(processes=(os.cpu_count()-1)) as pool:
      results = pool.starmap(self.core_setup, args)



  def cmtnum(self):
    '''
    Enforces that there is only one cmtnum specified
    amongst all the param specifications in `self.params`.

    Returns
    -------
    cmtnum : int or None
      The cmtnum specified, or None if cmt not set.
    
    Raises
    ------
    RuntimeError - if there in valid specification of
    cmtnum in the params list.
    '''
    try:
      c = set([x['cmtnum'] for x in self.params])
      if not (len(c) == 1):
        raise RuntimeError("Problem with cmt specification in param_spec!")
      c = c.pop()
    except AttributeError:
      c = None
    except KeyError:
      c = None
    
    return c
  
  def _ssrf_name(self, idx):
    '''generate the Sample Specific Run Folder name.'''
    return os.path.join(self.work_dir, 'sample_{:09d}'.format(idx))

  def _ssrf_names(self):
    '''Generate a list of Sample Specific Run Folder names.'''
    return [self._ssrf_name(i) for i in range(0,len(self.sample_matrix))]

  def run_all_samples(self):
    '''
    Starts run in each Sample Specific Run Folder.

    Wrapper around `run_model(..)` that allows for parallelization.
    '''

    folders = self._ssrf_names()

    with multiprocessing.Pool(processes=(os.cpu_count()-1)) as pool:
      results = pool.map(self.run_model, folders)
    print()

  def run_model(self, rundirectory):
    '''
    Run the model. 
    
    Assumes everything is setup in a "Sample Specific Run Folder".
    
    Returns
    -------
    None
    '''
    program = '/work/dvmdostem'
    ctrl_file = os.path.join(rundirectory, 'config','config.js')
    opt_str = '-l err --force-cmt {} --ctrl-file {}'.format(self.cmtnum(), ctrl_file)
    cmdline = program + ' ' + self.opt_run_setup + opt_str
    with log_wrapper(cmdline, tag='run') as lw:
      completed_process = subprocess.run(
        cmdline,             # The program + options 
        shell=True,          # must be used if passing options as str and not list
        check=True,          # raise CalledProcessError on failure
        #capture_output=True,# collect stdout and stderr; causes memory problems I think
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=rundirectory)    # control context
      if not completed_process.returncode == 0:
        print(completed_process.stdout)
        print(completed_process.stderr)

  def first_steps_sensitivity_analysis(self):
    '''
    Grab the summarized sensitivity csvs and glue them
    together, then make correlation matrix. When glued together, 
    the data will look like this, with one row for each sample, 
    and one column for each parameter followed by one column for
    each output:

    :: 

      p_cmax,  p_rhq10,   p_micbnup,   o_GPP,  o_VEGC
      1.215,   2.108,     0.432,       0.533,  5.112
      1.315,   3.208,     0.632,       0.721,  8.325
      1.295,   1.949,     0.468,       0.560,  5.201
      1.189,   2.076,     0.420,       0.592,  5.310
      1.138,   2.035,     0.441,       0.537,  5.132
      1.156,   1.911,     0.433,       0.557,  5.192
    
    Return
    ------
    None
    '''

    # Elchin: please improve or comment on this function. 
    # Feel free to change the name of the function as you see fit!
    # Is there more we need to do to collect the data in a meaningful
    # way?

    # pattern = '{}/*/sensitivity.csv'.format(self.work_dir)
    # file_list = sorted(glob.glob(pattern, recursive=True))
    file_list = self.get_sensitivity_csvs()
    df = pd.concat( map(pd.read_csv, file_list), ignore_index=True)
    #df = df.sort_values('p_cmax')
    #print(df)
    #print()
    corr = df.corr()
    print(corr)
    print("Make some cool plot here....")

  def make_cool_plot_2(self):
    '''
    stitches all run stages together and plots one 
    line for each sample run.

    Return
    ------
    None
    '''

    # Elchin please improve or comment on this plot!
    # It is meant mostly as an exmaple of how you might
    # access and process the dvmdostem output data.
 
    fig, axes = plt.subplots(len(self.outputs))

    for r in os.listdir(self.work_dir):
      for i, o in enumerate(self.outputs):
        pattern = os.path.join(self.work_dir, r, 'output', '{}_monthly_*.nc'.format(o['name']))
        results = glob.glob(pattern, recursive=True)

        all_data = pd.DataFrame({}, columns=[o['name']])
        def sort_stage(x):
          STAGE_ORDER = {'pr':0, 'eq':1, 'sp':2, 'tr':3, 'sc':4}
          stg = os.path.splitext(os.path.basename(x))[0][-2:]
          return STAGE_ORDER[stg]

        for f in sorted(results, key=sort_stage):
          stg_data = nc.Dataset(f, 'r')
          d = stg_data.variables[o['name']][:]
          if o['type'] == 'pool':
            d = ou.average_monthly_pool_to_yearly(d)
          elif o['type'] == 'flux':
            d = ou.sum_monthly_flux_to_yearly(d)
          else:
            print("What the heck??")
          d = ou.sum_across_pfts(d)
          d = pd.DataFrame(d[:,self.PXy,self.PXx], columns=[o['name']])
          all_data = all_data.append(d, ignore_index=True)

        axes[i].plot(all_data)
        axes[i].set_ylabel(o['name'])
    plt.show()

  def extract_data_for_sensitivity_analysis(self, posthoc=True, multi=True):
    '''
    Creates a csv file in each run directory that summarizes the run's
    parameters and outut. The csv file will look something like this:

    ::

        p_cmax,  p_rhq10,   p_micbnup,   o_GPP,  o_VEGC
        1.215,   2.108,     0.432,       0.533,  5.112
    
    with one column for each parameter and one column for each output.

    ::

      For each row in the sensitivity matrix (and corresponding run folder), 
        For each variable specified in self.outputs:
            - opens the NetCDF files that were output from dvmdostem
            - grabs the last datapoint
            - writes it to the sensitivity.csv file

    Parameters
    ----------
    posthoc : bool (Not implemented yet)
      Flag for controlling whether this step should be run after the model run
      or as part of the model run
    
    multi : bool (Not implemented yet)
      Flag for if the runs are done all in one directory or each in its own
      directory. If all runs are done in one directory then paralleization is
      harder and this step of collating the output data must be done at the end
      of the run before the next run overwrites it.
      
    Returns
    -------
    None
    '''
    
    for row in self.sample_matrix.itertuples():
      sample_specific_folder = self._ssrf_name(row.Index)
      sensitivity_outfile = os.path.join(sample_specific_folder, 'sensitivity.csv')

      # Not sure if this is how we want to set things up...
      # Seems like each of these files will have only one row, but the 
      # advantage of having a sensitivity file per sample directory is that
      # we can leverage the same parallelism for running this function
      # Then we'll need another step to collect all the csv files into one
      # at the end.

      def make_col_name(pdict):
        '''Given a parameter, returns a column name like p_rhq10 or p_cmax_1, 
        depending on whether the parameter is specified by PFT or not...'''
        s = f"p_{pdict['name']}"
        if 'pftnum' in pdict.keys():
          s+= f"_pft{pdict['pftnum']}"
        return s

      pstr = ','.join(make_col_name(p) for p in self.params)
      #pstr = ','.join(['p_{}???'.format(p['name'], ) for p in self.params]) 
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

        # Not sure what is most meaningful here, so collapsing PFT dimension
        # into ecosystem totals...
        data_y_eco = ou.sum_across_pfts(data_y)

        # TODO: Need to handle non-PFT outputs!
        ostr += '{:2.3f},'.format(data_y_eco[-1,self.PXy,self.PXx])

      ostr = ostr.rstrip(',') # remove trailing comma...
 
      with open(sensitivity_outfile, 'a') as f:
        f.write(pstr + ',' + ostr + '\n')

  def plot_sensitivity_matrix(self):
    '''
    Make a quick plot showing the properties of the sensitivity matrix.
    
    One row for each parameter:
      Left column is sample values with bounds marked in red.
      Middle column is histogram of sample values.
      Right column is boxplot of sample values

    '''

    # Elchin: please improve or comment on this plot. I am not sure
    # what the standard, meaningful ways to visualize the sample matrix
    # data are!

    fig, axes = plt.subplots(len(self.params),3)

    for i, (p, ax) in enumerate(zip(self.params, axes)):
      ax[0].plot(self.sample_matrix.iloc[:, i], marker='.', linewidth=0)
      ax[0].set_ylabel(p['name'])
      ax[0].hlines(p['bounds'], 0, len(self.sample_matrix)-1, linestyles='dotted', colors='red')
      ax[1].hist(self.sample_matrix.iloc[:, i], range=p['bounds'], orientation='horizontal', alpha=0.75, rwidth=0.8)
      ax[2].boxplot(self.sample_matrix.iloc[:, i])
      ax[2].set_ylim(ax[0].get_ylim())
      
    plt.tight_layout()

if __name__ == '__main__':
  import doctest
  doctest.testmod()
  
  # For some reason if the exteral testfile is run here as well as the testmod()
  # function, the external test file fails! The external testfile runs fine on
  # its own, (e.g.: python -m doctest doctests_Sensitivity.py) and if you run 
  # the external testfile here by itself (without also calling 
  # doctest.testmod()) then it works. But if you run both of them here, then 
  # a couple of the tests in the external testfile fail??? So commenting out
  # for now.
  #doctest.testfile("doctests_Sensitivity.md")
    
