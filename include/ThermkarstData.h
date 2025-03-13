#ifndef THERMOKARSTDATA_H_
#define THERMOKARSTDATA_H_
/*! this class contains the fire at annually time steps.
*/
#include <iostream>
#include <math.h>
#include <string>
#include <sstream>

#include "diagnostics.h"
#include "fluxes.h"
#include "states.h"
#include "timeconst.h"

class ThermokarstData {
public:

  ThermokarstData();
  ~ThermokarstData();

  void clear();

  bool useseverity;

  // soidiag_fir fire_soid;
  soidiag_thermokarst thermokarst_soid;

  // veg2atm_fir fire_v2a;
  veg2atm_thermokarst thermokarst_v2a;

  // veg2soi_fir fire_v2soi;
  veg2soi_thermokarst thermokarst_v2soi;

  // veg2dead_fir fire_v2dead;
  veg2dead_thermokarst thermokarst_v2dead;

  // soi2atm_fir fire_soi2a;
  soi2atm_thermokarst thermokarst_soi2a;

  // atm2soi_fir fire_a2soi;
  atm2soi_thermokarst thermokarst_a2soi;

  void init();
  void beginOfYear();
  void endOfYear();
  void beginOfMonth();
  void burn();
  
  std::string report_to_string(const std::string& msg);


};

#endif /*FIREDATA_H_*/
