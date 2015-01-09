//
//  TEMUtilityFunctions.cpp
//  dvm-dos-tem
//
//  Created by Tobey Carman on 4/10/14.
//  Copyright (c) 2014 Spatial Ecology Lab. All rights reserved.
//

#include <string>
#include <stdexcept>
#include <fstream>
#include <cerrno>

#include <netcdfcpp.h>

#include <json/reader.h>
#include <json/value.h>

#include "TEMLogger.h"
#include "TEMUtilityFunctions.h"

extern src::severity_logger< severity_level > glg;

namespace temutil {

  /** Returns true for 'on' and false for 'off'.
   * Throws exception if s is not "on" or "off".
   * might want to inherit from std exception or do something else?
   */
  bool onoffstr2bool(const std::string &s) {
    if (s.compare("on") == 0) {
      return true;
    } else if (s.compare("off") == 0) {
      return false;
    } else {
      throw std::runtime_error("Invalid string! Must be 'on' or 'off'.");
    }
  }

  /** Read a file into a string. Return the string. 
  * Throws exceptions if there is an error reading the file. Poached from:
  * http://insanecoding.blogspot.com/2011/11/how-to-read-in-file-in-c.html
  */
  std::string file2string(const char *filename) {
    std::ifstream in(filename, std::ios::in | std::ios::binary);
    if (in) {
      std::string contents;
      in.seekg(0, std::ios::end);
      contents.resize(in.tellg());
      in.seekg(0, std::ios::beg);
      in.read(&contents[0], contents.size());
      in.close();
      return(contents);
    }
    throw(errno);
  }

  /** Reads a json foramtted "control file", returning a json data object.
  */
  Json::Value parse_control_file(const std::string &filepath) {

    BOOST_LOG_SEV(glg, debug) << "Read the control file ('" << filepath << "') into a string...";
    std::string datastring = file2string(filepath.c_str());

    BOOST_LOG_SEV(glg, debug) << "Creating Json Value and Reader objects...";
    Json::Value root;   // will contain the root value after parsing
    Json::Reader reader;

    BOOST_LOG_SEV(glg, debug) << "Trying to parse the json data string...";

    bool parsingSuccessful = reader.parse( datastring, root );

    BOOST_LOG_SEV(glg, debug) << "Parsing successful?: " << parsingSuccessful;

    if ( !parsingSuccessful ) {
        BOOST_LOG_SEV(glg, fatal) << "Failed to parse configuration file! "
                                  << reader.getFormatedErrorMessages();
        exit(-1);
    }

    return root;
  }

  /** Opens a netcdf file for reading, returns NcFile object.
  * 
  * NetCDF library error mode is set to silent (no printing to std::out), and
  * non-fatal. If the file open fails, it logs a message and exits the program
  * with a non-zero exit code.
  */
  NcFile open_ncfile(std::string filename) {
    
    BOOST_LOG_SEV(glg, info) << "Opening NetCDF file: " << filename;

    NcError err(NcError::silent_nonfatal);
    NcFile file(filename.c_str(), NcFile::ReadOnly);
    
    if( !file.is_valid() ) {
      BOOST_LOG_SEV(glg, fatal) << "Problem opening/reading " << filename;
      exit(-1);
    }

    return file;

  }

  /** Given an NcFile object and dimension name, reutrns a pointer to the NcDim.
  * 
  * If the dimension-read is not valid, then an error message is logged and 
  * the program exits with a non-zero status.
  */
  NcDim* get_ncdim(const NcFile& file, std::string dimname) {
  
    BOOST_LOG_SEV(glg, debug) << "Looking for dimension '" << dimname << "' in NetCDF file...";
    NcDim* dim = file.get_dim(dimname.c_str());
    
    BOOST_LOG_SEV(glg, debug) << "'" << dimname <<"' is valid?: " << dim->is_valid();
    if ( !dim->is_valid() ) {
      BOOST_LOG_SEV(glg, fatal) << "Problem with '" << dimname << "' in NetCDF file.";
      exit(-1);
    }

    return dim;

  }

  /** Given an NcFile object and a variable name, returns a pointer to the NcVar.
  *
  * If getting the variable fails, then an error message is logged, and the
  * the program exits with a non-zero status.
  */
  NcVar* get_ncvar(const NcFile& file, std::string varname) {
    BOOST_LOG_SEV(glg, debug) << "Looking for variable '" << varname << "' in NetCDF file...";
    NcVar* var = file.get_var(varname.c_str());
    if (var == NULL) {
      BOOST_LOG_SEV(glg, fatal) << "Problem with '" << varname << "' variable in NetCDF file!";
      exit(-1);
    }
    return var;
  }


