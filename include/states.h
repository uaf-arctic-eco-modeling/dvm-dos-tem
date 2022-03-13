/*
 * \file
 * defines struct for state variables between atmosphere, vegetation, land(snow and soil)
 */
#ifndef STATES_H_
#define STATES_H_

#include "errorcode.h"
#include "cohortconst.h"
#include "layerconst.h"

struct atmstate_env {
  double co2; //ppmv
  double ta;
  int dsr;   // day since rain

  atmstate_env(): co2(UIN_D), ta(UIN_D), dsr(UIN_I) {}

};

struct vegstate_dim {

  int vegage[NUM_PFT]; // in years

  int ifwoody[NUM_PFT]; //woody-plant vs non-woody: different functions
                        //  for 'foliage' equation
  int ifdeciwoody[NUM_PFT]; //decidous vs evergreen woodland: different
                            //  'nfactor' for ground-surface temperature
                            //  estimation
  int ifperenial[NUM_PFT]; //perennial plant (1) or not (0): not yet used
  int nonvascular[NUM_PFT]; //vascular plant (0), sphagnum (1),
                            //feathermoss (2), lichen (3)
  double vegcov[NUM_PFT]; //veg. coverage fraction (max. fpc over time, i.e.
                          //land coverage fraction (max. value by whole canopy))

  double lai[NUM_PFT]; //lai
  double fpc[NUM_PFT]; //foliage percentage coverage (seasonally dynamics),
                       //  related to LAI
  double frootfrac[MAX_ROT_LAY][NUM_PFT]; // fine root distribution

  vegstate_dim() {
    for (int i = 0; i < NUM_PFT; ++i) {
      vegage[i] = UIN_I;
      ifwoody[i] = UIN_I;
      ifdeciwoody[i] = UIN_I;
      ifperenial[i] = UIN_I;
      nonvascular[i] = UIN_I;
      vegcov[i] = UIN_D;
      lai[i] = UIN_D;
      fpc[i] = UIN_D;
    }
    for (int i = 0; i < MAX_ROT_LAY; ++i) {
      for (int pft = 0; pft < NUM_PFT; ++pft) {
        frootfrac[i][pft] = UIN_D;
      }
    }

  }
};

struct vegstate_env {
  double snow;   // snow on veg // mm (H2O)
  double rwater;  // rain water on veg // mm (H2O)
  vegstate_env():snow(UIN_D), rwater(UIN_D) {}
};

struct vegstate_bgc {
  double call;
  double c[NUM_PFT_PART];

  double nall;        //Yuan: total N in vegetation
  double labn;        //Yuan: labile N in vegetation
  double strnall;     //Yuan: total structural-N
  double strn[NUM_PFT_PART];    //Yuan: part structural-N

  double nreqall;
  double nreq[NUM_PFT_PART];

  double deadc;    //C in the dead vegetation
  double deadn;    //N in the dead vegetation

  double deadc0; //Initial value of C in standing dead post-fire
  double deadn0; //Initial value of N in standing dead post-fire

  vegstate_bgc(): call(UIN_D), nall(UIN_D), labn(UIN_D), strnall(UIN_D),
      deadc(UIN_D), deadn(UIN_D), deadc0(UIN_D), deadn0(UIN_D) {

    for (int i = 0; i < NUM_PFT_PART; ++i) {
      c[i] = UIN_D;
      strn[i] = UIN_D;
    }

  }
};

struct snwstate_dim {
  int numsnwl;
  double olds;      // the oldest snow layer age
  double thick;     // unit: m
  double dense;     // unit: kg/m3

  double extramass; /* // snow mass not yet reaches a minimum thickness for
                       a snow-layer (unit: kg/m2) */
  double dz[MAX_SNW_LAY];    // m
  double age[MAX_SNW_LAY];   // years
  double rho[MAX_SNW_LAY];   // kg/m3
  double por[MAX_SNW_LAY];   // fraction

  snwstate_dim(): numsnwl(UIN_D), olds(UIN_D), thick(UIN_D), dense(UIN_D),
      extramass(UIN_D){
    for (int i = 0; i < MAX_SNW_LAY; ++i) {
      dz[i] = UIN_D;
      age[i] = UIN_D;
      rho[i] = UIN_D;
      por[i] = UIN_D;

    }
  }

};


struct snwstate_env {

  double tsnw[MAX_SNW_LAY];
  double swe[MAX_SNW_LAY];
  double snwliq[MAX_SNW_LAY];
  double snwice[MAX_SNW_LAY];
  double extraswe; //snow mass NOT large enough to cover ground to
                   //  form a layer of min. thickness
  double swesum; // total snow water equivalent (mm H2O, or, kg/m2)
  double tsnwave;
  double snowthick;

  //The following two variables are used to track the presence or absence
  // of enough snow to create a snow layer. The output variables SNOWSTART
  // and SNOWEND are determined from them.
  int days_present; //Consecutive days with a snow layer
  int days_absent; //Consecutive days without snow

