/*! \file
 *
 */
#include "../include/MossLayer.h"

#include "../include/TEMLogger.h"
extern src::severity_logger< severity_level > glg;

MossLayer::MossLayer(const double &pdz, const int & newmosstype, const CohortLookup* chtlu) {
  BOOST_LOG_SEV(glg, debug) << "==> ==> Creating a MossLayer...";
  tkey=I_MOSS;
  isMoss    = true;
  isOrganic = false;
  isFibric  = false;
  isHumic   = false;
  isMineral = false;
  // dimension
  age = 0;
  mosstype = newmosstype;
  dz       = pdz;
  poro     = chtlu->poro_moss;
  bulkden  = chtlu->bulkden_moss; // g/m3
  // light properties
  albsatvis = 0.09;
  albsatnir = 0.18;
  albdryvis = 0.18;
  albdrynir = 0.36;
  // thermal properties
  tcsolid = chtlu->tcsolid_moss;
  vhcsolid=2.5e6; //J/m3K

  // hydraulic properties
  //bsw should be 1, but is set to 1.01 in order
  // to avoid NaNs in hydraulic calculations (see Richards)
  if(mosstype ==1) {
    hksat  = chtlu->hksat_moss; //mm/s
    psisat = -10; // mm
    bsw = 1.01;
  } else if(mosstype ==2) {
    hksat  = chtlu->hksat_moss; //mm/s
    psisat = -120; // mm
    bsw = 1.01;
  } else {
    hksat = chtlu->hksat_moss; //mm/s
    psisat = -50; // mm
    bsw = 1.01;
  }

  derivePhysicalProperty();
  // biogeochemical properties
  cfrac = 39.8; // %  O'Donnel et al. (GCB, 2011)
}

MossLayer::~MossLayer(){
  BOOST_LOG_SEV(glg, debug) << "--> --> Deleting a MossLayer object...";
}
