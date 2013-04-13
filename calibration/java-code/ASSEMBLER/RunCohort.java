package ASSEMBLER;
/*
 * RunCohort.java
 *
 * Cohort initialization, run, and output
 * 		Note: the output modules are put here, so can be flexible for outputs
 *
*/
import java.util.ArrayList;
import java.util.List;

import TEMJNI.Cohort;
import TEMJNI.OutDataRegn;
import TEMJNI.RestartData;

import DATA.ConstCohort;
import DATA.ConstLayer;
import DATA.DataCohort;
import DATA.DataRestart;
import DATA.ConstTime;

import INPUT.CohortInputer;
import INPUT.RestartInputer;

public class RunCohort {

	 public Cohort cht = new Cohort();
 		
 	 public DataCohort jcd = new DataCohort();
 	 public DataRestart jresid = new DataRestart();
   
 	 // Output data (extracted from model's data structure)
 	 public OutDataRegn regnod = new OutDataRegn();
 	 public RestartData resod = new RestartData();

 	 //I/O operators
 	 public CohortInputer cinputer = new CohortInputer();
 	 public RestartInputer resinputer = new RestartInputer();

/*    	public ChtOutputer dimmlyouter;
    	public ChtOutputer dimylyouter;

    	public EnvOutputer envdlyouter;
    	public EnvOutputer envmlyouter;
    	public EnvOutputer envylyouter;
 		
    	public BgcOutputer bgcmlyouter;
    	public BgcOutputer bgcylyouter;

    	public RegnOutputer regnouter;
    	public RestartOutputer resouter;
*/ 	  		 	 

 	/* all cohort data id lists
 	 * ids are labeling the datasets, which exist in .nc files
  	 * and, the order (index) in these lists are actually record no. in the .nc files
  	 */
 	 public List<Integer> chtids     = new ArrayList<Integer>();   // 'cohortid.nc'
 	 public List<Integer> chtinitids = new ArrayList<Integer>(); 
 	 public List<Integer> chtgridids = new ArrayList<Integer>(); 
 	 public List<Integer> chtclmids  = new ArrayList<Integer>(); 
 	 public List<Integer> chtvegids  = new ArrayList<Integer>(); 
 	 public List<Integer> chtfireids = new ArrayList<Integer>(); 

 	 public List<Integer> chtdrainids = new ArrayList<Integer>(); // from 'grid.nc' to 'cohortid.nc' via 'GRIDID'
 	 public List<Integer> chtsoilids  = new ArrayList<Integer>(); 
 	 public List<Integer> chtgfireids = new ArrayList<Integer>(); 

 	 public List<Integer> initids = new ArrayList<Integer>();   // from 'restart.nc' or 'sitein.nc'
 	 public List<Integer> clmids  = new ArrayList<Integer>();   // from 'climate.nc'
 	 public List<Integer> vegids  = new ArrayList<Integer>();   // from 'vegetation.nc'
 	 public List<Integer> fireids = new ArrayList<Integer>();   // from 'fire.nc'

	/* the following is FOR one cohort only (current cohort)
	 *
	 */
 	 public int cohortcount=0;
 	 public int initrecno  =-9999;
 	 public int clmrecno   =-9999;
 	 public int vegrecno   =-9999;
 	 public int firerecno  =-9999;
	
 	 public int usedatmyr  =-9999;
	 public int yrstart    =-9999;
	 public int yrend      =-9999;
	 
	 int dstepcnt=0;
	 int mstepcnt=0;
	 int ystepcnt=0;

