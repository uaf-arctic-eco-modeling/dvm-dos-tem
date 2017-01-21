#include <string>
#include <algorithm>
#include <json/writer.h>


#ifdef WITHMPI
#include <mpi.h>
#include "parallel-code/Master.h"
#include "parallel-code/Slave.h"
#include "inc/tbc_mpi_constants.h"
#endif

#include "../include/Runner.h"
#include "runmodule/Cohort.h"
#include "TEMUtilityFunctions.h"
#include "TEMLogger.h"
#include "util/tbc-debug-util.h"

extern src::severity_logger< severity_level > glg;

Runner::Runner(ModelData mdldata, bool cal_mode, int y, int x):
    calibrationMode(false), y(y), x(x) {

  BOOST_LOG_SEV(glg, note) << "RUNNER Constructing a Runner, new style, with ctor-"
                           << "injected ModelData, and for explicit (y,x) "
                           << "position w/in the input data region.";
  this->md = mdldata;
  this->cohort = Cohort(y, x, &mdldata); // explicitly constructed cohort...

  BOOST_LOG_SEV(glg, info) << "Calibration mode?: " << cal_mode;
  if ( cal_mode ) {
    this->calcontroller_ptr.reset( new CalController(&this->cohort) );
    this->calcontroller_ptr->clear_and_create_json_storage();
  } // else null??


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

void Runner::run_years(int start_year, int end_year, const std::string& stage) {

  /** YEAR TIMESTEP LOOP */
  BOOST_LOG_NAMED_SCOPE("Y") {
  for (int iy = start_year; iy < end_year; ++iy) {
    BOOST_LOG_SEV(glg, debug) << "(Beginning of year loop) " << cohort.ground.layer_report_string("depth thermal CN");
    BOOST_LOG_SEV(glg, err) << "Year loop, year: "<<iy;

    /* Interpolate all the monthly values...? */
    if( (stage.find("eq") != std::string::npos
           || stage.find("pre") != std::string::npos) ){
      this->cohort.climate.prepare_daily_driving_data(iy, stage);
    }

    else if(stage.find("sp") != std::string::npos){
      //FIX - 30 should not be hardcoded
      this->cohort.climate.prepare_daily_driving_data(iy%30, stage);
    }

    else if(stage.find("tr") != std::string::npos
              || stage.find("sc") != std::string::npos){
      this->cohort.climate.prepare_daily_driving_data(iy, stage);
    }


    if (this->calcontroller_ptr) { // should be null unless we are in "calibration mode"

      this->output_debug_daily_drivers(iy, this->calcontroller_ptr->daily_json);

      // Run any pre-configured directives
      this->calcontroller_ptr->run_config(iy, stage);

      // See if a signal has arrived (possibly from user
      // hitting Ctrl-C) and if so, stop the simulation
      // and drop into the calibration "shell".
      this->calcontroller_ptr->check_for_signals();

    }

    /** MONTH TIMESTEP LOOP */
    BOOST_LOG_NAMED_SCOPE("M") {
      for (int im = 0; im < 12; ++im) {
        BOOST_LOG_SEV(glg, note) << "(Beginning of month loop, iy:"<<iy<<", im:"<<im<<") " << cohort.ground.layer_report_string("depth thermal CN desc");

        this->cohort.updateMonthly(iy, im, DINM[im], stage);

        this->monthly_output(iy, im, stage);

      } // end month loop
    } // end named scope

    this->yearly_output(iy, stage, start_year, end_year);

    BOOST_LOG_SEV(glg, note) << "(END OF YEAR) " << cohort.ground.layer_report_string("depth thermal CN ptr");

    BOOST_LOG_SEV(glg, note) << "Completed year " << iy << " for cohort/cell (row,col): (" << this->y << "," << this->x << ")";

  }} // end year loop (and named scope
}

void Runner::monthly_output(const int year, const int month, const std::string& runstage) {

  if (md.output_monthly) {

    // Calibration json files....
    if(this->calcontroller_ptr) {
      BOOST_LOG_SEV(glg, debug) << "Write monthly data to json files...";
      this->output_caljson_monthly(year, month, runstage, this->calcontroller_ptr->monthly_json);
    }

  } else {
    BOOST_LOG_SEV(glg, debug) << "Monthly output turned off in config settings.";
  }

  // NetCDF output is not controlled by the monthly output flag in
  // the config file. TODO Semi-kludgy
  if(   (runstage.find("eq")!=std::string::npos && md.nc_eq)
     || (runstage.find("sp")!=std::string::npos && md.nc_sp)
     || (runstage.find("tr")!=std::string::npos && md.nc_tr)
     || (runstage.find("sc")!=std::string::npos && md.nc_sc) ){
    BOOST_LOG_SEV(glg, debug) << "Monthly NetCDF output function call, runstage: "<<runstage<<" year: "<<year<<" month: "<<month;
    output_netCDF_monthly(year, month);
  }

}

void Runner::yearly_output(const int year, const std::string& stage,
    const int startyr, const int endyr) {

  if(this->calcontroller_ptr) {
    if ( -1 == md.last_n_json_files ) {
      this->output_caljson_yearly(year, stage, this->calcontroller_ptr->yearly_json);
    }

    if ( year >= (endyr - md.last_n_json_files) ) {
      this->output_caljson_yearly(year, stage, this->calcontroller_ptr->yearly_json);
    }
  }

  // NetCDF output. Semi-kludgy
  if(   (stage.find("eq")!=std::string::npos && md.nc_eq)
     || (stage.find("sp")!=std::string::npos && md.nc_sp)
     || (stage.find("tr")!=std::string::npos && md.nc_tr)
     || (stage.find("sc")!=std::string::npos && md.nc_sc) ){
    BOOST_LOG_SEV(glg, debug) << "Yearly NetCDF output function call, runstage: "<<stage<<" year: "<<year;
    output_netCDF_yearly(year);
  }


}

void Runner::log_not_equal(const std::string& a_desc,
                           const std::string& b_desc,
                           int PFT,
                           double A, double B) {

  if ( !temutil::AlmostEqualRelative(A, B) ) {
    BOOST_LOG_SEV(glg, err) << "PFT:" << PFT
                            << " " << a_desc << " and " << b_desc
                            << " not summing correctly!"
                            << " A: "<< A <<" B: "<< B <<" (A-B: "<< A - B <<")";
  }

}

void Runner::log_not_equal(double A, double B, const std::string& msg) {
  if ( !temutil::AlmostEqualRelative(A,B) ) {
    BOOST_LOG_SEV(glg, err) << msg
                            <<" A: "<< A <<" B: "<< B <<" (A-B: "<< A - B <<")";
  }
}

/** Used to check that sums across PFT compartments match the 
    corresponding 'all' container.

*/
void Runner::check_sum_over_compartments() {

  for (int ip = 0; ip < NUM_PFT; ++ip) {

    log_not_equal("whole plant C", "plant C PART", ip,
                  cohort.bd[ip].m_vegs.call,
                  cohort.bd[ip].m_vegs.c[I_leaf] +
                  cohort.bd[ip].m_vegs.c[I_stem] +
                  cohort.bd[ip].m_vegs.c[I_root]);

    log_not_equal("whole plant strn", "plant strn PART", ip,
                  cohort.bd[ip].m_vegs.strnall,
                  cohort.bd[ip].m_vegs.strn[I_leaf] +
                  cohort.bd[ip].m_vegs.strn[I_stem] +
                  cohort.bd[ip].m_vegs.strn[I_root]);

    log_not_equal("whole plant ingpp", "plant ingpp PART", ip,
                  cohort.bd[ip].m_a2v.ingppall,
                  cohort.bd[ip].m_a2v.ingpp[I_leaf] +
                  cohort.bd[ip].m_a2v.ingpp[I_stem] +
                  cohort.bd[ip].m_a2v.ingpp[I_root]);


    log_not_equal("whole plant gpp", "plant gpp PART", ip,
                  cohort.bd[ip].m_a2v.gppall,
                  cohort.bd[ip].m_a2v.gpp[I_leaf] +
                  cohort.bd[ip].m_a2v.gpp[I_stem] +
                  cohort.bd[ip].m_a2v.gpp[I_root]);

    log_not_equal("whole plant npp", "plant npp PART", ip,
                  cohort.bd[ip].m_a2v.nppall,
                  cohort.bd[ip].m_a2v.npp[I_leaf] +
                  cohort.bd[ip].m_a2v.npp[I_stem] +
                  cohort.bd[ip].m_a2v.npp[I_root]);

    log_not_equal("whole plant innpp", "plant innpp PART", ip,
                  cohort.bd[ip].m_a2v.innppall,
                  cohort.bd[ip].m_a2v.innpp[I_leaf] +
                  cohort.bd[ip].m_a2v.innpp[I_stem] +
                  cohort.bd[ip].m_a2v.innpp[I_root]);

    log_not_equal("whole plant rm", "plant rm PART", ip,
                  cohort.bd[ip].m_v2a.rmall,
                  cohort.bd[ip].m_v2a.rm[I_leaf] +
                  cohort.bd[ip].m_v2a.rm[I_stem] +
                  cohort.bd[ip].m_v2a.rm[I_root]);

    log_not_equal("whole plant rg", "plant rg PART", ip,
                  cohort.bd[ip].m_v2a.rgall,
                  cohort.bd[ip].m_v2a.rg[I_leaf] +
                  cohort.bd[ip].m_v2a.rg[I_stem] +
                  cohort.bd[ip].m_v2a.rg[I_root]);

    log_not_equal("whole plant N litterfall", "plant N litterfall PART", ip,
                  cohort.bd[ip].m_v2soi.ltrfalnall + cohort.bd[ip].m_v2soi.mossdeathn,
                  cohort.bd[ip].m_v2soi.ltrfaln[I_leaf] +
                  cohort.bd[ip].m_v2soi.ltrfaln[I_stem] +
                  cohort.bd[ip].m_v2soi.ltrfaln[I_root]);

    log_not_equal("whole plant C litterfall", "plant C litterfall PART", ip,
                  cohort.bd[ip].m_v2soi.ltrfalcall + cohort.bd[ip].m_v2soi.mossdeathc,
                  cohort.bd[ip].m_v2soi.ltrfalc[I_leaf] +
                  cohort.bd[ip].m_v2soi.ltrfalc[I_stem] +
                  cohort.bd[ip].m_v2soi.ltrfalc[I_root]);

    log_not_equal("whole plant snuptake", "plant snuptake PART", ip,
                  cohort.bd[ip].m_soi2v.snuptakeall,
                  cohort.bd[ip].m_soi2v.snuptake[I_leaf] +
                  cohort.bd[ip].m_soi2v.snuptake[I_stem] +
                  cohort.bd[ip].m_soi2v.snuptake[I_root]);

    log_not_equal("whole plant nmobil", "plant nmobil PART", ip,
                  cohort.bd[ip].m_v2v.nmobilall,
                  cohort.bd[ip].m_v2v.nmobil[I_leaf] +
                  cohort.bd[ip].m_v2v.nmobil[I_stem] +
                  cohort.bd[ip].m_v2v.nmobil[I_root]);

    log_not_equal("whole plant nresorb", "plant nresorb PART", ip,
                  cohort.bd[ip].m_v2v.nresorball,
                  cohort.bd[ip].m_v2v.nresorb[I_leaf] +
                  cohort.bd[ip].m_v2v.nresorb[I_stem] +
                  cohort.bd[ip].m_v2v.nresorb[I_root]);

  } // end loop over PFTS
}

/** Sum across PFTs, compare with ecosystem totals (eg data from 'bdall').

Used to add up across all pfts (data held in cohort's bd array of BgcData objects)
and compare with the data held in cohort's bdall BgcData object.
*/
void Runner::check_sum_over_PFTs(){

  double ecosystem_C = 0;
  double ecosystem_C_by_compartment = 0;

  double ecosystem_N = 0;
  double ecosystem_strn = 0;
  double ecosystem_strn_by_compartment = 0;
  double ecosystem_labn = 0;

  double ecosystem_ingpp = 0;
  double ecosystem_gpp = 0;
  double ecosystem_innpp = 0;
  double ecosystem_npp = 0;

  double ecosystem_rm = 0;
  double ecosystem_rg = 0;

  double ecosystem_ltrfalc = 0;
  double ecosystem_ltrfaln = 0;
  double ecosystem_snuptake = 0;
  double ecosystem_nmobil = 0;
  double ecosystem_nresorb = 0;

  // sum various quantities over all PFTs
  for (int ip = 0; ip < NUM_PFT; ++ip) {
    ecosystem_C += this->cohort.bd[ip].m_vegs.call;
    ecosystem_C_by_compartment += (this->cohort.bd[ip].m_vegs.c[I_leaf] +
                                   this->cohort.bd[ip].m_vegs.c[I_stem] +
                                   this->cohort.bd[ip].m_vegs.c[I_root]);

    ecosystem_strn += this->cohort.bd[ip].m_vegs.strnall;
    ecosystem_strn_by_compartment += (this->cohort.bd[ip].m_vegs.strn[I_leaf] +
                                      this->cohort.bd[ip].m_vegs.strn[I_stem] +
                                      this->cohort.bd[ip].m_vegs.strn[I_root]);
    ecosystem_labn += this->cohort.bd[ip].m_vegs.labn;

    ecosystem_N += (this->cohort.bd[ip].m_vegs.strnall + this->cohort.bd[ip].m_vegs.labn);

    ecosystem_ingpp += this->cohort.bd[ip].m_a2v.ingppall;
    ecosystem_gpp += this->cohort.bd[ip].m_a2v.gppall;
    ecosystem_innpp += this->cohort.bd[ip].m_a2v.innppall;
    ecosystem_npp += this->cohort.bd[ip].m_a2v.nppall;

    ecosystem_rm += this->cohort.bd[ip].m_v2a.rmall;
    ecosystem_rg += this->cohort.bd[ip].m_v2a.rgall;

    ecosystem_ltrfalc += this->cohort.bd[ip].m_v2soi.ltrfalcall;
    ecosystem_ltrfaln += this->cohort.bd[ip].m_v2soi.ltrfalnall;

    ecosystem_snuptake += this->cohort.bd[ip].m_soi2v.snuptakeall;

    ecosystem_nmobil += this->cohort.bd[ip].m_v2v.nmobilall;
    ecosystem_nresorb += this->cohort.bd[ip].m_v2v.nresorball;

  }

  // Check that the sums are equal to the Runner level containers (ecosystem totals)
  log_not_equal(this->cohort.bdall->m_vegs.call, ecosystem_C, "Runner:: ecosystem veg C not matching sum over PFTs!");
  log_not_equal(this->cohort.bdall->m_vegs.call, ecosystem_C_by_compartment, "Runner:: ecosystem veg C not matching sum over compartments");

  log_not_equal(this->cohort.bdall->m_vegs.nall, ecosystem_N, "Runner:: ecosystem nall not matching sum over PFTs (of strn and nall)!");
  log_not_equal(this->cohort.bdall->m_vegs.labn, ecosystem_labn, "Runner:: ecosystem labn not matching sum over PFTs!");
  log_not_equal(this->cohort.bdall->m_vegs.strnall, ecosystem_strn, "Runner:: ecosystem strn not matching sum over PFTs!");
  log_not_equal(this->cohort.bdall->m_vegs.strnall, ecosystem_strn_by_compartment, "Runner:: ecosystem strn not matching sum over compartments!");

  log_not_equal(this->cohort.bdall->m_a2v.ingppall, ecosystem_ingpp, "Runner:: ecosystem npp not matching sum over PFTs!");
  log_not_equal(this->cohort.bdall->m_a2v.gppall, ecosystem_gpp, "Runner:: ecosystem npp not matching sum over PFTs!");
  log_not_equal(this->cohort.bdall->m_a2v.innppall, ecosystem_innpp, "Runner:: ecosystem innpp not matching sum over PFTs!");
  log_not_equal(this->cohort.bdall->m_a2v.nppall, ecosystem_npp, "Runner:: ecosystem npp not matching sum over PFTs!");

  log_not_equal(this->cohort.bdall->m_v2a.rmall, ecosystem_rm, "Runner:: ecosystem rm not matching sum over PFTs!");
  log_not_equal(this->cohort.bdall->m_v2a.rgall, ecosystem_rg, "Runner:: ecosystem rg not matching sum over PFTs!");

  log_not_equal(this->cohort.bdall->m_v2soi.ltrfalcall, ecosystem_ltrfalc, "Runner:: ecosystem ltrfalc not matching sum over PFTs!");
  log_not_equal(this->cohort.bdall->m_v2soi.ltrfalnall, ecosystem_ltrfaln, "Runner:: ecosystem ltrfaln not matching sum over PFTs!");

  log_not_equal(this->cohort.bdall->m_soi2v.snuptakeall, ecosystem_snuptake, "Runner:: ecosystem snuptake not matching sum over PFTs!");

  log_not_equal(this->cohort.bdall->m_v2v.nmobilall, ecosystem_nmobil, "Runner:: ecosystem nmobil not matching sum over PFTs!");
  log_not_equal(this->cohort.bdall->m_v2v.nresorball, ecosystem_nresorb, "Runner:: ecosystem nresorb not matching sum over PFTs!");

}

void Runner::output_caljson_monthly(int year, int month, std::string stage, boost::filesystem::path p){

  BOOST_LOG_SEV(glg, err) << "========== MONTHLY CHECKSUMMING ============";
  check_sum_over_compartments();
  check_sum_over_PFTs();
  BOOST_LOG_SEV(glg, err) << "========== END MONTHLY CHECKSUMMING ========";

  // CAUTION: this->md and this->cohort.md are different instances!

  Json::Value data;
  std::ofstream out_stream;

  /* Not PFT dependent */
  data["Runstage"] = stage;
  data["Year"] = year;
  data["Month"] = month;
  data["CMT"] = this->cohort.chtlu.cmtcode;
  data["Lat"] = this->cohort.lat;
  data["Lon"] = this->cohort.lon;

  data["Nfeed"] = this->cohort.md->get_nfeed();
  data["AvlNFlag"] = this->cohort.md->get_avlnflg();
  data["Baseline"] = this->cohort.md->get_baseline();
  data["EnvModule"] = this->cohort.md->get_envmodule();
  data["BgcModule"] = this->cohort.md->get_bgcmodule();
  data["DvmModule"] = this->cohort.md->get_dvmmodule();
  data["DslModule"] = this->cohort.md->get_dslmodule();
  data["DsbModule"] = this->cohort.md->get_dsbmodule();

  data["TAir"] = cohort.edall->m_atms.ta;
  data["Snowfall"] = cohort.edall->m_a2l.snfl;
  data["Rainfall"] = cohort.edall->m_a2l.rnfl;
  data["WaterTable"] = cohort.edall->m_sois.watertab;
  data["ActiveLayerDepth"] = cohort.edall->m_soid.ald;
  data["CO2"] = cohort.edall->m_atms.co2;
  data["VPD"] = cohort.edall->m_atmd.vpd;
  data["EET"] = cohort.edall->m_l2a.eet;
  data["PET"] = cohort.edall->m_l2a.pet;
  data["PAR"] = cohort.edall->m_a2v.pardown;            // <-- from edall
  data["PARAbsorb"] = cohort.edall->m_a2v.parabsorb;    // <-- from edall

  data["VWCShlw"] = cohort.edall->m_soid.vwcshlw;
  data["VWCDeep"] = cohort.edall->m_soid.vwcdeep;
  data["VWCMineA"] = cohort.edall->m_soid.vwcminea;
  data["VWCMineB"] = cohort.edall->m_soid.vwcmineb;
  data["VWCMineC"] = cohort.edall->m_soid.vwcminec;
  data["TShlw"] = cohort.edall->m_soid.tshlw;
  data["TDeep"] = cohort.edall->m_soid.tdeep;
  data["TMineA"] = cohort.edall->m_soid.tminea;
  data["TMineB"] = cohort.edall->m_soid.tmineb;
  data["TMineC"] = cohort.edall->m_soid.tminec;


  data["NMobilAll"] = cohort.bdall->m_v2v.nmobilall;
  data["NResorbAll"] = cohort.bdall->m_v2v.nresorball;

  data["StNitrogenUptakeAll"] = cohort.bdall->m_soi2v.snuptakeall;
  data["InNitrogenUptakeAll"] = cohort.bdall->m_soi2v.innuptake;
  data["AvailableNitrogenSum"] = cohort.bdall->m_soid.avlnsum;
  data["OrganicNitrogenSum"] = cohort.bdall->m_soid.orgnsum;
  data["CarbonShallow"] = cohort.bdall->m_soid.shlwc;
  data["CarbonDeep"] = cohort.bdall->m_soid.deepc;
  data["CarbonMineralSum"] = cohort.bdall->m_soid.mineac
                             + cohort.bdall->m_soid.minebc
                             + cohort.bdall->m_soid.minecc;
  // pools
  data["StandingDeadC"] = cohort.bdall->m_vegs.deadc;
  data["StandingDeadN"] = cohort.bdall->m_vegs.deadn;
  data["WoodyDebrisC"] = cohort.bdall->m_sois.wdebrisc;
  data["WoodyDebrisN"] = cohort.bdall->m_sois.wdebrisn;
  // fluxes
  data["MossDeathC"] = cohort.bdall->m_v2soi.mossdeathc;
  data["MossdeathNitrogen"] = cohort.bdall->m_v2soi.mossdeathn;
  data["D2WoodyDebrisC"] = cohort.bdall->m_v2soi.d2wdebrisc;
  data["D2WoodyDebrisN"] = cohort.bdall->m_v2soi.d2wdebrisn;

  data["NetNMin"] = cohort.bdall->m_soi2soi.netnminsum;
  data["NetNImmob"] = cohort.bdall->m_soi2soi.nimmobsum;
  data["OrgNInput"] = cohort.bdall->m_a2soi.orgninput;
  data["AvlNInput"] = cohort.bdall->m_a2soi.avlninput;
  data["AvlNLost"] = cohort.bdall->m_soi2l.avlnlost;
  data["RHraw"] = cohort.bdall->m_soi2a.rhrawcsum;
  data["RHsoma"] = cohort.bdall->m_soi2a.rhsomasum;
  data["RHsompr"] = cohort.bdall->m_soi2a.rhsomprsum;
  data["RHsomcr"] = cohort.bdall->m_soi2a.rhsomcrsum;
  data["RHwdeb"] = cohort.bdall->m_soi2a.rhwdeb;
  data["RH"] = cohort.bdall->m_soi2a.rhtot;

  data["YearsSinceDisturb"] = cohort.cd.yrsdist;
  data["Burnthick"] = cohort.year_fd[month].fire_soid.burnthick;
  data["BurnVeg2AirC"] = cohort.year_fd[month].fire_v2a.orgc;
  data["BurnVeg2AirN"] = cohort.year_fd[month].fire_v2a.orgn;
  data["BurnVeg2SoiAbvVegC"] = cohort.year_fd[month].fire_v2soi.abvc;
  data["BurnVeg2SoiBlwVegC"] = cohort.year_fd[month].fire_v2soi.blwc;
  data["BurnVeg2SoiAbvVegN"] = cohort.year_fd[month].fire_v2soi.abvn;
  data["BurnVeg2SoiBlwVegN"] = cohort.year_fd[month].fire_v2soi.blwn;
  data["BurnSoi2AirC"] = cohort.year_fd[month].fire_soi2a.orgc;
  data["BurnSoi2AirN"] = cohort.year_fd[month].fire_soi2a.orgn;
  data["BurnAir2SoiN"] = cohort.year_fd[month].fire_a2soi.orgn;
  data["BurnAbvVeg2DeadC"] = cohort.year_fd[month].fire_v2dead.vegC;
  data["BurnAbvVeg2DeadN"] = cohort.year_fd[month].fire_v2dead.strN;
  data["RawCSum"] = cohort.bdall->m_soid.rawcsum;
  data["SomaSum"] = cohort.bdall->m_soid.somasum;
  data["SomcrSum"] = cohort.bdall->m_soid.somcrsum;
  data["SomprSum"] = cohort.bdall->m_soid.somprsum;


  /* PFT dependent variables */

  // calculated ecosystem summary values
  double parDownSum = 0;
  double parAbsorbSum = 0;

  for(int pft=0; pft<NUM_PFT; pft++) {
    char pft_chars[5];
    sprintf(pft_chars, "%d", pft);
    std::string pft_str = std::string(pft_chars);
    // c++0x equivalent: std::string pftvalue = std::to_string(pft);
    data["PFT" + pft_str]["VegCarbon"]["Leaf"] = cohort.bd[pft].m_vegs.c[I_leaf];
    data["PFT" + pft_str]["VegCarbon"]["Stem"] = cohort.bd[pft].m_vegs.c[I_stem];
    data["PFT" + pft_str]["VegCarbon"]["Root"] = cohort.bd[pft].m_vegs.c[I_root];
    data["PFT" + pft_str]["VegStructuralNitrogen"]["Leaf"] = cohort.bd[pft].m_vegs.strn[I_leaf];
    data["PFT" + pft_str]["VegStructuralNitrogen"]["Stem"] = cohort.bd[pft].m_vegs.strn[I_stem];
    data["PFT" + pft_str]["VegStructuralNitrogen"]["Root"] = cohort.bd[pft].m_vegs.strn[I_root];
    data["PFT" + pft_str]["VegLabileNitrogen"] = cohort.bd[pft].m_vegs.labn;

    data["PFT" + pft_str]["NAll"] = cohort.bd[pft].m_vegs.nall; // <-- Sum of labn and strn
    data["PFT" + pft_str]["StandingDeadC"] = cohort.bd[pft].m_vegs.deadc;
    data["PFT" + pft_str]["StandingDeadN"] = cohort.bd[pft].m_vegs.deadn;

    data["PFT" + pft_str]["NMobil"] = cohort.bd[pft].m_v2v.nmobilall; // <- the all denotes multi-compartment
    data["PFT" + pft_str]["NResorb"] = cohort.bd[pft].m_v2v.nresorball;

    data["PFT" + pft_str]["GPPAll"] = cohort.bd[pft].m_a2v.gppall;
    data["PFT" + pft_str]["NPPAll"] = cohort.bd[pft].m_a2v.nppall;
    data["PFT" + pft_str]["GPPAllIgnoringNitrogen"] = cohort.bd[pft].m_a2v.ingppall;
    data["PFT" + pft_str]["NPPAllIgnoringNitrogen"] = cohort.bd[pft].m_a2v.innppall;
    data["PFT" + pft_str]["LitterfallCarbonAll"] = cohort.bd[pft].m_v2soi.ltrfalcall;
    data["PFT" + pft_str]["LitterfallNitrogenPFT"] = cohort.bd[pft].m_v2soi.ltrfalnall;
    data["PFT" + pft_str]["LitterfallNitrogen"]["Leaf"] = cohort.bd[pft].m_v2soi.ltrfaln[I_leaf];
    data["PFT" + pft_str]["LitterfallNitrogen"]["Stem"] = cohort.bd[pft].m_v2soi.ltrfaln[I_stem];
    data["PFT" + pft_str]["LitterfallNitrogen"]["Root"] = cohort.bd[pft].m_v2soi.ltrfaln[I_root];
    data["PFT" + pft_str]["StNitrogenUptake"] = cohort.bd[pft].m_soi2v.snuptakeall;
    data["PFT" + pft_str]["InNitrogenUptake"] = cohort.bd[pft].m_soi2v.innuptake;
    data["PFT" + pft_str]["LabNitrogenUptake"] = cohort.bd[pft].m_soi2v.lnuptake;
    data["PFT" + pft_str]["TotNitrogenUptake"] = cohort.bd[pft].m_soi2v.snuptakeall + cohort.bd[pft].m_soi2v.lnuptake;
    data["PFT" + pft_str]["MossDeathC"] = cohort.bd[pft].m_v2soi.mossdeathc;

    data["PFT" + pft_str]["PARDown"] = cohort.ed[pft].m_a2v.pardown;
    data["PFT" + pft_str]["PARAbsorb"] = cohort.ed[pft].m_a2v.parabsorb;

    parDownSum += cohort.ed[pft].m_a2v.pardown;
    parAbsorbSum += cohort.ed[pft].m_a2v.parabsorb;

  }

  data["PARAbsorbSum"] = parAbsorbSum;
  data["PARDownSum"] = parDownSum;
  data["GPPSum"] = cohort.bdall->m_a2v.gppall;
  data["NPPSum"] = cohort.bdall->m_a2v.nppall;

  // Writes files like this:
  //  0000000.json, 0000001.json, 0000002.json, ...

  std::stringstream filename;
  filename.fill('0');
  filename << std::setw(7) << (12 * year) + month << ".json";

  // Add the file name to the path
  p /= filename.str();

  // write out the data
  out_stream.open(p.string().c_str(), std::ofstream::out);
  out_stream << data << std::endl;
  out_stream.close();

}


void Runner::output_caljson_yearly(int year, std::string stage, boost::filesystem::path p) {

  BOOST_LOG_SEV(glg, err) << "========== YEARLY CHECKSUMMING ============";

  check_sum_over_compartments();
  check_sum_over_PFTs();

  BOOST_LOG_SEV(glg, err) << "========== END YEARLY CHECKSUMMING ========";

  // CAUTION: this->md and this->cohort.md are different instances!

  Json::Value data;
  std::ofstream out_stream;

  /* Not PFT dependent */
  data["Runstage"] = stage;
  data["Year"] = year;
  data["CMT"] = this->cohort.chtlu.cmtcode;
  data["Lat"] = this->cohort.lat;
  data["Lon"] = this->cohort.lon;

  data["Nfeed"] = this->cohort.md->get_nfeed();
  data["AvlNFlag"] = this->cohort.md->get_avlnflg();
  data["Baseline"] = this->cohort.md->get_baseline();
  data["EnvModule"] = this->cohort.md->get_envmodule();
  data["BgcModule"] = this->cohort.md->get_bgcmodule();
  data["DvmModule"] = this->cohort.md->get_dvmmodule();
  data["DslModule"] = this->cohort.md->get_dslmodule();
  data["DsbModule"] = this->cohort.md->get_dsbmodule();

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

  data["NMobilAll"] = cohort.bdall->y_v2v.nmobilall;
  data["NResorbAll"] = cohort.bdall->y_v2v.nresorball;

  data["StNitrogenUptakeAll"] = cohort.bdall->y_soi2v.snuptakeall;
  data["InNitrogenUptakeAll"] = cohort.bdall->y_soi2v.innuptake;
  data["AvailableNitrogenSum"] = cohort.bdall->y_soid.avlnsum;
  data["OrganicNitrogenSum"] = cohort.bdall->y_soid.orgnsum;
  data["CarbonShallow"] = cohort.bdall->y_soid.shlwc;
  data["CarbonDeep"] = cohort.bdall->y_soid.deepc;
  data["CarbonMineralSum"] = cohort.bdall->y_soid.mineac
                             + cohort.bdall->y_soid.minebc
                             + cohort.bdall->y_soid.minecc;
  // pools
  data["StandingDeadC"] = cohort.bdall->y_vegs.deadc;
  data["StandingDeadN"] = cohort.bdall->y_vegs.deadn;
  data["WoodyDebrisC"] = cohort.bdall->y_sois.wdebrisc;
  data["WoodyDebrisN"] = cohort.bdall->y_sois.wdebrisn;
  // fluxes
  data["MossDeathC"] = cohort.bdall->y_v2soi.mossdeathc;
  data["MossdeathNitrogen"] = cohort.bdall->y_v2soi.mossdeathn;
  data["D2WoodyDebrisC"] = cohort.bdall->y_v2soi.d2wdebrisc;
  data["D2WoodyDebrisN"] = cohort.bdall->y_v2soi.d2wdebrisn;

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
 
  //Placeholders for summing fire variables for the entire year
  double burnthick = 0.0, veg2airc = 0.0, veg2airn = 0.0, veg2soiabvvegc=0.0, veg2soiabvvegn = 0.0, veg2soiblwvegc = 0.0, veg2soiblwvegn = 0.0, veg2deadc = 0.0, veg2deadn = 0.0, soi2airc = 0.0, soi2airn = 0.0, air2soin = 0.0;
 
  for(int im=0; im<12; im++){
    char mth_chars[2];
    sprintf(mth_chars, "%02d", im);
    std::string mth_str = std::string(mth_chars);
    data["Fire"][mth_str]["Burnthick"] = cohort.year_fd[im].fire_soid.burnthick;
    data["Fire"][mth_str]["Veg2AirC"] = cohort.year_fd[im].fire_v2a.orgc;
    data["Fire"][mth_str]["Veg2AirN"] = cohort.year_fd[im].fire_v2a.orgn;
    data["Fire"][mth_str]["Veg2SoiAbvVegC"] = cohort.year_fd[im].fire_v2soi.abvc;
    data["Fire"][mth_str]["Veg2SoiBlwVegC"] = cohort.year_fd[im].fire_v2soi.blwc;
    data["Fire"][mth_str]["Veg2SoiAbvVegN"] = cohort.year_fd[im].fire_v2soi.abvn;
    data["Fire"][mth_str]["Veg2SoiBlwVegN"] = cohort.year_fd[im].fire_v2soi.blwn;
    data["Fire"][mth_str]["Veg2DeadC"] = cohort.year_fd[im].fire_v2dead.vegC;
    data["Fire"][mth_str]["Veg2DeadN"] = cohort.year_fd[im].fire_v2dead.strN;
    data["Fire"][mth_str]["Soi2AirC"] = cohort.year_fd[im].fire_soi2a.orgc;
    data["Fire"][mth_str]["Soi2AirN"] = cohort.year_fd[im].fire_soi2a.orgn;
    data["Fire"][mth_str]["Air2SoiN"] = cohort.year_fd[im].fire_a2soi.orgn/12;

    //Summed data for the entire year
    burnthick += cohort.year_fd[im].fire_soid.burnthick;
    veg2airc += cohort.year_fd[im].fire_v2a.orgc;
    veg2airn += cohort.year_fd[im].fire_v2a.orgn;
    veg2soiabvvegc += cohort.year_fd[im].fire_v2soi.abvc;
    veg2soiblwvegc += cohort.year_fd[im].fire_v2soi.blwc;
    veg2soiabvvegn += cohort.year_fd[im].fire_v2soi.abvn;
    veg2soiblwvegn += cohort.year_fd[im].fire_v2soi.blwn;
    veg2deadc += cohort.year_fd[im].fire_v2dead.vegC;
    veg2deadn += cohort.year_fd[im].fire_v2dead.strN;
    soi2airc += cohort.year_fd[im].fire_soi2a.orgc;
    soi2airn += cohort.year_fd[im].fire_soi2a.orgn;
    air2soin += cohort.year_fd[im].fire_a2soi.orgn/12;

  }
  data["Burnthick"] = burnthick;
  data["BurnVeg2AirC"] = veg2airc;
  data["BurnVeg2AirN"] = veg2airn;
  data["BurnVeg2SoiAbvVegC"] = veg2soiabvvegc;
  data["BurnVeg2SoiAbvVegN"] = veg2soiabvvegn;
  data["BurnVeg2SoiBlwVegN"] = veg2soiblwvegn;
  data["BurnVeg2SoiBlwVegC"] = veg2soiblwvegc;
  data["BurnSoi2AirC"] = soi2airc;
  data["BurnSoi2AirN"] = soi2airn;
  data["BurnAir2SoiN"] = air2soin;
  data["BurnAbvVeg2DeadC"] = veg2deadc;
  data["BurnAbvVeg2DeadN"] = veg2deadn;

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

    data["PFT" + pft_str]["NAll"] = cohort.bd[pft].y_vegs.nall; // <-- Sum of labn and strn
    data["PFT" + pft_str]["StandingDeadC"] = cohort.bd[pft].y_vegs.deadc;
    data["PFT" + pft_str]["StandingDeadN"] = cohort.bd[pft].y_vegs.deadn;

    data["PFT" + pft_str]["NMobil"] = cohort.bd[pft].y_v2v.nmobilall; // <- the all denotes multi-compartment
    data["PFT" + pft_str]["NResorb"] = cohort.bd[pft].y_v2v.nresorball;

    data["PFT" + pft_str]["GPPAll"] = cohort.bd[pft].y_a2v.gppall;
    data["PFT" + pft_str]["NPPAll"] = cohort.bd[pft].y_a2v.nppall;
    data["PFT" + pft_str]["GPPAllIgnoringNitrogen"] = cohort.bd[pft].y_a2v.ingppall;
    data["PFT" + pft_str]["NPPAllIgnoringNitrogen"] = cohort.bd[pft].y_a2v.innppall;
    data["PFT" + pft_str]["LitterfallCarbonAll"] = cohort.bd[pft].y_v2soi.ltrfalcall;
    data["PFT" + pft_str]["LitterfallNitrogenPFT"] = cohort.bd[pft].y_v2soi.ltrfalnall;
    data["PFT" + pft_str]["LitterfallNitrogen"]["Leaf"] = cohort.bd[pft].y_v2soi.ltrfaln[I_leaf];
    data["PFT" + pft_str]["LitterfallNitrogen"]["Stem"] = cohort.bd[pft].y_v2soi.ltrfaln[I_stem];
    data["PFT" + pft_str]["LitterfallNitrogen"]["Root"] = cohort.bd[pft].y_v2soi.ltrfaln[I_root];
    data["PFT" + pft_str]["StNitrogenUptake"] = cohort.bd[pft].y_soi2v.snuptakeall;
    data["PFT" + pft_str]["InNitrogenUptake"] = cohort.bd[pft].y_soi2v.innuptake;
    data["PFT" + pft_str]["LabNitrogenUptake"] = cohort.bd[pft].y_soi2v.lnuptake;
    data["PFT" + pft_str]["TotNitrogenUptake"] = cohort.bd[pft].y_soi2v.snuptakeall + cohort.bd[pft].y_soi2v.lnuptake;

    data["PFT" + pft_str]["PARDown"] = cohort.ed[pft].y_a2v.pardown;
    data["PFT" + pft_str]["PARAbsorb"] = cohort.ed[pft].y_a2v.parabsorb;

  }

  // Writes files like this:
  //  00000.json, 00001.json, 00002.json

  std::stringstream filename;
  filename.fill('0');
  filename << std::setw(5) << year << ".json";

  // Add the filename to the path
  p /= filename.str();

  out_stream.open(p.string().c_str(), std::ofstream::out);
  out_stream << data << std::endl;
  out_stream.close();

}

