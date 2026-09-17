#include "../include/Thermokarst.h"
#include "../include/physicalconst.h"
#include <algorithm>
#include <cmath>
#include <iomanip>
#include <istream>
#include <ostream>
#include <stdexcept>
#include <string>

namespace thermokarst {
namespace {
void require(bool ok, const char *message) {
  if (!ok)
    throw std::invalid_argument(message);
}
bool nonnegative(double x) { return std::isfinite(x) && x >= 0.; }
int phase(const Cell &c) {
  if (c.enthalpy < 0.)
    return -1;
  if (c.enthalpy > LHFUS * c.mass())
    return 1;
  return 0;
}
// Phase equilibrium with pore ice melting before excess ice. Excess ice never
// regenerates. This is a documented first-prototype subgrid closure.
void equilibrate(Cell &c) {
  const double m = c.mass();
  const double liquid = std::max(0., std::min(m, c.enthalpy / LHFUS));
  const double frozen = m - liquid;
  c.excess = std::min(c.excess, frozen);
  c.ice = frozen - c.excess;
  c.water = liquid;
}
} // namespace
double Cell::thickness() const { return matrix + excess / DENICE; }
double Cell::mass() const { return water + ice + excess; }
double Cell::capacity() const {
  return (material == SNOW_MATERIAL ? 0. : matrix * (1. - porosity) * solid_heat) + water * SHCLIQ +
         (ice + excess) * SHCICE;
}
double Cell::temperature() const {
  return (enthalpy - LHFUS * water) / capacity();
}
void Cell::set_temperature(double t) {
  require(std::isfinite(t), "nonfinite temperature");
  require(!(t < 0. && water > 0.) && !(t > 0. && ice + excess > 0.),
          "initial phases inconsistent with temperature");
  enthalpy = capacity() * t + LHFUS * water;
}
double Cell::conductivity() const {
  if (material == SNOW_MATERIAL) return solid_k;
  const double d = thickness();
  const double solid = matrix * (1. - porosity) / d;
  const double liquid = water / DENLIQ / d;
  const double frozen = (ice + excess) / DENICE / d;
  const double air = std::max(0., 1. - solid - liquid - frozen);
  // Geometric mixture; a prototype closure, not a calibrated TEM replacement.
  return std::pow(solid_k, solid) * std::pow(TCLIQ, liquid) *
         std::pow(TCICE, frozen) * std::pow(TCAIR, air);
}
double Column::depth() const {
  double d = 0.;
  for (const auto &c : cells)
    d += c.thickness();
  return d;
}
Budget Column::budget() const {
  Budget b;
  b.water = surface_mass + runoff_mass;
  b.energy = surface_energy + runoff_energy;
  for (const auto &c : cells) {
    b.water += c.mass();
    b.energy += c.enthalpy;
    b.matrix += c.matrix;
    for (unsigned k = 0; k < 6; ++k)
      b.pools[k] += c.pools[k];
  }
  return b;
}
std::vector<double> remap_extensive(
    const std::vector<std::vector<double> >& weights,
    const std::vector<double>& old_values) {
  require(!weights.empty(), "empty topology map");
  std::vector<double> result(weights.size(), 0.);
  for (unsigned i=0;i<weights.size();++i) {
    require(weights[i].size()==old_values.size(), "topology map width mismatch");
    for (unsigned j=0;j<old_values.size();++j) {
      require(std::isfinite(weights[i][j]) && weights[i][j]>=0.,
              "invalid topology remap weight");
      require(std::isfinite(old_values[j]),
              "nonfinite topology donor value");
      result[i]+=weights[i][j]*old_values[j];
    }
  }
  return result;
}
std::vector<double> remap_intensive(
    const std::vector<std::vector<double> >& weights,
    const std::vector<double>& old_values) {
  return remap_extensive(weights,old_values);
}
TopologyMap remap_matrix_topology(const std::vector<Cell>& old_cells,
                                  const std::vector<double>& new_matrix,
                                  const std::vector<int>& new_material) {
  require(!old_cells.empty() && !new_matrix.empty() &&
          new_matrix.size()==new_material.size(), "invalid topology map shape");
  const unsigned no=old_cells.size(),nn=new_matrix.size();
  TopologyMap map;map.cells.resize(nn);
  map.donor_fraction.assign(nn,std::vector<double>(no,0.));
  map.intensive_weight.assign(nn,std::vector<double>(no,0.));
  for(double d:new_matrix) require(std::isfinite(d)&&d>1.e-9,"invalid target matrix thickness");
  // Treat each contiguous material horizon independently. Normalized material
  // coordinates allow a SOM-driven horizon thickness change while assigning
  // every old extensive quantity exactly once.
  unsigned ob=0,nb=0;
  while(ob<no || nb<nn) {
    require(ob<no && nb<nn,"material horizon missing from target topology");
    const int material=old_cells[ob].material;
    require(new_material[nb]==material,"material horizon order changed");
    unsigned oe=ob,ne=nb;
    while(oe<no && old_cells[oe].material==material) ++oe;
    while(ne<nn && new_material[ne]==material) ++ne;
    double old_total=0.,new_total=0.;
    for(unsigned j=ob;j<oe;++j) {require(old_cells[j].matrix>1.e-9,"invalid donor matrix thickness");old_total+=old_cells[j].matrix;}
    for(unsigned i=nb;i<ne;++i) new_total+=new_matrix[i];
    double ntop=0.;
    for(unsigned i=nb;i<ne;++i) {
      const double nbot=ntop+new_matrix[i]/new_total;
      double otop=0.;
      for(unsigned j=ob;j<oe;++j) {
        const double obot=otop+old_cells[j].matrix/old_total;
        const double overlap=std::max(0.,std::min(nbot,obot)-std::max(ntop,otop));
        if(overlap>0.) {
          map.donor_fraction[i][j]=overlap/(obot-otop);
          map.intensive_weight[i][j]=overlap/(nbot-ntop);
        }
        otop=obot;
      }
      ntop=nbot;
    }
    ob=oe;nb=ne;
  }
  std::vector<double> water(no),ice(no),excess(no),enthalpy(no),porosity(no),solid_heat(no),solid_k(no);
  std::array<std::vector<double>,6> pools;
  for(unsigned j=0;j<no;++j) {
    water[j]=old_cells[j].water;ice[j]=old_cells[j].ice;excess[j]=old_cells[j].excess;
    enthalpy[j]=old_cells[j].enthalpy;porosity[j]=old_cells[j].porosity;
    solid_heat[j]=old_cells[j].solid_heat;solid_k[j]=old_cells[j].solid_k;
    for(unsigned k=0;k<6;++k)pools[k].push_back(old_cells[j].pools[k]);
  }
  const auto rw=remap_extensive(map.donor_fraction,water),ri=remap_extensive(map.donor_fraction,ice),
    rx=remap_extensive(map.donor_fraction,excess),rh=remap_extensive(map.donor_fraction,enthalpy),
    rp=remap_intensive(map.intensive_weight,porosity),rc=remap_intensive(map.intensive_weight,solid_heat),
    rk=remap_intensive(map.intensive_weight,solid_k);
  std::array<std::vector<double>,6> remapped_pools;
  for(unsigned k=0;k<6;++k)
    remapped_pools[k]=remap_extensive(map.donor_fraction,pools[k]);
  for(unsigned i=0;i<nn;++i) {
    Cell& c=map.cells[i];c.material=new_material[i];c.matrix=new_matrix[i];c.porosity=rp[i];
    c.solid_heat=rc[i];c.solid_k=rk[i];c.water=rw[i];c.ice=ri[i];c.excess=rx[i];c.enthalpy=rh[i];
    for(unsigned k=0;k<6;++k)c.pools[k]=remapped_pools[k][i];
  }
  // Every donor fraction must sum to one and every intensive target row to one.
  for(unsigned j=0;j<no;++j){double s=0.;for(unsigned i=0;i<nn;++i)s+=map.donor_fraction[i][j];require(std::abs(s-1.)<1.e-10,"incomplete donor coverage");}
  for(unsigned i=0;i<nn;++i){double s=0.;for(double w:map.intensive_weight[i])s+=w;require(std::abs(s-1.)<1.e-10,"incomplete target coverage");}
  return map;
}
FireTopologyMap remap_fire_topology(const std::vector<Cell>& old_cells,
                                    double burned_physical_depth,
                                    const std::vector<double>& new_matrix,
                                    const std::vector<int>& new_material) {
  require(!old_cells.empty() && !new_matrix.empty() &&
          new_matrix.size()==new_material.size(),"invalid fire topology shape");
  require(std::isfinite(burned_physical_depth) && burned_physical_depth>=0.,
          "invalid fire burn depth");
  FireTopologyMap result;
  const unsigned no=old_cells.size(),nn=new_matrix.size();
  result.surviving_fraction.assign(no,1.);
  double remaining=burned_physical_depth;
  for(unsigned j=0;j<no && remaining>0.;++j) {
    const double thickness=old_cells[j].thickness();
    require(std::isfinite(thickness) && thickness>1.e-9,
            "invalid fire donor thickness");
    const double consumed=std::min(remaining,thickness);
    result.surviving_fraction[j]=1.-consumed/thickness;
    remaining-=consumed;
  }
  require(remaining<=1.e-9*std::max(1.,burned_physical_depth),
          "fire burn depth exceeds soil column");
  double survivor_matrix=0.,target_matrix=0.;
  for(unsigned j=0;j<no;++j) survivor_matrix+=old_cells[j].matrix*result.surviving_fraction[j];
  for(double d:new_matrix) {
    require(std::isfinite(d) && d>1.e-9,"invalid fire target thickness");
    target_matrix+=d;
  }
  require(survivor_matrix>1.e-9 && target_matrix>1.e-9,
          "fire removed complete soil column");
  TopologyMap& map=result.topology;
  map.cells.resize(nn);map.donor_fraction.assign(nn,std::vector<double>(no,0.));
  map.intensive_weight.assign(nn,std::vector<double>(no,0.));
  double ntop=0.;
  for(unsigned i=0;i<nn;++i) {
    const double nbot=ntop+new_matrix[i]/target_matrix;
    double otop=0.;
    for(unsigned j=0;j<no;++j) {
      const double span=old_cells[j].matrix*result.surviving_fraction[j]/survivor_matrix;
      const double obot=otop+span;
      const double overlap=std::max(0.,std::min(nbot,obot)-std::max(ntop,otop));
      if(overlap>0. && span>0.) {
        map.donor_fraction[i][j]=result.surviving_fraction[j]*overlap/span;
        map.intensive_weight[i][j]=overlap/(nbot-ntop);
      }
      otop=obot;
    }
    ntop=nbot;
  }
  std::vector<double> water(no),ice(no),excess(no),enthalpy(no),porosity(no),solid_heat(no),solid_k(no);
  std::array<std::vector<double>,6> pools;
  for(unsigned j=0;j<no;++j) {
    const Cell& c=old_cells[j];const double burned=1.-result.surviving_fraction[j];
    require(std::isfinite(c.water),"nonfinite fire donor liquid");
    require(std::isfinite(c.ice),"nonfinite fire donor pore ice");
    require(std::isfinite(c.excess),"nonfinite fire donor excess ice");
    require(std::isfinite(c.enthalpy),"nonfinite fire donor enthalpy");
    require(std::isfinite(c.porosity),"nonfinite fire donor porosity");
    require(std::isfinite(c.solid_heat),"nonfinite fire donor heat capacity");
    require(std::isfinite(c.solid_k),"nonfinite fire donor conductivity");
    for(unsigned k=0;k<6;++k)require(std::isfinite(c.pools[k]),"nonfinite fire donor C/N pool");
    water[j]=c.water;ice[j]=c.ice;excess[j]=c.excess;enthalpy[j]=c.enthalpy;
    porosity[j]=c.porosity;solid_heat[j]=c.solid_heat;solid_k[j]=c.solid_k;
    for(unsigned k=0;k<6;++k)pools[k].push_back(c.pools[k]);
    result.burned_matrix+=burned*c.matrix;
    result.released_liquid+=burned*c.water;
    result.released_ice+=burned*c.ice;
    result.released_excess+=burned*c.excess;
    const double temperature=c.temperature();
    result.released_phase_energy+=burned*((c.water*SHCLIQ+(c.ice+c.excess)*SHCICE)*temperature+LHFUS*c.water);
    result.exported_solid_energy+=burned*c.matrix*(1.-c.porosity)*c.solid_heat*temperature;
  }
  result.released_water=result.released_liquid+result.released_ice+result.released_excess;
  const auto rw=remap_extensive(map.donor_fraction,water),ri=remap_extensive(map.donor_fraction,ice),
    rx=remap_extensive(map.donor_fraction,excess),rh=remap_extensive(map.donor_fraction,enthalpy),
    rp=remap_intensive(map.intensive_weight,porosity),rc=remap_intensive(map.intensive_weight,solid_heat),
    rk=remap_intensive(map.intensive_weight,solid_k);
  std::array<std::vector<double>,6> remapped_pools;
  for(unsigned k=0;k<6;++k)remapped_pools[k]=remap_extensive(map.donor_fraction,pools[k]);
  for(unsigned i=0;i<nn;++i) {
    Cell& c=map.cells[i];c.material=new_material[i];c.matrix=new_matrix[i];c.porosity=rp[i];
    c.solid_heat=rc[i];c.solid_k=rk[i];c.water=rw[i];c.ice=ri[i];c.excess=rx[i];c.enthalpy=rh[i];
    for(unsigned k=0;k<6;++k)c.pools[k]=remapped_pools[k][i];
  }
  for(unsigned j=0;j<no;++j){double s=0.;for(unsigned i=0;i<nn;++i)s+=map.donor_fraction[i][j];
    require(std::abs(s-result.surviving_fraction[j])<1.e-10,"incomplete fire donor coverage");}
  for(unsigned i=0;i<nn;++i){double s=0.;for(double w:map.intensive_weight[i])s+=w;
    require(std::abs(s-1.)<1.e-10,"incomplete fire target coverage");}
  return result;
}
void Column::validate() const {
  require(!cells.empty() && cells.size() <= 10000, "invalid layer count");
  require(std::isfinite(surface) && nonnegative(subsidence) &&
              nonnegative(surface_mass) && nonnegative(runoff_mass) &&
              std::isfinite(surface_energy) && std::isfinite(runoff_energy) &&
              std::isfinite(boundary_energy) && nonnegative(elapsed) &&
              nonnegative(pond_capacity),
          "invalid column state");
  const double surface_liquid =
      std::max(0., std::min(surface_mass, surface_energy / LHFUS));
  require(surface_liquid <= pond_capacity + 1e-8,
          "surface liquid exceeds capacity");
  require(surface_mass > 0. || std::abs(surface_energy) < 1e-8,
          "energy without surface mass");
  for (const auto &c : cells) {
    require(std::isfinite(c.matrix) && c.matrix > 1e-9 &&
                std::isfinite(c.porosity) && c.porosity >= 0. &&
                (c.porosity < 1. || (c.material == SNOW_MATERIAL && c.porosity == 1.)) && std::isfinite(c.solid_heat) &&
                c.solid_heat > 0. && std::isfinite(c.solid_k) && c.solid_k > 0.,
            "invalid matrix properties");
    require(nonnegative(c.water) && nonnegative(c.ice) &&
                nonnegative(c.excess) && std::isfinite(c.enthalpy),
            "invalid water/energy state");
    require(c.material == SNOW_MATERIAL || c.water / DENLIQ + c.ice / DENICE <= c.matrix * c.porosity + 1e-9,
            "ordinary water exceeds pore capacity");
    const double t = c.temperature();
    require(std::isfinite(t) && !(t < -1e-8 && c.water > 1e-8) &&
                !(t > 1e-8 && c.ice + c.excess > 1e-8),
            "nonequilibrium phase state");
    for (double p : c.pools)
      require(nonnegative(p), "invalid C/N pool");
  }
}
void Column::route_surplus() {
  // Local overflow to a surface reservoir, not a Richards-flow approximation.
  // Frozen overflow on refreezing is retained as surface ice; only liquid runs
  // off.
  for (auto &c : cells) {
    if (c.material == SNOW_MATERIAL) continue;
    const double pore = c.matrix * c.porosity;
    const double temp = c.temperature();
    const double extra_ice = std::max(0., c.ice - pore * DENICE);
    if (extra_ice > 0.) {
      const double e = extra_ice * SHCICE * temp;
      c.ice -= extra_ice;
      c.enthalpy -= e;
      surface_mass += extra_ice;
      surface_energy += e;
    }
    const double cap = std::max(0., (pore - c.ice / DENICE) * DENLIQ);
    const double extra = std::max(0., c.water - cap);
    const double e = extra * (LHFUS + SHCLIQ * temp);
    c.water -= extra;
    c.enthalpy -= e;
    surface_mass += extra;
    surface_energy += e;
  }
  const double liquid =
      std::max(0., std::min(surface_mass, surface_energy / LHFUS));
  if (liquid > pond_capacity) {
    const double out = liquid - pond_capacity;
    const double specific = (liquid == surface_mass)
                                ? surface_energy / surface_mass
                                : double(LHFUS);
    const double e = out * specific;
    runoff_mass += out;
    runoff_energy += e;
    surface_mass -= out;
    surface_energy -= e;
  }
}
void Column::equilibrate_and_settle() {
  double collapse = 0.;
  for (auto &c : cells) {
    const double x = c.excess;
    equilibrate(c);
    collapse += (x - c.excess) / DENICE;
  }
  surface -= collapse;
  subsidence += collapse;
  route_surplus();
}
void Column::reconcile_phase() {
  for (const auto& c : cells) {
    require(std::isfinite(c.matrix) && c.matrix > 1e-9 &&
      nonnegative(c.water) && nonnegative(c.ice) && nonnegative(c.excess) &&
      std::isfinite(c.enthalpy) && std::isfinite(c.capacity()) && c.capacity()>0.,
      "invalid imported thermodynamic state");
  }
  equilibrate_and_settle();
  validate();
}
void Column::add_energy(const std::vector<double> &joules) {
  validate();
  require(joules.size() == cells.size(), "one energy input required per layer");
  for (double e : joules)
    require(std::isfinite(e), "nonfinite energy input");
  for (unsigned i = 0; i < cells.size(); ++i) {
    cells[i].enthalpy += joules[i];
    boundary_energy += joules[i];
  }
  equilibrate_and_settle();
  validate();
}
void Column::advance(double seconds, double top_temperature, double basal_flux,
                     double max_step) {
  validate();
  require(nonnegative(seconds) && std::isfinite(top_temperature) &&
              std::isfinite(basal_flux) && std::isfinite(max_step) &&
              max_step > 0.,
          "invalid thermal forcing/timestep");
  double done = 0.;
  while (done < seconds) {
    const unsigned n = cells.size();
    std::vector<double> g(n + 1, 0.), rate(n, 0.);
    g[0] = 2. * cells[0].conductivity() / cells[0].thickness();
    for (unsigned i = 1; i < n; ++i)
      g[i] =
          1. / (0.5 * cells[i - 1].thickness() / cells[i - 1].conductivity() +
                0.5 * cells[i].thickness() / cells[i].conductivity());
    double dt = std::min(max_step, seconds - done);
    for (unsigned i = 0; i < n; ++i) {
      // Minimum phase heat capacity gives a conservative explicit stability
      // bound.
      const auto &c = cells[i];
      const double cmin =
          (c.material == SNOW_MATERIAL ? 0. : c.matrix * (1. - c.porosity) * c.solid_heat) + c.mass() * SHCICE;
      dt = std::min(dt, 0.2 * cmin / (g[i] + g[i + 1]));
    }
    require(dt > 0. && done + dt > done, "thermal timestep underflow");
    const double top = g[0] * (top_temperature - cells[0].temperature());
    rate[0] += top;
    rate[n - 1] += basal_flux;
    for (unsigned i = 1; i < n; ++i) {
      const double flux =
          g[i] * (cells[i - 1].temperature() - cells[i].temperature());
      rate[i - 1] -= flux;
      rate[i] += flux;
    }
    for (unsigned i = 0; i < n; ++i)
      cells[i].enthalpy += dt * rate[i];
    boundary_energy += dt * (top + basal_flux);
    equilibrate_and_settle();
    done += dt;
  }
  elapsed += seconds;
  validate();
}
void Column::regrid(const std::vector<double> &target) {
  validate();
  require(!target.empty() && target.size() <= 10000,
          "invalid target layer count");
  double total = 0.;
  for (double d : target) {
    require(std::isfinite(d) && d > 1e-9, "invalid target thickness");
    total += d;
  }
  require(std::abs(total - depth()) <= 1e-10 * std::max(1., depth()),
          "target must cover collapsed column exactly");
  std::vector<Cell> result;
  double top = 0.;
  for (double dz : target) {
    Cell out;
    out.matrix = out.water = out.ice = out.excess = out.enthalpy = 0.;
    double donor_top = 0., pore = 0., heat = 0., solid = 0.;
    const Cell *first = nullptr;
    for (const auto &c : cells) {
      const double overlap =
          std::max(0., std::min(top + dz, donor_top + c.thickness()) -
                           std::max(top, donor_top));
      donor_top += c.thickness();
      if (overlap < 1e-13)
        continue;
      if (!first) {
        first = &c;
        out.material = c.material;
        out.solid_k = c.solid_k;
      }
      // Never mix materials or frozen/thawing/thawed regimes numerically.
      require(c.material == first->material && phase(c) == phase(*first) &&
                  c.solid_k == first->solid_k,
              "target crosses material or phase boundary");
      const double w = overlap / c.thickness();
      out.matrix += w * c.matrix;
      pore += w * c.matrix * c.porosity;
      solid += w * c.matrix * (1. - c.porosity);
      heat += w * c.matrix * (1. - c.porosity) * c.solid_heat;
      out.water += w * c.water;
      out.ice += w * c.ice;
      out.excess += w * c.excess;
      out.enthalpy += w * c.enthalpy;
      for (unsigned k = 0; k < 6; ++k)
        out.pools[k] += w * c.pools[k];
    }
    require(first != nullptr, "uncovered target layer");
    out.porosity = pore / out.matrix;
    out.solid_heat = heat / solid;
    result.push_back(out);
    top += dz;
  }
  Column candidate = *this;
  candidate.cells = result;
  candidate.validate();
  cells.swap(candidate.cells);
}
void Column::split_thick(double limit) {
  require(std::isfinite(limit) && limit > 1e-9, "invalid split limit");
  std::vector<double> target;
  for (const auto &c : cells) {
    const double count = std::ceil(c.thickness() / limit);
    require(count <= 10000 && target.size() + count <= 10000,
            "too many split layers");
    const unsigned n = static_cast<unsigned>(count);
    for (unsigned i = 0; i < n; ++i)
      target.push_back(c.thickness() / n);
  }
  regrid(target);
}
void Column::write_restart(std::ostream &out) const {
  validate();
  out << std::setprecision(17) << "TEM_THERMOKARST 1\n"
      << cells.size() << ' ' << surface << ' ' << subsidence << ' '
      << surface_mass << ' ' << surface_energy << ' ' << runoff_mass << ' '
      << runoff_energy << ' ' << boundary_energy << ' ' << elapsed << ' '
      << pond_capacity << '\n';
  for (const auto &c : cells) {
    out << c.material << ' ' << c.matrix << ' ' << c.porosity << ' '
        << c.solid_heat << ' ' << c.solid_k << ' ' << c.water << ' ' << c.ice
        << ' ' << c.excess << ' ' << c.enthalpy;
    for (double p : c.pools)
      out << ' ' << p;
    out << '\n';
  }
  if (!out)
    throw std::runtime_error("restart write failed");
}
Column Column::read_restart(std::istream &in) {
  std::string magic;
  int version;
  unsigned n;
  require(bool(in >> magic >> version) && magic == "TEM_THERMOKARST" &&
              version == 1,
          "unsupported restart header");
  Column c;
  require(bool(in >> n) && n > 0 && n <= 10000, "invalid restart count");
  require(bool(in >> c.surface >> c.subsidence >> c.surface_mass >>
               c.surface_energy >> c.runoff_mass >> c.runoff_energy >>
               c.boundary_energy >> c.elapsed >> c.pond_capacity),
          "truncated restart metadata");
  c.cells.resize(n);
  for (auto &x : c.cells) {
    require(bool(in >> x.material >> x.matrix >> x.porosity >> x.solid_heat >>
                 x.solid_k >> x.water >> x.ice >> x.excess >> x.enthalpy),
            "truncated restart layer");
    for (double &p : x.pools)
      require(bool(in >> p), "truncated restart pools");
  }
  std::string extra;
  require(!(in >> extra), "unexpected restart content");
  c.validate();
  return c;
}
} // namespace thermokarst
