#!/bin/bash


export PATH="$HOME/custom_software/openmpi-3.0.0/bin:$PATH"

export LD_LIBRARY_PATH="$HOME/custom_software/openmpi-3.0.0/lib:$HOME/custom_software/boost_1_55_0/lib:$HOME/custom_software/jsoncpp/libs/linux-gcc-4.4.7:$HOME/custom_software/hdf5-1.8.19/hdf5/lib:$HOME/custom_software/netcdf-4.4.1.1/netcdf/lib:$LD_LIBRARY_PATH"


echo "NOTE: This file will NOT work if it is run as a script!"
echo "      Instead use the 'source' command like this:"
echo "      $ source env-setup-scripts/setup-env-for-atlas.sh"
echo ""


