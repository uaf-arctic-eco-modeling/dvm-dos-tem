#include "ArgHandler.h"


ArgHandler::ArgHandler(){
	//boost::filesystem::path p = boost::filesystem::initial_path();
	mode = "siterun";
	debug = false;
	help = false;
	version = false;

}
void ArgHandler::parse(int argc, char** argv){
	desc.add_options()
		("mode,m", boost::program_options::value<string>(), "change mode between siterun and regnrun")
		("help,h", "produces helps message")
		("version,v", "show the version information")
		("debug,d", "enable debug mode")
	;

	boost::program_options::store(boost::program_options::parse_command_line(argc, argv, desc), varmap);
	boost::program_options::notify(varmap);

	if (varmap.count("help")){
		help = true;
	}
	if (varmap.count("debug")){
		debug = true;
	}

	if (varmap.count("mode")){
        	mode = varmap["mode"].as<string>();
	}
}
string ArgHandler::getMode(){
	return mode;
}
void ArgHandler::showHelp(){
/**
 * Print out command help
 */
	//std::cout << desc << std::endl;
}
