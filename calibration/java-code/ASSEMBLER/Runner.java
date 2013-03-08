package ASSEMBLER;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;

import TEMJNI.Controller;
import TEMJNI.ModelData;
import TEMJNI.EnvData;
import TEMJNI.BgcData;
import TEMJNI.FirData;
import TEMJNI.Timer;

import GUI.Configurer;
import INPUT.CohortlistInputer;
import DATA.ConstTime;

public class Runner {

//		public int chtid = -1;
		public int error = -1;
		
    	//TEM domains (hiarchy)
    	RunRegion runreg = new RunRegion();
		RunGrid rungrd = new RunGrid();
    	public RunCohort runcht = new RunCohort();

    	//Inptuer  	
    	Controller configin = new Controller();   //c++ controller
    	
    	public Configurer jconfigin;   //java GUI configuration input (initialized in main())
    	CohortlistInputer chtlister = new CohortlistInputer();
        
    	//data classes
    	ModelData md = new ModelData();

    	EnvData  grded = new EnvData();   // all-grid level 'ed'
    	BgcData  grdbd = new BgcData();

    	EnvData  chted = new EnvData();   // all-cht level 'ed' (i.e. 'edall in 'cht')
    	BgcData  chtbd = new BgcData();
    	FirData  chtfd = new FirData();

    	//util
    	Timer timer = new Timer();
    	
	// modules
	public void initInput(String controlfile, String runmode){

		System.out.println("Starting initialization ...");
		System.out.println("control file: "+controlfile);
		System.out.println("TEM run mode: "+runmode);
		
		// configuration 
		if (runmode.compareToIgnoreCase("GUI")==0) {  //configuration by GUI input
			md.setRunmode(jconfigin.runmode);
 			
			md.setCasename(jconfigin.casename);
 		  	md.setConfigdir(jconfigin.configdir); 
 			md.setRunchtfile(jconfigin.runchtfile);
 			md.setOutputdir(jconfigin.outputdir); 
 		  	md.setReginputdir(jconfigin.reginputdir);
 		  	md.setGrdinputdir(jconfigin.grdinputdir);
 		  	md.setChtinputdir(jconfigin.chtinputdir);
 		  
 		  	md.setRunstages(jconfigin.runstages);
 		  	md.setInitmodes(jconfigin.initmodes);
 		  	md.setInitialfile(jconfigin.initialfile);

 		   	md.setChangeclimate(jconfigin.changeclimate);
 			md.setChangeco2(jconfigin.changeco2);
 			md.setUpdatelai(jconfigin.updtaelai);
 			md.setUseseverity(jconfigin.useseverity);

 			md.setOutstartyr(jconfigin.outstartyr);
 			
 			md.setOutSiteDay(jconfigin.useseverity);
 			md.setOutSiteMonth(jconfigin.useseverity);
 			md.setOutSiteYear(jconfigin.useseverity);
 			md.setOutRegn(jconfigin.useseverity);			
			
		} else {  //configuration by control file

			// Input and processing for reading configuration
			configin.setControlfile(controlfile);

			//	
			if (runmode.compareTo("siter")==0) {
 				md.setRunmode(1);
			} else if (runmode.compareTo("regner1")==0) {
 				md.setRunmode(2);                            //regional run - time-series
			} else if (runmode.compareTo("regner2")==0) {
 				md.setRunmode(3);                            //regional run - spatially (NOT yet configured!)
			} else {
 				System.out.println("TEM run mode: "+runmode+" must be ONE of:");
 				System.out.println("'siter', 'regner1', or, 'regner2'");
 				System.exit(-1);
			}
 		
			configin.ctrl4run(md);   //read in model configure info from "config/controlfile_site.txt"
 		 		
			if (md.getRunmode()!=1) md.setConsoledebug(false);
 		
		} // end of configuration of model running
 		
 		// checking the input configuration information
		md.checking4run();
		
		// timer initialization
		timer.setModeldata(md);

		//region-level input
 		runreg.rinputer.init(md, md.getReginputdir());			        //checking data file
 		
 		//grid-level input
 		rungrd.ginputer.init(md.getGrdinputdir());			        //checking data file

 		//cohort-level input
 		runcht.cinputer.init(md.getChtinputdir());                //checking data file
 		if (md.getRunmode()==2 || md.getRunmode()==3) {
 			String runchtlist = md.getRunchtfile();
 			chtlister.init(runchtlist);   // the running cohort list, if multple-cohort run mode on
 		} else if (md.getRunmode()==1) {
	 		System.out.println("CHTID and INITCHTID in 'cohortid.nc' MUST be 1 for 'siter' runmode!");
 	   		runcht.jcd.chtid = 1;
 		}

 		//initial conditions
 		if (md.getInitmode()==3){
 		 	if(md.getRuneq()){
 		 		System.out.println("cannot set initmode as restart for equlibrium run");
 		 		System.out.println("reset to 'lookup'");
 		 		md.setInitmode(1);
 		 	} else {
 		 		runcht.resinputer.init(md.getInitialfile());
 		 	}
 		} else if (md.getInitmode()==2) {
            // will add later
 		} else if (md.getInitmode()==1) {

 		}
 		 
	};

