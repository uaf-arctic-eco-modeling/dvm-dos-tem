#include "SoilLookup.h"

//constructor
SoilLookup::SoilLookup(){
	
	setLookupParam();
	
	deriveParam5Texture(); // determine the value of parameters based on texture
	
    deriveParam5TextureEnv();//also based on soil moisture and/or temperature
	
};

//deconstructor
SoilLookup::~SoilLookup(){

};

void SoilLookup::deriveParam5TextureEnv(){
	
	for(int it=0; it<MAX_SOIL_TXTR; it++){
	 	double sw;
	 	double bb = b[it];

	 	for(int ism =0; ism<MAX_SM; ism++){
	 		sw = ism * 1./MAX_SM;
	 		if(ism==0){
	 	  		psi[it][ism] = -1.e+12;	
	 		} else {
	 	  		psi[it][ism] = Psisat[it] * pow(sw, -bb );	
	 		}
	 	
	 		hk[it][ism] = Ksat[it] * pow(sw, 2*bb +2.);
	 	}

    }// end of loop
	
}

void SoilLookup::deriveParam5Texture(){
	
	for(int it=0; it<MAX_SOIL_TXTR; it++){
     	double p = poro[it];
     	double k = Ksolids[it];

     	tcunfsat[it] = pow(k , 1- p) * pow((double)TCLIQ, p);
	 	tcfrzsat[it] = pow(k , 1- p) * pow((double)TCICE, p);
	 	tcdry[it] = getDryThermCond(bulkden[it]);
	
   	 	//if(color[it]==4){   //not used, but maybe in future version
   	    	albsatvis[it] =0.09;
			albsatnir[it] =0.18;
			albdryvis[it] =0.18;
			albdrynir[it] =0.36;
     	//}
   	    
	} // end of it loop
} 


//set the value of look up parameters 
void SoilLookup::setLookupParam(){
	// 11 classes
	//sand, loamy sand, sandy loam, loam, silty loam, sandy clay loam, clay loam, silty clay loam, sandy clay, silty clay, clay
	//one more gravel, not used
	// assign values to the parameters, which only depend on soil texture
	int dumsand[] = {92, 82, 58, 43, 17, 58, 32, 10, 52, 6 , 22, 92};
	int dumsilt[] = {5 , 12, 32, 39, 70, 15, 34, 56, 6 , 47, 20, 5};
	int dumclay[] = {3 , 6 , 10, 18, 13, 27, 34, 34, 42, 47, 58, 3};
	
	float dumksolids[] = {8.6143, 8.3991, 7.9353, 7.0649, 6.2520, 6.9323, 5.7709, 
						4.2564, 6.1728, 3.5856, 4.5370, 8.6143};
										
	float dumcsolids[]= {2136116, 2145523, 2165794, 2203836, 2239367, 2209635, 2260394,
					     2326591, 2242830, 2355906, 2314325, 2136116};
	float dumksat[] = {0.023558, 0.016563, 0.007111, 0.004192, 0.001677, 0.007111, 0.002845,
				       0.001311, 0.005756, 0.001139, 0.002, 0.023558     };				   
	float dumpsisat[]={-47.29 , -63.94 , -131.88, -207.34, -454.25, -131.88, -288.93,
					  -561.04, -158.05, -632.99, -390.66, -47.29};
				  
    float dumporo[]  ={ 0.3731, 0.3857, 0.4159, 0.4348, 0.4676, 0.4159, 0.4487,
		                0.4764, 0.4235, 0.4814, 0.4613, 0.50};

    float dumb[] = {3.39, 3.86, 4.50, 5.77, 4.98, 7.20, 8.32, 8.32, 9.59, 10.38, 12.13, 3.39};
 
    int  dumcolor[] = {4, 4, 4, 4,4,4,4,4,4,4,4, 4};
    
    for(int it=0; it<MAX_SOIL_TXTR; it++){
    	sand[it] = dumsand[it];
    	silt[it] = dumsilt[it];
    	clay[it] = dumclay[it];
    	Ksolids[it] = dumksolids[it];
    	Csolids[it] = dumcsolids[it];
    	Ksat[it] = dumksat[it];
    	Psisat[it] = dumpsisat[it];
    	poro[it] = dumporo[it];
    	b[it] = dumb[it];
    	bulkden[it] = getBulkden(poro[it]);
    	color[it] = dumcolor[it];
    }
     
};
	
float SoilLookup::getSolidThermalCond(const float & clay ,const float & sand ){
    float tc = (8.8 * sand +2.92 * clay)/(sand + clay);
	return tc;
};
    
float SoilLookup::getSolidVolHeatCapa(const float & clay ,const float & sand ){
    	float hc = (2.128*sand +2.385*clay)/(sand+clay) * 1.0e6;
    	return hc;
};

float SoilLookup::getSatuHydraulCond(const float & sand){
    	return   0.0070556 *pow( 10.,(-0.884+0.0153*sand) ) ;// mm/s
};
    	
float SoilLookup::getSatuMatrPotential(const float & sand){
    	return    -10. * pow( 10.,(1.88-0.0131*sand) );
};

float SoilLookup::getPorosity(const float & sand){
    	return  0.489 - 0.00126*sand;
};

float SoilLookup::getBSW(const float & clay){
    	return  2.91 + 0.159*clay;
};
    
float SoilLookup::getBulkden(const float & poro){
        return 2700 *(1-poro);	
}

float SoilLookup::getDryThermCond(const float & bulkden){
   float kdry =0.;
  
   kdry = (0.135*bulkden +64.7)/(2700-0.947*bulkden);
   return kdry;
}   



