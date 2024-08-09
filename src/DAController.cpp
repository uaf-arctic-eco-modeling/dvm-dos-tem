#include <iostream>
#include <string>
#include <map>

#include <boost/asio.hpp>
#include <boost/asio/signal_set.hpp>
#include <boost/bind.hpp>
#include <boost/filesystem.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/tokenizer.hpp>
#include <boost/lexical_cast.hpp>

#include "../include/DAController.h"
#include "../include/TEMLogger.h"
#include "../include/Cohort.h"
#include "../include/TEMUtilityFunctions.h"

extern src::severity_logger< severity_level > glg;

/** An object for controlling data assimilation
*/
DAController::DAController(){
//DAController::DAController():
//  io_service(new boost::asio::io_service),
//  pause_sigs(*io_service, SIGINT, SIGTERM){
//  cohort_ptr(cht_p) {
//  cmd_map = {
//            {"q", CalCommand("quit the calibrator",
//                             boost::bind(&CalController::quit, this)) },
//            {"c",
//              CalCommand("continue simulation",
//                          boost::bind(&CalController::continue_simulation,
//                                      this)) },
//            {"r",
//              CalCommand("reload calparbgc file",
//                          boost::bind(&CalController::reload_calparbgc_file,
//                                      this)) },
//            {"reload all",
//              CalCommand("reload all cmt files",
//                          boost::bind(&CalController::reload_all_cmt_files,
//                                      this)) },
//            {"h",
//              CalCommand("show short menu",
//                          boost::bind(&CalController::show_short_menu, this)) },
//            {"help",
//              CalCommand("show full menu",
//                          boost::bind(&CalController::show_full_menu, this)) },
//
//            {"print calparbgc",
//              CalCommand("prints out the calparbgc parameters ",
//                         boost::bind(&CalController::print_calparbgc, this)) },
//            {"print module settings",
//              CalCommand("print module settings (on/off)",
//                         boost::bind(&CalController::print_modules_settings, this)) },
//
//            {"print directives",
//              CalCommand("show data from the run_configuration data structure",
//                         boost::bind(&CalController::print_directive_settings, this)) },
//
//            {"quitat",
//              CalCommand("quits and exits at simulation year specified",
//                         boost::bind(&CalController::quit_at, this, _1)) },
//            {"pauseat",
//              CalCommand("pauses at simulation year specified",
//                         boost::bind(&CalController::pause_at, this, _1)) },
//            };

//  BOOST_LOG_SEV(glg, debug) << "Set async wait on signals to PAUSE handler.";
//  pause_sigs.async_wait( boost::bind(&CalController::pause_handler, this,
//                                     boost::asio::placeholders::error,
//                                     boost::asio::placeholders::signal_number));

//  this->run_configuration =
//      this->load_directives_from_file("config/calibration_directives.txt");

//  this->set_caljson_storage_paths();
//  this->clear_and_create_json_storage();
//  this->clear_archived_json();

//  if (!this->cohort_ptr) {
//    BOOST_LOG_SEV(glg, warn) << "Something is wrong and the Cohort pointer is null!";
//  }


  //TODO replace placeholder - artificially constructing outspec for testing
  boost::filesystem::path output_base = "output/";
  this->outspec.file_path = output_base.string();
  this->outspec.filename_prefix = "DA_statefile"; //ALD_monthly
  this->outspec.var_name = "TEM_LAI";
  this->outspec.data_type = NC_DOUBLE;
  this->outspec.dim_count = 3;//Maybe?

  create_da_nc_file();

  load_pause_dates();

  pause_this_month = false;
  pause_this_year = false;

  BOOST_LOG_SEV(glg, debug) << "Done constructing a DAController.";
}

void DAController::set_month_pause(bool new_state){
  pause_this_month = new_state;
}

bool DAController::get_month_pause(){
  return pause_this_month;
}

/** Forcibly pauses the simulation.
  * Writes to and reads from the external data assimilation process
  */
//void DAController::pause() {
//  BOOST_LOG_SEV(glg, info) << "Pausing for data assimilation";
  //write_DA_var();
  //watch file for change? How to tell when to unpause?
  //Might need to have a command input similar to CalController
  //read_DA_var();
  //control_loop();
//}

/** Writes a DA variable to file for an external DA process
  */
//void DAController::write_DA_var(){
//}


enum stage_idx {
  pr_idx, eq_idx, sp_idx, tr_idx, sc_idx
};


/** Checks for a pause at the current monthly timestep
  */
bool DAController::check_for_pause(timestep_id current_step){
  //iterators to pause_dates
  std::vector<timestep_id>::iterator it = pause_dates.begin();

  while(it != pause_dates.end()){
    if(it->stage == current_step.stage
       && it->year == current_step.year
       && it->month == current_step.month){

      //remove first pause?
      return true;
    }
    it++;
  }

  return false;
}


void DAController::print_pause_dates(){
  BOOST_LOG_SEV(glg, fatal) << "DAController pause times:";
  std::vector<timestep_id>::iterator it = pause_dates.begin();

  while(it != pause_dates.end()){
    BOOST_LOG_SEV(glg, fatal) << it->stage << " " << it->year << " " << it->month << std::endl;
    it++;
  }
}


/** Loads timesteps to pause for DA from a csv file
  */
