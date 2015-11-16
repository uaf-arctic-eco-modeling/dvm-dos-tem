#include <iostream>
#include <string>
#include <map>

#include <boost/asio.hpp>
#include <boost/asio/signal_set.hpp>
#include <boost/bind.hpp>
#include <boost/filesystem.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/tokenizer.hpp>
#include <boost/lexical_cast.hpp>

#include "../include/CalController.h"
#include "TEMLogger.h"
#include "runmodule/Cohort.h"
#include "TEMUtilityFunctions.h"

extern src::severity_logger< severity_level > glg;

/** An object that can control parts of a simulation thru a Cohort pointer.

 You must pass a pointer to a Cohort in order to make a valid CalController!

 The CalibrationController will try to load a set of configurations from
 a txt file in the config/ director.
*/
CalController::CalController(Cohort* cht_p):
  io_service(new boost::asio::io_service),
  pause_sigs(*io_service, SIGINT, SIGTERM),
  cohort_ptr(cht_p) {
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

            ("print calparbgc",
              CalCommand("prints out the calparbgc parameters ",
                         boost::bind(&CalController::print_calparbgc, this)) )
            ("print module settings",
              CalCommand("print module settings (on/off)",
                         boost::bind(&CalController::print_modules_settings, this)) )

            ("print directives",
              CalCommand("show data from the run_configuration data structure",
                         boost::bind(&CalController::print_directive_settings, this)) )

            ("quitat",
              CalCommand("quits and exits at simulation year specified",
                         boost::bind(&CalController::quit_at, this, _1)) )
            ("pauseat",
              CalCommand("pauses at simulation year specified",
                         boost::bind(&CalController::pause_at, this, _1)) )

            ("env",
              CalCommand("changes env module state",
                         boost::bind(&CalController::env_cmd, this, _1)) )
            ("bgc",
              CalCommand("changes bgc module state",
                         boost::bind(&CalController::bgc_cmd, this, _1)) )
            ("avln",
              CalCommand("changes available Nitrogen setting",
                         boost::bind(&CalController::avln_cmd, this, _1)) )
            ("dsb",
              CalCommand("changes dsb module state",
                         boost::bind(&CalController::dsb_cmd, this, _1)) )
            ("dsl",
              CalCommand("changes dsl module state",
                         boost::bind(&CalController::dsl_cmd, this, _1)) )
            ("dvm",
              CalCommand("changes dvm module state",
                         boost::bind(&CalController::dvm_cmd, this, _1)) )
            ("nfeed",
              CalCommand("changes nitrogen feedback setting",
                          boost::bind(&CalController::nfeed_cmd, this, _1)) )
            ("baseline",
              CalCommand("changes baseline setting",
                          boost::bind(&CalController::baseline_cmd, this, _1)) )
            ;

  BOOST_LOG_SEV(glg, debug) << "Set async wait on signals to PAUSE handler.";
  pause_sigs.async_wait( boost::bind(&CalController::pause_handler, this,
                                     boost::asio::placeholders::error,
                                     boost::asio::placeholders::signal_number));

  this->run_configuration =
      this->load_directives_from_file("config/calibration_directives.txt");

  if (!this->cohort_ptr) {
    BOOST_LOG_SEV(glg, err) << "Something is wrong and the Cohort pointer is null!";
  }

  BOOST_LOG_SEV(glg, debug) << "Done constructing a CalController.";
}


/** Trys to load a calibration directives file, returns empty object if it fails.

  The directives file, if present, should take this form (json, with comments):
  {
    "calibration_autorun_settings": {
      "quitat": 1100,
      "488": ["dsl on", "nfeed on", "dsb on"]
      "1000": ["dsb on"]
    }
  }
*/
Json::Value CalController::load_directives_from_file(
    const std::string& filename) {

  Json::Value v;

  if ( !(boost::filesystem::exists(filename)) ) {
    BOOST_LOG_SEV(glg, warn) << "Calibraiton directives file '"
                             << filename <<"' does not exist. "
                             << "Returning empty Json::Value.";
  } else {

    BOOST_LOG_SEV(glg, note) << "Parse file '"<< filename
                             << "' for calibration directives.";
    v = temutil::parse_control_file(filename);
  }

  BOOST_LOG_SEV(glg, debug) << v.toStyledString();

  return v["calibration_autorun_settings"];
}

