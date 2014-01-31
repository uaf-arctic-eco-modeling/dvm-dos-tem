#include <string>
#include <map>

#include "CalController.h"
#include "TEMLogger.h"

BOOST_LOG_INLINE_GLOBAL_LOGGER_INIT(my_cal_logger, severity_channel_logger_t) {
  return severity_channel_logger_t(keywords::channel = "CALIB");
}

severity_channel_logger_t& CalController::clg = my_cal_logger::get();

std::string CalController::getUserCommand() {
  std::string ui = "";
  while( !(commands.count(ui)) ) {
    std::cout << "What now?> ";
    std::getline(std::cin, ui);
    std::cin.clear();
  }
  return ui;
}
void CalController::showCalibrationControlMenu() {

  std::string m = "Entering calibration controller....\n"
                  "\n"
                  "-------------- Menu -----------------\n"
                  "Choose one of the following options:\n";
                  
  std::map<std::string, std::string>::const_iterator citer;
  for(citer = commands.begin(); citer != commands.end(); ++citer) {
    m += citer->first;
    m += " - ";
    m += citer->second;
    m += "\n";
  }

  BOOST_LOG_SEV(clg, info) << m;
  
}



