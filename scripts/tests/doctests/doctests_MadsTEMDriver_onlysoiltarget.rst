# Testing, developing and describing the interface for MadsTEMDriver.py
=========================================================================

Testing for using only a soil target. No PFTs, no compartments. This primarily
makes sure that the interface can handle situation with only soil targets are
specified.

>>> import yaml

>>> my_yaml_string = """
... work_dir: /tmp/test_CA
... site: /work/testing-data/inputs/cru-ts40_ar5_rcp85_ncar-ccsm4_IMNAVIAT_CREEK_10x10
... PXx: 0
... PXy: 0
... calib_mode: GPPAllIgnoringNitrogen
... target_names: 
... - CarbonShallow
... cmtnum: 6
... opt_run_setup: --pr-yrs 5 --eq-yrs 10 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0
... params:
... - cmax
... - cmax
... - cmax
... pftnums:
... - 0
... - 1
... - 2
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

> Notice here that the `MadsTEMDriver.targets` datastructure includes **all**
the target data that is included for that CMT (loaded from the
calibration_targets.py file). In most cases, we are only interested in working
with a certain subset of the target data - namely those targets that are
specified in the config yaml. So the `MadsTEMDriver.observed_vec(..)` function
is provided that can return only the targets of interest. 

>>> import pandas as pd

>>> flat_targets = d.observed_vec(format='flat')

>>> df_targets = pd.DataFrame(d.observed_vec(format='labeled'))

If we check a for a target that is not specified, we should get nothing:

>>> df_targets.loc[df_targets['ctname'] == 'GPPAllIgnoringNitrogen']
Empty DataFrame
Columns: [cmtnum, ctname, observed]
Index: []

>>> flat_targets
[3358.0]

>>> df_targets
   cmtnum         ctname  observed
0       6  CarbonShallow    3358.0

>>> d.params_vec()
[22.8, 250.6, 65.0]

This makes sense because we haven't run the model yet so there are no outputs.

>>> d.clean()

>>> d.setup_run_dir()

>>> d.run()

>>> d.gather_model_outputs()
[{'cmt': 'CMT06', 'ctname': 'CarbonShallow', 'value': 3193.170117276907, 'truth': 3358.0}]

