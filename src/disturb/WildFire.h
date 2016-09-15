#ifndef WILDFIRE_H_
#define WILDFIRE_H_

#include <cmath>
#include <math.h>
#include <vector>
#include <algorithm>

#include "../data/CohortData.h"
#include "../data/EnvData.h"
#include "../data/FirData.h"
#include "../data/BgcData.h"
#include "../data/RestartData.h"

#include "../inc/errorcode.h"
#include "../inc/timeconst.h"
#include "../inc/parameters.h"

#include "../lookup/CohortLookup.h"

using namespace std;
class WildFire {
public:
  WildFire();
  WildFire(const std::string& fname, const int y, const int x);
  
  ~WildFire();
  
//  int fri;
//
//  int oneseverity;  //Yuan: fire severity category

  void setCohortData(CohortData* cdp);
  void setAllEnvBgcData(EnvData* edp, BgcData* bdp);
  void setBgcData(BgcData* bdp, const int &ip);
  void setFirData(FirData* fdp);
  void setCohortLookup(CohortLookup* chtlup);

  void initializeParameter();
  void initializeState();
  void set_state_from_restartdata(const RestartData & rdata);

  bool should_ignite(const int yr, const int midx, const std::string& stage);
  int derive_fire_severity(const int drainage, const int day_of_burn, const int size);

  void burn();

private:

  int fri;
  std::vector<int> severity;
  std::vector<int> explicit_fire_year;

  int fri_day_of_burn;
  float fri_area_of_burn;
  
  // explicit fire occurance
  std::vector<int> day_of_burn;
  std::vector<float> area_of_burn;   // km^2?

  firepar_bgc firpar;

  double r_live_cn;      // ratio of living veg. after burning
  double r_dead2ag_cn;   // ratio of dead veg. after burning
  double r_burn2ag_cn;   // burned above-ground veg. after burning

  CohortLookup * chtlu;
  CohortData * cd;

  FirData * fd;
  EnvData * edall;
  BgcData * bd[NUM_PFT];
  BgcData * bdall;

  double getBurnOrgSoilthick(const int severity);
  void getBurnAbgVegetation(const int &ip, const int severity);

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
