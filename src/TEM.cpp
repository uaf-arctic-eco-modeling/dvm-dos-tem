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

void calibration_user_input_thread( boost::shared_ptr< boost::asio::io_service >);
void calibration_worker_thread( boost::shared_ptr< boost::asio::io_service > );

void remapsigs(boost::shared_ptr< boost::asio::io_service >, char);
bool valid_calibration_user_response(std::string ui);


// DEFINE FREE FUNCTIIONS...
void remapsigs(boost::shared_ptr< boost::asio::io_service > io_service, char mode){
  severity_channel_logger_t& clg = my_cal_logger::get();
  BOOST_LOG_SEV(clg, debug) << "  Define a signal set...";  
  boost::asio::signal_set signals(*io_service, SIGINT, SIGTERM);

//   BOOST_LOG_SEV(clg, debug) << "  Stop the io_service.";  
//   io_service->stop();
 
//   BOOST_LOG_SEV(clg, debug) << "  Reset io_service.";  
//   io_service->reset();
  
  
  
  if (mode == 'q') {
    BOOST_LOG_SEV(clg, debug) << "  Set async wait on signals to QUIT handler.";
    signals.async_wait(
        boost::bind(quit_handler, boost::asio::placeholders::error, io_service) );
  } else if (mode == 'p') {
    BOOST_LOG_SEV(clg, debug) <<   "  Set async wait on signals to PAUSE handler.";
    signals.async_wait(
        boost::bind(pause_handler, boost::asio::placeholders::error, io_service) );
  }

}



void quit_handler(const boost::system::error_code& error,
                  boost::shared_ptr< boost::asio::io_service > io_service ){
  severity_channel_logger_t& clg = my_cal_logger::get();
  BOOST_LOG_SEV(clg, info) << "Got a message to quit.";
  BOOST_LOG_SEV(clg, info) << "Stopping the io_service.";
  io_service->stop();

  BOOST_LOG_SEV(clg, debug) << "Quitting. Exit with -1.";
  exit(-1);
}


bool valid_calibration_user_response(std::string ui) {

  if ( ui.length() > 1 ) {
    return false;
  }
  if ( ui[0] == 'c' ) {
    return true;
  }
  if ( ui[0] == 'r' ) {
    return true;
  } else {
    return false;
  }
}


/** The signal handler that will pause the calibration on CTRL-C */
void pause_handler( const boost::system::error_code& error,
                    boost::shared_ptr< boost::asio::io_service > io_service ){

  severity_channel_logger_t& clg = my_cal_logger::get();
  BOOST_LOG_SEV(clg, debug) << "Caught signal!"; //number: " << signal_number;
  BOOST_LOG_SEV(clg, debug) << "Running pause handler."; //number: " << signal_number;


  // Blocking call to collect user input
  std::string ui;
  do {
    BOOST_LOG_SEV(clg, debug) << "Enter 'c' for continue, 'r' for reload:";
    std::getline(std::cin, ui);
  } while (!valid_calibration_user_response(ui));

  BOOST_LOG_SEV(clg, debug) << "Got some good UI!";

  //BOOST_LOG_SEV(clg, debug) << "Set signals to quit";
  //remapsigs(io_service, 'q');

  //BOOST_LOG_SEV(clg, debug) << "Spawn a thread to collect user input...";
  //boost::thread userInputThread( boost::bind(calibration_user_input_thread, io_service) );

  
  //BOOST_LOG_SEV(clg, debug) << "Setup a blocking run in the workerThread, waiting "
  //                         << "for a quit signal to be caught while the ui thread is getting user input...";
  //io_service->run();

  //BOOST_LOG_SEV(clg, debug) << "worker thread now waiting for user input thread to join before returning...";
  //userInputThread.join();
  //BOOST_LOG_SEV(clg, debug) << "The ui thread is joined, so we haven't quit and we have collected the user input..."; 

  BOOST_LOG_SEV(clg, debug) << "Remap signals to pause.";
  remapsigs(io_service, 'p');
   
}

void calibration_user_input_thread( boost::shared_ptr< boost::asio::io_service > io_service ) {

  severity_channel_logger_t& clg = my_cal_logger::get();
  BOOST_LOG_SEV(clg, info) << "Hit 'Enter' to continue.";
  std::cin.get();

  BOOST_LOG_SEV(clg, info) << "I got some user input!";
  
  BOOST_LOG_SEV(clg, info) << "Reset signal handling to pause";
  remapsigs(io_service, 'p');

  //BOOST_LOG_SEV(clg, info) << "I got some user input";

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

      BOOST_LOG_SEV(clg, info) << "poll the io_service, ";

      int handlers_run = 0;
      boost::system::error_code ec;
      handlers_run = io_service->poll_one(ec);
      BOOST_LOG_SEV(clg, info) << "Handlers run: " << handlers_run << "     Error Code: " << ec;

      BOOST_LOG_SEV(clg, info) << "STOP the io_service...";
      io_service->stop();

      BOOST_LOG_SEV(clg, info) << "RESET the io_service...";
      io_service->reset();

      for(int m = 0; m < 12; ++m) {
        int sleeptime = 300;
        BOOST_LOG_SEV(clg, info) << "(cht, yr, m):" << "(" << cohort <<", "<< yr <<", "<< m << ") "
                                 << "Thinking for " << sleeptime << " milliseconds...";
        boost::posix_time::milliseconds workTime(sleeptime);
        boost::this_thread::sleep(workTime);

      } // end month loop
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

    BOOST_LOG_SEV(glg, info) << "Make shared pointers to an io_service";
    boost::shared_ptr< boost::asio::io_service > io_service(
      new boost::asio::io_service    
    );

    BOOST_LOG_SEV(glg, info) << "Add some work to the service so it won't die.";
    boost::shared_ptr< boost::asio::io_service::work > work(
      new boost::asio::io_service::work( *io_service )
    );
    
    
    BOOST_LOG_SEV(clg, info) << "Set signal handling to pause...";
    remapsigs(io_service, 'p');

    BOOST_LOG_SEV(glg, info) << "Start a worker thread to run tem, passing in the pointer to the io_service.";
    boost::thread workerThread( boost::bind(calibration_worker_thread, io_service) );

    BOOST_LOG_SEV(glg, info) << "Run the io_service in the main thread...";
    io_service->run();

    BOOST_LOG_SEV(glg, info) << "Main thread now waiting for worker to join before returning...";
    workerThread.join();
    BOOST_LOG_SEV(glg, info) << "Worker thread had finished (joined) main thread. Calibration done. Quitting.";
    


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
