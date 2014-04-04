package INPUT;

import java.io.File;
import java.io.IOException;

import ucar.ma2.Array;
import ucar.ma2.Index;
import ucar.nc2.NetcdfFile;
import ucar.nc2.Variable;

import TEMJNI.ModelData;

public class CohortInputer {
	public int act_chtno;
	public int act_initchtno;
	
	public int act_clmno;   //
	public int act_clmyr;
	
	public int act_vegno;
	public int act_vegset;
	
	public int act_fireno;
	public int act_fireset;

	//ids for a cohort, as in 'cohortid.nc' file
	Array chtidA;
	Array chtinitidA;
	Array chtgrididA;
	Array chtclmidA;
	Array chtvegidA;
	Array chtfireidA;

	// id in initial file ('sitein.nc', or 'restart.nc')
	Array initchtidA;
	
	// id and data in 'climate.nc'
	Array clmidA;
	Array clmyearA;
	Array tairA;
	Array precA;
	Array nirrA;
	Array vapoA;
	
	// id and data in 'vegetation.nc'
	Array vegidA;
	Array vegsetyrA;
	Array vegtypeA;
	Array vegfracA;
	
	// id and data in 'fire.nc'
	Array fireidA;
	Array fyearA;
	Array fseasonA;
	Array fsizeA;
	Array fseverityA;
	
	//one cohort-level data set will be done in cohort.java, 
	// but functions are defined here.
	
	public void init(ModelData md){
		  
	  	initChtidFile(md.getChtinputdir());
	  	if (!md.getRuneq()) initChtinitFile(md.getInitialfile());
	  	initClmFile(md.getChtinputdir());
	  	initVegFile(md.getChtinputdir());
		initFireFile(md.getChtinputdir());
	    
  	}; 
  	
	void initChtidFile(String dir){
		String chtidfname = dir +"cohortid.nc";
		NetcdfFile chtidncfile = null;
		File chtidfile = new File(chtidfname);
		if (chtidfile.exists()){
			try {
				chtidncfile = NetcdfFile.open(chtidfname);

				Variable chtidV = chtidncfile.findVariable("CHTID");
				this.chtidA = chtidV.read();
				
				this.act_chtno = this.chtidA.getShape()[0];

				Variable chtinitidV = chtidncfile.findVariable("INITCHTID");
				this.chtinitidA = chtinitidV.read();

				Variable chtgrididV = chtidncfile.findVariable("GRIDID");
				this.chtgrididA = chtgrididV.read();

				Variable chtclmidV = chtidncfile.findVariable("CLMID");
				this.chtclmidA = chtclmidV.read();

				Variable chtvegidV = chtidncfile.findVariable("VEGID");
				this.chtvegidA = chtvegidV.read();

				Variable chtfireidV = chtidncfile.findVariable("FIREID");
				this.chtfireidA = chtfireidV.read();

			} catch (IOException ioe) {
					System.out.println(ioe.getMessage());
			} finally {
					if (chtidncfile != null) {
						try {
							chtidncfile.close();
						} catch (IOException ioee) {
							System.out.println(ioee.getMessage());
						}
					}
			}
		} else {   //file not exist
			System.out.println("Input file: "+chtidfname+" NOT existed");
			System.exit(-1);
		}
 	 
	};
	
	void initChtinitFile(String initialfile){

		String chtinitfname = initialfile;

		NetcdfFile chtinitncfile = null;
		File chtinitfile = new File(chtinitfname);
		if (chtinitfile.exists()){
			try {
				chtinitncfile = NetcdfFile.open(chtinitfname);

				Variable initchtidV = chtinitncfile.findVariable("CHTID");
				this.initchtidA = initchtidV.read();
				
				this.act_initchtno = this.initchtidA.getShape()[0];


			} catch (IOException ioe) {
					System.out.println(ioe.getMessage());
			} finally {
					if (chtinitncfile != null) {
						try {
							chtinitncfile.close();
						} catch (IOException ioee) {
							System.out.println(ioee.getMessage());
						}
					}
			}
		} else {   //file not exist
			System.out.println("Input file: "+chtinitfname+" NOT existed");
			System.exit(-1);
		}

	}
  	
