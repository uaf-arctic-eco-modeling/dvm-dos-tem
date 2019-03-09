#include "../include/Richards.h"

#include "../include/TEMLogger.h"
extern src::severity_logger< severity_level > glg;
#include "lapacke/lapacke.h"

Richards::Richards() {
  delta_t = SEC_IN_DAY;//Total time to incorporate; set to SEC_IN_DAY for no iteration
  dtmin = 10; //min timestep (sec); set to SEC_IN_DAY for no iteration
  toler_upper = 1.e-1;
  toler_lower = 1.e-2;
  e_ice = 6; //Ice impedance parameter. CLM5 uses 6, Lundin (1990) suggests 1.4 for loamy soils. Lower valus increase water flow.
};

Richards::~Richards() {
};
void Richards::update(Layer *fstsoill, Layer* bdrainl,
                      const double & bdraindepth, const double & fbaseflow,
                      const double & watertab,
                      double trans[], const double & evap,
                      const double & infil, const double & cell_slope) {

  //all fluxes already in mm/sec as input
  qinfil = infil;
  qevap  = evap;
  qdrain = 0.;

  if (bdraindepth <= fstsoill->z) {// no percolation
    if(qinfil > 0.0){//add infil back to ponding/qover
      qinfil *= SEC_IN_DAY;// -->mm/day
      //Add to ponding TODO replace hardcoded 10.0mm with puddle_max_mm from soil env
      double space_in_puddle = 10.0 - ed.d_soi2l.magic_puddle;
      double add_to_puddle = fmin(space_in_puddle, qinfil);
      ed.d_soi2l.magic_puddle += add_to_puddle;
      qinfil -= add_to_puddle;
      ed.d_soi2l.qover += infil;
      ed.d_soi2l.qinfl = 0;
    }
    return;
  }
  drainl = bdrainl;
  z_watertab = watertab * 1.e3;

  //Be sure we're skipping moss
  Layer* currl=fstsoill;
  while (currl != NULL && currl->isMoss) {
    currl = currl->nextl;
  }
  fstsoill = currl;
  int topind = fstsoill->solind;
  int drainind = drainl->solind;


  //Clear arrays before use
  clearRichardsArrays();

  //Prepare soil column parameter arrays
  prepareSoilColumn(fstsoill, drainind);

  //Re-index trans to match the other arrays used in Richards
  for(int il=topind; il<MAX_SOI_LAY; il++){
    qtrans[il] = trans[il-topind];
  }
  //For testing: turn off trans and infil
  //for(int il=topind; il<MAX_SOI_LAY; il++){
  //  qtrans[il] = 0.0;
  //}
  //qinfil = 0.0;

  double n_substep = 0;
  double dtsub = delta_t/24; //length of first substep (s)
  double dtdone = 0.0; //time completed
  bool continue_iterate = true;
  bool lapack_solver = true; //whether to use the newer LAPACK solver or the old Thomas algorithm

  //Start of adaptive-length iteration substeps
  //For testing: track the smallest substep used:
  double min_dtsub = delta_t;
  while(continue_iterate = true){
    n_substep += 1;

    //(Re)calculate dt_dz and vol_liq
    for(int ind = topind; ind <=drainind+1; ind++){
      dt_dz[ind] = dtsub / dzmm[ind];
      vol_liq[ind] = fmax(soi_liq[ind], 1.e-6) / (DENLIQ*(dzmm[ind]/1.e3));
      vol_h2o[ind] = fmax(fmin(vol_liq[ind] + vol_ice[ind], 1.0), 0.0);
    }

    computeHydraulicProperties(fstsoill, drainind);

    computeMoistureFluxesAndDerivs(fstsoill, topind, drainind);

    //dtsub trial loop - find the best length for this dtsub substep
    bool try_dtsub = true;

    while(try_dtsub){

      computeLHS(fstsoill, topind, drainind); //compute left hand side of tridiagonal matrix equation
      computeRHS(fstsoill, topind, drainind); //compute right hand side of the tridiagonal matrix equation

      if(lapack_solver && num_al >= 2){ //use the LAPACK solver

        double sub_diagonal[num_al-1];
        double diagonal[num_al];
        double super_diagonal[num_al-1];
        double result[num_al];

        for(int ii=0; ii<num_al; ii++){
          diagonal[ii] = bmx[ii+topind];
          result[ii] = rmx[ii+topind];
        }
        for(int ii=0; ii<num_al-1; ii++){
          sub_diagonal[ii] = amx[ii+topind+1];//amx n/a for top active layer
          super_diagonal[ii] = cmx[ii+topind];//cmx n/a for bottom active layer
        }
        lapack_int ldb, num_layers, nrhs;
        ldb = 1;
        num_layers = num_al;
        nrhs = 1;
        LAPACKE_dgtsv(LAPACK_ROW_MAJOR, num_layers, nrhs, sub_diagonal, diagonal, super_diagonal, result, ldb);
        //copy values from result into deltathetaliq
        for(int ii=0; ii<num_al; ii++){
          deltathetaliq[ii+topind] = result[ii];
        }
      }
      else{ //use the old Thomas algorithm as solver
        cn.tridiagonal(topind, num_al, amx, bmx, cmx, rmx, deltathetaliq);
      }

      max_tridiag_error = 0.0;
      for(int ind = topind; ind <=drainind; ind++){
        fluxNet0[ind] = deltathetaliq[ind]/dt_dz[ind];
        fluxNet1[ind] = qin[ind] - qout[ind] - qtrans[ind];
        tridiag_error[ind] = fabs(fluxNet1[ind] - fluxNet0[ind]) * dtsub * 0.5;
        max_tridiag_error = fmax(max_tridiag_error, tridiag_error[ind]);
      }
      if(max_tridiag_error > toler_upper && dtsub > dtmin){
        dtsub = fmax(dtsub/2, dtmin);//solution no good, halve timestep and start again
      }
      else{try_dtsub = false;}
    } //end of trial timestep

    //Modify layer liquid in each active layer by calculated
    //change in liquid.
    currl = fstsoill;

    while(currl != NULL && currl->solind<=drainind){
      int ind = currl->solind;
      //TODO - verify
      double liquid_change = dzmm[ind] * deltathetaliq[ind];
      currl->liq += liquid_change;
      percolation[ind] += liquid_change;

      //update soi_liq so that vol_liq can be recalculated for
      // lateral drainage (below) and next iteration (above)
      soi_liq[ind] = fmax(0.0001, currl->liq);

      currl = currl->nextl;
    }

    dtdone += dtsub;

    //For testing: track smallest dtsub used:
    min_dtsub = fmin(min_dtsub, dtsub);

    if(fabs(delta_t - dtdone) < 1.e-8){
      continue_iterate = false;
      break; //day complete
    }

    if(max_tridiag_error < toler_lower){
      dtsub *= 2; //If the solution was very accurate, double the substep
    }
    dtsub = fmin(dtsub, delta_t - dtdone); //don't go over delta_t
  } //End of substep loop
  //End of iteration domain

  //Update layer volumetric water post percolation so lateral drainage is
  // based on today's values
  //Note that soi_liq is updated above (post layer
  // water modification).
  for(int ind=topind; ind<=drainind+1; ind++){
    if(dzmm[ind]>0){
      vol_liq[ind] = soi_liq[ind] / (DENLIQ*(dzmm[ind]/1.e3));
      vol_h2o[ind] = fmax(fmin(vol_liq[ind] + vol_ice[ind], 1.0), 0.0);
    }
  }

  //Calculating lateral drainage (only for saturated layers)
  //CLM 5 eq 7.103
  double eq7103_num = 0.0;
  double eq7103_den = 0.0;
  bool sat_soil = false;//If there is at least one saturated layer

  for(int ind=topind; ind<=drainind; ind++){
    //For any saturated layer
    if(vol_liq[ind] / liq_poro[ind] >= 0.9){
      sat_soil = true;

      //originally eq7103_num is multiplied by impedance as well;
      //removed to achieve sufficient drainage
      eq7103_num += ksat[ind] * dzmm[ind]/1.e3;
      eq7103_den += dzmm[ind]/1.e3;
    }
  }

  //If there is at least one saturated layer, apply lateral drainage
  if(sat_soil){
    //CLM5 Equations 7.103 and 7.102
    double slope_rads = cell_slope * PI / 180;//Converting to radians
    double kdrain_perch = 10.e0* sin(slope_rads) //original factor 10e-5; to be adjusted per S.Swenson
                        * (eq7103_num / eq7103_den);
    double qdrain_perch = kdrain_perch * (bdraindepth - watertab)
                        * fbaseflow;
    if(qdrain_perch < 0.0){
      BOOST_LOG_SEV(glg, err) << "qdrain_perch is negative";
    }

    //Calculate drainage from saturated layers
    currl = fstsoill;
    while(currl != NULL && currl->solind <= drainind){
      int ind = currl->solind;
      if(vol_liq[ind] / liq_poro[ind] >= 0.9){
        double layer_max_drain = currl->liq - effminliq[ind];
        double layer_calc_drain = qdrain_perch * SEC_IN_DAY
                                * ((dzmm[ind]/1.e3) / eq7103_den);
        layer_drain[ind] = fmin(layer_max_drain, layer_calc_drain);
        qdrain += layer_drain[ind]; //mm/day
      }
      currl = currl->nextl;
    }
    //Drainage is calculated from saturated layers (usually bottom layers);
    //however, to avoid creating isolated unsaturated deep layers,
    //remove the calculated drainage from the top down.
    if(qdrain > 0){
      double to_drain = qdrain;
      currl = fstsoill;
      while(currl != NULL && currl->solind <= drainind && to_drain > 0){
        int ind = currl->solind;
        double avail_liq = currl->liq - effminliq[ind];
        double take_liq = fmin(to_drain, avail_liq);
        currl->liq -= take_liq;
        to_drain -= take_liq;

        currl = currl->nextl;
      }
    }
  }
};

