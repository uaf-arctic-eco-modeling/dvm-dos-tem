#include "ArgHandler.h"


ArgHandler::ArgHandler() {
	// handle defaults in the parse(..) and verify(..) functions
}
void ArgHandler::parse(int argc, char** argv) {
	desc.add_options()
		("mode,m", boost::program_options::value<string>(&mode)->default_value("siterun"),"change mode between siterun and regnrun")
		("control-file,f", boost::program_options::value<string>(&ctrlfile)->default_value("config/controlfile_site.txt"), "choose a control file to use")
		("cohort-id,c", boost::program_options::value<string>(&chtid)->default_value("1"), "choose a specific cohort to run")
		("space-time-config,s", boost::program_options::value<string>(), "choose spatial or temporal running mode")
		("help,h", "produces helps message")
		("version,v", "show the version information")
		("debug,d", "enable debug mode")
	;

	boost::program_options::store(boost::program_options::parse_command_line(argc, argv, desc), varmap);
	boost::program_options::notify(varmap);

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

	verify();

}

void ArgHandler::verify() {
	std::cout << "Could/should do some option verification here...?\n";
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
