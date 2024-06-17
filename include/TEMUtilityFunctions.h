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
#include <iomanip>
#include <iostream>
#include <sstream>
#include <list>
#include <netcdf.h>
#include <json/value.h>

#include <boost/lexical_cast.hpp>

#include "cohortconst.h" // needed for NUM_PFT
#include "TEMLogger.h"

#ifdef WITHMPI
#include <mpi.h>
#include <netcdf_par.h>
#else
#include <netcdf.h>
#endif

extern src::severity_logger< severity_level > glg;

namespace temutil {

  /** A 'predicate' function that can be used with std::remove_if(..)

   Intended to be used with STL containers, so requirements on T are
   that T must have a .empty() method!
  */
  template <typename T>
  bool emptyContainer(T t) {
    return t.empty();
  }

  template <typename T>
  T point_on_line(T m, T x, T b) {
    return (m*x)+b;
  }

  template <typename T>
  std::pair<T, T> line(std::pair<T,T> point1,
      std::pair<T, T> point2) {

    std::pair<T, T> mb;
    T m;
    T b;
    m = (point2.second - point1.second) / (point2.first - point1.first);
    b = point2.second - (m * point2.first);
    mb.first = m;
    mb.second = b;
    return mb; 
  }

  template <typename T>
  std::vector<T> resample(
      std::pair<T, T> p1,
      std::pair<T, T> p2,
      int begin, int end, int step) {

//    static_assert( std::is_same<float, T>::value ||
//                   std::is_same<double, Y>::value,
//                   "unsupported type for template argument T!" );

    std::pair<T, T> mb;
    mb = temutil::line(p1, p2);
    //std::cout << "(" << p1.first << ", "<< p1.second <<")"<< std::endl;
    //std::cout << "(" << p2.first << ", "<< p2.second <<")"<< std::endl;
    std::vector<T> y;
    for (int x_val = begin; x_val < end; x_val += step) {
      //std::cout << mb.first <<" "<< x_val <<" "<< mb.second << std::endl;
      y.push_back(temutil::point_on_line(mb.first, T(x_val), mb.second));
    }
    return y;
  }

  /** Quick 'n dirty pretty printer for vector of things
  */
  template <typename TYPE>
  void ppv(const std::vector<TYPE> &v){
    typename std::vector<TYPE>::const_iterator it;
    for (it = v.begin(); it != v.end(); ++it) {
      std::cout << *it << " ";
    }
    std::cout << "\n";
  }

  bool AlmostEqualRelative(double A, double B);

  void force_negative2zero(float& i);

  double NON_ZERO(const double val, const int sign);

  bool all_whitespace(const std::string &s);

  int doy2month(const int doy);
  int doy2dom(const int doy);

  int day_of_year(int month, int day);

  float length_of_day(float lat, int doy);

  std::string cmtnum2str(int cmtnumber);

  bool onoffstr2bool(const std::string &s);

  std::string file2string(const char *filename);

  Json::Value parse_control_file(const std::string &filepath);

  std::vector< std::vector<int> > read_run_mask(const std::string &filename);

  std::string report_on_netcdf_file(const std::string& fname, const std::string& varname);

  std::string report_yx_pixel_dims2str(const std::string& fname);

  int get_nc_timedim_len(const int& ncid);

  void handle_error(int status);
  
  void nc(int status);
  
  /** rough draft for reading a scalar variable for a single location. */
  template <typename DTYPE>
  DTYPE get_scalar(const std::string &filename,
                   const std::string &var,
                   const int y, const int x);

  /** rough draft for reading a timeseries for a single location from a
  *   new-style input file
  */
  template <typename DTYPE>
  std::vector<DTYPE> get_timeseries(const std::string &filename,
                                    const std::string &var,
                                    const int y, const int x);

  int get_timeseries_start_year(const std::string &filename);
  int get_timeseries_end_year(const std::string &filename);

  // draft - reads all timesteps co2 data
  std::vector<float> get_timeseries(const std::string &filename,
                                    const std::string &var);

  std::pair<float,float> get_latlon(const std::string& filename, int y, int x);

  // draft - reading in vegetation for a single location
  int get_veg_class(const std::string &filename, int y, int x);
  
  // draft - reading in drainage for a single location
  int get_drainage_class(const std::string &filename, int y, int x);

  // Copy a variable's attributes from one NetCDF file (group) to another.
  void copy_atts(int igrp, int ivar, int ogrp, int ovar);

  // Copy a netCDF variable schema (name, dimensons, attributes, etc, but no 
  // actual data) from the src group (file) to the dest group (file).
  void copy_var(int srcgrp, int varid, int dstgrp);

  // Find the id of the grid_mapping variable in a netCDF file; 
  // returns -1 if no such variable exists in the file.
  int get_gridmapping_vid(int ncid);

  // draft - reading in fire information for a single location
  int get_fri(const std::string &filename, int y, int x);
  std::vector<int> get_fire_years(const std::string &filename, int y, int x);
  std::vector<int> get_fire_sizes(const std::string &filename, int y, int x);

