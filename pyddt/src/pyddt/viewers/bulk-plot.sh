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
  echo "usage: "
  echo "  $ ./bulk-plot [--numpfts N] [--sparse] [--parallel] [--format F] [-h | --help] --outdir PATH --tag TAG"
  echo ""
  echo "  --sparse    Prints only one suite, for faster runs and testing."
  echo "  --parallel  Runs the plotting script as a background process so"
  echo "              many plots are made in parallel."
  echo "  --numpfts   Change the number of pfts plotted. '3' will plot pfts 0,1,2".
  echo "  --outdir    The path to a directory in which to store the generated plots."
  echo "  --tag       A pre-fix for the folder containing the generated plots."
  echo "              The folder will be created within the folder specified at the"
  echo "              path given for '--outdir'. The current git tag is good to use,"
  echo "              but the value you provide for "--tag" can be anything else you like."
  echo "  --format    The file format to use for saving plots. Default=pdf"
  echo ""
  echo "NOTE: The bulk plot capability has been added directly to the "
  echo "      calibration-viewer.py script. The implementation there is much "
  echo "      more efficient because the json files/archives only need to be "
  echo "      opened once. It is probably preferable to use "
  echo "      calibration-viewer.py over this script! See the "
  echo "      calibration-viewer.py --help flag for more info."
  echo "      "

  if [[ "$#" -gt 0 ]]
  then
    echo "Error: $1"
  fi
  echo ""
}

# Function that basically just passes arguments thru to the
# underlying calibration-viewer. This facilitates running the
# calibration viewer in the background by calling "parallel_plotter <ARGS> &"
function parallel_plotter () {

  ./calibration/calibration-viewer.py "$@"

}


NUM_PFTS=10
SUITES=("Fire" "Soil" "Vegetation" "VegSoil" "Environment" "NCycle")
TAG=
TARGET_CMT=5
OUTDIR=
FORMAT="pdf"
PFLAG=   # Set to '&' to run plotting processes in background.

while [ "$1" != "" ]; do
  case $1 in
    -n | --numpfts )    shift
                        NUM_PFTS="$1"
                        ;;

    # useful for debugging so you don't have to 
    # wait for everything to plot
    --sparse )          SUITES=("VegSoil")
                        ;;

    --parallel )        PFLAG="true"
                        ;;

    --tag )             shift
                        TAG="$1"
                        ;;

    --format )          shift
                        FORMAT="$1"
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

echo "Plotting for pfts 0 to $NUM_PFTS"
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

# Collect metadata
cp "config/config.js" "$SAVE_LOC/"
cp "config/calibration_directives.txt" "$SAVE_LOC"
# build metadata? cmd line args?

# Loop over suites and pfts creating and saving a bunch of plots.
for SUITE in ${SUITES[@]};
do

  if [[ "$SUITE" == "Fire" || "$SUITE" == "Environment" ]]
  then

    args="--save-format $FORMAT --suite $SUITE --tar-cmtnum $TARGET_CMT --no-show --save-name $SAVE_LOC/$TAG-$SUITE"

    if $PFLAG
    then
      parallel_plotter $args &
    else
      parallel_plotter $args
    fi

  else
    for (( I=0; I<$NUM_PFTS; ++I ))
    do

      args="--save-format $FORMAT --suite $SUITE --tar-cmtnum $TARGET_CMT --no-show --save-name $SAVE_LOC/$TAG-$SUITE-pft$I --pft $I"

      if $PFLAG
      then
        parallel_plotter $args &
      else
        parallel_plotter $args
      fi

    done
  fi

done

if $PFLAG
then
  echo "waiting for all sub processes to finish..."
  wait
fi

echo "Done plotting."
