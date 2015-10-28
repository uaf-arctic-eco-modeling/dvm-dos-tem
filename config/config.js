{
  "general": {
    "run_name": "Toolik area, 10x10 test cells"
  },

  "IO": {
    "parameter_dir":      "parameters/",
    "hist_climate_file":  "DATA/Toolik_10x10_30yrs/historic-climate.nc",
    "proj_climate_file":  "DATA/Toolik_10x10_30yrs/projected-climate.nc",
    "veg_class_file":     "DATA/Toolik_10x10_30yrs/vegetation.nc",
    "fire_file":          "DATA/Toolik_10x10_30yrs/historic-fire.nc",
    "drainage_file":      "DATA/Toolik_10x10_30yrs/drainage.nc",
    "soil_texture_file":  "DATA/Toolik_10x10_30yrs/soil_texture.nc",
    "co2_file":           "DATA/Toolik_10x10_30yrs/co2.nc",
    "runmask_file":       "DATA/Toolik_10x10_30yrs/run-mask.nc",

    "output_dir":         "DATA/Toolik_10x10_30yrs/output/",

    "output_monthly":     1
  },

  "stage_settings": {
    "run_stage": "eq",           // eq, sp, tr, sc, or some combo there-of
    "restart_mode": "restart"   // other options??
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
