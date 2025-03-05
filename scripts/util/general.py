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





