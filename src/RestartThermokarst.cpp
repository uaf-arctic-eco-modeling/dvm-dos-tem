#include "../include/RestartThermokarst.h"

#include "../include/RestartData.h"
#include "../include/errorcode.h"

#include <netcdf.h>
#include <algorithm>
#include <stdexcept>
#include <string>

namespace restart_thermokarst {
namespace {

void nc_ok(int status, const std::string& operation) {
  if (status != NC_NOERR) {
    throw std::runtime_error(operation + ": " + nc_strerror(status));
  }
}

void fill_double(int ncid, int variable) {
  const double missing = MISSING_D;
  nc_ok(nc_put_att_double(ncid, variable, "_FillValue", NC_DOUBLE, 1,
                          &missing),
        "set thermokarst fill value");
}

} // namespace

void define_netcdf_fields(int ncid, int y_dim, int x_dim, int soil_dim) {
  int state_dim = -1;
  nc_ok(nc_def_dim(ncid, "thermokarst_state", ThermokarstState::COUNT,
                   &state_dim),
        "define thermokarst_state dimension");

  const int dims2[] = {y_dim, x_dim};
  const int dims_state[] = {y_dim, x_dim, state_dim};
  const int dims_soil[] = {y_dim, x_dim, soil_dim};
  int variable = -1;

  nc_ok(nc_def_var(ncid, "TKversion", NC_INT, 2, dims2, &variable),
        "define TKversion");
  nc_ok(nc_def_var(ncid, "TKactive", NC_INT, 2, dims2, &variable),
        "define TKactive");
  nc_ok(nc_def_var(ncid, "TKstate", NC_DOUBLE, 3, dims_state, &variable),
        "define TKstate");
  fill_double(ncid, variable);
  nc_ok(nc_def_var(ncid, "TKpuddle", NC_DOUBLE, 2, dims2, &variable),
        "define TKpuddle");
  fill_double(ncid, variable);
  nc_ok(nc_def_var(ncid, "TKmatrix", NC_DOUBLE, 3, dims_soil, &variable),
        "define TKmatrix");
  fill_double(ncid, variable);
  nc_ok(nc_def_var(ncid, "TKporosity", NC_DOUBLE, 3, dims_soil, &variable),
        "define TKporosity");
  fill_double(ncid, variable);
  nc_ok(nc_def_var(ncid, "TKexcess", NC_DOUBLE, 3, dims_soil, &variable),
        "define TKexcess");
  fill_double(ncid, variable);
}

void read_netcdf_fields(RestartData& data, const char* filename, int row,
                        int column) {
  int ncid = -1;
  nc_ok(nc_open(filename, NC_NOWRITE, &ncid), "open thermokarst restart");
  int variable = -1;
  const int version_status = nc_inq_varid(ncid, "TKversion", &variable);
  if (version_status == NC_ENOTVAR) {
    nc_ok(nc_close(ncid), "close legacy restart");
    return;
  }
  nc_ok(version_status, "find TKversion");

  const size_t point[] = {static_cast<size_t>(row),
                          static_cast<size_t>(column)};
  nc_ok(nc_get_var1_int(ncid, variable, point, &data.TKversion),
        "read TKversion");
  nc_ok(nc_inq_varid(ncid, "TKactive", &variable), "find TKactive");
  nc_ok(nc_get_var1_int(ncid, variable, point, &data.TKactive),
        "read TKactive");
  nc_ok(nc_inq_varid(ncid, "TKpuddle", &variable), "find TKpuddle");
  nc_ok(nc_get_var1_double(ncid, variable, point, &data.TKpuddle),
        "read TKpuddle");

  const size_t start3[] = {point[0], point[1], 0};
  size_t count3[] = {1, 1, ThermokarstState::COUNT};
  nc_ok(nc_inq_varid(ncid, "TKstate", &variable), "find TKstate");
  int state_dims[3]={-1,-1,-1};
  size_t stored_state_count=0;
  nc_ok(nc_inq_vardimid(ncid,variable,state_dims),"find TKstate dimensions");
  nc_ok(nc_inq_dimlen(ncid,state_dims[2],&stored_state_count),
        "read thermokarst_state length");
  count3[2]=std::min(stored_state_count,
                     static_cast<size_t>(ThermokarstState::COUNT));
  nc_ok(nc_get_vara_double(ncid, variable, start3, count3, data.TKstate),
        "read TKstate");
  count3[2] = MAX_SOI_LAY;
  nc_ok(nc_inq_varid(ncid, "TKmatrix", &variable), "find TKmatrix");
  nc_ok(nc_get_vara_double(ncid, variable, start3, count3, data.TKmatrix),
        "read TKmatrix");
  nc_ok(nc_inq_varid(ncid, "TKporosity", &variable), "find TKporosity");
  nc_ok(nc_get_vara_double(ncid, variable, start3, count3, data.TKporosity),
        "read TKporosity");
  nc_ok(nc_inq_varid(ncid, "TKexcess", &variable), "find TKexcess");
  nc_ok(nc_get_vara_double(ncid, variable, start3, count3, data.TKexcess),
        "read TKexcess");
  nc_ok(nc_close(ncid), "close thermokarst restart");
}

void write_netcdf_fields(const RestartData& data, const char* filename, int row,
                         int column) {
  int ncid = -1;
  nc_ok(nc_open(filename, NC_WRITE, &ncid), "open thermokarst restart");
  int variable = -1;
  const size_t point[] = {static_cast<size_t>(row),
                          static_cast<size_t>(column)};
  nc_ok(nc_inq_varid(ncid, "TKversion", &variable), "find TKversion");
  nc_ok(nc_put_var1_int(ncid, variable, point, &data.TKversion),
        "write TKversion");
  nc_ok(nc_inq_varid(ncid, "TKactive", &variable), "find TKactive");
  nc_ok(nc_put_var1_int(ncid, variable, point, &data.TKactive),
        "write TKactive");
  nc_ok(nc_inq_varid(ncid, "TKpuddle", &variable), "find TKpuddle");
  nc_ok(nc_put_var1_double(ncid, variable, point, &data.TKpuddle),
        "write TKpuddle");

  const size_t start3[] = {point[0], point[1], 0};
  size_t count3[] = {1, 1, ThermokarstState::COUNT};
  nc_ok(nc_inq_varid(ncid, "TKstate", &variable), "find TKstate");
  nc_ok(nc_put_vara_double(ncid, variable, start3, count3, data.TKstate),
        "write TKstate");
  count3[2] = MAX_SOI_LAY;
  nc_ok(nc_inq_varid(ncid, "TKmatrix", &variable), "find TKmatrix");
  nc_ok(nc_put_vara_double(ncid, variable, start3, count3, data.TKmatrix),
        "write TKmatrix");
  nc_ok(nc_inq_varid(ncid, "TKporosity", &variable), "find TKporosity");
  nc_ok(nc_put_vara_double(ncid, variable, start3, count3,
                           data.TKporosity),
        "write TKporosity");
  nc_ok(nc_inq_varid(ncid, "TKexcess", &variable), "find TKexcess");
  nc_ok(nc_put_vara_double(ncid, variable, start3, count3, data.TKexcess),
        "write TKexcess");
  nc_ok(nc_close(ncid), "close thermokarst restart");
}

} // namespace restart_thermokarst

void RestartData::read_px_thermokarst_vars(const std::string& filename, int row,
                                           int column) {
  restart_thermokarst::read_netcdf_fields(*this, filename.c_str(), row, column);
}

void RestartData::write_px_thermokarst_vars(const std::string& filename, int row,
                                            int column) {
  restart_thermokarst::write_netcdf_fields(*this, filename.c_str(), row,
                                           column);
}
