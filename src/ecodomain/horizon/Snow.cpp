#include "Snow.h"

Snow::Snow(){
	
	int indl=0;
	mindz[indl] =0.005;
	maxdz[indl] =0.10;
	
	indl++;
	mindz[indl] =0.045;
	maxdz[indl] =0.15;
	
	indl++;
	mindz[indl] =0.075;
	maxdz[indl] =0.33;

    indl++;
	mindz[indl] =0.165;
	maxdz[indl] =0.69;
	
	indl++;
	mindz[indl] =0.345;
	maxdz[indl] =1.00;

	indl++;
	mindz[indl] =0.670;
	maxdz[indl] =100;
	
	reset();

};

Snow::~Snow(){
	
};

void Snow::setSnowThicknesses(double dzp[], const int & maxnum){
	numl   = 0;
	thick  = 0.;

   	for(int i=0; i<maxnum; i++){
   		if (i<MAX_SNW_LAY) {
   			dz[i] = dzp[i];
   			numl++;
   		}else {
   			dz[numl-1] += dzp[i];
   		}

   		thick+= dz[i];
   	}
};

void Snow::reset(){
	thick= 0.;
	numl = 0;
	age  = 0.;

   	for(int i=0; i<MAX_SNW_LAY; i++){
   		dz[i] = MISSING_D;
   	}

	coverage = 0.;
	swe      = 0.;
	dense    = 0.;
	extramass = 0.;

};


