/*
 * RunGrid.cpp
 * 
 * Grid-level initialization, run, and output (if any)
 * 		Note: the output modules are put here, so can be flexible for outputs
 * 
*/

#include "RunGrid.h"

RunGrid::RunGrid(){
	// grided data record ids in .nc files
	gridrecno  = MISSING_I;
	drainrecno = MISSING_I;
	soilrecno  = MISSING_I;
	gfirerecno = MISSING_I;

};

RunGrid::~RunGrid(){

};

void RunGrid::setModelData(ModelData * mdp){
  	md= mdp;
};

//reading grid-level all data ids
int RunGrid::allgridids(){
	int error = 0;
	int id = MISSING_I;
	int id1 = MISSING_I;
	int id2 = MISSING_I;
	int id3 = MISSING_I;

	for (int i=0; i<md->act_gridno; i++) {
		error = ginputer.getGridids(id, id1, id2, id3, i);
		if (error!=0) return error;
		grdids.push_back(id);
		grddrgids.push_back(id1);
		grdsoilids.push_back(id2);
		grdfireids.push_back(id3);
	}

	for (int i=0; i<md->act_drainno; i++) {
		error = ginputer.getDrainId(id, i);
		if (error!=0) return error;
		drainids.push_back(id);
	}

	for (int i=0; i<md->act_soilno; i++) {
		error = ginputer.getSoilId(id, i);
		if (error!=0) return error;
		soilids.push_back(id);
	}

	for (int i=0; i<md->act_gfireno; i++) {
		error = ginputer.getGfireId(id, i);
		if (error!=0) return error;
		gfireids.push_back(id);
	}

	return error;
};

//reading data for ONE grid, using its record no (the order) in .nc files,
// which must be known before calling
int RunGrid::readData(){

	//reading the grided 'lat/lon' data
  	if (gridrecno<0) return -1;
	ginputer.getLatlon(grid.gd.lat, grid.gd.lon, gridrecno);

	//reading the grided 'drainage type' data
  	if (drainrecno<0) return -2;
	ginputer.getDrainType(grid.gd.drgtype, drainrecno);

	//reading the grided 'soil texture' data
  	if (soilrecno<0) return -3;
	ginputer.getSoilTexture(grid.gd.topsoil, grid.gd.botsoil, soilrecno);

	//reading the grided 'fire' data
  	if (gfirerecno<0) return -4;
	ginputer.getGfire(grid.gd.fri, grid.gd.pfseason, grid.gd.pfsize, gfirerecno);

	//
	grid.reinit();          //checking grid data
	
    return 0;
};
