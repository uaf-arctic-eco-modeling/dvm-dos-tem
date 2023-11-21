#! /usr/bin/env python

import os
import sys

class BaseDriver(object):

  def __init__(self, work_dir=None, clean=False, opt_run_setup=None):
    '''Create a BaseDriver object. General expectation is that you will
    instantiate specific classes that inherit from Base.'''

    # These are setup in this construction, but are declared here simply to 
    # keep the object definition more explicit.
    self._seedpath = None
    self.work_dir = None
    self.__initial_params_rundir = None

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
      self.__initial_params_rundir = os.path.join(self.work_dir, 'initial_params_run_dir')
    else:
      self.work_dir = None
      self.__initial_params_rundir = None

  def set_seed_path(self, path):
    self._seedpath = path

  def get_initial_params_dir(self):
    '''Read only accessor to private member variable.'''
    return self.__initial_params_rundir

