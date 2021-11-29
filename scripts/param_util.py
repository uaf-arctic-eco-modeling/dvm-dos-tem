#!/usr/bin/env python

# T. Carman
# January 2017

import os
import json
import re
import glob
import sys
import csv
import itertools

# This helps to more quickly diagnose errors that show up when
# using older (typically system) versions of Python. Usually this
# happens when a user forgets to activate a virtual environment or
# load the correct modules.
if float('%d.%d'%(sys.version_info[0:2])) < 2.7:
 raise Exception("Must use Python version 2.7 or greater!")


class ParamUtilSpeedHelper(object):
  '''
  Experimenting with having an object oriented API so that we can 
  cache some data in the object. Will save lots of time for various
  look up type functionality.

  With param_util.py in general the idea has been to have it be flexible
  with repsect to the location of the parameter files. But that makes 
  some operations expensive because the code is constantly having to 
  re-build lookup datastructures to find parameter names or files.

  With this object the idea is to set the parameter directory upon
  instantiation, and build the lookup data structure. Then future
  operations can use that cached structure.

  Examples
  --------
  >>> import param_util as pu
  >>> psh = pu.ParamUtilSpeedHelper("/work/parameters")
  >>> psh.get_value(pname='cmax', cmtnum=4, pftnum=3, with_metadata=False)

  '''
  def __init__(self, pdir):
    '''
    Sets parameter directory, build lookup structure.

    Parameters
    ----------
    `pdir` is path to a directory of dvmdostem parameter files.
    '''
    self.__pdir = pdir
    self.lu = build_param_lookup(self.__pdir)

  def get_value(self, pname=None, cmtnum=None, pftnum=None, with_metadata=False):
    '''
    Look up the parameter value by name for given CMT and PFT.

    Parameters
    ----------
    pname : str
      Name of parameter as found in dvmdostem parameter files.

    cmtnum : int
      The number of the community type to grab data from.

    pftnum : int
      The PFT of the data to grab (for PFT parameters), None (default)
      for non-pft parameters.

    with_metadata : bool
      (not implemented yet) flag for returning just the raw data or
      a package with more metadata (e.g. param directory, filename, etc)

    Returns
    -------
    v : float
      The parameter value, or if `with_metadata=True`, a dict with more
      info.
    '''
    f = which_file(self.__pdir, pname, lookup_struct=self.lu)
    cmt_dict = cmtdatablock2dict(get_CMT_datablock(f, cmtnum))
    rv = None
    if pname in cmt_dict.keys():
      # Not a PFT parameter...
      rv =  cmt_dict[pname]
    else:
      pftkey = 'pft{}'.format(pftnum)
      rv = cmt_dict[pftkey][pname]

    return rv

  def list_non_pft_params(self, cmtnum=None):
    '''
    Gets a listing of all non-PFT parameters.

    Parameters
    ----------
    cmtnum : int
      The CMT number to read from.

    Returns
    -------
    s : str
      A formatted string of all non-PFT parameters, (i.e. soil params)
    '''
    s = ''
    for fname, pdict in self.lu.items():
      s += '{}:\n'.format(fname)
      for p in pdict['non_pft_params']:
        s += '    {}\n'.format(p)
    return s



  def list_params(self, cmtnum=None, pftnum=None):
    '''
    Builds and returns a formatted string listing all the 
    parameters for a given CMT and PFT.

    Parameters
    ----------
    cmtnum : int
      The community type number to list parameters for.

    pftnum : int
      The PFT number to list parameters for.

    Returns
    -------
    s : string
      A formatted string listing all the parameters for a given CMT and PFT.
    '''
    assert cmtnum is not None, "Must pass cmtnum!"
    assert pftnum is not None, "Must pass pftnum!"

    pvn = get_pft_verbose_name(cmtnum=cmtnum, pftnum=pftnum,lookup_path=self.__pdir)
    s = ''
    for fname, pdict in self.lu.items():
      s += '{} CMT{} PFT{} {}\n'.format(fname, cmtnum, pftnum, pvn)
      for ptype, plist in pdict.items():
        s += "  {}\n".format(ptype)
        for pname in plist:
          val = self.get_value(pname=pname, cmtnum=cmtnum, pftnum=pftnum)
          s += "   {:>15s} {:>12.4f}\n".format(pname, val)

    return s




def error_exit(fname, msg, linenumber=None):
  '''
  Prints and error message and exits.

  Parameters
  ----------
  fname : string, required
    The path to the offending file.

  msg : string, required
    A message or note to tbe printed.

  linenumber : int, optional
    The problematic line in the offending file.
  '''
  print("ERROR! {} file: {}:{}".format(msg, fname, linenumber))
  sys.exit(-1)


def csv_specification():
  '''
  Specification for csv files that hold parameter data.
  
  This csv format is intended to be used as a bridge between Excel
  and the dvmdostem space delimited parameter files. Expected usage: A user
  maintains or develops a spreadsheet with parameter data. Then user exports
  this spreadsheet to csv file. The utility functions in this script can then
  be used to parse the csv file and re-format the data as space delimited 
  text that can be copied into dvmdostem parameter files.

  The csv file should be setup as follows:
  - The csv file must have blank rows (lines) separating each section, or block 
    of data. Generally each block of data will be intended for a different parameter 
    file, i.e. cmt_envcanopy.txt, etc.
  - Each section must start with a row that has all CAPS text in the first column 
    and no data in the subsequent columns.
  - There must be a row in the file with 'pft name' in the first column followed
    by names for each PFT in the subsequent columns. These names will be applied
    to all the sections of data in the file.
  - There must not be more than 10 PFT columns.

  CAVEATS: PFT names will be converetd to CamelCase, comments
  will not be preserved or added to the file, the CMT number won't be filled 
  out, and no verification is done to see if there is a conflicting CMT number in 
  any existing parameter files.

  Example File
  ------------

        $ cat example.csv
        ,,,,
        pft name,EVR TREE,DEC SHRUB,DEC TREE,MOSS
        ,,,,
        CALIBRATION TARGETS,,,,
        GPPAllIgnoringNitrogen,306.07,24.53,46.53,54.20
        NPPAllIgnoringNitrogen,229.91,18.42,34.98,40.65
        NPPAll,153.03,12.26,23.26,27.1
        ,,,,
        BCGVEGETATION,,,,
        kc,400,400,400,400
        ki,75,75,75,75
        tmin,-1,-1,-1,-1
        toptmin,15,15,15,15
  '''
  # This is a do-nothing function, used simply as a way to hold a nice 
  # docstring describing the csv format.
  pass


