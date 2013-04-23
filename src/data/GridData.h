#ifndef GRIDDATA_H_
#define GRIDDATA_H_

#include "../inc/errorcode.h"
#include "../inc/timeconst.h"
#include "../inc/cohortconst.h"

#include <list>
using namespace std;

class GridData{
  public:
  	GridData();
  	~GridData();

  	void clear();
  
  	/* data for ONE grid (current) */
  	float lat;
    float lon;
    float alldaylengths[365]; 

	int drgtype;

    int topsoil;
    int botsoil;

    int fri;
	double pfsize[NUM_FSIZE];
	double pfseason[NUM_FSEASON];

};


#endif /*GRIDDATA_H_*/
