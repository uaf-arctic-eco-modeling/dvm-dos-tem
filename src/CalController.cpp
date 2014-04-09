#include <string>
#include <map>

#include <boost/asio.hpp>
#include <boost/asio/signal_set.hpp>
#include <boost/bind.hpp>
#include <boost/shared_ptr.hpp>

#include "CalController.h"
#include "TEMLogger.h"
#include "runmodule/Cohort.h"

extern src::severity_logger< severity_level > glg;


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
  ( "r", CalCommand("reload calparbgc file", boost::bind(&CalController::reload_calparbgc_file, this)) )
  ( "reload all",
    CalCommand("reload all cmt files",
               boost::bind(&CalController::reload_all_cmt_files, this)) )
  ( "h", CalCommand("show short menu", boost::bind(&CalController::show_short_menu, this)) )
  ( "help", CalCommand("show full menu", boost::bind(&CalController::show_full_menu, this)) )
  ( "env on", CalCommand("turn env module ON", boost::bind(&CalController::env_ON, this)) )
  ( "env off", CalCommand("turn env module OFF", boost::bind(&CalController::env_OFF, this)) )
  ( "bgc on", CalCommand("turn bgc module ON", boost::bind(&CalController::bgc_ON, this)) )
  ( "bgc off", CalCommand("turn bgc module OFF", boost::bind(&CalController::bgc_OFF, this)) )
  ( "dsb on", CalCommand("turn dsb module ON", boost::bind(&CalController::dsb_ON, this)) )
  ( "dsb off", CalCommand("turn dsb module OFF", boost::bind(&CalController::dsb_OFF, this)) )
  ( "dsl on", CalCommand("turn dsl module ON", boost::bind(&CalController::dsl_ON, this)) )
  ( "dsl off", CalCommand("turn dsl module OFF", boost::bind(&CalController::dsl_OFF, this)) )
  ( "dvm on", CalCommand("turn dvm module ON", boost::bind(&CalController::dvm_ON, this)) )
  ( "dvm off", CalCommand("turn dvm module OFF", boost::bind(&CalController::dvm_OFF, this)) )
  ( "print calparbgc",
    CalCommand("prints out the calparbgc parameters ",
               boost::bind(&CalController::print_calparbgc, this)) )
  ( "print module settings", 
    CalCommand("print module settings (on/off)",
               boost::bind(&CalController::print_modules_settings, this)) )
  ;
  
  
  BOOST_LOG_SEV(glg, debug) << "Set async wait on signals to PAUSE handler.";
  pause_sigs.async_wait( boost::bind(&CalController::pause_handler, this, 
                                     boost::asio::placeholders::error,
                                     boost::asio::placeholders::signal_number));
  if (!this->cohort_ptr) {
    BOOST_LOG_SEV(glg, err) << "Something is wrong and the Cohort pointer is null!";
  }
  BOOST_LOG_SEV(glg, debug) << "Done contructing a CalController.";
}  
  
/** Keep getting commands and executing commands from the user. 
 * 
 * It is possible to exit this loop with either a quit or continue command.
 */
void CalController::control_loop() {

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
  BOOST_LOG_SEV(glg, debug) << "In the CalController pause_handler";
  BOOST_LOG_SEV(glg, debug) << "Caught signal number: " << signal_number << " Error(s): " << error;

  //BOOST_LOG_SEV(clg, debug) << "BEFORE PARAMS: \n" << cohort_ptr->chtlu.dump_calparbgc();

  control_loop();
  BOOST_LOG_SEV(glg, debug) << "Done in pause handler...";

}

/** Pause, but asynchronously?
 *
 *  Posts a message to the io_service (which is asynchronously waiting).
 *  When the message is processed, the control loop is run, and the control loop
 *  blocks waiting for user input, so the simulaiton is stopped while the 
 *  control loop is blocking.
 *
 *  So it seems that the simulation may not pause immediately, but only once
 *  the io_service gets around to processing this posted message.
 *  Not sure how useful this actually is, but we'll leave it around for now.
 */
void CalController::async_pause( ) {
  BOOST_LOG_SEV(glg, debug) << "Posting to the io_service.";
  this->io_service->post( boost::bind(&CalController::control_loop, this) );
}

/** Forcibly pauses the simulation.
  * Runs the control loop, which blocks, waiting for user input.
  */
void CalController::pause( ) {
  BOOST_LOG_SEV(glg, info) << "Starting control loop to pause simulation.";
  control_loop();
}

