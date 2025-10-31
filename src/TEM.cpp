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
#include <boost/bind/bind.hpp>
#include <boost/asio.hpp>

#include <json/value.h>

#include <omp.h>

#ifdef WITHMPI
#include <mpi.h>
#include "../include/RestartData.h" // for defining MPI typemap...
//#include "../include/tbc_mpi_constants.h"
#endif

// For managing the floating point environment
#ifdef BSD_FPE
  #include <xmmintrin.h> // BSD (OSX)
#endif

#ifdef GNU_FPE
  #include <fenv.h> // GNU Linux
#endif



#include "../include/timeconst.h"
#include "../include/ArgHandler.h"
#include "../include/OutputEstimate.h"
#include "../include/TEMLogger.h"
#include "../include/TEMUtilityFunctions.h"
#include "../include/Runner.h"
#include "../include/RestartData.h"

#include <netcdf.h>


/** Write out a status code to a particular pixel in the run status file.
*/
void write_status_info(const std::string fname, std::string varname, int row, int col, int statusCode);


/** Builds an empty netcdf file for recording the run status. 
 * Ultimately we might want to spit the run status out in a more easily 
 * consumable way like txt to stdout or json, but for now we can use netcdf. 
 * Also it makes for a simple netcdf file to experiment with for MPI, 
 * parallel output
 */
void create_empty_run_status_file(const std::string& fname,
    const int ysize, const int xsize);

// The main driving function
void advance_model(const int rowidx, const int colidx,
                   const ModelData&, const bool calmode,
                   const std::string& pr_restart_fname,
                   const std::string& eq_restart_fname,
                   const std::string& sp_restart_fname,
                   const std::string& tr_restart_fname,
                   const std::string& sc_restart_fname);


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
  else if(args->get_print_sha()){
    std::cout<<GIT_SHA<<std::endl;
    return 0;
  }

  std::cout << "Setting up logging...\n";
  setup_logging(args->get_log_level(), args->get_log_scope());

  BOOST_LOG_SEV(glg, info) << "Checking command line arguments...";
  args->verify(); // stub - doesn't really do anything yet

  BOOST_LOG_SEV(glg, info) << "Turn floating point exceptions on?: " << args->get_fpe();
  if (args->get_fpe()) { enable_floating_point_exceptions(); }

  BOOST_LOG_SEV(glg, info) << "Reading controlfile into main(..) scope...";
  Json::Value controldata = temutil::parse_control_file(args->get_ctrl_file());

  BOOST_LOG_SEV(glg, info) << "Creating a ModelData object based on settings in the control file";
  ModelData modeldata(controldata);

  BOOST_LOG_SEV(glg, info) << "Update model settings based on command line flags/options...";
  modeldata.update(args);

  // Further verification that the cmd line args and the config file don't have
  // conflicting settings


  // Make sure that if user wants a restart run, they explicitly set the 
  // path to the restart file in their config.js file. Also make sure that 
  // they are not trying to run PR or EQ years when restarting from a previous run.
  
  if (modeldata.restart_from.length() > 0) {
    assert( boost::filesystem::exists(modeldata.restart_from) && 
      "Restart file specified but not found!");

    assert( (args->get_pr_yrs() == 0) && 
      "Cannot run PR years when restarting from a previous run!");

    assert ( (args->get_eq_yrs() == 0) && 
      "Cannot run EQ years when restarting from a previous run!");
  }



  /*
      Someday it may be worth the time/effort to make better use of
      boots::program_options here to manage the arguments from config file
      and the command line.
  */


  BOOST_LOG_SEV(glg, info) << "Running PR stage: " << modeldata.pr_yrs << "yrs";
  BOOST_LOG_SEV(glg, info) << "Running EQ stage: " << modeldata.eq_yrs << "yrs";
  BOOST_LOG_SEV(glg, info) << "Running SP stage: " << modeldata.sp_yrs << "yrs";
  BOOST_LOG_SEV(glg, info) << "Running TR stage: " << modeldata.tr_yrs << "yrs";
  BOOST_LOG_SEV(glg, info) << "Running SC stage: " << modeldata.sc_yrs << "yrs";

  // Turn off buffering...
  setvbuf(stdout, NULL, _IONBF, 0);
  setvbuf(stderr, NULL, _IONBF, 0);
  
  time_t stime, etime, cell_stime, cell_etime;
  stime = time(0);
  modeldata.cell_stime = stime;

  BOOST_LOG_SEV(glg, info) << "Start dvmdostem @ " << ctime(&stime);

  BOOST_LOG_SEV(glg, debug) << "Running over a 2D spatial area covered by a "
                            << "run mask. Use the run mask to exclude pixels "
                            << "from computation. The outer loop is over the "
                            << "spatial dimensions and the inner loops are "
                            << "over the time axes.";

  // Open the run mask (spatial mask)
  std::vector< std::vector<int> > run_mask = temutil::read_run_mask(modeldata.runmask_file);

  // Figure out how big the run_mask is
  int num_rows = run_mask.size();
  int num_cols = run_mask[0].size();

  // Make some convenient handles for later...
  std::string run_status_fname = modeldata.output_dir + "run_status.nc";
  std::string pr_restart_fname = modeldata.output_dir + "restart-pr.nc";
  std::string eq_restart_fname = modeldata.output_dir + "restart-eq.nc";
  std::string sp_restart_fname = modeldata.output_dir + "restart-sp.nc";
  std::string tr_restart_fname = modeldata.output_dir + "restart-tr.nc";
  std::string sc_restart_fname = modeldata.output_dir + "restart-sc.nc";

