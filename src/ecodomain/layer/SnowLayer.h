/*! \file
 *
 */
#ifndef SNOWLAYER_H_
#define SNOWLAYER_H_
#include "../layer/Layer.h"
#include "../../inc/physicalconst.h"
#include "../../inc/parameters.h"

#include <string>
#include <cmath>
using namespace std;

class SnowLayer: public Layer{
	public:
		SnowLayer();
		~SnowLayer();

		void clone(SnowLayer* sl); /*assign same member to another layer*/

		void updateThick();
		void updateDensity(snwpar_dim *snwpar);
    
		virtual double getFrzThermCond(); // get frozen layer thermal conductivity
		virtual double getUnfThermCond();// get unfrozen layer thermal conductivity

		virtual double getFrzVolHeatCapa();// get frozen layer specific heat capcity
		virtual double getUnfVolHeatCapa();// get unfrozen layer specific heat capacity

		virtual double getMixVolHeatCapa();  //Yuan:

	private:

	   double getThermCond5Sturm();
	   double getThermCond5Jordan();
	    
};
#endif /*SNOWLAYER_H_*/
