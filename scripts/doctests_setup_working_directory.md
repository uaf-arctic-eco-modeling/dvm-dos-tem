Load the tools

    >>> import shutil

    >>> import setup_working_directory as swd
  
Cleanup

    >>> shutil.rmtree("/tmp/test-setup_working_directory")

Run the tool on some arguments. Lets try working ones first.

    >>> args = swd.cmdline_parse(
    ... [ '--input-data-path',
    ...   '../demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10',
    ...   '/tmp/test-setup_working_directory'
    ... ])

See what we got:

    >>> print(args)
    Namespace(copy_inputs=False, input_data_path='../demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10', new_directory='/tmp/test-setup_working_directory', no_cal_targets=False)

Now that we've parsed them, lets run the setup functionality:

    >>> swd.cmdline_run(args)

If we try yo run again, it should fail because the files exist and we don't want
to overwrite them: 

    >>> swd.cmdline_entry([
    ...   '--input-data-path',
    ...   '../demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10', 
    ...   '/tmp/test-setup_working_directory'
    ... ])
    Traceback (most recent call last):
       ...
    FileExistsError: [Errno 17] File exists: '/tmp/test-setup_working_directory/config'

If we would like to overwrite the files, then pass the `--force` flag:

    >>> swd.cmdline_entry([
    ...   '--input-data-path',
    ...   '../demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10', 
    ...   '--force',
    ...   '/tmp/test-setup_working_directory'
    ... ])




  