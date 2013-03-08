package ASSEMBLER;
/*
 * RunCohort.java
 *
 * Cohort initialization, run, and output
 * 		Note: the output modules are put here, so can be flexible for outputs
 *
*/
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

	 public int cohortcount=0;

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
	 int usedatmyr=-999;

	 int yrstart=-999;
	 int yrend=-999;
	 int dstepcnt=0;
	 int mstepcnt=0;
	 int ystepcnt=0;

	// data connections in modules
	public void initData(){
				
		// output (buffer) data connection
		if (cht.getMd().getOutRegn()) {
			cht.getOutbuffer().setRegnOutData(regnod);
		}

		cht.getOutbuffer().setRestartOutData(resod);   //restart output data sets connenction

		// output operators
		// regnouter.setOutData(&regnod);
		// resouter.setRestartOutData(&resod);
	};

	//read-in data for a cohort
	public int readData(){

		// record ids in '.nc' datasets
		int clmrecid = -999;
		int vegrecid = -999;
		int firerecid= -999;

		//reading the climate data
		jcd.act_atm_drv_yr = cinputer.act_clmyr;
		clmrecid = cinputer.getClmRec(jcd.clmid);
		if (clmrecid<0) return -1;
		
		cinputer.getClimate(jcd.tair, jcd.prec, jcd.nirr, jcd.vapo, jcd.act_atm_drv_yr, clmrecid);

		//reading the vegetation community type data from '.nc', otherwise from 'chtlu' for site-run
		jcd.act_vegset = cinputer.act_vegset;

		vegrecid = cinputer.getVegRec(jcd.vegid);
		if (vegrecid<0) return -2;
		cinputer.getVegetation(jcd.vegyear, jcd.vegtype, jcd.vegfrac, vegrecid);

		jcd.cmttype = jcd.vegtype[0];  //default, i.e., the first set of data

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

		//reading the fire occurence data from '.nc', otherwise from 'chtlu' for site-run
		jcd.act_fireset = cinputer.act_fireset;
		firerecid = cinputer.getFireRec(jcd.vegid);
		if (firerecid<0) return -3;
		cinputer.getFire(jcd.fireyear, jcd.fireseason, jcd.firesize, firerecid);
		if (cht.getMd().getUseseverity()) {
			cinputer.getFireSeverity(jcd.fireseverity, firerecid);
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
		
  		return 0;
	};

	// when initializing a cohort, using its record ids RATHER THAN chtids
	// cid - the record id for chort;
	public int reinit(int cid){

		// initializing module-calling controls
		cht.setFailed(false);
		cht.setErrorid(0);

		int errcode = 0;

		if (cid < 0) return -1;

		//initial modes other than lookup (i.e., initmode = 1)
		if (cht.getMd().getInitmode()==2) {
		 //note: the cohort order in sitein.nc must be exactly same as cohort in cohortid.nc
/*			 int err=0;
		 	 err=sinputer->getSiteinData(cht.md->chtinputdir,&cht.sitein, cid);
		 	 if (err!=0) return -1;
*/
		} else if (cht.getMd().getInitmode() == 3) {
			int inichtid = cht.getCd().getInichtid();
			resinputer.getErrcode(errcode, inichtid);
			if (errcode!=0) {
				return -1;
			} else {

				cht.getResid().setChtid(inichtid);
				resinputer.getRestartData(jresid, inichtid);
				
				//'jresid' to 'cht.resid'
				
				
			}

		}

		//set initial state variables and parameters read-in from above
		cht.initStatePar();

		//clm/fire driving data (monthly/all years)
		cht.prepareAllDrivingData();

		return 0;
	};
	
	public void run(){

		// N cycles
	    cht.getMd().setNfeed(false);
	    cht.getMd().setBaseline(true);
	    cht.getMd().setAvlnflg(false);

	    //
	    cht.getTimer().reset();

		if(cht.getMd().getRuneq()){
			cht.getTimer().setStageyrind(0);
    		runEquilibrium();               //module options included
		}

		cht.getMd().setEnvmodule(true);
		cht.getMd().setBgcmodule(true);
		cht.getMd().setDsbmodule(true);
		cht.getMd().setDslmodule(true);
		cht.getMd().setDvmmodule(true);

		if(cht.getMd().getRunsp()){
			cht.getTimer().setStageyrind(0);
			cht.getTimer().setEqend(true);
    		runSpinup();
		}

		if(cht.getMd().getRuntr()){
			cht.getTimer().setStageyrind(0);
			cht.getTimer().setEqend(true);
			cht.getTimer().setSpend(true);
			runTransit();
		}

		if(cht.getMd().getRunsc()){
			cht.getTimer().setStageyrind(0);
			cht.getTimer().setEqend(true);
			cht.getTimer().setSpend(true);
			cht.getTimer().setTrend(true);
			runScenario();
		}
		
		//restart.nc always output
		//resouter.outputVariables(cohortcount);

	};

	private void runEquilibrium(){

		// first, run model with "ENV module" only

		cht.getMd().setEnvmodule(true);
		cht.getMd().setBgcmodule(false);
		cht.getMd().setDsbmodule(false);
		cht.getMd().setDslmodule(false);
		cht.getMd().setDvmmodule(false);

		dstepcnt = 0;
		mstepcnt = 0;
		ystepcnt = 0;

		cht.getFd().setYsf(1000);

		yrstart = 0;
		yrend   = 100;
		modulerun();

	    //Then, use equilibrium environment driver to run model with all modules ON

		cht.getTimer().reset();

		cht.getMd().setEnvmodule(true);
		cht.getMd().setBgcmodule(true);
		cht.getMd().setDsbmodule(true);
		cht.getMd().setDslmodule(true);
		cht.getMd().setDvmmodule(true);

		dstepcnt = 0;
		mstepcnt = 0;
		ystepcnt = 0;
		cht.getFd().setYsf(0);

		yrstart = 0;
		yrend   = Math.min(ConstTime.MAX_EQ_YR, 20*cht.getGd().getFri()-2);   //20 FRI or max. MAX_EQ_YR
		cht.getMd().setFriderived(true);
		modulerun();

	};

	private void runSpinup(){

		usedatmyr = Math.min(ConstTime.MAX_ATM_NOM_YR, cht.getCd().getAct_atm_drv_yr());

		yrstart = cht.getTimer().getSpbegyr();
		yrend   = cht.getTimer().getSpendyr();
		modulerun();

	};

	private void runTransit(){

		usedatmyr = cht.getCd().getAct_atm_drv_yr();

		yrstart = cht.getTimer().getTrbegyr();
		yrend   = cht.getTimer().getTrendyr();
		modulerun();

	};

	private void runScenario(){

		usedatmyr = cht.getCd().getAct_atm_drv_yr();

		yrstart = cht.getTimer().getScbegyr();
		yrend   = cht.getTimer().getScendyr();
		modulerun();

	};

	private void modulerun(){

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

