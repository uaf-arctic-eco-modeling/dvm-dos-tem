/*! \file
 * 
 */
#include "OrganicLayer.h"

OrganicLayer::OrganicLayer(const double & pdz, const int & type){
	
	stkey=I_NONE;

	isMoss    = false;
	isMineral = false;
	isOrganic = true;
    isFibric = false;
    isHumic  = false;

	dz = pdz;

    if(type==1){
    	tkey=I_FIB;
		isFibric =true;
		poro = 0.95;
   	    bulkden = 51000; // g/m3

   	    albsatvis = 0.075;
   		albsatnir = 0.15;
   		albdryvis = 0.15;
   		albdrynir = 0.3; 

   	    tcsolid = 0.25;
   	   	vhcsolid= 2.5e6; //J/m3K

   		hksat = 0.28;  
   	 	bsw=2.7;
   		psisat =-10.0;

   		cfrac = 44.2; // %
    }else if (type==2){
    	tkey=I_HUM;
		isHumic =true;
    	poro = 0.8;
       	bulkden = 176000; // g/m3

       	albsatvis = 0.075;
   		albsatnir = 0.15;
   		albdryvis = 0.15;
   		albdrynir = 0.3;
 
   	    tcsolid = 0.25;
   	   	vhcsolid= 2.5e6; //J/m3K
   		
   		bsw=8;
   		hksat  =0.002;
   		psisat =-12;

   		cfrac = 35.2; // %
    }

    derivePhysicalProperty();
};

void OrganicLayer::humify(){
    	tkey=I_HUM;
		isHumic =true;	
		isFibric=false;
	    poro = 0.8;
       	bulkden = 176000; // g/m3

       	albsatvis = 0.075;
   		albsatnir = 0.15;
   		albdryvis = 0.15;
   		albdrynir = 0.3;
   	
   	    tcsolid = 0.25;
   	   	vhcsolid= 2.5e6; //J/m3K

   		bsw=8;
   		hksat  =0.002;
   		psisat =-12;

   		cfrac = 35.2; // %

	 	derivePhysicalProperty();
};