#ifdef WITHMPI
  BOOST_LOG_SEV(glg, monitor) << "Built and running with MPI";

  // Intended for passing argc and argv, the arguments to MPI_Init
  // are currently unnecessary.
  MPI_Init(NULL, NULL);

  int id, ntasks;
  MPI_Comm_rank(MPI_COMM_WORLD, &id);
  MPI_Comm_size(MPI_COMM_WORLD, &ntasks);

#else
  //
  int id = 0;
#endif

  // Limit output directory and file setup to a single process.
  // variable 'id' is artificially set to 0 if not built with MPI.
  if(id==0){
    BOOST_LOG_SEV(glg, info) << "Handling single-process setup";

    BOOST_LOG_SEV(glg, info) << "Checking for output directory: " << modeldata.output_dir;
    boost::filesystem::path out_dir_path(modeldata.output_dir);
    if( boost::filesystem::exists(out_dir_path) ){
      if (args->get_no_output_cleanup() || (modeldata.restart_from.length() > 0)) {
        BOOST_LOG_SEV(glg, warn) << "WARNING!! Not cleaning up output directory! "
                                 << "Old and potentially confusing files may be "
                                 << "present from previous runs!!";
      } else {
        BOOST_LOG_SEV(glg, info) << "Output directory exists. Deleting...";
        boost::filesystem::remove_all(out_dir_path);
      }
    }
    BOOST_LOG_SEV(glg, info) << "Creating output directory: "<<modeldata.output_dir;
    boost::filesystem::create_directories(out_dir_path);


  // Creating file to store configuration information to be packaged
  // with the output data.
  boost::filesystem::path config_log_fpath = modeldata.output_dir + "config_log.js";
  boost::filesystem::ofstream config_log_file(config_log_fpath);

  Json::Value configrecord = {};

  // Store original config file settings
  configrecord["original_config"] = controldata;

  // This is a temporary approach for writing the command line overrides
  // to the configuration output record.
  std::string CLI_string = "";
  for(int ii=0; ii<argc; ii++){
    CLI_string += argv[ii];
    CLI_string += " ";
  }
  BOOST_LOG_SEV(glg, info) << CLI_string;
  configrecord["CLI command"] = CLI_string;

  config_log_file << configrecord;
  config_log_file.close();

#ifdef WITHMPI

    MPI_Barrier(MPI_COMM_WORLD);
  } // End of single-process setup
  else{
    // Block all processes until process 0 has completed output
    // directory setup.
    MPI_Barrier(MPI_COMM_WORLD);
  }
#else
  } // Nothing to do; only one process, id will equal 0.
