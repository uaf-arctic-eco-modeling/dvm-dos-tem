#ifndef _ARGHANDLER_H
#define _ARGHANDLER_H
#include <iostream>
#include <string>

#include <boost/filesystem.hpp>
#include <boost/program_options.hpp>

using namespace std;

class ArgHandler {
	boost::program_options::options_description desc;
	boost::program_options::variables_map varmap;
  string calibrationmode;	
  string loglevel;
  string mode;
	string ctrlfile;
	string chtid;
	string regrunmode;

  string env;
  string bgc;
  string dvm;

  bool help;
	bool version;
	bool debug;

public:
	ArgHandler();
	void parse(int argc, char** argv);
	void verify();
	void showHelp();
	
  string getEnv() const;
  string getBgc() const;
  string getDvm() const;

  string getCalibrationMode();
  string getLogLevel();
	string getMode();
	string getCtrlfile();
	string getChtid();
	string getRegrunmode(); // spatial or temporal mode switch w/in regnrun mode
	
	inline const bool getDebug(){return debug;};
	inline const bool getHelp(){return help;};
	inline const bool getVersion(){return version;};
};
#endif /* _ARGHANDLER_H */