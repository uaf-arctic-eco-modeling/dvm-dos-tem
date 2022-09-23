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
import subprocess
import tempfile

# For command line interface
import sys
import argparse
import textwrap


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
  re-build lookup data structures to find parameter names or files.

  With this object the idea is to set the parameter directory upon
  instantiation, and build the lookup data structure. Then future
  operations can use that cached structure.

  Examples
  --------
  >>> import param_util as pu
  >>> psh = pu.ParamUtilSpeedHelper("/work/parameters")
  >>> psh.get_value(pname='cmax', cmtnum=4, pftnum=3, with_metadata=False)
  13.45

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


def fwt2csv_v1(param_dir, req_cmts='all', targets_path=None):
    '''
    Convert from dvmdostem fixed width text (fwt) format to CSV (comma separated
    values), version 1.

    Writes one file for each CMT, with all parameters from the fixed width
    files. The output files will be named like "SAMPLE_CMT_01.csv", etc and 
    will be written in your current working directory.
    
    Parameters
    ==========
    param_dir : string, path
      Path to a directory of parameter files to convert.

    req_cmts : list of ints or string
      A list of the requested CMTs (numbers) or the string 'all'.

    targets_path : string, path
      Path to a targets file to convert.

    Returns
    =======
    None
    '''
    # NOTE: currently there is no mechanism for storing reference data in the 
    # fixed width text files....

    avail_cmts = get_available_CMTs(param_dir)

    if req_cmts == 'all':
      cmts = avail_cmts
    else:
      cmts = req_cmts

    if not all([i in avail_cmts for i in cmts]):
      raise RuntimeError("One of the requested cmts is not available! Requested: {}".format(req_cmts))

    for cmt in cmts:
      print("Working on CMT {}...".format(cmt))
      meta = []
      pftdata = []
      nonpftdata = []

      meta.append('file,cmtkey,cmtname,comment\n')
      pftdata.append('file,name,0,1,2,3,4,5,6,7,8,9,units,description,comment,refs\n')
      nonpftdata.append('file,name,value,units,description,comment,refs\n')

      if targets_path:
        # Try importing parameter data
        if os.path.exists(targets_path):
          try:
            sys.path.append(os.path.dirname(targets_path))
            from calibration_targets import calibration_targets as targets
          except:
            print("Problem importing calibration targets!")
        else:
          raise RuntimeError("Can't find targets file!")


        for cmtname, tvals in targets.items():
          if cmtname == 'meta':
            pass # nothing to do here...
          else:
            if targets[cmtname]['cmtnumber'] in cmts:
              for k,v in targets[cmtname].items():

                if k in ['meta']:
                  pass

                elif k == 'cmtnumber':
                  meta.append('{},{},{},"{}"\n'.format(targets_path, targets[cmtname]['cmtnumber'], cmtname, "comment"))

                elif k == 'PFTNames':
                  s = '{},PFTNames,'.format(targets_path)
                  for i in range(0,10):
                    s += "{},".format(v[i])
                  s += '"{}","{}","{}","{}"\n'.format("units", "desc","comment", "ref")
                  pftdata.append(s)

                elif isinstance(v, (int, float)) and not isinstance(v, bool):
                  #print("--->", k, v)
                  units = targets['meta'][k]['units']
                  desc = targets['meta'][k]['desc']
                  comment = targets['meta'][k]['comment']
                  ref = targets['meta'][k]['ref']
                  nonpftdata.append('{},{},{},"{}","{}","{}","{}"\n'.format(targets_path, k, v, units, desc, comment, ref))

                elif isinstance(v, (list)):
                  units = targets['meta'][k]['units']
                  desc = targets['meta'][k]['desc']
                  comment = targets['meta'][k]['comment']
                  ref = targets['meta'][k]['ref']
                  s = ''
                  s += '{},{},'.format(targets_path, k)
                  for i in range(0,10):
                    s += '{:0.3f},'.format(v[i])
                  s += '"{}","{}","{}","{}"\n'.format(units, desc, comment, ref)
                  pftdata.append(s)

                elif isinstance(v, (dict)):
                  s = ''
                  for cmpt, data in v.items():
                    units = targets['meta'][k][cmpt]['units']
                    desc = targets['meta'][k][cmpt]['desc']
                    comment = targets['meta'][k][cmpt]['comment']
                    s += '{},'.format(targets_path)
                    s += '{}:{},'.format(k,cmpt)
                    for i in range(0,10):
                      s += '{:0.3f},'.format(data[i])
                    s += '"{}","{}","{}","{}"\n'.format(units, desc, comment, ref)
                  pftdata.append(s)

                else:
                  print("Here?? ")


      for f in os.listdir(param_dir):
        pfile = os.path.join(param_dir, f)
        print(pfile)
        if isParamFile(pfile):
          db = get_CMT_datablock(pfile, cmt)
          dd = cmtdatablock2dict(db)

          if detect_block_with_pft_info(db):

            s = ''
            # Add line for pft numbers
            s += '{},pftkey,'.format(pfile)
            for pft in sorted(get_datablock_pftkeys(dd)):
              s += "{},".format(pft)
            s += '\n'

            # Add line for pft verbose names
            s += '{},pftname,'.format(pfile)
            for pft in sorted(get_datablock_pftkeys(dd)):
              s += "{},".format(dd[pft]['name'])
            s += '\n'

            # add line for each variable
            vnames = [x for x in dd['pft0'].keys() if x != 'name']  # <---IMPROVE THIS!
            vnames = [x for x in vnames if 'units_' not in x]
            vnames = [x for x in vnames if 'desc_' not in x]
            vnames = [x for x in vnames if 'comment_' not in x]
            vnames = [x for x in vnames if 'refs_' not in x]

            for v in vnames:
              s += "{},{},".format(pfile, v)
              for pft in sorted(get_datablock_pftkeys(dd)):
                #s += "{:0.3f},".format(dd[pft][v])
                s += '{},'.format(smart_format(dd[pft][v]))
              s += '{},'.format(dd[pft]['units_{}'.format(v)])
              s += '"{}",'.format(dd[pft]['desc_{}'.format(v)])
              s += '"{}",'.format(dd[pft]['comment_{}'.format(v)])
              s += '"{}"'.format(dd[pft]['refs_{}'.format(v)])
              s += '\n'
            pftdata.append(s)

          s = ''
          nonpftvars = [x for x in dd.keys() if x not in ['tag','cmtname','comment']] # Alternate formulation? filter(lambda x: x not in ['tag','cmtname','comment'], dd.keys())
          nonpftvars = [x for x in nonpftvars if 'pft' not in x]
          nonpftvars = [x for x in nonpftvars if '_' not in x]
          #s += '{},{},{},"{}"\n'.format('file','pname','pvalue','comment')
          for i in nonpftvars:
            #file,name,value,units,description,comment,refs
            dataline = '{},{},{},{},"{}","{}","{}"\n'.format(
              pfile, i, dd[i],
              dd['units_{}'.format(i)], 
              dd['desc_{}'.format(i)], 
              dd['comment_{}'.format(i)],
              dd['refs_{}'.format(i)]
            )
            nonpftdata.append(dataline)

          meta.append('{},{},{},"{}"\n'.format(pfile, dd['tag'], dd['cmtname'], dd['comment']))

        else:
          print(" ********* deemed {} as non parameter file, skipping!  *********\n".format(pfile))
          pass # nothing to do for non-param files

      with open("SAMPLE_CMT_{:02d}.csv".format(cmt), 'w') as f:
        label = subprocess.check_output(["git", "describe"],).strip().decode('utf-8')
        cmtname = '??' 
        desc = 'A long winded description. Spaces? Quotes? Special charachters?'
        site = 'The site specification. Make a standard for coords?'
        notes = 'Any other notes, date of calibration, calibrator? references?'
        ref_file = 'refs.bib'
        hdr = ''
        hdr += textwrap.dedent('''\
        #
        # dvmdostem parameters: {}
        # cmtnumber: {}
        # cmtname: {}
        # cmtdescription: "{}"
        # calibration site: "{}"
        # calibration notes: "{}"
        # references file: {}
        #
        # This file was generated using the param_util.fwt2csv_v1(...) function.
        # There are columns here (comment units desc refs)
        # that are not represented in a standard way in the 
        # fixed width text parameter files.
        # 
        # To convert this file back to fixed width text for use with dvmdostem,
        # see the param_util.csv2fwt_v1() function. 
        # 
        '''.format(label, cmt, cmtname, desc, site, notes, ref_file))

        f.writelines(hdr)

        f.writelines(meta)
        f.writelines("\n\n")
        f.writelines(pftdata)
        f.writelines("\n\n")
        f.writelines(nonpftdata)


