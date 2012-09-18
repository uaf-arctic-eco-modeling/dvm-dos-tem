#include "ArgHandler.h"


ArgHandler::ArgHandler() {
	//boost::filesystem::path p = boost::filesystem::initial_path();
	mode = "siterun";

	if (mode == "siterun") {
		ctrlfile = "config/controlfile_site.txt";
		chtid = "1";
		regrunmode = ""; // meaningless in this context
	} else if (mode == "regnrun") {
		ctrlfile = "config/controlfile_regn.txt";
		chtid = ""; // meaningless in this context
		regrunmode = "regner2"; 
	}

	help = false;
	version = false;
	debug = false;

}
void ArgHandler::parse(int argc, char** argv) {
	desc.add_options()
		("mode,m", boost::program_options::value<string>(), "change mode between siterun and regnrun")
		("ctrlfile,cf", "choose a control file to use")
		("chtid,cid", "choose a specific cohort to run")
		("regrunmode,rrm", "choose spatial or temporal running mode")
		("help,h", "produces helps message")
		("version,v", "show the version information")
		("debug,d", "enable debug mode")
	;

	boost::program_options::store(boost::program_options::parse_command_line(argc, argv, desc), varmap);
	boost::program_options::notify(varmap);

	if (varmap.count("mode")) {
    	mode = varmap["mode"].as<string>();
	}

	if (varmap.count("ctrlfile")) {
		ctrlfile = varmap["ctrlfile"].as<string>();
	}

	if (varmap.count("chtid")) {
		chtid = varmap["chtid"].as<string>();
	}
	if (varmap.count("regrunmode")) {
		regrunmode = varmap["regrunmode"].as<string>();
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