#endif

  // Attempting to restrict file creation to one process (in the conditional
  // statements above) causes a silent hang in nc_create_par(...)

  // Creating empty restart files for stages that will be run.
  //  This avoids overwriting any restart files that might be in use.
  BOOST_LOG_SEV(glg, info) << "Creating restart files for stages to be run";
  if(args->get_pr_yrs() > 0){
    BOOST_LOG_SEV(glg, info) << "Creating empty PR restart file";
    RestartData::create_empty_file(pr_restart_fname, num_rows, num_cols);
  }
  if(args->get_eq_yrs() > 0){
    BOOST_LOG_SEV(glg, info) << "Creating empty EQ restart file";
    RestartData::create_empty_file(eq_restart_fname, num_rows, num_cols);
  }
  if(args->get_sp_yrs() > 0){
    BOOST_LOG_SEV(glg, info) << "Creating empty SP restart file";
    RestartData::create_empty_file(sp_restart_fname, num_rows, num_cols);
  }
  if(args->get_tr_yrs() > 0){
    BOOST_LOG_SEV(glg, info) << "Creating empty TR restart file";
    RestartData::create_empty_file(tr_restart_fname, num_rows, num_cols);
  }
  if(args->get_sc_yrs() > 0){
    BOOST_LOG_SEV(glg, info) << "Creating empty SC restart file";
    RestartData::create_empty_file(sc_restart_fname, num_rows, num_cols);
  }

  // Create empty run status file
  BOOST_LOG_SEV(glg, info) << "Creating empty run status file.";
  create_empty_run_status_file(run_status_fname, num_rows, num_cols);

  // Create empty output files now so that later, as the program
  // proceeds, there is somewhere to append output data...
  BOOST_LOG_SEV(glg, info) << "Creating a set of empty NetCDF output files";
  bool copy_gm = true;
  if(modeldata.eq_yrs > 0 && modeldata.nc_eq){
    modeldata.create_netCDF_output_files(num_rows, num_cols, "eq", modeldata.eq_yrs, copy_gm);
    if(modeldata.eq_yrs > 100 && modeldata.daily_netcdf_outputs.size() > 0){
      BOOST_LOG_SEV(glg, fatal) << "Daily outputs specified with EQ run greater than 100 years! Reconsider...";
    }
  }
  if(modeldata.sp_yrs > 0 && modeldata.nc_sp){
    modeldata.create_netCDF_output_files(num_rows, num_cols, "sp", modeldata.sp_yrs, copy_gm);
  }
  if(modeldata.tr_yrs > 0 && modeldata.nc_tr){
    modeldata.create_netCDF_output_files(num_rows, num_cols, "tr", modeldata.tr_yrs, copy_gm);
  }
  if(modeldata.sc_yrs > 0 && modeldata.nc_sc){
    modeldata.create_netCDF_output_files(num_rows, num_cols, "sc", modeldata.sc_yrs, copy_gm);
  }

  // Warn if CMTNUM output is not enabled.
  bool cmtoutput_enabled = false;
  boost::filesystem::directory_iterator end;
  for (boost::filesystem::directory_iterator fsdi(boost::filesystem::path(modeldata.output_dir)); fsdi != end; ++fsdi) {
    if ((*fsdi).path().string().find("CMTNUM") != std::string::npos) {
      BOOST_LOG_SEV(glg, info) << "Looks good, CMTNUM output is enabled: " << *fsdi;
      cmtoutput_enabled = true;
      break;
    }
  }
  if (!cmtoutput_enabled) {
    BOOST_LOG_SEV(glg, warn) << "Looks like CMTNUM output is NOT enabled."
                            << " Strongly recommended to enable this output!"
                            << " Use util/outspec.py to turn on the CMTNUM output!";
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
#ifdef WITHMPI
    BOOST_LOG_SEV(glg, info) << "Beginning MPI parallel section";

    int id, ntasks;
    MPI_Comm_rank(MPI_COMM_WORLD, &id);
    MPI_Comm_size(MPI_COMM_WORLD, &ntasks);

    int total_cells = num_rows*num_cols;

    BOOST_LOG_SEV(glg, debug) << "id: "<<id<<" of ntasks: "<<ntasks;

    #pragma omp parallel for schedule(dynamic)
    for(int curr_cell=id; curr_cell<total_cells; curr_cell+=ntasks){

      int rowidx = curr_cell / num_cols;
      int colidx = curr_cell % num_cols;

      bool mask_value = run_mask[rowidx][colidx];
      BOOST_LOG_SEV(glg, monitor) << "MPI rank: "<<id<<", cell: "<<rowidx\
                                  << ", "<<colidx<<" run: "<<mask_value;

#else
    BOOST_LOG_SEV(glg, debug) << "Not built with MPI";

   #pragma omp parallel for collapse(2) schedule(dynamic)
    for(int rowidx=0; rowidx<num_rows; rowidx++){
      for(int colidx=0; colidx<num_cols; colidx++){

        bool mask_value = run_mask[rowidx].at(colidx);

#endif

        if (true == mask_value) {

          // I think this is safe w/in our OpenMP block because I am
          // handling the exception here...
          // Not sure about other OpenMP pragama blocks w/in this one? Any
          // Exceptions would leak out of the inner pragma and be handled
          // by this try/catch??
          try {

            cell_stime = time(0);

            advance_model(rowidx, colidx, modeldata, args->get_cal_mode(), pr_restart_fname, eq_restart_fname, sp_restart_fname, tr_restart_fname, sc_restart_fname);

            cell_etime = time(0);

            BOOST_LOG_SEV(glg, info) << "Finished cell " << rowidx << ", " << colidx << ". Writing status file...";
            std::cout << "cell " << rowidx << ", " << colidx << " complete." << std::endl;
            write_status_info(run_status_fname, "run_status", rowidx, colidx, STATUS_SUCCESS);
            write_status_info(run_status_fname, "total_runtime", rowidx, colidx, difftime(cell_etime, cell_stime));
 
          }
          catch (const temutil::CellTimeExceeded& e) {
            BOOST_LOG_SEV(glg, warn) << "Time Exception (row, col): (" << rowidx << ", " << colidx << "): " << e.what();

            write_status_info(run_status_fname, "run_status", rowidx, colidx, STATUS_TIMEOUT); // <- what if this throws??
            BOOST_LOG_SEV(glg, warn) << "End of Time Exception handler";

          }
          catch (std::exception& e) {

            BOOST_LOG_SEV(glg, warn) << "EXCEPTION!! (row, col): (" << rowidx << ", " << colidx << "): " << e.what();

            // IS THIS THREAD SAFE??
            // IS IT SAFE WITH MPI??
            std::ofstream outfile;
            outfile.open((modeldata.output_dir + "fail_log.txt").c_str(), std::ios_base::app); // Append mode
            outfile << "EXCEPTION!! At pixel at (row, col): ("<<rowidx <<", "<<colidx<<") "<< e.what() <<"\n";
            outfile.close();

            // Write to fail_mask.nc file?? or json? might be good for visualization
            write_status_info(run_status_fname, "run_status", rowidx, colidx, STATUS_FAIL); // <- what if this throws??
            BOOST_LOG_SEV(glg, warn) << "End of exception handler.";

          }
        }//End of active cell
        else {
          BOOST_LOG_SEV(glg, monitor) << "Skipping cell (" << rowidx << ", " << colidx << ")";
          write_status_info(run_status_fname, "run_status", rowidx, colidx, STATUS_MASKED);
        }
 
#ifdef WITHMPI
    }
    MPI_Finalize();

#else
      }//end col loop
    }//end row loop

#endif
 
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

  BOOST_LOG_SEV(glg, info) << "Done with run (loop order: " << args->get_loop_order() << ")";

  etime = time(0);
  BOOST_LOG_SEV(glg, info) << "Total Seconds: " << difftime(etime, stime);
  //cout as well as log, since Atlas runs have logging disabled.
  std::cout << "Total Seconds: " << difftime(etime, stime) << std::endl;
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

/** Advance model. Attempt to drive the model thru the run-stages.
 * May throw exceptions. (Which kind?)
*/
void advance_model(const int rowidx, const int colidx,
                   const ModelData& modeldata, const bool calmode,
                   const std::string& pr_restart_fname,
                   const std::string& eq_restart_fname,
                   const std::string& sp_restart_fname,
                   const std::string& tr_restart_fname,
                   const std::string& sc_restart_fname) {

  BOOST_LOG_SEV(glg, info) << "Running cell (" << rowidx << ", " << colidx << ")";

  BOOST_LOG_SEV(glg, info) << "Setup the Runner object...";
  Runner runner(modeldata, calmode, rowidx, colidx);

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

    assert(modeldata.restart_from.empty() && 
      "You can't restart a pre-run! Make sure restart_from config setting is blank (empty string) or turn off pr years.");

    if (runner.calcontroller_ptr) {
      runner.calcontroller_ptr->handle_stage_start();
    }

    // turn off everything but env
    runner.cohort.md->set_envmodule(runner.cohort.md->pr_env);
    runner.cohort.md->set_bgcmodule(runner.cohort.md->pr_bgc);
    runner.cohort.md->set_nfeed(runner.cohort.md->pr_nfeed);
    runner.cohort.md->set_avlnflg(runner.cohort.md->pr_avln);
    runner.cohort.md->set_baseline(runner.cohort.md->pr_baseline);
    runner.cohort.md->set_dsbmodule(runner.cohort.md->pr_dsb);
    runner.cohort.md->set_dslmodule(runner.cohort.md->pr_dsl);
    runner.cohort.md->set_dynamic_lai_module(runner.cohort.md->pr_dyn_lai);

    BOOST_LOG_SEV(glg, debug) << "Ground, right before 'pre-run'. "
                              << runner.cohort.ground.layer_report_string("depth thermal");

    runner.run_years(0, modeldata.pr_yrs, "pre-run"); // climate is prepared w/in here.

    BOOST_LOG_SEV(glg, debug) << "Ground, right after 'pre-run'"
                              << runner.cohort.ground.layer_report_string("depth thermal");

    // Update restartdata structure from the running state
    runner.cohort.set_restartdata_from_state();

    runner.cohort.restartdata.verify_logical_values();
    BOOST_LOG_SEV(glg, debug) << "RestartData post PR";
    runner.cohort.restartdata.restartdata_to_log();

    BOOST_LOG_SEV(glg, info) << "Writing RestartData to: " << pr_restart_fname;
    runner.cohort.restartdata.write_pixel_to_ncfile(pr_restart_fname, rowidx, colidx);

    if (runner.calcontroller_ptr) {
      runner.calcontroller_ptr->handle_stage_end("pr");
    }

  }

  // EQUILIBRIUM STAGE (EQ)
  if (modeldata.eq_yrs > 0) {
    BOOST_LOG_NAMED_SCOPE("EQ");
    BOOST_LOG_SEV(glg, monitor) << "Equilibrium Initial Year Count: " << modeldata.eq_yrs;

    //assert( (modeldata.restart_from.length() < 1) && "You can't restart an equilibrium run!");
    assert( modeldata.restart_from.empty()  && 
      "You can't restart an eq run. Either turn off eq years, or set restart_from to an empty string!");
    
    if (runner.calcontroller_ptr) {
      runner.calcontroller_ptr->handle_stage_start();
    }

    runner.cohort.md->set_envmodule(runner.cohort.md->eq_env);
    runner.cohort.md->set_bgcmodule(runner.cohort.md->eq_bgc);
    runner.cohort.md->set_nfeed(runner.cohort.md->eq_nfeed);
    runner.cohort.md->set_avlnflg(runner.cohort.md->eq_avln);
    runner.cohort.md->set_baseline(runner.cohort.md->eq_baseline);
    runner.cohort.md->set_dsbmodule(runner.cohort.md->eq_dsb);
    runner.cohort.md->set_dslmodule(runner.cohort.md->eq_dsl);
    runner.cohort.md->set_dynamic_lai_module(runner.cohort.md->eq_dyn_lai);

    // This variable ensures that OpenMP threads do not modify
    // the shared modeldata.eq_yrs value.
    int fri_adj_eq_yrs = modeldata.eq_yrs;//EQ years adjusted by FRI if necessary
    if (runner.cohort.md->get_dsbmodule()) {
      // The transition to SP must occur at the completion of a
      // fire cycle (i.e. a year or two prior to the next fire).
      // To ensure this, re-set modeldata's EQ year count to an
      // even multiple of the FRI minus 2 (to be safe)
      if (modeldata.eq_yrs < runner.cohort.fire.getFRI()) {
        BOOST_LOG_SEV(glg, warn) << "The model will not run enough years to complete a disturbance cycle!";
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
    BOOST_LOG_SEV(glg, monitor) << "Running Equilibrium, " << fri_adj_eq_yrs << " years.";
    runner.run_years(0, fri_adj_eq_yrs, "eq-run");

    // Update restartdata structure from the running state
    runner.cohort.set_restartdata_from_state();

    runner.cohort.restartdata.verify_logical_values();
    BOOST_LOG_SEV(glg, debug) << "RestartData post EQ";
    runner.cohort.restartdata.restartdata_to_log();

    BOOST_LOG_SEV(glg, info) << "Writing RestartData to: " << eq_restart_fname;
    runner.cohort.restartdata.write_pixel_to_ncfile(eq_restart_fname, rowidx, colidx);

    if (modeldata.eq_yrs < runner.cohort.fire.getFRI()) {
      BOOST_LOG_SEV(glg, warn) << "The model did not run enough years to complete a disturbance cycle!";
    }

    if (runner.calcontroller_ptr) {
      runner.calcontroller_ptr->handle_stage_end("eq");
    }

  }

  // SPINUP STAGE (SP)
  if (modeldata.sp_yrs > 0) {
    BOOST_LOG_NAMED_SCOPE("SP");
    BOOST_LOG_SEV(glg, monitor) << "Running Spinup, " << modeldata.sp_yrs << " years.";

    if (runner.calcontroller_ptr) {
      runner.calcontroller_ptr->handle_stage_start();
    }

    runner.cohort.md->set_envmodule(runner.cohort.md->sp_env);
    runner.cohort.md->set_bgcmodule(runner.cohort.md->sp_bgc);
    runner.cohort.md->set_nfeed(runner.cohort.md->sp_nfeed);
    runner.cohort.md->set_avlnflg(runner.cohort.md->sp_avln);
    runner.cohort.md->set_baseline(runner.cohort.md->sp_baseline);
    runner.cohort.md->set_dsbmodule(runner.cohort.md->sp_dsb);
    runner.cohort.md->set_dslmodule(runner.cohort.md->sp_dsl);
    runner.cohort.md->set_dynamic_lai_module(runner.cohort.md->sp_dyn_lai);

    runner.cohort.climate.monthlycontainers2log();

    if ( modeldata.restart_from.empty() ) {
      BOOST_LOG_SEV(glg, warn) << "No restart file specified for SP stage. "
                               << "Using default EQ restart file from previous stage of this run: " << eq_restart_fname;
      BOOST_LOG_SEV(glg, debug) << "Loading RestartData from: " << eq_restart_fname;
      runner.cohort.restartdata.update_from_ncfile(eq_restart_fname, rowidx, colidx);
    } else {
      BOOST_LOG_SEV(glg, info) << "User specified restart file for SP stage: " << modeldata.restart_from;
      BOOST_LOG_SEV(glg, info) << "Restarting from: " << modeldata.restart_from;
      runner.cohort.restartdata.update_from_ncfile(modeldata.restart_from, rowidx, colidx);
    }
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

    BOOST_LOG_SEV(glg, info) << "Writing RestartData out to: " << sp_restart_fname;
    runner.cohort.restartdata.write_pixel_to_ncfile(sp_restart_fname, rowidx, colidx);

    if (runner.calcontroller_ptr) {
      runner.calcontroller_ptr->handle_stage_end("sp");
    }

  }

  // TRANSIENT STAGE (TR)
  if (modeldata.tr_yrs > 0) {
    BOOST_LOG_NAMED_SCOPE("TR");
    BOOST_LOG_SEV(glg, monitor) << "Running Transient, " << modeldata.tr_yrs << " years";

    if (runner.calcontroller_ptr) {
      runner.calcontroller_ptr->handle_stage_start();
    }

    runner.cohort.md->set_envmodule(runner.cohort.md->tr_env);
    runner.cohort.md->set_bgcmodule(runner.cohort.md->tr_bgc);
    runner.cohort.md->set_nfeed(runner.cohort.md->tr_nfeed);
    runner.cohort.md->set_avlnflg(runner.cohort.md->tr_avln);
    runner.cohort.md->set_baseline(runner.cohort.md->tr_baseline);
    runner.cohort.md->set_dsbmodule(runner.cohort.md->tr_dsb);
    runner.cohort.md->set_dslmodule(runner.cohort.md->tr_dsl);
    runner.cohort.md->set_dynamic_lai_module(runner.cohort.md->tr_dyn_lai);

    if ( modeldata.restart_from.empty() ) {
      BOOST_LOG_SEV(glg, warn) << "No restart file specified for TR stage. "
                               << "Using default SP restart file from previous stage of this run: " << sp_restart_fname;
      BOOST_LOG_SEV(glg, debug) << "Loading RestartData from: " << sp_restart_fname;
      runner.cohort.restartdata.update_from_ncfile(sp_restart_fname, rowidx, colidx);
    } else {
      BOOST_LOG_SEV(glg, info) << "User specified restart file for SP stage: " << modeldata.restart_from;
      BOOST_LOG_SEV(glg, info) << "Restarting from: " << modeldata.restart_from;
      runner.cohort.restartdata.update_from_ncfile(modeldata.restart_from, rowidx, colidx);
    }


    runner.cohort.restartdata.verify_logical_values();

    BOOST_LOG_SEV(glg, debug) << "RestartData pre TR";
    runner.cohort.restartdata.restartdata_to_log();

    // Copy values from the updated restart data to cohort and cd
    runner.cohort.set_state_from_restartdata();

    BOOST_LOG_SEV(glg, warn) << "MAKE SURE YOUR FIRE INPUTS ARE SETUP CORRECTLY!";

    // Run model
    runner.run_years(0, modeldata.tr_yrs, "tr-run");

    // Update restartdata structure from the running state
    runner.cohort.set_restartdata_from_state();

    BOOST_LOG_SEV(glg, debug) << "RestartData post TR";
    runner.cohort.restartdata.restartdata_to_log();

    BOOST_LOG_SEV(glg, info) << "Writing RestartData out to: " << tr_restart_fname;
    runner.cohort.restartdata.write_pixel_to_ncfile(tr_restart_fname, rowidx, colidx);

    if (runner.calcontroller_ptr) {
      runner.calcontroller_ptr->handle_stage_end("tr");
    }

  }

  // SCENARIO STAGE (SC)
  if (modeldata.sc_yrs > 0) {
    BOOST_LOG_NAMED_SCOPE("SC");
    BOOST_LOG_SEV(glg, monitor) << "Running Scenario, " << modeldata.sc_yrs << " years.";

    if (runner.calcontroller_ptr) {
      runner.calcontroller_ptr->handle_stage_start();
    }

    runner.cohort.md->set_envmodule(runner.cohort.md->sc_env);
    runner.cohort.md->set_bgcmodule(runner.cohort.md->sc_bgc);
    runner.cohort.md->set_nfeed(runner.cohort.md->sc_nfeed);
    runner.cohort.md->set_avlnflg(runner.cohort.md->sc_avln);
    runner.cohort.md->set_baseline(runner.cohort.md->sc_baseline);
    runner.cohort.md->set_dsbmodule(runner.cohort.md->sc_dsb);
    runner.cohort.md->set_dslmodule(runner.cohort.md->sc_dsl);
    runner.cohort.md->set_dynamic_lai_module(runner.cohort.md->sc_dyn_lai);

    // update the cohort's restart data object

    if ( modeldata.restart_from.empty() ) {
      BOOST_LOG_SEV(glg, warn) << "No restart file specified for SC stage. "
                               << "Using default TR restart file from previous stage of this run: " << tr_restart_fname;
      BOOST_LOG_SEV(glg, debug) << "Loading RestartData from: " << tr_restart_fname;
      runner.cohort.restartdata.update_from_ncfile(tr_restart_fname, rowidx, colidx);
    } else {
      BOOST_LOG_SEV(glg, info) << "User specified restart file for SC stage: " << modeldata.restart_from;
      BOOST_LOG_SEV(glg, info) << "Restarting from: " << modeldata.restart_from;
      runner.cohort.restartdata.update_from_ncfile(modeldata.restart_from, rowidx, colidx);
    }


    BOOST_LOG_SEV(glg, debug) << "RestartData pre SC";
    runner.cohort.restartdata.restartdata_to_log();

    // Copy values from the updated restart data to cohort and cd
    runner.cohort.set_state_from_restartdata();

    // Loading projected data instead of historic. FIX?
    runner.cohort.load_proj_climate(modeldata.proj_climate_file);
    runner.cohort.load_proj_co2(modeldata.proj_co2_file);
    runner.cohort.load_proj_explicit_fire(modeldata.proj_exp_fire_file);

    BOOST_LOG_SEV(glg, warn) << "MAKE SURE YOUR FIRE INPUTS ARE SETUP CORRECTLY!";

    // Run model
    runner.run_years(0, modeldata.sc_yrs, "sc-run");

    // Update restartdata structure from the running state
    runner.cohort.set_restartdata_from_state();

    BOOST_LOG_SEV(glg, debug) << "RestartData post SC";
    runner.cohort.restartdata.restartdata_to_log();

    BOOST_LOG_SEV(glg, info) << "Writing RestartData out to: " << sc_restart_fname;
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




} // end advance_model

/** Creates (overwrites) an empty run_status file. */
void create_empty_run_status_file(const std::string& fname,
    const int ysize, const int xsize) {

  BOOST_LOG_SEV(glg, debug) << "Creating new file: "<<fname<<" with 'NC_CLOBBER'";
  int ncid;


#ifdef WITHMPI

  int id, ntasks;
  MPI_Comm_rank(MPI_COMM_WORLD, &id);
  MPI_Comm_size(MPI_COMM_WORLD, &ntasks);

                            // path            c mode               mpi comm obj     mpi info netcdfid
  temutil::nc( nc_create_par(fname.c_str(), NC_CLOBBER|NC_NETCDF4|NC_MPIIO, MPI_COMM_WORLD, MPI_INFO_NULL, &ncid) );

  BOOST_LOG_SEV(glg, debug) << "(MPI " << id << "/" << ntasks << ") Creating PARALLEL run_status file! \n";

#else

  BOOST_LOG_SEV(glg, debug) << "Opening new file with 'NC_CLOBBER'";
  temutil::nc( nc_create(fname.c_str(), NC_CLOBBER, &ncid) );

#endif

  // Define handles for dimensions
  int yD;
  int xD;

  BOOST_LOG_SEV(glg, debug) << "Creating nc dimensions ["<<fname<<"]";
  temutil::nc( nc_def_dim(ncid, "Y", ysize, &yD) );
  temutil::nc( nc_def_dim(ncid, "X", xsize, &xD) );

  // Setup arrays holding dimids for different "types" of variables
  // --> will re-arrange these later to define variables with different dims
  int vartype2D_dimids[2];
  vartype2D_dimids[0] = yD;
  vartype2D_dimids[1] = xD;

  // Setup 2D vars, integer
  // Define handle for variable(s)
  int run_statusV;
  int total_runtimeV;
  
  // Create variables in nc file and add attributes where relevant
  // Status
  temutil::nc( nc_def_var(ncid, "run_status", NC_INT, 2, vartype2D_dimids, &run_statusV) );
  temutil::nc( nc_put_att_int(ncid, run_statusV, "_FillValue", NC_INT, 1, &MISSING_I) );
  temutil::nc( nc_put_att_int(ncid, run_statusV, "success", NC_INT, 1, &STATUS_SUCCESS) );
  temutil::nc( nc_put_att_int(ncid, run_statusV, "masked", NC_INT, 1, &STATUS_MASKED) );
  temutil::nc( nc_put_att_int(ncid, run_statusV, "timeout", NC_INT, 1, &STATUS_TIMEOUT) );
  temutil::nc( nc_put_att_int(ncid, run_statusV, "fail", NC_INT, 1, &STATUS_FAIL) );

  // Runtime
  temutil::nc( nc_def_var(ncid, "total_runtime", NC_INT, 2, vartype2D_dimids, &total_runtimeV) );
  temutil::nc( nc_put_att_int(ncid, total_runtimeV, "_FillValue", NC_INT, 1, &MISSING_I) );
  std::string runtime_units = "seconds";
  temutil::nc( nc_put_att_text(ncid, total_runtimeV, "units", runtime_units.length(), runtime_units.c_str()) );

  // Global attributes
  temutil::nc( nc_put_att_text(ncid, NC_GLOBAL, "Git_SHA", strlen(GIT_SHA), GIT_SHA) );

  /* End Define Mode (not strictly necessary for netcdf 4) */
  BOOST_LOG_SEV(glg, debug) << "Leaving 'define mode' ["<<fname<<"]";
  try {
    temutil::nc( nc_enddef(ncid) );
  } catch (const temutil::NetCDFDefineModeException& e) {
    BOOST_LOG_SEV(glg, info) << "Error ending define mode: " << e.what();
  }

  /* Close file. */
  BOOST_LOG_SEV(glg, debug) << "Closing new file ["<<fname<<"]";
  temutil::nc( nc_close(ncid) );

}

void write_status_info(const std::string fname, std::string varname, int row, int col, int statusCode) {

  int ncid;
  int statusV;

  int NDIMS = 2;

  size_t start[NDIMS], count[NDIMS];
  // Set point to write
  start[0] = row;
  start[1] = col;

  BOOST_LOG_SEV(glg, debug) << "Opening status file: " << fname;

#ifdef WITHMPI

  // These are for logging identification only.
  int id, ntasks;
  MPI_Comm_rank(MPI_COMM_WORLD, &id);
  MPI_Comm_size(MPI_COMM_WORLD, &ntasks);

  // Open dataset
  temutil::nc( nc_open_par(fname.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
  //temutil::nc( nc_inq_varid(ncid, "run_status", &statusV) );
  temutil::nc( nc_inq_varid(ncid, varname.c_str(), &statusV) );
  temutil::nc( nc_var_par_access(ncid, statusV, NC_INDEPENDENT) );

  // Write data
  BOOST_LOG_SEV(glg, info) << "(MPI " << id << "/" << ntasks << ") WRITING "<< varname << " for pixel (row, col): " << row << ", " << col << "\n";
  temutil::nc( nc_put_var1_int(ncid, statusV, start,  &statusCode) );

  /* Close the netcdf file. */
  BOOST_LOG_SEV(glg, debug) << "(MPI " << id << "/" << ntasks << ") Closing PARALLEL file." << row << ", " << col << "\n";
  temutil::nc( nc_close(ncid) );
#else

  // Open dataset
  temutil::nc( nc_open(fname.c_str(), NC_WRITE, &ncid) );
  temutil::nc( nc_inq_varid(ncid, varname.c_str(), &statusV) );
  
  // Write data
  BOOST_LOG_SEV(glg, info) << "WRITING "<< varname <<" for (row, col): " << row << ", " << col << "\n";
  temutil::nc( nc_put_var1_int(ncid, statusV, start, &statusCode) );

  /* Close the netcdf file. */
  temutil::nc( nc_close(ncid) );

#endif
}
