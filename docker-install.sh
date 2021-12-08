#!/bin/bash 

# This script will build the docker images for the dvmdostem project.
# Note: Some steps may take a while, please be patient.

# Makes a general development image with various dev tools installed:
# e.g. compiler, make, gdb, etc
docker build --target cpp-dev --tag cpp-dev:0.0.1 .

# Makes the specific dvmdostem development image with dvmdostem
# specific dependencies installed, e.g:
# boost, netcdf, jsoncpp, etc
# Intention is that your host machine's repo will be mounted 
# as a volume at /work, and you can use this container as 
# a compile time and run time environment.
docker build --target dvmdostem-dev --tag dvmdostem-dev:0.0.1 .

# An image with the compiled dvmdostem binary program inside it
# Intention is to use this purely as a compile time environment
# used to create the dvmdostem binary so that it can be copied into
# the lean run image.
docker build --target dvmdostem-build --tag dvmdostem-build:0.0.1 .

# A lean images with only the bare minimum stuff to run dvmdostem
# Does NOT have development tools, compilers, editors, etc
# First we run a container from the dev image, use it to compile the code
# with a volume mount, so that the resulting binary ends up in our 
# local directory on this host. Then when building the run image, we
# copy the binary from local host into the image.
#docker run --rm --volume $(pwd):/work dvmdostem-dev:0.0.1 make
docker build --target dvmdostem-run --tag dvmdostem-run:0.0.1 .



# The bastard step child needed to run various gdal tools
docker build --tag dvmdostem-mapping-support:0.0.1 -f Dockerfile-mapping-support .
