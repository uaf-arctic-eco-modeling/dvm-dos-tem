#ifndef COHORTDATA_H_
#define COHORTDATA_H_

#include <deque>

#include "errorcode.h"
#include "timeconst.h"
#include "cohortconst.h"

#include "states.h"
#include "diagnostics.h"

#include "ModelData.h"

using namespace std;

class CohortData {
public:
  CohortData();
  CohortData(int year, int month, int day,
      const ModelData* modeldatapointer);

  ~CohortData();

  void clear();

  int chtid;
  int year;     // only used for output (old format)
  int month;    // only used for output (old format)

  int cmttype; // vegetation community type
  int yrsdist; // years since last disturbance
  int mthsdist; //months since last disturbance
  
  int drainage_type;
  double cell_slope;
  double cell_aspect;
  double cell_elevation;

  bool hasnonvascular; //if exists non-vascular PFT(s) within the vegetation community

  int vegyear[MAX_VEG_SET];
  int vegtype[MAX_VEG_SET];
  double vegfrac[MAX_VEG_SET];

  int fri;

  // community dimension
  vegstate_dim d_veg;   //at daily-interval   - 'd' is for daily
  vegstate_dim m_veg;   //at monthly-interval - 'm' is for monthly
  vegstate_dim y_veg;   //at yearly-interval  - 'y' is for yearly

  vegdiag_dim d_vegd;   //at daily-interval   - 'd' is for monthly
  vegdiag_dim m_vegd;   //at monthly-interval - 'm' is for monthly
  vegdiag_dim y_vegd;   //at yearly-interval  - 'y' is for yearly

  snwstate_dim d_snow;   //at daily-interval   - 'd' is for daily
  snwstate_dim m_snow;   //at monthly-interval - 'm' is for monthly
  snwstate_dim y_snow;   //at yearly-interval  - 'y' is for yearly

  soistate_dim d_soil;   //at daily-interval   - 'd' is for daily
  soistate_dim m_soil;   //at monthly-interval - 'm' is for monthly
  soistate_dim y_soil;   //at yearly-interval  - 'y' is for yearly

  //the last 10 years eet/ppt for long-lasting effect of drought on GPP,
  //  through f(phenology)
  deque <double> prveetmxque[NUM_PFT];
  // deque to store 'unnormleafmx' of at-most previous 10 years
  deque <double> prvunnormleafmxque[NUM_PFT];
  // deque to store 'thermal time (degree-day)' of at-most previous 10 years
  deque <double> prvgrowingttimeque[NUM_PFT];
  // a deque-array to store previous 10 year 'topt'
  deque <double> toptque[NUM_PFT];

  void beginOfYear();
  void beginOfMonth();
  void beginOfDay();

  void endOfDay(const int & dinm);
  void endOfMonth();
  void endOfYear();

};

#endif /*COHORTDATA_H_*/
