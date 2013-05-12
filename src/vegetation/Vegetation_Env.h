#ifndef VEGETATION_ENV_H_
#define VEGETATION_ENV_H_
#include <cmath>

#include "../lookup/CohortLookup.h"
#include "../inc/states.h"
#include "../inc/fluxes.h"
#include "../inc/diagnostics.h"
#include "../inc/parameters.h"

#include "../data/CohortData.h"
#include "../data/EnvData.h"
#include "../data/FirData.h"
#include "../data/RestartData.h"

class Vegetation_Env{
	  public:

		Vegetation_Env();
		~Vegetation_Env();

		int ipft;

		vegpar_env envpar;
	
		void setCohortLookup(CohortLookup * chtlup);
		void setCohortData(CohortData* cdp);
		void setEnvData(EnvData* edatap);
		void setFirData(FirData* fdp);
    
		void initializeParameter();
		void initializeState();
		void initializeState5restart(RestartData* resin);
     
		void updateRadiation();
		void updateWaterBalance(const double & daylhr);

   private:

		CohortData * cd;
		EnvData * ed;
		FirData * fd;
		CohortLookup * chtlu;

		//function
		double getRainInterception(const double & rain, const double & lai);
		double getSnowInterception(const double & snow, const double & lai);
		double getLeafStomaCond(const double & ta, const double &  parin,
		        const double & vpdin, const double& btran,
		        double & m_ppfd, double & m_vpd );
		double getCanopySubl(const double & rac, const double & sinter, const double & lai );
   
		double getPenMonET(const double & ta, const double& vpd, const double &irad,
				const double &rv, const double & rh);
   
   
};
#endif /*VEGETATION_ENV_H_*/
