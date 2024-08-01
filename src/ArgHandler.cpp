#include <json/reader.h>

#include "../include/ArgHandler.h"

#include "../include/TEMLogger.h"
#include "../include/TEMUtilityFunctions.h"

extern src::severity_logger< severity_level > glg;

ArgHandler::ArgHandler() {
	// handle defaults in the parse(..) and verify(..) functions
}
void ArgHandler::parse(int argc, char** argv) {
	desc.add_options()

    ("cal-mode,c", boost::program_options::bool_switch(&cal_mode),
     "Switch for calibration mode. When this flag is present, the program will "
     "be forced to run a single site and with '--loop-order=space-major'. The "
     "program will generate yearly and monthly .json files (commonly somewhere "
     "in your /tmp directory so that the operating system will periodically clean "
     "them up). The location that the .json files will be written can be controlled "
     "by the caldata_tree_loc configuration setting.")

    ("force-cmt", boost::program_options::value<int>(&force_cmt)
     ->default_value(-1),
     "Force the model to run with a particular CMT number. Without this flag, "
     "the model determines which CMT to use for a grid cell based on the input "
     "vegetation map (specified in the config file). This flag allows the user to "
     "force a grid cell to run with a particular CMT regardless of what the input "
     "vegetation map holds. If multiple grid cells are being run then all cells "
     "will be forced to the same vegetation type." 
    )

    ("max-output-volume", boost::program_options::value<std::string>(&max_output_volume)
     ->default_value("0.75 GB"),
     "Sets the maximum allowed value for the estimated output volume. If the "
     "estimated output volume exceeds this value, the program will quit. Use "
     "the special value '-1' to indicate no cap on output volume. Use this at "
     "your own risk - you may end up filling your hard-drive!")

    ("no-output-cleanup", boost::program_options::bool_switch(&no_output_cleanup),
     "Do not clean the output directory at the beginning of a run. This might "
     "be useful when running dvmdostem under the control of an outside program "
     "such as PEcAn that makes assumptions about the presence of an output "
     "directory and may perform its own cleanup.")

    ("restart-run", boost::program_options::bool_switch(&restart_run),
     "Restart at the first stage with >0 years specified and "
     "do not overwrite the files needed for that.")

    ("inter-stage-pause", boost::program_options::bool_switch(&inter_stage_pause),
     "With this flag, (and when in calibration mode), the model will pause and "
     "wait for user input at the end of each run-stage.")

    ("last-n-json", boost::program_options::value<int>(&last_n_json_files)
     ->default_value(-1),
     "Only output the json files for the last N years. -1 indicates to output "
     "all years. This is useful for running with PEST, where we do need the "
     "json files (and calibration mode), but PEST only looks at the last year, "
     "so we can save a lot of effort and only write out the last file. Made "
     "this option configurable so that we can write out a number of files, in "
     "case we need to do some averaging over the last few years for PEST.")

    ("tar-caljson", boost::program_options::bool_switch(&tar_caljson),
     "When this flag is present, the calibration-json files will be bundled "
     "into a *-data.tar.gz archive at the end of each stage. The prefix for "
     "the archive will be a two letter code for the run-stage, (i.e. 'pr', "
     "'eq', 'sp', 'tr', or 'sc'). The resulting archive will be written to the "
     "location specified in the output_dir configuration setting.")

    ("archive-all-json", boost::program_options::bool_switch(&archive_all_json),
     "DEPRECATED! Prefer --tar-caljson. "
     "With this flag, the json files for every stage will be archived (at the "
     "end of the stage), into directory named for the stage, within the main "
     "json output directory location. Default behavior (without this flag) is "
     "that each stage overwrites the json files from the previous stage.")

    ("pid-tag,u", boost::program_options::value<std::string>(&pid_tag)
      ->default_value(""),
      "Use the process ID (passed as an argmument) to tag the output cal json "
      "directories. Facilitates parallel runs, but may make the "
      "calibration-viewer.py more difficult to work with (must pass/set the "
      "PID tag so that the calibration-viewer.py knows where to find the json "
      "files.)")

    ("pr-yrs,p", boost::program_options::value<int>(&pr_yrs)
       ->default_value(100),
     "Number of PRE RUN years to run.")

    ("eq-yrs,e", boost::program_options::value<int>(&eq_yrs)
       ->default_value(1000),
     "Number of EQUILIBRIUM years to run.")

    ("sp-yrs,s", boost::program_options::value<int>(&sp_yrs)
       ->default_value(100),
     "Number of SPINUP years to run.")

    ("tr-yrs,t", boost::program_options::value<int>(&tr_yrs)
       ->default_value(0),
     "Number of TRANSIENT years to run.")

    ("sc-yrs,n", boost::program_options::value<int>(&sc_yrs)
       ->default_value(0),
     "Number of SCENARIO years to run.")

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
     "Control the verbosity of the console log statements. Choose one of "
     "the following: debug, info, warn, monitor, fatal.")

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

    ("sha", boost::program_options::bool_switch(&print_sha),
     "Prints the SHA of the commit used to build this binary then exits")

    ("help,h",
     boost::program_options::bool_switch(&help),
     "Produces helps message, then quits")

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

  if ((this->pid_tag.compare("") != 0) && (!this->cal_mode)) {
    BOOST_LOG_SEV(glg, fatal) << "Invalid argument combination!: If you have specified a PID tag, you must also specify --cal-mode!";
    exit(-1);
  }

  if ( (this->inter_stage_pause) && (!this->cal_mode) ) {
    BOOST_LOG_SEV(glg, warn) << "Invalid argument combination!: --inter-stage-pause is not effective without --cal-mode!";
  }

  if (this->force_cmt >= 0) {
    BOOST_LOG_SEV(glg, warn) << "Forcing cmt number to " << this->force_cmt << "!";
  }
  // Check that the value for --force-cmt is present in all input parameter files?

}


/** Print out command help.
 */
void ArgHandler::show_help(){
	std::cout << desc << std::endl;
}
