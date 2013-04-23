#ifndef GRID_H_
#define GRID_H_

#include <cmath>
#include <iostream>
using namespace std;

#include "../data/GridData.h"
#include "../data/RegionData.h"
#include "../data/EnvData.h"
#include "../data/BgcData.h"

#include "../inc/errorcode.h"

class Grid{
	public :
	Grid();
	~Grid();

	int reinit();
	
 	void setEnvData(EnvData * ed);
 	void setBgcData(BgcData * bd);
 	void setRegionData(RegionData *rd);
	
    EnvData *grded;   // 'ed' integrated over whole grid
    BgcData *grdbd;   // 'bd' integrated over whole grid
    RegionData* rd;

    GridData gd;

};
#endif /*GRID_H_*/
