#!/usr/bin/env python
# coding: utf-8

# # The first prototype of the sensitivity analysis workflow. 
# 
# The workflow is designed to run from the inside of the docker container and assumes a specific folder layout.  
# 
# Authors: Tobey Carman and Elchin Jafarov

# ## Working with the docker 
# Assuming that docker was successfully installed, navigate to your local dvmdostem folder:
# 
# 1. Strat the containers <br/>
# `$ docker compose up -d` <br/>
# 2. Enter to the container <br/>
# `$ docker compose exec dvmdostem-run bash` <br/>
# 3. Start jupyter notebook inside the /work folder <br/>
# `$ jupyter notebook --ip 0.0.0.0 --no-browser --allow-root` <br/>
# 4. Copy the url into your browser. <br/>
# 5. When done. Shut down container <br/>
# `$ docker compose down` <br/>

import netCDF4 as nc
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json
import output_utils as ou
import param_util as pu
import os
import subprocess
from contextlib import contextmanager


@contextmanager
def log_wrapper(message,tag=''):
    print('[SA:{}] {}'.format(tag, message))
    try:
        yield
    finally:
        print()

class Sensitivity:
    """Sensitivity analysis class."""

    def __init__(self):

        # row and columns location of the point/site
        self.PXx = 0
        self.PXy = 0

        # workspace location, input location
        self.work_dir = '/data/workflows/sensitivity_analysis'
        self.input_cat = '/data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_CALM_Toolik_LTER_10x10/'


        # output variables to use...
        self.outputs = [
            {
                'name':'GPP',
                'type':'flux'
            },
            {
                'name':'VEGC',
                'type':'pool'
            },
            {
                'name':'VEGN',
                'type':'pool'
            },


        ]

        self.params = [
            {
                'name': 'cmax',
                'cmtnum': 4,
                'pftnum': 1,
                'samples': np.linspace(start=100, stop=700, num=5)
            },
            {
                'name': 'rhq10',
                'cmtnum': 4,
                'pftnum': None,
                'samples': np.linspace(start=0.01, stop=5, num=5) 
            }
        ]

    def PFTNUM(self):
        '''Not sure what to do with this one...
        should the pft that the outputs look at be the same as the param pfts?
        what about non-pft outputs?
        '''
        pft_nums = set([item['pftnum'] for item in self.params])
        pft_nums.discard(None) # Get rid of None from soil (non-pft) params...
        if not (len(pft_nums) == 1):
            raise RuntimeError("Problem!! You must have consistent PFT NUMBERS in parameter specification!")
        return pft_nums.pop()

    def CMTNUM(self):
        '''
        Look at the param dictionary, extract the CMT 
        numbers specified, make sure they are consistent,
        and return the number.

        Returns
        -------
        cmtnum : int
          the cmtnumber specified in the param dictionaries

        Raises
        ------
        RuntimeError :
          if there is an inconsistency in cmtnumber
          amongst the parameter specifications
        '''
        cmt_nums = set([item['cmtnum'] for item in self.params])

        if not (len(cmt_nums) == 1):
            raise RuntimeError("Problem!! You must have consistent CMT NUMBERS in parameter specification!")

        return cmt_nums.pop()



    def setup(self):
        '''Sequence of steps necessary to commence sensitvity analysis.'''

        os.chdir('/work/scripts')

        with log_wrapper('Cleaning up...',tag='setup') as lw:
            if os.path.exists(self.work_dir):
                os.system('rm -r {}'.format(self.work_dir))

        m = 'Copy params, config files into the new_folder, adjust paths in config...'
        with log_wrapper(m,tag='setup') as lw:
            program = '/work/scripts/setup_working_directory.py'
            opt_str = '--input-data-path {} {}'.format(self.input_cat, self.work_dir)
            cmdline = program + ' ' + opt_str
            print('Running setup:', cmdline)
            comp_proc = subprocess.run(cmdline, shell=True, check=True, capture_output=True) 
            #print()


        print('---> Apply the mask...')
        program = '/work/scripts/runmask-util.py'
        options = '--reset --yx {} {} {}/run-mask.nc'.format(self.PXy, self.PXx, self.work_dir)
        cmdline = program + ' ' + options
        print("Running:", cmdline)
        comp_proc = subprocess.run(cmdline, shell=True, check=True, capture_output=True)
        print()

        print('---> Enable output variables in outspec.csv file...')
        for output_spec in self.outputs:
            program = '/work/scripts/outspec_utils.py'
            options = '{}/config/output_spec.csv --on {} m p'.format(self.work_dir, output_spec['name'])
            cmdline = program + ' ' + options
            print("Running:", cmdline)
            comp_proc = subprocess.run(cmdline, shell=True, capture_output=True, check=True)
        print()

        print('---> Turn on the CMT output only yearly resolution...')
        program = '/work/scripts/outspec_utils.py'
        options = '{}/config/output_spec.csv --on CMTNUM y'.format(self.work_dir)
        cmdline = program + ' ' + options
        print("Running:", cmdline)
        comp_proc = subprocess.run(cmdline, shell=True, check=True, capture_output=True)
        print()
        
        print('---> Modify config file to enable equlibrium outputs...')
        CONFIG_FILE = self.work_dir + '/config/config.js'
        # Read the existing data into memory
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            
        # Modify value...
        config['IO']['output_nc_eq'] = 1

        # Write it back..
        print('CONFIG_FILE:',CONFIG_FILE,'was modified!')
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        print()
            
        # Backup default params. The defaults will be static, and 
        # in each run, the parameters in the parameters/ directory
        # will be modified...
        print('---> Backup default params...')
        get_ipython().system('cp -r {self.work_dir}/parameters {self.work_dir}/default_parameters')
        print()

        for p in self.params:
            with open('{}/sensitivity_{}.csv'.format(self.work_dir, p['name']), 'w') as f:
                f.write('{:},{:},{:},{:}\n'.format('pname','pvalue','output_gpp','output_vegc'))
            print()
            
        # Make an empty file for storing our sensitivity data
        # and put the header in the file.
        print('---> Create empty file for accumulating sensitivity results...')
        with open('{}/sensitivity_{}.csv'.format(self.work_dir, 'default'), 'w') as f:
            f.write('{:},{:},{:},{:}\n'.format('pname','pvalue','output_gpp','output_vegc'))
        print()
    
    def update_param(self, new_value, pname):
        pftnum = [i['pftnum'] for i in self.params if i['name']==pname]
        pu.update_inplace(new_value, '{}/parameters/'.format(x.work_dir), pname, self.CMTNUM(), pftnum[0])

    def collect_outputs(self, param_dict=None):

        # Next step will be trying to loop over the self.output_vars...
        # not sure how to handle sum over fluxes for pool vars??
        # need more complicated data structure for self.output_vars that 
        # can describe what the vars are??
        ds = nc.Dataset('{}/output/VEGC_monthly_eq.nc'.format(self.work_dir))
        vegc = ds.variables['VEGC'][:]
        yr_vegc = ou.average_monthly_pool_to_yearly(vegc)
        out_vegc = yr_vegc[-1:,self.PFTNUM(), self.PXy,self.PXx]

        # Get the model output
        ds = nc.Dataset('{}/output/GPP_monthly_eq.nc'.format(self.work_dir))
        gpp = ds.variables['GPP'][:]
        yr_gpp = ou.sum_monthly_flux_to_yearly(gpp)
        # grab the last time step
        out_gpp = yr_gpp[-1:,self.PFTNUM(),self.PXy,self.PXx]

        if param_dict['name'] == 'default':
            with open('{}/sensitivity_{}.csv'.format(self.work_dir, param_dict['name']), 'a') as f:
                f.write('{:},{:},{:},{:}\n'.format(param_dict['name'], '', out_gpp[0], out_vegc[0]))

        else:
            CMT = self.CMTNUM()
            f = pu.which_file(self.work_dir + '/parameters', param_dict['name'])
            paramdata = get_ipython().getoutput('param_util.py --dump-block-to-json {f} {CMT}')
            jparamdata = json.loads(paramdata[0])
            #print(jparamdata)
            #print()
            if param_dict['name'] in jparamdata.keys():
                run_param_value = jparamdata[param_dict['name']]
            else:
                pft = 'pft{}'.format(self.PFTNUM())
                run_param_value = jparamdata[pft][param_dict['name']]

            # Need to modify if we want to save timeseries output!!
            # Need to syncronize this with setting up header!!
            with open('{}/sensitivity_{}.csv'.format(self.work_dir,param_dict['name']), 'a') as f:
                f.write('{:},{:},{:},{:}\n'.format(param_dict['name'], run_param_value, out_gpp[0], out_vegc[0]))



    def run_model(self):
        m = "Running model..."
        with log_wrapper(m, tag='run') as lw:
            program = '/work/dvmdostem'
            ctrl_file = os.path.join(self.work_dir, 'config','config.js')
            opt_str = '-p 5 -e 5 -s 5 -t 5 -n 5 -l err --force-cmt {} --ctrl-file {}'.format(self.CMTNUM(), ctrl_file)
            command_line = program + ' ' + opt_str
            print("Running command: ", command_line)
            completed_process = subprocess.run(
                command_line,        # The program + options 
                shell=True,          # must be used if passing options as str and not list
                check=True,          # raise CalledProcessError on failure
                capture_output=True, # collect stdout and stderr
                cwd=self.work_dir)   # control context


