#ifndef VEGETATION_BGC_H_
#define VEGETATION_BGC_H_
#include "CohortLookup.h"
#include "ModelData.h"

#include "CohortData.h"
#include "EnvData.h"
#include "FireData.h"
#include "ThermokarstData.h"
#include "BgcData.h"
#include "RestartData.h"

#include "parameters.h"

#include "Soil_Bgc.h"

#include "Vegetation.h"

#include <cmath>

class Vegetation_Bgc {
public:
  Vegetation_Bgc();
  ~Vegetation_Bgc();

  int ipft;

  vegpar_cal calpar;
  vegpar_bgc bgcpar;

  vegstate_bgc tmp_vegs;

  atm2veg_bgc del_a2v;
  veg2atm_bgc del_v2a;
  veg2soi_bgc del_v2soi;
  soi2veg_bgc del_soi2v;
  veg2veg_bgc del_v2v;
  vegstate_bgc del_vegs;

  void initializeParameter();

  void initializeState();
  void set_state_from_restartdata(const RestartData & rdata);

  void prepareIntegration(const bool &nfeedback);
  void delta();
  void deltanfeed();
  void deltastate();
  void afterIntegration();

  //void adapt();
  void adapt_c2n_ratio_with_co2(const double & yreet, const double & yrpet,
      const double & initco2, const double & currentco2);

  void setCohortLookup(CohortLookup* chtlup);

  void setCohortData(CohortData* cdp);
  void setEnvData(EnvData* edp);
  void setBgcData(BgcData* bdp);

  bool get_nfeed();
  void set_nfeed(bool);
  void set_nfeed(const std::string &value);

private:

  bool nfeed; // NOTE: It seems like this is probably supposed to shadow
  // ModelData.nfeed. Not sure if this should be strictly
  // enforced somehow?


  //fraction of N extraction in each soil layer for current PFT
  double fracnuptake[MAX_SOI_LAY];

  double fltrfall; //season fraction of max. monthly litterfalling fraction
  double dleafc; // C requirement of foliage growth at current timestep
  double d2wdebrisc;
  double d2wdebrisn;

  CohortLookup * chtlu;

  CohortData * cd;
  EnvData * ed;
  BgcData * bd;

  void updateCNeven(const double & yreet,const double & yrpet,
                    const double & initco2,const double & currentco2 );

  double getGPP(const double &co2, const double & par,
                const double &leaf, const double & foliage,
                const double &ftemp, const double & gv);

  double getTempFactor4GPP(const double & tair, const double & tgppopt);
  double getGV(const double & eet,const double & pet );

  double getRm(const double & vegc,const double & raq10, const double &kr);

  /*!  rq10: effect of temperature on plant respiration, updated every month */
  double getRaq10(const double & tair);

  /*! kr: for calculating plant maintanence respiration*/
  double getKr(const double & vegc, const int & ipart);

  double getNuptake(const double & foliage, const double & raq10,
                    const double & kn1, const double & nmax);

};

#endif /*VEGETATION_BGC_H_*/
