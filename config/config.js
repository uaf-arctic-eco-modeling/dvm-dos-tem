{
  "general": {
    "run_name": "A sample dvmdostem run. Modify this text to suit your needs."
  },

  "IO": {
    "parameter_dir":      "parameters/",
    "hist_climate_file":  "demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/historic-climate.nc",
    "proj_climate_file":  "demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/projected-climate.nc",
    "veg_class_file":     "demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/vegetation.nc",
    "drainage_file":      "demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/drainage.nc",
    "soil_texture_file":  "demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/soil-texture.nc",
    "co2_file":           "demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/co2.nc",
    "proj_co2_file":      "demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/projected-co2.nc",
    "runmask_file":       "demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/run-mask.nc",
    "topo_file":          "demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/topo.nc",
    "fri_fire_file":      "demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/fri-fire.nc",
    "hist_exp_fire_file": "demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/historic-explicit-fire.nc",
    "proj_exp_fire_file": "demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10/projected-explicit-fire.nc",
    "output_dir":         "output/",
    "output_spec_file":   "config/output_spec.csv",
    "output_monthly":     1, //JSON specific
    "output_nc_eq":       0,
    "output_nc_sp":       0,
    "output_nc_tr":       1,
    "output_nc_sc":       1, 
    "output_interval":    1 
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
    "inter_stage_pause": false,
    //Per-stage module settings
    "pr": {
      "env": true,
      "bgc": false,
      "nfeed": false,
      "avlnflg": false,
      "baseline": false,
      "dsb": false,
      "dsl": false,
      "dyn_lai": false
    },
    "eq": {
      "env": true,
      "bgc": true,
      "nfeed": true,
      "avlnflg": true,
      "baseline": true,
      "dsb": false,
      "dsl": true,
      "dyn_lai": true
    },
    "sp": {
      "env": true,
      "bgc": true,
      "nfeed": true,
      "avlnflg": true,
      "baseline": true,
      "dsb": false,
      "dsl": true,
      "dyn_lai": true 
    },
    "tr": {
      "env": true,
      "bgc": true,
      "nfeed": true,
      "avlnflg": true,
      "baseline": true,
      "dsb": false,
      "dsl": true,
      "dyn_lai": true
    },
    "sc": {
      "env": true,
      "bgc": true,
      "nfeed": true,
      "avlnflg": true,
      "baseline": true,
      "dsb": false,
      "dsl": true,
      "dyn_lai": true
    }

    // maybe less confusing if these settings are only available from cmd line?
    //"tr_yrs": 109,
    //"sc_yrs": 100

    // ??
    //"restartfile_dir": "DATA/Toolik_10x10_30yrs/" // location for restart-XX.nc file

  },

  "model_settings": {
    "dynamic_lai": 1,                   // from model (1) or from input (0)
    "baseline_start": 1901,  //start year for baseline EQ climate
    "baseline_end": 1931     //end year for baseline EQ climate
//    //"dynamic_climate": 0,
//    //"varied_co2": 0,
//    //"fire_severity_as_input": 0,    // fire sev. as input or ??
//    //"output_starting_year": -9999
  }

//  "output_switches": {
//    "daily_output": 0,
//    "monthly_output": 0,
//    "yearly_output": 1,
//    "summarized_output": 0,
//    "soil_climate_output": 0
//  }
}
