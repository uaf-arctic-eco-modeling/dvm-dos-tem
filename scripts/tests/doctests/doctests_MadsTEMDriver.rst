# Testing, developing and describing the interface for MadsTEMDriver.py
=========================================================================

>>> import yaml

>>> my_yaml_string = """
... work_dir: /tmp/test_CA
... site: /data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_IMNAVIAT_CREEK_10x10
... PXx: 0
... PXy: 0
... calib_mode: GPPAllIgnoringNitrogen
... target_names: 
... - GPPAllIgnoringNitrogen
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

>>> d.targets_meta['GPPAllIgnoringNitrogen']['units']
'g/m2/year'

>>> d.work_dir
'/tmp/test_CA'

>>> d.setup_outputs(d.target_names)

Grab the targets in two differnt formats (flat and labeled) and make sure the 
values line up as expected.

>>> import pandas as pd

>>> flat_targets = d.observed_vec(format='flat')
>>> df_targets = pd.DataFrame(d.observed_vec(format='labeled'))

Check on the first block of data, which is a PFT target, but not by compartment.
First print out the tables so we can see the expected shapes.
>>> df_targets.loc[df_targets['ctname'] == 'GPPAllIgnoringNitrogen']
   cmtnum                  ctname  pft  observed cmprt
0       6  GPPAllIgnoringNitrogen    0    11.833   NaN
1       6  GPPAllIgnoringNitrogen    1   197.867   NaN
2       6  GPPAllIgnoringNitrogen    2    42.987   NaN
3       6  GPPAllIgnoringNitrogen    3    10.667   NaN
4       6  GPPAllIgnoringNitrogen    4     3.375   NaN
5       6  GPPAllIgnoringNitrogen    5    16.000   NaN
6       6  GPPAllIgnoringNitrogen    6     6.000   NaN
>>> flat_targets[0:len(d.pftnums)]
[11.833, 197.867, 42.987, 10.667, 3.375, 16.0, 6.0]

Then actually check the data so that we are confident in the output order for
the flat list.
>>> a = flat_targets[0:len(d.pftnums)]
>>> b = df_targets.loc[df_targets['ctname'] == 'GPPAllIgnoringNitrogen']['observed']
>>> all(a == b)
True

Then check on some compartment data. First print out the tables of data so we 
can see the expected shapes.

>>> flat_targets[len(d.pftnums):len(d.pftnums)+3]
[2.0, 4.0, 0.297]
>>> df_targets.loc[ (df_targets['ctname']=='VegCarbon') & (df_targets['pft']==0) ]
   cmtnum     ctname  pft  observed cmprt
7       6  VegCarbon    0     2.000  Leaf
8       6  VegCarbon    0     4.000  Stem
9       6  VegCarbon    0     0.297  Root

Then check the data so that we are confident that we understand the ordering.

>>> a = flat_targets[len(d.pftnums):len(d.pftnums)+3]
>>> b = df_targets.loc[ (df_targets['ctname']=='VegCarbon') & (df_targets['pft']==0) ]['observed']
>>> all(a == b)
True

>>> d.params_vec()
[22.8, 250.6, 65.0, 38.5, 7.8, 21.0, 36.3]

This makes sense because we haven't run the model yet so there are no outputs.

.. comment: 
  # This is going to be tricky to test...need to add a better mechanism to the
  # MadsTEMDriver object for detecting if the model has run and if there is output
  # available....
  # >>> d.modeled_vec()
  # Traceback (most recent call last):
  # ...
  # RuntimeError: Can't find file: /tmp/test_CA/output/INGPP_yearly_eq.nc

>>> d.clean()

>>> d.setup_run_dir()

>>> d.run()

>>> final_data = d.gather_model_outputs()
>>> import pandas as pd
>>> df_finaldata = pd.DataFrame(final_data)
>>> df_finaldata.loc[(df_finaldata['ctname']=='VegCarbon') & (df_finaldata['cmprt']=='Leaf')]
      cmt     ctname      value  truth  pft cmprt
7   CMT06  VegCarbon   2.138998   2.00    0  Leaf
10  CMT06  VegCarbon  42.925257  37.10    1  Leaf
12  CMT06  VegCarbon   0.156739   8.06    2  Leaf
14  CMT06  VegCarbon   2.602119   2.00    3  Leaf
16  CMT06  VegCarbon   2.250932   2.00    4  Leaf
17  CMT06  VegCarbon  22.572059  22.00    5  Leaf
18  CMT06  VegCarbon  22.400614  23.00    6  Leaf

Now check that the observed values that are put in the final output data are
indeed the same as the observed values that are read and setup in the
`self.targets` datastructure before running the model. This is harder because in
the outputs, there are only rows for valid PFT/compartment combos, whereas in 
the targets dataframe, there are rows with zero values for the observations for
PFT/compartment combos that are not defined...for example the Stem and Root 
compartments are not set for Lichen, but in the targets, there are (empty) rows
for them. So here we drop the empty rows, and then compare with the final data.

>>> a = df_targets.loc[ (df_targets['ctname']=='VegCarbon') & (df_targets['pft']==2) ]['observed']
>>> b = df_finaldata.loc[ (df_finaldata['ctname']=='VegCarbon') & (df_finaldata['pft']==2) ]['truth']
>>> all( a[a>0].values == b.values ) 
True
