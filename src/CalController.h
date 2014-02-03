#ifndef _CALCONTROLLER_H_
#define _CALCONTROLLER_H_

#include <string>
#include <map>

#include <boost/assign/list_of.hpp> // for map_list_of()

#include <boost/asio.hpp>
#include <boost/asio/signal_set.hpp>
#include <boost/shared_ptr.hpp>


#include "TEMLogger.h"
#include "runmodule/Cohort.h"

class CalController {
public:
  
  CalController(boost::shared_ptr< Cohort > cht_ptr);
  
  std::string getUserCommand();
  void showCalibrationControlMenu();
  void check_for_signals();

private:
  static severity_channel_logger_t& clg;

  boost::shared_ptr< boost::asio::io_service > io_service;
  boost::asio::signal_set pause_sigs;

  boost::shared_ptr< Cohort > cht_ptr;
  
  std::map<std::string, std::string> commands;

  void pause_handler( const boost::system::error_code& error, int signal_number);
  
};

#endif /* _CALCONTROLLER_H_ */


