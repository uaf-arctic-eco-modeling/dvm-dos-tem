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
#include <json/writer.h>

#include <json/value.h>

#include <boost/filesystem.hpp>
#include <boost/asio/signal_set.hpp>
#include <boost/thread.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/bind.hpp>
#include <boost/asio.hpp>

#include <json/value.h>

#include <omp.h>

#ifdef WITHMPI
#include <mpi.h>
#include "data/RestartData.h" // for defining MPI typemap...
#include "inc/tbc_mpi_constants.h"
#endif

// For managing the floating point environment
#ifdef BSD_FPE
  #include <xmmintrin.h> // BSD (OSX)
#endif

#ifdef GNU_FPE
  #include <fenv.h> // GNU Linux
#endif



#include "inc/timeconst.h"
#include "../include/ArgHandler.h"
#include "../include/OutputEstimate.h"
#include "TEMLogger.h"
#include "TEMUtilityFunctions.h"
#include "../include/Runner.h"
#include "data/RestartData.h"

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
//void create_netCDF_output_files(int ysize, int xsize);

// draft - reading new-style co2 file
std::vector<float> read_new_co2_file(const std::string &filename);

/** Enables a 'floating point exception' mask that will make the program crash
 *  when a floating point number is generated (and or operated upon).
 *
 * Some more info
 * http://www.johndcook.com/blog/ieee_exceptions_in_cpp/
 * http://stackoverflow.com/questions/247053/enabling-floating-point-interrupts-on-mac-os-x-intel
 *
 * It might be helpful to add a singal handler at some point that could report
 * on what/where the exception is generated?
*/
void enable_floating_point_exceptions() {
  std::cout << "Enabling floating point exceptions mask!" << std::endl;

  // BSD (OSX)
  #ifdef BSD_FPE
    _MM_SET_EXCEPTION_MASK(_MM_GET_EXCEPTION_MASK() & ~_MM_MASK_INVALID);
  #endif

  // GNU Linux
  #ifdef GNU_FPE
    feenableexcept(FE_DIVBYZERO | FE_INVALID | FE_OVERFLOW);
  #endif

}

ArgHandler* args = new ArgHandler();

extern src::severity_logger< severity_level > glg;

