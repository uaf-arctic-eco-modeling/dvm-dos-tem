#ifndef COHORT_H_
	#define COHORT_H_

	#include "../ecodomain/Ground.h"
	#include "../ecodomain/Vegetation.h"

	#include "../atmosphere/Atmosphere.h"

	#include "../vegetation/Vegetation_Env.h"
	#include "../vegetation/Vegetation_Bgc.h"

	#include "../snowsoil/Snow_Env.h"
	#include "../snowsoil/Soil_Env.h"
	#include "../snowsoil/SoilParent_Env.h"
	#include "../snowsoil/Soil_Bgc.h"

	#include "../disturb/WildFire.h"

	#include "../data/RegionData.h"
	#include "../data/GridData.h"
	#include "../data/CohortData.h"

	#include "../data/EnvData.h"
	#include "../data/BgcData.h"
	#include "../data/FirData.h"

	#include "../data/RestartData.h"

	#include "../lookup/CohortLookup.h"

	#include "Integrator.h"

// headers for run
	#include "Timer.h"
	#include "ModelData.h"
	#include "OutRetrive.h"

	class Cohort{
		public :
			Cohort();
			~Cohort();
	
	        // model running status
			int errorid;
			bool failed;    // when an exception is caught, set failed to be true
	
 			//
 			Timer * timer;

 			//inputs
			CohortLookup chtlu;

			// domain
            Atmosphere atm;
            Vegetation veg;
            Ground ground;

            // processes
            Vegetation_Env vegenv[NUM_PFT];
            Snow_Env snowenv;
            Soil_Env soilenv;
            SoilParent_Env solprntenv;

            Vegetation_Bgc vegbgc[NUM_PFT];
            Soil_Bgc soilbgc;

            WildFire fire;

            // output
            OutRetrive outbuffer;

		// data
            EnvData ed[NUM_PFT];
            BgcData bd[NUM_PFT];
            EnvData * edall;
            BgcData * bdall;

            FirData * fd;   // this for all PFTs and their soil
    
            ModelData * md;
            RegionData * rd;
            GridData * gd;

            CohortData cd;
            RestartData resid;    //for input

 		    void initSubmodules();
 		    void setTime(Timer * timerp);

 		    void setModelData(ModelData* md);
 		    void setInputData(RegionData * rd, GridData * gd);
 		    void setProcessData(EnvData * alledp, BgcData * allbdp, FirData *fdp);

 		    void initStatePar();
 		    void prepareAllDrivingData();
 	        void prepareDayDrivingData(const int & yrcnt, const int &usedatmyr);
 		    void updateMonthly(const int & yrcnt, const int & currmind, const int & dinmcurr);

	private:

            Integrator vegintegrator[NUM_PFT];
            Integrator solintegrator;


     	    void updateMonthly_DIMveg(const int & currmind, const bool & dvmmodule);
     	    void updateMonthly_DIMgrd(const int & currmind, const bool & dslmodule);

     	    void updateMonthly_Env(const int & currmind, const int & dinmcurr);
 	 	    void updateMonthly_Bgc(const int & currmind);
     	    void updateMonthly_Fir(const int & yrcnt, const int & currmind);

		    // update root distribution
		    void getSoilFineRootFrac_Monthly();
		    double assignSoilLayerRootFrac(const double & topz, const double & botz,
		           const double csumrootfrac[MAX_ROT_LAY], const double dzrotlay[MAX_ROT_LAY]);

		   //
     	   void assignAtmEd2pfts_daily();
     	   void assignGroundEd2pfts_daily();
		   void getSoilTransfactor4all_daily();
		   void getEd4allveg_daily();
     	   void getEd4land_daily();

     	   void assignSoilBd2pfts_monthly();
     	   void getBd4allveg_monthly();

};
#endif /*COHORT_H_*/
