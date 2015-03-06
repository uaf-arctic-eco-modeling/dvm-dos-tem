#include <exception>
#include <json/value.h>
#include <boost/filesystem.hpp>
#include "ModelData.h"

#include "../TEMLogger.h"
#include "../TEMUtilityFunctions.h"

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


ModelData::ModelData() {
  runmode = "single";
  runeq = false;
  runsp = false;
  runtr = false;
  runsc = false;
  initmode =-1;
  changeclimate= 0;
  changeco2    = 0;
  updatelai    = false;
  useseverity  = false;
  //some options for parallel-computing in the future (but not here)
  myid = 0;
  numprocs = 1;
  // module switches
  set_envmodule(false);
  set_bgcmodule(false);
  set_dvmmodule(false);
  set_dslmodule(false);
  set_dsbmodule(false);
  set_friderived(false);
  // the data record numbers of all input datasets
  act_gridno = 0;
  act_drainno= 0;
  act_soilno = 0;
  act_gfireno= 0;
  act_chtno    = 0;
  act_initchtno= 0;
  act_clmno    = 0;
  act_clmyr_beg= 0;
  act_clmyr_end= 0;
  act_clmyr    = 0;
  act_vegno    = 0;
  act_vegset   = 0;
  act_fireno   = 0;
  act_fireset  = 0;
};

ModelData::~ModelData() {
}

/** Reads a co2.nc file and sets the "actual"?? number of co2 years to run?
*/
void ModelData::setup_act_co2yr_from_file() {
  NcFile f = temutil::open_ncfile(this->reginputdir + "co2.nc");
  
  NcDim* d = temutil::get_ncdim(f, "YEAR");
  
  BOOST_LOG_SEV(glg, info) << "Setting the 'actual' co2 years to be run (in ModelData)...";
  this->act_co2yr = d->size();
}


/** Reads a cohortid.nc file and sets the "actual" number of cohorts to be run.
 */
int ModelData::set_chtids_from_file() {

  NcFile chtid_file = temutil::open_ncfile(this->chtinputdir + "cohortid.nc");

  NcDim* chtD = temutil::get_ncdim(chtid_file, "CHTID");

  BOOST_LOG_SEV(glg, info) << "Setting the 'actual' cohorts to be run (in ModelData)...";
  this->act_chtno = chtD->size();

  return 0;
}

/** Reads an "initial file" and sets the "actual" initial cohort number to run.
 */
int ModelData::set_initial_cohort_from_file() {
  if ( !this->runeq ) {
    
    NcFile cohort_initial_file = temutil::open_ncfile(this->initialfile);
    
    NcDim* chtD = temutil::get_ncdim(cohort_initial_file, "CHTID");
    
    BOOST_LOG_SEV(glg, info) << "Set the actual initial cohort number???";
    this->act_initchtno = chtD->size();
    
  } else {
    BOOST_LOG_SEV(glg, err) << "Not running 'eq' stage; can't read/set inital file?";
    return -1;
  }
  
  return 0;
  
}

/** Reads a climate.nc file and sets the "actual" climate begin and end years.
 */
int ModelData::set_climate_from_file() {
  
  BOOST_LOG_SEV(glg, debug) << "Some new stuff?";
  NcFile climate_file = temutil::open_ncfile(this->chtinputdir+"climate.nc");

  // not really used - but the get_ncdim function will fail an exit if the
  // dimension doesn't exist, or there is a problem accessing it...
  NcDim* monD = temutil::get_ncdim(climate_file, "MONTH");
  
  NcDim* clmD = temutil::get_ncdim(climate_file, "CLMID");
  
  this->act_clmno = clmD->size(); // number of actual atm data records..?
  
  NcVar* clmyrV = climate_file.get_var("YEAR");
  
  if (clmyrV == NULL) {
    BOOST_LOG_SEV(glg, err) << "Problem reading YEAR variable in climate.nc file!";
    return -1;
  } else {
    
    int yrno = 0;
    int yr = -1;
    
    BOOST_LOG_SEV(glg, info) << "Set ModelData's climate begining year to the "
    << "first year found in the climate.nc file ??";
    clmyrV->set_cur(yrno);
    clmyrV->get(&yr, 1);
    
    this->act_clmyr_beg = yr;
    
    yrno = clmyrV->num_vals()-1;
    clmyrV->set_cur(yrno);
    clmyrV->get(&yr, 1);
    
    this->act_clmyr_end = yr;
    this->act_clmyr = yr - this->act_clmyr_beg + 1;  //actual atm data years
    
  }
  return 0;
}