void Runner::output_debug_daily_drivers(int iy, boost::filesystem::path p) {

  // Writes files like this:
  //  year_00000_daily_drivers.text
  //  year_00001_daily_drivers.text
  //  year_00002_daily_drivers.text

  std::stringstream filename;
  filename.fill('0');
  filename << "year_" << std::setw(5) << iy << "_daily_drivers.text";

  // NOTE: (FIX?) This may not be the best place for these files as they are
  // not exactly the same format/layout as the normal "calibration" json files

  // Add the file name to the path
  p /= filename.str();

  std::ofstream out_stream;
  out_stream.open(p.string().c_str(), std::ofstream::out);

  out_stream << "tair_d = [" << temutil::vec2csv(cohort.climate.tair_d) << "]" << std::endl;
  out_stream << "nirr_d = [" << temutil::vec2csv(cohort.climate.nirr_d) << "]" << std::endl;
  out_stream << "vapo_d = [" << temutil::vec2csv(cohort.climate.vapo_d) << "]" << std::endl;
  out_stream << "prec_d = [" << temutil::vec2csv(cohort.climate.prec_d) << "]" << std::endl;
  out_stream << "rain_d = [" << temutil::vec2csv(cohort.climate.rain_d) << "]" << std::endl;
  out_stream << "snow_d = [" << temutil::vec2csv(cohort.climate.snow_d) << "]" << std::endl;
  out_stream << "svp_d = [" << temutil::vec2csv(cohort.climate.svp_d) << "]" << std::endl;
  out_stream << "vpd_d = [" << temutil::vec2csv(cohort.climate.vpd_d) << "]" << std::endl;
  out_stream << "girr_d = [" << temutil::vec2csv(cohort.climate.girr_d) << "]" << std::endl;
  out_stream << "cld_d = [" << temutil::vec2csv(cohort.climate.cld_d) << "]" << std::endl;
  out_stream << "par_d = [" << temutil::vec2csv(cohort.climate.par_d) << "]" << std::endl;

  out_stream.close();
}


