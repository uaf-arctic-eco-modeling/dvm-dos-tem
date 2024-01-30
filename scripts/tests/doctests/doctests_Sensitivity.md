# Basic testing of Sensitivity.py module

This file is intended to both exercise the basic functionality of the
Sensitivity Analysis process and to demonstrate the API. An end user would not
be expected to follow these steps exactly, but should be able to read along with
the tests here and see how Sensitivity.py might be used.

The general idea with the the sensitivity analysis is to run the model a number
of times, each time with a different parameter value and then look at the
outputs and see which parameter most influences the outputs. To accomplish this,
Sensitivity.py provides a `Sensitivity` class which helps setup, organize and
carry out the runs. The `Sensitivity` class inherits from a `BaseDriver` class
that provides a lot of the common operations amongst drivers.

## Get started

Load the library

    >>> import drivers.Sensitivity

In order to conduct a sensitivity analysis we must consider the following:

 - the location where the runs and outputs will be stored
 - the source for the initial parameter values (seed values)
 - the list of parameters that should be tested
 - for each parameter, which PFT should be tested
 - the community type that should be analyzed
 - the scheme by which to modify parameter values (sampling stragegy and bounds)
 - the outputs variables upon which the analysis will be conducted

The driver object constructor requires a configuration dict which allows for
providing data to answer the above questions.
 
    >>> config_dict = dict(
    ... site='/work/demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10',
    ... PXx=0, PXy=0, 
    ... params=['cmax', 'cmax'], 
    ... pftnums=[0,1],
    ... sampling_method='uniform',
    ... seed_path='/work/parameters',
    ... cmtnum=6,
    ... N_samples=10
    ... )
    >>> sd = drivers.Sensitivity.Sensitivity(config=config_dict)

The `Sensitivity` object has properties and methods that will allow us to
further address the issues outlined above so that we can setup and conduct an
anlysis.

> NOTE: at present the module is under construction, and not all of the above
> concerns are easily modified with the API. 

The `Sensitivity` object has the concept of a "working directory", and a
"seed path". The working directory is the folder where all the runs will be
setup and carried out. Each run will have its own folder which holds the
run-specific configuration, parameters, and output files. There is one special
run folder named the `initial_params_run_dir` which holds the run with the
intial parameter values. The parameter values in the `initial_params_run_dir`
are set from the `seed_path`. Each of the other run directories within the
working directory has parameter values that vary according to the data in the
`sample_matrix`. The values in the `sample_matrix` are set based on:

 - the seed values, 
 - the parameters and PFTs under analysis,
 - the sampling scheme, and 
 - the bounds.

> NOTE: The paths given here for site, seed path and work dir assume that you
> are working inside the docker containers for the project.

If the working directory is not passed to the `Sensitivity` constructor,
then there is no directory set.

    >>> print(type(sd.work_dir), sd.work_dir)
    <class 'NoneType'> None

Here, we will set the working directory to a temporary location for this sample
run.

    >>> sd.set_work_dir('/tmp/tests-Sensitivity')
    
    >>> print(sd.work_dir)
    /tmp/tests-Sensitivity

At this point we can see the folder where the initial paramter values will be
held, but there are no files there yet because we have not set the seed path:

    >>> print(sd.get_initial_params_dir())
    /tmp/tests-Sensitivity/initial_params_run_dir

Here we go ahead and set the seed path.

    >>> sd.set_seed_path('/work/parameters')

If you investigate your files you will still find that there is nothing in the
working directory. Nothing has been setup yet, no folders have been created, and
no parameters set or copied. We have simply told the `Sensitivity` where
we would like the files to go, but we haven't actually initialized anything yet.

To finish setting up the experiment we need to create the `sample_matrix` and
have all the individual sample run directories be setup with the correct
parameter values from the sample matrix. In addition, the
`initial_params_run_dir` should be setup with parameter values from the
`seed_path`. All the runs should have common configuration in terms of which
pixel to run, which outputs are enabled, how many years to run, etc. 

Lets start by using the convienience function for setting up an experiment that
looks at the sensitivity of both PFT parameter and non-PFT parameters. There is
a convenience funciton, `design_experiment`, that helps with configuring your
run. The function takes 5 arguments:

 - `Nsamples`: the number of rows in the sample matrix (number of runs to do)
 - `cmtnum`: which community type to work with
 - `params`: a list of parameter names to analyze
 - `pftnums`: a list, same length as `params`, of the PFT numbers to work with
   for each parameter, None for non-PFT parameters, nested list for multiple
   PFTs per parameter.
 - `sampling_method`: a string specifying a sampling method for determining
   parameter values.