  int snowstart;//DOY - first day a snow layer exists and sticks for 7 days
  int snowend;//DOY - first day of no snow layers for 7 consecutive days

  snwstate_env():swesum(UIN_D), tsnwave(UIN_D), extraswe(UIN_D),
                 snowthick(UIN_D), days_present(UIN_I), days_absent(UIN_I),
                 snowstart(UIN_I), snowend(UIN_I) {
    for (int i = 0; i < MAX_SNW_LAY; ++i) {
      tsnw[i] = UIN_D;
      swe[i] = UIN_D;
      snwliq[i] = UIN_D;
      snwice[i] = UIN_D;
    }

  }
};

struct soistate_dim {

  int numsl; // total number of soil layers
  int mossnum;
  int shlwnum;
  int deepnum;
  int minenum;

  int mosstype;   // 1: sphagnum, 0: feathermoss

  double totthick;
  double mossthick;
  double shlwthick;
  double deepthick;
  double mineathick;
  double minebthick;
  double minecthick;

  double z[MAX_SOI_LAY]; // distance between soil surface and layer top
  double dz[MAX_SOI_LAY]; // layer thickness
  double por[MAX_SOI_LAY];
  int age[MAX_SOI_LAY];
  int type[MAX_SOI_LAY]; //layer type://0,1,2,3 for moss, shallow peat,
                         //                       deep peat, mineral

  double frootfrac[MAX_SOI_LAY][NUM_PFT]; //fine root vertical distribution

  soistate_dim():numsl(UIN_I),mossnum(UIN_I),shlwnum(UIN_I),deepnum(UIN_I),
      minenum(UIN_I), mosstype(UIN_I), totthick(UIN_D), mossthick(UIN_D),
      shlwthick(UIN_D), deepthick(UIN_D), mineathick(UIN_D), minebthick(UIN_D),
      minecthick(UIN_D) {

    for (int i = 0; i < MAX_SOI_LAY; ++i) {
      z[i] = UIN_D;
      dz[i] = UIN_D;
      por[i] = UIN_D;
      age[i] = UIN_I;
      type[i] = UIN_I;

    }

    for (int i = 0; i < MAX_SOI_LAY; ++i) {
      for (int pft = 0; pft < NUM_PFT; ++pft) {
        frootfrac[i][pft] = UIN_D;
      }
    }

  }
};

struct soistate_env {

  double frozen[MAX_SOI_LAY]; //totally frozen: 1, totally unfrozen: -1,
                              //partially frozen: 0 (daily) or <1~>-1
                              //(for monthly/yearly)
  double frozenfrac[MAX_SOI_LAY]; //totally frozen: 1.0, totally unfrozen: 0.0,
                                  //partially frozen: 0 - 1.0
  double ts[MAX_SOI_LAY];
  double liq[MAX_SOI_LAY]; // soil liquid water content kg/m2 (or 1 mm liq. H2O)
  double ice[MAX_SOI_LAY]; // soil ice content kg/m2 (or 1 mm liq. H2O)

  double trock[MAX_ROC_LAY];

  int frontstype[MAX_NUM_FNT];   //type of fronts (1: freezing, -1: thawing)
  double frontsz[MAX_NUM_FNT];   //depth from ground surface

  double watertab;       // water table depth below ground surface (m)
  double draindepth;     // drainage depth below ground surface (m)

  soistate_env():watertab(UIN_D), draindepth(UIN_D) {

    for (int i = 0; i < MAX_SOI_LAY; ++i) {
      frozen[i] = UIN_D;
      frozenfrac[i] = UIN_D;
      ts[i] = UIN_D;
      liq[i] = UIN_D;
      ice[i] = UIN_D;
    }

    for (int i = 0; i < MAX_ROC_LAY; ++i) {
      trock[i] = UIN_D;
    }

    for (int i = 0; i < MAX_NUM_FNT; ++i) {
      frontstype[i] = UIN_I;
      frontsz[i] = UIN_D;
    }

  }
};

struct soistate_bgc {
  //Woody debris is *NOT* an actual soil layer. It is conceptually
  //a separate set of pools.
  double wdebrisc;    // wood debris C
  double wdebrisn;    // wood debris N

  double rawc[MAX_SOI_LAY];   //soil raw plant material C
  double soma[MAX_SOI_LAY];   //active som c
  double sompr[MAX_SOI_LAY];  //physically-resistant som c
  double somcr[MAX_SOI_LAY];  //chemically-resistant som c

  double orgn[MAX_SOI_LAY];   // soil total N content kg/m2
  double avln[MAX_SOI_LAY];   // soil available N content kg/m2
  
  soistate_bgc(): wdebrisc(UIN_D),wdebrisn(UIN_D) {
    for (int i=0; i < MAX_SOI_LAY; ++i) {
      rawc[i] = UIN_D;
      soma[i] = UIN_D;
      sompr[i] = UIN_D;
      somcr[i] = UIN_D;
      orgn[i] = UIN_D;
      avln[i] = UIN_D;
    }
  }
  
};

#endif /*STATES_H_*/
