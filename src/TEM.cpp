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

/** Quick 'n dirty pretty printer for vector of things
*/
template <typename TYPE>
void ppv(const std::vector<TYPE> &v){
  typename std::vector<TYPE>::const_iterator it;
  for (it = v.begin(); it != v.end(); ++it) {
    std::cout << *it << " ";
  }
  std::cout << "\n";
}

// draft pretty-printers...
void pp_2dvec(const std::vector<std::vector<int> > & vv);

// draft - generate a netcdf file that can follow CF conventions
void create_new_output();

// draft - reading new-style co2 file
std::vector<float> read_new_co2_file(const std::string &filename);

// draft - reading in a 2D run mask...
std::vector< std::vector<int> > read_run_mask(const std::string &filename);




ArgHandler* args = new ArgHandler();

extern src::severity_logger< severity_level > glg;

int main(int argc, char* argv[]){

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

  BOOST_LOG_SEV(glg, note) << "Creating a ModelData object based on settings in the control file";
  ModelData modeldata(controldata);
  
  // Modify the ModelData object based on cmd line args?
  // Maybe look into boost program obtions config file and property tree?

  // Turn off buffering...
  setvbuf(stdout, NULL, _IONBF, 0);
  setvbuf(stderr, NULL, _IONBF, 0);

  // Create empty output files now so that later, as the program
  // proceeds, there is somewhere to append output data...
  // ??? Maybe the type/shape of outputs that we create can, or should, depend on
  // ??? some of the settings in the ModelData object?
  BOOST_LOG_SEV(glg, note) << "Creating a fresh 'n clean NEW output file...";
  create_new_output();
  
  time_t stime;
  time_t etime;
  stime = time(0);

  BOOST_LOG_SEV(glg, note) << "Start dvmdostem @ " << ctime(&stime);

  // Read in C02 - read all data (years) even though some stages/configurations
  //               may use only the first year
  std::vector<float> co2_vec = read_new_co2_file("scripts/new-co2-dataset.nc");
  
  // NOTE: Are there any conttraints on the length of the co2 vector??
  
  /* Can read the input data and parameters to choose a few things:
  
   - Stage
    eq
    sp
    tr
    sc

   - Cal mode
    - available in all stages?
   - outputs to setup
   
  */

  if (args->get_new_style()) {

    BOOST_LOG_SEV(glg, debug) << "NEW STYLE: Going to run space-major over a 2D area covered by run mask...";

    // Open the run mask (spatial mask)
    std::vector< std::vector<int> > run_mask = read_run_mask("scripts/run-mask.nc");

    if (args->get_loop_order() == "space-major") {

      // y <==> row <==> lat
      // x <==> col <==> lon

      /* 
         Loop over a 2D grid of 'cells' (cohorts?),
         run each cell for some number of years. 
         
         Processing starts in the lower left corner (0,0).
         Should really look into replacing this loop with 
         something like python's map(...) function...
          --> Could this allow us to use a map reduce strategy??
       
         Look into std::transform. 
      */

      // Use a few type definitions to save some typing.
      typedef std::vector<int> vec;
      typedef std::vector<vec> vec2D;

      vec2D::const_iterator row;
      vec::const_iterator col;
      for (row = run_mask.begin(); row != run_mask.end() ; ++row) {
        for (col = row->begin(); col != row->end(); ++col) {
          
          bool mask_value = *col;
          
          int rowidx = row - run_mask.begin();
          int colidx = col - row->begin();
          
          if (true == mask_value) {


            BOOST_LOG_SEV(glg, debug) << "Running cell (" << rowidx << ", " << colidx << ")";

            Runner runner(modeldata, rowidx, colidx);

            // should we need to call all these cohort setup functions?
            // Or assume that when a Runner is created, for a spatial
            // location, the Cohort is smart enough to correctly "load"
            // itself with all the right stuff...?
            runner.cohort.NEW_load_climate_from_file(rowidx, colidx);
            runner.cohort.NEW_load_veg_class_from_file(rowidx, colidx);

            runner.cohort.initSubmodules();
            runner.cohort.initStatePar();

            // hard coding module on/off here for testing...
            runner.cohort.md->set_envmodule(true);
            runner.cohort.md->set_dvmmodule(true);
            runner.cohort.md->set_dslmodule(true);
            runner.cohort.md->set_bgcmodule(true);
            runner.cohort.md->set_dsbmodule(false);
            
            // Ends up as a null pointer if calibrationMode is off.
            boost::shared_ptr<CalController> calcontroller_ptr;
            if ( args->get_cal_mode() ) {
              calcontroller_ptr.reset( new CalController(&runner.cohort) );
              calcontroller_ptr->clear_and_create_json_storage();

            }

            if (modeldata.runeq) {
              runner.quick_env_only_warmup_run(0, 100, calcontroller_ptr);
            }

            if (calcontroller_ptr) {
              BOOST_LOG_SEV(glg, info) << "CALIBRATION MODE. Pausing. "
                                       << "Please check that the 'warm up' "
                                       << "data looks good.";

              calcontroller_ptr->pause();

              calcontroller_ptr->clear_and_create_json_storage();

              BOOST_LOG_SEV(glg, info) << "Set default calibration module settings...";
              runner.cohort.md->set_envmodule(true);
              runner.cohort.md->set_bgcmodule(true);
              runner.cohort.md->set_nfeed(false);
              runner.cohort.md->set_avlnflg(true);
              runner.cohort.md->set_baseline(true);
              runner.cohort.md->set_dsbmodule(false);
              runner.cohort.md->set_dslmodule(false);
              runner.cohort.md->set_dvmmodule(true);
              runner.cohort.md->set_friderived(true);
            } else {
                BOOST_LOG_SEV(glg, warn) << "EXTRAPOLATION MODE. Anything special to do?";
            }
            // Determine year settings? list of years to run based on stage?
            // Or simply base off of the amount of the inputdataset?
            //??
            //timesettings_from_stage();
            runner.run_years(0, 1000, calcontroller_ptr);

          } else {
            BOOST_LOG_SEV(glg, debug) << "Skipping cell (" << rowidx << ", " << colidx << ")";
          }
        }
      }
    
      
    } else if(args->get_loop_order() == "time-major") {
      
      // for each year

        // Read in Climate - all locations, one year/timestep

        // Read in Vegetation - all locations
        // Read in Drainage - all locations
        // Read in Fire - all locations
      
        // for each cohort
          // updateMonthly(...)

    }

    BOOST_LOG_SEV(glg, note) << "DONE WITH NEW STYLE run (" << args->get_loop_order() << ")";
    exit(-1);
  }
  
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
} /* End main() */