//This collects already-known values into arrays for ease of use, and
// calculates basic values needed in the more complex equations later
void Richards::prepareSoilColumn(Layer* fstsoill, int drainind) {

  Layer* currl = fstsoill; // the first soil layer is 'fstsoill'
  num_al = 0; // number of active layers

  while(currl != NULL && currl->solind <= drainind+1){
    int ind = currl->solind;

    soi_liq[ind] = fmax(0.0001, currl->liq);
    vol_liq[ind] = fmax(soi_liq[ind], 1.e-6) / (currl->dz * DENLIQ);
    vol_ice[ind] = currl->ice/(DENICE*currl->dz);
    vol_h2o[ind] = fmax(fmin(vol_liq[ind] + vol_ice[ind], 1.0), 0.0);
    vol_poro[ind] = fmax(0., currl->poro);
    liq_poro[ind] = fmax(0., vol_poro[ind] - vol_ice[ind]);
    ice_frac[ind] = vol_ice[ind]/vol_poro[ind];
    dzmm[ind] = currl->dz*1.e3;
    z_h[ind] = (currl->z + currl->dz)*1.e3;
    nodemm[ind] = (currl->z + 0.5 * currl->dz)*1.e3;
    double frac_unfrozen = 1.0 - currl->frozenfrac;
    effminliq[ind] = currl->minliq * frac_unfrozen;
    effmaxliq[ind] = currl->maxliq * frac_unfrozen;

    psisat[ind] = -currl->psisat; //made negative to match CLM5 code
    ksat[ind] = currl->hksat;
    Bsw[ind] = currl->bsw;
    if(currl->frozen <=0){
      num_al += 1;
    }
    currl= currl->nextl;
  }
}

