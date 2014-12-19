/*
 * RunCohort.cpp
 *
 * Cohort initialization, run, and output
 *    Note: the output modules are put here, so can be flexible for outputs
 *
*/
#include <json/writer.h>

#include "RunCohort.h"
#include "../CalController.h"

#include "../TEMUtilityFunctions.h"
#include "../TEMLogger.h"
extern src::severity_logger< severity_level > glg;

RunCohort::RunCohort() {
  dstepcnt = 0;
  mstepcnt = 0;
  ystepcnt = 0;
  cohortcount = 0;   // counter for cohort have been run
}

RunCohort::~RunCohort() {
}

bool RunCohort::get_calMode() {
  return this->calMode;
}

void RunCohort::set_calMode(bool new_value) {
  this->calMode = new_value;
}

void RunCohort::setModelData(ModelData * mdp) {
  md = mdp;
}

int RunCohort::setup_cohort_ids(int cohort_idx) {

  NcFile chtid_file = temutil::open_ncfile(md->chtinputdir+"cohortid.nc");

  NcVar* v = NULL;

  this->chtids.push_back(MISSING_I);
  v = temutil::get_ncvar(chtid_file, "CHTID");
  v->set_cur(cohort_idx);
  v->get(&this->chtids.back(), 1);

  this->chtinitids.push_back(MISSING_I);
  v = temutil::get_ncvar(chtid_file, "INITCHTID");
  v->set_cur(cohort_idx);
  v->get(&this->chtinitids.back(), 1);

  this->chtgridids.push_back(MISSING_I);
  v = temutil::get_ncvar(chtid_file, "GRIDID");
  v->set_cur(cohort_idx);
  v->get(&chtgridids.back(), 1);

  this->chtclmids.push_back(MISSING_I);
  v = temutil::get_ncvar(chtid_file, "CLMID");
  v->set_cur(cohort_idx);
  v->get(&this->chtclmids.back(), 1);

  this->chtfireids.push_back(MISSING_I);
  v = temutil::get_ncvar(chtid_file, "FIREID");
  v->set_cur(cohort_idx);
  v->get(&this->chtfireids.back(), 1);

  this->chtvegids.push_back(MISSING_I);
  v = temutil::get_ncvar(chtid_file, "VEGID");
  v->set_cur(cohort_idx);
  v->get(&this->chtvegids.back(), 1);
  
  return 0;
}

int RunCohort::setup_initcohort_ids(int cohort_idx) {

  NcFile cohort_init_file = temutil::open_ncfile(md->initialfile);
  NcVar* v = temutil::get_ncvar(cohort_init_file, "CHTID");
  this->initids.push_back(MISSING_I);
  v->set_cur(cohort_idx);
  v->get(&this->initids.back(), 1);
  return 0;
}

int RunCohort::setup_clm_ids(int cohort_idx) {
  NcFile clm_id_file = temutil::open_ncfile(md->chtinputdir+"climate.nc");
  NcVar* v = temutil::get_ncvar(clm_id_file, "CLMID");
  this->clmids.push_back(MISSING_I);
  v->set_cur(cohort_idx);
  v->get(&this->clmids.back(),1);
  return 0;
}

int RunCohort::setup_veg_ids(int cohort_idx){
  NcFile veg_id_file = temutil::open_ncfile(md->chtinputdir+"vegetation.nc");
  NcVar* v = temutil::get_ncvar(veg_id_file, "VEGID");
  this->vegids.push_back(MISSING_I);
  v->set_cur(cohort_idx);
  v->get(&this->vegids.back(), 1);
  return 0;
}

int RunCohort::setup_fire_ids(int cohort_idx) {
  NcFile fire_id_file = temutil::open_ncfile(md->chtinputdir+"fire.nc");
  NcVar* v = temutil::get_ncvar(fire_id_file, "FIREID");
  this->fireids.push_back(MISSING_I);
  v->set_cur(cohort_idx);
  v->get(&this->fireids.back(), 1);
  return 0;
}

