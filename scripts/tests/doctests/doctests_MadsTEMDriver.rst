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

>>> d.observed_vec()
[11.833, 197.867, 42.987, 10.667, 3.375, 16.0, 6.0]

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

.. 
  >>> #pd.DataFrame(final_data)
  >>> #print(final_data)
  >>> #print(d.params)

