#ifndef _CALCONTROLLER_H_
#define _CALCONTROLLER_H_

#include <string>
#include <map>

#include <boost/assign/list_of.hpp> // for map_list_of()

#include "TEMLogger.h"
#include "assembler/Runner.h"

class CalController {
public:
  Runner runner;
  
  CalController() { 
      commands = boost::assign::map_list_of<std::string, std::string>
                                         ("c", "continue simulation")
                                         ("r", "reload config files")
                                         ("q", "quit");
  }
                                       
  std::string getUserCommand();
  void showCalibrationControlMenu();

private:
  std::map<std::string, std::string> commands;
  static severity_channel_logger_t& glg;
  static severity_channel_logger_t& clg;

  
};

#endif /* _CALCONTROLLER_H_ */


