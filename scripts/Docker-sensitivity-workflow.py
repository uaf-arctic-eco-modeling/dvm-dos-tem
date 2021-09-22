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

get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')


import netCDF4 as nc
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json
import output_utils as ou
import param_util as pu
import os
import subprocess

import Sensitivity


param_specs = [
    {'name':'cmax', 'cmtnum':4, 'pftnum':3, 'bounds':[100,700],'enabled':True },
    {'name':'rhq10', 'cmtnum':4, 'pftnum':None, 'bounds':[0.1,5],'enabled':True },
    {'name':'micbnup', 'cmtnum':4, 'pftnum':None, 'bounds':[0.1,10],'enabled':True },
]


def generate_sample_matrix(pspecs, N, method='uniform'):
    
    if not method == 'uniform':
        raise RuntimeError("Not implemented yet!")
    
    sample_matrix = {}
    for i, p in enumerate(filter(lambda x: x['enabled'], param_specs)):
        samples = np.linspace(p['bounds'][0], p['bounds'][1], N)
        sample_matrix[p['name']] = samples

    return pd.DataFrame(sample_matrix)














sample_matrix = generate_sample_matrix(param_specs, 10)
sample_matrix.head()





driver = Sensitivity.SensitivityDriver(param_specs, sample_matrix)


get_ipython().run_line_magic('time', 'driver.setup_multi()')





get_ipython().run_line_magic('time', 'driver.run_all_samples()')





driver.collect_outputs()


import glob
file_list = glob.glob('/data/workflows/sensitivity_analysis/**/*sensitivity.csv', recursive=True)
df = pd.concat( map(pd.read_csv, file_list), ignore_index=True)
df = df.sort_values('p_cmax')
corr = df.corr()

print(corr)


corr.plot()





























# Sets initial values from the parameters directory - works better when used with 
# Sensitivity.setup_single() 
# Not sure how to use this yet...
for param in param_specs:
    pfile = pu.which_file(os.path.join(x2.work_dir, "parameters"), param['name'])
    data = pu.get_CMT_datablock(pfile, param['cmtnum'])
    data_dict = pu.cmtdatablock2dict(data)
    if param['pftnum'] is not None:
        pftkey = 'pft{}'.format(param['pftnum'])
        #print(param['name'], data_dict[pftkey][param['name']])
        param['initial_value'] = data_dict[pftkey][param['name']]
    else:
        #print(param['name'], data_dict[param['name']])
        param['initial_value'] = data_dict[param['name']]
    print(param)





























































