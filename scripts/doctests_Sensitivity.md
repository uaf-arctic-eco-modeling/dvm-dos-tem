# Basic testing of Sensitivity.py module

This file is intended to both exercise the basic functionality of the
Sensitivity Analaysis process and to demonstrage the API. An end user would not
be expected to follow these steps exactly, but should be able to read along with
the tests here and see how Sensitivity.py might be used.

The general idea with the the sensitivity analysis is to run the model a number
of times, each time with a different parameter value and then look at the
outputs and see which parameter most influences the outputs. To accomplish this,
Sensitivity.py provides a `SensitivityDriver` class which helps setup, organize
and carry out the runs.

## Get started

Load the library

    >>> import Sensitivity

Instantiate an object

    >>> sd = Sensitivity.SensitivityDriver()

See what the working directory is. It should be nothing as we have not set
anything up yet:

    >>> print(type(sd.work_dir), sd.work_dir)
    <class 'NoneType'> None

Set the working directory to a temporary location for this sample run.

    >>> sd.work_dir = '/tmp/tests-Sensitivity'

There are two ways to setup an experiment. You can use the `design_experiment`
convienience function or do it manually. Lets start by using the convienience
function for an experiment that looks at the sensitivity of both PFT parameter
and non-PFT parameters. The first argument for the convenience function is for
the number of samples in the experiment (rows in the sensitivity matrix) and the
second argument is for the CMT number to work with.

> Note: What happens if there is already data in the `work_dir`? You will get a
> `RuntimeError` indicating that you should run the `.clean()` method before
> continuing.

    >>> import os
    >>> import pathlib

Make a junk file at in the driver's working directory:

    >>> pathlib.Path("/tmp/tests-Sensitivity/some/path/to/junkdirectory").mkdir(parents=True, exist_ok=True)

And then try running the convienience function. It should fail with an
exception.

    >>> sd.design_experiment(5, 4,
    ...   params=['cmax','rhq10','nfall(1)'],
    ...   pftnums=[2,None,2], 
    ...   sampling_method='lhc')
    Traceback (most recent call last):
      ...
    RuntimeError: SensitivityDriver.work_dir is not empty! You must run SensitivityDriver.clean() before designing an experiment.

So first we should clean up, then try making the experiment.

    >>> sd.clean()
    >>> sd.design_experiment(5, 4,
    ...   params=['cmax','rhq10','nfall(1)'],
    ...   pftnums=[2,None,2], 
    ...   sampling_method='lhc')

The driver object has methods for retrieving the pft and cmt being used for this
driver: 

    >>> sd.pftnum()
    2
    >>> sd.cmtnum()
    4

Lets just verify again where the experiment is being stored:

    >>> sd.work_dir
    '/tmp/tests-Sensitivity'

Clean the working directory of any existing data so that the next tests
have predictable output.

    >>> sd.clean()

If you should like to "export" an experiment for later use or examination in
another program, you can "save" the experiment design using a convenience
function that will write the sample matrix and parameter properties out to
files. This function writes two `.csv` files to the `SensitivityDriver.work_dir`
folder. One file describes the `param_props` dictionary, and the other file
holds the sample matrix data. In addition, there is a file called info.txt that
contains the sampling method used to generate the sampling matrix.

    >>> sd.save_experiment()

See what we got:

    >>> import os
    >>> sorted(os.listdir(sd.work_dir))
    ['info.txt', 'param_props.csv', 'sample_matrix.csv']

Now see if we can load the experiment again into a new driver:

    >>> sd2 = Sensitivity.SensitivityDriver()

This new driver should not have its `work_dir` set:

    >>> print(sd2.work_dir)
    None

Now we can load an experiment that has already been setup (and saved) into this
driver by passing paths to the required files for loading:

    >>> sd2.load_experiment(os.path.join(sd.work_dir, 'param_props.csv'), 
    ...                     os.path.join(sd.work_dir, 'sample_matrix.csv'),
    ...                     os.path.join(sd.work_dir, 'info.txt'))

Lets make sure that loading the experiment from files results in a
SensitivityDriver object with the same sample matrix, parameters, and other
attributes.

    >>> sd.params == sd2.params
    True

    >>> sd.sample_matrix.round(9).equals(sd2.sample_matrix.round(9))
    True

    >>> sd.sampling_method == sd2.sampling_method
    True

    >>> sd.cmtnum() == sd2.cmtnum()
    True

    >>> sd.pftnum() == sd2.pftnum()
    True

We won't be using the second driver object, so we can delete it.

    >>> del(sd2)

And lets cleanup the original driver's working directory before moving on:

    >>> sd.clean()

Now that the save/load functionality has been tested we can go back to testing
the main functionality of the driver. We'll start by setting up a small
experiment and running it. We already have designed our experiment, so the
driver object has a list of parameters to modify and has generated a sample
matrix from the parameter specifications. But in order to run the analysis we
need to have a dedicated folder for each of the runs. Each run folder should
have in it parameter files with the modified parameter values. The
`SensitivityDriver` object provides a funciton for creating and populating these
directories:

    >>> sd.setup_multi()

After this runs, we should have, within the `work_dir`, a bunch of new folders.
There should be one folder for each sample run (row in the sample matrix) and
one folder for the intial value run as well as the files that are written when
the experiment is saved:

    >>> sorted(os.listdir(sd.work_dir))
    ['info.txt', 'initial_value_run', 'param_props.csv', 'sample_000000000', 'sample_000000001', 'sample_000000002', 'sample_000000003', 'sample_000000004', 'sample_matrix.csv']

If we try to run the setup function again, it will fail complaining about output
that may already exists. 

    >>> sd.setup_multi()
    Traceback (most recent call last):
      ...
    RuntimeError: SensitivityDriver.work_dir is not empty! You must run SensitivityDriver.clean() before designing an experiment.

Use the `force` argument to proceed and overwrite any existing files.

> NOTE: Be careful with the `force` argument as it will forcibly remove entire
> directory trees without hesitation. You could accidentally delete a lot of
> stuff if you are not careful!
    
    >>> sd.setup_multi(force=True)

Should have the same files we had the first time:

    >>> sorted(os.listdir(sd.work_dir))
    ['info.txt', 'initial_value_run', 'param_props.csv', 'sample_000000000', 'sample_000000001', 'sample_000000002', 'sample_000000003', 'sample_000000004', 'sample_matrix.csv']

First we can spot check a couple parameter values in the sample folders to see
that they were set according to the sample matrix:

    >>> import param_util as pu
    >>> idx = 0
    >>> pfile = os.path.join(sd._ssrf_name(idx), "parameters/cmt_calparbgc.txt")
    >>> data = pu.get_CMT_datablock(pfile, sd.cmtnum())
    >>> dd = pu.cmtdatablock2dict(data)
    >>> print("Value as set in file:", round(dd["pft{}".format(sd.pftnum())]["cmax"], 3))
    Value as set in file: 63.537
    >>> print("Value as set in sample_matrix:", sd.sample_matrix.cmax[idx].round(3))
    Value as set in sample_matrix: 63.537

We could get fancy and write some loops to check all the rest of the parameters
and sample folders but for now, we'll assume its working.

The next step will be checking that running the samples works. At this time this
is not practical because there is still too much data being printed to stdout to
make the `doctest`s easy to write.





