#!/bin/bash

# Tobey Carman
# Sept 2015
# UAF, Spatial Ecology Lab
#
# Take a snapshot of calibration state by making static plots
# from the json files for all the suites, both monthly and yearly.
# Spefify the pft to plot as the first command line arg. e.g.:
#
#     $ ./snapshot 2
#


PFT=$1

echo "Clearing/removing your snapshot directory..."
rm -r snapshot/monthly-plots
rm -r snapshot/yearly-plots

echo "Making new snapshot directory..."
mkdir -p snapshot
mkdir -p snapshot/monthly-plots
mkdir -p snapshot/yearly-plots

echo "Create monthly plots..."
./calibration/calibration-viewer.py --monthly --pft $PFT --no-show --save-name snapshot/monthly-plots/Vegetation --suite Vegetation
./calibration/calibration-viewer.py --monthly --pft $PFT --no-show --save-name snapshot/monthly-plots/VegSoil --suite VegSoil
./calibration/calibration-viewer.py --monthly --pft $PFT --no-show --save-name snapshot/monthly-plots/Soil --suite Soil
./calibration/calibration-viewer.py --monthly --pft $PFT --no-show --save-name snapshot/monthly-plots/Fire --suite Fire
./calibration/calibration-viewer.py --monthly --pft $PFT --no-show --save-name snapshot/monthly-plots/NCycle --suite NCycle
./calibration/calibration-viewer.py --monthly --pft $PFT --no-show --save-name snapshot/monthly-plots/Environment --suite Environment

echo "Create yearly plots..."
./calibration/calibration-viewer.py --pft $PFT --no-show --save-name snapshot/yearly-plots/Vegetation --suite Vegetation
./calibration/calibration-viewer.py --pft $PFT --no-show --save-name snapshot/yearly-plots/VegSoil --suite VegSoil
./calibration/calibration-viewer.py --pft $PFT --no-show --save-name snapshot/yearly-plots/Soil --suite Soil
./calibration/calibration-viewer.py --pft $PFT --no-show --save-name snapshot/yearly-plots/Fire --suite Fire
./calibration/calibration-viewer.py --pft $PFT --no-show --save-name snapshot/yearly-plots/NCycle --suite NCycle
./calibration/calibration-viewer.py --pft $PFT --no-show --save-name snapshot/yearly-plots/Environment --suite Environment
