#!/bin/bash

# Paths here assume that you are running inside 
# docker container with the input catalog and a 
# workflows directory mounted in /data


# Copy paste as needed to run workflow...
# Or maybe this will actually run as a script??
# Haven't tried doing it all at once


# 1) setup working directories:
for i in basecase modopt1 modopt2 modopt3;
do
  ./scripts/setup_working_directory.py \
  --input-data-path /data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_CALM_Betty_Pingo_MNT_10x10/ \
  /data/workflows/workshop-lab2/$i
done

# 2) run mod script
for i in 1 2 3;
do
  ./scripts/Input_exp.py --opt $i \
  --inpath /data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_CALM_Betty_Pingo_MNT_10x10/ \
  --outpath /data/workflows/workshop-lab2/modopt$i
done
