#!/usr/bin/env python

import os
import util
import util.input
import util.param
import util.runmask
import util.config
import commentjson


verbose = True

#Print expected config file path
#Load expected config file
assumed_config_file = "config/config.js"
print("Loading " + assumed_config_file)
with open(assumed_config_file) as config_file:
  config = commentjson.load(config_file)


#Extract and display input file path prefixes (excluding parameter files
# and output_spec)
input_filepaths = util.config.get_input_paths(assumed_config_file)
path_prefixes = []
for filepath in input_filepaths:
  prefix = os.path.dirname(filepath)
  if prefix not in path_prefixes:
    path_prefixes.append(prefix)
print("*********************************************************")
print("|", len(path_prefixes), "input path prefixes specified:")
for prefix in path_prefixes:
  print("|", prefix)
print("*********************************************************")


#Check that all input files specified in the config file exist (excluding
# parameter files and output_spec)
#We are not using the following method because that checks a whole
# directory, which would not allow individually different input paths
#util.input.check_input_set_existence(input directory)
missing_files = [path for path in input_filepaths if not os.path.exists(path)]
if len(missing_files) > 0:
  star_len = len(max(missing_files, key=len)) + 4
  star_str = '*' * star_len

  print(star_str)
  print("| Missing input files:")
  print("|", *missing_files)
  print(star_str)
else:
  print("***********************************")
  print("| All specified input files exist |")
  print("***********************************")


#Find total count of active cells
#The call to cell_count will also flag invalid values
mask_info = util.runmask.cell_count(config['IO']['runmask_file'], verbose)
invalid_values = {value:count for value,count in mask_info.items() if value not in [0,1]}

print("*********************************************************")
print("| Active cells in run mask:", mask_info[1])
print("| Inactive cells in run mask:", mask_info[0])
print("| Other values:", invalid_values)
print("*********************************************************")


#Check that all CMT values specified in the input vegetation file
# have a parameterization in the parameter files.
input_CMTs = util.input.get_vegtypes(config['IO']['veg_class_file'], verbose)
print("Input veg types:", *input_CMTs.keys(), sep=', ')
print("input veg counts:", *input_CMTs.values(), sep=', ')
print(input_CMTs)

param_CMTs = util.param.get_available_CMTs(config['IO']['parameter_dir'])
print("Param CMTs:", param_CMTs)

unparameterized_CMTs = [x for x in input_CMTs.keys() if x not in param_CMTs]

if len(unparameterized_CMTs) > 0:
  print("There are CMTs in the veg file that have no parameterization")
  print(unparameterized_CMTs)
  print("Check that these are masked out by the run mask or set to\
        different values before running.")
else:
  print("************************************************")
  print("| All input CMTs exist in the parameter files. |")
  print("| Please ensure that all are calibrated.       |")
  print("************************************************")


