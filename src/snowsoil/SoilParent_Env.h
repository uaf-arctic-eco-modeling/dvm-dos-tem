#ifndef SOILPARENT_ENV_H_
#define SOILPARENT_ENV_H_

#include "../data/EnvData.h"
#include "../data/RestartData.h"

#include "../ecodomain/Ground.h"

class SoilParent_Env{
	public:
		SoilParent_Env();

		void initializeState();
		void initializeState5restart(RestartData* resin);

		void retrieveDailyTM(Layer* lstsoill);
	
		void  setEnvData(EnvData* ed);
		void  setGround(Ground* ground);

	private:
		Ground *ground;
		EnvData *ed;

};

#endif /*SOILPARENT_ENV_H_*/
