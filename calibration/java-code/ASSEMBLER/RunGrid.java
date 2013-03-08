/*
 * RunGrid.java
 * 
 * Grid-level initialization, run, and output (if any)
 * 		Note: the output modules are put here, so can be flexible for outputs
 * 
*/
package ASSEMBLER;

import TEMJNI.Grid;

import DATA.DataGrid;
import INPUT.GridInputer;

public class RunGrid {

	public Grid grid = new Grid();
	public GridInputer ginputer = new GridInputer();
	
	DataGrid jgd = new DataGrid();   //this is for ONE cohort only
	
	//when initializing a grid, using its grdids
	public int reinit(int grdid){

		jgd.gid = grdid;
		
		// grided data record ids in .nc files
		int grecid    = - 999;
		int drgrecid  = - 999;
		int soilrecid = - 999;
		int gfrecid= - 999;

		grecid=ginputer.getGridDataids(jgd, grdid);
		if (grecid<0) return -1;

	    //reading the grided 'drainage type' data
		drgrecid = ginputer.getDrainRecid(jgd.drainageid);
		if (drgrecid<0) return -2;
		ginputer.getDrainType(jgd.drgtype, drgrecid);

		//reading the grided 'soil texture' data
		soilrecid = ginputer.getSoilRecid(jgd.soilid);
		if (soilrecid<0) return -3;
		ginputer.getSoilTexture(jgd, soilrecid);

		//reading the grided 'fire' data
		gfrecid = ginputer.getGfireRecid(jgd.gfireid);
		if (gfrecid<0) return -4;
		ginputer.getGfire(jgd, gfrecid);

		//assign the java-read-in data to 'c++' holder
		grid.getGd().setGid(jgd.gid);
		grid.getGd().setLat(jgd.lat);
		grid.getGd().setLon(jgd.lon);
		
		grid.getGd().setDrainageid(jgd.drainageid);
		grid.getGd().setDrgtype(jgd.drgtype);
		
		grid.getGd().setSoilid(jgd.soilid);
		grid.getGd().setTopsoil(jgd.topsoil);
		grid.getGd().setBotsoil(jgd.botsoil);
		
		grid.getGd().setGfireid(jgd.gfireid);
		grid.getGd().setFri(jgd.fri);
		grid.getGd().setPfseason(jgd.pfseason);
		grid.getGd().setPfsize(jgd.pfsize);
		
		//checking grid data
		grid.reinit();          
	
		return 0;
	};

}

