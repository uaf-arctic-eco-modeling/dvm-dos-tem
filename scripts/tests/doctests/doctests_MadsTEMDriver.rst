# Testing, developing and describing the interface for MadsTEMDriver.py
=========================================================================

>>> import yaml

>>> my_yaml_string = """
work_dir: /tmp/test_CA
site: /data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_IMNAVIAT_CREEK_10x10
calib_mode: GPPAllIgnoringNitrogen
target_names: 
- GPPAllIgnoringNitrogen
- VegCarbon
cmtnum: 6
opt_run_setup: --pr-yrs 10 --eq-yrs 25 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0
params:
- cmax
- cmax
- cmax
- cmax
- cmax
- cmax
- cmax
pftnums:
- 0
- 1
- 2
- 3
- 4
- 5
- 6
"""

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

>>> #d.clean()

>>> #d.setup_run_dir()

>>> #d.run_wrapper()

>>> final_data = d.gather_model_outputs()
>>> import pandas as pd
>>> pd.DataFrame(final_data)
>>> print(final_data)

