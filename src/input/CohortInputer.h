#ifndef COHORTINPUTER_H_
#define COHORTINPUTER_H_

/*! this class is used to readin input of parameters, forcings for TEM
 * \file
 */

#include <iostream>
#include <fstream>
#include <cstdio>
#include <string>
#include <cmath>

using namespace std;

#include "netcdfcpp.h"

//local header
#include "../runmodule/ModelData.h"

#include "../inc/cohortconst.h"
#include "../inc/layerconst.h"
#include "../inc/timeconst.h"
#include "../inc/ErrorCode.h"

class CohortInputer{
	public:
		CohortInputer();
		~CohortInputer();

		int act_clmyr;
		int act_vegset;
		int act_fireset;

		void init(string & dir);

		int getChtDataids(int & inichtid, int & grdid, int & clmid,int & vegid,
				int & fireid, const int &chtid);

		int getClmRec(const int &clmid);
		int getVegRec(const int &vegid);
		int getFireRec(const int &fireid);

		void getClimate(float tair[], float prec[], float nirr[], float vap[],
				const int& yrno, const int & recid);

		void getVegetation(int vsetyr[], int vtype[], double vfrac[], const int & recid);

		void getFire(int fyear[], int fseason[], int fsize[], const int &recid);
		void getFireSeverity(int fseverity[], const int &recid);

	private:
	 
		 string chtidfname;
		 string clmfname;
		 string vegfname;
		 string firefname;

		 void initChtidFile(string& dir);
		 int initClmFile(string& dir);
		 int initVegFile(string& dir);
		 int initFireFile(string& dir);
	
};


#endif /*COHORTINPUTER_H_*/
