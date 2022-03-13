#!/bin/bash

# Set environment variables for working with dvm-dos-tem on aeshna.
# NetCDF and Boost's Program Options are not available as system libraries on
# aeshna. The user tobey has compiled these and made them available for others to use.
# 
# This script sets a couple environment variables to make that happen.
# You can either source this script each time you logon to aeshna, before compiling and 
# running, or you can add a line to your .bashrc or .bash_profile that will source this 
# script each time you logon to the machine.

# For compiling and linking
export SITE_SPECIFIC_INCLUDES="-I/home/tobey/usr/local/include"
export SITE_SPECIFIC_LIBS="-L/home/tobey/usr/local/lib"

# For locating the boost libs at run time
export LD_LIBRARY_PATH="/home/tobey/usr/local/lib:$LD_LIBRARY_PATH"