def standardize_pftnames(names):
  '''
  Replaces any spaces, dots, underscores or dashes with CamelCase.
  
  Parameters
  ----------
  names : list, required
    A list of strings, with PFT names.

  Returns
  -------
    A list of strings with each item changed to CamelCase.

  Example
  -------
      >>> standardize_pftnames(['Test 1','Test-32','test_6','test.34.helper'])
      ['Test1', 'Test32', 'Test6', 'Test34Helper']
  '''
  def fix(x):
    # look for common separators, have to escape the period
    x = re.sub(r"(_|-| |\.)+", "$",x).title().replace("$",'')
    return x
  return list(map(fix, names))


def get_pftnames(data):
  '''
  Retrieves PFT names from a specially formatted csv file.
  
  Assumes that `data` is a list of lines read from a csv file that
  is formatted according to the csv_specification. See help for the
  csv_specification() function.

  Parameters
  ----------
  data : list of strings, required
    Assumed to be a list generated by reading a csv file that is
    formatted as described above.

  Returns
  -------
  A list of pft names read from the incoming data.
  '''
  csvreader = csv.reader(data, dialect='excel', strict=True, skipinitialspace=True)
  for row in csvreader:
    if 'pft name' in row:
      if row.index('pft name') != 0:
        print("WARNING! pft name column not in the proper place. Returned PFT names might be incorrect.")
      if len(row[1:]) > 10:
        print("WARNING! appears there are too many PFT columns!")
      return row[1:]


def find_section_starts(data):
  '''
  Gets the starting index and name for sections of data in a specially formatted csv file.

  Assumes that `data` is a list of lines read from a csv file. See help
  (docstring) for csv_specification().

  Parameters
  ----------
  data : list of strings, required
    Assumed to be a list generated by reading a csv file that is
    formatted as in csv_specification.

  Returns
  -------
  A list of tuples, where the first item in the tuple is the index in the 
  csv file where the section starts, and the second item in the tuple is the
  text name for the section, as read from the file.
  '''
  csvreader = csv.reader(data, dialect='excel', strict=True, skipinitialspace=True)
  starts = []
  sections = []
  for i, row in enumerate(csvreader):
    if all(x == '' for x in row[1:]):
      if row[0] != '':
        if row[0].isupper():
          #print(i, row)
          starts.append(i)
          sections.append(row[0])
  results = list(zip(starts, sections))
  return results


def get_section(data, start):
  '''
  Extracts a section of block of data from a specially formatted csv file.

  Assumes that `data` is a list of lines read from a csv file. See help 
  (the docstring) for the csv_specification() function to get more details
  on how the csv file should be setup.

  Parameters
  ----------
  data : list of strings, required
    Assumed to be a list generated by reading a csv file that is formatted as 
    described in the docstring for csv_specification()
  start:
    The index in the `data` list where the section starts.

  Returns
  -------
  The list of lines (rows) from `data` that belongs to a section or block.
  '''
  sectiondata = []
  for row in data[start:]:
    row = [x.strip() for x in row.split(',')]
    if all(x=='' for x in row):
      break
    else:
      sectiondata.append(row)
  return sectiondata  


def converter(x):
  '''
  Convert data to float type for printing. Converts empty string to 0.0
  
  Parameters
  ----------
    x : anything

  Returns
  -------
  If x castable to a float, a float is returned. If x is an empty string, 0.0
  is returned. Otherwise x is returned un-modified.
  '''
  try:
    x = float(x)
  except ValueError:
    pass
  if x == '':
    x = 0.0
  return x


def format_section(section_data, full_data):
  '''
  Prints data (presumably from csv file) to dvmdostem space delimited parameter format.

  No effort is made to standardize the variable names or comments in the resulting
  block. Used a fixed width column, space delimited.

  See the help for csv_specification() function to find more info on how the
  csv file should be formatted.

  Parameters
  ----------
  section_data : list
    Assumed to be a list of lines for one section of data read from a csv file. The csv 
    file must be formatted as described in the docstring for csv_specification().
    
  full_data : list
    Assumed to be a list of lines of all the data read from a csv file. The csv 
    file must be formatted as described in the docstring for csv_specification().

  Returns
  -------
  A formatted string with space delimited parameter data.
  '''

  s = ''
  for i, row in enumerate(section_data):
    if i == 0:
      s += "// CMT???? // ASSIGN OR FIX CMT NUMBER AT LEFT AND ADD SOME COMMENT HERE....\n"

      zed = [i[0] for i in itertools.zip_longest(standardize_pftnames(get_pftnames(full_data)), range(0,10), fillvalue='PFT')]
      fs = ' '.join(['{:>15s}' for i in range(0,10)])
      s += ('//' + fs.format(*(zed)) + '\n') 

    else:
      zed = [i[0] for i in itertools.zip_longest(list(map(converter, row[1:])), range(0,10), fillvalue=0.0)]
      fs = ' '.join(['{:15.4f}' for i in range(0,10)])
      s += ('  ' + fs.format(*zed) +'  // ' + row[0] +'\n')

  return(s)


