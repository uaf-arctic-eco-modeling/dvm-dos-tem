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
./calibration/ExpandingWindow.py --monthly --pft $PFT --no-show --save-name snapshot/monthly-plots/Vegetation --suite Vegetation
./calibration/ExpandingWindow.py --monthly --pft $PFT --no-show --save-name snapshot/monthly-plots/VegSoil --suite VegSoil
./calibration/ExpandingWindow.py --monthly --pft $PFT --no-show --save-name snapshot/monthly-plots/Soil --suite Soil
./calibration/ExpandingWindow.py --monthly --pft $PFT --no-show --save-name snapshot/monthly-plots/Fire --suite Fire
./calibration/ExpandingWindow.py --monthly --pft $PFT --no-show --save-name snapshot/monthly-plots/NCycle --suite NCycle
./calibration/ExpandingWindow.py --monthly --pft $PFT --no-show --save-name snapshot/monthly-plots/Environment --suite Environment

echo "Create yearly plots..."
./calibration/ExpandingWindow.py --pft $PFT --no-show --save-name snapshot/yearly-plots/Vegetation --suite Vegetation
./calibration/ExpandingWindow.py --pft $PFT --no-show --save-name snapshot/yearly-plots/VegSoil --suite VegSoil
./calibration/ExpandingWindow.py --pft $PFT --no-show --save-name snapshot/yearly-plots/Soil --suite Soil
./calibration/ExpandingWindow.py --pft $PFT --no-show --save-name snapshot/yearly-plots/Fire --suite Fire
./calibration/ExpandingWindow.py --pft $PFT --no-show --save-name snapshot/yearly-plots/NCycle --suite NCycle
./calibration/ExpandingWindow.py --pft $PFT --no-show --save-name snapshot/yearly-plots/Environment --suite Environment
