<!-- # Testing the seed path

This is designed to test that the seed path concept is being honored in the
driver classes. For example it is expected that if user sets the seed path
and then runs the method(s) that sets up the run directory(s), the parameters
in the run directory(s) will be from the seed.

To run these tests make sure you have access to the testing data. The testing
data is stored in the project's `testing-data/` directroy. It is tracked with
Git LFS so you may need to fetch the files locally before you begin ()


    >>> site = 'testing-data/inputs/cru-ts40_ar5_rcp85_mri-cgcm3_NEON_Healy_10x10'
    >>> sa_config = dict(
    ... work_dir='/tmp/someplace',
    ... site=site,
    ... PXx=0, PXy=0, 
    ... params=['cmax', 'cmax'], 
    ... pftnums=[0,1],
    ... sampling_method='uniform',
    ... seed_path='testing-data/parameters_CMT01',
    ... cmtnum=1,
    ... N_samples=3
    ... )

    >>> import drivers.Sensitivity
    >>> d = drivers.Sensitivity.Sensitivity(config=sa_config, clean=True)
    >>> d.load_target_data('/work/calibration')
    >>> d.setup_outputs(['GPPAllIgnoringNitrogen'])
    >>> print(d._seedpath)
    >>> d.setup_multi()
    
Now the parameters in each sample directory should be the same as the parameters
in the seed with the exception of the parameters specified to be modified as
part of the analysis.

Spot check a few:

    >>> pass -->