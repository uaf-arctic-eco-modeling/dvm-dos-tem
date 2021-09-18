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
import os
import subprocess


class Sensitivity:
    """Sensitivity analysis class."""

    def __init__(self):
        self.PARAM = 'cmax'
        self.PFTNUM = 1 #plant functional type
        self.CMTNUM = 4 #community type
        # row and columns location of the point/site
        self.PXx = 0; 
        self.PXy = 0 
        # the variable corresponds to the path where we will run the analysis
        self.work_dir = '/data/workflows/sensitivity_analysis'
        self.input_cat = '/data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_CALM_Toolik_LTER_10x10/'
        # the sample distribution range (in this case vcmax in [vcmax_min,vcmax_max])
        self.samples = np.linspace(start=100, stop=700, num=20)

    def setup(self):
        os.chdir('/work/scripts')

        if os.path.exists(self.work_dir):
            os.system('rm -r {}'.format(self.work_dir))

        #copies config files and params directory
        #copy input data files to the D_RUNFOLDER folder
        print('Copy input files into the new_folder')
        get_ipython().run_line_magic('run', '-i setup_working_directory.py         --input-data-path {self.input_cat} {self.work_dir}')
        print()
        print('---')
        
        print('Apply the mask')
        get_ipython().run_line_magic('run', '-i runmask-util.py         --reset --yx {self.PXy} {self.PXx} {self.work_dir}/run-mask.nc')
        print()
        print('---')
        
        # Outputs: GPP, monthly and pft resolution
        print('Setup output variable temporal resolution')
        get_ipython().run_line_magic('run', '-i outspec_utils.py         {self.work_dir}/config/output_spec.csv --on GPP m p')
        print()
        print('---')
        
        #Turn on the CMT output only yearly resolution
        print('Turn on the CMT output only yearly resolution')
        get_ipython().run_line_magic('run', '-i outspec_utils.py         {self.work_dir}/config/output_spec.csv --on CMTNUM y')
        print()
        print('---')
        
        # Config, enable eq outputs
        CONFIG_FILE = self.work_dir + '/config/config.js'
        # Read the existing data into memory
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            
        # Modify it
        config['IO']['output_nc_eq'] = 1

        # Write it back..
        print('CONFIG_FILE:',CONFIG_FILE,'was modified!')
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
            
        # Backup default params. The defaults will be static, and 
        # in each run, the parameters in the parameters/ directory
        # will be modified...
        print('Backup default params...')
        get_ipython().system('cp -r {self.work_dir}/parameters {self.work_dir}/default_parameters')
        print()
        print('---')

        # Make an empty file for storing our sensitivity data
        # and put the header in the file.
        print("Create empty file for accumulating sensitivity results...")
        with open('{}/sensitivity.csv'.format(self.work_dir), 'w') as f:
            f.write('{:},{:}\n'.format('pvalue','output'))
        print()
        print('---')

    def update_param(self,new_value):
        # reading dvmdostem param file and puts it in the json format
        data = get_ipython().getoutput('param_util.py --dump-block-to-json {self.work_dir}/default_parameters/cmt_calparbgc.txt {self.CMTNUM}')
        jdata = json.loads(data[0])

        pft = 'pft{}'.format(self.PFTNUM)
        jdata[pft][self.PARAM] = new_value

        with open("tmp_json.json", 'w') as f:
            json.dump(jdata, f)

        new_data = get_ipython().getoutput('param_util.py --fmt-block-from-json tmp_json.json {self.work_dir}/default_parameters/cmt_calparbgc.txt')

        with open('{:}/parameters/cmt_calparbgc.txt'.format(self.work_dir), 'w') as f:
            # make sure to add newlines!
            f.write('\n'.join(new_data))
    
    def collect_outputs(self):
        # Get the model output
        ds = nc.Dataset('{}/output/GPP_monthly_eq.nc'.format(self.work_dir))
        gpp = ds.variables['GPP'][:]
        yr_gpp = ou.sum_monthly_flux_to_yearly(gpp)
        # grab the last time step
        output_data = yr_gpp[-1:,self.PFTNUM,self.PXy,self.PXx]

        # Get the parameter value for the run
        paramdata = get_ipython().getoutput('param_util.py --dump-block-to-json {self.work_dir}/parameters/cmt_calparbgc.txt {self.CMTNUM}')
        jparamdata = json.loads(paramdata[0])
        pft = 'pft{}'.format(self.PFTNUM)
        run_param_value = jparamdata[pft][self.PARAM]

        #need to modify if we want to save timeseries output
        with open('{}/sensitivity.csv'.format(self.work_dir), 'a') as f:
            f.write('{:},{:}\n'.format(run_param_value, output_data[0]))

    def run_model(self):
        command_line = '/work/dvmdostem'
        #options = '-p 50 -e 200 -s 0 -t 0 -n 0 -l err --force-cmt {}'.format(CMTNUM)
        ctrl_file = os.path.join(self.work_dir, 'config','config.js')
        options = '-p 5 -e 5 -s 5 -t 5 -n 5 -l err --force-cmt {} --ctrl-file {}'.format(self.CMTNUM, ctrl_file)
        command_line = command_line + ' ' + options
        print("Calling to run model: ", command_line)
        status=subprocess.call(command_line, shell=True, cwd=self.work_dir)


x = Sensitivity()
x.setup()





x.run_model()
x.collect_outputs()


for i in x.samples:
    print("adjust_param({:}) --> run_model() --> collect_outputs()".format(i))
    x.update_param(i)
    x.run_model()
    x.collect_outputs()


df = pd.read_csv('{:}/sensitivity.csv'.format(x.work_dir))
df.head(4)


df.plot()


sens_df = pd.DataFrame(dict(pvalue=df.pvalue[1:], sensitivity=abs(df.output[0] - df.output[1:])/abs(df.output[0])))
axes = sens_df.plot('pvalue', 'sensitivity', kind='line', ylabel='% error from default')




