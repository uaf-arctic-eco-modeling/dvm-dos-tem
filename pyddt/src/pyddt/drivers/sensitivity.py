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


from . import basedriver
from .. import util

@contextmanager
def log_wrapper(message):
  '''
  Print the ``message`` with the process name at the beginning.

  Use via a context manager, for example:

    .. code:

      with log_wrapper("my message") as _: pass

  To get something like this:

    .. code:

      ForkPoolWorker-4: my message

  '''
  pin = multiprocessing.current_process().name
  print(f'{pin}: {message}', flush=True)
  try:
    yield
  finally:
    pass


def make_col_name(pdict):
  '''
  Make standardized column names for parameters.

  Expects ``pdict`` to be a dictionary of items related to a parameter, e.g.:

  .. code:

    {'name': 'micbnup',
    'bounds': '[0.0729, 1.387]',
    'initial': 0.73,
    'cmtnum': 6,
    'pftnum': nan}


  Returns
  =======
  col_name : str
    A string to use for the sample_matrix column name. Should be simply the
    parameter name for non-PFT parameters and for PFT parameters, the name
    should be suffixe with _pftN where N is the PFT number.
  '''
  s = f"{pdict['name']}"
  if 'pftnum' in pdict.keys():
    tests = [#np.isnan(pdict['pftnum']), # can't handle string
             pdict['pftnum'] == '',
             pdict['pftnum'] == 'Nan',
             pdict['pftnum'] == 'NaN',
             pdict['pftnum'] == 'nan',
             pd.isna(pdict['pftnum']), # handles strings, etc
             pd.isnull(pdict['pftnum']),
             pdict['pftnum'] is None, ]
    if any(tests):
      pass
    else:
      s+= f"_pft{pdict['pftnum']}"
  return s


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

  # TO DO:
  #  - add concept of seed for reproducibility
  #  - add concept of log params for small intervals

  #print(param_props)
  l = np.random.uniform(size=(N, len(param_props)))

  # Generate bounds, based on specification in params list
  lows = np.array([p['bounds'][0] for p in param_props])
  highs = np.array([p['bounds'][1] for p in param_props])

  # Figure out the spread, or difference between bounds
  spreads = highs - lows

  sm = l * spreads + lows

  return pd.DataFrame(sm, columns=[make_col_name(p) for p in param_props])


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

  names = [make_col_name(p) for p in param_props]

  return pd.DataFrame(sample_matrix, columns=names)


def params_from_seed(seedpath, params, pftnums, percent_diffs, cmtnum):
  '''
  Builds a list of "param specifications" from the data in the `seedpath` and
  for params specified in `params` for the pfts specified in `pftnums` and the
  Community specified in `cmtnum`. Sets bounds based on the intial values
  found in the `seedpath` and according to the percent_diffs.
  
  NOTE: What happens for negative numbers? Do the bounds need to be reversed?
  
  '''

  assert len(params) == len(pftnums), "params list and pftnums list must be same length!"
  assert len(params) == len(percent_diffs), "params list and percent_diffs list must be same length"

  final = []
  plu = util.param.build_param_lookup(seedpath)

  for pname, pftnum, perturbation in zip(params, pftnums, percent_diffs):
    original_pdata_file = util.param.which_file(seedpath, pname, lookup_struct=plu)

    p_db = util.param.get_CMT_datablock(original_pdata_file, cmtnum)
    p_dd = util.param.cmtdatablock2dict(p_db)

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
      elif isinstance(pftnum, list):
        for pftidx in pftnum:
          p_initial = p_dd['pft{}'.format(pftidx)][pname]
          p_bounds = [p_initial - (p_initial*perturbation), p_initial + (p_initial*perturbation)]
          final.append(dict(name=pname, bounds=p_bounds, initial=p_initial, cmtnum=cmtnum, pftnum=pftidx))
      elif isinstance(pftnum, int):
        p_initial = p_dd['pft{}'.format(pftnum)][pname]
        p_bounds = [p_initial - (p_initial*perturbation), p_initial + (p_initial*perturbation)]
        final.append(dict(name=pname, bounds=p_bounds, initial=p_initial, cmtnum=cmtnum, pftnum=pftnum))

  return final
  


