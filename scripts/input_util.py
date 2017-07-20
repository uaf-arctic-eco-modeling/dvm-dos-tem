#!/usr/bin/env python

import os

'''
Utility functions for working with dvmdostem inputs.
'''

#################################################################
# Define custom errors that are relevant for this application
#################################################################
class BadInputFilesValueError(ValueError):
  '''Raise when there is a problem with the input files.'''

class MissingInputFilesValueError(ValueError):
  '''Raise when not enough files are present.'''


def verify_input_files(in_folder):
  '''
  Raises various exceptions if there are problems with the files in the in_folder.

  Parameters
  ----------
  in_folder : str
    A path to a folder of dvmdostem inputs.

  Throws
  ------  
  BadInputFilesValueError, 

  Returns
  -------
  None
  '''
  required_files = set(['co2.nc', 'drainage.nc', 'fri-fire.nc', 
      'historic-climate.nc', 'historic-explicit-fire.nc',
      'projected-climate.nc', 'projected-explicit-fire.nc', 'run-mask.nc',
      'soil-texture.nc', 'topo.nc', 'vegetation.nc'])

  files = set([f for f in os.listdir(in_folder) if os.path.isfile(os.path.join(in_folder, f))])
  dirs = [d for d in os.listdir(in_folder) if os.path.isdir(os.path.join(in_folder, d))]

  # any 
  #print "Symetric difference: ", files.symmetric_difference(required_files)
  
  if len(files.difference(required_files)) > 0:
    print "WARNING: extra files present: ", files.difference(required_files)

  if len(required_files.difference(files)):
    msg = "Missing files: {}".format(required_files.difference(files))
    raise MissingInputFilesValueError(msg)


  if 'output' not in dirs:
    raise MissingInputFilesValueError("'output/' directory not present!")