/** Reads a vegetation.nc file and set the ModelData's notion
 * of "actual vegetation set", and the "actual veg number".
 */
int ModelData::set_veg_from_file() {
  
  NcFile veg_file = temutil::open_ncfile(this->chtinputdir+"vegetation.nc");
  
  NcDim* vegD = temutil::get_ncdim(veg_file, "VEGID");
  
  this->act_vegno = vegD->size(); // actual veg data record number?
  
  NcDim* vegsetD = temutil::get_ncdim(veg_file, "VEGSET");
  
  this->act_vegset = vegsetD->size();  //actual vegetation data sets
  
  return 0;
}

/** Reads a fire.nc file and sets the ModelData's notion of ???
 */
int ModelData::set_fire_from_file(){
  
  NcFile fire_file = temutil::open_ncfile(this->chtinputdir + "fire.nc");
  
  NcDim* fireD = temutil::get_ncdim(fire_file, "FIREID");
  
  this->act_fireno = fireD->size();  //actual fire data record number
  
  NcDim* fireyrD = temutil::get_ncdim(fire_file, "FIRESET");
  
  this->act_fireset=fireyrD->size();  //actual fire year-set number
  
  return 0;
}

/** Set up ModelData's notion of "grid data"?? from the grid files.
*/
void ModelData::setup_griddata_from_files() {
  
  NcFile grid_file = temutil::open_ncfile( this->grdinputdir + "grid.nc");
  NcDim* grdD = temutil::get_ncdim(grid_file, "GRIDID");
  this->act_gridno = grdD->size();
  
  NcFile drainage_file = temutil::open_ncfile( this->grdinputdir + "drainage.nc" );
  NcDim* drainD = temutil::get_ncdim(drainage_file, "DRAINAGEID");
  this->act_drainno = drainD->size(); //actual drainage type datset number
  
  NcFile soil_file = temutil::open_ncfile( this->grdinputdir + "soiltexture.nc" );
  NcDim* soilD = temutil::get_ncdim(soil_file, "SOILID");
  this->act_soilno = soilD->size(); //actual soil dataset number
  
  NcFile fire_file = temutil::open_ncfile( this->grdinputdir + "firestatistics.nc" );
  NcDim* gfireD = temutil::get_ncdim(fire_file, "GFIREID");
  NcDim* gfsizeD = temutil::get_ncdim(fire_file, "GFSIZENO");
  NcDim* gfseasonD = temutil::get_ncdim(fire_file, "GFSEASONNO");
  this->act_gfireno = gfireD->size();  //actual grid fire dataset number

}

void ModelData::updateFromControlFile(const std::string& cf) {

  BOOST_LOG_SEV(glg, debug) << "Read control file '" << cf << "' into Json::Value data structure...";
  Json::Value controldata = temutil::parse_control_file(cf);

  BOOST_LOG_SEV(glg, debug) << "Assign to ModelData members from Json::Value data structure...";
  this->casename = controldata["general"]["run_name"].asString();
  this->configdir = controldata["general"]["config_dir"].asString();
  this->runmode = controldata["general"]["runmode"].asString();

  this->runchtfile = controldata["data_directories"]["run_cohort_list"].asString();
  this->outputdir = controldata["data_directories"]["output_data_dir"].asString();
  this->reginputdir = controldata["data_directories"]["region_data_dir"].asString();
  this->grdinputdir = controldata["data_directories"]["grid_data_dir"].asString();
  this->chtinputdir = controldata["data_directories"]["cohort_data_dir"].asString();

  this->runstages = controldata["stage_settings"]["run_stage"].asString();
  this->initmodes = controldata["stage_settings"]["restart_mode"].asString();
  this->initialfile = controldata["stage_settings"]["restart_file"].asString();

  this->changeclimate = controldata["model_settings"]["dynamic_climate"].asInt();
  this->changeco2 = controldata["model_settings"]["varied_co2"].asInt();
  this->updatelai = controldata["model_settings"]["dynamic_lai"].asInt();
  this->useseverity = controldata["model_settings"]["fire_severity_as_input"].asInt();
  this->outstartyr = controldata["model_settings"]["output_starting_year"].asInt();

  this->outSiteDay = controldata["output_switches"]["daily_output"].asInt();
  this->outSiteMonth = controldata["output_switches"]["monthly_output"].asInt();
  this->outSiteYear = controldata["output_switches"]["yearly_output"].asInt();
  this->outRegn = controldata["output_switches"]["summarized_output"].asInt();
  this->outSiteDay = controldata["output_switches"]["soil_climate_output"].asInt();
  BOOST_LOG_SEV(glg, debug) << "DONE assigning ModeData members from json.";

}

