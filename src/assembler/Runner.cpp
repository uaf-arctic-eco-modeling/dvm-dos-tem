#include <string>
#include <algorithm>
#include <json/writer.h>


#ifdef WITHMPI
#include <mpi.h>
#include "../parallel-code/Master.h"
#include "../parallel-code/Slave.h"
#include "../inc/tbc_mpi_constants.h"
#endif

#include "Runner.h"
#include "../runmodule/Cohort.h"
#include "../TEMUtilityFunctions.h"
#include "../TEMLogger.h"
#include "../util/tbc-debug-util.h"

extern src::severity_logger< severity_level > glg;

Runner::Runner(): calibrationMode(false) {
  chtid = -1;
  error = 0;
  BOOST_LOG_SEV(glg, debug) << "RUNNER mostly empty default ctor.";
};


Runner::Runner(ModelData mdldata, int y, int x):
    calibrationMode(false), y(y), x(x) {

  BOOST_LOG_SEV(glg, note) << "RUNNER Constructing a Runner, new style, with ctor-"
                           << "injected ModelData, and for explicit (y,x) "
                           << "position w/in the input data region.";
  this->md = mdldata;
  this->cohort = Cohort(y, x, &mdldata); // explicitly constructed cohort...

  // within-grid cohort-level aggregated 'ed' (i.e. 'edall in 'cht')
  BOOST_LOG_SEV(glg, debug) << "Create some empty containers for 'cohort-level "
                            << "aggregations of 'ed', (i.e. 'edall in 'cohort')";
  this->chted = EnvData();
  this->chtbd = BgcData();
  this->chtfd = FirData();
  
  // Now give the cohort pointers to these containers.
  this->cohort.setProcessData(&this->chted, &this->chtbd, &this->chtfd);

}


Runner::~Runner() {
};

void Runner::modeldata_module_settings_from_args(const ArgHandler &args) {
//  this->md.set_envmodule(args.getEnv());
//  this->md.set_bgcmodule(args.getBgc());
//  this->md.set_dvmmodule(args.getDvm());
}

void Runner::set_calibrationMode(bool new_setting) {
  BOOST_LOG_SEV(glg, debug) << "Turning runner instance's calibrationMode to "
                            << new_setting;
  this->runcht.set_calMode(new_setting);  // RunCohort's calibration status shadows Runner!
  this->calibrationMode = new_setting;
}

bool Runner::get_calibrationMode() {
  return this->calibrationMode;
}

void Runner::initInput(const string &controlfile, const string &loop_order) {

  // Read controlfile. Sets a bunch of data in the ModelData pointer
  md.updateFromControlFile(controlfile);

  BOOST_LOG_SEV(glg, debug) << "Done with the parse_control_file(..) function..";

  if (md.runmode.compare("single") == 0) {
    BOOST_LOG_SEV(glg, debug) << "In single site mode...no loop orders to set? Nothing to do?";
  } else if (md.runmode.compare("multi") == 0) {
    BOOST_LOG_SEV(glg, debug) << "In multi-site mode, gotta set the loop order!";
    if (loop_order.compare("time-major") == 0) {
      md.loop_order = "time-major";
    } else if (loop_order.compare("space-major") == 0){
      md.loop_order = "space-major";
    } else {
      BOOST_LOG_SEV(glg, fatal) << "Invalid runmode and loop-order combo: "
                                << runmode << ", " << loop_order << ". "
                                << "(controls time vs space major and single vs multi site runs)";
      exit(-1);
    }
  }

  BOOST_LOG_SEV(glg, debug) << "Done reading in the config file. twiddling some settings...";
  md.checking4run();
  // timer initialization
  timer.setModeldata(&md);

  // these are likely redundant??
  md.setup_act_co2yr_from_file();
  regionaldata.set_act_co2yr_from_file(md.reginputdir + "co2.nc");

  //grid-level input
  md.setup_griddata_from_files();

  BOOST_LOG_SEV(glg, warn) << "Taking care of cohort-level inputs...??";
  md.set_chtids_from_file();
  md.set_initial_cohort_from_file();
  md.set_climate_from_file();
  md.set_veg_from_file();
  md.set_fire_from_file();

  runchtlist.clear();

  if (md.runmode.compare("multi") == 0) {
    BOOST_LOG_SEV(glg, info) << "Multi-site running mode! Creating the cohort list...";
    createCohortList4Run(); // the running cohort list, if multple-cohort run mode on
  } else if (md.runmode.compare("single") == 0) {
    BOOST_LOG_SEV(glg, warn) << "Single-site running mode! CHTID and INITCHTID "
                             << "are " << chtid << ". Be sure they exist and "
                             << "are consistent in 'cohortid.nc'!";
    runchtlist.push_back(chtid);
  } else {
    BOOST_LOG_SEV(glg, fatal) << "INVALID ModelData.runmode!: " << md.runmode;
    exit(-1);
  }

  //initial conditions
  if (md.initmode==3) {
    if(md.runeq) {
      BOOST_LOG_SEV(glg, warn) << "Cannot set initmode to 'restart' for equlibrium run-stage";
      BOOST_LOG_SEV(glg, warn) << "Reset initmode to 'default'...";
      md.initmode=1;
    } else {
      runcht.resinputer.init(md.initialfile);
    }
  } else if (md.initmode==2) {
    // will add later
  } else if (md.initmode==1) {
    // initial condition from 'chtlup'
    BOOST_LOG_SEV(glg, info) << "Using initial conditions from default for each 'cmttype'";
  }

  // pass the 'md' switches/controls/options to two major running modules 'rungrd' and 'runcht'
  rungrd.setModelData(&md);
  runcht.setModelData(&md);
};

