/*! \file
 * 
 */
#include "SoilLayer.h"
 
SoilLayer::SoilLayer(){

	isSoil = true;

};

SoilLayer::~SoilLayer(){

};

double SoilLayer::getFrzVolHeatCapa(){
	 double vhc = vhcsolid * (1-poro) + (liq+ice)/dz *SHCICE;
	 return vhc;
};

double SoilLayer::getUnfVolHeatCapa(){
	 double vhc= vhcsolid * (1-poro) + (liq+ice)/dz *SHCLIQ;
	 return vhc;
};
	   
//Yuan: unfrozen/frozen put together
double SoilLayer::getMixVolHeatCapa(){
	 double vhc = vhcsolid * (1-poro) + liq/dz *SHCLIQ+ice/dz *SHCICE;
	 return vhc;
};
	  
// get frozen layer thermal conductivity
double SoilLayer::getFrzThermCond(){
	  double tc;
	  double vice = getVolIce();
	  double vliq = getVolLiq();
	  double s = (vice + vliq)/poro;
	  s = min(s, 1.0);
	  double ke= s; // for frozen case
	  if(s < 1.e-7){
	  	 tc = tcdry;	
	  }else{
	  	 tc = ke *tcsatfrz + (1-ke)*tcdry;
	  }
	  
	  return tc;
};
	  
// get unfrozen layer thermal conductivity
double SoilLayer::getUnfThermCond(){
  	double tc;
  	double vice = getVolIce();
  	double vliq = getVolLiq();
  	double s = (vice + vliq)/poro;
  	s = min(s, 1.0);
  	double ke= log(s) +1; // for unfrozen case
  	ke = fmax(ke, 0.);
  	if(s < 1.e-7){
	  	 tc = tcdry;	
  	}else{
	  	 tc = ke *tcsatunf + (1-ke)*tcdry;
  	}

  	if(poro>=0.9 || (poro>=0.8 &&solind ==1)){
	  	tc = fmax(tc, tcmin);
  	}

  	return tc;
};

double SoilLayer::getMatricPotential(){
  	double psi;
  	double lf = 3.337e5 ;// latent heat of fusion J/kg
	double g =9.8;
	if(tem<0){
		psi =1000. * lf/g *(tem/(tem+273.16));
		if (psi<-1.e8)psi=-1.e8;
	}else{
	  	double voliq = getEffVolLiq();

	  	double ws = fmax(0.01, voliq);
	  	ws = fmin(1.0, ws);
	  	psi = psisat * pow(ws, -bsw);
	  	if (psi<-1.e8){	
	  		psi=-1.e8;
	  	}

	}

	return psi;
};
	  
// get albedo of visible radition
double SoilLayer::getAlbedoVis(){
       	double vis;
      	double liq1 = getVolLiq();
      	double ice1 = getVolIce();
       	double delta = 0.11-0.4*(liq1+ice1);
       	delta =fmax(0., delta);
       	vis = albsatvis + delta;
       	vis = min(vis, (double)albdryvis);
       	return vis;
};
     
// get albedo of nir radition
double SoilLayer::getAlbedoNir(){
       	double nir;
       	double wat = getVolLiq()+getVolIce();
       	double delta = 0.11-0.4*wat;
       	delta =fmax(0., delta);
       	nir = albsatnir + delta;
       	nir = fmin(nir, (double)albdrynir);
       	return nir;
};
     
// derive properties from the assigned property
// called when porosity/thickness is changed
void SoilLayer::derivePhysicalProperty(){

	 //hydraulic properties
  	 minliq = 0.05*poro * DENLIQ * dz;
   	 maxliq = poro * DENLIQ * dz;
   	 maxice = poro * DENICE * dz;

   	 //thermal properties

   	 tcsatunf= pow((double)tcsolid , (double)1- poro) * pow((double)TCLIQ, (double)poro);
	 tcsatfrz= pow((double)tcsolid , (double)1- poro) * pow((double)TCICE, (double)poro);
	 tcdry   = pow((double)tcsolid , (double)1- poro) * pow((double)TCAIR, (double)poro);
   	 tcmin   = tcdry;
   	 
};
   