  /** Look up a lat-lon pair in a NetCDF file given a rec_id.
  *
  * Note: rec_id - the order (from ZERO) in the .nc file,
  *       gridid - the grid id user-defined in the dataset
  */
  std::pair<float, float> get_location(std::string gridfilename, int rec_id) {

    float lat;
    float lon;

    NcFile grid_file = temutil::open_ncfile(gridfilename);

    NcVar* latV = temutil::get_ncvar(grid_file, "LAT");
    latV->set_cur(rec_id);
    latV->get(&lat, 1);

    NcVar* lonV = temutil::get_ncvar(grid_file, "LON");
    lonV->set_cur(rec_id);
    lonV->get(&lon, 1);

    return std::pair<float, float> (lat, lon);

  }
  
  /** Handles NetCDF errors by printing message and exiting. */
  void handle_error(int status) {
    if (status != NC_NOERR) {
      fprintf(stderr, "%s\n", nc_strerror(status));
      BOOST_LOG_SEV(glg, fatal) << nc_strerror(status);
      exit(-1);
    }
  }
  
  /** Two letter alias for handle_error() */
  void nc(int status) {
    handle_error(status);
  }
  
  
  /** rough draft for reading a timeseries for a single location from a 
  *   new-style climate file
  */
  std::vector<float> get_climate_var_timeseries(const std::string &filename,
                                                const std::string &var,
                                                int y, int x) {

    BOOST_LOG_SEV(glg, debug) << "Opening dataset: " << filename;
    BOOST_LOG_SEV(glg, debug) << "Getting variable: " << var;

    int ncid;
    temutil::nc( nc_open(filename.c_str(), NC_NOWRITE, &ncid) );

    int timeD, yD, xD;
    
    size_t timeD_len, yD_len, xD_len;

    temutil::nc( nc_inq_dimid(ncid, "Y", &yD) );
    temutil::nc( nc_inq_dimlen(ncid, yD, &yD_len) );

    temutil::nc( nc_inq_dimid(ncid, "X", &xD) );
    temutil::nc( nc_inq_dimlen(ncid, xD, &xD_len) );

    temutil::nc( nc_inq_dimid(ncid, "time", &timeD) );
    temutil::nc( nc_inq_dimlen(ncid, timeD, &timeD_len) );
    
    int climate_var;
    temutil::nc( nc_inq_varid(ncid, var.c_str(), &climate_var) );

    BOOST_LOG_SEV(glg, debug) << "Allocate a vector with enough space for the whole timeseries (" << timeD_len << " timesteps)";
    std::vector<float> climate_data(timeD_len);
    
    // specify start indices for each dimension (y, x)
    size_t start[3];
    start[0] = 0;     // from begining of time
    start[1] = y;     // specified location
    start[2] = x;     // specified location

    // specify counts for each dimension
    size_t count[3];
    count[0] = timeD_len;     // all time
    count[1] = 1;             // one location
    count[2] = 1;             // one location

    BOOST_LOG_SEV(glg, debug) << "Grab the data from the netCDF file...";
    temutil::nc( nc_get_vara_float(ncid, climate_var, start, count, &climate_data[0]) );

    return climate_data;
    
  }
  
  /** rough draft for reading a single location, veg classification
  */
  int get_veg_class(const std::string &filename, int y, int x) {

    BOOST_LOG_SEV(glg, debug) << "Opening dataset: " << filename;
    int ncid;
    temutil::nc( nc_open(filename.c_str(), NC_NOWRITE, &ncid ) );

    int xD, yD;
    
    //size_t yD_len, xD_len;

    temutil::nc( nc_inq_dimid(ncid, "Y", &yD) );
    //temutil::nc( nc_inq_dimlen(ncid, yD, &yD_len) );

    temutil::nc( nc_inq_dimid(ncid, "X", &xD) );
    //temutil::nc( nc_inq_dimlen(ncid, xD, &xD_len) );
    
    int veg_classificationV;
    temutil::nc( nc_inq_varid(ncid, "veg_class", &veg_classificationV) );

    size_t start[2];
    start[0] = y;
    start[1] = x;

    int veg_class_value;
    temutil::nc( nc_get_var1_int(ncid, veg_classificationV, start, &veg_class_value)  );

    return veg_class_value;
  }

  

}