//output setting-up
void Runner::initOutput() {
  string stage = "-"+md.runstages;

  // 1)for general outputs
  if (md.runmode.compare("single") == 0) {   //very detailed output for ONE cohort ONLY
    string dimfname ="";
    string envfname ="";
    string bgcfname ="";

    if (md.outSiteDay) {
      envfname = md.outputdir+"cmtenv_dly"+stage+".nc";
      runcht.envdlyouter.init(envfname); // set netcdf files for output
    }

    if (md.outSiteMonth) {
      dimfname = md.outputdir+"cmtdim_mly"+stage+".nc";
      runcht.dimmlyouter.init(dimfname); // set netcdf files for output
      envfname = md.outputdir+"cmtenv_mly"+stage+".nc";
      runcht.envmlyouter.init(envfname); // set netcdf files for output
      bgcfname = md.outputdir+"cmtbgc_mly"+stage+".nc";
      runcht.bgcmlyouter.init(bgcfname); // set netcdf files for output
    }

    if (md.outSiteYear) {
      dimfname = md.outputdir+"cmtdim_yly"+stage+".nc";
      runcht.dimylyouter.init(dimfname); // set netcdf files for output
      envfname = md.outputdir+"cmtenv_yly"+stage+".nc";
      runcht.envylyouter.init(envfname); // set netcdf files for output
      bgcfname = md.outputdir+"cmtbgc_yly"+stage+".nc";
      runcht.bgcylyouter.init(bgcfname); // set netcdf files for output
    }
  } else if ( (md.runmode.compare("multi") == 0) && (!md.runeq) ) {
    BOOST_LOG_SEV(glg, note) << "Outputting regional data! We are in multisite mode and NOT eq stage!";
    // output options (switches)
    md.outRegn      = true;
    md.outSiteYear  = false;
    md.outSiteDay   = false;
    md.outSiteMonth = false;
  } else {
    BOOST_LOG_SEV(glg, err) << "What mode is this?? How did we get here??";
    md.outRegn=false;
    md.outSiteYear=false;
    md.outSiteDay=false;
    md.outSiteMonth=false;
  }

  // 2) summarized output by a list of variables
  BOOST_LOG_SEV(glg, note) << "Output regional stuff (md.outRegn)?: " << md.outRegn;
  if (md.outRegn) {
    // varlist
    string outlistfile = "config/outvarlist.txt";
    createOutvarList(outlistfile);
    // output years
    int maxoutyrs = 0;

    if (md.runsp) {
      maxoutyrs += MAX_SP_YR;
    }

    if (md.runtr) {
      maxoutyrs += MAX_TR_YR;
    }

    if (md.runsc) {
      maxoutyrs += MAX_SC_YR;
    }

    runcht.regnouter.setOutData(&runcht.regnod);
    runcht.regnouter.init(md.outputdir, stage, maxoutyrs);   //set netcdf files for output, note NOT output from "eq" run
  }

  // 3)for restart.nc outputs
  runcht.resouter.init(md.outputdir, stage); //define netcdf file for restart output
};

void Runner::initialize_regional_data(std::string filename) {
  BOOST_LOG_SEV(glg, note) << "Initializing this Runner's RegionData structure.";

  // set the RegionData's notion of "actual co2years"??
  this->regionaldata.set_act_co2yr_from_file(filename);

  // make RegionData load data from a file into its arrays...
  this->regionaldata.setup_co2_and_yr_from_file(filename);
  
  // empty (Region::Region())
  
  // Tell RegionData what its own first co2 value is??
  this->regionaldata.initco2 = this->regionaldata.co2[0];

}
//set up data connection and data pointer initialization
void Runner::setupData() {
  BOOST_LOG_SEV(glg, note) << " Some message while setting up the data...";
  // input data connection
  rungrd.grid.setRegionData(&this->regionaldata);
  runcht.cht.setModelData(&md);
  runcht.cht.setTime(&timer);
  runcht.cht.setInputData(&this->regionaldata, &rungrd.grid.gd);
  // process data connection
  runcht.cht.setProcessData(&chted, &chtbd, &chtfd);  //
  // initializing pointers data connection and TEM module switches
  runcht.init();
  //initializing pointers used in called modules in one 'cht'
  runcht.cht.initSubmodules();
};

