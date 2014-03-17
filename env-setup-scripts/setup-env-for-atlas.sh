#!/bin/bash


# setting up to use boost on atlas

echo "Setting up site specific inlcudes..."
export SITE_SPECIFIC_INCLUDES="-I/home/UA/tcarman2/boost_1_55_0"

echo "Setting up site specific libs..."
export SITE_SPECIFIC_LIBS="-L/home/UA/tcarman2/boost_1_55_0/stage/lib"

echo "Setting the path for loading libraries..."
export LD_LIBRARY_PATH="/home/UA/tcarman2/boost_1_55_0/stage/lib:$LD_LIBRARY_PATH"

