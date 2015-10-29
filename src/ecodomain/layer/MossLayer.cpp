/*! \file
 *
 */
#include "MossLayer.h"

#include "../../TEMLogger.h"
extern src::severity_logger< severity_level > glg;

MossLayer::MossLayer(const double &pdz, const int & newmosstype) {
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
  poro     = 0.98;
  bulkden  = 25000; // g/m3
  // light properties
  albsatvis = 0.09;
  albsatnir = 0.18;
  albdryvis = 0.18;
  albdrynir = 0.36;
  // thermal properties
  tcsolid = 0.25;
  vhcsolid=2.5e6; //J/m3K

  // hydraulic properties
  if(mosstype ==1) {
    hksat  = 0.15; //mm/s
    psisat = -10; // mm
    bsw = 1;
  } else if(mosstype ==2) {
    hksat  = 0.15; //mm/s
    psisat = -120; // mm
    bsw = 1;
  } else {
    hksat = 0.15; //mm/s
    psisat = -50; // mm
    bsw = 1;
  }

  derivePhysicalProperty();
  // biogeochemical properties
  cfrac = 39.8; // %  O'Donnel et al. (GCB, 2011)
}

MossLayer::~MossLayer(){
  BOOST_LOG_SEV(glg, debug) << "--> --> Deleting a MossLayer object...";
}
