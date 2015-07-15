{
  "general": {
    "run_name": "Toolik area, 10x10 test cells"
  },

  "IO": {
    "parameter_dir": "parameters/",
    "input":    "DATA/sample/Toolik_10x10/",
    "output":   "DATA/sample/Toolik_10x10/output"
  },

  "stage_settings": {
    "run_stage": "eq",           // eq, sp, tr, sc, or some cobmo there-of
    "restart_mode": "restart",   // other options??
    "restart_file": "DATA/sample/Toolik_10x10/" // location for restart-XX.nc file
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