/*
 * RunRegion.cpp
 *
 * Region-level initialization, run, and output (if any)
 *    Note: the output modules are put here, so can be flexible for outputs
 *
*/

#include <string>

#include "RunRegion.h"

RunRegion::RunRegion() {
};

RunRegion::~RunRegion() {
};

int RunRegion::reinit(const int &recid) {
  if (recid<0) {
    return -1;
  }

  //region.rd.act_co2yr = rinputer.act_co2yr;
  region.rd.set_act_co2yr_from_file(rinputer.co2filename);

  
  // needs to set rd->co2[0] thru rd->co2[act_co2yr] to values read from co2file, (CO2 variable)
  // needs to set rd->co2yr[0] thru rd->co2[act_co2yr] to values read from co2file, (CO2 variable)
  // ??
  //  region.rd.setup_co2yr_from_file();
  //  region.rd.setup_co2_from_file();
  //  NcFile co2File = temutil::open_ncfile(co2filename);
  //  
  //  NcVar* co2yrV = temutil::get_ncvar(co2File, "YEAR");
  //  NcVar* co2V = temutil::get_ncvar(co2File, "CO2");
  //  
  //  NcBool nb1 = co2yrV->get(&region.rd->co2year[0], region.rd->act_co2yr);
  //  NcBool nb2 = co2V->get(&regon.rd->co2[0], region.rd->act_co2yr);
  //  
  //  if(!nb1 || !nb2) {
  //    string msg = "problem in reading CO2 in RegionInputer::getCO2 ";
  //    cout<<msg+"\n";
  //    exit(-1);
  //  }

  
  rinputer.getCO2(&region.rd);
  region.init();
  region.getinitco2();
  return 0;
};