def csv2fwt_v1(csv_file, ref_directory='../parameters', 
            overwrite_files=None, ref_targets=None):
  '''
  Convert from csv parameter files to fixed width text format.

  Uses csv_v1_specification().

  Unrefined function that depends on the csv file being
  appropriately formatted in a variety of ways, including at least:
   - consistent pft names
   - all variables present
   - calibration targets variables for leaf/stem/roots being named as follows
     - VegCarbon:Leaf, etc
     - VegStructuralNitrogen:Leaf, etc
   - PFT names <= 12 characters long
   - consistent CMT names
  
  Parameters
  ==========
  csv_file : string, path
    Path to an input csv file to convert.

  ref_directory : string, path
    Path to a folder containing parameter files to be used as reference for
    formatting the resulting fixed width data.
  
  ref_targets : string, path
    Path to a calibration_targets.py file that will be used for reference in
    formatting the resulting data.
  
  overwrite_files : bool
    (experimental) Flag for determining whether to print results to stdout
    (default) or to overwrite the data in the reference files. May not work if
    the CMT number in the csv file is not present in the reference files.

  Return
  ======
  Zero.
  '''

  sections = csv_v1_find_section_indices(csv_file)

  with open(csv_file, 'r') as f:
    data = f.readlines()

  pft_data = csv_v1_read_section(data, bounds=sections['pft'])
  nonpft_data = csv_v1_read_section(data, bounds=sections['nonpft'])
  meta = csv_v1_read_section(data, bounds=sections['meta'])

  # The csv_v1_read_section function doesn't work well for the header comments
  # as the data is not csv and doesn't parse easily using csv.reader.
  # So we can parse it manually here. Goal is to pull out all the relevant 
  # metadata, strip off extraneous charachters (#, \n, etc) and print the data
  # in comment lines in the fixed width text files.
  commentstr = ''
  s, e = sections['headercomments']
  for i, line in enumerate(data[s:e]):
    l2 = line.split(':')
    if len(l2) > 1:
      k = l2[0].strip().strip('#').strip('"').strip('#')
      v = ''.join(l2[1:]).strip().strip(',')
      if k.strip() == 'cmtnumber' or k.strip() == 'cmtname':
        pass
      else:
        commentstr += "// {} // {}\n".format(k, v)
  # Will use this commentstr later in the fucntion when assembling the output.

  if ref_targets:
    # Take care of the targets data - this is formatted differently from
    # the other parameters. While the other parameters are the fixed width
    # text format, the calibration targets are stored in a python object.
    # So here we print the object out
    if not(os.path.exists(ref_targets)):
      print("ERROR - targets ({}) don't exist, quitting.".format(ref_targets))
      exit(-1)

    print(ref_targets)

    # filter by column with the file name/path in it
    relevant_pft_vars = list(filter(lambda x: ref_targets in x['file'], pft_data))
    relevant_nonpft_vars = list(filter(lambda x: ref_targets in x['file'], nonpft_data))
    relevant_meta = list(filter(lambda x: ref_targets in x['file'], meta))

    if all(map(lambda x: len(x)<1, [relevant_pft_vars, relevant_meta, relevant_nonpft_vars])):
      raise RuntimeError("Invalid ref_targets file! Can't find appropriate data.")

    new_targs = {}

    for i in relevant_nonpft_vars:
      new_targs[i['name']] = i['value']

    for i in relevant_pft_vars:
      l = []
      for pftnum in range(0,10):
        if i['name'] == 'PFTNames':
          l.append(i[str(pftnum)])
        else:
          l.append(float(i[str(pftnum)]))

      if ':' in i['name']:
        a, b = i['name'].split(':')
        if a not in new_targs:
          new_targs[a] = dict()
        new_targs[a][b] = l
      else:
        new_targs[i['name']] = l

    # Print it out in some kind of semi-reasonable format...
    new_targs['cmtnumber'] = relevant_meta[0]['cmtkey']
    full_string = ''
    full_string += "'{}' : {{\n".format(relevant_meta[0]['cmtname'])
    for k, v in new_targs.items():
      if isinstance(v, list):
        if k == 'PFTNames':
          full_string += "  '{}':  {},\n".format(k, v)
        else:
          u = ['{:0.3f}, ' for i in v]
          s = "".join(u).format(*v)
          full_string += "  '{}':  [{}],\n".format(k, s)
      elif isinstance(v, dict):
        full_string += "  '{}': {{\n".format(k)
        for kk, vv in v.items():
          u = ['{:0.3f}, ' for i in vv]
          s = "".join(u).format(*vv)
          full_string += "    '{}' : [{}],\n".format(kk, s)
        full_string += "  },\n"
      else:
        full_string += "  '{}': {},\n".format(k, v)
    full_string += "}\n"
    print(full_string)

  ## All other parameters (not calibration targets)
  for reffile in os.listdir(ref_directory):
    print(reffile)

    relevant_pft_vars = list(filter(lambda x: reffile in x['file'], pft_data))
    relevant_nonpft_vars = list(filter(lambda x: reffile in x['file'], nonpft_data))
    relevant_meta = list(filter(lambda x: reffile in x['file'], meta))

    # Handle the datablock header
    full_string = '//==========================================================\n'
    full_string += '// {} // {} // {}\n'.format(relevant_meta[0]['cmtkey'], relevant_meta[0]['cmtname'], relevant_meta[0]['comment'])
    full_string += commentstr # This was built up earlier when parsing the file.

    # Handle the PFT header line
    if len(list(filter(lambda x: x['name'] == 'pftname', relevant_pft_vars))) > 0:
      s = '//' # Comment out the header line for PFT Names
      k = [x for x in relevant_pft_vars if x['name'] == 'pftname']
      for i in range(0,10):
        s += '{:>12} '.format(k[0][str(i)])
      s += '// name: units // description // comment // refs\n'
      full_string += s

    # Handle the data
    order = generate_reference_order(os.path.join(ref_directory, reffile))
    for v in order:
      p = list(filter(lambda x: x['name'] == v, relevant_pft_vars))
      n = list(filter(lambda x: x['name'] == v, relevant_nonpft_vars))
      if len(p) > 0 and len(n) > 0:
        raise RuntimeError("Something is wrong...")

      if len(p) > 0:
        p = p[0]
        # it is a pft variable...
        # start with 2 spaces so that columns line up with commented PFT name
        # line above...
        s = '  '
        for i in range(0,10):
          s += smart_format(p[str(i)])
        s += '// {}: {} // {} // {} // {}\n'.format(p['name'], p['units'], p['description'], p['comment'], p['refs'])
        full_string += s

      elif len(n) > 0:
        n = n[0]
        # is is a non-pft variable...
        s = '{val} // {name}: {units} // {desc} // {comment} // {refs}\n'
        s = s.format(val=smart_format(n['value']), name=n['name'], units=n['units'],
          desc=n['description'], comment=n['comment'], refs=n['refs'])
        full_string += s
    if overwrite_files:
      with tempfile.NamedTemporaryFile(mode='w+t') as temp:
        temp.writelines(full_string)
        temp.flush()
        replace_CMT_data(os.path.join(ref_directory, reffile), temp.name, 0, overwrite=True)
    else:
      print(full_string)
      print()
      print()

  return 0


