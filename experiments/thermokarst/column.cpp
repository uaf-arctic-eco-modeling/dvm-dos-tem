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
Column initial(double ice_depth) {
  Column c;
  c.pond_capacity = 30.;
  for (int i = 0; i < 15; ++i) {
    Cell x;
    x.matrix = .1;
    x.porosity = .5;
    x.ice = .9 * x.matrix * x.porosity * DENICE;
    x.excess = (i >= 3 && i < 8) ? ice_depth / 5. * DENICE : 0.;
    x.material = i < 3 ? 1 : 2;
    x.pools = {{100., 200., 300., 400., 40., 2.}};
    x.set_temperature(-2.);
    c.cells.push_back(x);
  }
  c.split_thick(.1);
  return c;
}
int main(int argc, char **argv) {
  try {
    std::string out = "column.csv", restart = "", save = "", profile = "";
    double days = 180., top = 8., ice = .25, step = 3600.;
    for (int i = 1; i < argc; ++i) {
      std::string a = argv[i];
      if (a == "--help") {
        std::cout << "thermokarst-column [--output CSV] [--profile CSV] "
                     "[--days N] [--top C] [--excess-depth m] [--max-step s] "
                     "[--restart FILE] [--save FILE]\n";
        return 0;
      }
      if (i + 1 == argc)
        throw std::invalid_argument("missing option value");
      std::string v = argv[++i];
      if (a == "--output")
        out = v;
      else if (a == "--profile")
        profile = v;
      else if (a == "--restart")
        restart = v;
      else if (a == "--save")
        save = v;
      else if (a == "--days")
        days = std::stod(v);
      else if (a == "--top")
        top = std::stod(v);
      else if (a == "--excess-depth")
        ice = std::stod(v);
      else if (a == "--max-step")
        step = std::stod(v);
      else
        throw std::invalid_argument("unknown option: " + a);
    }
    if (!std::isfinite(top) || !std::isfinite(step) || step <= 0. ||
        !std::isfinite(days) || days < 0. || days > 10000. ||
        !std::isfinite(ice) || ice < 0. || ice > 10.)
      throw std::invalid_argument("invalid days or excess depth");
    Column c;
    if (restart.empty())
      c = initial(ice);
    else {
      std::ifstream f(restart);
      c = Column::read_restart(f);
    }
    Budget initial_budget = c.budget();
    double initial_boundary = c.boundary_energy;
    std::ofstream f(out), p;
    if (!f)
      throw std::runtime_error("cannot open output");
    if (!profile.empty()) {
      p.open(profile);
      if (!p)
        throw std::runtime_error("cannot open profile");
      p << "day,layer,top_elevation_m,bottom_elevation_m,temperature_C,excess_"
           "kg_m2,liquid_kg_m2,pore_ice_kg_m2\n"
        << std::setprecision(17);
    }
    f << "day,surface_m,subsidence_m,excess_kg_m2,soil_liquid_kg_m2,pond_kg_m2,"
         "runoff_kg_m2,energy_input_J_m2,water_residual_kg_m2,energy_residual_"
         "J_m2,carbon_residual_g_m2,nitrogen_residual_g_m2\n"
      << std::setprecision(17);
    auto output = [&] {
      auto b = c.budget();
      double x = 0., w = 0.;
      for (auto &a : c.cells) {
        x += a.excess;
        w += a.water;
      }
      double cr = 0., nr = 0.;
      for (int k = 0; k < 4; ++k)
        cr += b.pools[k] - initial_budget.pools[k];
      for (int k = 4; k < 6; ++k)
        nr += b.pools[k] - initial_budget.pools[k];
      f << c.elapsed / 86400. << ',' << c.surface << ',' << c.subsidence << ','
        << x << ',' << w << ',' << c.surface_mass << ',' << c.runoff_mass << ','
        << c.boundary_energy << ',' << b.water - initial_budget.water << ','
        << b.energy - initial_budget.energy -
               (c.boundary_energy - initial_boundary)
        << ',' << cr << ',' << nr << '\n';
      if (p) {
        double z = c.surface;
        unsigned i = 0;
        for (auto &a : c.cells) {
          p << c.elapsed / 86400. << ',' << i++ << ',' << z << ','
            << z - a.thickness() << ',' << a.temperature() << ',' << a.excess
            << ',' << a.water << ',' << a.ice << '\n';
          z -= a.thickness();
        }
      }
    };
    output();
    double done = 0.;
    while (done < days) {
      double d = std::min(1., days - done);
      c.advance(d * 86400., top, 0., step);
      output();
      done += d;
    }
    if (!save.empty()) {
      std::ofstream s(save);
      c.write_restart(s);
    }
    std::cout << "Wrote " << out << "; subsidence " << c.subsidence << " m\n";
  } catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