//reading cohort-level all data ids
int RunCohort::allchtids() {
  int error = 0;
  int id = MISSING_I;
  int id1 = MISSING_I;
  int id2 = MISSING_I;
  int id3 = MISSING_I;
  int id4 = MISSING_I;
  int id5 = MISSING_I;


  for (int i = 0; i < md->act_chtno; ++i) {
    this->setup_cohort_ids(i);
  }

  // from 'restart.nc' or 'sitein.nc'
  if (md->initmode>1) { // 'runeq' stage doesn't require initial file
    for (int i = 0; i < md->act_chtno; ++i) {
      this->setup_initcohort_ids(i);
    }
  }

  for (int i=0; i<md->act_clmno; i++) {
    // from 'climate.nc'
    this->setup_clm_ids(i);
  }

  // from 'vegetation.nc'
  for (int i=0; i<md->act_vegno; i++) {
    this->setup_veg_ids(i);
  }

  // from 'fire.nc'
  for (int i=0; i<md->act_fireno; i++) {
    this->setup_fire_ids(i);
  }

  return error;
};

// general initialization
void RunCohort::init() {
  BOOST_LOG_SEV(glg, info) << "In RunCohort::init(), setting a bunch of modules on/off";
  // switches of N cycles
  md->set_nfeed(true);
  md->set_avlnflg(true);
  md->set_baseline(false);
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

  cht.outbuffer.setRestartOutData(&resod);//restart output data sets connection
  // output operators
  regnouter.setOutData(&regnod);
  resouter.setRestartOutData(&resod);
}

//read-in one-timestep data for a cohort
int RunCohort::readData() {
  //reading the climate data
  cht.cd.act_atm_drv_yr = md->act_clmyr;

  // Read climate data from the netcdf file into data arrays...
  cht.load_climate_from_file(cht.cd.act_atm_drv_yr, clmrecno);

  // ??
  cht.cd.act_vegset = md->act_vegset;
  
  // Read vegetation community type data from netcdf file into data arrays...
  cht.load_vegdata_from_file(vegrecno);

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

  if (cht.cd.cmttype<10) {
    cht.chtlu.cmtcode = "CMT0"+ss.str();
  } else {
    cht.chtlu.cmtcode = "CMT"+ss.str();
  }

  cht.chtlu.init();   //put the parameter files in 'config/' with same directory of model

  //reading the fire occurence data from '.nc', if not FRI derived
  if (!md->get_friderived() && !md->runeq) {

    cht.cd.act_fireset = md->act_fireset;
    cht.load_fire_info_from_file(firerecno);

    if (md->useseverity) {
      cht.load_fire_severity_from_file(firerecno);
    }
  }

  return 0;
};

