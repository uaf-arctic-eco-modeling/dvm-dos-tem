#ifndef COHORTLOOKUP_H_
#define COHORTLOOKUP_H_

#include <string>
#include <iostream>
#include <fstream>
#include <sstream>
#include <cmath>
#include <cstdlib>
using namespace std;

#include "../inc/cohortconst.h"
#include "../inc/timeconst.h"
#include "../inc/layerconst.h"

class CohortLookup{
  	  public:
		CohortLookup();
		~CohortLookup();

		string dir;
		string cmtcode;

		void init();
        void assignBgcCalpar(string & dirname);

	//calibration related
	    //vegetation
	    double cmax[NUM_PFT];
	    double nmax[NUM_PFT];

	    double cfall[NUM_PFT_PART][NUM_PFT];
	    double nfall[NUM_PFT_PART][NUM_PFT];

	    double kra[NUM_PFT];                   // parameter for maintenance resp. (rm)
	    double krb[NUM_PFT_PART][NUM_PFT];     // parameter for maintenance resp. (rm)
	    double frg[NUM_PFT];                   // fraction of available NPP (GPP after rm) for growth respiration

	    // soil
	    double micbnup;  // parameter related to N immoblization by soil microbial

	    double kdcmoss;    // calibrated dead moss C material respiration rate (at 0oC)
	    double kdcrawc;    // calibrated soil raw C material respiration rate (at 0oC)
	    double kdcsoma;    // calibrated soil active SOM respiration rate (at 0oC)
	    double kdcsompr;   // calibrated soil physically-resistant SOM respiration rate (at 0oC)
	    double kdcsomcr;   // calibrated soil chemically-resistant SOM respiration rate (at 0oC)

	// canopy dimensions
	  	double sla[NUM_PFT];         // specific leaf area
	  	double klai[NUM_PFT];        // a coefficient to convert LAI to FPC (foliage percentage coverage)

	  	double vegcov[NUM_PFT];      // actual veg. covered fraction, NOTE this is different from 'fpc' - the former is for the whole canopy, while the latter is for foliage
	  	double lai[NUM_PFT];         // lai
	  	int ifwoody[NUM_PFT];        // woody (1) or non-woody (0)
	  	int ifdeciwoody[NUM_PFT];    // deciduous (1) or evergreen (0) woodland (forest or shrubland)
	  	int ifperenial[NUM_PFT];     // perenial plant (1) or not (0)
	  	int nonvascular[NUM_PFT];    //vascular plant (0), sphagnum (1), feathermoss (2), lichen (3)

	  	double envlai[12][NUM_PFT];  // input static monthly lai for a year

    // root distribution
	    double frootfrac[MAX_ROT_LAY][NUM_PFT];   // percentage

   // snow dimensions
	    double snwdenmax;        // max. snow bulk density: kg snow /m3
	    double snwdennew;        // max. snow bulk density: kg snow /m3

	    double initsnwthick;     // initial snow thickness (m)
	    double initsnwdense;     // initial snow bulk density: kg snow /m3

   // ground/soil dimensions
  	    // moss
	  	double maxdmossthick;
	  	double initdmossthick;
	  	int mosstype;
	  	double coefmossa;//carbon vs thick
	  	double coefmossb;//carbon vs thick

	  	// soils
	  	double initfibthick;
        double inithumthick;

	  	double coefshlwa;//carbon vs thick
	  	double coefshlwb;//carbon vs thick

	    double coefdeepa;//carbon vs thick
	  	double coefdeepb;//carbon vs thick

	  	double coefminea;//carbon density vs ham
	  	double coefmineb;//carbon density vs ham

	  	int minetexture[MAX_MIN_LAY];

	  	// active root depth criteria for determining thawing/freezing-derived growing season and degree-day
	  	double rtdp4gdd;

  //for canopy biometeorological processes

	  	double albvisnir[NUM_PFT]; // canopy radiation albedo for both visible and nir
	  	double er[NUM_PFT];        // canopy light extinction coefficient

	  	double ircoef[NUM_PFT];    // canopy interception coeff for rain
	  	double iscoef[NUM_PFT];    // canopy interception coeff for snow

	  	double glmax[NUM_PFT];  // maximum leaf conductance m/s
	  	double gl_bl[NUM_PFT];  // leaf boundary layer conductance m/s
	  	double gl_c[NUM_PFT];   // leaf cuticular conductance

	  	double vpd_open[NUM_PFT];  // vpd for starting of stomata open
	  	double vpd_close[NUM_PFT]; // vpd for complete conductance reduction (stomata closure)
	    double ppfd50[NUM_PFT];    // ppfd for half stomata closure

	    double initvegwater[NUM_PFT];  // canopy rain water (mm)
	  	double initvegsnow[NUM_PFT];   // canopy snow water equivalent (mm)

