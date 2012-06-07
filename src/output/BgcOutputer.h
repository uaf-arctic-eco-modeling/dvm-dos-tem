/*output One Site Bgc-Module variables */


#ifndef BGCOUTPUTER_H_
#define BGCOUTPUTER_H_
#include <iostream>
#include "netcdfcpp.h"

#include "../inc/timeconst.h"
#include "../inc/cohortconst.h"
#include "../inc/layerconst.h"
#include "../inc/ErrorCode.h"

#include "../data/BgcData.h"

using namespace std;

class BgcOutputer{
	public:
		BgcOutputer();
		~BgcOutputer();
				
		void init(string & dirfile);
		void outputCohortBgcVars_mly(BgcData *bgcod, const int & calyr, const int &calmon, const int &ipft, const int & recordcnt);
		void outputCohortBgcVars_yly(BgcData *bgcod, const int & calyr, const int &ipft, const int & recordcnt);

		string ncfname;

	private :

		NcFile * ncfileenv;

		NcDim * timeD;
		NcDim * pftD;
		NcDim * partD;
		NcDim * soilayerD;

		NcVar* chtidV;
		NcVar* errorV;    //error code
		NcVar* yearV;
		NcVar* monV;

	   	NcVar* callV;
	   	NcVar* cV;
	   	NcVar* nallV;
	   	NcVar* labnV;
	   	NcVar* strnallV;
	   	NcVar* strnV;
	   	NcVar* deadcV;
	   	NcVar* deadnV;
	   	NcVar* wdebriscV;
	   	NcVar* wdebrisnV;

	   	NcVar* rawcV;
	   	NcVar* somaV;
	   	NcVar* somprV;
	   	NcVar* somcrV;
	   	NcVar* orgnV;
	   	NcVar* avlnV;

	   	NcVar* shlwcV;
	   	NcVar* deepcV;
	   	NcVar* mineacV;
	   	NcVar* minebcV;
	   	NcVar* mineccV;
	   	NcVar* rawcsumV;
	   	NcVar* somasumV;
	   	NcVar* somprsumV;
	   	NcVar* somcrsumV;
	   	NcVar* orgnsumV;
	   	NcVar* avlnsumV;

	   	NcVar* gppftV;
	   	NcVar* raq10V;
	   	NcVar* rmkrV;
	   	NcVar* gvV;
	   	NcVar* fnaV;
	   	NcVar* fcaV;

	   	NcVar* knmoistV;
	   	NcVar* rhmoistV;
	   	NcVar* rhq10V;
	   	NcVar* soilltrfcnV;

	   	// C fluxes
	   	NcVar* nepV;

  		NcVar* ingppallV;  // gpp not limited by nitrogen availability
  		NcVar* ingppV;
  		NcVar* innppallV;
  		NcVar* innppV;

  		NcVar* gppallV;
  		NcVar* gppV;
  		NcVar* nppallV;
  		NcVar* nppV;

  		NcVar* rmallV; // maintainance respiration
 		NcVar* rmV;
 		NcVar* rgallV;  // growth respirationV;
 		NcVar* rgV;
  		NcVar* ltrfalcallV;
 		NcVar* ltrfalcV;

  		// N fluxes
  		NcVar* ltrfalnallV;
  		NcVar* ltrfalnV;
  		NcVar* innuptakeV;
  		NcVar* nrootextractV;
   		NcVar* luptakeV;
 		NcVar* suptakeallV;
 		NcVar* suptakeV;
  		NcVar* nmobilallV;      //N allocation from labile-N pool to tissue pool when needed
  		NcVar* nmobilV;

  		NcVar* nresorballV;     //N resorbation into labile-N pool when litter-falling
  		NcVar* nresorbV;

  		//
  		NcVar* doclostV;      //DOC lost
 		NcVar* avlnlostV;     // N leaching
 		NcVar* orgnlostV;     // N loss with DOC

};


#endif /*BGCOUTPUER_H_*/
