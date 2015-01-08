//
//  TEMUtilityFunctions.h
//  dvm-dos-tem
//
//  Created by Tobey Carman on 4/10/14.
//  Copyright (c) 2014 Spatial Ecology Lab. All rights reserved.
//

#ifndef TEMUtilityFunctions_H
#define TEMUtilityFunctions_H

#include <string>
#include <netcdfcpp.h>
#include <json/value.h>

namespace temutil {

  bool onoffstr2bool(const std::string &s);

  std::string file2string(const char *filename);

  Json::Value parse_control_file(const std::string &filepath);
  
  NcFile open_ncfile(std::string filename);

  NcDim* get_ncdim(const NcFile& file, std::string dimname);

  NcVar* get_ncvar(const NcFile& file, std::string varname);


  std::pair<float, float> get_location(std::string gridfilename, int grid_id);

  void handle_error(int status);
  
  void nc(int status);
  
  // draft - reading one location, all timesteps climate variable
  std::vector<float> get_climate_var_timeseries(const std::string &filename,
                                              const std::string &var,
                                              int y, int x);

}

#endif /* TEMUtilityFunctions_H */
