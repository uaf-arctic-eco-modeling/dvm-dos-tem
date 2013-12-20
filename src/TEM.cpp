/**
 *  TEM.cpp
 *  main program for running DVM-DOS-TEM
 *  
 *  It runs at 3 run-mods:
 *      (1) site-specific
 *      (2) regional - time series
 * 		(3) regional - spatially (not yet available)
 * 
 * Authors: Shuhua Yi - the original codes
 * 		    Fengming Yuan - re-designing and re-coding for (1) easily code managing;
 *                                        (2) java interface developing for calibration;
 *                                        (3) stand-alone application of TEM (java-c++)
 *                                        (4) inputs/outputs using netcdf format, have to be modified
 *                                        to fix memory-leaks
 *                                        (5) fix the snow/soil thermal/hydraulic algorithms
 *                                        (6) DVM coupled
 * 			Tobey Carman - modifications and maintenance
 *            1) update application entry point with boost command line arg. handling.
 *
 * Affilation: Spatial Ecology Lab, University of Alaska Fairbanks 
 *
 * started: 11/01/2010
 * last modified: 09/18/2012
*/

#include <string>
#include <iostream>
#include <fstream>
#include <sstream>
#include <ctime>
#include <cstdlib>
#include <exception>
#include <map>


//#include <boost/log/expressions.hpp>
//#include <boost/log/sources/severity_logger.hpp>
#include <boost/log/sources/record_ostream.hpp>
#include <boost/log/utility/formatting_ostream.hpp>
//#include <boost/log/utility/manipulators/to_log.hpp>
#include <boost/log/utility/setup/console.hpp>
//#include <boost/log/utility/setup/common_attributes.hpp>



#include <boost/log/core.hpp>
#include <boost/log/trivial.hpp>
#include <boost/log/expressions.hpp>
#include <boost/log/attributes.hpp>
//#include <boost/move/utility.hpp>
#include <boost/log/sources/logger.hpp>
//#include <boost/log/sources/record_ostream.hpp>
#include <boost/log/sources/global_logger_storage.hpp>
//#include <boost/log/utility/setup/file.hpp>
#include <boost/log/utility/setup/common_attributes.hpp>

#include <boost/log/sources/severity_feature.hpp>
#include <boost/log/sources/severity_logger.hpp>

#include "assembler/Runner.h"
#include "ArgHandler.h"

using namespace std;
namespace logging = boost::log;
namespace src = boost::log::sources;
namespace attrs = boost::log::attributes;
namespace keywords = boost::log::keywords;
namespace expr = boost::log::expressions;

enum general_severity_level {
  debug,
  info,
  note,
  warn,
  error,
  fatal
};
// The operator is used for regular stream formatting
std::ostream& operator<< (std::ostream& strm, general_severity_level level)
{
    static const char* strings[] =
    {
        "debug",
        "info",
        "note",
        "warn",
        "error",
        "fatal"
    };

    if (static_cast< std::size_t >(level) < sizeof(strings) / sizeof(*strings))
        strm << strings[level];
    else
        strm << static_cast< int >(level);

    return strm;
}



enum calibration_severity_level {
  daily,
  monthly,
  yearly
};
BOOST_LOG_INLINE_GLOBAL_LOGGER_DEFAULT(general_logger, src::severity_logger< general_severity_level >) //{
  //src::severity_logger< > glg;
  //glg.add_attribute();
  //return glg;
//}
BOOST_LOG_INLINE_GLOBAL_LOGGER_DEFAULT(calibration_logger, src::severity_logger< >)

void init_general_logging(std::string lglevel) {
  logging::add_console_log
  (
     std::clog,
     // This makes the sink to write log records that look like this:
     // 1: <NORM> A normal severity message
     // 2: <ERRR> An error severity message
     keywords::format =
     (
         expr::stream
             //<< expr::attr< unsigned int >("LineID")
             << ": <" << expr::attr< general_severity_level >("Severity")
             << "> " << expr::smessage
     )
  );


  // Setup the a GLOBAL general logger
  src::severity_logger< general_severity_level > glg = general_logger::get();
  //logging::add_common_attributes();  
  BOOST_LOG_SEV(glg, debug) << "This would be a general logger, debug level...";
  BOOST_LOG_SEV(glg, info) << "This would be a general logger, info level...";
  BOOST_LOG_SEV(glg, note) << "This would be a general logger, note level...";
  BOOST_LOG_SEV(glg, warn) << "This would be a general logger, warn level...";
}

