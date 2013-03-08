package INPUT;

import java.io.File;
import java.io.IOException;

import ucar.ma2.Array;
import ucar.ma2.Index;
import ucar.nc2.NetcdfFile;
import ucar.nc2.Variable;

import DATA.DataCohort;

public class CohortInputer {
	public int act_chtno;
	
	public int act_clmidno;   //
	public int act_clmyr;
	
	public int act_vegidno;
	public int act_vegset;
	
	public int act_fireidno;
	public int act_fireset;

	//ids for a cohort
	Array chtidA;
	Array initchtidA;

	Array chtgrididA;
	Array chtclmidA;
	Array chtvegidA;
	Array chtfireidA;
	
	Array clmidA;
	Array clmyearA;
	Array tairA;
	Array precA;
	Array nirrA;
	Array vapoA;
	
	Array vegidA;
	Array vegsetyrA;
	Array vegtypeA;
	Array vegfracA;
	
	Array fireidA;
	Array fyearA;
	Array fseasonA;
	Array fsizeA;
	Array fseverityA;
	
	//one cohort-level data set will be done in cohort.java, 
	// but functions are defined here.
	
	public void init(String chtinputdir){
		  
	  	initChtidFile(chtinputdir);
	  	initClmFile(chtinputdir);
	  	initVegFile(chtinputdir);
		initFireFile(chtinputdir);
	    
  	}; 
  	
