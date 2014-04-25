//
//  TEMUtilityFunctions.cpp
//  dvm-dos-tem
//
//  Created by Tobey Carman on 4/10/14.
//  Copyright (c) 2014 Spatial Ecology Lab. All rights reserved.
//

#include <string>
#include <stdexcept>

#include "TEMUtilityFunctions.h"

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

}
