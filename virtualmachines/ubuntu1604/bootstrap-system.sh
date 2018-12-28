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

# Going for minimal install for starters. Ubuntu comes with gcc and git
# Not dealing with any MPI stuff for now.
apt-get update
apt-get install -y xauth git-gui
apt-get install -y nvidia-367 # <- maybe this was for QTCreator??

# Debugger - could not get QTCreator to work!!
# Local variable display broken, also tried updated version of qtcreator 
# downloaded and installed direct from QT web site - still broken!
# Use gdbgui instead (python web-app, install with pip), see below
#apt-get install -y qtcreator 

apt-get install -y libjsoncpp-dev libnetcdf-dev libboost-all-dev

# Note that in this script, pip is installed with sudo!
apt-get install python-pip

pip install gdbgui matplotlib netCDF4 pandas

apt-get install -y qgis

apt-get install -y python-tk netcdf-bin nco ncview

# Other stuff you may want:
#doxygen, graphviz, gitk

