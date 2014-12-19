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

#include <json/value.h>

#ifdef WITHMPI
#include <mpi.h>
#include "data/RestartData.h" // for defining MPI typemap...
#include "inc/tbc_mpi_constants.h"
#endif


#include "ArgHandler.h"
#include "TEMLogger.h"
#include "TEMUtilityFunctions.h"
#include "assembler/Runner.h"

#include <netcdf.h>

/** work in progress function to generate a netcdf file that can follow 
* CF conventions 
*/
void create_new_output();

ArgHandler* args = new ArgHandler();

int main(int argc, char* argv[]){
extern src::severity_logger< severity_level > glg;

  args->parse(argc, argv);
	if (args->get_help()){
		args->show_help();
		return 0;
	}

  std::cout << "Setting up logging...\n";
  setup_logging(args->get_log_level());

  BOOST_LOG_SEV(glg, note) << "Checking command line arguments...";
  args->verify();

  BOOST_LOG_SEV(glg, note) << "Reading controlfile into main(..) scope...";
  Json::Value controldata = temutil::parse_control_file(args->get_ctrl_file());

  setvbuf(stdout, NULL, _IONBF, 0);
  setvbuf(stderr, NULL, _IONBF, 0);

  // Create empty output files now so that later, as the program
  // proceeds, there is somewhere to append output data...
  BOOST_LOG_SEV(glg, note) << "Creating a fresh 'n clean NEW output file...";
  create_new_output();

  time_t stime;
  time_t etime;
  stime=time(0);

  BOOST_LOG_SEV(glg, note) << "Start dvmdostem @ " << ctime(&stime);

  Runner runner;

  if (controldata["general"]["runmode"].asString() == "single") {
    runner.chtid = args->get_cohort_id();
  }

  runner.initInput(args->get_ctrl_file(), args->get_loop_order());
  runner.initOutput();
  runner.setupData();
  runner.setupIDs();

  if (controldata["general"]["runmode"].asString() == "single") {

    if (args->get_cal_mode()) {
      BOOST_LOG_SEV(glg, note) << "Turning CalibrationMode on in Runner (runner).";
      runner.set_calibrationMode(true);

      BOOST_LOG_SEV(glg, note) << "Clearing / creating folders for storing json files.";
      CalController::clear_and_create_json_storage();

    } else {
      BOOST_LOG_SEV(glg, note) << "Running in extrapolation mode.";
    }

    runner.single_site();

  } else if (controldata["general"]["runmode"].asString() == "multi") {

    if (args->get_loop_order().compare("space-major") == 0) {
      BOOST_LOG_SEV(glg, note) << "Running SPACE-MAJOR order: for each cohort, for each year";
      runner.regional_space_major();
    } else if (args->get_loop_order().compare("time-major") == 0){
      BOOST_LOG_SEV(glg, note) << "Running TIME-MAJOR: for each year, for each cohort";
      int rank;
      int processors;
      #ifdef WITHMPI
        MPI_Init(&argc, &argv); // requires default args...empty?
      
        MPI_Comm_size(MPI_COMM_WORLD, &processors);
        MPI_Comm_rank(MPI_COMM_WORLD, &rank);
        BOOST_LOG_SEV(glg, note) << "This is processor " << rank << " of "
                                 << processors << " available on this system.";
        if (processors > 2) {
          // do the real work...
          runner.regional_time_major(processors, rank);

          BOOST_LOG_SEV(glg, note) << "Done with regional_time_major(...), "
                                   << "(parallel (MPI) mode). Cleanup MPI...";
          MPI_Finalize();

        } else {
          BOOST_LOG_SEV(glg, warn) << "Not enough processors on this system "
                                   << "to run in parallel. Closing / finalizing "
                                   << "the MPI environment and defaulting to "
                                   << "serial operation.";
          MPI_Finalize();
          runner.regional_time_major(processors, rank);

        }
      #else
        runner.regional_time_major(processors, rank);
      #endif
    } else {
      BOOST_LOG_SEV(glg, fatal) << "Invalid loop-order! Must be " 
                                << "'space-major', or 'time-major'. Quitting...";
      exit(-1);
    }
  } else {
    BOOST_LOG_SEV(glg, err) << "Unrecognized mode from control file? Quitting.";
  }

  etime=time(0);
  BOOST_LOG_SEV(glg, info) << "Done with dvmdostem @" << ctime(&etime);
  BOOST_LOG_SEV(glg, info) << "Total Seconds: " << difftime(etime, stime);
  return 0;
}

void create_new_output() {

  int status;
  int ncid;

  std::cout << "Creating dataset...\n";
  temutil::nc( nc_create("general-outputs-monthly.nc", NC_CLOBBER, &ncid) );

  int timeD;    // unlimited dimension
  int pftD;
  int xD;
  int yD;

  /* Create Dimensions */
  std::cout << "Adding dimensions...\n";
  temutil::nc( nc_def_dim(ncid, "time", NC_UNLIMITED, &timeD) );
  temutil::nc( nc_def_dim(ncid, "pft", NUM_PFT, &pftD) );
  temutil::nc( nc_def_dim(ncid, "y", 10, &yD) );
  temutil::nc( nc_def_dim(ncid, "x", 10, &xD) );

  /* Create Coordinate Variables?? */

  /* Create Data Variables */

  // 4D vars
  std::cout << "Adding 4D variables...\n";
  int vartypeA_dimids[4];
  vartypeA_dimids[0] = timeD;
  vartypeA_dimids[1] = pftD;
  vartypeA_dimids[2] = yD;
  vartypeA_dimids[3] = xD;

  int vegcV;
  int veg_fractionV;
  int growstartV;
  temutil::nc( nc_def_var(ncid, "vegc", NC_DOUBLE, 4, vartypeA_dimids,  &vegcV) );
  temutil::nc( nc_def_var(ncid, "veg_fraction", NC_DOUBLE, 4, vartypeA_dimids, &veg_fractionV) );
  temutil::nc( nc_def_var(ncid, "growstart", NC_DOUBLE, 4, vartypeA_dimids, &growstartV) );

  // 3D vars
  std::cout << "Adding 3D variables...\n";
  int vartypeB_dimids[3];
  vartypeB_dimids[0] = timeD;
  vartypeB_dimids[1] = yD;
  vartypeB_dimids[2] = xD;

  int org_shlw_thicknessV;
  temutil::nc( nc_def_var(ncid, "org_shlw_thickness", NC_DOUBLE, 3, vartypeB_dimids, &org_shlw_thicknessV) );
  
  /* Create Attributes? */
  

  /* End Define Mode (not scrictly necessary for netcdf 4) */
  std::cout << "Leaving 'define mode'...\n";
  temutil::nc( nc_enddef(ncid) );

  /* Load coordinate variables?? */

  /* Close file. */
  std::cout << "Closing new file...\n";
  temutil::nc( nc_close(ncid) );

}

