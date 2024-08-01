#!/usr/bin/env python

import os
import subprocess
import util.runmask
import util.setup_working_directory
import util.outspec


def run_case(config, output_set):
  '''
  Checks out a given branch name or SHA
  Builds the binary
  Sets up: working directory
           run mask (assumes 0,0)
           output selection (enables eq output)
  Runs model with the case settings
  '''
   
  branch_name = config["branch_name"]
  SHA = config["SHA"]

  #Check out code at the specified point
  if(branch_name):
    subprocess.run(["git", "checkout", branch_name])
  elif(SHA):
    subprocess.run(["git", "checkout", SHA])
  else:
    print("Please provide a valid branch name or SHA ID")
    exit

  #Needs to check for successful branch change. There could be issues
  # with conflicts, unstashed changes, etc.

  #Clean and re-make binary
  subprocess.run(["make", "clean"])
  subprocess.run(["make"])


  #Create working directory
  util.setup_working_directory.cmdline_entry(["--input-data-path",
                               config["input_dir"], config["working_dir"]])


  #Enable only cell 0,0 in the run mask
  case_run_mask = "{}/run-mask.nc".format(config["working_dir"])
  util.runmask.cmdline_entry(["--reset", case_run_mask])
  util.runmask.cmdline_entry(["--yx", "0", "0", case_run_mask])


  #Turn on EQ output in the config file
  #There is not currently a config utility script/module so we're
  # doing this manually.
  subprocess.run(["sed", "-i", 's/"output_nc_eq": 0,/"output_nc_eq": 1,/',
                  "{}/config/config.js".format(config["working_dir"])])


  #Set up output choices
  #util.outspec.enable_output_set(short_test_set)
  outspecs = "{}/config/output_spec.csv".format(config["working_dir"])
  util.outspec.cmdline_entry([outspecs, "--empty"])

  for entry in output_set:
    entry = entry.split()
    util.outspec.cmdline_entry([outspecs, "--on", *entry])


  #Switch to the working directory so local paths work
  os.chdir(config["working_dir"])


  #Run the model
  #run() requires strings, conversions are prior to the call
  # for ease of reading.
  cmt_str = str(config["cmt_num"])
  pr_str = str(config["pr_years"])
  eq_str = str(config["eq_years"])
  sp_str = str(config["sp_years"])
  tr_str = str(config["tr_years"])
  sc_str = str(config["sc_years"])
  subprocess.run(["/work/dvmdostem", "-l", "warn", "--force-cmt", cmt_str,
                  "-p", pr_str, "-e", eq_str, "-s", sp_str,
                  "-t", tr_str, "-n", sc_str])


  #Switch back to code directory
  os.chdir("/work/")