def get_CMTs_in_file(aFile):
  '''
  Gets a list of the CMTs found in a file.

  Looks at all lines in the file and considers any commented line with the 
  'CMT' as the first non-whitespace charachters after the initial comment
  symbol to be a CMT definition line. Parses this line and sets the following
  keys in a dict: cmtkey, cmtnum, cmtname, cmtcomments

  Parameters
  ----------
  aFile : string, required
    The path to a file to read.

  Returns
  -------
  A list of dicts with info about the CMTs found in a file.
  '''
  data = read_paramfile(aFile)

  cmt_list = []
  for i, line in enumerate(data):
    # Looks for CMT at the beginning of a comment line.
    # Will match:
    # "// CMT06 ....", or "  //   CMT06 ..."
    # but not
    # '// some other text CMT06 '
    line = line.strip().lstrip('//').strip()
    if line.find('CMT') == 0:
      cmtkey, cmtname, cmtcomments = parse_header_line(line)
      cmtnum = int(cmtkey[3:])
      cmtdict = dict(cmtkey=cmtkey, cmtnum=cmtnum, cmtname=cmtname, cmtcomment=cmtcomments)
      cmt_list.append(cmtdict)

    elif line.find('CMT') > 0:
      # Must be a comment line, and not the start of a valid CMT data block.
      pass

  return cmt_list


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

  # NOTE: Should probably rasie some kind of ERROR if CMTKEY is not 
  # somethign like CMT00

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

def compare_CMTs(fileA, cmtnumA, fileB, cmtnumB, ignore_formatting=True):
  '''
  Compares the specified CMT data blocks in each file line by line, prints
  "Match" if the lines are the same, otherwise print the lines for visual 
  comparison.

  By running the datablocks thru the format function, we can compare on values
  and ignore whitespace/formatting differences.

  Parameters
  ----------
  fileA : str
    Path to file for comparison.
  cmtnumA : int
    Number of CMT for comparison.
  fileB : str
    Path to file for comparison.
  cmtnumB : int
    Number of CMT for comparison.
  ignore_formatting : bool
    When True (default) it is easy to see how the numbers differ. When this 
    setting is False, lines with different formatting will not match, i.e. 
    0.0 and  0.000 will show up as different.

  Returns
  -------
  None
  '''
  dataA = get_CMT_datablock(fileA, cmtnumA)
  dataB = get_CMT_datablock(fileB, cmtnumB)

  # Standardize whitespace and numeric format using the foratting function.
  if ignore_formatting:
    dataA = format_CMTdatadict(cmtdatablock2dict(dataA), fileA)
    dataB = format_CMTdatadict(cmtdatablock2dict(dataB), fileB)
  else:
    pass

  # Loop over the lines in the data block testing them
  for i, (A, B) in enumerate(zip(dataA, dataB)):
    if A == B:
      print("LINE {} match!".format(i))
    else:
      print("LINE {} difference detected! ".format(i))
      print("   A: {}".format(A))
      print("   B: {}".format(B))
      print("")

def is_CMT_divider_line(line):
  '''
  Checks to see if a line is one of the comment lines we use to divide
  CMT data blocks in parameter files, e.g. // ====== '''
  return re.search('^//[ =]+', line.strip())


def replace_CMT_data(origfile, newfile, cmtnum, overwrite=False):
  '''
  Replaces the CMT datablock in `origfile` with the data block found in
  `newfile` for the provided `cmtnum`. If `overwrite` is True, then `origfile`
  is written with the new data. Returns a list of lines which can then be 
  printed to stdout or otherwise redirected to a file.

  Parameters
  ----------
  `origfile` : str
    Path to a file with CMT data blocks.
  `newfile` : str
    Path to a file with CMT data blocks.
  `cmtnum` : int
    Number of the CMT to look for.

  Returns
  -------
  List of lines.
  '''
  with open(origfile, 'r') as f:
    data = f.readlines()

  sidx = find_cmt_start_idx(data, 'CMT{:02d}'.format(cmtnum))

  # What should happen if both files don't have the requested CMT?

  orig_data = get_CMT_datablock(origfile, cmtnum)
  if not is_CMT_divider_line(orig_data[-1]):
    print("WARNING: last line of data block in original file is not as expected!")

  data[sidx:(sidx+len(orig_data))] = []

  new_data = get_CMT_datablock(newfile, cmtnum)

  if not is_CMT_divider_line(new_data[-1]):
    if is_CMT_divider_line(orig_data[-1]):
      new_data.append(orig_data[-1])
    else:
      print("WARNING: last line of data block in original file is not as expected!")

  data[sidx:sidx] = new_data

  if overwrite:
    with open(origfile, 'w') as f:
      f.writelines(data)
  else:
    pass

  return data


def get_CMT_datablock(afile, cmtnum):
  '''
  Search file, returns the first block of data for one CMT as a list of strings.
  Ignores empty lines.

  Parameters
  ----------
  afile : str
    Path to a file to search.
  cmtnum : int or str
    The CMT number to search for. Converted (internally) to the CMT key.


  Returns
  -------
  d : [str, str, ...]
    A list of strings, one item for each line in the CMT's datablock.
    Each string will have a newline charachter in it.
  '''
  data = read_paramfile(afile)

  data = [i for i in data if i != '\n']

  if type(cmtnum) == int:
    cmtkey = 'CMT%02i' % cmtnum
  else:
    cmtkey = cmtnum

  startidx = find_cmt_start_idx(data, cmtkey)
  if startidx is None:
    raise RuntimeError("Can't find datablock for CMT: {} in {}".format(cmtkey, afile))

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


def parse_header_line(linedata):
  '''Splits a header line into components: cmtkey, text name, comment.

  Assumes a CMT block header line looks like this:
  // CMT07 // Heath Tundra - (ma.....

  or like this:
  // CMT07 // Heath Tundra // some other comment...

  Parameters
  ----------
  data : string
    Assumed to be valid header line of a CMT datablock. 

  Returns
  -------
  A tuple containing the (cmtkey, cmtname, cmtcomment)
  '''

  header_components = [_f for _f in linedata.strip().split('//') if _f]
  clean_header_components = [i.strip() for i in header_components]

  if len(clean_header_components) < 2:
    print("ERROR! Could not find CMT name in ", clean_header_components)
    sys.exit(-1)

  cmtkey = clean_header_components[0]

  if len(clean_header_components) == 2:

    # Check for old style comment (using - after name)
    if len(clean_header_components[1].split('-')) > 1:
      cmtname = clean_header_components[1].split('-')[0].strip()
      cmtcomment = '-'.join(clean_header_components[1].split('-')[1:])

    # No old comment provided
    else:
      cmtname = clean_header_components[1]
      cmtcomment = ''

  # There must be a comment following the name using // as a delimiter
  if len(clean_header_components) > 2:
    cmtname = clean_header_components[1]
    cmtcomment = ' '.join(clean_header_components[2:])

  return cmtkey, cmtname, cmtcomment