	//reading cohort-level all data ids
	 public int allchtids(){
	 	int error = 0;
	 	int id  = -9999;
	 	int ids[] = new int []{-9999,-9999,-9999,-9999,-9999, -9999};

	 	// from 'cohortid.nc'
	 	for (int i=0; i<cht.getMd().getAct_chtno(); i++) {
	 		error = cinputer.getChtDataids(ids, i);
	 		if (error!=0) return error;

	 		chtids.add(ids[0]);
	 		chtinitids.add(ids[1]);
	 		chtgridids.add(ids[2]);
	 		chtclmids.add(ids[3]);
	 		chtvegids.add(ids[4]);
	 		chtfireids.add(ids[5]);

	 	}

	 	// from 'restart.nc' or 'sitein.nc'
	 	if (!cht.getMd().getRuneq()) { // 'runeq' stage doesn't require initial file
	 		for (int i=0; i<cht.getMd().getAct_initchtno(); i++) {
	 			id = cinputer.getInitchtId(i);
		 		if (id<0) return id;
	 			initids.add(id);
	 		}
	 	}

	 	// from 'climate.nc'
	 	for (int i=0; i<cht.getMd().getAct_clmno(); i++) {
	 		id = cinputer.getClmId(i);
	 		if (id<0) return id;
	 		clmids.add(id);
	 	}

	 	// from 'vegetation.nc'
	 	for (int i=0; i<cht.getMd().getAct_vegno(); i++) {
	 		id = cinputer.getVegId(i);
	 		if (id<0) return id;
	 		vegids.add(id);
	 	}

	 	// from 'fire.nc'
	 	for (int i=0; i<cht.getMd().getAct_fireno(); i++) {
	 		id = cinputer.getFireId(i);
	 		if (id<0) return id;
	 		fireids.add(id);
	 	}

	 	return error;
	 };

	 // general initialization
	 public void init(){

	 	// switches of N cycles
	     cht.getMd().setNfeed(true);
	     cht.getMd().setAvlnflg(false);
	     cht.getMd().setBaseline(true);

	 	// switches of modules
	     cht.getMd().setEnvmodule(true);
	     cht.getMd().setBgcmodule(true);
	     cht.getMd().setDsbmodule(true);
	     cht.getMd().setDslmodule(true);
	     cht.getMd().setDvmmodule(true);

	 	// output (buffer) data connection
	 	 if (cht.getMd().getOutRegn()) {
	 		 cht.getOutbuffer().setRegnOutData(regnod);
	 	 }

	 	 cht.getOutbuffer().setRestartOutData(resod);   //restart output data sets connenction

	 	 // output operators
	 	 //regnouter.setOutData(&regnod);
	 	 //resouter.setRestartOutData(&resod);
	 }

	//read-in data for a cohort
	public int readData(boolean vegread){

		int error = 0;
		
		//reading the climate data
		jcd.act_atm_drv_yr = cinputer.act_clmyr;	
		error = cinputer.getClimate(jcd.tair, jcd.prec, jcd.nirr, jcd.vapo, 
				jcd.act_atm_drv_yr,	clmrecno);
		if (error<0) return error;

		if (vegread) {
			//reading the vegetation community type data from 'vegetation.nc'
			jcd.act_vegset = cinputer.act_vegset;
			error = cinputer.getVegetation(jcd.vegyear, jcd.vegtype, 
				jcd.vegfrac, vegrecno);
			if (error<0) return error;

			//INDEX of veg. community codes, must be one of in those parameter files under 'config/'
			jcd.cmttype = jcd.vegtype[0];  //default, i.e., the first set of data
			for (int i=1; i<jcd.act_vegset; i++) {
				if (jcd.year>=jcd.vegyear[i]) {
					jcd.cmttype = jcd.vegtype[i];
				}
			}
		
		} else { // for calibration - veg type not yet defined
			jcd.cmttype = 0;   // will take the default parameters except for those to be calibrated
			jcd.vegfrac[0] = 1.0;
		}
		
		// read-in parameters AND initial conditions as inputs
		String configdir = "config/";
		cht.getChtlu().setDir(configdir);
		if (jcd.cmttype<10) {
			cht.getChtlu().setCmtcode("CMT0"+String.valueOf(jcd.cmttype));
		} else {
			cht.getChtlu().setCmtcode("CMT"+String.valueOf(jcd.cmttype));			
		}
		cht.getChtlu().init();   //put the parameter files in 'config/' with same directory of model
		
		// get soil texture data from gridded data
		int [] soiltexture = new int[ConstLayer.MAX_MIN_LAY];
		for (int il=0; il<ConstLayer.MAX_MIN_LAY; il++) {
			double topthick = 0.;
			topthick += ConstLayer.MINETHICK[il];
			if (topthick<=0.30) {
				soiltexture[il] = cht.getGd().getTopsoil();
			} else {
				soiltexture[il] = cht.getGd().getBotsoil();				
			}
		}
		cht.getChtlu().setMinetexture(soiltexture);

		//reading the fire occurence data from 'fire.nc'
		jcd.act_fireset = cinputer.act_fireset;
		cinputer.getFire(jcd.fireyear, jcd.fireseason, jcd.firesize, firerecno);
		if (cht.getMd().getUseseverity()) {
			cinputer.getFireSeverity(jcd.fireseverity, firerecno);
		}
		
		// transfer 'jcd' (only variables assinged above) to 'cht.cd'		
		cht.getCd().setAct_atm_drv_yr(jcd.act_atm_drv_yr);
		cht.getCd().setTair(jcd.tair);
		cht.getCd().setPrec(jcd.prec);
		cht.getCd().setNirr(jcd.nirr);
		cht.getCd().setVapo(jcd.vapo);

		cht.getCd().setAct_vegset(jcd.act_vegset);
		cht.getCd().setVegyear(jcd.vegyear);
		cht.getCd().setVegtype(jcd.vegtype);
		cht.getCd().setVegfrac(jcd.vegfrac);
		cht.getCd().setCmttype(jcd.cmttype);
		
		cht.getCd().setAct_fireset(jcd.act_fireset);
		cht.getCd().setFireyear(jcd.fireyear);
		cht.getCd().setFireseason(jcd.fireseason);
		cht.getCd().setFiresize(jcd.firesize);
		cht.getCd().setFireseverity(jcd.fireseverity);
		
  		return error;
	};

