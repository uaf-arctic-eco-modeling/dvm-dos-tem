#! /usr/bin/env python

import os
import sys

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

  def __init__(self, work_dir=None, clean=False, opt_run_setup=None):
    '''Create a BaseDriver object. General expectation is that you will
    instantiate specific classes that inherit from Base.'''

    # These are setup in this construction, but are declared here simply to 
    # keep the object definition more explicit.
    self._seedpath = None
    self.work_dir = None

    # This needs to be set by the client before targets and parameters can be
    # loaded...
    self.cmtnum = None

    # handles __initial_params_rundir as well
    self.set_work_dir(work_dir)

    self.site = '/work/demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10'
    self.PXx = 0
    self.PXy = 0
    self.outputs = [
      { 'name': 'GPP', 'type': 'flux',},
      { 'name': 'VEGC','type': 'pool',},
    ]
    self.opt_run_setup = opt_run_setup

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
    else:
      self.work_dir = None

  def set_seed_path(self, path):
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
    the targets for the CMTNUM of this SensitivityDriver object.

    Note: This function loads executable code from an arbitrary loction which is
    probably not ideal from a security standpoint. Maybe calibration_targets.py
    should be re-facotred into a data file and a set of target utilities similar
    to the parameters files.

    Parameters
    ==========
    ref_target_path : str (path)
      A path to a folder containing a calibration_targets.py file. 

    Modifies/Sets
    =============
    self.targets, self.targets_meta

    Returns
    =======
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