  // ground/soil biophysical processes
	    // snow physical processes
	    double snwalbmax;        //max. albedo of snow
	    double snwalbmin;        //min. albedo of snow
	    // parameters for evapotranspiration
	    double psimax;        // max. soil matrical potential for transpiration (root water uptake)
	    double evapmin;       // min. reduction of potential soil evaporation after rainfall (that's why 'dsr' is needed)

	    // parameter for soil drainage
	    double drainmax;

	    // inital thermal/water states of snow/soil
	    double initsnwtem;  // 1 snow input: initial snow temperature (note: initial water of snow can be from initial thickness and density)
	    double initvwc[10]; // 10 soil initial input for each 10 cm thickness of layers
	    double initts[10];

  // for vegetation	BGC
	    //parameters for f(phenology) in GPP
	   	double minleaf[NUM_PFT];   //EET determined leaf phenology parameters
	 	double aleaf[NUM_PFT];
	  	double bleaf[NUM_PFT];
	  	double cleaf[NUM_PFT];

	  	//parameters for f(foliage) in GPP
	   	double kfoliage[NUM_PFT];    //for non-woody plants
	  	double cov[NUM_PFT];
	  	double m1[NUM_PFT];        //for woody plants
	  	double m2[NUM_PFT];
	  	double m3[NUM_PFT];
	  	double m4[NUM_PFT];

	  	//parameter for f(CO2) in GPP
	    double kc[NUM_PFT];

	    //parameter for f(par) in GPP
	    double ki[NUM_PFT];

	    //parameter for f(tair) in GPP
	    double tmin[NUM_PFT];
	    double toptmin[NUM_PFT];
	    double toptmax[NUM_PFT];
	    double tmax[NUM_PFT];

	    //parameter for f(tair) in nuptake
	    double raq10a0[NUM_PFT];
	    double raq10a1[NUM_PFT];
	    double raq10a2[NUM_PFT];
	    double raq10a3[NUM_PFT];

	    // parameter for root-zone water/avln in nuptake
	    double knuptake[NUM_PFT];

	    // parameters for GPP/NPP allocations in tissues
	    double cpart[NUM_PFT_PART][NUM_PFT];   //biomass C partioning fraction

	    // parameters for tissue C/N ratios at optimal states ('cneven')
	    double initc2neven[NUM_PFT_PART][NUM_PFT];
	    double c2nmin[NUM_PFT_PART][NUM_PFT];        // these 3 are for adjusting 'cneven' with atm. CO2
	    double c2na[NUM_PFT];
	    double c2nb[NUM_PFT_PART][NUM_PFT];

	    // a parameter to estimate plant labile N uptake
	    double labncon[NUM_PFT];
  
  // for soil mcrobial processes

	    // Q10 and soil moisture factors for Rh
	    double rhq10;
	    double moistmin;
	    double moistopt;
	    double moistmax;

	    // litterfall C/N ratio criteria to adjust soil C decomposition rates annually
	    double lcclnc;

	    // parameters for SOM C transformation
	    double fsoma;     // fraction of SOMA production during respiration
	    double fsompr;    // fraction of SOMPR production during respiration
	    double fsomcr;    // fraction of SOMCR production during respiration
	    double som2co2;   // ratio of total SOM production and CO2 release during respiration

	    // a parameter for soil N immobilization
	    double kn2;

	    // parameters for soil net N mineralization
	    double propftos;
	    double nmincnsoil;     // soil C/N ratio at which net mineralization occurs

	    // fraction of avln in soil leaching out with drainage water
	    double fnloss;


  //init values
	    double initvegc[NUM_PFT_PART][NUM_PFT];     //or, target value for calibration
	    double initvegn[NUM_PFT_PART][NUM_PFT];
	    double initdeadc[NUM_PFT];
	    double initdeadn[NUM_PFT];
  
	    double initdmossc;
	    double initshlwc;
	    double initdeepc;
	    double initminec;
	    double initsoln;    // total soil organic N
	    double initavln;    // total soil available N

//fire related parameters
	    double fvcombust[NUM_FSEVR][NUM_PFT]; // fraction of burned above-ground vegetation
	    double fvslash[NUM_FSEVR][NUM_PFT];   // fraction of slashed above-ground vegetation

	    double foslburn[NUM_FSEVR];        // fire severity based organic soil layer burning fraction
	    double vsmburn;            // a threshold value of VWC for burn organic layers

	    double r_retain_c;         // 0.1 calculated from Harden et al., 2003 (ATHarden42003a)
	    double r_retain_n;         // 0.3 calculated from Harden et al., 2003 (ATHarden42003a)

  private:

	    void assignVegDimension(string & dir);
	    void assignGroundDimension(string & dir);

	    void assignEnv4Canopy(string & dir);
	    void assignBgc4Vegetation(string & dir);

	    void assignEnv4Ground(string & dir);
	    void assignBgc4Ground(string & dir);

	    void assignFirePar(string & dir);
   
};

#endif /*COHORTLOOKUP_H_*/
