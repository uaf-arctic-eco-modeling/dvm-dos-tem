import sys,os
sys.path.append(os.path.join('/work','scripts'))

#import os
#os.chdir('/work/scripts')
#import os.path

# -*- coding: utf-8 -*-
import yaml
import numpy as np                         # For the time array
from scipy.integrate import odeint         # To integrate our equation
import math
import json
import subprocess
import sys
import netCDF4 as nc
import output_utils as ou
import param_util as pu
import shutil
from contextlib import contextmanager

import pandas as pd
import datetime 
# Required libraries for authentication
import netCDF4 as nc
import matplotlib.pyplot as plt

from pathlib import Path
import setup_working_directory
import importlib
runmask_util = importlib.import_module("runmask-util")
import outspec_utils

@contextmanager
def log_wrapper(message,tag=''):
    '''
    Likely will abandon or repurpose this function.
    Not super helpful as a log printer.
    '''
    print('[AC:{}] {}'.format(tag, message))
    try:
        yield
    finally:
        print()

class TEM_model:
    
    def __init__(self,config_file=[]):
        
        if config_file==[]:
            self.site = '/data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_CALM_Toolik_LTER_10x10/'
            self.work_dir = '/data/workflows/single_run' 
            self.calib_mode=''
            self.opt_run_setup = '-p 5 -e 5 -s 5 -t 5 -n 5'
            self.cmtnum={}
            self.pftnums={}
            self.paramnames = {}
            self.target_names = ['GPPAllIgnoringNitrogen']
            
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
        
        self.caltarget_to_ncname_map = [
        ('GPPAllIgnoringNitrogen','INGPP'),
        ('NPPAllIgnoringNitrogen','INNPP'),
        #('GPPAll','GPP'),
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
        self.params = {}
        self.param_dir = '/work/parameters'
        self.sampling_method = ''
        self.PXx = 0
        self.PXy = 0
        self.outputs = [
          { 'name': 'GPP', 'type': 'flux',},
          { 'name': 'VEGC','type': 'pool',},
        ]

    def set_params(self, cmtnum, params, pftnums):

        assert len(params) == len(pftnums), "params list and pftnums list must be same length!"

        self.params = []
        plu = pu.build_param_lookup(self.param_dir)
        
        for pname, pftnum in zip(params, pftnums):
            original_pdata_file = pu.which_file(self.param_dir, pname, lookup_struct=plu)
            p_db = pu.get_CMT_datablock(original_pdata_file, cmtnum)
            p_dd = pu.cmtdatablock2dict(p_db)
            if pname in p_dd.keys():
                p_val = p_dd[pname]
            else:
                p_val = p_dd['pft{}'.format(pftnum)][pname]

            self.params.append(dict(name=pname, val=p_val, cmtnum=cmtnum, pftnum=pftnum))

        return
    
    def setup(self,calib=False):
        # this will create work_dir and copy all required files in there
                
        DA_specific_folder = self.work_dir
        program = '/work/scripts/setup_working_directory.py'
        opt_str = '--input-data-path {} {}'.format(self.site, DA_specific_folder)
        cmdline = program + ' ' + opt_str

        with log_wrapper(cmdline, tag='setup') as lw:
            comp_proc = subprocess.run(cmdline, shell=True, 
                                       check=True, 
                                       stdout=subprocess.DEVNULL, 
                                       stderr=subprocess.STDOUT)

        program = '/work/scripts/runmask-util.py'
        opt_str = '--reset --yx {} {} {}/run-mask.nc'.format(self.PXy, self.PXx, DA_specific_folder)
        cmdline = program + ' ' + opt_str 
        with log_wrapper(cmdline, tag='setup') as lw:
            comp_proc = subprocess.run(cmdline, shell=True, check=True)

        for output_spec in self.outputs:
            program = '/work/scripts/outspec_utils.py'
            #Elchin added layer component 
            if output_spec['type']=='layer':
                opt_str = '{}/config/output_spec.csv --on {} m p l'.format(DA_specific_folder, output_spec['name'])
            else:
                opt_str = '{}/config/output_spec.csv --on {} m p'.format(DA_specific_folder, output_spec['name'])
            cmdline = program + ' ' + opt_str
            with log_wrapper(cmdline, tag='setup') as lw:
                comp_proc = subprocess.run(cmdline, shell=True, check=True)

        program = '/work/scripts/outspec_utils.py'
        opt_str = '{}/config/output_spec.csv --on CMTNUM y'.format(DA_specific_folder)
        if calib:
            opt_str = '--enable-cal-vars {}/config/output_spec.csv --on CMTNUM y'.format(DA_specific_folder)
        cmdline = program + ' ' + opt_str
        with log_wrapper(cmdline, tag='setup') as lw:
            comp_proc = subprocess.run(cmdline, shell=True, check=True)

        CONFIG_FILE = os.path.join(DA_specific_folder, 'config/config.js')
        # Read the existing data into memory
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        config['IO']['output_nc_eq'] = 1 # Modify value...
        if calib:
            config['calibration-IO']['caldata_tree_loc']=self.work_dir
            
            CALIB_FILE = os.path.join(self.work_dir, 'config/calibration_directives.txt')
            with open(CALIB_FILE, 'r') as file:
                data = file.readlines()

            if self.calib_mode == 'GPPAllIgnoringNitrogen':
                data[8] = '    "1": ["dsl off", "nfeed off"]\n'
            elif self.calib_mode == 'NPPAll':
                data[8] = '    "1": ["dsl on", "nfeed on"]\n'
            elif self.calib_mode == 'VEGC':
                data[8] = '    "1": ["dsl on", "nfeed on"]\n'
                
            with open(CALIB_FILE, 'w') as file:
                file.writelines(data)

        # Write it back..
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        #this could be separated from the setup like update_params
        for j in range(len(self.params)):
            pu.update_inplace(
              self.params[j]['val'], 
              os.path.join(DA_specific_folder, 'parameters'), 
              self.params[j]['name'],
              self.params[j]['cmtnum'],
              self.params[j]['pftnum']
            )
        return

    def update_params(self):
        for j in range(len(self.params)):
            pu.update_inplace(
              self.params[j]['val'], 
              os.path.join(self.work_dir, 'parameters'), 
              self.params[j]['name'],
              self.params[j]['cmtnum'],
              self.params[j]['pftnum']
            )
        return
    
    def get_cmtnum(self):
        '''
        I don't think that we need this anymore
        Tobey please check

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
        
        return

    def run(self,calib=False):
        #Check if /work/scripts/test_runs/config/output_spec.csv there
        spec_file=os.path.join(self.work_dir, 'config','output_spec.csv')
        self.checkifexists(spec_file)
        
        program = '/work/dvmdostem'
        ctrl_file = os.path.join(self.work_dir, 'config','config.js')
        opt_str = ' -l fatal --force-cmt {} --ctrl-file {}'.format(self.get_cmtnum(), ctrl_file)
        if calib:
            opt_str = ' --cal-mode --log-level err --ctrl-file {}'.format(ctrl_file)
        cmdline = program + ' ' + self.opt_run_setup + opt_str
        
        self.checkifexists(ctrl_file)

        with log_wrapper(cmdline, tag='run') as lw:
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
        return

    def checkifexists(self,filename):
        my_file = Path(filename)            
        try:
            with open(my_file) as f:
                print(my_file, "File present!")
        except FileNotFoundError:
            print(my_file, 'File is not present...........')    

        
    def clean(self):
        '''
        Remove the entire tree at `self.work_dir`.
        This function is careful, so be careful using it!
        '''
        shutil.rmtree(self.work_dir, ignore_errors=True)
        return
    

    def run_TEM(self,x):
    
        for j in range(len(self.params)):
            self.params[j]['val']=x[j]   
        # update param files
        self.clean()
        self.setup(calib=True)
        self.update_params()
        self.run()

        return self.get_targets()

    def get_targets(self,targets=False):
        # targets=False grab model outputs
        # targets=True grab model observations
        # fill the final_data list using targets from 
        # calibration/calibration_targets.py
        self.get_calibration_outputs()
        # organize the ouput in the form of the dictionary 
        # generates the flat list only for given target_names 
        print ('Output variables:')
        print ('Observations [1-True], Modeled [0-False]:',targets)
        d=dict()
        if len(self.target_names)>1:
            for icase in self.target_names: #zip(ikeys,icase):
                #print (icase)
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
        
        print(d.keys())
        out_list = [d[item] for item in d.keys()]
        out_flat = [item for sublist in out_list for item in sublist]
        
        return out_flat

    def get_calibration_outputs(self):

        output_directory_path=self.work_dir+"/output"
        ref_param_dir=self.work_dir+"/parameters"
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

