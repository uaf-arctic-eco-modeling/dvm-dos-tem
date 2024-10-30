/*! \file
 * Super class for SoilLayer and SnowLayer
*/
#ifndef LAYER_H_
#define LAYER_H_

#include <string>
#include <iostream>
#include <sstream>
#include <cmath>

using namespace std;

#include "errorcode.h"
#include "physicalconst.h"
#include "layerconst.h"

class Layer {
private:

public:
  Layer();
  virtual ~Layer();
  enum TYPEKEY {I_SNOW, I_MOSS, I_FIB, I_HUM, I_MINE, I_ROCK, I_UNKNOWN};

  Layer* nextl;   // point to next layer
  Layer* prevl;   // point to previous layer

  TYPEKEY tkey;   // layer type key

  // layer type controls for processes
  bool isSnow;
  bool isSoil;
  bool isRock;
  bool isMoss;
  bool isMineral;
  bool isOrganic;
  bool isFibric;
  bool isHumic;

  int indl;      ///< layer index, start from 1
  int solind;    ///< soil layer index, start from 1
  double age;    ///< age of a layer (year)
  double dz;     ///< thickness of layer (unit : \f$ m \f$)
  double z;      ///< distance to the ground surface:
  // + means below surface, for soil layer
  // - means above surface, for snow layer

  double rho;     //< density of this layer (unit : \f$ kg m^{-3} \f$)
  double bulkden; //< bulk density: the kg solid/ volume of whole layer
  double poro;    //< porosity

  double tcmin;    //< minimum thermal conductivity, to consider the effect of air and water convection
  double tcdry;    //< dry matter thermal conductivity W/mK
  double tcsolid;  //< solid thermal conductivity W/mK
  double tcsatfrz; //< saturated frozen soil thermal conductivity
  double tcsatunf; //< saturated unfrozen soil thermal conductivity
  double vhcsolid; //< solid volumetric heat capacity

  double albdryvis;  //< visible light albedo at dry
  double albdrynir;  //< nir light albedo at dry
  double albsatvis;  //< visible light albedo at saturation
  double albsatnir;  //< nir light albedo at saturation

  double minliq; //< minimum liq water content
  double maxliq; //< maximum liq water content
  double maxice; //< maximum ice content

  double psisat; //< saturated matric potential
  double hksat;  //< saturated matric potential
  double bsw;    //< Clap and Hornberger constant

  double temp_dep;
  double b_parameter;

  // thermal status
  int frozen;        //< thermal state of a layer, 0: partially frozen, 1: frozen, -1: unfrozen
  double frozenfrac; //< frozen fraction of a layer (0 - 1)
  double tem;        //< temperature (oC)
  double tcond;      //< thermal conductivity
  double hcapa;      //< heat capacity
  double pce_t;      //< phase-change energy for thawing
  double pce_f;      //< phase-change energy for freezing

  // hydrological status
  double liq;    //< liquid water kg/m2
  double ice;    //< ice content kg/m2
  double hcond;  //< hydraulic conductivity

  // soil carbon pool unit : gC/m^2
  double rawc;
  double soma;
  double sompr;
  double somcr;

  double orgn;
  double avln;

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

  // first unfrozen water / apparent heat capacity functions
  double getUnfVolLiq();
  double getDeltaUnfVolLiq();

  // functions based on Nicolsky et al. 2007 and GIPL2.0
  double funf_water(double const & Temperature);    // unfrozen water
  double fdunf_water(double const & Temperature);   // unfrozen water derivative with respect to temperature
  double fhcap(const double &T1, const double &T2); // phase change component of apparent heat capacity
  double fapp_hcap();                               // apparent heat capacity


  virtual double getFrzThermCond()=0; // get frozen layer thermal conductivity
  virtual double getUnfThermCond()=0; // get unfrozen layer thermal conductivity
  virtual double getMixThermCond()=0;
  virtual double getFrzVolHeatCapa()=0;// get frozen layer specific heat capcity
  virtual double getUnfVolHeatCapa()=0;// get unfrozen layer specific heat capacity
  virtual double getMixVolHeatCapa()=0;//Yuan

};
#endif //LAYER_H_
