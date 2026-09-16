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
