#!/bin/bash

# Setting up the environment for the PEcAn VM 1.5.1

# NOTE: I had to install jsoncpp, I think I did it using 
# apt-get and I may have had to install libjsoncpp-dev too.

# Not sure why the include path needs setting...

echo "Setting up site specific inlcudes..."
export SITE_SPECIFIC_INCLUDES="-I/usr/include/jsoncpp"

echo "NOTE: This file will NOT work if it is run as a script!"
echo "      Instead use the 'source' command like this:"
echo "      $ source env-setup-scripts/setup-env-for-pecanVM.sh"
echo ""