def get_pft_verbose_name(cmtkey=None, pftkey=None, cmtnum=None, pftnum=None, lookup_path=None):
  if lookup_path == "relative_to_dvmdostem":
    path2params = os.path.join(os.path.split(os.path.dirname(os.path.realpath(__file__)))[0], 'parameters/')
  elif lookup_path == "relative_to_curdir":
    path2params = os.path.join(os.path.abspath(os.path.curdir), 'parameters/')
  elif os.path.isdir(lookup_path):
    path2params = lookup_path
  else:
    msg = "ERROR!: lookup_path parameter must be one of 'relative_to_dvmdostem' or 'relative_to_curdir', not {}".format(lookup_path)
    raise ValueError(msg)

  if cmtkey and cmtnum:
    raise ValueError("you must provide only one of cmtkey or cmtnumber")

  if pftkey and pftnum:
    raise ValueError("you must provide only one of pftkey or pftnumber")

  if cmtkey is not None: # convert to number
    cmtnum = int(cmtkey.lstrip('CMT'))

  if pftnum is not None: # convert to key
    pftkey = 'pft%i' % pftnum

  if not (pftnum or pftkey):
    raise ValueError("you must provide a pft number or key!")

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
    values.
  '''

  cmtdict = {}

  pftblock = detect_block_with_pft_info(cmtdatablock)

  hdr_cmtkey, txtcmtname, hdrcomment = parse_header_line(cmtdatablock[0])
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
      if len(dline) > 1:
        comment = dline[1].strip().strip("//").split(':')[0]
      else:
        comment = ''

      if len(values) >= 5: # <--ARBITRARY! likely a pft data line?
        for i, value in enumerate(values):
          cmtdict['pft%i'%i][comment] = float(value)
      else:
        cmtdict[comment] = float(values[0])

  return cmtdict


def format_CMTdatadict(dd, refFile, format=None):
  '''
  Format a block of CMT data.

  `dd` : dict containing parameter names and values for a CMT.

  `refFile` : str with a path to a file that should be used for reference 
  in formatting the output.

  `format` : str (optional) specifying which format to return. Defaults to None.

  Returns
  =======

  `ll` : [str, str, ...] A list of strings that are formatted with fixed width
  columns, 12 chars wide, with 6 places after the decimal, something like this:

      // CMT05 // Tussock Tundra  ...
      //    Betula       Decid.   ...
        400.000000   400.000000   ...
         75.000000    75.000000   ...
         -5.000000    -5.000000   ...
      ...

  '''
  if format is not None:
    print("NOT IMPLEMENTED YET!")
    exit(-1)

  # Figure out which order to print the variables in.
  ref_order = generate_reference_order(refFile)

  # The line list
  ll = []

  # Work on formatting the first comment line
  cmt, name, comment = parse_header_line(get_CMT_datablock(refFile, dd['tag'])[0])
  ll.append("// " + " // ".join((cmt, name, comment)))

  # Now work on formatting the second comment line, which may not exist, or
  # may need to have PFT names as column headers. Look at the keys in the
  # data dict to figure out what to do...
  pftnamelist = []
  for k in sorted(dd.keys()):
    # regular expression matching pft and a digit
    # need this 'cuz cmt_bgcsoil.txt has a parameter named 'propftos'
    # when there is a match, the result is a regular expression object
    # otherwise it is None.
    result = re.match('pft\d', k)
    if result:
      pftnamelist.append(dd[k]['name'])
    else:
      pass # not a PFT key

  if len(pftnamelist) > 0:
    s = " ".join(["{: >12s}".format(i) for i in pftnamelist])
    if s.startswith("  "):
      s2 = "//" + s[2:]
    else:
      print("ERROR!: initial PFT name is too long - no space for comment chars: ", s)
    ll.append(s2)
  else:
    pass # No need for second comment line

  def is_pft_var(v):
    '''Function for testing if a variable is PFT specific or not.'''
    if v not in list(dd.keys()) and v in list(dd['pft0'].keys()):
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
        linestring += "{: >12.6f} ".format(dd[pft][var])
      linestring += ('// %s: ' % var)
      ll.append(linestring)

  for var in ref_order:
    if is_pft_var(var):
      pass # Nothing to do; already did pft stuff
    else:
      # get item from dict, append to line
      ll.append('{:<12.6f} // {}'.format(dd[var], var))

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

  available_cmts = get_CMTs_in_file(aFile)
  if not (len(available_cmts) > 0):
    raise RuntimeError("Invalid file! Can't find any CMT data blocks!")
  print("Using CMT{} as reference...".format(available_cmts[0]['cmtnum']))
  db = get_CMT_datablock(aFile, available_cmts[0]['cmtnum'])

  #pftblock = detect_block_with_pft_info(db)

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
      #print("Found tag:", tag, " Desc: ", desc)
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
  return sorted([i for i in list(dd.keys()) if 'pft' in i])

def enforce_initvegc_split(aFile, cmtnum):
  '''
  Makes sure that the 'cpart' compartments variables match the proportions
  set in initvegc variables in a cmt_bgcvegetation.txt file.

  The initvegc(leaf, wood, root) variables in cmt_bgcvegetation.txt are the
  measured values from literature. The cpart(leaf, wood, root) variables, which 
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

