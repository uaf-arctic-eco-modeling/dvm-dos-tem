/**
 *  TEM.cpp
 *  main program for running DVM-DOS-TEM
 *  
 *  It runs at 3 run-mods:
 *    (1) site-specific
 *    (2) regional - time series
 * 		(3) regional - spatially (not yet available)
 * 
 * Authors: 
 *    Shuhua Yi - the original codes
 * 		Fengming Yuan - re-designing and re-coding for 
 *       (1) easily code managing;
 *       (2) java interface developing for calibration;
 *       (3) stand-alone application of TEM (java-c++)
 *       (4) inputs/outputs using netcdf format, have to be modified to fix memory-leaks
 *       (5) fix the snow/soil thermal/hydraulic algorithms
 *       (6) DVM coupled
 * 		Tobey Carman - modifications and maintenance
 *       (1) update application entry point with boost command line arg. handling.
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
#include <cstddef> // for offsetof()
#include <exception>
#include <map>
#include <set>

#include <boost/filesystem.hpp>
#include <boost/asio/signal_set.hpp>
#include <boost/thread.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/bind.hpp>
#include <boost/asio.hpp>

#include <mpi.h>

#include "ArgHandler.h"
#include "TEMLogger.h"
#include "assembler/Runner.h"

#include "data/RestartData.h" // for defining MPI typemap...
#include "inc/tbc_mpi_constants.h"

ArgHandler* args = new ArgHandler();

int main(int argc, char* argv[]){
extern src::severity_logger< severity_level > glg;

  args->parse(argc, argv);
	if (args->getHelp()){
		args->showHelp();
		return 0;
	}
  args->verify();

  std::cout << "Setting up logging...\n";

  setup_logging(args->getLogLevel());

  setvbuf(stdout, NULL, _IONBF, 0);
  setvbuf(stderr, NULL, _IONBF, 0);

  if (args->getMode() == "siterun") {
    time_t stime;
    time_t etime;
    stime=time(0);
    BOOST_LOG_SEV(glg, note) << "Running dvm-dos-tem in siterun mode. Start @ " 
                             << ctime(&stime);

    string controlfile = args->getCtrlfile();
    string chtid = args->getChtid();

    Runner siter;

    // Not working yet. Need to figure out if it is even possible to
    // control modules from the command line? and if so how this should working
    // in all the different run stages.
    //siter.modeldata_module_settings_from_args(*args);
    
    if (args->getCalibrationMode() == "on") {
      BOOST_LOG_SEV(glg, note) << "Turning CalibrationMode on in Runner (siter).";
      siter.set_calibrationMode(true);

      boost::filesystem::path tmp_json_folder("/tmp/cal-dvmdostem/");
      boost::filesystem::path tmp_json_folder_yly("/tmp/year-cal-dvmdostem");

      if( !(boost::filesystem::exists(tmp_json_folder_yly)) ) {
        BOOST_LOG_SEV(glg, info) << "Creating folder: " << tmp_json_folder_yly;
        boost::filesystem::create_directory(tmp_json_folder_yly);
      } else {
        BOOST_LOG_SEV(glg, info) << "Calibraiton json yearly folder already exists. ("
                                 << tmp_json_folder << ")";
        BOOST_LOG_SEV(glg, info) << "Deleting any exisiting calibration yearly json data.";
        boost::filesystem::remove_all(tmp_json_folder_yly);
        boost::filesystem::create_directory(tmp_json_folder_yly);
      }

      if( !(boost::filesystem::exists(tmp_json_folder)) ) {
        BOOST_LOG_SEV(glg, info) << "Creating folder: " << tmp_json_folder;
        boost::filesystem::create_directory(tmp_json_folder);
      } else {
        BOOST_LOG_SEV(glg, info) << "Calibraiton json folder already exists. ("
                                 << tmp_json_folder << ")";
        BOOST_LOG_SEV(glg, info) << "Deleting any exisiting calibration json data.";
        boost::filesystem::remove_all(tmp_json_folder);
        boost::filesystem::create_directory(tmp_json_folder);
      }

    } else {
      BOOST_LOG_SEV(glg, note) << "Running in extrapolation mode.";
    }

    siter.chtid = atoi(chtid.c_str());

    siter.initInput(controlfile, "siter");

    siter.initOutput();

    siter.setupData();

    siter.setupIDs();

    siter.single_site();
  
    etime=time(0);
    BOOST_LOG_SEV(glg, info) << "Done running TEM stand-alone mode @" 
                             << ctime(&etime);
    BOOST_LOG_SEV(glg, info) << "Total Seconds: " << difftime(etime, stime);                              

  } else if (args->getMode() == "regnrun") {

    time_t stime;
    time_t etime;
    stime=time(0);
    BOOST_LOG_SEV(glg, note) << "Running dvm-dos-tem in regional mode. Start @ "
                              << ctime(&stime);

    string controlfile = args->getCtrlfile();
    string runmode = args->getRegrunmode();

    Runner regner;

    regner.initInput(controlfile, runmode);

    regner.initOutput();

    regner.setupData();

    regner.setupIDs();

    if (runmode.compare("regner1")==0) {
      BOOST_LOG_SEV(glg, note) << "Running in regner1: regional_space_major(...)";
      regner.regional_space_major();
    } else if (runmode.compare("regner2")==0){
      BOOST_LOG_SEV(glg, note) << "Running in regner2...(runmode3)";
      int rank;
      int processors;
      #ifdef WITHMPI
        MPI_Init(&argc, &argv); // requires default args...empty?
      
        MPI_Comm_size(MPI_COMM_WORLD, &processors);
        MPI_Comm_rank(MPI_COMM_WORLD, &rank);
        BOOST_LOG_SEV(glg, note) << "This is processor " << rank << " of " << processors << " available on this system.";

        if (processors < 2) {
          MPI_Finalize();
          cout << "This is a master/slave program and requires more than one "
          << "processor to run when compiled with the WITHMPI flag.\n"
          << "EXITING...\n";
          exit(-1);
        }
      
        // do the real work...
        regner.runmode3(processors, rank);
      
        std::cout << "MADE it back from runmode3(..), parallel mode...\n";
        MPI_Finalize();
      #else
        regner.runmode3(processors, rank);
      #endif
    } else {
      BOOST_LOG_SEV(glg, fatal) << "Invalid runmode...quitting.";
      BOOST_LOG_SEV(glg, fatal) << "EITHER 'regner1', or 'regner2'!";
      exit(-1);
    }

    etime = time(0);
    BOOST_LOG_SEV(glg, note) << "Done running dvm-dos-tem regionally " 
                              << "(" << ctime(&etime) << ").";
    BOOST_LOG_SEV(glg, note) << "total seconds: " << difftime(etime, stime);
  }
  return 0;
};
