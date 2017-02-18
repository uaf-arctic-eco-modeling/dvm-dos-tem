#!/usr/bin/env python

# T. Carman
# January 2017

import os
import json


def get_CMTs_in_file(aFile):
  '''
  Gets a list of the CMTs found in a file.

  Parameters
  ----------
  aFile : string, required
    The path to a file to read.

  Returns
  -------
  A list of CMTs found in a file.
  '''
  data = read_paramfile(aFile)

  cmtkey_list = []
  for line in data:
    if line.find('CMT') >= 0:
        sidx = line.find('CMT')
        cmtkey_list.append(line[sidx:sidx+5])

  return cmtkey_list

def find_cmt_start_idx(data, cmtkey):
  '''
  Finds the starting index for a CMT data block in a list of lines.

  Parameters
  ----------
  data : [str, str, ...] 
    A list of strings (maybe from a parameter file)
  cmtkey : str
    A a CMT code string like 'CMT05' to search for in the list.

  Returns
  -------
  i : int 
    The first index in the list where the CMT key is found. If key is not found
    returns None.
  '''
  for i, line in enumerate(data):
    if cmtkey.upper() in line:
      return i

  # Key not found
  return None

def read_paramfile(thefile):
  '''
  Opens and reads a file, returning the data as a list of lines (with newlines).

  Parameters
  ----------
  theFile : str
    A path to a file to open and read.

  Returns
  -------
  d : [str, str, str, ...]
    A list of strings (with newlines at the end of each string).
  '''
  with open(thefile, 'r') as f:
    data = f.readlines()
  return data

def get_CMT_datablock(afile, cmtnum):
  '''
  Search file, returns the first block of data for one CMT as a list of strings.

  Parameters
  ----------
  afile : str
    Path to a file to search.
  cmtnum : int
    The CMT number to search for. Converted (internally) to the CMT key.


  Returns
  -------
  d : [str, str, ...]
    A list of strings, one item for each line in the CMT's datablock.
    Each string will have a newline charachter in it.
  '''
  data = read_paramfile(afile)

  cmtkey = 'CMT%02i' % cmtnum

  startidx = find_cmt_start_idx(data, cmtkey)

  end = None

  for i, line in enumerate(data[startidx:]):
    if i == 0: # Header line, e.g.: "// CMT07 // Heath Tundra - (ma.....""
      pass    
    elif i == 1: # PFT name line, e,g.: "//Decid.     E.green      ...."
      # Not sure how/why this is working on non-PFT data blocks
      # but is seems to do the trick?
      pass

    if (i > 0) and "CMT" in line:
      #print "end of datablock, i=", i
      end = startidx + i
      break

  return data[startidx:end]

def detect_block_with_pft_info(cmtdatablock):
  # Perhaps should look at all lines??
  secondline = cmtdatablock[1].strip("//").split()
  if len(secondline) >= 9:
    #print "Looks like a PFT header line!"
    return True
  else:
    return False

def parse_header_line(datablock):
  '''Splits a header line into components: cmtkey, text name, comment.

  Assumes a CMT block header line looks like this:
  // CMT07 // Heath Tundra - (ma.....

  '''

  # Assume header is first line
  l0 = datablock[0]

  # Header line, e.g: 
  header = l0.strip().strip("//").strip().split("//")

  hdr_cmtkey = header[0].strip()
  txtcmtname = header[1].strip().split('-')[0].strip()
  hdrcomment = header[1].strip().split('-')[1].strip()
  return hdr_cmtkey, txtcmtname, hdrcomment

def get_pft_verbose_name(cmtkey=None, pftkey=None, cmtnum=None, pftnum=None):
  path2params = os.path.join(os.path.split(os.path.dirname(os.path.realpath(__file__)))[0], 'parameters/')

  if cmtkey and cmtnum:
    raise ValueError("you must provide only one of you cmtkey or cmtnumber")

  if pftkey and pftnum:
    raise ValueError("you must provide only one of pftkey or pftnumber")

  if cmtkey: # convert to number
    cmtnum = int(cmtkey.lstrip('CMT'))

  if pftnum: # convert to key
    pftkey = 'pft%i' % pftnum

  data = get_CMT_datablock(os.path.join(path2params, 'cmt_calparbgc.txt'), cmtnum)
  dd = cmtdatablock2dict(data)


  return dd[pftkey.lower()]['name']

def cmtdatablock2dict(cmtdatablock):
  '''
  Converts a "CMT datablock" (list of strings) into a dict structure.

  Parameters
  ----------
  cmtdatablock : [str, str, ...]
    A list of strings (with new lines) holding parameter data for a CMT.

  Returns
  -------
  d : dict
    A multi-level dict mapping names (deduced from comments) to parameter 
    values.holding parameter values.
  '''

  cmtdict = {}

  pftblock = detect_block_with_pft_info(cmtdatablock)

  hdr_cmtkey, txtcmtname, hdrcomment = parse_header_line(cmtdatablock)
  cmtdict['tag'] = hdr_cmtkey
  cmtdict['cmtname'] = txtcmtname
  cmtdict['comment'] = hdrcomment

  if pftblock:
    # Look at the second line for something like this:
    # PFT name line, like: "//Decid.     E.green      ...."
    pftlist = cmtdatablock[1].strip("//").strip().split()
    pftnames = pftlist[0:10]
    
    for i, pftname in enumerate(pftnames):
      cmtdict['pft%i'%i] = {}
      cmtdict['pft%i'%i]['name'] = pftname


  for i, line in enumerate(cmtdatablock):
    if line.strip()[0:2] == "//":
      #print "passing line", i
      continue # Nothing to do...commented line

    else: # normal data line
      dline = line.strip().split("//")
      values = dline[0].split()
      comment = dline[1].strip().strip("//").split(':')[0]
      if len(values) >= 5: # <--ARBITRARY! likely a pft data line?
        for i, value in enumerate(values):
          cmtdict['pft%i'%i][comment] = float(value)
      else:
        cmtdict[comment] = float(values[0])

  return cmtdict



if __name__ == '__main__':

  print "NOTE! Does not work correctly on non-PFT files yet!!"

  testFiles = [
    'parameters/cmt_calparbgc.txt',
    'parameters/cmt_bgcsoil.txt',
    'parameters/cmt_bgcvegetation.txt',
    'parameters/cmt_calparbgc.txt.backupsomeparams',
    'parameters/cmt_dimground.txt',
    'parameters/cmt_dimvegetation.txt',
    'parameters/cmt_envcanopy.txt',
    'parameters/cmt_envground.txt',
    'parameters/cmt_firepar.txt'
  ]

  for i in testFiles:
    print "{:>45s}: {}".format(i, get_CMTs_in_file(i)) 

  # for i in testFiles:
  #   print "{:>45s}".format(i)
  #   print "".join(get_CMT_datablock(i, 2))
  #   print "{:45s}".format("DONE")

  d = get_CMT_datablock(testFiles[4], 2)
  print "".join(d)

  print json.dumps(cmtdatablock2dict(d), sort_keys=True, indent=2)
   
  print "NOTE! Does not work correctly on non-PFT files yet!!"

