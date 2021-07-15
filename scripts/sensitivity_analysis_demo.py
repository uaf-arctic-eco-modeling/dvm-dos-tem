#!/usr/bin/env python
# coding: utf-8

# In[4]:


import os
os.chdir('/Users/tobeycarman/Documents/SEL/dvm-dos-tem')


# In[9]:


import netCDF4 as nc
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json
import output_utils as ou


# In[10]:


PARAM = 'cmax'
PFTNUM = 1
CMTNUM = 4
PXx = 0; PXy = 0
H_RUNFOLDER = '../dvmdostem-workflows/sensitivity_analysis'
D_RUNFOLDER = '/data/workflows/sensitivity_analysis'

samples = np.linspace(start=100, stop=700, num=20)


# In[ ]:





# In[ ]:





# In[11]:


# Cleanup
get_ipython().system('rm -r {H_RUNFOLDER}')

# Place to work
get_ipython().system('docker compose exec dvmdostem-run setup_working_directory.py --input-data-path /data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_CALM_Toolik_LTER_10x10/ {D_RUNFOLDER}')

# Run mask
get_ipython().system('docker compose exec dvmdostem-run runmask-util.py --reset --yx {PXy} {PXx} {D_RUNFOLDER}/run-mask.nc')

# Outputs
get_ipython().system('docker compose exec dvmdostem-run outspec_utils.py {D_RUNFOLDER}/config/output_spec.csv --on GPP m p')

get_ipython().system('docker compose exec dvmdostem-run outspec_utils.py {D_RUNFOLDER}/config/output_spec.csv --on CMTNUM y')


# Config, enable eq outputs
CONFIG_FILE = H_RUNFOLDER + '/config/config.js'

# Read the existing data into memory
with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)

# Modify it
config['IO']['output_nc_eq'] = 1

# Write it back..
with open(CONFIG_FILE, 'w') as f:
    json.dump(config, f, indent=2)


# In[12]:


def adjust_param(new_value):
    data = get_ipython().getoutput('param_util.py --dump-block-to-json {H_RUNFOLDER}/default_parameters/cmt_calparbgc.txt {CMTNUM}')

    jdata = json.loads(data[0])

    pft = 'pft{}'.format(PFTNUM)
    jdata[pft][PARAM] = new_value

    with open("tmp_json.json", 'w') as f:
        json.dump(jdata, f)

    new_data = get_ipython().getoutput('param_util.py --fmt-block-from-json tmp_json.json {H_RUNFOLDER}/default_parameters/cmt_calparbgc.txt')

    with open('{:}/parameters/cmt_calparbgc.txt'.format(H_RUNFOLDER), 'w') as f:
        # make sure to add newlines!
        f.write('\n'.join(new_data))


# In[13]:


def run_model():
    get_ipython().system('docker compose exec --workdir {D_RUNFOLDER} dvmdostem-run     dvmdostem -p 50 -e 200 -s 0 -t 0 -n 0 -l err --force-cmt {CMTNUM}')

def collect_outputs():
    # Get the model output
    ds = nc.Dataset('{}/output/GPP_monthly_eq.nc'.format(H_RUNFOLDER))
    gpp = ds.variables['GPP'][:]
    yr_gpp = ou.sum_monthly_flux_to_yearly(gpp)
    output_data = yr_gpp[-1:,PFTNUM,PXy,PXx]

    # Get the parameter value for the run
    paramdata = get_ipython().getoutput('param_util.py --dump-block-to-json {H_RUNFOLDER}/parameters/cmt_calparbgc.txt {CMTNUM}')
    jparamdata = json.loads(paramdata[0])
    pft = 'pft{}'.format(PFTNUM)
    run_param_value = jparamdata[pft][PARAM]

    with open('{}/sensitivity.csv'.format(H_RUNFOLDER), 'a') as f:
        f.write('{:},{:}\n'.format(run_param_value, output_data[0]))
    


# In[ ]:





# In[14]:


# Backup default params
get_ipython().system('cp -r {H_RUNFOLDER}/parameters {H_RUNFOLDER}/default_parameters')

# Make a file for storing our sensitivity data
# and put the header in the file.
with open('{}/sensitivity.csv'.format(H_RUNFOLDER), 'w') as f:
  f.write('{:},{:}\n'.format('pvalue','output'))

# Run default case
print("Run default case....")
run_model()
collect_outputs()


for i in samples:
    print("adjust_param({:}) --> run_model() --> collect_outputs()".format(i))
    adjust_param(i)
    run_model()
    collect_outputs()


# In[ ]:





# In[15]:


df = pd.read_csv('{:}/sensitivity.csv'.format(H_RUNFOLDER))


# In[16]:


sens_df = pd.DataFrame(dict(pvalue=df.pvalue[1:], sensitivity=(df.output[0] - df.output[1:])/abs(df.output[0])))


# In[30]:


axes = sens_df.plot('pvalue', 'sensitivity', kind='line', ylabel='% error from default')
#axes = plt.plot(sens_df.pvalue, sens_df.sensitivity)


# In[29]:


type(ax)


# In[314]:


df


# In[312]:


get_ipython().system('cat {H_RUNFOLDER}/sensitivity.csv')


# In[253]:





# In[255]:





# In[256]:





# In[ ]:





# In[ ]:





# In[258]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




