#!/bin/bash

# setting up to use boost on modex
echo "Loading module files..."
module purge; module load python/2.7.14 gcc/5.4.0 boost/1.67.0 netcdf/4.4.1.1-gnu540

echo "Setting up site specific inlcudes..."
export SITE_SPECIFIC_INCLUDES="-I/data/software/src/jsoncpp_1.8.4/jsoncpp-1.8.4/include/"

echo "Setting up site specific libs..."
export SITE_SPECIFIC_LIBS="-L/data/software/boost/1.67.0/lib/ -L/data/software/src/jsoncpp_1.8.4/jsoncpp-1.8.4/build-shared/"

echo "Setting path for loading libraries..."
export LD_LIBRARY_PATH="/data/software/gcc/gcc-5.4.0/lib64/:/data/software/src/jsoncpp_1.8.4/jsoncpp-1.8.4/build-shared/:/data/software/boost/1.67.0/lib/"

echo "NOTE: With recent versions of jsoncpp, the API changed so that Json::Reader "
echo "      is no longer a valid use pattern. Fortunatley this was only used once "
echo "      in our application, in src/TEMUtilityFunctions.cpp, line ~206 in "
echo "      parse_control_file(...). As of 4/24/2018 we are reluctant to change the "
echo "      dvmdostem application because it would break all our other intstalls of "
echo "      jsoncpp and force and upgrade. So what we'll do here is apply a "
echo "      'monkey patch' on modex so that we can use the latest version."
echo ""
git apply env-setup-scripts/modex.monkeypatch.patch

echo "NOTE: This file will NOT work if it is run as a script!"
echo "      Instead use the 'source' command like this:"
echo "      $ source env-setup-scripts/setup-env-for-atlas.sh"
echo ""
echo "NOTE: Please remember not to commit the modified src/TEMUtilityFunctions.cpp!!!"
echo "      You can revert the change with this command:"
echo "      $ git checkout -- src/TEMUtilityFunctions.cpp"


