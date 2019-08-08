/*
 * \file
 * defines struct for diagnostic variables between atmosphere, vegetation,
 * land(snow and soil)
 */
#ifndef DIAGNOSTICS_H_
#define DIAGNOSTICS_H_

#include "errorcode.h"
#include "cohortconst.h"
#include "layerconst.h"

// Diagnostic Variables
struct atmdiag_env {
  double vpd; // vapor pressure deficit (Pa)
  double vp; // vapor pressure (Pa)
  double svp; // saturated vapor pressure (Pa)
  atmdiag_env(): vpd(UIN_D), vp(UIN_D), svp(UIN_D) {}
};

struct vegdiag_dim {
  double fpcsum; // sum of fpc[] (must not be greater than 1.0)

  // phenoloy variables
  double growingttime[NUM_PFT]; // (current but accumulated) growing thermal time
  double maxleafc[NUM_PFT]; // max. leaf C limited by plant state itself

  double fleaf[NUM_PFT]; //(current) normalized (scalar) foliage growth
                         //  index based on current and previous EET
  double unnormleaf[NUM_PFT]; // (current) un-normarlized fleaf
  double eetmx[NUM_PFT]; // (yearly) max. month eet
  double unnormleafmx[NUM_PFT]; // (yearly max.) un-normarlized fleaf
  double topt[NUM_PFT]; //(yearly) evolving optimium temperature for
                        //  temperature-scalar of GPP

  double ffoliage[NUM_PFT]; //(current)foliage growth index (scalar) based
                            //  on vegetation C (stand age related)
  double foliagemx[NUM_PFT]; //this is for 'ffoliage' not growing backward

  vegdiag_dim(): fpcsum(UIN_D) {
    for (int i = 0; i < NUM_PFT; ++i) {
      growingttime[i] = UIN_D;
      maxleafc[i] = UIN_D;
      fleaf[i] = UIN_D;
      unnormleaf[i] = UIN_D;
      eetmx[i] = UIN_D;
      unnormleafmx[i] = UIN_D;
      topt[i] = UIN_D;
      ffoliage[i] = UIN_D;
      foliagemx[i] = UIN_D;
    }
  }
};

struct vegdiag_env {
  double btran;

  double rc;         // canopy resistance s/m
  double cc;         // canopy conductance m/s

  double m_ppfd;     //
  double m_vpd;

  vegdiag_env(): btran(UIN_D), rc(UIN_D), cc(UIN_D), m_ppfd(UIN_D), m_vpd(UIN_D)
  {}

};

struct vegdiag_bgc {

  double raq10;
  double ftemp; /*! temperature factor for gpp*/
  double gv;

  double kr[NUM_PFT_PART]; //maintainence resp: is related to kra, krb,
                           //  and vegetation carbon  pool
  double fna; // effect of nitrogen availability on gpp
  double fca; // effect of carbon availability on nuptake

  vegdiag_bgc(): raq10(UIN_D), ftemp(UIN_D), gv(UIN_D), fna(UIN_D), fca(UIN_D) {
    for (int i = 0; i < NUM_PFT_PART; ++i) {
      kr[i] = UIN_D;
    }
  }
};

struct snwdiag_env {
  int snowfreeFst;       //used for estimating growing season
  int snowfreeLst;       //used for estimating growing season
  double tcond[MAX_SNW_LAY];

  double fcmelt;         /*! melting factor */

  snwdiag_env(): snowfreeFst(UIN_D), snowfreeLst(UIN_D), fcmelt(UIN_D) {
    for (int i = 0; i < MAX_SNW_LAY; ++i) {
      tcond[i] = UIN_D;
    }
  }

};

struct soidiag_env {

  int permafrost;
  double unfrzcolumn; // unfrozen soil column length (m)
  double alc; //active layer cap (m), i.e. the top of active layer -
              //  seasonal frezing front
  double ald; //active layer depth (m), i.e., the bottom of active layer -
              //  seasonal or permafrost

  //variables used for estimating growing season and growth timing
  double rtdpts; //soil temperature over the active root zone depth 'rtdp4gdd'
  double rtdpthawpct; //soil thawing period percentage over 'rtdp4gdd'
  double rtdpgdd; //growing degree-days over 'rtdep4gdd'
  int rtdpgrowstart; //growing starting DOY based on soil thawing over
                     //  'rtdep4gdd'
  int rtdpgrowend; //growing ending DOY based on soil freezing over 'rtdep4gdd'
  //The previous two variables will only contain values when the other
  //  does not. 
  //The following two variables hold the growstart and growend DOYs
  //  for output at the end of the year.
  int rtdpGSoutput;
  int rtdpGEoutput;

  double nfactor;

