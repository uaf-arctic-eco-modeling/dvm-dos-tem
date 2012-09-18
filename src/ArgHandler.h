#include <iostream>
#include <string>

// using "" because I am using tobey-specific custom install paths right now
#include "boost/filesystem.hpp"
#include "boost/program_options.hpp"

using namespace std;

class ArgHandler {
	boost::program_options::options_description desc;
	boost::program_options::variables_map varmap;
	string mode;
	string ctrlfile;
	string chtid;
	string regrunmode;
	bool help;
	bool version;
	bool debug;

public:
	ArgHandler();
	void parse(int argc, char** argv);

	void showHelp();
	
	string getMode();
	string getCtrlfile();
	string getChtid();
	string getRegrunmode(); // spatial or temporal mode switch w/in regnrun mode
	
	inline const bool getDebug(){return debug;};
	inline const bool getHelp(){return help;};
	inline const bool getVersion(){return version;};
};
