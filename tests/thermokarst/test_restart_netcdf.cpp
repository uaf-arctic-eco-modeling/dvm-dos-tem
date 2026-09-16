#include "../../include/RestartData.h"
#include "../../include/RestartThermokarst.h"

#include <netcdf.h>

#include <cmath>
#include <cstdio>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

void nc_ok(int status, const char* operation) {
  if(status != NC_NOERR)
    throw std::runtime_error(std::string(operation) + ": " + nc_strerror(status));
}

void check(bool condition, const char* message) {
  if(!condition) throw std::runtime_error(message);
}

void create_restart_shell(const std::string& path, bool with_thermokarst) {
  int ncid=-1, y=-1, x=-1, soil=-1;
  nc_ok(nc_create(path.c_str(), NC_CLOBBER, &ncid), "create test restart");
  nc_ok(nc_def_dim(ncid, "Y", 2, &y), "define Y");
  nc_ok(nc_def_dim(ncid, "X", 2, &x), "define X");
  nc_ok(nc_def_dim(ncid, "soillayer", MAX_SOI_LAY, &soil), "define soil");
  if(with_thermokarst)
    restart_thermokarst::define_netcdf_fields(ncid, y, x, soil);
  nc_ok(nc_enddef(ncid), "end define mode");
  nc_ok(nc_close(ncid), "close test restart");
}

void fill(RestartData& data) {
  data.TKversion=2;
  data.TKactive=1;
  data.TKpuddle=4.25;
  for(int i=0;i<ThermokarstState::COUNT;++i)
    data.TKstate[i]=0.125+1.5*i;
  for(int i=0;i<MAX_SOI_LAY;++i) {
    data.TKmatrix[i]=0.01*(i+1);
    data.TKporosity[i]=0.25+0.005*i;
    data.TKexcess[i]=2.0*i;
  }
}

void compare(const RestartData& expected, const RestartData& actual) {
  check(actual.TKversion==expected.TKversion, "TKversion changed");
  check(actual.TKactive==expected.TKactive, "TKactive changed");
  check(actual.TKpuddle==expected.TKpuddle, "TKpuddle changed");
  for(int i=0;i<ThermokarstState::COUNT;++i)
    check(actual.TKstate[i]==expected.TKstate[i], "TKstate changed");
  for(int i=0;i<MAX_SOI_LAY;++i) {
    check(actual.TKmatrix[i]==expected.TKmatrix[i], "TKmatrix changed");
    check(actual.TKporosity[i]==expected.TKporosity[i], "TKporosity changed");
    check(actual.TKexcess[i]==expected.TKexcess[i], "TKexcess changed");
  }
}

} // namespace

// This focused test links the thermokarst restart adapter without the legacy
// RestartData translation unit, whose constructor initializes many unrelated
// model fields and logger dependencies.
RestartData::RestartData() {
  TKversion=0;
  TKactive=0;
  TKpuddle=0.0;
  for(int i=0;i<ThermokarstState::COUNT;++i) TKstate[i]=0.0;
  for(int i=0;i<MAX_SOI_LAY;++i) {
    TKmatrix[i]=0.0;
    TKporosity[i]=0.0;
    TKexcess[i]=0.0;
  }
}
RestartData::~RestartData() {}

int main() {
  const std::string current="/tmp/tem-thermokarst-restart-test.nc";
  const std::string legacy="/tmp/tem-thermokarst-legacy-test.nc";
  std::remove(current.c_str());
  std::remove(legacy.c_str());
  try {
    create_restart_shell(current, true);
    RestartData written;
    fill(written);
    written.write_px_thermokarst_vars(current, 1, 0);

    RestartData read;
    read.read_px_thermokarst_vars(current, 1, 0);
    compare(written, read);

    // Writing another pixel must not contaminate the first one.
    RestartData alternate;
    fill(alternate);
    alternate.TKpuddle=9.5;
    alternate.TKstate[0]=-3.0;
    alternate.write_px_thermokarst_vars(current, 0, 1);
    RestartData second;
    second.read_px_thermokarst_vars(current, 0, 1);
    compare(alternate, second);
    RestartData reread;
    reread.read_px_thermokarst_vars(current, 1, 0);
    compare(written, reread);

    // Pre-feature restart files have no TKversion. They remain version zero,
    // allowing Cohort to initialize from configuration.
    create_restart_shell(legacy, false);
    RestartData old;
    old.read_px_thermokarst_vars(legacy, 0, 0);
    check(old.TKversion==0 && old.TKactive==0,
          "legacy restart was not treated as version zero");

    std::remove(current.c_str());
    std::remove(legacy.c_str());
    std::cout << "PASS netcdf_round_trip\nPASS legacy_restart_compatibility\n";
  } catch(const std::exception& error) {
    std::remove(current.c_str());
    std::remove(legacy.c_str());
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
  return 0;
}