def get_ecosystem_total_C(cmtstr, ref_params_dir):
  

  veg_param_file = os.path.join(os.path.abspath(ref_params_dir), 'cmt_bgcvegetation.txt')
  soil_param_file = os.path.join(os.path.abspath(ref_params_dir), 'cmt_bgcsoil.txt')

  # First start with the vegetation numbers
  d = get_CMT_datablock(veg_param_file, int(cmtstr.upper().lstrip('CMT')))
  dd = cmtdatablock2dict(d)

  vegC = 0.0
  for pft in ['pft{}'.format(i) for i in range(0,10)]:
    
    if dd[pft]['name'].lower() in 'none,misc,misc.,pft0,pft1,pft2,pft3,pft4,pft5,pft6,pft7,pft8,pft9'.split(","):
      pass # This PFT is not defined for this community
      # This is probably unnecessary because generally un-defined PFTs have all 
      # zero values...
    else:
      vegC += dd[pft]['initvegcl']
      vegC += dd[pft]['initvegcw']
      vegC += dd[pft]['initvegcr']

  # Now load up the soil numbers
  d = get_CMT_datablock(soil_param_file, int(cmtstr.upper().lstrip('CMT')))
  dd = cmtdatablock2dict(d)

  soilC = 0.0
  soilC += dd['initshlwc']
  soilC += dd['initdeepc']
  soilC += dd['initminec']

  return vegC + soilC


def percent_ecosys_contribution(cmtstr, tname=None, pftnum=None, compartment=None, ref_params_dir=None):

  pec = 1.0 # Start by assuming everythign has a contribution of 1
  total_C = get_ecosystem_total_C(cmtstr, ref_params_dir)

  veg_param_ref_file = os.path.join(os.path.abspath(ref_params_dir), 'cmt_bgcvegetation.txt')

  if tname == 'OrganicNitrogenSum' or tname == 'AvailableNitrogenSum':
    # These parameters are in cmt_bgcsoil.txt as 'initsoln' and 'initavln'
    # but I am not sure what to do with them yet...
    pec = 1.0

  if tname in ['MossDeathC','CarbonShallow','CarbonDeep','CarbonMineralSum']:
    pec = 1.0

  if pftnum is not None and compartment is None:

    d = get_CMT_datablock(veg_param_ref_file, int(cmtstr.upper().lstrip('CMT')))
    dd = cmtdatablock2dict(d)

    pftstr = 'pft{}'.format(pftnum)
    pft_total_init_c = dd[pftstr]['initvegcl'] + dd[pftstr]['initvegcw'] + dd[pftstr]['initvegcr']
    pec = pft_total_init_c / total_C

  if pftnum is not None and compartment is not None:
    total = get_ecosystem_total_C(cmtstr, ref_params_dir)

    d = get_CMT_datablock(veg_param_ref_file, int(cmtstr.upper().lstrip('CMT')))
    dd = cmtdatablock2dict(d)
    pftstr = 'pft{}'.format(pftnum)

    if compartment == 'Leaf':
      c = 'initvegcl'
    elif compartment == 'Stem':
      c = 'initvegcw'
    elif compartment == 'Root':
      c = 'initvegcr'
    else:
      raise RuntimeError("Invalid compartment specification: {}! Must be one of Leaf, Stem Root".format(compartment)) 

    pec = dd[pftstr][c] / total_C

  #print "cmtstr: {}  tname: {}  pftnum: {}  compartment: {}  PEC: {}".format(cmtstr, tname, pftnum, compartment, pec)
  return pec

def is_ecosys_contributor(cmtstr, pftnum=None, compartment=None, ref_params_dir=None):

  pftstr = 'pft{}'.format(pftnum)

  d = get_CMT_datablock(os.path.join(os.path.abspath(ref_params_dir), 'cmt_bgcvegetation.txt'), int(cmtstr.upper().lstrip('CMT')))
  dd = cmtdatablock2dict(d)

  is_contrib = True

  if pftnum is not None:

    if dd[pftstr]['name'].lower() in 'none,misc,misc.,pft0,pft1,pft2,pft3,pft4,pft5,pft6,pft7,pft8,pft9'.split(","):
      is_contrib = False
    else:
      
      if compartment is not None:
        if compartment == 'Leaf':
          c = 'initvegcl'
        elif compartment == 'Stem':
          c = 'initvegcw'
        elif compartment == 'Root':
          c = 'initvegcr'
        else:
          raise RuntimeError("Invalid compartment specification: {}! Must be one of Leaf, Stem Root".format(compartment))    

        if dd[pftstr][c] <= 0.0:
          is_contrib = False

  return is_contrib

def get_available_CMTs(pdir):
  '''
  Return list of available CMT numbers in directory.

  Only returns CMTs that are defined in all files.

  Assumptions:
   - nothing else in `pdir`
   - parameter files in `pdir` are valid
   - CMTs not defined twice in one file

  Parameters
  ----------
  pdir : str
    Path to directory of dvmdostem parameter files.

  Returns
  -------
  x : list of ints
    A list of all the CMTs available in `pdir`. 
  '''

  all_cmts = set()
  files = os.listdir(pdir)
  for f in files:
    file_cmts = []
    data = get_CMTs_in_file(os.path.join(pdir, f))
    for cmt in data:
      file_cmts.append((cmt['cmtkey'], cmt['cmtnum'], cmt['cmtname'], f))
    file_cmt_set = set([x[1] for x in file_cmts])
    assert len([x[1] for x in file_cmts]) == len(file_cmt_set), "Must not have redundant cmt definitions in a file!: {}".format(f)
    all_cmts = all_cmts.union(file_cmt_set)

  return list(all_cmts)

def which_file(pdir, pname, lookup_struct=None):
  '''
  Given a parameter directory and parameter name, searches the
  files to find which file the parameter is defined in.

  Parameters
  ----------
  pdir : str
    A path to a directort of parameter files.
  pname : str
    Name of the parameter to lookup.
  lookup_struct : dict, default=None
    Mapping from filenames to parameter lists. This optional
    parameter allows passing in the lookup table which will be
    more efficient if `which_file(...)` is called inside a loop
    and the `lookup_struct` doesn't need to be rebuilt each time.

  Returns
  -------
  filename : if found, othewise raises RuntimeError!

  Raises
  ------
  RuntimeError : when parameter is not found in any of the files in the directory.
  '''
  if not lookup_struct:
    lookup_struct = build_param_lookup(pdir)

  for fname, lu in lookup_struct.items():
    if pname in lu['non_pft_params']:
        return fname
    elif pname in lu['pft_params']:
        return fname
    else:
        pass
  raise RuntimeError("Parameter not found!")