  std::string read_cmt_code(std::string s);
  int cmtcode2num(std::string s);
  std::string cmtnum2str(int cmtnumber);
  std::vector<std::string> get_cmt_data_block(std::string filename, int cmtnum);
  std::list<std::string> strip_comments(std::vector<std::string> idb);

  std::list<std::string> parse_parameter_file(
      const std::string& fname, int cmtnumber, int linesofdata);


  /** Templated function for reading a timeseries variable from a basic netcdf
      file.
  */
  template <typename DTYPE>
  std::vector<DTYPE> get_timeseries2(const std::string &filename,
                                     const std::string &var,
                                     DTYPE type_example) {

    BOOST_LOG_SEV(glg, debug) << "Opening dataset: " << filename;

    int ncid;
    temutil::nc( nc_open(filename.c_str(), NC_NOWRITE, &ncid) );

    int timeseries_var;
    temutil::nc( nc_inq_varid(ncid, var.c_str(), &timeseries_var) );

    int timeD;
    size_t timeD_len;

    temutil::nc( nc_inq_dimid(ncid, "time", &timeD) );
    temutil::nc( nc_inq_dimlen(ncid, timeD, &timeD_len) );

    size_t start[1];
    start[0] = 0;         // from beginning of time

    size_t count[1];
    count[0] = timeD_len; // all time

    // Stuff for figuring out what kind of variable we have
    char vname[NC_MAX_NAME+1];
    nc_type the_type;
    int num_dims;
    int dim_ids[NC_MAX_VAR_DIMS];
    int num_atts;
    temutil::nc( nc_inq_var(ncid, timeseries_var, vname, &the_type, &num_dims, dim_ids, &num_atts) );

    // final data location
    std::vector<DTYPE> data2;

    if (the_type == NC_INT64 || NC_INT) {
      int dataI[timeD_len];
      temutil::nc( nc_get_vara_int(ncid, timeseries_var, start, count, &dataI[0]) );
      unsigned dataArraySize = sizeof(dataI) / sizeof(DTYPE);
      data2.insert(data2.end(), &dataI[0], &dataI[dataArraySize]);
    } else if (the_type == NC_FLOAT){
      float dataF[timeD_len];
      temutil::nc( nc_get_vara_float(ncid, timeseries_var, start, count, &dataF[0]) );
      unsigned dataArraySize = sizeof(dataF) / sizeof(DTYPE);
      data2.insert(data2.end(), &dataF[0], &dataF[dataArraySize]);
    } else {
      std::cout << "Unknown datatype: '" << the_type << "'. Returning empty vector.\n";
    }

    return data2;
  }

  /* NOTES:
   - not sure these need to be templates? to work with doubles, ints, or floats?
     right now I think all data is doubles.

   - seems like there should be a way to detect if it is a pft variable or not
     and thereby combine these two functions?
     read from string to tokenize into vectort, then if vector.size > 1, assume
     it is a pft - try and read data into appropriate spot?
     
   - need to some kind of check/safety to not overwrite the end of data??
   
   - Might eventually be useful to re-factor this again (so that the various
     codes for handling communities's parameter data can be compiled into a 
     stand-along command line utility..?
     
   - Not sure how to deal with writing errors...std::cout?? BOOST_LOG??
  */


  /** Pop the front of a "line-list" and store at the location of "data".
   * For setting internal data from dvmdostem parameter files.
  */
  template<typename T>
  void pfll2data(std::list<std::string> &l, T &data) {

    std::stringstream s(l.front());

    if ( !(s >> data) ) {
        BOOST_LOG_SEV(glg, fatal) << "ERROR in pfll2data! Problem converting parameter in this line to numeric value: " << l.front();
      data = -999999.0;
    }

    l.pop_front();
  }

  /** Pop the front of line-list and store at data. For multi pft 
   *  (multi-column) parameters 
   * For setting internal data from dvmdostem parameter files.
   *
  */
  template<typename T>
  void pfll2data_pft(std::list<std::string> &l, T *data) {

    std::stringstream s(l.front());
   
    for(int i = 0; i < NUM_PFT; i++) {

      if ( !(s >> data[i]) ) {
        BOOST_LOG_SEV(glg, fatal) << "ERROR in pfll2data_pft! Problem converting parameter in column " << i << " of this line to numeric value: " << l.front();
        data[i] = -99999.0;
      }
    }
   
    l.pop_front();

  }
  
  template<typename T>
  std::string vec2csv(const std::vector<T>& vec) {
    std::string s;
    for (typename std::vector<T>::const_iterator it = vec.begin(); it != vec.end(); ++it) {
      s += boost::lexical_cast<std::string>(*it);
      s += ", ";
    }
    if (s.size() >= 2) {   // clear the trailing comma, space
      s.erase(s.size()-2);
    }
    return s;
  }

}

#endif /* TEMUtilityFunctions_H */