	void initClmFile(String dir){
		String clmfname = dir +"climate.nc";
		NetcdfFile clmncfile = null;
		File clmfile = new File(clmfname);
		if (clmfile.exists()){
			try {
				clmncfile = NetcdfFile.open(clmfname);

				Variable clmidV = clmncfile.findVariable("CLMID");
				this.clmidA = clmidV.read();
				
				this.act_clmno = this.clmidA.getShape()[0];

				Variable clmyearV = clmncfile.findVariable("YEAR");
				this.clmyearA = clmyearV.read();
				
				this.act_clmyr = this.clmyearA.getShape()[0];

				Variable tairV = clmncfile.findVariable("TAIR");
				this.tairA = tairV.read();

				Variable precV = clmncfile.findVariable("PREC");
				this.precA = precV.read();

				Variable nirrV = clmncfile.findVariable("NIRR");
				this.nirrA = nirrV.read();

				Variable vapoV = clmncfile.findVariable("VAPO");
				this.vapoA = vapoV.read();

			} catch (IOException ioe) {
					System.out.println(ioe.getMessage());
			} finally {
					if (clmncfile != null) {
						try {
							clmncfile.close();
						} catch (IOException ioee) {
							System.out.println(ioee.getMessage());
						}
					}
			}
		} else {   //file not exist
			System.out.println("Input file: "+clmfname+" NOT existed");
			System.exit(-1);
		}
 	 
	};
  	
