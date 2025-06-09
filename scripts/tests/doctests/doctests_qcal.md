# Basic testing of the `qcal.py` tool

The `qcal.py` tool is an attempt at "Quantitative Calibration". The idea is to
measure the discrepancy between target values and model outputs. The tool allows
for the measurement to be done on either the calibraiton json files or the
model's standard NetCDF output files.

There is a command line interface to the `qcal.py` script or it may be used as a
module.

The tests here will use the module form and test the `QCal` object. The command
line interface for the most part provides a convenient way to supply arguments
to the `QCal` object.

In order to test the module, we first must run the model and have output
variables to measure against the targets. So the initial work of these tests will
simply be setting up a dummy model run, and running the model.

Start by defining a working directory for the tests and making sure it is
cleaned of any prior experiments.

    >>> import os
    >>> TMP_DIR = "/tmp/dvmdostem-doctests-qcal"
    >>> import shutil
    >>> shutil.rmtree(TMP_DIR)

Next use the utility script to setup the test folder with parameters, config
file, etc.

    >>> import util.setup_working_directory
    >>> util.setup_working_directory.cmdline_entry([ '--input-data-path',
    ...   'demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10',
    ...   TMP_DIR
    ... ])

Use another utility script to fiddle with the run mask, turning on only one
pixel.

    >>> import util.runmask
    >>> util.runmask.cmdline_entry(['--reset', '--yx', '0', '0', os.path.join(TMP_DIR, 'run-mask.nc')])
    0

Then turn on all the appropriate NetCDF outputs for matching with the targets:

    >>> import util.outspec
    >>> util.outspec.cmdline_entry(['--enable-cal-vars',os.path.join(TMP_DIR, 'config',  'output_spec.csv')])
    NOTE: Make sure to enable 'eq' outputs in the config file!!!
    0

Manually make an adjustment to the config file (there is no utility script for
this) such that equilibrium outputs are enabled:

    >>> import json
    >>> with open(os.path.join(TMP_DIR, 'config', 'config.js')) as f:
    ...    cfig = json.loads(f.read())

    >>> cfig['IO']['output_nc_eq'] = 1

    >>> with open(os.path.join(TMP_DIR, 'config', 'config.js'), 'w') as f:
    ...    json.dump(cfig, f)

And finally, run the model. Note that we must change directories first.

    >>> import subprocess
    >>> os.chdir(TMP_DIR)
    >>> subprocess.run(['/work/dvmdostem', '-c', '-f','config/config.js','--log-level', 'fatal', '-p','5','-e','20','-s','0','-t','0','-n','0'])
    CompletedProcess(args=['/work/dvmdostem', '-c', '-f', 'config/config.js', '--log-level', 'fatal', '-p', '5', '-e', '20', '-s', '0', '-t', '0', '-n', '0'], returncode=0)

After this all this is done, we can expect that there are both json and NetCDF
outputs available to be compared with the target values that are specified in
the `calibration_targets.py` file that ships with the model (and is copied into
the experiment directory by the `setup_working_directory.py` utility script).

Now we can make the `QCal` object:

    >>> import util.qcal
    >>> q = util.qcal.QCal( # doctest: +ELLIPSIS
    ...   jsondata_path=os.path.join(TMP_DIR, 'dvmdostem'),
    ...   ncdata_path=os.path.join(TMP_DIR, 'output'), 
    ...   ref_params_dir=os.path.join(TMP_DIR, 'parameters'), 
    ...   ref_targets_dir=os.path.join(TMP_DIR, 'calibration'), y=0, x=0)
    WARNING: No __init__.py python package file present. Copying targets to a temporary location for facilitate import
    Loading calibration_targets from : ['/tmp/dvmdostem-user-...-tmp-cal']
    Cleaning up temporary targets and __init__.py file used for import...
    Resetting path...

And print out the reports detailing how the model outputs compare to the
targets:

    >>> print(q.report(which='nc')) # doctest: +ELLIPSIS
            modeled data: /tmp/dvmdostem-doctests-qcal/output
              pixel(y,x): (0,0)
            targets file: /tmp/dvmdostem-doctests-qcal/calibration
         parameter files: /tmp/dvmdostem-doctests-qcal/parameters
                     CMT: {'CMT05'}
                     QCR: ...
            Weighted QCR: ...
    <BLANKLINE> 

The NetCDF and json reports should in theory match exactly, but there is
frequently a little variation due to rounding errors.

    >>> print(q.report(which='json')) # doctest: +ELLIPSIS
            modeled data: /tmp/dvmdostem-doctests-qcal/dvmdostem
              pixel(y,x): (n/a,n/a)
            targets file: /tmp/dvmdostem-doctests-qcal/calibration
         parameter files: /tmp/dvmdostem-doctests-qcal/parameters
                     CMT: {'CMT05'}
                     QCR: ...
            Weighted QCR: ...
    <BLANKLINE>    





