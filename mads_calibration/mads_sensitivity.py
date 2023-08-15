#!/usr/bin/env python
# Author Tobey Carman
# this version includes multiple pfts
# EJ 05/11/22

# uniform and lhc now part of sensitivity class
# self.params dict has all required info on pfts and cmts
# renamed cmtnum get_cmtnum
# removed pftnum (do need them) 
# self.params includes pftnum and cmtnum
# info modified to display multiple pfts
# removed all plotting functions from here

import sys,os
sys.path.append(os.path.join('/work','scripts'))

import pathlib
import numpy as np
import netCDF4 as nc
import pandas as pd
import multiprocessing
import textwrap
from scipy.stats import loguniform

import lhsmdu
import yaml
import glob
import json
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

class SensitivityDriver(object):
  '''
  Sensitivity Analysis Driver class.

  Driver class for conducting dvmdostem SensitivityAnalysis.
  Methods for cleaning, setup, running model, collecting outputs.

  Basic overview of use is like this:
   1. Instantiate driver object.
   2. Setup/design the experiment (parameters, to use, 
      number of samples, etc)
   3. Use driver object to setup the run folders.
   4. Use driver object to carry out model runs.
   5. Use driver object to summarize/collect outputs.
   6. Use driver object to make plots, do analysis.

  Parameters
  ----------

  See Also
  --------

  Examples
  --------
  Instantiate object, sets pixel, outputs, working directory, 
  site selection (input data path)
  >>> driver = SensitivityDriver()
  >>> driver.work_dir = '/tmp/tests-Sensitivity'

  Show info about the driver object:
  >>> driver.design_experiment(5, 4, params=['cmax','rhq10','nfall(1)'], pftnums=[2,None,2])
  >>> driver.sample_matrix
          cmax     rhq10  nfall(1)
  0  63.536594  1.919504  0.000162
  1  62.528847  2.161819  0.000159
  2  67.606747  1.834203  0.000145
  3  59.671967  2.042034  0.000171
  4  57.711999  1.968631  0.000155
  >>> driver.generate_uniform(3)
  >>> driver.generate_lhc(3)

  '''
  def __init__(self, work_dir=None, sampling_method=None, clean=False, config_file=[]):
    '''
    Constructor
    Hard code a bunch of stuff for now...

    Parameters
    ----------
    work_dir : 

    clean : bool
      CAREFUL! - this will forecfully remove the entrire tree rooted at `work_dir`.
    '''

    # Made this one private because I don't want it to get confused with 
    # the later params directories that will be created in each run folder.

    if config_file==[]:
       print('provide yaml config file')
       return
    else:
        with open(config_file, 'r') as config_data:
            config = yaml.safe_load(config_data)
        self.site = config['site'] 
        self.work_dir = config['work_dir']
        self.calib_mode = config['calib_mode']
        self.opt_run_setup = config['opt_run_setup']
        self.cmtnum = config['cmtnum']
        self.pftnums = config['pftnums']
        self.paramnames = config['params']
        self.target_names = config['target_names']
        
    self.__initial_params = '/work/parameters'

    #self.work_dir = work_dir 
    #self.site = '/data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_CALM_Toolik_LTER_10x10/'
    self.PXx = 1
    self.PXy = 0
    self.outputs = [
      { 'name': 'GPP', 'type': 'flux',},
      { 'name': 'VEGC','type': 'pool',},
    ]
    #self.pftnums={}
    #self.cmtnum={}
    #self.opt_run_setup = '-p 5 -e 5 -s 5 -t 5 -n 5'
    #self.opt_run_setup = '--pr-yrs 100 --eq-yrs 200 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0'
    self.params = {}
    self.sampling_method = sampling_method
    #self.calib_mode = 'GPPAllIgnoringNitrogen'
    self.caltarget_to_ncname_map = [
        ('GPPAllIgnoringNitrogen','INGPP'),
        ('NPPAllIgnoringNitrogen','INNPP'),
        #('GPPAll','GPP'),
        #('RHAll','RH'),
        #('Litter','LTRFALC'),
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
    self.final_data = []

    if self.work_dir is not None:
      if not os.path.isdir(self.work_dir):
        os.mkdir(self.work_dir)

    if clean and work_dir is not None:
      self.clean()

  def get_initial_params_dir(self):
    '''Read only accessor to private member variable.'''
    return self.__initial_params

  def generate_uniform(self, N, seed=''):
    '''
    Generate sample matrix using uniform method.

    Sample matrix will have one row for each "sample" of the
    parameters. There will be one column for each parameter in
    the `param_props` list.

    Parameters
    ----------
    N : int
      number of samples (rows) to create

    params : list of dicts
      Each item in `param_props` list will be a dictionary
      with at least the following:
      >>> params = {
      ...   'name': 'rhq10',        # name in dvmdostem parameter file (cmt_*.txt)
      ...   'bounds': [5.2, 6.4],   # the min and max values the parameter can have
      ... }

    Returns
    -------
    sample_matrix : pandas.DataFrame, shape (N, len(params))
      There will be one column for each parameter in the
      `param_props` list and N rows (samples).
    '''
    #print(param_props)
    if seed!='':
      np.random.seed(seed)
    self.sampling_method = 'uniform'
    l = np.random.uniform(size=(N, len(self.params)))

    # Generate bounds, based on specification in params list
    lows = np.array([p['bounds'][0] for p in self.params])
    highs = np.array([p['bounds'][1] for p in self.params])

    # Figure out the spread, or difference between bounds
    spreads = highs - lows

    sm = l * spreads + lows
    
    self.sample_matrix = pd.DataFrame(sm, columns=[p['name'] for p in self.params])
    
  def generate_loguniform(self, N):
    '''
    Generate sample matrix using log-uniform method.

    Sample matrix will have one row for each "sample" of the
    parameters. There will be one column for each parameter in
    the `param_props` list.

    Parameters
    ----------
    N : int
      number of samples (rows) to create

    params : list of dicts
      Each item in `param_props` list will be a dictionary
      with at least the following:
      >>> params = {
      ...   'name': 'kdcsomcr',               # name in dvmdostem parameter file (cmt_*.txt)
      ...   'bounds': [1e-5, 1e-10],     # the min and max values the parameter can have
      ... }

    Returns
    -------
    sample_matrix : pandas.DataFrame, shape (N, len(params))
      There will be one column for each parameter in the
      `param_props` list and N rows (samples).
    '''
    self.sampling_method = 'loguniform'
    loguniform_samples = np.transpose(np.array([loguniform.rvs(p['bounds'][0],p['bounds'][1],size=N) for p in self.params]))
    
    print(loguniform_samples)
    print(np.shape(loguniform_samples))

    self.sample_matrix = pd.DataFrame(loguniform_samples, columns=[p['name'] for p in self.params])

  def generate_lhc(self, N):
    '''
    Generate sample matrix using Latin Hyper Cube method.

    Sample matrix will have one row for each "sample" of the
    parameters. There will be one column for each parameter in
    the `param_props` list.

    Parameters
    ----------
    N : int
      number of samples (rows) to create

    params : list of dicts
      Each item in `param_props` list will be a dictionary
      with at least the following:
      >>> params = {
      ...   'name': 'cmax',               # name in dvmdostem parameter file (cmt_*.txt)
      ...   'bounds': [100.1, 105.1],     # the min and max values the parameter can have
      ... }

    Returns
    -------
    sample_matrix : pandas.DataFrame, shape (N, len(params))
      There will be one column for each parameter in the
      `param_props` list and N rows (samples).
    '''

    self.sampling_method = 'lhc'
    # Generate bounds, based on specification in params list
    lo_bounds = np.array([p['bounds'][0] for p in self.params])
    hi_bounds = np.array([p['bounds'][1] for p in self.params])

    # Figure out the spread, or difference between bounds
    spreads = hi_bounds - lo_bounds

    # create M by N sampling matrix
    l = lhsmdu.sample(len(self.params), N)
    
    # transpose the matrix
    l = lhsmdu.resample().T

    # ??
    mat_diff = np.diag(spreads)

    # ??
    sample_matrix = l * mat_diff + lo_bounds

    self.sample_matrix = pd.DataFrame(sample_matrix, columns=[p['name'] for p in self.params])

  def design_experiment(self, Nsamples, cmtnum, params, pftnums, 
      percent_diffs=None, sampling_method='lhc'):
    '''
    Builds bounds based on initial values found in dvmdostem parameter 
    files (cmt_*.txt files) and the `percent_diffs` array. 
    The `percent_diffs` array gets used to figure out how far
    the bounds should be from the initial value. Defaults to initial 
    value +/-10%.

    Sets instance values for `self.params` and `self.sample_matrix`.

    Parameters
    ----------
    Nsamples : int
      How many samples to draw. One sample equates to one run to be done with 
      the parameter values in the sample.
    
    cmtnum : int
      Which community type number to use for initial parameter values, for
      doing runs and analyzing outputs.
    
    params : list of strings
      List of parameter names to use in the experiment. Each name must be
      in one of the dvmdostem parameter files (cmt_*.txt).
    
    pftnums : list of ints
      List of PFT numbers, one number for each parameter in `params`. Use
      `None` in the list for any non-pft parameter (i.e. a soil parameter).
    
    percent_diffs : list of floats
      List values, one for each parameter in `params`. The value is used to
      the bounds with respect to the intial parameter value. I.e. passing
      a value in the percent_diff array of .3 would mean that bounds should
      be +/-30% of the initial value of the parameter.
    
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

    assert len(params) == len(pftnums), "params list and pftnums list must be same length!"
    assert len(params) == len(percent_diffs), "params list and percent_diffs list must be same length"

    self.params = []
    plu = pu.build_param_lookup(self.__initial_params)

    for pname, pftnum, perturbation in zip(params, pftnums, percent_diffs):
      original_pdata_file = pu.which_file(self.__initial_params, pname, lookup_struct=plu)

      p_db = pu.get_CMT_datablock(original_pdata_file, cmtnum)
      p_dd = pu.cmtdatablock2dict(p_db)

      if pname in p_dd.keys():
        p_initial = p_dd[pname]
      else:
        p_initial = p_dd['pft{}'.format(pftnum)][pname]

      p_bounds = [p_initial - (p_initial*perturbation), p_initial + (p_initial*perturbation)]

      self.params.append(dict(name=pname, bounds=p_bounds, initial=p_initial, cmtnum=cmtnum, pftnum=pftnum))

    if self.sampling_method == 'lhc':
      self.generate_lhc(Nsamples)
    elif sampling_method == 'uniform':
      self.generate_uniform(Nsamples)
    elif sampling_method == 'loguniform':
      self.generate_loguniform(Nsamples)

  def save_experiment(self, name=''):
    '''Write the parameter properties and sensitivity matrix to files.'''
    if self.work_dir!='':
        if name == '':
          sm_fname = os.path.join(self.work_dir, 'sample_matrix.csv')
          pp_fname = os.path.join(self.work_dir, 'param_props.csv')
          info_fname = os.path.join(self.work_dir, 'info.txt')
        else:
          sm_fname = os.path.join(self.work_dir,'{}_sample_matrix.csv'.format(name)) 
          pp_fname = os.path.join(self.work_dir,'{}_param_props.csv'.format(name))
          info_fname = os.path.join(self.work_dir,'{}_info.txt'.format(name))

    for p in [sm_fname, pp_fname, info_fname]:
      if not os.path.exists(os.path.dirname(p)):
        pathlib.Path(os.path.dirname(p)).mkdir(parents=True, exist_ok=True)

    self.sample_matrix.to_csv(sm_fname, index=False)
    pd.DataFrame(self.params).to_csv(pp_fname, index=False)
    with open(info_fname, 'w') as f:
      f.write("sampling_method: {}".format(self.sampling_method))

  def save_results(self, name=''):
    [Nsample,Nparam]=self.sample_matrix.shape
    sample_specific_folder = self._ssrf_name(0)
    OUT_FILE = os.path.join(sample_specific_folder, 'output.txt')
    df_out=pd.read_csv(OUT_FILE, header=None)
   
    for i in range(1,Nsample):
      sample_specific_folder = self._ssrf_name(i)
      print(sample_specific_folder)
      OUT_FILE = os.path.join(sample_specific_folder, 'output.txt')
      df = pd.read_csv(OUT_FILE, header=None)
      df_out=pd.concat([df_out,df],axis=0)
                    
    targets=self.get_targets(cdir=sample_specific_folder,targets=True)
    df = pd.DataFrame(targets).T
    df_out=pd.concat([df_out,df],axis=0)
    df_out=df_out.reset_index(drop=True)
    out_file=os.path.join(self.work_dir, 'results.csv')
    df_out.to_csv(out_file, header=False, index=False)
    return 

  def load_experiment(self, param_props_path, sample_matrix_path, info_path):
    '''Load parameter properties and sample matrix from files.'''

    with open(info_path) as f:
      data = f.readlines()

    for l in data:
      if 'sampling_method' in l:
        self.sampling_method = l.split(':')[1].strip()

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
    pft_verbose_name=[]
    try:
        pftnums=set([p['pftnum'] for p in self.params])
        pftnums.discard(None)
        for pft in pftnums:
            pft_verbose_name.append( pu.get_pft_verbose_name(
            cmtnum=self.params[0]['cmtnum'], pftnum=pft, 
            lookup_path=self.get_initial_params_dir()
            ))
    except (AttributeError, ValueError) as e:
      pft_verbose_name = ''

    # Not all class attributes might be initialized, so if an 
    # attribute is not set, then print empty string.
    try:
      # DataFrame prints nicely
      df = pd.DataFrame(self.params)
      # prevents printing nan
      # Might want to make this more specific to PFT column, 
      # in case there somehow ends up being bad data in one of the 
      # number columns that buggers things farther along?
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
      work_dir: {}
      site: {}
      pixel(y,x): ({},{})
      cmtnum: {}
      pftnum: {} ({})
      sampling_method: {}

      '''.format(
        self.work_dir, self.site, self.PXy, self.PXx, self.get_cmtnum(),
        pftnums, pft_verbose_name, self.sampling_method))

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

  def core_setup(self, row, idx, initial=False, calib=False):
    '''
    Do all the work to setup and configure a model run.
    Uses the `row` parameter (one row of the sample matrix) to
    set the parameter values for the run.

    Currently relies on command line API for various dvmdostem
    helper scripts. Would be nice to transition to using a Python
    API for all these helper scripts (modules).

    Parameters
    ----------
    row : dict
      One row of the sample matrix, in dict form. So like this:
        `{'cmax': 108.2, 'rhq10': 34.24}`
      with one key for each parameter name.

    idx : int
      The row index of the `sample_matrix` being worked on. Gets
      used to set the run specific folder name, i.e. sample_000001.

    Returns
    -------
    None
    '''
    #print("PROC:{}  ".format(multiprocessing.current_process()), row)

    if initial:
      #print("Ignoring idx, it is not really relevant here.")
      #print("Ignoring row dict, not really relevant here.")
      # Build our own row dict, based on initial values in params
      row = {x['name']:x['initial'] for x in self.params}
      sample_specific_folder = os.path.join(self.work_dir, 'initial_value_run')
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
      '--yx',str(self.PXy), str(self.PXx),
      '{}/run-mask.nc'.format(sample_specific_folder)
    ])

    # Enable outputs as specified
    if not(initial) and calib:
        program = '/work/scripts/outspec_utils.py'
        opt_str = '--enable-cal-vars {}/config/output_spec.csv --on CMTNUM y'.format(sample_specific_folder)
        cmdline = program + ' ' + opt_str
        with log_wrapper(cmdline, tag='setup') as lw:
            comp_proc = subprocess.run(cmdline, shell=True, check=True)