void Runner::setupIDs() {
  BOOST_LOG_NAMED_SCOPE("setup");
  // all grid data ids
  error = rungrd.allgridids();

  if (error != 0) {
    BOOST_LOG_SEV(glg, fatal) << "Problem reading grid-level data IDs in Runner::setupIDs";
    exit(-1);
  }

  // all cohort data ids
  error = runcht.allchtids();

  if (error != 0) {
    BOOST_LOG_SEV(glg, fatal) << "Problem reading cohort-level data IDs in Runner::setupIDs";
    exit(-1);
  }

  // 1) assign grid-level data IDs (in 'grid.nc') for 'chtid' in 'cohortid.nc':
  //       related key - 'GRIDID'
  // note: one 'chtid' only has one set of grid-level data IDs,
  //       while not in reverse
  unsigned int icht;
  unsigned int igrd;
  vector<int>:: iterator it;

  for (icht=0; icht<runcht.chtids.size(); icht++) {
    int gridid = runcht.chtgridids.at(icht);
    it = find(rungrd.grdids.begin(), rungrd.grdids.end(), gridid);

    if (it != rungrd.grdids.end() ||
        (it == rungrd.grdids.end() && *it == gridid)) {
      igrd = (unsigned int)(it-rungrd.grdids.begin());
      runcht.chtdrainids.push_back(rungrd.grddrgids.at(igrd));
      runcht.chtsoilids.push_back(rungrd.grdsoilids.at(igrd));
      runcht.chtgfireids.push_back(rungrd.grdfireids.at(igrd));
    }
  }

  // 2) output the record no. for all data IDs, in the 'runchtlist.nc' so that
  //       read-data doesn't need to
  // search each IDs in the .nc files during computation, which may cost a lot
  //       of computation time
  unsigned int jcht;
  unsigned int jdata;
  vector<int>::iterator jt;
  unsigned int jj;

  for (jj=0; jj<runchtlist.size(); jj++) {
    int ichtid = runchtlist.at(jj);
    jt   = find(runcht.chtids.begin(), runcht.chtids.end(), ichtid);
    jcht = (unsigned int)(jt - runcht.chtids.begin());

    if (jcht>=runcht.chtids.size()) {
      BOOST_LOG_SEV(glg, fatal) << "Cohort: "<<ichtid
                                <<" is not in datacht/cohortid.nc";
      exit(-1);
    }

    // grid record no. (in 'grid.nc') for 'chtid' (needed for lat/lon)
    jt = find(rungrd.grdids.begin(), rungrd.grdids.end(),
              runcht.chtgridids.at(jcht));
    jdata = (int)(jt - rungrd.grdids.begin());

    if (jdata>=rungrd.grdids.size()) {
      BOOST_LOG_SEV(glg, fatal) << "GridID: " << runcht.chtgridids.at(jcht)
                                << "for Cohort: " << ichtid
                                << " is not in datagrid/grid.nc";
      exit(-1);
    }

    reclistgrid.push_back(jdata);

    // jdata?? hopefully it is the "record" or "record id" in the NC file...
    std::pair<float, float> latlon = temutil::get_location(md.grdinputdir + "grid.nc", jdata);
    runchtlats.push_back(latlon.first);
    runchtlons.push_back(latlon.second);


    // drainage-type record no. (in 'drainage.nc') for 'chtid'
    jt = find(rungrd.drainids.begin(), rungrd.drainids.end(),
              runcht.chtdrainids.at(jcht));
    jdata = (int)(jt - rungrd.drainids.begin());

    if (jdata>=rungrd.drainids.size()) {
      cout<<"DRAINAGEID: "<<runcht.chtdrainids.at(jcht)
          <<" for Cohort: "<<ichtid<<" is not in datagrid/drainage.nc";
      exit(-1);
    }

    reclistdrain.push_back(jdata);
    // soil-texture record no. (in 'soiltexture.nc') for 'chtid'
    jt = find(rungrd.soilids.begin(), rungrd.soilids.end(),
              runcht.chtsoilids.at(jcht));
    jdata = (int)(jt - rungrd.soilids.begin());

    if (jdata>=rungrd.soilids.size()) {
      cout<<"SOILID: "<<runcht.chtsoilids.at(jcht)
          <<" for Cohort: "<<ichtid<<" is not in datagrid/drainage.nc";
      exit(-1);
    }

    reclistsoil.push_back(jdata);
    // grid-fire-statistics ('gfire') record no. (in 'firestatistics.nc')
    //    for 'chtid'
    jt = find(rungrd.gfireids.begin(), rungrd.gfireids.end(),
              runcht.chtgfireids.at(jcht));
    jdata = (int)(jt - rungrd.gfireids.begin());

    if (jdata>=rungrd.gfireids.size()) {
      cout<<"GFIREID: "<<runcht.chtfireids.at(jcht)
          <<" for Cohort: "<<ichtid<<" is not in datagrid/firestatistics.nc";
      exit(-1);
    }

    reclistgfire.push_back(jdata);

    // initial data record no. (in 'restart.nc' or 'sitein.nc', or '-1')
    //   for 'chtid'
    if (md.initmode>1) {
      jt = find(runcht.initids.begin(), runcht.initids.end(),
                runcht.chtinitids.at(jcht));
      jdata = (int)(jt - runcht.initids.begin());

      if (jdata>=runcht.initids.size()) {
        cout<<"initial/restart CHTID: "<<runcht.chtinitids.at(jcht)
            <<" for Cohort: "<<ichtid<<" is not in "<<md.initialfile;
        exit(-1);
      }

      reclistinit.push_back(jdata);
    } else {
      reclistinit.push_back(-1);
    }

    // climate data record no. (in 'climate.nc') for 'chtid'
    jt = find(runcht.clmids.begin(), runcht.clmids.end(),
              runcht.chtclmids.at(jcht));
    jdata = (int)(jt - runcht.clmids.begin());

    if (jdata>=runcht.clmids.size()) {
      cout<<"CLMID: "<<runcht.chtclmids.at(jcht)
          <<" for Cohort: "<<ichtid<<" is not in datacht/climate.nc";
      exit(-1);
    }

    reclistclm.push_back(jdata);
    // vegetation community data record no. (in 'vegetation.nc') for 'chtid'
    jt = find(runcht.vegids.begin(), runcht.vegids.end(),
              runcht.chtvegids.at(jcht));
    jdata = (int)(jt - runcht.vegids.begin());

    if (jdata>=runcht.vegids.size()) {
      cout<<"VEGID: "<<runcht.chtvegids.at(jcht)
          <<" for Cohort: "<<ichtid<<" is not in datacht/vegetation.nc";
      exit(-1);
    }

    reclistveg.push_back(jdata);
    // fire data record no. (in 'fire.nc') for 'chtid'
    jt = find(runcht.fireids.begin(), runcht.fireids.end(),
              runcht.chtfireids.at(jcht));
    jdata = (int)(jt - runcht.fireids.begin());

    if (jdata>=runcht.fireids.size()) {
      cout<<"FIREID: "<<runcht.chtfireids.at(jcht)
          <<" for Cohort: "<<ichtid<<" is not in datacht/fire.nc";
      exit(-1);
    }

    reclistfire.push_back(jdata);
  }
};