/** Pretty print a 2D vector of ints */
void pp_2dvec(const std::vector<std::vector<int> > & vv) {

  typedef std::vector<int> vec;
  typedef std::vector<vec> vec2D;

  for (vec2D::const_iterator row = vv.begin(); row != vv.end(); ++row) {
    for (vec::const_iterator col = row->begin(); col != row->end(); ++col) {
      std::cout << *col << " ";
    }
    std::cout << std::endl;
  }
}

/** rough draft for reading a run-mask (2D vector of ints)
*/
std::vector< std::vector<int> > read_run_mask(const std::string &filename) {
  int ncid;
  
  BOOST_LOG_SEV(glg, debug) << "Opening dataset...";
  temutil::nc( nc_open(filename.c_str(), NC_NOWRITE, &ncid) );
  
  BOOST_LOG_SEV(glg, debug) << "Find out how much data there is...";
  int yD, xD;
  size_t yD_len, xD_len;

  temutil::nc( nc_inq_dimid(ncid, "Y", &yD) );
  temutil::nc( nc_inq_dimlen(ncid, yD, &yD_len) );

  temutil::nc( nc_inq_dimid(ncid, "X", &xD) );
  temutil::nc( nc_inq_dimlen(ncid, xD, &xD_len) );

  BOOST_LOG_SEV(glg, debug) << "Allocate a 2D run-mask vector (y,x). Size: (" << yD_len << ", " << xD_len << ")";
  std::vector< std::vector<int> > run_mask(yD_len, std::vector<int>(xD_len));
  
  BOOST_LOG_SEV(glg, debug) << "Read the run flag data from the file into the 2D vector...";
  int runV;
  temutil::nc( nc_inq_varid(ncid, "run", &runV) );

  BOOST_LOG_SEV(glg, debug) << "Grab one row at a time";
  BOOST_LOG_SEV(glg, debug) << "(need contiguous memory, and vector<vector> are not contiguous)";

  std::vector< std::vector<int> >::iterator row;
  for (row = run_mask.begin();  row != run_mask.end(); ++row) {

    int rowidx = row - run_mask.begin();

    // specify start indices for each dimension (y, x)
    size_t start[2];
    start[0] = rowidx;    // Y
    start[1] = 0;         // X

    // specify counts for each dimension
    size_t count[2];
    count[0] = 1;         // one row
    count[1] = xD_len;    // all data
    
    std::vector<int> rowdata(xD_len);

    temutil::nc( nc_get_vara_int(ncid, runV, start, count, &rowdata[0] ) );
  
    run_mask[rowidx] = rowdata;
    
  }
  
  temutil::nc( nc_close(ncid) );

  //pp_2dvec(run_mask);

  BOOST_LOG_SEV(glg, debug) << "Return the vector...";
  return run_mask;

}


