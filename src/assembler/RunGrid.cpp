/*
 * RunGrid.cpp
 * 
 * Grid-level initialization, run, and output (if any)
 * 		Note: the output modules are put here, so can be flexible for outputs
 * 
*/

#include "RunGrid.h"

RunGrid::RunGrid(){

};

RunGrid::~RunGrid(){

};

void RunGrid::setModelData(ModelData * mdp){
  	md= mdp;
};

//when initializing a grid, using its grdids
int RunGrid::reinit(const int &grdid){

	grid.gd.gid = grdid;

	// grided data record ids in .nc files
	int grecid    = - 999;
	int drgrecid  = - 999;
	int soilrecid = - 999;
	int gfrecid= - 999;

	grecid=ginputer.getGridDataids(grid.gd.lat, grid.gd.lon, grid.gd.drainageid,
			grid.gd.soilid, grid.gd.gfireid, grdid);
  	if (grecid<0) return -1;

	//reading the grided 'drainage type' data
  	drgrecid = ginputer.getDrainRecid(grid.gd.drainageid);
  	if (drgrecid<0) return -2;
	ginputer.getDrainType(grid.gd.drgtype, drgrecid);

	//reading the grided 'soil texture' data
  	soilrecid = ginputer.getSoilRecid(grid.gd.soilid);
  	if (soilrecid<0) return -3;
	ginputer.getSoilTexture(grid.gd.topsoil, grid.gd.botsoil, soilrecid);

	//reading the grided 'fire' data
  	gfrecid = ginputer.getGfireRecid(grid.gd.gfireid);
  	if (gfrecid<0) return -4;
	ginputer.getGfire(grid.gd.fri, grid.gd.pfseason, grid.gd.pfsize, gfrecid);

	//
	grid.reinit();          //checking grid data
	
    return 0;
};