void init_calibration_logging(std::string cal_logging) {
  src::severity_logger< >& clg = calibration_logger::get();  
  BOOST_LOG_SEV(clg, daily) << "This would be a calibration logger, daily level...";
  BOOST_LOG_SEV(clg, monthly) << "This would be a calibraiton logger, monthly level...";
}

ArgHandler* args = new ArgHandler();

int main(int argc, char* argv[]){
	//BOOST_LOG_TRIVIAL(trace) << "Starting dvm-dos-tem...";
  //BOOST_LOG_TRIVIAL(trace) << "Parsing command line args...";
  args->parse(argc, argv);
	if (args->getHelp()){
		args->showHelp();
		return 0;
	}

  //BOOST_LOG_TRIVIAL(trace) << "Done parsing command line args...";
  //BOOST_LOG_TRIVIAL(trace) << "Setting up the logging level filter...";

  init_general_logging(args->getLogLevel());
  init_calibration_logging(args->getCalibLog());

  // Setup the a GLOBAL general logger
  src::severity_logger< general_severity_level > glg = general_logger::get();
  //logging::add_common_attributes();  
  BOOST_LOG_SEV(glg, debug) << "This would be a general logger, debug level...";
  BOOST_LOG_SEV(glg, info) << "This would be a general logger, info level...";



  //BOOST_LOG_SEV(glg, trace) << "This would be a general logger, trace level...";
  //BOOST_LOG_SEV(clg, daily) << "This would be a calibration logger daily level...";
  //BOOST_LOG_SEV(clg, monthly) << "This would be a calibration logger, monthly level...";

	setvbuf(stdout, NULL, _IONBF, 0);
	setvbuf(stderr, NULL, _IONBF, 0);

	if (args->getMode() == "siterun") {
		time_t stime;
		time_t etime;
		stime=time(0);
    //BOOST_LOG_TRIVIAL(info) << "Running dvm-dos-tem in siterun mode. Start @ " 
    //                        << ctime(&stime);

		string controlfile = args->getCtrlfile();
		string chtid = args->getChtid();

		Runner siter;

		siter.chtid = atoi(chtid.c_str());

		siter.initInput(controlfile, "siter");

		siter.initOutput();

 		siter.setupData();

 		siter.setupIDs();

 		siter.runmode1();
 
 		etime=time(0);

    //BOOST_LOG_TRIVIAL(info) << "Done running dvm-dos-tem in siterun mode. Finish @ " 
    //                       << ctime(&etime);
    //BOOST_LOG_TRIVIAL(info) << "Total time (secs): " << difftime(etime, stime);
    
  } else if (args->getMode() == "regnrun") {

		time_t stime;
		time_t etime;
		stime=time(0);
		cout <<"run TEM regionally - start @"<<ctime(&stime)<<"\n";

		string controlfile = args->getCtrlfile();
		string runmode = args->getRegrunmode();

		Runner regner;

		regner.initInput(controlfile, runmode);

		regner.initOutput();

		regner.setupData();

		regner.setupIDs();

 		if (runmode.compare("regner1")==0) {
 			regner.runmode2();
 		} else if (runmode.compare("regner2")==0){
 			regner.runmode3();
		} else {

			// Should move this to the ArgHandler class.
			cout <<"run-mode for TEM regional run must be: \n";
			cout <<" EITHER 'regner1' OR 'regner2' \n";
			exit(-1);
		}

		etime=time(0);
		cout <<"run TEM regionally - done @"<<ctime(&etime)<<"\n";
		cout <<"total seconds: "<<difftime(etime, stime)<<"\n";

	}
	
	return 0;

};