void Runner::output_netCDF_monthly(int year, int month){
  BOOST_LOG_SEV(glg, fatal)<<"NetCDF monthly output";
  output_netCDF(md.monthly_netcdf_outputs, year, month);

  BOOST_LOG_SEV(glg, fatal)<<"Outputting accumulated daily data on the monthly timestep";
  output_netCDF(md.daily_netcdf_outputs, year, month);
}

void Runner::output_netCDF_yearly(int year){
  BOOST_LOG_SEV(glg, fatal)<<"NetCDF yearly output";
  output_netCDF(md.yearly_netcdf_outputs, year, 0);
}

void Runner::output_netCDF(std::map<std::string, output_spec> &netcdf_outputs, int year, int month){
  int timestep = year*12 + month;

  int dinm = DINM[month];

  int rowidx = this->y;
  int colidx = this->x;

  output_spec curr_spec;
  int ncid;
  int timeD; //unlimited dimension
  int xD;
  int yD;
  int pftD;
  int pftpartD;
  int layerD;
  int cv; //reusable variable handle

  std::map<std::string, output_spec>::iterator map_itr;

  /*** 3D variables ***/
  size_t start3[3];
  //Index 0 is set later from the length of the time dimension
  start3[1] = rowidx;
  start3[2] = colidx;

  //For daily-level variables
  size_t count3[3];
  count3[0] = dinm;
  count3[1] = 1;
  count3[2] = 1;

  /*** Soil Variables ***/
  size_t soilstart4[4];
  //Index 0 is set later from the length of the time dimension
  soilstart4[1] = 0;
  soilstart4[2] = rowidx;
  soilstart4[3] = colidx;

  size_t soilcount4[4];
  soilcount4[0] = 1;
  soilcount4[1] = MAX_SOI_LAY;
  soilcount4[2] = 1;
  soilcount4[3] = 1;

  /*** PFT variables ***/
  size_t PFTstart4[4];
  //Index 0 is set later from the length of the time dimension
  PFTstart4[1] = 0;//PFT
  PFTstart4[2] = rowidx;
  PFTstart4[3] = colidx;

  size_t PFTcount4[4];
  PFTcount4[0] = 1;
  PFTcount4[1] = NUM_PFT;
  PFTcount4[2] = 1;
  PFTcount4[3] = 1;

  /*** Compartment variables ***/
  size_t CompStart4[4];
  //Index 0 is set later from the length of the time dimension
  CompStart4[1] = 0;//PFT compartment
  CompStart4[2] = rowidx;
  CompStart4[3] = colidx;

  size_t CompCount4[4];
  CompCount4[0] = 1;
  CompCount4[1] = NUM_PFT_PART;
  CompCount4[2] = 1;
  CompCount4[3] = 1;

  /*** PFT and PFT compartment variables ***/
  size_t start5[5];
  //Index 0 is set later from the length of the time dimension
  start5[1] = 0;//PFT Compartment
  start5[2] = 0;//PFT
  start5[3] = rowidx;
  start5[4] = colidx;

  size_t count5[5];
  count5[0] = 1;
  count5[1] = NUM_PFT_PART;
  count5[2] = NUM_PFT;
  count5[3] = 1;
  count5[4] = 1;


  /*** Single option vars: (year) ***/
  map_itr = netcdf_outputs.find("ALD");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"ALD";
    curr_spec = map_itr->second;

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    temutil::nc( nc_inq_varid(ncid, "ALD", &cv) );
    start3[0] = temutil::get_nc_timedim_len(ncid);

    temutil::nc( nc_put_var1_double(ncid, cv, start3, &cohort.edall->y_soid.ald) );
    temutil::nc( nc_close(ncid) );
  }//end ALD
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("DEEPDZ");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"deepdz";
    curr_spec = map_itr->second;

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    temutil::nc( nc_inq_varid(ncid, "DEEPDZ", &cv) );
    start3[0] = temutil::get_nc_timedim_len(ncid);

    double deepdz = 0;
    Layer* currL = cohort.ground.toplayer;
    while(currL!=NULL){
      if(currL->isHumic){
        deepdz += currL->dz;
      }
      currL = currL->nextl;
    }

    temutil::nc( nc_put_var1_double(ncid, cv, start3, &deepdz) );
    temutil::nc( nc_close(ncid) );
  }//end DEEPDZ
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("GROWEND");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"GROWEND";
    curr_spec = map_itr->second;

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    temutil::nc( nc_inq_varid(ncid, "GROWEND", &cv) );
    start3[0] = temutil::get_nc_timedim_len(ncid);