def smart_format(x, n=6, basefmt='{:12.4f} ', toolongfmt='{:12.3e} '):
  '''
  Provides a flexible method for printing different number formats.

  Tries to assess the length of the string version of x and apply different
  formats based on the length. While the formats are flexible using 
  keyword arguments, the defauts are generally for fixed decimal notation for
  shorter numbers and scientific notation for longer numbers.

  Parameters
  ----------
  x : anything that can cast to a float
    The value to format.

  n : int
    The length at which the function switches between basefmt and toolongfmt.

  basefmt :  a format string
    The format to use for x if string representation of x is shorter than n.

  toolongfmt : a format string
    The format to use for x if string representation of x is longer than n.

  Returns
  -------
  str : formatted version of x
  '''
  if type(x) == str:
    if x == '0':
      pass
    else:
      x = x.strip()
      x = x.strip('0')

  if len(str(x).strip()) > n:
    return toolongfmt.format(float(x))
  else:
    return basefmt.format(float(x))


def csv_v1_specification():
  '''
  Specification for v1 csv files for holding parameter data.

  Each csv file will hold the data for one Community Type (CMT). As such the csv
  file will be broken into sections to accomodate the different number of
  columns in different sections. The sections of the file will be: 
   - a metadata section,
   - a section for PFT specific parameters, and
   - a section for non-PFT parameters.

  Each section will begin with a header line that describes the columns.
  
  The header for the metadata will be: 
  file,cmtkey,cmtname,comment

  The header for the PFT section will be:
  file,name,0,1,2,3,4,5,6,7,8,9,units,description,comment,refs

  The header for the non-PFT section will be:
  file,name,value,units,description,comment,refs

  Each section will end with two consecutive blank lines.

  Note that csv files prepared from different spreadsheet programs may have
  different treatment regarding blank lines and rows with varying numbers of
  columns. Many programs will produce files with lots of extra commas 
  deliniating empty columns. Some of these extraneous commas have been omitted 
  in the sample below.

  Example data:

  # dvmdostem parameters: v0.5.6-178-g4cdb7c34
  # cmtnumber: 22
  # cmtname: Single PFT Alpine Tussock Tundra
  # cmtdescription: alpine tussock tundra for Interior Alaska ....
  # calibration site: The sentinel site used ....
  # calibration notes: Calibration conducted manually by Joy ... 
  # references file: refs.bib
  #
  # To convert this file back to fixed width text for use with dvmdostem
  # see the param_util.csv2fwt_v1() function.
  #
  file,cmtkey,cmtname,comment,,,,,,,,,,,,
  ../parameters/cmt_bgcvegetation.txt,CMT22,Single PFT Alpine Tussock Tundra,,,,,,,,,,,,,
  ../parameters/cmt_dimvegetation.txt,CMT22,Single PFT Alpine Tussock Tundra,,,,,,,,,,,,,
  ,,,,,,,,,,,,,,,
  ,,,,,,,,,,,,,,,
  file,name,0,1,2,3,4,5,6,7,8,9,units,description,comment,refs
  ../calibration/calibration_targets.py,PFTNames,ecosystem,pft1,pft2,pft3,pft4,pft5,pft6,pft7,pft8,pft9,,,,
  ../calibration/calibration_targets.py,VegCarbon:Leaf,320.2073015,0,0,0,0,0,0,0,0,0,,,,
  ../calibration/calibration_targets.py,VegCarbon:Root,480.9949012,0,0,0,0,0,0,0,0,0,,,,
  ,,,,,,,,,,,,,,,
  ,,,,,,,,,,,,,,,
  file,name,value,units,description,comment,refs,,,,,,,,,
  ../calibration/calibration_targets.py,AvailableNitrogenSum,1.7,,,,,,,,,,,,,
  ../calibration/calibration_targets.py,MossDeathC,0,,,,,,,,,,,,,
  ../parameters/cmt_bgcsoil.txt,fnloss,0,,  fraction N leaching (0 - 1) when drainage occurs,,,,,,,,,,,
  ../parameters/cmt_bgcsoil.txt,fsompr,0.611,,,,,,,,,,,,,
  '''
  pass # Do nothing, simply a docstring function!


