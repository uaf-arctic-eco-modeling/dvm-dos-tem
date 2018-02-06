#ifndef FIREDATA_H_
#define FIREDATA_H_
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

class FirData {
public:

  FirData();
  ~FirData();

  void clear();

  bool useseverity;

  soidiag_fir fire_soid;

  veg2atm_fir fire_v2a;
  veg2soi_fir fire_v2soi;
  veg2dead_fir fire_v2dead;

  soi2atm_fir fire_soi2a;
  atm2soi_fir fire_a2soi;

  void init();
  void beginOfYear();
  void endOfYear();
  void beginOfMonth();
  void burn();
  
  std::string report_to_string(const std::string& msg);


};

#endif /*FIREDATA_H_*/
