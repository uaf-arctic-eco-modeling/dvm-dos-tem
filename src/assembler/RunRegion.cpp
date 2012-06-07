/*
 * RunRegion.cpp
 * 
 * Region-level initialization, run, and output (if any)
 * 		Note: the output modules are put here, so can be flexible for outputs
 * 
*/

#include "RunRegion.h"

RunRegion::RunRegion(){

};

RunRegion::~RunRegion(){

};

int RunRegion::reinit(const int &recid){
	if (recid<0) return -1;

	region.rd.act_co2yr = rinputer.act_co2yr;
	rinputer.getCO2(&region.rd);

	region.init();

	region.getinitco2();

	return 0;
};