	// when initializing a cohort, using its record ids RATHER THAN chtids
	public int reinit(){

		// initializing module-calling controls
		cht.setFailed(false);
		cht.setErrorid(0);

		int errcode = 0;

		if (initrecno < 0 && cht.getMd().getInitmode()!=1) return -1;

		//initial modes other than lookup (i.e., initmode = 1)
		if (cht.getMd().getInitmode()==2) {
		 //note: the cohort order in sitein.nc must be exactly same as cohort in cohortid.nc
/*			 int err=0;
		 	 err=sinputer->getSiteinData(cht.md->chtinputdir,&cht.sitein, cid);
		 	 if (err!=0) return -1;
*/
		} else if (cht.getMd().getInitmode() == 3) {
			resinputer.getErrcode(errcode, initrecno);
			if (errcode!=0) {
				return -1;
			} else {

				cht.getResid().setChtid(initrecno);
				resinputer.getRestartData(jresid, initrecno);
				
				//'jresid' to 'cht.resid'
				
				
			}

		}

		//set initial state variables and parameters read-in from above
		cht.initStatePar();

		//clm/fire driving data (monthly/all years)
		cht.prepareAllDrivingData();

		return 0;
	};
	
	public void run_cohortly(){

		if(cht.getMd().getRuneq()){
			// a quick pre-run to get reasonably-well 'env' conditions, which may be good for 'eq' run
			runEnvmodule();

		    //
		    cht.getTimer().reset();
			cht.getMd().setEnvmodule(true);
			cht.getMd().setBgcmodule(true);
			cht.getMd().setDsbmodule(true);
			cht.getMd().setDslmodule(true);
			cht.getMd().setDvmmodule(true);

			cht.getMd().setFriderived(true);	
			cht.getCd().setYrsdist(0);

			cht.getTimer().setStageyrind(0);

		    yrstart = 0;
		    int nfri = Math.max(ConstTime.MIN_EQ_YR/cht.getGd().getFri(), 20);
		    nfri     = Math.min(nfri, ConstTime.MAX_EQ_YR/cht.getGd().getFri());
		    yrend    = nfri*cht.getGd().getFri()-1;   //20 FRI and within min. and max. MAX_EQ_YR
    		
		    run_timeseries();               
		}


		if(cht.getMd().getRunsp()){
			cht.getMd().setFriderived(false);	

			cht.getTimer().setStageyrind(0);
			cht.getTimer().setEqend(true);

			usedatmyr = Math.min(ConstTime.MAX_ATM_NOM_YR, cht.getCd().getAct_atm_drv_yr());

			yrstart = cht.getTimer().getSpbegyr();
			yrend   = cht.getTimer().getSpendyr();
			
			run_timeseries();
		}

		if(cht.getMd().getRuntr()){
			cht.getMd().setFriderived(false);	

			cht.getTimer().setStageyrind(0);
			cht.getTimer().setEqend(true);
			cht.getTimer().setSpend(true);

			usedatmyr = cht.getCd().getAct_atm_drv_yr();

			yrstart = cht.getTimer().getTrbegyr();
			yrend   = cht.getTimer().getTrendyr();
			
			run_timeseries();
		}

		if(cht.getMd().getRunsc()){
			cht.getMd().setFriderived(false);	

			cht.getTimer().setStageyrind(0);
			cht.getTimer().setEqend(true);
			cht.getTimer().setSpend(true);
			cht.getTimer().setTrend(true);

			usedatmyr = cht.getCd().getAct_atm_drv_yr();

			yrstart = cht.getTimer().getScbegyr();
			yrend   = cht.getTimer().getScendyr();
			
			run_timeseries();
		}
		
		//restart.nc always output
		//resouter.outputVariables(cohortcount);

	};

