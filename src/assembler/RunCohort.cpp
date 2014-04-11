/*
 * RunCohort.cpp
 * 
 * Cohort initialization, run, and output
 * 		Note: the output modules are put here, so can be flexible for outputs
 * 
*/
#include <json/writer.h>
#include <boost/filesystem.hpp>
#include "RunCohort.h"
#include "../CalController.h"

#include "../TEMLogger.h"
extern src::severity_logger< severity_level > glg;


RunCohort::RunCohort(){

    dstepcnt = 0;
    mstepcnt = 0;
    ystepcnt = 0;

	cohortcount = 0;   // counter for cohort have been run
}

RunCohort::~RunCohort(){

}

bool RunCohort::get_calMode() {
  return this->calMode;
}
void RunCohort::set_calMode(bool new_value) {
  this->calMode = new_value;
}


void RunCohort::setModelData(ModelData * mdp){
  	md = mdp;
}

//reading cohort-level all data ids
int RunCohort::allchtids(){
	int error = 0;
	int id = MISSING_I;
	int id1 = MISSING_I;
	int id2 = MISSING_I;
	int id3 = MISSING_I;
	int id4 = MISSING_I;
	int id5 = MISSING_I;

	// from 'cohortid.nc'
	for (int i=0; i<md->act_chtno; i++) {
		error = cinputer.getChtDataids(id, id1, id2, id3, id4, id5, i);
		if (error!=0) return error;

		chtids.push_back(id);
		chtinitids.push_back(id1);
		chtgridids.push_back(id2);
		chtclmids.push_back(id3);
		chtvegids.push_back(id4);
		chtfireids.push_back(id5);

	}

	// from 'restart.nc' or 'sitein.nc'
	if (md->initmode>1) { // 'runeq' stage doesn't require initial file
		for (int i=0; i<md->act_initchtno; i++) {
			error = cinputer.getInitchtId(id, i);
			if (error!=0) return error;
			initids.push_back(id);
		}
	}

	// from 'climate.nc'
	for (int i=0; i<md->act_clmno; i++) {
		error = cinputer.getClmId(id, i);
		if (error!=0) return error;
		clmids.push_back(id);
	}

	// from 'vegetation.nc'
	for (int i=0; i<md->act_vegno; i++) {
		error = cinputer.getVegId(id, i);
		if (error!=0) return error;
		vegids.push_back(id);
	}

	// from 'fire.nc'
	for (int i=0; i<md->act_fireno; i++) {
		error = cinputer.getFireId(id, i);
		if (error!=0) return error;
		fireids.push_back(id);
	}

	return error;
};

// general initialization
void RunCohort::init(){
  BOOST_LOG_SEV(glg, info) << "In RunCohort::init(), setting a bunch of modules on/off";

	// switches of N cycles
    md->set_nfeed(true);
    md->set_avlnflg(false);
	md->baseline= 1;

	  // switches of modules
	  md->set_envmodule(true);
    md->set_bgcmodule(true);
    md->set_dsbmodule(true);
    md->set_dslmodule(true);
    md->set_dvmmodule(true);

	// output (buffer) data connection
	 if (md->outRegn) {
		 cht.outbuffer.setRegnOutData(&regnod);
	 }

	 cht.outbuffer.setRestartOutData(&resod);   //restart output data sets connenction

	 // output operators
	 regnouter.setOutData(&regnod);
	 resouter.setRestartOutData(&resod);
}

//read-in one-timestep data for a cohort
int RunCohort::readData(){

	//reading the climate data
	cht.cd.act_atm_drv_yr = md->act_clmyr;
	cinputer.getClimate(cht.cd.tair, cht.cd.prec, cht.cd.nirr, cht.cd.vapo, cht.cd.act_atm_drv_yr, clmrecno);

	//reading the vegetation community type data from 'vegetation.nc'
	cht.cd.act_vegset = md->act_vegset;
	cinputer.getVegetation(cht.cd.vegyear, cht.cd.vegtype, cht.cd.vegfrac, vegrecno);

	//INDEX of veg. community codes, must be one of in those parameter files under 'config/'
	cht.cd.cmttype = cht.cd.vegtype[0];  //default, i.e., the first set of data
	for (int i=1; i<md->act_vegset; i++) {
		if (cht.cd.year>=cht.cd.vegyear[i]) {
			cht.cd.cmttype = cht.cd.vegtype[i];
		}
	}

	// read-in parameters AND initial conditions for the above 'cmttype'
	 string configdir = "config/";
	 cht.chtlu.dir = configdir;
	 stringstream ss;
	 ss<<cht.cd.cmttype;
	 if (cht.cd.cmttype<10){
		 cht.chtlu.cmtcode = "CMT0"+ss.str();
	 } else {
		 cht.chtlu.cmtcode = "CMT"+ss.str();
	 }
	 cht.chtlu.init();   //put the parameter files in 'config/' with same directory of model

	//reading the fire occurence data from '.nc', if not FRI derived
  	if (!md->get_friderived() && !md->runeq){
  		cht.cd.act_fireset = md->act_fireset;
  		cinputer.getFire(cht.cd.fireyear, cht.cd.fireseason, cht.cd.firesize, firerecno);
  		if (md->useseverity) {
  			cinputer.getFireSeverity(cht.cd.fireseverity, firerecno);
  		}
  	}

    return 0;
};