/** Print the run_configuration data structure to std out. */
void CalController::print_directive_settings() {
  std::cout << "Calibration Directives" << std::endl;
  std::cout << "----------------------" << std::endl;
  std::cout << this->run_configuration.toStyledString() << std::endl;
}

/** Set the year to quit in the run_configuration data structure */
void CalController::quit_at(const std::string& s) {
  int year;
  try {
    year = boost::lexical_cast<int>(s);
    this->run_configuration["quitat"] = year;
    BOOST_LOG_SEV(glg, info) << "Setting the quitat year in CalController's "
                             << "run_configuration to " << year;

   } catch( const boost::bad_lexical_cast & ) {
    BOOST_LOG_SEV(glg, warn) << "Unable to convert '"<< s <<"' to valid "
                             << "integer for a quit-at year.";
  }
}

/** Set the year to pause in the run_configuration data structure */
void CalController::pause_at(const std::string& s) {
  int year;
  try {
    year = boost::lexical_cast<int>(s);
    this->run_configuration["pauseat"] = year;
    BOOST_LOG_SEV(glg, info) << "Set the pauseat year in CalController's "
                             << "run_configuration to " << year;

  } catch( const boost::bad_lexical_cast & ) {
    BOOST_LOG_SEV(glg, warn) << "Unable to convert '"<< s <<"' to valid "
                             << "integer for a pauseat year.";
  }
}

/** Look thru the run_configuration data structure and run any commands that
    are found by calling operate_on_directive_str(..).
*/
void CalController::run_config(int year, const std::string& stage) {

  typedef Json::Value::iterator JVIt;
  for (JVIt it = run_configuration.begin(); it != run_configuration.end(); ++it) {
    Json::Value key = it.key();
    Json::Value val = *it;

    if ("quitat" == key.asString()) {
      if (year == val.asInt()) {
        BOOST_LOG_SEV(glg, note) << "QUITTING because "<< year <<" set in "
                                 << "CalController's run_configuration data "
                                 << "structure.";
        exit(0);
      }
    }
    if ("pauseat" == key.asString()) {
      if (year == val.asInt()){
        BOOST_LOG_SEV(glg, note) << "PAUSING because year is equal to year in "
                                 << "CalController's run configuration data "
                                 << "structure.";
        this->control_loop();
      }
    }
    if (stage.compare("pre-run") == 0) {
      BOOST_LOG_SEV(glg, debug) << "In pre-run stage; ignoring calibraiton directives...";
    } else {

      if (boost::lexical_cast<string>(year) == key.asString()) {
        BOOST_LOG_SEV(glg, info) << "ITERATE over the directives in the value... "
                                 << "(which is an array of string commands)";

        for( Json::ValueIterator itr = val.begin(); itr != val.end(); itr++ ) {
          string directive  =  (*itr).asString();

          operate_on_directive_str(directive);

        }
      }

    } // end stage check...
  } // end for loop over json items
}

void CalController::auto_run(int simulation_year) {
  std::cout << "year: " << simulation_year << ". YEAH! auto-running!! \n";
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

      this->operate_on_directive_str(line);

    }
  }
}



/** Parse a string and carry out an operation if a valid operation is found.

    For example a string like this: "dsb on" would match one of the 
    (parameterized) commands that is setup in the constructor, so the 
    appropriate boost::bind function is called.
*/
void CalController::operate_on_directive_str(const std::string& line) {

  // Match non-paramererized command (maybe multiple words)
  if (this->cmd_map.count(line)) {
    BOOST_LOG_SEV(glg, info) << "Calling non-parameterized command.";
    this->cmd_map[line].executor(""); // send empty string to executor...

  // See if we can find a match of command token and parameters
  } else {

    // Parse string of commands and parameters, calling appropriate function.
    boost::tokenizer<> tokens(line);
    typedef boost::tokenizer<>::iterator BstTknIt;
    for (BstTknIt tkn_it=tokens.begin(); tkn_it!=tokens.end(); ++tkn_it) {
      std::string tkn = *tkn_it;

      if (this->cmd_map.count(tkn)) {

        BOOST_LOG_SEV(glg, debug) << "Found token '"<<tkn<<"' in the cmd_map.";

        // store the command, and bump the iterator forward
        std::string cmd = tkn;
        std::vector<std::string> params;
        ++tkn_it;

        BOOST_LOG_SEV(glg, debug) << "Looking for any additional command parameters...";
        if (tkn_it != tokens.end()) {

          // Accumulate any parameters for the command. Continue scanning for
          // parameters until the end of the input string is reached.
          for (BstTknIt param_it = tkn_it; param_it != tokens.end(); ++param_it) {
            params.push_back(*param_it);
          }
        }

        // Although some of the bound executors don't take any arguments,
        // we must provide enough arguments to match the signature in
        // the CalCommand structure. Use an empty string if the user
        // didn't provide anything.
        if (params.size() == 0) {
          params.push_back("");
        }

        BOOST_LOG_SEV(glg, note) << "Command token: '" << cmd
                                 << "'. Parameters: ["
                                 << temutil::vec2csv(params) << "]";

        BOOST_LOG_SEV(glg, info) << "NOTE: Only using 1st parameter. Others are"
                                 << "ignored for the time being.";

        this->cmd_map[cmd].executor(params.at(0));

        if (tkn_it == tokens.end()) {
          break;
        }

      } /* end token in map */
    } /* end token loop */
  } /* end else: match full-line */
}