	public void initChtidFile(String dir){
		String chtidfname = dir +"cohortid.nc";
		NetcdfFile chtidncfile = null;
		File chtidfile = new File(chtidfname);
		if (chtidfile.exists()){
			try {
				chtidncfile = NetcdfFile.open(chtidfname);

				Variable chtidV = chtidncfile.findVariable("CHTID");
				chtidA = chtidV.read();
				
				act_chtno = chtidA.getShape()[0];

				Variable initchtidV = chtidncfile.findVariable("INITCHTID");
				initchtidA = initchtidV.read();

				Variable chtgrididV = chtidncfile.findVariable("GRIDID");
				chtgrididA = chtgrididV.read();

				Variable chtclmidV = chtidncfile.findVariable("CLMID");
				chtclmidA = chtclmidV.read();

				Variable chtvegidV = chtidncfile.findVariable("VEGID");
				chtvegidA = chtvegidV.read();

				Variable chtfireidV = chtidncfile.findVariable("FIREID");
				chtfireidA = chtfireidV.read();

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
  	
	public void initClmFile(String dir){
		String clmfname = dir +"climate.nc";
		NetcdfFile clmncfile = null;
		File clmfile = new File(clmfname);
		if (clmfile.exists()){
			try {
				clmncfile = NetcdfFile.open(clmfname);

				Variable clmidV = clmncfile.findVariable("CLMID");
				clmidA = clmidV.read();
				
				act_clmidno = clmidA.getShape()[0];

				Variable clmyearV = clmncfile.findVariable("YEAR");
				clmyearA = clmyearV.read();
				
				act_clmyr = clmyearA.getShape()[0];

				Variable tairV = clmncfile.findVariable("TAIR");
				tairA = tairV.read();

				Variable precV = clmncfile.findVariable("PREC");
				precA = precV.read();

				Variable nirrV = clmncfile.findVariable("NIRR");
				nirrA = nirrV.read();

				Variable vapoV = clmncfile.findVariable("VAPO");
				vapoA = vapoV.read();

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
  	
	public void initVegFile(String dir){
		String filename = dir +"vegetation.nc";

		NetcdfFile ncfile = null;
		File vegfile = new File(filename);
		if (vegfile.exists()){
			try {
				ncfile = NetcdfFile.open(filename);
				
				Variable vegidV = ncfile.findVariable("VEGID");
				vegidA = vegidV.read();
				act_vegidno = vegidA.getShape()[0];
				
				Variable vegsetyrV = ncfile.findVariable("VEGSETYR");
				vegsetyrA = vegsetyrV.read();				
				act_vegset = vegsetyrA.getShape()[1];

				Variable vegtypeV = ncfile.findVariable("VEGTYPE");
				vegtypeA = vegtypeV.read();

				Variable vegfracV = ncfile.findVariable("VEGFRAC");
				vegfracA = vegfracV.read();

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

	public void initFireFile(String dir){
		String filename = dir +"fire.nc";
		NetcdfFile ncfile = null;
		File spchtidfile = new File(filename);
		if (spchtidfile.exists()){
			try {
				ncfile = NetcdfFile.open(filename);
				Variable fireidV = ncfile.findVariable("FIREID");
				fireidA = fireidV.read();
				act_fireidno = fireidA.getShape()[0];
				
				Variable fyearV = ncfile.findVariable("YEAR");
				fyearA = fyearV.read();				
				act_fireset = fyearA.getShape()[1];

				Variable fseasonV = ncfile.findVariable("SEASON");
				fseasonA = fseasonV.read();

				Variable fsizeV = ncfile.findVariable("SIZE");
				fsizeA = fsizeV.read();

				Variable fseverityV = ncfile.findVariable("SEVERITY");
				fseverityA = fseverityV.read();

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

 	//cid - record id (starting from 0), NOT chtid
	public int getChtDataids(DataCohort jcd, int chtid){
		Index ind = chtidA.getIndex();
		for (int i=0; i<chtidA.getSize(); i++) {
			if (chtidA.getInt(ind.set(i))==chtid) {
				Index ind1 = initchtidA.getIndex();
				jcd.inichtid = initchtidA.getInt(ind1.set(i));

				Index ind2 = chtgrididA.getIndex();
				jcd.grdid = chtgrididA.getInt(ind2.set(i));

				Index ind3 = chtclmidA.getIndex();
				jcd.clmid = chtclmidA.getInt(ind3.set(i));

				Index ind4 = chtvegidA.getIndex();
				jcd.vegid = chtvegidA.getInt(ind4.set(i));

				Index ind5 = chtfireidA.getIndex();
				jcd.fireid = chtfireidA.getInt(ind5.set(i));

				return i;
				
			}
		}
		
		return -1;
		
	};

	public int getClmRec(int chtid){
		Index ind = clmidA.getIndex();
		for (int i=0; i<clmidA.getSize(); i++) {
			if (clmidA.getInt(ind.set(i))==chtid) return i;
		}
		return -1;
	};

	public int getVegRec(int vegid){
		Index ind = vegidA.getIndex();
		for (int i=0; i<vegidA.getSize(); i++) {
			if (vegidA.getInt(ind.set(i))==vegid) return i;
		}
		return -1;
	};

	public int getFireRec(int fireid){
		Index ind = fireidA.getIndex();
		for (int i=0; i<fireidA.getSize(); i++) {
			if (fireidA.getInt(ind.set(i))==fireid) return i;
		}
		return -1;
	};

	public void getClimate(float tair[], float prec[], float nirr[], float vapo[], 
			int act_atm_drv_yr, int recid){     //recid starts from 0
		
		Index ind1 = tairA.getIndex();
		for (int iy = 0; iy < act_atm_drv_yr; iy++) {
			for (int im = 0; im < 12; im++) {
				int iyim =iy*12+im;
				tair[iyim] = tairA.getFloat(ind1.set(recid,iy,im));
			}
		}

		Index ind2 = nirrA.getIndex();
		for (int iy = 0; iy < act_atm_drv_yr; iy++) {
			for (int im = 0; im < 12; im++){
				int iyim =iy*12+im;
				nirr[iyim] = nirrA.getFloat(ind2.set(recid,iy,im));
			}
		}

		Index ind3 = precA.getIndex();
		for (int iy = 0; iy < act_atm_drv_yr; iy++) {
			for (int im = 0; im < 12; im++) {
				int iyim =iy*12+im;
				prec[iyim] = precA.getFloat(ind3.set(recid,iy,im));
			}
		}

		Index ind4 = vapoA.getIndex();
		for (int iy = 0; iy < act_atm_drv_yr; iy++) {
			for (int im = 0; im < 12; im++) {
				int iyim =iy*12+im;
				vapo[iyim] = vapoA.getFloat(ind4.set(recid,iy,im));
			}
		}

	}; 

	public void getVegetation(int vsetyr[], int vtype[], double vfrac[], int recid){
		Index vsetyri = vegsetyrA.getIndex();
		Index vtypei  = vegtypeA.getIndex();
		Index vfraci  = vegfracA.getIndex();
		for (int i=0; i<act_vegset; i++){
			vsetyr[i] = vegsetyrA.getInt(vsetyri.set(recid, i));
			vtype[i] = vegtypeA.getInt(vtypei.set(recid, i));
			vfrac[i] = vegfracA.getDouble(vfraci.set(recid, i));
		}
	};

	public void getFire(int fyear[], int fseason[], int fsize[], int recid){
				
		Index ind1 = fyearA.getIndex();
		Index ind2 = fseasonA.getIndex();
		Index ind3 = fsizeA.getIndex();

		for (int i=0; i<act_fireset; i++) {
			fyear[i]   = fyearA.getInt(ind1.set(recid, i));
			fseason[i] = fseasonA.getInt(ind2.set(recid, i));
			fsize[i]   = fsizeA.getInt(ind3.set(recid, i));
		}
	}
	
	public void getFireSeverity(int fseverity[], int recid){

		Index ind = fseverityA.getIndex();
		for (int i=0; i<act_fireset; i++) {
			fseverity[i] = fseverityA.getInt(ind.set(recid, i));
		}
		
	};

}
