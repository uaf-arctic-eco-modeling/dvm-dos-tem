#This module provides very general utility methods

import os


def breakdown_outfile_name(outfilepath):
  '''
  Takes a TEM output file name, with or without full path,
  and returns the path, variable name, time step, and stage.

  Example inputs:
    /data/workflows/testing1/output/ALD_yearly_sc.nc
    ALD_yearly_sc.nc

  Example outputs:
    /data/workflows/testing1/output, ALD, yearly, sc
    [current dir], ALD, yearly, sc
  '''

  #Resolve any symbolic links
  outputfile = os.path.realpath(outfilepath)

  #Collapse any extra separators (and remove any trailing slashes)
  outputfile = os.path.normpath(outputfile)

  path_prefix, filename = os.path.split(outputfile)

  #Split filename: varname_timeres_stage.nc
  filename_base = filename.partition('.')[0]
  varname, timeres, stage = filename_base.split('_')

#  print(path_prefix)
#  print(varname)
#  print(timeres)
#  print(stage)

  return path_prefix, varname, timeres, stage


'''
pyTEM
pytem
dvmdostem
pydvmdostem
dvmdostempy
tempy
TEMpy


pyddt
  README
  pyproject.toml
  
  docs/

  tests/
    pull_request_test.py
    doctests/
      doctests_outspec_utils.md
        
  util.general.py
  util.metrics.py
  util.param.py
  util.runmask.py
  util.outspec.py
    
  util.drivers
    BaseDriver.py
    MadsTEMDriver.py
    Sensitivity.py
  
  calibration
    ca-config-demo.yaml
    AC-MADS-TEM.jl
    AC-SCIPY-TEM.py

  sensitivity
    SA_setup_and_run.py
    SA_post_hoc_analysis.py
    sa-demo-config.yaml
  
  

'''