#!/usr/bin/env python
# coding: utf-8

# # The step-by-step guide into the sensitivity analysis workflow. 
# 
# The workflow is designed to run from the inside of the docker container and assumes a specific folder layout. This notebook shows how to use the SensitivityDriver object and methods in the Sensitivity module to design and conduct a sensitivity analysis of dvmdostem parameters.
# 
# Authors: Tobey Carman and Elchin Jafarov

# ## Working with docker 
# Assuming that docker was successfully installed, and that you have built the appropriate docker images (see note) navigate to your local dvmdostem folder and then:
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
# 
# > NOTE: In the future we will have pre-built docker images hosted at a container registry like Dockerhub, or Github Container Registry, or Google Container Registry, but until we get that setup, you will need to build your own images. The directions for this are in the comments of the `Dockerfile` in the dvmdostem repo.

# In[1]:


# This helps for development and automatically re-imports any modules when they change
get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')


# ## Getting Started

# In[2]:


import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import Sensitivity
import param_util as pu


# Lets get started by making a driver object and print out some info about it.

# In[3]:


driver = Sensitivity.SensitivityDriver()
print(driver.info())


# OK, well now we have a `SensitivityDriver` object, but what can we do with it?? Well we can modify any parameter that exists for `dvmdostem`. How do we find these parameters? There are some helper functions in the `param_util` module for working with parameter files.
# > Note: Why in the world do we need a special `ParamUtilSpeedHelper` object here? Well the param_util.py file is written to be used in a wide varietly of circumstances and does not by default have any kind of cache or lookup structure for mapping files to parameter names. So we use a special object here, that builds such a cache and uses it, which is much faster than running the file-->parameter name look everytime.

# In[4]:


psh = pu.ParamUtilSpeedHelper(driver.get_initial_params_dir())
print(psh.list_params(cmtnum=4, pftnum=0))


# There are a lot of dvmdostem parameters! There is also a function that can show just the non-pft parameters:
# 
# > Note: Why do we have to print the result? We made the design decision to return the value and let the client decide what to do with it instead of printing within the function. This is awkward in some situations (needing to add `print(...)` all the time), and really helpful in other situations.

# In[16]:


print(psh.list_non_pft_params())


# The `SensitivtyDriver` object is designed to help setup and conduct a sensitivity analysis. At the present time there are some hard-coded assumptions in the driver object (which pixel to run, the input dataset/site to use, the source of the initial parameter values, which outputs to process and the location of the working directory). The driver object is configurable with respect to the parameters to be used in the sensitivity analysis, the bounds for the parameters, which PFT to analyze, and which CMT (community type) to run.
# 
# Now we have a few ways we can setup our `SensitivityDriver` object. 
# 
# ### Option 1
# This sets up the sample_matrix based on:
# 1. looking up the initial values from dvmdostem parameter files (cmt_*.txt), and
# 2. setting up the bounds based on those initial values plus/minus the percent diffs.
# 
# > Need a better name for `percent_diffs` - these are the % range that the bounds will be set around the initial value. Right now it defaults to +/-10% if the `percent_diffs` array is not passed.

# In[5]:


driver.design_experiment(50, 4, params=['cmax','rhq10'], pftnums=[0,None], percent_diffs=[.6, .2])
print(driver.info())


# We can also make some plots to see how our samples look with respect to the bounds and the distribution.

# In[6]:


driver.plot_sensitivity_matrix()


# ### Option 2
# Simply build the parameter specification by hand. The bounds are set totally manually.
# > Note that a `cmtnum` and `pftnums` are not set! This is not a problem for generating the sensitivity matrix. However it will be necessary to set a `cmtnum` and `pftnums` before conducting runs - so that the driver knows which parameters to modify and the model knows which community type to run. Knowing the community type that was used for the run will also be necessary for processing the outputs.

# In[7]:


names=['cmax','rhq10','micbnup']
#pfts=[3, None, None] # meaningless w/o cmt number too!
bounds=[[0.0,1.0], [25.0,60.0], [0.1, 0.4]]
initials=[0.5, 40.0, 0.3]
driver.params = [{'name':name, 'bounds':bound, 'initial':init} for name, bound, init in zip(names,bounds,initials)]
driver.sample_matrix = Sensitivity.generate_lhc(15, driver.params)
print(driver.info())


# Additionally, there is a way to save the experiment. This will output 2 files, one for the parameters, and one of the sample matrix.

# In[8]:


driver.save_experiment("/tmp/test_001")
get_ipython().system('cat /tmp/test_001_param_props.csv')
get_ipython().system('cat /tmp/test_001_sample_matrix.csv')


# And there is a way to load an experiment design from the text files. 
# > Note that the path handling could probably be improved

# In[9]:


driver.load_experiment("/tmp/test_001_param_props.csv","/tmp/test_001_sample_matrix.csv")
print(driver.info())


# ## Run the model over an experiment space
# 
# Now that we see a few ways to use a `SensitivityDriver` object, let's start fresh with a new driver instance, setup and execute some runs.
# 
# For this toy experiment, we are going to draw 10 sample sets across 3 parameters (2 soil parameter and one PFT parameter). We are going to use the default `percent_diffs` for generating the sample matrix: +/-10%. And we are going to be analyzing CMT 5 (Tussock Tundra).

# In[10]:


# Instantiate object, sets pixel, outputs, working directory, site selection (input data path)
driver = Sensitivity.SensitivityDriver()

# choose parameters, number of samples, 
driver.design_experiment(10, 5, params=['cmax', 'rhq10', 'micbnup'], pftnums=[3,None,None])
print(driver.info())
driver.plot_sensitivity_matrix()


# With the experiment designed, we need to setup all the required directories, and make all the required adjustments for each run, such as:
#  - enabling output variables, 
#  - adjusting the run mask, 
#  - adjusting the config file, and 
#  - injecting the parameter values from our `sample_matrix`.

# In[11]:


# makes directories, sets config files, input data, etc for each run
driver.setup_multi()


# And once the setup is complete, now we can carry out the runs. 

# In[12]:


# carry out the run and do initial output collection
driver.run_all_samples()


# ## Process, analyze, and plot data after runs

# In[13]:


driver.extract_data_for_sensitivity_analysis()

driver.first_steps_sensitivity_analysis()


# In[14]:


driver.make_cool_plot_2()


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# 

# In[ ]:





# In[ ]:





# Below here is some old code, leaving here for reference. WIll remove in another commit or so.
# 
# Elchin: 
# 
# 1. `get_CMT_params()` function is now implemented in `SensitivityDriver::design_experiment()`. 
# 2. `create_a_sample_matrix()` function is now implemented directly in the Sensitivity module. If you followed the code above, you will see how to use it. It needs some comments as found myself unable to describe the maths.
# 
# I used the "design_experiment" for the function name after looking into the `pyDOE` package as an alternate way to do the LHC sampling. See here: https://pythonhosted.org/pyDOE/
# 

# In[ ]:


def get_CMT_params(cmtnum=4,pftnum=3,perc=0.1):
    
    from collections import defaultdict
    '''
    This function gets the cmtnum and pftnum parameters from my-path-to-default/cmt_calparbgc.txt
    and sets the parameter specification. The default boundary setup is perc=+-10% from the original value

    Inputs:
        cmtnum : community type number (default=4)
        pftnum : plant functional type number (default=3)
        perc :   percent difference from the origina value (default=10%)

    Outputs:
        param_specs : paramter specifications dictionary

    Example:
       param_specs=get_CMT_params()
       for key in list(param_specs.keys()):
          print(key,':',param_specs[key])

    '''
    # Tobey consider changing param_util.py to more appropriate calling of a function from the .py file
    # change driver.work_dir to self.work_dir
    data = get_ipython().getoutput('param_util.py --dump-block-to-json /work/parameters/cmt_calparbgc.txt {cmtnum}')
    #data = run -i param_util.py --dump-block-to-json {self.work_dir}/default_parameters/cmt_calparbgc.txt {cmtnum}
    CMT_data = json.loads(data[0])

    #choose parameters correspoding to a given pfnum
    d=pd.Series(CMT_data['pft'+str(pftnum)])
    param_specs = defaultdict()
    print('Getting parameters for PFT:',d['name'])
    for key, val in d.items():
        if key=='name':
            continue
        param_specs[key]={'val':val, 'bnds':[val-perc*val,val+perc*val], 
                          'cmtnum':cmtnum, 'pftnum':pftnum, 'opt':False }

    return param_specs


