/*! contains parameters for veg, and soil
 */
#ifndef PARAMETERS_H_
#define PARAMETERS_H_

#include "cohortconst.h"
#include "layerconst.h"
#include "errorcode.h"

struct vegpar_cal {

  double cmax;
  double nmax;

  double cfall[NUM_PFT_PART];
  double nfall[NUM_PFT_PART];

  double kra;               // parameter for maintenance resp. (rm)
  double krb[NUM_PFT_PART]; // parameter for maintenance resp. (rm)
  double frg;               // fraction of available GPP after rm for
                            // growth respiration

  vegpar_cal(): cmax(UIN_D), nmax(UIN_D), kra(UIN_D), frg(UIN_D) {
    for (int i = 0; i < NUM_PFT_PART; ++i) {
      cfall[i] = UIN_D;
      nfall[i] = UIN_D;
      krb[i] = UIN_D;
    }
  }
};

// dimension parameters for vegetation
struct vegpar_dim {
  double sla[NUM_PFT];  // specific leaf area
  double klai[NUM_PFT]; // a coefficient to convert LAI to FPC
                        // (foliage percentage coverage)

  // the following 4 parameters are for eet adjusted leaf phenology
  // including previous eet, implied some of drought's extended effects
  // on leaf development
  double minleaf[NUM_PFT];
  double aleaf[NUM_PFT];
  double bleaf[NUM_PFT];
  double cleaf[NUM_PFT];

  // for the vegetation biomass (C) or age adjusted leaf phenology
  double kfoliage[NUM_PFT];  // these 2 parameters for non-forest
  double cov[NUM_PFT];
  double m1[NUM_PFT];        // these 4 parameters for forest
  double m2[NUM_PFT];
  double m3[NUM_PFT];
  double m4[NUM_PFT];
  
  vegpar_dim() {
    for (int i = 0; i < NUM_PFT; ++i) {
      sla[i] = UIN_D;
      klai[i] = UIN_D;
      minleaf[i] = UIN_D;
      aleaf[i] = UIN_D;
      bleaf[i] = UIN_D;
      cleaf[i] = UIN_D;
      kfoliage[i] = UIN_D;
      cov[i] = UIN_D;
      m1[i] = UIN_D;
      m2[i] = UIN_D;
      m3[i] = UIN_D;
      m4[i] = UIN_D;
    }
  }

};

struct vegpar_env {
  double albvisnir; // canopy radiation albedo for both visible and nir
  double er;        // canopy light extinction coefficient

  double ircoef;    // canopy interception coeff for rain
  double iscoef;    // canopy interception coeff for snow

  double glmax;  // maximum leaf conductance m/s
  double gl_bl;  // leaf boundary layer conductance m/s
  double gl_c;   // canopy conductance

  double vpd_open;  // vpd for starting of stomata open
  double vpd_close; // vpd for complete conductance reduction (stomata closure)
  double ppfd50;    // ppfd for half stomata closure

  vegpar_env():
      albvisnir(UIN_D), er(UIN_D), ircoef(UIN_D), iscoef(UIN_D),
      glmax(UIN_D), gl_bl(UIN_D), gl_c(UIN_D), vpd_open(UIN_D),
      vpd_close(UIN_D), ppfd50(UIN_D) {}

};

struct vegpar_bgc {

  // new production allocation (partioning)
  double cpart[NUM_PFT_PART]; //Yuan: biomass partioning

  // new production C:N ratios - determining the N requirements
  double c2neven[NUM_PFT_PART]; //C:N ratio in new production at current CO2,
                                //  and adjsted by eet/pet
  double c2na; // for vegetation C:N ratio adjustment by eet/pet
  double c2nb[NUM_PFT_PART]; // for vegetation C:N ratios adjustment by eet/pet
  double c2nmin[NUM_PFT_PART]; // min. C:N ratios
  double dc2n; // factor for changing C:N per ppmv of enhanced CO2*/

  double labncon; //max. fraction of labile-N change over total
                  //veg structural N change

  double raq10a0; // for maintenence respiration and root uptake
                  //  regulation by air temperature
  double raq10a1;
  double raq10a2;
  double raq10a3;

  double kc;        // constant for CO2 regulated GPP
  double ki;        // constant for light regulated GPP

  double tmin;      // for GPP air temperature factor
  double tmax;
  double toptmin;
  double toptmax;

  double knuptake;  // constant for N uptake equation
  
  vegpar_bgc(): c2na(UIN_D),  dc2n(UIN_D), labncon(UIN_D), raq10a0(UIN_D),
      raq10a1(UIN_D), raq10a2(UIN_D), raq10a3(UIN_D), kc(UIN_D), ki(UIN_D),
      tmin(UIN_D), tmax(UIN_D), toptmin(UIN_D), toptmax(UIN_D), knuptake(UIN_D){
    for (int i = 0; i < NUM_PFT_PART; ++i) {
      cpart[i] = UIN_D;
      c2neven[i] = UIN_D;
      c2nb[i] = UIN_D;
      c2nmin[i] = UIN_D;
    }
  }

};

struct soipar_cal {
  double micbnup;  // parameter related to N immoblization by soil microbial