/** rough draft - run some env-only warmup years...*/
void Runner::quick_env_only_warmup_run(int year_start, int year_end, boost::shared_ptr<CalController> calcontroller_ptr) {
  BOOST_LOG_SEV(glg, info) << "Starting a quick pre-run to get "
                           << "reasonably-good 'env' conditions, "
                           << "which may then be good for 'eq' run...";

  BOOST_LOG_SEV(glg, info) << "Turn off all modules except 'env'.";
  this->md.set_envmodule(true);
  this->md.set_bgcmodule(false);
  this->md.set_nfeed(false);
  this->md.set_avlnflg(false);
  this->md.set_baseline(false);
  this->md.set_dsbmodule(false);
  this->md.set_dslmodule(false);
  this->md.set_dvmmodule(false);

  BOOST_LOG_SEV(glg, info) << "Set years since disturbance (1000)";
  this->cohort.cd.yrsdist = 1000;

  BOOST_LOG_SEV(glg, info) << "Run years " << year_start << " to " << year_end;
  this->run_years(year_start, year_end, "", calcontroller_ptr);

  BOOST_LOG_SEV(glg, info) << "Completed env module only 'warm up' run.";
}



void Runner::run_years(int start_year, int end_year, const std::string& stage,
    boost::shared_ptr<CalController> cal_ctrl_ptr) {

  /** YEAR TIMESTEP LOOP */
  for (int iy = start_year; iy < end_year; ++iy) {

    /* Interpolate all the monthly values...? */
    //cohort.prepareDayDrivingData(iy, 0);
    this->cohort.climate.preapre_daily_driving_data(iy, stage);


    if (cal_ctrl_ptr) { // should be null unless we are in "calibration mode"

      // Run any pre-configured directives
      cal_ctrl_ptr->run_config(iy);

      // See if a signal has arrived (possibly from user
      // hitting Ctrl-C) and if so, stop the simulation
      // and drop into the calibration "shell".
      cal_ctrl_ptr->check_for_signals();

    }

    /** MONTH TIMESTEP LOOP */
    for (int im = 0; im < 12; ++im) {

      int dinmcurr = this->cohort.timer->getDaysInMonth(im);
      this->cohort.updateMonthly(iy, im, dinmcurr);

      // Maybe we are not really using this? Restults in a whole
      // boat load of files generated....
      //if(this->get_calMode()) {
      //  BOOST_LOG_SEV(glg, debug) << "Send monthly calibration data to json files...";
      //  this->output_caljson_monthly(icalyr, im);
      //}

    } /* end month loop */

    BOOST_LOG_SEV(glg, note) << "Completed year " << iy << " for cohort/cell (row,col): (" << this->y << "," << this->x << ")";

    if(cal_ctrl_ptr) { // check args->get_cal_mode() or calcontroller_ptr? ??
      BOOST_LOG_SEV(glg, debug) << "Send yearly calibration data to json files...";
      this->output_caljson_yearly(iy);
    }

  } /* end year loop */
}


/** Single site runmode.
*/
void Runner::single_site() {
  BOOST_LOG_NAMED_SCOPE("single site");

  this->initialize_regional_data(this->md.reginputdir + "co2.nc");

  runcht.cht.cd.chtid = chtid;
  // assgning the record no. for all needed data IDs to run 'chtid'
  // for 'siter', all record no. are in the first position of the lists
  rungrd.gridrecno  = *reclistgrid.begin();
  rungrd.drainrecno = *reclistdrain.begin();
  rungrd.soilrecno  = *reclistsoil.begin();
  rungrd.gfirerecno = *reclistgfire.begin();
  runcht.initrecno  = *reclistinit.begin();
  runcht.clmrecno   = *reclistclm.begin();
  runcht.vegrecno   = *reclistveg.begin();
  runcht.firerecno  = *reclistfire.begin();
  //getting the grided data and checking data for current cohort
  error = rungrd.readData();

  if (error!=0) {
    BOOST_LOG_SEV(glg, fatal) << "Problem reading grided data in Runner::single_site(...)";
    exit(-1);
  }

  //getting the cohort data for current cohort
  error = runcht.readData();

  if (error!=0) {
    BOOST_LOG_SEV(glg, fatal) << "Problem reading cohort data in Runner::single_site(...)";
    exit(-1);
  }

  error = runcht.reinit();

  if (error!=0) {
    BOOST_LOG_SEV(glg, fatal) << "Problem re-initializing cohort in Runner::single_site(...)";
    exit(-1);
  }

  BOOST_LOG_SEV(glg, info) << "cohort: " << chtid << " - choosing stage settings...!";
  runcht.choose_run_stage_settings();
};


