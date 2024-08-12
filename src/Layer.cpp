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

// double Layer::getUnfVolLiq(){
//   // Calculating unfrozen water content using power law
//   // defined in Lovell 1957, and used in Romanovsky et 
//   // al. 1997 and 2000

//   // Tunable empirical constants - here we are using values for Bonanza Creek
//   double A, B, uwc;
//   if (isMoss){
//     A = 0.1;
//     B = -0.1;
//   } else if (isFibric){
//     A = 0.08;
//     B = -0.1;
//   } else if (isHumic){
//     A = .1;
//     B = -0.38;
//   } else{
//     A = .3;
//     B = -0.35;
//   }

//   if (tem<0.0){
//     uwc = A * pow(abs(tem), B);
//   } else {
//     uwc = 0.0;
//   }

//   return uwc;

// }

// double Layer::getDeltaUnfVolLiq()
// {
//   // Calculating derivative of unfrozen water content
//   // with respect to temperature following Romanovsky
//   // et al. 1997

//   // Tunable empirical constants - here we are using values for Bonanza Creek
//   double A, B, d_uwc;
//   if (isMoss){
//     A = 0.1;
//     B = -0.1;
//   } else if (isFibric){
//     A = 0.1;
//     B = -0.1;
//   } else if (isHumic){
//     A = 3.2;
//     B = -0.38;
//   } else{
//     A = 6;
//     B = -0.35;
//   }

//   if (tem<0.0){
//     d_uwc = -B * A * pow(abs(tem), B - 1); // / 100  Do we need percentage conversion in derivative?  
//   } else {
//     d_uwc = 0.0;
//   }

//   return d_uwc;

// }

double Layer::getUnfVolLiq(){
 
  double T_, b, uwc;
  T_ = -0.01;

  if (isMoss){
    b = 1.0;
  } else if (isFibric){
    b = 0.9;
  } else if (isHumic){
    b = 0.6;
  } else {
    b = 0.5;
  }

  if (tem < T_){
    uwc = pow(abs(T_), b) * pow(abs(tem), -b); 
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
  T_ = -0.01;

  if (isMoss){
    b = 1.0;
  } else if (isFibric){
    b = 0.9;
  } else if (isHumic){
    b = 0.6;
  } else {
    b = 0.5;
  }

  if (tem < T_){
    d_uwc = b * pow(abs(T_), b) * pow(abs(tem), -b-1);
  } else {
    d_uwc = 0.0;
  }

  if (isSnow){
    d_uwc = 0.0;
  }

  return d_uwc;
}

double Layer::getVolWater() { // We could try implementing uwc here as well
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
    return evliq;
  } else {
    return 0;
  }
};
