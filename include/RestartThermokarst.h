#ifndef RESTART_THERMOKARST_H
#define RESTART_THERMOKARST_H

class RestartData;

namespace restart_thermokarst {

void define_netcdf_fields(int ncid, int y_dim, int x_dim, int soil_dim);
void read_netcdf_fields(RestartData& data, const char* filename, int row,
                        int column);
void write_netcdf_fields(const RestartData& data, const char* filename, int row,
                         int column);

} // namespace restart_thermokarst

#endif
