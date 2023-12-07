#!/usr/bin/env python

#adapted from calib_param_update.py
#Aiza, 11/2022
#contains python functions to process random calibration with more than 1 test:

# read_results(filename): reads in final result file for calibration
#   returns key-value pairs of parameters and their values (lines), params are repeated for multiple runs

# create_dict_params(lines): merges results of multiple calibrations into one key-value set
#   returns merged_params

import collections
import sys
import textwrap
import math
from pathlib import Path
from collections import OrderedDict

# filename ='Calibration_STEP2_r2.finalresults'

def read_results(filename):
    #read in optimal sets from file (file name passed in as arg)
    #here, assumes there are three lines - 0=OF, 1=lambda, 2=params
    with open(filename) as f:
        lines = f.readlines()
        print(lines)
    #for multiple optimal sets, need to loop through them all
    filelength = len(lines)
    num_sets = math.floor(filelength/3) #truncate in case there's an empty extra line at end of file
    for nn in range(1,num_sets+1):
        del lines[(nn-1)] #delete OF line
        del lines[(nn-1)] #delete lambda line

    for nn in range(0,num_sets):
        lines[nn]=lines[nn].replace("OrderedCollections.OrderedDict", "") 
        lines[nn]=lines[nn].replace(" ", "")
        lines[nn]=lines[nn].replace("\"", "")
        lines[nn]=lines[nn].replace("\n", "")
        lines[nn]=lines[nn].replace("(", "")
        lines[nn]=lines[nn].replace(")", "")
        lines[nn]= OrderedDict(subString.split("=>") for subString in lines[nn].split(","))

    return lines

#at this point, lines is a set of key:value pairs of optimal sets for each calibration run
#we combine all runs into one set of keys (params) with multiple optimal value to plot easier:
def create_dict_params(lines):
    merged_params = {}
    for sub in lines:
        for key, val in sub.items(): 
            merged_params.setdefault(key, []).append(val)

    return merged_params

def read_error(filename):
    #read in error from file (file name passed in as arg)
    #here, assumes there are three lines - 0=OF, 1=lambda, 2=params
    with open(filename) as f:
        errors = f.readlines()
        print(errors)
    #for multiple optimal sets, need to loop through them all
    filelength = len(errors)
    num_sets = math.floor(filelength/3) #truncate in case there's an empty extra line at end of file
    for nn in range(1,num_sets+1):
        del errors[(nn)] #delete lambda line
        del errors[(nn)] #delete params line

    for nn in range(0,num_sets):
        # errors[nn]=errors[nn].replace("OF:", "") 
        errors[nn]=errors[nn].replace(" ", "")
        errors[nn]=errors[nn].replace("\"", "")
        errors[nn]=errors[nn].replace("\n", "")
    
    return errors


#plot in histogram
#draw histograms (one for each cmax/nmax/param) for n values from the n calibraterandom simulations