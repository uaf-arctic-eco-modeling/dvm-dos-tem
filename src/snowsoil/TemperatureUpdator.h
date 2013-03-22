/*
 * TemperatureUpdator.h
 *
 *  Created on: 2011-8-18
 *      Author: yis
 */

#ifndef TEMPERATUREUPDATOR_H_
#define TEMPERATUREUPDATOR_H_

#include <cmath>

#include "../ecodomain/Ground.h"
#include "../ecodomain/layer/Layer.h"
#include "../ecodomain/layer/SnowLayer.h"
#include "../ecodomain/layer/SoilLayer.h"

#include "../inc/physicalconst.h"
#include "../inc/errorcode.h"
#include "../inc/layerconst.h"

#include "../data/EnvData.h"
#include "../util/CrankNicholson.h"

class TemperatureUpdator{
	public:
	 	 TemperatureUpdator();
	 	 ~TemperatureUpdator();

	 	 bool debugging;

	 	 int itsumall;

	 	 //update temperatures for valid layers
	 	 void updateTemps(const double & tdrv, Layer *frontl, Layer *backl,
			  Layer *fstsoill, Layer* fstfntl, Layer*lstfntl,
			  const double & timestep, const bool & meltsnow);

	 	 //update temperatures for invalid layers
	 	 void  interpolate4Invalid(Layer* frontl, const double& tdrv);

	 	 //adjust temperatures based on the frozen state of layer
	 	 void adjustTempsWithFrozenState(Layer* frontl);

	 	 void  setGround(Ground* groundp);

	private:

	 	 double zerodegc;
	 	 double mindzlay;
	     double timestep;

	     // for updating temperatures
	     double s[MAX_GRN_LAY+2];
	     double e[MAX_GRN_LAY+2];
	     double cn[MAX_GRN_LAY+2];
	     double cap[MAX_GRN_LAY+2];
	     double tca[MAX_GRN_LAY+2];
	     double hca[MAX_GRN_LAY+2];

	     double t[MAX_GRN_LAY+2];
	     double dx[MAX_GRN_LAY+2];

	     double tld[MAX_GRN_LAY+2];
	     double tid[MAX_GRN_LAY+2];
	     double tis[MAX_GRN_LAY+2];
	     double tii[MAX_GRN_LAY+2];
	     double tit[MAX_GRN_LAY+2];
	     int type[MAX_GRN_LAY+2];


	     double ttole;   /*! tolerance of difference*/

         double tleft;  /*! the amount of time left for update (day)*/
         double tmld;  /*!the last determined time, short for time-last-determined*/
         bool upperTemps5FrontUpdated;/*! whether the time step has been changed for last factional time step */

         int itsum;
         int itsumabv;
         int itsumblw;
         double tstep;

         bool tschanged;

         double TSTEPMAX;
         double TSTEPMIN;
         double TSTEPORG;		/* the original time step*/

	     CrankNicholson cns;
         Ground *ground;

	 	 void processColumnNofront(Layer* frontl, Layer *backl, const double & tdrv, const bool & meltsnow);

	 	 void processAboveFronts(Layer* frontl, Layer*fstfntl, const double & tdrv, const bool & meltsnow, const bool &usefntl);
	 	 void processBelowFronts(Layer *backl, Layer*lstfntl, const bool &adjfntl, const bool &usefntl);
	 	 void processBetweenFronts(Layer*fstfntl, Layer*lstfntl, const bool &adjfntl, const bool &usefntl);

	 	 void iterate(const int &startind, const int &endind);
	 	 int updateOneTimeStep(const int &startind, const int & endind);
	 	 int updateOneIteration(const int &startind, const int & endind);


};

#endif /* TEMPERATUREUPDATOR_H_ */
