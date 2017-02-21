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



def format_CMTdatadict(dd, refFile, format=None):
  '''
  Returns a formatted block of CMT data.

  Parameters
  ----------
  dd : dict
    Dictionary containing parameter names and values for a CMT.
  refFile : str
    A path to a file that should be used for reference in formatting the output.
  format : str (optional)
    A string specifying which format to return. Defaults to None.

  Returns
  -------
  d : [str, str, ...]
    A list of strings
  '''
  if format is not None:
    print "NOT IMPLEMENTED YET!"
    exit(-1)

  ref_order = generate_reference_order(refFile)
  dwpftvs = False

  ll = []
  ll.append("// First line comment...")
  ll.append("// Second line comment (?? PFT string?)")

  def is_pft_var(v):
    if v not in dd.keys() and v in dd['pft0'].keys():
      return True
    else:
      return False

  for var in ref_order:
    if not is_pft_var(var):
      pass
    else:
      # get each item from dict, append to line
      linestring = ''
      for pft in get_datablock_pftkeys(dd):
        linestring += "{:>12.6f} ".format(dd[pft][var])
      linestring += ('// %s: ' % var)
      ll.append(linestring)

  for var in ref_order:
    if is_pft_var(var):
      pass # Nothing to do; already did pft stuff
    else:
      # get item from dict, append to line
      ll.append('{:<12.5f} // comment??'.format(dd[var]))

  return ll




def generate_reference_order(aFile):
  '''
  Lists order that variables should be in in a parameter file based on CMT 0.

  Parameters
  ----------
  aFile: str
    The file to use as a base.

  Returns
  -------
  l : [str, str, ...]
    A list of strings containing the variable names, parsed from the input file
    in the order they appear in the input file.
  '''

  cmt_calparbgc = []
  db = get_CMT_datablock(aFile, 0)

  pftblock = detect_block_with_pft_info(db)

  ref_order = []

  for line in db:
    t = comment_splitter(line)
    if t[0] == '':
      pass # nothing before the comment, ignore this line - is has no data
    else:
      # looks like t0 has some data, so now we need the
      # comment (t[1]) which we will further refine to get the
      # tag, which we will append to the "reference order" list
      tokens = t[1].strip().lstrip("//").strip().split(":")
      tag = tokens[0]
      desc = "".join(tokens[1:])
      print "Found tag:", tag, " Desc: ", desc
      ref_order.append(tag)

  return ref_order


def comment_splitter(line):
  '''
  Splits a string into data before comment and after comment.

  The comment delimiter ('//') will be included in the after component.

  Parameters
  ----------
  line : str
    A string representing the line of data. May or may not contain the comment
    delimiter.

  Returns
  -------
  t : (str, str) - Tuple of strings.
    A tuple containing the "before comment" string, and the "after comment"
    string. The "after commnet" string will include the comment charachter.
  '''
  cmtidx = line.find("//")
  if cmtidx < 0:
    return (line, '')
  else:
    return (line[0:cmtidx], line[cmtidx:])


def get_datablock_pftkeys(dd):
  '''
  Returns a sorted list of the pft keys present in a CMT data dictionary.

  Parameters
  ----------
  dd : dict
    A CMT data dictionary (as might be created from cmtdatablock2dict(..)).

  Returns
  -------
  A sorted list of the keys present in dd that contain the string 'pft'.
  '''
  return sorted([i for i in dd.keys() if 'pft' in i])

def enforce_initvegc_split(aFile, cmtnum):
  '''
  Makes sure that the 'cpart' compartments variables match the proportions
  set in initvegc variables in a cmt_bgcvegetation.txt file.

  The initvegc(leaf, wood, root) variables in cmt_bgcvegetation.txt are the
  measured values from literature. The cpar(leaf, wood, root) variables, which 
  are in the same file, should be set to the fractional make up of the the
  components. So if the initvegc values for l, w, r are 100, 200, 300, then the 
  cpart values should be 0.166, 0.33, and 0.5. It is very easy for these values
  to get out of sync when users manually update the parameter file.

  Parameters
  ----------
  aFile : str
    Path to a parameter file to work on. Must have bgcvegetation.txt in the name
    and must be a 'bgcvegetation' parameter file for this function to make sense
    and work.
  cmtnum : int
    The community number in the file to work on.


  Returns
  -------
  d : dict
    A CMT data dictionary with the updated cpart values.
  '''

  if ('bgcvegetation.txt' not in aFile):
    raise ValueError("This function only makes sense on cmt_bgcvegetation.txt files.")


  d = get_CMT_datablock(aFile, cmtnum)
  dd = cmtdatablock2dict(d)

  for pft in get_datablock_pftkeys(dd):
    sumC = dd[pft]['initvegcl'] + dd[pft]['initvegcw'] + dd[pft]['initvegcr']
    if sumC > 0.0:
      dd[pft]['cpartl'] = dd[pft]['initvegcl'] / sumC
      dd[pft]['cpartw'] = dd[pft]['initvegcw'] / sumC
      dd[pft]['cpartr'] = dd[pft]['initvegcr'] / sumC
    else:
      dd[pft]['cpartl'] = 0.0
      dd[pft]['cpartw'] = 0.0
      dd[pft]['cpartr'] = 0.0

  return dd





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

