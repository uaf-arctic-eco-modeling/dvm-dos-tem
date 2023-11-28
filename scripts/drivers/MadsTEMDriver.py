#!/usr/bin/env python
import os
import yaml
import json
import subprocess
import shutil

import util.param as pu
import util.setup_working_directory
import util.runmask
import util.outspec
import util.output

from drivers.BaseDriver import BaseDriver

class MadsTEMDriver(BaseDriver):
  '''
  MadsTEMDriver class for controlling and running the driving the dvmdostem
  model from a Julia script with the Mads package.

  This class extends the functionality of the BaseDriver class and includes
  methods for setting up the run directory, updating parameters, running the
  model, and gathering model outputs.

  Parameters
  ----------
  config_dict : dict, optional
      A dictionary containing configuration parameters for the driver.

  **kwargs
      Additional keyword arguments to pass to the BaseDriver constructor.
  '''

  def __init__(self, config_dict=None, **kwargs):
    super().__init__(**kwargs)

    self.set_seed_path('/work/parameters')

    self.site = config_dict['site'] 
    self.work_dir = config_dict['work_dir']
    self.calib_mode = config_dict['calib_mode']
    self.opt_run_setup = config_dict['opt_run_setup']
    self.cmtnum = config_dict['cmtnum']
    self.pftnums = config_dict['pftnums']
    self.paramnames = config_dict['params']
    self.target_names = config_dict['target_names']

    # will present key error if config dict is missing keys!

  @classmethod
  def fromfilename(cls, filename):
    with open(filename, 'r') as config_data:
      config = yaml.safe_load(config_data)
    return cls(config)

  def set_params_from_seed(self):
    '''
    Sets up a list of dicts mapping parameter names to values....

    Assumes that various things have been setup:
      self.cmtnum, self.paramnames, self.pftnums, self._seedpath

    Analogous to ``Sensitivity.params_from_seed(...)`` but this one uses a
    different name in the dict ('vals' vs 'intial') and this is setup as a
    member function that modifies/updates a member variable (self.params)
    whereas in Sensitivity, it is a stand alone module function... Would be
    great to combine these...

    Migrated directly from TEM.py::set_params(...)

    This just makes an internal lookup structure...not sure what it is used for
    yet...
    '''
    assert len(self.paramnames) == len(self.pftnums), "params list and pftnums list must be same length!"

    self.params = []
    plu = pu.build_param_lookup(self._seedpath)

    for pname, pftnum in zip(self.paramnames, self.pftnums):
      original_pdata_file = pu.which_file(self._seedpath, pname, lookup_struct=plu)
      p_db = pu.get_CMT_datablock(original_pdata_file, self.cmtnum)
      p_dd = pu.cmtdatablock2dict(p_db)
      if pname in p_dd.keys():
        p_val = p_dd[pname]
      else:
        p_val = p_dd['pft{}'.format(pftnum)][pname]

      self.params.append(dict(name=pname, val=p_val, cmtnum=self.cmtnum, pftnum=pftnum))

    return None

  def setup_run_dir(self):

    # Make the working directory
    util.setup_working_directory.cmdline_entry([
      '--input-data-path', self.site, 
      self.work_dir
    ])

    # Adjust run mask for appropriate pixel
    util.runmask.cmdline_entry([
      '--reset',
      '--yx',self.PXy, self.PXx,
      '{}/run-mask.nc'.format(self.work_dir)
    ])

    # First clear the file incase the user has funky modifications in their repo's
    # copy of the template output spec file.
    # maybe a flag should be added to setup_working_directory.py that can
    # enforce starting with an empty outspec file...
    util.outspec.cmdline_entry([
      '{}/config/output_spec.csv'.format(self.work_dir),
      '--empty',
    ])

    # Next run thru the requested outputs toggling them on in the file.
    for output_spec in self.outputs:
      util.outspec.cmdline_entry([
        '{}/config/output_spec.csv'.format(self.work_dir),
        '--on', output_spec['ncname'], 
        output_spec['timeres'],
        output_spec['pftres'],
        output_spec['cpartres'],
        output_spec['layerres'],
      ])

    # Make sure CMTNUM output is on
    util.outspec.cmdline_entry([
      '{}/config/output_spec.csv'.format(self.work_dir),
      '--on','CMTNUM','y'
    ])

    # Adjust the config file
    CONFIG_FILE = os.path.join(self.work_dir, 'config/config.js')
    # Read the existing data into memory
    with open(CONFIG_FILE, 'r') as f:
      config = json.load(f)

    config['IO']['output_nc_eq'] = 1 # Modify value...

    # NOTE, TODO: 
    # The TEM.py file has an implementation that sets values in the 
    # calibration_directives.txt...this should be modified to use the
    # stuff recently added to the dvmdostem config file.
    # Need to turn dsl off, nfeed on depending on calib_mode
    # if doing GPPAllIgnoringNitrogen, then dsl off, nfeed off, 
    # othewise dsl on, nfeed on

    # Write it back..
    with open(CONFIG_FILE, 'w') as f:
      json.dump(config, f, indent=2)

  def update_params(self, vector, junk=None):
    '''
    Update the values in ``self.params`` with values in ``vector``.

    .. note::

      This does not actually update anything the run directory. See the other
      function for that. Maybe these functions should be combined? Is there
      ever a reason to update the internal data structure (self.params) without
      writing the data to the run directory?

    '''
    assert len(vector) == len(self.params)
    for i in range(len(vector)):
      self.params[i]['val'] = vector[i]

  def write_params2rundir(self):
    # Make sure that the parameters in the run dir are set to those we
    # have in our params table
    for param in self.params:
      pu.update_inplace(param['val'],
                        os.path.join(self.work_dir, 'parameters'),
                        param['name'],
                        param['cmtnum'],
                        param['pftnum'])
    return None

  def run(self):
    '''
    Run the model according to the setup.

    Assumes everything is setup in the self.work_dir

    Returns
    -------
    None
    '''
    program = '/work/dvmdostem'
    ctrl_file = os.path.join(self.work_dir, 'config','config.js')
    opt_str = f" -l err --force-cmt {self.cmtnum} --ctrl-file {ctrl_file}"
    cmdline = program + ' ' + self.opt_run_setup + opt_str
    completed_process = subprocess.run(
      cmdline,             # The program + options 
      shell=True,          # must be used if passing options as str and not list
      check=True,          # raise CalledProcessError on failure
      #capture_output=True,# collect stdout and stderr; causes memory problems I think
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
      cwd=self.work_dir)    # control context
    if not completed_process.returncode == 0:
      print(completed_process.stdout)
      print(completed_process.stderr)

    return None


  def run_wrapper(self, parameter_vector):
    '''
    Takes in a vector of parameters; used the parameters to run the model
    and returns a collection of outputs. Outputs are intended to be compared
    to target data. So if you have 5 targets you are comparing to, you should
    expect 5 output variables

    Set the parameters in the run directory based upon the values held in
    ``self.params``

    Run the model - using all the settings in the work_dir
    Collect the outputs
    '''
    self.update_params(parameter_vector)
    self.write_params2rundir()

    if os.path.exists(os.path.join(self.work_dir, 'output')):
      shutil.rmtree(os.path.join(self.work_dir, 'output'))

    self.run()

    return self.gather_model_outputs()


  def gather_model_outputs(self):
    cmtkey = f'CMT{self.cmtnum:02d}'
    ref_param_dir = os.path.join(self.work_dir, 'parameters')
    final_data = []
    for o in self.outputs:
      data, dims = util.output.get_last_n_eq(o['ncname'],
                                             'yearly',
                                             self.work_dir+'/output',
                                             n=10)

      dsizes, dnames = list(zip(*dims))
      if dnames == ('time','y','x'):
        pec = pu.percent_ecosys_contribution(cmtkey, o['ctname'], 
                                             ref_params_dir=ref_param_dir)
        truth = self.targets[o['ctname']]
        value = data[:,self.PXy,self.PXx].mean()

        d = dict(cmt=cmtkey, ctname=o['ctname'], value=value, truth=truth)
        final_data.append(d)

      elif dnames == ('time','y','x','pft'):
        for pft in range(0,10):
          if pu.is_ecosys_contributor(cmtkey, pft, ref_params_dir=ref_param_dir):
            pec = pu.percent_ecosys_contribution(cmtkey, o['ctname'], 
                                                 pftnum=pft, 
                                                 ref_params_dir=ref_param_dir)
            truth = self.targets[o['ctname']][pft]
            value = data[:,pft,self.PXy,self.PXx].mean()

            d = dict(cmt=cmtkey, ctname=o['ctname'],value=value,truth=truth,pft=pft)
            final_data.append(d)
          else:
              pass
            #print "  -> Failed" # contributor test! Ignoring pft:{}, caltarget:{}, output:{}".format(pft, ctname, ncname)

      elif dnames == ('time','y','x','pft','pftpart'):
        for pft in range(0,10):
          clu = {0:'Leaf', 1:'Stem', 2:'Root'}
          for cmprt in range(0,3):
            #print "analyzing... ctname {} (nc output: {}) for pft {} compartment {}".format(ctname, ncname, pft, cmprt),
            if pu.is_ecosys_contributor(cmtkey, pft, clu[cmprt], ref_params_dir=ref_param_dir):
              pec = pu.percent_ecosys_contribution(
                cmtkey, o['ctname'], pftnum=pft, compartment=clu[cmprt], ref_params_dir=ref_param_dir)
              truth = self.targets[o['ctname']][clu[cmprt]][pft]
              value = data[:,cmprt,pft,self.PXy,self.PXx].mean()

              d = dict(cmt=cmtkey, ctname=o['ctname'],value=value,truth=truth,pft=pft,cmprt=clu[cmprt])
              final_data.append(d)

            else:
              pass
              #print "  -> Failed! "#contributor test! Ignoring pft:{}, compartment:{}, caltarget:{}, output:{}".format(pft, cmprt, ctname, ofname)

      else:
        raise RuntimeError("SOMETHING IS WRONG?")

    return final_data



    # Now keep going in collecting stuff from 
    #        TEM.py::get_calibration_outputs()
    #







