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
#include <boost/thread/condition_variable.hpp>
#include <boost/thread/mutex.hpp>
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
boost::condition_variable cond;
bool pause_calibration = false;
boost::mutex mtex1;

/** The signal handler that will pause the calibration on CTRL-C */
void stop_calibration(const boost::system::error_code& error,
                      /*int signal_number,*/
                      boost::shared_ptr< boost::asio::io_service > io_service){
  severity_channel_logger_t& clg = my_cal_logger::get();
  BOOST_LOG_SEV(clg, info) << "Caught signal number: " ;//<< signal_number;
  BOOST_LOG_SEV(clg, info) << "Lock the mutex and set condition variable to true...";
  boost::lock_guard<boost::mutex> lock(mtex1);
  pause_calibration = true;
  BOOST_LOG_SEV(clg, info) << "call the notify function for the condition variable...";
  cond.notify_one();
}

/** A seperate thread to run the model. */
void calibration_worker_thread( boost::shared_ptr< boost::asio::io_service > io_service
                                /*ArgHandler* const args ? */){

  // get handles for each of global loggers
  severity_channel_logger_t& clg = my_cal_logger::get();

  BOOST_LOG_SEV(clg, info) << "Starting Calibration Worker Thread.";
  BOOST_LOG_SEV(clg, info) << "This should start the model in some mode, depending "
                           << "on command line args and and crunch numbers....";
  BOOST_LOG_SEV(clg, info) << "To simulate that I will loop over "
                           << "cohorts, years, months with brief pause in each.";


  for(int cohort = 0; cohort < 1; cohort++){
    for(int yr = 0; yr < 100; ++yr){

      BOOST_LOG_SEV(clg, info) << "Ask central io service if there has been a signal?";
      BOOST_LOG_SEV(clg, info) << "If so, post a collect_userin handler to the service";
      
      boost::unique_lock<boost::mutex> lock(mtex1);
      while(!pause_calibration){
        cond.wait(lock);      

        for(int m = 0; m < 12; ++m) {
          int sleeptime = 1;
          BOOST_LOG_SEV(clg, info) << "(cht, yr, m):" << "(" << cohort <<", "<< yr <<", "<< m << ") "
                                   << "Thinking for " << sleeptime << " seconds...";
          boost::posix_time::seconds workTime(sleeptime);
          boost::this_thread::sleep(workTime);
  
        } // end month loop
      } // end while !pause loop
    } // end yr loop
  } // end cht loop
  
  BOOST_LOG_SEV(clg, info)  << "Done working. This worker thread is finished.";
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

    BOOST_LOG_SEV(glg, info) << "Make shared pointers to an io_service and some work.";
    boost::shared_ptr< boost::asio::io_service > io_service(
      new boost::asio::io_service    
    );
  	boost::shared_ptr< boost::asio::io_service::work > work(
		  new boost::asio::io_service::work( *io_service )
   	);

    //BOOST_LOG_SEV(glg, info) << "Make a condition variable for 'pause_calibration' and set it to false.";

    BOOST_LOG_SEV(glg, info) << "Defining a signal set that the io_service will listen for.";
    boost::asio::signal_set signals(*io_service, SIGINT, SIGTERM);
    
    BOOST_LOG_SEV(glg, info) << "Define a callback that will run when the service "
                             << "delivers of the defined signals This callback needs " 
                             << "to be able to 1) stop the worker thread 2) block until a) user input is ok or "
                             << "b) another signal is recieved, in which case exit. In case (a), then "
                             << "choose what to do based on user input.";
    
    signals.async_wait( boost::bind(stop_calibration, 
                                    boost::asio::placeholders::error, io_service) ); // need to pass the io_service here...

    BOOST_LOG_SEV(glg, info) << "Start a worker thread to run tem, passing in the pointer to the io_service.";
    boost::thread workerThread( boost::bind(calibration_worker_thread, io_service) );

    BOOST_LOG_SEV(glg, info) << "Run the io_service event loop in the main thread, waiting "
                             << "for a signal to be captured/handled...";
    io_service->run();

    BOOST_LOG_SEV(glg, info) << "Exited from io_service.run()... "
                             << "all handlers have been run and there is no more work.";



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
