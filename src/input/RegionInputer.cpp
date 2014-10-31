
#include "RegionInputer.h"
#include "../TEMUtilityFunctions.h"
#include "../TEMLogger.h"

extern src::severity_logger< severity_level > glg;


RegionInputer::RegionInputer() {
};

RegionInputer::~RegionInputer() {
};

void RegionInputer::init() {
  if(md!=NULL) {
    act_co2yr = initCO2file(md->reginputdir);
  } else {
    string msg = "inputer in RegionInputer::init is null";
    cout<<msg+"\n";
    exit(-1);
  }
};

int RegionInputer::initCO2file(string &dir) {

  this->co2filename = dir +"co2.nc";

  if (md->runsc) {
    BOOST_LOG_SEV(glg, info) << "Running in scenario stage! Make sure that the co2_sc.nc file exists!";
    this->co2filename = dir +"co2_sc.nc";  //Yuan: read in CO2 ppm from projection
  }

  NcFile co2File = temutil::open_ncfile(this->co2filename);

  NcDim* yrD = temutil::get_ncdim(co2File,"YEAR");

  return yrD->size();
}

void RegionInputer::getCO2(RegionData *rd) {

  NcFile co2File = temutil::open_ncfile(this->co2filename);

  NcVar* co2yrV = temutil::get_ncvar(co2File, "YEAR");
  NcVar* co2V = temutil::get_ncvar(co2File, "CO2");

  NcBool nb1 = co2yrV->get(&rd->co2year[0], rd->act_co2yr);
  NcBool nb2 = co2V->get(&rd->co2[0], rd->act_co2yr);

  if(!nb1 || !nb2) {
    string msg = "problem in reading CO2 in RegionInputer::getCO2 ";
    cout<<msg+"\n";
    exit(-1);
  }

}

void RegionInputer::setModelData(ModelData* mdp) {
  md = mdp;
};

