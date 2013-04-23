#ifndef SOILPARENT_H_
#define SOILPARENT_H_
#include "../layer/ParentLayer.h"

class SoilParent{
	public:
		SoilParent();
		~SoilParent();
	
		int num;/*! number of soil parent layer*/
	
		double thick;/*! total thickness of all soil parent layers (m) */
	
		double dz[MAX_ROC_LAY];
		double type[MAX_ROC_LAY];    // 1- bed rock; 2 - weathered soil parent materials (not used currently)

		void updateThicknesses(const double & thickness);
	
};

#endif /*ROCK_H_*/
