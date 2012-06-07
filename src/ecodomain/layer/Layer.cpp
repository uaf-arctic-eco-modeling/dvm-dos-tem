/*! \file
 * 
 */
 #include "Layer.h"
 
 Layer::Layer(){
	nextl= NULL;
 	prevl= NULL;
 	
	isSnow = false;
	isSoil = false;
	isRock = false;
	isMoss    = false;
	isMineral = false;
	isOrganic = false;
    isFibric = false;
    isHumic  = false;

    age    = 0.;
    
};
 
Layer::~Layer(){

};
 
 
void Layer::advanceOneDay(){
	age+=1/365.;
};
 
double Layer::getHeatCapacity(){ // volumetric heat capacity
    	double hcap = MISSING_D;

    	if(isSoil){
			if(frozen==-1){
				hcap = getUnfVolHeatCapa();
			}else if(frozen ==1){
				hcap = getFrzVolHeatCapa();
			}else if(frozen ==0){
				hcap = getMixVolHeatCapa();
			}

    	}else if(isSnow){
		    hcap = getFrzVolHeatCapa();

    	}else if(isRock){
		    hcap = getFrzVolHeatCapa();
    	}

    	return hcap;
};
    
double Layer::getThermalConductivity(){
    	double tc = MISSING_D;

    	if(isSoil || isSnow){
			if(frozen==1){
				tc = getFrzThermCond();
			}else{
				tc = getUnfThermCond();
			}

    	}else if (isRock){
		    tc = getFrzThermCond();
		}
				
		return tc;		

};

double Layer::getVolWater(){
 	double vice = getVolIce();
 	double vliq = getVolLiq();
 	return min((double)poro,(double)vice+vliq);
};
 
double Layer::getEffVolWater(){
 	double effvol = 0.;
 	if(isSoil){
 	  effvol = getVolWater() - minliq/DENLIQ/dz * poro;
 	}else if (isSnow){
 	  effvol = getVolWater();	
 	}

 	if(effvol<0) effvol =0.;

 	return effvol;
};
 
double Layer::getVolIce(){
    double vice = ice/DENICE/dz;
    vice = min((double)vice, (double)poro);
    return vice;
};
 
double Layer::getVolLiq(){
    double vliq = liq/DENLIQ/dz;
    vliq = min((double)vliq,(double)poro);
    return vliq;
};
