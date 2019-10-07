#!/bin/bash

# setting up to use boost on modex
echo "Loading module files..."
echo "NOTE: This will work with netcdf/4.3.3.1 or netcdf/4.7.1-gnu540" 
echo ""
module purge; module load python/2.7.14 gcc/5.4.0 boost/1.67.0 netcdf/4.7.1-gnu540 jsoncpp/jsoncpp-1.8.4

echo "Setting up site specific inlcudes..."
echo ""
export SITE_SPECIFIC_INCLUDES="-I/data/software/src/jsoncpp_1.8.4/jsoncpp-1.8.4/include/ -I/data/software/src/openblas/OpenBLAS-0.3.7/lapack-netlib/LAPACKE/include/"

echo "Setting up site specific link flags..."
echo "NOTE: I have no idea why this has become an issue all of a sudden. Seems "
echo "      to have to do with linking openblas, but for some reason now we get "
echo "      a netcdf error about unresolved symbols in TEMUtilityFunctions.cpp?!?"
echo "      Interwebs say that this can be an issue if you don't have netcdf 4 "
echo "      enabled but I checked that we do (nc-config). And this hasn't been an "
echo "      issue on any other machine with dvmdostem v0.2.3. So here we add some "
echo "      special options to the gcc link step."
echo ""
export SITE_SPECIFIC_LINK_FLAGS="-Wl,--unresolved-symbols=ignore-in-object-files"

echo "Setting up site specific libs..."
echo ""
export SITE_SPECIFIC_LIBS="-L/data/software/boost/1.67.0/lib/ -L/data/software/src/jsoncpp_1.8.4/jsoncpp-1.8.4/build-shared/ -L/data/software/src/openblas/OpenBLAS-0.3.7/"

# Also got this to work with statically linked openblas, by using an explicit
# full path to the .a file.
echo "Adjusting Makefile to use static linked openblas (for lapacke libary)."
echo ""
sed -e 's:-llapacke:-lopenblas:' Makefile > Makefile.tmp && mv Makefile.tmp Makefile

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
echo "NOTE: Please remember not to commit the modified src/TEMUtilityFunctions.cpp or Makefile!"
echo "      You can revert the change with this command:"
echo "      $ git checkout -- src/TEMUtilityFunctions.cpp"


