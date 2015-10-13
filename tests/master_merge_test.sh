#!/bin/bash


#Tests to be run on merge to master


#Prep

#Build

#Run
#Is this necessary if immediately preceded by merge to devel?


#Package
#Clean everything prior to zip
#Zip
#tar --exclude-vcs -czf dvmdostem.tgz .
#Build RPM tree structure
#mv dvmdostem.tgz to SOURCES
#verify that all prerequisites are installed - what permissions do we have?
#yum-builddep to install dependencies
#Add openmpi and jsoncpp paths to env variables as necessary
#pack rpm
#rpmbuild -ba --define "release x" --define "version x" SPECS/rpmspec
#Note that the defines above will not be necessary once Jenkins
# is set up correctly.
