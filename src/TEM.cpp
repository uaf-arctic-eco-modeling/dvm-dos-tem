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
#include <set>

#include <boost/asio/signal_set.hpp>
#include <boost/thread.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/bind.hpp>
#include <boost/asio.hpp>


#include "ArgHandler.h"
#include "TEMLogger.h"
#include "assembler/Runner.h"

BOOST_LOG_INLINE_GLOBAL_LOGGER_INIT(my_general_logger, severity_channel_logger_t) {
  return severity_channel_logger_t(keywords::channel = "GENER");
}
BOOST_LOG_INLINE_GLOBAL_LOGGER_INIT(my_cal_logger, severity_channel_logger_t) {
  return severity_channel_logger_t(keywords::channel = "CALIB");
}

// forward declaration of various free fucntions...

// DEFINE FREE FUNCTIIONS...

ArgHandler* args = new ArgHandler();

int main(int argc, char* argv[]){
  args->parse(argc, argv);
	if (args->getHelp()){
		args->showHelp();
		return 0;
	}
  args->verify();

  std::cout << "Setting up Logging...\n";

  setup_console_log_sink();

  set_log_severity_level(args->getLogLevel());  

  // get handles for each of the global loggers...
  severity_channel_logger_t& glg = my_general_logger::get();
  severity_channel_logger_t& clg = my_cal_logger::get();


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

    args->getEnv(),
    siter.modeldata_module_settings_from_args(*args);
    
    if (args->getCalibrationMode() == "on") {
      BOOST_LOG_SEV(glg, info) << "Turning CalibrationMode on in Runner (siter).";
      siter.setCalibrationMode(true);
    } else {
      BOOST_LOG_SEV(glg, info) << "Running in extrapolation mode.";
    }

    siter.chtid = atoi(chtid.c_str());

    siter.initInput(controlfile, "siter");

    siter.initOutput();

    siter.setupData();

    siter.setupIDs();

    siter.runmode1();
  
    etime=time(0);

  } else if (args->getMode() == "regnrun") {

    time_t stime;
    time_t etime;
    stime=time(0);
    BOOST_LOG_SEV(glg, info) << "Running dvm-dos-tem in regional mode. Start @ "
                              << ctime(&stime);

    string controlfile = args->getCtrlfile();
    string runmode = args->getRegrunmode();

    Runner regner;

    regner.initInput(controlfile, runmode);

    regner.initOutput();

    regner.setupData();

    regner.setupIDs();

    if (runmode.compare("regner1")==0) {
      BOOST_LOG_SEV(glg, debug) << "Running in regner1...(runmode2)";
      regner.runmode2();
    } else if (runmode.compare("regner2")==0){
      BOOST_LOG_SEV(glg, debug) << "Running in regner2...(runmode3)";
      regner.runmode3();
    } else {
      BOOST_LOG_SEV(glg, fatal) << "Invalid runmode...quitting.";
      exit(-1);
    }

    etime = time(0);
    BOOST_LOG_SEV(glg, info) << "Done running dvm-dos-tem regionally " 
                              << "(" << ctime(&etime) << ").";
    BOOST_LOG_SEV(glg, info) << "total seconds: " << difftime(etime, stime);
  }
  return 0;
};
