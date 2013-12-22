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
#include <iomanip>

#include <boost/date_time/posix_time/ptime.hpp>

#include <boost/log/core.hpp>
#include <boost/log/trivial.hpp>
#include <boost/log/sources/record_ostream.hpp>
#include <boost/log/sources/logger.hpp>
#include <boost/log/sources/global_logger_storage.hpp>
#include <boost/log/sources/severity_feature.hpp>
#include <boost/log/sources/severity_logger.hpp>
#include <boost/log/sources/severity_channel_logger.hpp>
#include <boost/log/expressions.hpp>
#include <boost/log/attributes.hpp>
#include <boost/log/support/date_time.hpp>
#include <boost/log/utility/setup/common_attributes.hpp>
#include <boost/log/utility/formatting_ostream.hpp>
#include <boost/log/utility/setup/console.hpp>


#include "assembler/Runner.h"
#include "ArgHandler.h"

using namespace std;
namespace logging = boost::log;
namespace src = boost::log::sources;
namespace attrs = boost::log::attributes;
namespace keywords = boost::log::keywords;
namespace expr = boost::log::expressions;
namespace sinks = boost::log::sinks;

enum general_severity_level {
  debug,
  info,
  note,
  warn,
  error,
  fatal
};

// The operator is used for regular stream formatting
// i.e. printing the flag instead of the enum value..
std::ostream& operator<< (std::ostream& strm, general_severity_level level) {
    static const char* strings[] = { 
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

BOOST_LOG_ATTRIBUTE_KEYWORD(severity, "Severity", general_severity_level)
BOOST_LOG_ATTRIBUTE_KEYWORD(channel, "Channel", std::string)
BOOST_LOG_ATTRIBUTE_KEYWORD(timestamp, "TimeStamp", boost::posix_time::ptime)

typedef src::severity_channel_logger< 
    general_severity_level, 
    std::string 
  > sev_chnl_logger_t;

BOOST_LOG_INLINE_GLOBAL_LOGGER_INIT(g_lg, sev_chnl_logger_t) {
  // Specify the channel name on construction...
  return sev_chnl_logger_t(keywords::channel = "GENER");
}
BOOST_LOG_INLINE_GLOBAL_LOGGER_INIT(c_lg, sev_chnl_logger_t) {
  // Specify the channel name on construction...
  return sev_chnl_logger_t(keywords::channel = "CALIB");
}

void init_console_log_filters(std::string gen_settings, std::string cal_settings){
  logging::core::get()->set_filter(
    severity >= warn || (expr::has_attr(channel) && channel == "CALIB")
  );
}

void init_console_log_sink(){

  logging::add_common_attributes();

  logging::add_console_log (
    std::clog,
    keywords::format = (
      expr::stream
        // works, just don't need timestamp right now...        
        //<< expr::format_date_time< boost::posix_time::ptime >("TimeStamp", "%Y-%m-%d %H:%M:%S ")
        << "(" << channel << ") "
        << "[" << severity << "] " << expr::smessage
    )
  );
  
  // MAYBE USEFUL?
  //<< std::setw(3) << std::setfill(' ')
}

ArgHandler* args = new ArgHandler();

int main(int argc, char* argv[]){
  args->parse(argc, argv);
	if (args->getHelp()){
		args->showHelp();
		return 0;
	}

  init_console_log_sink();
  init_console_log_filters(args->getLogLevel(), args->getCalibLog());

  BOOST_LOG_SEV(g_lg::get(), debug) << "A debug message to the general logger...";
  BOOST_LOG_SEV(g_lg::get(), info) << "info, general"; 
  BOOST_LOG_SEV(g_lg::get(), note) << "note, general"; 
  BOOST_LOG_SEV(g_lg::get(), warn) << "warn, genearl"; 
  BOOST_LOG_SEV(g_lg::get(), error) << "error, general"; 
  BOOST_LOG_SEV(g_lg::get(), fatal) << "fatal, general"; 

  BOOST_LOG_SEV(c_lg::get(), debug) << "debug, calib"; 
  BOOST_LOG_SEV(c_lg::get(), info) << "info, calib"; 
  BOOST_LOG_SEV(c_lg::get(), note) << "note, calib"; 
  BOOST_LOG_SEV(c_lg::get(), warn) << "warn, calib"; 
  BOOST_LOG_SEV(c_lg::get(), error) << "error, calib"; 
  BOOST_LOG_SEV(c_lg::get(), fatal) << "fatal, calib"; 


	setvbuf(stdout, NULL, _IONBF, 0);
	setvbuf(stderr, NULL, _IONBF, 0);

	if (args->getMode() == "siterun") {
		time_t stime;
		time_t etime;
		stime=time(0);
    BOOST_LOG_SEV(g_lg::get(), info) << "Running dvm-dos-tem in siterun mode. Start @ " 
                            << ctime(&stime);

		string controlfile = args->getCtrlfile();
		string chtid = args->getChtid();

		Runner siter;

		siter.chtid = atoi(chtid.c_str());

		siter.initInput(controlfile, "siter");

		siter.initOutput();

 		siter.setupData();

 		siter.setupIDs();

    //BOOST_LOG_SEV(clg, daily) << "Much  be a calibration logger daily level...";
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