void Richards::computeHydraulicProperties(Layer *fstsoill, int drainind){
  // compute the relative saturation at each layer first b/c
  // it is used later in calculation of s1
  Layer *currl = fstsoill;
  while(currl != NULL && currl->solind <=drainind+1){
    int ind = currl->solind;
    s2[ind] = vol_liq[ind]/liq_poro[ind];
    // impose constraints on relative saturation at the layer node
    s2[ind] = fmin(s2[ind], 1.0);
    s2[ind] = fmax(0.01, s2[ind]);

    currl = currl->nextl;
  }
  currl = fstsoill;
  while(currl != NULL && currl->solind <=drainind+1){
    int ind = currl->solind;
    // s1 is interface value, s2 is node value
    if(ind > drainind){
      s1[ind] = s2[ind];
      imped[ind] = pow(10.0, -e_ice * ice_frac[ind]);
    }
    else{
      s1[ind] = 0.5 * (s2[ind] + s2[ind+1]);
      imped[ind] = pow(10.0, -e_ice * (0.5 * (ice_frac[ind] + ice_frac[ind+1])));
    }
    s1[ind] = fmin(s1[ind], 1.0);
    s1[ind] = fmax(0.01, s1[ind]);

    hk[ind] = imped[ind] * ksat[ind] * pow(s1[ind], 2.0 * Bsw[ind] + 3);
    dhkdw[ind] = (2.0* Bsw[ind] + 3.0) * hk[ind] / s1[ind];
    smp[ind] = -psisat[ind] * pow(s2[ind], -Bsw[ind]);
    dsmpdw[ind] = (-Bsw[ind] * smp[ind] / s2[ind]) / liq_poro[ind];

    currl = currl->nextl;
  }
}

