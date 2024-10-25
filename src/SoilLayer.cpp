/*! \file
 *
 */
#include "../include/SoilLayer.h"

#include "../include/TEMLogger.h"
extern src::severity_logger< severity_level > glg;

SoilLayer::SoilLayer() {
  BOOST_LOG_SEV(glg, debug) << "==> Creating a SoilLayer object...";
  isSoil = true;
};

SoilLayer::~SoilLayer() {
  BOOST_LOG_SEV(glg, debug) << "--> Deleting a SoilLayer object...";
};

double SoilLayer::getFrzVolHeatCapa() {
  double vhc = vhcsolid * (1 - poro) + (poro * DENICE) * SHCICE;
  return vhc;
};

double SoilLayer::getUnfVolHeatCapa() {
  double vhc= vhcsolid * (1-poro) + (poro * DENLIQ) * SHCLIQ; 
  return vhc;
};

double SoilLayer::getMixVolHeatCapa() {

  double uwc = getUnfVolLiq();
  double lwc = getVolLiq();

  double vhcf = getFrzVolHeatCapa();
  double vhcu = getUnfVolHeatCapa();

  // scaling based on mobile liquid water content (lwc) and immobile
  // unfrozen pore water content (uwc) and porosity. These are summed
  // as lwc freezes around 0 degC uwc begins to increase.
  double scaler = fmin(uwc + lwc, poro);

  double vhc = (1 - poro) * vhcsolid + (poro * vhcu * scaler) + (poro * vhcf * (1 - scaler));

  if (tem >= temp_dep){
    vhc = vhcu;
  }
  
  return vhc;

};

// get frozen layer thermal conductivity
double SoilLayer::getFrzThermCond() {
  double tc;
  double vice = getVolIce();
  double vliq = getVolLiq();
  double s = (vice + vliq)/poro;
  s = min(s, 1.0);
  double ke = s; // for frozen case

  if(s < 1.e-7) {
    tc = tcdry;
  } else {
    tc = ke *tcsatfrz + (1-ke)*tcdry;
  }

  return tc;
};

// get unfrozen layer thermal conductivity
double SoilLayer::getUnfThermCond() {
  double tc;
  double vice = getVolIce();
  double vliq = getVolLiq();
  double s = (vice + vliq)/poro;
  s = min(s, 1.0);
  double ke= log(s) +1; // for unfrozen case
  ke = fmax(ke, 0.);

  if(s < 1.e-7) {
    tc = tcdry;
  } else {
    tc = ke *tcsatunf + (1-ke)*tcdry;
  }

  if(poro>=0.9 || (poro>=0.8 &&solind ==1)) {
    tc = fmax(tc, tcmin);
  }

  return tc;
};

double SoilLayer::getMixThermCond() { 

  // Note: accounting for porosity, liquid, ice content is imperative when reviewing 
  // this equation, see reference:

  // Hailong He, Gerald N. Flerchinger, Yuki Kojima, Miles Dyck, Jialong Lv,
  // A review and evaluation of 39 thermal conductivity models for frozen soils,
  // https://doi.org/10.1016/j.geoderma.2020.114694.

  double tc = MISSING_D;
  double tcf = MISSING_D;
  double tcu = MISSING_D;

  double lwc = getVolLiq();
  double uwc = getUnfVolLiq();

  tcf = getFrzThermCond();
  tcu = getUnfThermCond();

  // scaling based on mobile liquid water content (lwc) and immobile
  // unfrozen pore water content (uwc) and porosity. These are summed
  // as lwc freezes around 0 degC uwc begins to increase.
  double scaler = fmin(uwc + lwc, poro);

  tc = pow(tcf, 1 - fmin(scaler, poro)) * pow(tcu, fmin(scaler, poro));

  if (tem >= temp_dep){
    tc = tcu;
  }

  return tc;
};

double SoilLayer::getMatricPotential() {
  double psi;
  double lf = 3.337e5 ;// latent heat of fusion J/kg
  double g =9.8;

  if(tem<0) {
    psi =1000. * lf/g *(tem/(tem+273.16));

    if (psi<-1.e8) {
      psi=-1.e8;
    }
  } else {
    double voliq = getEffVolLiq();
    double ws = fmax(0.01, voliq);
    ws = fmin(1.0, ws);
    psi = psisat * pow(ws, -bsw);

    if (psi<-1.e8) {
      psi=-1.e8;
    }
  }

  return psi;
};

// get albedo of visible radiation
double SoilLayer::getAlbedoVis() {
  double vis;
  double liq1 = getVolLiq();
  double ice1 = getVolIce();
  double delta = 0.11-0.4*(liq1+ice1);
  delta =fmax(0., delta);
  vis = albsatvis + delta;
  vis = min(vis, (double)albdryvis);
  return vis;
};

// get albedo of nir radiation
double SoilLayer::getAlbedoNir() {
  double nir;
  double wat = getVolLiq()+getVolIce();
  double delta = 0.11-0.4*wat;
  delta =fmax(0., delta);
  nir = albsatnir + delta;
  nir = fmin(nir, (double)albdrynir);
  return nir;
};

// derive properties from the assigned property
// called when porosity/thickness is changed
void SoilLayer::derivePhysicalProperty() {
  //hydraulic properties
  minliq = getUnfVolLiq() * poro * DENLIQ * dz;
  maxliq = poro * DENLIQ * dz;
  maxice = poro * DENICE * dz - minliq;
  //thermal properties
  tcsatunf= pow((double)tcsolid , (double)1- poro) * pow((double)TCLIQ, (double)poro);
  tcsatfrz= pow((double)tcsolid , (double)1- poro) * pow((double)TCICE, (double)poro);
  tcdry   = pow((double)tcsolid , (double)1- poro) * pow((double)TCAIR, (double)poro);
  tcmin   = tcdry;
};

