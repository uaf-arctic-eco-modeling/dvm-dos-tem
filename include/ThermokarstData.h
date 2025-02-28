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

  soidiag_fir thermokarst_soid;

  veg2atm_fir thermokarst_v2a;
  veg2soi_fir thermokarst_v2soi;
  veg2dead_fir thermokarst_v2dead;

  soi2atm_fir thermokarst_soi2a;
  atm2soi_fir thermokarst_a2soi;

  void init();
  void beginOfYear();
  void endOfYear();
  void beginOfMonth();
  void burn();
  
  std::string report_to_string(const std::string& msg);


};

#endif /*THERMOKARSTDATA_H_*/
