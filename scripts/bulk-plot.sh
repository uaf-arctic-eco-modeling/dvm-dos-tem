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
	echo "Error: " $1
}

if [[ $# -lt 1 ]]
then
	usage "Not enough args"
	exit
fi

# Find sha of most recent commit
SHA=$(git log -1 --oneline | cut -d ' ' -f 1)

TAG="all-mods-$SHA"
echo "Using TAG: " $TAG

# vv-------- CHANGE SETTINGS AS NEEDED ----vv

NUM_PFTS=7
TARGET_CMT=5
SUITES=("Fire" "Soil" "Vegetation" "VegSoil" "Environment" "NCycle")

# Build a tag to use as the directory AND
# to preprend to each file name (before suite and pft)

# CAUTION - Need to check that this works right no matter
# where the bulk-plot script is called from!!
SAVE_LOC="../../output-vault/$TAG"

#
# vv-------- USER SHOULDN'T NEED TO MODIFY BELOW HERE ---vv
#
echo "MAKING THE FOLLOWING DIRECTORY:"
echo "$SAVE_LOC"
mkdir -p "$SAVE_LOC"

# Loop over suites and pfts creating and saving a bunch of plots.
for SUITE in ${SUITES[@]};
do

	if [[ "$SUITE" == "Fire" || "$SUITE" == "Environment" ]]
	then
	  # echo $SUITE
	  ../calibration/calibration-viewer.py --suite "$SUITE" \
	  																		 --tar-cmtnum "$TARGET_CMT" \
	  																		 --no-show \
	  																		 --save-name "$SAVE_LOC/$TAG-$SUITE"
	else
		for (( I=0; I<=$NUM_PFTS; ++I ))
		do
			# echo $SUITE $I
		  ../calibration/calibration-viewer.py --suite "$SUITE" \
		  																		 --tar-cmtnum "$TARGET_CMT" \
		  																		 --no-show \
		  																		 --save-name "$SAVE_LOC/$TAG-$SUITE-pft$I" \
		  																		 --pft "$I"
		done
	fi

done

function report_args {
	echo $#
	echo '0 -->' $0
	echo '1 -->' $1
	echo '2 -->' $2
	echo '3 -->' $3
	echo '4 -->' $4
	exit
}
