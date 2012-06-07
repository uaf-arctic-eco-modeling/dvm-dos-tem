/*
 * RunCohort.cpp
 * 
 * Cohort initialization, run, and output
 * 		Note: the output modules are put here, so can be flexible for outputs
 * 
*/

#include "RunCohort.h"

RunCohort::RunCohort(){

    dstepcnt = 0;
    mstepcnt = 0;
    ystepcnt = 0;

	cohortcount = 0;   // counter for cohort have been run
}

RunCohort::~RunCohort(){

}

void RunCohort::setModelData(ModelData * mdp){
  	md = mdp;
}

// data connections in modules
void RunCohort::initData(string & cmttype){

	 // read-in parameters AND initial conditions as inputs
	 string configdir = "config/";
	 cht.chtlu.dircmtname = configdir+cmttype;
	 cht.chtlu.init();   //put the parameter files in 'config/' with same directory of model

	// output (buffer) data connection
	 if (md->outRegn) {
		 cht.outbuffer.setRegnOutData(&regnod);
	 }

	 cht.outbuffer.setRestartOutData(&resod);   //restart output data sets connenction

	 // output operators
	 regnouter.setOutData(&regnod);
	 resouter.setRestartOutData(&resod);
}

//read-in data for a cohort
int RunCohort::readData(){

	// record ids in '.nc' datasets
	int clmrecid = MISSING_I;
	int vegrecid = MISSING_I;
	int firerecid= MISSING_I;

	//reading the climate data
	cht.cd.act_atm_drv_yr = cinputer.act_clmyr;
  	clmrecid = cinputer.getClmRec(cht.cd.clmid);
  	if (clmrecid<0) return -1;
	cinputer.getClimate(cht.cd.tair, cht.cd.prec, cht.cd.nirr, cht.cd.vapo, cht.cd.act_atm_drv_yr, clmrecid);

  	if (md->runmode==2) {
  		//reading the vegetation community type data from '.nc', otherwise from 'chtlu' for site-run
  		cht.cd.act_vegset = cinputer.act_vegset;

  		vegrecid = cinputer.getVegRec(cht.cd.vegid);
  		if (vegrecid<0) return -2;
  		cinputer.getVegetation(cht.cd.vegyear, cht.cd.vegtype, cht.cd.vegfrac, vegrecid);

  		cht.cd.cmttype = cht.cd.vegtype[0];  //default, i.e., the first set of data
  		cht.cd.cmtfrac = cht.cd.vegfrac[0];

  		//reading the fire occurence data from '.nc', otherwise from 'chtlu' for site-run
  		cht.cd.act_fireset = cinputer.act_fireset;
  		firerecid = cinputer.getFireRec(cht.cd.vegid);
  		if (firerecid<0) return -3;
		cinputer.getFire(cht.cd.fireyear, cht.cd.fireseason, cht.cd.firesize, firerecid);
  		if (md->useseverity) {
  			cinputer.getFireSeverity(cht.cd.fireseverity, firerecid);
  		}
  	} else {
  		cht.cd.cmttype = 0;   // means for one input 'community type'
  		cht.cd.cmtfrac = 1.0;  // means the whole community is fully occupied by one single type

  		//fire occurence data from 'chtlu'
  		for (int i=0; i<MAX_FIR_OCRNUM; i++){
  			cht.cd.fireyear[i]    = cht.chtlu.fireyear[i];
  			cht.cd.fireseason[i]  = cht.chtlu.fireseason[i];
  			cht.cd.firesize[i]    = cht.chtlu.firesize[i];
  			cht.cd.fireseverity[i]= cht.chtlu.fireseverity[i];
  		}

  	}

    return 0;
};

// when initializing a cohort, using its record ids RATHER THAN chtids
// cid - the record id for chort;
int RunCohort::reinit(const int &cid){

	// initializing module-calling controls
	cht.failed  = false;
	cht.errorid = 0;

	int errcode = 0;
	
    if (cid < 0) return -1;
	 
	 //initial modes other than lookup (i.e., initmode = 1)
	 if (md->initmode==2) {
		 //note: the cohort order in sitein.nc must be exactly same as cohort in cohortid.nc
/*		 int err=0;
		 err=sinputer->getSiteinData(cht.md->chtinputdir,&cht.sitein, cid);
		 if (err!=0) return -1;
*/
	 } else if (md->initmode == 3) {

		 resinputer.getErrcode(errcode, inichtind);
		 if (errcode!=0) {
			 return -1;
		 } else {

			 cht.resid.chtid = inichtind;
			 resinputer.getRestartData(&cht.resid, inichtind);
		 }

	 }
	 
	 //set initial state variables and parameters read-in from above
	 cht.initStatePar();

	 //clm/fire driving data (monthly/all years)
	 cht.prepareAllDrivingData();

     return 0;
};

void RunCohort::run(){

		// N cycles
	    md->nfeed   = 1;
	    md->avlnflg = 0;
		md->baseline= 1;

	    //
	    cht.timer->reset();

///*
		if(cht.md->runeq){
			cht.timer->stageyrind = 0;
    		runEquilibrium();               //module options included
		}

		md->envmodule = true;
	    md->bgcmodule = true;
	    md->dsbmodule = true;
	    md->dslmodule = true;
	    md->dvmmodule = true;

		if(cht.md->runsp){
			cht.timer->stageyrind = 0;
			cht.timer->eqend = true;
    		runSpinup();
		}
		
		if(cht.md->runtr){	
			cht.timer->stageyrind = 0;
			cht.timer->eqend = true;
			cht.timer->spend = true;
			runTransit();
		}

		if(cht.md->runsc){
			cht.timer->stageyrind = 0;
			cht.timer->eqend = true;
			cht.timer->spend = true;
			cht.timer->trend = true;
			runScenario();
		}
//*/
		//restart.nc always output
		resouter.outputVariables(cohortcount);
	
}; 

