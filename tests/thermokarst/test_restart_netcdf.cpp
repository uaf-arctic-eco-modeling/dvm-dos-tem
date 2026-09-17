#include "../../include/RestartData.h"
#include "../../include/RestartThermokarst.h"

#include <netcdf.h>

#include <cmath>
#include <cstdio>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

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

void create_versioned_restart(const std::string& path,int version_value,
                              size_t state_length) {
  create_restart_shell(path, false);
  int ncid=-1,y=-1,x=-1,soil=-1,state=-1,var=-1;
  nc_ok(nc_open(path.c_str(),NC_WRITE,&ncid),"open v1 restart");
  nc_ok(nc_inq_dimid(ncid,"Y",&y),"find Y");
  nc_ok(nc_inq_dimid(ncid,"X",&x),"find X");
  nc_ok(nc_inq_dimid(ncid,"soillayer",&soil),"find soil");
  nc_ok(nc_redef(ncid),"redefine v1 restart");
  nc_ok(nc_def_dim(ncid,"thermokarst_state",state_length,&state),"define old state");
  int d2[]={y,x},ds[]={y,x,state},dl[]={y,x,soil};
  nc_ok(nc_def_var(ncid,"TKversion",NC_INT,2,d2,&var),"define v1 version");
  nc_ok(nc_def_var(ncid,"TKactive",NC_INT,2,d2,&var),"define v1 active");
  nc_ok(nc_def_var(ncid,"TKstate",NC_DOUBLE,3,ds,&var),"define v1 state values");
  nc_ok(nc_def_var(ncid,"TKpuddle",NC_DOUBLE,2,d2,&var),"define v1 puddle");
  nc_ok(nc_def_var(ncid,"TKmatrix",NC_DOUBLE,3,dl,&var),"define v1 matrix");
  nc_ok(nc_def_var(ncid,"TKporosity",NC_DOUBLE,3,dl,&var),"define v1 porosity");
  nc_ok(nc_def_var(ncid,"TKexcess",NC_DOUBLE,3,dl,&var),"define v1 excess");
  nc_ok(nc_enddef(ncid),"end v1 define");
  int active=1;double puddle=2.5;std::vector<double> state_values(state_length);
  double layers[MAX_SOI_LAY]={};for(size_t i=0;i<state_length;++i)state_values[i]=i+.5;
  size_t point[]={0,0},start[]={0,0,0},state_count[]={1,1,state_length},layer_count[]={1,1,MAX_SOI_LAY};
  nc_inq_varid(ncid,"TKversion",&var);nc_ok(nc_put_var1_int(ncid,var,point,&version_value),"write old version");
  nc_inq_varid(ncid,"TKactive",&var);nc_ok(nc_put_var1_int(ncid,var,point,&active),"write v1 active");
  nc_inq_varid(ncid,"TKpuddle",&var);nc_ok(nc_put_var1_double(ncid,var,point,&puddle),"write v1 puddle");
  nc_inq_varid(ncid,"TKstate",&var);nc_ok(nc_put_vara_double(ncid,var,start,state_count,state_values.data()),"write old state");
  for(const char* name:{"TKmatrix","TKporosity","TKexcess"}){nc_inq_varid(ncid,name,&var);nc_ok(nc_put_vara_double(ncid,var,start,layer_count,layers),"write v1 layer data");}
  nc_ok(nc_close(ncid),"close v1 restart");
}

void fill(RestartData& data) {
  data.TKversion=3;
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
  const std::string version_one="/tmp/tem-thermokarst-version-one-test.nc";
  const std::string version_two="/tmp/tem-thermokarst-version-two-test.nc";
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

    create_versioned_restart(version_one,1,10);
    RestartData v1;
    v1.read_px_thermokarst_vars(version_one,0,0);
    check(v1.TKversion==1 && v1.TKstate[9]==9.5,
          "version-one restart state was not read");
    for(int i=10;i<ThermokarstState::COUNT;++i)
      check(v1.TKstate[i]==0.,"new diagnostic state was not defaulted");

    create_versioned_restart(version_two,2,15);
    RestartData v2;
    v2.read_px_thermokarst_vars(version_two,0,0);
    check(v2.TKversion==2 && v2.TKstate[14]==14.5,
          "version-two restart state was not read");
    for(int i=15;i<ThermokarstState::COUNT;++i)
      check(v2.TKstate[i]==0.,"fire diagnostic state was not defaulted");

    std::remove(current.c_str());
    std::remove(legacy.c_str());
    std::remove(version_one.c_str());
    std::remove(version_two.c_str());
    std::cout << "PASS netcdf_round_trip\nPASS legacy_restart_compatibility\nPASS version_one_restart_compatibility\nPASS version_two_restart_compatibility\n";
  } catch(const std::exception& error) {
    std::remove(current.c_str());
    std::remove(legacy.c_str());
    std::remove(version_one.c_str());
    std::remove(version_two.c_str());
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
  return 0;
}