  double kdcrawc; // calibrated soil raw C material respiration rate
                  // (at 0oC, favoriable soil moisture, and not
                  // litter C/N adjusted)
  double kdcsoma; // calibrated soil active SOM respiration rate (at 0oC)
  double kdcsompr; //calibrated soil physically-resistant SOM
                   //respiration rate (at 0oC)
  double kdcsomcr; // calibrated soil chemically-resistant SOM
                   // respiration rate (at 0oC)
  soipar_cal(): micbnup(UIN_D), kdcrawc(UIN_D), kdcsoma(UIN_D),
      kdcsompr(UIN_D), kdcsomcr(UIN_D) {}
};

struct soipar_dim {

  // moss
  double maxmossthick;
  double minmossthick;

  // soils
  double minshlwthick;
  double coefshlwa;//carbon vs thick
  double coefshlwb;//carbon vs thick

  double mindeepthick; // FIX: Unused???
  double coefdeepa;//carbon vs thick
  double coefdeepb;//carbon vs thick

  double coefminea;//carbon density vs ham
  double coefmineb;//carbon density vs ham
  
  soipar_dim(): maxmossthick(UIN_D), minmossthick(UIN_D), 
      minshlwthick(UIN_D), coefshlwa(UIN_D), coefshlwb(UIN_D),
      mindeepthick(UIN_D), coefdeepa(UIN_D), coefdeepb(UIN_D), coefminea(UIN_D),
      coefmineb(UIN_D) {}

};

struct soipar_env {

  // active root depth criteria for determining thawing/freezing-derived growing season and degree-day
  double rtdp4gdd;

  double psimax;
  double evapmin;

  double nfactor_s;
  double nfactor_w;

  double drainmax;
  
  soipar_env():rtdp4gdd(UIN_D), psimax(UIN_D), evapmin(UIN_D), nfactor_s(UIN_D), nfactor_w(UIN_D), drainmax(UIN_D){}

};

struct soipar_bgc {

  double kn2;   //used in N immmobilization

  double moistmin;
  double moistmax;
  double moistopt;
  double rhq10;
  double rhmoistfrozen;

  double propftos;
  double nmincnsoil;

  double fnloss;   //fraction of N leaching with drainage water

  //Yuan: fraction of soil organic components produced when respiration
  double fsoma;    // active SOM
  double fsompr;   // physically-resistant SOM
  double fsomcr;   // chemically-resistant SOM
  double som2co2;  // ratio of all SOM to released CO2-C during respiration (decomposition)

  //Yuan: fraction of soil organic components at steady state
  //(final when equilibrium). Used for initializing C pools and can be
  //estimated from soilpar_cal: k values
  double eqrawc;    // raw material C
  double eqsoma;    // active SOM
  double eqsompr;   // physically-resistant SOM
  double eqsomcr;   // chemically-resistant SOM

  // litter C/N ratio adjusted C decomposition rate
  double lcclnc; // the litterfalling C/N ratio base for adjusting 'kdc' to 'kd'
  double kdrawc[MAX_SOI_LAY];
  double kdsoma[MAX_SOI_LAY];
  double kdsompr[MAX_SOI_LAY];
  double kdsomcr[MAX_SOI_LAY];

  soipar_bgc(): kn2(UIN_D), moistmin(UIN_D), moistmax(UIN_D), moistopt(UIN_D),
                rhq10(UIN_D), rhmoistfrozen(UIN_D), propftos(UIN_D),
                nmincnsoil(UIN_D), fnloss(UIN_D),
                fsoma(UIN_D), fsompr(UIN_D), fsomcr(UIN_D), som2co2(UIN_D),
                eqrawc(UIN_D), eqsoma(UIN_D), eqsompr(UIN_D), eqsomcr(UIN_D),
                lcclnc(UIN_D) {
                
    for (int i = 0; i < MAX_SOI_LAY; ++i) {
      kdrawc[i] = UIN_D;
      kdsoma[i] = UIN_D;
      kdsompr[i] = UIN_D;
      kdsomcr[i] = UIN_D;
    }
  }

};

struct snwpar_dim {
  double newden;
  double denmax;
  snwpar_dim(): newden(UIN_D), denmax(UIN_D) {}
};

struct snwpar_env {
  double albmax;
  double albmin;
  snwpar_env(): albmax(UIN_D), albmin(UIN_D) {}
};

struct firepar_bgc {
  double vsmburn; //volume soil moisture criterial for burning
                  //  organic soil horizon
  double foslburn[NUM_FSEVR]; //fire severity specific max. organic
                              //  soil thickness fraction (0 - 1)
  double fvcomb[NUM_FSEVR][NUM_PFT]; //fraction of burned total veg. by each
                                     //  PFT, sum of which is 1
  double fvdead[NUM_FSEVR][NUM_PFT]; //fraction of dead total veg. by each
                                     //  PFT, sum of which is 1

  double r_retain_c;     //ratio of fire emitted C return
  double r_retain_n;     //ratio of fire emitted N return
  
  firepar_bgc(): vsmburn(UIN_D), r_retain_c(UIN_D), r_retain_n(UIN_D) {
    for (int i = 0; i < NUM_FSEVR; ++i) {
      foslburn[i] = UIN_D;
    }
    for (int i = 0; i < NUM_FSEVR; ++i) {
      for (int pft = 0; pft < NUM_PFT; ++pft) {
        fvcomb[i][pft] = UIN_D;
        fvdead[i][pft] = UIN_D;
      }
    }
  }
};

#endif /*PARAMETERS_H_*/
