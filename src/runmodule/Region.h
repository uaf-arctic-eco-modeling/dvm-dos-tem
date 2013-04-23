#ifndef REGION_H_
#define REGION_H_

#include <cmath>
#include <iostream>
using namespace std;

#include "../data/RegionData.h"

#include "../inc/errorcode.h"

class Region{
	public :
		Region();
		~Region();
	
		RegionData rd;
	
		void init();
		void getinitco2();
		//void setRegionData(RegionData *rd);

};
#endif /*REGION_H_*/
