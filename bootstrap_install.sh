#!/bin/bash

# T. Carman, Oct 2025
#
# Draft of a simple install script for dvmdostem and pyddt. 
# 
# Developing for use in Docker container for NGEE ModEx 2025 Fall workshop. This
# is not intended to be a full-featured installer, just something simple to copy
# the relevant files into a location in the image. Notably this does not
# actually install the pyddt package into a Python environment, it just copies
# the files. The user will need to do the installation into their Python
# environment themselves, (e.g. pip install -e pyddt).


# Default installation prefix
PREFIX="install"

# Parse command line arguments
while [ $# -gt 0 ]; do
  case $1 in
    --help|-h)
      echo "Usage: $0 [--prefix=PATH]"
      echo "  --prefix=PATH   Specify installation prefix (default: install)"
      exit 0
      ;;
    --prefix=*)
      PREFIX="${1#*=}" # remove --prefix= part
      ;;
    --prefix)
      PREFIX="$2"
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
  shift
done
echo "Installing to prefix: $PREFIX"

# Create installation directories
mkdir -p "${PREFIX}"
mkdir -p "${PREFIX}/bin"
mkdir -p "${PREFIX}/parameters"
mkdir -p "${PREFIX}/config"
mkdir -p "${PREFIX}/pyddt"

# Copy binary
if [ -f "./dvmdostem" ]; then
  cp ./dvmdostem "${PREFIX}/bin/"
  chmod +x "${PREFIX}/bin/dvmdostem"
else
  echo "Error: dvmdostem binary not found. Try compiling first!"
  exit 1
fi

# Copy directories
if [ -d "./parameters" ]; then
  cp -r ./parameters/* "${PREFIX}/parameters/"
else
  echo "Warning: parameters directory not found. Skipping."
fi

if [ -d "./demo-data" ]; then
  cp -r ./demo-data/* "${PREFIX}/demo-data/"
else
  echo "Warning: demo-data directory not found. Skipping."
fi


if [ -d "./config" ]; then
  cp -r ./config/* "${PREFIX}/config/"
else
  echo "Warning: config directory not found. Skipping."
fi

if [ -d "./pyddt" ]; then
  cp -r ./pyddt/* "${PREFIX}/pyddt/"
else
  echo "Warning: pyddt directory not found. Skipping."
fi

echo "Installation completed in ${PREFIX}"
