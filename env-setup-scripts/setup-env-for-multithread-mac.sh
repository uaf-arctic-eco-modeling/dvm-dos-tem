#!/bin/bash

# Modify the Makefile to use the multi-threaded boost libraries on a Mac.
# For some reason, the library naming convention on a Mac is different than Linux, so
# the -l flags passed to g++ need to be modified.
# 
# This script allows the default project Makfile to remain simple and generic. After each
# git checkout, you will end up with the plain Makefile in your working directory. Run
# this script to fix the Makefile for use with a Mac that has multi-threaded boost 
# compiled. The script simply changes the line in the Makefile.
#
# The modified Makefile will show up as changed in the git status command, but you can 
# basically ignore it, since this script will allow you to freshly re-create the Mac
# specific Makefile easily. So don't commit the changes to the Makefile!! Instead it is 
# better to modify this script if more Mac specific settings are found...

F=Makefile

normal_flags="CFLAGS=-c -Wall -ansi -O2 -g -fPIC"
debug_flags="CFLAGS=-c -Wall -ansi -g -fPIC"

cat $F | sed 's:'"$normal_flags"':'"$debug_flags"':' > $F.new
mv $F.new $F

normal_lib_line="LIBS=-lnetcdf_c++ -lnetcdf -lboost_system -lboost_filesystem -lboost_program_options"
mt_mac_lib_line="LIBS=-lnetcdf_c++ -lnetcdf -lboost_system-mt -lboost_filesystem-mt -lboost_program_options-mt"

cat $F | sed 's:'"$normal_lib_line"':'"$mt_mac_lib_line"':' > $F.new
mv $F.new $F


