{
  "general": {
    "run_name": "Toolik area, 10x10 test cells, all years"
  },

  "IO": {
    "parameter_dir":      "parameters/",
    "hist_climate_file":  "DATA/Toolik_10x10_allyrs/historic-climate.nc",
    "proj_climate_file":  "DATA/Toolik_10x10_allyrs/projected-climate.nc",
    "veg_class_file":     "DATA/Toolik_10x10_allyrs/vegetation.nc",
    "fire_file":          "DATA/Toolik_10x10_allyrs/historic-fire.nc",
    "drainage_file":      "DATA/Toolik_10x10_allyrs/drainage.nc",
    "soil_texture_file":  "DATA/Toolik_10x10_allyrs/soil_texture.nc",
    "co2_file":           "DATA/Toolik_10x10_allyrs/co2.nc",
    "runmask_file":       "DATA/Toolik_10x10_allyrs/run-mask.nc",

    "output_dir":         "DATA/Toolik_10x10_allyrs/output/",
    "output_monthly":     1
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
    "restart_mode": "restart",   // other options??
    "inter_stage_pause": false

    // maybe less confusing if these settings are only available from cmd line?
    //"tr_yrs": 109,
    //"sc_yrs": 100

    // ??
    //"restartfile_dir": "DATA/Toolik_10x10_30yrs/" // location for restart-XX.nc file

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