void ModelData::checking4run() {
  //run stage
  if(runstages == "eq") {
    runeq = true;
  } else if(runstages == "sp") {
    runsp = true;
  } else if(runstages == "tr") {
    runtr = true;
  } else if(runstages == "sc") {
    runsc = true;
  } else if(runstages == "eqsp") {
    runeq = true;
    runsp = true;
  } else if(runstages == "sptr") {
    runsp = true;
    runtr = true;
  } else if(runstages == "eqsptr") {
    runeq = true;
    runsp = true;
    runtr = true;
  } else if(runstages == "all") {
    runeq = true;
    runsp = true;
    runtr = true;
    runsc = false;
  } else {
    cout <<"the run stage " << runstages << "  was not recognized  \n";
    cout <<"should be one of 'eq', 'sp', 'tr','sc', 'eqsp', 'sptr', 'eqsptr', or 'all'";
    exit(-1);
  }

  //initilization modes for state variables
  if(initmodes =="default") {
    initmode =1;
  } else if(initmodes =="sitein") {
    initmode =2;
  } else if(initmodes =="restart") {
    initmode =3;
  } else {
    cout <<"the initialize mode " << initmodes << "  was not recognized  \n";
    cout <<"should be one of 'default', 'sitein', or 'restart'";
    exit(-1);
  }

  //model run I/O directory checking
  if (!(boost::filesystem::exists(outputdir))) {
    BOOST_LOG_SEV(glg, note) << "'" << outputdir << "' not recognized. Attempting to create...";
    
    boost::system::error_code returnedError;
    boost::filesystem::create_directories( outputdir, returnedError );

    if ( returnedError ) {
      BOOST_LOG_SEV(glg, fatal) << "There was some problem trying to create '" << outputdir << "'";
      exit(-1);
    }
  }

  if (reginputdir == "") {
    cout <<"directory for Region-level input was not recognized  \n";
    exit(-1);
  }

  if (grdinputdir == "") {
    cout <<"directory for Grided data iutput was not recognized  \n";
    exit(-1);
  }

  if (chtinputdir == "") {
    cout <<"directory for cohort data input was not recognized  \n";
    exit(-1);
  }

  if (initialfile == "" && initmode==2) {
    cout <<"directory for sitein file was not recognized  \n";
    exit(-1);
  }

  if (initialfile == "" && initmode==3) {
    cout <<"directory for restart file was not recognized  \n";
    exit(-1);
  }
};

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

bool ModelData::get_friderived() {
  return this->friderived;
}
void ModelData::set_friderived(const std::string &s) {
  BOOST_LOG_SEV(glg, info) << "Setting friderived to " << s;
  this->friderived = temutil::onoffstr2bool(s);
}
void ModelData::set_friderived(const bool v) {
  BOOST_LOG_SEV(glg, info) << "Setting friderived to " << v;
  this->friderived = v;
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
  s << table_row(15, "friderived", this->friderived);
  s << table_row(15, "nfeed", this->get_nfeed());
  s << table_row(15, "avlnflg", this->get_avlnflg());
  return s.str();
}