def csv_v1_find_section_indices(csv_file):
  '''
  Parses a csv file and returns the starting and ending indices for each 
  section in the file.

  Uses csv_v1_specification().

  Returns
  =======
  sections : dict
    Mapping of section names to a pair of ints representing the start and end
    indices of the section, for example: 
    {'meta':(0,5), 'pft':(8,25), 'nonpft':(25,35)}
  '''

  sections = {}

  with open(csv_file, 'r') as f:
    data = f.readlines()

  for i, line in enumerate(data):
    if len(line) > 0 and line[0] == '#':
      pass # skipping comments...
    elif 'file,cmtkey,cmtname,comment' in line:
      sections['meta'] = [i, None]
    elif 'file,name,0,1,2,3,4,5,6,7,8,9,units,description,comment,refs' in line:
      sections['pft'] = [i, None]
    elif 'file,name,value,units,description,comment,refs' in line:
      sections['nonpft'] = [i,None]

  for section, (start, end) in sections.items():
    for i, line in enumerate(data[start:]):
      ldata = [x.strip() for x in line.split(',')]
      if len(ldata) == 0 or ldata[0] == '':
        sections[section][1] = sections[section][0] + i
        break

  # The header comments are assumed to run from the start of the file
  # to the line right before the meta section starts.
  sections['headercomments'] = [0, sections['meta'][0]-1]

  return sections


