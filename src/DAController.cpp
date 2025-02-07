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

  this->sla_outspec.file_path = output_base.string();
  this->sla_outspec.filename_prefix = "DA_statefile";
  this->sla_outspec.var_name = "TEM_SLA";
  this->sla_outspec.data_type = NC_DOUBLE;

  this->lai_outspec.file_path = output_base.string();
  this->lai_outspec.filename_prefix = "DA_statefile";
  this->lai_outspec.var_name = "TEM_LAI";
  this->lai_outspec.data_type = NC_DOUBLE;
  this->lai_outspec.dim_count = 3;//Maybe?

  this->vegc_outspec.file_path = output_base.string();
  this->vegc_outspec.filename_prefix = "DA_statefile";
  this->vegc_outspec.var_name = "TEM_VEGC";
  this->vegc_outspec.data_type = NC_DOUBLE;
  this->vegc_outspec.dim_count = 5;//Maybe?

  this->strn_outspec.file_path = output_base.string();
  this->strn_outspec.filename_prefix = "DA_statefile";
  this->strn_outspec.var_name = "TEM_STRN";
  this->strn_outspec.data_type = NC_DOUBLE;

  this->lwc_outspec.file_path = output_base.string();
  this->lwc_outspec.filename_prefix = "DA_statefile";
  this->lwc_outspec.var_name = "TEM_LWC";
  this->lwc_outspec.data_type = NC_DOUBLE;

  this->rawc_outspec.file_path = output_base.string();
  this->rawc_outspec.filename_prefix = "DA_statefile";
  this->rawc_outspec.var_name = "TEM_RAWC";
  this->rawc_outspec.data_type = NC_DOUBLE;
  this->rawc_outspec.dim_count = 3;//Maybe?

  this->soma_outspec.file_path = output_base.string();
  this->soma_outspec.filename_prefix = "DA_statefile";
  this->soma_outspec.var_name = "TEM_SOMA";
  this->soma_outspec.data_type = NC_DOUBLE;

  this->sompr_outspec.file_path = output_base.string();
  this->sompr_outspec.filename_prefix = "DA_statefile";
  this->sompr_outspec.var_name = "TEM_SOMPR";
  this->sompr_outspec.data_type = NC_DOUBLE;

  this->somcr_outspec.file_path = output_base.string();
  this->somcr_outspec.filename_prefix = "DA_statefile";
  this->somcr_outspec.var_name = "TEM_SOMCR";
  this->somcr_outspec.data_type = NC_DOUBLE;

  this->layerdz_outspec.file_path = output_base.string();
  this->layerdz_outspec.filename_prefix = "DA_statefile";
  this->layerdz_outspec.var_name = "TEM_LAYERDZ";
  this->layerdz_outspec.data_type = NC_DOUBLE;

  this->tlayer_outspec.file_path = output_base.string();
  this->tlayer_outspec.filename_prefix = "DA_statefile";
  this->tlayer_outspec.var_name = "TEM_TLAYER";
  this->tlayer_outspec.data_type = NC_DOUBLE;


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


