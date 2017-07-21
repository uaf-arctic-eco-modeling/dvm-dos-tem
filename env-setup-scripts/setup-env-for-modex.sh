#!/bin/bash

# setting up to use boost on modex
echo "Loading module files..."
module purge; module load python/2.7.13 gcc/4.8.4 boost/1.64.0 netcdf/4.4.1.1-gnu540

echo "Setting up site specific inlcudes..."
export SITE_SPECIFIC_INCLUDES="-I/data/software/src/jsoncpp/include/"

echo "Setting up site specific libs..."
export SITE_SPECIFIC_LIBS="-L/data/software/boost/1.64.0/lib"

# For now don't even need the LD_LIBRARY_PATH variable set -
# This seems to be smart enough with the proper modules loaded to 
# pick up the right path to boost etc...
#export LD_LIBRARY_PATH="/home/UA/rarutter/lib:/home/UA/tcarman2/boost_1_55_0/stage/lib:$LD_LIBRARY_PATH"

# For some reason we were never able to link to the shared version of 
# jsoncpp...not sure why?? tried lots of stuff. But in the end, this
# works, just link directly to the static one.
echo "Fixing jsoncpp library name in Makefile..."
sed -e 's:-ljsoncpp\>:/data/software/src/jsoncpp/libs/linux-gcc-4.8.4/libjson_linux-gcc-4.8.4_libmt.a:g' Makefile > Makefile.tmp && mv Makefile.tmp Makefile 


echo "NOTE: You may run into issues with a deprecated function in"
echo "      jsoncpp. Very annoying. Temporary work around is to "
echo "      comment out the offending line in src/TEMUtilityFunctions.cpp"
echo "      (in the parse_control_file(..) function)."
echo ""
echo "NOTE: This file will NOT work if it is run as a script!"
echo "      Instead use the 'source' command like this:"
echo "      $ source env-setup-scripts/setup-env-for-atlas.sh"
echo ""
echo "NOTE: Please remember not to commit the modified Makefile!!"
echo "      You can revert the change with this command:"
echo "      $ git checkout -- Makefile"