def csv_v1_read_section(data, bounds):
  '''
  Write this...

  Uses csv_v1_specification().

  Parameters
  ==========
  data : list
    The list of lines of a specially formatted csv file.
  bounds : tuple
    Pair of ints representing the starting and ending indices of a section.

  Returns
  =======
  A list of dicts produced by csv.DictReader, one key for each column name.
  '''
  start = bounds[0]
  end = bounds[1]
  csvreader = csv.DictReader(data[start:end], dialect='excel')
  return [row for row in csvreader]


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


def csv_v0_specification():
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


def csv_v0_get_pftnames(data):
  '''
  Retrieves PFT names from a specially formatted csv file.

  Assumes that `data` is a list of lines read from a csv file that
  is formatted according to the csv_v0_specification. See help for the
  csv_v0_specification() function.

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


def csv_v0_find_section_starts(data):
  '''
  Gets the starting index and name for sections of data in a specially formatted csv file.

  Assumes that `data` is a list of lines read from a csv file. See help
  (docstring) for csv_v0_specification().

  Parameters
  ----------
  data : list of strings, required
    Assumed to be a list generated by reading a csv file that is
    formatted as in csv_v0_specification.

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
    if all(x == '' for x in row[1:]): # found a blank line
      if len(row) > 0 and row[0] != '': # found a
        if row[0].isupper():
          #print(i, row)
          starts.append(i)
          sections.append(row[0])
  results = list(zip(starts, sections))
  return results


def csv_v0_get_section(data, start):
  '''
  Extracts a section of block of data from a specially formatted csv file.

  Assumes that `data` is a list of lines read from a csv file. See help 
  (the docstring) for the csv_v0_specification() function to get more details
  on how the csv file should be setup.

  Parameters
  ----------
  data : list of strings, required
    Assumed to be a list generated by reading a csv file that is formatted as 
    described in the docstring for csv_v0_specification()
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


def format_section_csv_v0(section_data, full_data):
  '''
  Prints data (presumably from csv file) to dvmdostem space delimited parameter format.

  No effort is made to standardize the variable names or comments in the resulting
  block. Used a fixed width column, space delimited.

  See the help for csv_v0_specification() function to find more info on how the
  csv file should be formatted.

  Parameters
  ----------
  section_data : list
    Assumed to be a list of lines for one section of data read from a csv file. The csv 
    file must be formatted as described in the docstring for csv_v0_specification().
    
  full_data : list
    Assumed to be a list of lines of all the data read from a csv file. The csv 
    file must be formatted as described in the docstring for csv_v0_specification().

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
  # something like CMT00

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

  # Standardize whitespace and numeric format using the formatting function.
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


