/*! \file
 * 
 */
#ifndef SOILLAYER_H_
#define SOILLAYER_H_
#include "Layer.h"

#include "../../lookup/SoilLookup.h"

#include <math.h>
#include <cmath>
#include <memory>
using namespace std;

class SoilLayer:public Layer{
	public:

		SoilLayer();
		virtual ~SoilLayer();

	    virtual double getFrzThermCond();// get frozen layer thermal conductivity
		virtual double getUnfThermCond();// get unfrozen layer thermal conductivity
		virtual double getFrzVolHeatCapa();// get frozen layer specific heat capcity
		virtual double getUnfVolHeatCapa();// get unfrozen layer specific heat capacity
    	virtual double getMixVolHeatCapa();   //Yuan: all soil components

	    double getAlbedoVis();// get albedo of visible radition
	    double getAlbedoNir();// get albedo of Nir radition

        void derivePhysicalProperty();

        double getMatricPotential();
        double getHydraulicCond();

};
#endif /*SOILLAYER_H_*/
