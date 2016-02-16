#!/bin/bash

# T. Carman, Spring 2016

# Simple example script for generating a bunch of static plots
# using the calibration-viewer.py program. Intended to be modified
# as needed.

NUM_PFTS=7
SUITE="Soil"
TAG="oldParams"
SAVE_LOC="../../pestdemo/tussock_full/results-32e669c-tussock_full"

for i in {0..$NUM_PFTS};
do
  ../calibration/calibration-viewer.py --suite "$SUITE" --tar-cmtnum 5 --no-show --save-name "$SAVE_LOC/$TAG-$SUITE-pft$i" --pft "$i"
done
