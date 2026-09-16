#ifndef TEM_THERMOKARST_INTEGRATION_H
#define TEM_THERMOKARST_INTEGRATION_H
#include "Ground.h"
namespace tem_thermokarst {
void initialize(Ground& ground, double fraction, double top, double bottom);
void advance(Ground& ground, double surface_temperature, double seconds);
void rebuild_fronts(Ground& ground, bool freezing);
}
#endif
