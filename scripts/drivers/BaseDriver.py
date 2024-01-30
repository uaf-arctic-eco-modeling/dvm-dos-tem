#! /usr/bin/env python

import os
import sys
import shutil
import yaml

def get_target_ncname(target, meta):
  '''
  Looks up the NetCDF output name based on the target name.

  Parameters
  ----------
  target : str
    The name of a target value that can be found in the calibration_targets.py
    file. This name should also be a key in the ``meta`` argument.

  meta : dict
    A dictionary of metadata describing calibration targets from the
    calibration_targets.py file. Must include a key for the ncname (NetCDF
    name).

  Returns
  -------
  '''
  ncname = None
  if 'ncname' in meta[target]:
    ncname = meta[target]['ncname']
  else:
    for cprt in 'Leaf Stem Root'.split(' '):
      ncname = meta[target][cprt]['ncname']
  return ncname

# Maybe these should be part of the calibration_targets.py...
def deduce_target_type(target, meta):
  '''
  Helper function to figure out wheter a target is a flux or a pool by
  inspecting the metadata for a target.

  TODO: Handle monthly or daily cases.

  Parameters
  ----------
  target : str
    The name of a target value that can be found in the calibration_targets.py
    file. This name should also be a key in the ``meta`` argument.

  meta : dict
    A dictionary of metadata describing calibration targets from the
    calibration_targets.py file.

  Returns
  -------
  type : str
    'flux' or 'pool'
  '''
  type = None
  units = None
  if 'units' in meta[target]:
     units = meta[target]['units']
  else:
    for cprt in 'Leaf Stem Root'.split(' '):
      units = meta[target][cprt]['units']

  if 'year' in units:
     type = 'flux'
  else:
     type = 'pool'

  return type

