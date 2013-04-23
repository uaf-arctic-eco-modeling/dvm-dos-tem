/*! \file 
 */
 
#include "Grid.h"

Grid::Grid(){
  
}

// deconstructor
Grid::~Grid(){
  
}

// initialization
int Grid::reinit(){

	for (int id=0; id<365; id++){
	   //  the following are the original algorithm, and modified as below by Yi (2013 Feb)
       //  double ampl;
       //  ampl = exp(7.42 +0.045 *gd.lat)/3600.;
       //  gd.alldaylengths[id] = ampl * (sin ((id -79) *0.01721)) +12.0;

    	double daylength = 0.0;
    	//http://www.jgiesen.de/astro/solarday.htm
        //http://www.gandraxa.com/length_of_day.xml
        //make sure all arguments in sin, cos and tan are in unit of arc (not degree)
    	double pi =3.14159;
    	double m = 1- tan(gd.lat*pi/180.0)* tan(23.45*cos(id*pi/182.625)*pi/180.0);
    	m = fmax(m, 0.);
    	m = fmin(m, 2.);

    	double b = acos(1-m)/pi;

    	daylength = b*24;
    	gd.alldaylengths[id] = daylength;
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








