
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
  double e_ice; //ice impedance factor (CLM5)

  //Array to hold lateral drainage values for output to file.
  double layer_drain[MAX_SOI_LAY];
  double percolation[MAX_SOI_LAY];

  void update(Layer *fstsoill, Layer* bdrainl, const double & bdraindepth,
              const double & fbaseflow, const double & watertab,
              double root_water_up[MAX_SOI_LAY],
              const double & evap, const double & infil,
              const double & cell_slope);

  void setCohortData(CohortData* cdp);
  void setEnvData(EnvData* edp);

  CrankNicholson cn;

private:

  EnvData ed;

  void prepareSoilColumn(Layer *currsoill, int drainind);
  void clearRichardsArrays();
  void computeHydraulicProperties(Layer *fstsoill, int drainind);
  void computeMoistureFluxesAndDerivs(Layer *fstsoill, int topind, int drainind);
  void computeLHS(Layer *fstsoill, int topind, int drainind);
  void computeRHS(Layer *fstsoill, int topind, int drainind);

  Layer * drainl; //bottom active layer
  double z_watertab; //water table depth in mm

  //Note that the Richards code uses arrays whose indices follow the 1-based indexing
  //of soil layers. That is, element zero of these arrays will not be used. An extra
  //element is added to the length of the arrays (MAX_SOI_LAY+1) to allow for this empty
  //placeholder. Element 1 will generally represent a moss layer, which are not currently
  //used in percolation and lateral drainage. Therefore, the first element of the arrays that
  //is filled will usually be element 2, corresponding to the index of the first fibric organic layer.

  //Hydraulic properties and water fluxes for calculation of percolation and lateral drainage
  double qtrans[MAX_SOI_LAY+1]; //root water uptake (incoming) (mm/s)
  double fluxNet0[MAX_SOI_LAY+1]; //column water flux based on solver solution; from CLM fortran code
  double fluxNet1[MAX_SOI_LAY+1]; //estimated column water flux based on water qin/qout/trans/evap/infil; from CLM fortran code
  double qin[MAX_SOI_LAY+1]; //water flux into soil layer (mm/s); see CLM 5 eq 7.74
  double qout[MAX_SOI_LAY+1]; //water flux out of soil layer (mm/s); see CLM 5 eq 7.75
  double s1[MAX_SOI_LAY+1]; //liquid saturation at the layer interface (unitless); from CLM fortran code
  double s2[MAX_SOI_LAY+1]; //liquid saturation at the layer node (unitless); from CLM fortran code
  double imped[MAX_SOI_LAY+1]; // ice impedance (unitless); see CLM 5 eq 7.48
  double hk[MAX_SOI_LAY+1]; //hydraulic conductivity (mm/s); see CLM 5 eq 7.47
  double dhkdw[MAX_SOI_LAY+1]; //d(hk)/d(vol_liq); see CLM 5 eqs 7.83-7.84
  double dsmpdw[MAX_SOI_LAY+1]; //d(smp)/d(vol_liq); see CLM 5 eqs 7.80-7.82
  double smp[MAX_SOI_LAY+1]; //soil matric potential (mm); see CLM 5 eq 7.53
  double dqidw0[MAX_SOI_LAY+1]; //d(qin)/d(vol_liq(i-1)); see CLM 5 eq 7.76
  double dqidw1[MAX_SOI_LAY+1]; //d(qin)/d(vol_liq(i)); see CLM 5 eq 7.77
  double dqodw1[MAX_SOI_LAY+1]; //d(qout)/d(vol_liq(i)); see CLM 5 eq 7.78
  double dqodw2[MAX_SOI_LAY+1]; //d(qout)/d(vol_liq(i+1)); see CLM 5 eq 7.79

  //Incoming layer property values copied to arrays for convenience.
  double Bsw[MAX_SOI_LAY+1]; //bsw hornberger constant (unitless) (by horizon type)
  double ksat[MAX_SOI_LAY+1]; //saturated hydraulic conductivity (mm/s) (by horizon type)
  double psisat[MAX_SOI_LAY+1]; //saturated soil matric potential (mm/s) (by horizon type)

  //Physical values calculated and/or collected to arrays for convenience
  double vol_liq[MAX_SOI_LAY+1];//volumetric liquid water (mm3 liquid water/mm3 soil)
  double vol_ice[MAX_SOI_LAY+1];//volumetric ice (mm3 ice/mm3 soil)
  double vol_h2o[MAX_SOI_LAY+1]; //total volumetric water (mm3 liq + mm3 ice)/mm3 soil)
  double vol_poro[MAX_SOI_LAY+1]; //total layer porosity
  double liq_poro[MAX_SOI_LAY+1]; //porosity available to be filled by liquid (vol_poro - vol_ice)
  double soi_liq[MAX_SOI_LAY+1]; //layer liquid water (kg/m2 or mm)
  double ice_frac[MAX_SOI_LAY+1]; //fraction of porosity filled by ice (vol_ice/vol_poro)
  double effminliq[MAX_SOI_LAY+1]; //minimum layer liquid adjusted for frozen layer fraction (kg m-2 or mm)
  double effmaxliq[MAX_SOI_LAY+1]; //maximum layer liquid adjusted for frozen layer fraction (kg m-2 or mm)
  double z_h[MAX_SOI_LAY+1]; //depth of layer bottom interface in mm; see CLM 5 Figure 7.2
  double dzmm[MAX_SOI_LAY+1]; // layer thickness in mm
  double nodemm[MAX_SOI_LAY+1]; //depth of center of layer in mm; CLM 5 Figure 7.2 'z(i)'

  //Arrays related to iteration and the tridiagonal matrix solution for richards percolation
  double deltathetaliq[MAX_SOI_LAY+1]; //Results from tridiagonal calculation
  double amx[MAX_SOI_LAY+1]; //left off-diagonal of tridiagonal matrix for richards solution
  double bmx[MAX_SOI_LAY+1]; //diagonal of tridiagonal matrix input for richards solution
  double cmx[MAX_SOI_LAY+1]; //right off-diagonal of tridiagonal matrix input for richards solution
  double rmx[MAX_SOI_LAY+1]; //forcing term of input for tridiagonal richards solution
  double dt_dz[MAX_SOI_LAY+1]; //temporary time/thickness variable used in iteration
  double tridiag_error[MAX_SOI_LAY+1]; //layer-wise error in tridiagonal solver solution per iteration; from CLM 5 eq 7.98

  //Values related to iteration and the tridiagonal matrix solution for richards percolation
  double max_tridiag_error; //maximum layer-wise error in tridiagonal solver solution per iteration
  double delta_t; //(seconds) total time to be completed during iteration (one day)
  double dtmin;  // minimum timestep length (seconds). Shorter values may be more accurate but take longer for total iteration.
  double toler_upper;  // Tolerance to halve length of substep
  double toler_lower;  // Tolerance to double length of substep

};

#endif /*RICHARDS_H_*/
