#!/bin/bash

echo "Building with Makefile..."

make clean;
scons --clean # scons and make leave files around that confuse eachother...

make -j4 dvm
make -j4 lib


echo "Building with Scons..."
make clean
scons --clean # scons and make leave files around that confuse eachother...

scons -j4

# Other stuff to test?
# - build w/ and w/o MPI
# - build single core and parallel
# - build library with scons

echo "Building documentation with Doxygen..."
doxygen -u
if [ ! -d docs/dvm-dos-tem ]; then
  mkdir -p docs/dvm-dos-tem
fi
doxygen Doxyfile