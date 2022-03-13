#ifndef SOIL_ENV_H_
#define SOIL_ENV_H_

#include "Stefan.h"
#include "Richards.h"
#include "TemperatureUpdator.h"

#include "CohortData.h"
#include "EnvData.h"
#include "FireData.h"
#include "RestartData.h"

#include "errorcode.h"
#include "parameters.h"
#include "layerconst.h"
#include "CohortLookup.h"

#include "Ground.h"

class Soil_Env {
public:

  Soil_Env();
  ~Soil_Env();

  soipar_env envpar;

  double root_water_up[MAX_SOI_LAY];

  Richards richards;
  Stefan stefan;
  TemperatureUpdator tempupdator;

  void setGround(Ground* grndp);
  void setCohortData(CohortData* cdp);
  void setEnvData(EnvData* edp);
  void setCohortLookup(CohortLookup * chtlup);

  void resetDiagnostic();   /*! reset diagnostic variables to initial values */

  void initializeParameter();
  void initializeState();
  void set_state_from_restartdata(const RestartData & rdata);

  void updateDailyGroundT(const double & tdrv, const double & dayl);
  void updateDailySM(double weighted_veg_tran);

  double getSoilTransFactor(double r_e_ij[MAX_SOI_LAY], Layer* fstsoill,
                            const double vrootfr[MAX_SOI_LAY]);

  void retrieveDailyTM(Layer* toplayer, Layer* lstsoill);
  void checkSoilLiquidWaterValidity(Layer *topsoill, int topind);

  double getWaterTable(Layer* fstsoil);

private:

  Ground * ground;
  CohortData * cd;
  EnvData * ed;
  CohortLookup* chtlu;

  double ponding_max_mm;//max ponding (surface water storage) (mm)

  void updateDailySurfFlux(Layer* frontl, const double & dayl);
  void updateDailySoilThermal4Growth(Layer* fstsoill, const double &tsurface);
  void updateLayerStateAfterThermal(Layer* fstsoill, Layer *lstsoill,
                                    Layer* botlayer);

  void retrieveDailyFronts();

  double getEvaporation(const double & dayl, const double &rad);
  double getPenMonET(const double & ta, const double& vpd, const double &irad,
                     const double &rv, const double & rh);
  double getRunoff(Layer* fstsoill, Layer* drainl,
                   const double & rnth,
                   const double & melt);

  // the following codes not used anymore
  double getInflFrozen(Layer *fstminl, const double &  rnth,
                       const double & melt);
  double updateLayerTemp5Lat(Layer* currl, const double & infil);

};

#endif /*SOIL_ENV_H_*/