x = Sensitivity()
x.setup()


get_ipython().system('ls /data/workflows/sensitivity_analysis/')


x.params


x.run_model()
# x.write_defaults()
# x.params

#sensitivity_defaults.csv
# pname,pvalue,output_gpp,output_vegc
# cmax,100,164.25517511367798,443.6672061284383
# rhq10,0.5,164.25517511367798,443.6672061284383
# vcmax,200,164.25517511367798,443.6672061284383

# sensitivity_default.csv
# output_gpp, output_vegc
#x.write_param_dict()

x.collect_outputs({'name':'default','file':''})


#!cat /data/workflows/sensitivity_analysis/default_param_values.csv
print()
# pname,default_value
# cmax,100
# rhq10,0.5


get_ipython().system('cat /data/workflows/sensitivity_analysis/sensitivity_default.csv')
print()
get_ipython().system('cat /data/workflows/sensitivity_analysis/sensitivity_cmax.csv')
print()
get_ipython().system('cat /data/workflows/sensitivity_analysis/sensitivity_rhq10.csv')





# Work in progress....
for param_dict in x.params:
    for sample in param_dict['samples']:
        x.update_param(sample, param_dict['name'])
        x.run_model()
        x.collect_outputs(param_dict)


get_ipython().system('cat /data/workflows/sensitivity_analysis/sensitivity_default.csv')
print()
get_ipython().system('cat /data/workflows/sensitivity_analysis/sensitivity_cmax.csv')
print()
get_ipython().system('cat /data/workflows/sensitivity_analysis/sensitivity_rhq10.csv')





