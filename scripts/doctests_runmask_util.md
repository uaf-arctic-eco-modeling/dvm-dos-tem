Load the tool. The script was inadvertently named with a hyphen in the name and
this makes normal `import` statements not work. So we use `importlib` to help
out.

    >>> import importlib
    >>> rmu  = importlib.import_module("runmask-util")

Next, make a copy of the demo input files so we can modify it without damaging
the original.

    >>> import shutil
    >>> shutil.rmtree("/tmp/test")
    >>> shutil.copytree(
    ...   "../demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10",
    ...   "/tmp/test"
    ... )
    '/tmp/test'

Show the copy:

    >>> rmu.show_mask("/tmp/test/run-mask.nc", 'Just a note')
    ========== Just a note ==================================
    ** Keep in mind that in this display the origin is the upper 
    ** left of the grid! This is opposite of the way that ncdump 
    ** and ncview display data (origin is lower left)!!
    <BLANKLINE>
    '/tmp/test/run-mask.nc'
    <class 'netCDF4._netCDF4.Variable'>
    int64 run(Y, X)
        grid_mapping: albers_conical_equal_area
    unlimited dimensions: 
    current shape = (10, 10)
    filling on, default _FillValue of -9223372036854775806 used
    [[1 0 0 0 0 0 0 0 0 0]
     [0 1 0 0 0 0 0 0 0 0]
     [0 0 0 0 0 0 0 0 0 0]
     [0 0 0 0 0 0 0 0 0 0]
     [0 0 0 0 0 0 0 0 0 0]
     [0 0 0 0 0 0 0 0 0 0]
     [0 0 0 0 0 0 0 0 0 0]
     [0 0 0 0 0 0 0 0 0 0]
     [0 0 0 0 0 0 0 0 0 0]
     [0 0 0 0 0 0 0 0 0 0]]
    <BLANKLINE>

Before we go any farther, we'll import some more helper libraries that we will
use for demonstration and testing:

    >>> import netCDF4 as nc
    >>> import numpy as np

While we are using `netCDF4` and `numpy` here for testing `runmask_util` was
written so that you should not need these libraries for basic manipulations of
the `dvmdostem` run mask file. Also, the style of programming used here is
geared toward testing - for general use, you are more likely to use the command
line interface from your shell.

Count the number of enabled pixels in the demo file.

    >>> d = nc.Dataset("/tmp/test/run-mask.nc")
    >>> np.count_nonzero(d.variables['run'])
    2
    >>> d.close()

Try clearing out the file with `rmu`. 

> This style of programming uses the command line interface, but is designed to
  be "programable" for use in a testing system. Normal use of the command line
  interface would be something like this `$ ./runmask-util.py --help`

    >>> rmu.cmdline_run(rmu.cmdline_parse(["--reset", "/tmp/test/run-mask.nc"]))
    0

And then check our file again - there should not be any pixels enabled after a
reset.

    >>> d = nc.Dataset("/tmp/test/run-mask.nc")
    >>> np.count_nonzero(d.variables['run'])
    0
    >>> d.close()



