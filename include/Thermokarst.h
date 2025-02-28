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

  Thermokarst(const std::string& exp_fname,
           const double cell_slope,
           const double cell_aspect,
           const double cell_elevation,
           const int y, const int x);

  ~Thermokarst();

  void load_projected_explicit_data(const std::string& exp_fname, int y, int x);
 
  void setCohortData(CohortData* cdp);
  void setAllEnvBgcData(EnvData* edp, BgcData* bdp);
  void setBgcData(BgcData* bdp, const int &ip);
  void setFirData(FirData* fdp);
  void setCohortLookup(CohortLookup* chtlup);

  void initializeParameter();
  void initializeState();
  void set_state_from_restartdata(const RestartData & rdata);

  bool should_thermokarst(const int yr, const int midx, const std::string& stage);

  // not used or fully implemented yet...
  //int lookup_severity(const int yr, const int midx, const std::string& stage);
  void thaw(int year);

  std::string report_fire_inputs();

private:

  // For now thermokarst will be based on explicit inputs
  // similarly to explicit fire history.
  //
  // Eventually we hope to integrate a state and transition
  // model to predict likelihoood of thermokarst occurrence.

  double slope;
  double asp;
  double elev;

  // These are following from Wildfire, but will need
  // renaming to thermokarst specific processes
  std::vector<int> exp_burn_mask;
  std::vector<int> exp_jday_of_burn;
  std::vector<int> exp_fire_severity;
  std::vector<int64_t> exp_area_of_burn;

  firepar_bgc firpar;

  double folb;           // Fraction of OL burned
  double r_live_cn;      // ratio of living veg. after burning
  double r_dead2ag_cn;   // ratio of dead veg. after burning
  double r_burn2ag_cn;   // burned above-ground veg. after burning

  CohortLookup * chtlu;
  CohortData * cd;

  FirData * fd;
  EnvData * edall;
  BgcData * bd[NUM_PFT];
  BgcData * bdall;

  double getThermokarstOrgSoilthick(const int year);
  void getBurnAbgVegetation(const int ipft, const int year);

};

#endif /* THERMOKARST_H_ */
