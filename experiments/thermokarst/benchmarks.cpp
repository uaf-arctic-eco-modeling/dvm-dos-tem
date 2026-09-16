#include "../../include/Thermokarst.h"
#include "../../include/physicalconst.h"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
using namespace thermokarst;
std::ofstream file(const std::string &p) {
  std::ofstream f(p);
  if (!f)
    throw std::runtime_error("cannot open " + p);
  f << std::setprecision(17);
  return f;
}
int main(int argc, char **argv) {
  try {
    if (argc != 2)
      throw std::invalid_argument("usage: benchmarks OUTPUT_DIRECTORY");
    const std::string dir = argv[1];
    Column c;
    Cell a;
    a.matrix = .5;
    a.porosity = .5;
    a.ice = .25 * DENICE;
    a.excess = .2 * DENICE;
    a.pools = {{1, 2, 3, 4, 5, 6}};
    a.set_temperature(0.);
    c.cells.push_back(a);
    auto before = c.budget();
    double pore = a.ice, total = a.mass();
    auto pulse = file(dir + "/heat_pulse.csv");
    pulse << "heat_MJ_m2,subsidence_m,analytical_m,excess_kg_m2,water_residual_"
             "kg_m2,energy_residual_J_m2\n";
    for (int i = 0; i <= 120; ++i) {
      if (i) {
        std::vector<double> e;
        for (auto &x : c.cells)
          e.push_back(total * LHFUS / 100. * x.matrix / .5);
        c.add_energy(e);
      }
      if (i == 40)
        c.split_thick(.1);
      auto b = c.budget();
      double x = 0.;
      for (auto &v : c.cells)
        x += v.excess;
      double analytical = std::min(
          .2, std::max(0., (c.boundary_energy / LHFUS - pore) / DENICE));
      pulse << c.boundary_energy / 1e6 << ',' << c.subsidence << ','
            << analytical << ',' << x << ',' << b.water - before.water << ','
            << b.energy - before.energy - c.boundary_energy << '\n';
      if (std::abs(c.subsidence - analytical) > 1e-10)
        throw std::runtime_error("heat-pulse benchmark failed");
    }
    auto stefan = file(dir + "/stefan.csv");
    stefan << "spacing_m,day,front_m,analytical_m,absolute_error_m\n";
    for (double dz : {.1, .05, .025}) {
      Column s;
      Cell frozen;
      frozen.matrix = dz;
      frozen.porosity = .5;
      frozen.ice = .9 * .5 * dz * DENICE;
      frozen.set_temperature(0.);
      for (int i = 0; i < static_cast<int>(std::round(3. / dz)); ++i)
        s.cells.push_back(frozen);
      Cell thawed = frozen;
      thawed.water = thawed.ice;
      thawed.ice = 0.;
      thawed.set_temperature(0.);
      double cv = thawed.capacity() / dz, k = thawed.conductivity(),
             alpha = k / cv;
      double ste = cv * 5. / (frozen.ice / dz * LHFUS), lo = 0., hi = 2.;
      for (int it = 0; it < 100; ++it) {
        double m = (lo + hi) / 2.;
        double val = m * std::exp(m * m) * std::erf(m);
        if (val < ste / std::sqrt(3.141592653589793))
          lo = m;
        else
          hi = m;
      }
      double lambda = (lo + hi) / 2.;
      for (int day = 1; day <= 15; ++day) {
        s.advance(86400., 5.);
        double front = 0.;
        for (auto &x : s.cells)
          front += dz * x.water / frozen.ice;
        double exact = 2. * lambda * std::sqrt(alpha * day * 86400.);
        stefan << dz << ',' << day << ',' << front << ',' << exact << ','
               << std::abs(front - exact) << '\n';
      }
    }
    std::cout << "Wrote heat-pulse and Stefan benchmark data\n";
  } catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
