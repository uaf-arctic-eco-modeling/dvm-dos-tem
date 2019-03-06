#include <exception>
#include <json/value.h>
#include <boost/filesystem.hpp>
#include "../include/ModelData.h"

#include "../include/TEMLogger.h"
#include "../include/TEMUtilityFunctions.h"

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

ModelData::ModelData(Json::Value controldata):force_cmt(-1) {

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

  dynamic_LAI       = controldata["model_settings"]["dynamic_lai"].asInt(); // checked in Cohort::updateMonthly_DIMVeg

  // Unused (11/23/2015)
  //changeclimate = controldata["model_settings"]["dynamic_climate"].asInt();
  //changeco2     = controldata["model_settings"]["varied_co2"].asInt();
  //useseverity   = controldata["model_settings"]["fire_severity_as_input"].asInt();

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

  // User wants to override the veg map
  if (arghandler->get_force_cmt() >= 0) {
    this->force_cmt = arghandler->get_force_cmt();
  }
}


ModelData::ModelData():force_cmt(-1) {
  set_envmodule(false);
  set_bgcmodule(false);
  set_dynamic_lai_module(false);
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

bool ModelData::get_dynamic_lai_module() {
  return this->dynamic_lai_module;
}
void ModelData::set_dynamic_lai_module(const std::string &s) {
  BOOST_LOG_SEV(glg, info) << "Setting dynamic_lai_module to " << s;
  this->dynamic_lai_module = temutil::onoffstr2bool(s);
}
void ModelData::set_dynamic_lai_module(const bool v) {
  BOOST_LOG_SEV(glg, info) << "Setting dynamic_lai_module to " << v;
  this->dynamic_lai_module = v;
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
  s << table_row(22, "envmodule", this->get_envmodule());
  s << table_row(22, "bgcmodule", this->get_bgcmodule());
  s << table_row(22, "dynamic_lai_module", this->get_dynamic_lai_module());
  s << table_row(22, "dslmodule", this->get_dslmodule());
  s << table_row(22, "dsbmodule", this->get_dsbmodule());
  s << table_row(22, "baseline", this->get_baseline());
  s << table_row(22, "nfeed", this->get_nfeed());
  s << table_row(22, "avlnflg", this->get_avlnflg());
  return s.str();
}


/** Construct empty netCDF output files.
 *
 *  This function reads in output selections from a csv file specified
 *  in the config file. It creates an OutputSpec and an empty
 *  NetCDF file for each line.
*/
void ModelData::create_netCDF_output_files(int ysize, int xsize, const std::string& stage, int stage_year_count) {

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

  // Handle for the NetCDF file
  int ncid;

  // NetCDF file dimensions, applicable to all output files
  int timeD;    // unlimited dimension
  int xD;
  int yD;

  // NetCDF file dimensions; different dims are applicable for different vars.
  int pftD;
  int pftpartD;
  int layerD;

  // NetCDF variable handle
  int Var;
  int tcVar; // time coordinate variable

  // 1D Coordinate
  int vartype1D_dimids[1];

  // 3D Ecosystem
  int vartype3D_dimids[3];

  // 4D Soil
  int vartypeSoil4D_dimids[4];

  // 4D Veg - PFT or compartment but not both
  int vartypeVeg4D_dimids[4];

  // 5D Veg - PFT and PFT compartment
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

    for(int ii=0; ii<10; ii++){
      std::getline(ss, token, ',');

      if(ii==0){ // Variable name
        name = token; 
      }
      else if(ii==1){ // Short description
        desc = token;
      }
      else if(ii==2){ // Units
        units = token;
      }
      else if(ii==3){//Yearly
        if(token.length()>0 && token.compare(invalid_option) != 0){
          timestep = "yearly";
          new_spec.yearly = true;
        }
      }
      else if(ii==4){ // Monthly
        if(token.length()>0 && token.compare(invalid_option) != 0){
          timestep = "monthly";
          new_spec.monthly = true;
          new_spec.yearly = false;
        }
      }
      else if(ii==5){ // Daily
        if(token.length()>0 && token.compare(invalid_option) != 0){
          timestep = "daily";
          new_spec.daily = true;
          new_spec.monthly = false;
          new_spec.yearly = false;
        }
      }
      else if(ii==6){ // PFT
        if(token.length()>0 && token.compare(invalid_option) != 0){
          new_spec.pft = true;
          new_spec.dim_count++;
        }
      }
      else if(ii==7){ // Compartment
        if(token.length()>0 && token.compare(invalid_option) != 0){
          new_spec.compartment = true;
          new_spec.dim_count++;
        }
      }
      else if(ii==8){ // Layer
        if(token.length()>0 && token.compare(invalid_option) != 0){
          new_spec.layer = true;
          new_spec.dim_count++;
        }
      }
      else if(ii==9){ // Data type
        if(token.length()>0 && token.compare(invalid_option) != 0){
          if(token.find("int")!=std::string::npos){
            new_spec.data_type = NC_INT;
          }
          else if(token.find("float")!=std::string::npos){
            new_spec.data_type = NC_FLOAT;
          }
          else{
            new_spec.data_type = NC_DOUBLE;
          }
        }
      }
    } // end looping over tokens (aka columns) in a line

    // Only create a file if a timestep is specified for the variable.
    // Otherwise, assume the user does not want that variable output.
    if(new_spec.yearly || new_spec.monthly || new_spec.daily){

      // File location information for reconstructing a complete path
      // and filename during output.
      new_spec.file_path = output_base.string();
      new_spec.filename_prefix = name + "_" + timestep;
      new_spec.var_name = name;

      // Temporary name for file creation.
      std::string creation_filename = name + "_" + timestep + "_" + stage + ".nc";

      BOOST_LOG_SEV(glg, debug)<<"Variable: "<<name<<". Timestep: "<<timestep;

      // filename with local path
      boost::filesystem::path output_filepath = output_base / creation_filename;
      // convert path to string for simplicity in the following function calls
      std::string creation_filestr = output_filepath.string();

#ifdef WITHMPI
      // Creating PARALLEL NetCDF file
      BOOST_LOG_SEV(glg, debug)<<"Creating a parallel output NetCDF file " << creation_filestr;
      temutil::nc( nc_create_par(creation_filestr.c_str(), NC_CLOBBER|NC_NETCDF4|NC_MPIIO, MPI_COMM_WORLD, MPI_INFO_NULL, &ncid) );
#else
      // Creating NetCDF file
      BOOST_LOG_SEV(glg, debug) << "Creating an output NetCDF file " << creation_filestr;
      temutil::nc( nc_create(creation_filestr.c_str(), NC_CLOBBER|NC_NETCDF4, &ncid) );
#endif

      BOOST_LOG_SEV(glg, debug) << "Adding file-level attributes";
      temutil::nc( nc_put_att_text(ncid, NC_GLOBAL, "Git_SHA", strlen(GIT_SHA), GIT_SHA ) );

      //Calculating total timesteps
      int stage_timestep_count = 0;
      if(timestep == "yearly"){
        stage_timestep_count = stage_year_count;
      }
      else if(timestep == "monthly"){
        stage_timestep_count = stage_year_count*12;
      }
      else if(timestep == "daily"){
        stage_timestep_count = stage_year_count*365;
      }

      BOOST_LOG_SEV(glg, debug) << "Adding dimensions...";
      // All variables will have dimensions: time, y, x
      temutil::nc( nc_def_dim(ncid, "time", stage_timestep_count, &timeD) );
      temutil::nc( nc_def_dim(ncid, "y", ysize, &yD) );
      temutil::nc( nc_def_dim(ncid, "x", xsize, &xD) );

      // System-wide variables
      if(new_spec.dim_count==3){
        vartype3D_dimids[0] = timeD;
        vartype3D_dimids[1] = yD;
        vartype3D_dimids[2] = xD;

        temutil::nc( nc_def_var(ncid, name.c_str(), new_spec.data_type, 3, vartype3D_dimids, &Var) );
#ifdef WITHMPI
        //Instruct HDF5 to use independent parallel access for this variable
        temutil::nc( nc_var_par_access(ncid, Var, NC_INDEPENDENT) );
#endif
      }

      // PFT specific dimensions
      else if(new_spec.pft && !new_spec.compartment){
        temutil::nc( nc_def_dim(ncid, "pft", NUM_PFT, &pftD) );

        vartypeVeg4D_dimids[0] = timeD;
        vartypeVeg4D_dimids[1] = pftD;
        vartypeVeg4D_dimids[2] = yD;
        vartypeVeg4D_dimids[3] = xD;

        temutil::nc( nc_def_var(ncid, name.c_str(), new_spec.data_type, 4, vartypeVeg4D_dimids, &Var) );
#ifdef WITHMPI
        //Instruct HDF5 to use independent parallel access for this variable
        temutil::nc( nc_var_par_access(ncid, Var, NC_INDEPENDENT) );
#endif
      }

      // PFT compartment only
      else if(!new_spec.pft && new_spec.compartment){
        temutil::nc( nc_def_dim(ncid, "pftpart", NUM_PFT_PART, &pftpartD) );

        vartypeVeg4D_dimids[0] = timeD;
        vartypeVeg4D_dimids[1] = pftpartD;
        vartypeVeg4D_dimids[2] = yD;
        vartypeVeg4D_dimids[3] = xD;

        temutil::nc( nc_def_var(ncid, name.c_str(), new_spec.data_type, 4, vartypeVeg4D_dimids, &Var) );
#ifdef WITHMPI
        //Instruct HDF5 to use independent parallel access for this variable
        temutil::nc( nc_var_par_access(ncid, Var, NC_INDEPENDENT) );
#endif
      }

      // PFT and PFT compartments
      else if(new_spec.pft && new_spec.compartment){ 
        temutil::nc( nc_def_dim(ncid, "pft", NUM_PFT, &pftD) );
        temutil::nc( nc_def_dim(ncid, "pftpart", NUM_PFT_PART, &pftpartD) );

        vartypeVeg5D_dimids[0] = timeD;
        vartypeVeg5D_dimids[1] = pftpartD;
        vartypeVeg5D_dimids[2] = pftD;
        vartypeVeg5D_dimids[3] = yD;
        vartypeVeg5D_dimids[4] = xD;

        temutil::nc( nc_def_var(ncid, name.c_str(), new_spec.data_type, 5, vartypeVeg5D_dimids, &Var) );
#ifdef WITHMPI
        //Instruct HDF5 to use independent parallel access for this variable
        temutil::nc( nc_var_par_access(ncid, Var, NC_INDEPENDENT) );
#endif
      }

      // Soil specific dimensions
      else if(new_spec.layer){
        temutil::nc( nc_def_dim(ncid, "layer", MAX_SOI_LAY, &layerD) );

        vartypeSoil4D_dimids[0] = timeD;
        vartypeSoil4D_dimids[1] = layerD;
        vartypeSoil4D_dimids[2] = yD;
        vartypeSoil4D_dimids[3] = xD;

        temutil::nc( nc_def_var(ncid, name.c_str(), new_spec.data_type, 4, vartypeSoil4D_dimids, &Var) );
#ifdef WITHMPI
        //Instruct HDF5 to use independent parallel access for this variable
        temutil::nc( nc_var_par_access(ncid, Var, NC_INDEPENDENT) );
#endif
      }

      //  monthly tr :  days since 1901, copy attributes and data from hist climate
      //  yearly tr :  days since 1901, copy attributes from hist climate; generate data...
      //
      //  monthly sc : days since 2001, copy attributes and data from proj climate
      //  yearly sc : days since 2001, copy attributes from proj climate, generate data...

      if (stage == "tr" && (timestep == "yearly" || timestep == "monthly")) {
        vartype1D_dimids[0] = timeD;
        temutil::nc( nc_def_var(ncid, "time", NC_DOUBLE, 1, vartype1D_dimids, &tcVar) );

        int hist_climate_ncid;
        int hist_climate_tcV;

        temutil::nc( nc_open(this->hist_climate_file.c_str(), NC_NOWRITE, &hist_climate_ncid) );
        temutil::nc( nc_inq_varid(hist_climate_ncid, "time", &hist_climate_tcV));

        // Copy attributes for time variable
        temutil::nc( nc_copy_att(hist_climate_ncid, hist_climate_tcV, "units", ncid, tcVar));
        temutil::nc( nc_copy_att(hist_climate_ncid, hist_climate_tcV, "calendar", ncid, tcVar));

        // perhaps write calendar attribute if it does not exist?
        //std::string s = "365_day";
        //temutil::nc( nc_put_att_text(ncid, tcVar, "calendar", s.length(), s.c_str()) );

      }

      if (stage == "sc" && (timestep == "yearly" || timestep == "monthly")) {
        vartype1D_dimids[0] = timeD;
        temutil::nc( nc_def_var(ncid, "time", NC_DOUBLE, 1, vartype1D_dimids, &tcVar) );

        int proj_climate_ncid;
        int proj_climate_tcV;

        temutil::nc( nc_open(this->proj_climate_file.c_str(), NC_NOWRITE, &proj_climate_ncid) );
        temutil::nc( nc_inq_varid(proj_climate_ncid, "time", &proj_climate_tcV));

        temutil::nc( nc_copy_att(proj_climate_ncid, proj_climate_tcV, "units", ncid, tcVar));
        temutil::nc( nc_copy_att(proj_climate_ncid, proj_climate_tcV, "calendar", ncid, tcVar));

        // perhaps write calendar attribute if it does not exist?
        //std::string s = "365_day";
        //temutil::nc( nc_put_att_text(ncid, tcVar, "calendar", s.length(), s.c_str()) );

      }

      BOOST_LOG_SEV(glg, debug) << "Adding variable-level attributes from output spec.";

      // Swap out generic /time unit from output spec with appropriate
      // timestep denomination.
      if (units.find("time") != std::string::npos) {
        BOOST_LOG_SEV(glg, debug) << "Updating units string! ";
        std::string real_timestep;
        if (timestep == "yearly") { real_timestep = "year"; }
        if (timestep == "monthly") { real_timestep = "month"; }
        if (timestep == "daily") { real_timestep = "day"; }
        units.replace(units.begin() + units.find("time"),
                      units.end(),
                      real_timestep.begin(),
                      real_timestep.end());

      }
      BOOST_LOG_SEV(glg, debug) << "Using units string: " << units.c_str();
      temutil::nc( nc_put_att_text(ncid, Var, "units", units.length(), units.c_str()) );
      temutil::nc( nc_put_att_text(ncid, Var, "long_name", desc.length(), desc.c_str()) );

      if(new_spec.data_type == NC_INT){
        temutil::nc( nc_put_att_int(ncid, Var, "_FillValue", NC_INT, 1, &MISSING_I) );
      }
      if(new_spec.data_type == NC_FLOAT){
        temutil::nc( nc_put_att_float(ncid, Var, "_FillValue", NC_FLOAT, 1, &MISSING_F) );
      }
      else if(new_spec.data_type == NC_DOUBLE){
        temutil::nc( nc_put_att_double(ncid, Var, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
      }

      /* End Define Mode (not strictly necessary for netcdf 4) */
      BOOST_LOG_SEV(glg, debug) << "Leaving 'define mode'...";
      temutil::nc( nc_enddef(ncid) );

      /* Fill out the time coordinate variable */
      if ((stage == "tr" || stage == "sc") && timestep == "yearly") {
        BOOST_LOG_SEV(glg, debug) << "Time coordinate variable, tr or sc, yearly.";

        int tcV;
        temutil::nc( nc_inq_varid(ncid, "time", &tcV));

        int runyrs;
        if (stage == "tr") { runyrs = this->tr_yrs; }
        if (stage == "sc") { runyrs = this->sc_yrs; }

        std::vector<int> time_coord_values(runyrs, 0);
        for (int i=0; i < runyrs; i++) {
          time_coord_values.at(i) = 365 * i; // assumes attribute calendar:'365_day'
        }
        size_t start[1];
        size_t count[1];

        start[0] = 0;
        count[0] = time_coord_values.size();

        temutil::nc( nc_put_vara_int(ncid, tcV, start, count, &time_coord_values[0]) );

      }

      if ((stage == "tr" || stage == "sc") && timestep == "monthly") {
        BOOST_LOG_SEV(glg, debug) << "Time coordinate variable, tr or sc, monthly.";

        int runyrs = 0;
        std::vector<int> full_time_coord;

        if (stage == "tr") {
          runyrs = this->tr_yrs;
          full_time_coord = temutil::get_timeseries2(this->hist_climate_file, "time", 0);
        }
        if (stage == "sc") {
          runyrs = this->sc_yrs;
          full_time_coord = temutil::get_timeseries2(this->proj_climate_file, "time", 0);
        }

        int tcV;
        temutil::nc( nc_inq_varid(ncid, "time", &tcV));

        size_t start[1];
        size_t count[1];

        start[0] = 0;
        count[0] = runyrs * 12;

        temutil::nc( nc_put_vara_int(ncid, tcV, start, count, &full_time_coord[0]) );

      }


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