# In[ ]:


param_specs=get_CMT_params(pftnum=1)
for key in list(param_specs.keys()):
   print(key,':',param_specs[key])


# We want to opt in vcmax and ncmax, change the bounds, and create the sample matrix.

# In[ ]:


print('Current cmax:',param_specs['cmax'])
param_specs['cmax']['bnds'][0]=param_specs['cmax']['val']-50
param_specs['cmax']['bnds'][1]=param_specs['cmax']['val']+50
param_specs['cmax']['opt']=True
print('Updated cmax:',param_specs['cmax'])

print('Current nmax:',param_specs['nmax'])
param_specs['nmax']['bnds'][0]=param_specs['nmax']['val']-3
param_specs['nmax']['bnds'][1]=param_specs['nmax']['val']+3
param_specs['nmax']['opt']=True
print('Updated nmax:',param_specs['nmax'])


# In[ ]:


def create_a_sample_matrix(run_name, param_specs, method='uniform', sample_N=5):
    # Tobey: we need to add lhsmdu in the docker file
    import lhsmdu    #generate Latin Hypercube samples
    '''
    This function creates a sampling matrix and saves it into the (var_'run_name'.csv) file
    Inputs:
        run_name: for a better tracking of the tests 
        param_specs: 'lhs', 'uniform' 
        sample_N: sample size
        param_specs: parameter specification dictionary
    Outputs:
        sample_matrix : the ( sample_N,len(sens_params) ) sample matrix 
    '''
    # 1. Create the sens_params dictionary that includes only opt-in values
    sens_params={}
    for key in list(param_specs.keys()):
        if param_specs[key]['opt']==True:
            sens_params[key]=param_specs[key]

    # 2. Select low boundaries from the sens_params dict. and calculate the difference
    val_low_bnd = [sens_params[key]['bnds'][0] for key in list(sens_params.keys())]
    val_diff = [sens_params[key]['bnds'][1]-sens_params[key]['bnds'][0] for key in list(sens_params.keys())]
    
    # 3. Choose sampling method: lhs or uniform
    if method == 'lhs':
        # Latin Hypercube Sampling, each column indicates a sample point
        # This is like an initialization, almost return the same results

        #Need to add lhsmdu in the docker file
        l = lhsmdu.sample(len(sens_params),sample_N)    #type:matrix
        # Latin Hypercube Sampling of factor(influent or parameter or ic)
        l = lhsmdu.resample().T        # Latin Hypercube Sampling from uniform, after transpose, each row indicates a sample point
        mat_diff = np.diag(val_diff)
        sample_matrix = l*mat_diff + val_low_bnd      # Scaling to Latin Hypercube Sampling of influent
                
    elif method == 'uniform':
        ## Uniform Sampling ##
        l = np.random.uniform(size=(sample_N, len(sens_params)))
        sample_matrix = l*val_diff + val_low_bnd

    np.savetxt('var_%s.csv'%(run_name),sample_matrix,delimiter=',',fmt='%13.5f')
    print ('Saves a sampling matrix [sample_size,array_size] into var_%s.csv'%(run_name))
    print ('sample_size,array_size: ',sample_matrix.shape)
    print ('Each column of the matrix corresponds to a variable perturbed 100 times around its original value ')
    print ('var_%s.csv'%(run_name), 'SAVED!')
    
    return sample_matrix


# In[ ]:


create_a_sample_matrix('test_run001',param_specs)


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




