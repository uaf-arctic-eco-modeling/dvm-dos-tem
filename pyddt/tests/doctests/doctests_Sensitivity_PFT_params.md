
# Testing config with all PFT params

First load some libraries

    >>> import pathlib
    >>> import yaml
    >>> import pyddt.drivers.sensitivity

Next define our config file. Notice that the number of samples is small and the
run years are small. We are just trying to make sure everything loads and runs
here. Also notice that the `work_dir` is set to be `/tmp` so that we don't have 
to remember to clean it up at the end.

    >>> my_yaml_string = """
    ... seed_path: /work/parameters
    ... observations: /work/calibration
    ... N_samples: 5
    ... work_dir: /tmp/testing/output/cmax_gppallignoringnitrogen/sa-N5
    ... params: [cmax, cmax, cmax, cmax, cmax, cmax, cmax]
    ... pftnums: [0, 1, 2, 3, 4, 5, 6]
    ... percent_diffs: [.9, .9, .9, .9, .9, .9, .9]
    ... site: /data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_IMNAVIAT_CREEK_10x10
    ... PXx: 0
    ... PXy: 0
    ... calib_mode: GPPALLIgnoringNitrogen
    ... sampling_method: uniform
    ... target_names: 
    ... - GPPAllIgnoringNitrogen
    ... cmtnum: 6
    ... opt_run_setup: --pr-yrs 5 --eq-yrs 35 --sp-yrs 0 --tr-yrs 0 --sc-yrs 0
    ... """

Read the config data.

    >>> config_dict = yaml.load(my_yaml_string, Loader=yaml.FullLoader)

Make sure the appropriate mid-level directories exist for the `work_dir`.

    >>> pathlib.Path(config_dict['work_dir']).mkdir(parents=True, exist_ok=True)

Now make the Sensitivity object, setup the run directories and do the runs.

    >>> driver = pyddt.drivers.sensitivity.Sensitivity(config_dict)

    >>> # Make sure the mid-level directories exist for the `work_dir`
   
    >>> driver.clean()

    >>> driver.setup_multi() 
    Saving plot /tmp/testing/output/cmax_gppallignoringnitrogen/sa-N5/sample_matrix_distributions.png
    
    >>> driver.run_all_samples()
    <BLANKLINE>

What else should we check?

