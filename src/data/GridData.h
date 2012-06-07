#ifndef GRIDDATA_H_
#define GRIDDATA_H_
#include "../inc/timeconst.h"
#include "../inc/cohortconst.h"
class GridData{
  public:
  	GridData();
  	~GridData();
  
    int gid;
    float lat;
    float lon;
    float alldaylengths[365]; 

    int drainageid;
	int drgtype;

    int soilid;
    int topsoil;
    int botsoil;

    int gfireid;
    int fri;
	double pfsize[NUM_FSIZE];
	double pfseason[NUM_FSEASON];

};


#endif /*GRIDDATA_H_*/
