/*output One Site Env-Module variables */


#ifndef ENVOUTPUTER_H_
#define ENVOUTPUTER_H_
#include <iostream>
#include <netcdfcpp.h>

#include "../data/EnvData.h"
#include "../data/EnvDataDly.h"

#include "../inc/errorcode.h"
#include "../inc/timeconst.h"
#include "../inc/layerconst.h"

using namespace std;

class EnvOutputer{
	public:
		EnvOutputer();
		~EnvOutputer();
				
		void init(string & dirfile);
		void outputCohortEnvVars_dly(const int &ipft, EnvDataDly *envodly, const int&iy, const int&im, const int &id, const int & tstepcnt);
		void outputCohortEnvVars_mly(const int &ipft, snwstate_dim *m_snow, EnvData * envod, const int&iy, const int&im, const int & tstepcnt);
		void outputCohortEnvVars_yly(const int &ipft, snwstate_dim *y_snow, EnvData * envod, const int &iy, const int & tstepcnt);

		string ncfname;

	private :

		NcFile * ncfileenv;

		NcDim * timeD;
		NcDim * pftD;
		NcDim * snwlayerD;
		NcDim * soilayerD;
		NcDim * frontD;

		NcVar* chtidV;
		NcVar* errorV;    //error code
		NcVar* yearV;
		NcVar* monV;
		NcVar* dayV;

	   	NcVar* tairV;
	   	NcVar* co2V;
	   	NcVar* vpV;
	   	NcVar* svpV;
	   	NcVar* vpdV;
	   	NcVar* nirrV;
	   	NcVar* parV;
	   	NcVar* precV;
	   	NcVar* rnflV;
	   	NcVar* snflV;

	   	NcVar* pardownV;
	   	NcVar* parabsorbV;
	   	NcVar* swdownV;
	   	NcVar* swinterV;
	   	NcVar* rinterV;
	   	NcVar* sinterV;
	   	NcVar* eetV;
	   	NcVar* petV;

	   	NcVar* vegwaterV;
	   	NcVar* vegsnowV;
	   	NcVar* vegrcV;
	   	NcVar* vegccV;
	   	NcVar* vegbtranV;
	   	NcVar* vegm_ppfdV;
	   	NcVar* vegm_vpdV;

	   	NcVar* vegswreflV;
	   	NcVar* vegevapV;
	   	NcVar* vegtranV;
	   	NcVar* vegevap_pV;
	   	NcVar* vegtran_pV;
	   	NcVar* vegsublimV;

	   	NcVar* vegswthflV;
	   	NcVar* vegrdripV;
	   	NcVar* vegrthflV;
	   	NcVar* vegsdripV;
	   	NcVar* vegsthflV;

		//snow
		NcVar* snwlnumV;
		NcVar* snwthickV;
		NcVar* snwdenseV;
		NcVar* snwextramassV;
		NcVar* snwdzV;
		NcVar* snwageV;
		NcVar* snwrhoV;
		NcVar* snwporV;

		NcVar* sweV;
	   	NcVar* tsnwV;
	   	NcVar* swesumV;
	   	NcVar* tsnwaveV;
	   	NcVar* snwswreflV;
	   	NcVar* snwsublimV;

	 	//soil
	   	NcVar* soilicesumV;
	   	NcVar* soilliqsumV;
	   	NcVar* soilvwcshlwV;
	   	NcVar* soilvwcdeepV;
	   	NcVar* soilvwcmineaV;
	   	NcVar* soilvwcminebV;
	   	NcVar* soilvwcminecV;

	   	NcVar* soiltaveV;
	   	NcVar* soiltshlwV;
	   	NcVar* soiltdeepV;
	   	NcVar* soiltmineaV;
	   	NcVar* soiltminebV;
	   	NcVar* soiltminecV;

	   	NcVar* soiltsV;
		NcVar* soilliqV;
		NcVar* soiliceV;
		NcVar* soilvwcV;
		NcVar* soillwcV;
		NcVar* soiliwcV;
		NcVar* soilfrontzV;
		NcVar* soilfronttypeV;

		NcVar* soilwatertabV;
		NcVar* permafrostV;
		NcVar* soilaldV;
		NcVar* soilalcV;

		NcVar* soilgrowstartV;
		NcVar* soilgrowendV;
		NcVar* soiltsrtdpV;
		NcVar* soiltsdegdayV;
		NcVar* soilrtthawpctV;

		//
		NcVar* soilswreflV;
		NcVar* soilevapV;
		NcVar* soilevap_pV;

		NcVar* qoverV;
		NcVar* qdrainV;

};


#endif /*SNOWSOILOUTPUER_H_*/
