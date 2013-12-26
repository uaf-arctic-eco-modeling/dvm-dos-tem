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


#include "ArgHandler.h"
#include "TEMLogger.h"
#include "assembler/Runner.h"

BOOST_LOG_INLINE_GLOBAL_LOGGER_INIT(my_general_logger, severity_channel_logger_t) {
  return severity_channel_logger_t(keywords::channel = "GENER");
}
BOOST_LOG_INLINE_GLOBAL_LOGGER_INIT(my_cal_logger, severity_channel_logger_t) {
  return severity_channel_logger_t(keywords::channel = "CALIB");
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
  
  HELPME();
  //init_logging_TBC();
  severity_channel_logger_t& glg = my_general_logger::get();
  severity_channel_logger_t& clg = my_cal_logger::get();

//  if (args->getLogging()){
//    include_turn_on_and_setup_all_logging();
//  }

//  if (args->getLogLevel()) {
//    set_global_log_level();
//  }

//  if (args->getCalLogging()) {
//    set_filters_for_calibration_logging();    
//  }
  
  init_console_log_sink();
  init_console_log_filters(args->getLogLevel(), args->getCalibLog());
  
  BOOST_LOG_SEV(glg, debug) << "A debug message to the general logger...";
  BOOST_LOG_SEV(glg, info) << "info, general"; 
  BOOST_LOG_SEV(glg, note) << "note, general"; 
  BOOST_LOG_SEV(glg, warn) << "warn, genearl"; 
  BOOST_LOG_SEV(glg, rterror) << "error, general"; 
  BOOST_LOG_SEV(glg, fatal) << "fatal, general"; 

  BOOST_LOG_SEV(clg, debug) << "debug, calib"; 
  BOOST_LOG_SEV(clg, info) << "info, calib"; 
  BOOST_LOG_SEV(clg, note) << "note, calib";
  BOOST_LOG_SEV(clg, warn) << "warn, calib"; 
  BOOST_LOG_SEV(clg, rterror) << "error, calib"; 
  BOOST_LOG_SEV(clg, fatal) << "fatal, calib"; 


	setvbuf(stdout, NULL, _IONBF, 0);
	setvbuf(stderr, NULL, _IONBF, 0);

	if (args->getMode() == "siterun") {
		time_t stime;
		time_t etime;
		stime=time(0);
    BOOST_LOG_SEV(glg, info) << "Running dvm-dos-tem in siterun mode. Start @ " 
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