// re-initializing state variables for current cohort
int RunCohort::reinit() {
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
    //note: the cohort order in sitein.nc must be exactly same as
    //  cohort in cohortid.nc
    /*     int err=0;
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
void RunCohort::choose_run_stage_settings() {
  // Ends up as a null pointer if calibrationMode is off.
  boost::shared_ptr<CalController> calcontroller_ptr;

  if ( this->get_calMode() ) {
    calcontroller_ptr.reset( new CalController(&this->cht) );
  }

  //
  cht.timer->reset();

  //
  if(cht.md->runeq) {
    BOOST_LOG_SEV(glg, info) << "Starting a quick pre-run to get "
                             << "reasonably-good 'env' conditions, "
                             << "which may then be good for 'eq' run...";
    env_only_warmup(calcontroller_ptr);

    // In calibration mode, equlibrium stage starting with only env and bgc
    // switches on!
    if (calcontroller_ptr) {
      BOOST_LOG_SEV(glg, info) << "Pausing. Please check that the 'pre-run' "
                               << "data looks good.";
      
      calcontroller_ptr->pause();

      calcontroller_ptr->clear_and_create_json_storage();

      cht.timer->reset();
      BOOST_LOG_SEV(glg, info) << "Equilibrium stage. CALIBRATION MODE!";
      BOOST_LOG_SEV(glg, info) << "";
      md->set_envmodule(true);
      md->set_bgcmodule(true);
      md->set_nfeed(false);
      md->set_avlnflg(true);
      md->set_baseline(true);
      md->set_dsbmodule(false);
      md->set_dslmodule(false);
      md->set_dvmmodule(true);
      md->set_friderived(true);
    } else {
      // In equilibrium stage, turning all switches on
      cht.timer->reset();
      BOOST_LOG_SEV(glg, info) << "Equilibrium stage.";
      BOOST_LOG_SEV(glg, info) << "Turning ON all switches!";
      md->set_envmodule(true);
      md->set_bgcmodule(true);
      md->set_nfeed(true);
      md->set_avlnflg(true);
      md->set_baseline(true);
      md->set_dsbmodule(false);
      md->set_dslmodule(false);
      md->set_dvmmodule(true);
      md->set_friderived(true);
    }

    cht.timer->stageyrind = 0;
    cht.cd.yrsdist = 0;
    yrstart = 0;

    if (cht.gd->fri>0) {
      int nfri = fmax(MIN_EQ_YR/cht.gd->fri, 20);
      //20 FRI and within range of min. and max. MAX_EQ_YEAR
      nfri = fmin(nfri, MAX_EQ_YR/cht.gd->fri);
      yrend= nfri*cht.gd->fri-1;// ending just prior to the fire occurrency year
    } else {
      yrend = MAX_EQ_YR;
    }

    run_timeseries(calcontroller_ptr);
  }

  if(cht.md->runsp) {
    cht.timer->stageyrind = 0;
    cht.timer->eqend = true;
    used_atmyr = fmin(MAX_ATM_NOM_YR, cht.cd.act_atm_drv_yr);
    yrstart = cht.timer->spbegyr;
    yrend   = cht.timer->spendyr;
    //md->set_friderived(false);
    run_timeseries(calcontroller_ptr);
    if (calcontroller_ptr) {
      BOOST_LOG_SEV(glg, info) << "Pausing. Please check that the 'pre-run' "
                               << "data looks good.";
      
      calcontroller_ptr->pause();

      calcontroller_ptr->clear_and_create_json_storage();

      cht.timer->reset();
      BOOST_LOG_SEV(glg, info) << "Spinup stage. CALIBRATION MODE!";
      BOOST_LOG_SEV(glg, info) << "";
      md->set_envmodule(true);
      md->set_bgcmodule(true);
      md->set_nfeed(true);
      md->set_avlnflg(true);
      md->set_baseline(true);
      md->set_dsbmodule(false);
      md->set_dslmodule(true);
      md->set_dvmmodule(true);
      md->set_friderived(false);
    } else {
      // In spinup stage, turning all switches on
      cht.timer->reset();
      BOOST_LOG_SEV(glg, info) << "Spinup stage.";
      BOOST_LOG_SEV(glg, info) << "Turning ON all switches!";
      md->set_envmodule(true);
      md->set_bgcmodule(true);
      md->set_nfeed(true);
      md->set_avlnflg(true);
      md->set_baseline(true);
      md->set_dsbmodule(false);
      md->set_dslmodule(true);
      md->set_dvmmodule(true);
      md->set_friderived(false);
    }
  }

  if(cht.md->runtr) {
    cht.timer->stageyrind = 0;
    cht.timer->eqend = true;
    cht.timer->spend = true;
    used_atmyr = cht.cd.act_atm_drv_yr;
    yrstart = cht.timer->trbegyr;
    yrend   = cht.timer->trendyr;
    run_timeseries(calcontroller_ptr);
    if (calcontroller_ptr) {
      BOOST_LOG_SEV(glg, info) << "Pausing. Please check that the 'pre-run' "
                               << "data looks good.";
      
      calcontroller_ptr->pause();

      calcontroller_ptr->clear_and_create_json_storage();
      BOOST_LOG_SEV(glg, info) << "Transient stage. CALIBRATION MODE!";
      BOOST_LOG_SEV(glg, info) << "";
      md->set_envmodule(true);
      md->set_bgcmodule(true);
      md->set_nfeed(true);
      md->set_avlnflg(true);
      md->set_baseline(false);
      md->set_dsbmodule(false);
      md->set_dslmodule(true);
      md->set_dvmmodule(true);
      md->set_friderived(false);
    } else {
      BOOST_LOG_SEV(glg, info) << "Transient stage.";
      BOOST_LOG_SEV(glg, info) << "Turning ON all switches except baseline!";
      md->set_envmodule(true);
      md->set_bgcmodule(true);
      md->set_nfeed(true);
      md->set_avlnflg(true);
      md->set_baseline(false);
      md->set_dsbmodule(false);
      md->set_dslmodule(true);
      md->set_dvmmodule(true);
      md->set_friderived(false);
    }
  }

  if(cht.md->runsc) {
    cht.timer->stageyrind = 0;
    cht.timer->eqend = true;
    cht.timer->spend = true;
    cht.timer->trend = true;
    used_atmyr = cht.cd.act_atm_drv_yr;
    yrstart = cht.timer->scbegyr;
    yrend   = cht.timer->scendyr;
    run_timeseries(calcontroller_ptr);
    if (calcontroller_ptr) {
      BOOST_LOG_SEV(glg, info) << "Pausing. Please check that the 'pre-run' "
                               << "data looks good.";
      
      calcontroller_ptr->pause();

      calcontroller_ptr->clear_and_create_json_storage();
      BOOST_LOG_SEV(glg, info) << "Scenario stage. CALIBRATION MODE!";
      BOOST_LOG_SEV(glg, info) << "";
      md->set_envmodule(true);
      md->set_bgcmodule(true);
      md->set_nfeed(true);
      md->set_avlnflg(true);
      md->set_baseline(false);
      md->set_dsbmodule(false);
      md->set_dslmodule(true);
      md->set_dvmmodule(true);
      md->set_friderived(false);
    } else {
      BOOST_LOG_SEV(glg, info) << "Scenario stage.";
      BOOST_LOG_SEV(glg, info) << "Turning ON all switches except baseline!";
      md->set_envmodule(true);
      md->set_bgcmodule(true);
      md->set_nfeed(true);
      md->set_avlnflg(true);
      md->set_baseline(false);
      md->set_dsbmodule(false);
      md->set_dslmodule(true);
      md->set_dvmmodule(true);
      md->set_friderived(false);
    }
  }

  //'restart.nc' always output at the end of run-time
  resouter.outputVariables(cohortcount);
};

void RunCohort::env_only_warmup(boost::shared_ptr<CalController> calcontroller_ptr) {
  BOOST_LOG_SEV(glg, info) << "In RunCohort::env_only_warmup(...)."
                           << "Turn off all modules except env and run for 101 years.";
  //run model with "ENV module" only
  md->set_envmodule(true);
  md->set_bgcmodule(false);
  md->set_nfeed(false);
  md->set_avlnflg(false);
  md->set_baseline(false);
  md->set_dsbmodule(false);
  md->set_dslmodule(false);
  md->set_dvmmodule(false);
  cht.cd.yrsdist = 1000;
  yrstart = 0;
  yrend   = 100; // This actually results in running 101 years...
  run_timeseries(calcontroller_ptr);
  BOOST_LOG_SEV(glg, info) << "Completed 101 year env module only 'warm up' run.";
};


/** Run one cohort thru time series.
 *
 * i.e.:
 * for each year
 *     for each month
 */
void RunCohort::run_timeseries(boost::shared_ptr<CalController> calcontroller_ptr) {
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

    for (int im=0; im<12; im++) {

      int currmind=  im;
      cht.cd.month = im+1;
      int dinmcurr = cht.timer->getDaysInMonth(im);

      cht.updateMonthly(yrindex, currmind, dinmcurr);

      cht.timer->advanceOneMonth();

      // new stuff...
      this->write_monthly_outputs(yrindex, im);
      
      // site output module calling
      if (outputyrind >=0) {
        if (md->outSiteDay) {
          for (int id=0; id<dinmcurr; id++) {
            cht.outbuffer.envoddlyall[id].chtid = cht.cd.chtid;
            //this will output non-veg (multiple PFT) related variables
            envdlyouter.outputCohortEnvVars_dly(-1,
                                                &cht.outbuffer.envoddlyall[id],
                                                icalyr, im, id, dstepcnt);

            for (int ip=0; ip<NUM_PFT; ip++) {
              if (cht.cd.d_veg.vegcov[ip]>0.) {
                envdlyouter.outputCohortEnvVars_dly(ip, &cht.outbuffer.envoddly[ip][id],
                                                    icalyr, im, id, dstepcnt);
              }
            }

            dstepcnt++;
          }
        }

        //
        if (md->outSiteMonth) {
          dimmlyouter.outputCohortDimVars_mly(&cht.cd, mstepcnt);
          envmlyouter.outputCohortEnvVars_mly(-1, &cht.cd.m_snow, cht.edall,
                                              icalyr, im, mstepcnt);
          bgcmlyouter.outputCohortBgcVars_mly(-1, cht.bdall, cht.fd,
                                              icalyr, im, mstepcnt);

          for (int ip=0; ip<NUM_PFT; ip++) {
            if (cht.cd.m_veg.vegcov[ip]>0.) {
              envmlyouter.outputCohortEnvVars_mly(ip, &cht.cd.m_snow,
                                                  &cht.ed[ip], icalyr,
                                                  im, mstepcnt);
              bgcmlyouter.outputCohortBgcVars_mly(ip, &cht.bd[ip], cht.fd,
                                                  icalyr, im, mstepcnt);
            }
          }

          mstepcnt++;
        }

        //
        if (md->outSiteYear && im==11) {
          dimylyouter.outputCohortDimVars_yly(&cht.cd, ystepcnt);
          envylyouter.outputCohortEnvVars_yly(-1, &cht.cd.y_snow, cht.edall,
                                              icalyr, ystepcnt);
          bgcylyouter.outputCohortBgcVars_yly(-1, cht.bdall, cht.fd,
                                              icalyr, ystepcnt);

          for (int ip=0; ip<NUM_PFT; ip++) {
            if (cht.cd.y_veg.vegcov[ip]>0.) {
              envylyouter.outputCohortEnvVars_yly(ip, &cht.cd.y_snow,
                                                  &cht.ed[ip],
                                                  icalyr, ystepcnt);
              bgcylyouter.outputCohortBgcVars_yly(ip, &cht.bd[ip], cht.fd,
                                                  icalyr, ystepcnt);
            }
          }

          ystepcnt++;
        }
      } // end of site calling output modules

      /*if(this->get_calMode()) {
        BOOST_LOG_SEV(glg, debug) << "Send monthly calibration data to json files...";
        this->output_caljson_monthly(icalyr, im);
      }*/

    } // end of month loop

    if (md->outRegn && outputyrind >=0) {
      regnouter.outputCohortVars(outputyrind, cohortcount, 0);  // "0" implies good data
    }

    BOOST_LOG_SEV(glg, note) << "TEM " << cht.md->runstages << " run: year "
                             << icalyr << " @cohort " << cohortcount + 1;

    // if EQ run,option for simulation break
    if (cht.md->runeq) {
      //cht.equiled = cht.testEquilibrium();
      //if(cht.equiled )break;
    }

    if(this->get_calMode()) {
      BOOST_LOG_SEV(glg, debug) << "Send yearly calibration data to json files...";
      this->output_caljson_yearly(icalyr);
    }

  } // end year loop
}