  double vwc[MAX_SOI_LAY]; //Yuan: soil water content: volume fraction of
                           //  all water/total soil volume (Theta)
  double iwc[MAX_SOI_LAY]; //Yuan: ice water content: volume fraction of
                           //  ice water/total soil volume (Theta)
  double lwc[MAX_SOI_LAY]; //Yuan: liquid water content: volume fraction of
                           //  liquid water/total soil volume (Theta)
  double sws[MAX_SOI_LAY]; //soil liquid water saturation (liq vwc/
                           //  total porosity) for use in Soil_Bgc
  double aws[MAX_SOI_LAY]; //adjusted soil liquid water saturation (liq vwc/
                           //  (porosity-ice vwc)) for use in Soil_Bgc

  double minliq[MAX_SOI_LAY];
  double tcond[MAX_SOI_LAY];
  double hcond[MAX_SOI_LAY];

  double r_e_i[MAX_SOI_LAY]; //Effective root fraction per layer
  //Effective root fraction per layer, per PFT
  // This array only has meaning in Soil_Env::getSoilTransFactor(),
  // which is called by PFT TODO - clarify commenting
  double r_e_ij[MAX_SOI_LAY];
  double fbtran[MAX_SOI_LAY]; //fraction of root water uptake (transpiration)
                              //  in each soil layer (total 1.0)

  //Variables used for or resulting from CH4 flux calculation
  double ch4flux;
  double dfratio;
  double co2ch4;
  double oxid;

  // variables of summarized over soil horizons
  double tsave;    // all soil profile
  double tshlw;
  double tdeep;
  double tminea;
  double tmineb;
  double tminec;
  double tbotrock;
  double tcshlw;   //thermal conductivity
  double tcdeep;
  double tcminea;
  double tcmineb;
  double tcminec;

  double frasat;  // soil saturation for all layers
  double liqsum;
  double icesum;
  double vwcshlw;
  double vwcdeep;
  double vwcminea;
  double vwcmineb;
  double vwcminec;
  double hkshlw;
  double hkdeep;
  double hkminea;
  double hkmineb;
  double hkminec;

  soidiag_env():

      permafrost(UIN_I), unfrzcolumn(UIN_D), alc(UIN_D), ald(UIN_D),
      rtdpts(UIN_D), rtdpthawpct(UIN_D), rtdpgdd(UIN_D), rtdpgrowstart(UIN_I),
      rtdpgrowend(UIN_I), nfactor(UIN_D),

      ch4flux(UIN_D), dfratio(UIN_D), co2ch4(UIN_D), oxid(UIN_D),

      tsave(UIN_D), tshlw(UIN_D), tdeep(UIN_D), tminea(UIN_D), tmineb(UIN_D),
      tminec(UIN_D), tbotrock(UIN_D), tcshlw(UIN_D), tcdeep(UIN_D),
      tcminea(UIN_D), tcmineb(UIN_D), tcminec(UIN_D), frasat(UIN_D),
      liqsum(UIN_D), icesum(UIN_D), vwcshlw(UIN_D), vwcdeep(UIN_D),
      vwcminea(UIN_D), vwcmineb(UIN_D), vwcminec(UIN_D), hkshlw(UIN_D),
      hkdeep(UIN_D), hkminea(UIN_D), hkmineb(UIN_D), hkminec(UIN_D) {

    for (int i = 0; i < MAX_SOI_LAY; ++i) {
      vwc[i] = UIN_D;
      iwc[i] = UIN_D;
      lwc[i] = UIN_D;
      sws[i] = UIN_D;
      aws[i] = UIN_D;
      minliq[i] = UIN_D;
      tcond[i] = UIN_D;
      hcond[i] = UIN_D;
      fbtran[i] = UIN_D;
    }
  }
};

struct soidiag_bgc {
  double knmoist[MAX_SOI_LAY]; //soil liq water factor to be used in N
                               //  immobilization and mineralization

  double rhmoist[MAX_SOI_LAY];
  double rhq10[MAX_SOI_LAY];

  double ltrfcn[MAX_SOI_LAY]; //litterfall (root death) input C/N ratios in
                              //  each soil layer for adjusting 'kd'

  double tsomc[MAX_SOI_LAY];

  //variables of summarized over soil horizons
  double shlwc;
  double deepc;
  double mineac;
  double minebc;
  double minecc;

  double rawcsum;
  double somasum;
  double somprsum;
  double somcrsum;

  double orgnsum;
  double avlnsum;

  soidiag_bgc(): shlwc(UIN_D), deepc(UIN_D), mineac(UIN_D), minebc(UIN_D),
      minecc(UIN_D), rawcsum(UIN_D), somasum(UIN_D), somprsum(UIN_D),
      somcrsum(UIN_D), orgnsum(UIN_D), avlnsum(UIN_D) {

    for (int i = 0; i < MAX_SOI_LAY; ++i) {
      knmoist[i] = UIN_D;
      rhmoist[i] = UIN_D;
      rhq10[i] = UIN_D;
      ltrfcn[i] = UIN_D;
      tsomc[i] = UIN_D;
    }
  }

};

struct soidiag_fir {
  double burnthick;
  double rolb;
  soidiag_fir(): burnthick(UIN_D), rolb(UIN_D) {}
};

#endif /*DIAGNOSTICS_H_*/
