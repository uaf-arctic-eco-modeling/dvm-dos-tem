#include "../include/ThermokarstIntegration.h"
#include "../include/Thermokarst.h"
#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <vector>
namespace tem_thermokarst {
namespace {
void properties(Layer& l) {
  if(l.isSoil) static_cast<SoilLayer&>(l).derivePhysicalProperty();
}
thermokarst::Cell import_cell(const Layer& l) {
  thermokarst::Cell c;
  if(l.isSoil) {
    if(l.matrix_dz<=0.) throw std::runtime_error("uninitialized thermokarst layer");
    c.matrix=l.matrix_dz;c.porosity=l.matrix_porosity;c.material=int(l.tkey);
    c.water=l.liq;c.ice=l.ice;c.excess=l.excess_ice;
    c.solid_heat=l.vhcsolid;c.solid_k=l.tcsolid;
    c.pools={{l.rawc,l.soma,l.sompr,l.somcr,l.orgn,l.avln}};
  } else if(l.isSnow) {
    c.material=thermokarst::SNOW_MATERIAL;c.matrix=l.dz;c.porosity=1.;
    c.water=l.liq;c.ice=l.ice;
    c.solid_k=const_cast<Layer&>(l).getThermalConductivity();
  } else {
    c.material=thermokarst::ROCK_MATERIAL;c.matrix=l.dz;c.porosity=0.;
    // ParentLayer shadows Layer::vhcsolid/tcsolid, so use the virtual
    // production accessors rather than the uninitialized base members.
    Layer& mutable_layer=const_cast<Layer&>(l);
    c.solid_heat=mutable_layer.getMixVolHeatCapa();
    c.solid_k=mutable_layer.getThermalConductivity();
  }
  // Hydrology uses temperature and mass; re-equilibrate at this enthalpy rather
  // than running a second, unbudgeted freezing calculation.
  c.enthalpy=c.capacity()*l.tem+LHFUS*c.water;
  return c;
}
void export_soil_cell(Layer& l,const thermokarst::Cell& a) {
  l.matrix_dz=a.matrix;l.matrix_porosity=a.porosity;
  l.dz=a.thickness();l.excess_ice=a.excess;l.ice=a.ice;l.liq=a.water;
  l.rawc=a.pools[0];l.soma=a.pools[1];l.sompr=a.pools[2];
  l.somcr=a.pools[3];l.orgn=a.pools[4];l.avln=a.pools[5];
  l.tem=a.temperature();l.pce_t=l.pce_f=0.;
  const double fv=(a.ice+a.excess)/DENICE,lv=a.water/DENLIQ;
  l.frozenfrac=(fv+lv>0.)?fv/(fv+lv):(l.tem<=0.?1.:0.);
  l.frozen=l.frozenfrac<=1e-12?-1:(l.frozenfrac>=1.-1e-12?1:0);
  properties(l);
}
void load_global_state(thermokarst::Column& c,const ThermokarstState& s) {
  using S=ThermokarstState;
  c.surface=s.value[S::ELEVATION];c.subsidence=s.value[S::SUBSIDENCE];
  c.surface_mass=s.value[S::SURFACE_MASS];c.surface_energy=s.value[S::SURFACE_ENERGY];
  c.runoff_mass=0.;c.runoff_energy=0.;
  c.boundary_energy=s.value[S::BOUNDARY_ENERGY];c.pond_capacity=0.;
}
void store_global_state(Ground& g,const thermokarst::Column& c,double generated,
                        double water_error,double energy_error) {
  auto& s=g.thermokarst;using S=ThermokarstState;
  s.pending_runoff+=c.runoff_mass;s.pending_generated+=generated;
  s.value[S::ELEVATION]=c.surface;s.value[S::SUBSIDENCE]=c.subsidence;
  s.value[S::SURFACE_MASS]=c.surface_mass;s.value[S::SURFACE_ENERGY]=c.surface_energy;
  s.value[S::EXPORTED_WATER]+=c.runoff_mass;s.value[S::EXPORTED_ENERGY]+=c.runoff_energy;
  s.value[S::HYDROLOGY_ENERGY]+=c.runoff_energy;s.value[S::BOUNDARY_ENERGY]=c.boundary_energy;
  s.value[S::WATER_RESIDUAL]=water_error;s.value[S::ENERGY_RESIDUAL]=energy_error;
  s.value[S::GENERATED_WATER]+=generated;
}
}
void initialize(Ground& g,double fraction,double top,double bottom) {
  g.thermokarst=ThermokarstState();g.thermokarst.enabled=true;
  for(Layer*l=g.fstsoill;l && l->isSoil;l=l->nextl) {
    l->matrix_dz=l->dz;l->matrix_porosity=l->poro;
    const double overlap=std::max(0.,std::min(l->z+l->dz,bottom)-std::max(l->z,top));
    if(fraction>0. && overlap>0. && l->tem>0.)
      throw std::invalid_argument("excess ice initialization requires frozen soil");
    l->excess_ice=DENICE*overlap*fraction/(1.-fraction);
    l->dz=l->matrix_dz+l->excess_ice/DENICE;
    properties(*l);
  }
  g.resortGroundLayers();g.updateSoilHorizons();
}
void rebuild_fronts(Ground& g,bool freezing) {
  g.frontsz.clear();g.frontstype.clear();
  bool previous=false,have=false;
  auto segment=[&](double depth,bool frozen){
    if(have && frozen!=previous) {
      if(g.frontsz.size()>=MAX_NUM_FNT) throw std::runtime_error("thermokarst front capacity exceeded");
      g.frontsz.push_back(depth);g.frontstype.push_back(previous?1:-1);
    }
    previous=frozen;have=true;
  };
  for(Layer*l=g.fstsoill;l && l->isSoil;l=l->nextl) {
    const double f=l->frozenfrac;
    if(f<=1e-12) segment(l->z,false);
    else if(f>=1.-1e-12) segment(l->z,true);
    else if(freezing) {segment(l->z,true);segment(l->z+f*l->dz,false);}
    else {segment(l->z,false);segment(l->z+(1.-f)*l->dz,true);}
  }
  for(int i=0;i<MAX_NUM_FNT;++i){g.frntz[i]=MISSING_D;g.frnttype[i]=MISSING_I;}
  for(unsigned i=0;i<g.frontsz.size();++i){g.frntz[i]=g.frontsz[i];g.frnttype[i]=g.frontstype[i];}
  g.setFstLstFrontLayers();g.updateWholeFrozenStatus();g.setDrainL();
}
void advance(Ground& g,double top,double seconds) {
  if(!g.thermokarst.enabled) throw std::logic_error("thermokarst solver called while disabled");
  thermokarst::Column c;std::vector<Layer*> layers;
  for(Layer*l=g.toplayer;l;l=l->nextl){layers.push_back(l);c.cells.push_back(import_cell(*l));}
  load_global_state(c,g.thermokarst);
  double excess_before=0.;
  for(const auto& cell:c.cells) if(cell.material!=thermokarst::SNOW_MATERIAL &&
                                    cell.material!=thermokarst::ROCK_MATERIAL)
    excess_before+=cell.excess;
  const auto before=c.budget();const double flux0=c.boundary_energy;
  c.reconcile_phase();c.advance(seconds,top);
  const auto after=c.budget();
  double excess_after=0.;
  for(const auto& cell:c.cells) if(cell.material!=thermokarst::SNOW_MATERIAL &&
                                    cell.material!=thermokarst::ROCK_MATERIAL)
    excess_after+=cell.excess;
  const double generated=std::max(0.,excess_before-excess_after);
  const double water_error=after.water-before.water;
  const double energy_error=after.energy-before.energy-(c.boundary_energy-flux0);
  if(std::abs(water_error)>1e-7 || std::abs(energy_error)>1e-3)
    throw std::runtime_error("production thermokarst thermal conservation failure");
  // Identity-preserving remap: each material layer contracts in place. No
  // topology change, so C/N and monthly accumulators retain their layer IDs.
  for(unsigned i=0;i<layers.size();++i) {
    Layer& l=*layers[i];const auto& a=c.cells[i];
    l.tem=a.temperature();l.pce_t=l.pce_f=0.;
    if(l.isSoil) {
      l.dz=a.thickness();l.excess_ice=a.excess;l.ice=a.ice;l.liq=a.water;
      const double frozen_volume=(a.ice+a.excess)/DENICE;
      const double liquid_volume=a.water/DENLIQ;
      l.frozenfrac=(frozen_volume+liquid_volume>0.)?frozen_volume/(frozen_volume+liquid_volume):(l.tem<=0.?1.:0.);
      l.frozen=l.frozenfrac<=1e-12?-1:(l.frozenfrac>=1.-1e-12?1:0);
      properties(l);
    } else if(l.isSnow) {
      // Snow_Env removes melt using constructSnowLayers(-melt). Present it with
      // pre-removal mass so phase conversion is not subtracted twice.
      l.ice=a.ice+a.water;l.liq=a.water;
      l.frozen=a.water<=1e-12?1:(a.ice<=1e-12?-1:0);
    }
  }
  store_global_state(g,c,generated,water_error,energy_error);
  g.resortGroundLayers();g.updateSoilHorizons();rebuild_fronts(g,top<0.);
}
TopologySnapshot prepare_topology_change(Ground& g) {
  if(!g.thermokarst.enabled) throw std::logic_error("thermokarst topology map called while disabled");
  TopologySnapshot result;
  result.freezing=!g.frontstype.empty()?g.frontstype.front()==1:
      (g.fstsoill && g.fstsoill->tem<0.);
  for(Layer*l=g.fstsoill;l&&l->isSoil;l=l->nextl) {
    result.cells.push_back(import_cell(*l));
    l->dz=l->matrix_dz;l->matrix_dz=0.;l->matrix_porosity=0.;l->excess_ice=0.;
    properties(*l);
  }
  if(result.cells.empty()) throw std::runtime_error("empty thermokarst soil column");
  g.resortGroundLayers();g.updateSoilHorizons();
  return result;
}
TopologyResult finish_topology_change(Ground& g,const TopologySnapshot& snapshot) {
  std::vector<Layer*> layers;std::vector<double> matrix;std::vector<int> material;
  for(Layer*l=g.fstsoill;l&&l->isSoil;l=l->nextl) {
    layers.push_back(l);matrix.push_back(l->dz);material.push_back(int(l->tkey));
  }
  TopologyResult result;
  result.map=thermokarst::remap_matrix_topology(snapshot.cells,matrix,material);
  thermokarst::Column before_column;before_column.cells=snapshot.cells;
  load_global_state(before_column,g.thermokarst);
  const auto before=before_column.budget();
  thermokarst::Column c;c.cells=result.map.cells;load_global_state(c,g.thermokarst);
  double excess_before=0.;for(const auto& x:c.cells) excess_before+=x.excess;
  c.reconcile_phase();
  double excess_after=0.;for(const auto& x:c.cells) excess_after+=x.excess;
  const double generated=std::max(0.,excess_before-excess_after);
  const auto after=c.budget();
  result.water_residual=after.water-before.water;
  result.energy_residual=after.energy-before.energy;
  for(unsigned k=0;k<6;++k) result.pool_residual[k]=after.pools[k]-before.pools[k];
  if(std::abs(result.water_residual)>1e-7 || std::abs(result.energy_residual)>1e-3)
    throw std::runtime_error("thermokarst topology water/energy conservation failure");
  for(double e:result.pool_residual) if(std::abs(e)>1e-8)
    throw std::runtime_error("thermokarst topology C/N conservation failure");
  if(c.cells.size()!=layers.size()) throw std::runtime_error("topology export size mismatch");
  for(unsigned i=0;i<layers.size();++i) export_soil_cell(*layers[i],c.cells[i]);
  store_global_state(g,c,generated,result.water_residual,result.energy_residual);
  g.resortGroundLayers();g.updateSoilHorizons();rebuild_fronts(g,snapshot.freezing);
  return result;
}
}
