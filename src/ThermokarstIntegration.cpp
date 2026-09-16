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
  auto& s=g.thermokarst;using S=ThermokarstState;
  c.surface=s.value[S::ELEVATION];c.subsidence=s.value[S::SUBSIDENCE];
  c.surface_mass=s.value[S::SURFACE_MASS];c.surface_energy=s.value[S::SURFACE_ENERGY];
  // Routed water is handed to TEM hydrology after this solve. It may
  // infiltrate and therefore reappear in tomorrow's imported layers, so a
  // historical routed total must not also be seeded into Column::budget().
  c.runoff_mass=0.;c.runoff_energy=0.;
  c.boundary_energy=s.value[S::BOUNDARY_ENERGY];c.pond_capacity=0.;
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
  s.pending_runoff+=c.runoff_mass;
  s.pending_generated+=generated;
  s.value[S::ELEVATION]=c.surface;s.value[S::SUBSIDENCE]=c.subsidence;
  s.value[S::SURFACE_MASS]=c.surface_mass;s.value[S::SURFACE_ENERGY]=c.surface_energy;
  s.value[S::EXPORTED_WATER]+=c.runoff_mass;
  s.value[S::EXPORTED_ENERGY]+=c.runoff_energy;
  s.value[S::HYDROLOGY_ENERGY]+=c.runoff_energy;
  s.value[S::BOUNDARY_ENERGY]=c.boundary_energy;
  s.value[S::WATER_RESIDUAL]=water_error;s.value[S::ENERGY_RESIDUAL]=energy_error;
  s.value[S::GENERATED_WATER]+=generated;
  g.resortGroundLayers();g.updateSoilHorizons();rebuild_fronts(g,top<0.);
}
}
