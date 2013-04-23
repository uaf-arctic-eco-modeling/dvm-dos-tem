/*! \file
 */
#ifndef MINERAL_H_
#define MINERAL_H_
 
#include <iostream>
#include "../layer/MineralLayer.h"

using namespace std;

class Mineral{
	public:
		Mineral();
		~Mineral();

		int num;	    /*! number of mineral layer*/
		double thick;   // total thickness of mineral soils (m)
 
		double dz[MAX_MIN_LAY];  // thickness of each mineral layer (m)
		int texture[MAX_MIN_LAY];   // soil texture of each layer
   
		void setDefaultThick(const double & thickness);
		void set5Soilprofile(int soiltype[], double dz[],int textures[], const int & maxnum);
	
};
#endif /*MINERAL_H_*/