class BaseDriver(object):
  '''
  Base class for driver objects. Specific driver classes should inherit from
  BaseDriver. A driver object is intended to help with setting up and running
  the dvmdostem model in a variety of patterns. 
  '''

  def __init__(self, config=None, clean=False, **kwargs):
    '''
    Parameters
    ----------
    config : dict
      A dictionary of configuration values.
    **kwargs : additional key word arguments
      Valid keywords are:

    Keys for the config dict 
    ------------------------   
    seed_path : string 
      A path to the directory where initial parameters will be read from.
    work_dir : string
      A path to a location where run folders, outputs and other data will be
      stored.
    cmtnum : int
      Community Type number (CMT; land cover classification)
    PXx : int
      The pixel number to run from the input dataset. 
    PXy : int
      The pixel number to run from the input dataset.
    site : string
      The path to the input dataset.
    opt_run_setup : string
      Additional command line parameters that will be passed to dvmdostem
    outputs : list of dicts
      List of dicts that specify outputs to turn of for dvmdostem. Each should
      have the following keys: name, type. The name key is for the NetCDF output
      name, and type specified "flux" or "pool".
    '''
    # Default a bunch of stuff to None
    self._seedpath = None
    self.work_dir = None
    self.cmtnum = None
    self.PXx = None
    self.PXy = None
    self.site = None
    self.opt_run_setup = ''
    self.outputs = [
      { 'name': 'GPP', 'type': 'flux',},
      { 'name': 'VEGC','type': 'pool',},
    ]

    # Override if client has provided in the config...
    if 'seed_path' in config.keys():
      self._seedpath = config['seed_path']

    if 'work_dir' in config.keys():
      self.work_dir = config['work_dir']

    # NOTE: cmt must be set before targets and parameters can be loaded!
    if 'cmtnum' in config.keys():
      self.cmtnum = config['cmtnum']

    # handles __initial_params_rundir as well
    if 'work_dir' in config.keys():
      self.set_work_dir(config['work_dir'])

    if 'site' in config.keys():
      self.site = config['site']

    if 'PXx' in config.keys():
      self.PXx = config['PXx']

    if 'PXy' in config.keys():
      self.PXy = config['PXy']

    if 'outputs' in config.keys():
      self.outputs = config['outputs']

    if 'opt_run_setup' in config.keys():
      self.opt_run_setup = config['opt_run_setup']

    if self.work_dir is not None:
      if not os.path.isdir(self.work_dir):
        os.mkdir(self.work_dir)

    if clean and self.work_dir is not None:
      self.clean()

  @classmethod
  def fromfilename(cls, filename):
    '''
    Create an instance of BaseDriver from a configuration file.

    Parameters
    ----------
    filename : str
      The path to the configuration file.

    Returns
    -------
    BaseDriver
      An instance of BaseDriver initialized with parameters from the
      configuration file.
    '''
    with open(filename, 'r') as config_file:
      config = yaml.safe_load(config_file)
    return cls(config)

  def set_work_dir(self, path):
    '''
    Set the working directory for the object.

    Parameters
    ----------
    path : str
      The path to set as the working directory.
    '''
    if path:
      self.work_dir = path
    else:
      self.work_dir = None

  def set_seed_path(self, path):
    '''
    Set the seed path for the object. 

    Seed path is where the default parameter values for all the runs will be
    read from. Subsequent steps may modify select parameters for individual
    runs, but the original source values will be set from the seed path.

    .. note::

      Should changing the seed path force a clean? If the seed path is set or
      changed, this should probably trigger a re-build of all the working
      directories.... or warn the user...?

    Parameters
    ----------
    path : str
      The path to set as the seed path.
    '''
    self._seedpath = path

  def load_target_data(self, ref_target_path=None):
    '''
    Load a set of target values from a calibration_targets.py file. When the
    function is done, the targets will be available as a dictionary that is a
    data member of the Driver object. There will be an
    additional dict named ``targets_meta`` that has the metadata about the
    targets, for example the corresponding NetCDF name, the units, etc.

    Targets could also be referred to as "observations". I.e. data that was
    measured in the field and that model should be able to produce by
    simulation.

    This function reads the entire calibration_target.py file but extracts only
    the targets for the CMTNUM of this driver object.

    Note: This function loads executable code from an arbitrary loction which is
    probably not ideal from a security standpoint. Maybe calibration_targets.py
    should be re-facotred into a data file and a set of target utilities similar
    to the parameters files.

    Modifies/Sets: ``self.targets``, ``self.targets_meta``

    Parameters
    ----------
    ref_target_path : str (path)
      A path to a folder containing a calibration_targets.py file.

    Raises
    ------
    RuntimeError
      If cmtnum is not set or if there's a problem loading targets.

    Returns
    -------
    None
    '''
    if not self.cmtnum:
      raise RuntimeError("cmtnum must be set before you can load targets.")

    original_path = sys.path

    if not os.path.isfile(os.path.join(ref_target_path, 'calibration_targets.py')):
      raise RuntimeError(f"Can't find calibration_targets.py file in {ref_target_path}")

    sys.path = [ref_target_path]
    # loading the calibration targets into ct and save them into caltargets dict
    import calibration_targets as ct

    targets = ct.cmtbynumber(self.cmtnum)
    targets_meta = ct.calibration_targets['meta']

    if len(targets) != 1:
      raise RuntimeError(f'''Problem loading targets for {self.cmtnum}
                             from {ref_target_path}. Check file for duplicate 
                             or missing CMTs.''')

    del ct

    sys.path = original_path

    # targets is a dict keyed by the cmt verbose name, which is annoying,
    # so we remove that layer and have targets simply be the inner dict, which
    # is then keyed by target name, i.e. MossDeathC
    self.targets = targets[list(targets.keys())[0]]
    self.targets_meta = targets_meta

  def setup_outputs(self, target_names):
    '''
    Setup the driver's list of output specifications based on the target
    (observation) names.

    The client must have already loaded the targets, i.e.
    (``load_target_data(...)``) for this to work.

    The resulting ``BaseDriver.outputs`` is a list of dicts, each of which is an
    "output specification" which contains the information that will allow a
    mapping from the target names (as stored in calibration_targets.py) to the
    corresponding NetCDF output. Additional informations in the specification
    are the resolutions desired and a type signifier allowing us to
    differentiate between fluxes and pools, which is necessary for some summary
    statistics that may be calculated later.

    This list of output specifications will be used to setup the correct outputs
    in each sample specific run folder as well as conveniences like naming
    columns in output summary files.

    Sets/Modifies: ``self.outputs``

    Parameters
    ----------
    target_names : list of str
      The list should be strings naming targets in the calibration_targets.py
      file.

    Raises
    ------
    RuntimeError
      If a requested target is not found in targets dict.

    Returns
    -------
    None
    '''
    for t in target_names:
      if t not in self.targets:
        raise RuntimeError(f"Can't find requested target ({t}) in targets dict!")

    self.outputs = []
    for t in target_names:
      name = get_target_ncname(t, self.targets_meta)
      ctname = t
      t_type = deduce_target_type(t, self.targets_meta)
      timeres = 'y'
      pftres = 'p' if type(self.targets[t]) == list else ''
      cpartres = 'c' if type(self.targets[t]) == dict else ''
      layerres = '' # nothing is by layer...yet

      outspec = dict( ncname=name,
                      ctname=ctname,
                      type=t_type,
                      timeres=timeres,
                      pftres=pftres,
                      cpartres=cpartres,
                      layerres=layerres )

      self.outputs.append(outspec)

    return None

  def clean(self):
    '''
    Remove the entire tree at `self.work_dir`.

    This function is NOT CAREFUL, so be careful using it!
    '''
    shutil.rmtree(self.work_dir, ignore_errors=True)
    os.makedirs(self.work_dir)







