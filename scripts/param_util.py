#!/usr/bin/env python

# T. Carman
# January 2017

import os
import json


def get_CMTs_in_file(aFile):

  data = read_paramfile(aFile)

  cmtkey_list = []
  for line in data:
    if line.find('CMT') >= 0:
        sidx = line.find('CMT')
        cmtkey_list.append(line[sidx:sidx+5])

  return cmtkey_list

def find_cmt_start_idx(data, cmtkey):
  for i, line in enumerate(data):
    if cmtkey.upper() in line:
      return i

  # returns None...
  # need to figure out what to do if key is not found...


def read_paramfile(thefile):
  with open(thefile, 'r') as f:
    data = f.readlines()
  return data


def get_CMT_datablock(afile, cmtnum):
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
      if len(values) >= 5: # <--ARBITRARY! likely a pft data line
        for i, value in enumerate(values):
          cmtdict['pft%i'%i][comment] = value
      else:
        cmtdict[comment] = values[0]

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