// re-initializing state variables for current cohort
int RunCohort::reinit(){

	// initializing module-calling controls
	cht.failed  = false;
	cht.errorid = 0;
	int errcode = 0;
	
    // checking
	if (initrecno < 0 && md->initmode!=1) {
		cout<<"initial condition record not exists! \n";
		return -1;
	}
	 
	 //initial modes other than lookup (i.e., initmode = 1)
	 if (md->initmode==2) {  // not yet done!
		 //note: the cohort order in sitein.nc must be exactly same as cohort in cohortid.nc
/*		 int err=0;
		 err=sinputer->getSiteinData(cht.md->chtinputdir,&cht.sitein, cid);
		 if (err!=0) return -1;
*/
	 } else if (md->initmode == 3) {

		 resinputer.getErrcode(errcode, initrecno);
		 if (errcode!=0) {
			 return -1;
		 } else {

			 resinputer.getReschtId(cht.resid.chtid, initrecno);
			 resinputer.getRestartData(&cht.resid, initrecno);
		 }

	 }
	 
	 // soil texture from gridded data
	 for (int il=0; il<MAX_MIN_LAY; il++) {
		 double topthick = 0.;
		 topthick +=MINETHICK[il];
		 if (topthick <=0.30) {
			 cht.chtlu.minetexture[il] = cht.cd.gd->topsoil;
		 } else {
			 cht.chtlu.minetexture[il] = cht.cd.gd->botsoil;
		 }
	 }

	 //set initial state variables and parameters read-in from above
	 cht.initStatePar();

	 //clm/fire driving data (monthly/all years)
	 cht.prepareAllDrivingData();

     return 0;
};

// run one cohort for a period of time
void RunCohort::run_cohortly(){

  // Ends up as a null pointer if calibratiionMode is off.
  boost::shared_ptr<CalController> calcontroller_ptr;
  if ( this->get_calMode() ) {
    calcontroller_ptr.reset( new CalController(&this->cht) );
  }


	    //
	    cht.timer->reset();

	    //
		if(cht.md->runeq){

			BOOST_LOG_SEV(glg, info) << "Starting a quick pre-run to get "
                                     << "reasonably-good 'env' conditions, "
                                     << "which may then be good for 'eq' run...";

			runEnvmodule(calcontroller_ptr);

            if (calcontroller_ptr) {
              BOOST_LOG_SEV(glg, info) << "Pausing. Please check that the 'pre-run' data looks good.";
              calcontroller_ptr->pause();
              BOOST_LOG_SEV(glg, info) << "Clearing out json files from pre-run...";

              boost::filesystem::path json_tmp_dir("/tmp/cal-dvmdostem");
              boost::filesystem::remove_all(json_tmp_dir);
              boost::filesystem::create_directory(json_tmp_dir);

              boost::filesystem::path yr_json_tmp_dir("/tmp/year-cal-dvmdostem");
              boost::filesystem::remove_all(yr_json_tmp_dir);
              boost::filesystem::create_directory(yr_json_tmp_dir);


            }
			//
			cht.timer->reset();
			BOOST_LOG_SEV(glg, info) << "In run_cohortly, setting all modules to on...";
      md->set_envmodule(true);
      md->set_bgcmodule(true);
      md->set_dsbmodule(true);
      md->set_dslmodule(true);
      md->set_dvmmodule(true);
      md->set_friderived(true);
			
      cht.timer->stageyrind = 0;

			cht.cd.yrsdist = 0;

		    yrstart = 0;

		    if (cht.gd->fri>0) {
		    	int nfri = fmax(MIN_EQ_YR/cht.gd->fri, 20);
		    	nfri = fmin(nfri, MAX_EQ_YR/cht.gd->fri); //20 FRI and within range of min. and max. MAX_EQ_YR
		    	yrend= nfri*cht.gd->fri-1;   // ending just prior to the fire occurrency year
		    } else {
		    	yrend = MAX_EQ_YR;
		    }

		    run_timeseries(calcontroller_ptr);

		}

		if(cht.md->runsp){
			cht.timer->stageyrind = 0;
			cht.timer->eqend = true;

		    used_atmyr = fmin(MAX_ATM_NOM_YR, cht.cd.act_atm_drv_yr);

		    yrstart = cht.timer->spbegyr;
		    yrend   = cht.timer->spendyr;

		    md->set_friderived(false);

		    run_timeseries(calcontroller_ptr);

		}
		
		if(cht.md->runtr){	
			cht.timer->stageyrind = 0;
			cht.timer->eqend = true;
			cht.timer->spend = true;

		    used_atmyr = cht.cd.act_atm_drv_yr;

		    yrstart = cht.timer->trbegyr;
		    yrend   = cht.timer->trendyr;

		    md->set_friderived(false);

		    run_timeseries(calcontroller_ptr);

		}

		if(cht.md->runsc){
			cht.timer->stageyrind = 0;
			cht.timer->eqend = true;
			cht.timer->spend = true;
			cht.timer->trend = true;

		    used_atmyr = cht.cd.act_atm_drv_yr;

		    yrstart = cht.timer->scbegyr;
		    yrend   = cht.timer->scendyr;

		    md->set_friderived(false);

		    run_timeseries(calcontroller_ptr);

		}

		//'restart.nc' always output at the end of run-time
		resouter.outputVariables(cohortcount);
	
}; 

