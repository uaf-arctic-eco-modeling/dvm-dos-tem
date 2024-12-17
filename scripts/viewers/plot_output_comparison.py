#!/usr/bin/env python


import sys
import netCDF4 as nc
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pandas as pd

import util.output
from util.output import load_output_dataframe

import util.general

import argparse
import textwrap


if __name__ == '__main__':


  #The files comprising all the components of the summed variable
  # being compared. Will be replaced with a proper argument handler.
  component_files = [
    "./output/SOCFROZEN_monthly_sc.nc",
    "./output/SOCUNFROZEN_monthly_sc.nc"]

  #The summed variable output file
  total_file = "./output/SOC_monthly_sc.nc"

  pixel_x = 0
  pixel_y = 0


  #Load all component data into one dataframe
  merged_df = pd.DataFrame()
  for component in component_files:
    path, varname, timeres, stage = util.general.breakdown_outfile_name(component)

    df, meta = load_output_dataframe(varname, stage, timeres, pixel_y, pixel_x, fileprefix=path)

    merged_df[varname] = df

  #Recalculate the sum from the components, for direct comparison
  # with the sum from the output file
  new_sum = merged_df.sum(axis=1, numeric_only=True)

  #Load summed output file
  path, varname, timeres, stage = util.general.breakdown_outfile_name(total_file)
  df, meta = load_output_dataframe(varname, stage, timeres, pixel_y, pixel_x, fileprefix=path)

  #Add the summed output to the dataframe
  label = varname + " (output)"
  merged_df[label] = df

  #Add the recalculated sum to the dataframe. Done here so we can
  # use the variable name in the label.
  label = varname + " (calculated)"
  merged_df[label] = new_sum

  stagetitle = varname + ' (' + stage + ')'
  plot = merged_df.plot(title=stagetitle)

  plt.show()


