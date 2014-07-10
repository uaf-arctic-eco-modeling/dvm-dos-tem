#include <exception>
#include <json/value.h>

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
  if (outputdir == "") {
    cout <<"directory for output was not recognized  \n";
    exit(-1);
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


