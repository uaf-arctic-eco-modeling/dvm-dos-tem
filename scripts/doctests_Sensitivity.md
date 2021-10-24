# Basic testing of Sensitivity.py module

Load the library

    >>> import Sensitivity

Instantiate an object

    >>> sd = Sensitivity.SensitivityDriver()

Setup an experiment, with pft and non-pft params
    
    >>> sd.design_experiment(nsamples=5, pftnum=4, 
                             params=['cmax','rhq10','nmax'],
                             pftnums=[2,None,2]
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

Now see if we can load the experiment again into a new driver:

    >>> sd2 = Sensitivity.SensitivityDriver()
    >>> sd2.load_experiment(os.path.join(sd2.work_dir, 'param_props.csv'), 
                            os.path.join(sd2.work_dir, 'sample_matrix.csv'))

And make sure the new object has the same stuff as the original object:

    >>> sd.params == sd2.params
    True

    >>> sd.sample_matrix.round(9).equals(sd2.sample_matrix.round(9))
    True

    
