#ifndef REGIONDATA_H_
#define REGIONDATA_H_

#include "../inc/timeconst.h"

class RegionData{
  	public:
  		RegionData();
  		~RegionData();
    
    	int act_co2yr;
  		int co2year[MAX_CO2_DRV_YR];
    	float co2[MAX_CO2_DRV_YR];

    	double initco2;

};

#endif /*REGIONDATA_H_*/
