#ifndef TEM_THERMOKARST_INTEGRATION_H
#define TEM_THERMOKARST_INTEGRATION_H
#include "Ground.h"
#include "Thermokarst.h"
#include <array>
#include <vector>
namespace tem_thermokarst {
struct TopologySnapshot {
  std::vector<thermokarst::Cell> cells;
  bool freezing = false;
};
struct TopologyResult {
  thermokarst::TopologyMap map;
  double water_residual = 0.;
  double energy_residual = 0.;
  std::array<double, 6> pool_residual{{0.,0.,0.,0.,0.,0.}};
};
struct FireTopologyResult {
  thermokarst::FireTopologyMap fire;
  double water_residual = 0.;
  double energy_residual = 0.;
  double matrix_residual = 0.;
  std::array<double, 6> pool_residual{{0.,0.,0.,0.,0.,0.}};
};
void initialize(Ground& ground, double fraction, double top, double bottom);
void advance(Ground& ground, double surface_temperature, double seconds);
// puddle_mm is TEM's overnight hydrology pond (mm = kg m-2). It is merged
// into the thermokarst surface store for the thermal solve, then liquid
// that still fits pond_capacity_mm is returned for the day's hydrology.
void advance(Ground& ground, double surface_temperature, double seconds,
             double& puddle_mm, double pond_capacity_mm);
void rebuild_fronts(Ground& ground, bool freezing);
// Convert the physical column to its matrix-only geometry before the legacy
// dynamic-soil routine changes layer count and thickness. finish_topology_change
// then projects the saved conservative state onto that prescribed matrix grid.
TopologySnapshot prepare_topology_change(Ground& ground);
TopologyResult finish_topology_change(Ground& ground,
                                      const TopologySnapshot& snapshot);
// Finish a fire transaction after WildFire has changed the C/N pools and the
// legacy Ground routine has prescribed the post-combustion layer grid.
FireTopologyResult finish_fire_topology_change(
    Ground& ground,const TopologySnapshot& snapshot,double burned_depth);
}
#endif
