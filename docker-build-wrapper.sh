#!/bin/bash 

# This script will build the docker images for the dvmdostem project.
# Note: Some steps may take a while, please be patient.

# Note: You may try --no-cache with the docker build commands if they
# fail with various errors reccomending --fix-missing errors.

# Here is a handy formulation for finding and deleting old docker images, 
# adjust the grep commands as necessary: 
#
#     $ docker image ls | grep dvmdostem \
#       | grep v0.5.6-87-g | awk '{print $1,$2}' | sed -e 's/ /:/g' 
#
# This can then be wrapped in a for loop that calls docker image rm to cleanup.

# Use --tags so that lightweight tags are found. Useful for local tagging
# as well as making sure that images built during the release process are 
# appropriately tagged.
GIT_VERSION=$(git describe --tags)

# IMAGE FOR GENERAL C++ DEVELOPMENT
# Makes a general development image with various dev tools installed:
# e.g. compiler, make, gdb, etc
docker build --build-arg GIT_VERSION=$GIT_VERSION \
             --target cpp-dev --tag cpp-dev:$GIT_VERSION .

# IMAGE FOR GENERAL DVMDOSTEM DEVELOPMENT 
# Makes the specific dvmdostem development image with dvmdostem specific
# dependencies installed, e.g: boost, netcdf, jsoncpp, etc. Intention is that
# your host machine's repo will be mounted as a volume at /work, and you can
# use this container as a compile time and run time environment.
docker build --build-arg GIT_VERSION=$GIT_VERSION \
             --target dvmdostem-dev --tag dvmdostem-dev:$GIT_VERSION .

# IMAGE FOR BUILDING (COMPILING) DVMDOSTEM
# This is for a stand-alone container that can be used to compile the
# dvmdostem binary without needing to mount volumes when the container
# is started. The required files are copied directly to the image.
# The intention is to use this purely as a compile time environment 
# used to create the dvmdostem binary so that it can be copied into
# the lean run image.
docker build --build-arg GIT_VERSION=$GIT_VERSION \
             --target dvmdostem-build --tag dvmdostem-build:$GIT_VERSION .

# IMAGE FOR SIMPLY RUNNING DMVDOSTEM AND ASSOCIATED SCRIPTS
# A lean images with only the bare minimum stuff to run dvmdostem
# Does NOT have development tools, compilers, editors, etc
docker build --build-arg GIT_VERSION=$GIT_VERSION \
             --target dvmdostem-run --tag dvmdostem-run:$GIT_VERSION .


# IMAGE FOR WORKING WITH MAPPING TOOLS, SPECIFICALLY GDAL
# The bastard step child needed to run various gdal tools
docker build --build-arg GIT_VERSION=$GIT_VERSION \
             --tag dvmdostem-mapping-support:$GIT_VERSION \
             -f Dockerfile-mapping-support .
