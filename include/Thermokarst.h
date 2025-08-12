#ifndef THERMOKARST_H_
#define THERMOKARST_H_

#include <cmath>
#include <math.h>
#include <vector>
#include <algorithm>

#include "CohortData.h"
#include "EnvData.h"
#include "ThermokarstData.h"
#include "BgcData.h"
#include "RestartData.h"

#include "errorcode.h"
#include "timeconst.h"
#include "parameters.h"

#include "CohortLookup.h"

using namespace std;

class Thermokarst {
public:
  Thermokarst();

  Thermokarst(const std::string &exp_fname,
              const double cell_slope,
              const double cell_aspect,
              const double cell_elevation,
              const int y, const int x);

  ~Thermokarst();

  void load_projected_explicit_data(const std::string& exp_fname, int y, int x);
  
  void setThawDepth(double);

  void setCohortData(CohortData* cdp);
  void setAllEnvBgcData(EnvData* edp, BgcData* bdp);
  void setBgcData(BgcData* bdp, const int &ip);
  void setThermokarstData(ThermokarstData* tdp);
  void setCohortLookup(CohortLookup* chtlup);

  // void initializeParameter();
  void initializeState();
  void set_state_from_restartdata(const RestartData & rdata);

  // decide whether a thermokarst should initiate
  bool should_initiate(const int yr, const int midx, const std::string &stage);

  // initiate thermokarst related processes
  void initiate(int year);

  std::string report_thermokarst_inputs();

private:

  // There are two distinct types of fire "drivers":
  // 1) Generic fire based on fire recurrance interval (FRI).
  // 2) Distinct and explicitly defined fires.
  //
  // The FRI approach is used for equlibrium and spinup stages, while
  // explicitly defined fire is used for transient and scenario stages.
  //
  // With an FRI approach, each pixel has an FRI, or periodicity.
  // When the model reaches the correct time according to the FRI, the
  // pixel burns according to the values set for julian day of burn, area
  // of burn, and severity of burn. In other words fire will be the same
  // each time it occurs.
  //
  // With the explicit approach, each pixel has a time-series of
  // properties that define fire. The properties the same properties
  // that define fire under an FRI regime, but the pixel can have
  // different types of fire over the course of the timeseries.
  //
  // The timeseries can be defined several ways:
  //  1) arbitrarily generated sample data
  //  2) based on outputs from the ALFRESCO model
  //  3) based on the historical data
  //
  // The client generating the input files is responsible for ensuring
  // that a pixel with a 10km^2 area of burn is in a contiguous group of
  // 10 pixels each of which also uses a 10km^2 area of burn.

  int fri;
  int fri_jday_of_burn;
  int fri_area_of_burn;
  int fri_severity;
  double slope;
  double asp;
  double elev;

  bool fri_derived;

  std::vector<int> exp_thermokarst_mask;
  std::vector<int> exp_jday_of_thermokarst;
  std::vector<int> exp_thermokarst_severity;
  std::vector<int64_t> exp_area_of_thermokarst;

  double thaw_depth;

  firepar_bgc firpar; // >>> Need to address these somewhere else in data structures

  double folr;           // Fraction Organic Layer Removed
  double r_live_cn;      // Ratio of living veg. after thermokarst

  double r_dead2ag_cn;   // ratio of dead veg. after thermokarst
  double r_thermokarst2ag_cn;   // removed above-ground veg. after thermokarst

  CohortLookup * chtlu;
  CohortData * cd;

  ThermokarstData *tkdata;
  EnvData * edall;
  BgcData * bd[NUM_PFT];
  BgcData * bdall;

  double getThermokarstSoilRemoval(const int year);
  void getThermokarstAbgVegetation(const int ipft, const int year);

};

#endif /* THERMOKARST_H_ */