/** rough draft for reading new-style co2 data
*/
std::vector<float> read_new_co2_file(const std::string &filename) {

  int ncid;
  
  BOOST_LOG_SEV(glg, debug) << "Opening dataset...";
  temutil::nc( nc_open(filename.c_str(), NC_NOWRITE, &ncid) );
  
  BOOST_LOG_SEV(glg, debug) << "Find out how much data there is...";
  int yearD;
  size_t yearD_len;
  temutil::nc( nc_inq_dimid(ncid, "year", &yearD) );
  temutil::nc( nc_inq_dimlen(ncid, yearD, &yearD_len) );

  BOOST_LOG_SEV(glg, debug) << "Allocate vector big enough for " << yearD_len << " years of co2 data...";
  std::vector<float> co2data(yearD_len);

  BOOST_LOG_SEV(glg, debug) << "Read the co2 data from the file into the vector...";
  int co2V;
  temutil::nc( nc_inq_varid(ncid, "co2", &co2V) );
  temutil::nc( nc_get_var(ncid, co2V, &co2data[0]) );
  
  temutil::nc( nc_close(ncid) );

  BOOST_LOG_SEV(glg, debug) << "Return the vector...";
  return co2data;
}

/** rough draft for new output files
*/
void create_new_output() {

  int ncid;

  BOOST_LOG_SEV(glg, debug) << "Creating dataset...";
  temutil::nc( nc_create("general-outputs-monthly.nc", NC_CLOBBER, &ncid) );

  int timeD;    // unlimited dimension
  int pftD;
  int xD;
  int yD;

  /* Create Dimensions */
  BOOST_LOG_SEV(glg, debug) << "Adding dimensions...";
  temutil::nc( nc_def_dim(ncid, "time", NC_UNLIMITED, &timeD) );
  temutil::nc( nc_def_dim(ncid, "pft", NUM_PFT, &pftD) );
  temutil::nc( nc_def_dim(ncid, "y", 10, &yD) );
  temutil::nc( nc_def_dim(ncid, "x", 10, &xD) );

  /* Create Coordinate Variables?? */

  /* Create Data Variables */

  // 4D vars
  BOOST_LOG_SEV(glg, debug) << "Adding 4D variables...";
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
  BOOST_LOG_SEV(glg, debug) << "Adding 3D variables...";
  int vartypeB_dimids[3];
  vartypeB_dimids[0] = timeD;
  vartypeB_dimids[1] = yD;
  vartypeB_dimids[2] = xD;

  int org_shlw_thicknessV;
  temutil::nc( nc_def_var(ncid, "org_shlw_thickness", NC_DOUBLE, 3, vartypeB_dimids, &org_shlw_thicknessV) );
  
  /* Create Attributes? */
  

  /* End Define Mode (not scrictly necessary for netcdf 4) */
  BOOST_LOG_SEV(glg, debug) << "Leaving 'define mode'...";
  temutil::nc( nc_enddef(ncid) );

  /* Load coordinate variables?? */

  /* Close file. */
  BOOST_LOG_SEV(glg, debug) << "Closing new file...";
  temutil::nc( nc_close(ncid) );

}

