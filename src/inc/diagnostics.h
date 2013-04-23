/*
 * \file
 * defines struct for diagnostic variables between atmosphere, vegetation, land(snow and soil)
 */
#ifndef DIAGNOSTICS_H_
#define DIAGNOSTICS_H_

#include "cohortconst.h"
#include "layerconst.h"

// Diagnostic Variables
struct atmdiag_env{
  	double vpd;     // vapor pressure deficit (Pa)
  	double vp;      // vapor pressure (Pa)
  	double svp; 	// saturated vapor pressure (Pa)
};

struct vegdiag_dim{
    double fpcsum;                   // sum of fpc[] (must not be greater than 1.0)

    // phenoloy variables
	double growingttime[NUM_PFT];     // (current but accumulated) growing thermal time
    double maxleafc[NUM_PFT];           // max. leaf C limited by plant state itself

    double fleaf[NUM_PFT];            // (current) normalized (scalar) foliage growth index based on current and previous EET
	double unnormleaf[NUM_PFT];       // (current) un-normarlized fleaf
	double eetmx[NUM_PFT];            // (yearly) max. month eet
	double unnormleafmx[NUM_PFT];     // (yearly max.) un-normarlized fleaf
	double topt[NUM_PFT];             // (yearly) evolving optimium temperature for temperature-scalar of GPP

	double ffoliage[NUM_PFT];         // (current)foliage growth index (scalar) based on vegetation C (stand age related)
    double foliagemx[NUM_PFT];        // this is for 'ffoliage' not growing backward

};

struct vegdiag_env{
  	double btran;
  
  	double rc;         // canopy resistance s/m
  	double cc;         // canopy conductance m/s

  	double m_ppfd;     //
  	double m_vpd;

};

struct vegdiag_bgc{

	double raq10;
  	double ftemp; /*! temperature factor for gpp*/
  	double gv;

  	double kr[NUM_PFT_PART];  // maintainence resp: is related to kra, krb, and vegetation carbon  pool
  	double fna; // effect of nitrogen availability on gpp
  	double fca; // effect of carbon availability on nuptake
};

struct snwdiag_env{
	int snowfreeFst;       //used for estimating growing season
	int snowfreeLst;       //used for estimating growing season
	double tcond[MAX_SNW_LAY];

    double fcmelt;         /*! melting factor */

};

struct soidiag_env{

	int permafrost;
	double unfrzcolumn;    // unfrozen soil column length (m)
	double alc;            // active layer cap (m), i.e. the top of active layer - seasonal frezing front
	double ald;            // active layer depth (m), i.e., the bottom of active layer - seasonal or permafrost

	//variables used for estimating growing season and growth timing
	double rtdpts;          // soil temperature over the active root zone depth 'rtdp4gdd'
	double rtdpthawpct;     // soil thawing period percentage over 'rtdp4gdd'
	double rtdpgdd;         // growing degree-days over 'rtdep4gdd'
	int rtdpgrowstart;      // growing starting DOY based on soil thawing over 'rtdep4gdd'
	int rtdpgrowend;        // growing ending DOY based on soil freezing over 'rtdep4gdd'

	double nfactor;

	double vwc[MAX_SOI_LAY];  // Yuan: soil water content: volume fraction of all water/total soil volume (Theta)
	double iwc[MAX_SOI_LAY];  // Yuan: ice water content: volume fraction of ice water/total soil volume (Theta)
	double lwc[MAX_SOI_LAY];  // Yuan: liquid water content: volume fraction of liquid water/total soil volume (Theta)
	double sws[MAX_SOI_LAY];  // soil liquid water saturation (liq vwc/total porosity) for use in Soil_Bgc
	double aws[MAX_SOI_LAY];  // adjusted soil liquid water saturation (liq vwc/(porosity-ice vwc)) for use in Soil_Bgc
	  
	double minliq[MAX_SOI_LAY];
	double tcond[MAX_SOI_LAY];
	double hcond[MAX_SOI_LAY];

	double fbtran[MAX_SOI_LAY];   // fraction of root water uptake (transpiration) in each soil layer (total 1.0)


///// variables of summarized over soil horizons
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


};

struct soidiag_bgc{
	double knmoist[MAX_SOI_LAY];        // soil liq water factor to be used in N immobilization and mineralization

  	double rhmoist[MAX_SOI_LAY];
  	double rhq10[MAX_SOI_LAY];

  	double ltrfcn[MAX_SOI_LAY];        //litterfall (root death) input C/N ratios in each soil layer for adjusting 'kd'

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

};

struct soidiag_fir{
  	double burnthick;
};

#endif /*DIAGNOSTICS_H_*/
