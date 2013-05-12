/*! \file
 * 
 */
 #include "ParentLayer.h"
 
ParentLayer::ParentLayer(const double & thick){
 	tkey=I_ROCK;
	stkey=I_NONE;

	isRock = true;
	solind = MISSING_I;

 	dz = thick;
 	updateProperty(); 
};

ParentLayer::~ParentLayer(){

};

void ParentLayer::updateProperty(){
    	poro =  0;
    	tcsolid =2;// 
  	    tcsatunf= tcsolid;
  	    tcsatfrz= tcsolid;
   	    vhcsolid = 2700000;
};

// get frozen layer specific heat capcity
double ParentLayer::getFrzVolHeatCapa(){
	 double vhc = vhcsolid ;
	 return vhc;
};

double ParentLayer::getUnfVolHeatCapa(){
	   double vhc= vhcsolid ;
	 	return vhc;
};
	   
double ParentLayer::getMixVolHeatCapa(){
	   double vhc= vhcsolid ;
	 	return vhc;
};
	  
// get frozen layer thermal conductivity
double ParentLayer::getFrzThermCond(){
	  	double tc=tcsolid;
	  	
	  	return tc;
};
	  
// get unfrozen layer thermal conductivity
double ParentLayer::getUnfThermCond(){
  	double tc=tcsolid;
	  	
  	return tc;
};
	  
// get albedo of visible radition
double ParentLayer::getAlbedoVis(){//should not used
    double vis=0.2;
    return vis;
};
     
// get albedo of nir radition
double ParentLayer::getAlbedoNir(){//should not used
    double nir=0.2;
       	
    return nir;
};
     
