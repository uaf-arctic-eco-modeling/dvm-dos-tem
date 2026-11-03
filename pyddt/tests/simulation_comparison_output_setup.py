#!/usr/bin/env python

#This is a placeholder script to record which
# outputs at which granularity we usually want
# to run for using the simulation comparison report.

import subprocess
import glob
import util.run_util
import tests.test_util as tests

enable_output_set = [
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
  "LFNVC y m",
  "LFNVN y m",
  "LFVC y m",
  "LFVN y m",
  "LWCLAYER y m l",
  "MINEC y m",
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
  "VEGNSTR y m pft",
  "VWCLAYER y m l",
  "WATERTAB y m",
  "YSD y"
]


if __name__ == '__main__':

  outspecs = "/work/config/output_spec.csv"
  util.outspec.cmdline_entry([outspecs, "--empty"])
 
  for entry in enable_output_set:
    entry = entry.split()
    util.outspec.cmdline_entry([outspecs, "--on", *entry])

