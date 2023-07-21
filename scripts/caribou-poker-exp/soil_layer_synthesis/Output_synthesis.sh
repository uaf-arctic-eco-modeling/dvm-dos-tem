
#!//usr/local/bin/bash

# Author: Helene Genet, UAF
# Creation date: Jan. 25 2022
# Purpose: general script to synthesis TEM outputs for data analysis



### INFORMATION REQUIRED

# path to the directory of TEM input files used to produce the TEM outputs
inputdir="/data/input-catalog/caribou-poker/"
# path to the TEM raw output directory
rawoutdir="/data/workflows/poker_flats_test/output/"
#tar -zxvf "${rawoutdir}.tar.gz"
# path to the directory containing the python scripts associated to this bash (e.g. Layer_var_synth.py)
scriptdir="/work/scripts/caribou-poker-exp/soil_layer_synthesis/"
# path to the directory to store output synthesis files
outdir="/work/scripts/caribou-poker-exp/soil_layer_synthesis/"
# historical period starting and ending years
hist_start=1901
hist_end=2015
# projection period starting and ending years
proj_start=2016
proj_end=2100
# list of simulation scenarios of interest: pr, eq, sp, tr, sc for pre-run, equilibrium, spin-up, historical and scenario runs
#sclist=(tr sc)
sclist=(tr)
# name of the scenario run
scname=usprr
# name of the variable of interest
var=LWCLAYER
# for variables with soil layer dimension, specify the soil depths, in meter, at which you woould like the variable to be synthesized
depthlist=(0.05,0.10,0.20)



### GETTING STARTED...

cd $rawoutdir
mkdir $outdir



### DETERMINE OUTPUTFILE TIME RESOLUTION AND LIST OF DIMENSIONS

## 1- Time resolution

# list the time frequency of all output files of interest
freq=()
for sc in "${sclist[@]}"; do
  #1- determine frequency of outputs
  if [[ $(basename "${rawoutdir}${var}_"*"_${sc}.nc") == *"monthly"* ]];then
    fq="monthly"
  elif [[ $(basename "${rawoutdir}${var}_"*"_${sc}.nc") == *"yearly"* ]];then
    fq="yearly";
  fi
  freq=("${freq[@]}" "${fq[@]}")
done
# check that the time resolution is the same for all output files.
echo ${freq[@]}
mapfile -t tres < <(printf "%s\n" "${freq[@]}" | sort -u)
if (( ${#tres[@]} > 1 ));then
  echo "All output files do not have the same time frequency. Please homogenize the time resolution of the output files. [To do so, you can rather reproduce the simulations with homogenous time resolution, or use the ncwa operator (nco) to rather sum (fluxes) or take the december value (stocks) of monthly outputs to generate yearly outputs which are the coarsest resolution of TEM outputs]."
else  
  echo "The time resolution of the output files is: ${tres[@]}"
fi


## 2- Dimensions

# list the dimensions from all output files of interest and check they are all the same.
prevdimlist=()
for sc in "${sclist[@]}"; do
  echo $sc;
  ncdump -h "${rawoutdir}${var}_"*"_${sc}.nc" > a.txt
  IFS=' ' read -r -a dimlist <<< "`grep $var'(' a.txt | awk -F"[()]" '{print $2}' | sed 's/ //g' | sed 's/,/ /g'`"
  if (( ${#prevdimlist[@]} > 0 ));then
    diff=$(diff <(printf "%s\n" "${dimlist[@]}") <(printf "%s\n" "${prevdimlist[@]}"))
    if [[ ! -z "$diff" ]]; then
      echo "The list of dimensions is not the same in all output files of interest. Please homogenize. [To do so, you can rather reproduce the simulations with homogenous dimensions, or use the ncwa operator (nco) to sum or averag the variable values along the dimensions that are missing in some of the outputs files of interest]."
      dimlist=()
      break
    fi
  fi
  prevdimlist=("${dimlist[@]}")
done
echo "The list of dimensions in the output files is: ${dimlist[@]}"




### PRODUCE SOIL LAYER OUTPUTS OF COMPARABLE DEPTH


for sc in "${sclist[@]}"; do
  echo "scenario ${sc}"
  # make sure that layer dz and layer types are present
  if [[ ! -f "${rawoutdir}LAYERTYPE_monthly_${sc}.nc" ]];then
    echo "LAYERTYPE for ${sc} mode doesn't exist. Yet it is need to run this procedure. Break";
    break
  elif [[ ! -f "${rawoutdir}LAYERDZ_monthly_${sc}.nc" ]];then
    echo "LAYERDZ for ${sc} mode doesn't exist. Yet it is need to run this procedure. Break";
    break
  fi
  cp "${rawoutdir}LAYERTYPE_monthly_${sc}.nc" "${rawoutdir}SOILSTRUCTURE_monthly_${sc}.nc" 
  ncks -A -h "${rawoutdir}LAYERDZ_monthly_${sc}.nc" "${rawoutdir}SOILSTRUCTURE_monthly_${sc}.nc" 
  # export the necessary info to run the python code
  export scrun=$sc
  export inpath=$rawoutdir
  export outpath=$outdir
  export ncvar=$var
  export timeres=${tres[0]}
  export dmnl=${dimlist[@]}
  for i in "${dimlist[@]:1}"; do
    dmnl+=,$i
  done
  export dl=${depthlist[0]}
  for i in "${depthlist[@]:1}"; do
    dl+=,$i
  done
  #run the python script for linear interpolation
  python3 "${scriptdir}Layer_var_synth.py" 
done



