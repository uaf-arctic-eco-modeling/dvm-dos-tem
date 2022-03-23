# Basic testing of Sensitivity.py module

Load the library
   
    >>> import Sensitivity

Instantiate an object

    >>> sd = Sensitivity.SensitivityDriver()

Setup an experiment, with pft and non-pft params
    
    >>> sd.design_experiment(5, 4, params=['cmax','rhq10','nfall(1)'], pftnums=[2,None,2])
    Sampling method: lhc

Retrieve the pft and cmt being used for this driver 

    >>> sd.pftnum()
    2
    >>> sd.cmtnum()
    4

See where the experiment is being stored:

    >>> sd.work_dir
    '/data/workflows/sensitivity_analysis'

Clean the working directory of any existing data so that the next tests
have predictable output.

    >>> sd.clean()

Setup run cycles

    >>> sd.opt_run_setup = '-p 1 -e 1 -s 1 -t 1 -n 1'

Save an experiment. This

    >>> sd.save_experiment('test')

    