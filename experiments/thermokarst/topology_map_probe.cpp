#include "../../include/Thermokarst.h"
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <vector>
using namespace thermokarst;

int main(int argc,char** argv) {
  if(argc!=2) return 2;
  std::vector<Cell> old(4);
  const int material[]={1,1,2,3};
  const double matrix[]={.12,.28,.35,.55};
  for(unsigned i=0;i<old.size();++i) {
    Cell& c=old[i];c.material=material[i];c.matrix=matrix[i];
    c.porosity=.72-.08*i;c.solid_heat=2.1e6+1.5e5*i;c.solid_k=.3+.25*i;
    c.water=i==2?28.:0.;c.ice=i==2?0.:18.+8.*i;c.excess=i==2?0.:12.+9.*i;
    for(unsigned k=0;k<6;++k)c.pools[k]=(i+1.)*(k+2.)*.7;
    c.set_temperature(i==2?3.:(-2.-i));
  }
  const std::vector<double> target_matrix={.08,.14,.22,.18,.17,.51};
  const std::vector<int> target_material={1,1,1,2,2,3};
  const TopologyMap map=remap_matrix_topology(old,target_matrix,target_material);
  const std::vector<double> roots=remap_extensive(
      map.donor_fraction,{.08,.27,.35,.30});
  const std::vector<double> drainage=remap_extensive(
      map.donor_fraction,{1.2,2.8,4.5,7.5});
  std::ofstream out(argv[1]);if(!out) return 3;
  out<<std::setprecision(17);
  out<<"grid,layer,material,matrix_m,excess_kg_m2,water_kg_m2,ice_kg_m2,enthalpy_J_m2,rawc,soma,sompr,somcr,orgn,avln,root_fraction,accumulated_drainage_mm\n";
  const double old_roots[]={.08,.27,.35,.30},old_drain[]={1.2,2.8,4.5,7.5};
  for(unsigned i=0;i<old.size();++i) {
    const Cell& c=old[i];
    out<<"old,"<<i<<','<<c.material<<','<<c.matrix<<','<<c.excess<<','
       <<c.water<<','<<c.ice<<','<<c.enthalpy;
    for(double x:c.pools)out<<','<<x;
    out<<','<<old_roots[i]<<','<<old_drain[i]<<'\n';
  }
  for(unsigned i=0;i<map.cells.size();++i) {
    const Cell& c=map.cells[i];
    out<<"new,"<<i<<','<<c.material<<','<<c.matrix<<','<<c.excess<<','
       <<c.water<<','<<c.ice<<','<<c.enthalpy;
    for(double x:c.pools)out<<','<<x;
    out<<','<<roots[i]<<','<<drainage[i]<<'\n';
  }
  return 0;
}