class Sensitivity(basedriver.BaseDriver):
  '''
  Sensitivity Analysis Driver class.

  Driver class for conducting a ``dvmdostem`` sensitivity analysis. Methods for
  cleaning, setup, running model, collecting outputs.

  Basic overview of use is like this:

    1. Design your experiment by choosing working directory, seed path,
       parameters to use, number of samples, etc.
    2. Instantiate driver object. 
    3. Use driver object to setup the run folders.
    4. Use driver object to carry out model runs.
    5. Use driver object to summarize/collect outputs.
    6. Use SA_post_hoc_analysis script to make plots and anaylsis.
  '''
  def __init__(self, config, **kwargs):
    '''
    Create a Sensitivity driver object.

    Parameters
    ----------
    config : dict
      A dictionary of configuration keys for setting up the object. 
    **kwargs :
      Optional extra arugments (nothing implemented at this time)

    Required keys for config dict
    ------------------------------
    params : list of strings
      The list of parameters that should be analyzed.
    sampling_method : string, {'uniform','lhc'}
      Which method to use for drawing parameter samples from sampling space.
    pftnums : list of ints
      The list of PFT numbers that should be analyzed. Length must match params.
    seed_path : string
      Path to a directory to use for see parameters.
    cmtnum : int
      The Community Type number (CMT) to use.
    N_samples : int
      The number of samples that the sensitivity analysis should run.
    '''
    #print(f"Sensitivity ctor\n{self=}\n{config=}\n{kwargs=}\n")
    super().__init__(config, **kwargs)

    # Handle kwargs here if necessary...

    # This is stuff that is specific to the sensitivity analysis
    self.params = None
    self.sample_matrix = None
    self.targets = None
    self.targets_meta = None # can't remember what this is used for?
    self.sampling_method = None
    self.calib_mode = None

    # A whole bunch of these are required and the object will fail to
    # instantiate the the config dict is missing the right data!!

    # Set if the user has provided them in the config
    if 'sampling_method' in config.keys():
      self.sampling_method = config['sampling_method']

    if 'calib_mode' in config.keys():
      self.calib_mode = config['calib_mode']

    if 'N_samples' in config.keys():
      N_samples = config['N_samples']

    if 'cmtnum' in config.keys():
      self.cmtnum = config['cmtnum']

    if 'params' not in config.keys():
      raise RuntimeError("You must have ``params`` to instantiate a Sensitivity driver!")

    if 'pftnums' not in config.keys():
      raise RuntimeError("You must specifiy the ``pftnums`` array. Use ``None`` for non-PFT parameters.")

    if 'percent_diffs' in config.keys() and 'p_bounds' in config.keys():
      raise RuntimeError("You musn't specify both percent_diffs and p_bounds at the same time. Choose one.")

    # OK this is slightly awkward - basically even if the user specified 
    # p_bounds, it ends up being easiest to setup the params structure using
    # the percent_diffs concept and then overwrite the bounds... alternatively
    # we could modify the params_from_seed function...
    if 'percent_diffs' not in config.keys():
      # use +/-90% for default perturbation
      percent_diffs = np.ones(len(config['params'])) * 0.9
    else:
      percent_diffs = config['percent_diffs']

    if 'params' in config.keys() and 'pftnums' in config.keys():
      self.params = params_from_seed(seedpath=self._seedpath, 
                                     params=config['params'], 
                                     pftnums=config['pftnums'], 
                                     percent_diffs=percent_diffs, 
                                     cmtnum=self.cmtnum)

    if 'p_bounds' in config.keys():
      assert len(self.params) == len(config['p_bounds']), "Length of params array and p_bounds array must be the same."
      for par, bnds in zip(self.params, config['p_bounds']): 
        par['bounds'] = bnds

    # Order matters here - gotta load the target data before we
    # setup the outputs...
    if 'observations' in config.keys():
      self.load_target_data(config['observations'])

    if 'target_names' in config.keys():
      self.setup_outputs(config['target_names'])

    # TODO: Handle naming the sample matrix columns??
    if self.sampling_method == 'lhc':
      self.sample_matrix = generate_lhc(N_samples, self.params)
    elif self.sampling_method == 'uniform':
      self.sample_matrix = generate_uniform(N_samples, self.params)
    else:
      raise RuntimeError(f"{self.sampling_method} is not implemented as a sampling method.")



  def get_initial_params_dir(self):
    '''
    Assumes that the working directory will have an ``initial_params_rundir``
    directory that will have the initial parameter values.

    Returns the path to the intial parameter run directory or None if the 
    objec't ``work_dir`` has not been set.
    '''
    if self.work_dir:
      return os.path.join(self.work_dir, 'initial_params_run_dir')
    else:
      return None

  def load_observations(self):
    '''
    Might want this to handle obs for data that are not in the
    calibration_targets.py file. This would need to be tied in with the 
    setup_outputs(...) function.
    '''
    print("NOT IMPLEMENTED")
    pass


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
      if self._seedpath is not None:
        lookup_path = self._seedpath
      elif self.get_initial_params_dir() is not None:
        lookup_path = os.path.join(self.get_initial_params_dir(), 'parameters')
      else:
        pft_verbose_name = None
        return pft_verbose_name

      if row.pftnum >= 0 and row.pftnum < 10:
        pft_verbose_name = util.param.get_pft_verbose_name(
          cmtnum=self.cmtnum, pftnum=row.pftnum, 
          lookup_path=lookup_path,
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
        pxY=self.PXy, pxX=self.PXx, cmtnum=self.cmtnum,
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



  def design_experiment(self, Nsamples, cmtnum, params, pftnums, 
      percent_diffs=None, sampling_method='lhc'):
    '''
    .. deprecated::
      Implemented in default constructor.

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
      List values, one for each parameter in `params`. The value is used to set
      the bounds with respect to the intial parameter value. I.e. passing a
      value in the percent_diff array of .3 would mean that bounds should be
      +/-30% of the initial value of the parameter.

    TODO: add somethign that lets you use non percentage based sampling range.
    
    sampling_method : str
      A string indicating which sampling method to use for getting values for
      the sample matrix. Currently the options are 'lhc' or 'uniform'. 

    Returns
    -------
    None
    '''
    self.cmtnum = cmtnum
    self.sampling_method = sampling_method

    if os.path.isdir(self.work_dir):
      if len(os.listdir(self.work_dir)) > 0:
        error_msg = textwrap.dedent(f'''\
            Sensitivity.work_dir ({self.work_dir}) is not empty! You must run 
            Sensitivity.clean() before designing an experiment.''')
        raise RuntimeError(error_msg)

    if not percent_diffs:
      percent_diffs = np.ones(len(params)) * 0.1 # use 10% for default perturbation

    self.params = params_from_seed(seedpath=self._seedpath, params=params, 
        pftnums=pftnums, percent_diffs=percent_diffs, cmtnum=cmtnum)

    if self.sampling_method == 'lhc':
      self.sample_matrix = generate_lhc(Nsamples, self.params)
    elif sampling_method == 'uniform':
      self.sample_matrix = generate_uniform(Nsamples, self.params)
    else:
      raise RuntimeError(f"{self.sampling_method} is not implemented as a sampling method.")

    # This little helper function is duplicated elsewhere in this file
    # and should be consolidated...
    def pdict2colname(pdict):
      '''Takes a parameter dict and returns something like cmax_pft1

      Examples
      ========
      >>> pdict2rowkey({'name': 'cmax','bounds': [117.0, 143.0], 'initial': 130.0,'cmtnum': 5, 'pftnum': 0})
      'cmax_pft0'
      '''
      if 'pftnum' in pdict.keys():
        if pdict['pftnum'] is not None:
          key = "{}_pft{}".format(pdict['name'], pdict['pftnum'] )
        else:
          key = pdict['name']
      else:
        key = pdict['name']
      return key

    # Fix the names on the sample matrix columns. Make sure that the
    # column names have the PFT info.
    self.sample_matrix.columns = [pdict2colname(p) for p in self.params]



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
      f.writelines(f"sampling_method: {self.sampling_method}\n")
      f.writelines(f"initial_params_seedpath: {self._seedpath}\n")
      f.writelines(f"site: {self.site}\n")
      f.writelines(f"PXx: {self.PXx}\n")
      f.writelines(f"PXy: {self.PXy}\n")
      f.writelines(f"--opt-run: {self.opt_run_setup}\n")
      f.writelines(f"outputs: {self.outputs}\n")


  def load_experiment(self, param_props_path, sample_matrix_path, info_path):
    '''Load parameter properties and sample matrix from files.'''

    with open(info_path) as f:
      data = f.readlines()

    for l in data:
      if 'sampling_method' in l:
        self.sampling_method = l.split(':')[1].strip()
      if 'initial_params_seedpath' in l:
        self._seedpath = l.split(':')[1].strip()

    self.sample_matrix = pd.read_csv(sample_matrix_path)
    self.params = pd.read_csv(param_props_path, 
        dtype={'name':'S10','cmtnum':np.int32,}, 
        converters={'bounds': ast.literal_eval}
    )



    self.params = self.params.to_dict(orient='records')

    # cmtnumber should be the same for every param
    cmtnums = [p['cmtnum'] for p in self.params]
    if len(set(cmtnums)) != 1:
      raise RuntimeError("Problem loading experiment! Can't figure out cmtnumber.")
    self.cmtnum = cmtnums[0]

    # nan to None so that self.pftnum() function works later 
    for x in self.params:
      if 'name' in x.keys():
        x['name'] = x['name'].decode('utf-8')
      if 'pftnum' in x.keys():
        if pd.isna(x['pftnum']): # could try np.isnan
          x['pftnum'] = None
        else:
          x['pftnum'] = int(x['pftnum'])

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

  def core_setup(self, row, idx, initial=False):
    '''Sets up a sample run folder for the given ``idx`` and ``row``.

    The following things are assumed:

     - you have called set_working_directory()
     - you have called set_seed_path()
     - you have called design experiment OR you at least have:
        * a sample_matrix
        * a list of param specs

    Do all the work to setup and configure a model run. Uses the `row` parameter
    (one row of the sample matrix) to set the parameter values for the run.

    Currently relies on command line API for various ``dvmdostem`` helper
    scripts. Would be nice to transition to using a Python API for all these
    helper scripts (modules).

    Parameters
    ----------
    row : dict
      One row of the sample matrix, in dict form. So like this: 

         ``{'cmax_pft0': 108.2, 'rhq10': 34.24}``

      with one key for each parameter name.

    idx : int
      The row index of the `sample_matrix` being worked on. Gets used to set the
      run specific folder name, i.e. sample_000001.

    initial : bool
      A flag indicating whether the folder to be setup  is the special "initial
      value" folder.


    Returns
    -------
    None
    '''
    #with log_wrapper(f"In core_setup, {row=}") as _: pass
    def rowkey2pdict(key):
      '''
      Takes a key such as 'rhq10' or 'cmax_pft1' and returns the parameter
      name and the pft number.

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

    # This function is duplicated elsewhere and should be consolidated.
    def pdict2rowkey(pdict):
      '''
      Takes a parameter dict and returns something like 'cmax_pft1' or
      rhq10'
      
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
    util.setup_working_directory.cmdline_entry([
      '--input-data-path', self.site, 
      '--seed-parameters', self._seedpath,
      sample_specific_folder
    ])

    # Strip all extra CMTs from parameter files
    util.param.cmdline_entry([
      '--extract-cmt',
      os.path.join(sample_specific_folder, 'parameters'),
      f'CMT{self.cmtnum:02d}',
      sample_specific_folder
    ])
    # The above creates a directory e.g. CMT01, in the sample folder
    # so here we delete the parameters folder and move one that we just
    # created to parameters
    shutil.rmtree(os.path.join(sample_specific_folder, "parameters/"))
    os.rename(os.path.join(sample_specific_folder, f'CMT{self.cmtnum:02d}'),
              os.path.join(sample_specific_folder, 'parameters'))

    # Adjust run mask for appropriate pixel
    util.runmask.cmdline_entry([
      '--reset',
      '--yx',self.PXy, self.PXx,
      '{}/run-mask.nc'.format(sample_specific_folder)
    ])

    # Looks like for the most part the mads_sensitivity.py was relying on just
    # using the --enable-cal-vars and was not trying to leave outputs
    # configurable in the .yaml file...which worked, but was inefficient when
    # the user is only looking at one or two of the output variables.
    #
    #util.outspec.cmdline_entry([
    #  '--enable-cal-vars',
    #  '{}/config/output_spec.csv'.format(sample_specific_folder),
    #])

    # First clear the file incase the user has funky modifications in their repo's
    # copy of the template output spec file.
    # maybe a flag should be added to setup_working_directory.py that can
    # enforce starting with an empty outspec file...
    util.outspec.cmdline_entry([
      '{}/config/output_spec.csv'.format(sample_specific_folder),
      '--empty',
    ])

    # Next run thru the requested outputs toggling them on in the file.
    for output_spec in self.outputs:
      util.outspec.cmdline_entry([
        '{}/config/output_spec.csv'.format(sample_specific_folder),
        '--on', output_spec['ncname'], 
        output_spec['timeres'],
        output_spec['pftres'],
        output_spec['cpartres'],
        output_spec['layerres'],
      ])

    for output_spec in self.aux_outputs:
      util.outspec.cmdline_entry([
        '{}/config/output_spec.csv'.format(sample_specific_folder),
        '--on', output_spec['ncname'],
        output_spec['timeres'],
        output_spec['pftres'],
        output_spec['cpartres'],
        output_spec['layerres'],
      ])


    # Make sure CMTNUM output is on
    util.outspec.cmdline_entry([
      '{}/config/output_spec.csv'.format(sample_specific_folder),
      '--on','CMTNUM','y'
    ])

    # Adjust the config file
    CONFIG_FILE = os.path.join(sample_specific_folder, 'config/config.js')
    # Read the existing data into memory
    with open(CONFIG_FILE, 'r') as f:
      config = json.load(f)

    # we need netcdf outputs for eq stage
    config['IO']['output_nc_eq'] = 1 # Modify value...

    # customize the modules that should be on for different run stages...
    if self.calib_mode:
      if self.calib_mode.lower() == 'gppallignoringnitrogen':
        config['stage_settings']['eq']["dsl"] = False
        config['stage_settings']['eq']["nfeed"] = False

      # I believe these default to on, but just in case, set them here...
      if self.calib_mode.lower() in ('nppall', 'vegc'):
        config['stage_settings']['eq']["dsl"] = True
        config['stage_settings']['eq']["nfeed"] = True

    # Write it back..
    with open(CONFIG_FILE, 'w') as f:
      json.dump(config, f, indent=2)

    # Modify parameters according to sample_matrix (param values). Iterate over
    # the items in a row, so we can find the param dict (out of the self.params
    # list) that matches the item in the row. Once we know the parameter name
    # and the PFT number, we can use the utility function to modify the
    # parameter in place.
    # row is a dict with one row of the sample matrix, e.g.: 
    #     {'cmax_pft1':2344, 'cmax_pft2':2344, 'rhq10':45} p
    # 
    # pdict is a dict with slightly different shape:
    #      {'name': 'cmax', 'bounds': [2.28, 43.32], 'initial': 22.8, 'cmtnum': 6, 'pftnum': 0}
    # 
    for rowkey, pval in row.items():
      #with log_wrapper(f"parameter modification loop: {rowkey=} {pval=}") as _: pass
      pname, pft = rowkey2pdict(rowkey)
      for pdict in self.params:
        #with log_wrapper(f"inner loop over self.params {pdict=}") as _: pass
        if pname == pdict['name']:
          if not pft and pdict['pftnum'] is None:
            #with log_wrapper(f"Updating a non-PFT param {rowkey=} {pval=} {pname=} {pft=} {pdict=}") as _: pass
            util.param.update_inplace(
              pval, os.path.join(sample_specific_folder, 'parameters'), 
              pdict['name'], pdict['cmtnum'], pft
            )
          if pft and 'pftnum' in pdict.keys():
            if pdict['pftnum'] is not None:
              if int(pft) == int(pdict['pftnum']):
                #with log_wrapper(f"Updating a PFT param {rowkey=} {pval=} {pname=} {pft=} {pdict=}") as _: pass
                util.param.update_inplace(
                  pval, os.path.join(sample_specific_folder, 'parameters'), 
                  pdict['name'], pdict['cmtnum'], pft
                )
            else:
              pass # pftnum key is set, but value could be None, so not a PFT parameter...
          else:
            pass # might be same param name, different pft
        else:
          pass # wrong parameter dict, keep moving...


  def setup_multi(self, force=False):
    '''
    Makes one run directory for each row in sample matrix.

    This is essentially a wrapper around `core_setup(..)` 
    that allows for parallelization.

    As a result of this function, multiple sample folders will be created in
    the object's ``work_dir``. There will be one sample folder for each row
    of the ``sample_matrix``.
    
    Returns
    -------
    None
    '''
    if not force:
      if any(os.scandir(self.work_dir)):
        raise RuntimeError('''Sensitivity.work_dir is not empty! You must run Sensitivity.clean() before designing an experiment.''')

    # Start fresh...
    self.clean()

    # Save the metadata type stuff
    self.save_experiment()

    self.plot_sensitivity_matrix(save=True)

    # Make a special directory for the "initial values" run.
    # row and idx args are ignored when setting up initial value run. 
    self.core_setup(row={'ignore this and idx':None}, idx=324234, initial=True)

    # Could save some time here by making a template output_spec.csv file and
    # copying it into the SSRFs rather than individually making each
    # output_spec.csv. Same strategy could be applied to the run mask!

    # Make the individial sample directories
    args = list(zip(self.sample_matrix.to_dict(orient='records'),
               range(0,len(self.sample_matrix)), 
               np.zeros(len(self.sample_matrix), dtype=bool)))

    with multiprocessing.Pool(processes=(os.cpu_count()-1)) as pool:
      results = pool.starmap(self.core_setup, args)


  
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
    Run the model according to the setup.
    
    Assumes everything is setup in a "Sample Specific Run Folder" (SSRF).

    When the run is complete, summarize the output data into a csv file that 
    is written into the SSRF. The csv file has one column for each output.
    The csv file should have only one row.
    
    Returns
    -------
    None
    '''
    program = '/work/dvmdostem'
    ctrl_file = os.path.join(rundirectory, 'config','config.js')
    opt_str = f" -l fatal --force-cmt {self.cmtnum} --ctrl-file {ctrl_file}"
    cmdline = program + ' ' + self.opt_run_setup + opt_str
    with log_wrapper(f"{cmdline=}") as _: pass

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

    # Run the extraction of data from NetCDF to csv for outputs.
    summary_data = self.summarize_ssrf(os.path.join(rundirectory, 'output'))

    # Turn this data into a csv format and write it to a file.
    csv_data = self.ssrf_summary2csv(summary_data)

    with open(os.path.join(rundirectory, 'results.csv'), 'w') as outfile:
      outfile.writelines(csv_data)

    # Make a csv file summarizing equlibrium state for each variable
    # has several columns per PFT with a few equlibrium metrics...
    for var in self.outputs:
      res = util.metrics.eq_quality(
          var['ncname'],
          cmtkey=f"CMT{self.cmtnum:02d}",
          PXx=self.PXx,
          PXy=self.PXy,
          fileprefix=os.path.join(rundirectory, 'output'),
          pref=os.path.join(rundirectory, 'parameters'),
      )
      with open(os.path.join(rundirectory, f"eq_{var['ncname']}_quality.csv"), 'w') as outfile:
        csv_data = pd.DataFrame(res, index=[0]).to_csv(index=False)
        outfile.writelines(csv_data)

    return None

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
            d = util.output.average_monthly_pool_to_yearly(d)
          elif o['type'] == 'flux':
            d = util.output.sum_monthly_flux_to_yearly(d)
          else:
            print("What the heck??")
          d = util.output.sum_across_pfts(d)
          d = pd.DataFrame(d[:,self.PXy,self.PXx], columns=[o['name']])
          all_data = all_data.append(d, ignore_index=True)

        axes[i].plot(all_data)
        axes[i].set_ylabel(o['name'])
    plt.show()

  def post_hoc_build_all(self):
    '''
    After the run is done, go make all the ssrf results.csv files...

    Typically these are created on-the-fly in the run_model(...) function, but
    in some cases it is nice to build them again later.

    Returns
    =======
    None
    '''

    # Make all the individual run summaries. Should parallelize this...
    for ssrf in self._ssrf_names():
      data = self.summarize_ssrf(os.path.join(ssrf, 'output'))
      csv_data = self.ssrf_summary2csv(data)
      with open(os.path.join(ssrf, 'results.csv'), 'w') as outfile:
        outfile.write(csv_data)

    #bring 'em all together into one file in the work dir
    self.collate_results()

    # make the targets file in the work dir too.
    d0 = self.summarize_ssrf(os.path.join(self._ssrf_names()[0], 'output'))
    self.ssrf_targets2csv( d0, os.path.join(self.work_dir, 'targets.csv') )

  def collate_results(self):
    '''
    Gathers up all the results.csv files from individual ssrf folders and
    stuffs them into one giant csv file. Number of rows should match rows in
    sample matrix.

    Writes file "results.csv" to the work dir.

    Returns
    =======
    None
    '''
    results = [os.path.join(ssrf, 'results.csv') for ssrf in self._ssrf_names()]
    df = pd.concat(map(pd.read_csv, results), ignore_index=True)
    with open(os.path.join(self.work_dir, 'results.csv'), 'w') as f:
      f.write(df.to_csv(index=False))

  def collate_eq_metrics(self):
    for var in self.outputs:
      results = [os.path.join(ssrf, f"eq_{var['ncname']}_quality.csv") for ssrf in self._ssrf_names()]
      df = pd.concat(map(pd.read_csv, results), ignore_index=True)
      with open(os.path.join(self.work_dir, f"eq_{var['ncname']}_quality.csv"), 'w') as f:
        f.write(df.to_csv(index=False))

  def summarize_ssrf(self, output_directory_path):
    '''
    Grabs the modeled data from the run and collates it into a list of dicts
    that can then be easily transformed into other formats. The intention here
    is to create a list of dicts that can be fed directly into a
    ``pandas.DataFrame`` with labeled columns.

    And there should be one dict in the list for each variable the outputs list.

    NOTE: This function takes extract the data from the output netcdf files and
    takes the mean over the last 10 timesteps!

    Parameters
    ==========
    output_directory_path : str (path)
      Path to a Sample Specific Run Folder (ssrf).

    Returns
    =======
    data : [{...}, ... {...}], list of dicts
      One dict for each output that is specified. The keys in the dicts will be
      cmt, ncname, ctname, modeled_value, target_value and pft and compartment
      when applicable. For example: 

        { 'cmt': 'CMT06',
          'ncname': 'INGPP', 'ctname': 'GPPAllIgnoringNitrogen',
          'modeled_value': 6.743048039242422, 'target_value': 11.833, 'pft': 0 }

      There will be one dict in the returned list for each output variable. 
    '''
    def standardize(resspec):
      '''
      Standardize the time resolution specification.
      '''
      std = ''
      if resspec.lower() in ['y','yr','yearly','year']:
        std = 'yearly'
      if resspec.lower() in ['m','monthly','month',]:
        std = 'monthly'
      return std

    # Note that the following block of code is quite similar to functions in
    # qcal.py::measure_calibration_quality...(...)
    final_data = []
    last_N_timesteps = 10
    cmtkey = f"CMT{self.targets['cmtnumber']:02d}"
    pref = os.path.join(self.get_initial_params_dir(), 'parameters')

    for output in self.outputs:
      ncname = output['ncname']
      ctname = output['ctname']
      resspec = standardize(output['timeres'])

      data, dims = util.output.get_last_n_eq(ncname, resspec, output_directory_path, n=last_N_timesteps)
      dsizes, dnames = list(zip(*dims))

      #print(ctname, output_directory_path, ncname, dims, dnames, dsizes)
      if dnames == ('time','y','x'):
        truth = self.targets[ctname]
        value = data[:,self.PXy,self.PXx].mean()
        d = dict(cmt=cmtkey, ncname=ncname, ctname=ctname, modeled_value=value, target_value=truth)
        final_data.append(d)

      elif dnames == ('time','y','x','pft'):
        for pft in range(0,10):
          if util.param.is_ecosys_contributor(cmtkey, pft, ref_params_dir=pref):
            truth = self.targets[ctname][pft]
            value = data[:,pft,self.PXy,self.PXx].mean()
            d = dict(cmt=cmtkey, ncname=ncname, ctname=ctname, modeled_value=value, target_value=truth, pft=pft)
            final_data.append(d)
          else:
            pass #print "  -> Failed" # contributor test! Ignoring pft:{}, caltarget:{}, output:{}".format(pft, ctname, ncname)

      elif dnames == ('time','y','x','pft','pftpart'):
        for pft in range(0,10):
          clu = {0:'Leaf', 1:'Stem', 2:'Root'}
          for cmprt in range(0,3):
            if util.param.is_ecosys_contributor(cmtkey, pft, clu[cmprt], ref_params_dir=pref):
              truth = self.targets[ctname][clu[cmprt]][pft]
              value = data[:,cmprt,pft,self.PXy,self.PXx].mean()
              d = dict(cmt=cmtkey, ncname=ncname, ctname=ctname, modeled_value=value, target_value=truth, pft=pft, cmprt=clu[cmprt])
              final_data.append(d)
            else:
              pass #print "  -> Failed! "#contributor test! Ignoring pft:{}, compartment:{}, caltarget:{}, output:{}".format(pft, cmprt, ctname, ofname)
      else:
          raise RuntimeError(f"Unexpeceted dimensions for variable {ncname}")

    return final_data

  def ssrf_summary2csv(self, list_of_data):
    '''
    Transforms a list of dicts with output data into a csv.

    Parameters
    ==========
    list_of_data : list of dicts
      List of dicts as produced by ``summarize_ssrf(..)``. Keys should be
      cmt, ncname, ctname, modeled_value, target_value and pft and compartment
      when applicable

    Returns
    =======
    data : str, formatted csv file
      data will be a string that is a csv file with column names being output
      variable (with PFT and compartment if applicable) and data will be the 
      modeled value for that output. The csv will should have one header line
      and one data line.

    '''
    def colname(x):
      '''Builds column names using NetCDF name, PFT and compartment.'''
      cname = ''
      if 'pft' in x and 'cmprt' in x:
        cname = f"{x['ncname']}_pft{x['pft']}_{x['cmprt']}"
      elif 'pft' in x and 'cmprt' not in x:
        cname = f"{x['ncname']}_pft{x['pft']}"
      else:
        cname = f"{x['ncname']}"
      return cname

    final = {}
    for data in list_of_data:
      final[colname(data)] = data['modeled_value']
    d = pd.DataFrame([final])
    return d.to_csv(index=False)

  def ssrf_targets2csv(self, data, filename):
    '''
    Write a nicely formatted csv file with the target values. The column names
    are the NetCDF variable names with PFT and compartment if applicable. The
    calibration target names (names that are used for target values in the
    calibration_targets.py file) are included as a commented out line at the top
    of the file.

    Including the comment line with calibration target names precludes following
    the API pattern of the ssrf_summary2csv(..) function, so here rather than
    returing the csv string, we require a path name and we write data to the
    file.

    Writes file to ``filename``.

    Parameters
    ----------
    data : list of dicts
      Something like this:

      [ {'cmt': 'CMT06',
         'ncname': 'INGPP', 'ctname': 'GPPAllIgnoringNitrogen', 'pft': 0
         'modeled_value': 8.8399451693811, 'target_value': 11.833, }, ... ]

    Returns
    -------
    None
    '''

    def colname(x, vname):
      '''Builds column names using NetCDF name, PFT and compartment.'''
      assert  vname in ('ctname','ncname'), "Invalid parameter"
      col = ''
      if 'pft' in x and 'cmprt' in x:
        col = f"{x[vname]}_pft{x['pft']}_{x['cmprt']}"
      elif 'pft' in x and 'cmprt' not in x:
        col = f"{x[vname]}_pft{x['pft']}"
      else:
        col = f"{x[vname]}"
      return col  # e.g. INGPP_pft0 or GPPAllIgnoringNitrogen_pft0

    with open(filename, 'w') as f:

      # write the header line which uses the calibration targets names.
      header = ','.join([colname(d, 'ctname') for d in data])
      f.write('#' + header + '\n')

      # make the data dictionary keyed by the netcdf name.
      final = []
      row_dict = {}
      for d in data:
        row_dict[colname(d, 'ncname')] = d['target_value']   
      final.append(row_dict)

      d = pd.DataFrame(final).to_csv(f, index=False)

    return None


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
          data_y = util.output.average_monthly_pool_to_yearly(data_m)
        elif output['type'] == 'flux':
          data_y = util.output.sum_monthly_flux_to_yearly(data_m)

        # Not sure what is most meaningful here, so collapsing PFT dimension
        # into ecosystem totals...
        data_y_eco = util.output.sum_across_pfts(data_y)

        # TODO: Need to handle non-PFT outputs!
        ostr += '{:2.3f},'.format(data_y_eco[-1,self.PXy,self.PXx])

      ostr = ostr.rstrip(',') # remove trailing comma...
 
      with open(sensitivity_outfile, 'a') as f:
        f.write(pstr + ',' + ostr + '\n')

  def plot_sensitivity_matrix(self, save=False):
    '''
    Make a set of plots showing the properties of the sensitivity matrix. This
    plot allows you to check that the sampling strategy is producing a
    reasonable distribution of samples across the range. Usually you want to see
    that the whole range is sampled evenly between the bounds and that no
    samples are falling outside the bounds.

    Shows one row of plots for each parameter with 3 different ways of viewing
    the sample distributions:

       - Left column is sample values with bounds marked in red. 
       - Middle column is a histogram of sample values.
       - Right column is boxplot of sample values

    Parameters
    ----------
    save : bool
      True saves plot in ``work_dir`` with name
      ``sample_matrix_distributions.png``

    Returns
    -------
    None
    '''

    fig, axes = plt.subplots(len(self.params), 3, 
                             figsize=(10, 3*len(self.params)), squeeze=False)

    for i, (p, ax) in enumerate(zip(self.params, axes)):
      ax[0].plot(self.sample_matrix.iloc[:, i], marker='.', linewidth=0, alpha=.5)
      ax[0].plot(0, p['initial'], marker='o', color='orange', alpha=.5,)
      ax[0].set_ylabel(f"{p['name']}_{p['pftnum']}")
      ax[0].hlines(p['bounds'], 0, len(self.sample_matrix)-1, linestyles='dotted', colors='red')
      ax[1].hist(self.sample_matrix.iloc[:, i], range=sorted(p['bounds']), orientation='horizontal', alpha=0.75, rwidth=0.8)
      ax[2].boxplot(self.sample_matrix.iloc[:, i])
      ax[2].set_ylim(ax[0].get_ylim())
      
    plt.tight_layout()

    if save:
      savename = os.path.join(self.work_dir, "sample_matrix_distributions.png")
      print(f"Saving plot {savename}")
      plt.savefig(savename)

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
