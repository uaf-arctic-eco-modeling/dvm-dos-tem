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

// draft - reading in a 2D run mask...
std::vector< std::vector<int> > read_run_mask(const std::string &filename);

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

struct NetcdfOutputTypes {
  double daily;
  double monthly;
  double yearly;
  NetcdfOutputTypes():daily(0), monthly(0), yearly(0) {}
};

struct JsonOutputTypes {
  double archive;
  double daily;
  double monthly;
  double yearly;

  int jcoef_archive;
  int jcoef_daily;
  int jcoef_monthly;
  int jcoef_yearly;

  JsonOutputTypes(int _jca, int _jcd, int _jcm, int _jcy):
    archive(0), daily(0), monthly(0), yearly(0),
    jcoef_archive(_jca), jcoef_daily(_jcd), jcoef_monthly(_jcm), jcoef_yearly(_jcy) {}
};

/** Holds the ouput volume estimate for a run-stage. Notes:
 *   - sizes are in bytes
 *   - for all years represented by runyears
 *   - for one cell
 */
struct StageOutputEstimate {
  std::string name;
  int runyears;
  NetcdfOutputTypes nc_out;
  JsonOutputTypes json_out;
  StageOutputEstimate(
      const std::string& _name, int _yrs,
      int _jca, int _jcd, int _jcm, int _jcy):
    name(_name),
    runyears(_yrs),
    nc_out(),
    json_out(_jca, _jcd, _jcm, _jcy){}
};

class OutputEstimate {

  /** Returns a 'human readable' size string with SI suffix */
  std::string hsize(double size) {
    int i = 0;
    const std::string units[] = {"B","kB","MB","GB","TB","PB","EB","ZB","YB"};
    while (size > 1024) {
      size /= 1024;
      i++;
    }
    std::stringstream ss;
    ss.precision(0);
    (size < 0.5) ? size = 0 : size=size;
    ss << fixed << size << " " << units[i];
    std::string size_string = ss.str();
    return size_string;
  }


  int active_cells;
  std::vector<StageOutputEstimate> stage_output_estimates;

public:

