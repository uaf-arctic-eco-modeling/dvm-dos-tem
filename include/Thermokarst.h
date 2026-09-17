#ifndef TEM_THERMOKARST_H
#define TEM_THERMOKARST_H

#include <array>
#include <iosfwd>
#include <vector>

// Experimental finite-volume column. Units: m, s, kg/m2, J/m2, degrees C.
// C/N pools use TEM's g/m2 convention. No dependency on the legacy Stefan
// solver.
namespace thermokarst {
// Reserved material identifiers used by the production snow/rock adapter.
const int SNOW_MATERIAL = -1;
const int ROCK_MATERIAL = -2;
struct Cell {
  int material = 0;
  double matrix = 0.1; // matrix thickness including ordinary pores
  double porosity = 0.5;
  double solid_heat = 2.0e6; // volumetric solid heat capacity J/m3/K
  double solid_k = 2.5;      // solid thermal conductivity W/m/K
  double water = 0.;         // liquid
  double ice = 0.;           // pore ice only
  double excess = 0.;        // segregated excess ice
  double enthalpy = 0.;      // ice at 0 C is the reference
  std::array<double, 6> pools{
      {0., 0., 0., 0., 0., 0.}}; // rawc,soma,sompr,somcr,orgn,avln
  double thickness() const;
  double mass() const;
  double capacity() const;
  double temperature() const;
  double conductivity() const;
  void set_temperature(double temperature);
};
struct Budget {
  double water = 0.;
  double energy = 0.;
  double matrix = 0.;
  std::array<double, 6> pools{{0., 0., 0., 0., 0., 0.}};
};
// Conservative mapping between two layerings of the same ordered material
// column. donor_fraction[i][j] is the fraction of old cell j assigned to new
// cell i. New matrix thickness is prescribed by the dynamic-soil grid; every
// extensive donor quantity is conserved within each material horizon.
struct TopologyMap {
  std::vector<Cell> cells;
  std::vector<std::vector<double> > donor_fraction;
  std::vector<std::vector<double> > intensive_weight;
};
TopologyMap remap_matrix_topology(const std::vector<Cell>& old_cells,
                                  const std::vector<double>& new_matrix,
                                  const std::vector<int>& new_material);
std::vector<double> remap_extensive(
    const std::vector<std::vector<double> >& donor_fraction,
    const std::vector<double>& old_values);
std::vector<double> remap_intensive(
    const std::vector<std::vector<double> >& intensive_weight,
    const std::vector<double>& old_values);
struct Column {
  std::vector<Cell> cells;
  double surface = 0.;
  double subsidence = 0.;
  double surface_mass = 0.; // retained overflow; can freeze, no heave
  double surface_energy = 0.;
  double runoff_mass = 0.; // cumulative exported mass and enthalpy
  double runoff_energy = 0.;
  double boundary_energy = 0.; // cumulative external energy input
  double elapsed = 0.;
  double pond_capacity =
      1000.; // liquid kg/m2; zero drains liquid, retains surface ice
  Budget budget() const; // includes surface store and exported water/energy
  double depth() const;
  void validate() const;
  // Re-equilibrate phases after an external hydrology operator at fixed enthalpy.
  void reconcile_phase();
  void add_energy(const std::vector<double> &joules);
  void advance(double seconds, double top_temperature, double basal_flux = 0.,
               double max_step = 3600.);
  void regrid(const std::vector<double> &target_thicknesses);
  void split_thick(double maximum_thickness);
  void write_restart(std::ostream &) const;
  static Column read_restart(std::istream &);

private:
  void equilibrate_and_settle();
  void route_surplus();
};
} // namespace thermokarst
#endif
