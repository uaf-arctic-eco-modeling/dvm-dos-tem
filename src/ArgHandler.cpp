#include "ArgHandler.h"

ArgHandler::ArgHandler() {
	// handle defaults in the parse(..) and verify(..) functions
}
void ArgHandler::parse(int argc, char** argv) {
	desc.add_options()
 
    /*
    --dsl on
    --dsb on
    --friderived on

    --nfeed on
    --avlnflg on
    --baseline on
    */
    ("env", boost::program_options::value<string>(&env)->default_value("on"),
     "Turn the environmental module on or off."
    )
    ("bgc", boost::program_options::value<string>(&bgc)->default_value("on"),
     "Turn the biogeochemical module on or off."
    )
    ("dvm", boost::program_options::value<string>(&dvm)->default_value("on"),
     "Turn the dynamic vegetation module on or off."
    )
    ("calibrationmode", boost::program_options::value<string>(&calibrationmode)->default_value("off"),
     "(NOT IMPLEMENTED) whether or not the calibration module is on...? "
     "list of strings for modules to calibrate?"
    )
    ("loglevel,l", boost::program_options::value<string>(&loglevel)->default_value("trace"), 
     "the level above which all log messages will be printed. Here are the "
     "choices: trace, debug, info, warning, error, fatal."
    )
		("mode,m", boost::program_options::value<string>(&mode)->default_value("siterun"),"change mode between siterun and regnrun")
		("control-file,f", boost::program_options::value<string>(&ctrlfile)->default_value("config/controlfile_site.txt"), "choose a control file to use")
		("cohort-id,c", boost::program_options::value<string>(&chtid)->default_value("1"), "choose a specific cohort to run")
		("space-time-config,s", boost::program_options::value<string>(), "choose spatial or temporal running mode")
		("help,h", "produces helps message")
		("version,v", "(NOT IMPLEMENTED)show the version information")
		("debug,d", "(NOT IMPLEMENTED) enable debug mode")
	;

	boost::program_options::store(boost::program_options::parse_command_line(argc, argv, desc), varmap);
	boost::program_options::notify(varmap);

  if (varmap.count("env")) {
    env = varmap["env"].as<string>();
  }
  if (varmap.count("bgc")) {
    bgc = varmap["bgc"].as<string>();
  }
  if (varmap.count("dvm")) {
    dvm = varmap["dvm"].as<string>();
  }
  
	if (varmap.count("cohort-id")) {
		chtid = varmap["cohort-id"].as<string>();
	}
	
	if (varmap.count("space-time-config")) {
		regrunmode = varmap["space-time-config"].as<string>();
	}

	if (varmap.count("help")) {
		help = true;
	}

	if (varmap.count("version")) {
		version = true;
	}

	if (varmap.count("debug")) {
		debug = true;
	}
}

void ArgHandler::verify() {
  // The regional "run mode"...loop order??
  if (mode.compare("regnrun") == 0) {
  if ( (regrunmode.compare("regner1") == 0) || 
       (regrunmode.compare("regner2") == 0) ) {
    // pass, all ok
  } else {
    std::cout << "Invalid option (regrunmode). Quitting.\n";
    exit(-1);
  }
}  
}

string ArgHandler::getEnv() const {
  return env;
}
string ArgHandler::getBgc() const {
  return bgc;
}
string ArgHandler::getDvm() const {
  return dvm;
}
string ArgHandler::getCalibrationMode(){
  return calibrationmode;
}
string ArgHandler::getLogLevel(){
	return loglevel;
}
string ArgHandler::getMode(){
	return mode;
}

string ArgHandler::getCtrlfile(){
	return ctrlfile;
}

string ArgHandler::getChtid(){
	return chtid;
}

string ArgHandler::getRegrunmode(){
	return regrunmode;
}

void ArgHandler::showHelp(){
/**
 * Print out command help
 */
	std::cout << desc << std::endl;
}