void RunCohort::output_caljson_yearly(int year) {
  Json::Value data;
  std::ofstream out_stream;
  /* Not PFT dependent */
  data["Year"] = year;
  data["TAir"] = cht.edall->y_atms.ta;
  data["Snowfall"] = cht.edall->y_a2l.snfl;
  data["Rainfall"] = cht.edall->y_a2l.rnfl;
  data["WaterTable"] = cht.edall->y_sois.watertab;
  data["ActiveLayerDepth"]= cht.edall-> y_soid.ald;
  data["CO2"] = cht.edall->y_atms.co2;
  data["VPD"] = cht.edall->y_atmd.vpd;
  data["EET"] = cht.edall->y_l2a.eet;
  data["PET"] = cht.edall->y_l2a.pet;
  data["PAR"] = cht.edall->y_a2l.par;
  data["PARAbsorb"] = cht.edall->y_a2v.parabsorb;

  data["VWCShlw"] = cht.edall->y_soid.vwcshlw;
  data["VWCDeep"] = cht.edall->y_soid.vwcdeep;
  data["VWCMineA"] = cht.edall->y_soid.vwcminea;
  data["VWCMineB"] = cht.edall->y_soid.vwcmineb;
  data["VWCMineC"] = cht.edall->y_soid.vwcminec;
  data["TShlw"] = cht.edall->y_soid.tshlw;
  data["TDeep"] = cht.edall->y_soid.tdeep;
  data["TMineA"] = cht.edall->y_soid.tminea;
  data["TMineB"] = cht.edall->y_soid.tmineb;
  data["TMineC"] = cht.edall->y_soid.tminec;

  data["StNitrogenUptakeAll"] = cht.bdall->y_soi2v.snuptakeall;
  data["InNitrogenUptakeAll"] = cht.bdall->y_soi2v.innuptake;
  data["AvailableNitrogenSum"] = cht.bdall->y_soid.avlnsum;
  data["OrganicNitrogenSum"] = cht.bdall->y_soid.orgnsum;
  data["CarbonShallow"] = cht.bdall->y_soid.shlwc;
  data["CarbonDeep"] = cht.bdall->y_soid.deepc;
  data["CarbonMineralSum"] = cht.bdall->y_soid.mineac
                             + cht.bdall->y_soid.minebc
                             + cht.bdall->y_soid.minecc;
  data["MossdeathCarbon"] = cht.bdall->y_sois.dmossc;
  data["MossdeathNitrogen"] = cht.bdall->y_sois.dmossn;
  data["NetNMin"] = cht.bdall->y_soi2soi.netnminsum;
  data["NetNImmob"] = cht.bdall->y_soi2soi.nimmobsum;
  data["OrgNInput"] = cht.bdall->y_a2soi.orgninput;
  data["AvlNInput"] = cht.bdall->y_a2soi.avlninput;
  data["AvlNLost"] = cht.bdall->y_soi2l.avlnlost;
  data["RHraw"] = cht.bdall->y_soi2a.rhrawcsum;
  data["RHsoma"] = cht.bdall->y_soi2a.rhsomasum;
  data["RHsompr"] = cht.bdall->y_soi2a.rhsomprsum;
  data["RHsomcr"] = cht.bdall->y_soi2a.rhsomcrsum;
  data["RH"] = cht.bdall->y_soi2a.rhtot;
  
  data["Burnthick"] = cht.fd->fire_soid.burnthick;
  data["BurnVeg2AirC"] = cht.fd->fire_v2a.orgc;
  data["BurnVeg2AirN"] = cht.fd->fire_v2a.orgn;
  data["BurnVeg2SoiAbvVegC"] = cht.fd->fire_v2soi.abvc;
  data["BurnVeg2SoiBlwVegC"] = cht.fd->fire_v2soi.blwc;
  data["BurnVeg2SoiAbvVegN"] = cht.fd->fire_v2soi.abvn;
  data["BurnVeg2SoiBlwVegN"] = cht.fd->fire_v2soi.blwn;
  data["BurnSoi2AirC"] = cht.fd->fire_soi2a.orgc;
  data["BurnSoi2AirN"] = cht.fd->fire_soi2a.orgn;


  for(int pft=0; pft<NUM_PFT; pft++) { //NUM_PFT
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
    data["PFT" + pft_str]["VegLabileNitrogen"] = cht.bd[pft].y_vegs.labn;
    data["PFT" + pft_str]["GPPAll"] = cht.bd[pft].y_a2v.gppall;
    data["PFT" + pft_str]["NPPAll"] = cht.bd[pft].y_a2v.nppall;
    data["PFT" + pft_str]["GPPAllIgnoringNitrogen"] = cht.bd[pft].y_a2v.ingppall;
    data["PFT" + pft_str]["NPPAllIgnoringNitrogen"] = cht.bd[pft].y_a2v.innppall;
    data["PFT" + pft_str]["PARDown"] = cht.ed[pft].y_a2v.pardown;
    data["PFT" + pft_str]["PARAbsorb"] = cht.ed[pft].y_a2v.parabsorb;
    data["PFT" + pft_str]["LitterfallCarbonAll"] = cht.bd[pft].y_v2soi.ltrfalcall;
    data["PFT" + pft_str]["LitterfallNitrogenPFT"] = cht.bd[pft].y_v2soi.ltrfalnall;
    data["PFT" + pft_str]["LitterfallNitrogen"]["Leaf"] = cht.bd[pft].y_v2soi.ltrfaln[I_leaf];
    data["PFT" + pft_str]["LitterfallNitrogen"]["Stem"] = cht.bd[pft].y_v2soi.ltrfaln[I_stem];
    data["PFT" + pft_str]["LitterfallNitrogen"]["Root"] = cht.bd[pft].y_v2soi.ltrfaln[I_root];
    data["PFT" + pft_str]["PARDown"] = cht.ed[pft].y_a2v.pardown;
    data["PFT" + pft_str]["PARAbsorb"] = cht.ed[pft].y_a2v.parabsorb;
    data["PFT" + pft_str]["StNitrogenUptake"] = cht.bd[pft].y_soi2v.snuptakeall;
    data["PFT" + pft_str]["InNitrogenUptake"] = cht.bd[pft].y_soi2v.innuptake;
    data["PFT" + pft_str]["LuxNitrogenUptake"] = cht.bd[pft].y_soi2v.lnuptake;
    data["PFT" + pft_str]["TotNitrogenUptake"] = cht.bd[pft].y_soi2v.snuptakeall + cht.bd[pft].y_soi2v.lnuptake;
  }

  std::stringstream filename;
  filename.fill('0');
  filename << "/tmp/year-cal-dvmdostem/" << std::setw(5) << year << ".json";
  out_stream.open(filename.str().c_str(), std::ofstream::out);
  out_stream << data << std::endl;
  out_stream.close();

}