def keyFnum(x):
  '''
  Given a number
  
  Examples:

  >>> keyFnum(4)
  'CMT04'

  >>> keyFnum(0)
  'CMT00'

  >>> keyFnum('4')
  'CMT04'

  >>> keyFnum('000')
  'CMT00'

  >>> keyFnum('101')
  Traceback (most recent call last):
    ...
  RuntimeError: Out of range 0 <= x <= 99

  >>> keyFnum(101)
  Traceback (most recent call last):
    ...
  RuntimeError: Out of range 0 <= x <= 99
  
  >>> keyFnum('  5 ')
  'CMT05'
  
  >>> keyFnum('50 0')
  Traceback (most recent call last):
    ...
  ValueError: invalid literal for int() with base 10: '50 0'
  '''
  num = int(x)
  if num < 0 or num > 99:
    raise RuntimeError("Out of range 0 <= x <= 99")
  
  return 'CMT{:02}'.format(num)


def isParamFile(x):
  '''
  Check to see if a file is likely a dvmdostem parameter file.
  '''
  if os.path.isfile(x):
    try:
      cmts = get_CMTs_in_file(x)
    except UnicodeDecodeError:
      return False

    if len(cmts) > 0:
      return True

  return False


def isCMTkey(x):
  '''
  Function for testing validity of a CMT key specifier.

  Examples:
  =========
  >>> [isCMTkey(x) for x in ('cmt04', 'cmt999', 'CMt56', 'CMT4y6', 'CMT00')]
  [True, False, True, False, True]

  >>> [isCMTkey(x) for x in ('cmt00', 'cmt1234', 'c mtx', ' cmt09', 'cmt04 ',)]
  [True, False, False, True, True]

  >>> [isCMTkey(x) for x in ('cmt 23', '4', '04', '0004', 'cmt4')]
  [True, False, False, False, False]
  '''

  if type(x) != str:
    return False #, "Not a string."

  x = x.strip()
  x = x.replace(' ','')

  if not x.isalnum():
    return False #, "Not an alphanumeric string"

  a = x[0:3]
  b = x[3:]
  if not b.isnumeric():
    return False #, End of specifier not a number

  if int(b) < 0 or int(b) > 99:
    return False #, Number out of range

  if x[0:3].upper() != 'CMT':
    return False #, "first 3 chars not CMT"

  if not x[-2:].isnumeric():
    return False #, "Last 2 chars not numeric"

  return True


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
      continue # Nothing to do...commented line
    else:
      data, *meta = line.strip().split('//')

      data = data.strip().split()

      vname = units = desc = comment = refs = ''

      if len(meta) < 1:
        raise RuntimeError("Invalid file - must have metadata for variable!")

      if len(meta) >= 1:
        if len(meta[0].strip().split(':')) != 2:
          raise RuntimeError("Problem with formatting of name:units for {} (line: {})".format(meta, line))
        vname, units = meta[0].strip().split(':')

      if len(meta) >= 2:
        # must have the name/units and desc fields
        desc = meta[1].strip()

      if len(meta) >= 3:
        # must have the name/units, desc, and comment
        comment = meta[2].strip()

      if len(meta) >= 4:
        # must have the name/units, desc, comment, and refs field
        refs = meta[3].strip()

      if len(data) > 1: # A PFT line should have more than one data value
        for i, value in enumerate(data):
          cmtdict['pft%i'%i][vname] = float(value)
          cmtdict['pft%i'%i]['units_{}'.format(vname)] = units
          cmtdict['pft%i'%i]['desc_{}'.format(vname)] = desc
          cmtdict['pft%i'%i]['comment_{}'.format(vname)] = comment
          cmtdict['pft%i'%i]['refs_{}'.format(vname)] = refs

      else:
        cmtdict[vname] = float(data[0])
        cmtdict['units_{}'.format(vname)] = units
        cmtdict['desc_{}'.format(vname)] = desc
        cmtdict['comment_{}'.format(vname)] = comment
        cmtdict['refs_{}'.format(vname)] = refs

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
  # should produce something like this:
  # // CMT04 // Shrub Tundra // comment...
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
  #print("Using CMT{} as reference...".format(available_cmts[0]['cmtnum']))
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