//diagnostics.h   rtdpgrowstart DOY
//    EnvData   d_soid, m_soid, y_soid.rtdpgrowstart

      //The following does not work as expected.
      //growstart and growend are re-set to UIN_INT when the other
      //is in effect.
//    int growstart = cohort.ed[0].y_soid.rtdpgrowstart;

//    temutil::nc( nc_put_var1_double(ncid, cv, start3, &growstart) );
    temutil::nc( nc_close(ncid) );
  }//end GROWEND
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("GROWSTART");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"GROWSTART";
  }//end GROWSTART
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("MOSSDZ");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"MOSSDZ";
    curr_spec = map_itr->second;

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    temutil::nc( nc_inq_varid(ncid, "MOSSDZ", &cv) );
    start3[0] = temutil::get_nc_timedim_len(ncid);

    double mossdz = 0;
    Layer* currL = cohort.ground.toplayer;
    while(currL!=NULL){
      if(currL->isMoss){
        mossdz += currL->dz;
      }
      currL = currL->nextl;
    }
    //The following may never get set to anything useful?
    //y_soil.mossthick;

    temutil::nc( nc_put_var1_double(ncid, cv, start3, &mossdz) );
    temutil::nc( nc_close(ncid) );
  }//end MOSSDZ
  map_itr = netcdf_outputs.end();