> NOTE: What happens if there is already data in the `work_dir`? You will get a
> `RuntimeError` indicating that you should run the `.clean()` method before
> continuing.
> 
>     >>> import os
>     >>> import pathlib
> 
> Make a junk file in the driver's working directory:
>
>     >>> pathlib.Path("/tmp/tests-Sensitivity/some/path/to/junkdirectory").mkdir(parents=True, exist_ok=True)
> 
> And then try running the convienience function. It should fail with an
> exception.
> 
>     >>> sd.design_experiment(5, 4, params=['cmax'], pftnums=[2], 
>     ...                      sampling_method='lhc')
>     Traceback (most recent call last):
>       ...
>     RuntimeError: Sensitivity.work_dir is not empty! You must run Sensitivity.clean() before designing an > experiment.
>
> For this purpose there is a function for cleaning up:
>
>     >>> sd.clean()

First we should clean up, then try making the experiment.

    >>> sd.clean()
    >>> sd.design_experiment(5, 4,
    ...   params=['cmax','rhq10','nfall(1)'],
    ...   pftnums=[1,None,3], 
    ...   sampling_method='lhc')

The above experiment will modify parameters for `cmax` PFT 1, `nfall(1)` PFT 3,
and `rhq10`, which is a soil parameter, so not connected to a specific PFT.

The driver object has methods for retrieving the cmt being used for this
driver: 

    >>> sd.cmtnum
    4

And now we can see that the `sample_matrix` is a Pandas DataFrame:

    >>> print(type(sd.sample_matrix))
    <class 'pandas.core.frame.DataFrame'>

And that the shape is as we expect - 5 rows, and 3 columns:

    >>> print(sd.sample_matrix.shape)
    (5, 3)

> NOTE: Utility function for generating a list of parameter specifications from
> a seed path:
> 
>     >>> Sensitivity.params_from_seed(seedpath='/work/parameters', 
>     ...    params=['rhq10','cmax'],
>     ...    pftnums=[None,1],
>     ...    percent_diffs=[.4, .1],
>     ...    cmtnum=5)
>     [{'name': 'rhq10', 'bounds': [1.2, 2.8], 'initial': 2.0, 'cmtnum': 5, 'pftnum': None}, {'name': 'cmax', 'bounds': [54.0, 66.0], 'initial': 60.0, 'cmtnum': 5, 'pftnum': 1}]
>
> This function simply returns a list of "parameter specification" dictionaries
> that map parameter names to initial values and bounds, which have been
> determined from the values in the `seed_path`.

Lets just verify again where the experiment is being stored:

    >>> sd.work_dir
    '/tmp/tests-Sensitivity'

Clean the working directory of any existing data so that the next tests
have predictable output.

    >>> sd.clean()

If you should like to "export" an experiment for later use or examination in
another program, you can "save" the experiment design using a convenience
function that will write the sample matrix and parameter properties out to
files. This function writes two `.csv` files to the `Sensitivity.work_dir`
folder. One file describes the `param_props` dictionary, and the other file
holds the sample matrix data. In addition, there is a file called info.txt that
contains the sampling method used to generate the sampling matrix.

    >>> sd.save_experiment()

See what we got:

    >>> import os
    >>> sorted(os.listdir(sd.work_dir))
    ['info.txt', 'param_props.csv', 'sample_matrix.csv']

Now see if we can load the experiment again into a new driver. In this case we
provide a bunch of garbage in the config dict because we are assuming it will
be overwritten when we run the ``load_experiment`` function on the new driver.

    >>> junk_config = dict(
    ... site='/junk',
    ... PXx=0, PXy=0, 
    ... params=['krb(0)', 'micbnup'], 
    ... pftnums=[6,7],
    ... sampling_method='lhc',
    ... seed_path='/work/parameters',
    ... cmtnum=2,
    ... N_samples=1
    ... )
    >>> sd2 = drivers.Sensitivity.Sensitivity(config=junk_config)

This new driver should not have its `work_dir` set:

    >>> print(sd2.work_dir)
    None

Now we can load an experiment that has already been setup (and saved) into this
driver by passing paths to the required files for loading:

    >>> sd2.load_experiment(os.path.join(sd.work_dir, 'param_props.csv'), 
    ...                     os.path.join(sd.work_dir, 'sample_matrix.csv'),
    ...                     os.path.join(sd.work_dir, 'info.txt'))

Lets make sure that loading the experiment from files results in a
Sensitivity object with the same sample matrix, parameters, and other
attributes.

    >>> sd.params == sd2.params
    True

    >>> sd.sample_matrix.round(9).equals(sd2.sample_matrix.round(9))
    True

    >>> sd.sampling_method == sd2.sampling_method
    True

    >>> sd.cmtnum == sd2.cmtnum
    True

We won't be using the second driver object, so we can delete it.

    >>> del(sd2)

And lets cleanup the original driver's working directory before moving on:

    >>> sd.clean()