	void initVegFile(String dir){
		String filename = dir +"vegetation.nc";

		NetcdfFile ncfile = null;
		File vegfile = new File(filename);
		if (vegfile.exists()){
			try {
				ncfile = NetcdfFile.open(filename);
				
				Variable vegidV = ncfile.findVariable("VEGID");
				this.vegidA = vegidV.read();
				this.act_vegno = this.vegidA.getShape()[0];
				
				Variable vegsetyrV = ncfile.findVariable("VEGSETYR");
				this.vegsetyrA = vegsetyrV.read();				
				this.act_vegset = this.vegsetyrA.getShape()[1];

				Variable vegtypeV = ncfile.findVariable("VEGTYPE");
				this.vegtypeA = vegtypeV.read();

				Variable vegfracV = ncfile.findVariable("VEGFRAC");
				this.vegfracA = vegfracV.read();

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

	void initFireFile(String dir){
		String filename = dir +"fire.nc";
		NetcdfFile ncfile = null;
		File spchtidfile = new File(filename);
		if (spchtidfile.exists()){
			try {
				ncfile = NetcdfFile.open(filename);
				Variable fireidV = ncfile.findVariable("FIREID");
				this.fireidA = fireidV.read();
				this.act_fireno = this.fireidA.getShape()[0];
				
				Variable fyearV = ncfile.findVariable("YEAR");
				this.fyearA = fyearV.read();				
				this.act_fireset = this.fyearA.getShape()[1];

				Variable fseasonV = ncfile.findVariable("SEASON");
				this.fseasonA = fseasonV.read();

				Variable fsizeV = ncfile.findVariable("SIZE");
				this.fsizeA = fsizeV.read();

				Variable fseverityV = ncfile.findVariable("SEVERITY");
				this.fseverityA = fseverityV.read();

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
			System.exit(-1);
		}
 	 
	};

	// the following is for a input file containing data ids for each cohort
 	//recno - record number (starting from 0), NOT chtid
	public int getChtDataids(int chtdataids[], int recno){
		
		try {
			Index ind1 = this.chtidA.getIndex();
			chtdataids[0] = this.chtidA.getInt(ind1.set(recno));
		
			Index ind2 = this.chtinitidA.getIndex();
			chtdataids[1] = this.chtinitidA.getInt(ind2.set(recno));

			Index ind3 = this.chtgrididA.getIndex();
			chtdataids[2] = this.chtgrididA.getInt(ind3.set(recno));

			Index ind4 = this.chtclmidA.getIndex();
			chtdataids[3] = this.chtclmidA.getInt(ind4.set(recno));

			Index ind5 = this.chtvegidA.getIndex();
			chtdataids[4] = this.chtvegidA.getInt(ind5.set(recno));

			Index ind6 = this.chtfireidA.getIndex();
			chtdataids[5] = this.chtfireidA.getInt(ind6.set(recno));
		
			return 0;
		
		} catch (Exception ex) {

			System.err.println("TEM input 'cohortid.nc' failed (ids reading)! - "+ex);		
		
			return -1;
		}
		
	};

	// the following are for data Ids from input data files
	public int getInitchtId(int recno){
		try {
			Index ind = this.initchtidA.getIndex();
			return this.initchtidA.getInt(ind.set(recno));
		
		} catch (Exception ex) {

			System.err.println("TEM input initial file ('restart.nc' or 'sitein.nc' failed (ids reading)! - "+ex);		
	
			return -1;
		}
	};

	public int getClmId(int recno){
	
		try {
			Index ind = this.clmidA.getIndex();
		
			return this.clmidA.getInt(ind.set(recno));
		
		} catch (Exception ex) {

			System.err.println("TEM input 'climate.nc' failed (ids reading)! - "+ex);		

			return -1;
		}
	};

	public int getVegId(int recno){
		try {
			Index ind = this.vegidA.getIndex();
			return this.vegidA.getInt(ind.set(recno));

		} catch (Exception ex) {

			System.err.println("TEM input 'vegetiation.nc' failed (ids reading)! - "+ex);		

			return -1;
		}
	};

	public int getFireId(int recno){
	
		try {
			Index ind = this.fireidA.getIndex();
			return this.fireidA.getInt(ind.set(recno));
	
		} catch (Exception ex) {

			System.err.println("TEM input 'fire.nc' failed (ids reading)! - "+ex);		

			return -1;
		}
	};

	//data reading for one record
	//Note: initial file has two types: 'sitein.nc', 'restart.nc', which are 
	//very different, so NOT read here.
	public int getClimate(float tair[], float prec[], float nirr[], float vapo[], 
			int act_atm_drv_yr, int recid){     //recid starts from 0
		
		try {
			Index ind1 = this.tairA.getIndex();
			for (int iy = 0; iy < act_atm_drv_yr; iy++) {
				for (int im = 0; im < 12; im++) {
					int iyim =iy*12+im;
					tair[iyim] = this.tairA.getFloat(ind1.set(recid,iy,im));
				}
			}

			Index ind2 = this.nirrA.getIndex();
			for (int iy = 0; iy < act_atm_drv_yr; iy++) {
				for (int im = 0; im < 12; im++){
					int iyim =iy*12+im;
					nirr[iyim] = this.nirrA.getFloat(ind2.set(recid,iy,im));
				}
			}

			Index ind3 = this.precA.getIndex();
			for (int iy = 0; iy < act_atm_drv_yr; iy++) {
				for (int im = 0; im < 12; im++) {
					int iyim =iy*12+im;
					prec[iyim] = this.precA.getFloat(ind3.set(recid,iy,im));
				}
			}

			Index ind4 = this.vapoA.getIndex();
			for (int iy = 0; iy < act_atm_drv_yr; iy++) {
				for (int im = 0; im < 12; im++) {
					int iyim =iy*12+im;
					vapo[iyim] = this.vapoA.getFloat(ind4.set(recid,iy,im));
				}
			}
			
			return 0;
		
		
		} catch (Exception ex) {

			System.err.println("TEM input 'climate.nc' failed (data reading)! - "+ex);		

			return -1;
		}

	}; 

	public int getVegetation(int vsetyr[], int vtype[], double vfrac[], int recid){
		
		try {
			Index vsetyri = this.vegsetyrA.getIndex();
			Index vtypei  = this.vegtypeA.getIndex();
			Index vfraci  = this.vegfracA.getIndex();
			for (int i=0; i<this.act_vegset; i++){
				vsetyr[i] = this.vegsetyrA.getInt(vsetyri.set(recid, i));
				vtype[i] = this.vegtypeA.getInt(vtypei.set(recid, i));
				vfrac[i] = this.vegfracA.getDouble(vfraci.set(recid, i));
			}
		
			return 0;
		
		
		} catch (Exception ex) {

			System.err.println("TEM input 'climate.nc' failed (data reading)! - "+ex);		

			return -1;
		}

	};

	public int getFire(int fyear[], int fseason[], int fsize[], int recid){
		
		try {
			Index ind1 = this.fyearA.getIndex();
			Index ind2 = this.fseasonA.getIndex();
			Index ind3 = this.fsizeA.getIndex();

			for (int i=0; i<this.act_fireset; i++) {
				fyear[i]   = this.fyearA.getInt(ind1.set(recid, i));
				fseason[i] = this.fseasonA.getInt(ind2.set(recid, i));
				fsize[i]   = this.fsizeA.getInt(ind3.set(recid, i));
			}
		
			return 0;
		
		
		} catch (Exception ex) {

			System.err.println("TEM input 'climate.nc' failed (data reading)! - "+ex);		

			return -1;
		}

	};
	
	public int getFireSeverity(int fseverity[], int recid){

		try {
			Index ind = this.fseverityA.getIndex();
			for (int i=0; i<this.act_fireset; i++) {
				fseverity[i] = this.fseverityA.getInt(ind.set(recid, i));
			}
		
			return 0;
		
		
		} catch (Exception ex) {

			System.err.println("TEM input 'climate.nc' failed (data reading)! - "+ex);		

			return -1;
		}

		
	};

}
