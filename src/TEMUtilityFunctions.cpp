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
  

}
