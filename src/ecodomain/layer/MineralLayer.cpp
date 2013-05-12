/*! \file
 * 
 */
#include "MineralLayer.h"

MineralLayer::MineralLayer(const double & pdz, int sttype , SoilLookup * soillup){
	tkey  = I_MINE;
	stkey = STKEY(sttype);
	dz    = pdz;

	isMoss    = false;
	isMineral = true;
	isOrganic = false;
    isFibric = false;
    isHumic  = false;

	updateProperty5Lookup(soillup);
	
};

void MineralLayer::updateProperty5Lookup(SoilLookup * soillu){

	poro    = soillu->poro[stkey];
	bulkden = soillu->bulkden[stkey];
	hksat   = soillu->Ksat[stkey];
	psisat  = soillu->Psisat[stkey];
	bsw     = soillu->b[stkey];

    tcsolid = soillu->Ksolids[stkey];
	tcdry   = soillu->tcdry[stkey];
  	tcsatunf= soillu->tcunfsat[stkey];
  	tcsatfrz= soillu->tcfrzsat[stkey];
   	vhcsolid= soillu->Csolids[stkey];
  	    
   	albsatvis = soillu->albsatvis[stkey];
   	albsatnir = soillu->albsatnir[stkey];
   	albdryvis = soillu->albdryvis[stkey];
   	albdrynir = soillu->albdryvis[stkey];
   	    
   	derivePhysicalProperty();

};


// dry thermal conductivity, if not lookup
double MineralLayer::getDryThermCond(const double & bulkden){
   // from ATBalland22005a
   double kdry =0.;
  
   kdry = (0.135*bulkden +64.7)/(2700-0.947*bulkden);
   return kdry;
}  

double MineralLayer::getDryThermCond(const double & tcsolid, const double & bulkden, const double & partden){
   // from ATBalland22005a
   double kdry =0.;
   double par_a = 0.053;
   double tcair = TCAIR;
   kdry = ((par_a* tcsolid - tcair) *bulkden + tcair*partden)/(partden - (1-par_a)*bulkden)	;
   return kdry;
}     

