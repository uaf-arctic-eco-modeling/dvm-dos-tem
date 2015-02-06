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

    ("loop-order,o",
     boost::program_options::value<std::string>(&loop_order)
       ->default_value("space-major"),
     "Which control loop is on the outside: 'space-major' or 'time-major'. For "
     "example 'space-major' means 'for each cohort, for each year'.")

    ("ctrl-file,f",
     boost::program_options::value<std::string>(&ctrl_file)
       ->default_value("config/controlfile_site.txt"),
     "choose a control file to use")

    ("log-level,l",
     boost::program_options::value<std::string>(&log_level)
       ->default_value("warn"),
     "Control the verbositiy of the console log statements. Choose one of "
     "the following: debug, info, note, warn, err, fatal.")

    ("cohort-id,n",
     boost::program_options::value<int>(&cohort_id)
       ->default_value(1),
     "choose a specific cohort to run. TODO: must be a number?? must be in runchtlist.nc?? implies single-site?? Allows slicing? or other specification of more than one cohort?")
    // Is this made obsolete by the idea of a run-mask??
    // If you want a different cohoert, just supply a differnet mask?
    //"Zero based index, starting from upper left corner of run-mask, rows "
    //"first. I.e. if the run mask is 
  
    ("new-style,",
     boost::program_options::bool_switch(&new_style),
     "Run the model under the new control and I/O structure.")

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

  std::string m = controldata["general"]["runmode"].asString();
  if ( (m == "multi") && this->get_cal_mode() ) {
    BOOST_LOG_SEV(glg, fatal) << "Can't use --cal-mode with a multi-site run. "
                              << "Please specify a different (single site) "
                              << "control file.";
    exit(-1);
  }
  if ( (m == "single") && (this->get_loop_order() == "time-major") ) {
    BOOST_LOG_SEV(glg, fatal) << "Can't use --loop-order=time-major for a "
                              << "single site run. Change loop order or "
                              << "specify a different control file.";
    exit(-1);
  }


  BOOST_LOG_SEV(glg, note) << "Command line arguments all OK.";
}


/** Print out command help.
 */
void ArgHandler::show_help(){
	std::cout << desc << std::endl;
}
