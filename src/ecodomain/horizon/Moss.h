/*! \file
 */
 
#ifndef MOSS_H_
#define MOSS_H_

#include "../layer/MossLayer.h"

class Moss{
	public:
		Moss();
		~Moss();
	
		int num;   // num of moss layers
		int type;  // moss types: 1: sphagnum; 2: feathermoss; 3: other (including lichen)
		double dmossc; // dead moss C (kg/m2), which not included in SOM, is always in the last moss layer;
		               // AND, used as a tracker to determine if a moss horizon exists.
		double thick;  // in meter
		double dz[MAX_MOS_LAY];

		void setThicknesses(int soiltype[], double soildz[],const int & soilmaxnum);
};
#endif /*MOSS_H_*/
