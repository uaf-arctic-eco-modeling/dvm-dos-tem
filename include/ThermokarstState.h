#ifndef TEM_THERMOKARST_STATE_H
#define TEM_THERMOKARST_STATE_H
// Fixed POD layout, shared by Ground and NetCDF/MPI restart serialization.
struct ThermokarstState {
  enum Field { ELEVATION, SUBSIDENCE, SURFACE_MASS, SURFACE_ENERGY,
    EXPORTED_WATER, EXPORTED_ENERGY, BOUNDARY_ENERGY, WATER_RESIDUAL,
    ENERGY_RESIDUAL, HYDROLOGY_ENERGY, GENERATED_WATER, TRACER_STORAGE,
    TRACER_RUNOFF, TRACER_DRAINAGE, TRACER_OTHER,
    FIRE_RELEASED_WATER, FIRE_EXPORTED_ENERGY, FIRE_MATRIX_LOSS,
    FIRE_ROUTED_LIQUID, COUNT };
  bool enabled = false;
  double value[COUNT] = {};
  double pending_runoff = 0.; // consumed once by TEM hydrology; not a second store
  double pending_generated = 0.; // diagnosed source water awaiting daily partitioning
};
#endif
