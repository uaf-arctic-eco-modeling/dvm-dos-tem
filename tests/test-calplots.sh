#!/bin/bash


# Make a place to save the plots (ensuring it is clean to begin with)
rm -rf auto-post-process
mkdir -p auto-post-process


./calibration/ExpandingWindow.py --suite Environment --pft 0 \
                                 --save-name auto-post-process/environment \
                                 --no-show

./calibration/ExpandingWindow.py --suite VegSoil --pft 0 \
                                 --save-name auto-post-process/vegsoil \
                                 --no-show


# SAVE THIS OLD SET OF COMMANDS FROM JENKINS
#  - This stuff is probably obsolete, but we will keep it around
#    for a bit for reference or ideas...
#cd $WORKSPACE
#
## Run the model.
## All default settings - should be a single cohort, in eq stage.
#export LD_LIBRARY_PATH="/var/lib/jenkins/boost_1_54_0/stage/lib:/var/lib/jenkins/lib:$LD_LIBRARY_PATH"
#./dvmdostem
#
## Make a place to work (ensuring it is clean to begin with)
#rm -rf auto-post-process
#mkdir -p auto-post-process
#
#cd auto-post-process
#
## Download the plotting tools
## Get just the last commit, then remove
## the .git directory in ddtv before it can conflict with 
## the .git directory for the dvm-dos-tem workspace
#git clone --depth=1 https://github.com/tobeycarman/ddtv.git ddtv
#rm -rf ddtv/.git
#
## Generate csv files from netcdf
#ddtv/output-extract.R --nc-files-dir ../DATA/test_single_site/output/ --generated-files-dir outex-gen-files
#
## Generate plots from csv files
#ddtv/plotting-output.R --generated-csv-dir "../DATA/test_single_site/output/outex-gen-files" --output-id devel-plots
#
## CLEANUP?
## or is it ok to leave this around and 
## let it get cleaned up on the next build?