void Runner::regional_space_major() {
  BOOST_LOG_NAMED_SCOPE("regional sm");

  this->initialize_regional_data(this->md.reginputdir + "co2.nc");

  //loop through cohort in 'runchtlist'
  unsigned int jj ;

  for (jj=0; jj<runchtlist.size(); jj++) {
    chtid = runchtlist.at(jj);

    BOOST_LOG_SEV(glg, note) << "Instantiate various data containers for new cohort...";
    // may need to clear up data containers for new cohort
    chted = EnvData();
    chtbd = BgcData();
    chtfd = FirData();
    rungrd.grid = Grid();
    runcht.cht = Cohort();
    //reset data pointer connection
    setupData();
    //
    runcht.cht.cd.chtid = chtid;
    // assgning the record no. for all needed data IDs
    rungrd.gridrecno  = reclistgrid.at(jj);
    rungrd.drainrecno = reclistdrain.at(jj);
    rungrd.soilrecno  = reclistsoil.at(jj);
    rungrd.gfirerecno = reclistgfire.at(jj);
    runcht.initrecno  = reclistinit.at(jj);
    runcht.clmrecno   = reclistclm.at(jj);
    runcht.vegrecno   = reclistveg.at(jj);
    runcht.firerecno  = reclistfire.at(jj);
    //getting the grided data for current cohort
    error = rungrd.readData();

    if (error!=0) {
      BOOST_LOG_SEV(glg, fatal) << "Problem reading grided data in Runner::regional_space_major(...)";
      exit(-1);
    }

    //getting the cohort data for current cohort
    error = runcht.readData();

    if (error!=0) {
      BOOST_LOG_SEV(glg, fatal) << "Problem reading cohort data in Runner::regional_space_major(...)";
      exit(-1);
    }

    error = runcht.reinit();

    if (error!=0) {
      BOOST_LOG_SEV(glg, fatal) << "Problem re-initializing cohort in Runner::regional_space_major(...)";
      exit(-3);
    }

    BOOST_LOG_SEV(glg, info) << "cohort: " << chtid << " - choosing stage settings...!";
    runcht.choose_run_stage_settings();
    runcht.cohortcount++;
  }
};

void Runner::regional_time_major(int processors, int rank) {
  BOOST_LOG_NAMED_SCOPE("regional tm");

  this->initialize_regional_data(this->md.reginputdir + "co2.nc");

  //
  timer.reset();

  // options for different run-stages:
  // NOTE: the following setting will not allow run two or more
  //   stages continuously
  if(md.runeq) {
    timer.stageyrind = 0;
    runcht.yrstart   = 0;
    runcht.yrend     = MAX_EQ_YR;
    md.set_friderived(true);
  }

  if(md.runsp) {
    timer.stageyrind = 0;
    timer.eqend      = true;
    runcht.used_atmyr= fmin(MAX_ATM_NOM_YR, md.act_clmyr);
    runcht.yrstart   = timer.spbegyr;
    runcht.yrend     = timer.spendyr;
    md.set_friderived(false);
  }

  if(md.runtr) {
    timer.stageyrind = 0;
    timer.eqend      = true;
    timer.spend      = true;
    runcht.used_atmyr= md.act_clmyr;
    runcht.yrstart   = timer.trbegyr;
    runcht.yrend     = timer.trendyr;
    md.set_friderived(false);
  }

  if(md.runsc) {
    timer.stageyrind = 0;
    timer.eqend = true;
    timer.spend = true;
    timer.trend = true;
    runcht.used_atmyr = md.act_clmyr;
    runcht.yrstart = timer.scbegyr;
    runcht.yrend   = timer.scendyr;
    md.set_friderived(false);
  } 
   
  //loop through time-step
  int totcohort = (int)runchtlist.size();

#ifdef WITHMPI
  if (1 == processors) {
    BOOST_LOG_SEV(glg, err) << "Not currently able to run in this mode on a "
                            << "computer with a single processor. Quitting.";
    exit(-1);
  } else if (rank == 0) {
    Master m = Master(rank, processors);

    m.dispense_cohorts_to_slaves(runchtlist);
    
    m.get_restartdata_and_progress_from_slaves(totcohort);

    /*
    std::vector<int> completed_cohorts;
    do {
      m.listen_for_progress_update();
      
      RestartData rd = m.listen_for_restart_data(); // should heap allocate a RestartData and return a pointer to it?
      if (rd != NULL) { // we have some data from a completed cohort!!
        write_restart_data_to_file(rd);
        completed_cohorts.push_back(rd.chtid)
      }
    } while (completed_cohorts.size() < runchtlist.size())
    */
      
  } else {
    Slave s = Slave(rank);
    s.recv_cohort_list_from_master();
    s.pp_cohort_list();
    
    for (int icalyr=runcht.yrstart; icalyr<=runcht.yrend; icalyr++) {
      int ifover = 0;
      for (int im = 0; im < 12; ++im) {
        runcht.cohortcount = 0;
        for (std::vector<int>::const_iterator cit = s.cohort_list.begin(); cit != s.cohort_list.end(); ++cit) {
          int cohort = *cit;
          
          /* this is convoluted because the slave's cohort_list stores the 
           cohort id, but later functions require the *index* of the cohort in
           the main runchtlist...so we have to look up the index based on the 
           value... */
          std::vector<int>::iterator it = find(runchtlist.begin(), runchtlist.end(), cohort);
          int cohort_idx = (it - runchtlist.begin()); // convert iterator to index...
          //std::cout << "Hi from slave " << rank << ". Working on " << icalyr << ", " << im << ", " << cohort << "\n";
          ifover = runSpatially(icalyr, im, cohort_idx);
          s.send_progress_update_to_master(icalyr, im, cohort);
        }
        md.initmode=4;
        timer.advanceOneMonth();
      }
      if (ifover==1) break;
      cout <<"TEM @"<< md.runstages <<" stage done with year "<<icalyr<<" for cohorts "<< s.cl_to_string() <<" (rank " << rank << ")\n";
    }

    std::cout << "This slave is done with all its cohorts, all years; time to send the RestartData objects to Master.\n";
    for (std::deque<RestartData>::iterator rdit = this->mlyres.begin(); rdit != this->mlyres.end(); ++rdit) {
      RestartData r = *rdit;
      s.send_restartdata_to_master(r);
    }

    //PAUSE_to_attach_gdb();
  }

#else
  // Just proceed serially...
  for (int icalyr=runcht.yrstart; icalyr<=runcht.yrend; icalyr++) {
    int ifover = 0;

    for (int im=0; im<12; im++) {
      runcht.cohortcount = 0;

      for (int jj=0; jj<totcohort; jj++) {
        ifover = runSpatially(icalyr, im, jj);
      }

      //
      /*  // restart data is saved into memory

      // The following is to save monthly-generated 'restart' file FOR
      // using to initialize the next time-steps for all cohorts
      // 1) need to close monthly I/O 'restart' files
      if (runcht.resouter.restartFile!=NULL) {
        runcht.resouter.restartFile->close();
        delete runcht.resouter.restartFile;
      }
      if (runcht.resinputer.restartFile!=NULL) {
        runcht.resinputer.restartFile->close();
        delete runcht.resinputer.restartFile;
      }

      // 2) copy the output 'restart' to the monthly 'restart'
      // after the first timestep, 'restart' as the initial conditions
      // So essentially every cohort has to be restarting from the
      //   previous time-step
      string mlyrestartfile = md.outputdir+"/restart-mly.nc";

      ifstream src((char*)runcht.resouter.restartfname.c_str(), ios::binary);
      ofstream dst((char*)mlyrestartfile.c_str(), ios::binary);
      dst<<src.rdbuf();
      src.close();
      dst.close();

      // 3) have to re-initialize I/O files for next timestep
      runcht.resinputer.init(mlyrestartfile);
      string stage="-"+md.runstages;
      runcht.resouter.init(md.outputdir, stage);
      //*/
      // no matter what initmode set in control file, must be 'restart'
      //   after the first time-step
      md.initmode=4;   // this will set 'initmode' as 'restart', but from
                       //'mlyres' rather than from restart file (initmode=3).
      // ticking timer once
      timer.advanceOneMonth();
    } // end of monthly loop

    // if get signal to break 'icalyr' loop (i.e., not reach to 'runcht.yrend'
    if (ifover==1) {
      break;
    }

    cout <<"TEM runs @" << md.runstages <<" - year "<<icalyr<<" is done! \n";
  } // end of yearly loop...

#endif /* WITHMPI */
  
  
};

