#include "Mineral.h"

Mineral::Mineral(){
	setDefaultThick(0.);
};

Mineral::~Mineral(){
	
};

void Mineral::setDefaultThick(const double & thickness){
	// The following is the default thickness and number of mineral layers (Yuan)
	num = MAX_MIN_LAY;
	thick = 0.0;
	for (int i=0; i<MAX_MIN_LAY; i++) {
		dz[i]=MINETHICK[i];   // default thickness (defined in MINETHICK[] in /inc/layerconst.h)
		thick+=dz[i];
	}

	// if total thickness input, needs update the actual bottom layer's thickness
	if (thickness > 0.) {
		thick = 0.0;
		num = 0;
		for (int i=0; i<MAX_MIN_LAY; i++){
			thick += dz[i];
			if (thick >= thickness) {
				dz[i] = thick - thickness;
				thick = thickness;

				break;
			} else if (i==MAX_MIN_LAY-1){     // last layer, but still input thickness too large
				dz[i] += thickness - thick;   // add the rest into the bottom layer
				thick = thickness;
			}

		num ++;
		}
	}
};


void Mineral::set5Soilprofile(int soiltype[], double soildz[], int soiltexture[], const int & maxnum){

	num =0;
	thick =0.;
	for(int i=0; i<maxnum; i++){
		if (soiltype[i]==3) {
			dz[num]    = soildz[i];
			texture[num] = soiltexture[i];
			num ++;
			thick += soildz[i];
		}
    } 
};
	
