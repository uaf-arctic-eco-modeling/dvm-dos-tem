#include "Moss.h"

Moss::Moss(){
	
};

Moss::~Moss(){

};

void Moss::setThicknesses(int soiltype[], double soildz[],const int &soilmaxnum){
	num =0;
	thick =0.;
   for(int i=0;i<soilmaxnum; i++){
	   if (soiltype[i]==0) {
		   dz[num] = soildz[i];
		   num ++;
		   thick += dz[i];
	   } else {
		   break;
	   }
   } 
};

