#/bin/bash
#
# June 2023
# T. Carman
#
# Driver script for executing a comparison test between a feature branch and
# a base branch (master); meant as companion to final_test_new.py
# 
# Not sure if this was ever run continuously or if commands were copied to a 
# terminal block by block...

# Run the base case - generally this should be the master branch, or the most
# recently tagged version.
git checkout master
git pull upstream master
./docker-build-wrapper.sh
V_TAG=$(git describe) docker compose up -d
docker compose exec dvmdostem-dev bash
make

INDS=/data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_CALM_Venetie_10x10

mkdir -p /data/workflows/test_PR593
cp /work/config/output_spec.csv /data/workflows/test_PR593

outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on GPP m c
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on RH m l
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on NETNMIN m l
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on EET m c
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on PET m p
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on LTRFALC m c
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on LTRFALN m c
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on RM m c
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on RG m c
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on INGPP m c
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on ALD y
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on VEGC m c
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on VEGN m c
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on WATERTAB m
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on SHLWC m
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on DEEPC m
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on MINEC m
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on AVLN m l
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on ORGN m l
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on LAYERTYPE m l
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on LAYERDEPTH m l
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on LAYERDZ m l
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on TLAYER m l
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on VEGC m c
outspec_utils.py /data/workflows/test_PR593/output_spec.csv --on VEGN m c


mkdir -p /data/workflows/test_PR593/base
mkdir -p /data/workflows/test_PR593/base/restart
mkdir -p /data/workflows/test_PR593/base/continuous

setup_working_directory.py --input-data-path $INDS /data/workflows/test_PR593/base/restart
setup_working_directory.py --input-data-path $INDS /data/workflows/test_PR593/base/continuous

# Do the continuous run 
cd /data/workflows/test_PR593/base/continuous
cp /data/workflows/test_PR593/output_spec.csv config/
runmask-util.py --reset run-mask.nc
runmask-util.py --yx 0 0 run-mask.nc
dvmdostem -l err -p 100 -e 100 -s 50 -t 115 -n 0

# Do the restart run
cd /data/workflows/test_PR593/base/restart
cp /data/workflows/test_PR593/output_spec.csv config/
runmask-util.py --reset run-mask.nc
runmask-util.py --yx 0 0 run-mask.nc
cp /data/workflows/test_PR593/base/continuous/output/restart-*.nc output/
dvmdostem -l err --no-output-cleanup --restart-run -p 0 -e 0 -s 0 -t 115 -n 0

# Log out of container
exit
docker compose down

# Get the new branch
git checkout fix_restart
git pull upstream fix_restart

# Make a temporary integration branch so that we can pull in upstream changes
# that make things run smoother...
git checkout -b temp-integration
git merge master

# re-build containers
./docker-build-wrapper.sh
V_TAG=$(git describe) docker compose up -d
docker compose exec dvmdostem-dev bash
make

# Setup directories
mkdir -p /data/workflows/test_PR593/fix
mkdir -p /data/workflows/test_PR593/fix/restart
mkdir -p /data/workflows/test_PR593/fix/continuous

# This has to be defined again since we are in a different container from
# the base run
INDS=/data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_CALM_Venetie_10x10

# Set everything up...
scripts/setup_working_directory.py --input-data-path $INDS /data/workflows/test_PR593/fix/restart
scripts/setup_working_directory.py --input-data-path $INDS /data/workflows/test_PR593/fix/continuous

cd /data/workflows/test_PR593/fix/continuous
cp /data/workflows/test_PR593/output_spec.csv config/

runmask-util.py --reset run-mask.nc
runmask-util.py --yx 0 0 run-mask.nc

# Do the continuous run
dvmdostem -l err -p 100 -e 100 -s 50 -t 115 -n 0

# Do the restart run
cd /data/workflows/test_PR593/fix/restart
cp /data/workflows/test_PR593/output_spec.csv config/
runmask-util.py --reset run-mask.nc
runmask-util.py --yx 0 0 run-mask.nc
cp /data/workflows/test_PR593/fix/continuous/output/restart-*.nc output/
dvmdostem -l err --no-output-cleanup --restart-run -p 0 -e 0 -s 0 -t 115 -n 0



