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

#include <netcdfcpp.h>

//local header
#include "../runmodule/ModelData.h"

#include "../inc/cohortconst.h"
#include "../inc/layerconst.h"
#include "../inc/timeconst.h"
#include "../inc/errorcode.h"

class CohortInputer{
	public:
		CohortInputer();
		~CohortInputer();

		void setModelData(ModelData *mdp);
		int init();

		int getChtDataids(int &chtid, int & inichtid, int & gridid,
				int & clmid, int & vegid, int & fireid, const int &recno);

		int getInitchtId(int &initchtid, const int &recno);
		int getClmId(int &clmid, const int &recno);
		int getVegId(int &vegid, const int &recno);
		int getFireId(int &fireid, const int &recno);

		void getClimate(float tair[], float prec[], float nirr[], float vap[],
				const int& yrno, const int & recno);

		void getVegetation(int vsetyr[], int vtype[], double vfrac[], const int & recno);

		void getFire(int fyear[], int fseason[], int fsize[], const int &recno);
		void getFireSeverity(int fseverity[], const int &recno);

	private:
	 
		 ModelData *md;
		 string chtidfname;
		 string chtinitfname;
		 string clmfname;
		 string vegfname;
		 string firefname;

		 int initChtidFile();
		 int initChtinitFile();
		 int initClmFile();
		 int initVegFile();
		 int initFireFile();
	
};


#endif /*COHORTINPUTER_H_*/
