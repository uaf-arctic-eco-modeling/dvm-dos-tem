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

import Sensitivity





x = Sensitivity.Sensitivity()
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







