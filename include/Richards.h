
/*!\file
 * Implementation of Richard's law for soil water dynamics*/

#ifndef RICHARDS_H_
#define RICHARDS_H_

#include <cmath>
#include <limits>

#include "CohortData.h"
#include "EnvData.h"

#include "Layer.h"
#include "SoilLayer.h"
#include "CrankNicholson.h"

class Richards {
public :
  Richards();
  ~Richards();

  int num_al;   // active layers' layer numbers
  double qdrain; // mm/day
  double qinfil; // mm/day
  double qevap; // mm/day
  double excess_runoff; //Runoff discovered in Richards (post getRunoff)
  double e_ice; //ice impedance factor (CLM5)


  //Array to hold lateral drainage values for output to file.
  double layer_drain[MAX_SOI_LAY];
  double percolation[MAX_SOI_LAY];

  void update(Layer *fstsoill, Layer* bdrainl, const double & bdraindepth,
              const double & fbaseflow, const double & watertab,
              double root_water_up[MAX_SOI_LAY],
              const double & evap, const double & infil,
              const double & cell_slope, const double &ts);

  void setCohortData(CohortData* cdp);
  void setEnvData(EnvData* edp);

  CrankNicholson cn;

private:

  EnvData ed;

  void prepareSoilColumn(Layer *currsoill, int drainind);
  void clearRichardsArrays();
  void computeHydraulicProperties(Layer *topsoill, int drainind);
  void computeMoistureFluxesAndDerivs(Layer *topsoill, int topind, int drainind);
  void computeLHS(Layer *topsoill, int topind, int drainind);
  void computeRHS(Layer *topsoill, int topind, int drainind);
  void checkPercolationValidity(Layer *topsoill, Layer *drainl, int topind, int drainind);

  Layer * drainl;
  double z_watertab; //Temporary var to hold the crudely calculated water table depth calculated in prepareSoilColumn. In mm.

  //The following arrays are made artificially large in order for the
  // indexing in the calculations to make more sense. The layer indices
  // (layer->solind) are 1-based, with 1 being moss (skipped in soil water).

  double qtrans[MAX_SOI_LAY+1];
  double tridiag_error[MAX_SOI_LAY+1];
  double fluxNet0[MAX_SOI_LAY+1];
  double fluxNet1[MAX_SOI_LAY+1];
  double qin[MAX_SOI_LAY+1];
  double qout[MAX_SOI_LAY+1];
  double s1[MAX_SOI_LAY+1];
  double s2[MAX_SOI_LAY+1];
  double imped[MAX_SOI_LAY+1];
  double hk[MAX_SOI_LAY+1];
  double dhkdw[MAX_SOI_LAY+1];
  double dsmpdw[MAX_SOI_LAY+1];
  double smp[MAX_SOI_LAY+1];
  double dqidw0[MAX_SOI_LAY+1];
  double dqidw1[MAX_SOI_LAY+1];
  double dqodw1[MAX_SOI_LAY+1];
  double dqodw2[MAX_SOI_LAY+1];

  //Incoming values. These already exist in the layers, and are
  // copied to arrays simply so that the equations in Richards
  // are easily comparable to the CLM paper.
  double Bsw[MAX_SOI_LAY+1]; //bsw hornberger constant (by horizon type)
  double ksat[MAX_SOI_LAY+1]; //Saturated hydraulic conductivity
  double psisat[MAX_SOI_LAY+1];

  double vol_liq[MAX_SOI_LAY+1];//volumetric liquid water
  double vol_ice[MAX_SOI_LAY+1];
  double vol_h2o[MAX_SOI_LAY+1]; //Total volumetric water (liq + ice)
  double vol_poro[MAX_SOI_LAY+1];
  double liq_poro[MAX_SOI_LAY+1];
  double soi_liq[MAX_SOI_LAY+1];
  double ice_frac[MAX_SOI_LAY+1];
  double effminliq[MAX_SOI_LAY+1];
  double effmaxliq[MAX_SOI_LAY+1];
  double dt_dz[MAX_SOI_LAY+1];
  double z_h[MAX_SOI_LAY+1]; //Depth of layer bottom in mm, named to match CLM paper
  double dzmm[MAX_SOI_LAY+1];      // layer thickness in mm
  double nodemm[MAX_SOI_LAY+1]; //depth of center of layer thawed portion in mm

  double deltathetaliq[MAX_SOI_LAY+1]; //Results from tridiagonal calculation
  double amx[MAX_SOI_LAY+1];
  double bmx[MAX_SOI_LAY+1];
  double cmx[MAX_SOI_LAY+1];
  double rmx[MAX_SOI_LAY+1];

  double max_tridiag_error;
  double delta_t = SEC_IN_DAY;
  double dtmin;  // minimum timestep length (sec)
  double toler_upper;  // Tolerance to halve length of substep
  double toler_lower;  // Tolerance to double length of substep

};

#endif /*RICHARDS_H_*/
