/*! \file
 * 
 */
#ifndef PARENTLAYER_H_
#define PARENTLAYER_H_

#include "Layer.h"

#include <string>
#include <cmath>
using namespace std;

class ParentLayer:public Layer{
	public:

		ParentLayer(const double & thick);
		~ParentLayer();
		
		double tcsolid;   /*! solid thermal conductivity W/mK*/
		double vhcsolid;  /*! solid volumetric heat capacity*/
		double tcsatfrz;  /*! saturated frozen soil thermal conductivity*/
		double tcsatunf;  /*! saturated unfrozen soil thermal conductivity*/
		
		virtual double getFrzThermCond();// get frozen layer thermal conductivity
		virtual double getUnfThermCond();// get unfrozen layer thermal conductivity
		virtual double getFrzVolHeatCapa();// get frozen layer specific heat capcity
		virtual double getUnfVolHeatCapa();// get unfrozen layer specific heat capacity
		virtual double getMixVolHeatCapa();// get blended layer specific heat capacity
		virtual double getAlbedoVis();// get albedo of visible radition
		virtual double getAlbedoNir();// get albedo of Nir radition
     
		void updateProperty();
    
};
#endif /*ROCKLAYER_H_*/