//  map_itr = netcdf_outputs.find("ORL");
//  if(map_itr != netcdf_outputs.end()){
//    BOOST_LOG_SEV(glg, fatal)<<"ORL";
//    curr_spec = map_itr->second;
//
//    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
//    temutil::nc( nc_inq_varid(ncid, "ORL", &cv) );
//    start3[0] = temutil::get_nc_timedim_len(ncid);
//
//    temutil::nc( nc_put_var1_double(ncid, cv, start3, &) );
//    temutil::nc( nc_close(ncid) );
//  }//end ORL
//  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("PERMAFROST");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"PERMAFROST";
    curr_spec = map_itr->second;

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    temutil::nc( nc_inq_varid(ncid, "PERMAFROST", &cv) );
    start3[0] = temutil::get_nc_timedim_len(ncid);

    double permafrost = cohort.edall->y_soid.permafrost;

    temutil::nc( nc_put_var1_double(ncid, cv, start3, &permafrost) );
    temutil::nc( nc_close(ncid) );
  }//end PERMAFROST
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("SHLWDZ");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"SHLWDZ";
    curr_spec = map_itr->second;

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    temutil::nc( nc_inq_varid(ncid, "SHLWDZ", &cv) );
    start3[0] = temutil::get_nc_timedim_len(ncid);

    double shlwdz = 0;
    Layer* currL = cohort.ground.toplayer;
    while(currL!=NULL){
      if(currL->isFibric){
        shlwdz += currL->dz;
      }
      currL = currL->nextl;
    }

    temutil::nc( nc_put_var1_double(ncid, cv, start3, &shlwdz) );
    temutil::nc( nc_close(ncid) );
  }//end SHLWDZ
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("SNOWEND");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"SNOWEND";
  }//end SNOWEND
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("SNOWSTART");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"SNOWSTART";
  }//end SNOWSTART
  map_itr = netcdf_outputs.end();



  /*** Two combination vars: (month, year) ***/
  map_itr = netcdf_outputs.find("BURNAIR2SOIC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"Burned soil C";
  }//end BURNAIR2SOIC
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("BURNAIR2SOIN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"Burned soil N";
  }//end BURNAIR2SOIN
  map_itr = netcdf_outputs.end();


  //Burn thickness
  map_itr = netcdf_outputs.find("BURNTHICK");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"burnthick";
    curr_spec = map_itr->second;

    double burnthick;
    if(curr_spec.monthly){
      burnthick = cohort.year_fd[month].fire_soid.burnthick;
    }
    else if(curr_spec.yearly){
      burnthick = 0;
      for(int im=0; im<12; im++){
        burnthick += cohort.year_fd[im].fire_soid.burnthick;
      }
    }

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    start3[0] = temutil::get_nc_timedim_len(ncid);
    temutil::nc( nc_inq_varid(ncid, "BURNTHICK", &cv) );
    temutil::nc( nc_put_var1_double(ncid, cv, start3, &burnthick) );
    temutil::nc( nc_close(ncid) );
  }//end BURNTHICK
  map_itr = netcdf_outputs.end();


  //Standing dead C
  map_itr = netcdf_outputs.find("DEADC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"standing dead C";
    curr_spec = map_itr->second;

    double deadc;
    if(curr_spec.monthly){
      deadc = cohort.bdall->m_vegs.deadc;
    }
    else if(curr_spec.yearly){
      deadc = cohort.bdall->y_vegs.deadc;
    }

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    start3[0] = temutil::get_nc_timedim_len(ncid);
    temutil::nc( nc_inq_varid(ncid, "DEADC", &cv) );
    temutil::nc( nc_put_var1_double(ncid, cv, start3, &deadc) );
    temutil::nc( nc_close(ncid) );
  }//end DEADC
  map_itr = netcdf_outputs.end();


  //Standing dead N
  map_itr = netcdf_outputs.find("DEADN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"standing dead N";
    curr_spec = map_itr->second;

    double deadn;
    if(curr_spec.monthly){
      deadn = cohort.bdall->m_vegs.deadn;
    }
    else if(curr_spec.yearly){
      deadn = cohort.bdall->y_vegs.deadn;
    }

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    start3[0] = temutil::get_nc_timedim_len(ncid);
    temutil::nc( nc_inq_varid(ncid, "DEADN", &cv) );
    temutil::nc( nc_put_var1_double(ncid, cv, start3, &deadn) );
    temutil::nc( nc_close(ncid) );
  }//end DEADN
  map_itr = netcdf_outputs.end();


  //Deep C
  map_itr = netcdf_outputs.find("DEEPC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"Deep C";
    curr_spec = map_itr->second;

    double deepc;
    if(curr_spec.monthly){
      deepc = cohort.bdall->m_soid.deepc;
    }
    else if(curr_spec.yearly){
      deepc = cohort.bdall->y_soid.deepc;
    }

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    start3[0] = temutil::get_nc_timedim_len(ncid);
    temutil::nc( nc_inq_varid(ncid, "DEEPC", &cv) );
    temutil::nc( nc_put_var1_double(ncid, cv, start3, &deepc) );
    temutil::nc( nc_close(ncid) ); 
  }//end DEEPC
  map_itr = netcdf_outputs.end();


  //Woody debris C
  map_itr = netcdf_outputs.find("DWDC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"woody debris C";
    curr_spec = map_itr->second;

    double woodyc;
    if(curr_spec.monthly){
      woodyc = cohort.bdall->m_sois.wdebrisc;
    }
    else if(curr_spec.yearly){
      woodyc = cohort.bdall->y_sois.wdebrisc;
    }

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    start3[0] = temutil::get_nc_timedim_len(ncid);
    temutil::nc( nc_inq_varid(ncid, "DWDC", &cv) );
    temutil::nc( nc_put_var1_double(ncid, cv, start3, &woodyc) );
    temutil::nc( nc_close(ncid) );
  }//end DWDC
  map_itr = netcdf_outputs.end();


  //Woody debris N
  map_itr = netcdf_outputs.find("DWDN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"woody debris N";
    curr_spec = map_itr->second;

    double woodyn;
    if(curr_spec.monthly){
      woodyn = cohort.bdall->m_sois.wdebrisn;
    }
    else if(curr_spec.yearly){
      woodyn = cohort.bdall->y_sois.wdebrisn;
    }

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    start3[0] = temutil::get_nc_timedim_len(ncid);
    temutil::nc( nc_inq_varid(ncid, "DWDN", &cv) );
    temutil::nc( nc_put_var1_double(ncid, cv, start3, &woodyn) );
    temutil::nc( nc_close(ncid) );
  }//end DWDN
  map_itr = netcdf_outputs.end();


  //Mineral C
  map_itr = netcdf_outputs.find("MINEC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"Mineral C";
    curr_spec = map_itr->second;

    double minec;
    if(curr_spec.monthly){
      minec = cohort.bdall->m_soid.mineac
              + cohort.bdall->m_soid.minebc
              + cohort.bdall->m_soid.minecc;
    }
    else if(curr_spec.yearly){
      minec = cohort.bdall->y_soid.mineac
              + cohort.bdall->y_soid.minebc
              + cohort.bdall->y_soid.minecc;
    }

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    start3[0] = temutil::get_nc_timedim_len(ncid);
    temutil::nc( nc_inq_varid(ncid, "MINEC", &cv) );
    temutil::nc( nc_put_var1_double(ncid, cv, start3, &minec) );
    temutil::nc( nc_close(ncid) ); 
  }//end MINEC
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("NDEOP");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"NDEOP";
    curr_spec = map_itr->second;

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    start3[0] = temutil::get_nc_timedim_len(ncid);

    /*** STUB ***/

    temutil::nc( nc_inq_varid(ncid, "NDEOP", &cv) );
    //temutil::nc( nc_put_var1_double(ncid, cv, start3, &minec) );
    temutil::nc( nc_close(ncid) ); 
  }//end NDEOP
  map_itr = netcdf_outputs.end();


  //Shallow C
  map_itr = netcdf_outputs.find("SHLWC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"Shallow C";
    curr_spec = map_itr->second;

    double shlwc;
    if(curr_spec.monthly){
      shlwc = cohort.bdall->m_soid.shlwc;
    }
    else if(curr_spec.yearly){
      shlwc = cohort.bdall->y_soid.shlwc;
    }

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    start3[0] = temutil::get_nc_timedim_len(ncid);
    temutil::nc( nc_inq_varid(ncid, "SHLWC", &cv) );
    temutil::nc( nc_put_var1_double(ncid, cv, start3, &shlwc) );
    temutil::nc( nc_close(ncid) ); 
  }//end SHLWC 
  map_itr = netcdf_outputs.end();


  //Woody debris RH
  map_itr = netcdf_outputs.find("WDRH");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"woody debris rh";
    curr_spec = map_itr->second;

    double woodyrh;
    if(curr_spec.monthly){
      woodyrh = cohort.bdall->m_soi2a.rhwdeb;
    }
    else if(curr_spec.yearly){
      woodyrh = cohort.bdall->y_soi2a.rhwdeb;
    }

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    start3[0] = temutil::get_nc_timedim_len(ncid);
    temutil::nc( nc_inq_varid(ncid, "WDRH", &cv) );
    temutil::nc( nc_put_var1_double(ncid, cv, start3, &woodyrh) );
    temutil::nc( nc_close(ncid) ); 
  }//end WDRH
  map_itr = netcdf_outputs.end();


  /*** Three combination vars: (year, month, day) ***/
  //HKDEEP
  //HKMINEBOT
  //HKMINETOP
  //HKSHLW

  //Snowthick - a snapshot of the time when output is called
  map_itr = netcdf_outputs.find("SNOWTHICK");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"Snowthick";
    curr_spec = map_itr->second;

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    temutil::nc( nc_inq_varid(ncid, "SNOWTHICK", &cv) );
    start3[0] = temutil::get_nc_timedim_len(ncid);

    if(curr_spec.daily){
      
      temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_snowthick[0]) );
    }
    else if(curr_spec.monthly || curr_spec.yearly){
      double snowthick;
      Layer* currL = cohort.ground.toplayer;
      while(currL->isSnow){
        snowthick += currL->dz;
        currL = currL->nextl;
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &snowthick) );
    }

    temutil::nc( nc_close(ncid) ); 
  }//end SNOWTHICK
  map_itr = netcdf_outputs.end();


  //Snow water equivalent - a snapshot of the time when output is called
  map_itr = netcdf_outputs.find("SWE");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"SWE";
    curr_spec = map_itr->second;

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    temutil::nc( nc_inq_varid(ncid, "SWE", &cv) );
    start3[0] = temutil::get_nc_timedim_len(ncid);

    double swe;
    if(curr_spec.daily){
      temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_swesum[0]) );
    }

    else if(curr_spec.monthly || curr_spec.yearly){
      temutil::nc( nc_put_var1_double(ncid, cv, start3, &cohort.edall->d_snws.swesum) );
    }

    temutil::nc( nc_close(ncid) ); 
  }//end SWE
  map_itr = netcdf_outputs.end();


  //TCDEEP
  //TCMINEBOT
  //TCMINETOP
  //TCSHLW
  //TDEEP
  //TMINEBOT
  //TMINETOP
  //TROCK34M
  //TSHLW
  //TTD
  //VWCDEEP
  //VWCMINEBOT
  //VWCMINETOP
  //VWCSHLW
  //VWCTD
  //WATERTAB


  /*** Four combination vars. (year, month)x(layer, tot)  ***/
  //AVLN


  //Burned soil carbon
  map_itr = netcdf_outputs.find("BURNSOIC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"Burned soil C";
    curr_spec = map_itr->second;

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    temutil::nc( nc_inq_varid(ncid, "BURNSOIC", &cv) );

    if(curr_spec.layer){
      /*** STUB ***/
    }
    else if(!curr_spec.layer){
      start3[0] = temutil::get_nc_timedim_len(ncid);

      double burnSoilC;
      if(curr_spec.monthly){
        burnSoilC = cohort.year_fd[month].fire_soi2a.orgc;
      }
      else if(curr_spec.yearly){
        burnSoilC = 0;
        for(int im=0; im<12; im++){
          burnSoilC += cohort.year_fd[im].fire_soi2a.orgc;
        }
      }
      temutil::nc( nc_put_var1_double(ncid, cv, start3, &burnSoilC) );
    }

    temutil::nc( nc_close(ncid) );
  }//end BURNSOIC
  map_itr = netcdf_outputs.end();


  //Burned soil nitrogen 
  map_itr = netcdf_outputs.find("BURNSOILN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"Burned soil N";
    curr_spec = map_itr->second;

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    temutil::nc( nc_inq_varid(ncid, "BURNSOILN", &cv) );

    if(curr_spec.layer){
      /*** STUB ***/
    }
    else if(!curr_spec.layer){
      start3[0] = temutil::get_nc_timedim_len(ncid);

      double burnSoilN;
      if(curr_spec.monthly){
        burnSoilN = cohort.year_fd[month].fire_soi2a.orgn;
      }
      else if(curr_spec.yearly){
        burnSoilN = 0;
        for(int im=0; im<12; im++){
          burnSoilN += cohort.year_fd[im].fire_soi2a.orgn;
        }
      }
      temutil::nc( nc_put_var1_double(ncid, cv, start3, &burnSoilN) );
    }

    temutil::nc( nc_close(ncid) );
  }//end BURNSOILN
  map_itr = netcdf_outputs.end();


  //NETNMIN
  //NINPUT
  //NLOST
  //ORGN
  //RH
 // data["RH"] = cohort.bdall->y_soi2a.rhtot;


  map_itr = netcdf_outputs.find("SOC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"SOC";
    curr_spec = map_itr->second;

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    temutil::nc( nc_inq_varid(ncid, "SOC", &cv) );
    soilstart4[0] = temutil::get_nc_timedim_len(ncid);

    double soilc[MAX_SOI_LAY];
    int il = 0;
    Layer* currL = this->cohort.ground.toplayer;
    while(currL != NULL){
      soilc[il] = currL->rawc;
      il++;
      currL = currL->nextl;
    }

    temutil::nc( nc_put_vara_double(ncid, cv, soilstart4, soilcount4, &soilc[0]) );
    temutil::nc( nc_close(ncid) );
  }//end SOC
  map_itr = netcdf_outputs.end();


  /*** Six combination vars: (year,month)x(PFT,Comp,Both)***/
  //BURNVEG2AIRC
  //BURNVEG2AIRN
  //BURNVEG2DEADC
  //BURNVEG2DEADN
  //BURNVEG2SOIABVC
  //BURNVEG2SOIABVN
  //BURNVEG2SOIBLWC
  //BURNVEG2SOIBLWN

  //Burned Veg Carbon
  map_itr = netcdf_outputs.find("BURNVEGC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"BURNVEGC";
    curr_spec = map_itr->second;

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    temutil::nc( nc_inq_varid(ncid, "BURNVEGC", &cv) );

    //PFT and compartment
    if(curr_spec.pft && curr_spec.compartment){
      start5[0] = temutil::get_nc_timedim_len(ncid);

      double burnvegc[NUM_PFT_PART][NUM_PFT];
      for(int ip=0; ip<NUM_PFT; ip++){
        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          //burnvegc[ipp][ip] = cohort.fd_month
        }
      }

      //temutil::nc( nc_put_vara_double(ncid, cv, start5, count5, &burnvegc[0][0]) );
    }
    //PFT only
    else if(curr_spec.pft && !curr_spec.compartment){
      PFTstart4[0] = temutil::get_nc_timedim_len(ncid);

    }
    //Compartment only
    else if(!curr_spec.pft && curr_spec.compartment){
      CompStart4[0] = temutil::get_nc_timedim_len(ncid);

    }
    temutil::nc( nc_close(ncid) );
  }//end Burn Veg C
  map_itr = netcdf_outputs.end();


  //GPP
  map_itr = netcdf_outputs.find("GPP");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"GPP";
    curr_spec = map_itr->second;

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    temutil::nc( nc_inq_varid(ncid, "GPP", &cv) );

    //PFT and compartment
    if(curr_spec.pft && curr_spec.compartment){
      start5[0] = temutil::get_nc_timedim_len(ncid);

      double gpp[NUM_PFT_PART][NUM_PFT];
      for(int ip=0; ip<NUM_PFT; ip++){
        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          gpp[ipp][ip] = cohort.bd[ip].m_a2v.gpp[ipp];
        }
      }

      temutil::nc( nc_put_vara_double(ncid, cv, start5, count5, &gpp[0][0]) );
    }
    //PFT only
    else if(curr_spec.pft && !curr_spec.compartment){
      PFTstart4[0] = temutil::get_nc_timedim_len(ncid);

      double gpp[NUM_PFT];
      for(int ip=0; ip<NUM_PFT; ip++){
        gpp[ip] = cohort.bd[ip].m_a2v.gppall; 
      }

      temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &gpp[0]) );
    }
    //Compartment only
    else if(!curr_spec.pft && curr_spec.compartment){
      CompStart4[0] = temutil::get_nc_timedim_len(ncid);

      double gpp[NUM_PFT_PART] = {0};
      for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
        for(int ip=0; ip<NUM_PFT; ip++){
          gpp[ipp] += cohort.bd[ip].m_a2v.gpp[ipp];
        }
      }

      temutil::nc( nc_put_vara_double(ncid, cv, CompStart4, CompCount4, &gpp[0]) );
    }

    temutil::nc( nc_close(ncid) );
  }//end GPP
  map_itr = netcdf_outputs.end();


  //LAI
  //LTRFALC
  //LTRVALN


  //NPP
  map_itr = netcdf_outputs.find("NPP");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"NPP";
    curr_spec = map_itr->second;

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    temutil::nc( nc_inq_varid(ncid, "NPP", &cv) );

    //PFT and compartment
    if(curr_spec.pft && curr_spec.compartment){
      start5[0] = temutil::get_nc_timedim_len(ncid);

      double npp[NUM_PFT_PART][NUM_PFT];
      for(int ip=0; ip<NUM_PFT; ip++){
        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          npp[ipp][ip] = cohort.bd[ip].m_a2v.npp[ipp];
        }
      }

      temutil::nc( nc_put_vara_double(ncid, cv, start5, count5, &npp[0][0]) );
    }
    //PFT only
    else if(curr_spec.pft && !curr_spec.compartment){
      PFTstart4[0] = temutil::get_nc_timedim_len(ncid);

      double npp[NUM_PFT];
      for(int ip=0; ip<NUM_PFT; ip++){
        npp[ip] = cohort.bd[ip].m_a2v.nppall; 
      }

      temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &npp[0]) );
    }
    //Compartment only
    else if(!curr_spec.pft && curr_spec.compartment){
      CompStart4[0] = temutil::get_nc_timedim_len(ncid);

      double npp[NUM_PFT_PART] = {0};
      for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
        for(int ip=0; ip<NUM_PFT; ip++){
          npp[ipp] += cohort.bd[ip].m_a2v.npp[ipp];
        }
      }

      temutil::nc( nc_put_vara_double(ncid, cv, CompStart4, CompCount4, &npp[0]) );
    }

    temutil::nc( nc_close(ncid) );
  }//end NPP
  map_itr = netcdf_outputs.end();


  //VEGC
  map_itr = netcdf_outputs.find("VEGC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"vegc";
    curr_spec = map_itr->second;

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    temutil::nc( nc_inq_varid(ncid, "VEGC", &cv) );

    //PFT and compartment
    if(curr_spec.pft && curr_spec.compartment){
      start5[0] = temutil::get_nc_timedim_len(ncid);

      double vegc[NUM_PFT_PART][NUM_PFT];
      for(int ip=0; ip<NUM_PFT; ip++){
        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          if(curr_spec.monthly){
            vegc[ipp][ip] = cohort.bd[ip].m_vegs.c[ipp];
          }
          else if(curr_spec.yearly){
            vegc[ipp][ip] = cohort.bd[ip].y_vegs.c[ipp];
          }
        }
      }

      temutil::nc( nc_put_vara_double(ncid, cv, start5, count5, &vegc[0][0]) );
    }
    //PFT only
    else if(curr_spec.pft && !curr_spec.compartment){
      PFTstart4[0] = temutil::get_nc_timedim_len(ncid);

      double vegc[NUM_PFT];
      for(int ip=0; ip<NUM_PFT; ip++){
        if(curr_spec.monthly){
          vegc[ip] = cohort.bd[ip].m_vegs.call;
        }
        else if(curr_spec.yearly){
          vegc[ip] = cohort.bd[ip].y_vegs.call;
        }
      }

      temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &vegc[0]) );
    }
    //Compartment only
    else if(!curr_spec.pft && curr_spec.compartment){
      CompStart4[0] = temutil::get_nc_timedim_len(ncid);

      double vegc[NUM_PFT_PART] = {0};
      for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
        for(int ip=0; ip<NUM_PFT; ip++){
          if(curr_spec.monthly){
            vegc[ipp] += cohort.bd[ip].m_vegs.c[ipp];
          }
          else if(curr_spec.yearly){
            vegc[ipp] += cohort.bd[ip].y_vegs.c[ipp];
          }
        }
      }

      temutil::nc( nc_put_vara_double(ncid, cv, CompStart4, CompCount4, &vegc[0]) );
    }
    temutil::nc( nc_close(ncid) );
  }//end VEGC
  map_itr = netcdf_outputs.end();


  //VEGN
  map_itr = netcdf_outputs.find("VEGN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"VEGN NetCDF output";
    curr_spec = map_itr->second;

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    temutil::nc( nc_inq_varid(ncid, "VEGN", &cv) );

    //PFT and compartment
    if(curr_spec.pft && curr_spec.compartment){
      start5[0] = temutil::get_nc_timedim_len(ncid);

      double vegn[NUM_PFT_PART][NUM_PFT];
      for(int ip=0; ip<NUM_PFT; ip++){
        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          if(curr_spec.monthly){
            vegn[ipp][ip] = cohort.bd[ip].m_vegs.strn[ipp];
          }
          else if(curr_spec.yearly){
            vegn[ipp][ip] = cohort.bd[ip].y_vegs.strn[ipp];
          }
        }
      }

      temutil::nc( nc_put_vara_double(ncid, cv, start5, count5, &vegn[0][0]) );
    }
    //PFT only
    else if(curr_spec.pft && !curr_spec.compartment){
      PFTstart4[0] = temutil::get_nc_timedim_len(ncid);

      double vegn[NUM_PFT];
      for(int ip=0; ip<NUM_PFT; ip++){
        if(curr_spec.monthly){
          vegn[ip] = cohort.bd[ip].m_vegs.strnall;
        }
        else if(curr_spec.yearly){
          vegn[ip] = cohort.bd[ip].y_vegs.strnall;
        }
      }

      temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &vegn[0]) );
    }
    //Compartment only
    else if(!curr_spec.pft && curr_spec.compartment){
      CompStart4[0] = temutil::get_nc_timedim_len(ncid);

      double vegn[NUM_PFT_PART] = {0};
      for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
        for(int ip=0; ip<NUM_PFT; ip++){
          if(curr_spec.monthly){
            vegn[ipp] += cohort.bd[ip].m_vegs.strn[ipp];
          }
          else if(curr_spec.yearly){
            vegn[ipp] += cohort.bd[ip].y_vegs.strn[ipp];
          }
        }
      }

      temutil::nc( nc_put_vara_double(ncid, cv, CompStart4, CompCount4, &vegn[0]) );
    }
    temutil::nc( nc_close(ncid) );
  }//end VEGN
  map_itr = netcdf_outputs.end();


  /*** Six combination vars: (year,month,day)x(PFT,total) ***/

  //EET
  map_itr = netcdf_outputs.find("EET");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"EET";
    curr_spec = map_itr->second;

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    temutil::nc( nc_inq_varid(ncid, "EET", &cv) );

    //PFT
    if(curr_spec.pft){
      PFTstart4[0] = temutil::get_nc_timedim_len(ncid);

      if(curr_spec.daily){
        PFTcount4[0] = dinm;

        double EET[dinm][NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          for(int id=0; id<dinm; id++){
            EET[id][ip] = cohort.ed[ip].daily_eet[id];
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &EET[0][0]) );
      }
      else if(curr_spec.monthly){
        double EET[NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          EET[ip] = cohort.ed[ip].m_l2a.eet;
        }

        temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &EET[0]) );
      }
      else if(curr_spec.yearly){
        double EET[NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          EET[ip] = cohort.ed[ip].y_l2a.eet;
        }

        temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &EET[0]) );
      }
    }
    //Not PFT. Total?
    else if(!curr_spec.pft){
      /*** STUB ***/
      //total EET - is this useful?
    }

   temutil::nc( nc_close(ncid) );
  }//end EET
  map_itr = netcdf_outputs.end();


  //PET
  map_itr = netcdf_outputs.find("PET");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, fatal)<<"PET";
    curr_spec = map_itr->second;

    temutil::nc( nc_open(curr_spec.filestr.c_str(), NC_WRITE, &ncid) );
    temutil::nc( nc_inq_varid(ncid, "PET", &cv) );

    //PFT
    if(curr_spec.pft){
      PFTstart4[0] = temutil::get_nc_timedim_len(ncid);

      if(curr_spec.daily){
        PFTcount4[0] = dinm;

        double PET[dinm][NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          for(int id=0; id<dinm; id++){
            PET[id][ip] = cohort.ed[ip].daily_pet[id];
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &PET[0][0]) );
      }
      else if(curr_spec.monthly){
        double PET[NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          PET[ip] = cohort.ed[ip].m_l2a.pet;
        }

        temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &PET[0]) );
      }
      else if(curr_spec.yearly){
        double PET[NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          PET[ip] = cohort.ed[ip].y_l2a.pet;
        }

        temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &PET[0]) );
      }
    }
    //Not PFT. Total?
    else if(!curr_spec.pft){
      /*** STUB ***/
      //total PET - is this useful?
    }

   temutil::nc( nc_close(ncid) );
  }//end PET
  map_itr = netcdf_outputs.end();

}


