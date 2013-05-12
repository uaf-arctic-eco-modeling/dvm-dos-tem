#include "SoilParent.h"

SoilParent::SoilParent(){
	
}

SoilParent::~SoilParent(){
	
}

void SoilParent::updateThicknesses(const double & thickness){

	num = 0;
    thick = 0.;
	for (int i=0; i<MAX_ROC_LAY; i++){
		dz[i] = ROCKTHICK[i];
		thick+=dz[i];
		num++;
		if (thick > thickness) {
			dz[i] -= (thick-thickness);
			thick = thickness;
			break;
		}

	}

};



