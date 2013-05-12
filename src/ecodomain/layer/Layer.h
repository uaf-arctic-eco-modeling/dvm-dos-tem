/*! \file
 * Super class for SoilLayer and SnowLayer
*/

#ifndef LAYER_H_
#define LAYER_H_

#include<string>
#include <iostream>
#include <sstream>
#include <cmath>

using namespace std;

#include "../../inc/errorcode.h"
#include "../../inc/physicalconst.h"
#include "../../inc/layerconst.h"

class Layer {
	public:
		Layer();
		virtual ~Layer();
		enum TYPEKEY {I_SNOW, I_MOSS, I_FIB, I_HUM, I_MINE, I_ROCK, I_UNKNOWN};
		// the texture class - see the 'SoilLookup.cpp'
		enum STKEY {I_SAND, I_LOAMY_SAND,  I_SANDY_LOAM,
	         I_LOAM, I_SILTY_LOAM, I_SANDY_CLAY_LOAM, I_CLAY_LOAM,
	         I_SILTY_CLAY_LOAM, I_SANDY_CLAY, I_SILTY_CLAY, I_CLAY, I_NONE};
	 
		Layer* nextl;   // point to next layer
		Layer* prevl;   // point to previous layer

		TYPEKEY tkey;   // layer type key
	    STKEY stkey;    // soil layer's texture key

	    // layer type controls for processes
		bool isSnow;
		bool isSoil;
		bool isRock;
		bool isMoss;
		bool isMineral;
		bool isOrganic;
	    bool isFibric;
	    bool isHumic;

		int indl;      //! layer index, start from 1
		int solind;    //! soil layer index, start from 1
		double age;    //! age of a layer (year)
		double dz;     //! thickness of layer (unit : \f$ m \f$)
		double z;      //! distance to the ground surface:
	                   // + means below surface, for soil layer
	                   // - means above surface, for snow layer

		double rho;     //! density of this layer (unit : \f$ kg m^{-3} \f$)
		double bulkden; //! bulk density: the kg solid/ volume of whole layer
		double poro;    //! porosity

		double tcmin;   // minimum thermal conductivity, to consider the effect of air and water convection
		double tcdry;   //! dry matter thermal conductivity W/mK
		double tcsolid; //! solid thermal conductivity W/mK
		double tcsatfrz;//! saturated frozen soil thermal conductivity
		double tcsatunf;//! saturated unfrozen soil thermal conductivity
		double vhcsolid;//! solid volumetric heat capacity

		double albdryvis;  //visiable light albedo at dry
		double albdrynir;  //nir light albedo at dry
		double albsatvis;  //visiable light albedo at saturation
		double albsatnir;  //nir light albedo at saturation

		double minliq; // minimum liq water content
		double maxliq; // maximum liq water content
		double maxice; // maximum ice content

		double psisat; // saturated matric potential
		double hksat;  // saturated matric potential
		double bsw;    // Clap and Hornberger consant

		// thermal status
		int frozen;        // thermal state of a layer, 0: partially frozen, 1: frozen, -1: unfrozen
		double frozenfrac; // frozen fraction of a layer (0 - 1)
		double tem;        // temperature (oC)
		double tcond;      // thermal conductivity
		double pce_t;      // phase-change energy for thawing
		double pce_f;      // phase-change energy for freezing

		// hydrological status
		double liq;   //!liquid water kg/m2
		double ice;   //!ice content kg/m2
		double hcond;  // hydraulic conductivity

		//! soil carbon pool unit : \{kgC}{m^2
		double rawc;
		double soma;
		double sompr;
		double somcr;

		// misc.
		double cfrac; //fraction of carbon, relative to total SOM weight (mass) - not used but should be useful in future

		void advanceOneDay();
		double getHeatCapacity();
		double getThermalConductivity();
		double getVolWater();  //!get volumetric soil water content
		double getEffVolWater();
		double getVolLiq();
		double getEffVolLiq();
		double getVolIce();

		virtual double getFrzThermCond()=0;     // get frozen layer thermal conductivity
		virtual double getUnfThermCond()=0;     // get unfrozen layer thermal conductivity
		virtual double getFrzVolHeatCapa()=0;   // get frozen layer specific heat capcity
		virtual double getUnfVolHeatCapa()=0;   // get unfrozen layer specific heat capacity
		virtual double getMixVolHeatCapa()=0;   //Yuan

	private:
	
};
#endif //LAYER_H_
