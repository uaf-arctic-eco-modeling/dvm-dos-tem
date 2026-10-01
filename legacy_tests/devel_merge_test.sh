#!/bin/bash

#Basic tests to be run on each commit.

#Prep
#This must be done to turn off the "post-warmup-pause" for running
# in an automated environment
echo "Modifying calibration directives to remove the post warmup pause."
cat <<EOF > config/calibration_directives.txt
{
  "calibration_autorun_settings": {
    //"quitat": 1500,
    "10": ["dsl on", "nfeed on", "dsb on"],
    "pwup": false // "post warm up pause", [true | false], boolean
  }
}
EOF


#Build
make clean
scons -c

echo "Building with Makefile"
make dvm
make lib

#Add:
# - build w/ and w/o MPI
# - build single core and parallel

echo "Building documentation with Doxygen"
doxygen -u
if [ ! -d docs/dvm-dos-tem ]; then
  mkdir -p docs/dvm-dos-tem
fi
doxygen Doxyfile


#Run
./dvmdostem --cal-mode --pre-run-yrs 10 --max-eq 100 --log-level debug

#Add:
# - stages


#Plot
#./calibration/calibration-viewer.py \
#             --suite Environment --pft 0 \
#             --save-name auto-post-process/environment \
#             --no-show

#./calibration/calibration-viewer.py \
#             --suite VegSoil --pft 0 \
#             --save-name auto-post-process/vegsoil \
#             --no-show



