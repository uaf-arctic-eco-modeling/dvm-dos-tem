#ifndef VEGETATION_BGC_H_
	#define VEGETATION_BGC_H_
	#include "../lookup/CohortLookup.h"
	#include "../runmodule/ModelData.h"

	#include "../data/CohortData.h"
	#include "../data/EnvData.h"
	#include "../data/FirData.h"
	#include "../data/BgcData.h"
	#include "../data/RestartData.h"

	#include "../inc/parameters.h"

	#include "../snowsoil/Soil_Bgc.h"

	#include "../ecodomain/Vegetation.h"

	#include <cmath>

	class Vegetation_Bgc{
  		public:
   			Vegetation_Bgc();
   			~Vegetation_Bgc();
  	
  			int ipft;
    		bool nfeed;

 			vegpar_cal calpar;
			vegpar_bgc bgcpar;

 			vegstate_bgc tmp_vegs;

			atm2veg_bgc del_a2v;
			veg2atm_bgc del_v2a;
			veg2soi_bgc del_v2soi;
			soi2veg_bgc del_soi2v;
			veg2veg_bgc del_v2v;
			vegstate_bgc del_vegs;

   			void initializeParameter();
    		void initializeState();
    		void initializeState5restart(RestartData *resin);
    
			void prepareIntegration(const bool &nfeedback);
  			void delta();
  			void deltanfeed();
  			void deltastate();
			void afterIntegration();

			void adapt();

			void setCohortLookup(CohortLookup* chtlup);

			void setCohortData(CohortData* cdp);
			void setEnvData(EnvData* edp);
   			void setBgcData(BgcData* bdp);

  		private:

			double fracnuptake[MAX_SOI_LAY];  //fraction of N extraction in each soil layer for current PFT
			double fltrfall;                  //season fraction of max. monthly litterfalling fraction
			double dleafc;                    // C requirement of foliage growth at current timestep
		    double d2wdebrisc;
		    double d2wdebrisn;

  			CohortLookup * chtlu;

  			CohortData * cd;
    		EnvData * ed;
   			BgcData * bd;

   			void updateCNeven(const double & yreet,const double & yrpet, const double & initco2,const double & currentco2 );

 			double getGPP(const double &co2, const double & par,
 					      const double &leaf, const double & foliage,
                          const double &ftemp, const double & gv);
			double getTempFactor4GPP(const double & tair, const double & tgppopt);
			double getGV(const double & eet,const double & pet );

			double getRm(const double & vegc,const double & raq10, const double &kr);
 			double getRaq10(const double & tair); /*!  rq10: effect of temperature on plant respiration, updated every month */
			double getKr(const double & vegc, const int & ipart); /*! kr: for calculating plant maintanence respiration*/

    	  	double getNuptake(const double & foliage, const double & raq10, const double & kn1, const double & nmax);

	};

#endif /*VEGETATION_BGC_H_*/
