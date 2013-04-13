#ifndef REGIONINPUTER_H_
#define REGIONINPUTER_H_
/*! this class is used to readin input of parameters, forcings for TEM
 * \file
 */

 
#include <iostream>
#include <fstream>
#include <cstdio>
#include <string>
#include <cmath>
using namespace std;

#include <netcdfcpp.h>

#include "../data/RegionData.h"
#include "../runmodule/ModelData.h"

class RegionInputer{
	public:
		RegionInputer();
		~RegionInputer();

		string co2filename;

		int act_co2yr;

		void init();

    // regional-level data
		int initCO2file(string & dir);
		void getCO2(RegionData * rd);
	
		void setModelData(ModelData* mdp);
	
	private:
		ModelData* md;
	
};

#endif /*REGIONINPUTER_H_*/
