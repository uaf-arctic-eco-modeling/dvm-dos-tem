#!/bin/bash

#
# bootstrap-system.sh
#
# For isntalling any system level software needed to run a dvm-dos-tem
# development environment.
#
# All commands in this script (or the script itself) should be run with sudo!
#

echo "Installing software..."

#  NOTE: You've gotta install openmpi *after* NetCDF! This keeps NetCDF from
#  getting setup with some pesky #defines that cause errors when trying to
#  compile files that include <mpi.h>.
#  More info: http://www.unidata.ucar.edu/mailing_lists/archives/netcdfgroup/2009/msg00347.html
yum install -y git gcc-c++ jsoncpp-devel readline-devel netcdf-devel netcdf-cxx-devel boost-devel
yum install -y openmpi-devel

echo "Will likely need to add install steps for lapacke (and maybe openblas)"
echo "libraries. Not testing or adding at this time (06-18-2019)."

# Need this to fix the "H5Pset_dxpl_mpio" error that otherwise comes when
# running IPython and importing netCDF4
yum install -y hdf5-openmpi-devel

# this seems to help x11 forwarding
yum install -y xauth

# packages used for plotting
yum install -y python-matplotlib python-matplotlib-wx netcdf4-python python-ipython python-jinja2

# Stuff for plotting on a basemap with python 
# useful for our pre and post processing scripts.
yum install python-basemap-data python-basemap-data-hires python-basemap


# For processing/preparing the "new style" inputs
yum install -y gdal-python
yum install -y gdal gdal-devel

# For compiling with Scons
yum install -y scons

#
# Bonus - basic functionality should exist w/o these packages and settings
#

yum install -y gitk git-gui

# For graphical debugging
# Note: If gdb is not installed, then QT Creator will complain about "Unable
#       to create a debugger engine of the type 'no engine'"
#       Also it may be necessary to install xterm. For some reason Colin and
#       Tobey's VMs (from this Vagrantfile) had xterm and gdb and Ruth's did
#       not...Strange?
yum install -y gdb xterm qt-creator

# For viewing IPython notebooks, and viewing Netcdf I/O files.
yum install -y ncview nco firefox

# Install Doxygen and Graphviz
# Note: There is a problem with some older versions of Doxygen (specifically
#       1.8.6, maybe others). The problem is that some classes and functions
#       don't have complete "Referenced by" lists and some of the links for
#       "Definition at line ..." links don't show up. This doesn't seem to be
#       the case with more recent versions of Doxygen, so we install the
#       "rawhide" repo and install Doxygen from there...
yum install -y fedora-release-rawhide
yum install -y --enablerepo rawhide doxygen
yum install -y graphviz

# The man page conflicts between vim and vim-minimal. Removing vim-minimal
# takes sudo with it, crippling later attempts at inline provisioning. So we
# make sure to reinstall sudo.
su -c "yum remove -y vim-minimal && yum install -y vim && yum install -y sudo"
