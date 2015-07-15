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

ModelData::~ModelData() {}

ModelData::ModelData(Json::Value controldata){

  BOOST_LOG_SEV(glg, debug) << "Creating a ModelData. New style constructor with injected controldata...";
  
  std::string stgstr(controldata["stage_settings"]["run_stage"].asString());
  runeq = (stgstr.find("eq") != std::string::npos) ? true : false;
  runsp = (stgstr.find("sp") != std::string::npos) ? true : false;
  runtr = (stgstr.find("tr") != std::string::npos) ? true : false;
  runsc = (stgstr.find("sc") != std::string::npos) ? true : false;

  initmode = controldata["stage_settings"]["restart"].asInt();  // may become obsolete
  parameter_dir = controldata["IO"]["parameter_dir"].asString();
  changeclimate = controldata["model_settings"]["dynamic_climate"].asInt();
  changeco2 = controldata["model_settings"]["varied_co2"].asInt();
  updatelai = controldata["model_settings"]["dynamic_lai"].asInt();
  useseverity = controldata["model_settings"]["fire_severity_as_input"].asInt();

}


ModelData::ModelData() {
  runeq = false;
  runsp = false;
  runtr = false;
  runsc = false;
  set_envmodule(false);
  set_bgcmodule(false);
  set_dvmmodule(false);
  set_dslmodule(false);
  set_dsbmodule(false);
  set_friderived(false);
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


