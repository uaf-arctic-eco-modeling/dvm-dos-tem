#include <string>

#include "FirData.h"

FirData::FirData() {
  fire_a2soi.orgn = 0.0;
  useseverity = false;
};

FirData::~FirData() {
};

/** Returns a multi-line string showing the state of the FirData object. */
std::string FirData::report_to_string(const std::string& msg) {
  std::stringstream report;
  report << "  " << msg << "  ==== FirData REPORT ====\n";
  report << "   useseverity: " << useseverity << "\n";
  report << "   fire_soid.burnthick: " << fire_soid.burnthick << "\n";
  report << "\n";
  report << "   fire_v2a.orc: " << fire_v2a.orgc << "\n";
  report << "   fire_v2a.orn: " << fire_v2a.orgn << "\n";
  report << "\n";
  report << "   fire_v2soi.abvc: " << fire_v2soi.abvc << "\n";
  report << "   fire_v2soi.abvn: " << fire_v2soi.abvn << "\n";
  report << "   fire_v2soi.blwc: " << fire_v2soi.blwc << "\n";
  report << "   fire_v2soi.blwn: " << fire_v2soi.blwn << "\n";
  report << "\n";
  report << "   fire_soi2a.orgc: " << fire_soi2a.orgc << "\n";
  report << "   fire_soi2a.orgn: " << fire_soi2a.orgn << "\n";
  report << "\n";
  report << "   fire_a2soi.orgn: " << fire_a2soi.orgn << "\n";

  return report.str();

}

void FirData::clear() {
  useseverity = false;
  fire_soid = soidiag_fir();
  fire_v2a  = veg2atm_fir();
  fire_v2soi= veg2soi_fir();
  fire_soi2a= soi2atm_fir();
  fire_a2soi= atm2soi_fir();
};

void FirData::init() {
  //
};

void FirData::beginOfYear() {
  fire_soid.burnthick =0.;
  fire_v2a.orgc =0.;
  fire_v2a.orgn =0.;
  fire_v2soi.abvc =0.;
  fire_v2soi.blwc =0.;
  fire_v2soi.abvn =0.;
  fire_v2soi.blwn =0.;
  fire_soi2a.orgc =0.;
  fire_soi2a.orgn =0.;
};

void FirData::endOfYear() {
//
};

void FirData::burn() {
  clear();
}
