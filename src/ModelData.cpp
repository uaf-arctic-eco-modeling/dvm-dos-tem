#include <exception>
#include <json/value.h>
#include <boost/filesystem.hpp>
#include "../include/ModelData.h"

#include "TEMLogger.h"
#include "TEMUtilityFunctions.h"

extern src::severity_logger< severity_level > glg;


/** Returns a string with first colum r justified and
 * of with 'w'. Can be used to build tables likle this:
 *
 *       somestr: 0
 *       somestr: 0
 *       somestr: 0
 *
 *  with a newline, for use in a table.
 */
std::string table_row(int w, std::string d, bool v) {
  std::stringstream s;
  s << std::setw(w) << std::setfill(' ') << d << ": " << v << "\n";
  return s.str();
}

ModelData::~ModelData() {}

ModelData::ModelData(Json::Value controldata) {

  BOOST_LOG_SEV(glg, debug) << "Creating a ModelData. New style constructor with injected controldata...";
  
  std::string stgstr(controldata["stage_settings"]["run_stage"].asString());

  inter_stage_pause = controldata["stage_settings"]["inter_stage_pause"].asBool();
  initmode = controldata["stage_settings"]["restart"].asInt();  // may become obsolete
  tr_yrs        = controldata["stage_settings"]["tr_yrs"].asInt();
  sc_yrs        = controldata["stage_settings"]["sc_yrs"].asInt();

  parameter_dir     = controldata["IO"]["parameter_dir"].asString();
  hist_climate_file = controldata["IO"]["hist_climate_file"].asString();
  proj_climate_file = controldata["IO"]["proj_climate_file"].asString();
  veg_class_file    = controldata["IO"]["veg_class_file"].asString();
  fri_fire_file     = controldata["IO"]["fri_fire_file"].asString();
  hist_exp_fire_file= controldata["IO"]["hist_exp_fire_file"].asString();
  proj_exp_fire_file= controldata["IO"]["proj_exp_fire_file"].asString();
  topo_file         = controldata["IO"]["topo_file"].asString();
  drainage_file     = controldata["IO"]["drainage_file"].asString();
  soil_texture_file = controldata["IO"]["soil_texture_file"].asString();
  co2_file          = controldata["IO"]["co2_file"].asString();
  runmask_file      = controldata["IO"]["runmask_file"].asString();
  output_dir        = controldata["IO"]["output_dir"].asString();
  output_spec_file  = controldata["IO"]["output_spec_file"].asString();
  output_monthly    = controldata["IO"]["output_monthly"].asInt();
  nc_eq             = controldata["IO"]["output_nc_eq"].asBool();
  nc_sp             = controldata["IO"]["output_nc_sp"].asBool();
  nc_tr             = controldata["IO"]["output_nc_tr"].asBool();
  nc_sc             = controldata["IO"]["output_nc_sc"].asBool();

  pid_tag           = controldata["calibration-IO"]["pid_tag"].asString();
  caldata_tree_loc  = controldata["calibration-IO"]["caldata_tree_loc"].asString();

  updatelai     = controldata["model_settings"]["dynamic_lai"].asInt(); // checked in Cohort::updateMonthly_DIMVeg


  // Unused (11/23/2015)
  changeclimate = controldata["model_settings"]["dynamic_climate"].asInt();
  changeco2     = controldata["model_settings"]["varied_co2"].asInt();
  useseverity   = controldata["model_settings"]["fire_severity_as_input"].asInt();

}

/** Update all the appropriate fields in ModelData from an ArgHandler object.

    Pass const * so that access to ArgHandler is read-only.
*/
void ModelData::update(ArgHandler const * arghandler) {

  BOOST_LOG_SEV(glg, debug) << "Updating ModelData from an ArgHandler...";

  this->pr_yrs = arghandler->get_pr_yrs();
  this->eq_yrs = arghandler->get_eq_yrs();
  this->sp_yrs = arghandler->get_sp_yrs();
  this->tr_yrs = arghandler->get_tr_yrs();
  this->sc_yrs = arghandler->get_sc_yrs();
  this->pid_tag = arghandler->get_pid_tag();
  this->last_n_json_files = arghandler->get_last_n_json_files();
  this->archive_all_json = arghandler->get_archive_all_json();
  this->tar_caljson = arghandler->get_tar_caljson();

  // it it was set on the command line, then use that value, otherwise,
  // use the value
  if (arghandler->get_inter_stage_pause()) {
    this->inter_stage_pause = arghandler->get_inter_stage_pause();
  }
}


