#ifndef GRIDINPUTER_H_
#define GRIDINPUTER_H_

/*! this class is used to readin input of parameters, forcings for TEM
 * \file
 *
 * Modified by F-M Yuan, due to memory-leaking
 *
 */

#include <vector>
#include <iostream>
#include <fstream>
#include <cstdio>
#include <string>
#include <cmath>
using namespace std;

#include "netcdfcpp.h"

#include "../inc/layerconst.h"
#include "../inc/ErrorCode.h"
#include "../data/GridData.h"

//local header
#include "../runmodule/ModelData.h"

class GridInputer{
	public:
		GridInputer();
		~GridInputer();

    	void init();

        // grid data
    	int getGridDataids(float &lat, float &lon, int &drainid, int &soilid,
    			int &gfireid, const int & gid);

    	int getDrainRecid(const int & drainid);
    	int getSoilRecid(const int & soilid);
    	int getGfireRecid(const int & gfireid);

    	void getDrainType(int & drgtype, const int & recid);
    	void getSoilTexture(int & topsoil, int & botsoil, const int & recid);

		void getGfire(int &fri, double pfseason[], double pfsize[],const int & recid);

    	void setModelData(ModelData* mdp);


	private:

    	void initGrid(string& dir);
		void initDrainType(string& dir);
    	void initSoilTexture(string& dir);
		void initFireStatistics(string& dir);

		void getLatLon(float & lat, float & lon, const int & recid);

		string gridfname;
		string drainfname;
		string soilfname;
		string gfirefname;

		ModelData* md;

};


#endif /*GRIDINPUTER_H_*/