df_cmax = pd.read_csv('{:}/sensitivity_cmax.csv'.format(x.work_dir))
df_rhq10 = pd.read_csv('{}/sensitivity_rhq10.csv'.format(x.work_dir))
df_default = pd.read_csv('{}/sensitivity_default.csv'.format(x.work_dir))
print(df_cmax.head())
print(df_rhq10.head())
print(df_default.head())





fig, axes = plt.subplots(2,2)
axes[0,0].plot(df_cmax.pvalue, df_cmax.output_gpp)
axes[1,0].plot(df_cmax.pvalue, df_cmax.output_vegc)

axes[0,1].plot(df_rhq10.pvalue, df_rhq10.output_gpp)
axes[1,1].plot(df_rhq10.pvalue, df_rhq10.output_vegc)

#axes[0].plot(df.pvalue[1:], df.output_gpp[1:])
#axes[0].plot(df.pvalue[0], df.output_gpp[0], marker='^', color='red')
#axes[0].plot(df.pvalue[1:], df.output_vegc[1:])

#axes[1].plot(df.pvalue[1:], df.output_vegc[1:])
#axes[1].plot(df.pvalue[0], df.output_vegc[0], marker='^', color='red')

#df.plot('pvalue','output_gpp', 'output_vegc')
#df.plot('pvalue','output_vegc')


gpp_sens_df = pd.DataFrame(dict(pvalue=df.pvalue[1:], sensitivity=abs(df.output_gpp[0] - df.output_gpp[1:])/abs(df.output_gpp[0])))
vegc_sens_df = pd.DataFrame(dict(pvalue=df.pvalue[1:], sensitivity=abs(df.output_vegc[0] - df.output_vegc[1:])/abs(df.output_vegc[0])))

axes = gpp_sens_df.plot('pvalue', 'sensitivity', kind='line', ylabel='% error from default')
axes = vegc_sens_df.plot('pvalue', 'sensitivity', kind='line', ylabel='% error from default')







