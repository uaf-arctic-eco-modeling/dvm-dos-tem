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
#include <sstream>
#include <limits>
#include <regex>

#include <json/reader.h>
#include <json/value.h>

#include "../include/physicalconst.h" // for PI
#include "../include/timeconst.h" // for mapping from first day of month -> day of year

#include "../include/TEMLogger.h"
#include "../include/TEMUtilityFunctions.h"

extern src::severity_logger< severity_level > glg;

namespace temutil {

  /** For safely comparing floating point numbers.
    Idea completely taken from here:
    https://randomascii.wordpress.com/2012/02/25/comparing-floating-point-numbers-2012-edition/
  */
  bool AlmostEqualRelative(double A, double B) {

    double maxRelDiff = 2 * std::numeric_limits<double>::epsilon();

    // Calculate the difference.
    double diff = std::abs(A - B);

    A = std::abs(A);
    B = std::abs(B);

    // Find the larger of A and B
    double largest = (B > A) ? B : A;

    if (diff <= largest * maxRelDiff) {
      return true;
    } else {
      return false;
    }
  }
  
  /** Sets a negative number to 0.0.
  Can be used with std::for_each to make sure the contents of a
  container does not contain positive numbers.
  */
  void force_negative2zero(float& i) {
    if (i < 0) {
      i = 0.0;
    } else {
      // do nothing...
    }
  }


  /** Maybe useful for preventing divide by zero errors?
      - probably not very effecient for production runs, but maybe helpful for 
        debugging
      - sign parameter lets you force the result to a given sign
  */
  double NON_ZERO(const double val, const int sign) {
    assert((sign == 1 || sign == -1) && "Invalid parameter for sign. Must be 1, or -1");

    if (val != 0) {
      return val; // nothing to do, value is already non-zero.
    }

    // otherwise, return some arbitrary very small number
    double vsm = 0.0000000000000001 * sign;
    BOOST_LOG_SEV(glg, debug) << "NON_ZERO: setting to a very small number: " << vsm;
    return vsm;

  }

  /** Determines if a string is composed only of whitespace characters. */
  bool all_whitespace(const std::string &s){

    const char *cstr = s.c_str();
    int ws_count = 0;
    int ii = 0;

    while(cstr[ii]){
      if(isspace(cstr[ii])){
        ws_count += 1;
      }
      ii++;
    }

    if(ws_count == s.length()){
      return true;
    }

    return false;
  }

  /** Return the day of year based on month and day, everything is zero based. */
  int day_of_year(int month, int day) {
    return DOYINDFST[month] + day;
  }

  /** Given a day of the year, return the month that the day lands in.
   *    - Does not handle leap years
   *    - assumes day of year and month are both zero based.
  */
  int doy2month(const int doy) {
    assert( (doy >= 0 && doy <= 364) && "Invalid day of year! DOY must be >= 0 and <= 364");

    int month;

    //Note that doy is an index starting at 0
    if (doy < 31) {
      month = 0;
    }
    if (doy >= 334) {
      month =  11;
    }

    for (int midx = 1; midx < 11; ++midx) {

      // from timeconst.h
      // DOYINDFST[12] = {0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334};
      if (doy >= DOYINDFST[midx] && doy < DOYINDFST[midx+1]) {
        month = midx;
        break; // found our month, no need to continue
      }
    }

    return month;

  }

  /** Given a day of the year, returns the day of the month it falls in.
   *    - Does not handle leap years
   *    - Assumes DOY and month are zero based
   */
  int doy2dom(const int doy){
    assert( (doy >= 0 && doy <= 364) && "Invalid day of year! DOY must be >= 0 and <= 364");

    int month = doy2month(doy);

    return doy-DOYINDFST[month]; 
  }

  /** Length of day as a function of latitude (degrees) and day of year.
  */
  float length_of_day(float lat, int doy) {
    // OLD COMMENTS - should update.
    // the following are the original algorithm, and
    //  modified as below by Yi (2013 Feb):
    //  double ampl;
    //  ampl = exp(7.42 +0.045 *gd.lat)/3600.;
    //  gd.alldaylengths[id] = ampl * (sin ((id -79) *0.01721)) +12.0;
    // make sure all arguments in sin, cos and tan are
    //  in unit of arc (not degree)
    //http://www.jgiesen.de/astro/solarday.htm
    //http://www.gandraxa.com/length_of_day.xml

    double m = 1 - tan(lat*PI/180.0) * tan(23.45 * cos(doy*PI/182.625) * PI/180.0);
    m = fmax(m, 0.0);
    m = fmin(m, 2.0);
    double b = acos(1-m)/PI;
    double daylength = b * 24;

    return daylength;
  }

