#ifndef OUTRETRIVE_H_
	#define OUTRETRIVE_H_

    #include "Timer.h"
	#include "ModelData.h"

	#include "../data/EnvData.h"
	#include "../data/BgcData.h"
	#include "../data/FirData.h"

    #include "../data/RestartData.h"

    #include "../data/OutDataRegn.h"
    #include "../data/EnvDataDly.h"

	class OutRetrive{
		public :
			OutRetrive();
			~OutRetrive();

			int cohortcount;

	    	EnvDataDly envoddly[NUM_PFT][31];
	    	EnvDataDly envoddlyall[31];

	    	OutDataRegn * regnod;

	    	RestartData * resod;

	    	//
	    	void setDimensionData(CohortData *cdp);
	    	void setProcessData(const int &ip, EnvData *edp, BgcData *bdp);
	    	void setFireData(FirData *fdp);

	    	//
	    	void setRegnOutData(OutDataRegn * regnodp);
	    	void setRestartOutData(RestartData *resodp);

	    	//
	    	void assignSiteDlyOutputBuffer_Env(snwstate_dim d_snow, const int &ipft, const int &iday);

	    	void updateRegnOutputBuffer(const int &im);

	    	void updateRestartOutputBuffer();

	    private:
	    	//
	    	CohortData *cd;
	    	EnvData *edall;
	    	BgcData *bdall;
	    	EnvData *ed[NUM_PFT];
	    	BgcData *bd[NUM_PFT];
	    	FirData *fd;

};
#endif /*COHORT_H_*/