ModelData::ModelData() {
  set_envmodule(false);
  set_bgcmodule(false);
  set_dvmmodule(false);
  set_dslmodule(false);
  set_dsbmodule(false);
}


bool ModelData::get_envmodule() {
  return this->envmodule;
}
void ModelData::set_envmodule(const std::string &s) {
  BOOST_LOG_SEV(glg, info) << "Setting envmodule to " << s;
  this->envmodule = temutil::onoffstr2bool(s);
}
void ModelData::set_envmodule(const bool v) {
  BOOST_LOG_SEV(glg, info) << "Setting envmodule to " << v;
  this->envmodule = v;
}

bool ModelData::get_bgcmodule() {
  return this->bgcmodule;
}
void ModelData::set_bgcmodule(const std::string &s) {
  BOOST_LOG_SEV(glg, info) << "Setting bgcmodule to " << s;
  this->bgcmodule = temutil::onoffstr2bool(s);
}
void ModelData::set_bgcmodule(const bool v) {
  BOOST_LOG_SEV(glg, info) << "Setting bgcmodule to " << v;
  this->bgcmodule = v;
}

bool ModelData::get_dvmmodule() {
  return this->dvmmodule;
}
void ModelData::set_dvmmodule(const std::string &s) {
  BOOST_LOG_SEV(glg, info) << "Setting dvmmodule to " << s;
  this->dvmmodule = temutil::onoffstr2bool(s);
}
void ModelData::set_dvmmodule(const bool v) {
  BOOST_LOG_SEV(glg, info) << "Setting dvmmodule to " << v;
  this->dvmmodule = v;
}

bool ModelData::get_dslmodule() {
  return this->dslmodule;
}
void ModelData::set_dslmodule(const std::string &s) {
  BOOST_LOG_SEV(glg, info) << "Setting dslmodule to " << s;
  this->dslmodule = temutil::onoffstr2bool(s);
}
void ModelData::set_dslmodule(const bool v) {
  BOOST_LOG_SEV(glg, info) << "Setting dslmodule to " << v;
  this->dslmodule = v;
}

bool ModelData::get_dsbmodule() {
  return this->dsbmodule;
}
void ModelData::set_dsbmodule(const std::string &s) {
  BOOST_LOG_SEV(glg, info) << "Setting dsbmodule to " << s;
  this->dsbmodule = temutil::onoffstr2bool(s);
}
void ModelData::set_dsbmodule(const bool v) {
  BOOST_LOG_SEV(glg, info) << "Setting dsbmodule to " << v;
  this->dsbmodule = v;
}

bool ModelData::get_nfeed() {
  return this->nfeed;
}
void ModelData::set_nfeed(const std::string &s) {
  BOOST_LOG_SEV(glg, info) << "Setting ModelData.nfeed to " << s;
  this->nfeed = temutil::onoffstr2bool(s);
}
void ModelData::set_nfeed(const bool v) {
  BOOST_LOG_SEV(glg, info) << "Setting ModelData.nfeed to " << v;
  this->nfeed = v;
}

bool ModelData::get_avlnflg() {
  return this->avlnflg;
}
void ModelData::set_avlnflg(const std::string &s) {
  BOOST_LOG_SEV(glg, info) << "Setting ModelData.avlnflg to " << s;
  this->avlnflg = temutil::onoffstr2bool(s);
}
void ModelData::set_avlnflg(const bool v) {
  BOOST_LOG_SEV(glg, info) << "Setting ModelData.avlnflg to " << v;
  this->avlnflg = v;
}

bool ModelData::get_baseline() {
  return this->baseline;
}
void ModelData::set_baseline(const std::string &s) {
  BOOST_LOG_SEV(glg, info) << "Setting ModelData.baseline to " << s;
  this->baseline = temutil::onoffstr2bool(s);
}
void ModelData::set_baseline(const bool v) {
  BOOST_LOG_SEV(glg, info) << "Setting ModelData.baseline to " << v;
  this->baseline = v;
}

std::string ModelData::describe_module_settings() {
  std::stringstream s;
  s << table_row(15, "envmodule", this->get_envmodule());
  s << table_row(15, "bgcmodule", this->get_bgcmodule());
  s << table_row(15, "dvmmodule", this->get_dvmmodule());
  s << table_row(15, "dslmodule", this->get_dslmodule());
  s << table_row(15, "dsbmodule", this->get_dsbmodule());
  s << table_row(15, "nfeed", this->get_nfeed());
  s << table_row(15, "avlnflg", this->get_avlnflg());
  return s.str();
}


