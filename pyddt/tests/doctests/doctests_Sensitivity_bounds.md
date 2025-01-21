
# Testing config with different parameter bounds settings.

Trying to test different ways the user may setup parameter bounds.
(percent_diffs, or p_bounds)

First load some libraries

    >>> import pathlib
    >>> import yaml
    >>> import drivers.Sensitivity

Next define our config file. Notice that the number of samples is small and the
run years are small. We are just trying to make sure everything loads and runs
here. Also notice that the `work_dir` is set to be `/tmp` so that we don't have 
to remember to clean it up at the end.

    >>> my_yaml_string = """
    ... seed_path: /work/parameters
    ... observations: /work/calibration # (also called targets)
    ... N_samples: 5
    ... work_dir: /tmp/nmax_krb_npp/sa-N5
    ... site: /data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_IMNAVIAT_CREEK_10x10
    ... PXx: 0
    ... PXy: 0
    ... calib_mode: OFF
    ... sampling_method: uniform
    ... target_names: [ NPPAll ]
    ... cmtnum: 6
    ... opt_run_setup: --pr-yrs 5 --eq-yrs 35 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0
    ... params: [nmax, nmax, nmax, nmax, nmax, nmax, nmax,
    ...          krb(0), krb(0), krb(0), krb(0), krb(0), krb(0), krb(0),
    ...          krb(1), 
    ...          krb(2), krb(2), krb(2), krb(2)]
    ... pftnums: [0, 1, 2, 3, 4, 5, 6,
    ...           0, 1, 2, 3, 4, 5, 6,
    ...           0,
    ...           0, 1, 2, 3]
    ... p_bounds: [[-100,200],[-100,200],[-100,200],[-100,200],[-100,200],[-100,200],[-100,200],
    ...            [-100,200],[-100,200],[-100,200],[-100,200],[-100,200],[-100,200],[-100,200],
    ...            [-100,200],
    ...            [-100,200],[-100,200],[-100,200],[-100,200]]    
    ... """
    

Read the config data.

    >>> config_dict = yaml.load(my_yaml_string, Loader=yaml.FullLoader)

Make sure the appropriate mid-level directories exist for the `work_dir`.

    >>> pathlib.Path(config_dict['work_dir']).mkdir(parents=True, exist_ok=True)

Make the driver object.

    >>> driver = drivers.Sensitivity.Sensitivity(config_dict)

Onece the driver is made we can look at the params and see that the bounds are 
set to the values specified.

    >>> for p in driver.params:
    ...     print(p['name'], p['pftnum'], p['bounds'])
    ...
    nmax 0 [-100, 200]
    nmax 1 [-100, 200]
    nmax 2 [-100, 200]
    nmax 3 [-100, 200]
    nmax 4 [-100, 200]
    nmax 5 [-100, 200]
    nmax 6 [-100, 200]
    krb(0) 0 [-100, 200]
    krb(0) 1 [-100, 200]
    krb(0) 2 [-100, 200]
    krb(0) 3 [-100, 200]
    krb(0) 4 [-100, 200]
    krb(0) 5 [-100, 200]
    krb(0) 6 [-100, 200]
    krb(1) 0 [-100, 200]
    krb(2) 0 [-100, 200]
    krb(2) 1 [-100, 200]
    krb(2) 2 [-100, 200]
    krb(2) 3 [-100, 200]

