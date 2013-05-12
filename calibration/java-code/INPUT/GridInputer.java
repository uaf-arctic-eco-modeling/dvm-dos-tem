package INPUT;

import java.io.File;
import java.io.IOException;

import ucar.ma2.Array;
import ucar.ma2.Index;
import ucar.nc2.NetcdfFile;
import ucar.nc2.Variable;

public class GridInputer {
	
	public int act_gridno;    // 'grid' number in 'grid.nc'
	public int act_drainno;   // 'drainageid' number in 'drainage.nc'
	public int act_soilno;    // 'soilid' number in 'soiltexture.nc'
	public int act_gfireno;   // 'gfireid' number in 'firestatistics.nc'	

	//all-grids
	
	Array grdidA;
	Array grdlatA;
	Array grdlonA;
	Array grddrainidA;
	Array grdsoilidA;
	Array grdfireidA;
	
	Array drainidA;
	Array drainagetypeA;
	
	Array soilidA;
	Array topsoilA;
	Array botsoilA;

	Array gfireidA;
	Array friA;
	Array pfseasonA;
	Array pfsizeA;
			
	public void init(String grdinputdir){
  
		initGrid(grdinputdir);
		initDrainType(grdinputdir);
		initSoilTexture(grdinputdir);
		initFireStatistics(grdinputdir);

	};
	
	void initGrid(String dir){
		String filename = dir +"grid.nc";
		
		NetcdfFile ncfile = null;
		File ffile = new File(filename);
		if (ffile.exists()){
			try {
				ncfile = NetcdfFile.open(filename);

				Variable var0 = ncfile.findVariable("GRIDID");
				grdidA = var0.read();
				
				act_gridno = grdidA.getShape()[0];

				Variable var1 = ncfile.findVariable("LAT");
				grdlatA = var1.read();

				Variable var2 = ncfile.findVariable("LON");
				grdlonA = var2.read();

				Variable var3 = ncfile.findVariable("DRAINAGEID");
				grddrainidA = var3.read();

				Variable var4 = ncfile.findVariable("SOILID");
				grdsoilidA = var4.read();
				
				Variable var5 = ncfile.findVariable("GFIREID");
				grdfireidA = var5.read();
												
			} catch (IOException ioe) {
					System.out.println(ioe.getMessage());
			} finally {
					if (ncfile != null) {
						try {
							ncfile.close();
						} catch (IOException ioee) {
							System.out.println(ioee.getMessage());
						}
					}
			}
		}else {   //file not exist
			System.out.println("Input file: "+filename+" NOT existed");
		}
	 
	};

	void initSoilTexture(String dir){
		String filename = dir +"soiltexture.nc";

		NetcdfFile ncfile = null;
		File ffile = new File(filename);
		if (ffile.exists()){
			try {
				ncfile = NetcdfFile.open(filename);

				Variable var6 = ncfile.findVariable("SOILID");
				soilidA = var6.read();

				act_soilno = soilidA.getShape()[0];

				Variable var7 = ncfile.findVariable("TOPSOIL");
				topsoilA = var7.read();

				Variable var8 = ncfile.findVariable("BOTSOIL");
				botsoilA = var8.read();

			} catch (IOException ioe) {
				System.out.println(ioe.getMessage());
			} finally {
				if (ncfile != null) {
					try {
						ncfile.close();
					} catch (IOException ioee) {
						System.out.println(ioee.getMessage());
					}
				}
			}
		}else {   //file not exist
			System.out.println("Input file: "+filename+" NOT existed");
			System.exit(-1);
		}

	};

	void initDrainType(String dir){
		String filename = dir +"drainage.nc";
 	
		NetcdfFile ncfile = null;
		File drgfile = new File(filename);
		if (drgfile.exists()){
			try {
				ncfile = NetcdfFile.open(filename);
				Variable drgidV = ncfile.findVariable("DRAINAGEID");
				drainidA = drgidV.read();

				act_drainno = drainidA.getShape()[0];

				Variable drgtypeV = ncfile.findVariable("DRAINAGETYPE");
				drainagetypeA = drgtypeV.read();

			} catch (IOException ioe) {
				System.out.println(ioe.getMessage());
			} finally {
				if (ncfile != null) {
					try {
						ncfile.close();
					} catch (IOException ioee) {
						System.out.println(ioee.getMessage());
					}
				}
			}
		} else {   //file not exist
			System.out.println("Input file: "+filename+" NOT existed");
		}
 
	};