#       outspec_utils.cmdline_entry([
#        '--enable-cal-vars {}/config/output_spec.csv'.format(sample_specific_folder),
#        '--on','CMTNUM','y'
#        ])
#       outspec_utils.cmdline_entry([
#'--enable-cal-vars {}/config/output_spec.csv --on CMTNUM y'.format(sample_specific_folder)
#])
    else:
        for output_spec in self.outputs:
            if output_spec['type']=='layer':
                outspec_utils.cmdline_entry([
                '{}/config/output_spec.csv'.format(sample_specific_folder),
                '--on', output_spec['name'], 'month', 'layer' 
                ])
            else:
                outspec_utils.cmdline_entry([
                '{}/config/output_spec.csv'.format(sample_specific_folder),
                '--on', output_spec['name'], 'month', 'pft'
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

    if calib:
        config['calibration-IO']['caldata_tree_loc']=sample_specific_folder
        
        CALIB_FILE = os.path.join(sample_specific_folder, 'config/calibration_directives.txt')
        with open(CALIB_FILE, 'r') as file:
            data = file.readlines()

        if self.calib_mode == 'GPPAllIgnoringNitrogen':
            data[8] = '    "1": ["dsl off", "nfeed off"]\n'
            
        with open(CALIB_FILE, 'w') as file:
            file.writelines(data)

    # Write it back..
    with open(CONFIG_FILE, 'w') as f:
      json.dump(config, f, indent=2)

    # modify parameters according to sample_matrix (param values)
    # and the  param_spec (cmtnum, pftnum)
    # Iterating over sample_matrix, which is a pandas.DataFrame, we use
    # itertuples() which coughs up a named tuple. So here we get the
    # name, and the sample value out of the named tuple for use in 
    # calling param_utils update function.
    if initial:
      for pname, pval in row.items():
        #for pname, pval in zip(row._fields[1:], row[1:]):
        pdict = list(filter(lambda x: x['name'] == pname, self.params))[0]
        pu.update_inplace(
            pval, os.path.join(sample_specific_folder, 'parameters'), 
            pname, pdict['cmtnum'], pdict['pftnum']
        )
    else:
      for pval,j in zip(row,range(len(row))):
        pu.update_inplace(
            pval, os.path.join(sample_specific_folder, 'parameters'), 
            self.params[j]['name'],
            self.params[j]['cmtnum'],
            self.params[j]['pftnum']
        )

  def setup_multi(self, force=False, calib=False):
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
    #args = zip(self.sample_matrix.values,range(0,len(self.sample_matrix)))
    n = len(self.sample_matrix) 
    args = list(zip(self.sample_matrix.values,
           range(0,n), 
           np.zeros(n, dtype=bool)))
    if calib:
        args = list(zip(self.sample_matrix.values,
           range(0,n), 
           np.zeros(n, dtype=bool),
           np.ones(n, dtype=bool)))
    print('args',args)
    with multiprocessing.Pool(processes=(os.cpu_count()-1)) as pool:
      results = pool.starmap(self.core_setup, args)

  def get_cmtnum(self):
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
    if self.params:
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
    else:
      print('parameters not assigned!')

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
    #opt_str = ' -l err --force-cmt {} --ctrl-file {}'.format(self.get_cmtnum(), ctrl_file)
    opt_str = ' -l fatal --force-cmt {} --ctrl-file {}'.format(self.get_cmtnum(), ctrl_file)
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
    out=self.get_targets(cdir=rundirectory)
    print('out',out)
    out_file = os.path.join(rundirectory,'output.txt')
    df = pd.DataFrame(out).T
    df.to_csv(out_file, header=False, index=False)
    #with open(out_file, "w") as output:
    #    output.write(str(out))
  
    return 

  def get_targets(self,cdir,targets=False):
    # targets=False grab model outputs
    # targets=True grab model observations
    # fill the final_data list using targets from 
    # calibration/calibration_targets.py
    self.get_calibration_outputs(cdir)
    # organize the ouput in the form of the dictionary 
    # generates the flat list only for given target_names 
    print ('Output variables:')
    print ('Observations [True-ON], Modeled [False-OFF ]:',targets)
    d=dict()
    if len(self.target_names)>1:
        for icase in self.target_names: #zip(ikeys,icase):
            print (icase)
            vals=[]
            for item in self.final_data:
                if item['ctname']==icase:
                    if targets:
                        vals.append(item['truth'])
                    else:
                        vals.append(item['value'])
            d[icase]= vals
    elif len(self.target_names)==1:
        icase=self.target_names[0]
        vals=[]
        for item in self.final_data:
            if item['ctname']==icase:
                if targets:
                    vals.append(item['truth'])
                else:
                    vals.append(item['value'])
        d[icase]= vals
    else:
        print('ERROR: The target_names list is empty')

    out_list = [d[item] for item in d.keys()]
    out_flat = [item for sublist in out_list for item in sublist]
    
    return out_flat

  def get_calibration_outputs(self,cdir):

    output_directory_path=cdir+"/output"
    ref_param_dir=cdir+"/parameters"
    ref_targets={}
    ref_targets_dir="/work"
    # averaging over last 10 year of the run
    last_N_yrs = 10
    
    nc_file=os.path.join(output_directory_path, 'CMTNUM_yearly_eq.nc')
    # check if CMTNUM_yearly_eq.nc exists
    if not(os.path.exists(nc_file)):
        return ''

    with nc.Dataset(nc_file, 'r') as ds:
        data = ds.variables['CMTNUM'][-last_N_yrs:,self.PXy,self.PXx]

    assert(data.min() == data.max()) # should be the same CMT for the whole time frame
    cmtkey = 'CMT{:02d}'.format(data[0])
    print('cmtkey',cmtkey)

    old_path = sys.path
    #print(old_path)
    sys.path = [os.path.join(ref_targets_dir, 'calibration')]
    print("Loading calibration_targets from : {}".format(sys.path))
    # loading the calibration targets into ct and save them into caltargets dict
    import calibration_targets as ct
    caltargets = {}
    for k, v in ct.calibration_targets.items():
        if k == 'meta' and 'cmtnumber' not in v.keys():
            pass # no need for the meta data here...
        elif 'cmtnumber' in v.keys():
            cmtid = "CMT{:02d}".format(v['cmtnumber'])
            caltargets[cmtid] = v
        else:
            print("Warning: something is wrong with target block {}".format(k))

    del ct
    print("Resetting path...")
    
    sys.path = old_path
    ref_targets = caltargets
    self.final_data = []
    #load the correspoding nc file into the data variable
    #save the targets from calibration_target and nc files into final_data dict list
    for ctname, ncname in self.caltarget_to_ncname_map:

        data, dims = ou.get_last_n_eq(ncname, 'yearly', output_directory_path, n=last_N_yrs)
        dsizes, dnames = list(zip(*dims))

        #print(ctname, output_directory_path, ncname, dims, dnames, dsizes)
        if dnames == ('time','y','x'):
            pec = pu.percent_ecosys_contribution(cmtkey, ctname, ref_params_dir=ref_param_dir)
            truth = ref_targets[cmtkey][ctname]
            value = data[:,self.PXy,self.PXx].mean()

            d = dict(cmt=cmtkey, ctname=ctname,value=value,truth=truth)
            self.final_data.append(d)

        elif dnames == ('time','y','x','pft'):
            for pft in range(0,10):
                if pu.is_ecosys_contributor(cmtkey, pft, ref_params_dir=ref_param_dir):
                    pec = pu.percent_ecosys_contribution(cmtkey, ctname, pftnum=pft, ref_params_dir=ref_param_dir)
                    truth = ref_targets[cmtkey][ctname][pft]
                    value = data[:,pft,self.PXy,self.PXx].mean()
                    d = dict(cmt=cmtkey, ctname=ctname,value=value,truth=truth,pft=pft)
                    self.final_data.append(d)
                else:
                    pass
                    #print "  -> Failed" # contributor test! Ignoring pft:{}, caltarget:{}, output:{}".format(pft, ctname, ncname)

        elif dnames == ('time','y','x','pft','pftpart'):
            for pft in range(0,10):
                clu = {0:'Leaf', 1:'Stem', 2:'Root'}
                for cmprt in range(0,3):
                    #print "analyzing... ctname {} (nc output: {}) for pft {} compartment {}".format(ctname, ncname, pft, cmprt),
                    if pu.is_ecosys_contributor(cmtkey, pft, clu[cmprt], ref_params_dir=ref_param_dir):
                        pec = pu.percent_ecosys_contribution(cmtkey, ctname, pftnum=pft, compartment=clu[cmprt], ref_params_dir=ref_param_dir)
                        truth = ref_targets[cmtkey][ctname][clu[cmprt]][pft]
                        value = data[:,cmprt,pft,self.PXy,self.PXx].mean()
                        d = dict(cmt=cmtkey, ctname=ctname,value=value,truth=truth,pft=pft)
                        self.final_data.append(d)
                    else:
                        pass
                    #print "  -> Failed! "#contributor test! Ignoring pft:{}, compartment:{}, caltarget:{}, output:{}".format(pft, cmprt, ctname, ofname)
        else:
            raise RuntimeError("SOMETHING IS WRONG?")

    return

  def extract_data_for_sensitivity_analysis(self, posthoc=True, multi=True):
    '''
    Creates a csv file in each run directory that summarizes
    the run's parameters and outut. The csv file will look 
    something like this:

    p_cmax,  p_rhq10,   p_micbnup,   o_GPP,  o_VEGC
    1.215,   2.108,     0.432,       0.533,  5.112

    with one columns for each parameter and one column for 
    each output. The

    For each row in the sensitivity matrix (and corresponding 
    run folder), 
      For each variable specified in self.outputs:
          - opens the NetCDF files that were output from
            dvmdostem
          - grabs the last datapoint
          - writes it to the sensitivity.csv file

    

    Parameters
    ----------
    posthoc : bool (Not implemented yet)
      Flag for controlling whether this step should be run after the
      model run or as part of the model run
    
    multi : bool (Not impolemented yet)
      Flag for if the runs are done all in one directory or each in 
      its own directory. If all runs are done in one directory
      then paralleization is harder and this step of collating the
      output data must be done at the end of the run before the next run
      overwrites it.
      

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

