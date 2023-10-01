#!/bin/bash

### Author: Hélène Genet
### Contact: hgenet@alaska.edu
### Institution: Institute of Arctic Biology, University of Alaska Fairbanks
### Script purpose: branch comparison. When a new branch is ready to be pushed to github, 
### this scripts can be run to evaluate the effect of the changes brought to the code
### on model outputs. The companion python script of this bash script 
### (simulation_comparison_setup.py) will produce a series of graphs for this purpose.
### the product of this comparison will be a pdf named result.pdf This pdf should be
### provided with the push of any new branch.
### The following information in the "FLAGS" section needs to be edited with the info
### related to the comparison.


### FLAGS

# Path to the main TEM directory
# example: temdir='/work'
temdir=''

# Path to the input directory used to conduct the model simulations and comparisons
# example: indir='/data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_bonanzacreeklter_10x10'
indir=''

# Path to the work directory where simulations will be stored
# example: workdir='/data/workflows/test'
workdir=''

# List of the branches to compare. This list should at least include maaster.
# example: branchlist=(master fire_fix)
branchlist=()

# List of the name of the directories for each simulations. This list should
# be the same SIZE and same ORDER as the list of branches (branchlist).
# example: scdirlist=(master mod1)
scdirlist=()

# List of the name of each simulations - these names will appear in the legend
# of thhe plots. This list should be the same SIZE and same ORDER as the list 
# of branches (branchlist).
# example: scnamelist=("0. master" "1. mod1")
scnamelist=()

# List of the line color and width of each simulations - these line color and width
# will be used to create some of the comparison plots. This list should be 
# the same SIZE and same ORDER as the list of branches (branchlist).
# example: sclinecolorlist=("black" "red"), sclinewidthlist=(4 3)
sclinecolorlist=()
sclinewidthlist=()

# Community type to use for the simulations
# example: cmtnum=1
cmtnum=

# Length of the prerun and equilibrium run (in years)
# example: prerun=10, eqrun=10
prerun=
eqrun=

# Location of the python code to generate the comparison report.
# example: pycode='/data/workflows/fire_fix/simulation_comparison_report.py'
pycode=''


temdir='/work'
indir='/data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_bonanzacreeklter_10x10'
workdir='/data/workflows/test'
branchlist=(master fire_fix)
scdirlist=(master mod1)
scnamelist=("0. master" "1. mod1")
sclinecolorlist=("black" "red")
sclinewidthlist=(4 3)
cmtnum=1
prerun=10 
eqrun=10
pycode='/data/workflows/fire_fix/simulation_comparison_report.py'


### SETTING UP AND CONDUCTING INDIVIDUAL SIMULATIONS

cd $temdir

if [ -d "$workdir" ]; then
    echo "$workdir does exist - please delete or rename this directory or change workdir's name"
else
    echo "Create output folder for the simulations"
    mkdir $workdir
fi  

for (( i=0; i<${#scdirlist[@]}; i++ )); do
    cd $temdir
    sc=${scdirlist[$i]}
    echo "Simulation for $sc scenario"
    if [ -d "$workdir/$sc" ]; then
        echo "   $workdir$sc does exist - please delete or rename this directory or change scdir's name"
        break
    fi
    echo "   create output folder for the simulations"
    mkdir $workdir/$sc
    echo "   checkout related branch and compile"
    git checkout "${branchlist[$i]}"
    make clean
    make
    echo "   setup simulatiion"
    ./scripts/setup_working_directory.py $workdir/$sc --input-data-path $indir
    echo "   select the pixel to run"
    ./scripts/runmask-util.py --reset $workdir/$sc/run-mask.nc
    ./scripts/runmask-util.py --yx 0 0 $workdir/$sc/run-mask.nc
    echo "   select the output variables"
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --empty
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on ALD y 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on AVLN y m l
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on BURNAIR2SOIN y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on BURNSOIC y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on BURNSOILN y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on BURNTHICK y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on BURNVEG2AIRC y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on BURNVEG2AIRN y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on BURNVEG2DEADC y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on BURNVEG2DEADN y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on BURNVEG2SOIABVC y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on BURNVEG2SOIABVN y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on BURNVEG2SOIBLWC y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on BURNVEG2SOIBLWN y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on DEADC y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on DEADN y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on DEEPC y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on DEEPDZ y 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on DWDC y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on DWDN y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on DWDRH y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on EET y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on GPP y m pft 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on INGPP y m pft 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on LAI y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on LAYERDEPTH y m l
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on LAYERDZ y m l
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on LAYERTYPE y m l
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on LTRFALC y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on LTRFALN y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on LWCLAYER y m l
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on MINEC y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on MOSSDEATHC y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on MOSSDEATHN y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on MOSSDZ y 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on NETNMIN y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on NIMMOB y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on NPP y m pft 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on NRESORB y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on NUPTAKELAB y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on NUPTAKEST y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on ORGN y m l
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on PET y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on RG y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on RH y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on RM y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on ROLB y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on SHLWC y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on SHLWDZ y 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on SNOWFALL y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on SNOWTHICK y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on SOMA y m l
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on SOMCR y m l
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on SOMPR y m l
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on SOMRAWC y m l
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on SWE y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on TLAYER y m l
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on TRANSPIRATION y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on VEGC y m pft 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on VEGN y m pft 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on VWCLAYER y m l
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on WATERTAB y m 
    ./scripts/outspec_utils.py $workdir/$sc/config/output_spec.csv --on YSD y 
    echo "   run the simulation"
    cd $workdir/$sc
    sed -i 's/"output_nc_eq": 0,/"output_nc_eq": 1,/' $workdir/$sc/config/config.js
    $temdir/dvmdostem -l err -f $workdir/$sc/config/config.js --force-cmt $cmtnum -p $prerun -e $eqrun -s 0 -t 0 -n 0
done


### SETTING UP AND CONDUCTING INDIVIDUAL SIMULATIONS

pip install xarray 
pip install PIL
pip install pypdf

declare -a POD=$workdir
declare -a PODlist="${scdirlist[@]}"
declare -a scenariolist="${scnamelist[@]}"
declare -a colorlist="${sclinecolorlist[@]}"
declare -a widthlist="${sclinewidthlist[@]}"

python3 $pycode --POD $workdir  --PODlist "${scdirlist[@]}" --scenariolist "${scnamelist[@]}" --colorlist "${sclinecolorlist[@]}" --widthlist "${sclinewidthlist[@]}" 


