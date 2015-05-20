#include <string>
#include <map>

#include <boost/asio.hpp>
#include <boost/asio/signal_set.hpp>
#include <boost/bind.hpp>
#include <boost/filesystem.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/tokenizer.hpp>
#include <boost/lexical_cast.hpp>


#include "CalController.h"
#include "TEMLogger.h"
#include "runmodule/Cohort.h"

#include <iostream>


extern src::severity_logger< severity_level > glg;

/** An object that can control parts of a simulation thru a Cohort pointer.
 
 A CalController needs a pointer to a Cohort, as well as a Json::Value that
 describes a set of pre-set actions to take when running in calibration mode.
 
 These actions could be simply a set of setup-steps after interactive control
 is given back to the user or, using the 'quit_at'
 
 You must pass a pointer to a Cohort in order to
 * make a valid CalController! Th
 */
CalController::CalController(Cohort* cht_p, bool itractv, Json::Value config_obj):
  io_service(new boost::asio::io_service),
  pause_sigs(*io_service, SIGINT, SIGTERM),
  run_configuration(config_obj),
  cohort_ptr(cht_p),
  interactive(itractv) {
  cmd_map = boost::assign::map_list_of
            ("q", CalCommand("quit the calibrator",
                             boost::bind(&CalController::quit, this)) )
            ("c",
              CalCommand("continue simulation",
                          boost::bind(&CalController::continue_simulation,
                                      this)) )
            ("r",
              CalCommand("reload calparbgc file",
                          boost::bind(&CalController::reload_calparbgc_file,
                                      this)) )
            ("reload all",
              CalCommand("reload all cmt files",
                          boost::bind(&CalController::reload_all_cmt_files,
                                      this)) )
            ("h",
              CalCommand("show short menu",
                          boost::bind(&CalController::show_short_menu, this)) )
            ("help",
              CalCommand("show full menu",
                          boost::bind(&CalController::show_full_menu, this)) )

            ("dsb on", CalCommand("turn dsb module ON",
                                   boost::bind(&CalController::dsb_ON, this)) )
            ("dsb off",
              CalCommand("turn dsb module OFF",
                          boost::bind(&CalController::dsb_OFF, this)) )
            ("dsl on", CalCommand("turn dsl module ON",
                                  boost::bind(&CalController::dsl_ON, this)) )
            ("dsl off", CalCommand("turn dsl module OFF",
                                   boost::bind(&CalController::dsl_OFF, this)) )
            ("dvm on", CalCommand("turn dvm module ON",
                                   boost::bind(&CalController::dvm_ON, this)) )
            ("dvm off", CalCommand("turn dvm module OFF",
                                   boost::bind(&CalController::dvm_OFF, this)) )
            ("nfeed on",
              CalCommand("turn nitrogen feedback ON",
                          boost::bind(&CalController::nfeed_ON, this)) )
            ("nfeed off",
              CalCommand("turn nitrogen feedback OFF",
                          boost::bind(&CalController::nfeed_OFF, this)) )
            ("avln on",
              CalCommand("turn available nitrogen ON",
                          boost::bind(&CalController::avlnflg_ON, this)) )
            ("avln off",
              CalCommand("turn available nitrogen OFF",
                          boost::bind(&CalController::avlnflg_OFF, this)) )
            ("baseline on",
              CalCommand("turn baseline ON",
                          boost::bind(&CalController::baseline_ON, this)) )
            ("baseline off",
              CalCommand("turn baseline OFF",
                          boost::bind(&CalController::baseline_OFF, this)) )
            ("print calparbgc",
              CalCommand("prints out the calparbgc parameters ",
                         boost::bind(&CalController::print_calparbgc, this)) )
            ("print module settings",
              CalCommand("print module settings (on/off)",
                         boost::bind(&CalController::print_modules_settings, this)) )
            ("quitat",
              CalCommand("quits and exits at simulation year specified",
                         boost::bind(&CalController::quit_at, this, _1)) )
            ("pauseat",
              CalCommand("pauses at simulation year specified",
                         boost::bind(&CalController::pause_at, this, _1)) )

            ("env",
              CalCommand("changes env module state...",
                         boost::bind(&CalController::env_cmd, this, _1)) )
            ("bgc",
              CalCommand("changes bgc module state...",
                         boost::bind(&CalController::bgc_cmd, this, _1)) )
            ("avln",
              CalCommand("changes available Nitrogen setting...",
                         boost::bind(&CalController::avln_cmd, this, _1)) )

            ;

  

  BOOST_LOG_SEV(glg, debug) << "Set async wait on signals to PAUSE handler.";
  pause_sigs.async_wait( boost::bind(&CalController::pause_handler, this,
                                     boost::asio::placeholders::error,
                                     boost::asio::placeholders::signal_number));

  if (!this->cohort_ptr) {
    BOOST_LOG_SEV(glg, err) << "Something is wrong and the Cohort pointer is null!";
  }

  BOOST_LOG_SEV(glg, debug) << "Done constructing a CalController.";
}

