/*! \file 
 */
 
#include "Grid.h"
// constructor 
Grid::Grid(){
  
}

// deconstructor
Grid::~Grid(){
  
}

// initialization
int Grid::reinit(){

    double ampl;
	for (int id=0; id<365; id++){
       	ampl = exp(7.42 +0.045 *gd.lat)/3600.;
       	gd.alldaylengths[id] = ampl * (sin ((id -79) *0.01721)) +12.0;
	}

 
    //check for the validity of grid level data
  	if(gd.fri<0|| gd.fri>2000){
  	 	gd.fri =2000;
  	}

  	//testing
  	gd.fri = 60;
  	gd.pfseason[1] = 0.80;
  	gd.pfsize[1] = 0.80;
  
  	if(gd.topsoil <0 || gd.botsoil <0){
  	    return -2;
  	}
  
  	return 0;

}

//'ed' for the whole grid
void Grid::setEnvData(EnvData* edp){
	grded = edp;
}

//'bd' for the whole grid
void Grid::setBgcData(BgcData* bdp){
	grdbd = bdp;
}

//inputs
void Grid::setRegionData(RegionData* rdp){
	rd = rdp;
}