/** Construct empty netCDF output files.
 *
 *  This function reads in output selections from a csv file specified
 *  in the config file. It creates an OutputSpec and an empty
 *  NetCDF file for each line.
*/
void ModelData::create_netCDF_output_files(int ysize, int xsize, const std::string& stage) {

  boost::filesystem::path output_base = output_dir;

  // Load output specification file
  BOOST_LOG_SEV(glg, debug) << "Loading output specification file "<<output_spec_file;
  std::ifstream output_csv(output_spec_file.c_str());

  std::string s;
  std::getline(output_csv, s); // Discard first line - header strings

  std::string token;    // Substrings between commas
  std::string name;     // CSV file variable name
  std::string timestep; // Yearly, monthly, or daily
  std::string invalid_option = "invalid"; // This marks an invalid selection

  // NetCDF file variables
  int ncid;
  int timeD;    // unlimited dimension
  int xD;
  int yD;
  int pftD;
  int pftpartD;
  int layerD;
  int Var;

  //3D Ecosystem
  int vartype3D_dimids[3];

  //4D Soil
  int vartypeSoil4D_dimids[4];

  //4D Veg - PFT or compartment but not both 
  int vartypeVeg4D_dimids[4];

  //5D Veg - PFT and PFT compartment
  int vartypeVeg5D_dimids[5];
 
  // Ingest output specification file, create OutputSpec for each entry.
  while(std::getline(output_csv, s)){ 

    std::istringstream ss(s);

    std::string units;
    std::string desc;

    OutputSpec new_spec;
    new_spec.pft = false;
    new_spec.compartment = false;
    new_spec.layer = false;
    new_spec.yearly = false;
    new_spec.monthly = false;
    new_spec.daily = false;
    new_spec.dim_count = 3; // All variables have time, y, x

    for(int ii=0; ii<9; ii++){
      std::getline(ss, token, ',');
      //std::cout<<"token: "<<token<<std::endl;

      if(ii==0){//Variable name
        name = token; 
      }
      else if(ii==1){//Short description
        desc = token;
      }
      else if(ii==2){//Units
        units = token;
      }
      else if(ii==3){//Yearly
        if(token.length()>0 && token.compare(invalid_option) != 0){
          timestep = "yearly";
          new_spec.yearly = true;
        }
      }
      else if(ii==4){//Monthly
        if(token.length()>0 && token.compare(invalid_option) != 0){
          timestep = "monthly";
          new_spec.monthly = true;
          new_spec.yearly = false;
        }
      }
      else if(ii==5){//Daily
        if(token.length()>0 && token.compare(invalid_option) != 0){
          timestep = "daily";
          new_spec.daily = true;
          new_spec.monthly = false;
          new_spec.yearly = false;
        }
      }
      else if(ii==6){//PFT
        if(token.length()>0 && token.compare(invalid_option) != 0){
          new_spec.pft = true;
          new_spec.dim_count++;
        }
      }
      else if(ii==7){//Compartment
        if(token.length()>0 && token.compare(invalid_option) != 0){
          new_spec.compartment = true;
          new_spec.dim_count++;
        }
      }
      else if(ii==8){//Layer
        if(token.length()>0 && token.compare(invalid_option) != 0){
          new_spec.layer = true;
          new_spec.dim_count++;
        }
      }
    } // end looping over tokens (aka columns) in a line

    // Only create a file if a timestep is specified for the variable.
    //  Otherwise, assume the user does not want that variable output.
    if(new_spec.yearly || new_spec.monthly || new_spec.daily){

      // File location information for reconstructing a complete path
      //  and filename during output.
      new_spec.file_path = output_base.string();
      new_spec.filename_prefix = name + "_" + timestep;

      //Temporary name for file creation.
      std::string creation_filename = name + "_" + timestep + "_" + stage + ".nc";

      BOOST_LOG_SEV(glg, debug)<<"Variable: "<<name<<". Timestep: "<<timestep;

      //filename with local path
      boost::filesystem::path output_filepath = output_base / creation_filename;
      //convert path to string for simplicity in the following function calls
      std::string creation_filestr = output_filepath.string();

      //Creating NetCDF file
      BOOST_LOG_SEV(glg, debug)<<"Creating output NetCDF file "<<creation_filestr;
      temutil::nc( nc_create(creation_filestr.c_str(), NC_CLOBBER, &ncid) );

      BOOST_LOG_SEV(glg, debug) << "Adding file-level attributes";
      temutil::nc( nc_put_att_text(ncid, NC_GLOBAL, "Git_SHA", strlen(GIT_SHA), GIT_SHA ) );

      BOOST_LOG_SEV(glg, debug) << "Adding dimensions...";

      //All variables will have time, y, x 
      temutil::nc( nc_def_dim(ncid, "time", NC_UNLIMITED, &timeD) );
      temutil::nc( nc_def_dim(ncid, "y", ysize, &yD) );
      temutil::nc( nc_def_dim(ncid, "x", xsize, &xD) );

      //System-wide variables
      if(new_spec.dim_count==3){
        vartype3D_dimids[0] = timeD;
        vartype3D_dimids[1] = yD;
        vartype3D_dimids[2] = xD;

        temutil::nc( nc_def_var(ncid, name.c_str(), NC_DOUBLE, 3, vartype3D_dimids, &Var) );
      }

      //PFT specific dimensions
      else if(new_spec.pft && !new_spec.compartment){
        temutil::nc( nc_def_dim(ncid, "pft", NUM_PFT, &pftD) );

        vartypeVeg4D_dimids[0] = timeD;
        vartypeVeg4D_dimids[1] = pftD;
        vartypeVeg4D_dimids[2] = yD;
        vartypeVeg4D_dimids[3] = xD;

        temutil::nc( nc_def_var(ncid, name.c_str(), NC_DOUBLE, 4, vartypeVeg4D_dimids, &Var) );
      }

      //PFT compartment only
      else if(!new_spec.pft && new_spec.compartment){
        temutil::nc( nc_def_dim(ncid, "pftpart", NUM_PFT_PART, &pftpartD) );

        vartypeVeg4D_dimids[0] = timeD;
        vartypeVeg4D_dimids[1] = pftpartD;
        vartypeVeg4D_dimids[2] = yD;
        vartypeVeg4D_dimids[3] = xD;

        temutil::nc( nc_def_var(ncid, name.c_str(), NC_DOUBLE, 4, vartypeVeg4D_dimids, &Var) );
      }

      //PFT and PFT compartments
      else if(new_spec.pft && new_spec.compartment){ 
        temutil::nc( nc_def_dim(ncid, "pft", NUM_PFT, &pftD) );
        temutil::nc( nc_def_dim(ncid, "pftpart", NUM_PFT_PART, &pftpartD) );

        vartypeVeg5D_dimids[0] = timeD;
        vartypeVeg5D_dimids[1] = pftpartD;
        vartypeVeg5D_dimids[2] = pftD;
        vartypeVeg5D_dimids[3] = yD;
        vartypeVeg5D_dimids[4] = xD;

        temutil::nc( nc_def_var(ncid, name.c_str(), NC_DOUBLE, 5, vartypeVeg5D_dimids, &Var) );
      }

      //Soil specific dimensions
      else if(new_spec.layer){
        temutil::nc( nc_def_dim(ncid, "layer", MAX_SOI_LAY, &layerD) );

        vartypeSoil4D_dimids[0] = timeD;
        vartypeSoil4D_dimids[1] = layerD;
        vartypeSoil4D_dimids[2] = yD;
        vartypeSoil4D_dimids[3] = xD;

        temutil::nc( nc_def_var(ncid, name.c_str(), NC_DOUBLE, 4, vartypeSoil4D_dimids, &Var) );
      }

      BOOST_LOG_SEV(glg, debug) << "Adding variable-level attributes";
      temutil::nc( nc_put_att_text(ncid, Var, "units", units.length(), units.c_str()) );
      temutil::nc( nc_put_att_text(ncid, Var, "long_name", desc.length(), desc.c_str()) );
      temutil::nc( nc_put_att_double(ncid, Var, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );

      /* End Define Mode (not strictly necessary for netcdf 4) */
      BOOST_LOG_SEV(glg, debug) << "Leaving 'define mode'...";
      temutil::nc( nc_enddef(ncid) );

      /* Close file. */
      BOOST_LOG_SEV(glg, debug) << "Closing new file...";
      temutil::nc( nc_close(ncid) );

      // Add OutputSpec objects to the map tracking the appropriate timestep
      if(new_spec.daily){
        daily_netcdf_outputs.insert(std::map<std::string, OutputSpec>::value_type(name, new_spec));
      }

      else if(new_spec.monthly){
        monthly_netcdf_outputs.insert(std::map<std::string, OutputSpec>::value_type(name, new_spec));
        //monthly_netcdf_outputs.insert({name, filename}); c++11
      }

      else if(new_spec.yearly){
        yearly_netcdf_outputs.insert(std::map<std::string, OutputSpec>::value_type(name, new_spec));
      }

    } // End file creation section (if timestep is specified)
  } // End looping over the output spec file.
}





