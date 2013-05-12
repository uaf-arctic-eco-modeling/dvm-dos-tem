#ifndef ATMOSUTIL_H_
#define ATMOSUTIL_H_
//provides utilities for creating datasets for equlibrium and spinup run
//and for creating daily drivings

#include <string>
#include <iostream>
#include <fstream>
#include <sstream>
#include <ctime>
#include <cstdlib>
using namespace std;

#include "../util/Interpolator.h"


class AtmosUtil{
	
	public:
	AtmosUtil();
	~AtmosUtil();
	
	
	void updateDailyDriver(float tad[],const float prevta, const float curta, const float nextta, const int & dinmprev, 
		const int & dinmcurr, const int & dinmnext);
		
	void updateDailyPrec(float precd[], const int & dinmcurr , const float & mta, const float & mprec);
	
	private:
	Interpolator itp;
	double RAININTE[32], RAINDUR[32];
	
};
#endif /*ATMOSUTIL_H_*/
