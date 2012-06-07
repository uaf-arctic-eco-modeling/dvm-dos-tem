#ifndef RESTARTOUTPUTER_H_
#define RESTARTOUTPUTER_H_

/*! this class is used to output the state in the netcdf format

 */

#include "netcdfcpp.h"

#include <math.h>
#include <iostream>
#include <string>
#include <sstream>
#include <ctime>
#include <cstdlib>
using namespace std;
#include <string>
using std::string;

#include "../data/RestartData.h"

class RestartOutputer {
	public :
		RestartOutputer();
		~RestartOutputer();

		void init(string& dir, string& stage);

		void outputVariables(const int & chtcount);
		void setRestartOutData(RestartData * resodp);
		int errorChecking();

		RestartData * resod;

		string restartfname;

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

		NcVar* ysfV;

	    //veg
		NcVar* numpftV;
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
		NcVar* unnormleafV;

		NcVar* toptAV;
	    NcVar* eetmxAV;
	    NcVar* growingttimeAV;
	    NcVar* unnormleafmxAV;
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

#endif /*RESTARTOUTPUTER_H_*/