void CalController::quit_at(const std::string& s) {
  int year;
  try {
    year = boost::lexical_cast<int>(s);
    this->run_configuration["quitat"] = year;
    BOOST_LOG_SEV(glg, info) << "Setting the quitat year in CalController's run_configuration to " << year;
  } catch( const boost::bad_lexical_cast & ) {
    BOOST_LOG_SEV(glg, warn) << "Unable to convert '"<< s <<"' to valid integer for a quit-at year.";
  }
}

void CalController::pause_at(const std::string& s) {
  int year;
  try {
    year = boost::lexical_cast<int>(s);
    this->run_configuration["pauseat"] = year;
    BOOST_LOG_SEV(glg, info) << "Setting the pauseat year in CalController's run_configuration to " << year;
  } catch( const boost::bad_lexical_cast & ) {
    BOOST_LOG_SEV(glg, warn) << "Unable to convert '"<< s <<"' to valid integer for a pause-at year.";
  }
}

void CalController::auto_run(int simulation_year) {
  std::cout << "year: " << simulation_year << ". FUCK YEAH! auto-running!! \n";
}

/** Keep getting commands and executing commands from the user.
 *
 * It is possible to exit this loop with either a quit or continue command.
 */
void CalController::control_loop() {
  show_short_menu();
  char * line_read = (char*)NULL;

  while (true) {
    if(line_read != (char *)NULL) {
      free (line_read);
      line_read = (char *)NULL;
    }

    /* Get a line from the user. */
    line_read = readline ("Enter command> ");

    /* If the line has any text in it, save it on the history. */
    if(line_read && *line_read) {
      add_history (line_read);
      std::string line = std::string(line_read);

      // Pick up the continue
      if(strcmp(line_read,"c")==0) {
        free(line_read);
        break;
      }

      // Otherwise, pickup any (old?), multi-word commands
      if(this->cmd_map.count(line)) {
        BOOST_LOG_SEV(glg, warn) << "OLD handlers being called NEW way...! Double check that things are working.";
        this->cmd_map[line].executor("");
      }

      // NOTE:
      // Things get double called if both the old-style multi-word command
      // and associated functions are declared as well as the new-style
      // parameterized command is declared.

      // Parse string of commands and parameters, calling appropriate function.
      boost::tokenizer<> tokens(line);
      for (boost::tokenizer<>::iterator tkn_it=tokens.begin(); tkn_it!=tokens.end(); ++tkn_it) {
        std::string tkn = *tkn_it;

        if (this->cmd_map.count(tkn)) {
        
          std::cout << "Found token '"<<tkn<<"' in the cmd_map.\n";

          // store the command, and bump the iterator forward
          std::string cmd = tkn;
          std::vector<std::string> params;//(4, "");
          ++tkn_it;
          
          std::cout << "Looking for any additional command parameters...\n";
          if (tkn_it != tokens.end()) {
          
            // Accumulate any parameters for the command. Continue scanning for
            // parameters until either the end of the input string is reached.
            for (boost::tokenizer<>::iterator param_it = tkn_it; param_it != tokens.end(); ++param_it) {
              params.push_back(*param_it);
            }
          }

          // All of our executors take one string argument, so if there is
          // nothing specified on the command line, then add an empty string
          // to the parameter vector...
          if (params.size() == 0) {
            params.push_back("");
          }
          
          // Now we have a command string and a vector of parameters (strings)
          // Only need one command at the moment, so the vector is overkill, but
          // it means we can take more complicated stuff in the future.
          BOOST_LOG_SEV(glg, info) << "Command token: '"<< cmd <<"'. Parameters: ";
          for (std::vector<std::string>::iterator it=params.begin(); it!=params.end(); ++it) {
            std::cout << "  [i]: " << *it << std::endl;
          }

          this->cmd_map[cmd].executor(params.at(0));
          
          if (tkn_it == tokens.end()) {
            break;
          }

        }
        
      }

    }
  }
}


/** The call back that is run when a registered signal is recieved and processed.
 * Technically, because of the async_wait, the may be run some time after the
 * signal is recieved, so it is really run when a recieved signal is processed.
 */
