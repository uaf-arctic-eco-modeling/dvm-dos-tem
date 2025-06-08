#!/usr/bin/env python

# Tobey Carman April 2018
# Utility script for handling dvmdostem output_spec files.
# The output_spec files are expected to be a csv file with 
# a header row and the following fields:

# Name, Description, Units, Yearly, Monthly, Daily, PFT, Compartments, Layers, Data Type, Placeholder

# An empty field means that variable is not specified (turned on) for output at
# that particular resolution (timestep or PFT or layer, etc).

# A field containing 'invalid' means that the variable is not available or is 
# meaningless at that particular resolution.

# A field containing anything other than "invalid" or an empty string is
# considered to be on or active. While any character or string can be used, 
# generally we have been using the first letter of the resolution in 
# question, i.e. 'y' in the field for 'Yearly'.

import csv
import sys
import argparse
import textwrap
import os

def print_line_dict(d, header=False):
  if header:
    print("{:>20s} {:>20s} {:>12} {:>12} {:>12} {:>12} {:>12} {:>12} {:>12}     {:}".format('Name','Units','Yearly','Monthly','Daily','PFT','Compartments','Layers','Data Type', 'Description'))
  else:
    print("{Name:>20s} {Units:>20s} {Yearly:>12} {Monthly:>12} {Daily:>12} {PFT:>12} {Compartments:>12} {Layers:>12} {Data Type:>12}     {Description}".format(**d))

def list_vars(data, verbose=False):
  var_names = [line['Name'] for line in data]
  if verbose:
    var_names = ['{:<20} {:<}'.format(line['Name'], line['Description']) for line in data]
  return sorted(var_names)

def list_var_options(line, var):
  var_options = [x for x in ['Yearly','Monthly','Daily','PFT','Compartments','Layers'] if line[x] != 'invalid' and line[x] != 'forced' ]
  return var_options

def show_yearly_vars(data):
  print_line_dict({}, header=True)
  for line in data:
    if line['Yearly'] != 'invalid':
      print_line_dict(line)

def show_monthly_vars(data):
  print_line_dict({}, header=True)
  for line in data:
    if line['Monthly'] != 'invalid':
      print_line_dict(line)

def show_daily_vars(data):
  print_line_dict({}, header=True)
  for line in data:
    if line['Daily'] != 'invalid':
      print_line_dict(line)

def show_pft_vars(list_of_lines):
  print_line_dict({}, header=True)
  for i in list_of_lines:
    if i['PFT'] != 'invalid':
      print_line_dict(i)

def show_compartment_vars(data):
  print_line_dict({}, header=True)
  for line in data:
    if line['Compartments'] != 'invalid':
      print_line_dict(line)

def show_layer_vars(list_of_lines):
  print_line_dict({},header=True)
  for i in list_of_lines:
    if i['Layers'] != 'invalid':
      print_line_dict(i)

def csv_file_to_data_dict_list(fname):
  
  expected_cols_sorted = ['Compartments', 'Daily', 'Data Type',
      'Description', 'Layers', 'Monthly', 'Name', 'PFT', 'Placeholder',
      'Units', 'Yearly']

  with open(fname, 'r') as f:
    s = f.readlines()
  
  data = []  
  for r in csv.DictReader(s):
    if None in r.keys():
      raise RuntimeError(f"Bad output spec file! Check your fields for {r['Name']}")
    if sorted(r.keys()) != expected_cols_sorted:
      print("PROBLEM WITH KEYS: ", sorted(r.keys()))
      if 'Name' in list(r.keys()):
        print("Problem with variable ", r['Name'])
      else:
        print("Missing the Name column??")
      raise RuntimeError("Bad output spec file!")
    data.append(r)

  return data

def write_data_to_csv(data, fname):
    with open(fname, 'w', newline='') as csvfile:
      fieldnames = "Name,Description,Units,Yearly,Monthly,Daily,PFT,Compartments,Layers,Data Type,Placeholder".split(",")
      writer = csv.DictWriter(csvfile, fieldnames=fieldnames, lineterminator='\n')
      writer.writeheader()
      writer.writerows(data)


def check_layer_vars(data):

  def warn_layers_not_set(dd):
    if all([x == '' for x in [dd['Layers'],]]):
      print("WARNING! output by Layers not set for {}".format(dd['Name']))

  for line in data:
    if 'LAYER' in line['Name'].upper():
      if any([line['Yearly'].lower() in ('y','year','yr','yearly')]):
        warn_layers_not_set(line)
      if any([line['Monthly'].lower() in ('m','month','monthly')]):
        warn_layers_not_set(line)
      if any([line['Daily'].lower() in ('d','day','daily',)]):
        warn_layers_not_set(line)