void Richards::computeMoistureFluxesAndDerivs(Layer *fstsoill, int topind, int drainind){
  Layer *currl = fstsoill;
  //top and inner layers (not bottom)
  while(currl!= NULL && currl->solind <=drainind){
    int ind = currl->solind;
    if(ind == topind){//top layer
      qin[ind] = qinfil;
      dqidw1[ind] = 0.0;
      double dhkds1 = 0.5 * dhkdw[ind] / liq_poro[ind]; // derivative w.r.t. volumetric liquid water in the upper layer
      double dhkds2 = 0.5 * dhkdw[ind] / liq_poro[ind+1]; // derivative w.r.t. volumetric liquid water in the lower layer
      double num = (smp[ind+1] - smp[ind]);
      double den = nodemm[ind+1] - nodemm[ind];
      if(ind == drainind){ //if this is the single active layer
        qout[ind] = 0.0;
        dqodw1[ind] = 0.0;
      }
      else{ //top layer and not the only active layer
        qout[ind] = -hk[ind] * num / den + hk[ind];
        dqodw1[ind] = (hk[ind] * dsmpdw[ind] - dhkds1 * num) / den + dhkds1;
        dqodw2[ind] = (-hk[ind] * dsmpdw[ind+1] - dhkds2 * num) / den + dhkds2;
      }
    }
    else{ //inner and bottom layers
      qin[ind] = qout[ind-1];
      dqidw0[ind] = dqodw1[ind-1];
      dqidw1[ind] = dqodw2[ind-1];
      double dhkds1 = 0.5 * dhkdw[ind] / liq_poro[ind]; // derivative w.r.t. volumetric liquid water in the upper layer
      double dhkds2 = 0.5 * dhkdw[ind] / liq_poro[ind+1]; // derivative w.r.t. volumetric liquid water in the lower layer
      double num = (smp[ind+1] - smp[ind]);
      double den = nodemm[ind+1] - nodemm[ind];
      if(ind == drainind){ //bottom layer
        qout[ind] = 0.0;
        dqodw1[ind] = 0.0;
      }
      else{ //inner layers
        qout[ind] = -hk[ind] * num / den + hk[ind];
        dqodw1[ind] = (hk[ind] * dsmpdw[ind] - dhkds1 * num) / den + dhkds1;
        dqodw2[ind] = (-hk[ind] * dsmpdw[ind+1] - dhkds2 * num) / den + dhkds2;
      }
    }
    currl = currl->nextl;
  }
}

