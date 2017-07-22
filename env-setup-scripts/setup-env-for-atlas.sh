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

echo "Setting up site specific inlcudes..."
export SITE_SPECIFIC_INCLUDES="-I/home/UA/tcarman2/boost_1_55_0/ -I/home/UA/tcarman2/custom-software/jsoncpp/include"

echo "Setting up site specific libs..."
export SITE_SPECIFIC_LIBS="-L/home/UA/tcarman2/boost_1_55_0/stage/lib -L/home/UA/tcarman2/custom-software/jsoncpp/libs/linux-gcc-4.4.7"

echo "Setting the path for loading libraries..."
export LD_LIBRARY_PATH="/home/UA/tcarman2/custom-software/jsoncpp/libs/linux-gcc-4.4.7:/home/UA/tcarman2/boost_1_55_0/stage/lib:$LD_LIBRARY_PATH"

echo "Fixing jsoncpp library name in Makefile..."
sed -e 's/\<ljsoncpp\>/ljson_linux-gcc-4.4.7_libmt/g' Makefile > Makefile.tmp && mv Makefile.tmp Makefile

echo "NOTE: This file will NOT work if it is run as a script!"
echo "      Instead use the 'source' command like this:"
echo "      $ source env-setup-scripts/setup-env-for-atlas.sh"
echo ""
echo "NOTE: Please remember not to commit the modified Makefile!!"
echo "      You can revert the change with this command:"
echo "      $ git checkout -- Makefile"