def build_param_lookup(pdir):
  '''
  Builds a lookup table, mapping file names to lists of 
  parameters (separate lists for PFT and non PFT params).

  Parameters
  ----------
  pdir : str Path to a folder of parameter files.

  Returns
  -------
  lu : dict 
    A dictionary mapping file names to lists of parameters (pft and non-pft)
    e.g. 
    lu = { 
      'cmt_calparbgc.txt': { 
        'non_pft_params':['kdcsoma', ...], 'pft_params':['cmax', ...] 
      },
      'cmt_bgcsoil.txt': { 
        'non_pft_params':['kdcsoma', ...], 'pft_params':[] 
      },
    }
  '''
  lu = {}
  for f in os.listdir(pdir):
    f = os.path.join(pdir, f) # Maybe this should be abspath(..)?
    cmts = get_CMTs_in_file(f)
    #print(f, len(data))
    # Using a set here, otherwise we get duplicates (one per PFT).
    pft_params = set()
    non_pft_params = set()
    for cmt in cmts:
      db = get_CMT_datablock(f, cmt['cmtnum'])
      db_dict = cmtdatablock2dict(db)
      if detect_block_with_pft_info(db):
        for pft in get_datablock_pftkeys(db_dict):
          plist = [k for k in db_dict[pft] if k not in ['name']]
          [pft_params.add(p) for p in plist]

        not_params = ['tag','cmtname','comment'] + ['pft{}'.format(x) for x in range(0,10)]
        non_pft_plist = [k for k in db_dict if k not in not_params]
        [non_pft_params.add(x) for x in non_pft_plist]
        #print(db_dict.keys())
      else:
        not_params = ['tag', 'name', 'comment', 'cmtname']
        plist = [k for k in db_dict.keys() if k not in not_params]
        [non_pft_params.add(p) for p in plist]

    lu[f] = {'non_pft_params':non_pft_params,'pft_params':pft_params}
  return lu

def update_inplace(new_value, param_dir, pname, cmtnum, pftnum=None):
  '''
  Updates a parameter value in a parameter file. This will overwrite the
  existing parameter file! Also note that it will remove all other CMTs
  in the file.

  Parameters
  ----------
  new_value : float
    The new parameter value.
  param_dir : str
    The directory of parameter files that should be updated.
  pname : str
    The name of the parameter to modify.
  cmtnum : int
    The number of the CMT (community type) where the parameter should be modifed
  pftnum : int
    The number of the PFT that should be modified - only applicable 
    for PFT specific parameters! Otherwise leave as None.

  Returns
  -------
  None
  '''
  f = which_file(param_dir, pname)
  
  cmt_dict = cmtdatablock2dict(get_CMT_datablock(f, cmtnum))

  if pname in cmt_dict.keys():
    # Not a PFT parameter...
    cmt_dict[pname] = new_value
  else:
    pftkey = 'pft{}'.format(pftnum)
    cmt_dict[pftkey][pname] = new_value

  formatted = format_CMTdatadict(cmt_dict, f)

  with open(f, 'w') as updated_file:
    updated_file.write('\n'.join(formatted))  



