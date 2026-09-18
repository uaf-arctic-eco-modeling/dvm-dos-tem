#include "../../include/Thermokarst.h"
#include "../../include/physicalconst.h"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <functional>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
using namespace thermokarst;
void check(bool ok, const char *msg) {
  if (!ok)
    throw std::runtime_error(msg);
}
void near(double a, double b, double tol = 1e-9) {
  if (!std::isfinite(a) || !std::isfinite(b) ||
      std::abs(a - b) >
          tol * std::max(1., std::max(std::abs(a), std::abs(b)))) {
    std::ostringstream s;
    s << "expected " << b << ", got " << a;
    throw std::runtime_error(s.str());
  }
}
void rejects(const std::function<void()> &f) {
  bool threw = false;
  try {
    f();
  } catch (const std::invalid_argument &) {
    threw = true;
  }
  check(threw, "invalid input accepted");
}
Column fixture(double x = 0.2, double t = 0.) {
  Column c;
  Cell a;
  a.matrix = .5;
  a.porosity = .5;
  a.ice = .5 * .5 * DENICE;
  a.excess = x * DENICE;
  a.pools = {{10., 20., 30., 40., 5., 2.}};
  a.set_temperature(t);
  c.cells.push_back(a);
  c.validate();
  return c;
}
void conserved(const Budget &a, const Budget &b, double energy = 0.) {
  near(a.water, b.water);
  near(a.energy + energy, b.energy, 1e-8);
  near(a.matrix, b.matrix);
  for (unsigned i = 0; i < 6; ++i)
    near(a.pools[i], b.pools[i]);
}
int main(int argc, char **argv) {
  std::ofstream results(argc > 1 ? argv[1] : "test_results.csv");
  if (!results) {
    std::cerr << "Cannot open results file\n";
    return 2;
  }
  results << "test,status\n";
  int pass = 0, fail = 0;
  auto run = [&](const char *name, const std::function<void()> &fn) {
    try {
      fn();
      ++pass;
      results << name << ",PASS\n";
      std::cout << "PASS " << name << '\n';
    } catch (const std::exception &e) {
      ++fail;
      results << name << ",FAIL\n";
      std::cerr << "FAIL " << name << ": " << e.what() << '\n';
    }
  };
  run("no_heat_no_change", [] {
    auto c = fixture(.2, -2.);
    auto b = c.budget();
    c.add_energy({0.});
    conserved(b, c.budget());
    near(c.subsidence, 0.);
  });
  run("zero_excess_no_subsidence", [] {
    auto c = fixture(0.);
    c.add_energy({1e8});
    near(c.subsidence, 0.);
    near(c.surface, 0.);
  });
  run("sensible_heat_before_melt", [] {
    auto c = fixture(.2, -2.);
    double e = c.cells[0].capacity();
    c.add_energy({e});
    near(c.cells[0].temperature(), -1.);
    near(c.subsidence, 0.);
  });
  run("pore_ice_melts_first", [] {
    auto c = fixture();
    double e = .5 * c.cells[0].ice * LHFUS;
    c.add_energy({e});
    near(c.cells[0].water, e / LHFUS);
    near(c.subsidence, 0.);
  });
  run("partial_excess_analytical", [] {
    auto c = fixture();
    auto b = c.budget();
    double e = (c.cells[0].ice + .05 * DENICE) * LHFUS;
    c.add_energy({e});
    near(c.subsidence, .05);
    near(c.cells[0].excess, .15 * DENICE);
    conserved(b, c.budget(), e);
  });
  run("complete_collapse_fixed_base", [] {
    auto c = fixture();
    double base = c.surface - c.depth();
    auto b = c.budget();
    double e = c.cells[0].mass() * LHFUS;
    c.add_energy({e});
    near(c.subsidence, .2);
    near(c.cells[0].thickness(), .5);
    near(c.surface - c.depth(), base);
    conserved(b, c.budget(), e);
  });
  run("melt_energy_exactly_once", [] {
    auto c = fixture();
    double m = c.cells[0].mass();
    c.add_energy({m * LHFUS});
    near(c.cells[0].temperature(), 0.);
    near(c.boundary_energy, m * LHFUS);
  });
  run("closed_overflow_retained", [] {
    auto c = fixture();
    double m = c.cells[0].mass();
    c.add_energy({m * LHFUS});
    near(c.surface_mass, m - 250.);
    near(c.runoff_mass, 0.);
    near(c.cells[0].water, 250.);
  });
  run("drained_water_and_energy", [] {
    auto c = fixture();
    c.pond_capacity = 0.;
    auto b = c.budget();
    double e = c.cells[0].mass() * LHFUS + 1e6;
    c.add_energy({e});
    check(c.runoff_mass > 0., "no runoff");
    near(c.surface_mass, 0.);
    conserved(b, c.budget(), e);
  });
  run("finite_pond_capacity", [] {
    auto c = fixture();
    c.pond_capacity = 10.;
    double m = c.cells[0].mass();
    c.add_energy({m * LHFUS});
    near(c.surface_mass, 10.);
    near(c.runoff_mass, m - 260.);
  });
  run("refreeze_no_heave_or_excess_creation", [] {
    auto c = fixture();
    auto b = c.budget();
    double e = c.cells[0].mass() * LHFUS;
    c.add_energy({e});
    c.add_energy({-c.cells[0].enthalpy - 1e6});
    near(c.subsidence, .2);
    near(c.cells[0].excess, 0.);
    check(c.cells[0].temperature() < 0., "not frozen");
    conserved(b, c.budget(), c.boundary_energy);
  });
  run("frozen_overflow_is_not_runoff", [] {
    auto c = fixture();
    c.pond_capacity = 0.;
    c.add_energy({c.cells[0].mass() * LHFUS});
    double runoff = c.runoff_mass;
    auto b = c.budget();
    double e = -c.cells[0].enthalpy - 1e6;
    c.add_energy({e});
    near(c.runoff_mass, runoff);
    check(c.surface_mass > 0., "missing surface ice");
    check(c.surface_energy < 0., "surface ice should be cold");
    conserved(b, c.budget(), e);
  });
  run("conservative_split_and_merge", [] {
    auto c = fixture(.2, -2.);
    auto b = c.budget();
    c.regrid({.1, .2, .4});
    conserved(b, c.budget());
    c.regrid({.7});
    conserved(b, c.budget());
    near(c.cells[0].temperature(), -2.);
    near(c.subsidence, 0.);
  });
  run("heterogeneous_frozen_enthalpy_remap", [] {
    auto c = fixture(.2, -2.);
    Cell d = c.cells[0];
    d.matrix = .3;
    d.porosity = .3;
    d.ice = 40.;
    d.excess = 0.;
    d.solid_heat = 3e6;
    d.set_temperature(-8.);
    c.cells.push_back(d);
    auto b = c.budget();
    c.regrid({1.});
    conserved(b, c.budget());
    check(c.cells[0].temperature() < -2. && c.cells[0].temperature() > -8.,
          "temperature outside donors");
  });
  run("all_six_pools_survive_repeated_regrid", [] {
    auto c = fixture(.2, -2.);
    auto b = c.budget();
    for (int i = 0; i < 100; ++i) {
      c.regrid({.1, .2, .4});
      c.regrid({.7});
    }
    conserved(b, c.budget());
  });
  run("material_boundary_rejected_atomically", [] {
    auto c = fixture();
    Cell d = c.cells[0];
    d.material = 1;
    c.cells.push_back(d);
    auto b = c.budget();
    rejects([&] { c.regrid({1.4}); });
    conserved(b, c.budget());
    check(c.cells.size() == 2, "changed after failed remap");
  });
  run("phase_boundary_not_smeared", [] {
    auto c = fixture(.2, -2.);
    Cell d = c.cells[0];
    d.excess = 0.;
    d.ice = 0.;
    d.water = 100.;
    d.set_temperature(5.);
    c.cells.push_back(d);
    rejects([&] { c.regrid({1.2}); });
  });
  run("invalid_grid_and_nan_rejected", [] {
    auto c = fixture();
    rejects([&] { c.regrid({.8}); });
    rejects([&] { c.regrid({0., .7}); });
    rejects([&] { c.add_energy({std::numeric_limits<double>::quiet_NaN()}); });
    rejects([&] { c.advance(-1., 2.); });
  });
  run("invalid_initial_state_rejected", [] {
    auto c = fixture();
    c.cells[0].porosity = 1.;
    rejects([&] { c.validate(); });
    c = fixture();
    c.cells[0].water = 1000.;
    rejects([&] { c.validate(); });
  });
  run("adaptive_split_layer_limit", [] {
    auto c = fixture(.2, -2.);
    auto b = c.budget();
    c.split_thick(.11);
    check(c.cells.size() == 7, "wrong split count");
    for (auto &x : c.cells)
      check(x.thickness() <= .11, "thick cell");
    conserved(b, c.budget());
  });
  run("isothermal_conduction_equilibrium", [] {
    auto c = fixture(.2, -2.);
    c.split_thick(.1);
    auto b = c.budget();
    c.advance(86400., -2.);
    conserved(b, c.budget());
    near(c.subsidence, 0.);
  });
  run("conduction_boundary_budget", [] {
    auto c = fixture(.2, -2.);
    c.split_thick(.1);
    auto b = c.budget();
    c.advance(30. * 86400., 10., .05);
    conserved(b, c.budget(), c.boundary_energy);
    check(c.boundary_energy > 0., "no warming");
  });
  run("restart_roundtrip_all_fields", [] {
    auto c = fixture();
    c.pond_capacity = 5.;
    c.add_energy({c.cells[0].mass() * LHFUS});
    c.elapsed = 123.;
    std::stringstream s;
    c.write_restart(s);
    auto d = Column::read_restart(s);
    std::stringstream t, u;
    c.write_restart(t);
    d.write_restart(u);
    check(t.str() == u.str(), "restart differs");
  });
  run("restart_continuation", [] {
    auto c = fixture(.2, -2.);
    c.split_thick(.1);
    c.advance(10. * 86400., 8.);
    std::stringstream s;
    c.write_restart(s);
    auto d = Column::read_restart(s);
    c.advance(20. * 86400., 8.);
    d.advance(20. * 86400., 8.);
    std::stringstream a, b;
    c.write_restart(a);
    d.write_restart(b);
    check(a.str() == b.str(), "continuation differs");
  });
  run("malformed_restart_rejected", [] {
    std::stringstream a("TEM_THERMOKARST 99\n");
    rejects([&] { Column::read_restart(a); });
    std::stringstream b("TEM_THERMOKARST 1\n1\n");
    rejects([&] { Column::read_restart(b); });
  });
  run("heat_pulse_timestep_independence", [] {
    auto a = fixture(), b = a;
    const double e = (a.cells[0].ice + .1 * DENICE) * LHFUS;
    a.add_energy({e});
    for (int i = 0; i < 100; ++i)
      b.add_energy({e / 100.});
    near(a.subsidence, b.subsidence);
    conserved(a.budget(), b.budget());
  });
  run("vanishing_snow_film_does_not_underflow_timestep", [] {
    auto c = fixture(.2, -5.);
    Cell snow;
    snow.material = SNOW_MATERIAL;
    snow.matrix = 1e-5;
    snow.porosity = 1.;
    snow.ice = 1e-4;
    snow.solid_k = .25;
    snow.solid_heat = 1.;
    snow.set_temperature(-5.);
    c.cells.insert(c.cells.begin(), snow);
    auto b = c.budget();
    c.advance(86400., -5.);
    conserved(b, c.budget());
    near(c.cells[1].temperature(), -5., 1e-6);
  });
  run("empty_snow_and_puddle_do_not_underflow", [] {
    auto c = fixture(.2, -8.);
    Cell snow;
    snow.material = SNOW_MATERIAL;
    snow.matrix = 2e-3;
    snow.porosity = 1.;
    snow.ice = 1e-6;
    snow.solid_k = .05;
    snow.solid_heat = 1.;
    snow.set_temperature(-8.);
    c.cells.insert(c.cells.begin(), snow);
    c.pond_capacity = 4.;
    c.accept_surface_water(4., LHFUS * 4.);
    auto b = c.budget();
    c.advance(86400., -8.);
    conserved(b, c.budget(), c.boundary_energy);
  });
  run("surface_reservoir_isothermal_with_snow", [] {
    auto c = fixture(.2, -5.);
    Cell snow;
    snow.material = SNOW_MATERIAL;
    snow.matrix = .15;
    snow.porosity = 1.;
    snow.ice = 40.;
    snow.solid_k = .25;
    snow.solid_heat = 1.;
    snow.set_temperature(-5.);
    c.cells.insert(c.cells.begin(), snow);
    c.surface_mass = 25.;
    c.surface_energy = 25. * SHCICE * (-5.);
    auto b = c.budget();
    c.advance(86400., -5.);
    conserved(b, c.budget());
    near(c.cells[0].temperature(), -5., 1e-6);
    near(c.cells[1].temperature(), -5., 1e-6);
    near(c.surface_energy, 25. * SHCICE * (-5.), 1e-6);
  });
  run("surface_reservoir_intercepts_atmospheric_heat", [] {
    auto bare = fixture(.2, -8.);
    auto ponded = bare;
    ponded.surface_mass = 80.;
    ponded.surface_energy = 80. * SHCICE * (-8.);
    const double ice0 = ponded.surface_energy;
    auto bb = ponded.budget();
    bare.advance(2. * 86400., 6.);
    ponded.advance(2. * 86400., 6.);
    conserved(bb, ponded.budget(), ponded.boundary_energy);
    check(ponded.surface_energy > ice0, "surface ice did not warm");
    check(ponded.cells[0].temperature() < bare.cells[0].temperature(),
          "pond/ice did not intercept atmospheric heat");
  });
  run("snow_pond_soil_thermal_sandwich", [] {
    auto c = fixture(.2, -1.);
    Cell snow;
    snow.material = SNOW_MATERIAL;
    snow.matrix = .2;
    snow.porosity = 1.;
    snow.ice = 60.;
    snow.solid_k = .2;
    snow.solid_heat = 1.;
    snow.set_temperature(-12.);
    c.cells.insert(c.cells.begin(), snow);
    c.surface_mass = 30.;
    c.surface_energy = 30. * SHCICE * (-6.);
    auto b = c.budget();
    c.advance(5. * 86400., -12.);
    conserved(b, c.budget(), c.boundary_energy);
    const double ice = std::max(0., c.surface_mass - std::max(0., std::min(c.surface_mass, c.surface_energy / LHFUS)));
    const double cap = ice * SHCICE + std::max(0., c.surface_mass - ice) * SHCLIQ;
    const double ts = cap > 0. ? (c.surface_energy - LHFUS * (c.surface_mass - ice)) / cap : 0.;
    check(ts > -12. && ts < c.cells[1].temperature() + 1e-8,
          "surface reservoir is not thermally between snow and soil");
  });
  run("overnight_puddle_is_thermal_mass", [] {
    auto bare = fixture(.2, -8.);
    auto ponded = bare;
    ponded.pond_capacity = 4.;
    ponded.accept_surface_water(4., LHFUS * 4.);
    auto b = ponded.budget();
    bare.advance(86400., -8.);
    ponded.advance(86400., -8.);
    conserved(b, ponded.budget(), ponded.boundary_energy);
    check(ponded.release_surface_liquid(4.) + ponded.surface_mass > 0.,
          "overnight puddle vanished");
    check(ponded.cells[0].temperature() > bare.cells[0].temperature(),
          "overnight puddle did not warm the soil");
  });
  run("matrix_topology_conserves_phase_water_and_six_pools", [] {
    std::vector<Cell> old(3);
    old[0].material=old[1].material=1;old[2].material=2;
    old[0].matrix=.2;old[1].matrix=.3;old[2].matrix=.5;
    for(unsigned i=0;i<old.size();++i) {
      old[i].porosity=.35+.05*i;old[i].solid_heat=2.e6+1.e5*i;
      old[i].solid_k=.4+.2*i;old[i].water=10.+i;old[i].ice=20.+2.*i;
      old[i].excess=30.+3.*i;old[i].enthalpy=-1.e7+2.e6*i;
      for(unsigned k=0;k<6;++k) old[i].pools[k]=(i+1.)*(k+1.);
    }
    const auto map=remap_matrix_topology(old,{.1,.25,.35,.4},{1,1,1,2});
    check(map.cells.size()==4,"wrong target layer count");
    double ow=0.,nw=0.,oe=0.,ne=0.;std::array<double,6> op={{0,0,0,0,0,0}},np=op;
    for(const auto& x:old){ow+=x.water+x.ice+x.excess;oe+=x.enthalpy;for(unsigned k=0;k<6;++k)op[k]+=x.pools[k];}
    for(const auto& x:map.cells){nw+=x.water+x.ice+x.excess;ne+=x.enthalpy;for(unsigned k=0;k<6;++k)np[k]+=x.pools[k];}
    near(nw,ow);near(ne,oe);for(unsigned k=0;k<6;++k)near(np[k],op[k]);
    near(map.cells[0].matrix,.1);near(map.cells[3].matrix,.4);
  });
  run("matrix_topology_conserves_roots_and_accumulators", [] {
    std::vector<Cell> old(2);old[0].material=old[1].material=3;
    old[0].matrix=.4;old[1].matrix=.6;
    const auto map=remap_matrix_topology(old,{.2,.3,.5},{3,3,3});
    const auto roots=remap_extensive(map.donor_fraction,{.25,.75});
    const auto drainage=remap_extensive(map.donor_fraction,{2.,7.});
    const auto temperature=remap_intensive(map.intensive_weight,{-8.,2.});
    double sr=0.,sd=0.;for(double x:roots)sr+=x;for(double x:drainage)sd+=x;
    near(sr,1.);near(sd,9.);
    for(double x:temperature)check(x>=-8.&&x<=2.,"intensive diagnostic outside donor range");
  });
  run("matrix_topology_rejects_material_reordering", [] {
    std::vector<Cell> old(2);old[0].material=1;old[1].material=2;
    old[0].matrix=old[1].matrix=.5;
    rejects([&]{remap_matrix_topology(old,{.5,.5},{2,1});});
  });
  run("fire_topology_partitions_consumed_matrix_water_and_energy", [] {
    std::vector<Cell> old(3);
    for(unsigned i=0;i<old.size();++i) {
      Cell& c=old[i];c.material=i<2?1:3;c.matrix=.2+.1*i;c.porosity=.5;
      c.solid_heat=2.e6;c.solid_k=.5;c.ice=40.+10.*i;c.excess=18.+4.*i;
      c.set_temperature(-2.-i);
      for(unsigned k=0;k<6;++k)c.pools[k]=(i+1.)*(k+1.);
    }
    const double burn=.25;
    const auto fire=remap_fire_topology(old,burn,{.18,.32,.38},{2,2,3});
    near(fire.surviving_fraction[0],0.);
    near(fire.surviving_fraction[1],1.-(burn-old[0].thickness())/old[1].thickness());
    double old_water=0.,mapped_water=0.,old_energy=0.,mapped_energy=0.;
    for(const auto& c:old){old_water+=c.mass();old_energy+=c.enthalpy;}
    for(const auto& c:fire.topology.cells){mapped_water+=c.mass();mapped_energy+=c.enthalpy;}
    near(mapped_water+fire.released_water,old_water);
    near(mapped_energy+fire.released_phase_energy+fire.exported_solid_energy,old_energy,1.e-8);
    near(fire.burned_matrix,
         old[0].matrix+(1.-fire.surviving_fraction[1])*old[1].matrix);
  });
  run("fire_topology_allows_horizon_loss_and_humification", [] {
    std::vector<Cell> old(3);
    old[0].material=1;old[1].material=2;old[2].material=3;
    for(unsigned i=0;i<old.size();++i) {
      old[i].matrix=.2;old[i].porosity=.5;old[i].ice=20.;old[i].set_temperature(-1.);
    }
    const auto fire=remap_fire_topology(old,old[0].thickness(),{.15,.25},{2,3});
    near(fire.surviving_fraction[0],0.);
    check(fire.topology.cells.size()==2,"wrong fire target layer count");
    check(fire.topology.cells[0].material==2,"post-fire material not prescribed");
  });
  run("fire_topology_rejects_burn_below_column", [] {
    auto c=fixture(.1,-2.);
    rejects([&]{remap_fire_topology(c.cells,2.,{.2},{1});});
  });
  std::cout << pass << " passed, " << fail << " failed\n";
  return fail ? 1 : 0;
}