  OutputEstimate(const ModelData& md, bool calmode) {

    stage_output_estimates = boost::assign::list_of
        // Table of coefficients for bytes per year of run-time for
        // each stage and different types of json output (archive, daily, etc).
        (StageOutputEstimate("pr", md.pr_yrs, 22000,  41000,  200000,  20000))
        (StageOutputEstimate("eq", md.eq_yrs, 56000,  41000,  240000,  24000))
        (StageOutputEstimate("sp", md.sp_yrs, 15000,  36000,  199000,  16000))
        (StageOutputEstimate("tr", md.tr_yrs, 15000,  36000,  199000,  16000))
        (StageOutputEstimate("sc", md.sc_yrs, 15000,  36000,  199000,  16000));

    // Open the run mask (spatial mask) and count all the non-zero cells.
    std::vector< std::vector<int> > run_mask = read_run_mask(md.runmask_file);

    this->active_cells = 0;

    // Use a few type definitions to save some typing.
    typedef std::vector<int> vec;
    typedef std::vector<vec> vec2D;

    vec2D::const_iterator row;
    vec::const_iterator col;
    for (row = run_mask.begin(); row != run_mask.end() ; ++row) {
      for (col = row->begin(); col != row->end(); ++col) {
        bool mask_value = *col;
        if (mask_value) {this->active_cells++;}
      }
    }

    std::cout << "Number of active cells: " << this->active_cells << std::endl;

    std::vector<StageOutputEstimate>::iterator itr;
    for (itr = stage_output_estimates.begin(); itr != stage_output_estimates.end(); itr++){

      std::cout << "Estimating output for stage: " << itr->name << std::endl;
      // handle all the calibration/json stuff
      if (calmode) {
        // cal mode means at least yearly and daily
        std::cout << "Estimating CALIBRATION output" << std::endl;
        itr->json_out.yearly = itr->runyears * itr->json_out.jcoef_yearly;
        itr->json_out.daily = itr->runyears * itr->json_out.jcoef_daily;

        // setting in config file
        if (md.output_monthly) {
          itr->json_out.monthly = itr->runyears * itr->json_out.jcoef_monthly;
        } else {
          itr->json_out.monthly = 0;
        }

        // could be an overestimate if user does not have monthly enabled too?
        if (md.tar_caljson) {
          itr->json_out.archive = itr->runyears * itr->json_out.jcoef_archive;
        } else {
          itr->json_out.archive = 0;
        }
      }

      // Handle the NetCDF stuff...
      double D_est = 0; double M_est = 0; double Y_est = 0;

      // yearly
      std::cout << "Estimating YEARLY NC output for stage: " << itr->name << std::endl;
      std::map<std::string, OutputSpec>::const_iterator map_itr;
      for(map_itr = md.yearly_netcdf_outputs.begin(); map_itr != md.yearly_netcdf_outputs.end(); ++map_itr ){

        double output_estimate = 8;
        OutputSpec os = map_itr->second;

        (os.pft) ? (output_estimate *= NUM_PFT) : output_estimate *= 1;
        (os.compartment) ? (output_estimate *= NUM_PFT_PART) : output_estimate *= 1;
        (os.layer) ? (output_estimate *= MAX_SOI_LAY) : output_estimate *= 1;
        (os.yearly) ? (output_estimate *= (1 * itr->runyears)) : output_estimate *= 1;

        Y_est += output_estimate;
      }
      map_itr = md.yearly_netcdf_outputs.end();

      // monthly
      std::cout << "Estimating MONTHLY NC output for stage: " << itr->name << std::endl;
      for(map_itr = md.monthly_netcdf_outputs.begin(); map_itr != md.monthly_netcdf_outputs.end(); ++map_itr ){

        double output_estimate = 8;
        OutputSpec os = map_itr->second;

        (os.pft) ? (output_estimate *= NUM_PFT) : output_estimate *= 1;
        (os.compartment) ? (output_estimate *= NUM_PFT_PART) : output_estimate *= 1;
        (os.layer) ? (output_estimate *= MAX_SOI_LAY) : output_estimate *= 1;
        (os.monthly) ? (output_estimate *= (12 * itr->runyears)) : output_estimate *= 1;

        M_est += output_estimate;
      }
      map_itr = md.monthly_netcdf_outputs.end();

      // daily
      std::cout << "Estimating DAILY NC output for stage: " << itr->name << std::endl;
      for(map_itr = md.daily_netcdf_outputs.begin(); map_itr != md.daily_netcdf_outputs.end(); ++map_itr ){

        double output_estimate = 8;
        OutputSpec os = map_itr->second;

        (os.pft) ? (output_estimate *= NUM_PFT) : output_estimate *= 1;
        (os.compartment) ? (output_estimate *= NUM_PFT_PART) : output_estimate *= 1;
        (os.layer) ? (output_estimate *= MAX_SOI_LAY) : output_estimate *= 1;
        (os.daily) ? (output_estimate *= (365 * itr->runyears)) : output_estimate *= 1;

        D_est += output_estimate;
      }
      map_itr = md.daily_netcdf_outputs.end();

      itr->nc_out.yearly = Y_est;
      itr->nc_out.monthly = M_est;
      itr->nc_out.daily = D_est;

    }
    //std::cout << "SET BREAKPOINT HERE\n";
  }

  void print_estimate(){

    std::stringstream ss;
    std::vector<StageOutputEstimate>::iterator itr;

    ss << "-- calibration json output data volume estimates: " << hsize(json_total()) << std::endl;
    ss << std::setw(10) << " "
       << std::setw(10) << "run years"
       << std::setw(10) << "archive"
       << std::setw(10) << "daily"
       << std::setw(10) << "monthly"
       << std::setw(10) << "yearly"
       << std::endl;
    for (itr = stage_output_estimates.begin(); itr != stage_output_estimates.end(); itr++) {
      ss << std::setw(10) << (*itr).name
         << std::setw(10) << (*itr).runyears
         << std::setw(10) << hsize((*itr).json_out.archive)
         << std::setw(10) << hsize((*itr).json_out.daily)
         << std::setw(10) << hsize((*itr).json_out.monthly)
         << std::setw(10) << hsize((*itr).json_out.yearly)
         << std::endl;
    }
    itr = stage_output_estimates.end();
    std::cout << ss.str();
    std::cout << std::endl;
    ss.str("");
    ss.clear(); // clear state flags

    ss << "-- netcdf output data volume estimate: " << hsize(netcdf_total()) << std::endl;
    ss << std::setw(10) << " "
       << std::setw(10) << "run years"
       << std::setw(10) << "daily"
       << std::setw(10) << "monthly"
       << std::setw(10) << "yearly"
       << std::endl;

    for (itr = stage_output_estimates.begin(); itr != stage_output_estimates.end(); itr++) {
      ss << std::setw(10) << (*itr).name;
      ss << std::setw(10) << (*itr).runyears;
      ss << std::setw(10) << hsize((*itr).nc_out.daily);
      ss << std::setw(10) << hsize((*itr).nc_out.monthly);
      ss << std::setw(10) << hsize((*itr).nc_out.yearly);
      ss << std::endl;
    }
    itr = stage_output_estimates.end();
    std::cout << ss.str();
    std::cout << std::endl;
    ss.str("");
    ss.clear(); // clear state flags

    std::cout << "Cell Total: " << hsize(this->cell_total()) << std::endl;
    std::cout << "All cells: " << hsize(this->all_cells_total()) << std::endl;
  }

