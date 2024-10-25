/*
 * \file
 * defines struct for fluxes between atmosphere, vegetation, land(snow and soil)
 */
#ifndef FLUXES_H_
#define FLUXES_H_

#include <limits>

#include "cohortconst.h"
#include "layerconst.h"
#include "errorcode.h"

// for water
struct lnd2atm_env {
  double eet;
  double pet;
  lnd2atm_env() : eet(UIN_D), pet(UIN_D) {}
};

struct lnd2atm_bgc {
  double nep;
  lnd2atm_bgc() : nep(UIN_D) {}
};

struct atm2lnd_env { //NOTE: land includes both veg and ground
  // water
  double prec;  // mm
  double snfl;  // mm
  double rnfl;  // mm
  // energy
  double nirr;  //  W/m2
  double par;   //  W/m2
  
  atm2lnd_env() : prec(UIN_D), snfl(UIN_D), rnfl(UIN_D), nirr(UIN_D), par(UIN_D)
  {}

};

struct atm2veg_env {
  // water
  double rnfl;
  double snfl;

  double rinter;
  double sinter;

  // radiation
  double swdown; // non-reflected (short-wave) solar radiation: W/m2
  double swinter; // intercepted (short-wave) solar radiation: W/m2
  double pardown; // non-reflected PAR: W/m2
  double parabsorb; // absorbed PAR: W/m2

  atm2veg_env() : rnfl(UIN_D), snfl(UIN_D), rinter(UIN_D), sinter(UIN_D),
                  swdown(UIN_D), swinter(UIN_D),pardown(UIN_D),
                  parabsorb(UIN_D) {}
  
};

struct atm2veg_bgc {
  // carbon
  double ingppall; // gpp not limited by nitrogen availability
  double ingpp[NUM_PFT_PART];

  double gppall;
  double gpp[NUM_PFT_PART];

  double innppall;
  double innpp[NUM_PFT_PART];

  double nppall;
  double npp[NUM_PFT_PART];

  atm2veg_bgc() : ingppall(UIN_D),gppall(UIN_D),innppall(UIN_D),nppall(UIN_D) {
    for (int i = 0; i < NUM_PFT_PART; ++i) {
      ingpp[i] = UIN_D;
      gpp[i]   = UIN_D;
      innpp[i] = UIN_D;
      npp[i]   = UIN_D;
    }
  }
};

struct veg2atm_env {
  //water
  double tran; // mm/day
  double evap; // mm/day
  double tran_pet; // mm/day
  double evap_pet; // mm/day

  double sublim; // mm/day

  //energy
  double swrefl; // W/m2: reflected solar radiation

  veg2atm_env() : tran(UIN_D), evap(UIN_D), tran_pet(UIN_D), evap_pet(std::numeric_limits<double>::signaling_NaN()),
                  sublim(UIN_D), swrefl(UIN_D) {}
  
};

struct veg2atm_bgc {
  //carbon
  double rmall;// maintainance respiration
  double rm[NUM_PFT_PART];

  double rgall; // growth respiration;
  double rg[NUM_PFT_PART];

  veg2atm_bgc() : rmall(UIN_D), rgall(UIN_D) {
    for (int i = 0; i < NUM_PFT_PART; ++i) {
      rm[i] = UIN_D;
      rg[i] = UIN_D;
    }
  }

};

struct veg2gnd_env {
  // water
  double rthfl; // rain throughfall
  double sthfl; // snow throughfall
  double rdrip; // rain drip
  double sdrip; // snow drip

  // radiation throught fall
  double swthfl;// shortwave W/m2
  
  veg2gnd_env() : rthfl(UIN_D), sthfl(UIN_D), rdrip(UIN_D),
                 sdrip(UIN_D), swthfl(UIN_D) {}

};

struct veg2soi_bgc {
  //
  double rtlfalfrac[MAX_SOI_LAY]; //root mortality vertical distribution

  // carbon
  double d2wdebrisc; // dead standing C to ground debris
  double ltrfalcall; //excluding moss/lichen mortality
  double mossdeathc; // moss/lichen mortality
  double ltrfalc[NUM_PFT_PART];

  // nitrogen
  double d2wdebrisn; // dead standing N to ground debris
  double ltrfalnall; //excluding moss/lichen mortality
  double mossdeathn; // moss/lichen mortality
  double ltrfaln[NUM_PFT_PART];

  veg2soi_bgc() : d2wdebrisc(UIN_D), ltrfalcall(UIN_D), mossdeathc(UIN_D),
                 d2wdebrisn(UIN_D), ltrfalnall(UIN_D), mossdeathn(UIN_D) {
  
    for (int i = 0; i < MAX_SOI_LAY; ++i) {
      rtlfalfrac[i] = UIN_D;
    }
    for (int i = 0; i < NUM_PFT_PART; ++i) {
      ltrfalc[i] = UIN_D;
      ltrfaln[i] = UIN_D;
    }
  }

};

struct soi2veg_bgc {
  // nitrogen

