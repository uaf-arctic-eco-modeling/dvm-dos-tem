# Basic testing of Sensitivity.py module

## Basic SA run

Load the library

    >>> import Sensitivity

Instantiate an object

    >>> sd = Sensitivity.SensitivityDriver()

Setup an experiment, with pft and non-pft params. Since 'rhq10' is a non-pft parameter we assign 'None' to its pftnum.
    
    >>> sd.design_experiment(nsamples=5, pftnum=4, 
                             params=['cmax','rhq10','nmax'],
                             pftnums=[0,None,0]
                             percent_diffs=[.5, .2, 0.1],
                             sampling_method='lhc')

Check the info

    >>> sd.info()
    Sampling method: lhc
    --- Setup ---
    work_dir: /data/workflows/sensitivity_analysis
    site: /data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_CALM_Toolik_LTER_10x10/
    pixel(y,x): (0,0)
    cmtnum: 4
    pftnum: 0 (Salix)

    --- Parameters ---
        name          bounds  initial  cmtnum pftnum
    0   cmax  [105.0, 315.0]      210       4    0.0
    1  rhq10      [1.6, 2.4]        2       4       
    2   nmax      [5.4, 6.6]        6       4    0.0

    --- Sample Matrix ---
    sample_matrix shape: (10, 3)

    --- Outputs ---
    > NOTE - these may be leftover from a prior run!
    found 1 existing sensitivity csv files.

Save parameters and sampling matrix in the workflows folder

    >>> driver.save_experiment('/data/workflows/')

Makes directories, sets config files, input data, etc for each run
    
    >>> driver.setup_multi()

Carry out the run and do initial output collection

    >>> driver.run_all_samples()

Process the data (creates the sensitivity.csv files)

    >>> driver.extract_data_for_sensitivity_analysis()
    >>> print('')
    >>> print('SUCCESS! Sensitivity analysis is finished!')

## Additional functionality

Retrieve the pft and cmt being used for this driver 

    >>> sd.pftnum()
    2
    >>> sd.cmtnum()
    4

See where the experiment is being stored:

    >>> sd.work_dir
    '/data/workflows/sensitivity_analysis'

Save an experiment. This

    >>> sd.save_experiment()

See what we got:

    >>> import os
    >>> os.listdir(sd.work_dir)
    ['sample_matrix.csv', 'param_props.csv']

## Retrive previous SA run for further analysis

Now see if we can load the experiment again into a new driver:

    >>> sd2 = Sensitivity.SensitivityDriver()
    >>> sd2.load_experiment(os.path.join(sd2.work_dir, 'param_props.csv'), 
                            os.path.join(sd2.work_dir, 'sample_matrix.csv'))

And make sure the new object has the same stuff as the original object:

    >>> sd.params == sd2.params
    True

    >>> sd.sample_matrix.round(9).equals(sd2.sample_matrix.round(9))
    True

Get the SA matrix using last time step. This function will get the sample matrix.

    >>> inout = sd.get_SA_correlation_matrix()

Get the SA time-series matrix for a desired output variable. This function will not get the sample matrix.

    >>> res = sd.get_SA_time_series('VEGC')