def toggle_off_variable(data, var, verbose=False):
  if var not in list_vars(data):
    raise ValueError("Invalid variable! {} not found!".format(var))

  for line in data:
    if line['Name'] == var.upper():
      for key in "Compartments,PFT,Layers,Monthly,Daily,Yearly".split(","):
        if line[key] == 'invalid':
          pass
        else:
          if verbose:
            print("Turning {} off for {} resolution".format(var, key))
          line[key] = ''
  return data

def all_vars_off(data, verbose=False):
  for line in data:
    for key in "Compartments,Layers,PFT,Monthly,Daily,Yearly".split(","):
      if line[key] == 'invalid' or line[key] == 'forced':
        pass
      else:
        line[key] = ''
        if verbose:
          print("Turning {} off for {} resolution".format(line['Name'], key))
  return data

def toggle_on_variable(data, var, res_spec, verbose=False):

  if var not in list_vars(data):
    raise ValueError("Invalid variable! {} not found!".format(var))

  for line in data:
    if 'Name' not in list(line.keys()):
      print("ERROR! Missing 'Name' field for row: {}".format(line))
      return -1

    if line['Name'] == var.upper():

      def safe_set(data_dict, key, new):
        '''Modify dict in place. Pass by name python sementics.'''
        if data_dict[key] == 'invalid':
          #print "passing: {} at {} resolution is set to invalid, not setting to '{}'".format(data_dict['Name'], key, new)
          pass
        else:
          data_dict[key] = new

      # Work from coarsest to finest so that if the user specifies
      # (for some reason) yearly *and* daily, the daily overwrites
      # the yearly setting.
      if any([r.lower() in ('y','year','yr','yearly') for r in res_spec.split(' ')]):
        safe_set(line, 'Yearly', 'y')
        safe_set(line, 'Monthly', '')
        safe_set(line, 'Daily', '')

      if any([r.lower() in ('m','month','monthly') for r in res_spec.split(' ')]):
        safe_set(line, 'Yearly', 'y')
        safe_set(line, 'Monthly', 'm')
        safe_set(line, 'Daily', '')

      if any([r.lower() in ('d','day','daily',) for r in res_spec.split(' ')]):
        safe_set(line, 'Yearly', 'y')
        safe_set(line, 'Monthly', 'm')
        safe_set(line, 'Daily', 'd')

      # Same for PFTs, work from coarsest to finest
      if any([r.lower() in ('p','pft',) for r in res_spec.split(' ')]):
        safe_set(line, 'PFT', 'p')
        safe_set(line, 'Compartments', '')

      if any([r.lower() in ('c','cpt','compartment','cmpt','compartments',) for r in res_spec.split(' ')]):
        safe_set(line, 'PFT', 'p')
        safe_set(line, 'Compartments', 'c')

      # And finally the layers...
      if any([r.lower() in ('l','layer','lay','layers') for r in res_spec.split(' ')]):
        safe_set(line, 'Layers', 'l')

      if verbose:
        print_line_dict({}, header=True)
        print_line_dict(line)

      if all([x == 'invalid' or x == '' for x in [line['Yearly'], line['Monthly'], line['Daily']]]):
        print("WARNING! Invalid TIME setting detected! You won't get output for {}".format(line['Name']))

  check_layer_vars(data)

  return data

