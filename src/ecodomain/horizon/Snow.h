/*! \file
 */
 
#ifndef SNOW_H_
#define SNOW_H_

#include "../layer/SnowLayer.h"

class Snow{
	public:
		Snow();
	    ~Snow();
	
	    double age;      // years
	    int numl;		 // number of snow layers
	    double thick;    // the total thickness of snow column.(unit: m)
	    double dense;    // the averaged bulk density of snow column (kg/m3)
	    double swe;      // total snow water equivalent (kg/m2)
	    double extramass;  // snow mass not yet reaches a minimum thickness for a snow-layer (unit: kg/m2, or mm H2O)
	    double coverage;   // snow coverage: <1, if 'extramass' not zero (i.e., not yet forming a layer)

	    double dz[MAX_SNW_LAY]; //
	    double maxdz[MAX_SNW_LAY];
	    double mindz[MAX_SNW_LAY];

	    void reset();
	    void setSnowThicknesses(double dzp[], const int & maxnum);

};
#endif /*MOSS_H_*/
