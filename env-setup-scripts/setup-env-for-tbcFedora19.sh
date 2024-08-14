#!/bin/bash

# Set environment variables for working with dvm-dos-tem on 
# tobey's development machine.

# I was unable to get a system install of BoostLog to work
# on Fedora 19. I think this is a temporary problem that
# I can get around with a local rpm build from source
# and subsequent yum install. But for now...

echo "Setting up site specific inlcudes..."
export SITE_SPECIFIC_INCLUDES="-I/home/tbc/usr/local/include"

echo "Setting up site specific libs..."
export SITE_SPECIFIC_LIBS="-L/home/tbc/usr/local/lib"

echo "Setting the path for loading libraries..."
export LD_LIBRARY_PATH="/home/tbc/usr/local/lib:$LD_LIBRARY_PATH"

echo "Remember to downgrade NetCDF!!"