void DAController::run_DA_LAI(timestep_id current_step){

  //If not set to pause this time step
  if(!check_for_pause(current_step)){
    return;
  }

  BOOST_LOG_SEV(glg, debug) << "Data assimilation, LAI";

  cell_coords curr_coords(cohort->y, cohort->x);

  //Write parameters to file
  //sla
  temutil::output_nc_3dim_notime(&this->sla_outspec, ".nc", &curr_coords, &cohort->veg.vegdimpar.sla[0], NUM_PFT);

  //Write accessory variables to file
  //VEGC
  std::array<std::array<double, NUM_PFT>, NUM_PFT_PART> vegc = cohort->get_vegc_pftandcomp_monthly();
  temutil::output_nc_4dim_notime(&this->vegc_outspec, ".nc", &curr_coords, &vegc[0][0], NUM_PFT_PART, NUM_PFT);

  //STRN
  std::array<std::array<double, NUM_PFT>, NUM_PFT_PART> strn = cohort->get_strn_pftandcomp_monthly();
  temutil::output_nc_4dim_notime(&this->strn_outspec, ".nc", &curr_coords, &strn[0][0], NUM_PFT_PART, NUM_PFT);

  //LWC
  temutil::output_nc_3dim_notime(&this->lwc_outspec, ".nc", &curr_coords, &cohort->edall->m_soid.lwc[0], MAX_SOI_LAY);

  //SOMRAWC
  temutil::output_nc_3dim_notime(&this->rawc_outspec, ".nc", &curr_coords, &cohort->bdall->m_sois.rawc[0], MAX_SOI_LAY);

  //SOMA
  temutil::output_nc_3dim_notime(&this->soma_outspec, ".nc", &curr_coords, &cohort->bdall->m_sois.soma[0], MAX_SOI_LAY);

  //SOMPR
  temutil::output_nc_3dim_notime(&this->sompr_outspec, ".nc", &curr_coords, &cohort->bdall->m_sois.sompr[0], MAX_SOI_LAY);

  //SOMCR
  temutil::output_nc_3dim_notime(&this->somcr_outspec, ".nc", &curr_coords, &cohort->bdall->m_sois.somcr[0], MAX_SOI_LAY);

  //LAYERDZ (for reference, not to be updated by DA)
  temutil::output_nc_3dim_notime(&this->layerdz_outspec, ".nc", &curr_coords, &cohort->cd.m_soil.dz[0], MAX_SOI_LAY);

  //TLAYER (for reference, not to be updated by DA)
  temutil::output_nc_3dim_notime(&this->tlayer_outspec, ".nc", &curr_coords, &cohort->edall->m_sois.ts[0], MAX_SOI_LAY);

  //calculate LAI stuff
//  double totalLAI = 0.0;
//  std::vector<double> lai_by_pft;
//  for(int ip=0; ip<NUM_PFT; ip++){
//    double templai = cohort->cd.m_veg.lai[ip];
//    if(templai > 0){
//      lai_by_pft.push_back(templai);
//      totalLAI += templai;
//    }
//  }

  //write LAI to file
  temutil::output_nc_3dim_notime(&this->lai_outspec, ".nc", &curr_coords, &cohort->cd.m_veg.lai[0], NUM_PFT);
//  temutil::output_nc_3dim(&this->lai_outspec, ".nc", &curr_coords, &totalLAI, 1, 0, 1);
//  temutil::ppv(lai_by_pft);
//  std::cout<<"total lai: "<<totalLAI<<std::endl;

  //Write to "pause" file for controlling script to monitor
  std::string pause_filename = this->lai_outspec.file_path + "/model_pause.txt";
  std::ofstream pause_fh(pause_filename);
  if(pause_fh.is_open()){
    BOOST_LOG_SEV(glg, debug) << "Writing to DA pause indicator file";
    pause_fh << "Stage: " << current_step.stage
             << "\nYear: " << current_step.year
             << "\nMonth: " << current_step.month;
    pause_fh.close();
  }
  else{
    BOOST_LOG_SEV(glg, fatal) << "Unable to open pause indicator file";
  }

  //Block until DA has run and somehow signaled completion
  std::cout<<"Paused for DA, enter 'c' to continue"<<std::endl;
  char curr_input = 'p';
  while(curr_input != 'c'){
    std::cin>>curr_input;
  }

  BOOST_LOG_SEV(glg, note) << "Loading data assimilation values";

  BOOST_LOG_SEV(glg, debug) << "Loading DA values for LAI";
//  double newLAI;
//  newLAI = this->read_scalar_var("DA_LAI");
  //std::cout<<"new LAI: "<<newLAI<<std::endl;

  //Redistribute new LAI to PFTs based on original percentages
//  for(int ip=0; ip<NUM_PFT; ip++){
//    if(cohort->cd.m_veg.lai[ip] > 0){
//      cohort->cd.m_veg.lai[ip] = newLAI * (lai_by_pft[ip] / totalLAI);
//    }
//  }

  //SLA
  std::array<double, NUM_PFT> da_sla;
  da_sla = temutil::read_pft_var_notime(this->da_filename, "DA_SLA", curr_coords.yidx, curr_coords.xidx);

  //LAI
  std::array<double, NUM_PFT> da_lai;
  da_lai = temutil::read_pft_var_notime(this->da_filename, "DA_LAI", curr_coords.yidx, curr_coords.xidx);

  //VEGC
  BOOST_LOG_SEV(glg, debug) << "Loading DA values for VEGC";
  std::array<std::array<double, NUM_PFT>, NUM_PFT_PART> da_vegc;
  da_vegc = temutil::read_veg_var_notime(this->da_filename, "DA_VEGC", curr_coords.yidx, curr_coords.xidx);

  //STRN
  BOOST_LOG_SEV(glg, debug) << "Loading DA values for STRN";
  std::array<std::array<double, NUM_PFT>, NUM_PFT_PART> da_strn;
  da_strn = temutil::read_veg_var_notime(this->da_filename, "DA_STRN", curr_coords.yidx, curr_coords.xidx);

  //Assign vegetation values back to model variables
  for(int ip=0; ip<NUM_PFT; ip++){
    cohort->cd.m_veg.lai[ip] = da_lai[ip];
    cohort->veg.vegdimpar.sla[ip] = da_sla[ip];

    for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
      cohort->bd[ip].m_vegs.c[ipp] = da_vegc[ipp][ip];
      cohort->bd[ip].m_vegs.strn[ipp] = da_strn[ipp][ip];
    }
  }

  //LWC
  BOOST_LOG_SEV(glg, debug) << "Loading DA values for LWC";
  std::array<double, MAX_SOI_LAY> da_lwc;
  da_lwc = temutil::read_soil_var_notime(this->da_filename, "DA_LWC", curr_coords.yidx, curr_coords.xidx);

  //SOMRAWC
  BOOST_LOG_SEV(glg, debug) << "Loading DA values for SOMRAWC";
  std::array<double, MAX_SOI_LAY> da_somrawc;
  da_somrawc = temutil::read_soil_var_notime(this->da_filename, "DA_RAWC", curr_coords.yidx, curr_coords.xidx);

  //SOMA
  BOOST_LOG_SEV(glg, debug) << "Loading DA values for SOMA";
  std::array<double, MAX_SOI_LAY> da_soma;
  da_soma = temutil::read_soil_var_notime(this->da_filename, "DA_SOMA", curr_coords.yidx, curr_coords.xidx);

  //SOMPR
  BOOST_LOG_SEV(glg, debug) << "Loading DA values for SOMPR";
  std::array<double, MAX_SOI_LAY> da_sompr;
  da_sompr = temutil::read_soil_var_notime(this->da_filename, "DA_SOMPR", curr_coords.yidx, curr_coords.xidx);

  //SOMCR
  BOOST_LOG_SEV(glg, debug) << "Loading DA values for SOMCR";
  std::array<double, MAX_SOI_LAY> da_somcr;
  da_somcr = temutil::read_soil_var_notime(this->da_filename, "DA_SOMCR", curr_coords.yidx, curr_coords.xidx);

  //Assign soil values back to model variables
  for(int il=0; il<MAX_SOI_LAY; il++){
    //std::cout<<da_lwc[il]<<std::endl;
    cohort->edall->m_soid.lwc[il] = da_lwc[il];
    cohort->bdall->m_sois.rawc[il] = da_somrawc[il];
    cohort->bdall->m_sois.soma[il] = da_soma[il];
    cohort->bdall->m_sois.sompr[il] = da_sompr[il];
    cohort->bdall->m_sois.somcr[il] = da_somcr[il];
  }
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

          //Assume the stage is specified as two chars, and
          // needs to have -run appended for later string comparison.
          if(token.find("run")==std::string::npos){
            token.append("-run");
          }
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


