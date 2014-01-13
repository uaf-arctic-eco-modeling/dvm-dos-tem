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

#include <boost/signals2.hpp>
#include <boost/asio/signal_set.hpp>
#include <boost/thread.hpp>

#include "ArgHandler.h"
#include "TEMLogger.h"
#include "assembler/Runner.h"

BOOST_LOG_INLINE_GLOBAL_LOGGER_INIT(my_general_logger, severity_channel_logger_t) {
  return severity_channel_logger_t(keywords::channel = "GENER");
}
BOOST_LOG_INLINE_GLOBAL_LOGGER_INIT(my_cal_logger, severity_channel_logger_t) {
  return severity_channel_logger_t(keywords::channel = "CALIB");
}

void handler(const boost::system::error_code& error, int signal_number) {
  if (!error) {
    cout << "Caught a signal!!\n";
    exit(-1);
  }
}

void tbc_runner(){
  std::cout << "jUST STARTING THE WORKER...\n";  
  boost::posix_time::seconds workTime(10);
  boost::this_thread::sleep(workTime);
  std::cout << "WORKER DONE SLEEPING!! thread done, moving on.....\n";
}

void stop_calibration(const boost::system::error_code& error,
    int signal_number){
  std::cout << "Now what? I caught a sigint: " << signal_number << std::endl;
  std::cout << "SLEEPING!...\n";  
  boost::posix_time::seconds workTime(10);
  boost::this_thread::sleep(workTime);
}

void calibration_worker_thread(/*ArgHandler* const args ? */){
  // get handles for each of global loggers...
  severity_channel_logger_t& glg = my_general_logger::get();
  severity_channel_logger_t& clg = my_cal_logger::get();

  BOOST_LOG_SEV(glg, info) << "Starting Calibration Worker Thread.";
  BOOST_LOG_SEV(glg, info) << "This should start the model in x,y,z mode and crunch numbers....";
  BOOST_LOG_SEV(glg, info) << "To simulate that, I am sleeping for 10 seconds...";
  boost::posix_time::seconds workTime(10);
  boost::this_thread::sleep(workTime);
  BOOST_LOG_SEV(glg, info)  << "Done working. This thread is finished.";
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
    BOOST_LOG_SEV(glg, info) << "Making an io_service.";
    boost::asio::io_service io_service;
    

    BOOST_LOG_SEV(glg, info) << "Defining a signal set that the io_service will listen for.";
    boost::asio::signal_set signals(io_service, SIGINT, SIGTERM);
    
    // ??? stops service ???.
    //  signals.async_wait(boost::bind(
    //      &boost::asio::io_service::stop, &io_service));
    
    BOOST_LOG_SEV(glg, info) << "Define a callback that will run when the service "
                     << "delivers one of the defined signals.";
    signals.async_wait(&stop_calibration);

    // this is going to go off and sleep for 10 secs...
    BOOST_LOG_SEV(glg, info) << "Start a worker thread to run tem.";
    boost::thread workerThread(&calibration_worker_thread); // need to figure out how to pass args to this..

    BOOST_LOG_SEV(glg, info) << "Run the io_service in the main thread, waiting "
                             << "asynchronously for a signal to be captured/handled...";

    io_service.run();
    BOOST_LOG_SEV(glg, info) << "Exited from io_service.run().";

    //workerThread.join();


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
