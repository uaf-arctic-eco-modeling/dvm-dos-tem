#!/usr/bin/env python

#This is both an example for the current state of our testing
# procedures and the beginning of a complete test to be run
# prior to a PR submission.
#Note that this approach is not finalized and will likely change.

import subprocess
import glob
import util.run_util
import tests.test_util as tests

#Configuration settings relevant for all cases
test_config = {
  "parent_out_dir": "/data/workflows"
}

test_cases = {
  "0": {
    "name": "master",
    "branch_name": "master",
    "SHA": "",
    "input_dir": "/work/demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/",
    "working_dir": "/data/workflows/master",
    "cmt_num": 5,
    "pr_years": 10,
    "eq_years": 30,
    "sp_years": 0,
    "tr_years": 0,
    "sc_years": 0,
    "line_color": "black",
    "line_width": 4
  },
  "1": {
    "name": "Testing init test framework",
    "branch_name": "init_test_framework",
    "SHA": "",
    "input_dir": "/work/demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/",
    "working_dir": "/data/workflows/testframework_again",
    "cmt_num": 5,
    "pr_years": 10,
    "eq_years": 30,
    "sp_years": 0,
    "tr_years": 0,
    "sc_years": 0,
    "line_color": "blue",
    "line_width": 2
  }
}

test_output_set = [
  "ALD y",
  "AVLN y m l",
  "BURNAIR2SOILN y m",
  "BURNSOIL2AIRC y m",
  "BURNSOIL2AIRN y m",
  "BURNTHICK y m",
  "BURNVEG2AIRC y m",
  "BURNVEG2AIRN y m",
  "BURNVEG2DEADC y m",
  "BURNVEG2DEADN y m",
  "BURNVEG2SOILABVC y m",
  "BURNVEG2SOILABVN y m",
  "BURNVEG2SOILBLWC y m",
  "BURNVEG2SOILBLWN y m",
  "DEADC y m",
  "DEADN y m",
  "DEEPC y m",
  "DEEPDZ y",
  "DWDC y m",
  "DWDN y m",
  "EET y m",
  "GPP y m pft",
  "INGPP y m pft",
  "LAI y m",
  "LAYERDEPTH y m l",
  "LAYERDZ y m l",
  "LAYERTYPE y m l",
  "LTRFALC y m",
  "LTRFALN y m",
  "LWCLAYER y m l",
  "MINEC y m",
  "MOSSDEATHC y m",
  "MOSSDEATHN y m",
  "MOSSDZ y",
  "NETNMIN y m",
  "NIMMOB y m",
  "NPP y m pft",
  "NRESORB y m",
  "NUPTAKELAB y m",
  "NUPTAKEST y m",
  "ORGN y m l",
  "PET y m",
  "RG y m",
  "RHDWD y m",
  "RHSOM y m",
  "RM y m",
  "ROLB y m",
  "SHLWC y m",
  "SHLWDZ y",
  "SNOWFALL y m",
  "SNOWTHICK y m",
  "SOMA y m l",
  "SOMCR y m l",
  "SOMPR y m l",
  "SOMRAWC y m l",
  "SWE y m",
  "TLAYER y m l",
  "TRANSPIRATION y m",
  "VEGC y m pft",
  "VEGN y m pft",
  "VWCLAYER y m l",
  "WATERTAB y m",
  "YSD y"
]


def run_pr_test():
  '''
  Runs each provided simulation setup (or test case),
    checks the data in each output file for differences,
    and produces a report PDF with plots.
  '''

  #Run each case
  for case_id,config in test_cases.items():
    util.run_util.run_case(config, test_output_set)

  #Binary output file comparison
  #Needs to handle more than two files, if there are more than two cases
  #This should eventually collect differences into a report
  for output in test_output_set:
    varname = output.split()[0]

    #This is very hacky and needs to be fixed. It assumes the existence
    # of a single file that matches, and it doesn't handle more
    # than two cases, either.
    patternA = test_cases["0"]["working_dir"] + "/" \
               + "output/" + varname + "_*_eq.nc"
    fileA = glob.glob(patternA)[0]

    patternB = test_cases["1"]["working_dir"] + "/" \
            + "output/" + varname + "_*_eq.nc"
    fileB = glob.glob(patternB)[0]

    filesmatch = tests.compare_nc_with_nco(fileA, fileB, varname, True)
    if not filesmatch:
      print("{} files differ".format(varname))

  if filesmatch:
    print("All files match")

  #Plotting setup
  #workdir is also hacky
  workdir_list = [case["working_dir"].split('/')[-1] for case_id,case in test_cases.items()]
  name_list = [case["name"] for case_id,case in test_cases.items()]
  color_list = [case["line_color"] for case_id,case in test_cases.items()]
  width_list = [str(case["line_width"]) for case_id,case in test_cases.items()]

  #The plotter needs to take a name for the final pdf
  #Plot things
  subprocess.run(["python", "/work/scripts/simulation_comparison_report.py",
                 "--POD", test_config["parent_out_dir"],
                 "--PODlist", *workdir_list,
                 "--scenariolist", *name_list,
                 "--colorlist", *color_list,
                 "--widthlist", *width_list]) 


if __name__ == '__main__':
  run_pr_test()