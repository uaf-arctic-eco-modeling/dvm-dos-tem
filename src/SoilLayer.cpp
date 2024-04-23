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
  double vhc = vhcsolid * (1-poro) + (liq+ice)/dz *SHCICE;
  return vhc;
};

double SoilLayer::getUnfVolHeatCapa() {
  double vhc= vhcsolid * (1-poro) + (liq+ice)/dz *SHCLIQ;
  return vhc;
};

//Yuan: unfrozen/frozen put together
double SoilLayer::getMixVolHeatCapa() { //BM: Not sure this calculation is correct, I think we want exp interpolation between two
  double vhc = vhcsolid * (1-poro) + liq/dz *SHCLIQ+ice/dz *SHCICE;
  return vhc;
};

double SoilLayer::getLatentHeatContent(){
  // eq. 15 Hinzman et al. 1998
  //J. GEOPHYS. RES., VOL. 103,
  //NO. D22, PAGES 28,975-28,991,

  // lhc is the latent heat content of soil at temperature T (J/m3)
  // L is total latent heat released during freezing (J/m3)
  // Q (J)  = m(kg)L(J/kg)
  // (J/m2) = liq (kg/m2) LHFUS (J/kg)
  // L(J/m3)= liq (kg/m2) LHFUS (J/kg) / dz (m)     
  // p is adjustable constant (sand = 10, clay = 1)
  // T is soil temperature (degC)
  // Tll is soil temperature when freezing ends
  // Thh is soil temperature when freezing begins
  // dT is Thh - Tll

  double lhc = MISSING_D;
  double L = liq * LHFUS / dz;
  double p = 5; // setting p to 5 to assume part clay part sand soils - may need adjustment for organic soil
  double T = tem;  
  double Tll = -2.0;
  double Thh =  0.0;
  double dT = Tll - Thh; // this seems to be inverted in the paper

  lhc = L * (exp(-p*T/dT) - exp(-p*Tll/dT)) / (exp(-p*Thh/dT) - exp(-p*Tll/dT));

  return lhc;

}

double SoilLayer::getDeltaLatentHeatContentDeltaT()
{
  // eq. 16 Hinzman et al. 1998
  // J. GEOPHYS. RES., VOL. 103,
  // NO. D22, PAGES 28,975-28,991,

  // dlhc/dT is the differential of latent heat content
  //         with respect to soil at temperature T

  // dlhc/dT = - (L / k2 - k1)(p/dT)exp(-pT/dT)
  // where k2=exp(-pThh/dT) and k1=exp(-pTll/dT) 

  // This can be differentiated using the chain rule
  // assuming L, p, Tll, Thh, are known or constants  

  double dlhc_dT = MISSING_D;
  double L = liq * LHFUS / dz;
  double p = 5; 
  double T = tem;
  double Tll = -2.0;
  double Thh = 0.0;
  double dT = Tll - Thh;

  double k1 = exp(-p * Tll / dT);
  double k2 = exp(-p * Thh / dT);
  
  dlhc_dT = -(L / (k2 - k1)) * (p / dT) * exp(-p * T/ dT); 

  return dlhc_dT;

}

// get frozen layer thermal conductivity
double SoilLayer::getFrzThermCond() {
  double tc;
  double vice = getVolIce();
  double vliq = getVolLiq();
  double s = (vice + vliq)/poro;
  s = min(s, 1.0);
  double ke= s; // for frozen case

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
  
  //Note: accounting for porosity, liquid, ice content is imperative when reviewing 
  // this equation, see reference:

  // Hailong He, Gerald N. Flerchinger, Yuki Kojima, Miles Dyck, Jialong Lv,
  // A review and evaluation of 39 thermal conductivity models for frozen soils,
  // https://doi.org/10.1016/j.geoderma.2020.114694.

  double tc = MISSING_D;
  double tcf = MISSING_D;
  double tcu = MISSING_D;

  tcf = getFrzThermCond();
  tcu = getUnfThermCond();

  tc = pow(tcf, frozenfrac) * pow(tcu, 1 - frozenfrac);

  return tc;
};

double SoilLayer::getMatricPotential() {
  double psi;

  if(tem<0) {
    psi =1000. * LHFUS/G *(tem/(tem+273.16));

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
  minliq = 0.05*poro * DENLIQ * dz; //BM: minliq could be parameterized here to equate to our unfrozen water content?
  maxliq = poro * DENLIQ * dz;
  maxice = poro * DENICE * dz;
  //thermal properties
  tcsatunf= pow((double)tcsolid , (double)1- poro) * pow((double)TCLIQ, (double)poro);
  tcsatfrz= pow((double)tcsolid , (double)1- poro) * pow((double)TCICE, (double)poro);
  tcdry   = pow((double)tcsolid , (double)1- poro) * pow((double)TCAIR, (double)poro);
  tcmin   = tcdry;
};

