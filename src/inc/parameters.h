/*! contains parameters for veg, and soil
 */
#ifndef PARAMETERS_H_
#define PARAMETERS_H_

#include "cohortconst.h"
#include "layerconst.h"

struct vegpar_cal{

	double cmax;
    double nmax;

    double cfall[NUM_PFT_PART];
    double nfall[NUM_PFT_PART];

    double kra;                   // parameter for maintenance resp. (rm)
    double krb[NUM_PFT_PART];     // parameter for maintenance resp. (rm)
    double frg;                   // fraction of available NPP (GPP after rm) for growth respiration

};

// dimension parameters for vegetation
struct vegpar_dim{
  	double sla[NUM_PFT];         // specific leaf area
  	double klai[NUM_PFT];        // a coefficient to convert LAI to FPC (foliage percentage coverage)

	// the following 4 parameters are for eet adjusted leaf phenology
	// including previous eet, implied some of drought's extended effects on leaf development
	double minleaf[NUM_PFT];
	double aleaf[NUM_PFT];
	double bleaf[NUM_PFT];
	double cleaf[NUM_PFT];

	// for the vegetation biomass (C) or age adjusted leaf phenology
	double kfoliage[NUM_PFT];  // these 2 parameters for non-forest
	double cov[NUM_PFT];
    double m1[NUM_PFT];	    // these 4 parameters for forest
    double m2[NUM_PFT];
    double m3[NUM_PFT];
    double m4[NUM_PFT];

};

struct vegpar_env{
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

};

struct vegpar_bgc{

	// new production allocation (partioning)
	double cpart[NUM_PFT_PART];   //Yuan: biomass partioning

	// new production C:N ratios - determining the N requirements
	double c2neven[NUM_PFT_PART];    // C:N ratio in new production at current CO2, and adjsted by eet/pet
    double c2na;                     // for vegetation C:N ratio adjustment by eet/pet
    double c2nb[NUM_PFT_PART];       // for vegetation C:N ratios adjustment by eet/pet
	double c2nmin[NUM_PFT_PART];     // min. C:N ratios
	double dc2n;                     // factor for changing C:N per ppmv of enhanced CO2*/

	double labncon;   // max. fraction of labile-N change over total veg structural N change

	double raq10a0;   // for maintenence respiration and root uptake regulation by air temperature
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

};

struct soipar_cal{
	double micbnup;  // parameter related to N immoblization by soil microbial

    double kdcmoss;    // calibrated dead moss C material respiration rate (at 0oC, favoriable soil moisture)
    double kdcrawc;    // calibrated soil raw C material respiration rate (at 0oC, favoriable soil moisture, and not litter C/N adjusted)
    double kdcsoma;    // calibrated soil active SOM respiration rate (at 0oC)
    double kdcsompr;   // calibrated soil physically-resistant SOM respiration rate (at 0oC)
    double kdcsomcr;   // calibrated soil chemically-resistant SOM respiration rate (at 0oC)

};

struct soipar_dim{

	// moss
  	double maxmossthick;
  	double minmossthick;
  	double coefmossa;//carbon vs thick
  	double coefmossb;//carbon vs thick

  	// soils
  	double minshlwthick;
  	double coefshlwa;//carbon vs thick
  	double coefshlwb;//carbon vs thick

  	double mindeepthick;
    double coefdeepa;//carbon vs thick
  	double coefdeepb;//carbon vs thick

  	double coefminea;//carbon density vs ham
  	double coefmineb;//carbon density vs ham

};

struct soipar_env{
	
  	// active root depth criteria for determining thawing/freezing-derived growing season and degree-day
	double rtdp4gdd;

    double psimax;
	double evapmin;

	double drainmax;
	
};

struct soipar_bgc{

    double kn2;   //used in N immmobilization

    double moistmin;
    double moistmax;
    double moistopt;
    double rhq10;
    
	double propftos;
    double nmincnsoil;

    double fnloss;   //fraction of N leaching with drainage water

    //Yuan: fraction of soil organic components produced when respiration
    double fsoma;    // active SOM
    double fsompr;   // physically-resistant SOM
    double fsomcr;   // chemically-resistant SOM
    double som2co2;  // ratio of all SOM to released CO2-C during respiration (decomposition)

    //Yuan: fraction of soil organic components at steady state (final when equilibrium)
    //    used for initializing C pools and can be estimated from soilpar_cal: k values
    double eqrawc;    // raw material C
    double eqsoma;    // active SOM
    double eqsompr;   // physically-resistant SOM
    double eqsomcr;   // chemically-resistant SOM

    // dead moss material decomposition rate
    double kdmoss;

    // litter C/N ratio adjusted C decomposition rate
    double lcclnc;    // the litterfalling C/N ratio base for adjusting 'kdc' to 'kd'
    double kdrawc[MAX_SOI_LAY];
    double kdsoma[MAX_SOI_LAY];
  	double kdsompr[MAX_SOI_LAY];
  	double kdsomcr[MAX_SOI_LAY];

};

struct snwpar_dim{
    double newden;
    double denmax;
};

struct snwpar_env{
    double albmax;
    double albmin;
};

struct firepar_bgc{
	double vsmburn;               //volume soil moisture criterial for burning organic soil horizon
	double foslburn[NUM_FSEVR];     // fire severity specific max. organic soil thickness fraction (0 - 1)
	double fvcomb[NUM_FSEVR][NUM_PFT];    //fraction of burned total veg. by each PFT, sum of which is 1
	double fvdead[NUM_FSEVR][NUM_PFT];    //fraction of dead total veg. by each PFT, sum of which is 1

	double r_retain_c;     //ratio of fire emitted C return
	double r_retain_n;     //ratio of fire emitted N return
};

#endif /*PARAMETERS_H_*/
