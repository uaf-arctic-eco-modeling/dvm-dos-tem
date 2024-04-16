#!/bin/bash

# Change directory to /work
cd /work || exit

# Workflow directories for different model runs
workflows=(
    '/data/workflows/BONA-black-spruce-fire-control'
    #'/data/workflows/BONA-black-spruce-fire-1930'
    #'/data/workflows/BONA-black-spruce-fire-1960'
    #'/data/workflows/BONA-black-spruce-fire-1990'
)

# Fire history files for different model runs
fire_hist_files=(
    'historic-explicit-fire.nc'
    #'historic-explicit-fire_1930.nc'
    #'historic-explicit-fire_1960.nc'
    #'historic-explicit-fire_1990.nc'
)

dsb_settings=(
	False
	#True
	#True
	#True
	)

setup_script='scripts/util/setup_working_directory.py'
outspec_script='scripts/util/outspec.py'

# Loop through different model runs
for (( i = 0; i < ${#workflows[@]}; i++ )); do
    
    cd /work || exit

    # Check if directory exists, if so, remove
    if [[ -d ${workflows[$i]} ]]; then
        rm -r "${workflows[$i]}"
    fi

    # Call setup working directory for model run, specifying corresponding fire history file
    python "$setup_script" --input-data-path /data/input-catalog/cpcrw_towers_downscaled/ "${workflows[$i]}" --fire_hist_file "${fire_hist_files[$i]}" --dsb_on ${dsb_settings[$i]}
	
    # Enable inputs for model run
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --empty
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on CMTNUM yearly
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on GPP monthly
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on RG monthly compartment
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on RH monthly layer
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on RM monthly compartment
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on NPP monthly
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on ALD yearly
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on SHLWC yearly monthly
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on DEEPC yearly
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on MINEC yearly
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on ORGN yearly
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on AVLN yearly
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on LTRFALC monthly
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on LWCLAYER monthly
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on TLAYER monthly
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on LAYERDEPTH monthly
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on LAYERDZ monthly
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on EET monthly
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on TRANSPIRATION monthly PFT
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on LAI monthly PFT
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on VEGC monthly PFT compartment
    python "$outspec_script" "${workflows[$i]}/config/output_spec.csv" --on BURNVEG2AIRC monthly

    # Change working directory to model run workflow directory
    cd ${workflows[$i]} || exit

    # Run model
    dvmdostem --force-cmt=15 --log-level='err' --eq-yrs=10 --sp-yrs=10 --tr-yrs=122 --sc-yrs=0

done