void DAController::load_pause_dates(){
  std::string timestep_file = "./config/DA_timesteps_LAI.csv";

  BOOST_LOG_SEV(glg, fatal) << "Opening DA file: " << timestep_file;
  //x, y, stage, year, month, day 
  std::ifstream ts_stream(timestep_file);

  if(ts_stream.is_open()){
    std::string line;

    std::string token;

    while(std::getline(ts_stream, line)){
      std::cout<<line<<std::endl;
      if(line.find("//")!=std::string::npos){//skipping headers and comments
        continue;
      }

      std::istringstream ss(line);
      timestep_id new_pause;

      for(int ii=0; ii<6; ii++){
        std::getline(ss, token, ',');

        if(ii == 0){//x
          new_pause.x = atoi(token.c_str());
        }
        else if(ii == 1){//y
          new_pause.y = atoi(token.c_str());
        } 
        else if(ii == 2){//stage
          new_pause.stage = token;
        }
        else if(ii == 3){//year
          new_pause.year = atoi(token.c_str());
        }
        else if(ii == 4){//month
          new_pause.month = atoi(token.c_str());
        }  
        else if(ii == 5){//day
          //new_pause.day = std::stoi(token);
        }
      }
      pause_dates.push_back(new_pause);
    }
    this->print_pause_dates();
    BOOST_LOG_SEV(glg, fatal) << "DA timestep loading complete";
  }
}




void DAController::create_da_nc_file(){

  boost::filesystem::path output_base = "output/";

  int ncid;
  std::string new_filename = "DA_statefile.nc";
  boost::filesystem::path output_filepath = output_base / new_filename;
  std::string new_file = output_filepath.string();

  BOOST_LOG_SEV(glg, info) << "Creating new DA LAI file: "<<new_file;
  this->da_filename = new_file;
  temutil::nc( nc_create(new_file.c_str(), NC_CLOBBER|NC_NETCDF4, &ncid) );

  int yD, xD;
  int pftD, pftpartD;
  int soillayerD;

  temutil::nc( nc_def_dim(ncid, "y", 1, &yD) );
  temutil::nc( nc_def_dim(ncid, "x", 1, &xD) );

  temutil::nc( nc_def_dim(ncid, "pft", NUM_PFT, &pftD) );
  temutil::nc( nc_def_dim(ncid, "pftpart", NUM_PFT_PART, &pftpartD) );
  temutil::nc( nc_def_dim(ncid, "soillayer", MAX_SOI_LAY, &soillayerD) );

  int vartype2D_dimids[2];
  vartype2D_dimids[0] = yD;
  vartype2D_dimids[1] = xD;

  int vartype3D_dimids[3];
  vartype3D_dimids[0] = yD;
  vartype3D_dimids[1] = xD;
  vartype3D_dimids[2] = soillayerD;

  int vartype4D_dimids[4];
  vartype4D_dimids[0] = yD;
  vartype4D_dimids[1] = xD;
  vartype4D_dimids[2] = pftpartD;
  vartype4D_dimids[3] = pftD;

  int temLAI_V, daLAI_V;
  int temVEGC_V, daVEGC_V;
  int temSTRN_V, daSTRN_V;

  //Timestep variable - single value

  //Vegetation variables
  temutil::nc( nc_def_var(ncid, "TEM_LAI", NC_DOUBLE, 2, vartype2D_dimids, &temLAI_V) );
  temutil::nc( nc_def_var(ncid, "DA_LAI", NC_DOUBLE, 2, vartype2D_dimids, &daLAI_V) );

  temutil::nc( nc_def_var(ncid, "TEM_VEGC", NC_DOUBLE, 4, vartype4D_dimids, &temVEGC_V) );
  temutil::nc( nc_def_var(ncid, "DA_VEGC", NC_DOUBLE, 4, vartype4D_dimids, &daVEGC_V) );

  temutil::nc( nc_def_var(ncid, "TEM_STRN", NC_DOUBLE, 4, vartype4D_dimids, &temSTRN_V) );
  temutil::nc( nc_def_var(ncid, "DA_STRN", NC_DOUBLE, 4, vartype4D_dimids, &daSTRN_V) );

  //Soil variables
  int temLWC_V, daLWC_V;
  int temRAWC_V, daRAWC_V;
  int temSOMA_V, daSOMA_V;
  int temSOMPR_V, daSOMPR_V;
  int temSOMCR_V, daSOMCR_V;

  temutil::nc( nc_def_var(ncid, "TEM_LWC", NC_DOUBLE, 3, vartype3D_dimids, &temLWC_V) );
  temutil::nc( nc_def_var(ncid, "DA_LWC", NC_DOUBLE, 3, vartype3D_dimids, &daLWC_V) );

  temutil::nc( nc_def_var(ncid, "TEM_RAWC", NC_DOUBLE, 3, vartype3D_dimids, &temRAWC_V) );
  temutil::nc( nc_def_var(ncid, "DA_RAWC", NC_DOUBLE, 3, vartype3D_dimids, &daRAWC_V) );

  temutil::nc( nc_def_var(ncid, "TEM_SOMA", NC_DOUBLE, 3, vartype3D_dimids, &temSOMA_V) );
  temutil::nc( nc_def_var(ncid, "DA_SOMA", NC_DOUBLE, 3, vartype3D_dimids, &daSOMA_V) );

  temutil::nc( nc_def_var(ncid, "TEM_SOMPR", NC_DOUBLE, 3, vartype3D_dimids, &temSOMPR_V) );
  temutil::nc( nc_def_var(ncid, "DA_SOMPR", NC_DOUBLE, 3, vartype3D_dimids, &daSOMPR_V) );

  temutil::nc( nc_def_var(ncid, "TEM_SOMCR", NC_DOUBLE, 3, vartype3D_dimids, &temSOMCR_V) );
  temutil::nc( nc_def_var(ncid, "DA_SOMCR", NC_DOUBLE, 3, vartype3D_dimids, &daSOMCR_V) );

  temutil::nc( nc_enddef(ncid) );
  temutil::nc( nc_close(ncid) );
}

