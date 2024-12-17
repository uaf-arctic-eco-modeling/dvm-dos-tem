# Testing, developing and describing the interface for MadsTEMDriver.py
=========================================================================

This file is intended to test that the driver can work with all three types of
targets specified (soil, PFT, PFT-compartment).

>>> import yaml

>>> my_yaml_string = """
... work_dir: /tmp/test_CA
... site: /work/testing-data/inputs/cru-ts40_ar5_rcp85_ncar-ccsm4_IMNAVIAT_CREEK_10x10
... PXx: 0
... PXy: 0
... calib_mode: GPPAllIgnoringNitrogen
... target_names: 
... - GPPAllIgnoringNitrogen
... - MossDeathC
... - VegCarbon
... cmtnum: 6
... opt_run_setup: --pr-yrs 5 --eq-yrs 10 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0
... params:
... - cmax
... - cmax
... - cmax
... - cmax
... - cmax
... - cmax
... - cmax
... pftnums:
... - 0
... - 1
... - 2
... - 3
... - 4
... - 5
... - 6
... """

>>> config_dict = yaml.load(my_yaml_string, Loader=yaml.FullLoader)

>>> import drivers.MadsTEMDriver

>>> d = drivers.MadsTEMDriver.MadsTEMDriver(config_dict)

>>> d.set_seed_path('/work/parameters')

>>> d.set_params_from_seed()

>>> d.load_target_data(ref_target_path='/work/calibration/')

>>> d.setup_outputs(d.target_names)

Grab the targets in two differnt formats (flat and labeled) and make sure the
values line up as expected. 

>>> import pandas as pd

>>> flat_targets = d.observed_vec(format='flat')
>>> df_targets = pd.DataFrame(d.observed_vec(format='labeled'))

Check on the first block of data, which is a PFT target, but not by compartment.
First print out the tables so we can see the expected shapes.

>>> df_targets.loc[df_targets['ctname'] == 'MossDeathC']
   cmtnum      ctname  pft  observed cmprt
7       6  MossDeathC  NaN     178.0   NaN

Then actually check the data so that we are confident in the output order for
the flat list.


Then check on some compartment data. Here we need to make sure that only targets
are included for PFTs, and compartments that are defined. So for example while
the main targets data structure includes zero for undefined PFTs and
compartments, these zero values should not be present in the `.observed_vec()`
outputs. E.g.:

>>> d.targets['VegCarbon']['Leaf']
[2.0, 37.1, 8.06, 2.0, 2.0, 22.0, 23.0, 0.0, 0.0, 0.0]

versus

>>> df_targets.loc[(df_targets['ctname']=='VegCarbon') & (df_targets['pft']==4)]
    cmtnum     ctname  pft  observed cmprt
17       6  VegCarbon  4.0       2.0  Leaf


>>> d.params_vec()
[22.8, 250.6, 65.0, 38.5, 7.8, 21.0, 36.3]

This makes sense because we haven't run the model yet so there are no outputs.

>>> d.clean()

>>> d.setup_run_dir()

>>> d.run()

Collect the model outputs and then stuff them into a DataFrame for easy
analysis.

>>> final_data = d.gather_model_outputs()
>>> import pandas as pd
>>> df_finaldata = pd.DataFrame(final_data)
>>> df_finaldata.info()
<class 'pandas.core.frame.DataFrame'>
RangeIndex: 20 entries, 0 to 19
Data columns (total 6 columns):
 #   Column  Non-Null Count  Dtype  
---  ------  --------------  -----  
 0   cmt     20 non-null     object 
 1   ctname  20 non-null     object 
 2   value   20 non-null     float64
 3   truth   20 non-null     float64
 4   pft     19 non-null     float64
 5   cmprt   12 non-null     object 
dtypes: float64(3), object(3)
memory usage: 1.1+ KB

Print out the top and bottom of the frame.

>>> df_finaldata.head()
     cmt                  ctname       value    truth  pft cmprt
0  CMT06  GPPAllIgnoringNitrogen    9.008573   11.833  0.0   NaN
1  CMT06  GPPAllIgnoringNitrogen  133.687429  197.867  1.0   NaN
2  CMT06  GPPAllIgnoringNitrogen   25.611490   42.987  2.0   NaN
3  CMT06  GPPAllIgnoringNitrogen    7.791676   10.667  3.0   NaN
4  CMT06  GPPAllIgnoringNitrogen    3.388915    3.375  4.0   NaN

>>> df_finaldata.tail()
      cmt     ctname      value  truth  pft cmprt
15  CMT06  VegCarbon   2.602119    2.0  3.0  Leaf
16  CMT06  VegCarbon   2.664471    3.2  3.0  Root
17  CMT06  VegCarbon   2.250932    2.0  4.0  Leaf
18  CMT06  VegCarbon  22.572059   22.0  5.0  Leaf
19  CMT06  VegCarbon  22.400614   23.0  6.0  Leaf