def cmdline_define():
  '''
  Define the command line interface and return the parser object. 

  Example API
  ./outspec.py.py --list-pft-vars PATH/TO/FILE
  ./outspec.py.py --list-layer-vars PATH/TO/FILE
  ./outspec.py.py --show-enabled PATH/TO/FILE

  ./outspec.py.py --show-enabled PATH/TO/FILE

  ./outspec.py --on LAI yearly PATH/TO/FILE
  ./outspec.py --off LAI

  '''

  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''
      Script for dealing with the output specification csv file.

      Some of the command line options will simply print info about
      the file to the screen, while others will modify the file. It
      should be obvious from the names of the command line options
      whether it is an "edit" or a "view" action.
    ''')
  )
  parser.add_argument('file', 
      #type=argparse.FileType('r'),
      metavar=('FILE'), 
      help=textwrap.dedent('''The file to analyze.'''))

  parser.add_argument('--print-file', action='store_true',
     help=textwrap.dedent('''Print a nicely formatted version of the file to the console.'''))

  parser.add_argument('--list-vars', action='store_true',
      help=textwrap.dedent('''List all available variables.'''))

  parser.add_argument('--show-yearly-vars', action='store_true',
      help=textwrap.dedent('''Print all variables available at yearly timestep.'''))

  parser.add_argument('--show-monthly-vars', action='store_true',
      help=textwrap.dedent('''Print all variables available at monthly timestep.'''))

  parser.add_argument('--show-daily-vars', action='store_true',
      help=textwrap.dedent('''Print all variables available at daily timestep.'''))

  parser.add_argument('--show-pft-vars', action='store_true',
      help=textwrap.dedent('''Print all variables available by PFT.'''))

  parser.add_argument('--show-compartment-vars', action='store_true',
      help=textwrap.dedent('''Print all variables available by Compartment.'''))

  parser.add_argument('--show-layer-vars', action='store_true',
      help=textwrap.dedent('''Print all variables available by Layer.'''))

  parser.add_argument('--show-options', 
      nargs=1, metavar=('VAR'),
      help=textwrap.dedent('''Show valid options for a specific 
        variable'''))

  parser.add_argument('-s','--summary', action='store_true',
      help=textwrap.dedent('''Print out all the variables that are enabled in 
        the file.'''))

  parser.add_argument('--enable-cal-vars', action='store_true',
    help=textwrap.dedent('''Enable netcdf outputs for all the calibration target variables.'''))

  parser.add_argument('--enable-all-yearly', action='store_true',
    help=textwrap.dedent('''Enable all yearly ecosystem-level outputs.'''))

  parser.add_argument('--max-output', action='store_true',
    help=textwrap.dedent('''Enable all outputs at the finest detail available'''))

  parser.add_argument('--max-yearly', action='store_true',
    help=textwrap.dedent('''Enable all yearly outputs at the finest detail available'''))

  parser.add_argument('--max-monthly', action='store_true',
    help=textwrap.dedent('''Enable all monthly outputs at the finest detail available'''))

  parser.add_argument('--on', 
      nargs='+', metavar=('VAR', 'RES',),
      help=textwrap.dedent('''Turn the selected variable on at the selected
        resolution. '''))

  parser.add_argument('--off', 
      nargs=1, metavar=('VAR'),
      help=textwrap.dedent(''''''))

  parser.add_argument('--empty', action='store_true',
      help=textwrap.dedent('''Turn off every variable in the file for all resolutions.'''))

  parser.add_argument('--DEBUG', action='store_true',
      help=textwrap.dedent('''Print extra info for debugging.'''))

  return parser

def cmdline_parse(argv=None):
  '''Wrapper function around the cmdline parsing.'''
  parser = cmdline_define()
  args = parser.parse_args(argv)

  return args


def cmdline_run(args):
  if args.DEBUG:
    print(args)

  if args.print_file:
    data = csv_file_to_data_dict_list(args.file)
    print_line_dict(data[0], header=True)
    for line in data:
      print_line_dict(line)

  if args.list_vars:
    data = csv_file_to_data_dict_list(args.file)
    print("\n".join(sorted(list_vars(data, verbose=True))))
    return 0

  if args.show_yearly_vars:
    data = csv_file_to_data_dict_list(args.file)
    show_yearly_vars(data)

  if args.show_monthly_vars:
    data = csv_file_to_data_dict_list(args.file)
    show_monthly_vars(data)

  if args.show_daily_vars:
    data = csv_file_to_data_dict_list(args.file)
    show_daily_vars(data)

  if args.show_pft_vars:
    data = csv_file_to_data_dict_list(args.file)
    show_pft_vars(data)

  if args.show_compartment_vars:
    data = csv_file_to_data_dict_list(args.file)
    show_compartment_vars(data)

  if args.show_layer_vars:
    data = csv_file_to_data_dict_list(args.file)
    show_layer_vars(data)

  if args.show_options:
    var = args.show_options[0].upper()
    data = csv_file_to_data_dict_list(args.file)

    for line in data:
      if line['Name'] == var.upper():
        print(list_var_options(line, var))
    return 0

  if args.summary:
    data = csv_file_to_data_dict_list(args.file)
    print_line_dict(data[0], header=True)
    for line in data:
      if all([line[x] == 'invalid' or line[x] == '' or line[x] == 'forced' for x in ['Yearly','Monthly','Daily','PFT','Compartments','Layers']]):
        pass # Nothing turned on...
      else:
        print_line_dict(line)
    check_layer_vars(data)
    return 0

  if args.enable_cal_vars:
    caltargets2ncname_map = [
      ('GPPAllIgnoringNitrogen','INGPP'),
      ('NPPAllIgnoringNitrogen','INNPP'),
      ('GPPAll','GPP'),  
      ('NPPAll','NPP'),
      # ??? There are snuptake, lnuptake and innuptake (in the C++)
      # and TotNitrogentUptake (in the cal targets) is the sum of sn and ln...
      #('Nuptake','NUPTAKE'), 
      ('VegCarbon','VEGC'),
      ('VegStructuralNitrogen','VEGNSTR'),
      ('MossDeathC','MOSSDEATHC'),
      ('CarbonShallow','SHLWC'),
      ('CarbonDeep','DEEPC'),
      ('CarbonMineralSum','MINEC'),
      ('OrganicNitrogenSum','ORGN'),
      ('AvailableNitrogenSum','AVLN'),
      ]

    data = csv_file_to_data_dict_list(args.file)

    for v in "MOSSDEATHC SHLWC DEEPC MINEC ORGN AVLN".split():
      data = toggle_on_variable(data, v, 'yearly', verbose=args.DEBUG)

    for v in "INGPP INNPP NPP GPP".split():
      data = toggle_on_variable(data, v, 'yearly pft', verbose=args.DEBUG)

    for v in "VEGC VEGNSTR".split():
      data = toggle_on_variable(data, v, 'yearly pft compartment', verbose=args.DEBUG)

    data = toggle_on_variable(data, 'CMTNUM', 'yearly', verbose=args.DEBUG)

    write_data_to_csv(data, args.file)

    print("NOTE: Make sure to enable 'eq' outputs in the config file!!!")

    return 0

  if args.enable_all_yearly:
    data = csv_file_to_data_dict_list(args.file)

    for line in data:
      if line['Yearly'] == '':
        data = toggle_on_variable(data, line['Name'], 'yearly', verbose=args.DEBUG)

    write_data_to_csv(data, args.file)
    return 0


  #Maximum output
  if args.max_output:
    data = csv_file_to_data_dict_list(args.file)

    for line in data:
      var = line['Name']
      var_options = list_var_options(line, var)
      var_options = " ".join(var_options)
      toggle_on_variable(data, var, var_options, verbose=args.DEBUG)

    write_data_to_csv(data, args.file)
    return 0


  if args.max_yearly:
    data = csv_file_to_data_dict_list(args.file)

    for line in data:
      if line['Yearly'] != 'invalid':
        var_options = list_var_options(line, line['Name'])

        #Remove time options other than yearly
        if 'Monthly' in var_options:
          var_options.remove('Monthly')
        if 'Daily' in var_options:
          var_options.remove('Daily')

        var_options = " ".join(var_options)

        data = toggle_on_variable(data, line['Name'], var_options, verbose=args.DEBUG)

    write_data_to_csv(data, args.file)
    return 0


  if args.max_monthly:
    data = csv_file_to_data_dict_list(args.file)

    for line in data:
      if line['Monthly'] != 'invalid':
        var_options = list_var_options(line, line['Name'])

        #Remove time options finer-grained than monthly
        if 'Daily' in var_options:
          var_options.remove('Daily')

        var_options = " ".join(var_options)
        data = toggle_on_variable(data, line['Name'], var_options, verbose=args.DEBUG)

    write_data_to_csv(data, args.file)
    return 0


  if args.on:
    if len(args.on) < 2:
      raise ValueError("--on flag requires variable and resolution specification (monthly, pft, layer, etc).")

    var = args.on[0]
    res_spec = args.on[1:]
    data = csv_file_to_data_dict_list(args.file)
    
    data = toggle_on_variable(data, var, ' '.join(res_spec), verbose=args.DEBUG)

    write_data_to_csv(data, args.file)

    return 0

  if args.off:
    var = args.off[0].upper()
    data = csv_file_to_data_dict_list(args.file)

    data = toggle_off_variable(data, var, verbose=args.DEBUG)

    write_data_to_csv(data, args.file)

    return 0

  if args.empty:

    data = csv_file_to_data_dict_list(args.file)
    data = all_vars_off(data, verbose=args.DEBUG)
    write_data_to_csv(data, args.file)

    return 0

def cmdline_entry(argv=None):
  args = cmdline_parse(argv)
  return cmdline_run(args)



if __name__ == '__main__':
  sys.exit(cmdline_entry())
