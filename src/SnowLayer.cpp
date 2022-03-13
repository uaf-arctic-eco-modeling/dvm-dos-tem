/*! \file
 *
 */
#include "../include/SnowLayer.h"

#include "../include/TEMLogger.h"
extern src::severity_logger< severity_level > glg;

SnowLayer::SnowLayer() {
  BOOST_LOG_SEV(glg, debug) << "==> Creating a SnowLayer layer object...";
  tkey = I_SNOW;
  isSnow = true;
  solind = MISSING_I;
  liq    = MISSING_D;
  maxliq = MISSING_D;
  frozen = 1;
  rawc = MISSING_D;
  soma = MISSING_D;
  sompr= MISSING_D;
  somcr= MISSING_D;
  cfrac= MISSING_D;
};

SnowLayer::~SnowLayer() {
  BOOST_LOG_SEV(glg, debug) << "--> Deleting a Snow Layer object...";
};

void SnowLayer::clone(SnowLayer* sl) {
  liq = sl->liq;
  ice = sl->ice;
  dz  = sl->dz;
  age = sl->age;
  rho = sl->rho;
}

void SnowLayer::updateDensity(snwpar_dim *snwpar) {
  double adjust=0.24; // corresponding to e-folding time of 4 days
  double tao1 = 86400.; //s
  double tao  = 86400.; // one day time step
  rho = (rho-snwpar->denmax)* exp(- tao/tao1* adjust) + snwpar->denmax;

  if(rho>snwpar->denmax) {
    rho= snwpar->denmax;
  }

  maxice = snwpar->denmax*dz;
  maxliq = maxice;  // note: this is SWE max
};

// after the update of density, snow thickness should also be changed
void SnowLayer::updateThick() {
  dz = ice/rho;
}

// get frozen layer thermal conductivity, according to Jordan 1991
double SnowLayer::getFrzThermCond() {
  //if (ctype==0){// tundra
  return getThermCond();
  //}else{
  //return getThermCond5Sturm();
  //}
};

// get unfrozen layer thermal conductivity
double SnowLayer::getUnfThermCond() {
  //if(ctype==0){
  return getThermCond();
  //}else{
  //return getThermCond5Sturm();
  //}
};

//From Sturm 2002 (which references Sturm 1997)
double SnowLayer::getThermCond5Sturm() {
  double tc=0;
  double rhogcm = rho /1000.; // convert from  kg/m3 to g/cm3

  if(rhogcm<=0.6 && rhogcm>=0.156) {
    tc = 0.138 - 1.01 * rhogcm + 3.233 * rhogcm * rhogcm;
  } else if(rhogcm<0.156) {
    tc =0.023 +0.234 *rhogcm;
  }

  return tc;
};

double SnowLayer::getThermCond() {
  double tc=0;

  //From Jordan 1991, referenced in Oleson 2004
  //tc = TCAIR + (7.75e-5 * rho + 1.105e-6*rho*rho)*(TCICE-TCAIR);

  //From Goodrich 1982
  //Shuhua's notes indicate that Goodrich should be used
  // for snow, but not for soil.
  tc = 2.9*1.e-6 * rho*rho;

  if(tc<0.04) {
    tc =0.04;
  }

  return tc;
}

// FIX THIS: THESE 3 functions see to be identical???
double SnowLayer::getFrzVolHeatCapa() {
  if (dz != 0) {
    // FIX THIS: divide by zero error when there is no thickness!
    double vhc = SHCICE * ice/dz;
    return vhc;
  } else {
    return 0;
  }
};

double SnowLayer::getUnfVolHeatCapa() {
  if (dz != 0) {
    // FIX THIS: divide by zero error when there is no thickness!
    double vhc = SHCICE * ice/dz;
    return vhc;
  } else {
    return 0;
  }
};

double SnowLayer::getMixVolHeatCapa() {
  if (dz != 0) {
    // FIX THIS: divide by zero error when there is no thickness!
    double vhc = SHCICE * ice/dz;
    return vhc;
  } else {
    return 0;
  }
};

