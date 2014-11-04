#include <cstdlib>
#include <netcdfcpp.h>

#include "RegionData.h"

#include "../TEMUtilityFunctions.h"
#include "../TEMLogger.h"
extern src::severity_logger< severity_level > glg;

RegionData::RegionData() {
};

RegionData::~RegionData() {
};

void RegionData::set_act_co2yr_from_file(std::string filename) {
  
  NcFile co2File = temutil::open_ncfile(filename);
  
  NcDim* yrD = temutil::get_ncdim(co2File,"YEAR");

  this->act_co2yr = yrD->size();

}

void RegionData::setup_co2_and_yr_from_file(std::string filename){
  
  NcFile co2File = temutil::open_ncfile(filename);
  
  NcVar* co2yrV = temutil::get_ncvar(co2File, "YEAR");
  NcVar* co2V = temutil::get_ncvar(co2File, "CO2");
  
  NcBool nb1 = co2yrV->get(&this->co2year[0], this->act_co2yr);
  NcBool nb2 = co2V->get(&this->co2[0], this->act_co2yr);
  
  if(!nb1 || !nb2) {
    BOOST_LOG_SEV(glg, fatal) << "There was a problem reading/setting CO2 "
                              << "variable(s) from " << filename << "!";
    exit(-1);

  }
}
