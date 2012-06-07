#ifndef RESTARTINPUTER_H_
#define RESTARTINPUTER_H_

#include "netcdfcpp.h"

#include <iostream>
#include <string>
#include <sstream>
#include <ctime>
#include <cstdlib>
using namespace std;
#include <string>
using std::string;

#include "../inc/layerconst.h"
#include "../inc/timeconst.h"

#include "../data/RestartData.h"

class RestartInputer {
	public :
		RestartInputer();
		~RestartInputer();

		void init(string & dirfile);
		int getRecordId(const int &chtid);
		void getChtId(int & chtid, const int &cid);
		void getErrcode(int & errcode, const int &cid);
		void getRestartData(RestartData *resid, const int &cid);

    private:

		NcFile* restartFile;

   		NcDim * chtD;
   		NcDim * pftD;
   		NcDim * pftpartD;
   		NcDim * rootlayerD;
   		NcDim * snowlayerD;
   		NcDim * soillayerD;
   		NcDim * minelayerD ;
   		NcDim * rocklayerD;
   		NcDim * frontD;
   		NcDim * prvyearD ;
	
		NcVar* chtidV;
		NcVar* errcodeV;

		//atm
		NcVar* dsrV;
		NcVar* firea2sorgnV;

	    //veg
		NcVar* numpftV;
		NcVar* ysfV;
	    NcVar* ifwoodyV;
	    NcVar* ifdeciwoodyV;
	    NcVar* ifperenialV;
	    NcVar* nonvascularV;

	    NcVar* vegageV;
	    NcVar* vegcovV;
	    NcVar* laiV;
	    NcVar* rootfracV;

		NcVar* vegwaterV;
		NcVar* vegsnowV;

		NcVar* vegcV;
		NcVar* labnV;
		NcVar* strnV;
		NcVar* deadcV;
		NcVar* deadnV;

		NcVar* toptAV;
	    NcVar* eetmxAV;
	    NcVar* unnormleafmxAV;
	    NcVar* growingttimeAV;
	    NcVar* prvfoliagemxV;

	    //snow
	    NcVar* numsnwlV;
	    NcVar* snwextramassV;
	    NcVar* DZsnowV;
	    NcVar* TSsnowV;
	    NcVar* LIQsnowV;
	    NcVar* RHOsnowV;
	    NcVar* ICEsnowV;
	    NcVar* AGEsnowV;

	    //ground-soil
	    NcVar* numslV;
	    NcVar* monthsfrozenV;
	    NcVar* watertabV;

	    NcVar* DZsoilV;
	    NcVar* AGEsoilV;
	    NcVar* TYPEsoilV;
	    NcVar* TSsoilV;
	    NcVar* LIQsoilV;
	    NcVar* ICEsoilV;
	    NcVar* FROZENFRACsoilV;
	    NcVar* TEXTUREsoilV;

	    NcVar* TSrockV;
	    NcVar* DZrockV;

	    NcVar* frontZV;
	    NcVar* frontFTV;

	    NcVar* wdebriscV;
	    NcVar* rawcV;
	    NcVar* somaV;
	    NcVar* somprV;
	    NcVar* somcrV;

	    NcVar* wdebrisnV;
	    NcVar* solnV;
	    NcVar* avlnV;

	    NcVar* prvltrfcnV;
   	
};

#endif /*RESTARTINPUTER_H_*/