int Runner::runSpatially(const int icalyr, const int im, const int jj) {
  chtid = runchtlist.at(jj);
  // may need to clear up data containers for new cohort
  chted = EnvData();
  chtbd = BgcData();
  chtfd = FirData();
  rungrd.grid = Grid();
  runcht.cht = Cohort();
  //reset data pointer connection
  setupData();
  // starting new cohort here
  runcht.cht.cd.chtid = chtid;
  runcht.cht.cd.year  = icalyr;
  runcht.cht.cd.month = im+1;
  // assigning the record no. for all needed data IDs
  rungrd.gridrecno  = reclistgrid.at(jj);
  rungrd.drainrecno = reclistdrain.at(jj);
  rungrd.soilrecno  = reclistsoil.at(jj);
  rungrd.gfirerecno = reclistgfire.at(jj);

  if (icalyr==runcht.yrstart && im==0) {
    runcht.initrecno  = reclistinit.at(jj);
  } else {    // after the first time-step, the initial record no. must be
              //   exactly same as in the runchtlist
    runcht.initrecno  = jj;
  }

  runcht.clmrecno = reclistclm.at(jj);
  runcht.vegrecno = reclistveg.at(jj);
  runcht.firerecno = reclistfire.at(jj);
  //getting the grided data for current cohort
  error = rungrd.readData();

  if (error!=0) {
    BOOST_LOG_SEV(glg, fatal) << "Problem reading grided data in Runner::regional_time_major(...)";
    exit(-1);
  }

  // getting the cohort data for the current cohort
  error = runcht.readData();

  if (error!=0) {
    BOOST_LOG_SEV(glg, fatal) << "Problem reading cohort data in Runner::regional_time_major(...)";
    exit(-1);
  }

  // a special case: for 'eq', ending year might be less than 'runcht.yrend'
  // this can only be done here (i.e., after reading data)
  int yrending = runcht.yrend;

  if (md.runeq) {
    int nfri = round(runcht.yrend/runcht.cht.cd.fri);
    nfri = min(max(nfri, 20),5); // 5 ~ 20 FRI
    yrending= nfri*runcht.cht.cd.fri-2;  //n*FRI-2: ending at 2 years prior to fire year

    if (icalyr>yrending) {
      if (jj==(int)runchtlist.size()-1) {
        return 1; // this will break the 'icalyr' loop in regional_time_major()
      } else {
        if (md.initmode>3) {
          mlyres.push_back(mlyres.at(0));
          mlyres.pop_front(); // these two will move the skipped cohort
                              //   'restart' to the back of 'deque'
        }

        return 0; // this will skip the following statements and jump to
                  //   next cohort (if not the last one)
      }
    }
  }

  // getting the initial data and drivers (climate and fire) for the
  //   current cohort
  if (md.initmode>3) {
    runcht.cht.resid = mlyres.at(0);
    mlyres.pop_front(); // this will always keep the first member in the
                        //   deque for the next cohort
  }

  error = runcht.reinit(); // here, if 'initmode=3', reads 'restart'
                           //   from 'md.initfile';

  //if 'initmode>3', takes 'restart' from above
  if (error!=0) {
    BOOST_LOG_SEV(glg, fatal) << "Problem re-initialzing cohort in Runner::regional_time_major(...)";
    exit(-1);
  }

  // run one timestep (monthly)
  runcht.advance_one_month();
  // save the new 'restart' in the back of deque, which will move forward
  mlyres.push_back(runcht.resod);

  if (mlyres.size()>runchtlist.size()) {
    mlyres.pop_front(); // this is not needed, if everything does well.
                        //   So here just in case
  }

  // TODO: will need to extend this to detect end of sp, tr, and sc
  if ((im == 11) && (timer.eqend || icalyr == timer.maxeqrunyrs) ) {
    #ifdef WITHMPI

      //int fake_buf;
      //fake_buf = 454;

      // send a message to master with the fake data...
      // this would actually end up being the restart data for
      // this cohort...might have to mess with passing custom types or strucs
      //cout << "Sending restart data to master! Done with last m of last yr for this cohort!\n";
      //MPI_Send(&fake_buf,                /* message buffer */
      //        1,                        /* one data item */
      //         MPI_INT,                  /* data item is an integer */
      //         0,                        /* to the master */
      //         PTEM_RESTARTDATA_TAG,     /* user chosen message tag */
      //         MPI_COMM_WORLD);          /* default communicator */
      
      // then noting should have to happen here? master will take care of writing
      // the restart data out to a file...
      
      //cout << "This process is done! The Send call to master completed, and "
      //     << "now this process can just quit?\n";
      //MPI::Barrier(MPI_COMM_WORLD);
      //cout << " THis is after the barrier, so all these should come in seq...\n";

    #else
      cout << "In Serial Mode.\n"
           << "\n"
           << "We are at the end of the eq run and need to write this cohort's "
           << "restart data (from the deque) to the restart file for the next "
           << "stage...\n";
      runcht.resouter.outputVariables(jj);
    #endif
  }

  //'restart.nc' always output at the ending time-step
  //  (which was adjusted above for 'eq')
  if (icalyr==yrending && im==11) {
    runcht.resouter.outputVariables(jj);
  }

  BOOST_LOG_SEV(glg, note) << "TEM " << md.runstages << " run,"
                           << " year: " << icalyr
                           << " month: " << im
                           << " cohort: "<< runcht.cht.cd.chtid;

  runcht.cohortcount++;
  return 0;
};