/** Check the io_service object for signals that may have arrived. */
void CalController::check_for_signals() {
  int handlers_run = 0;
  boost::system::error_code ec;

  BOOST_LOG_SEV(glg, debug) << "Poll the io_service...";
  handlers_run = io_service->poll(ec);
  BOOST_LOG_SEV(glg, debug) << "Handlers run: " << handlers_run;

  if (handlers_run > 0) {

    BOOST_LOG_SEV(glg, debug) << "Reset the io_service object.";
    io_service->reset();

    BOOST_LOG_SEV(glg, debug) << "Set async wait on signals to PAUSE handler.";
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




void CalController::continue_simulation() {
  BOOST_LOG_SEV(glg, note) << "Executing continue_simulation callback...";
  // not quite sure how to do this one?
  // seems like nothing needs to happen here...
}

void CalController::reload_all_cmt_files() {
  BOOST_LOG_SEV(glg, note) << "Executing reload_cmt_files callback...";
  BOOST_LOG_SEV(glg, debug) << "Use cohort pointer to reload all cmt files...";
  this->cohort_ptr->chtlu.init();
  BOOST_LOG_SEV(glg, note) << "Done reloading config/parameter files.";
}

void CalController::reload_calparbgc_file() {
  BOOST_LOG_SEV(glg, note) << "Executing reload_calparbgc_file callback...";
  BOOST_LOG_SEV(glg, debug) << "Use cohort pointer's cohort lookup object to 'assignBgcCalpar'...";
  std::string config_dir = this->cohort_ptr->chtlu.dir;
  this->cohort_ptr->chtlu.assignBgcCalpar(config_dir);
  BOOST_LOG_SEV(glg, note) << "Done reloading calparbgc file.";
  
}

void CalController::quit() {
  BOOST_LOG_SEV(glg, note) << "Executing the quit callback...";
  BOOST_LOG_SEV(glg, note) << "Quitting via CalController."; 
  exit(-1);
}

void CalController::env_ON() {
  BOOST_LOG_SEV(glg, note) << "CalController is turing env module ON via cohort pointer...";
  this->cohort_ptr->md->set_envmodule(true);
}
void CalController::env_OFF() {
  BOOST_LOG_SEV(glg, note) << "CalController is turing env module OFF via cohort pointer...";
  this->cohort_ptr->md->set_envmodule(false);
}

void CalController::bgc_ON() {
  BOOST_LOG_SEV(glg, note) << "CalController is turing bgc module ON via cohort pointer...";
  this->cohort_ptr->md->set_bgcmodule(true);
}
void CalController::bgc_OFF() {
  BOOST_LOG_SEV(glg, note) << "CalController is turing bgc module OFF via cohort pointer...";
  this->cohort_ptr->md->set_bgcmodule(false);
}

void CalController::dsb_ON() {
  BOOST_LOG_SEV(glg, note) << "CalController is turing dsb module ON via cohort pointer...";
  this->cohort_ptr->md->set_dsbmodule(true);
}
void CalController::dsb_OFF() {
  BOOST_LOG_SEV(glg, note) << "CalController is turing dsb module OFF via cohort pointer...";
  this->cohort_ptr->md->set_dsbmodule(false);
}

void CalController::dsl_ON() {
  BOOST_LOG_SEV(glg, note) << "CalController is turing dsl module ON via cohort pointer...";
  this->cohort_ptr->md->set_dslmodule(true);
}
void CalController::dsl_OFF() {
  BOOST_LOG_SEV(glg, note) << "CalController is turing dsl module OFF via cohort pointer...";
  this->cohort_ptr->md->set_dslmodule(false);
}

void CalController::dvm_ON() {
  BOOST_LOG_SEV(glg, note) << "CalController is turing dvm module ON via cohort pointer...";
  this->cohort_ptr->md->set_dvmmodule(true);
}
void CalController::dvm_OFF() {
  BOOST_LOG_SEV(glg, note) << "CalController is turing dvm module OFF via cohort pointer...";
  this->cohort_ptr->md->set_dvmmodule(false);
}

void CalController::print_calparbgc() {
  BOOST_LOG_SEV(glg, note) << "Printing the 'calparbgc' parameters stored in the CohortLookup pointer...";
  std::string a_string = this->cohort_ptr->chtlu.calparbgc2str();
  std::cout << a_string;
}

void CalController::print_modules_settings() {
  BOOST_LOG_SEV(glg, note) << "Showing module settings from cohort pointer's "
                           << "ModelData.\n";
  std::string s = this->cohort_ptr->md->describe_module_settings();
  std::cout << s;
}
void CalController::show_short_menu() {
   BOOST_LOG_SEV(glg, note) << "Showing short menu...";
   std::string m = "";
   m += "  q - "; m += this->cmd_map["q"].desc; m += "\n";
   m += "  c - "; m += this->cmd_map["c"].desc; m += "\n";
   m += "  r - "; m += this->cmd_map["r"].desc; m += "\n";
   m += "  h - "; m += this->cmd_map["h"].desc; m += "\n";
   m += "  help - "; m += this->cmd_map["help"].desc; m += "\n";
   std::cout << m;
}

void CalController::show_full_menu() {

  BOOST_LOG_SEV(glg, note) << "Showing full menu...";

  std::string m = "--  Full Calibration Controller Menu --\n";

  std::map<std::string, CalCommand>::const_iterator citer;
  for(citer = cmd_map.begin(); citer != cmd_map.end(); ++citer) {
     m += "    "; 
     m += citer->first; 
     m += " - ";
     m += citer->second.desc;
     m += "\n";
  }
  m += "---------------------------------------\n";
  std::cout << m;
  
}


