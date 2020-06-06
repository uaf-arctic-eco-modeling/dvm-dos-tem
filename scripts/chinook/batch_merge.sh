#!/bin/bash

# Merge dvm-dos-tem outputs along spatial dimensions

# H. Genet, T. Carman, R. Rutter 
# 2018


OUTPUT_DIR_PREFIX="/center1/AKINTMDL/rarutter/Toolik_50x50_ncarprodrun_20181204_0"
OUTPUT_SPEC_PATH="./config/output_spec_production.csv"
STAGES="eq sp tr sc"
TIMESTEPS="daily monthly yearly"
BATCH_DIR="${OUTPUT_DIR_PREFIX}/batch-run"
FINAL_DIR="${OUTPUT_DIR_PREFIX}/all-merged"

mkdir -p "${OUTPUT_DIR_PREFIX}/all-merged"

variables=$(cat $OUTPUT_SPEC_PATH | cut -d, -f1)

#If merging files for a single variable
if [ $# != 0 ] ; then
  echo "single variable: $1"
  variables=$1
fi

# First handle all the normal outputs.
for variable in $variables 
do
  echo "Processing variable: $variable"
  if [ $variable != 'Name' ] ; then   # ignore the header

    for stage in $STAGES
    do
      echo "  --> stage: $stage"

      for timestep in $TIMESTEPS
      do
        echo "  --> timestep: $timestep"

        # Determine the file name of the outputs variable for the specific
        # run mode and time step
        filename="${variable}_${timestep}_${stage}.nc" # Not sure why we need {}??
        echo "  --> find $filename"

        # List all the output files for the variable in question in every 
        # output sub-directory (one directory = one sub-regional run)
        filelist=$(find $BATCH_DIR -maxdepth 4 -type f -name $filename)
        #echo "  --> filelist: $filelist"

        if [ ! -z "$filelist" ] ; then

          # Concatenate all these files together
          echo "merge files"

          # Something is messed up with my quoting, as this only works with 
          # the filelist variable **unquoted** which I think is bad practice.
          ncea -O -h -y avg $filelist "$FINAL_DIR/$filename"
        else
          echo "  --> nothing to do; no files found..."
        fi
      done
    done
  fi
done

# Next handle the run_status file
filelist=$(find $BATCH_DIR -maxdepth 4 -type f -name "run_status.nc")
echo "THE FILE LIST IS: $filelist"
if [ ! -z "$filelist" ] ; then
  # NOTE: for some reason the 'avg' operator does not work with this file!!
  ncea -O -h -y max $filelist "$FINAL_DIR/run_status.nc"
else
  echo "nothing to do - no run_status.nc files found?"
fi

# Finally, handle the fail log
filelist=$(find $BATCH_DIR -maxdepth 4 -type f -name "fail_log.txt")
echo "THE FILE LIST IS: $filelist"
if [ ! -z "$filelist" ] ; then
  for f in $filelist
  do
    cat $f >> "$FINAL_DIR/fail_log.txt"
  done
else
  echo "nothing to do - no fail_log.txt files found?"
fi