if __name__ == '__main__':
  import sys
  import argparse
  import textwrap

  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''
      Script for manipulating dvmdostem parameter files.

      '''.format('')
    )
  )

  parser.add_argument('--reformat-block', nargs=2, metavar=('FILE', 'CMT'),
      help=textwrap.dedent('''??'''))

  parser.add_argument('--enforce-initvegc', nargs=2, metavar=('FILE', 'CMT'),
      help=textwrap.dedent('''Reads data from cmt_bgcvegetation.txt file for
        the specified community and adjusts the cpart compartment parmeters so 
        as to match the proportions of the initvegc compartment parameters.
        Re-formats the block of data and prints to stdout.'''))

  parser.add_argument('--replace-cmt-block', nargs=3, metavar=('AFILE','BFILE','CMTNUM'),
      help=textwrap.dedent('''Replaces the CMT datablock in AFILE with the 
        contents CMT data in BFILE. Assumes that the CMTNUM exists in both files!'''))

  parser.add_argument('--compare-cmtblocks', nargs=4, metavar=('AFILE','ANUM','BFILE','BNUM'),
      help=textwrap.dedent('''Do a line by line comparison of the CMT data blocks
        in FILEA and FILEB. The comparison ignores whitespace and numeric formatting.
        prints report indicating which lines match.'''))

  parser.add_argument('--dump-block-to-json', nargs=2, metavar=('FILE', 'CMT'),
      help=textwrap.dedent('''Extract the specific CMT data block from the
        specified data input file and print the contents to stdout as a json
        object (string).'''))

  parser.add_argument('--dump-block', nargs=2, metavar=('FILE', 'CMT'),
      help=textwrap.dedent('''Extract the specific CMT data block from the
        specified input file and print the contents to stdout'''))

  parser.add_argument('--fmt-block-from-json', nargs=2, metavar=('INFILE', 'REFFILE'),
      help=textwrap.dedent('''Reads infile (assumed to be a well formed data
        dict of dvmdostem parameter data in json form), formats the block
        according to the reffile, and spits contents back to stdouts'''))

  parser.add_argument('--report-pft-names', nargs=2, metavar=('INFOLDER', 'CMTNUM'),
      help=textwrap.dedent('''Prints the PFT name lines for each parameter file
        so that it is easy to visually check that all the PFTs are named
        exactly the same for the given %(metavar)s. Might require a wide screen
        to view the columns lined up appropriately! Prints n/a if the CMT
        does not exist in the file.'''))

  parser.add_argument('--report-pft-stats', nargs=2, metavar=('INFOLDER', 'CMTNUM'),
      help=textwrap.dedent('''Prints a tables summarizing the amount of C and N
        allocated to each PFT and the percent contribution to the ecosystem totals
        of C and N. Assumes that a file 'cmt_bgcvegetation.txt' exists in the
        INFOLDER.'''))

  parser.add_argument('--report-cmt-names', nargs=2, metavar=('INFOLDER', 'CMTNUM'),
      help=textwrap.dedent('''Prints the CMT number and name for each file.
        Prints n/a if the CMT does not exist in the file!'''))

  parser.add_argument('--report-all-cmts', nargs=1, metavar=('FOLDER'),
      help=textwrap.dedent('''Prints out a table with all the CMT names found
        in each file found in the %(metavar)s. Only looks at files named like:
        'cmt_*.txt' in the %(metavar)s.'''))

  parser.add_argument('--plot-static-lai', nargs=2, metavar=('INFOLDER','CMT'),
      help=textwrap.dedent('''Makes plots of the static_lai parameter. static_lai
        is a monthly value, so each PFT has 12 entries in the parameter file. 
        The plot shows the values over the year so you can check the seasonality.
        Looks a 'cmt_dimvegetation.txt file in the INFOLDER.'''))
 
  parser.add_argument('--csv2cmtdatablocks', nargs=2, metavar=('CSVFILE', 'CMTNAME'),
      help=textwrap.dedent('''(BETA) Reads data from csv file and prints CMT 
        datablocks to stdout. Expected workflow is that user starts with a spreadsheet
        that is exported to csv, then use this feature is used to parse the csv and 
        print formatted sections of data to stdout that can be pasted into the standard
        dvmdostem space delimited text files that are used for parameters.'''))

  parser.add_argument('--csv-specification', action='store_true',
      help='''Print the specification for supported csv files.''')

  args = parser.parse_args()

  required_param_files = [
    'cmt_bgcsoil.txt',
    'cmt_bgcvegetation.txt',
    'cmt_calparbgc.txt',
    'cmt_dimground.txt',
    'cmt_dimvegetation.txt',
    'cmt_envcanopy.txt',
    'cmt_envground.txt',
    'cmt_firepar.txt',
  ]
  
  if args.csv_specification:
    print(csv_specification.__doc__)
    sys.exit(0)

  if args.csv2cmtdatablocks:
    inputcsv = args.csv2cmtdatablocks[0]
    cmtname = args.csv2cmtdatablocks[1]

    with open(inputcsv) as f:
      data = f.readlines()

    for (start, section_name) in find_section_starts(data):
      print(" ----  {}  ----  CMT {}  ----".format(section_name, cmtname))
      print(format_section(get_section(data, start), data))
      print("")

    sys.exit(0)

  if args.report_pft_stats:
    infolder = args.report_pft_stats[0]
    cmtnum = int(args.report_pft_stats[1])

    src_file = os.path.join(infolder, 'cmt_bgcvegetation.txt')

    db = get_CMT_datablock(src_file, cmtnum)
    dd = cmtdatablock2dict(db)

    ecosystem_total_C = 0.0
    for pft in get_datablock_pftkeys(dd):
      ecosystem_total_C += dd[pft]['initvegcl']
      ecosystem_total_C += dd[pft]['initvegcw']
      ecosystem_total_C += dd[pft]['initvegcr']

    print("Reading from file: {}".format(src_file))
    print("{:<6} {:>12} {:>10} {:>12} {:>8} {:>8} {:>8}".format(' ','name','% veg C', 'C', 'leaf C', 'wood C', 'root C'))
    whole_plant_C = 0.0
    for pft in get_datablock_pftkeys(dd):
      whole_plant_C = (dd[pft]['initvegcl'] + dd[pft]['initvegcw'] + dd[pft]['initvegcr'])
      frac_C = whole_plant_C / ecosystem_total_C
      print("{:<6} {:>12} {:>10.2f} {:>12} {:>8} {:>8} {:>8}".format(
          pft, dd[pft]['name'], frac_C*100, whole_plant_C,
          dd[pft]['initvegcl'], dd[pft]['initvegcw'], dd[pft]['initvegcr']
      ))
    print("{:<6} {:>12} {:>10} {:->12} {:>8} {:>8} {:>8}".format('','','','','','',''))
    print("{:>31} {:>11.2f}".format("Community Total Vegetation C:", ecosystem_total_C))
    print("")

    ecosystem_total_N = 0.0
    for pft in get_datablock_pftkeys(dd):
      ecosystem_total_N += dd[pft]['initvegnl']
      ecosystem_total_N += dd[pft]['initvegnw']
      ecosystem_total_N += dd[pft]['initvegnr']

    print("Reading from file: {}".format(src_file))
    print("{:<6} {:>12} {:>10} {:>12} {:>8} {:>8} {:>8}".format(' ','name','% veg N', 'N', 'leaf N', 'wood N', 'root N'))
    whole_plant_N = 0.0
    for pft in get_datablock_pftkeys(dd):
      whole_plant_N = (dd[pft]['initvegnl'] + dd[pft]['initvegnw'] + dd[pft]['initvegnr'])
      frac_N = whole_plant_N / ecosystem_total_N
      print("{:<6} {:>12} {:>10.2f} {:>12} {:>8} {:>8} {:>8}".format(
          pft, dd[pft]['name'], frac_N*100, whole_plant_N,
          dd[pft]['initvegnl'], dd[pft]['initvegnw'], dd[pft]['initvegnr']
      ))
    print("{:<6} {:>12} {:>10} {:->12} {:>8} {:>8} {:>8}".format('','','','','','',''))
    print("{:>31} {:>11.2f}".format("Community Total Vegetation N:", ecosystem_total_N))
    print("")
 
    sys.exit(0)

  if args.plot_static_lai:
    infolder = args.plot_static_lai[0]
    cmtnum = int(args.plot_static_lai[1])

    print(infolder, cmtnum)
    print("Reading: {}".format(os.path.join(infolder, "cmt_dimvegetation.txt")))

    db = get_CMT_datablock(os.path.join(infolder, "cmt_dimvegetation.txt"), cmtnum)
    dd = cmtdatablock2dict(db)

    # Print tabular report
    print("{:>12}   jan   feb   mar   apr   may   jun   jul   aug   sep   oct   nov   dec".format(" "))
    for key in sorted([x for x in list(dd.keys()) if 'pft' in x]):
      pft = dd[key]
      print("{:>12}".format(pft['name']), end=' ')
      static_lai = [ pft['static_lai[%s]'%m] for m in range(0,12) ]
      print("{:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}  {:.2f}".format(*static_lai))

    # make plots, keep imports here so that other features of the script 
    # can be used withough maplotlib installed.
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(len([x for x in list(dd.keys()) if 'pft' in x])+1, 1, sharex=True)
    for i, key in enumerate(sorted([x for x in list(dd.keys()) if 'pft' in x])):
      static_lai = [ dd[key]['static_lai[%s]'%m] for m in range(0,12) ]
      l = axes[0].plot(list(range(0,12)), static_lai, label=dd[key]['name'])
      axes[i+1].plot(list(range(0,12)), static_lai, label=dd[key]['name'], color=l[0].get_color(), marker='o')
      axes[i+1].set_ylabel(dd[key]['name'], rotation=0, labelpad=35)
      axes[i+1].scatter(0.5,dd[key]['initial_lai'], marker='x', color='black')

    plt.suptitle("file: {}\n CMT: {}".format(
        os.path.abspath(os.path.join(infolder, "cmt_dimvegetation.txt")),
        cmtnum
    ))
    axes[-1].set_xticks(list(range(0,12)))
    axes[-1].set_xticklabels('jan,feb,mar,apr,may,jun,jul,aug,sep,oct,nov,dec'.split(','))
    #from IPython import embed; embed()
    plt.show(block=True)

    sys.exit(0)

  if args.compare_cmtblocks:
    fileA, numA, fileB, numB = args.compare_cmtblocks
    numA = int(numA)
    numB = int(numB)
    print("Comparing:")
    print("      CMT {} in {} ".format(fileA, numA))
    print("      CMT {} in {} ".format(fileB, numB))

    compare_CMTs(fileA, numA, fileB, numB)
    sys.exit(0)

  if args.replace_cmt_block:
    A, B, cmtnum = args.replace_cmt_block
    # Print the result to stdout, where it can be inspected and or 
    # re-directed to a file
    lines = replace_CMT_data(A, B, int(cmtnum))
    for l in lines:
      print(l.rstrip("\n"))
    sys.exit(0)

  if args.report_pft_names:

    infolder = args.report_pft_names[0]
    cmtnum = int(args.report_pft_names[1])

    print("Checking for {}".format(cmtnum))
    for f in required_param_files:
      f2 = os.path.join(infolder, f)

      cmts_in_file = get_CMTs_in_file(f2)
      cmt_numbers = [cmt['cmtnum'] for cmt in cmts_in_file]
      if cmtnum not in cmt_numbers:
        print("{:>45s} {}".format(f2, "n/a"))
      else:
        db = get_CMT_datablock(f2, cmtnum)
        if detect_block_with_pft_info(db):
          print("{:>45s}: {}".format(f2, (db[1]).strip()))
        else:
          pass #print "{} is not a pft file!".format(f)
    sys.exit(0)

  if args.report_all_cmts:

    infolder = args.report_all_cmts[0]

    all_files = glob.glob(os.path.join(args.report_all_cmts[0], 'cmt_*.txt'))

    for f in all_files:
      cmts = get_CMTs_in_file(f)
      print(f)
      print("{:>7} {:>5}   {:<50s} {}".format('key', 'num', 'name', 'comment'))
      for c in cmts:
        print("{:>7} {:>5d}   {:50s} {}".format(c['cmtkey'], c['cmtnum'], c['cmtname'], c['cmtcomment']))
      print("")

    sys.exit(0)

  if args.report_cmt_names:

    infolder = args.report_cmt_names[0]
    cmtnum = int(args.report_cmt_names[1])

    print("{:>45s} {:>8s}   {}".format("file name","cmt key","long name"))
    for f in required_param_files:
      f2 = os.path.join(infolder, f)

      cmts_in_file = get_CMTs_in_file(f2)
      cmt_numbers = [cmt['cmtnum'] for cmt in cmts_in_file]
      if cmtnum not in cmt_numbers:
        print("{0:>45s} {1:>8s}   {1}".format(f2, "n/a"))

      else:
        db = get_CMT_datablock(f2, cmtnum)
        dd = cmtdatablock2dict(db)
        print("{:>45s} {:>8s}   {}".format(f2, dd['tag'], dd['cmtname']))
    sys.exit(0)

  if args.fmt_block_from_json:
    inFile = args.fmt_block_from_json[0]
    refFile = args.fmt_block_from_json[1]
    with open(inFile) as data_file:
      dd = json.load(data_file)
    lines = format_CMTdatadict(dd, refFile)
    for l in lines:
      print(l)
    sys.exit(0)

  if args.dump_block:
    theFile = args.dump_block[0]
    cmt = int(args.dump_block[1])
    d = get_CMT_datablock(theFile, cmt)
    print(''.join(d))
    sys.exit(0)

  if args.dump_block_to_json:
    theFile = args.dump_block_to_json[0]
    cmt = int(args.dump_block_to_json[1])
    d = get_CMT_datablock(theFile, cmt)
    dd = cmtdatablock2dict(d)
    # Dumping to a string (json.dumps()) before printing helps make sure
    # that only double quotes are used, wich is critical for valid json
    # and reading back in as a json object
    print(json.dumps(dd))
    sys.exit(0)

  if args.reformat_block:
    theFile = args.reformat_block[0]
    cmt = int(args.reformat_block[1])
    d = get_CMT_datablock(theFile, cmt)
    dd = cmtdatablock2dict(d)
    lines = format_CMTdatadict(dd, theFile)
    for l in lines:
      print(l)
    sys.exit(0)

  if args.enforce_initvegc:
    theFile = args.enforce_initvegc[0]
    cmt = int(args.enforce_initvegc[1])
    dd = enforce_initvegc_split(theFile, cmt)
    lines = format_CMTdatadict(dd, theFile)
    for l in lines:
      print(l)
    sys.exit(0)



