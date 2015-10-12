#!/bin/bash

#Tests to be run on a weekly basis.

#These are less critical to check frequently.
#easier to locate errors

#Prep


#Build
echo "Building with Scons parallel"
scons -j4
scons -c

#Add:
# - build library with scons

#Run


#Plot

