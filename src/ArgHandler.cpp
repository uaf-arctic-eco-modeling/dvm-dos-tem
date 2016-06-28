#include <json/reader.h>

#include "../include/ArgHandler.h"

#include "TEMLogger.h"
#include "TEMUtilityFunctions.h"

extern src::severity_logger< severity_level > glg;

ArgHandler::ArgHandler() {
	// handle defaults in the parse(..) and verify(..) functions
}
void ArgHandler::parse(int argc, char** argv) {
	desc.add_options()

    ("cal-mode,c", boost::program_options::bool_switch(&cal_mode),
     "Switch for calibration mode. When this flag is present, the program will "
     "be forced to run a single site and with '--loop-order=space-major'. The "
     "program will generate yearly and monthly '.json' files in your /tmp "
     " directory that are intended to be read by other programs or scripts.")

    ("pid-tag,u", boost::program_options::value<std::string>(&pid_tag)
      ->default_value(""),
      "Use the process ID (passed as an argmument) to tag the output cal json "
      "directories. Facilitates parallel runs, but may make the "
      "calibration-viewer.py more difficult to work with (must pass/set the "
      "PID tag so that the calibration-viewer.py knows where to find the json "
      "files.)")

    ("pre-run-yrs,p", boost::program_options::value<int>(&pre_run_yrs)
       ->default_value(10),
     "The number of 'pre-run' years.")

    ("max-eq,m", boost::program_options::value<int>(&max_eq)
       ->default_value(1000),
     "The maximum number of years to run in equlibrium stage.")

    ("sp-yrs,s", boost::program_options::value<int>(&sp_yrs)
       ->default_value(100),
     "The number of spinup years.")

    ("tr-yrs,t", boost::program_options::value<int>(&tr_yrs)
       ->default_value(0),
     "The number of years to run transient. Overrides config for testing.")

    ("sc-yrs,n", boost::program_options::value<int>(&sc_yrs)
       ->default_value(0),
     "The number of years to run scenario. Overrides config for testing.")

    ("loop-order,o",
     boost::program_options::value<std::string>(&loop_order)
       ->default_value("space-major"),
     "Which control loop is on the outside: 'space-major' or 'time-major'. For "
     "example 'space-major' means 'for each cohort, for each year'.")

    ("ctrl-file,f",
     boost::program_options::value<std::string>(&ctrl_file)
       ->default_value("config/config.js"),
     "choose a control file to use")

    ("log-level,l",
     boost::program_options::value<std::string>(&log_level)
       ->default_value("warn"),
     "Control the verbositiy of the console log statements. Choose one of "
     "the following: debug, info, note, warn, err, fatal.")

    ("log-scope",
     boost::program_options::value<std::string>(&log_scope)
       ->default_value("all"),
     "Control the scope of log messages: yearly, monthly, or daily. With a "
     "setting of M (monthly), messages within the monthly (and yearly) scope "
     "will be shown, but not messages within the daily scope. Values other "
     "than 'Y', 'M', 'D', or 'all' will be ignored. Scopes are determined by "
     "'boost log named scopes' set within the source code.")

    ("fpe,x", boost::program_options::bool_switch(&floating_point_exp),
     "Switch for enabling floating point exceptions. If present, the program "
     "will crash when NaN or Inf are generated.")

    ("help,h",
     boost::program_options::bool_switch(&help),
     "produces helps message, then quits")

//    ("foo,f",
//     po::value<std::std::string>()
//       ->implicit_value("")
//       ->zero_tokens()
//       ->notifier(&got_foo),
//     "foo description")

	;

	boost::program_options::store(
      boost::program_options::parse_command_line(argc, argv, desc), varmap);

	boost::program_options::notify(varmap);

}

/** Exit with non-zero value if there are any problems / conflicts with 
* command line args.
*/
void ArgHandler::verify() {

  BOOST_LOG_SEV(glg, warn) << "Argument validation/verification NOT fully implemented yet!";

  Json::Value controldata = temutil::parse_control_file(this->get_ctrl_file());

}


/** Print out command help.
 */
void ArgHandler::show_help(){
	std::cout << desc << std::endl;
}
