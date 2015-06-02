#!/bin/bash

# setting up to use boost on atlas
# Ruth has provided jsoncpp for us (used for the calibration interface)
# and Tobey has provided boost (used for a variety of things - logging, signals, etc)

echo "Setting up site specific inlcudes..."
export SITE_SPECIFIC_INCLUDES="-I/home/UA/tcarman2/boost_1_55_0/ -I/home/UA/rarutter/include"

echo "Setting up site specific libs..."
export SITE_SPECIFIC_LIBS="-L/home/UA/tcarman2/boost_1_55_0/stage/lib -L/home/UA/rarutter/lib"

echo "Setting the path for loading libraries..."
export LD_LIBRARY_PATH="/home/UA/rarutter/lib:/home/UA/tcarman2/boost_1_55_0/stage/lib:$LD_LIBRARY_PATH"

echo "Fixing jsoncpp library name in Makefile..."
sed -e 's/\<ljsoncpp\>/ljson_linux-gcc-4.4.7_libmt/g' Makefile > Makefile.tmp && mv Makefile.tmp Makefile

echo "NOTE: This file will NOT work if it is run as a script!"
echo "      Instead use the 'source' command like this:"
echo "      $ source env-setup-scripts/setup-env-for-atlas.sh"
echo ""
echo "NOTE: Please remember not to commit the modified Makefile!!"
echo "      You can revert the change with this command:"
echo "      $ git checkout -- Makefile"


