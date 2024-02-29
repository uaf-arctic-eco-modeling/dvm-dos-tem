
# Testing config with calib mode

Here we are checking that the user can pass a varierly of forms of
"GPPAllIgnoringNitrogen" as the key word for ``calib_mode`` and get the desired
result (``dsl`` and ``nfeed`` being turned off).

First load some libraries

    >>> import pathlib
    >>> import yaml
    >>> import json
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
    ... site: /work/testing-data/inputs/cru-ts40_ar5_rcp85_ncar-ccsm4_IMNAVIAT_CREEK_10x10
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
    ... percent_diffs: [.9, .9, .9, .9, .9, .9, .9,
    ...                 .9, .9, .9, .9, .9, .9, .9,
    ...                 .9,
    ...                 .9, .9, .9, .9]    
    ... """

Read the config data.

    >>> config_dict = yaml.load(my_yaml_string, Loader=yaml.FullLoader)

Make sure the appropriate mid-level directories exist for the `work_dir`.

    >>> pathlib.Path(config_dict['work_dir']).mkdir(parents=True, exist_ok=True)

Now make the Sensitivity object, setup the run directories and do the runs.

    >>> driver = drivers.Sensitivity.Sensitivity(config_dict)

    >>> driver.clean()

    >>> driver.setup_multi() 
    Saving plot /tmp/nmax_krb_npp/sa-N5/sample_matrix_distributions.png

``dsl`` and ``nfeed`` should be ON:

    >>> configs = [path for path in pathlib.Path(driver.work_dir).rglob('config.js')]
    >>> for f in configs:
    ...   with open(f) as ff:
    ...     cfg = json.load(ff)
    ...     nfeed = cfg['stage_settings']['eq']["nfeed"]
    ...     dsl = cfg['stage_settings']['eq']['dsl'] 
    ...     print(dsl, nfeed) 
    True True
    True True
    True True
    True True
    True True
    True True

Now set ``calib_mode``, using a totally whacky case, and ``dsl`` and ``nfeed`` 
should be OFF:

    >>> driver.calib_mode = 'GppAlLignoringNitroGen'
    >>> driver.clean()
    >>> driver.setup_multi() 
    Saving plot /tmp/nmax_krb_npp/sa-N5/sample_matrix_distributions.png
    >>> configs = [path for path in pathlib.Path(driver.work_dir).rglob('config.js')]
    >>> for f in configs:
    ...   with open(f) as ff:
    ...     cfg = json.load(ff)
    ...     nfeed = cfg['stage_settings']['eq']["nfeed"]
    ...     dsl = cfg['stage_settings']['eq']['dsl'] 
    ...     print(dsl, nfeed)
    False False
    False False
    False False
    False False
    False False
    False False