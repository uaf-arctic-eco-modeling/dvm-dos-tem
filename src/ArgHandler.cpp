#include "ArgHandler.h"

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
     "the following: debug, info, note, warn, err, fatal."
    )

    ("cohort-id,n",
     boost::program_options::value<int>(&cohort_id)
       ->default_value(1),
     "choose a specific cohort to run. TODO: must be a number?? must be in runchtlist.nc?? implies single-site?? Allows slicing? or other specification of more than one cohort?")

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

void ArgHandler::verify() {
  // The regional "run mode"...loop order??
  std::cout << "Verification reuimentary - needs more programming help!\n";
  if (mode.compare("cal-mode") == 0) {
    if ( true ) {
      // pass, all ok
    } else {
      std::cout << "Invalid option. Quitting.\n";
      exit(-1);
    }
  }  
}


/** Print out command help.
 */
void ArgHandler::show_help(){
	std::cout << desc << std::endl;
}
