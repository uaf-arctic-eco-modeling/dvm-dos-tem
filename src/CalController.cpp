#include <string>
#include <map>

#include <boost/asio.hpp>
#include <boost/asio/signal_set.hpp>
#include <boost/bind.hpp>
#include <boost/shared_ptr.hpp>

#include "CalController.h"
#include "TEMLogger.h"
#include "runmodule/Cohort.h"

BOOST_LOG_INLINE_GLOBAL_LOGGER_INIT(my_cal_logger, severity_channel_logger_t) {
  return severity_channel_logger_t(keywords::channel = "CALIB");
}
severity_channel_logger_t& CalController::clg = my_cal_logger::get();


CalController::CalController(Cohort* cht_p):
    io_service(new boost::asio::io_service),
    pause_sigs(*io_service, SIGINT, SIGTERM),
    cohort_ptr(cht_p)
{
  // can't seem to use initializaiton list; ambiguous overload error...
  commands = boost::assign::map_list_of<std::string, std::string>
                                      ("c", "continue simulation")
                                      ("r", "reload config files")
                                      ("q", "quit");
                                      
  BOOST_LOG_SEV(clg, debug) << "Set async wait on signals to PAUSE handler.";
  pause_sigs.async_wait( boost::bind(&CalController::pause_handler, this, 
                                     boost::asio::placeholders::error,
                                     boost::asio::placeholders::signal_number));
  if (!this->cohort_ptr) {
    BOOST_LOG_SEV(clg, err) << "Something is wrong and the Cohort pointer is null!";
  }
  BOOST_LOG_SEV(clg, debug) << "Done contructing a CalController.";
}

void CalController::pause_handler( const boost::system::error_code& error, int signal_number) {
  BOOST_LOG_SEV(clg, debug) << "In the CalController pause_handler";
  BOOST_LOG_SEV(clg, debug) << "Signal Number: " << signal_number << " Error(s): " << error;

  BOOST_LOG_SEV(clg, debug) << "BEFORE PARAMS: \n" << cohort_ptr->chtlu.dump_calparbgc();
  
  show_cal_control_menu();

  std::string cmd = "";
  cmd = get_user_command();

  if (cmd.compare("r") == 0) {
    BOOST_LOG_SEV(clg, debug) << "We are going to reload all the parameter files...";
    cohort_ptr->chtlu.init();
    BOOST_LOG_SEV(clg, debug) << "AFTER MODIFYING/RELOADING PARAMS:\n" << cohort_ptr->chtlu.dump_calparbgc();

    show_cal_control_menu();
    std::string cmd = "";
    while (cmd != "c") {
      cmd = get_user_command();
    }
  }
  
  BOOST_LOG_SEV(clg, debug) << "Done in pause handler...";

}

void CalController::check_for_signals() {
  int handlers_run = 0;
  boost::system::error_code ec;

  BOOST_LOG_SEV(clg, debug) << "Poll the io_service...";
  handlers_run = io_service->poll(ec);
  BOOST_LOG_SEV(clg, debug) << "Handlers run: " << handlers_run;

  if (handlers_run > 0) {

    BOOST_LOG_SEV(clg, debug) << "Reset the io_service object.";
    io_service->reset();

    BOOST_LOG_SEV(clg, debug) << "Set async wait on signals to PAUSE handler.";
    pause_sigs.async_wait( boost::bind(&CalController::pause_handler, this, 
                                       boost::asio::placeholders::error,
                                       boost::asio::placeholders::signal_number));
  }
}


std::string CalController::get_user_command() {
  std::string ui = "";
  while( !(commands.count(ui)) ) {
    std::cout << "What now?> ";
    std::getline(std::cin, ui);
    std::cin.clear();
  }
  return ui;
}
void CalController::show_cal_control_menu() {

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


