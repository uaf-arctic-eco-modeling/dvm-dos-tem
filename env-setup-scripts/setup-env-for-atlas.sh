#!/bin/bash

# setting up to use boost on atlas
# Ruth has provided jsoncpp for us (used for the calibration interface)
# and Tobey has provided boost (used for a variety of things - logging, signals, etc)

# NOTE: (07-21-2017) Tobey re-compiled a more recent version of jsoncpp so as
# to avoid a problem with a deprecated function (getFormattedErrorMessages()).
# So now we've changed this file to look in Tobey's home for the jsoncpp libs.
# One funky thing with the jsoncpp build is that it puts the libraries in 
# an architecture and compiler dependant sub-directory. So we have to add that to the 
# LD_LIBRARY_PATH, as the linker does not seem smart enough to look the extra 
# level of depth...

# NOTE: (Nov 2017) Using EasyBuild, we no longer need to update LD_LIBRARY_PATH
# or manually adjust the jsoncpp path in the Makefile. We might want a separate
# environment setup script for Ruth's atlas environment?

echo "Loading modules..."
module purge
module load jsoncpp/1.8.1-foss-2016a netCDF/4.4.0-foss-2016a Boost/1.55.0-foss-2016a-Python-2.7.11
module load netcdf4-python/1.2.2-foss-2016a-Python-2.7.11

echo "Setting up site specific inlcudes..."
export SITE_SPECIFIC_INCLUDES="-I/home/UA/tcarman2/.local/easybuild/software/jsoncpp/1.8.1-foss-2016a/include/jsoncpp/ -I/home/UA/tcarman2/.local/easybuild/build/netCDF/4.4.0/foss-2016a/netcdf-c-4.4.0/include/"

echo "Setting up site specific libs..."
export SITE_SPECIFIC_LIBS="-L/home/UA/tcarman2/.local/easybuild/software/Boost/1.55.0-foss-2016a-Python-2.7.11/lib/"

echo "NOTE: This file will NOT work if it is run as a script!"
echo "      Instead use the 'source' command like this:"
echo "      $ source env-setup-scripts/setup-env-for-atlas.sh"
echo ""


