#ifndef REGNOUTDATA_H_
#define REGNOUTDATA_H_
/* 
 * define output variables for regional TEM run
 * memory consumption too much, so modified as output year by year
 *  rather than cohort by cohort - Yuan
 */

#include "../inc/errorcode.h"
#include "../inc/timeconst.h"
#include "../inc/cohortconst.h"

// the following index MUST be exactly match up with the var list in "outvarlist.txt" located in /config/
// this list of index is used in 'OutTrieve::OutRegnBuffer.ccp' and 'RegnOutputer.cpp'
// (it's for easy code maintainence)
enum outvarlistkey {
   		     I_growstart = 0, I_growend, I_vegcov, I_vegage,
   		     I_lai,  I_vegc, I_leafc, I_stemc, I_rootc,
   		     I_vegn, I_labn, I_leafn, I_stemn, I_rootn,
   		     I_gpp,  I_npp,  I_ltrfalc, I_ltrfaln, I_nuptake,

   		     I_permafrost, I_mossdz, I_oshlwdz, I_odeepdz, I_mineadz, I_minebdz, I_minecdz,
   		     I_oshlwc, I_odeepc, I_mineac, I_minebc, I_minecc, I_orgn, I_avln,
   		     I_rh, I_netnmin,

   		     I_orgninput, I_avlninput, I_doclost, I_orgnlost, I_avlnlost,

   		     I_eet,	I_pet, I_qinfl,	I_qdrain, I_qrunoff,
      	     I_snwthick, I_swe,	I_wtd, I_alc, I_ald,
   		     I_vwcshlw,	I_vwcdeep, I_vwcminea, I_vwcmineb, I_vwcminec,
   		     I_tshlw,I_tdeep,I_tminea, I_tmineb, I_tminec, I_tbotrock,
   		     I_hkshlw, I_hkdeep, I_hkminea, I_hkmineb, I_hkminec,
   		     I_tcshlw, I_tcdeep, I_tcminea, I_tcmineb, I_tcminec,

			I_burnthick, I_burnsoic, I_burnvegc, I_burnsoin, I_burnvegn,
			I_burnretainc, I_burnretainn,

			I_outvarno

};

class OutDataRegn{

	public:

		OutDataRegn();
		~OutDataRegn();

	 	int chtid;
	  	int status[12];
		int year;
		int month[12];
   		int yrsdist;

   		int outvarlist[78];

   		// after update the following vars, please update the list and enum above
   		int growstart[12][NUM_PFT];
   		int growend[12][NUM_PFT];
   		double vegcov[12][NUM_PFT];
   		double vegage[12][NUM_PFT];

   		double lai[12][NUM_PFT];
   		double vegc[12][NUM_PFT];
   		double leafc[12][NUM_PFT];
   		double stemc[12][NUM_PFT];
   		double rootc[12][NUM_PFT];
   		double vegn[12][NUM_PFT];
   		double labn[12][NUM_PFT];
   		double leafn[12][NUM_PFT];
  		double stemn[12][NUM_PFT];
  		double rootn[12][NUM_PFT];

   		double gpp[12][NUM_PFT];
   		double npp[12][NUM_PFT];

        double ltrfalc[12][NUM_PFT];
        double ltrfaln[12][NUM_PFT];

        double nuptake[12][NUM_PFT];

        //
   		int permafrost[12];

   		double mossdz[12];
   		double oshlwdz[12];
   		double odeepdz[12];
   		double mineadz[12];
   		double minebdz[12];
   		double minecdz[12];

   		double oshlwc[12];
   		double odeepc[12];
   		double mineac[12];
   		double minebc[12];
   		double minecc[12];

   		double orgn[12];
   		double avln[12];

   		double rh[12];
   		double netnmin[12];

   		double orgninput[12];
   		double avlninput[12];

      	double doclost[12];
      	double orgnlost[12];
      	double avlnlost[12];

      	//
      	double eet[12];
   		double pet[12];
   		double qinfl[12];
   		double qdrain[12];
      	double qrunoff[12];

      	double snwthick[12];
      	double swe[12];

   		double wtd[12];
   		double alc[12];
      	double ald[12];

   		double vwcshlw[12];
   		double vwcdeep[12];
   		double vwcminea[12];
      	double vwcmineb[12];
      	double vwcminec[12];

   		double tshlw[12];
   		double tdeep[12];
   		double tminea[12];
   		double tmineb[12];
   		double tminec[12];

   		double hkshlw[12];
   		double hkdeep[12];
   		double hkminea[12];
   		double hkmineb[12];
   		double hkminec[12];

   		double tcshlw[12];
   		double tcdeep[12];
   		double tcminea[12];
   		double tcmineb[12];
   		double tcminec[12];

   		double tbotrock[12];

   		//
   		double burnthick[12];
   		double burnsoic[12];
   		double burnvegc[12];
   		double burnsoin[12];
   		double burnvegn[12];
   		double burnretainc[12];
   		double burnretainn[12];
	 
};

#endif /*REGNOUTDATA_H_*/
