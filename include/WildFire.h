#ifndef WILDFIRE_H_
#define WILDFIRE_H_

#include <cmath>
#include <math.h>
#include <vector>
#include <algorithm>

#include "CohortData.h"
#include "EnvData.h"
#include "FireData.h"
#include "BgcData.h"
#include "RestartData.h"

#include "errorcode.h"
#include "timeconst.h"
#include "parameters.h"

#include "CohortLookup.h"

using namespace std;

class WildFire {
public:
  WildFire();

  WildFire(const std::string& fri_fname,
           const std::string& exp_fname,
           const double cell_slope,
           const double cell_aspect,
           const double cell_elevation,
           const int y, const int x);
  
  ~WildFire();

  int getFRI();
 
  void setCohortData(CohortData* cdp);
  void setAllEnvBgcData(EnvData* edp, BgcData* bdp);
  void setBgcData(BgcData* bdp, const int &ip);
  void setFirData(FirData* fdp);
  void setCohortLookup(CohortLookup* chtlup);

  void initializeParameter();
  void initializeState();
  void set_state_from_restartdata(const RestartData & rdata);

  bool should_ignite(const int yr, const int midx, const std::string& stage);

  // not used or fully implemented yet...
  //int lookup_severity(const int yr, const int midx, const std::string& stage);
  void burn(int year);

  std::string report_fire_inputs();

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

  std::vector<int> exp_burn_mask;
  std::vector<int> exp_jday_of_burn;
  std::vector<int> exp_fire_severity;
  std::vector<int> exp_area_of_burn;



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

  double getBurnOrgSoilthick(const int year);
  void getBurnAbgVegetation(const int ipft, const int year);

  ////////
  // MAYBE get rid of all these???
  //  int firstfireyr;
  //  int oneyear;
  //  int onemonth;
  //  int oneseason;
  //  int onesize;
  //////////////

  //Yuan: the following if using years will result in huge
  //        memory needs, if spin-up is long
  // Hopefully get rid of these too...
  //  int fyear[MAX_FIR_OCRNUM];
  //  int fseason[MAX_FIR_OCRNUM];
  //  int fmonth[MAX_FIR_OCRNUM];
  //  int fsize[MAX_FIR_OCRNUM];
  //  int fseverity[MAX_FIR_OCRNUM];
  ///////////////////

  // Unused...
  //void prepareDrivingData();
  //int getOccur(const int & yrind, const bool & fridrived); //Yuan: modified;
  //void deriveFireSeverity();
};

#endif /* WILDFIRE_H_ */
