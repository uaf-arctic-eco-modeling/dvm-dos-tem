/*! \file
 *
 */
#include "../include/MineralLayer.h"

#include "../include/TEMLogger.h"
extern src::severity_logger< severity_level > glg;

MineralLayer::MineralLayer(const double & pdz,
                           float psand, float psilt, float pclay
                           //int sttype,
                           ) {
  BOOST_LOG_SEV(glg, debug) << "==> ==> Creating a MineralLayer...";
  tkey  = I_MINE;
  dz    = pdz;
  pctsand = psand;
  pctsilt = psilt;
  pctclay = pclay;
  isMoss    = false;
  isMineral = true;
  isOrganic = false;
  isFibric = false;
  isHumic  = false;
  updateProperty5Lookup();
};
MineralLayer::~MineralLayer() {
  BOOST_LOG_SEV(glg, debug) << "--> --> Deleting a MineraLayer object...";
}

/** Calculate properties 'inline'.
 * Previous approach used soil classes (11 or 12 of them) and stored values in a
 * 'lookup object' (SoilLookup). Now we are trying to use percent sand/silt/clay
 * directly and to calculate various derived properties from these percentages
 * instead of looking the values up from the classificaiton 'tables'.
*/
void MineralLayer::updateProperty5Lookup() {

  // 10-27-2015
  // borrowed the following calculations/properties from H. Genet's dos-tem
  // implementation which can be found here:
  // https://github.com/ua-snap/dos-tem/commit/4de04dacb8741aa3b8b0e9c348bc19cfb2b4fb3c

  poro =  0.489 - 0.00126 * this->pctsand;

  tcsolid = (8.8 * this->pctsand + 2.92 * this->pctclay) /
            (this->pctsand + this->pctclay);

  hksat = 0.0070556 * pow( 10.0, (-0.884 + 0.0153 * this->pctsand) );

  psisat =  -10.0 * pow( 10.0, (1.88 - 0.0131 * this->pctsand) );

  bsw = 2.91 + 0.159 * this->pctclay;

  bulkden = 2700 * (1 - poro);

  tcdry = (0.135 * bulkden + 64.7) / (2700 - 0.947 * bulkden);

  //prtlden = 2700.0; // not present in dvmdostem??

  tcsatunf = pow(tcsolid , 1.0 - poro) * pow((double)TCLIQ, poro);
  tcsatfrz = pow(tcsolid , 1.0 - poro) * pow((double)TCICE, poro);
  vhcsolid = (2.128 * this->pctsand + 2.385 * this->pctclay) /
             (this->pctsand + this->pctclay) * 1.0e6;

  albsatvis = 0.09;
  albsatnir = 0.18;
  albdryvis = 0.18;
  albdrynir = 0.36;

  //TODO
  // Note:
  // in dos-tem, these values are calculated here. In dvm-dos-tem, the values
  // are calculated in derivePhysicalPropert(..). So there is a bit of
  // redundancy present until we figure out the best way to arrange this.
  //minliq = 0.05 * 1000.0 * dz;
  //maxliq = poro * 1000.0 * dz;
  //maxice = poro * 1000.0 * dz - minliq;

  derivePhysicalProperty();
};


// dry thermal conductivity, if not lookup
double MineralLayer::getDryThermCond(const double & bulkden) {
  // from ATBalland22005a
  double kdry =0.;
  kdry = (0.135*bulkden +64.7)/(2700-0.947*bulkden);
  return kdry;
}

double MineralLayer::getDryThermCond(const double & tcsolid,
                                     const double & bulkden,
                                     const double & partden) {
  // from ATBalland22005a
  double kdry =0.;
  double par_a = 0.053;
  double tcair = TCAIR;
  kdry = ((par_a* tcsolid - tcair) *bulkden + tcair*partden)
         / (partden - (1-par_a)*bulkden) ;
  return kdry;
}