def cmdline_parse(argv=None):
  '''
  Define and parse the command line interface.

  When argv is None, the parser will evaluate sys.argv[1:]

  Return
  ------
  args : Namespace
    A Namespace object with all the arguments and associated values.
  '''
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
      help=textwrap.dedent('''Makes plots of the static_lai parameter. 
        static_lai is a monthly value, so each PFT has 12 entries in the
        parameter file. The plot shows the values over the year so you can check
        the seasonality. Looks a 'cmt_dimvegetation.txt file in the
        INFOLDER.'''))

  parser.add_argument('--extract-cmt', nargs=2, metavar=('INFOLDER','CMTKEY'),
      help=textwrap.dedent('''Given a folder of parameter files, and a CMT
        number, this will open each file, copy the block of data for the CMT 
        and paste that block in to a new file named CMTKEY_cmt_*.txt, 
        i.e: CMT04_cmt_calparbgc.txt'''))

  parser.add_argument('--csv-v1-spec', action='store_true',
      help='Print the specification for the supported csv files, v1.')

  parser.add_argument('--fwt2csv-v1', nargs=3, 
      metavar=('PARAMDIR','REQ_CMTS','TARGETS'),
      help=textwrap.dedent('''Converts all the parameters found in the files in
      PARAMDIR into csv format, creating one csv file for each requested CMT.
      REQ_CMTs should be a comma separatedlist of CMT numbers. The resulting csv
      file will be v1, and will have the targets included as found in the
      TARGETS file.'''))

  parser.add_argument('--csv2fwt-v1', nargs=3,
        metavar=('CSV','REFPARAMS','REFTARGETS'),
        help=textwrap.dedent('''Converts the input CSV file into the standard 
        dvmdostem Fixed Width Text parameter format. The CSV file must conform
        to the v1 specification and must have all info present! Prints the
        resulting data to stdout in a format that can be copied into new or
        existing dvmdostem parameter files. Also prints the targets data such
        that if can be copied into an existing targets file, although the key
        order may not match the hand-formatted targets.'''))

  parser.add_argument('--csv-v0-2cmtdatablocks', nargs=2,
      metavar=('CSVFILE', 'CMTNAME'),
      help=textwrap.dedent('''(BETA) Reads data from csv file and prints CMT 
        datablocks to stdout. Expected workflow is that user starts with a
        spreadsheet that is exported to csv, then use this feature is used to
        parse the csv and print formatted sections of data to stdout that can be
        pasted into the standard dvmdostem space delimited text files that are
        used for parameters.'''))

  parser.add_argument('--csv-v0-spec', action='store_true',
      help='''Print the specification for supported csv files, v0.''')

  parser.add_argument('--params2csv-v0', nargs=2, metavar=('PARAMFOLDER','CMTKEY'),
      help=textwrap.dedent('''Dumps a parameter file to csv format.'''))

  args = parser.parse_args(argv)

  return args


