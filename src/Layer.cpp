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
  temp_dep = MISSING_D;
  b_parameter = MISSING_D;
  // thermal status
  frozen    = MISSING_I;
  frozenfrac= MISSING_D;
  tem  = MISSING_D;
  tcond= MISSING_D;
  hcapa = MISSING_D;
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
    if(tem >= temp_dep) {
      hcap = getUnfVolHeatCapa();
    } else {
      hcap = getMixVolHeatCapa();
    }
  } else if(isSnow) {
    hcap = getFrzVolHeatCapa();
  } else if(isRock) {
    hcap = getFrzVolHeatCapa();
  }

  this->hcapa = hcap + (DENLIQ * LHFUS) * fapp_hcap();

  return hcap;

};

double Layer::getThermalConductivity() {
  double tc = MISSING_D;

  if(isSoil) {
    if(tem >= temp_dep){
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

  double uwc;

  if (tem < temp_dep){
    uwc = poro * pow(abs(temp_dep), b_parameter) * pow(abs(tem), -b_parameter);
  } else{
    uwc = 0.0;
  }

  uwc = fmin(uwc, getVolWater());

  if (isSnow){
    uwc = 0.0;
  }

  return 0.0;
}

double Layer::getDeltaUnfVolLiq(){

  double d_uwc;

  if (tem < temp_dep){
    d_uwc = -b_parameter * tem * poro * pow(abs(temp_dep), b_parameter) * pow(abs(tem), -b_parameter - 2);
  } else {
    d_uwc = 0.0;
  }

  if (isSnow){
    d_uwc = 0.0;
  }

  return 0.0;
}

double Layer::getVolWater(){
    double vice = getVolIce();
    double vliq = getVolLiq();
    return fmin((double)poro, (double)vice + vliq);
};

double Layer::getEffVolWater() {
  double effvol = 0.;

  if(isSoil) {
    effvol = getVolWater() - 0.05 * poro;
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
      vice = fmin((double)vice, (double)maxice);
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
      vliq = fmax((double)vliq, (double)minliq/DENLIQ/dz);
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

  /* 
  Incorporating equations from Nicolsky et al. 2007
  mimicking GIPL2.0 unfrozen water and apparent
  heat capacity formulation. 

  prevl, nextl are assigned based on finite difference
  method, and fitting within the Layer class structure
  so in certain cases prevl->fhcap will be used which
  corresponds to this work around. See GIPL2.0 and 
  Nicolsky et al. 2007 for more information on the 
  finite difference method used.

   */

double Layer::funf_water(double const & Temperature){
  /* Calculate unfrozen water content based on 
     temperature using empirical parameters */
  double uwc = 0.0;

  if (Temperature < temp_dep){
    uwc = poro * pow(abs(temp_dep), b_parameter) * pow(abs(Temperature), -b_parameter);
  } // We may want to include a smoothing function when / if T=temp_dep, see GIPL 
  else {
    uwc = 0.5;
  }

  uwc = fmin(uwc, getVolWater());

  if (!isSoil){
    uwc = 0.0;
  }

  return uwc;
};

double Layer::fdunf_water(double const & Temperature) {
  /* Calculate derivative of unfrozen water 
     content based on temperature and empirical
     parameters */
  double duwc = 0.0;

  if (Temperature < temp_dep){
    duwc = abs(-b_parameter * Temperature * poro * pow(abs(temp_dep), b_parameter) * pow(abs(Temperature), -b_parameter - 2));
  } else {
    duwc = 0.0;
  }

  if (!isSoil){
    duwc = 0.0;
  }

  return duwc;
};

double Layer::fhcap(const double &T1, const double &T2){
  /* Calculate phase change component of
     apparent heat capacity */
  double fhcap, H = 0.0;

  if (abs(T1 - T2) < 1e-1){
    fhcap = 0.5 * (fdunf_water(T1) + nextl->fdunf_water(T2));
  } else {
    if (tkey != nextl->tkey){
      H = 1 / (T1 - T2);
      fhcap = 0.5 * (H * (funf_water(T1) - funf_water(T2)) + H * (nextl->funf_water(T1) - nextl->funf_water(T2)));
    }else{
      H = 1 / (T1 - T2);
      fhcap = H * (funf_water(T1) - nextl->funf_water(T2));
    }
  }
  return abs(fhcap);
};

double Layer::fapp_hcap(){
  /* Assign temperatures for calculating 
     phase change component of apparent 
     heat capacity using finite 
     difference */
  double app_hcap, T1, T2 = 0.0;

  if (isSoil){
    // for first soil layer in stack
    if (!prevl || !prevl->isSoil){ // isfstsoil?

      T1 = tem;
      T2 = (nextl->tem + tem)/2.0;
      app_hcap = fhcap(T1, T2);  

    // for all layers in the column exept the last 
    } else if (prevl->isSoil && !nextl->isRock){ // islstsoil?

      T1 = (prevl->tem+tem)/2.0;
      T2 = tem;
      app_hcap = prevl->fhcap(T1, T2) * dz / (prevl->dz + dz); 

      T1 = tem;
      T2 = (nextl->tem + tem)/2.0;
      app_hcap += fhcap(T1, T2) * nextl->dz / (nextl->dz + dz);

      // last soil layer before bedrock
    } else if (nextl->isRock && prevl->isSoil){

      T1 = (prevl->tem + tem)/2.0;
      T2 = tem;
      app_hcap = prevl->fhcap(T1, T2); 

      // otherwise we assume snow, or rock so ignore   
    } else {
      app_hcap = 0.0;
    }
  } else {
    app_hcap = 0.0;
  } 
  return app_hcap;
};