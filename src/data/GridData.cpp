#include "GridData.h"

GridData::GridData(){
	
};

GridData::~GridData(){
	
};

void GridData::clear(){

  	lat = MISSING_F;
    lon = MISSING_F;
    fill_n(alldaylengths, 365, MISSING_F);

	drgtype = MISSING_I;

    topsoil = MISSING_I;
    botsoil = MISSING_I;

    fri = MISSING_I;
	fill_n(pfsize, NUM_FSIZE, MISSING_D);
	fill_n(pfseason, NUM_FSEASON, MISSING_D);

};

