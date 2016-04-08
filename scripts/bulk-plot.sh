#!/bin/bash

# T. Carman, Spring 2016

# Simple example script for generating a bunch of static plots
# using the calibration-viewer.py program. Intended to be modified
# as needed.
#

# 
# Command line argument processing
#
function usage () {
  echo "usage: $ ./bulk-plot TAG"
  echo "       $ ./bulk-plot [--numpfts N] [--sparse] [-h | --help] --outdir PATH --tag TAG"
  echo "Error: " $1
}

NUM_PFTS=10
SUITES=("Fire" "Soil" "Vegetation" "VegSoil" "Environment" "NCycle")
TAG=
TARGET_CMT=5
OUTDIR=

while [ "$1" != "" ]; do
  case $1 in
    -n | --numpfts )    shift
                        NUM_PFTS="$1"
                        ;;

    # useful for debugging so you don't have to 
    # wait for everything to plot
    --sparse )          SUITES=("VegSoil")
                        ;;

    --tag )             shift
                        TAG="$1"
                        ;;

    --targetcmt )       shift
                        TARGET_CMT="$1"
                        ;;

    --outdir )          shift
                        OUTDIR="$1"
                        ;;

    -h | --help )       usage "no error"
                        exit
                        ;;

    * )                 usage "Problem with command line arguments!"
                        exit 1
  esac
  shift
done

if [[ $TAG == "" ]]
then
  usage "You must supply a tag!"
  exit 1
fi
if [[ $OUTDIR == "" ]]
  then
  usage "You must supply a directory for output!"
  exit 1
fi

if [[ ! -x "calibration/calibration-viewer.py" ]]
then
  echo "Cannot find the plotter from here!"
  echo "Try executing this script ($(basename $0)) from the main dvmdostem directory."
  exit 1
fi

echo "Plotting for pfs 0 to $NUM_PFTS"
echo "Will plot these suites:"
for SUITE in ${SUITES[@]}
do
  echo "    $SUITE"
done
echo "Using TAG: $TAG"

#
# Finally, start working
#
SAVE_LOC="$OUTDIR/$TAG"
echo "Making directory: $SAVE_LOC"
mkdir -p "$SAVE_LOC"

# Loop over suites and pfts creating and saving a bunch of plots.
for SUITE in ${SUITES[@]};
do

  if [[ "$SUITE" == "Fire" || "$SUITE" == "Environment" ]]
  then
    # echo $SUITE
    ./calibration/calibration-viewer.py --suite "$SUITE" \
                                        --tar-cmtnum "$TARGET_CMT" \
                                        --no-show \
                                        --save-name "$SAVE_LOC/$TAG-$SUITE"
  else
    for (( I=0; I<=$NUM_PFTS; ++I ))
    do
      # echo $SUITE $I
      ./calibration/calibration-viewer.py --suite "$SUITE" \
                                          --tar-cmtnum "$TARGET_CMT" \
                                          --no-show \
                                          --save-name "$SAVE_LOC/$TAG-$SUITE-pft$I" \
                                          --pft "$I"
    done
  fi

done


