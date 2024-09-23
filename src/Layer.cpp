/*! \file
 *
 */
#include "../include/Layer.h"

#include "../include/TEMLogger.h"
extern src::severity_logger< severity_level > glg;

Layer::Layer() {
  BOOST_LOG_SEV(glg, debug) << "Creating a (generic) layer object...";
  nextl= NULL;
  prevl= NULL;
  isSnow = false;
  isSoil = false;
  isRock = false;
  isMoss    = false;
  isMineral = false;
  isOrganic = false;
  isFibric = false;
  isHumic  = false;
  tkey  = I_UNKNOWN;
  indl  = MISSING_I;
  solind= MISSING_I;
  age   = 0.;
  dz    = MISSING_D;
  z     = MISSING_D;
  rho= MISSING_D;
  bulkden= MISSING_D;
  poro= MISSING_D;
  tcmin= MISSING_D;
  tcdry= MISSING_D;
  tcsolid= MISSING_D;
  tcsatfrz= MISSING_D;
  tcsatunf= MISSING_D;
  vhcsolid= MISSING_D;
  albdryvis= MISSING_D;
  albdrynir= MISSING_D;
  albsatvis= MISSING_D;
  albsatnir= MISSING_D;
  maxliq  = MISSING_D;
  maxice  = MISSING_D;
  psisat= MISSING_D;
  hksat = MISSING_D;
  bsw   = MISSING_D;
  // thermal status
  frozen    = MISSING_I;
  frozenfrac= MISSING_D;
  tem  = MISSING_D;
  tcond= MISSING_D;
  pce_t= MISSING_D;
  pce_f= MISSING_D;
  // hydrological status
  liq  = MISSING_D;
  ice  = MISSING_D;
  hcond= MISSING_D;
  // soil carbon pool
  rawc = MISSING_D;
  soma = MISSING_D;
  sompr= MISSING_D;
  somcr= MISSING_D;
  cfrac= MISSING_D;
};

Layer::~Layer() {
  BOOST_LOG_SEV(glg, debug) << "Deleting a (generic) layer object...";
};

void Layer::advanceOneDay() {
  age+=1/365.;
};

double Layer::getHeatCapacity() { // volumetric heat capacity
  double hcap = MISSING_D;

  if(isSoil) {
    if(tem>=0) {
      hcap = getUnfVolHeatCapa();
    } else {
      hcap = getMixVolHeatCapa();
    }
  } else if(isSnow) {
    hcap = getFrzVolHeatCapa();
  } else if(isRock) {
    hcap = getFrzVolHeatCapa();
  }

  return hcap;
};

double Layer::getThermalConductivity() {
  double tc = MISSING_D;

  if(isSoil) {
    if(tem>=0){
      tc = getUnfThermCond();
    } else {
      tc = getMixThermCond();
    }
  } else if (isSnow){
    tc = getFrzThermCond();
  } else if (isRock) {
    tc = getFrzThermCond();
  }

  this->tcond = tc;
  return tc;
};

double Layer::getUnfVolLiq(){

  double T_, b, uwc;

  if (isMoss){
    T_ = -0.01;
    b = 0.8;
  } else if (isFibric){
    T_ = -0.03;
    b = 0.5;
  } else if (isHumic){
    T_ = -0.03;
    b = 0.5;
  } else {
    T_ = -0.04;
    b = 0.5;
  }

  if (tem < T_){
    uwc = poro * pow(abs(T_), b) * pow(abs(tem), -b);
  } else{
    uwc = 0.0;
  }

  uwc = fmin(uwc, 1.0);

  if (isSnow){
    uwc = 0.0;
  }

  return uwc;
}

double Layer::getDeltaUnfVolLiq(){

  double T_, b, d_uwc;

  if (isMoss){
    T_ = -0.01;
    b = 0.8;
  } else if (isFibric){
    T_ = -0.03;
    b = 0.4;
  } else if (isHumic){
    T_ = -0.03;
    b = 0.4;
  } else {
    T_ = -0.03;
    b = 0.4;
  }

  if (tem < T_){
    d_uwc = b * poro * pow(abs(T_), b) * pow(abs(tem), -b - 1);
  } else {
    d_uwc = 0.0;
  }

  if (isSnow){
    d_uwc = 0.0;
  }

  return d_uwc;
}

double Layer::getVolWater() {
  double vice = getVolIce();
  double vliq = getVolLiq();
  return fmin((double)poro,(double)vice+vliq);
};

double Layer::getEffVolWater() {
  double effvol = 0.;

  if(isSoil) {
    effvol = getVolWater() - minliq/DENLIQ/dz;
  } else if (isSnow) {
    effvol = getVolWater();
  }

  if(effvol<0) {
    effvol =0.;
  }

  return effvol;
};

double Layer::getVolIce() {
  if (dz != 0) {
    double vice = ice/DENICE/dz; // FIX THIS: divide by zero error when there is no thickness!

    //The logic for snow is slightly different than for soil, as
    // it is the actual matrix being modified, rather than
    // material within the matrix. In this case, snow
    // layers have no value for porosity. 
    if(isSnow){
      vice = fmax(0.0, vice);
    }
    else{
      vice = fmin((double)vice, (double)poro);
    }

    return vice;
  } else {
    return 0;
  }
};

double Layer::getVolLiq() {
  if (dz != 0) {
    double vliq = liq/DENLIQ/dz; // FIX THIS: divide by zero error when there is no thickness!

    //The logic for snow is slightly different than for soil, as
    // it is the actual matrix being modified, rather than
    // material within the matrix. In this case, snow
    // layers have no value for porosity.
    if(isSnow){
      vliq = fmax(0.0, vliq);
    }
    else{
      vliq = fmin((double)vliq,(double)poro);
    }
    
    return vliq;
  } else {
    return 0;
  }

};

double Layer::getEffVolLiq() {
  if (dz != 0) {
    double evliq = (liq-minliq)/DENLIQ/dz; // FIX THIS: divide by zero error when there is no thickness!
    evliq = fmin((double)evliq,(double)poro);
    if (liq < 0){
      std::cout << "If getEffVolLiq gets -ve liq   " << liq;
    }
    return evliq;
  } else {
    return 0;
  }
};

// peat-dos-tem:
// double Layer::getEffVolWater(){
//  	double effvol =0.;
//  	if(isSoil()){
//  	  effvol = getVolWater() -0.05 * poro;	
//  	}else if (isSnow()){
//  	  effvol = getVolWater();	
//  	}
//  	if(effvol<0){
//  	 effvol =0.;	
//  	}
//  	return effvol;
// };