/** The call back that is run when a registered signal is recieved and processed.
 * Technically, because of the async_wait, the may be run some time after the
 * signal is recieved, so it is really run when a recieved signal is processed.
 */
void CalController::pause_handler(const boost::system::error_code& error,
                                  int signal_number) {
  BOOST_LOG_SEV(glg, debug) << "In the CalController pause_handler";
  BOOST_LOG_SEV(glg, debug) << "Caught signal number: " << signal_number
                            << " Error(s): " << error;
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

/** Returns T/F indicating whether to pause after env warmup run or not.
* Allows the post warmup pause functionality to be set in the
* calibration_directives file by adding an entry like this:
*   {
*     ..,
*     "pwup": true //
*   }
*/
bool CalController::post_warmup_pause() {

  // look thru the run_configuration json object for the right key
  typedef Json::Value::iterator JVIt;
  for (JVIt it = run_configuration.begin(); it != run_configuration.end(); ++it) {
    Json::Value key = it.key();
    Json::Value val = *it;
    if ( "pwup" == key.asString() ) {
      return val.asBool();
    }
  }

  // post warm up pause parameter key not found. default to true/yes.
  return true;
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


void CalController::print_calparbgc() {
  BOOST_LOG_SEV(glg, note) << "Printing the 'calparbgc' parameters stored in "
                           << "the CohortLookup pointer...";
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

/** Define a wrapper so that all commands can reuse the try/catch and logging.

  Parameters are a "pointer to a member function", the module name (for the 
  log message), and the new setting string.

  Inspired from my (tbc) stack overflow question:
  http://stackoverflow.com/questions/30447878

*/
void CalController::cmd_wrapper(void (ModelData::*fn)(bool),
    const std::string& name, const std::string& s) {

  try {

    (this->cohort_ptr->md->*fn)(temutil::onoffstr2bool(s));

    BOOST_LOG_SEV(glg, note) << "CalController->cohort_ptr turned " << name
                             << " module/flag " << s;

  } catch (const std::runtime_error& e) {
    BOOST_LOG_SEV(glg, warn) << e.what();
  }

}

void CalController::env_cmd(const std::string& s) {
  cmd_wrapper(&ModelData::set_envmodule, "env", s);
}

void CalController::bgc_cmd(const std::string& s) {
  cmd_wrapper(&ModelData::set_bgcmodule, "bgc", s);
}

void CalController::avln_cmd(const std::string& s) {
  cmd_wrapper(&ModelData::set_avlnflg, "avln", s);
}

void CalController::dsb_cmd(const std::string& s) {
  cmd_wrapper(&ModelData::set_dsbmodule, "dsb", s);
}

void CalController::dsl_cmd(const std::string& s) {
  cmd_wrapper(&ModelData::set_dslmodule, "dsl", s);
}

void CalController::dvm_cmd(const std::string& s) {
  cmd_wrapper(&ModelData::set_dvmmodule, "dvm", s);
}

void CalController::nfeed_cmd(const std::string& s) {
  cmd_wrapper(&ModelData::set_nfeed, "nfeed", s);
}

void CalController::baseline_cmd(const std::string& s) {
  cmd_wrapper(&ModelData::set_baseline, "baseline", s);
}
