#ifndef _CALCONTROLLER_H_
#define _CALCONTROLLER_H_

#include <string>
#include <map>

#include <boost/assign/list_of.hpp> // for map_list_of()
#include <boost/function.hpp>

#include <boost/asio.hpp>
#include <boost/asio/signal_set.hpp>
#include <boost/shared_ptr.hpp>


#include "TEMLogger.h"
#include "runmodule/Cohort.h"

typedef struct CalCommand {
  std::string desc;
  boost::function<void ()> executor;
  
  CalCommand(){} // somehow I need this to compile?
  CalCommand( std::string adesc, boost::function<void ()> aexecutor ) :
      desc(adesc), executor(aexecutor) {}
  
} CalCommand;

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
  
  std::map<std::string, CalCommand> cmd_map; 

  void pause_handler( const boost::system::error_code& error, int signal_number);
  void control_loop();

  void quit();
  void reload_cmt_files();
  void continue_simulation();
  void show_full_menu();
  void show_short_menu();

  void env_ON();
  void env_OFF();
};

#endif /* _CALCONTROLLER_H_ */


