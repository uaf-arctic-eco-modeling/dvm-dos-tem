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
  
  CalController(Cohort* cht_p);
  
  std::string get_user_command();
  void show_cal_control_menu();
  void check_for_signals();

private:
  static severity_channel_logger_t& clg;

  boost::shared_ptr< boost::asio::io_service > io_service;
  boost::asio::signal_set pause_sigs;

  Cohort* cohort_ptr;
  
  std::map<std::string, std::string> commands;

  void pause_handler( const boost::system::error_code& error, int signal_number);
  
};

#endif /* _CALCONTROLLER_H_ */