void RunCohort::output_caljson_monthly(int year, int month) {

  Json::Value data;
  std::ofstream out_stream;
  data["Year"] = year;
  data["Month"] = month;
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
  //m_soid.vwc[] has approx 23 values
  //  I assume these are summed in the following.
  data["VWCOrganicLayer"] = cht.ed->m_soid.vwcshlw
                            + cht.ed->m_soid.vwcdeep;
  data["VWCMineralLayer"] = cht.ed->m_soid.vwcminea
                            + cht.ed->m_soid.vwcmineb
                            + cht.ed->m_soid.vwcminec;
  //land should include both vegetation and ground.
  data["Evapotranspiration"] = cht.ed->m_l2a.eet;
  /* PFT dependent variables */
  double parDownSum = 0;
  double parAbsorbSum = 0;

  for(int pft=0; pft<NUM_PFT; pft++) {
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
    data["PFT" + pft_str]["NitrogenUptake"] = cht.bd[pft].m_soi2v.snuptakeall;
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
  filename << "/tmp/cal-dvmdostem/" << std::setw(5) << year << "_"
           << std::setw(2) << month << ".json";
  out_stream.open(filename.str().c_str(), std::ofstream::out);
  out_stream << data << std::endl;
  out_stream.close();


}

// run one cohort at one time-step (monthly)
void RunCohort::advance_one_month() {
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
  if (md->outRegn && (outputyrind>=0 && cht.cd.month==11)) {
    regnouter.outputCohortVars(outputyrind, cohortcount, 0);  // "0" implies good data
  }
};
void RunCohort::write_monthly_outputs(int year_idx, int month_idx) {

  //  ///////////////////////////////////////////////
  //   NEW OUTPUT STUFF
  //  ///////////////////////////////////////////////
  //
  //  /*
  //  Concerns
  //   - need to open a fresh file at begining of run and define vars/dims
  //     if an appropriate one doesn;t exist
  //   - problem assigning start and count arrays
  //   - need to figure out whre to grab the right data
  //   - may need mapped arrays to efficiently assign some values that are 
  //     laid out very differently in memory than we want them in the file?
  //   - need to figure out what to do with the Y,X dimensions
  //  */

  BOOST_LOG_SEV(glg, note) << "Starting NEW OUTPUT WRITE PROCESS";

  // get a file handle
  int ncid;
  temutil::nc( nc_open("general-outputs-monthly.nc", NC_WRITE, &ncid) );

  // get dimension ids (nc_inq_dimid family)
  int unlimitedD;  // unlimited dimension
  int timeD;
  int pftD;
  int xD;
  int yD;

  temutil::nc( nc_inq_unlimdim(ncid, &unlimitedD) );
  temutil::nc( nc_inq_dimid(ncid, "time", &timeD) );
  temutil::nc( nc_inq_dimid(ncid, "pft", &pftD) );
  temutil::nc( nc_inq_dimid(ncid, "y", &yD) );
  temutil::nc( nc_inq_dimid(ncid, "x", &xD) );


  // Check file validity
  if (unlimitedD != timeD) {
    BOOST_LOG_SEV(glg, err) << "Problem! The record dimension is not the same as the time dimension!";
  }

  // get variable IDs (nc_inq_varid family)
  int org_shlw_thicknessV;
  int veg_fractionV;
  int vegcV;
  int growstartV;

  temutil::nc( nc_inq_varid(ncid, "org_shlw_thickness", &org_shlw_thicknessV) );
  temutil::nc( nc_inq_varid(ncid, "veg_fraction", &veg_fractionV) );
  temutil::nc( nc_inq_varid(ncid, "vegc", &vegcV) );
  temutil::nc( nc_inq_varid(ncid, "growstart", &growstartV) );

  /* 4-D variables (time, pft, y, x) */
  // nc_put needs: (fileid, varid, start[], count[], datarray)

  // corner of dataset to start in
  static size_t corner[4];
  corner[0] = (year_idx * 12) + month_idx;  // (timestep) this current timestep
  corner[1] = 0;                            // (pft) beginning - will write all pfts w/o loop
  corner[2] = this->cht.cd.chtid;           // (y) junk!: set x,y both to chtid
  corner[3] = this->cht.cd.chtid;           // (x)

  // one timestep, all pfts, one spatial location
  static size_t count[] = {1, NUM_PFT, 1, 1}; // number or records along each dim

  std::cout << "Corner/count arrays: \n";
  for (int i=0; i < 4; ++i) {
    std::cout << "corner["<<i<<"]: " << corner[i] << "  count["<<i<<"]: " << count[i] << std::endl;
  }

  // If the variable we are interested in is not stored as an array, one value
  // for each pft, then we have to collect that data into a temporary location
  // so we can write it all in one chunk
  double tempdata[NUM_PFT];
  for (int i=0; i < NUM_PFT; ++i) {
    tempdata[i] = this->cht.bd[i].m_vegs.call;
  }

  temutil::nc( nc_put_vara_double(ncid, vegcV, corner, count, tempdata) );
  temutil::nc( nc_put_vara_double(ncid, veg_fractionV, corner, count, this->cht.cd.m_veg.vegcov) );

  double tempdata2[NUM_PFT];
  for (int i=0; i < NUM_PFT; ++i) {
    tempdata2[i] = this->cht.ed[i].m_soid.rtdpgrowstart;
  }
  temutil::nc( nc_put_vara_double(ncid, growstartV, corner, count, tempdata2) );


  //  GROWSTART   - (1) growing starting day
  //  GROWEND     - (2) growing ending day
  //  VEGFRAC     - (3) each pft's land coverage fraction (m2/m2)
  //  VEGAGE      - (4) each pft's age (years)
  //  LAI         - (5) each pft's LAI (m2/m2)
  //  VEGC        - (6) each pft's total veg. biomass C (gC/m2)
  //  LEAFC       - (7) each pft's leaf biomass C (gC/m2)
  //  STEMC       - (8) each pft's stem biomass C (gC/m2)
  //  ROOTC       - (9) each pft's root biomass C (gC/m2)



  /* 3-D variables (time, y, x) */
  




  temutil::nc( nc_close(ncid) );
}



