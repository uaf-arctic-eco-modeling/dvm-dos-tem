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
#include <list>
#include <netcdfcpp.h>
#include <json/value.h>
#include "inc/cohortconst.h" // needed for NUM_PFT

namespace temutil {

  int day_of_year(int month, int day);

  float length_of_day(float lat, int doy);

  std::string cmtnum2str(int cmtnumber);

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
  
  std::pair<float,float> get_latlon(const std::string& filename, int y, int x);

  // draft - reading in vegetation for a single location
  int get_veg_class(const std::string &filename, int y, int x);
  
  // draft - reading in drainage for a single location
  int get_drainage_class(const std::string &filename, int y, int x);

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
      //BOOST_LOG_SEV(glg, err) << "ERROR! Problem converting parameter in this line to numeric value: " << l.front();
      std::cout << "Problem...\n";
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
        //BOOST_LOG_SEV(glg, err) << "ERROR! Problem converting parameter in column "<<i<<"of this line to numeric value: " << l.front();
        std::cout << "Problem...\n";
        data[i] = -99999.0;
      }
    }
   
    l.pop_front();

  }
  
  template<typename T>
  std::string vec2csv(const std::vector<T> vec) {
    std::string s;
    for (typename std::vector<T>::const_iterator it = vec.begin(); it != vec.end(); ++it) {
      s += *it;
      s += ", ";
    }
    s.erase(s.size()-2);
    return s;
  }

}

#endif /* TEMUtilityFunctions_H */
