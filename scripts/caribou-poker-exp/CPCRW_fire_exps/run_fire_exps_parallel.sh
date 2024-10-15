#!/bin/bash

# Change directory to /work
cd /work || exit

# Workflow directories for different model runs
workflows=(
    '/data/workflows/BONA-black-spruce-fire-control'
    '/data/workflows/BONA-black-spruce-fire-1930'
    '/data/workflows/BONA-black-spruce-fire-1960'
    '/data/workflows/BONA-black-spruce-fire-1990'
    '/data/workflows/BONA-black-spruce-fire-2030'
    '/data/workflows/BONA-birch-fire-control'
    '/data/workflows/BONA-birch-fire-1930'
    '/data/workflows/BONA-birch-fire-1960'
    '/data/workflows/BONA-birch-fire-1990'
    '/data/workflows/BONA-birch-fire-2030'

)

# Fire history files for different model runs
fire_hist_files=(
    'historic-explicit-nofire.nc'
    'historic-explicit-fire_1930.nc'
    'historic-explicit-fire_1960.nc'
    'historic-explicit-fire_1990.nc'
    'historic-explicit-nofire.nc'
    'historic-explicit-nofire.nc'
    'historic-explicit-fire_1930.nc'
    'historic-explicit-fire_1960.nc'
    'historic-explicit-fire_1990.nc'
    'historic-explicit-nofire.nc'
)
fire_future_files=(
    'projected_explicit_fire_CC_CCSM4_85_nofire.nc'
    'projected_explicit_fire_CC_CCSM4_85_nofire.nc'
    'projected_explicit_fire_CC_CCSM4_85_nofire.nc'
    'projected_explicit_fire_CC_CCSM4_85_nofire.nc'
    'projected_explicit_fire_CC_CCSM4_85.nc'
    'projected_explicit_fire_CC_CCSM4_85_nofire.nc'
    'projected_explicit_fire_CC_CCSM4_85_nofire.nc'
    'projected_explicit_fire_CC_CCSM4_85_nofire.nc'
    'projected_explicit_fire_CC_CCSM4_85_nofire.nc'
    'projected_explicit_fire_CC_CCSM4_85.nc'
)
dsb=(
    false
    true
    true
    true
    true
    false
    true
    true
    true
    true
)

dsl=(
    true 
    true
    true
    true
    true
    true
    true
    true
    true
    true
)

cmt=(
    15
    15
    15
    15
    15
    14
    14
    14
    14
    14
)


setup_script='scripts/util/setup_working_directory.py'
outspec_script='scripts/util/outspec.py'

# Function to execute model run for each workflow
run_model() {
    workflow=$1
    fire_hist_file=$2
    fire_future_file=$3
    dsb_on=$4
    dsl_on=$5
    cmt=$6

    cd /work || exit
    
    # Check if directory exists, if so, remove
    if [[ -d $workflow ]]; then
        rm -r "$workflow"
    fi

    # Call setup working directory for model run, specifying corresponding fire history file
    python "$setup_script" --input-data-path /data/input-catalog/cpcrw_towers_downscaled/ "$workflow" --fire_hist_file "$fire_hist_file" --fire_future_file "$fire_future_file" --dsb_on "$dsb_on" --dsl_on "$dsl_on"

    # Enable inputs for model run
    python "$outspec_script" "${workflow}/config/output_spec.csv" --empty
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on CMTNUM yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on GPP monthly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on RG monthly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on RH monthly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on RM monthly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on NPP monthly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on INNPP monthly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on ALD yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on DEEPDZ yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on SHLWDZ yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on WATERTAB yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on SHLWC yearly monthly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on DEEPC yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on MINEC yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on SOMA yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on SOMCR yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on SOMPR yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on SOMRAWC yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on ORGN yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on AVLN yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on LTRFALC monthly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on LWCLAYER yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on TLAYER yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on LAYERDEPTH yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on LAYERDZ yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on LAYERTYPE yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on EET monthly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on TRANSPIRATION monthly PFT
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on LAI monthly PFT
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on VEGC monthly PFT
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on BURNVEG2AIRC yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on EET yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on PET yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on BURNSOIC yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on DEADC yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on DWDC yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on YSD yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on GROWSTART yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on GROWEND yearly
    
    # Change working directory to model run workflow directory
    cd ${workflow} || exit

    # Run model
    #dvmdostem --force-cmt=$cmt --log-level='debug' --eq-yrs=0 --sp-yrs=0 --pr=0 --tr-yrs=122 --sc-yrs=0 --restart-run --no-output-cleanup
    dvmdostem --force-cmt=$cmt --log-level='fatal' --eq-yrs=300 --sp-yrs=300 --pr-yrs=100 --tr-yrs=122 --sc-yrs=78
    #dvmdostem --force-cmt=$cmt --log-level='fatal' --eq-yrs=1500 --sp-yrs=300 --pr-yrs=100 --tr-yrs=122 --sc-yrs=78

}

export -f run_model

# Run each model in parallel
#parallel -j 3 run_model ::: "${workflows[@]}" ::: "${fire_hist_files[@]}"


# Run each model in a separate background subshell
for ((i = 0; i < ${#workflows[@]}; i++)); do
    run_model "${workflows[$i]}" "${fire_hist_files[$i]}" "${fire_future_files[$i]}" "${dsb[$i]}" "${dsl[$i]}" ${cmt[$i]} &
done

# Wait for all background subshells to finish
wait

