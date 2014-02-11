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

/** Constructor. You gotta pass a pointer to a Cohort in order to 
 * make a valid CalController!
 */
CalController::CalController(Cohort* cht_p):
    io_service(new boost::asio::io_service),
    pause_sigs(*io_service, SIGINT, SIGTERM),
    cohort_ptr(cht_p)
{
  cmd_map = boost::assign::map_list_of
  ( "q", CalCommand("quit the calibrator", boost::bind(&CalController::quit, this)) )
  ( "c", CalCommand("continue simulation", boost::bind(&CalController::continue_simulation, this)) )
  ( "r", CalCommand("reload cmt files", boost::bind(&CalController::reload_cmt_files, this)) )
  ( "h", CalCommand("show short menu", boost::bind(&CalController::show_short_menu, this)) )
  ( "help", CalCommand("show full menu", boost::bind(&CalController::show_full_menu, this)) );
  
  
  BOOST_LOG_SEV(clg, debug) << "Set async wait on signals to PAUSE handler.";
  pause_sigs.async_wait( boost::bind(&CalController::pause_handler, this, 
                                     boost::asio::placeholders::error,
                                     boost::asio::placeholders::signal_number));
  if (!this->cohort_ptr) {
    BOOST_LOG_SEV(clg, err) << "Something is wrong and the Cohort pointer is null!";
  }
  BOOST_LOG_SEV(clg, debug) << "Done contructing a CalController.";
}  
  
/** Keep getting commands and executing commands from the user. 
 * 
 * It is possible to exit this loop with either a quit or continue command.
 */
void CalController::control_loop(){

  show_short_menu();

  while (true) {

    std::string user_input = "";

    user_input = get_user_command();

    if (user_input.compare("c") == 0) {
      // do nothing and break the loop to let the simulation continue 
      break;
    }

    // Otherwise, do one of the commands.
    this->cmd_map[user_input].executor();
  }
}

/** The call back that is run when a registered signal is recieved and processed.
 * Technically, because of the async_wait, the may be run some time after the 
 * signal is recieved, so it is really run when a recieved signal is processed.
 */
void CalController::pause_handler( const boost::system::error_code& error, int signal_number) {
  BOOST_LOG_SEV(clg, debug) << "In the CalController pause_handler";
  BOOST_LOG_SEV(clg, debug) << "Caught signal number: " << signal_number << " Error(s): " << error;

  //BOOST_LOG_SEV(clg, debug) << "BEFORE PARAMS: \n" << cohort_ptr->chtlu.dump_calparbgc();

  control_loop();
  BOOST_LOG_SEV(clg, debug) << "Done in pause handler...";

}

/** Check the io_service object for signals that may have arrived. */
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

/** Get a string from the user until it matches one in the cmd_map 
 */
std::string CalController::get_user_command() {
  std::string ui = "";
  while( !(this->cmd_map.count(ui)) ) {
    std::cout << "What now?> ";
    std::getline(std::cin, ui);
    std::cin.clear();
  }
  return ui;
}




void CalController::continue_simulation(){
  BOOST_LOG_SEV(clg, info) << "Executing continue_simulation callback...";
  // not quite sure how to do this one?
}
void CalController::reload_cmt_files(){
  BOOST_LOG_SEV(clg, info) << "Executing reload_cmt_files callback...";
  BOOST_LOG_SEV(clg, info) << "Tickling the cohort pointer to reload config/parameter files...";
  cohort_ptr->chtlu.init();
  BOOST_LOG_SEV(clg, info) << "Done reloading config/parameter files.";
  
}
void CalController::quit(){
  BOOST_LOG_SEV(clg, info) << "Executing the quit callback...";
  BOOST_LOG_SEV(clg, info) << "Quitting via CalController."; 
  exit(-1);
}

// void CalController::env_ON(){
//   this->cohort_ptr->md->envmodule = true;
// }
// void CalController::env_OFF(){
//   this->cohort_ptr->md->envmodule = false;
// }


void CalController::show_short_menu() {
   BOOST_LOG_SEV(clg, debug) << "Showing short menu...";
   std::string m = "";
   m += "q - "; m += this->cmd_map["q"].desc; m += "\n";
   m += "c - "; m += this->cmd_map["c"].desc; m += "\n";
   m += "r - "; m += this->cmd_map["r"].desc; m += "\n";
   m += "h - "; m += this->cmd_map["h"].desc; m += "\n";
   m += "help - "; m += this->cmd_map["help"].desc; m += "\n";
   std::cout << m;
}

void CalController::show_full_menu() {

  BOOST_LOG_SEV(clg, debug) << "Showing full menu...";

  std::string m = "--  Full Calibration Controller Menu --\n";

  std::map<std::string, CalCommand>::const_iterator citer;
  for(citer = cmd_map.begin(); citer != cmd_map.end(); ++citer) {
     m += citer->first; 
     m += " - ";
     m += citer->second.desc;
     m += "\n";
  }
  m += "---------------------------------------\n";
  std::cout << m;
  
}

// dvmmodule
// bgcmodule
// envmodule
// bool dslmodule;  

// bool dsbmodule;  
// bool friderived; 

// bool nfeed;    
// bool avlnflg;
// bool baseline; 