  double innuptake;
  double lnuptake;
  double snuptakeall;
  double snuptake[NUM_PFT_PART];

  double nextract[MAX_SOI_LAY]; //all root N extraction from each soil layer

  soi2veg_bgc() : innuptake(UIN_D), lnuptake(UIN_D), snuptakeall(UIN_D) {
    for (int i = 0; i < NUM_PFT_PART; ++i) {
      snuptake[i] = UIN_D;
    }
    for (int i = 0; i < MAX_SOI_LAY; ++i) {
      nextract[i] = UIN_D;
    }
  }

};

struct veg2veg_bgc {
  //nitrogen
  double nmobilall; //N allocation from labile-N pool to tissue pool when needed
  double nmobil[NUM_PFT_PART];

  double nresorball; //N resorbation into labile-N pool when litter-falling
  double nresorb[NUM_PFT_PART];

  veg2veg_bgc() : nmobilall(UIN_D), nresorball(UIN_D) {
    for (int i = 0 ; i < NUM_PFT_PART; ++i) {
      nmobil[i] = UIN_D;
      nresorb[i] = UIN_D;
    }
  }

};

struct soi2lnd_env {
  double qinfl; // infiltration water
  double qover;
  double qdrain;
  double layer_drain[MAX_SOI_LAY];
  double magic_puddle;//This is an artificial construct to prevent
                      // losing too much water to runoff.
  soi2lnd_env(): qinfl(UIN_D), qover(UIN_D), qdrain(UIN_D),
                 magic_puddle(UIN_D) {
    for(int il=0; il<MAX_SOI_LAY; il++){
      layer_drain[il] = UIN_D;
    }
  }
};

struct soi2lnd_bgc {
  double doclost; //DOC lost

  // nitrogen
  double avlnlost; // N leaching
  double orgnlost; // N loss with DOC

  soi2lnd_bgc(): doclost(UIN_D), avlnlost(UIN_D), orgnlost(UIN_D) {}
};


struct soi2atm_env {
  double evap;
  double evap_pet;
  double swrefl;
  soi2atm_env(): evap(UIN_D), evap_pet(std::numeric_limits<double>::signaling_NaN()), swrefl(UIN_D) {}
};

struct soi2atm_bgc {
  double rhwdeb; //rh from wood debris

  double rhrawc[MAX_SOI_LAY];
  double rhsoma[MAX_SOI_LAY];
  double rhsompr[MAX_SOI_LAY];
  double rhsomcr[MAX_SOI_LAY];

  double rhrawcsum;
  double rhsomasum;
  double rhsomprsum;
  double rhsomcrsum;

  double rhsom;  //RH for soil organic matter
  
  soi2atm_bgc(): rhwdeb(UIN_D), rhrawcsum(UIN_D),
                 rhsomasum(UIN_D), rhsomprsum(UIN_D), rhsomcrsum(UIN_D) {

    for (int i = 0; i < MAX_SOI_LAY; ++i) {
      rhrawc[i] = UIN_D;
      rhsoma[i] = UIN_D;
      rhsompr[i] = UIN_D;
      rhsomcr[i] = UIN_D;
    }
  }
  
};

struct snw2atm_env {
  double sublim;
  double swrefl;
  snw2atm_env(): sublim(UIN_D), swrefl(UIN_D){}
};

struct snw2soi_env {
  double melt;
  snw2soi_env(): melt(UIN_D){}
};

struct atm2soi_bgc {
  double orgcinput;
  double orgninput;
  double avlninput;
  atm2soi_bgc(): orgcinput(UIN_D), orgninput(UIN_D), avlninput(UIN_D) {}
};

struct soi2soi_bgc {
  double netnminsum;
  double nimmobsum;

  double netnmin[MAX_SOI_LAY];
  double nimmob[MAX_SOI_LAY];
  
  soi2soi_bgc() : netnminsum(UIN_D), nimmobsum(UIN_D) {
    for (int i = 0; i < MAX_SOI_LAY; ++i) {
      netnmin[i] = UIN_D;
      nimmob[i] = UIN_D;
    }
  }
  
};

struct atm2soi_fir {
  double orgn;
  atm2soi_fir(): orgn(UIN_D){}
};

struct soi2atm_fir {
  double orgc;
  double orgn;
  soi2atm_fir(): orgc(UIN_D), orgn(UIN_D) {}
};

struct veg2atm_fir {
  double orgc;
  double orgn;
  veg2atm_fir(): orgc(UIN_D), orgn(UIN_D) {}
};

struct veg2soi_fir {
  double abvc;
  double abvn;
  double blwc;
  double blwn;
  veg2soi_fir(): abvc(UIN_D), abvn(UIN_D), blwc(UIN_D), blwn(UIN_D) {}

};

struct veg2dead_fir{
  double vegC;
  double strN;
  veg2dead_fir(): vegC(UIN_D), strN(UIN_D) {}
};

#endif /*FLUXES_H_*/