	void initFireStatistics(String dir){
		String filename = dir+"firestatistics.nc";
		
		NetcdfFile ncfile = null;
		File ffile = new File(filename);
		if (ffile.exists()){
			try {
				ncfile = NetcdfFile.open(filename);
				Variable var0 = ncfile.findVariable("GFIREID");
				gfireidA = var0.read();

				act_gfireno = gfireidA.getShape()[0];

				Variable var1 = ncfile.findVariable("FRI");
				friA = var1.read();

				Variable var2 = ncfile.findVariable("PFSEASON");
				pfseasonA = var2.read();

				Variable var3 = ncfile.findVariable("PFSIZE");
				pfsizeA = var3.read();

			} catch (IOException ioe) {
				System.out.println(ioe.getMessage());
			} finally {
				if (ncfile != null) {
					try {
						ncfile.close();
					} catch (IOException ioee) {
						System.out.println(ioee.getMessage());
					}
				}
			}
		}else {   //file not exist
			System.out.println("Input file: "+filename+" NOT existed");
			System.exit(-1);
		}
 
	};

	public int getGridids(int gridids [], int recno){    //get recid (starts from 0) from grid id (gid)
		try {
			Index ind0 = grdidA.getIndex();
			gridids[0] = grdidA.getInt(ind0.set(recno));
		
			Index ind1 = grddrainidA.getIndex();
			gridids[1] = grddrainidA.getInt(ind1.set(recno));

			Index ind2 = grdsoilidA.getIndex();
			gridids[2] = grdsoilidA.getInt(ind2.set(recno));

			Index ind3 = grdfireidA.getIndex();
			gridids[3] = grdfireidA.getInt(ind3.set(recno));
				
			return 0;
		
		} catch (Exception ex) {

			System.err.println("TEM input 'grid.nc' failed (ids reading)! - "+ex);		
			
			return -1;
		}

	}; 

	public int getDrainId(int recno){ 
		try {
			Index ind = drainidA.getIndex();
			return drainidA.getInt(ind.set(recno));
		
		} catch (Exception ex) {

			System.err.println("TEM input 'drainage.nc' failed (id reading)! - "+ex);		
		
			return -1;
		}

	}; 

	public int getSoilId(int recno){
		try {
			Index ind = soilidA.getIndex();

			return soilidA.getInt(ind.set(recno));
		} catch (Exception ex) {

			System.err.println("TEM input 'soiltexture.nc' failed (id reading)! - "+ex);		
	
			return -1;
		}

	}; 

	public int getGfireId(int recno){
		try {
			Index ind = gfireidA.getIndex();

			return gfireidA.getInt(ind.set(recno));
		} catch (Exception ex) {

			System.err.println("TEM input 'firestatistic.nc' failed (id reading)! - "+ex);		
	
			return -1;
		}
		
	}; 

	public int getDrainType(int recid){   //recid starts from 0
		
		try {
			Index ind = drainagetypeA.getIndex();
			return drainagetypeA.getInt(ind.set(recid));
		
		} catch (Exception ex) {

			System.err.println("TEM input 'drainage.nc' failed (drainage type reading)! - "+ex);		
	
			return -1;
		}
		
	}; 

	//
	public int getLatlon(float latlon[], int recid){   //recid starts from 0
		try {
			
			Index ind0 = grdlatA.getIndex();
			latlon[0]  = grdlatA.getFloat(ind0.set(recid));
		
			Index ind1 = grdlonA.getIndex();
			latlon[1]  = grdlonA.getFloat(ind1.set(recid));
			
			return 0;
		
		} catch (Exception ex) {

			System.err.println("TEM input 'grid.nc' failed (lat/lon reading)! - "+ex);		
	
			return -1;
		}
	
	}; 

	public int getSoilTexture(int soiltexture[], int recid){   //recid starts from 0
		try {
			
			Index ind1 = topsoilA.getIndex();
			soiltexture[0] = topsoilA.getInt(ind1.set(recid));

			Index ind2 = botsoilA.getIndex();
			soiltexture[1] = botsoilA.getInt(ind2.set(recid));
			
			return 0;
		
		} catch (Exception ex) {

			System.err.println("TEM input 'soiltexture.nc' failed (texture reading)! - "+ex);		

			return -1;
		}
		
	}; 

	public int getGfire(double pfseason[], double pfsize[], int recid){     //recid starts from 0

		try {
		
			Index ind1 = friA.getIndex();
			int fri=friA.getInt(ind1.set(recid));
			
			Index ind2 = pfseasonA.getIndex();
			int[] ij = pfseasonA.getShape();
			for (int j = 0; j <ij[1]; j++) {
				pfseason[j] = pfseasonA.getDouble(ind2.set(recid,j));
			}

			Index ind3 = pfsizeA.getIndex();
			ij = pfsizeA.getShape();
			for (int j = 0; j < ij[1]; j++) {
				pfsize[j] = pfsizeA.getDouble(ind3.set(recid,j));
			}
		
			return fri;
				
		} catch (Exception ex) {

			System.err.println("TEM input 'firestatistic.nc' failed (data reading)! - "+ex);		

			return -1;
		}


	}; 

}