void RunCohort::runEnvmodule(boost::shared_ptr<CalController> calcontroller_ptr){
  BOOST_LOG_SEV(glg, info) << "In RunCohort::runEnvmodule, setting only envmodule on.";

  //run model with "ENV module" only

	 md->set_envmodule(true);
     md->set_bgcmodule(false);
     md->set_dsbmodule(false);
     md->set_dslmodule(false);
     md->set_dvmmodule(false);

     cht.cd.yrsdist = 1000;

     yrstart = 0;
     yrend   = 100; // This actually results in running 101 years...

     run_timeseries(calcontroller_ptr);
     BOOST_LOG_SEV(glg, info) << "Done running env module for 101 year 'warm up'.";

};

/** Run one cohort thru time series.
 * 
 * i.e.: 
 * for each year
 *     for each month
 */ 
void RunCohort::run_timeseries(boost::shared_ptr<CalController> calcontroller_ptr){
  
  srand (time(NULL));

	for (int icalyr=yrstart; icalyr<=yrend; icalyr++) {
    
    BOOST_LOG_SEV(glg, debug) << "Some begin of year data for plotting...";
    
    // See if a signal has arrived (possibly from user
    // hitting Ctrl-C) and if so, stop the simulation
    // and drop into the calibration "shell".
    if (calcontroller_ptr) {
      calcontroller_ptr->check_for_signals();
    }
     int yrindex = cht.timer->getCurrentYearIndex();   //starting from 0
		 cht.cd.year = cht.timer->getCalendarYear();

		 cht.prepareDayDrivingData(yrindex, used_atmyr);

		 int outputyrind = cht.timer->getOutputYearIndex();
    for (int im=0; im<12;im++){
       BOOST_LOG_SEV(glg, debug) << "Some beginning of month data for plotting...";

		   int currmind=  im;
		   cht.cd.month = im+1;
		   int dinmcurr = cht.timer->getDaysInMonth(im);;

		   cht.updateMonthly(yrindex, currmind, dinmcurr);
	       cht.timer->advanceOneMonth();

	    	// site output module calling
	       if (outputyrind >=0) {
	    	   if (md->outSiteDay){
	    		   for (int id=0; id<dinmcurr; id++) {
	    			   cht.outbuffer.envoddlyall[id].chtid = cht.cd.chtid;
	    			   envdlyouter.outputCohortEnvVars_dly(-1, &cht.outbuffer.envoddlyall[id],
			    				                               icalyr, im, id, dstepcnt);     // this will output non-veg (multiple PFT) related variables
	    			   for (int ip=0; ip<NUM_PFT; ip++) {
	    			    	if (cht.cd.d_veg.vegcov[ip]>0.){
	    			    		envdlyouter.outputCohortEnvVars_dly(ip, &cht.outbuffer.envoddly[ip][id],
	    			    				                               icalyr, im, id, dstepcnt);

	    			    	}
	    			   }

	    			   dstepcnt++;
	    		   }
	    	   }

	    	   //
	    	   if (md->outSiteMonth){
	    		   dimmlyouter.outputCohortDimVars_mly(&cht.cd, mstepcnt);
	    		   envmlyouter.outputCohortEnvVars_mly(-1, &cht.cd.m_snow, cht.edall,
	    				                               icalyr, im, mstepcnt);
		    	   bgcmlyouter.outputCohortBgcVars_mly(-1, cht.bdall, cht.fd,
		    			                               icalyr, im, mstepcnt);

		    	   for (int ip=0; ip<NUM_PFT; ip++) {
	    		    	if (cht.cd.m_veg.vegcov[ip]>0.){
	    		    		envmlyouter.outputCohortEnvVars_mly(ip, &cht.cd.m_snow, &cht.ed[ip],
	    		    				icalyr, im, mstepcnt);
	    		    		bgcmlyouter.outputCohortBgcVars_mly(ip, &cht.bd[ip], cht.fd,
	    		    				icalyr, im, mstepcnt);
	    		    	}
	    		   }
	    		   mstepcnt++;
	    	   }

	    		//
	    	   if (md->outSiteYear && im==11){
	    		   dimylyouter.outputCohortDimVars_yly(&cht.cd, ystepcnt);
	    		   envylyouter.outputCohortEnvVars_yly(-1, &cht.cd.y_snow, cht.edall, icalyr, ystepcnt);
		    	   bgcylyouter.outputCohortBgcVars_yly(-1, cht.bdall, cht.fd, icalyr, ystepcnt);

		    	   for (int ip=0; ip<NUM_PFT; ip++) {
	    		    	if (cht.cd.y_veg.vegcov[ip]>0.){
	    		    		envylyouter.outputCohortEnvVars_yly(ip, &cht.cd.y_snow, &cht.ed[ip],
	    		    				icalyr, ystepcnt);
	    		    		bgcylyouter.outputCohortBgcVars_yly(ip, &cht.bd[ip], cht.fd,
	    		    				icalyr, ystepcnt);
	    		    	}
	    		   }
	    		   ystepcnt++;

	    	   }

	       } // end of site calling output modules
         BOOST_LOG_SEV(glg, debug) << "Some end of month data for plotting...";
	

        if(this->get_calMode()){    
            Json::Value data;

            std::ofstream out_stream;

            data["Year"] = icalyr;
            data["Month"] = im;
   
            /* Environmental variables */   
            /* Monthly Thermal information */
            data["TempAir"] = cht.ed->m_atms.ta;
            //cht.ed->m_sois.ts[MAX_SOI_LAY], but no pre-summed values, so...
            data["TempOrganicLayer"] = -1;
            data["TempMineralLayer"] = -1;
            data["ActiveLayerDepth"] = cht.ed->m_soid.ald;

            /* Monthly Hydrodynamic information */
            data["Snowfall"] = cht.ed->m_a2l.snfl;
            data["Rainfall"] = cht.ed->m_a2l.rnfl;
            data["WaterTable"] = cht.ed->m_sois.watertab;
            //m_soid.vwc[] has approx 23 values - I assume these are summed in the following.
            data["VWCOrganicLayer"] = cht.ed->m_soid.vwcshlw + cht.ed->m_soid.vwcdeep;
            data["VWCMineralLayer"] = cht.ed->m_soid.vwcminea 
                                      + cht.ed->m_soid.vwcmineb 
                                      + cht.ed->m_soid.vwcminec;
            //land should include both vegetation and ground.
            data["Evapotranspiration"] = cht.ed->m_l2a.eet;

            /* PFT dependent variables */
            double parDownSum = 0;
            double parAbsorbSum = 0;
            for(int pft=0;pft<NUM_PFT;pft++){
                char pft_chars[5];
                sprintf(pft_chars, "%d", pft);
                std::string pft_str = std::string(pft_chars);
                //c++0x equivalent: std::string pftvalue = std::to_string(pft);
                data["PFT" + pft_str]["VegCarbon"]["Leaf"] = cht.bd[pft].m_vegs.c[I_leaf];
                data["PFT" + pft_str]["VegCarbon"]["Stem"] = cht.bd[pft].m_vegs.c[I_stem];
                data["PFT" + pft_str]["VegCarbon"]["Root"] = cht.bd[pft].m_vegs.c[I_root];
                data["PFT" + pft_str]["VegStructuralNitrogen"]["Leaf"] = cht.bd[pft].m_vegs.strn[I_leaf];
                data["PFT" + pft_str]["VegStructuralNitrogen"]["Stem"] = cht.bd[pft].m_vegs.strn[I_stem];
                data["PFT" + pft_str]["VegStructuralNitrogen"]["Root"] = cht.bd[pft].m_vegs.strn[I_root];
                data["PFT" + pft_str]["GPPAll"] = cht.bd[pft].m_a2v.gppall;
                data["PFT" + pft_str]["NPPAll"] = cht.bd[pft].m_a2v.nppall;
                data["PFT" + pft_str]["GPPAllIgnoringNitrogen"] = cht.bd[pft].m_a2v.ingppall;
                data["PFT" + pft_str]["NPPAllIgnoringNitrogen"] = cht.bd[pft].m_a2v.innppall;
                data["PFT" + pft_str]["LitterfallCarbonAll"] = cht.bd[pft].m_v2soi.ltrfalcall;
                data["PFT" + pft_str]["LitterfallNitrogenAll"] = cht.bd[pft].m_v2soi.ltrfalnall;
                data["PFT" + pft_str]["PARDown"] = cht.ed[pft].m_a2v.pardown;
                parDownSum+=cht.ed[pft].m_a2v.pardown;
                data["PFT" + pft_str]["PARAbsorb"] = cht.ed[pft].m_a2v.parabsorb;
                parAbsorbSum+=cht.ed[pft].m_a2v.parabsorb;
            }
            data["PARAbsorbSum"] = parAbsorbSum;
            data["PARDownSum"] = parDownSum;
            data["GPPSum"] = cht.bdall->m_a2v.gppall;
            data["NPPSum"] = cht.bdall->m_a2v.nppall;

            /* Not PFT dependent */
            data["NitrogenUptakeAll"] = cht.bd->m_soi2v.snuptakeall;
            data["AvailableNitrogenSum"] = cht.bd->m_soid.avlnsum;
            data["OrganicNitrogenSum"] = cht.bd->m_soid.orgnsum;
            data["CarbonShallow"] = cht.bd->m_soid.shlwc;
            data["CarbonDeep"] = cht.bd->m_soid.deepc;
            data["CarbonMineralSum"] = cht.bd->m_soid.mineac
                                       + cht.bd->m_soid.minebc
                                       + cht.bd->m_soid.minecc;

            /* Unknown PFT dependence */
            data["MossdeathCarbon"] = cht.bdall->m_v2soi.mossdeathc;
            data["MossdeathNitrogen"] = cht.bdall->m_v2soi.mossdeathn;

            std::stringstream filename;
            filename.fill('0');
            filename << "/tmp/cal-dvmdostem/" << std::setw(4) << icalyr << "_" 
                     << std::setw(2) << im << ".json";

            out_stream.open(filename.str().c_str(), std::ofstream::out);

            out_stream << data << std::endl;

            out_stream.close();
        }

	    } // end of month loop

	    
	    
	    
  
		if (md->outRegn && outputyrind >=0){
			regnouter.outputCohortVars(outputyrind, cohortcount, 0);  // "0" implies good data
		}

		if(cht.md->consoledebug){
	    	cout <<"TEM " << cht.md->runstages <<" run: year "
	    	<<icalyr<<" @cohort "<<cohortcount+1<<"\n";

	    }

		// if EQ run,option for simulation break
  	   	if (cht.md->runeq) {
  	   		//cht.equiled = cht.testEquilibrium();
  	   		//if(cht.equiled )break;
  	   	}
        BOOST_LOG_SEV(glg, debug) << "Some end of year data for plotting...";

        if(this->get_calMode()){    
            Json::Value data;

            std::ofstream out_stream;

            /* Not PFT dependent */
            data["Year"] = icalyr;
            data["Snowfall"] = cht.edall->y_a2l.snfl;
            data["Rainfall"] = cht.edall->y_a2l.rnfl;
            data["WaterTable"] = cht.edall->y_sois.watertab;
            data["NitrogenUptakeAll"] = cht.bdall->y_soi2v.snuptakeall;
            data["AvailableNitrogenSum"] = cht.bdall->y_soid.avlnsum;
            data["OrganicNitrogenSum"] = cht.bdall->y_soid.orgnsum;
            data["CarbonShallow"] = cht.bdall->y_soid.shlwc;
            data["CarbonDeep"] = cht.bdall->y_soid.deepc;
            data["CarbonMineralSum"] = cht.bdall->y_soid.mineac
                                     + cht.bdall->y_soid.minebc
                                     + cht.bdall->y_soid.minecc;
            data["MossdeathCarbon"] = cht.bdall->y_v2soi.mossdeathc;
            data["MossdeathNitrogen"] = cht.bdall->y_v2soi.mossdeathn;

            for(int pft=0;pft<NUM_PFT;pft++){//NUM_PFT
                char pft_chars[5];
                sprintf(pft_chars, "%d", pft);
                std::string pft_str = std::string(pft_chars);
                //c++0x equivalent: std::string pftvalue = std::to_string(pft);

                data["PFT" + pft_str]["VegCarbon"]["Leaf"] = cht.bd[pft].y_vegs.c[I_leaf];
                data["PFT" + pft_str]["VegCarbon"]["Stem"] = cht.bd[pft].y_vegs.c[I_stem];
                data["PFT" + pft_str]["VegCarbon"]["Root"] = cht.bd[pft].y_vegs.c[I_root];
                data["PFT" + pft_str]["VegStructuralNitrogen"]["Leaf"] = cht.bd[pft].y_vegs.strn[I_leaf];
                data["PFT" + pft_str]["VegStructuralNitrogen"]["Stem"] = cht.bd[pft].y_vegs.strn[I_stem];
                data["PFT" + pft_str]["VegStructuralNitrogen"]["Root"] = cht.bd[pft].y_vegs.strn[I_root];
                data["PFT" + pft_str]["GPPAll"] = cht.bd[pft].y_a2v.gppall;
                data["PFT" + pft_str]["NPPAll"] = cht.bd[pft].y_a2v.nppall;
                data["PFT" + pft_str]["GPPAllIgnoringNitrogen"] = cht.bd[pft].y_a2v.ingppall;
                data["PFT" + pft_str]["NPPAllIgnoringNitrogen"] = cht.bd[pft].y_a2v.innppall;
                data["PFT" + pft_str]["PARDown"] = cht.ed[pft].y_a2v.pardown;
                data["PFT" + pft_str]["PARAbsorb"] = cht.ed[pft].y_a2v.parabsorb;
                data["PFT" + pft_str]["LitterfallCarbonAll"] = cht.bd[pft].y_v2soi.ltrfalcall;
                data["PFT" + pft_str]["LitterfallNitrogenAll"] = cht.bd[pft].y_v2soi.ltrfalnall;
                data["PFT" + pft_str]["PARDown"] = cht.ed[pft].y_a2v.pardown;
                data["PFT" + pft_str]["PARAbsorb"] = cht.ed[pft].y_a2v.parabsorb;
            }

            std::stringstream filename;
            filename.fill('0');
            filename << "/tmp/year-cal-dvmdostem/" << std::setw(4) << icalyr << ".json";

            out_stream.open(filename.str().c_str(), std::ofstream::out);

            out_stream << data << std::endl;

            out_stream.close();
        }
    } // end year loop

}

// run one cohort at one time-step (monthly)
void RunCohort::run_monthly(){

	 // timing
	 int yrindex = cht.timer->getCurrentYearIndex();     // starting from 0
	 cht.cd.year = cht.timer->getCalendarYear();

     int mnindex = cht.timer->getCurrentMonthIndex();    // 0 - 11
	 cht.cd.month = mnindex + 1;

     int dinmcurr = cht.timer->getDaysInMonth(mnindex);  // 28/30/31

     int outputyrind = cht.timer->getOutputYearIndex();  // starting from 0 (i.e., md->outstartyr)

     // driving data re-set when timer is ticking
     cht.prepareAllDrivingData();
	 cht.prepareDayDrivingData(yrindex, used_atmyr);

     // calling the core model modules
	 cht.updateMonthly(yrindex, mnindex, dinmcurr);

	 //'restart.nc' always output at the end of time-step (monthly)
	 resouter.outputVariables(cohortcount);

   	 // output module calling at end of year
	 if (md->outRegn && (outputyrind>=0 && cht.cd.month==11)){
		 regnouter.outputCohortVars(outputyrind, cohortcount, 0);  // "0" implies good data
	 }

};


////////////////////////////////////////////////////////////////////////
