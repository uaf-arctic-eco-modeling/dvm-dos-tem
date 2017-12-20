{
  "general": {
    "run_name": "A sample dvmdostem run. Modify this text to suit your needs."
  },

  "IO": {
    "parameter_dir":      "parameters/",
    "hist_climate_file":  "DATA/Toolik_10x10/historic-climate.nc",
    "proj_climate_file":  "DATA/Toolik_10x10/projected-climate.nc",
    "veg_class_file":     "DATA/Toolik_10x10/vegetation.nc",
    "drainage_file":      "DATA/Toolik_10x10/drainage.nc",
    "soil_texture_file":  "DATA/Toolik_10x10/soil-texture.nc",
    "co2_file":           "DATA/Toolik_10x10/co2.nc",
    "runmask_file":       "DATA/Toolik_10x10/run-mask.nc",
    "topo_file":          "DATA/Toolik_10x10/topo.nc",
    "fri_fire_file":      "DATA/Toolik_10x10/fri-fire.nc",
    "hist_exp_fire_file": "DATA/Toolik_10x10/historic-explicit-fire.nc",
    "proj_exp_fire_file": "DATA/Toolik_10x10/projected-explicit-fire.nc",
    "topo_file":          "DATA/Toolik_10x10/topo.nc",
    "output_dir":         "DATA/Toolik_10x10/output/",
    "output_spec_file":   "config/output_spec.csv",
    "output_monthly":     1, //JSON specific
    "output_nc_eq":       0,
    "output_nc_sp":       1,
    "output_nc_tr":       1,
    "output_nc_sc":       1 
  },

  // Define storage locations for json files generated and used
  // during calibration. The calibration-viewer.py program will read
  // this config file and these settings to determine where to look for
  // the json files. dvmdostem will create a directory tree that looks
  // like this:
  //  dvmdostem/
  //  └── calibration
  //      ├── daily
  //      │   ├── year_00000_daily_drivers.text
  //      │   └── year_00001_daily_drivers.text
  //      ├── monthly
  //      │   ├── 0000000.json
  //      │   ├── ...
  //      │   └── 0000011.json
  //      └── yearly
  //          └── 00000.json
  "calibration-IO": {
    "unique_pid_tag": "",
    "caldata_tree_loc": "/tmp"

    // NOTE: It is generally reccomended that the files be kept in the /tmp
    // directory so that the operating system will clean up the files, as the
    // output can be voluminous, especially when generating monthly or daily
    // files. The main reason to have this location configurable is so that
    // we will be able to run dvmdostem on Atlas under the control of PEST and
    // can use the compute node-specific /scratch directories and keep different
    // running instances of dvmdostem from overwriting eachothers json files.
  },
  "stage_settings": {
    "inter_stage_pause": false,

     // These defaults can be overridden on the command line
    "pr_yrs": 10,
    "eq_yrs": 100,
    "sp_yrs": 20,
    "tr_yrs": 109,
    "sc_yrs": 91,

    // If this is an empty string, then the model will use its default
    // restart files to transition between stages. This means that at the end
    // of each stage, the model will write out to disk all the data required
    // to save the state of the model. Then at the beginning of the next stage,
    // the model will look for this "restart file" and use it to initialize the
    // model stage before beginning to run the years in the stage. These files
    // get created automatically when the run begins and have names following
    // the pattern:
    //      <model-output-dir>/restart-<stage>.nc file file
    // For example, "restart-pr.nc" represents the state at the end of
    // the pre-run stage.
    //
    // If a non-empty string is set for any of the following variables, then
    // the model will look for a file located at the path specified in the
    // string and use this file to initialize the stage (instead of the default
    //     <model-output-dir>/restart-<stage>.nc file

    "eq_restart_from": "",
    "sp_restart_from": "",
    "tr_restart_from": "",
    "sc_restart_from": ""

  }

//  "model_settings": {
//    //"dynamic_climate": 0,
//    //"varied_co2": 0,
//    //"dynamic_lai": 1,               // from model (1) or from input (0)
//    //"fire_severity_as_input": 0,    // fire sev. as input or ??
//    //"output_starting_year": -9999
//  }

//  "output_switches": {
//    "daily_output": 0,
//    "monthly_output": 0,
//    "yearly_output": 1,
//    "summarized_output": 0,
//    "soil_climate_output": 0
//  }
}