	// run model with "ENV module" on only
	private void runEnvmodule(){


		cht.getMd().setEnvmodule(true);
		cht.getMd().setBgcmodule(false);
		cht.getMd().setDsbmodule(false);
		cht.getMd().setDslmodule(false);
		cht.getMd().setDvmmodule(false);

		dstepcnt = 0;
		mstepcnt = 0;
		ystepcnt = 0;

		cht.getCd().setYrsdist(1000);

		yrstart = 0;
		yrend   = 100;
		
		run_timeseries();

	};

	private void run_timeseries(){

		for (int icalyr=yrstart; icalyr<=yrend; icalyr++){

			int yrindex = cht.getTimer().getCurrentYearIndex();   //starting from 0
			cht.getCd().setYear(cht.getTimer().getCalendarYear());

			cht.prepareDayDrivingData(yrindex, usedatmyr);

			int outputyrind = cht.getTimer().getOutputYearIndex();
			for (int im=0; im<12;im++){

				int currmind=  im;
				cht.getCd().setMonth(im+1);
				int dinmcurr = ConstTime.DINM[im];

				cht.updateMonthly(yrindex, currmind, dinmcurr);
				cht.getTimer().advanceOneMonth();

				// site output module calling
				if (outputyrind >=0) {
					if (cht.getMd().getOutSiteDay()){
						for (int id=0; id<dinmcurr; id++) {
							for (int ip=0; ip<ConstCohort.NUM_PFT; ip++) {
								
								//cht.getOutbuffer().getEnvoddly()[ip][id].chtid = cht.cd.chtid;
								//EnvDataDly *envoddly = &cht.outbuffer.envoddly[ip][id];
								//envdlyouter.outputCohortEnvVars_dly(envoddly, icalyr, im, id, ip, dstepcnt);
							}

							dstepcnt++;
						}
					}

					//
					if (cht.getMd().getOutSiteMonth()){
						//dimmlyouter.outputCohortDimVars_mly(&cht.cd, mstepcnt);
						for (int ip=0; ip<ConstCohort.NUM_PFT; ip++) {
							//envmlyouter.outputCohortEnvVars_mly(&cht.cd.m_snow, &cht.ed[ip], icalyr, im, ip, mstepcnt);
							//bgcmlyouter.outputCohortBgcVars_mly(&cht.bd[ip], icalyr, im, ip, mstepcnt);
						}
						mstepcnt++;
					}

					//
					if (cht.getMd().getOutSiteYear() && im==11){
						//dimylyouter.outputCohortDimVars_yly(&cht.cd, ystepcnt);
						for (int ip=0; ip<ConstCohort.NUM_PFT; ip++) {
							//envylyouter.outputCohortEnvVars_yly(&cht.cd.y_snow, &cht.ed[ip], icalyr, ip, ystepcnt);
							//bgcylyouter.outputCohortBgcVars_yly(&cht.bd[ip], icalyr, ip, ystepcnt);
						}
						ystepcnt++;

					}

				} // end of site calling output modules

			}

			if (cht.getMd().getOutRegn() && outputyrind >=0){
				//regnouter.outputCohortVars(outputyrind, cohortcount, 0);  // "0" implies good data
			}

			if(cht.getMd().getConsoledebug()){
				System.out.println("TEM " +cht.getMd().getRunstages() 
						+" run: year "+icalyr
						+" @cohort "+cht.getCd().getChtid());

			}

			// if EQ run,option for simulation break
  	   		if (cht.getMd().getRuneq()) {
  	   			//cht.equiled = cht.testEquilibrium();
  	   			//if(cht.equiled )break;
  	   		}
		}

	};

}

