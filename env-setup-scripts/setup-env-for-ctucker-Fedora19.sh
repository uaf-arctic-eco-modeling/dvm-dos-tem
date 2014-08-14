#!/bin/bash

# Set environment variables for working with dvm-dos-tem on 
# tobey's development machine.

# I was unable to get a system install of BoostLog to work
# on Fedora 19. I think this is a temporary problem that
# I can get around with a local rpm build from source
# and subsequent yum install. But for now...

echo "Setting up site specific inlcudes..."
export SITE_SPECIFIC_INCLUDES="-I/home/colin_tucker/boost_1_55_0 -I/usr/include/jsoncpp"

echo "Setting up site specific libs..."
export SITE_SPECIFIC_LIBS="-L/home/colin_tucker/boost_1_55_0/stage/lib -L/user/lib64"

echo "Setting the path for loading libraries..."
export LD_LIBRARY_PATH="/usr/lib64:/home/colin_tucker/boost_1_55_0/stage/lib:$LD_LIBRARY_PATH"

echo "Remember to downgrade NetCDF!!"