def cmdline_run(args):

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

  if args.csv_v1_spec:
    print(csv_v1_specification.__doc__)
    return(0)

  if args.fwt2csv_v1:
    pdir = args.fwt2csv_v1[0]
    req_cmts = args.fwt2csv_v1[1].split(',')
    targets = args.fwt2csv_v1[2]
    if len(req_cmts) == 1 and 'all' in req_cmts:
      req_cmts = 'all'
    else:
      req_cmts = [int(x) for x in req_cmts]
    fwt2csv_v1(pdir, req_cmts, targets)
    return 0

  if args.csv2fwt_v1:
    csvfile = args.csv2fwt_v1[0]
    ref_params = args.csv2fwt_v1[1]
    ref_targets = args.csv2fwt_v1[2]
    csv2fwt_v1(csvfile, ref_directory=ref_params, ref_targets=ref_targets)
    return 0

  if args.params2csv_v0:
    folder = args.params2csv_v0[0]
    cmtkey = args.params2csv_v0[1]

    if not isCMTkey(cmtkey):
      print("Invalid CMT key! Aborting.")
      return -1

    param_files = os.listdir(folder)
    param_files = [os.path.join(folder, f) for f in param_files]

    if len(param_files) < 1:
      print("No files in specified folder! Aborting.")
      return -1

    lines = []
    for f in param_files:
      if isParamFile(f):

        # use the incoming file as a reference
        ref_order = generate_reference_order(f)

        # A line for the file name
        lines.append('{}'.format(f).upper())

        # get data from the fixed width formatted file...
        dd = cmtdatablock2dict(get_CMT_datablock(f, int(cmtkey[3:])))

        # Work on formatting the first comment line
        # should produce something like this:
        # // CMT04 // Shrub Tundra // comment...
        cmt, name, comment = parse_header_line(get_CMT_datablock(f, dd['tag'])[0])
        lines.append("// " + " // ".join((cmt, name, comment)))
        
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
          s = ",".join(["{}".format(i) for i in pftnamelist])
          lines.append(s)

        def is_pft_var(v):
          '''Function for testing if a variable is PFT specific or not.'''
          if v not in list(dd.keys()) and v in list(dd['pft0'].keys()):
            return True
          else:
            return False

        # First take care of the PFT variables
        for var in ref_order:
          if not is_pft_var(var):
            pass
          else:
            # get each item from dict, append to line
            linestring = ''
            for pft in get_datablock_pftkeys(dd):
              linestring += "{:0.6f},".format(dd[pft][var])
            linestring += ('{}'.format(var))
            lines.append(linestring)

        
        # Then take care of the non-pft vars.
        for var in ref_order:
          if is_pft_var(var):
            pass # Nothing to do; already did pft stuff
          else:
            # get item from dict, append to line
            lines.append('{:0.6f},{}'.format(dd[var], var))

      else:
        pass # nothing to do with non-param files
      
      lines.append('')
      lines.append('')

      for l in lines:
        print(l)

  if args.extract_cmt:
    folder, cmtkey = args.extract_cmt
    if not isCMTkey(cmtkey):
      print("Invalid CMT key! Aborting.")
      return -1

    param_files = os.listdir(folder)
    param_files = [os.path.join(folder, f) for f in param_files]

    if len(param_files) < 1:
      print("No files in specified folder! Aborting.")
      return -1

    for f in param_files:
      if isParamFile(f):
        db = get_CMT_datablock(f, int(cmtkey[3:]))
        new_fname = os.path.join(os.path.dirname(f), cmtkey.upper(), '{}'.format(os.path.basename(f)))
        if not os.path.exists(os.path.dirname(new_fname)):
          os.makedirs(os.path.dirname(new_fname))
        with open(new_fname, 'w') as fp:
           fp.writelines(db)
      else:
        pass # nothing do do with non-parameter files...

    return 0

  if args.csv_v0_spec:
    print(csv_v0_specification.__doc__)
    return 0

  if args.csv_v0_2cmtdatablocks:
    inputcsv = args.csv_v0_2cmtdatablocks[0]
    cmtname = args.csv_v0_2cmtdatablocks[1]

    with open(inputcsv) as f:
      data = f.readlines()

    for (start, section_name) in csv_v0_find_section_starts(data):
      print(" ----  {}  ----  CMT {}  ----".format(section_name, cmtname))
      print(format_section_csv_v0(csv_v0_get_section(data, start), data))
      print("")

    return 0

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
 
    return 0

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

    return 0

  if args.compare_cmtblocks:
    fileA, numA, fileB, numB = args.compare_cmtblocks
    numA = int(numA)
    numB = int(numB)
    print("Comparing:")
    print("      CMT {} in {} ".format(fileA, numA))
    print("      CMT {} in {} ".format(fileB, numB))

    compare_CMTs(fileA, numA, fileB, numB)
    return 0

  if args.replace_cmt_block:
    A, B, cmtnum = args.replace_cmt_block
    # Print the result to stdout, where it can be inspected and or 
    # re-directed to a file
    lines = replace_CMT_data(A, B, int(cmtnum))
    for l in lines:
      print(l.rstrip("\n"))
    return 0

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
    return 0

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

    return 0

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
    return 0

  if args.fmt_block_from_json:
    inFile = args.fmt_block_from_json[0]
    refFile = args.fmt_block_from_json[1]
    with open(inFile) as data_file:
      dd = json.load(data_file)
    lines = format_CMTdatadict(dd, refFile)
    for l in lines:
      print(l)
    return 0

  if args.dump_block:
    theFile = args.dump_block[0]
    cmt = int(args.dump_block[1])
    d = get_CMT_datablock(theFile, cmt)
    print(''.join(d))
    return 0

  if args.dump_block_to_json:
    theFile = args.dump_block_to_json[0]
    cmt = int(args.dump_block_to_json[1])
    d = get_CMT_datablock(theFile, cmt)
    dd = cmtdatablock2dict(d)
    # Dumping to a string (json.dumps()) before printing helps make sure
    # that only double quotes are used, wich is critical for valid json
    # and reading back in as a json object
    print(json.dumps(dd))
    return 0

  if args.reformat_block:
    theFile = args.reformat_block[0]
    cmt = int(args.reformat_block[1])
    d = get_CMT_datablock(theFile, cmt)
    dd = cmtdatablock2dict(d)
    lines = format_CMTdatadict(dd, theFile)
    for l in lines:
      print(l)
    return 0

  if args.enforce_initvegc:
    theFile = args.enforce_initvegc[0]
    cmt = int(args.enforce_initvegc[1])
    dd = enforce_initvegc_split(theFile, cmt)
    lines = format_CMTdatadict(dd, theFile)
    for l in lines:
      print(l)
    return 0


def cmdline_entry(argv=None):
  args = cmdline_parse(argv)
  return cmdline_run(args)


if __name__ == '__main__':
  sys.exit(cmdline_entry())
