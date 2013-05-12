#ifndef VEGETATION_H_
	#define VEGETATION_H_
	#include "../lookup/CohortLookup.h"

	#include "../data/EnvData.h"
	#include "../data/BgcData.h"
	#include "../data/CohortData.h"
	#include "../data/RestartData.h"

	#include "../inc/errorcode.h"
	#include "../inc/parameters.h"

	#include <cmath>

	class Vegetation{
  		public:
   			Vegetation();
   			~Vegetation();
  	
   			vegpar_dim vegdimpar;

   			bool updateLAI5vegc;

   			void initializeParameter();
    		void initializeState();
    		void initializeState5restart(RestartData *resin);
    
    		void updateLai(const int & currmind);
    		void updateFpc();
    		void updateVegcov();
			void updateFrootfrac();

			void phenology(const int &currmind);

			void setCohortLookup(CohortLookup* chtlup);
			void setCohortData(CohortData * cdp);

			void setEnvData(const int &ip, EnvData * edp);
			void setBgcData(const int &ip, BgcData * bdp);

  		private:
  			CohortLookup * chtlu;
  			CohortData * cd;

  			EnvData * ed[NUM_PFT];
  			BgcData * bd[NUM_PFT];

			double getFleaf(const int &ipft, const double & unnormleaf, const double &prvunnormleafmx);
   			double getUnnormleaf(const int& ipft, double &prveetmx, const double & eet, const double & prvunleaf);
			double getFfoliage(const int &ipft, const bool & ifwoody, const bool &ifperenial, const double &vegc);
			double getYearlyMaxLAI(const int &ipft);

	};

#endif /*VEGETATION_H_*/
