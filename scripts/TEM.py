import os
os.chdir('/work/scripts')
#import os.path


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
    print('[SA:{}] {}'.format(tag, message))
    try:
        yield
    finally:
        print()

class TEM_model:

    def __init__(self): 
        self.param_dir = '/work/parameters'
        self.work_dir = '/data/workflows/single_run'
        self.site = '/data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_CALM_Toolik_LTER_10x10/'
        self.PXx = 0
        self.PXy = 0
        self.outputs = [
          { 'name': 'GPP', 'type': 'flux',},
          { 'name': 'VEGC','type': 'pool',},
        ]
        self.pftnums={}
        self.cmtnum={}
        self.opt_run_setup = '-p 5 -e 5 -s 5 -t 5 -n 5'
        self.sampling_method = ''
        self.params = {}
        self.calib_mode=''
        
        
    def collect_outputs(self):
        # Get the model output
        ds = nc.Dataset('{}/output/{}_monthly_tr.nc'.format(self.work_dir,self.outputs[0]['name']))
        var_data = ds.variables[self.outputs[0]['name']][:]

        # Here we grab only last 5 years of the GPP data
        # in the future we might combine multiple outputs
        output_data = var_data[-60:,self.get_cmtnum(),self.PXy,self.PXx]

        return output_data


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
        DA_specific_folder = self.work_dir
        for j in range(len(self.params)):
            pu.update_inplace(
              self.params[j]['val'], 
              os.path.join(DA_specific_folder, 'parameters'), 
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
    
    def netcdf2df(self,var_name,TIME,outfolder=''):    
        '''
        Input:
            fdir: path to the resutls folder
            var_name: output variable name
            TIME: 'monthly' or 'yearly'
        Output:
            df1: dataframe of oname time series for tr run
        Example:
        vegc=netcdf2df('/data/workflows/single_run/output/','VEGC','monthly')
        '''  

        #fname=fdir+var_name+'_'+TIME+'_tr.nc'
        fname=self.work_dir+'/output/'+var_name+'_'+TIME+'_tr.nc'
        print(fname)

        if TIME == 'monthly' :
          period = 15*12
          freq = 'M'
        elif TIME == 'yearly':
          period = 15
          freq = 'Y' 
        else:
          print('Unknown period and freq')
        #get the 'oname' variable time series from the correspoding output nc files  
        stg_data = nc.Dataset(fname, 'r')

        if len(stg_data.dimensions)==4:
            keys=[item for item in stg_data.dimensions.keys()]   
            df1 = pd.DataFrame(stg_data.variables[var_name][-period:,:,0,0], \
                     columns=[var_name+'_'+str(idx) for idx in range(stg_data.dimensions[keys[3]].size)])
        else:
            df1 = pd.DataFrame(stg_data.variables[var_name][-period:,0,0], columns=[var_name]) 
        df1 = df1.set_index(pd.Series(pd.period_range("1/2000", freq=freq, periods=period)))
        df1.index.name = 'date'

        return df1

    def get_TEM_output(self,var_name):
        '''
        fdir: '/data/workflows/single_run/output/'
        var_name: 'VWCLAYER'
        Example:
            gpp=get_TEM_output('/data/workflows/single_run/output/','TLAYER')
        '''
        #path_to_out=self.work_dir+'/output/'
        if var_name=='GPP':
            out=self.netcdf2df(var_name,'monthly')
            out['Total']= out.sum(axis=1)
        elif var_name=='ALD':
            out=self.netcdf2df(var_name,'yearly')
        else:
            out=self.netcdf2df(var_name,'monthly')

        return out

    def get_Toolik_obs_out(self, VAROBS, VAROUT):

        '''
        VAROUT: GPP
        VAROBS: gpp
        Output:
        out: dateframe of outputs
        obs: dataframe of obervations
        Example:
            [obs,out]=get_Toolik_obs_out('gpp','GPP')
        '''
        path_to_obser="/data/input-catalog/Toolik/observations/"
        obs_fname=path_to_obser+"Toolik_"+VAROBS+".csv"
        obs=pd.read_csv(obs_fname)
        print(VAROBS+' observ shape (before):',obs.shape)
        #print(obs.head())

        obs.dropna(inplace=True)
        obs=obs.set_index('date')
        formatted_vars=['gpp','10cm_tlayer4','20cm_tlayer5','40cm_tlayer7','snowthick','reco']
        if VAROBS in formatted_vars:
            obs.index = pd.to_datetime(obs.index, format = '%Y-%m-%d').strftime('%Y-%m') 
            #Comment this out for yearly observations (ald, deepdz, shlwdz)

        # NOTE: The index periods should match 
        obs.index=pd.PeriodIndex(obs.index.values, freq='M')
        #obs=obs.set_index('date')
        obs.index.name = 'date'
        #print('obs:',obs.head())

        #VAROUT
        #path_to_out='/data/workflows/single_run/output/'
        #path_to_out=self.work_dir+'/output/'
        #print(path_to_out,VAROUT)
        out=self.get_TEM_output(VAROUT)
        print(VAROUT+' TEM outputs shape (before):',out.shape)
        print('out:',out.tail())

        common_index = set(obs.index).intersection(out.index)
        #obs = obs.loc[common_index].sort_values(by='date')
        #out = out.loc[common_index].sort_values(by='date')
        obs = obs.loc[list(common_index)].sort_index()
        out = out.loc[list(common_index)].sort_index()
        print(VAROBS+' observ shape (after):',obs.shape)
        print(VAROUT+' TEM outputs shape (after):',out.shape)
        print()

        return [obs,out]

    def get_calibration_outputs(self,calib=False):
        #get_calibration_outputs("/data/workflows/qcal-demo/") 
        #self.work_dir = '/data/workflows/single_run'

        output_directory_path=self.work_dir+"/output"
        ref_param_dir=self.work_dir+"/parameters"
        ref_targets={}
        ref_targets_dir="/work"

        #Y = 0 #self.PXx
        #X = 0
        last_N_yrs = 10
        
        nc_file=os.path.join(output_directory_path, 'CMTNUM_yearly_eq.nc')
        if not(os.path.exists(nc_file)):
            return ''

        with nc.Dataset(nc_file, 'r') as ds:
            data = ds.variables['CMTNUM'][-last_N_yrs:,self.PXy,self.PXx]

        assert(data.min() == data.max()) # should be the same CMT for the whole time frame
        cmtkey = 'CMT{:02d}'.format(data[0])

        caltarget_to_ncname_map = [
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

        old_path = sys.path
        #print(old_path)
        sys.path = [os.path.join(ref_targets_dir, 'calibration')]
        print("Loading calibration_targets from : {}".format(sys.path))
        import calibration_targets as ct
        caltargets = {'CMT{:02d}'.format(v['cmtnumber']):v for k, v in iter(ct.calibration_targets.items())}
        del ct
        print("Resetting path...")
        sys.path = old_path

        ref_targets = caltargets

        final_data = []
        for ctname, ncname in caltarget_to_ncname_map:

            data, dims = ou.get_last_n_eq(ncname, 'yearly', output_directory_path, n=last_N_yrs)
            dsizes, dnames = list(zip(*dims))

            #print(ctname, output_directory_path, ncname, dims, dnames, dsizes)
            if dnames == ('time','y','x'):
                pec = pu.percent_ecosys_contribution(cmtkey, ctname, ref_params_dir=ref_param_dir)
                truth = ref_targets[cmtkey][ctname]
                value = data[:,self.PXy,self.PXx].mean()

                d = dict(cmt=cmtkey, ctname=ctname,value=value,truth=truth)
                final_data.append(d)

            elif dnames == ('time','y','x','pft'):
              for pft in range(0,10):
                if pu.is_ecosys_contributor(cmtkey, pft, ref_params_dir=ref_param_dir):
                  pec = pu.percent_ecosys_contribution(cmtkey, ctname, pftnum=pft, ref_params_dir=ref_param_dir)
                  truth = ref_targets[cmtkey][ctname][pft]
                  value = data[:,pft,self.PXy,self.PXx].mean()

                  d = dict(cmt=cmtkey, ctname=ctname,value=value,truth=truth,pft=pft)
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
                    pec = pu.percent_ecosys_contribution(cmtkey, ctname, pftnum=pft, compartment=clu[cmprt], ref_params_dir=ref_param_dir)
                    truth = ref_targets[cmtkey][ctname][clu[cmprt]][pft]
                    value = data[:,cmprt,pft,self.PXy,self.PXx].mean()

                    d = dict(cmt=cmtkey, ctname=ctname,value=value,truth=truth,pft=pft)
                    final_data.append(d)

                  else:
                    pass
                    #print "  -> Failed! "#contributor test! Ignoring pft:{}, compartment:{}, caltarget:{}, output:{}".format(pft, cmprt, ctname, ofname)

            else:
              raise RuntimeError("SOMETHING IS WRONG?")

        if calib: # calib=truth get the truth otherwise output
            out=[item['truth'] for item in final_data]
        else:
            out=[item['value'] for item in final_data]

        return out

 

#dvmdostem=TEM_model()
# The setup is slighly different from the Sensitivity Analysis (SA).
# We do not include bounds here, there is no need in bounds for the DA. 
# Similar to SA we have params dictionary in following form
# {'name': 'cmax', 'val': 210.0, 'cmtnum': 4, 'pftnum': 0}
# This is dictionary is taking into account multiple pfts
# set_params setups number of parameters for a given cmtnum.
# currently (similar to SA) we cannot do that for multiple cmtnums
# Then we call `model_setup`, which copies all the input 
# and parameter files from dvmdostem to the `work_dir`. This allows to not interfere
# with setup in the dvmdostem folder (i.e. run DA in the designated folder). 
# NOTE: this formulation is different from SA, because we run everything in designated 
# work_dir folder. The pymc will do the required optimization and parallelization on its own.
# Our goal is to create a `custom_model` function which could update parameters in the model. 

# To make this parallel, use setup from SA
# generate unique xxxx number based on number of processors that will be used
# for example sample will use 4 cores
# then `run` should have 16 unique samples 
# random.sample(range(1000, 9999), 4)
#dvmdostem.set_params(cmtnum=4, params=['cmax','cmax'], pftnums=[0,1])
#print(dvmdostem.params)
#print()
#dvmdostem.clean()
#dvmdostem.setup()
#dvmdostem.run()
#Need to wirte the run function 
