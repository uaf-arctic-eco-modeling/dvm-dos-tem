/*! \file
 * 
 */
#include "SnowLayer.h"

SnowLayer::SnowLayer(){
	tkey = I_SNOW;
	stkey= I_NONE;

	isSnow = true;
	solind = MISSING_I;

	liq    = MISSING_D;
    maxliq = MISSING_D;
    
	frozen = 1;

	rawc = MISSING_D;
	soma = MISSING_D;
	sompr= MISSING_D;
	somcr= MISSING_D;
	cfrac= MISSING_D;
};

SnowLayer::~SnowLayer(){

};

void SnowLayer::clone(SnowLayer* sl){
  liq = sl->liq;
  ice = sl->ice;
  dz  = sl->dz;
  age = sl->age;
  rho = sl->rho;
}

void SnowLayer::updateDensity(snwpar_dim *snwpar){
	double adjust=0.24; // corresponding to e-folding time of 4 days
    double tao1 = 86400.; //s
    double tao  = 86400.; // one day time step
	rho = (rho-snwpar->denmax)* exp(- tao/tao1* adjust) + snwpar->denmax;
	if(rho>snwpar->denmax) rho= snwpar->denmax;
	maxice = snwpar->denmax*dz;
	maxliq = maxice;  // note: this is SWE max
};

// after the update of density, snow thickness should also be changed
void SnowLayer::updateThick(){
   dz = ice/rho;
}

// get frozen layer thermal conductivity, according to Jordan 1991
double SnowLayer::getFrzThermCond(){
	  	//if (ctype==0){// tundra
	      return getThermCond5Jordan();
	  	 
	  	//}else{
	  //return getThermCond5Sturm();
	  	//}
};

// get unfrozen layer thermal conductivity
double SnowLayer::getUnfThermCond(){
	   //if(ctype==0){
	   return getThermCond5Jordan();
	   //}else{
	   //return getThermCond5Sturm();
	   //}
};
	  
double SnowLayer::getThermCond5Sturm(){
  	double tc=0;
    double rhogcm = rho /1000.; // convert from  kg/m3 to g/cm3

    if(rhogcm<=0.6 && rhogcm>=0.156){
    	tc = 0.138 -1.01* rhogcm +3.233* rhogcm*rhogcm;
    }else if(rhogcm<0.156){
        tc =0.023 +0.234 *rhogcm;
    }

    return tc;
};
	  
//in TROleson142004a
double SnowLayer::getThermCond5Jordan(){
  	double tc=0;
    tc = TCAIR + (7.75e-5 * rho + 1.105e-6*rho*rho)*(TCICE-TCAIR);
    tc = 2.9*1.e-6 * rho*rho;
    if(tc<0.04) tc =0.04;

    return tc;
}
	 
double SnowLayer::getFrzVolHeatCapa(){
	 
    double vhc = SHCICE * ice/dz;
 	return vhc;
};

double SnowLayer::getUnfVolHeatCapa(){
	double vhc = SHCICE * ice/dz;
	return vhc;
};

double SnowLayer::getMixVolHeatCapa(){
    double vhc = SHCICE * ice/dz;
 	return vhc;
};
	 
