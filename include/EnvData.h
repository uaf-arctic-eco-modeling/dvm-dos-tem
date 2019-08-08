#ifndef ENVDATA_H_
#define ENVDATA_H_

#include <deque>

#include "diagnostics.h"
#include "fluxes.h"
#include "states.h"

#include "errorcode.h"
#include "layerconst.h"
#include "timeconst.h"
#include "physicalconst.h"
#include "cohortconst.h"

#include "Climate.h"
#include "CohortData.h"

using namespace std;

class EnvData {
public:
  EnvData();
  ~EnvData();

  void clear();

  // for daily  - 'd' is daily
  atmstate_env d_atms;  // last 's' - state variable
  vegstate_env d_vegs;
  snwstate_env d_snws;
  soistate_env d_sois;

  atmdiag_env d_atmd;   // last 'd' - diagnostic variable
  vegdiag_env d_vegd;
  snwdiag_env d_snwd;
  soidiag_env d_soid;

  lnd2atm_env d_l2a;    // 'l' - land, '2' - 'to', 'a' - atm
  atm2lnd_env d_a2l;
  atm2veg_env d_a2v;    // 'v' - veg
  veg2atm_env d_v2a;
  veg2gnd_env d_v2g;    // 'g' - ground
  soi2lnd_env d_soi2l;  // 'soi' - soil
  soi2atm_env d_soi2a;
  snw2atm_env d_snw2a;  // 'snw' - snow
  snw2soi_env d_snw2soi;

  // monthly
  atmstate_env m_atms;
  vegstate_env m_vegs;
  snwstate_env m_snws;
  soistate_env m_sois;

  atmdiag_env m_atmd;
  vegdiag_env m_vegd;
  snwdiag_env m_snwd;
  soidiag_env m_soid;

  lnd2atm_env m_l2a;
  atm2lnd_env m_a2l;
  atm2veg_env m_a2v;
  veg2atm_env m_v2a;
  veg2gnd_env m_v2g;
  soi2lnd_env m_soi2l;
  soi2atm_env m_soi2a;
  snw2atm_env m_snw2a;
  snw2soi_env m_snw2soi;

  // annually
  atmstate_env y_atms;
  vegstate_env y_vegs;
  snwstate_env y_snws;
  soistate_env y_sois;

  atmdiag_env y_atmd;
  vegdiag_env y_vegd;
  snwdiag_env y_snwd;
  soidiag_env y_soid;

  lnd2atm_env y_l2a;
  atm2lnd_env y_a2l;
  atm2veg_env y_a2v;
  veg2atm_env y_v2a;
  veg2gnd_env y_v2g;
  soi2lnd_env y_soi2l;
  soi2atm_env y_soi2a;
  snw2atm_env y_snw2a;
  snw2soi_env y_snw2soi;

  //Arrays to hold a month's worth of variables for daily
  // netCDF output.
  double daily_eet[31];
  double daily_pet[31];
  double daily_swesum[31];
  double daily_snowthick[31];
  double daily_tshlw[31];
  double daily_tdeep[31];
  double daily_tminea[31];
  double daily_tmineb[31];
  double daily_tminec[31];
  double daily_vwcshlw[31];
  double daily_vwcdeep[31];
  double daily_vwcminea[31];
  double daily_vwcmineb[31];
  double daily_vwcminec[31];
  double daily_tcshlw[31];
  double daily_tcdeep[31];
  double daily_tcminea[31];
  double daily_tcmineb[31];
  double daily_tcminec[31];
  double daily_hkshlw[31];
  double daily_hkdeep[31];
  double daily_hkminea[31];
  double daily_hkmineb[31];
  double daily_hkminec[31];
  double daily_watertab[31];
  double daily_layer_drain[31][MAX_SOI_LAY];
  double daily_qdrain[31];
  double daily_qinfl[31];
  double daily_qover[31];
  double daily_frontsdepth[31][MAX_NUM_FNT];
  int daily_frontstype[31][MAX_NUM_FNT];
  double daily_tlayer[31][MAX_SOI_LAY];
  double daily_root_water_uptake[31][MAX_SOI_LAY];
  double daily_percolation[31][MAX_SOI_LAY];

  double monthsfrozen;      // months since bottom soil frozen started -
                            //   24 months is the criterion for permafrost
  int rtfrozendays;         // soil top rootzone continuously frozen days
  int rtunfrozendays;       // soil top rootzone continuously unfrozen days

  CohortData * cd;

  // initializing yearly/monthly accumulators
  void atm_beginOfYear();
  void veg_beginOfYear();
  void grnd_beginOfYear();
  void atm_beginOfMonth();
  void veg_beginOfMonth();
  void grnd_beginOfMonth();

  // initializing some daily variables
  void grnd_beginOfDay();

  // accumulating/averaging monthly variables at the end of day
  void atm_endOfDay(const int & dinm);
  void veg_endOfDay(const int & dinm);
  void grnd_endOfDay(const int & dinm, const int & doy);

  // accumulating/averaging yearly variables at the end of month
  void atm_endOfMonth();
  void veg_endOfMonth(const int & currmind);
  void grnd_endOfMonth(const int & currmind);

  void update_from_climate(const Climate& clm, const int mid, const int dayid);

private:
};

#endif /*ENVDATA_H_*/
