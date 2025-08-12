#include <string>

#include "../include/ThermokarstData.h"

ThermokarstData::ThermokarstData() {
  thermokarst_a2soi.orgn = 0.0;
  useThermokarstSeverity = false;
};

ThermokarstData::~ThermokarstData() {
};

/** Returns a multi-line string showing the state of the FirData object. */
std::string ThermokarstData::report_to_string(const std::string& msg) {
  std::stringstream report;

  report << "  " << msg << "  ==== ThermokarstData REPORT ====\n";
  report << "   useThermokarstSeverity: " << useThermokarstSeverity << "\n";
  report << "   thermokarst_soid.removal_thickness: " << thermokarst_soid.removal_thickness << "\n";
  report << "\n";
  // report << "   fire_v2a.orc: " << fire_v2a.orgc << "\n";
  // report << "   fire_v2a.orn: " << fire_v2a.orgn << "\n";
  // report << "\n";
  // report << "   fire_v2soi.abvc: " << fire_v2soi.abvc << "\n";
  // report << "   fire_v2soi.abvn: " << fire_v2soi.abvn << "\n";
  // report << "   fire_v2soi.blwc: " << fire_v2soi.blwc << "\n";
  // report << "   fire_v2soi.blwn: " << fire_v2soi.blwn << "\n";
  // report << "\n";
  // report << "   fire_soi2a.orgc: " << fire_soi2a.orgc << "\n";
  // report << "   fire_soi2a.orgn: " << fire_soi2a.orgn << "\n";
  // report << "\n";
  // report << "   fire_a2soi.orgn: " << fire_a2soi.orgn << "\n";

  return report.str();

}

void ThermokarstData::clear() {
  useThermokarstSeverity = false;
  thermokarst_soid = soidiag_thermokarst();
  thermokarst_v2a = veg2atm_thermokarst();
  thermokarst_v2soi = veg2soi_thermokarst();
  thermokarst_soi2a = soi2atm_thermokarst();
  thermokarst_v2dead = veg2dead_thermokarst();

  //fire_a2soi is not cleared until FRI*12 months post fire, as it
  //holds the flux value for transferring N back to the soil.
  //fire_a2soi= atm2soi_fir();
};

void ThermokarstData::init() {
  //
};

void ThermokarstData::beginOfMonth(){
  thermokarst_v2dead = veg2dead_thermokarst();
}

void ThermokarstData::beginOfYear() {
  //>>> need to review these and rename them
  // they are defined in diagnostics.h and fluxes.h

  // fire_soid.burnthick =0.;
  // fire_v2a.orgc =0.;
  // fire_v2a.orgn =0.;
  // fire_v2soi.abvc =0.;
  // fire_v2soi.blwc =0.;
  // fire_v2soi.abvn =0.;
  // fire_v2soi.blwn =0.;
  // fire_soi2a.orgc =0.;
  // fire_soi2a.orgn =0.;
};

void ThermokarstData::endOfYear() {
  //
};

void ThermokarstData::clearing() {
  clear();
}