  double netcdf_total() {
    double t = 0;
    std::vector<StageOutputEstimate>::iterator itr;
    for (itr = stage_output_estimates.begin(); itr != stage_output_estimates.end(); itr++) {
      t += (*itr).nc_out.daily;
      t += (*itr).nc_out.monthly;
      t += (*itr).nc_out.yearly;
    }
    return t;
  }

  double json_total() {
    // This will probably over-estimate, as the yearly/monthly/daily outputs
    // are deleted for each stage. Maybe should find the stage with the max
    // runyears and use that for the yearly/monthly/daily estimates.
    double t = 0;
    std::vector<StageOutputEstimate>::iterator itr;
    for (itr = stage_output_estimates.begin(); itr != stage_output_estimates.end(); itr++) {
      t += (*itr).json_out.archive;
      t += (*itr).json_out.daily;
      t += (*itr).json_out.monthly;
      t += (*itr).json_out.yearly;
    }
    return t;
  }

  double cell_total() {
    double t = 0;
      t += json_total();
      t += netcdf_total();
    return t;
  }

  double all_cells_total() {
    return active_cells * (json_total() + netcdf_total());
  }

  /** (UNTESTED!) Given a string like "1.5 MB" should return a double (bytes). */
  int hsize2bytes(const std::string& sizestr) {
    // last 2 chars
    std::string hrunit = sizestr.substr(sizestr.size()-2, std::string::npos); // last 2 chars

    // first bit of string (till 2nd to last char), converted to dbl
    double size = atof(sizestr.substr(0, sizestr.size()-2).c_str());

    //assert( (size > 0 && size < ??) & "INVALID SIZE! CAN'T CONVERT!");

    std::vector<std::string> units = boost::assign::list_of("B")("kB")("MB")("GB")("TB")("PB")("EB")("ZB")("YB");

    //assert( !(std::find(units.begin(), units.end(), hrunit) != units.end()) & "INVALID UNITS!!" );

    int i = 0;
    while ( !(hrunit.compare(units[i])) == 0 )  {
      size *= 1024;
      i++;
    }
    return size; // in bytes
  }

// ideas for  API functions
//  oe.per_grid_cell()
//  oe.per_year()
//  oe.print_table()

};



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
  std::vector< std::vector<int> > run_mask = read_run_mask(modeldata.runmask_file);

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

  OutputEstimate oe = OutputEstimate(modeldata, args->get_cal_mode());
  oe.print_estimate();
  if ( oe.all_cells_total() > oe.hsize2bytes("1 GB") ) {
    BOOST_LOG_SEV(glg, fatal) << "TOO MUCH OUTPUT SPECIFIED! ADJUST YOUR SETTINGS AND TRY AGAIN. Or run with '--force-output'";
    exit(-1);
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
    for (row = run_mask.begin(); row != run_mask.end() ; ++row) {
      for (col = row->begin(); col != row->end(); ++col) {

        bool mask_value = *col;

        int rowidx = row - run_mask.begin();
        int colidx = col - row->begin();

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
            BOOST_LOG_SEV(glg, fatal) << "Running Equilibrium, " << modeldata.eq_yrs << " years.";

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
                  modeldata.eq_yrs = fri * (EQ_fire_cycles + 1) - 2;
                }
              }
            }

            // Run model
            runner.run_years(0, modeldata.eq_yrs, "eq-run");

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
      }
    }
  
    
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

/** rough draft for reading a run-mask (2D vector of ints)
*/
std::vector< std::vector<int> > read_run_mask(const std::string &filename) {
  int ncid;
  
  BOOST_LOG_SEV(glg, debug) << "Opening dataset: " << filename;
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