void RunCohort::runEquilibrium(){

	// first, run model with "ENV module" only

	 md->envmodule = true;
     md->bgcmodule = false;
     md->dsbmodule = false;
     md->dslmodule = false;
     md->dvmmodule = false;

     dstepcnt = 0;
     mstepcnt = 0;
     ystepcnt = 0;

     cht.fd->ysf =1000;

     yrstart = 0;
     yrend   = 100;
     modulerun();

	 //Then, use equilibrium environment driver to run model with all modules ON
///*
     cht.timer->reset();

 	 md->envmodule = true;
     md->bgcmodule = true;
     md->dvmmodule = true;
     md->dsbmodule = true;
     md->dslmodule = true;

     dstepcnt = 0;
     mstepcnt = 0;
     ystepcnt = 0;
     cht.fd->ysf =0;

     yrstart = 0;
     yrend   = min(MAX_EQ_YR, 20*cht.gd->fri-2);   //20 FRI or max. MAX_EQ_YR
     md->friderived = true;
     modulerun();
//*/
};

void RunCohort::runSpinup(){

    usedatmyr = min(MAX_ATM_NOM_YR, cht.cd.act_atm_drv_yr);

    yrstart = cht.timer->spbegyr;
    yrend   = cht.timer->spendyr;
    modulerun();
	 
};

void RunCohort::runTransit(){

    usedatmyr = cht.cd.act_atm_drv_yr;

    yrstart = cht.timer->trbegyr;
    yrend   = cht.timer->trendyr;
    modulerun();

};

void RunCohort::runScenario(){

    usedatmyr = cht.cd.act_atm_drv_yr;

    yrstart = cht.timer->scbegyr;
    yrend   = cht.timer->scendyr;
    modulerun();

};

void RunCohort::modulerun(){

	for (int icalyr=yrstart; icalyr<=yrend; icalyr++){

		 int yrindex = cht.timer->getCurrentYearIndex();   //starting from 0
		 cht.cd.year = cht.timer->getCalendarYear();

		 cht.prepareDayDrivingData(yrindex, usedatmyr);

		 int outputyrind = cht.timer->getOutputYearIndex();
		 for (int im=0; im<12;im++){

		   int currmind=  im;
		   cht.cd.month = im+1;
		   int dinmcurr = cht.timer->getDaysInMonth(im);;

		   cht.updateMonthly(yrindex, currmind, dinmcurr);
	       cht.timer->advanceOneMonth();

	    	// site output module calling
	       if (outputyrind >=0) {
	    	   if (md->outSiteDay){
	    		   for (int id=0; id<dinmcurr; id++) {
	    			   for (int ip=0; ip<cht.cd.numpft; ip++) {
	    				   cht.outbuffer.envoddly[ip][id].chtid = cht.cd.chtid;
	    				   EnvDataDly *envoddly = &cht.outbuffer.envoddly[ip][id];
	    				   envdlyouter.outputCohortEnvVars_dly(envoddly, icalyr, im, id, ip, dstepcnt);
	    			   }

	    			   dstepcnt++;
	    		   }
	    	   }

	    	   //
	    	   if (md->outSiteMonth){
	    		   dimmlyouter.outputCohortDimVars_mly(&cht.cd, mstepcnt);
	    		   for (int ip=0; ip<cht.cd.numpft; ip++) {
	    			   envmlyouter.outputCohortEnvVars_mly(&cht.cd.m_snow, &cht.ed[ip], icalyr, im, ip, mstepcnt);
	    			   bgcmlyouter.outputCohortBgcVars_mly(&cht.bd[ip], icalyr, im, ip, mstepcnt);
	    		   }
	    		   mstepcnt++;
	    	   }

	    		//
	    	   if (md->outSiteYear && im==11){
	    		   dimylyouter.outputCohortDimVars_yly(&cht.cd, ystepcnt);
	    		   for (int ip=0; ip<cht.cd.numpft; ip++) {
	    			   envylyouter.outputCohortEnvVars_yly(&cht.cd.y_snow, &cht.ed[ip], icalyr, ip, ystepcnt);
	    			   bgcylyouter.outputCohortBgcVars_yly(&cht.bd[ip], icalyr, ip, ystepcnt);
	    		   }
	    		   ystepcnt++;

	    	   }

	       } // end of site calling output modules

	    }

		if (md->outRegn && outputyrind >=0){
			regnouter.outputCohortVars(outputyrind, cohortcount, 0);  // "0" implies good data
		}

		if(cht.md->consoledebug){
	    	cout <<"TEM " << cht.md->runstages <<" run: year "
	    	<<icalyr<<" @cohort "<<cht.cd.chtid<<"\n";

	    }

		// if EQ run,option for simulation break
  	   	if (cht.md->runeq) {
  	   		//cht.equiled = cht.testEquilibrium();
  	   		//if(cht.equiled )break;
  	   	}
	}

};

////////////////////////////////////////////////////////////////////////
