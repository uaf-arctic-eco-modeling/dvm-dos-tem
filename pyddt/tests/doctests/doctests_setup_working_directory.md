Load the tools

    >>> import shutil
    >>> import os

    >>> import pyddt.util.setup_working_directory
    >>> import pyddt.util.param
  
Cleanup

    >>> tmp_dir = "/tmp/test-setup_working_directory"
    >>> if(os.path.isdir(tmp_dir)):
    ...   shutil.rmtree(tmp_dir)

Run the tool on some arguments. Lets try working ones first.

    >>> args = pyddt.util.setup_working_directory.cmdline_parse(
    ... [ '--input-data-path',
    ...   '/work/testing-data/standard/inputs/cru-ts40_ar5_rcp85_ncar-ccsm4_IMNAVIAT_CREEK_10x10',
    ...   '/tmp/test-setup_working_directory'
    ... ])

See what we got:

    >>> print(args)
    Namespace(copy_inputs=False, force=False, input_data_path='/work/testing-data/standard/inputs/cru-ts40_ar5_rcp85_ncar-ccsm4_IMNAVIAT_CREEK_10x10', new_directory='/tmp/test-setup_working_directory', no_cal_targets=False, seed_parameters=None, seed_targets=None)

Now that we've parsed them, lets run the primary functionality of the utility -
setting up a new working directory for a `dvmdostem` run!
 
    >>> pyddt.util.setup_working_directory.cmdline_run(args)

If we try to run again, it should fail because the files exist and we don't want
to overwrite them: 

    >>> pyddt.util.setup_working_directory.cmdline_entry([
    ...   '--input-data-path',
    ...   'testing-data/standard/inputs/cru-ts40_ar5_rcp85_ncar-ccsm4_IMNAVIAT_CREEK_10x10', 
    ...   '/tmp/test-setup_working_directory'
    ... ])
    Traceback (most recent call last):
       ...
    FileExistsError: [Errno 17] File exists: '/tmp/test-setup_working_directory/parameters'

> Notice in the above examples we used both the `cmdline_parse` and `cmdline_run`
  functions - this isn't really necessary, and we can use the entry point function
  instead, (`cmdline_entry`) to run the script in one function call. This is what
  we will do in the future steps unless we are explicitly trying to test one of
  the other functions.

If we would like to overwrite the files, then pass the `--force` flag:

    >>> pyddt.util.setup_working_directory.cmdline_entry([
    ...   '--input-data-path',
    ...   '/work/testing-data/standard/inputs/cru-ts40_ar5_rcp85_ncar-ccsm4_IMNAVIAT_CREEK_10x10', 
    ...   '--force',
    ...   '/tmp/test-setup_working_directory'
    ... ])

If you want a custom parameter seed path, you can pass an option for that:

    >>> pyddt.util.setup_working_directory.cmdline_entry([
    ...   '--input-data-path',
    ...   '/work/testing-data/standard/inputs/cru-ts40_ar5_rcp85_ncar-ccsm4_IMNAVIAT_CREEK_10x10', 
    ...   '--force',
    ...   '--seed-parameters', '/work/testing-data/minimal/parameters/single_cmt',
    ...   '/tmp/test-setup_working_directory'
    ... ])

Now if we look in the new directory, there should be only a single CMT of data
in the parameters (whereas if we had not set the seed, there would be many
CMTs of data):

    >>> pyddt.util.param.get_CMTs_in_file("/tmp/test-setup_working_directory/parameters/cmt_calparbgc.txt")
    [{'cmtkey': 'CMT01', 'cmtnum': 1, 'cmtname': 'Boreal Black Spruce', 'cmtcomment': '6/29/20 boreal black spruce with Murphy Dome climate'}]