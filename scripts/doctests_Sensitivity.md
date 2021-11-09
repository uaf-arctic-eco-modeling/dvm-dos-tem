# Basic testing of Sensitivity.py module

Load the library

    >>> import Sensitivity

Instantiate an object

    >>> sd = Sensitivity.SensitivityDriver()

Setup an experiment, with pft and non-pft params
    
    >>> sd.design_experiment(5, 4, params=['cmax','rhq10','nfall(1)'], pftnums=[2,None,2])

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

Save an experiment. This

    >>> sd.save_experiment()

See what we got:

    >>> import os
    >>> os.listdir(sd.work_dir)
    ['sample_matrix.csv', 'param_props.csv']

Now see if we can load the experiment again into a new driver:

    >>> sd2 = Sensitivity.SensitivityDriver()
    >>> sd2.load_experiment(os.path.join(sd2.work_dir, 'param_props.csv'), os.path.join(sd2.work_dir, 'sample_matrix.csv'))

And make sure the new object has the same stuff as the original object:

    >>> sd.params == sd2.params
    True

    >>> sd.sample_matrix.round(9).equals(sd2.sample_matrix.round(9))
    True

Next steps will be testing the `sd.setup_multi()` function but right
now this will fail because the function has lots of stdout that is not
suppressed and therefore messes with the doctests module.
    