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
void quit_handler(const boost::system::error_code&,
                  boost::shared_ptr< boost::asio::io_service >);

void pause_handler(const boost::system::error_code&,
                      boost::shared_ptr< boost::asio::io_service >);

void calibration_worker( boost::shared_ptr< boost::asio::io_service > );



// DEFINE FREE FUNCTIIONS...
void quit_handler(const boost::system::error_code& error,
                  boost::shared_ptr< boost::asio::io_service > io_service ){
  severity_channel_logger_t& clg = my_cal_logger::get();
  BOOST_LOG_SEV(clg, info) << "Running the quit signal handler...";
  BOOST_LOG_SEV(clg, info) << "Stopping the io_service.";
  io_service->stop();

  BOOST_LOG_SEV(clg, debug) << "Quitting. Exit with -1.";
  exit(-1);
}

/** The signal handler that will pause the calibration */
void pause_handler( const boost::system::error_code& error,
                    boost::shared_ptr< boost::asio::io_service > io_service ){

  severity_channel_logger_t& clg = my_cal_logger::get();
  BOOST_LOG_SEV(clg, info) << "Caught signal!"; 
  BOOST_LOG_SEV(clg, info) << "Running pause handler."; ;
  
  std::string continueCommand = "c";
  std::string reloadCommand = "r";
  std::string quitCommand = "q";

  std::set<std::string> validCommands;
  validCommands.insert(continueCommand);
  validCommands.insert(reloadCommand);
  validCommands.insert(quitCommand);

  std::string fullMenu = "\n"
                         "--------- Calibration Controller -------------\n"
                         "Enter one of the following options:\n"
                         "q - quit\n"
                         "c - continue simulation\n"
                         "r - reload config files\n";
  
  BOOST_LOG_SEV(clg, info) << fullMenu ; 
  
  std::string ui = "";
  
  while (!(validCommands.count(ui))) {
    std::cout << "What do you want to do now?> ";
    std::getline(std::cin, ui);
    std::cin.clear();
  }
  
  BOOST_LOG_SEV(clg, info) << "Got some good user input: " << ui; 
  BOOST_LOG_SEV(clg, info) << "Now should call the appropriate function...";
  
  BOOST_LOG_SEV(clg, info) << "Done in Handler...";
}

/** A seperate function to run the model. */
void calibration_worker( ) {

  // get handles for each of global loggers
  severity_channel_logger_t& clg = my_cal_logger::get();

  BOOST_LOG_SEV(clg, info) << "Start loop over cohorts, years, months.";

  
  BOOST_LOG_SEV(clg, info) << "Make shared pointers to an io_service";
  boost::shared_ptr< boost::asio::io_service > io_service(
    new boost::asio::io_service    
  );

  BOOST_LOG_SEV(clg, debug) << "Define a signal set...";  
  boost::asio::signal_set signals(*io_service, SIGINT, SIGTERM);

  BOOST_LOG_SEV(clg, debug) <<   "Set async wait on signals to PAUSE handler.";
  signals.async_wait(
    boost::bind(pause_handler, boost::asio::placeholders::error, io_service) );

  for(int cohort = 0; cohort < 1; cohort++){
    for(int yr = 0; yr < 100; ++yr){

      int handlers_run = 0;
      boost::system::error_code ec;

      BOOST_LOG_SEV(clg, info) << "poll the io_service...";
      handlers_run = io_service->poll(ec);
      BOOST_LOG_SEV(clg, info) << handlers_run << " handlers run.";

      if (handlers_run > 0) {

        BOOST_LOG_SEV(clg, debug) <<   "Reset the io_service object.";
        io_service->reset();

        BOOST_LOG_SEV(clg, debug) <<   "Set async wait on signals to PAUSE handler.";
        signals.async_wait(
          boost::bind(pause_handler, boost::asio::placeholders::error, io_service) );

      }
      
      
      for(int m = 0; m < 12; ++m) {
        int sleeptime = 300;
        BOOST_LOG_SEV(clg, info) << "(cht, yr, m):" << "(" << cohort <<", "<< yr <<", "<< m << ") "
                                 << "Thinking for " << sleeptime << " milliseconds...";
        boost::posix_time::milliseconds workTime(sleeptime);
        boost::this_thread::sleep(workTime);

      } // end month loop
    } // end yr loop
  } // end cht loop

  BOOST_LOG_SEV(clg, info)  << "Done working. This simulation loops have exited.";
}


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

  // get handles for each of global loggers...
  severity_channel_logger_t& glg = my_general_logger::get();
  severity_channel_logger_t& clg = my_cal_logger::get();


  if (args->getCalibrationMode() == "on") {
    BOOST_LOG_SEV(glg, info) << "Running in Calibration Mode";

    calibration_worker();

  } else {
    BOOST_LOG_SEV(glg, info) << "Running in extrapolation mode.";
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
  }
};