void Richards::computeLHS(Layer *fstsoill, int topind, int drainind){
  Layer *currl = fstsoill;
  while(currl!= NULL && currl->solind <=drainind){
    int ind = currl->solind;
    if(ind == topind){
      //a coefficient top layer only
      amx[ind] = 0.0;
    }
    else{
      //a coefficient middle and bottom layers
      amx[ind] = dqidw0[ind] * dt_dz[ind];
    }
    //b coefficient all layers
    bmx[ind] = -1.0 - (-dqidw1[ind] + dqodw1[ind]) * dt_dz[ind];
    if(ind == drainind){
      //c coefficient bottom layer
      cmx[ind] = 0.0;
    }
    else{
      //c coefficient top and middle layers
      cmx[ind] = -dqodw2[ind] * dt_dz[ind];
    }
    currl = currl->nextl;
  }
}

void Richards::computeRHS(Layer *fstsoill, int topind, int drainind){
  double fluxNet = 0.0;
  Layer *currl = fstsoill;
  while(currl != NULL && currl->solind<=drainind){
    int ind = currl->solind;
    if (ind == topind){
      fluxNet = qinfil - qout[ind] - (qtrans[ind] + qevap);
    }
    else{
      fluxNet = qin[ind] - qout[ind] - qtrans[ind];
    }
    rmx[ind] = -fluxNet*dt_dz[ind];

    currl = currl->nextl;
  }
}


void Richards::clearRichardsArrays(){
  for(int ii=0; ii<=MAX_SOI_LAY; ii++){

    qtrans[ii] = 0.0;
    tridiag_error[ii] = 0.0;
    fluxNet0[ii] = 0.0;
    fluxNet1[ii] = 0.0;
    qin[ii] = 0.0;
    qout[ii] = 0.0;
    s1[ii] = 0.0;
    s2[ii] = 0.0;
    imped[ii] = 0.0;
    hk[ii] = 0.0;
    dhkdw[ii] = 0.0;
    dsmpdw[ii] = 0.0;
    smp[ii] = 0.0;
    dqidw0[ii] = 0.0;
    dqidw1[ii] = 0.0;
    dqodw1[ii] = 0.0;
    dqodw2[ii] = 0.0;

    Bsw[ii] = 0.0; //bsw hornberger constant (by horizon type)
    ksat[ii] = 0.0; //Saturated hydraulic conductivity (by horizon type)
    psisat[ii] = 0.0;;//Saturated soil matric potential (by horizon type)

    vol_liq[ii] = 0.0;//volumetric liquid water
    vol_ice[ii] = 0.0;
    vol_h2o[ii] = 0.0; //Total volumetric water (liq + ice)
    vol_poro[ii] = 0.0; //Layer porosity
    liq_poro[ii] = 0.0; //Porosity not filled by ice (= vol_poro - vol_ice)
    soi_liq[ii] = 0.0; //Layer liquid
    ice_frac[ii] = 0.0; //Fraction of porosity filled with ice
    effminliq[ii] = 0.0;
    effmaxliq[ii] = 0.0;
    z_h[ii] = 0.0; //Depth of layer bottom in mm, named to match CLM paper
    dzmm[ii] = 0.0; // layer thickness in mm
    nodemm[ii] = 0.0; //depth of center of layer thawed portion in mm
    dt_dz[ii] = 0.0;

    deltathetaliq[ii] = 0.0;
    amx[ii] = 0.0;
    bmx[ii] = 0.0;
    cmx[ii] = 0.0;
    rmx[ii] = 0.0;

    percolation[ii] = 0.0;
    layer_drain[ii] = 0.0;

  }
};