	//output setting-up
	public void initOutput() {

		String stage = "-"+md.getRunstages();

 		// 1)for general outputs
		if (md.getRunmode()==1) {   //very detailed output for ONE cohort ONLY

			md.setOutRegn(false);

	    	String dimfname ="";
	    	String envfname ="";
	    	String bgcfname ="";

			if (md.getOutSiteDay()){
				envfname = md.getOutputdir()+"cmtenv_dly"+stage+".nc";
//				runcht.getEnvdlyouter().init(envfname);				// set netcdf files for output
			}

			if (md.getOutSiteMonth()){
				dimfname = md.getOutputdir()+"cmtdim_mly"+stage+".nc";
				//runcht.dimmlyouter.init(dimfname);				// set netcdf files for output

				envfname = md.getOutputdir()+"cmtenv_mly"+stage+".nc";
				//runcht.envmlyouter.init(envfname);				// set netcdf files for output

				bgcfname = md.getOutputdir()+"cmtbgc_mly"+stage+".nc";
				//runcht.bgcmlyouter.init(bgcfname);				// set netcdf files for output
			}

			if (md.getOutSiteYear()){
				dimfname = md.getOutputdir()+"cmtdim_yly"+stage+".nc";
				//runcht.dimylyouter.init(dimfname);				// set netcdf files for output

				envfname = md.getOutputdir()+"cmtenv_yly"+stage+".nc";
				//runcht.envylyouter.init(envfname);				// set netcdf files for output

				bgcfname = md.getOutputdir()+"cmtbgc_yly"+stage+".nc";
				//runcht.bgcylyouter.init(bgcfname);				// set netcdf files for output
			}

	     } else if (md.getRunmode() == 2){
			 // output options (swithes)
			 md.setOutSiteYear(false);
			 md.setOutSiteDay(false);
			 md.setOutSiteMonth(false);

			 // varlist
			 String outlistfile = "config/outvarlist.txt";
			 try {
				 createOutvarList(outlistfile);
			 } catch (Exception ex){
				 //
			 }
			 // output years
			 int maxoutyrs = 0;
			 if (md.getRunsp()) {
				maxoutyrs += ConstTime.MAX_SP_YR;
			 }
			 if (md.getRuntr()) {
				maxoutyrs += ConstTime.MAX_TR_YR;
			 }
			 if (md.getRunsc()) {
				maxoutyrs += ConstTime.MAX_SC_YR;
			 }

			 //runcht.regnouter.init(md.outputdir, stage, maxoutyrs);				  //set netcdf files for output
			 //runcht.regnouter.setOutData(&runcht.regnod);

	     } else {
	    	 md.setOutRegn(false);
			 md.setOutSiteYear(false);
			 md.setOutSiteDay(false);
			 md.setOutSiteMonth(false);
	     }

 		// 2)for restart.nc outputs
		//runcht.resouter.init(md.outputdir, stage);       //define netcdf file for restart output

	};

