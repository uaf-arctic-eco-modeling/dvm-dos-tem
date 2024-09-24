/*! \file
 *
 */
#include "../include/OrganicLayer.h"

#include "../include/TEMLogger.h"
extern src::severity_logger< severity_level > glg;

OrganicLayer::OrganicLayer(const double & pdz, const int & type, const CohortLookup* chtlu) {
  BOOST_LOG_SEV(glg, debug) << "==> ==> Creating an OrganicLayer object...";
  isMoss    = false;
  isMineral = false;
  isOrganic = true;
  isFibric = false;
  isHumic  = false;
  dz = pdz;

  if(type==1) {
    tkey=I_FIB;
    isFibric =true;
    poro = chtlu->poro_f;
    bulkden = chtlu->bulkden_f; // g/m3
    albsatvis = 0.075;
    albsatnir = 0.15;
    albdryvis = 0.15;
    albdrynir = 0.3;
    tcsolid = chtlu->tcsolid_f;
    vhcsolid= 2.5e6; //J/m3K
    hksat = chtlu->hksat_f;
    bsw=2.7;
    psisat =-10.0;
    cfrac = 44.2; // %
    temp_dep = chtlu->temp_dep_f;
    b_parameter = chtlu->b_f;
  } else if (type==2) {
    tkey=I_HUM;
    isHumic =true;
    poro = chtlu->poro_h;
    bulkden = chtlu->bulkden_h; // g/m3
    albsatvis = 0.075;
    albsatnir = 0.15;
    albdryvis = 0.15;
    albdrynir = 0.3;
    tcsolid = chtlu->tcsolid_h;
    vhcsolid= 2.5e6; //J/m3K
    bsw=8;
    hksat = chtlu->hksat_h;
    psisat =-12;
    cfrac = 35.2; // %
    temp_dep = chtlu->temp_dep_h;
    b_parameter = chtlu->b_h;
  }

  derivePhysicalProperty();
};

OrganicLayer::~OrganicLayer(){
  BOOST_LOG_SEV(glg, debug) << "--> --> Deleting an OrganicLayer object...";
}

void OrganicLayer::humify(const CohortLookup* chtlu) {
  tkey=I_HUM;
  isHumic =true;
  isFibric=false;
  poro = chtlu->poro_h;
  bulkden = chtlu->bulkden_h; // g/m3
  albsatvis = 0.075;
  albsatnir = 0.15;
  albdryvis = 0.15;
  albdrynir = 0.3;
  tcsolid = chtlu->tcsolid_h;
  vhcsolid= 2.5e6; //J/m3K
  bsw=8;
  hksat  = chtlu->hksat_h;
  psisat =-12;
  cfrac = 35.2; // %
  temp_dep = chtlu->temp_dep_h;
  b_parameter = chtlu->b_h;
  derivePhysicalProperty();
};