void Runner::createCohortList4Run() {

  BOOST_LOG_SEV(glg, info) << "Creating the cohort list for run...";

  NcFile runFile = temutil::open_ncfile(md.runchtfile);

  NcDim* chtD = temutil::get_ncdim(runFile, "CHTID");

  NcVar* chtV = temutil::get_ncvar(runFile, "CHTID");

  int numcht = chtD->size();
  int chtid  = -1;
  int chtid0 = -1;
  int chtidx = -1;

  for (int i=0; i<numcht; i++) {
    chtV->set_cur(i);
    chtV->get(&chtid, 1);
    runchtlist.push_back(chtid);

    if (i==0) {
      chtid0=chtid;
    }

    if (i==numcht-1) {
      chtidx=chtid;
    }
  }

  cout << md.casename << ": " << numcht <<"  cohorts to be run @"
       << md.runstages << "\n" <<"   from:  " << chtid0 <<"  to:  "
       << chtidx << "\n";
};

void Runner::createOutvarList(string & txtfile) {
  string outvarfile = txtfile;
  ifstream fctr;
  fctr.open(outvarfile.c_str(),ios::in );
  bool isOpen = fctr.is_open();

  if ( !isOpen ) {
    cout << "\nCannot open " << outvarfile << "  \n" ;
    exit( -2 );
  }

  string comments;
  getline(fctr, comments);
  getline(fctr, comments);
  int varno = I_outvarno;

  for (int ivar=0; ivar<varno; ivar++) {
    fctr >> runcht.regnod.outvarlist[ivar];
    getline(fctr, comments);
  }

  fctr.close();
};


