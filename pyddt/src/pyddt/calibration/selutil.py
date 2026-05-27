#!/usr/bin/env python


# A bunch of utility functions for dvm-dos-tem calibration plotting

import logging
import os

logging = logging.getLogger(__name__)

def check_dir(directory):
  '''Check for the existence of a directory. If it does not exist, create it.'''
  if not os.path.isdir(directory):
    os.mkdir(directory)

def jfname2idx(jfname):
  '''Convert 'YYYY_MM*' str to index, e.g.: '0000_00.json' -> 0'''
  assert type(jfname) == str, "jfname (json file name) must be a string"
  year = int(jfname[0:4])
  month = int(jfname[5:7])
  assert (month >= 0) and (month <= 11), "Month must be a number, 0-11"
  return (year * 12) + month

def idx2jfname(idx):
  '''Convert index to 'YYYY_MM*' str, e.g.: 0 -> '0000_00.json' '''
  #assert type(idx) == int, "idx must be an integer"
  year = str(idx/12)
  month = str(idx%12)
  return '{:0>4}'.format(year) + '_' + '{:0>2}'.format(month) + '.json'

def assert_zero_start(file_list, log=True):
  '''Returns True if first element in file list is a string starting 
  with '0000_00'. 
  
  If the assertion fails and log=True, the assertion is sent to log.warn().
  '''
  try:
    assert jfname2idx( os.path.basename(file_list[0]) ) == 0, "File list does not start with 0000_00!"
  except AssertionError as e:
    logging.warn(e)
    return False
  return True

def assert_continuity(file_list, log=True):
  '''Returns True if the file listing has no gaps.
  
  If the assertion fails and log=True, the assertion is sent to log.warn().
  '''

  first = jfname2idx( os.path.basename(file_list[0]) )
  last = jfname2idx( os.path.basename(file_list[-1]) )

  try:
    assert len(range(first, last + 1)) == len(file_list), "File list is not continuous!"
  except AssertionError as e:
    logging.warn(e)
    return False

  return True

if __name__ == '__main__':
  print "Nothing happening here..."







