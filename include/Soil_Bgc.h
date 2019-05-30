#ifndef SOIL_BGC_H_
#define SOIL_BGC_H_

#include "errorcode.h"

#include "CohortData.h"
#include "EnvData.h"
#include "FireData.h"
#include "BgcData.h"
#include "RestartData.h"

#include "CohortLookup.h"
#include "ModelData.h"

#include "parameters.h"

#include "Ground.h"

#include <cmath>

using namespace std;

class Soil_Bgc {
public:
  Soil_Bgc();
  ~Soil_Bgc();

  soistate_bgc tmp_sois;   // the previous soistate_bgc
  soistate_bgc del_sois;   // the change of soistate_bgc

  soi2soi_bgc del_soi2soi;
  soi2atm_bgc del_soi2a;
  soi2lnd_bgc del_soi2l;

  atm2soi_bgc del_a2soi;

  soipar_bgc bgcpar;
  soipar_cal calpar;

  void setCohortData(CohortData* cdp);
  void setEnvData(EnvData* edp);
  void setBgcData(BgcData* bdp);
  void setFirData(FirData* fdp);
  void setCohortLookup(CohortLookup* chtlup);

  void setGround(Ground * ground);

  void initializeParameter();

  void initializeState();
  void set_state_from_restartdata(const RestartData & resdata);

  void assignCarbonBd2LayerMonthly();
  void assignCarbonLayer2BdMonthly();

  void deltac();
  void deltan();
  void deltastate();

  void prepareIntegration(const bool &mdnfeedback, const bool &mdavlnflg,
                          const bool &mdbaseline);
  void afterIntegration();
  void clear_del_structs();

  int get_nfeed();
  void set_nfeed(int);

  int get_avlnflg();
  void set_avlnflg(int);

  int get_baseline();
  void set_baseline(int);

  void CH4Flux(const int mind, const int id);

private:

  // NOTE: seems like these 3 variables are supposed to shadow the
  // corresponding ModelData members. Not sure if this should be
  // strictly enforced somehow?

  int nfeed;  // soil-plant-air N module switch

  int avlnflg; // open-N cycle switch; otherwise, N budget method used to
               // balance the N I/O from the ecosystem

  int baseline;  // open-N cycle switch; otherwise, N budget method used to
                 // balance the N I/O from the ecosystem

  double d2wdebrisc;
  double d2wdebrisn;
  double mossdeathc;
  double mossdeathn;
  double ltrflc[MAX_SOI_LAY];     //litterfall C into each soil layer
  double ltrfln[MAX_SOI_LAY];     //litterfall N into each soil layer

  double rtnextract[MAX_SOI_LAY];  // root N extraction from each soil layer

  double kdshlw;
  double kddeep;
  double decay;
  double nup;

  double totdzliq;     // total drainage zone liq water
  double totdzavln;    // total drainage zone avln

  double totnetnmin;   // total net N mineralization
  double totnextract;  // total root N extract (uptake) from soil

  CohortData * cd;
  EnvData * ed;
  BgcData * bd;
  FirData * fd;

  CohortLookup * chtlu;
  Ground * ground;

  //TODO This should likely be replaced with the same solver
  //  used for soil moisture
  void TriSolver(int matrix_size, double *A, double *D, double *C, double *B, double *X);

  void initSoilCarbon(double & initshlwc, double & initdeepc,
                      double & initminec);
  void initOslayerCarbon(double & shlwc, double & deepc);
  void initMslayerCarbon(double & minec);

  double getRhmoist(const double &vsm, const double & moistmin,
                    const double & moistmax, const double & moistopt);
  double getRhq10(const double & tsoil);

  double getNimmob(const double & soilh2o, const double & soilorgc,
                   const double & soilorgn, const double & availn,
                   const double & ksoil, const double kn2);

  double getNetmin(const double & nimmob, const double & soilorgc,
                   const double & soilorgn,
                   const double & rh, const double & tcnsoil,
                   const double & decay, const double & nup );

  double getKnsoilmoist(const double & vsm);   //

  void updateKdyrly4all();

  double getKdyrly(double& yrltrcn, const double lcclnc, const double & kdc);

};
#endif /*SOIL_BGC_H_*/