  /** Takes an integer number and returns a string like "CMT01".
  * Inserts leading zeros if needed. Works if 0 <= cmtnumber <= 99.
  */
  std::string cmtnum2str(int cmtnumber) {

    // get string representation of number
    std::stringstream cmtnumber_ss;
    cmtnumber_ss << cmtnumber;

    // take care of leading zero...
    std::string prefix = "";
    if (cmtnumber < 10) {
      prefix =  "CMT0";
    } else {
      prefix = "CMT";
    }

    return prefix + cmtnumber_ss.str();
  }


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
    Json::Value root;
    Json::CharReaderBuilder rbuilder;
    // March 2020, updated to work with newer jsoncpp (~1.9.x) where
    // the Reader class has been deprecated in favor of CharReader.
    // Not sure the exact version where this will break, but we had previously
    // been using jsoncpp 1.8.3 and 1.8.1 successfully without CharReaderBuilder.
    std::string errs;
    std::stringstream ss;
    ss << datastring;

    BOOST_LOG_SEV(glg, debug) << "Trying to parse the json data string...";
    bool parsingSuccessful = Json::parseFromStream(rbuilder, ss, &root, &errs);

    BOOST_LOG_SEV(glg, debug) << "Parsing successful?: " << parsingSuccessful;
    if (!parsingSuccessful) {
      BOOST_LOG_SEV(glg, fatal) << "Error parsing json file! " << errs; 
      exit(-1);
    }
    return root;
  }

  /** rough draft for reading a run-mask (2D vector of ints)
  */
  std::vector< std::vector<int> > read_run_mask(const std::string &filename) {
    int ncid;
    
    BOOST_LOG_SEV(glg, debug) << "Opening dataset: " << filename;
    temutil::nc( nc_open(filename.c_str(), NC_NOWRITE, &ncid) );
    
    BOOST_LOG_SEV(glg, debug) << "Find out how much data there is...";
    int yD, xD;
    size_t yD_len, xD_len;

    temutil::nc( nc_inq_dimid(ncid, "Y", &yD) );
    temutil::nc( nc_inq_dimlen(ncid, yD, &yD_len) );

    temutil::nc( nc_inq_dimid(ncid, "X", &xD) );
    temutil::nc( nc_inq_dimlen(ncid, xD, &xD_len) );

    BOOST_LOG_SEV(glg, debug) << "Allocate a 2D run-mask vector (y,x). Size: (" << yD_len << ", " << xD_len << ")";
    std::vector< std::vector<int> > run_mask(yD_len, std::vector<int>(xD_len));
    
    BOOST_LOG_SEV(glg, debug) << "Read the run flag data from the file into the 2D vector...";
    int runV;
    temutil::nc( nc_inq_varid(ncid, "run", &runV) );

    BOOST_LOG_SEV(glg, debug) << "Grab one row at a time";
    BOOST_LOG_SEV(glg, debug) << "(need contiguous memory, and vector<vector> are not contiguous)";

    std::vector< std::vector<int> >::iterator row;
    for (row = run_mask.begin();  row != run_mask.end(); ++row) {

      int rowidx = row - run_mask.begin();

      // specify start indices for each dimension (y, x)
      size_t start[2];
      start[0] = rowidx;    // Y
      start[1] = 0;         // X

      // specify counts for each dimension
      size_t count[2];
      count[0] = 1;         // one row
      count[1] = xD_len;    // all data
      
      std::vector<int> rowdata(xD_len);

      temutil::nc( nc_get_vara_int(ncid, runV, start, count, &rowdata[0] ) );
    
      run_mask[rowidx] = rowdata;
      
    }
    
    temutil::nc( nc_close(ncid) );

    //pp_2dvec(run_mask);

    BOOST_LOG_SEV(glg, debug) << "Return the vector...";
    return run_mask;

  }

  /** Opens a netcdf file and collects a bunch of info into a string for printing.
  */
  std::string report_on_netcdf_file(const std::string& fname, const std::string& varname) {

    std::stringstream ss;

    BOOST_LOG_SEV(glg, debug) << "Opening dataset: " << fname;

    int ncid;

#ifdef WITHMPI
    temutil::nc( nc_open_par(fname.c_str(), NC_NOWRITE|NC_MPIIO, MPI_COMM_WORLD, MPI_INFO_NULL, &ncid) );
#else
    temutil::nc( nc_open(fname.c_str(), NC_NOWRITE, &ncid) );
#endif

    // lookup variable by name
    int vid;
    temutil::nc( nc_inq_varid(ncid, varname.c_str(), &vid) );

    // stuff to report
    nc_type v_type;                      /* variable type */
    int v_ndims;                         /* number of dims */
    int v_dimids[NC_MAX_VAR_DIMS];       /* dimension IDs */
    int v_natts;                         /* number of attributes */

    temutil::nc( nc_inq_var (ncid, vid, 0 /*NC_MAX_NAME*/, &v_type,
                             &v_ndims, v_dimids, &v_natts ) );

    temutil::nc( nc_close(ncid) );

    ss << "varname: " << varname.c_str()
       << " id: " << vid
       << " type: " << v_type      // crude - prints number
       << " ndims: " << v_ndims
       << " dimids: " << v_dimids  // crude - prints address
       << " natts: " << v_natts;

    return ss.str();

  }

  /** Opens a netcdf file, assumed to be setup for dvmdostem, and reports y,x
  * dimension lengths.
  */
  std::string report_yx_pixel_dims2str(const std::string& fname) {

    std::stringstream ss;

    BOOST_LOG_SEV(glg, debug) << "Opening dataset: " << fname;

    int ncid;

#ifdef WITHMPI
    temutil::nc( nc_open_par(fname.c_str(), NC_NOWRITE|NC_MPIIO, MPI_COMM_WORLD, MPI_INFO_NULL, &ncid) );
#else
    temutil::nc( nc_open(fname.c_str(), NC_NOWRITE, &ncid) );
#endif

    int xD, yD;
    size_t xD_len, yD_len;

    temutil::nc( nc_inq_dimid(ncid, "X", &xD) );
    temutil::nc( nc_inq_dimlen(ncid, xD, &xD_len) );

    temutil::nc( nc_inq_dimid(ncid, "Y", &yD) );
    temutil::nc( nc_inq_dimlen(ncid, yD, &yD_len) );

    temutil::nc( nc_close(ncid) );

    ss << "Y len: " << yD_len << " X len: " << xD_len << " (" << fname << ")";

    return ss.str();
  }


  /** Given an NetCDF file ID, returns the length of the "time" dimension
 *
 * TODO: What should the behaviour be with an error?
 */
  int get_nc_timedim_len(const int& ncid){
    int cv;
    size_t dimlen;
    temutil::nc( nc_inq_dimid(ncid, "time", &cv) );
    temutil::nc( nc_inq_dimlen(ncid, cv, &dimlen) );
    return dimlen;
  }

 
  /** Handles NetCDF errors by printing message and exiting. */
  void handle_error(int status) {
    if (status != NC_NOERR) {

      // Add more specific error handling here. It can be helpful for debugging
      // to raise specific exceptions for specific errors, and raising specific
      // exceptions can help clientls selectively deal with the errors.
      if (status == NC_ENOTINDEFINE) {
        BOOST_LOG_SEV(glg, info) << "NetCDF file is already in data mode! ";
        throw NetCDFDefineModeException();
      }

      // No specific error to raise, so just print the error message and 
      // throw a generic runtime error.
      fprintf(stderr, "%s\n", nc_strerror(status));
      BOOST_LOG_SEV(glg, warn) << nc_strerror(status);

      std::string msg = "Exception from netcdf: ";
      msg = msg + nc_strerror(status);

      throw std::runtime_error(msg);

      //exit(-1);
    }
  }
  
  /** Two letter alias for handle_error() */
  void nc(int status) {
    handle_error(status);
  }

  template <typename DTYPE>
  DTYPE get_scalar(const std::string &filename,
                   const std::string &var,
                   const int y, const int x) {

    BOOST_LOG_SEV(glg, debug) << "Opening dataset: " << filename;
    BOOST_LOG_SEV(glg, debug) << "Getting variable: " << var;

    int ncid;
    temutil::nc( nc_open(filename.c_str(), NC_NOWRITE, &ncid) );


    int scalar_var;
    temutil::nc( nc_inq_varid(ncid, var.c_str(), &scalar_var) );

    BOOST_LOG_SEV(glg, info) << "Getting value for pixel(y,x): ("<< y <<","<< x <<").";
    int yD, xD;
    size_t yD_len, xD_len;

    temutil::nc( nc_inq_dimid(ncid, "Y", &yD) );
    temutil::nc( nc_inq_dimlen(ncid, yD, &yD_len) );

    temutil::nc( nc_inq_dimid(ncid, "X", &xD) );
    temutil::nc( nc_inq_dimlen(ncid, xD, &xD_len) );

    // specify start indices for each dimension (y, x)
    size_t start[2];
    start[0] = y;     // specified location
    start[1] = x;     // specified location

    // specify counts for each dimension
    size_t count[2];
    count[0] = 1;             // one location
    count[1] = 1;             // one location

    // might need to add a call to nc_inq_var so we can find the type and call
    // the right nc_get_var_type(...) function..
    char vname[NC_MAX_NAME+1];
    nc_type the_type;
    int num_dims;
    int dim_ids[NC_MAX_VAR_DIMS];
    int num_atts;
    temutil::nc( nc_inq_var(ncid, scalar_var, vname, &the_type, &num_dims, dim_ids, &num_atts) );

    // from netcdf.h
    //  NC_NAT          0   
    //  NC_BYTE         1   
    //  NC_CHAR         2
    //  NC_SHORT        3
    //  NC_INT          4   
    //  NC_LONG         NC_INT  
    //  NC_FLOAT        5
    //  NC_DOUBLE       6
    //  NC_UBYTE        7
    //  NC_USHORT       8
    //  NC_UINT         9
    //  NC_INT64       10
    //  NC_UINT64      11
    //  NC_STRING      12

    DTYPE data2;

    if (the_type == NC_INT64 || the_type == NC_INT) {
      BOOST_LOG_SEV(glg, debug) << "--> NC_INT64 or NC_INT";
      int data3;
      temutil::nc( nc_get_vara_int(ncid, scalar_var, start, count, &data3) );
      data2 = (DTYPE)data3;
    } else if (the_type == NC_FLOAT) {
      BOOST_LOG_SEV(glg, debug) << "--> NC_FLOAT";
      float data3;
      temutil::nc( nc_get_vara_float(ncid, scalar_var, start, count, &data3) );
      data2 = (DTYPE)data3;
    } else if (the_type == NC_DOUBLE) {
      BOOST_LOG_SEV(glg, debug) << "--> NC_DOUBLE";
      double data3;
      temutil::nc( nc_get_vara_double(ncid, scalar_var, start, count, &data3) );
      data2 = (DTYPE)data3;
    } else {
      BOOST_LOG_SEV(glg, warn) << "Unknown datatype: '" << the_type << "'. Returning empty vector.";
    }

    return data2;
  }

  /** rough draft for reading a timeseries for a single location from a
  *   new-style input file
  */
  template <typename DTYPE>
  std::vector<DTYPE> get_timeseries(const std::string &filename,
                                    const std::string &var,
                                    const int y, const int x) {

    BOOST_LOG_SEV(glg, debug) << "Opening dataset: " << filename;
    BOOST_LOG_SEV(glg, debug) << "Getting variable: " << var;

    int ncid;
    temutil::nc( nc_open(filename.c_str(), NC_NOWRITE, &ncid) );

    int timeD;
    size_t timeD_len;

    temutil::nc( nc_inq_dimid(ncid, "time", &timeD) );
    temutil::nc( nc_inq_dimlen(ncid, timeD, &timeD_len) );

    int timeseries_var;
    temutil::nc( nc_inq_varid(ncid, var.c_str(), &timeseries_var) );

    BOOST_LOG_SEV(glg, info) << "Getting value for pixel(y,x): ("<< y <<","<< x <<").";
    int yD, xD;
    size_t yD_len, xD_len;

    temutil::nc( nc_inq_dimid(ncid, "Y", &yD) );
    temutil::nc( nc_inq_dimlen(ncid, yD, &yD_len) );

    temutil::nc( nc_inq_dimid(ncid, "X", &xD) );
    temutil::nc( nc_inq_dimlen(ncid, xD, &xD_len) );

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

    // might need to add a call to nc_inq_var so we can find the type and call
    // the right nc_get_var_type(...) function..
    char vname[NC_MAX_NAME+1];
    nc_type the_type;
    int num_dims;
    int dim_ids[NC_MAX_VAR_DIMS];
    int num_atts;
    temutil::nc( nc_inq_var(ncid, timeseries_var, vname, &the_type, &num_dims, dim_ids, &num_atts) );

    std::vector<DTYPE> data2;

    BOOST_LOG_SEV(glg, debug) << "Grab the data from the netCDF file...";
    if (the_type == NC_INT) {
      int dataI[timeD_len];
      temutil::nc( nc_get_vara_int(ncid, timeseries_var, start, count, &dataI[0]) );
      unsigned dataArraySize = sizeof(dataI) / sizeof(DTYPE);
      data2.insert(data2.end(), &dataI[0], &dataI[dataArraySize]);
    } else if (the_type == NC_INT64) {
      int64_t dataI64[timeD_len];
      temutil::nc( nc_get_vara(ncid, timeseries_var, start, count, &dataI64[0]) );
      unsigned dataArraySize = sizeof(dataI64) / sizeof(DTYPE);
      data2.insert(data2.end(), &dataI64[0], &dataI64[dataArraySize]);
    } else if (the_type == NC_FLOAT) {
      float dataF[timeD_len];
      temutil::nc( nc_get_vara_float(ncid, timeseries_var, start, count, &dataF[0]) );
      unsigned dataArraySize = sizeof(dataF) / sizeof(DTYPE);
      data2.insert(data2.end(), &dataF[0], &dataF[dataArraySize]);

    } else {
      BOOST_LOG_SEV(glg, warn) << "Unknown datatype: '" << the_type << "'. Returning empty vector.";
    }
    return data2;
  }

  /** rough draft for reading a timeseries of co2 data from a new-style co2 file.
  */
  std::vector<float> get_timeseries(const std::string &filename,
                                    const std::string &var) {

    BOOST_LOG_SEV(glg, debug) << "Opening dataset: " << filename;
    BOOST_LOG_SEV(glg, debug) << "Getting variable: " << var;

    int ncid;
    temutil::nc( nc_open(filename.c_str(), NC_NOWRITE, &ncid) );

    int timeseries_var;
    temutil::nc( nc_inq_varid(ncid, var.c_str(), &timeseries_var) );

    int yearD;
    size_t yearD_len;

    temutil::nc( nc_inq_dimid(ncid, "year", &yearD) );
    temutil::nc( nc_inq_dimlen(ncid, yearD, &yearD_len) );

    BOOST_LOG_SEV(glg, debug) << "Allocate a vector with enough space for the whole timeseries (" << yearD_len << " timesteps)";
    std::vector<float> data(yearD_len);

    size_t start[1];
    start[0] = 0;         // from beginning of time

    size_t count[1];
    count[0] = yearD_len; // all time

    BOOST_LOG_SEV(glg, debug) << "Grab the data from the netCDF file...";
    temutil::nc( nc_get_vara_float(ncid, timeseries_var, start, count, &data[0]) );

    return data;
  }

  /** Return the calendar start year of a timeseries netcdf file. 
  * Usually this will be a climate file, but it should function with
  * any file that has a time variable with a units attribute
  * based on time since a specific year. 
  */
  int get_timeseries_start_year(const std::string& fname){

    BOOST_LOG_SEV(glg, debug) << "Opening dataset: " << fname;

    int ncid;
    temutil::nc( nc_open(fname.c_str(), NC_NOWRITE, &ncid) );

    int timeV;
    temutil::nc( nc_inq_varid(ncid, "time", &timeV) );

    size_t timeUnitsLen;
    temutil::nc( nc_inq_attlen(ncid, timeV, "units", &timeUnitsLen) );

    char timeAttUnits[timeUnitsLen];
    temutil::nc( nc_get_att_text(ncid, timeV, "units", timeAttUnits) );
    std::string timeAttUnits_s(timeAttUnits);

    temutil::nc( nc_close(ncid) );

    //Pattern match the year value out of timeAttUnits
    //Example attribute units string: "days since 2016-1-1 0:0:0"
    std::regex year_exp("[0-9][0-9][0-9][0-9]");

    std::smatch sm;
    std::regex_search(timeAttUnits_s, sm, year_exp);

    //Convert from string to int
    std::stringstream ss;
    int start_year;
    ss << sm[0];
    ss >> start_year;

    return start_year;
  }

  /** Return the calendar end year of a timeseries netcdf file.
  * Assumes that input files have complete years
  * Assumes that time units are "days since..."
  */
  int get_timeseries_end_year(const std::string& fname){

    int start_year = get_timeseries_start_year(fname);

    BOOST_LOG_SEV(glg, debug) << "Opening dataset: " << fname;

    int ncid;
    temutil::nc( nc_open(fname.c_str(), NC_NOWRITE, &ncid) );

    //Information about the time *dimension*
    int timeD;
    size_t timeD_len;
    temutil::nc( nc_inq_dimid(ncid, "time", &timeD) );
    temutil::nc( nc_inq_dimlen(ncid, timeD, &timeD_len) );

    //Information about the time *variable*
    int timeV;
    temutil::nc( nc_inq_varid(ncid, "time", &timeV) );

    size_t start[3];
    start[0] = timeD_len-1; //Last entry only
    start[1] = 0;
    start[2] = 0;

    size_t count[3];
    count[0] = 1;
    count[1] = 1;
    count[2] = 1;

    int time_value;
    temutil::nc( nc_get_vara_int(ncid, timeV, start, count, &time_value) );

    //Round up, because the time value will be for the beginning
    // of the last time step and so will not divide evenly by 365.
    //Casting one of the values to a double to force use of the
    // proper operator/
    int year_count = ceil(double(time_value) / DINY);

    int end_year = start_year + year_count;
    return end_year;
  }

  /** rough draft - look up lon/lat in nc file from y,x coordinates. 
      Assumes that the file has some coordinate dimensions...
  */
  std::pair<float, float> get_latlon(const std::string& filename, int y, int x) {

    //Variables needed outside the openmp block
    float lat_value;
    float lon_value;

    #pragma omp critical(load_input)
    {
      BOOST_LOG_SEV(glg, debug) << "Opening dataset: " << filename;
      int ncid;
      temutil::nc( nc_open(filename.c_str(), NC_NOWRITE, &ncid ) );

      int yD, xD;
      temutil::nc( nc_inq_dimid(ncid, "Y", &yD) );
      temutil::nc( nc_inq_dimid(ncid, "X", &xD) );

      int latV;
      int lonV;
      temutil::nc( nc_inq_varid(ncid, "lat", &latV) );
      temutil::nc( nc_inq_varid(ncid, "lon", &lonV) );

      size_t start[2];
      start[0] = y;
      start[1] = x;

      temutil::nc( nc_get_var1_float(ncid, latV, start, &lat_value));
      temutil::nc( nc_get_var1_float(ncid, lonV, start, &lon_value));

      temutil::nc( nc_close(ncid) );
    }//End critical(get_latlon)

    return std::pair<float, float>(lat_value, lon_value);
  }

  /** rough draft for reading a fri for a single location */
  int get_fri(const std::string &filename, int y, int x) {
    BOOST_LOG_SEV(glg, debug) << "Opening dataset: " << filename;
    int ncid;
    temutil::nc( nc_open(filename.c_str(), NC_NOWRITE, &ncid ) );

    int yD, xD;
    temutil::nc( nc_inq_dimid(ncid, "Y", &yD) );
    temutil::nc( nc_inq_dimid(ncid, "X", &xD) );

    int friV;
    temutil::nc( nc_inq_varid(ncid, "fri", &friV));

    size_t start[2];
    start[0] = y;
    start[1] = x;

    int fri_value;
    temutil::nc( nc_get_var1_int(ncid, friV, start, &fri_value)  );

    return fri_value;

  }

  /** rough draft for reading a single location's, list of 'fire years' 
    (explicit replacement for FRI) */
  std::vector<int> get_fire_years(const std::string &filename, int y, int x) {
  // FIX: implement this!
/*
    BOOST_LOG_SEV(glg, debug) << "Opening dataset: " << filename;
    int ncid;
    temutil::nc( nc_open(filename.c_str(), NC_NOWRITE, &ncid ) );

    int yD, xD;
    temutil::nc( nc_inq_dimid(ncid, "Y", &yD) );
    temutil::nc( nc_inq_dimid(ncid, "X", &xD) );
  
  
    int fyV;
    temutil::nc( nc_inq_varid, "fire_years", fyV);

       int nc_get_vara       (int ncid, int varid, const size_t start[],
                            const size_t count[], void *ip);
    size_t start[2];
    start[0] = y;
    start[1] = x;
    nc_get_vara(ncid, fyV, start, &)
    
    nc_vlen_t fyrs[?];
    nc_vlen_t fszs[?];

    
//ncid
//The ncid of the file that contains the VLEN type.
//xtype
//The type of the VLEN to inquire about. 
//name
//A pointer for storage for the types name. The name will be NC_MAX_NAME characters or less. 
//datum_sizep
//A pointer to a size_t, this will get the size of one element of this vlen. 
//base_nc_typep
//A pointer to an nc_type, this will get the type of the VLEN base type. (In other words, what type is this a VLEN of?)

    temutil::nc( nc_inq_vlen(ncid, NC_INT, "fire_years", ??,??))
  
  
    if (nc_inq_vlen(ncid, typeid, name_in, &size_in, &base_nc_type_in)) ERR;
    
    std::vector<int> fy = ??
*/
    std::vector<int> JUNK(10,-34567);
    BOOST_LOG_SEV(glg, warn) << "THIS IS JUNK DATA! NOT IMPLEMENTED YET!!";
    return JUNK;
  }

  /** rough draft for reading a single location's list of 'fire sizes'. 
      This should parallel fire_years. In otherwords for every year mentioned
      in fire-years, there must be a corresponding fire size?
      Does this imply that the fire_years must be sorted?
  */
  std::vector<int> get_fire_sizes(const std::string &filename, int y, int x){
    // FIX: implement this!
    std::vector<int> JUNK(10,-2432);
    BOOST_LOG_SEV(glg, warn) << "THIS IS JUNK DATA! NOT IMPLEMENTED YET!!";
    return JUNK;
  }

  /** rough draft for reading a single location, veg classification
  */
  int get_veg_class(const std::string &filename2, int y2, int x2) {

    //Variable needed outside the omp block
    int veg_class_value;

    #pragma omp critical(load_input)
    {
      BOOST_LOG_SEV(glg, debug) << "Opening dataset: " << filename2;
      int ncid2;
      temutil::nc( nc_open(filename2.c_str(), NC_NOWRITE, &ncid2 ) );

      int xD2, yD2;

      //size_t yD_len, xD_len;

      temutil::nc( nc_inq_dimid(ncid2, "Y", &yD2) );
      //temutil::nc( nc_inq_dimlen(ncid, yD, &yD_len) );

      temutil::nc( nc_inq_dimid(ncid2, "X", &xD2) );
      //temutil::nc( nc_inq_dimlen(ncid, xD, &xD_len) );

      int veg_classificationV;
      temutil::nc( nc_inq_varid(ncid2, "veg_class", &veg_classificationV) );

      size_t start[2];
      start[0] = y2;
      start[1] = x2;

      temutil::nc( nc_get_var1_int(ncid2, veg_classificationV, start, &veg_class_value)  );

      temutil::nc( nc_close(ncid2) );
    }//End critical(get_veg_class)

    return veg_class_value;
  }

  /** Looks up a pixel's drainage class from a netcdf file */
  int get_drainage_class(const std::string& filename, int y, int x) {

    BOOST_LOG_SEV(glg, debug) << "Opening dataset: " << filename;

    //This variable is needed outside the omp block 
    int drainage_class_value;

    #pragma omp critical(load_input)
    {
      int ncid;
      temutil::nc( nc_open(filename.c_str(), NC_NOWRITE, &ncid ) );

      int xD, yD;

      temutil::nc( nc_inq_dimid(ncid, "Y", &yD) );
      temutil::nc( nc_inq_dimid(ncid, "X", &xD) );

      int drainage_classV;
      temutil::nc( nc_inq_varid(ncid, "drainage_class", &drainage_classV) );

      size_t start[2];
      start[0] = y;
      start[1] = x;

      temutil::nc( nc_get_var1_int(ncid, drainage_classV, start, &drainage_class_value)  );

      temutil::nc( nc_close(ncid) );
    }//End critical(get_drainage)

    return drainage_class_value;
  }

  /* Copy the attributes for variable `ivar` in group `igrp` to variable
   * `ovar` in group `ogrp`.  Global (group) attributes are specified by
   * using the varid NC_GLOBAL 
   * Adapted from the example programs "nccopy3.c" and "nccopy4.c" found here:
   * https://www.unidata.ucar.edu/software/netcdf/examples/programs/
   */
  void copy_atts(int igrp, int ivar, int ogrp, int ovar) {
      int natts;
      int iatt;

      temutil::nc( nc_inq_varnatts(igrp, ivar, &natts) );

      for(iatt = 0; iatt < natts; iatt++) {
        char name[NC_MAX_NAME];
        temutil::nc( nc_inq_attname(igrp, ivar, iatt, name) );
        temutil::nc( nc_copy_att(igrp, ivar, name, ogrp, ovar) );
      }
  }

  /** Copy the schema (no data) for a single variable in group 'srcgrp' to
   * group 'dstgrp'.
   *
   * Will put the destination file in and out of define mode as necessary.
   *
   * Adapted from the example programs "nccopy3.c" and "nccopy4.c" found here:
   * https://www.unidata.ucar.edu/software/netcdf/examples/programs/
  */
  void copy_var(int srcgrp, int varid, int dstgrp) {

    int ndims;
    int srcdimids[NC_MAX_DIMS]; /* ids of dims for input variable */
    int dstdimids[NC_MAX_DIMS]; /* ids of dims for output variable */
    char name[NC_MAX_NAME];
    nc_type src_typeid;
    nc_type dst_typeid;
    int natts;
    int dst_varid;

    temutil::nc( nc_inq_varndims(srcgrp, varid, &ndims) );
    temutil::nc( nc_inq_var(srcgrp, varid, name, &src_typeid, &ndims, srcdimids, &natts) );

    dst_typeid = src_typeid;

    /* get the corresponding dimids in the output file */
    for(int i = 0; i < ndims; i++) {
      char dimname[NC_MAX_NAME];
      temutil::nc( nc_inq_dimname(srcgrp, srcdimids[i], dimname) );
      temutil::nc( nc_inq_dimid(dstgrp, dimname, &dstdimids[i]) );
    }

    int ofgmvid = -1;
    ofgmvid = temutil::get_gridmapping_vid(dstgrp);
    if (ofgmvid >= 0) {
      BOOST_LOG_SEV(glg, warn) << "WARNING!! It appears that the output file ("
                               << dstgrp << ") already has a grid_mapping"
                               << " variable! Doing nothing...";
    } else {

      // Put in define mode...
      if (nc_redef(dstgrp) == NC_EINDEFINE) {
        // Already in define mode...
        /* define the output variable */
        temutil::nc( nc_def_var(dstgrp, name, dst_typeid, ndims, dstdimids, &dst_varid) );

        /* attach the variable attributes to the output variable */
        copy_atts(srcgrp, varid, dstgrp, dst_varid);

      } else {

        // enter define mode...
        temutil::nc( nc_redef(dstgrp) );

        /* define the output variable */
        temutil::nc( nc_def_var(dstgrp, name, dst_typeid, ndims, dstdimids, &dst_varid) );

        /* attach the variable attributes to the output variable */
        copy_atts(srcgrp, varid, dstgrp, dst_varid);

        // leave define mode...
        temutil::nc( nc_enddef(dstgrp) );

      }
    }
  }

  /** Given a handle to an (already open) netcdf file, return the variable id 
  * for the grid mapping variable, or a negative number if no such variable
  * exists.
  */
  int get_gridmapping_vid(int ncid) {

    int gmvid;

    gmvid = -1;

    // // General inquiry: number of variables, dims, global attrs, and which dim
    // // is unlimited.
    int n_vars;
    int n_dims;
    int n_gatts;
    int ulim_dimid;
    temutil::nc( nc_inq(ncid, &n_dims, &n_vars, &n_gatts, &ulim_dimid));


    // Get ids (handles) to all the variables
    int varids[n_vars];
    temutil::nc( nc_inq_varids(ncid, &n_vars, varids) );

    // Look at each variable  
    for (int i = 0; i < n_vars; i++) {

      // Get all the info about the variable
      int vid;
      vid = varids[i];
      char vname[NC_MAX_NAME];
      nc_type vtype;
      int vndims;
      int vdimids[NC_MAX_VAR_DIMS];
      int vnatts;
      temutil::nc( nc_inq_var(ncid, vid, vname, &vtype, &vndims, vdimids, &vnatts) );

      //std::cout << "    vid: " << vid << " vname: " << vname << "\n";

      // Loop over all the attributes for the variable
      for (int a=0; a<vnatts; a++) {
        char attname[NC_MAX_NAME];
        temutil::nc( nc_inq_attname(ncid, vid, a, attname) );
        if (0 == std::string(attname).compare("grid_mapping_name")) {
          gmvid = vid;
          //std::cout << "    vtype: " << vtype << std::endl;
        }
      }
    }

    if (gmvid < 0) {
      BOOST_LOG_SEV(glg, warn) << "WARNING! No Grid Mapping found in file with"
                               << " ncid: " << ncid;
    }

    return gmvid;
  }



  /** Parses a string, looking for a community code.
   Reads the string, finds the first occurrence of the characters "CMT", and
   returns a string consisting of CMT and the following two characters.

   Returns something like "CMT01".
  */
  std::string read_cmt_code(std::string s) {
    int pos = s.find("CMT");
    return s.substr(pos, 5);
  }

  /** Parses a string, looking for a community code, returns an integer.
  */
  int cmtcode2num(std::string s) {
    int pos = s.find("CMT");
    
    return std::atoi( s.substr(pos+3, 2).c_str() );
  }

  /** Reads a file, returning a contiguous section of lines surrounded by "CMT".
  * Each line from the file is an element in the vector. 
  */  
  std::vector<std::string> get_cmt_data_block(std::string filename, int cmtnum) {

    BOOST_LOG_SEV(glg, info) << "Opening file: " << filename;
    std::ifstream par_file(filename.c_str(), std::ifstream::in);

    if ( !par_file.is_open() ) {
      BOOST_LOG_SEV(glg, fatal) << "Problem opening " << filename << "!";
      exit(-1);
    }

    std::string cmtstr = cmtnum2str(cmtnum);

    // create a place to store lines making up the community data "block"
    std::vector<std::string> cmt_block_vector; 
    BOOST_LOG_SEV(glg, info) << "Searching file for community: " << cmtstr;
    for (std::string line; std::getline(par_file, line); ) {
      int pos = line.find(cmtstr);
      if ( pos != std::string::npos ) {

        // add the 'header line' to the data block
        cmt_block_vector.push_back(line);			

      for (std::string block_line; std::getline(par_file, block_line); ) {

        int block_line_pos = block_line.find("CMT");
        if ( block_line_pos != std::string::npos ) {
          //std::cout << "Whoops - line contains 'CMT'. Must be first line of next community data block; breaking loop.\n";
          break;
        } else {
          //std::cout << "Add line to cmt_block_vector: " << block_line << std::endl;
          cmt_block_vector.push_back(block_line);
        }
      }

      }
    }
    return cmt_block_vector;
  }

  /** Takes a cmt data "block" and strips any comments. */
  std::list<std::string> strip_comments(std::vector<std::string> idb) {
    
    std::list<std::string> l;

    for (std::vector<std::string>::iterator it = idb.begin(); it != idb.end(); ++it ) {

      std::string line = *it;

      // // strip comment and everthing after
      // size_t pos = line.find("//");
      // line = line.substr(0, pos);

      // Split into data and comment (everything after '//')
      size_t pos = line.find("//");
      std::string data = line.substr(0, pos);
      std::string comment = "";
      if (pos != std::string::npos) {
        comment = line.substr(pos+2, std::string::npos);
      }
      //std::cout << "Data: " << data << " Comment: " << comment << std::endl;

      if (data.size() == 0) {
        // pass
      } else {
        l.push_back(line);
      }

    }

    return l;
  }


  /** Given a file name, a community number and a number for expected lines of
   * data, returns a list of strings with just that data, after stripping 
   * comments.
   */
  std::list<std::string> parse_parameter_file(
      const std::string& fname, int cmtnumber, int linesofdata) {
    
    BOOST_LOG_SEV(glg, info) << "Parsing '"<< fname << "', "
                             << "for community number: " << cmtnumber;

    // get a vector of strings for that cmt "block". includes comments.
    std::vector<std::string> v(get_cmt_data_block(fname, cmtnumber));
    
    // strip the comments and turn it into a list
    std::list<std::string> datalist(strip_comments(v));

    // handy for debugging...
    //std::list<std::string>::iterator it = datalist.begin();
    //for (it; it != datalist.end(); ++it) {
    //  std::cout << "list item: " << *it << std::endl;
    //}

    // check the size
    if (datalist.size() != linesofdata) {
      BOOST_LOG_SEV(glg, warn) << "Expected " << linesofdata << ". "
                              << "Found " << datalist.size() << ". "
                              << "(" << fname << ", community " << cmtnumber << ")";
      exit(-1);
    }
    
    return datalist;
  }


  // Explicit instatiation of different template types...??
  // Not sure if this is necessary ??
  template void pfll2data(std::list<std::string> &l, double &data);
  template void pfll2data(std::list<std::string> &l, float &data);
  
  template void pfll2data_pft(std::list<std::string> &l, double *data);
  template void pfll2data_pft(std::list<std::string> &l, float *data);

  // inorder to keep the template function definition out of the header
  // we have to explicitly instantiate it here...

  template int get_scalar(const std::string &filename,
      const std::string &var, const int y, const int x);
  template float get_scalar(const std::string &filename,
      const std::string &var, const int y, const int x);
  template double get_scalar(const std::string &filename,
      const std::string &var, const int y, const int x);

  template std::vector<int> get_timeseries<int>(const std::string &filename,
      const std::string &var, const int y, const int x);
  template std::vector<int64_t> get_timeseries<int64_t>(const std::string &filename,
      const std::string &var, const int y, const int x);
  template std::vector<float> get_timeseries<float>(const std::string &filename,
      const std::string &var, const int y, const int x);

}
