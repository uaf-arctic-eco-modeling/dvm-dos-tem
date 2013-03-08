package INPUT;

import java.io.File;
import java.io.IOException;

import ucar.ma2.Array;
import ucar.ma2.Index;
import ucar.nc2.NetcdfFile;
import ucar.nc2.Variable;

import DATA.DataGrid;

public class GridInputer {
	
	//all-grids
	
	Array grididA;
	Array latA;
	Array lonA;
	Array gdrainidA;
	Array gsoilidA;
	Array gfireidA;
	
	Array drainidA;
	Array drainagetypeA;
	
	Array soilidA;
	Array topsoilA;
	Array botsoilA;

	Array fireidA;
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
				grididA = var0.read();

				Variable var1 = ncfile.findVariable("LAT");
				latA = var1.read();

				Variable var2 = ncfile.findVariable("LON");
				lonA = var2.read();

				Variable var3 = ncfile.findVariable("DRAINAGEID");
				gdrainidA = var3.read();

				Variable var4 = ncfile.findVariable("SOILID");
				gsoilidA = var4.read();
				
				Variable var5 = ncfile.findVariable("GFIREID");
				gfireidA = var5.read();
												
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

	public void initDrainType(String dir){
		String filename = dir +"drainage.nc";
 	
		NetcdfFile ncfile = null;
		File drgfile = new File(filename);
		if (drgfile.exists()){
			try {
				ncfile = NetcdfFile.open(filename);
				Variable drgidV = ncfile.findVariable("DRAINAGEID");
				drainidA = drgidV.read();

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
				fireidA = var0.read();

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

	public int getGridDataids(DataGrid jgd, int gid){    //get recid (starts from 0) from grid id (gid)
		Index ind = grididA.getIndex();
		for (int i=0; i<grididA.getSize(); i++) {
			if (grididA.getInt(ind.set(i))==gid) {

				Index ind1 = latA.getIndex();
				jgd.lat = latA.getFloat(ind1.set(i));

				Index ind2 = lonA.getIndex();
				jgd.lon = lonA.getFloat(ind2.set(i));

				Index ind3 = gdrainidA.getIndex();
				jgd.drainageid = gdrainidA.getInt(ind3.set(i));

				Index ind4 = gsoilidA.getIndex();
				jgd.soilid = gsoilidA.getInt(ind4.set(i));

				Index ind5 = gfireidA.getIndex();
				jgd.gfireid = gfireidA.getInt(ind5.set(i));

				return i;
			}
		}
		return -1;

	}; 

	public int getDrainRecid(int drainid){    //get recid (starts from 0)
		Index ind = drainidA.getIndex();
		for (int i=0; i<drainidA.getSize(); i++) {
			if (drainidA.getInt(ind.set(i))==drainid) {
				return i;
			}
		}
		return -1;

	}; 

	public int getSoilRecid(int soilid){    //get recid (starts from 0)
		Index ind = soilidA.getIndex();
		for (int i=0; i<soilidA.getSize(); i++) {
			if (soilidA.getInt(ind.set(i))==soilid) {
				return i;
			}
		}
		return -1;

	}; 

	public int getGfireRecid(int fireid){    //get recid (starts from 0)
		Index ind = fireidA.getIndex();
		for (int i=0; i<fireidA.getSize(); i++) {
			if (fireidA.getInt(ind.set(i))==fireid) {
				return i;
			}
		}
		return -1;

	}; 

	public void getDrainType(int drainagetype, int recid){   //recid starts from 0
		
		Index ind = drainagetypeA.getIndex();
		drainagetype = drainagetypeA.getInt(ind.set(recid));
		
	}; 

	public void getSoilTexture(DataGrid jgd, int recid){   //recid starts from 0
		Index ind1 = topsoilA.getIndex();
		jgd.topsoil = topsoilA.getInt(ind1.set(recid));

		Index ind2 = botsoilA.getIndex();
		jgd.botsoil = botsoilA.getInt(ind2.set(recid));
		
	}; 

	public void getGfire(DataGrid jgd, int recid){     //recid starts from 0

		Index ind1 = friA.getIndex();
		jgd.fri = friA.getInt(ind1.set(recid));
			
		Index ind2 = pfseasonA.getIndex();
		int[] ij = pfseasonA.getShape();
		for (int j = 0; j <ij[1]; j++) {
			jgd.pfseason[j] = pfseasonA.getDouble(ind2.set(recid,j));
		}

		Index ind3 = pfsizeA.getIndex();
		ij = pfsizeA.getShape();
		for (int j = 0; j < ij[1]; j++) {
			jgd.pfsize[j] = pfsizeA.getDouble(ind3.set(recid,j));
		}

	}; 

}
