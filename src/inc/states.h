/*
 * \file
 * defines struct for state variables between atmosphere, vegetation, land(snow and soil)
 */
#ifndef STATES_H_
#define STATES_H_

#include "cohortconst.h"
#include "layerconst.h"

struct atmstate_env{
	double co2; //ppmv
	double ta;
	int dsr;   // day since rain
};

struct vegstate_dim{

    int vegage[NUM_PFT];             // in years

    int ifwoody[NUM_PFT];            // woody-plant vs non-woody: different functions for 'foliage' equation
    int ifdeciwoody[NUM_PFT];        // decidous vs evergreen woodland: different 'nfactor' for ground-surface temperture estimation
    int ifperenial[NUM_PFT];         // perenial plant (1) or not (0): not yet used
    int nonvascular[NUM_PFT];        // vascular plant (0), sphagnum (1), feathermoss (2), lichen (3)
    double vegcov[NUM_PFT];          // veg. coverage fraction (max. fpc over time, i.e. land coverage fraction (max. value by whole canopy))

    double lai[NUM_PFT];             // lai
    double fpc[NUM_PFT];             // foliage percentage coverage (seasonally dynamics), related to LAI
    double frootfrac[MAX_ROT_LAY][NUM_PFT];    // fine root distribution

};

struct vegstate_env{
    double snow;   // snow on veg // mm (H2O)
    double rwater;  // rain water on veg // mm (H2O)
};

struct vegstate_bgc{
    double call;
    double c[NUM_PFT_PART];

    double nall;        //Yuan: total N in vegetation
    double labn;        //Yuan: labile N in vegetation
    double strnall;     //Yuan: total structural-N
    double strn[NUM_PFT_PART];    //Yuan: part structural-N

    double deadc;    //C in the dead vegetation
    double deadn;    //N in the dead vegetation

};

struct snwstate_dim{
	int numsnwl;
	double olds;      // the oldest snow layer age
	double thick;     // unit: m
  	double dense;     // unit: kg/m3

    double extramass; 	   /* // snow mass not yet reaches a minimum thickness for a snow-layer (unit: kg/m2) */
  	double dz[MAX_SNW_LAY];    // m
	double age[MAX_SNW_LAY];   // years
	double rho[MAX_SNW_LAY];   // kg/m3
	double por[MAX_SNW_LAY];   // fraction

};


struct snwstate_env{

	double tsnw[MAX_SNW_LAY];
	double swe[MAX_SNW_LAY];
	double snwliq[MAX_SNW_LAY];
	double snwice[MAX_SNW_LAY];
	double extraswe;     // snow mass NOT large enough to cover ground to form a layer of min. thickness
	double swesum;       // total snow water equivalent (mm H2O, or, kg/m2)
	double tsnwave;

};

struct soistate_dim{

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

	double z[MAX_SOI_LAY];   // distance between soil surface and layer top
	double dz[MAX_SOI_LAY];  // layer thickness
	double por[MAX_SOI_LAY];
	int age[MAX_SOI_LAY];
	int type[MAX_SOI_LAY];   // layer type://0,1,2,3 for moss, shallow peat, deep peat, mineral
	int texture[MAX_SOI_LAY];  // 0 ~ 11, see the SoilLookup.cpp
	double frootfrac[MAX_SOI_LAY][NUM_PFT];    //fine root vertical distribution

};

struct soistate_env{

	double frozenfrac[MAX_SOI_LAY];   //totally frozen: 1, totally unfrozen: -1, partially frozen: 0 (daily) or <1~>-1 (for monthly/yearly)
	double ts[MAX_SOI_LAY];
	double liq[MAX_SOI_LAY]; // soil liquid water content kg/m2 (or 1 mm liq. H2O)
	double ice[MAX_SOI_LAY]; // soil ice content kg/m2 (or 1 mm liq. H2O)

	double trock[MAX_ROC_LAY];

	int frontstype[MAX_NUM_FNT];   //type of fronts (1: freezing, -1: thawing)
	double frontsz[MAX_NUM_FNT];   //depth from ground surface

	double watertab;       // water table depth below ground surface (m)
	double draindepth;     // drainage depth below ground surface (m)

};

struct soistate_bgc{
	double wdebrisc;    //wood debris C
	double wdebrisn;    //wood debris N

	double dmossc;  //dead moss material C
	double dmossn;  //dead moss material N

	double rawc[MAX_SOI_LAY];   //soil raw plant material C
	double soma[MAX_SOI_LAY];   //active som c
	double sompr[MAX_SOI_LAY];  //physically-resistant som c
	double somcr[MAX_SOI_LAY];  //chemically-resistant som c

	double orgn[MAX_SOI_LAY];   // soil total N content kg/m2
	double avln[MAX_SOI_LAY];   // soil available N content kg/m2
};

#endif /*STATES_H_*/