Now that the save/load functionality has been tested we can go back to testing
the main functionality of the driver. We'll start by setting up a small
experiment and running it. We already have designed our experiment, so the
driver object has a list of parameters to modify and has generated a sample
matrix from the parameter specifications. An additional piece of setup remains:
setting the targets values and turning on the appropriate model outputs so that
a comparison with the targets is possible. Targets are stored in a special
python file named `calibration_targets.py`. This is a python file with a
dictionary datastructure holding the target values. For this experiment, we will
use the default target set that comes with the repository. THis function loads
up all the targets for the driver's cmt number.

    >>> sd.load_target_data('/work/calibration')

The next step is to setup the output variables that the model runs should
produce. The helper function used below takes a list of target names and assumes
that you want the corresponding NetCDF outputs to be enabled so that you can
compare the model outputs with the target values to check model performance.

    >>> sd.setup_outputs(['GPPAllIgnoringNitrogen', 'VegCarbon']) 

Finally, to actually run the mode (in parallel) each run needs to have a
dedicated folder to run in. Each run folder should have in it
parameter files with the modified parameter values. The `Sensitivity`
object provides a funciton for creating and populating these directories:

    >>> sd.setup_multi()
    Saving plot /tmp/tests-Sensitivity/sample_matrix_distributions.png

After this runs, we should have, within the `work_dir`, a bunch of new folders.
There should be one folder for each sample run (row in the sample matrix) and
one folder for the intial value run as well as the files that are written when
the experiment is saved:

    >>> sorted(os.listdir(sd.work_dir))
    ['info.txt', 'initial_params_run_dir', 'param_props.csv', 'sample_000000000', 'sample_000000001', 'sample_000000002', 'sample_000000003', 'sample_000000004', 'sample_matrix.csv', 'sample_matrix_distributions.png']

If we try to run the setup function again, it will fail complaining about output
that may already exists. 

    >>> sd.setup_multi()
    Traceback (most recent call last):
      ...
    RuntimeError: Sensitivity.work_dir is not empty! You must run Sensitivity.clean() before designing an experiment.

Use the `force` argument to proceed and overwrite any existing files.

> NOTE: Be careful with the `force` argument as it will forcibly remove entire
> directory trees without hesitation. You could accidentally delete a lot of
> stuff if you are not careful!
    
    >>> sd.setup_multi(force=True)
    Saving plot /tmp/tests-Sensitivity/sample_matrix_distributions.png

Now we should have the same files we had the first time:

    >>> sorted(os.listdir(sd.work_dir))
    ['info.txt', 'initial_params_run_dir', 'param_props.csv', 'sample_000000000', 'sample_000000001', 'sample_000000002', 'sample_000000003', 'sample_000000004', 'sample_matrix.csv', 'sample_matrix_distributions.png']

With all the sample directories setup, we can now spot check a couple parameter
values in the sample folders to see that they were set according to the sample
matrix.

> NOTE: A user of the`SensitivtyDriver` object will not need to perform the
> following steps, they are here as a test of the module to make sure that the
> sample folders are being setup correctly.

    >>> # Read the data in sample folder's parameter file
    >>> import util.param
    >>> idx = 0
    >>> pfile = os.path.join(sd._ssrf_name(idx), "parameters/cmt_calparbgc.txt")
    >>> data = util.param.get_CMT_datablock(pfile, sd.cmtnum)
    >>> dd = util.param.cmtdatablock2dict(data)

    >>> # get the correct param spec out of the params list
    >>> PS = [pdict for pdict in sd.params if pdict['name'] == 'cmax'][0]
    >>> colname = 'cmax_pft{}'.format(PS['pftnum'])
    >>> value_from_sample_matrix = sd.sample_matrix[colname][idx].round(3)
    >>> value_from_sample_run_folder = round(dd["pft{}".format(PS['pftnum'])]["cmax"], 3)
    >>> value_from_sample_matrix == value_from_sample_run_folder
    True

    >>> print("Value from run folder: {}".format(value_from_sample_run_folder))
    Value from run folder: 337.141
    >>> print("Value from sample matrix: {}".format(value_from_sample_matrix))
    Value from sample matrix: 337.141

We could get fancy and write some loops to check all the rest of the parameters
and sample folders but for now, we'll assume its working.

    >>> # Clean up
    >>> del(sd)

# Check multi-pft functionality

Next we can check that the multi-PFT functionality works:

    >>> sd = drivers.Sensitivity.Sensitivity(config=config_dict)
    >>> sd.set_work_dir('/tmp/tests-Sensitivity')
    >>> sd.set_seed_path('/work/parameters')

Here we are going to setup an experiment where `nfall(1)` is modified for 3
different PFTs.

    >>> sd.clean()
    >>> sd.design_experiment(6, 5,
    ...   params=['cmax','rhq10','nfall(1)'],
    ...   pftnums=[1,None,[0,2,5]], 
    ...   sampling_method='lhc')

In this case we expect the sample matrix to have 6 rows, and 5 columns:

    >>> sd.sample_matrix.shape
    (6, 5)

# Check runs

The next step will be checking that running the samples works. At this time this
is not practical because there is still too much data being printed to stdout to
make the `doctest`s easy to write.





