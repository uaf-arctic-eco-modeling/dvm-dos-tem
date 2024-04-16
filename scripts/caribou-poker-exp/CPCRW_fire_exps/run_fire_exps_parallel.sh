#!/bin/bash

# Change directory to /work
cd /work || exit

# Workflow directories for different model runs
workflows=(
    #'/data/workflows/BONA-black-spruce-fire-control'
    '/data/workflows/BONA-black-spruce-fire-1930-nfix'
    #'/data/workflows/BONA-black-spruce-fire-1960'
    #'/data/workflows/BONA-black-spruce-fire-1990-rhmoist'
    #'/data/workflows/BONA-birch-fire-control-rhmoist'
    #'/data/workflows/BONA-birch-fire-1930-rhmoist'
    #'/data/workflows/BONA-birch-fire-1960-rhmoist'
    #'/data/workflows/BONA-birch-fire-1990-rhmoist'

)

# Fire history files for different model runs
fire_hist_files=(
    #'historic-explicit-fire.nc'
    'historic-explicit-fire_1930.nc'
    #'historic-explicit-fire_1960.nc'
    #'historic-explicit-fire_1990.nc'
    #'historic-explicit-fire.nc'
    #'historic-explicit-fire_1930.nc'
    #'historic-explicit-fire_1960.nc'
    #'historic-explicit-fire_1990.nc'
)
dsb=(
    #false
    true
    #true
    #true
    #false
    #true
    #true
    #true
)

dsl=(
    #true 
    true
    #true
    #true
    #true
    #true
    #true
    #true
)

cmt=(
    #15
    15
    #15
    #15
    #14
    #14
    #14
    #14
)


setup_script='scripts/util/setup_working_directory.py'
outspec_script='scripts/util/outspec.py'

# Function to execute model run for each workflow
run_model() {
    workflow=$1
    fire_hist_file=$2
    dsb_on=$3
    dsl_on=$4
    cmt=$5

    cd /work || exit
    
    # Check if directory exists, if so, remove
    if [[ -d $workflow ]]; then
        rm -r "$workflow"
    fi

    # Call setup working directory for model run, specifying corresponding fire history file
    python "$setup_script" --input-data-path /data/input-catalog/cpcrw_towers_downscaled/ "$workflow" --fire_hist_file "$fire_hist_file" --dsb_on "$dsb_on" --dsl_on "$dsl_on"

    # Enable inputs for model run
    python "$outspec_script" "${workflow}/config/output_spec.csv" --empty
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on CMTNUM yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on GPP monthly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on RG monthly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on RH monthly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on RM monthly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on NPP monthly
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
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on VEGC monthly PFT compartment
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on BURNVEG2AIRC monthly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on EET yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on PET yearly
    python "$outspec_script" "${workflow}/config/output_spec.csv" --on BURNSOIC yearly

    # Change working directory to model run workflow directory
    cd ${workflow} || exit

    # Run model
    dvmdostem --force-cmt=$cmt --log-level='debug' --eq-yrs=0 --sp-yrs=0 --pr=0 --tr-yrs=122 --sc-yrs=0 --restart-run --no-output-cleanup
}

export -f run_model

# Run each model in parallel
#parallel -j 3 run_model ::: "${workflows[@]}" ::: "${fire_hist_files[@]}"


# Run each model in a separate background subshell
for ((i = 0; i < ${#workflows[@]}; i++)); do
    run_model "${workflows[$i]}" "${fire_hist_files[$i]}" "${dsb[$i]}" "${dsl[$i]}" ${cmt[$i]} &
done

# Wait for all background subshells to finish
wait