void Runner::output_caljson_yearly(int year) {
  Json::Value data;
  std::ofstream out_stream;
  /* Not PFT dependent */
  data["Year"] = year;
  data["TAir"] = cohort.edall->y_atms.ta;
  data["Snowfall"] = cohort.edall->y_a2l.snfl;
  data["Rainfall"] = cohort.edall->y_a2l.rnfl;
  data["WaterTable"] = cohort.edall->y_sois.watertab;
  data["ActiveLayerDepth"]= cohort.edall-> y_soid.ald;
  data["CO2"] = cohort.edall->y_atms.co2;
  data["VPD"] = cohort.edall->y_atmd.vpd;
  data["EET"] = cohort.edall->y_l2a.eet;
  data["PET"] = cohort.edall->y_l2a.pet;
  data["PAR"] = cohort.edall->y_a2l.par;
  data["PARAbsorb"] = cohort.edall->y_a2v.parabsorb;

  data["VWCShlw"] = cohort.edall->y_soid.vwcshlw;
  data["VWCDeep"] = cohort.edall->y_soid.vwcdeep;
  data["VWCMineA"] = cohort.edall->y_soid.vwcminea;
  data["VWCMineB"] = cohort.edall->y_soid.vwcmineb;
  data["VWCMineC"] = cohort.edall->y_soid.vwcminec;
  data["TShlw"] = cohort.edall->y_soid.tshlw;
  data["TDeep"] = cohort.edall->y_soid.tdeep;
  data["TMineA"] = cohort.edall->y_soid.tminea;
  data["TMineB"] = cohort.edall->y_soid.tmineb;
  data["TMineC"] = cohort.edall->y_soid.tminec;

  data["StNitrogenUptakeAll"] = cohort.bdall->y_soi2v.snuptakeall;
  data["InNitrogenUptakeAll"] = cohort.bdall->y_soi2v.innuptake;
  data["AvailableNitrogenSum"] = cohort.bdall->y_soid.avlnsum;
  data["OrganicNitrogenSum"] = cohort.bdall->y_soid.orgnsum;
  data["CarbonShallow"] = cohort.bdall->y_soid.shlwc;
  data["CarbonDeep"] = cohort.bdall->y_soid.deepc;
  data["CarbonMineralSum"] = cohort.bdall->y_soid.mineac
                             + cohort.bdall->y_soid.minebc
                             + cohort.bdall->y_soid.minecc;
  data["MossdeathCarbon"] = cohort.bdall->y_sois.dmossc;
  data["MossdeathNitrogen"] = cohort.bdall->y_sois.dmossn;
  data["NetNMin"] = cohort.bdall->y_soi2soi.netnminsum;
  data["NetNImmob"] = cohort.bdall->y_soi2soi.nimmobsum;
  data["OrgNInput"] = cohort.bdall->y_a2soi.orgninput;
  data["AvlNInput"] = cohort.bdall->y_a2soi.avlninput;
  data["AvlNLost"] = cohort.bdall->y_soi2l.avlnlost;
  data["RHraw"] = cohort.bdall->y_soi2a.rhrawcsum;
  data["RHsoma"] = cohort.bdall->y_soi2a.rhsomasum;
  data["RHsompr"] = cohort.bdall->y_soi2a.rhsomprsum;
  data["RHsomcr"] = cohort.bdall->y_soi2a.rhsomcrsum;
  data["RH"] = cohort.bdall->y_soi2a.rhtot;
  
  data["Burnthick"] = cohort.fd->fire_soid.burnthick;
  data["BurnVeg2AirC"] = cohort.fd->fire_v2a.orgc;
  data["BurnVeg2AirN"] = cohort.fd->fire_v2a.orgn;
  data["BurnVeg2SoiAbvVegC"] = cohort.fd->fire_v2soi.abvc;
  data["BurnVeg2SoiBlwVegC"] = cohort.fd->fire_v2soi.blwc;
  data["BurnVeg2SoiAbvVegN"] = cohort.fd->fire_v2soi.abvn;
  data["BurnVeg2SoiBlwVegN"] = cohort.fd->fire_v2soi.blwn;
  data["BurnSoi2AirC"] = cohort.fd->fire_soi2a.orgc;
  data["BurnSoi2AirN"] = cohort.fd->fire_soi2a.orgn;


  for(int pft=0; pft<NUM_PFT; pft++) { //NUM_PFT
    char pft_chars[5];
    sprintf(pft_chars, "%d", pft);
    std::string pft_str = std::string(pft_chars);
    //c++0x equivalent: std::string pftvalue = std::to_string(pft);
    data["PFT" + pft_str]["VegCarbon"]["Leaf"] = cohort.bd[pft].y_vegs.c[I_leaf];
    data["PFT" + pft_str]["VegCarbon"]["Stem"] = cohort.bd[pft].y_vegs.c[I_stem];
    data["PFT" + pft_str]["VegCarbon"]["Root"] = cohort.bd[pft].y_vegs.c[I_root];
    data["PFT" + pft_str]["VegStructuralNitrogen"]["Leaf"] = cohort.bd[pft].y_vegs.strn[I_leaf];
    data["PFT" + pft_str]["VegStructuralNitrogen"]["Stem"] = cohort.bd[pft].y_vegs.strn[I_stem];
    data["PFT" + pft_str]["VegStructuralNitrogen"]["Root"] = cohort.bd[pft].y_vegs.strn[I_root];
    data["PFT" + pft_str]["VegLabileNitrogen"] = cohort.bd[pft].y_vegs.labn;
    data["PFT" + pft_str]["GPPAll"] = cohort.bd[pft].y_a2v.gppall;
    data["PFT" + pft_str]["NPPAll"] = cohort.bd[pft].y_a2v.nppall;
    data["PFT" + pft_str]["GPPAllIgnoringNitrogen"] = cohort.bd[pft].y_a2v.ingppall;
    data["PFT" + pft_str]["NPPAllIgnoringNitrogen"] = cohort.bd[pft].y_a2v.innppall;
    data["PFT" + pft_str]["PARDown"] = cohort.ed[pft].y_a2v.pardown;
    data["PFT" + pft_str]["PARAbsorb"] = cohort.ed[pft].y_a2v.parabsorb;
    data["PFT" + pft_str]["LitterfallCarbonAll"] = cohort.bd[pft].y_v2soi.ltrfalcall;
    data["PFT" + pft_str]["LitterfallNitrogenPFT"] = cohort.bd[pft].y_v2soi.ltrfalnall;
    data["PFT" + pft_str]["LitterfallNitrogen"]["Leaf"] = cohort.bd[pft].y_v2soi.ltrfaln[I_leaf];
    data["PFT" + pft_str]["LitterfallNitrogen"]["Stem"] = cohort.bd[pft].y_v2soi.ltrfaln[I_stem];
    data["PFT" + pft_str]["LitterfallNitrogen"]["Root"] = cohort.bd[pft].y_v2soi.ltrfaln[I_root];
    data["PFT" + pft_str]["PARDown"] = cohort.ed[pft].y_a2v.pardown;
    data["PFT" + pft_str]["PARAbsorb"] = cohort.ed[pft].y_a2v.parabsorb;
    data["PFT" + pft_str]["StNitrogenUptake"] = cohort.bd[pft].y_soi2v.snuptakeall;
    data["PFT" + pft_str]["InNitrogenUptake"] = cohort.bd[pft].y_soi2v.innuptake;
    data["PFT" + pft_str]["LuxNitrogenUptake"] = cohort.bd[pft].y_soi2v.lnuptake;
    data["PFT" + pft_str]["TotNitrogenUptake"] = cohort.bd[pft].y_soi2v.snuptakeall + cohort.bd[pft].y_soi2v.lnuptake;
  }

  std::stringstream filename;
  filename.fill('0');
  filename << "/tmp/year-cal-dvmdostem/" << std::setw(5) << year << ".json";
  out_stream.open(filename.str().c_str(), std::ofstream::out);
  out_stream << data << std::endl;
  out_stream.close();

}