	//set up data connection and data pointer initialization
	public void setupData(){

		// input data connection
		rungrd.grid.setRegionData(runreg.region.getRd());
		
 		runcht.cht.setModelData(md);
 		runcht.cht.setTime(timer);
 		runcht.cht.setInputData(runreg.region.getRd(), rungrd.grid.getGd());

 		// process data connection
 		runcht.cht.setProcessData(chted, chtbd, chtfd);  //

 		// initializing pointers data connection used in 'runcht'
 		runcht.initData();

 		//initializing pointers used in called modules in one 'cht'
 		runcht.cht.initSubmodules();

	};

	public int run(){
		try {
			//read-in region-level data (Yuan: this is the portal for multiple region run, if needed in the future)
			error = runreg.reinit(0);          //can be modified, if more than 1 record of data
			if (error!=0){
				System.out.println("problem in reinitialize regional-module in Runner::run ()");
				System.exit(-1);
			}
		
			//IDs for ONE single cohort		
			error = setupIDs();
			if (error!=0){
				System.out.println("problem in setupIDs for CHTID = "+runcht.jcd.chtid+" in Runner::run ()");
				System.exit(-1);
			}
			
			//getting the grided data for ONE single cohort
			error = rungrd.reinit(runcht.cht.getCd().getGrdid());
			if (error!=0){
				System.out.println("problem in reinitialize grid-module in Runner::run ()");
				System.exit(-1);
			}
				
			//getting the cohort data
			error = runcht.readData();

			error = runcht.reinit(runcht.jcd.chtid);

			if (error!=0) {
				System.out.println("Error for reinit cohort: "+ runcht.jcd.chtid +" - will exit! ");
				System.exit(-3);
			} else {
				System.out.println("cohort: " + runcht.jcd.chtid +" - running! ");
				runcht.run();
			}

			runcht.cohortcount++;
		
		} catch (Exception ex) {
	  		System.err.println("Error in Runner::run() " + ex);
	  		return -1;
		} 
		
		return 0;

	};

	// make IDs consistent through all data sets
	public int setupIDs(){
		try {
			// NOTE: 'chtid' must be assigned a value before
			runcht.cht.getCd().setChtid(runcht.jcd.chtid);
						
			int chtrec = runcht.cinputer.getChtDataids(runcht.jcd, runcht.jcd.chtid);
		  	
			if (chtrec<0) {
		  		return -4;
		  	} else {  //assign to c++ 'cd' holder
		  		
		  		runcht.cht.getCd().setChtid(runcht.jcd.chtid);
		  		runcht.cht.getCd().setInichtid(runcht.jcd.inichtid);
		  		runcht.cht.getCd().setGrdid(runcht.jcd.grdid);
		  		runcht.cht.getCd().setClmid(runcht.jcd.clmid);
		  		runcht.cht.getCd().setVegid(runcht.jcd.vegid);
		  		runcht.cht.getCd().setFireid(runcht.jcd.fireid);
		  	}
    
		} catch (Exception ex) {
	    	System.err.println("TEM cohort set IDs failed! - "+ex);		
		}

		return 0;
	};

	private void createOutvarList(String txtfile) throws IOException {

		String outvarfile = txtfile;
	    try {
	    	BufferedReader input =  new BufferedReader(new FileReader(outvarfile));
	    	try {
	        	File outlistF = new File(outvarfile);
	        	if(!outlistF.exists()){
	        		System.out.println("output variable list file: "+ outvarfile+" not exists! ");
	        		System.exit(-1);
	        	}

	        	String dummy = "";
	        	dummy=input.readLine();   //two lines of comments
	        	dummy=input.readLine();

	        	int[] ovarsoption = new int[78];
	        	int ivar = 0;
	        	while (true){
	        		if (!input.ready()) break;
	        		dummy = input.readLine();
	        		String[] dummypart = new String[2];
	        		dummypart = dummy.split("//");
	        		ovarsoption[ivar] = Integer.valueOf(dummypart[0]);
	        		ivar++;
	        	}
	    		runcht.regnod.setOutvarlist(ovarsoption);
	    		
	        	
	    	} catch (Exception e){
        		System.out.println("reading file: "+ outvarfile+" failed! ");
	    	} finally {
	    		input.close();
	    	}
	    
	    } catch (IOException ex){
	      ex.printStackTrace();
	    }		


	};

}

