/*output One Site Bgc-Module variables */


#ifndef BGCOUTPUTER_H_
#define BGCOUTPUTER_H_
#include <iostream>
#include <netcdfcpp.h>

#include "../inc/timeconst.h"
#include "../inc/cohortconst.h"
#include "../inc/layerconst.h"
#include "../inc/errorcode.h"

#include "../data/BgcData.h"
#include "../data/FirData.h"

using namespace std;

class BgcOutputer{
	public:
		BgcOutputer();
		~BgcOutputer();
				
		void init(string & dirfile);
		void outputCohortBgcVars_mly(const int &ipft, BgcData *bgcod, FirData *fod, const int & calyr, const int & calmon, const int & recordcnt);
		void outputCohortBgcVars_yly(const int &ipft, BgcData *bgcod, FirData *fod, const int & calyr, const int & recordcnt);

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

		// vegetation stats/fluxes
	   	NcVar* callV;
	   	NcVar* cV;
	   	NcVar* nallV;
	   	NcVar* labnV;
	   	NcVar* strnallV;
	   	NcVar* strnV;
	   	NcVar* deadcV;
	   	NcVar* deadnV;

	   	NcVar* gppftV;
	   	NcVar* gppgvV;
	   	NcVar* gppfnaV;
	   	NcVar* gppfcaV;
	   	NcVar* rmkrV;
	   	NcVar* raq10V;

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

  		NcVar* ltrfalnallV;
  		NcVar* ltrfalnV;
  		NcVar* innuptakeV;
   		NcVar* luptakeV;
 		NcVar* suptakeallV;
 		NcVar* suptakeV;
  		NcVar* nmobilallV;      //N allocation from labile-N pool to tissue pool when needed
  		NcVar* nmobilV;

  		NcVar* nresorballV;     //N resorbation into labile-N pool when litter-falling
  		NcVar* nresorbV;

  		NcVar* nrootextractV;

  		// ground-soil states/fluxes
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

	   	NcVar* rhV;
	   	NcVar* rhmoistV;
	   	NcVar* rhq10V;
	   	NcVar* soilltrfcnV;

	   	NcVar* grsnminV;
	   	NcVar* netnminV;
	   	NcVar* knmoistV;

	   	NcVar* nepV;

	   	NcVar* orgcinputV;     // org. C inputs
 		NcVar* orgninputV;     // org. N inputs
 		NcVar* avlninputV;     // inorg. N inputs (deposition+fertilization)

 		NcVar* doclostV;      // DOC lost
 		NcVar* avlnlostV;     // N leaching
 		NcVar* orgnlostV;     // N loss with DOC

   		// fire disturbance caused C/N in/out
   		NcVar* burnthickV;
   		NcVar* burnsoicV;
   		NcVar* burnvegcV;
   		NcVar* burnsoinV;
   		NcVar* burnvegnV;
   		NcVar* burnretaincV;
   		NcVar* burnretainnV;


};


#endif /*BGCOUTPUER_H_*/