int main(int argc, char* argv[]){

  // Read in and parse the command line arguments
  args->parse(argc, argv);
	if (args->get_help()) {
		args->show_help();
		return 0;
	}

  std::cout << "Setting up logging...\n";
  setup_logging(args->get_log_level(), args->get_log_scope());

  BOOST_LOG_SEV(glg, note) << "Checking command line arguments...";
  args->verify(); // stub - doesn't really do anything yet

  BOOST_LOG_SEV(glg, note) << "Turn floating point exceptions on?: " << args->get_fpe();
  if (args->get_fpe()) { enable_floating_point_exceptions(); }

  BOOST_LOG_SEV(glg, note) << "Reading controlfile into main(..) scope...";
  Json::Value controldata = temutil::parse_control_file(args->get_ctrl_file());

  BOOST_LOG_SEV(glg, note) << "Creating a ModelData object based on settings in the control file";
  ModelData modeldata(controldata);

  BOOST_LOG_SEV(glg, note) << "Update model settings based on command line flags/options...";
  modeldata.update(args);

  /*  
      Someday it may be worth the time/effort to make better use of
      boots::program_options here to manage the arguments from config file
      and the command line.
  */
  
  BOOST_LOG_SEV(glg, note) << "Running PR stage: " << modeldata.pr_yrs << "yrs";
  BOOST_LOG_SEV(glg, note) << "Running EQ stage: " << modeldata.eq_yrs << "yrs";
  BOOST_LOG_SEV(glg, note) << "Running SP stage: " << modeldata.sp_yrs << "yrs";
  BOOST_LOG_SEV(glg, note) << "Running TR stage: " << modeldata.tr_yrs << "yrs";
  BOOST_LOG_SEV(glg, note) << "Running SC stage: " << modeldata.sc_yrs << "yrs";

  // Turn off buffering...
  setvbuf(stdout, NULL, _IONBF, 0);
  setvbuf(stderr, NULL, _IONBF, 0);
  
  time_t stime;
  time_t etime;
  stime = time(0);

  BOOST_LOG_SEV(glg, note) << "Start dvmdostem @ " << ctime(&stime);

  BOOST_LOG_SEV(glg, debug) << "NEW STYLE: Going to run space-major over a 2D area covered by run mask...";

  // Open the run mask (spatial mask)
  std::vector< std::vector<int> > run_mask = temutil::read_run_mask(modeldata.runmask_file);

  // Make some convenient handles for later...
  std::string eq_restart_fname = modeldata.output_dir + "restart-eq.nc";
  std::string sp_restart_fname = modeldata.output_dir + "restart-sp.nc";
  std::string tr_restart_fname = modeldata.output_dir + "restart-tr.nc";
  std::string sc_restart_fname = modeldata.output_dir + "restart-sc.nc";

  // Figure out how big the run_mask is
  int num_rows = run_mask.size();
  int num_cols = run_mask[0].size();

  // Create empty restart files for all stages based on size of run mask
  if (!boost::filesystem::exists(modeldata.output_dir)) {
    BOOST_LOG_SEV(glg, info) << "Creating output directory as specified in "
                             << "config file: ", modeldata.output_dir;
    boost::filesystem::create_directory(modeldata.output_dir);
  }
  RestartData::create_empty_file(eq_restart_fname, num_rows, num_cols);
  RestartData::create_empty_file(sp_restart_fname, num_rows, num_cols);
  RestartData::create_empty_file(tr_restart_fname, num_rows, num_cols);
  RestartData::create_empty_file(sc_restart_fname, num_rows, num_cols);

  // Create empty output files now so that later, as the program
  // proceeds, there is somewhere to append output data...
  BOOST_LOG_SEV(glg, info) << "Creating a set of empty NetCDF output files";
  if(modeldata.eq_yrs > 0 && modeldata.nc_eq){
    modeldata.create_netCDF_output_files(num_rows, num_cols, "eq");
    if(modeldata.eq_yrs > 100 && modeldata.daily_netcdf_outputs.size() > 0){
      BOOST_LOG_SEV(glg, fatal) << "Daily outputs specified with EQ run greater than 100 years! Reconsider...";
    }
  }
  if(modeldata.sp_yrs > 0 && modeldata.nc_sp){
    modeldata.create_netCDF_output_files(num_rows, num_cols, "sp");
  }
  if(modeldata.tr_yrs > 0 && modeldata.nc_tr){
    modeldata.create_netCDF_output_files(num_rows, num_cols, "tr");
  }
  if(modeldata.sc_yrs > 0 && modeldata.nc_sc){
    modeldata.create_netCDF_output_files(num_rows, num_cols, "sc");
  }


  // Work on checking that the particular configuration will not result in too
  // much output.
  OutputEstimate oe = OutputEstimate(modeldata, args->get_cal_mode());
  BOOST_LOG_SEV(glg, info) << oe.estimate_as_table();

  if (args->get_max_output_volume().compare("-1") == 0) {
    // pass - nothing to do, user doesn't want to check for excessive output.
  } else {

    std::string  mxsz_s = args->get_max_output_volume();
    double mxsz = oe.hsize2bytes(mxsz_s);

    if ( !(mxsz >= 0) ) {
      BOOST_LOG_SEV(glg, fatal) << "Invalid size specification!: " << mxsz_s;
      exit(-1);
    }

    if ( oe.all_cells_total() > mxsz ) {
      BOOST_LOG_SEV(glg, fatal) << oe.estimate_as_table();
      BOOST_LOG_SEV(glg, fatal) << "TOO MUCH OUTPUT SPECIFIED! "
                                << "ADJUST YOUR SETTINGS AND TRY AGAIN. "
                                << "Or run with '--max-output-volume=-1'";
      exit(-1);
    }
  }

  if (args->get_loop_order() == "space-major") {

    // y <==> row <==> lat
    // x <==> col <==> lon

    // Loop over a 2D grid of 'cells' (cohorts?),
    // run each cell for some number of years. 
    //
    // Processing starts in the lower left corner (0,0).
    // Should really look into replacing this loop with 
    // something like python's map(...) function...
    // --> Could this allow us to use a map reduce strategy??
    //
    // Look into std::transform.

    // Use a few type definitions to save some typing.
    typedef std::vector<int> vec;
    typedef std::vector<vec> vec2D;

    vec2D::const_iterator row;
    vec::const_iterator col;

    // OpenMP requires:
    //  - The structured block to have a single entry and exit point.
    //  - The loop variable must be of type signed integer.
    //  - The comparison operator must be in the form
    //      loop_variable [<|<=|>|>=] loop_invariant integer
    //  - The third expression must be either integer addition or
    //      subtraction by a loop invariant value
    //  - The loop must increment or decrement on every iteration,
    //      depending on the comparison operator
    //  - The loop must be a basic block: no jump to outside the loop
    //      other than the exit statement.
    #pragma omp parallel for collapse(2) schedule(dynamic)
    for(int rowidx=0; rowidx<num_rows; rowidx++){
      for(int colidx=0; colidx<num_cols; colidx++){

        bool mask_value = run_mask[rowidx].at(colidx);

        if (true == mask_value) {

          BOOST_LOG_SEV(glg, note) << "Running cell (" << rowidx << ", " << colidx << ")";

          //modeldata.initmode = 1; // OBSOLETE?

          BOOST_LOG_SEV(glg, info) << "Setup the NEW STYLE RUNNER OBJECT ...";
          Runner runner(modeldata, args->get_cal_mode(), rowidx, colidx);

          BOOST_LOG_SEV(glg, debug) << runner.cohort.ground.layer_report_string("depth thermal");

          // seg fault w/o preparing climate...so prepare year zero...
          // this is also called inside run_years(...)
          runner.cohort.climate.prepare_daily_driving_data(0, "eq");

          runner.cohort.initialize_internal_pointers(); // sets up lots of pointers to various things
          runner.cohort.initialize_state_parameters();  // sets data based on values in cohortlookup
          BOOST_LOG_SEV(glg, debug) << "right after initialize_internal_pointers() and initialize_state_parameters()"
                                    << runner.cohort.ground.layer_report_string("depth ptr");


          // PRE RUN STAGE (PR)
          if (modeldata.pr_yrs > 0) {
            BOOST_LOG_NAMED_SCOPE("PRE-RUN");
            /** Env-only "pre-run" stage.
                 - should use only the env module
                 - number of years to run can be controlled on cmd line
                 - use fixed climate that is averaged over first X years
                 - use static (fixed) co2 value (first element of co2 file)
                 - FIX: need to set yrs since dsb ?
                 - FIX: should ignore calibration directives?
            */

            if (runner.calcontroller_ptr) {
              runner.calcontroller_ptr->handle_stage_start();
            }

            // turn off everything but env
            runner.cohort.md->set_envmodule(true);
            runner.cohort.md->set_bgcmodule(false);
            runner.cohort.md->set_nfeed(false);
            runner.cohort.md->set_avlnflg(false);
            runner.cohort.md->set_baseline(false);
            runner.cohort.md->set_dsbmodule(false);
            runner.cohort.md->set_dslmodule(false);
            runner.cohort.md->set_dvmmodule(false);

            BOOST_LOG_SEV(glg, debug) << "Ground, right before 'pre-run'. "
                                      << runner.cohort.ground.layer_report_string("depth thermal");

            runner.run_years(0, modeldata.pr_yrs, "pre-run"); // climate is prepared w/in here.

            BOOST_LOG_SEV(glg, debug) << "Ground, right after 'pre-run'"
                                      << runner.cohort.ground.layer_report_string("depth thermal");

            if (runner.calcontroller_ptr) {
              runner.calcontroller_ptr->handle_stage_end("pr");
            }

          }

          // EQUILIBRIUM STAGE (EQ)
          if (modeldata.eq_yrs > 0) {
            BOOST_LOG_NAMED_SCOPE("EQ");
            BOOST_LOG_SEV(glg, fatal) << "Equilibrium Initial Year Count: " << modeldata.eq_yrs;

            if (runner.calcontroller_ptr) {
              runner.calcontroller_ptr->handle_stage_start();
            }

            runner.cohort.md->set_envmodule(true);
            runner.cohort.md->set_dvmmodule(true);
            runner.cohort.md->set_bgcmodule(true);
            runner.cohort.md->set_dslmodule(true);

            runner.cohort.md->set_nfeed(true);
            runner.cohort.md->set_avlnflg(true);
            runner.cohort.md->set_baseline(true);

            runner.cohort.md->set_dsbmodule(true);

            // This variable ensures that OpenMP threads do not modify
            // the shared modeldata.eq_yrs value.
            int fri_adj_eq_yrs = modeldata.eq_yrs;//EQ years adjusted by FRI if necessary
            if (runner.cohort.md->get_dsbmodule()) {
              // The transition to SP must occur at the completion of a
              // fire cycle (i.e. a year or two prior to the next fire).
              // To ensure this, re-set modeldata's EQ year count to an
              // even multiple of the FRI minus 2 (to be safe)
              if (modeldata.eq_yrs < runner.cohort.fire.getFRI()) {
                BOOST_LOG_SEV(glg, err) << "The model will not run enough years to complete a disturbance cycle!";
              } else {
                int fri = runner.cohort.fire.getFRI();
                int EQ_fire_cycles = modeldata.eq_yrs / fri;
                if (modeldata.eq_yrs%fri != 0) {
                  // Extend the run to the end of the current fire cycle
                  fri_adj_eq_yrs = fri * (EQ_fire_cycles + 1) - 2;
                }
                else{
                  fri_adj_eq_yrs -= 2;
                }
              }
            }

            // Run model
            BOOST_LOG_SEV(glg, fatal) << "Running Equilibrium, " << fri_adj_eq_yrs << " years.";
            runner.run_years(0, fri_adj_eq_yrs, "eq-run");

            // Update restartdata structure from the running state
            runner.cohort.set_restartdata_from_state();

            runner.cohort.restartdata.verify_logical_values();
            BOOST_LOG_SEV(glg, debug) << "RestartData post EQ";
            runner.cohort.restartdata.restartdata_to_log();

            BOOST_LOG_SEV(glg, note) << "Writing RestartData to: " << eq_restart_fname;
            runner.cohort.restartdata.write_pixel_to_ncfile(eq_restart_fname, rowidx, colidx);

            if (modeldata.eq_yrs < runner.cohort.fire.getFRI()) {
              BOOST_LOG_SEV(glg, err) << "The model did not run enough years to complete a disturbance cycle!";
            }

            if (runner.calcontroller_ptr) {
              runner.calcontroller_ptr->handle_stage_end("eq");
            }

          }

          // SPINUP STAGE (SP)
          if (modeldata.sp_yrs > 0) {
            BOOST_LOG_NAMED_SCOPE("SP");
            BOOST_LOG_SEV(glg, fatal) << "Running Spinup, " << modeldata.sp_yrs << " years.";

            if (runner.calcontroller_ptr) {
              runner.calcontroller_ptr->handle_stage_start();
            }

            runner.cohort.climate.monthlycontainers2log();

            BOOST_LOG_SEV(glg, debug) << "Loading RestartData from: " << eq_restart_fname;
            runner.cohort.restartdata.update_from_ncfile(eq_restart_fname, rowidx, colidx);

            // FIX: if restart file has -9999, then soil temps can end up
            // impossibly low should check for valid values prior to actual use

            // Maybe a diffcult to maintain in the future
            // when/if more variables are added?
            runner.cohort.restartdata.verify_logical_values();

            BOOST_LOG_SEV(glg, debug) << "RestartData pre SP";
            runner.cohort.restartdata.restartdata_to_log();

            // Copy values from the updated restart data to cohort and cd
            runner.cohort.set_state_from_restartdata();

            // Run model
            runner.run_years(0, modeldata.sp_yrs, "sp-run");

            // Update restartdata structure from the running state
            runner.cohort.set_restartdata_from_state();

            BOOST_LOG_SEV(glg, debug) << "RestartData post SP";
            runner.cohort.restartdata.restartdata_to_log();

            BOOST_LOG_SEV(glg, note) << "Writing RestartData out to: " << sp_restart_fname;
            runner.cohort.restartdata.write_pixel_to_ncfile(sp_restart_fname, rowidx, colidx);

            if (runner.calcontroller_ptr) {
              runner.calcontroller_ptr->handle_stage_end("sp");
            }

          }

          // TRANSIENT STAGE (TR)
          if (modeldata.tr_yrs > 0) {
            BOOST_LOG_NAMED_SCOPE("TR");
            BOOST_LOG_SEV(glg, fatal) << "Running Transient, " << modeldata.tr_yrs << " years";

            if (runner.calcontroller_ptr) {
              runner.calcontroller_ptr->handle_stage_start();
            }

            // update the cohort's restart data object
            BOOST_LOG_SEV(glg, debug) << "Loading RestartData from: " << sp_restart_fname;
            runner.cohort.restartdata.update_from_ncfile(sp_restart_fname, rowidx, colidx);

            runner.cohort.restartdata.verify_logical_values();

            BOOST_LOG_SEV(glg, debug) << "RestartData pre TR";
            runner.cohort.restartdata.restartdata_to_log();

            // Copy values from the updated restart data to cohort and cd
            runner.cohort.set_state_from_restartdata();

            // Run model
            runner.run_years(0, modeldata.tr_yrs, "tr-run");

            // Update restartdata structure from the running state
            runner.cohort.set_restartdata_from_state();

            BOOST_LOG_SEV(glg, debug) << "RestartData post TR";
            runner.cohort.restartdata.restartdata_to_log();

            BOOST_LOG_SEV(glg, note) << "Writing RestartData out to: " << tr_restart_fname;
            runner.cohort.restartdata.write_pixel_to_ncfile(tr_restart_fname, rowidx, colidx);

            if (runner.calcontroller_ptr) {
              runner.calcontroller_ptr->handle_stage_end("tr");
            }

          }

          // SCENARIO STAGE (SC)
          if (modeldata.sc_yrs > 0) {
            BOOST_LOG_NAMED_SCOPE("SC");
            BOOST_LOG_SEV(glg, fatal) << "Running Scenario, " << modeldata.sc_yrs << " years.";

            if (runner.calcontroller_ptr) {
              runner.calcontroller_ptr->handle_stage_start();
            }

            // update the cohort's restart data object
            BOOST_LOG_SEV(glg, debug) << "Loading RestartData from: " << tr_restart_fname;
            runner.cohort.restartdata.update_from_ncfile(tr_restart_fname, rowidx, colidx);

            BOOST_LOG_SEV(glg, debug) << "RestartData pre SC";
            runner.cohort.restartdata.restartdata_to_log();

            // Copy values from the updated restart data to cohort and cd
            runner.cohort.set_state_from_restartdata();

            // Loading projected data instead of historic. FIX?
            runner.cohort.load_proj_climate(modeldata.proj_climate_file);

            BOOST_LOG_SEV(glg,fatal) << "Need to deal with loading projected fire data";
            exit(-1);

            // Run model
            runner.run_years(0, modeldata.sc_yrs, "sc-run");

            // Update restartdata structure from the running state
            runner.cohort.set_restartdata_from_state();

            BOOST_LOG_SEV(glg, debug) << "RestartData post SC";
            runner.cohort.restartdata.restartdata_to_log();

            BOOST_LOG_SEV(glg, note) << "Writing RestartData out to: " << sc_restart_fname;
            runner.cohort.restartdata.write_pixel_to_ncfile(sc_restart_fname, rowidx, colidx);

            if (runner.calcontroller_ptr) {
              runner.calcontroller_ptr->handle_stage_end("sc");
            }

          }

          // NOTE: Could have an option to set some time constants based on
          //       some sizes/dimensions of the input driving data...

          /**
          

           
            eq
              - create the climate from the average of the first X years
                of the driving climate data. 
                SIZE: 12 months,  1 year
              - set to default module settings to: ??
              - run_years( 0 <= iy < MAX_EQ_YEAR )
              - act on calibration directives
              -
           
            sp
              - create the climate from the first X years of the driving
                climate dataset. 
                SIZE: 12 months,  X years
              - set to default module settings: ??
              - run_years( SP_BEG <= iy <= SP_END )
              
            tr
              - create climate by loading the driving climate data (historic)
                SIZE: 12 months, length of driving dataset? OR number from inc/timeconst.h
              - set to default module settings: ??
              - run_years( TR_BEG <= iy <= TR_END )
              
          */

        } else {
          BOOST_LOG_SEV(glg, debug) << "Skipping cell (" << rowidx << ", " << colidx << ")";
        }
      }//end col loop
    }//end row loop
  
    
  } else if (args->get_loop_order() == "time-major") {
    BOOST_LOG_SEV(glg, warn) << "DO NOTHING. NOT IMPLEMENTED YET.";
    // for each year

      // Read in Climate - all locations, one year/timestep

      // Read in Vegetation - all locations
      // Read in Drainage - all locations
      // Read in Fire - all locations
    
      // for each cohort
        // updateMonthly(...)

  }

  BOOST_LOG_SEV(glg, note) << "DONE WITH NEW STYLE run (" << args->get_loop_order() << ")";

  etime = time(0);
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

/** rough draft for reading new-style co2 data
*/
std::vector<float> read_new_co2_file(const std::string &filename) {

  int ncid;
  
  BOOST_LOG_SEV(glg, debug) << "Opening dataset: " << filename;
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


