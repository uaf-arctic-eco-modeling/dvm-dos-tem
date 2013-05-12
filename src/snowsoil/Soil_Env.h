#ifndef SOIL_ENV_H_
#define SOIL_ENV_H_

#include "Stefan.h"  
#include "Richards.h"
#include "TemperatureUpdator.h"

#include "../data/CohortData.h"
#include "../data/EnvData.h"
#include "../data/FirData.h"
#include "../data/RestartData.h"

#include "../inc/errorcode.h"
#include "../inc/parameters.h"
#include "../inc/layerconst.h"
#include "../lookup/CohortLookup.h"

#include "../ecodomain/Ground.h"

class Soil_Env{
	public:

		Soil_Env();
		~Soil_Env();

		soipar_env envpar;
	
		Richards richards;
		Stefan stefan;
		TemperatureUpdator tempupdator;

		void setGround(Ground* grndp);
		void setCohortData(CohortData* cdp);
		void setEnvData(EnvData* edp);
		void setCohortLookup(CohortLookup * chtlup);

		void resetDiagnostic();   /*! reset diagnostic variables to initial values */

		void initializeParameter();
		void initializeState();
		void initializeState5restart(RestartData* resin);

		void updateDailyGroundT(const double & tdrv, const double & dayl);
      	void updateDailySM();

      	void getSoilTransFactor(double btran[MAX_SOI_LAY], Layer* fstsoill, const double vrootfr[MAX_SOI_LAY]);

		void retrieveDailyTM(Layer* toplayer, Layer* lstsoill);

	private:

		 Ground * ground;
		 CohortData * cd;
		 EnvData * ed;
		 CohortLookup* chtlu;
  
		 void updateDailySurfFlux(Layer* frontl, const double & dayl);
		 void updateDailySoilThermal4Growth(Layer* fstsoill, const double &tsurface);
		 void updateLayerStateAfterThermal(Layer* fstsoill, Layer *lstsoill, Layer* botlayer);

		 void retrieveDailyFronts();

		 double getEvaporation(const double & dayl, const double &rad);
		 double getPenMonET(const double & ta, const double& vpd, const double &irad,
				const double &rv, const double & rh);
		 double getWaterTable(Layer* fstsoil);
		 double getRunoff(Layer* fstsoill, Layer* drainl, const double & rnth, const double & melt);

		 // the following codes not used anymore
		 double getInflFrozen(Layer *fstminl, const double &  rnth, const double & melt);
		 double updateLayerTemp5Lat(Layer* currl, const double & infil);

};

#endif /*SOIL_ENV_H_*/
