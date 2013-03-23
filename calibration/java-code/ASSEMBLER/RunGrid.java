/*
 * RunGrid.java
 * 
 * Grid-level initialization, run, and output (if any)
 * 		Note: the output modules are put here, so can be flexible for outputs
 * 
*/
package ASSEMBLER;

import java.util.ArrayList;
import java.util.List;

import TEMJNI.Grid;

import DATA.DataGrid;
import INPUT.GridInputer;

public class RunGrid {

	public Grid grid = new Grid();
	public GridInputer ginputer = new GridInputer();
	
	/* all grid data id lists
	 * ids are labeling the datasets, which exist in .nc files
 	 * and, the order (index) in these lists are actually record no. in the .nc files
 	 */
	public List<Integer> grdids     = new ArrayList<Integer>();   // 'grid.nc'
	public List<Integer> grddrgids  = new ArrayList<Integer>();
	public List<Integer> grdsoilids = new ArrayList<Integer>();
	public List<Integer> grdfireids = new ArrayList<Integer>();
	
	public List<Integer> drainids = new ArrayList<Integer>();  // 'drainage.nc'
	public List<Integer> soilids  = new ArrayList<Integer>();  // 'soiltexture.nc'
	public List<Integer> gfireids = new ArrayList<Integer>();  // 'firestatistics.nc'
	
	DataGrid jgd = new DataGrid();   //this is for ONE cohort only
	// grided data record numbers in .nc files
	public int gridrecno  = - 9999;
	public int drainrecno = - 9999;
	public int soilrecno  = - 9999;
	public int gfirerecno = - 9999;
	
	//reading grid-level all data ids
	public int allgridids(int act_gridno, int act_drainno, int act_soilno,
			int act_gfireno){
		int error = 0;
		int id = -9999;
		int ids [] = new int[4];

		for (int i=0; i<act_gridno; i++) {
			error = ginputer.getGridids(ids, i);
			if (error!=0) {
				return error;
			}
			grdids.add(ids[0]);
			grddrgids.add(ids[1]);
			grdsoilids.add(ids[2]);
			grdfireids.add(ids[3]);
		}

		for (int i=0; i<act_drainno; i++) {
			id = ginputer.getDrainId(i);
			drainids.add(id);
		}

		for (int i=0; i<act_soilno; i++) {
			id = ginputer.getSoilId(i);
			soilids.add(id);
		}

		for (int i=0; i<act_gfireno; i++) {
			id = ginputer.getGfireId(i);
			gfireids.add(id);
		}

		return error;
	};

	//reading data for ONE grid, using its record no (the order) in .nc files,
	// which must be known before calling
	public int readData(){
	
		// reading the grided 'lat/lon' data ('grid.nc')
		if (gridrecno<0) return -1;
		float latlon [] = new float[2];
		ginputer.getLatlon(latlon, gridrecno);
		jgd.lat = latlon[0];
		jgd.lon = latlon[1];
	   
		//reading the grided 'drainage type' data ('drainage.nc')
		if (drainrecno<0) return -2;
		jgd.drgtype = ginputer.getDrainType(drainrecno);

		//reading the grided 'soil texture' data ('soiltexture.nc')
		if (soilrecno<0) return -3;
		int soiltexture[] = new int[2];
		ginputer.getSoilTexture(soiltexture, soilrecno);
		jgd.topsoil = soiltexture[0];
		jgd.botsoil = soiltexture[1];
		
		//reading the grided 'fire' data
		if (gfirerecno<0) return -4;
		jgd.fri=ginputer.getGfire(jgd.pfseason, jgd.pfsize, gfirerecno);

		//assign the java-read-in data to 'c++' holder
		grid.getGd().setLat(jgd.lat);
		grid.getGd().setLon(jgd.lon);
		
		grid.getGd().setDrgtype(jgd.drgtype);
		
		grid.getGd().setTopsoil(jgd.topsoil);
		grid.getGd().setBotsoil(jgd.botsoil);
		
		grid.getGd().setFri(jgd.fri);
		grid.getGd().setPfseason(jgd.pfseason);
		grid.getGd().setPfsize(jgd.pfsize);
		
		//checking grid data
		grid.reinit();          
	
		return 0;
	};

}

