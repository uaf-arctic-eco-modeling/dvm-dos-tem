#include <json/reader.h>

#include "ArgHandler.h"

#include "TEMLogger.h"
#include "TEMUtilityFunctions.h"

extern src::severity_logger< severity_level > glg;

ArgHandler::ArgHandler() {
	// handle defaults in the parse(..) and verify(..) functions
}
void ArgHandler::parse(int argc, char** argv) {
	desc.add_options()

    ("cal-mode,c", boost::program_options::bool_switch(&cal_mode),
     "Switch for calibration mode. When this flag is preset, the program will "
     "be forced to run a single site and with --loop-order=space-major. The "
     "program will generate yearly and monthly '.json' files in your /tmp "
     " directory that are intended to be read by other programs or scripts.")

    ("max-eq,m", boost::program_options::value<int>(&max_eq)
       ->default_value(1000),
     "The maximum number of years to run in equlibrium stage.")

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

  Json::Value controldata = temutil::parse_control_file(this->get_ctrl_file());

  BOOST_LOG_SEV(glg, warn) << "Argument validation/verification NOT IMPLEMENTED YET!";
}


/** Print out command help.
 */
void ArgHandler::show_help(){
	std::cout << desc << std::endl;
}
