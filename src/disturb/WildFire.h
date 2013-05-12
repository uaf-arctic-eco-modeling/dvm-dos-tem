#ifndef WILDFIRE_H_
#define WILDFIRE_H_

#include <cmath>
#include <math.h>
#include <vector>
#include <algorithm>
using namespace std;

#include "../data/CohortData.h"
#include "../data/EnvData.h"
#include "../data/FirData.h"
#include "../data/BgcData.h"
#include "../data/RestartData.h"

#include "../inc/errorcode.h"
#include "../inc/timeconst.h"
#include "../inc/parameters.h"

#include "../lookup/CohortLookup.h"

class WildFire{
	public:
		WildFire();
		~WildFire();

    	int firstfireyr;

    	int oneyear;
     	int onemonth;
     	int oneseverity;  //Yuan: fire severity category

     	int oneseason;
    	int onesize;

     	void setCohortData(CohortData* cdp);
     	void setAllEnvBgcData(EnvData* edp, BgcData* bdp);
     	void setBgcData(BgcData* bdp, const int &ip);
     	void setFirData(FirData* fdp);
    	void setCohortLookup(CohortLookup* chtlup);
    
    	void initializeParameter();
    	void initializeState(); 
    	void initializeState5restart(RestartData *resin);
    	void prepareDrivingData();
    	
		int getOccur(const int & yrind, const bool & fridrived);  	//Yuan: modified;
		void burn();  	//Yuan: modified

	private:

     	firepar_bgc firpar;

     	double r_live_cn; //ratio of living veg. after burning
     	double r_dead2ag_cn; //ratio of dead veg. after burning
     	double r_burn2ag_cn; //burned above-ground veg. after burning

//Yuan: the following if using years will result in huge memory needs, if spin-up is long
		int fyear[MAX_FIR_OCRNUM];
		int fseason[MAX_FIR_OCRNUM];
		int fmonth[MAX_FIR_OCRNUM];
		int fsize[MAX_FIR_OCRNUM];
		int fseverity[MAX_FIR_OCRNUM];

     	CohortLookup * chtlu;
    	CohortData * cd;

    	FirData * fd;
   	 	EnvData * edall;
   	 	BgcData * bd[NUM_PFT];
   	 	BgcData * bdall;

    	void deriveFireSeverity();
    	double getBurnOrgSoilthick();
    	void getBurnAbgVegetation(const int &ip);

};

#endif /*WILDFIRE_H_*/
