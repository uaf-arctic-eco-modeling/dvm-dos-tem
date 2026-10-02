#!/usr/bin/env python3

'''
This tool is for preflight checks of dvmdostem runs. It should accept a path to
a run directory as an argument. The tool should provide a report with items
flagged as either WARNING or ERROR. Items that are ERRORS must be addressed
before you can expect the dvmdostem run to actually complete. Items that are
WARNING may not prevent the run from completing, but should be reviewed because
they may make the outputs questionable.

Here is a list of checks:

Layout of the run directory, expected files and directories:
  calibration/ (directory, not really used at this time) (warning if not
  present) config/ (has a config.js file, as well as output_spec.csv) (error)
  output/ (empty directory)  (warn if not empty) parameters/ (folder of
  parameter files) (error if not present) run-mask.nc (file) (error if not
  present)
    - note that the run-mask.nc file is required for the run and common practice
      is to keep the run mask in the run folder (with relative path in the
      config.js file, but it could also be valid to keep it elsewhere with an
      absolute path in the config file...))

Note that for checking the paths to the input files (and parameters, output/
etc) there is the question of execution context of this pre-flight check tool vs
the execution context of the dvmdostem run itself. Sometimes the preflight tool
might be run from inside the docker container in which case, the paths in the
config file can be checked directly. But other times the user might wish to run
the preflight from outside the docker container in which case the paths in the
config file may need to be interpreted relative to the host system rather than
the container. This same problem is present with the pyddt-runmonitor and
pyddt-resume-region tooling, so following the same pattern as used in those
tools might be helpful.
    

Integrity of config.js file
  - run-mask.nc exists (error)
  - parameters/ exists (error)
  - output/ exists (error)
  - config/config.js exists and is readable (error)
  - check the IO section of the config for:
  - output is relative path (warning)
  - parameters is relative path (warning)
  - run-mask.nc is relative path (warning)
  - all input paths exist (error)

The current "standard" way to setup a dvmdostem run is to have a working
directory that contains the config/, output/, parameters/ directories and the
run-mask.nc file. Then in the config/config.js file, the paths to these
directories and files should be specified relative to this working directory.
while the paths to the "heavier" inputs may be specified either relative to this
working directory or as absolute paths. However note that the user could have
specified a run that used absolute paths to the config file, output_spec file,
parameter files, etc. This would allow sharing these resources between runs.
Perhaps this merits a warning because there are some valid use cases for sharing
these resources.


Output specification:
   - Check the output_spec.csv file for required columns and consistency (error)
   - Check that the user has enabled CMTNUM as an output (error)
   - Check that if the user has enabled any layer outputs, then at least LAYERDZ
     is also enabled (error)
   - Warn user of other LAYER description outputs that are enabled without
     LAYERDZ (warning)

Then we need to open the run-mask file and the vegetation file and the parameter
files. We should confirm that for every enabled grid cell in the run mask, there
is a corresponding CMT entry in the parameter files corresponding to the CMT
number that is in the vegetation.nc file. For example if cell 1,1 is ON in the
run mask and cell 1,1 in the vegetation.nc file has value 234, then the
parameters files must have a valid block of data for CMT234. This must exist in
all the parameter files. Please make use of the pyddt-param (`pyddt.util.param`)
module to parse and query the parameter files.

'''