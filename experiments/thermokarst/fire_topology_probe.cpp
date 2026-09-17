#include "../../include/Thermokarst.h"
#include <fstream>
#include <iomanip>
#include <iostream>
#include <vector>
using namespace thermokarst;
int main(int argc,char** argv) {
  if(argc!=2)return 2;
  std::vector<Cell> old(4);const int material[]={1,1,2,3};
  const double matrix[]={.10,.20,.30,.50};
  for(unsigned i=0;i<old.size();++i) {
    Cell& c=old[i];c.material=material[i];c.matrix=matrix[i];
    c.porosity=.75-.08*i;c.solid_heat=2.e6+1.e5*i;c.solid_k=.35+.2*i;
    c.water=i==0?12.:0.;c.ice=20.+5.*i;c.excess=8.+4.*i;
    for(unsigned k=0;k<6;++k)c.pools[k]=(i+1.)*(k+1.);
    c.set_temperature(i==0?0.:-2.-i);
  }
  const double burn=.18;
  const FireTopologyMap fire=remap_fire_topology(old,burn,{.16,.24,.42},{2,2,3});
  std::ofstream out(argv[1]);if(!out)return 3;out<<std::setprecision(17);
  out<<"metric,value\n";
  double old_water=0.,new_water=0.,old_energy=0.,new_energy=0.,old_matrix=0.;
  for(const auto& c:old){old_water+=c.mass();old_energy+=c.enthalpy;old_matrix+=c.matrix;}
  for(const auto& c:fire.topology.cells){new_water+=c.mass();new_energy+=c.enthalpy;}
  out<<"old_water_kg_m2,"<<old_water<<"\nnew_water_kg_m2,"<<new_water<<'\n';
  out<<"released_water_kg_m2,"<<fire.released_water<<'\n';
  out<<"water_residual_kg_m2,"<<new_water+fire.released_water-old_water<<'\n';
  out<<"old_energy_J_m2,"<<old_energy<<"\nnew_energy_J_m2,"<<new_energy<<'\n';
  out<<"released_phase_energy_J_m2,"<<fire.released_phase_energy<<'\n';
  out<<"exported_solid_energy_J_m2,"<<fire.exported_solid_energy<<'\n';
  out<<"energy_residual_J_m2,"<<new_energy+fire.released_phase_energy+fire.exported_solid_energy-old_energy<<'\n';
  out<<"old_matrix_m,"<<old_matrix<<"\nburned_matrix_m,"<<fire.burned_matrix<<'\n';
  out<<"target_matrix_m,"<<.82<<'\n';
  for(unsigned i=0;i<fire.surviving_fraction.size();++i)
    out<<"surviving_fraction_"<<i<<','<<fire.surviving_fraction[i]<<'\n';
  return 0;
}
