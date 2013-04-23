/*
 * \file
 * defines struct for fluxes between atmosphere, vegetation, land(snow and soil)
 */
#ifndef FLUXES_H_
#define FLUXES_H_

#include "cohortconst.h"
#include "layerconst.h"

// for water
	struct lnd2atm_env{
  		double eet;
  		double pet;

	};

	struct lnd2atm_bgc{
  		double nep;
	};

	struct atm2lnd_env{          //NOTE: land includes both veg and ground
		// water	
  		double prec;  // mm
  		double snfl;  // mm
  		double rnfl;  // mm
		// energy
  		double nirr;  //  W/m2
  		double par;	  //  W/m2
  
	};

	struct atm2veg_env{
		// water
  		double rnfl;
  		double snfl;	

  		double rinter;
  		double sinter;

  		// radiation
  		double swdown;     // non-reflected (short-wave) solar radiation: W/m2
 		double swinter;    // intercepted (short-wave) solar radiation: W/m2
  		double pardown;    // non-reflected PAR: W/m2
  	  	double parabsorb;  // absorbed PAR: W/m2
	};

	struct atm2veg_bgc{
		// carbon	
  		double ingppall; // gpp not limited by nitrogen availability
  		double ingpp[NUM_PFT_PART];

  		double gppall;
  		double gpp[NUM_PFT_PART];

  		double innppall;
  		double innpp[NUM_PFT_PART];

  		double nppall;
  		double npp[NUM_PFT_PART];

	};

	struct veg2atm_env{
  		//water
  		double tran; // mm/day
  		double evap; // mm/day
  		double tran_pet; // mm/day
  		double evap_pet; // mm/day
  
  		double sublim; // mm/day	

  		//energy
  		double swrefl; // W/m2: reflected solar radiation
	};

	struct veg2atm_bgc{
  		//carbon
 		double rmall;// maintainance respiration
 		double rm[NUM_PFT_PART];

 		double rgall; // growth respiration;
 		double rg[NUM_PFT_PART];

	};

	struct veg2gnd_env{
  		// water
  		double rthfl; // rain throughfall
  		double sthfl; // snow throughfall	
  		double rdrip; // rain drip
  		double sdrip; // snow drip	
  
  		// radiation throught fall
  		double swthfl;// shortwave W/m2
	};

	struct veg2soi_bgc{
		//
		double rtlfalfrac[MAX_SOI_LAY];  //root mortality vertical distribution

		// carbon
  		double d2wdebrisc;   // dead standing C to ground debris
  		double ltrfalcall;     //excluding moss/lichen mortality
  		double mossdeathc;     // moss/lichen mortality
 		double ltrfalc[NUM_PFT_PART];
  
  		// nitrogen
  		double d2wdebrisn;   // dead standing N to ground debris
  		double ltrfalnall;     //excluding moss/lichen mortality
  		double mossdeathn;     // moss/lichen mortality
  		double ltrfaln[NUM_PFT_PART];
	};

	struct soi2veg_bgc{
  		// nitrogen	

   		double innuptake;
   		double lnuptake;
 		double snuptakeall;
 		double snuptake[NUM_PFT_PART];

 		double nextract[MAX_SOI_LAY];  //all root N extraction from each soil layer

	};

	struct veg2veg_bgc{
  		//nitrogen
  		double nmobilall;     //N allocation from labile-N pool to tissue pool when needed
  		double nmobil[NUM_PFT_PART];

  		double nresorball;    //N resorbation into labile-N pool when litter-falling
  		double nresorb[NUM_PFT_PART];

	};

	struct soi2lnd_env{
		double qinfl;    // infiltration water
 		double qover;
 		double qdrain;
	};

	struct soi2lnd_bgc{
 		double doclost;     //DOC lost

 		// nitrogen
 		double avlnlost;    // N leaching
 		double orgnlost;    // N loss with DOC

	};


	struct soi2atm_env{
  		double evap;
  		double evap_pet;
  		double swrefl;

	};

	struct soi2atm_bgc{
  		double rhwdeb; //rh from wood debris

  		double rhmossc;

  		double rhrawc[MAX_SOI_LAY];
  		double rhsoma[MAX_SOI_LAY];
  		double rhsompr[MAX_SOI_LAY];
  		double rhsomcr[MAX_SOI_LAY];

  	   	double rhrawcsum;
  	   	double rhsomasum;
  	   	double rhsomprsum;
  	   	double rhsomcrsum;

  	   	double rhtot;  //total rhs
	};

	struct snw2atm_env{
  		double sublim;	
  		double swrefl;
	};

	struct snw2soi_env{
	  	double melt;
	};

	struct atm2soi_bgc{
  		double orgcinput;
  		double orgninput;
 		double avlninput;
	};

	struct soi2soi_bgc{
  		double netnmin[MAX_SOI_LAY];
  		double nimmob[MAX_SOI_LAY];
  		double netnminsum;
  		double nimmobsum;
	};

	struct atm2soi_fir{
 		double orgn;
	};

	struct soi2atm_fir{
  		double orgc;
  		double orgn;	
	};

	struct veg2atm_fir{
  		double orgc;
  		double orgn;
	};

	struct veg2soi_fir{
  		double abvc;
  		double abvn;
  		double blwc;
  		double blwn;
  	
	};
#endif /*FLUXES_H_*/