void CalController::pause_handler(const boost::system::error_code& error,
                                  int signal_number) {
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

/** Clean out json files.
 * Cleans out all the json files in /tmp that were generated by the model by
 * deleting directories. Creates new empty directories.
*/
void CalController::clear_and_create_json_storage() {

  boost::filesystem::path mly_json_folder("/tmp/cal-dvmdostem/");
  boost::filesystem::path yly_json_folder("/tmp/year-cal-dvmdostem");

  if( !(boost::filesystem::exists(yly_json_folder)) ) {
    BOOST_LOG_SEV(glg, info) << "Creating folder: " << yly_json_folder;
    boost::filesystem::create_directory(yly_json_folder);
  } else {
    BOOST_LOG_SEV(glg, info) << "Calibraiton json yearly folder already exists!"
                             << "Delete and recreate...";
    boost::filesystem::remove_all(yly_json_folder);
    boost::filesystem::create_directory(yly_json_folder);
  }

  if( !(boost::filesystem::exists(mly_json_folder)) ) {
    BOOST_LOG_SEV(glg, info) << "Creating folder: " << mly_json_folder;
    boost::filesystem::create_directory(mly_json_folder);
  } else {
    BOOST_LOG_SEV(glg, info) << "Calibraiton json monthly folder already exists!"
                             << "Delete and recreate...";
    boost::filesystem::remove_all(mly_json_folder);
    boost::filesystem::create_directory(mly_json_folder);
  }
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
    pause_sigs.async_wait(boost::bind(&CalController::pause_handler, this,
                                      boost::asio::placeholders::error,
                                      boost::asio::placeholders::signal_number));
  }
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
  BOOST_LOG_SEV(glg, note) << "Next, make sure the veg parameters propogate?";
  for (int i = 0; i < NUM_PFT; ++i) {
    BOOST_LOG_SEV(glg, note) << "Assign the cohort's vegbgc params to those held in the chtlu object...";
    this->cohort_ptr->vegbgc[i].initializeParameter();
  }
  BOOST_LOG_SEV(glg, note) << "Finally, make sure the soil parameters propogate?";
  this->cohort_ptr->soilbgc.initializeParameter();
}

void CalController::quit() {
  BOOST_LOG_SEV(glg, note) << "Executing the quit callback...";
  BOOST_LOG_SEV(glg, note) << "Quitting via CalController.";
  exit(-1);
}

void CalController::env_cmd(const std::string& s) {
  try {
    this->cohort_ptr->md->set_envmodule(temutil::onoffstr2bool(s));

    BOOST_LOG_SEV(glg, note) << "CalController turned env module to "
                             << s <<" via cohort pointer...";

  } catch (const std::runtime_error& e) {
    BOOST_LOG_SEV(glg, warn) << e.what();
  }
}

void CalController::bgc_cmd(const std::string& s) {
  try {
    this->cohort_ptr->md->set_bgcmodule(temutil::onoffstr2bool(s));

    BOOST_LOG_SEV(glg, note) << "CalController turned bgc module to "
                             << s <<" via cohort pointer...";

  } catch (const std::runtime_error& e) {
    BOOST_LOG_SEV(glg, warn) << e.what();
  }
}
void CalController::avln_cmd(const std::string& s) {
  try {
    this->cohort_ptr->md->set_avlnflg(temutil::onoffstr2bool(s));

    BOOST_LOG_SEV(glg, note) << "CalController turned available Nitrogen flag to "
                             << s <<" via cohort pointer...";

  } catch (const std::runtime_error& e) {
    BOOST_LOG_SEV(glg, warn) << e.what();
  }
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

void CalController::nfeed_ON() {
  BOOST_LOG_SEV(glg, note) << "CalController is turing nitrogen feedback ON via cohort pointer...";
  this->cohort_ptr->md->set_nfeed(true);
}

void CalController::nfeed_OFF() {
  BOOST_LOG_SEV(glg, note) << "CalController is turing nitrogen feedback OFF via cohort pointer...";
  this->cohort_ptr->md->set_nfeed(false);
}

void CalController::avlnflg_ON() {
  BOOST_LOG_SEV(glg, note) << "CalController is turing available nitrogen ON via cohort pointer...";
  this->cohort_ptr->md->set_avlnflg(true);
}
void CalController::avlnflg_OFF() {
  BOOST_LOG_SEV(glg, note) << "CalController is turing available nitrogen OFF via cohort pointer...";
  this->cohort_ptr->md->set_avlnflg(false);
}

void CalController::baseline_ON() {
  BOOST_LOG_SEV(glg, note) << "CalController is turing baseline ON via cohort pointer...";
  this->cohort_ptr->md->set_baseline(true);
}

void CalController::baseline_OFF() {
  BOOST_LOG_SEV(glg, note) << "CalController is turing baseline OFF via cohort pointer...";
  this->cohort_ptr->md->set_baseline(false);
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
  m += "  q - ";
  m += this->cmd_map["q"].desc;
  m += "\n";
  m += "  c - ";
  m += this->cmd_map["c"].desc;
  m += "\n";
  m += "  r - ";
  m += this->cmd_map["r"].desc;
  m += "\n";
  m += "  h - ";
  m += this->cmd_map["h"].desc;
  m += "\n";
  m += "  help - ";
  m += this->cmd_map["help"].desc;
  m += "\n";
  std::cout << m;
}

/** Returns whether or not interactive control is being used.

  When interactive is true, the program will wait for interupt signal
  (SIGINT) and use the CalController::control_loop() function to get commands 
  from the stdin (the user or possibly a file if one is redirected to stdin). 
  
  When interactive is false, the program will instead use the run_configuration
  member to carry out a specific set of calibration tasks - basically turning 
  modules on and off at specified years.
*/
bool CalController::get_interactive(){
  return this->interactive;
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


          // For example this string should
          // call the first command (print) with 4 parameters, and the second
          // command with 2 parameters: "print p1 p2 p3 p4 dsl on 100"
