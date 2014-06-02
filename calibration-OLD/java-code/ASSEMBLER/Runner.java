package ASSEMBLER;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

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

		public int chtid = -1;   /* currently-running 'cohort' id */
		public int error = 0;   /* error indx */
		
    	public List<Integer> runchtlist = new ArrayList<Integer>();  //a vector listing all cohort id
    	
    	public List<Float> runchtlats  = new ArrayList<Float>();  //a vector of latitudes for all cohorts in order of 'runchtlist'
    	public List<Float> runchtlons  = new ArrayList<Float>();  //a vector of longitudes for all cohorts in order of 'runchtlist'

    	/* all data record no. lists FOR all cohorts in 'runchtlist', IN EXACTLY SAME ORDER, for all !
    	 * the 'record' no. (starting from 0) is the order in the netcdf files
    	 * for all 'chort (cell)' in the 'runchtlist',
    	 * so, the length of all these lists are same as that of 'runchtlist'
    	 * will save time to search those real data ids if do the ordering in the first place
    	 * */

    	/* from grided-data (geo-referenced only, or grid-level)*/
    	public List<Integer> reclistgrid  = new ArrayList<Integer>();
    	public List<Integer> reclistdrain = new ArrayList<Integer>();
    	public List<Integer> reclistsoil  = new ArrayList<Integer>();
    	public List<Integer> reclistgfire = new ArrayList<Integer>();

    	/* from grided-/non-grided and time-series data (cohort-level)*/
    	public List<Integer> reclistinit  = new ArrayList<Integer>();
    	public List<Integer> reclistclm   = new ArrayList<Integer>();
    	public List<Integer> reclistveg   = new ArrayList<Integer>();
    	public List<Integer> reclistfire  = new ArrayList<Integer>();
		
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
 			md.setUpdatelai(jconfigin.updatelai);
 			md.setUseseverity(jconfigin.useseverity);

 			md.setOutstartyr(jconfigin.outstartyr);
 			
 			md.setOutSiteDay(jconfigin.outsiteday);
 			md.setOutSiteMonth(jconfigin.outsitemonth);
 			md.setOutSiteYear(jconfigin.outsiteyear);
 			md.setOutRegn(jconfigin.outregn);			
			
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
 		runreg.rinputer.init(md, md.getReginputdir());			     //checking data file
 		
 		//grid-level input
 		rungrd.ginputer.init(md.getGrdinputdir());			        //checking data file and their dimensions
 		md.setAct_gridno(rungrd.ginputer.act_gridno);
 		md.setAct_soilno(rungrd.ginputer.act_soilno);
 		md.setAct_drainno(rungrd.ginputer.act_drainno);
 		md.setAct_gfireno(rungrd.ginputer.act_gfireno);

 		//cohort-level input
 		runcht.cinputer.init(md);                //checking data file and their dimensions
 		md.setAct_chtno(runcht.cinputer.act_chtno);
 		md.setAct_initchtno(runcht.cinputer.act_initchtno);
 		md.setAct_clmno(runcht.cinputer.act_clmno);
 		md.setAct_clmyr(runcht.cinputer.act_clmyr);
 		md.setAct_vegno(runcht.cinputer.act_vegno);
 		md.setAct_vegset(runcht.cinputer.act_vegset);
 		md.setAct_fireno(runcht.cinputer.act_fireno);
 		md.setAct_fireset(runcht.cinputer.act_fireset);
 		
 		runchtlist.clear();
 		if (md.getRunmode()==2 || md.getRunmode()==3) {
 			String runchtlist = md.getRunchtfile();
 			chtlister.init(runchtlist);   // the running cohort list, if multple-cohort run mode on
 		} else if (md.getRunmode()==1) {
	 		System.out.println("CHTID and INITCHTID is "+chtid+" for 'siter' runmode! ");
	 		System.out.println("Be sure they exist and are consistent in 'cohortid.nc'! ");
 	   		runchtlist.add(chtid);
 		}

 		//initial conditions
 		if (md.getInitmode()==3){
 		 	if(md.getRuneq()){
 		 		System.out.println("cannot set initmode as restart for equlibrium run ");
 		 		System.out.println("reset to 'lookup' \n");
 		 		md.setInitmode(1);
 		 	} else {
 		 		runcht.resinputer.init(md.getInitialfile());
 		 	}
 		} else if (md.getInitmode()==2) {
            // will add later
 		} else if (md.getInitmode()==1) {
		 	System.out.println("initial conditions from default for each 'cmttype' \n");
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

	     } else if ((md.getRunmode()==2 || md.getRunmode()==3) && !md.getRuneq()){
			 // output options (swithes)
			 md.setOutSiteYear(false);
			 md.setOutSiteDay(false);
			 md.setOutSiteMonth(false);


	     } else {
	    	 md.setOutRegn(false);
			 md.setOutSiteYear(false);
			 md.setOutSiteDay(false);
			 md.setOutSiteMonth(false);
	     }

		// 2) summarized output by a list of variables 
		if (md.getOutRegn()) {
		 
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
 		runcht.init();

 		//initializing pointers used in called modules in one 'cht'
 		runcht.cht.initSubmodules();

	};

	// make IDs consistent through all data sets
	public int setupIDs(){
		
		try {
			
			// all grid data ids
			error = rungrd.allgridids(md.getAct_gridno(), 
			                          md.getAct_drainno(), 
			                          md.getAct_soilno(),
					                  md.getAct_gfireno());
			if (error != 0) {
		  		System.out.println("problem in reading all grid-level data IDs in Runner::setupIDs \n");
		  		System.exit(-1);
			}

			// all cohort data ids
			error = runcht.allchtids();
			if (error != 0) {
				System.out.println("problem in reading all cohort-level data IDs in Runner::setupIDs \n");
		  		System.exit(-1);
			}

			// 1) assign grid-level data IDs (in 'grid.nc') for ALL 'chtid' in 'cohortid.nc': related key - 'GRIDID'
			//    note: one 'chtid' only has one set of grid-level data IDs, while not in reverse
			int icht=-1;
			int igrd=-1;					
			for (icht=0; icht<runcht.chtids.size(); icht++){
				int gridid = runcht.chtgridids.get(icht);

				int it = rungrd.grdids.indexOf(gridid);
				if (it>=0) {
					igrd = rungrd.grdids.get(it);
					runcht.chtdrainids.add(rungrd.drainids.get(igrd));
					runcht.chtsoilids.add(rungrd.soilids.get(igrd));
					runcht.chtgfireids.add(rungrd.gfireids.get(igrd));

				} else {
					runcht.chtdrainids.add(-1);
					runcht.chtsoilids.add(-1);
					runcht.chtgfireids.add(-1);
					
				}
			}

			// 2) output the record no. for all data IDs, in the 'runchtlist' so that read-data doesn't need to
			// search each IDs in the .nc files during computation, which may cost a lot of computation time
			int jcht  = -1;
			int jt    = -1;
			float latlon[] = new float []{-9999.0f, -9999.0f};

			int jj;
			for (jj=0; jj<runchtlist.size(); jj++){
				chtid = runchtlist.get(jj);

				jcht = runcht.chtids.indexOf(chtid);

				// grid record no. (in 'grid.nc') for 'chtid' (needed for lat/lon)
				jt    = rungrd.grdids.indexOf(runcht.chtgridids.get(jcht));
				if (jt>=0) {
					rungrd.ginputer.getLatlon(latlon, jt);

					reclistgrid.add(jt);
					runchtlats.add(latlon[0]);
					runchtlons.add(latlon[1]);
				} else {
					reclistgrid.add(-1);
					runchtlats.add(-9999.0f);
					runchtlons.add(-9999.0f);				
				}

				// drainage-type record no. (in 'drainage.nc') for 'chtid'
				jt    = rungrd.drainids.indexOf(runcht.chtdrainids.get(jcht));
				if (jt>=0) {
					reclistdrain.add(jt);
				} else {
					reclistdrain.add(-1);					
				}
				
				// soil-texture record no. (in 'soiltexture.nc') for 'chtid'
				jt    = rungrd.soilids.indexOf(runcht.chtsoilids.get(jcht));
				if (jt>=0) {
					reclistsoil.add(jt);
				} else {
					reclistsoil.add(-1);
				}
				// grid-fire-statistics ('gfire') record no. (in 'firestatistics.nc') for 'chtid'
				jt    = rungrd.gfireids.indexOf(runcht.chtgfireids.get(jcht));
				if (jt>=0) {
					reclistgfire.add(jt);
				} else {
					reclistgfire.add(-1);
				}

				// initial data record no. (in 'restart.nc' or 'sitein.nc', or '-1') for 'chtid'
				if (!md.getRuneq()) {
					jt    = runcht.initids.indexOf(runcht.chtinitids.get(jcht));
					if (jt>=0) {
						reclistinit.add(jt);
					} else {
						reclistinit.add(-1);
					}
				} else {
					reclistinit.add(-1);
				}
				
				// climate data record no. (in 'climate.nc') for 'chtid'
				jt  = runcht.clmids.indexOf(runcht.chtclmids.get(jcht));
				if (jt>=0) {
					reclistclm.add(jt);
				} else {
					reclistclm.add(-1);
				}
				
				// vegetation community data record no. (in 'vegetation.nc') for 'chtid'
				jt    = runcht.vegids.indexOf(runcht.chtvegids.get(jcht));
				if (jt>=0){
					reclistveg.add(jt);
				} else {
					reclistveg.add(-1);
				}
				
				// fire data record no. (in 'fire.nc') for 'chtid'
				jt    = runcht.fireids.indexOf(runcht.chtfireids.get(jcht));
				if (jt>=0){
					reclistfire.add(jt);
				} else {
					reclistfire.add(-1);
				}
								
			}
    
		} catch (Exception ex) {
	    	System.err.println("TEM cohort set IDs failed! - "+ex);		
		}

		return 0;
	};

	public int run_siter(){
		try {
			//read-in region-level data (Yuan: this is the portal for multiple region run, if needed in the future)
			error = runreg.reinit(0);          //can be modified, if more than 1 record of data
			if (error!=0){
				System.out.println("problem in reinitialize regional-module in Runner::run ()");
				System.exit(-1);
			}
		
			runcht.cht.getCd().setChtid(chtid);
			
			// assgning the record no. for all needed data IDs to run 'chtid'
			// for 'siter', all record no. are in the first position of the lists
			// because, 'chtid' is the only one in 'runchtlist', which are synchorized with all the lists.
			rungrd.gridrecno  = reclistgrid.get(0);
			rungrd.drainrecno = reclistdrain.get(0);
			rungrd.soilrecno  = reclistsoil.get(0);
			rungrd.gfirerecno = reclistgfire.get(0);

			runcht.initrecno  = reclistinit.get(0);
			runcht.clmrecno   = reclistclm.get(0);
			runcht.vegrecno   = reclistveg.get(0);
			runcht.firerecno  = reclistfire.get(0);

			//getting the grided data and checking data for current cohort
			error = rungrd.readData();
			if (error!=0){
				System.out.println("problem in reading grided data in Runner::run_siter \n");
				System.exit(-1);
			}

			//getting the cohort data for current cohort
			error = runcht.readData(true);
			if (error!=0){
				System.out.println("problem in reading grided data in Runner::run_siter \n");
				System.exit(-1);
			}

			error = runcht.reinit();
			if (error!=0){
				System.out.println("problem in reading grided data in Runner::run_siter \n");
				System.exit(-1);
			}

			System.out.println("cohort: "+ chtid+ " - running! \n");
			runcht.run_cohortly();
		
		} catch (Exception ex) {
	  		System.err.println("Error in Runner::run_siter() " + ex);
	  		return -1;
		} 
		
		return 0;

	};
	
	public int run_regner(){
		try {
			//read-in region-level data (Yuan: this is the portal for multiple region run, if needed in the future)
			error = runreg.reinit(0);          //can be modified, if more than 1 record of data
			if (error!=0){
				System.out.println("problem in reinitialize regional-module in Runner::run ()");
				System.exit(-1);
			}
		
			//loop through cohort in 'runchtlist'
			int jj ;
			for (jj=0; jj<runchtlist.size(); jj++){
				// may need to clear up data containers for new cohort

		 		runcht.cht.setModelData(md);
		 		runcht.cht.setTime(timer);
		 		runcht.cht.setInputData(runreg.region.getRd(), rungrd.grid.getGd());
		 		runcht.cht.setProcessData(chted, chtbd, chtfd);  //

		 		chtid = runchtlist.get(jj);
				runcht.cht.getCd().setChtid(chtid);
			
				// assgning the record no. for all needed data IDs to run 'chtid'
				// for 'siter', all record no. are in the first position of the lists
				rungrd.gridrecno  = reclistgrid.get(jj);
				rungrd.drainrecno = reclistdrain.get(jj);
				rungrd.soilrecno  = reclistsoil.get(jj);
				rungrd.gfirerecno = reclistgfire.get(jj);

				runcht.initrecno  = reclistinit.get(jj);
				runcht.clmrecno   = reclistclm.get(jj);
				runcht.vegrecno   = reclistveg.get(jj);
				runcht.firerecno  = reclistfire.get(jj);

				//getting the grided data and checking data for current cohort
				error = rungrd.readData();
				if (error!=0){
					System.out.println("problem in reading grided data in Runner::run_siter \n");
					System.exit(-1);
				}

				//getting the cohort data for current cohort
				error = runcht.readData(true);
				if (error!=0){
					System.out.println("problem in reading grided data in Runner::run_regner \n");
					System.exit(-1);
				}

				error = runcht.reinit();
				if (error!=0){
					System.out.println("problem in reading grided data in Runner::run_regner \n");
					System.exit(-1);
				}

				System.out.println("cohort: "+ chtid+ " - running! \n");
				runcht.run_cohortly();
				
				runcht.cohortcount++;
			
			} // end of 'runchtlist' loop

		} catch (Exception ex) {
	  		System.err.println("Error in Runner::run_regner() " + ex);
	  		return -1;
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

