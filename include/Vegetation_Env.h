#ifndef VEGETATION_ENV_H_
#define VEGETATION_ENV_H_
#include <cmath>

#include "CohortLookup.h"
#include "states.h"
#include "fluxes.h"
#include "diagnostics.h"
#include "parameters.h"

#include "CohortData.h"
#include "EnvData.h"
#include "FireData.h"
#include "ThermokarstData.h"
#include "RestartData.h"

class Vegetation_Env {
public:

  Vegetation_Env();
  ~Vegetation_Env();

  int ipft;

  vegpar_env envpar;

  void setCohortLookup(CohortLookup * chtlup);
  void setEnvData(EnvData* edatap);
  void setFirData(FirData* fdp);

  void initializeParameter();
  void initializeState();
  void set_state_from_restartdata(const RestartData & rdata);

  void updateRadiation(double leaf_area_index, double foliar_projected_cover);
  void updateWaterBalance(const double &daylhr, double leaf_area_index, double foliar_projected_cover);

private:

  EnvData * ed;
  FirData * fd;
  CohortLookup * chtlu;

  //function
  double getRainInterception(const double & rain, const double & lai);
  double getSnowInterception(const double & snow, const double & lai);
  double getLeafStomaCond(const double & ta, const double &  parin,
                          const double & vpdin, const double& btran,
                          double & m_ppfd, double & m_vpd );
  double getCanopySubl(const double & rac, const double & sinter,
                       const double & lai );

  double getPenMonET(const double & ta, const double& vpd, const double &irad,
                     const double &rv, const double & rh);

};
#endif /*VEGETATION_ENV_H_*/