double DAController::read_scalar_var(const std::string& varname){
  BOOST_LOG_SEV(glg, debug) << "DAController, reading scalar var: " << varname;
  double new_value = temutil::get_scalar<double>(this->da_filename, varname, 0, 0);
  return new_value;
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

//  int timeD;
  int yD, xD;
  int pftD, pftpartD;
  int soillayerD;

//  temutil::nc( nc_def_dim(ncid, "time", 1, &timeD) );

  temutil::nc( nc_def_dim(ncid, "y", 1, &yD) );
  temutil::nc( nc_def_dim(ncid, "x", 1, &xD) );

  temutil::nc( nc_def_dim(ncid, "pft", NUM_PFT, &pftD) );
  temutil::nc( nc_def_dim(ncid, "pftpart", NUM_PFT_PART, &pftpartD) );
  temutil::nc( nc_def_dim(ncid, "soillayer", MAX_SOI_LAY, &soillayerD) );

//  int vartype2D_dimids[2];
//  vartype2D_dimids[0] = yD;
//  vartype2D_dimids[1] = xD;
//
//  int vartype3D_dimids[3];
//  vartype3D_dimids[0] = soillayerD;
//  vartype3D_dimids[1] = yD;
//  vartype3D_dimids[2] = xD;

  int layer3D_dimids[3];
  layer3D_dimids[0] = soillayerD;
  layer3D_dimids[1] = yD;
  layer3D_dimids[2] = xD;

  int pft3D_dimids[3];
  pft3D_dimids[0] = pftD;
  pft3D_dimids[1] = yD;
  pft3D_dimids[2] = xD;

  int pft_comp_4D_dimids[4];
  pft_comp_4D_dimids[0] = pftpartD;
  pft_comp_4D_dimids[1] = pftD;
  pft_comp_4D_dimids[2] = yD;
  pft_comp_4D_dimids[3] = xD;

  int temSLA_V, daSLA_V;
  int temLAI_V, daLAI_V;
  int temVEGC_V, daVEGC_V;
  int temSTRN_V, daSTRN_V;

  //Vegetation params
  temutil::nc( nc_def_var(ncid, "TEM_SLA", NC_DOUBLE, 3, pft3D_dimids, &temSLA_V) );
  temutil::nc( nc_put_att_double(ncid, temSLA_V, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "DA_SLA", NC_DOUBLE, 3, pft3D_dimids, &daSLA_V) );
  temutil::nc( nc_put_att_double(ncid, daSLA_V, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );

  //Vegetation variables
  temutil::nc( nc_def_var(ncid, "TEM_LAI", NC_DOUBLE, 3, pft3D_dimids, &temLAI_V) );
  temutil::nc( nc_put_att_double(ncid, temLAI_V, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "DA_LAI", NC_DOUBLE, 3, pft3D_dimids, &daLAI_V) );
  temutil::nc( nc_put_att_double(ncid, daLAI_V, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );

  temutil::nc( nc_def_var(ncid, "TEM_VEGC", NC_DOUBLE, 4, pft_comp_4D_dimids, &temVEGC_V) );
  temutil::nc( nc_put_att_double(ncid, temVEGC_V, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "DA_VEGC", NC_DOUBLE, 4, pft_comp_4D_dimids, &daVEGC_V) );
  temutil::nc( nc_put_att_double(ncid, daVEGC_V, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );

  temutil::nc( nc_def_var(ncid, "TEM_STRN", NC_DOUBLE, 4, pft_comp_4D_dimids, &temSTRN_V) );
  temutil::nc( nc_put_att_double(ncid, temSTRN_V, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "DA_STRN", NC_DOUBLE, 4, pft_comp_4D_dimids, &daSTRN_V) );
  temutil::nc( nc_put_att_double(ncid, daSTRN_V, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );

  //Soil variables
  int temLWC_V, daLWC_V;
  int temRAWC_V, daRAWC_V;
  int temSOMA_V, daSOMA_V;
  int temSOMPR_V, daSOMPR_V;
  int temSOMCR_V, daSOMCR_V;
  int temLAYERDZ_V;
  int temTLAYER_V;

  temutil::nc( nc_def_var(ncid, "TEM_LWC", NC_DOUBLE, 3, layer3D_dimids, &temLWC_V) );
  temutil::nc( nc_put_att_double(ncid, temLWC_V, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "DA_LWC", NC_DOUBLE, 3, layer3D_dimids, &daLWC_V) );
  temutil::nc( nc_put_att_double(ncid, daLWC_V, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );

  temutil::nc( nc_def_var(ncid, "TEM_RAWC", NC_DOUBLE, 3, layer3D_dimids, &temRAWC_V) );
  temutil::nc( nc_put_att_double(ncid, temRAWC_V, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "DA_RAWC", NC_DOUBLE, 3, layer3D_dimids, &daRAWC_V) );
  temutil::nc( nc_put_att_double(ncid, daRAWC_V, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );

  temutil::nc( nc_def_var(ncid, "TEM_SOMA", NC_DOUBLE, 3, layer3D_dimids, &temSOMA_V) );
  temutil::nc( nc_put_att_double(ncid, temSOMA_V, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "DA_SOMA", NC_DOUBLE, 3, layer3D_dimids, &daSOMA_V) );
  temutil::nc( nc_put_att_double(ncid, daSOMA_V, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );

  temutil::nc( nc_def_var(ncid, "TEM_SOMPR", NC_DOUBLE, 3, layer3D_dimids, &temSOMPR_V) );
  temutil::nc( nc_put_att_double(ncid, temSOMPR_V, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "DA_SOMPR", NC_DOUBLE, 3, layer3D_dimids, &daSOMPR_V) );
  temutil::nc( nc_put_att_double(ncid, daSOMPR_V, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );

  temutil::nc( nc_def_var(ncid, "TEM_SOMCR", NC_DOUBLE, 3, layer3D_dimids, &temSOMCR_V) );
  temutil::nc( nc_put_att_double(ncid, temSOMCR_V, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "DA_SOMCR", NC_DOUBLE, 3, layer3D_dimids, &daSOMCR_V) );
  temutil::nc( nc_put_att_double(ncid, daSOMCR_V, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );

  temutil::nc( nc_def_var(ncid, "TEM_LAYERDZ", NC_DOUBLE, 3, layer3D_dimids, &temLAYERDZ_V) );
  temutil::nc( nc_put_att_double(ncid, temLAYERDZ_V, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );

  temutil::nc( nc_def_var(ncid, "TEM_TLAYER", NC_DOUBLE, 3, layer3D_dimids, &temTLAYER_V) );
  temutil::nc( nc_put_att_double(ncid, temTLAYER_V, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );

  temutil::nc( nc_enddef(ncid) );
  temutil::nc( nc_close(ncid) );
}

