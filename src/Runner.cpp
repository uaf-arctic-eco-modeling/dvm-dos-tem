#include <string>
#include <algorithm>
#include <json/writer.h>


#ifdef WITHMPI
#include <mpi.h>
#endif

#include "../include/Runner.h"
#include "../include/Cohort.h"
#include "../include/TEMUtilityFunctions.h"
#include "../include/TEMLogger.h"
#include "../include/tbc-debug-util.h"

extern src::severity_logger< severity_level > glg;

Runner::Runner(ModelData mdldata, bool cal_mode, int y, int x):
    calibrationMode(false), y(y), x(x) {

  BOOST_LOG_SEV(glg, info) << "RUNNER Constructing a Runner, new style, with ctor-"
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


Runner::~Runner() {};

void Runner::run_years(int start_year, int end_year, const std::string& stage) {

  /** YEAR TIMESTEP LOOP */
  BOOST_LOG_NAMED_SCOPE("Y") {
  for (int iy = start_year; iy < end_year; ++iy) {
    BOOST_LOG_SEV(glg, debug) << "(Beginning of year loop) " << cohort.ground.layer_report_string("depth thermal CN");
    BOOST_LOG_SEV(glg, warn) << "y: "<<this->y<<" x: "<<this->x<<" Year: "<<iy;

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
        BOOST_LOG_SEV(glg, info) << "(Beginning of month loop, iy:"<<iy<<", im:"<<im<<") " << cohort.ground.layer_report_string("depth thermal CN desc");

        this->cohort.updateMonthly(iy, im, DINM[im], stage);

        this->monthly_output(iy, im, stage, end_year);

        // Prevent cells from running for an exceptionally long time,
        //  mostly for use in large regional runs.
        if(md.cell_timelimit > 0){//If a limit is specified at all
          time_t cell_curr_time = time(0);
          int run_seconds = difftime(cell_curr_time, md.cell_stime);
          if(run_seconds > md.cell_timelimit){
            throw temutil::CellTimeExceeded();
          }
        }

      } // end month loop
    } // end named scope

    this->yearly_output(iy, stage, start_year, end_year);

    BOOST_LOG_SEV(glg, info) << "(END OF YEAR) " << cohort.ground.layer_report_string("depth thermal CN ptr");

    BOOST_LOG_SEV(glg, info) << "Completed year " << iy << " for cohort/cell (row,col): (" << this->y << "," << this->x << ")";

  }} // end year loop (and named scope
}

void Runner::monthly_output(const int year, const int month, const std::string& runstage, int endyr) {

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

    output_netCDF_monthly(year, month, runstage, endyr);
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
    output_netCDF_yearly(year, stage, endyr);
  }


}

std::string Runner::report_not_equal(const std::string& a_desc,
                                     const std::string& b_desc,
                                     int PFT,
                                     double A, double B) {
  std::stringstream ss;
  if ( !temutil::AlmostEqualRelative(A, B) ) {
    ss << "PFT:" << PFT << " " << a_desc << " and " << b_desc
       << " not summing correctly!" << " A: "<< A <<" B: "<< B
       << " (A-B: "<< A - B <<")";
  }
  return ss.str(); // empty string if no error
}

std::string Runner::report_not_equal(double A, double B, const std::string& msg) {
  std::stringstream ss;
  if ( !temutil::AlmostEqualRelative(A, B) ) {
    ss << msg <<" A: "<< A <<" B: "<< B <<" (A-B: "<< A - B <<")";
  }
  return ss.str(); // empty string if no error
}

/** Used to check that sums across PFT compartments match the 
    corresponding 'all' container.

*/
std::list<std::string> Runner::check_sum_over_compartments() {

  std::list<std::string> errlist;

  for (int ip = 0; ip < NUM_PFT; ++ip) {

    errlist.push_back(report_not_equal(
                      "whole plant C", "plant C PART", ip,
                      cohort.bd[ip].m_vegs.call,
                      cohort.bd[ip].m_vegs.c[I_leaf] +
                      cohort.bd[ip].m_vegs.c[I_stem] +
                      cohort.bd[ip].m_vegs.c[I_root]));

    errlist.push_back(report_not_equal("whole plant C", "plant C PART", ip,
                  cohort.bd[ip].m_vegs.call,
                  cohort.bd[ip].m_vegs.c[I_leaf] +
                  cohort.bd[ip].m_vegs.c[I_stem] +
                  cohort.bd[ip].m_vegs.c[I_root]));

    errlist.push_back(report_not_equal("whole plant strn", "plant strn PART", ip,
                  cohort.bd[ip].m_vegs.strnall,
                  cohort.bd[ip].m_vegs.strn[I_leaf] +
                  cohort.bd[ip].m_vegs.strn[I_stem] +
                  cohort.bd[ip].m_vegs.strn[I_root]));

    errlist.push_back(report_not_equal("whole plant ingpp", "plant ingpp PART", ip,
                  cohort.bd[ip].m_a2v.ingppall,
                  cohort.bd[ip].m_a2v.ingpp[I_leaf] +
                  cohort.bd[ip].m_a2v.ingpp[I_stem] +
                  cohort.bd[ip].m_a2v.ingpp[I_root]));


    errlist.push_back(report_not_equal("whole plant gpp", "plant gpp PART", ip,
                  cohort.bd[ip].m_a2v.gppall,
                  cohort.bd[ip].m_a2v.gpp[I_leaf] +
                  cohort.bd[ip].m_a2v.gpp[I_stem] +
                  cohort.bd[ip].m_a2v.gpp[I_root]));

    errlist.push_back(report_not_equal("whole plant npp", "plant npp PART", ip,
                  cohort.bd[ip].m_a2v.nppall,
                  cohort.bd[ip].m_a2v.npp[I_leaf] +
                  cohort.bd[ip].m_a2v.npp[I_stem] +
                  cohort.bd[ip].m_a2v.npp[I_root]));

    errlist.push_back(report_not_equal("whole plant innpp", "plant innpp PART", ip,
                  cohort.bd[ip].m_a2v.innppall,
                  cohort.bd[ip].m_a2v.innpp[I_leaf] +
                  cohort.bd[ip].m_a2v.innpp[I_stem] +
                  cohort.bd[ip].m_a2v.innpp[I_root]));

    errlist.push_back(report_not_equal("whole plant rm", "plant rm PART", ip,
                  cohort.bd[ip].m_v2a.rmall,
                  cohort.bd[ip].m_v2a.rm[I_leaf] +
                  cohort.bd[ip].m_v2a.rm[I_stem] +
                  cohort.bd[ip].m_v2a.rm[I_root]));

    errlist.push_back(report_not_equal("whole plant rg", "plant rg PART", ip,
                  cohort.bd[ip].m_v2a.rgall,
                  cohort.bd[ip].m_v2a.rg[I_leaf] +
                  cohort.bd[ip].m_v2a.rg[I_stem] +
                  cohort.bd[ip].m_v2a.rg[I_root]));

    errlist.push_back(report_not_equal("whole plant N litterfall", "plant N litterfall PART", ip,
                  cohort.bd[ip].m_v2soi.ltrfalnall + cohort.bd[ip].m_v2soi.mossdeathn,
                  cohort.bd[ip].m_v2soi.ltrfaln[I_leaf] +
                  cohort.bd[ip].m_v2soi.ltrfaln[I_stem] +
                  cohort.bd[ip].m_v2soi.ltrfaln[I_root]));

    errlist.push_back(report_not_equal("whole plant C litterfall", "plant C litterfall PART", ip,
                  cohort.bd[ip].m_v2soi.ltrfalcall + cohort.bd[ip].m_v2soi.mossdeathc,
                  cohort.bd[ip].m_v2soi.ltrfalc[I_leaf] +
                  cohort.bd[ip].m_v2soi.ltrfalc[I_stem] +
                  cohort.bd[ip].m_v2soi.ltrfalc[I_root]));

    errlist.push_back(report_not_equal("whole plant snuptake", "plant snuptake PART", ip,
                  cohort.bd[ip].m_soi2v.snuptakeall,
                  cohort.bd[ip].m_soi2v.snuptake[I_leaf] +
                  cohort.bd[ip].m_soi2v.snuptake[I_stem] +
                  cohort.bd[ip].m_soi2v.snuptake[I_root]));

    errlist.push_back(report_not_equal("whole plant nmobil", "plant nmobil PART", ip,
                  cohort.bd[ip].m_v2v.nmobilall,
                  cohort.bd[ip].m_v2v.nmobil[I_leaf] +
                  cohort.bd[ip].m_v2v.nmobil[I_stem] +
                  cohort.bd[ip].m_v2v.nmobil[I_root]));

    errlist.push_back(report_not_equal("whole plant nresorb", "plant nresorb PART", ip,
                  cohort.bd[ip].m_v2v.nresorball,
                  cohort.bd[ip].m_v2v.nresorb[I_leaf] +
                  cohort.bd[ip].m_v2v.nresorb[I_stem] +
                  cohort.bd[ip].m_v2v.nresorb[I_root]));

  } // end loop over PFTS

  // The way this works, we end up with a bunch of empty items in the list,
  // so here we remove them.
  errlist.erase(std::remove_if(errlist.begin(), errlist.end(), temutil::emptyContainer<std::string>), errlist.end());

  return errlist;
}

/** Sum across PFTs, compare with ecosystem totals (eg data from 'bdall').

Used to add up across all pfts (data held in cohort's bd array of BgcData objects)
and compare with the data held in cohort's bdall BgcData object.
*/
std::list<std::string> Runner::check_sum_over_PFTs(){

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

  std::list<std::string> errlist;

  // Check that the sums are equal to the Runner level containers (ecosystem totals)
  errlist.push_back(report_not_equal(this->cohort.bdall->m_vegs.call, ecosystem_C, "Runner:: ecosystem veg C not matching sum over PFTs!"));
  errlist.push_back(report_not_equal(this->cohort.bdall->m_vegs.call, ecosystem_C_by_compartment, "Runner:: ecosystem veg C not matching sum over compartments"));

  errlist.push_back(report_not_equal(this->cohort.bdall->m_vegs.nall, ecosystem_N, "Runner:: ecosystem nall not matching sum over PFTs (of strn and nall)!"));
  errlist.push_back(report_not_equal(this->cohort.bdall->m_vegs.labn, ecosystem_labn, "Runner:: ecosystem labn not matching sum over PFTs!"));
  errlist.push_back(report_not_equal(this->cohort.bdall->m_vegs.strnall, ecosystem_strn, "Runner:: ecosystem strn not matching sum over PFTs!"));
  errlist.push_back(report_not_equal(this->cohort.bdall->m_vegs.strnall, ecosystem_strn_by_compartment, "Runner:: ecosystem strn not matching sum over compartments!"));

  errlist.push_back(report_not_equal(this->cohort.bdall->m_a2v.ingppall, ecosystem_ingpp, "Runner:: ecosystem npp not matching sum over PFTs!"));
  errlist.push_back(report_not_equal(this->cohort.bdall->m_a2v.gppall, ecosystem_gpp, "Runner:: ecosystem npp not matching sum over PFTs!"));
  errlist.push_back(report_not_equal(this->cohort.bdall->m_a2v.innppall, ecosystem_innpp, "Runner:: ecosystem innpp not matching sum over PFTs!"));
  errlist.push_back(report_not_equal(this->cohort.bdall->m_a2v.nppall, ecosystem_npp, "Runner:: ecosystem npp not matching sum over PFTs!"));

  errlist.push_back(report_not_equal(this->cohort.bdall->m_v2a.rmall, ecosystem_rm, "Runner:: ecosystem rm not matching sum over PFTs!"));
  errlist.push_back(report_not_equal(this->cohort.bdall->m_v2a.rgall, ecosystem_rg, "Runner:: ecosystem rg not matching sum over PFTs!"));

  errlist.push_back(report_not_equal(this->cohort.bdall->m_v2soi.ltrfalcall, ecosystem_ltrfalc, "Runner:: ecosystem ltrfalc not matching sum over PFTs!"));
  errlist.push_back(report_not_equal(this->cohort.bdall->m_v2soi.ltrfalnall, ecosystem_ltrfaln, "Runner:: ecosystem ltrfaln not matching sum over PFTs!"));

  errlist.push_back(report_not_equal(this->cohort.bdall->m_soi2v.snuptakeall, ecosystem_snuptake, "Runner:: ecosystem snuptake not matching sum over PFTs!"));

  errlist.push_back(report_not_equal(this->cohort.bdall->m_v2v.nmobilall, ecosystem_nmobil, "Runner:: ecosystem nmobil not matching sum over PFTs!"));
  errlist.push_back(report_not_equal(this->cohort.bdall->m_v2v.nresorball, ecosystem_nresorb, "Runner:: ecosystem nresorb not matching sum over PFTs!"));

  // The way this works, we end up with a bunch of empty items in the list,
  // so here we remove them.
  errlist.erase(std::remove_if(errlist.begin(), errlist.end(), temutil::emptyContainer<std::string>), errlist.end());

  return errlist;

}

void Runner::output_caljson_monthly(int year, int month, std::string stage, boost::filesystem::path p){

  std::list<std::string> compartment_err_report = check_sum_over_compartments();
  std::list<std::string> pft_err_report = check_sum_over_PFTs();


  if ( !compartment_err_report.empty() || !pft_err_report.empty() ) {
    BOOST_LOG_SEV(glg, warn) << "========== MONTHLY CHECKSUM ERRORS ============";
    while (!compartment_err_report.empty()) {
      BOOST_LOG_SEV(glg, warn) << compartment_err_report.front();
      compartment_err_report.pop_front();
    }
    while ( !(pft_err_report.empty()) ){
      BOOST_LOG_SEV(glg, warn) << pft_err_report.front();
      pft_err_report.pop_front();
    }
    BOOST_LOG_SEV(glg, warn) << "========== END MONTHLY CHECKSUMMING month: " << month << " year: " << year << " ============";
  }


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
  data["DynLaiModule"] = this->cohort.md->get_dynamic_lai_module();
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

  double t = 0.0;
  for (int il=0; il < MAX_SOI_LAY; il++) {
    t += cohort.bdall->m_soi2v.nextract[il];
  }
  data["NExtract"] = t;
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
  data["RH"] = cohort.bdall->m_soi2a.rhsom;

  // Add up Respiration_maintenance and Respiration_growth for all PFTs
  double rh_veg;
  double gpp_all_veg;
  rh_veg = 0;
  gpp_all_veg = 0;
  for(int pft=0; pft<NUM_PFT; pft++) {
    rh_veg += cohort.bd[pft].m_v2a.rg[I_leaf];
    rh_veg += cohort.bd[pft].m_v2a.rg[I_stem];
    rh_veg += cohort.bd[pft].m_v2a.rg[I_root];
    rh_veg += cohort.bd[pft].m_v2a.rm[I_leaf];
    rh_veg += cohort.bd[pft].m_v2a.rm[I_stem];
    rh_veg += cohort.bd[pft].m_v2a.rm[I_root];

    gpp_all_veg += cohort.bd[pft].m_a2v.gppall;
  }
  // RE, aka Respiration_ecosystem or Ecosystem Respiration or ER
  data["RE"] = cohort.bdall->m_soi2a.rhsom + rh_veg;

  // NEE, aka Net Ecosystem Exchange
  data["NEE"] = gpp_all_veg - (cohort.bdall->m_soi2a.rhsom + rh_veg);

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
  data["BurnAir2SoilN"] = cohort.year_fd[month].fire_a2soi.orgn;
  data["BurnAbvVeg2DeadC"] = cohort.year_fd[month].fire_v2dead.vegC;
  data["BurnAbvVeg2DeadN"] = cohort.year_fd[month].fire_v2dead.strN;
  data["RawCSum"] = cohort.bdall->m_soid.rawcsum;
  data["SomaSum"] = cohort.bdall->m_soid.somasum;
  data["SomcrSum"] = cohort.bdall->m_soid.somcrsum;
  data["SomprSum"] = cohort.bdall->m_soid.somprsum;


  /* PFT dependent variables */

  // calculated ecosystem summary values
  double litterfallCsum = 0;
  double litterfallNsum = 0;
  double parDownSum = 0;
  double parAbsorbSum = 0;

  for(int pft=0; pft<NUM_PFT; pft++) {
    char pft_chars[10];
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
    data["PFT" + pft_str]["GPP"]["Leaf"] = cohort.bd[pft].m_a2v.gpp[I_leaf];
    data["PFT" + pft_str]["GPP"]["Stem"] = cohort.bd[pft].m_a2v.gpp[I_stem];
    data["PFT" + pft_str]["GPP"]["Root"] = cohort.bd[pft].m_a2v.gpp[I_root];

    data["PFT" + pft_str]["NPPAll"] = cohort.bd[pft].m_a2v.nppall;
    data["PFT" + pft_str]["NPP"]["Leaf"] = cohort.bd[pft].m_a2v.npp[I_leaf];
    data["PFT" + pft_str]["NPP"]["Stem"] = cohort.bd[pft].m_a2v.npp[I_stem];
    data["PFT" + pft_str]["NPP"]["Root"] = cohort.bd[pft].m_a2v.npp[I_root];

    data["PFT" + pft_str]["GPPAllIgnoringNitrogen"] = cohort.bd[pft].m_a2v.ingppall;
    data["PFT" + pft_str]["NPPAllIgnoringNitrogen"] = cohort.bd[pft].m_a2v.innppall;

    data["PFT" + pft_str]["LitterfallCarbonAll"] = cohort.bd[pft].m_v2soi.ltrfalcall;
    data["PFT" + pft_str]["LitterfallCarbon"]["Leaf"] = cohort.bd[pft].m_v2soi.ltrfalc[I_leaf];
    data["PFT" + pft_str]["LitterfallCarbon"]["Stem"] = cohort.bd[pft].m_v2soi.ltrfalc[I_stem];
    data["PFT" + pft_str]["LitterfallCarbon"]["Root"] = cohort.bd[pft].m_v2soi.ltrfalc[I_root];

    data["PFT" + pft_str]["RespGrowth"]["Leaf"] = cohort.bd[pft].m_v2a.rg[I_leaf];
    data["PFT" + pft_str]["RespGrowth"]["Stem"] = cohort.bd[pft].m_v2a.rg[I_stem];
    data["PFT" + pft_str]["RespGrowth"]["Root"] = cohort.bd[pft].m_v2a.rg[I_root];

    data["PFT" + pft_str]["RespMaint"]["Leaf"] = cohort.bd[pft].m_v2a.rm[I_leaf];
    data["PFT" + pft_str]["RespMaint"]["Stem"] = cohort.bd[pft].m_v2a.rm[I_stem];
    data["PFT" + pft_str]["RespMaint"]["Root"] = cohort.bd[pft].m_v2a.rm[I_root];

    data["PFT" + pft_str]["LitterfallNitrogenPFT"] = cohort.bd[pft].m_v2soi.ltrfalnall;
    data["PFT" + pft_str]["LitterfallNitrogen"]["Leaf"] = cohort.bd[pft].m_v2soi.ltrfaln[I_leaf];
    data["PFT" + pft_str]["LitterfallNitrogen"]["Stem"] = cohort.bd[pft].m_v2soi.ltrfaln[I_stem];
    data["PFT" + pft_str]["LitterfallNitrogen"]["Root"] = cohort.bd[pft].m_v2soi.ltrfaln[I_root];

    data["PFT" + pft_str]["StNitrogenUptake"] = cohort.bd[pft].m_soi2v.snuptakeall;
    data["PFT" + pft_str]["InNitrogenUptake"] = cohort.bd[pft].m_soi2v.innuptake;
    data["PFT" + pft_str]["LabNitrogenUptake"] = cohort.bd[pft].m_soi2v.lnuptake;
    data["PFT" + pft_str]["TotNitrogenUptake"] = cohort.bd[pft].m_soi2v.snuptakeall + cohort.bd[pft].m_soi2v.lnuptake;
    data["PFT" + pft_str]["MossDeathC"] = cohort.bd[pft].m_v2soi.mossdeathc;

    litterfallCsum += cohort.bd[pft].m_v2soi.ltrfalcall;
    litterfallNsum += cohort.bd[pft].m_v2soi.ltrfalnall;

    data["PFT" + pft_str]["PARDown"] = cohort.ed[pft].m_a2v.pardown;
    data["PFT" + pft_str]["PARAbsorb"] = cohort.ed[pft].m_a2v.parabsorb;

    parDownSum += cohort.ed[pft].m_a2v.pardown;
    parAbsorbSum += cohort.ed[pft].m_a2v.parabsorb;

  }

  data["LitterfallCsum"] = litterfallCsum;
  data["LitterfallNsum"] = litterfallNsum;

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

  std::list<std::string> compartment_err_report = check_sum_over_compartments();
  std::list<std::string> pft_err_report = check_sum_over_PFTs();

  if ( !compartment_err_report.empty() || !pft_err_report.empty() ) {
    BOOST_LOG_SEV(glg, warn) << "========== YEARLY CHECKSUM ERRORS ============";
    while (!compartment_err_report.empty()) {
      BOOST_LOG_SEV(glg, warn) << compartment_err_report.front();
      compartment_err_report.pop_front();
    }
    while ( !(pft_err_report.empty()) ){
      BOOST_LOG_SEV(glg, warn) << pft_err_report.front();
      pft_err_report.pop_front();
    }
    BOOST_LOG_SEV(glg, warn) << "========== END YEARLY CHECKSUMMING year: " << year << " ============";
  }

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
  data["DynLaiModule"] = this->cohort.md->get_dynamic_lai_module();
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

  double t = 0.0;
  for (int il=0; il < MAX_SOI_LAY; il++) {
    t += cohort.bdall->m_soi2v.nextract[il];
  }
  data["NExtract"] = t;
  data["NetNMin"] = cohort.bdall->y_soi2soi.netnminsum;
  data["NetNImmob"] = cohort.bdall->y_soi2soi.nimmobsum;
  data["OrgNInput"] = cohort.bdall->y_a2soi.orgninput;
  data["AvlNInput"] = cohort.bdall->y_a2soi.avlninput;
  data["AvlNLost"] = cohort.bdall->y_soi2l.avlnlost;
  data["RHraw"] = cohort.bdall->y_soi2a.rhrawcsum;
  data["RHsoma"] = cohort.bdall->y_soi2a.rhsomasum;
  data["RHsompr"] = cohort.bdall->y_soi2a.rhsomprsum;
  data["RHsomcr"] = cohort.bdall->y_soi2a.rhsomcrsum;
  data["RH"] = cohort.bdall->y_soi2a.rhsom;
 
  // Add up Respiration_maintenance and Respiration_growth for all PFTs
  double rh_veg;
  double gpp_all_veg;
  rh_veg = 0;
  gpp_all_veg = 0;
  for(int pft=0; pft<NUM_PFT; pft++) {
    rh_veg += cohort.bd[pft].y_v2a.rg[I_leaf];
    rh_veg += cohort.bd[pft].y_v2a.rg[I_stem];
    rh_veg += cohort.bd[pft].y_v2a.rg[I_root];
    rh_veg += cohort.bd[pft].y_v2a.rm[I_leaf];
    rh_veg += cohort.bd[pft].y_v2a.rm[I_stem];
    rh_veg += cohort.bd[pft].y_v2a.rm[I_root];

    gpp_all_veg += cohort.bd[pft].y_a2v.gppall;
  }
  // RE, aka Respiration_ecosystem or Ecosystem Respiration or ER
  data["RE"] = cohort.bdall->y_soi2a.rhsom + rh_veg;

  // NEE, aka Net Ecosystem Exchange
  data["NEE"] = gpp_all_veg - (cohort.bdall->y_soi2a.rhsom + rh_veg);

  //Placeholders for summing fire variables for the entire year
  double burnthick = 0.0, veg2airc = 0.0, veg2airn = 0.0, veg2soiabvvegc=0.0, veg2soiabvvegn = 0.0, veg2soiblwvegc = 0.0, veg2soiblwvegn = 0.0, veg2deadc = 0.0, veg2deadn = 0.0, soi2airc = 0.0, soi2airn = 0.0, air2soin = 0.0;
 
  for(int im=0; im<12; im++){
    char mth_chars[10];
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
  data["BurnAir2SoilN"] = air2soin;
  data["BurnAbvVeg2DeadC"] = veg2deadc;
  data["BurnAbvVeg2DeadN"] = veg2deadn;

  //Calculated sums
  double litterfallCsum = 0;
  double litterfallNsum = 0;

  for(int pft=0; pft<NUM_PFT; pft++) { //NUM_PFT
    char pft_chars[10];
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
    data["PFT" + pft_str]["GPP"]["Leaf"] = cohort.bd[pft].y_a2v.gpp[I_leaf];
    data["PFT" + pft_str]["GPP"]["Stem"] = cohort.bd[pft].y_a2v.gpp[I_stem];
    data["PFT" + pft_str]["GPP"]["Root"] = cohort.bd[pft].y_a2v.gpp[I_root];

    data["PFT" + pft_str]["NPPAll"] = cohort.bd[pft].y_a2v.nppall;
    data["PFT" + pft_str]["NPP"]["Leaf"] = cohort.bd[pft].y_a2v.npp[I_leaf];
    data["PFT" + pft_str]["NPP"]["Stem"] = cohort.bd[pft].y_a2v.npp[I_stem];
    data["PFT" + pft_str]["NPP"]["Root"] = cohort.bd[pft].y_a2v.npp[I_root];

    data["PFT" + pft_str]["GPPAllIgnoringNitrogen"] = cohort.bd[pft].y_a2v.ingppall;
    data["PFT" + pft_str]["NPPAllIgnoringNitrogen"] = cohort.bd[pft].y_a2v.innppall;

    data["PFT" + pft_str]["LitterfallCarbonAll"] = cohort.bd[pft].y_v2soi.ltrfalcall;
    data["PFT" + pft_str]["LitterfallCarbon"]["Leaf"] = cohort.bd[pft].y_v2soi.ltrfalc[I_leaf];
    data["PFT" + pft_str]["LitterfallCarbon"]["Stem"] = cohort.bd[pft].y_v2soi.ltrfalc[I_stem];
    data["PFT" + pft_str]["LitterfallCarbon"]["Root"] = cohort.bd[pft].y_v2soi.ltrfalc[I_root];

    data["PFT" + pft_str]["RespGrowth"]["Leaf"] = cohort.bd[pft].y_v2a.rg[I_leaf];
    data["PFT" + pft_str]["RespGrowth"]["Stem"] = cohort.bd[pft].y_v2a.rg[I_stem];
    data["PFT" + pft_str]["RespGrowth"]["Root"] = cohort.bd[pft].y_v2a.rg[I_root];

    data["PFT" + pft_str]["RespMaint"]["Leaf"] = cohort.bd[pft].y_v2a.rm[I_leaf];
    data["PFT" + pft_str]["RespMaint"]["Stem"] = cohort.bd[pft].y_v2a.rm[I_stem];
    data["PFT" + pft_str]["RespMaint"]["Root"] = cohort.bd[pft].y_v2a.rm[I_root];

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

    litterfallCsum += cohort.bd[pft].y_v2soi.ltrfalcall; 
    litterfallNsum += cohort.bd[pft].y_v2soi.ltrfalnall;

  }

  data["LitterfallCsum"] = litterfallCsum;
  data["LitterfallNsum"] = litterfallNsum;

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


void Runner::output_netCDF_monthly(int year, int month, std::string stage, int endyr){

    BOOST_LOG_SEV(glg, debug)<<"NetCDF monthly output, year: "<<year<<" month: "<<month;
    output_netCDF(md.monthly_netcdf_outputs, year, month, stage, endyr);

    BOOST_LOG_SEV(glg, debug)<<"Outputting accumulated daily data on the monthly timestep";
    output_netCDF(md.daily_netcdf_outputs, year, month, stage, endyr);
}

void Runner::output_netCDF_yearly(int year, std::string stage, int endyr){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF yearly output, year: "<<year;
    output_netCDF(md.yearly_netcdf_outputs, year, 11, stage, endyr);
}


template <typename PTYPE>
void Runner::output_nc_3dim(OutputSpec* out_spec, std::string stage_suffix,
                            PTYPE data, int max_var_count,
                            int start_timestep, int timesteps){
  BOOST_LOG_SEV(glg, debug)<<"output_nc_3dim, var: "<<out_spec->var_name;
  //timestep, row, col
  size_t datastart[3];
  datastart[0] = start_timestep;
  datastart[1] = this->y;
  datastart[2] = this->x;

  size_t datacount[3];
  datacount[0] = timesteps;
  datacount[1] = 1;
  datacount[2] = 1;

  int ncid, cv;
  std::string output_filename = out_spec->file_path + out_spec->filename_prefix + stage_suffix;

  BOOST_LOG_SEV(glg, debug) << "Opening output file: " << output_filename;

#ifdef WITHMPI
  temutil::nc( nc_open_par(output_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
#else
  temutil::nc( nc_open(output_filename.c_str(), NC_WRITE, &ncid) );
#endif

  temutil::nc( nc_inq_varid(ncid, out_spec->var_name.c_str(), &cv) );
  BOOST_LOG_SEV(glg, debug)<<"inq_varid completed";

#ifdef WITHMPI
  temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#endif

  temutil::nc( nc_put_vara(ncid, cv, datastart, datacount, data) );
  BOOST_LOG_SEV(glg, debug)<<"put_vara completed";

  temutil::nc( nc_close(ncid) );
  BOOST_LOG_SEV(glg, debug)<<"close completed";
}


template <typename PTYPE>
void Runner::output_nc_4dim(OutputSpec* out_spec, std::string stage_suffix,
                            PTYPE data, int max_var_count,
                            int start_timestep, int timesteps){
  BOOST_LOG_SEV(glg, debug)<<"output_nc_4dim, var: "<<out_spec->var_name;
  //timestep, layer, row, col
  size_t datastart[4];
  datastart[0] = start_timestep;
  datastart[1] = 0;
  datastart[2] = this->y;
  datastart[3] = this->x;

  size_t datacount[4];
  datacount[0] = timesteps;
  datacount[1] = max_var_count;
  datacount[2] = 1;
  datacount[3] = 1;

  int ncid, cv;
  std::string output_filename = out_spec->file_path + out_spec->filename_prefix + stage_suffix;

  BOOST_LOG_SEV(glg, debug) << "Opening output file: " << output_filename;

#ifdef WITHMPI
  temutil::nc( nc_open_par(output_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
#else
  temutil::nc( nc_open(output_filename.c_str(), NC_WRITE, &ncid) );
#endif

  temutil::nc( nc_inq_varid(ncid, out_spec->var_name.c_str(), &cv) );

#ifdef WITHMPI
  temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#endif

  temutil::nc( nc_put_vara(ncid, cv, datastart, datacount, data) );

  temutil::nc( nc_close(ncid) );
}


template <typename PTYPE>
void Runner::output_nc_5dim(OutputSpec* out_spec, std::string stage_suffix,
                            PTYPE data, int max_var_count_1,
                            int max_var_count_2,
                            int start_timestep, int timesteps){
  BOOST_LOG_SEV(glg, debug)<<"output_nc_5dim, var: "<<out_spec->var_name;
  //timestep, compartment, pft, row, col
  size_t datastart[5];
  datastart[0] = start_timestep;
  datastart[1] = 0;
  datastart[2] = 0;
  datastart[3] = this->y;
  datastart[4] = this->x;

  size_t datacount[5];
  datacount[0] = timesteps; 
  datacount[1] = max_var_count_1;
  datacount[2] = max_var_count_2;
  datacount[3] = 1;
  datacount[4] = 1;

  int ncid, cv;
  std::string output_filename = out_spec->file_path + out_spec->filename_prefix + stage_suffix;

  BOOST_LOG_SEV(glg, debug) << "Opening output file: " << output_filename;

#ifdef WITHMPI
  temutil::nc( nc_open_par(output_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
#else
  temutil::nc( nc_open(output_filename.c_str(), NC_WRITE, &ncid) );
#endif

  temutil::nc( nc_inq_varid(ncid, out_spec->var_name.c_str(), &cv) );

#ifdef WITHMPI
  temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#endif

  temutil::nc( nc_put_vara(ncid, cv, datastart, datacount, data) );

  temutil::nc( nc_close(ncid) );
}


/* Some of the following outputs are written out at the timesteps
 * they have specified in the output_spec file, but some have
 * been converted to write to an OutputHolder in order to reduce
 * the amount of file I/O that occurs during a large run. The period
 * of time to hold data is specified in the config file. */
void Runner::output_netCDF(std::map<std::string, OutputSpec> &netcdf_outputs, int year, int month, std::string stage, int endyr){
  int month_timestep = year*12 + month;

  int day_timestep = year*365;
//This was needed when we output daily data on a monthly basis.
//It should likely be removed.
//  for(int im=0; im<month; im++){
//    day_timestep += DINM[im];
//  }

  //For outputting subsets of driving data arrays
  int doy = temutil::day_of_year(month, 0); 

  int output_interval = md.output_interval;//years

  int yearcount = year+1;//To differentiate from year index

  bool output_this_timestep = false;
  int years_to_output;
  int months_to_output;

  //This does not currently need to be a variable, but it might
  // be useful in the future.
  bool end_of_year = false;
  if((month_timestep+1)%12==0){
    end_of_year = true;
  }

  //At the end of an output interval and end of the year
  if((yearcount%output_interval==0) && end_of_year){
    output_this_timestep = true;
    years_to_output = output_interval;
    months_to_output = output_interval*12;
  }
  //For when the years in a stage are not evenly divisible
  // by the output interval
  else if((yearcount==endyr) && end_of_year){
    output_this_timestep = true;
    years_to_output = yearcount%output_interval;
    months_to_output = years_to_output*12;
  }
  int year_start_idx = yearcount-years_to_output;
  int month_start_idx = month_timestep-months_to_output+1;

  std::string file_stage_suffix;
  if(stage.find("eq")!=std::string::npos){
    file_stage_suffix = "_eq.nc";
  }
  else if(stage.find("sp")!=std::string::npos){
    file_stage_suffix = "_sp.nc";
  }
  else if(stage.find("tr")!=std::string::npos){
    file_stage_suffix = "_tr.nc";
  }
  else if(stage.find("sc")!=std::string::npos){
    file_stage_suffix = "_sc.nc";
  }

  std::string curr_filename;

  int dinm = DINM[month];

  int rowidx = this->y;
  int colidx = this->x;

  OutputSpec curr_spec;
  std::map<std::string, OutputSpec>::iterator map_itr;

  //ALD
  map_itr = netcdf_outputs.find("ALD");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: ALD";
    curr_spec = map_itr->second;

    //Store data intended for output
    outhold.ald_for_output.push_back(cohort.edall->y_soid.ald);

    //If set to output this timestep, do so
    if(output_this_timestep){
      #pragma omp critical(outputALD)
      {
        output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.ald_for_output[0], 1, year_start_idx, years_to_output);
        outhold.ald_for_output.clear();
      }//end critical(outputALD)
    }
  }//end ALD
  map_itr = netcdf_outputs.end();


  //AVLN
  map_itr = netcdf_outputs.find("AVLN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: AVLN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputAVLN)
    {
      //By layer
      if(curr_spec.layer){
        std::array<double, MAX_SOI_LAY> avln_arr{};

        //monthly
        if(curr_spec.monthly){
          for(int il=0; il<MAX_SOI_LAY; il++){
            avln_arr[il] = cohort.bdall->m_sois.avln[il];
          }
          outhold.avln_for_output.push_back(avln_arr);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.avln_for_output[0], MAX_SOI_LAY, month_start_idx, months_to_output);
            outhold.avln_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          for(int il=0; il<MAX_SOI_LAY; il++){
            avln_arr[il] = cohort.bdall->y_sois.avln[il];
          }
          outhold.avln_for_output.push_back(avln_arr);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.avln_for_output[0], MAX_SOI_LAY, year_start_idx, years_to_output);
            outhold.avln_for_output.clear();
          }
        }
      }
      //Total
      else if(!curr_spec.layer){
        //monthly
        if(curr_spec.monthly){
          outhold.avln_tot_for_output.push_back(cohort.bdall->m_soid.avlnsum);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.avln_tot_for_output[0], 1, month_start_idx, months_to_output);
            outhold.avln_tot_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.avln_tot_for_output.push_back(cohort.bdall->y_soid.avlnsum);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.avln_tot_for_output[0], 1, year_start_idx, years_to_output);
            outhold.avln_tot_for_output.clear();
          }
        }
      }
    }//end critical(outputAVLN)
  }//end AVLN
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("BURNAIR2SOILN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNAIR2SOILN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputBURNAIR2SOILN)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.year_fd[month].fire_a2soi.orgn, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        double burnair2soiln = 0.;
        for(int im=0; im<12; im++){
          burnair2soiln += cohort.year_fd[im].fire_a2soi.orgn;
        }
        output_nc_3dim(&curr_spec, file_stage_suffix, &burnair2soiln, 1, year, 1);
      }
    }//end critical(outputBURNAIR2SOILN)
  }//end BURNAIR2SOILN
  map_itr = netcdf_outputs.end();


  //Burned soil carbon
  map_itr = netcdf_outputs.find("BURNSOIL2AIRC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNSOIL2AIRC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputBURNSOIL2AIRC)
    {
      //By layer
      if(curr_spec.layer){
        /*** STUB ***/
        //By-layer may not be feasible yet.
      }
      //Total
      else if(!curr_spec.layer){
        //monthly
        if(curr_spec.monthly){
          outhold.burnsoil2airc_for_output.push_back(cohort.year_fd[month].fire_soi2a.orgc);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.burnsoil2airc_for_output[0], 1, month_start_idx, months_to_output);
            outhold.burnsoil2airc_for_output.clear();
          }
        }
        else if(curr_spec.yearly){
          double burnsoilC = 0.;
          for(int im=0; im<12; im++){
            burnsoilC += cohort.year_fd[im].fire_soi2a.orgc;
          }
          outhold.burnsoil2airc_for_output.push_back(burnsoilC);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.burnsoil2airc_for_output[0], 1, year_start_idx, years_to_output);
            outhold.burnsoil2airc_for_output.clear();
          }
        }
      }
    }//end critical(outputBURNSOIL2AIRC)
  }//end BURNSOIL2AIRC
  map_itr = netcdf_outputs.end();


  //Burned soil nitrogen 
  map_itr = netcdf_outputs.find("BURNSOIL2AIRN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNSOIL2AIRN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputBURNSOIL2AIRN)
    {
      //By layer
      if(curr_spec.layer){
        /*** STUB ***/
      }
      //Total
      else if(!curr_spec.layer){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.year_fd[month].fire_soi2a.orgn, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          double burnSoilN = 0.;
          for(int im=0; im<12; im++){
            burnSoilN += cohort.year_fd[im].fire_soi2a.orgn;
          }
          output_nc_3dim(&curr_spec, file_stage_suffix, &burnSoilN, 1, year, 1);
        }
      }
    }//end critical(outputBURNSOIL2AIRN)
  }//end BURNSOIL2AIRN
  map_itr = netcdf_outputs.end();


  //Burn thickness
  map_itr = netcdf_outputs.find("BURNTHICK");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNTHICK";
    curr_spec = map_itr->second;

    #pragma omp critical(outputBURNTHICK)
    {
      //monthly
      if(curr_spec.monthly){
        outhold.burnthick_for_output.push_back(cohort.year_fd[month].fire_soid.burnthick);
        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.burnthick_for_output[0], 1, month_start_idx, months_to_output);
          outhold.burnthick_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        double burnthick = 0.;
        for(int im=0; im<12; im++){
          burnthick += cohort.year_fd[im].fire_soid.burnthick;
        }
        outhold.burnthick_for_output.push_back(burnthick);
        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.burnthick_for_output[0], 1, year_start_idx, years_to_output);
          outhold.burnthick_for_output.clear();
        }
      }
    }//end critical(outputBURNTHICK)
  }//end BURNTHICK
  map_itr = netcdf_outputs.end();


  //BURNVEG2AIRC
  map_itr = netcdf_outputs.find("BURNVEG2AIRC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNVEG2AIRC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputBURNVEG2AIRC)
    {
      //monthly
      if(curr_spec.monthly){
        outhold.burnveg2airc_for_output.push_back(cohort.year_fd[month].fire_v2a.orgc);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.burnveg2airc_for_output[0], 1, month_start_idx, months_to_output);
          outhold.burnveg2airc_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        double yearly_v2a_orgc = 0.0;
        for(int im=0; im<MINY; im++){
          yearly_v2a_orgc += cohort.year_fd[im].fire_v2a.orgc;
        }
        outhold.burnveg2airc_for_output.push_back(yearly_v2a_orgc);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.burnveg2airc_for_output[0], 1, year_start_idx, years_to_output);
          outhold.burnveg2airc_for_output.clear();
        }
      }
    }//end critical(outputBURNVEG2AIRC)
  }//end BURNVEG2AIRC
  map_itr = netcdf_outputs.end();


  //BURNVEG2AIRN
  map_itr = netcdf_outputs.find("BURNVEG2AIRN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNVEG2AIRN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputBURNVEG2AIRN)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.year_fd[month].fire_v2a.orgn, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.fd->fire_v2a.orgn, 1, year, 1);
      }
    }//end critical(outputBURNVEG2AIRN)
  }//end BURNVEG2AIRN
  map_itr = netcdf_outputs.end();


  //BURNVEG2DEADC
  map_itr = netcdf_outputs.find("BURNVEG2DEADC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNVEG2DEADC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputBURNVEG2DEADC)
    {
      //monthly
      if(curr_spec.monthly){
        outhold.burnveg2deadc_for_output.push_back(cohort.year_fd[month].fire_v2dead.vegC);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.burnveg2deadc_for_output[0], 1, month_start_idx, months_to_output);
          outhold.burnveg2deadc_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        outhold.burnveg2deadc_for_output.push_back(cohort.fd->fire_v2dead.vegC);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.burnveg2deadc_for_output[0], 1, year_start_idx, years_to_output);
          outhold.burnveg2deadc_for_output.clear();
        }
      }
    }//end critical(outputBURNVEG2DEADC)
  }//end BURNVEG2DEADC
  map_itr = netcdf_outputs.end();


  //BURNVEG2DEADN
  map_itr = netcdf_outputs.find("BURNVEG2DEADN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNVEG2DEADN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputBURNVEG2DEADN)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.year_fd[month].fire_v2dead.strN, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.fd->fire_v2dead.strN, 1, year, 1);
      }
    }//end critical(outputBURNVEG2DEADN)
  }//end BURNVEG2DEADN
  map_itr = netcdf_outputs.end();


  //BURNVEG2SOILABVC
  map_itr = netcdf_outputs.find("BURNVEG2SOILABVC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNVEG2SOILABVC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputBURNVEG2SOILABVC)
    {
      //monthly
      if(curr_spec.monthly){
        outhold.burnveg2soilabvc_for_output.push_back(cohort.year_fd[month].fire_v2soi.abvc);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.burnveg2soilabvc_for_output[0], 1, month_start_idx, months_to_output);
          outhold.burnveg2soilabvc_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        outhold.burnveg2soilabvc_for_output.push_back(cohort.fd->fire_v2soi.abvc);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.burnveg2soilabvc_for_output[0], 1, year_start_idx, years_to_output);
          outhold.burnveg2soilabvc_for_output.clear();
        }
      }
    }//end critical(outputBURNVEG2SOILABVC)
  }//end BURNVEG2SOILABVC
  map_itr = netcdf_outputs.end();


  //BURNVEG2SOILABVN
  map_itr = netcdf_outputs.find("BURNVEG2SOILABVN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNVEG2SOILABVN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputBURNVEG2SOILABVN)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.year_fd[month].fire_v2soi.abvn, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.fd->fire_v2soi.abvn, 1, year, 1);
      }
    }//end critical(outputBURNVEG2SOILABVN)
  }//end BURNVEG2SOILABVN
  map_itr = netcdf_outputs.end();


  //BURNVEG2SOILBLWC
  map_itr = netcdf_outputs.find("BURNVEG2SOILBLWC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNVEG2SOILBLWC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputBURNVEG2SOILBLWC)
    {
      //monthly
      if(curr_spec.monthly){
        outhold.burnveg2soilblwc_for_output.push_back(cohort.year_fd[month].fire_v2soi.blwc);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.burnveg2soilblwc_for_output[0], 1, month_start_idx, months_to_output);
          outhold.burnveg2soilblwc_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        outhold.burnveg2soilblwc_for_output.push_back(cohort.fd->fire_v2soi.blwc);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.burnveg2soilblwc_for_output[0], 1, year_start_idx, years_to_output);
          outhold.burnveg2soilblwc_for_output.clear();
        }
      }
    }//end critical(outputBURNVEG2SOILBLWC)
  }//end BURNVEG2SOILBLWC
  map_itr = netcdf_outputs.end();


  //BURNVEG2SOILBLWN
  map_itr = netcdf_outputs.find("BURNVEG2SOILBLWN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNVEG2SOILBLWN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputBURNVEG2SOILBLWN)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.year_fd[month].fire_v2soi.blwn, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.fd->fire_v2soi.blwn, 1, year, 1);
      }
    }//end critical(outputBURNVEG2SOILBLWN)
  }//end BURNVEG2SOILBLWN
  map_itr = netcdf_outputs.end();


  //Community Type Code (CMT NUMBER)
  map_itr = netcdf_outputs.find("CMTNUM");
  if(map_itr != netcdf_outputs.end()) {
    BOOST_LOG_SEV(glg, debug) << "NetCDF output: CMTNUM";
    curr_spec = map_itr->second;
    #pragma omp critical(outputCMTNUM)
    {
      int cmtnum;
      cmtnum = temutil::cmtcode2num(this->cohort.chtlu.cmtcode);

      outhold.cmtnum_for_output.push_back(cmtnum);

      if(output_this_timestep){
        output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.cmtnum_for_output[0], 1, year_start_idx, years_to_output);
        outhold.cmtnum_for_output.clear();
      }
    } //end critical(outputCMTNUM)
  } //end CMTNUM
  map_itr = netcdf_outputs.end();


  //Standing dead C
  map_itr = netcdf_outputs.find("DEADC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: DEADC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputDEADC)
    {
      //monthly
      if(curr_spec.monthly){
        outhold.deadc_for_output.push_back(cohort.bdall->m_vegs.deadc);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.deadc_for_output[0], 1, month_start_idx, months_to_output);
          outhold.deadc_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        outhold.deadc_for_output.push_back(cohort.bdall->y_vegs.deadc);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.deadc_for_output[0], 1, year_start_idx, years_to_output);
          outhold.deadc_for_output.clear();
        }
      }
    }//end critical(outputDEADC)
  }//end DEADC
  map_itr = netcdf_outputs.end();


  //Standing dead N
  map_itr = netcdf_outputs.find("DEADN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: DEADN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputDEADN)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_vegs.deadn, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_vegs.deadn, 1, year, 1);
      }
    }//end critical(outputDEADN)
  }//end DEADN
  map_itr = netcdf_outputs.end();


  //Deep C
  map_itr = netcdf_outputs.find("DEEPC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: DEEPC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputDEEPC)
    {
      //monthly
      if(curr_spec.monthly){
        outhold.deepc_for_output.push_back(cohort.bdall->m_soid.deepc);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.deepc_for_output[0], 1, month_start_idx, months_to_output);
          outhold.deepc_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        outhold.deepc_for_output.push_back(cohort.bdall->y_soid.deepc);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.deepc_for_output[0], 1, year_start_idx, years_to_output);
          outhold.deepc_for_output.clear();
        }
      }
    }//end critical(outputDEEPC)
  }//end DEEPC
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("DEEPDZ");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: DEEPDZ";
    curr_spec = map_itr->second;

    #pragma omp critical(outputDEEPDZ)
    {
      double deepdz = 0;
      Layer* currL = cohort.ground.toplayer;
      while(currL!=NULL){
        if(currL->isHumic){
          deepdz += currL->dz;
        }
        currL = currL->nextl;
      }
      output_nc_3dim(&curr_spec, file_stage_suffix, &deepdz, 1, year, 1);
    }//end critical(outputDEEPDZ)
  }//end DEEPDZ
  map_itr = netcdf_outputs.end();


  //DRIVINGNIRR
  map_itr = netcdf_outputs.find("DRIVINGNIRR");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: DRIVINGNIRR";
    curr_spec = map_itr->second;

    #pragma omp critical(outputDRIVINGNIRR)
    {
      //This does not need an entry in OutputHolder because the
      // driving data is already holding a year's worth of values
      // and daily outputs are not held for multiple years.
      if(curr_spec.daily){
        if(end_of_year){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.climate.nirr_d[0], 1, day_timestep, DINY);
        }
      }

    }//end critical(outputDRIVINGNIRR)
  }//end DRIVINGNIRR
  map_itr = netcdf_outputs.end();


  //DRIVINGRAINFALL
  map_itr = netcdf_outputs.find("DRIVINGRAINFALL");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: DRIVINGRAINFALL";
    curr_spec = map_itr->second;

    #pragma omp critical(outputDRIVINGRAINFALL)
    {
      //daily
      if(curr_spec.daily){
        if(end_of_year){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.climate.rain_d[0], 1, day_timestep, DINY);
        }
      }
      //monthly
      else if(curr_spec.monthly){
        float m_d_rnfl = 0;
        for(int id=0; id<dinm; id++){
          m_d_rnfl += cohort.climate.rain_d[doy+id];
        }
        output_nc_3dim(&curr_spec, file_stage_suffix, &m_d_rnfl, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        float y_d_rnfl = 0;
        for(int id=0; id<DINY; id++){
          y_d_rnfl += cohort.climate.rain_d[id];
        }
        output_nc_3dim(&curr_spec, file_stage_suffix, &y_d_rnfl, 1, year, 1);
      }
    }//end critical(outputDRIVINGRAINFALL)
  }//end DRIVINGRAINFALL
  map_itr = netcdf_outputs.end();


  //DRIVINGSNOWFALL
  map_itr = netcdf_outputs.find("DRIVINGSNOWFALL");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: DRIVINGSNOWFALL";
    curr_spec = map_itr->second;

    #pragma omp critical(outputDRIVINGSNOWFALL)
    {
      //daily
      if(curr_spec.daily){
        if(end_of_year){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.climate.snow_d[0], 1, day_timestep, DINY);
        }
      }
      //monthly
      else if(curr_spec.monthly){
        float m_d_snfl = 0;
        for(int id=0; id<dinm; id++){
          m_d_snfl += cohort.climate.snow_d[doy+id];
        }
        output_nc_3dim(&curr_spec, file_stage_suffix, &m_d_snfl, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        float y_d_snfl = 0;
        for(int id=0; id<DINY; id++){
          y_d_snfl += cohort.climate.snow_d[id];
        }
        output_nc_3dim(&curr_spec, file_stage_suffix, &y_d_snfl, 1, year, 1);
      }
    }//end critical(outputDRIVINGSNOWFALL)
  }//end DRIVINGSNOWFALL
  map_itr = netcdf_outputs.end();


  //DRIVINGTAIR
  map_itr = netcdf_outputs.find("DRIVINGTAIR");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: DRIVINGTAIR";
    curr_spec = map_itr->second;

    #pragma omp critical(outputDRIVINGTAIR)
    {
      //This does not need an entry in OutputHolder because the
      // driving data is already holding a year's worth of values
      // and daily outputs are not held for multiple years.
      if(curr_spec.daily){
        if(end_of_year){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.climate.tair_d[0], 1, day_timestep, DINY);
        }
      }

    }//end critical(outputDRIVINGTAIR)
  }//end DRIVINGTAIR
  map_itr = netcdf_outputs.end();


  //DRIVINGVAPO
  map_itr = netcdf_outputs.find("DRIVINGVAPO");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: DRIVINGVAPO";
    curr_spec = map_itr->second;

    #pragma omp critical(outputDRIVINGVAPO)
    {
      //This does not need an entry in OutputHolder because the
      // driving data is already holding a year's worth of values
      // and daily outputs are not held for multiple years.
      if(curr_spec.daily){
        if(end_of_year){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.climate.vapo_d[0], 1, day_timestep, DINY);
        }
      }

    }//end critical(outputDRIVINGVAPO)
  }//end DRIVINGVAPO
  map_itr = netcdf_outputs.end();


  //Woody debris C
  map_itr = netcdf_outputs.find("DWDC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: DWDC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputDWDC)
    {
      //monthly
      if(curr_spec.monthly){
        outhold.dwdc_for_output.push_back(cohort.bdall->m_sois.wdebrisc);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.dwdc_for_output[0], 1, month_start_idx, months_to_output);
          outhold.dwdc_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        outhold.dwdc_for_output.push_back(cohort.bdall->y_sois.wdebrisc);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.dwdc_for_output[0], 1, year_start_idx, years_to_output);
          outhold.dwdc_for_output.clear();
        }
      }
    }//end critical(outputDWDC)
  }//end DWDC
  map_itr = netcdf_outputs.end();


  //Woody debris N
  map_itr = netcdf_outputs.find("DWDN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"DWDN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputDWDN)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_sois.wdebrisn, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_sois.wdebrisn, 1, year, 1);
      }
    }//end critical(outputDWDN)
  }//end DWDN
  map_itr = netcdf_outputs.end();


  //EET
  map_itr = netcdf_outputs.find("EET");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: EET";
    curr_spec = map_itr->second;

    #pragma omp critical(outputEET)
    {
      //by PFT
//by PFT is disabled for now because it erroneously
// includes soil and snow evaporation per PFT, which
// throws off results if the PFT values are summed.
/*      if(curr_spec.pft){
        std::array<double, NUM_PFT> eet_arr{};

        //daily
        if(curr_spec.daily){

          for(int id=0; id<DINM[month]; id++){
            for(int ip=0; ip<NUM_PFT; ip++){
              eet_arr[ip] = cohort.ed[ip].daily_eet[id];
            }
            outhold.eet_for_output.push_back(eet_arr);
          }

          if(end_of_year){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.eet_for_output[0][0], NUM_PFT, day_timestep, DINY);
            outhold.eet_for_output.clear();
          }
        }
        //monthly
        else if(curr_spec.monthly){
          for(int ip=0; ip<NUM_PFT; ip++){
            eet_arr[ip] = cohort.ed[ip].m_l2a.eet;
          }
          outhold.eet_for_output.push_back(eet_arr);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.eet_for_output[0][0], NUM_PFT, month_start_idx, months_to_output);
            outhold.eet_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          for(int ip=0; ip<NUM_PFT; ip++){
            eet_arr[ip] = cohort.ed[ip].y_l2a.eet;
          }
          outhold.eet_for_output.push_back(eet_arr);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.eet_for_output[0][0], NUM_PFT, year_start_idx, years_to_output);
            outhold.eet_for_output.clear();
          }
        }
      }*/
      //Total, instead of by PFT
      if(!curr_spec.pft){

        //daily
        if(curr_spec.daily){

          for(int id=0; id<DINM[month]; id++){
            double daily_eet_tot = 0.;
            for(int ip=0; ip<NUM_PFT; ip++){
              daily_eet_tot += cohort.ed[ip].daily_eet[id];
            }
            outhold.eet_tot_for_output.push_back(daily_eet_tot);
          }

          if(end_of_year){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.eet_tot_for_output[0], 1, day_timestep, DINY);
            outhold.eet_tot_for_output.clear();
          }
        }
        //monthly
        else if(curr_spec.monthly){

          outhold.eet_tot_for_output.push_back(cohort.edall->m_l2a.eet);
          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.eet_tot_for_output[0], 1, month_start_idx, months_to_output);
            outhold.eet_tot_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.eet_tot_for_output.push_back(cohort.edall->y_l2a.eet);
          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.eet_tot_for_output[0], 1, year_start_idx, years_to_output);
            outhold.eet_tot_for_output.clear();
          }
        }
      }
 

//      //By PFT
//      if(curr_spec.pft){
//
//        double m_EET[NUM_PFT], y_EET[NUM_PFT];
//        for(int ip=0; ip<NUM_PFT; ip++){
//          m_EET[ip] = cohort.ed[ip].m_l2a.eet;
//          y_EET[ip] = cohort.ed[ip].y_l2a.eet;
//        }
//
//        //daily
//        if(curr_spec.daily){
//
//          double d_EET[dinm][NUM_PFT];
//          for(int ip=0; ip<NUM_PFT; ip++){
//            for(int id=0; id<dinm; id++){
//              d_EET[id][ip] = cohort.ed[ip].daily_eet[id];
//            }
//          }
//
//          output_nc_4dim(&curr_spec, file_stage_suffix, &d_EET[0][0], NUM_PFT, day_timestep, dinm);
//        }
//        //monthly
//        else if(curr_spec.monthly){
//
//
//          //This will be called monthly for now, even if monthly data
//          // is to be held for batch output.
//          if(!md.hold_monthly_output){
//            output_nc_4dim(&curr_spec, file_stage_suffix, &m_EET[0], NUM_PFT, month_timestep, 1);
//          }
//
//          else if(md.hold_monthly_output && ((month_timestep+1)%12==0)){
//            //For calculating the actual index in the file
//            int hist_month_idx = month_timestep-11;
//
//            for(int iv=0; iv<outhold.eet_for_output.size(); iv++){
//              output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.eet_for_output[iv][0], NUM_PFT, hist_month_idx, 1);
//              hist_month_idx++;
//            }
//            outhold.eet_for_output.clear();
//          }
//
//          //mock-up for if it was stored in a queue not a vector
////          else if(md.hold_monthly_output && (())){
////            int hist_month_idx = month_timestep-11;
////            while(!outhold.eet_for_output.empty()){
////              output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.eet_for_output.front()[0], NUM_PFT, hist_month_idx, 1);
////              outhold.eet_for_output.pop_front();
////              hist_month_idx++;
////            }
////          }
//
//
//        }
//        //yearly
//        else if(curr_spec.yearly){
//          output_nc_4dim(&curr_spec, file_stage_suffix, &y_EET[0], NUM_PFT, year, 1);
//        }
//      }
//
//      //Total, instead of by PFT
//      else if(!curr_spec.pft){
//        //daily
//        if(curr_spec.daily){
//          double eet[31] = {0};
//          for(int ii=0; ii<31; ii++){
//            for(int ip=0; ip<NUM_PFT; ip++){
//              eet[ii] += cohort.ed[ip].daily_eet[ii];
//            }
//          }
//          output_nc_3dim(&curr_spec, file_stage_suffix, &eet[0], 1, day_timestep, dinm);
//        }
//        //monthly
//        else if(curr_spec.monthly){
//          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_l2a.eet, 1, month_timestep, 1);
//        }
//        //yearly
//        else if(curr_spec.yearly){
//          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_l2a.eet, 1, year, 1);
//        }
//      }
    }//end critical(outputEET)
  }//end EET
  map_itr = netcdf_outputs.end();


  //FRONTSDEPTH
  map_itr = netcdf_outputs.find("FRONTSDEPTH");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: FRONTSDEPTH";
    curr_spec = map_itr->second;

    #pragma omp critical(outputFRONTSDEPTH)
    {
      //This uses the summary structs, but might be more accurate
      // if the deque of fronts was checked directly.
      //daily
      if(curr_spec.daily){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_frontsdepth[0][0], MAX_NUM_FNT, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.ground.frntz[0], MAX_NUM_FNT, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.ground.frntz[0], MAX_NUM_FNT, year, 1);
      }
    }//end critical(outputFRONTSDEPTH)
  }//end FRONTSDEPTH
  map_itr = netcdf_outputs.end();


  //FRONTSTYPE
  map_itr = netcdf_outputs.find("FRONTSTYPE");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: ";
    curr_spec = map_itr->second;

    #pragma omp critical(outputFRONTSTYPE)
    {
      //This uses the summary structs, but might be more accurate
      // if the deque of fronts was checked directly.
      //daily
      if(curr_spec.daily){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_frontstype[0][0], MAX_NUM_FNT, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.ground.frnttype[0], MAX_NUM_FNT, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.ground.frnttype[0], MAX_NUM_FNT, year, 1);
      }
    }//end critical(outputFRONTSTYPE)
  }//end FRONTSTYPE
  map_itr = netcdf_outputs.end();


  //GPP
  map_itr = netcdf_outputs.find("GPP");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: GPP";
    curr_spec = map_itr->second;

    #pragma omp critical(outputGPP)
    {
      //PFT and compartment (5 dimensions)
      if(curr_spec.pft && curr_spec.compartment){
        std::array<std::array<double, NUM_PFT>, NUM_PFT_PART> m_gpp{};
        std::array<std::array<double, NUM_PFT>, NUM_PFT_PART> y_gpp{};
        //std::array<std::array<double, NUM_PFT_PART>, NUM_PFT> y_gpp{};

        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            m_gpp[ipp][ip] = cohort.bd[ip].m_a2v.gpp[ipp];
            y_gpp[ipp][ip] = cohort.bd[ip].y_a2v.gpp[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          outhold.gpp_for_output.push_back(m_gpp);
          if(output_this_timestep){
            output_nc_5dim(&curr_spec, file_stage_suffix, &outhold.gpp_for_output[0][0], NUM_PFT_PART, NUM_PFT, month_start_idx, months_to_output);
            outhold.gpp_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.gpp_for_output.push_back(y_gpp);
          if(output_this_timestep){
            output_nc_5dim(&curr_spec, file_stage_suffix, &outhold.gpp_for_output[0][0], NUM_PFT_PART, NUM_PFT, year_start_idx, years_to_output);
            outhold.gpp_for_output.clear();
          }
        }
      }
      //PFT only (4 dimensions)
      else if(curr_spec.pft && !curr_spec.compartment){
        std::array<double, NUM_PFT> m_gpp{};
        std::array<double, NUM_PFT> y_gpp{};

        for(int ip=0; ip<NUM_PFT; ip++){
          m_gpp[ip] = cohort.bd[ip].m_a2v.gppall;
          y_gpp[ip] = cohort.bd[ip].y_a2v.gppall;
        }

        //monthly
        if(curr_spec.monthly){
          outhold.gpp_pft_for_output.push_back(m_gpp);
          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.gpp_pft_for_output[0], NUM_PFT, month_start_idx, months_to_output);
            outhold.gpp_pft_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.gpp_pft_for_output.push_back(y_gpp);
          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.gpp_pft_for_output[0], NUM_PFT, year_start_idx, years_to_output);
            outhold.gpp_pft_for_output.clear();
          }
        }
      }


      //Compartment only (4 dimensions)
      else if(!curr_spec.pft && curr_spec.compartment){
        std::array<double, NUM_PFT_PART> m_gpp{};
        std::array<double, NUM_PFT_PART> y_gpp{};

        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){

            m_gpp[ipp] += cohort.bd[ip].m_a2v.gpp[ipp];
            y_gpp[ipp] += cohort.bd[ip].y_a2v.gpp[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          outhold.gpp_part_for_output.push_back(m_gpp);
          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.gpp_part_for_output[0], NUM_PFT_PART, month_start_idx, months_to_output);
            outhold.gpp_part_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.gpp_part_for_output.push_back(y_gpp);
          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.gpp_part_for_output[0], NUM_PFT_PART, year_start_idx, years_to_output);
            outhold.gpp_part_for_output.clear();
          }
        }
      }

      //Neither PFT nor Compartment - total instead (3 dimensions)
      else if(!curr_spec.pft && !curr_spec.compartment){
        //monthly
        if(curr_spec.monthly){
          outhold.gpp_tot_for_output.push_back(cohort.bdall->m_a2v.gppall);
          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.gpp_tot_for_output[0], 1, month_start_idx, months_to_output);
            outhold.gpp_tot_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.gpp_tot_for_output.push_back(cohort.bdall->y_a2v.gppall);
          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.gpp_tot_for_output[0], 1, year_start_idx, years_to_output);
            outhold.gpp_tot_for_output.clear();
          }
        }
      }
    }//end critical(outputGPP)
  }//end GPP
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("GROWEND");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: GROWEND";
    curr_spec = map_itr->second;

    #pragma omp critical(outputGROWEND)
    {
      output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.rtdpGEoutput, 1, year, 1);
    }//end critical(outputGROWEND)
  }//end GROWEND
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("GROWSTART");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: GROWSTART";
    curr_spec = map_itr->second;

    #pragma omp critical(outputGROWSTART)
    {
      output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.rtdpGSoutput, 1, year, 1);
    }//end critical(outputGROWSTART)
  }//end GROWSTART
  map_itr = netcdf_outputs.end();


  //HKDEEP
  map_itr = netcdf_outputs.find("HKDEEP");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: HKDEEP";
    curr_spec = map_itr->second;

    #pragma omp critical(outputHKDEEP)
    {
      //daily
      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_hkdeep[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.hkdeep, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.hkdeep, 1, year, 1);
      }
    }//end critical(outputHKDEEP)
  }//end HKDEEP 
  map_itr = netcdf_outputs.end();


  //HKLAYER
  map_itr = netcdf_outputs.find("HKLAYER");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: HKLAYER";
    curr_spec = map_itr->second;

    #pragma omp critical(outputHKLAYER)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.hcond[0], MAX_SOI_LAY, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.hcond[0], MAX_SOI_LAY, year, 1);
      }
    }//end critical(outputHKLAYER)

  }//end HKLAYER
  map_itr = netcdf_outputs.end();


  //HKMINEA
  map_itr = netcdf_outputs.find("HKMINEA");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: HKMINEA";
    curr_spec = map_itr->second;

    #pragma omp critical(outputHKMINEA)
    {
      //daily
      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_hkminea[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.hkminea, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.hkminea, 1, year, 1);
      }
    }//end critical(outputHKMINEA)
  }//end HKMINEA
  map_itr = netcdf_outputs.end();


  //HKMINEB
  map_itr = netcdf_outputs.find("HKMINEB");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: HKMINEB";
    curr_spec = map_itr->second;

    #pragma omp critical(outputHKMINEB)
    {
      //daily
      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_hkmineb[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.hkmineb, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.hkmineb, 1, year, 1);
      }
    }//end critical(outputHKMINEB)
  }//end HKMINEB
  map_itr = netcdf_outputs.end();


  //HKMINEC
  map_itr = netcdf_outputs.find("HKMINEC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: HKMINEC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputHKMINEC)
    {
      //daily
      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_hkminec[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.hkminec, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.hkminec, 1, year, 1);
      }
    }//end critical(outputHKMINEC)
  }//end HKMINEC
  map_itr = netcdf_outputs.end();


  //HKSHLW
  map_itr = netcdf_outputs.find("HKSHLW");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: HKSHLW";
    curr_spec = map_itr->second;

    #pragma omp critical(outputHKSHLW)
    {
      //daily
      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_hkshlw[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.hkshlw, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.hkshlw, 1, year, 1);
      }
    }
  }//end HKSHLW 
  map_itr = netcdf_outputs.end();


  //INGPP
  map_itr = netcdf_outputs.find("INGPP");
  if (map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug) << "NetCDF output: INGPP";
    curr_spec = map_itr->second;

    #pragma omp critical(outputINGPP)
    {
      // PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){

        std::array<std::array<double, NUM_PFT>, NUM_PFT_PART> m_ingpp{};
        std::array<std::array<double, NUM_PFT>, NUM_PFT_PART> y_ingpp{};

        for(int ip = 0; ip < NUM_PFT; ip++) {
          for(int ipp = 0; ipp < NUM_PFT_PART; ipp++){
            m_ingpp[ipp][ip] = cohort.bd[ip].m_a2v.ingpp[ipp];
            y_ingpp[ipp][ip] = cohort.bd[ip].y_a2v.ingpp[ipp];
          }
        }
        // monthly
        if(curr_spec.monthly){
          outhold.ingpp_for_output.push_back(m_ingpp);

          if(output_this_timestep){
            output_nc_5dim(&curr_spec, file_stage_suffix, &outhold.ingpp_for_output[0][0], NUM_PFT_PART, NUM_PFT, month_start_idx, months_to_output);
            outhold.ingpp_for_output.clear();
          }
        }
        // yearly
        else if(curr_spec.yearly){
          outhold.ingpp_for_output.push_back(y_ingpp);

          if(output_this_timestep){
            output_nc_5dim(&curr_spec, file_stage_suffix, &outhold.ingpp_for_output[0][0], NUM_PFT_PART, NUM_PFT, year_start_idx, years_to_output);
            outhold.ingpp_for_output.clear();
          }
        }
      }
      // PFT only (4 dimensions)
      else if(curr_spec.pft && !curr_spec.compartment){

        std::array<double, NUM_PFT> m_ingpp{};
        std::array<double, NUM_PFT> y_ingpp{};

        for(int ip = 0; ip < NUM_PFT; ip++){
          m_ingpp[ip] = cohort.bd[ip].m_a2v.ingppall;
          y_ingpp[ip] = cohort.bd[ip].y_a2v.ingppall;
        }

        // monthly
        if(curr_spec.monthly){
          outhold.ingpp_pft_for_output.push_back(m_ingpp);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.ingpp_pft_for_output[0], NUM_PFT, month_start_idx, months_to_output);
            outhold.ingpp_pft_for_output.clear();
          }
        }
        // yearly
        else if(curr_spec.yearly){
          outhold.ingpp_pft_for_output.push_back(y_ingpp);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.ingpp_pft_for_output[0], NUM_PFT, year_start_idx, years_to_output);
            outhold.ingpp_pft_for_output.clear();
          }
        }
      }
      // Compartment only (4 dimensions)
      else if(!curr_spec.pft && curr_spec.compartment){
        std::array<double, NUM_PFT_PART> m_ingpp{};
        std::array<double, NUM_PFT_PART> y_ingpp{};

        for(int ipp = 0; ipp < NUM_PFT_PART; ipp++){
          for(int ip = 0; ip < NUM_PFT; ip++){
            m_ingpp[ipp] += cohort.bd[ip].m_a2v.ingpp[ipp];
            y_ingpp[ipp] += cohort.bd[ip].y_a2v.ingpp[ipp];
          }
        }
        // monthly
        if(curr_spec.monthly){
          outhold.ingpp_part_for_output.push_back(m_ingpp);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.ingpp_part_for_output[0], NUM_PFT_PART, month_start_idx, months_to_output);
            outhold.ingpp_part_for_output.clear();
          }
        }
        // yearly
        else if(curr_spec.yearly){
          outhold.ingpp_part_for_output.push_back(y_ingpp);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.ingpp_part_for_output[0], NUM_PFT_PART, year_start_idx, years_to_output);
            outhold.ingpp_part_for_output.clear();
          }
        }
      }
      // Neither PFT nor Compartment - total instead
      else if(!curr_spec.pft && !curr_spec.compartment){
        // monthly
        if(curr_spec.monthly){
          outhold.ingpp_tot_for_output.push_back(cohort.bdall->m_a2v.ingppall);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.ingpp_tot_for_output[0], 1, month_start_idx, months_to_output);
            outhold.ingpp_tot_for_output.clear();
          }
        }
        // yearly
        else if(curr_spec.yearly){
          outhold.ingpp_tot_for_output.push_back(cohort.bdall->y_a2v.ingppall);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.ingpp_tot_for_output[0], 1, year_start_idx, years_to_output);
            outhold.ingpp_tot_for_output.clear();
          }
        }
      }
    } // end critical(outputINGPP)
  } // end INGPP
  map_itr = netcdf_outputs.end();

  //INNPP
  map_itr = netcdf_outputs.find("INNPP");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: INNPP";
    curr_spec = map_itr->second;

    #pragma omp critical(outputINNPP)
    {
      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){

        double m_innpp[NUM_PFT_PART][NUM_PFT];
        double y_innpp[NUM_PFT_PART][NUM_PFT];

        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            m_innpp[ipp][ip] = cohort.bd[ip].m_a2v.innpp[ipp];
            y_innpp[ipp][ip] = cohort.bd[ip].y_a2v.innpp[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &m_innpp[0][0], NUM_PFT_PART, NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &y_innpp[0][0], NUM_PFT_PART, NUM_PFT, year, 1);
        }
      }
      //PFT only (4 dimensions)
      else if(curr_spec.pft && !curr_spec.compartment){

        double m_innpp[NUM_PFT], y_innpp[NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          m_innpp[ip] = cohort.bd[ip].m_a2v.innppall;
          y_innpp[ip] = cohort.bd[ip].y_a2v.innppall;
        }

        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_innpp[0], NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_innpp[0], NUM_PFT, year, 1);
        }
      }
      //Compartment only (4 dimensions)
      else if(!curr_spec.pft && curr_spec.compartment){

        double m_innpp[NUM_PFT_PART] = {0};
        double y_innpp[NUM_PFT_PART] = {0};

        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){
            m_innpp[ipp] += cohort.bd[ip].m_a2v.innpp[ipp];
            y_innpp[ipp] += cohort.bd[ip].y_a2v.innpp[ipp];
          }
        }

        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_innpp[0], NUM_PFT_PART, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_innpp[0], NUM_PFT_PART, year, 1);
        }
      }
      //Neither PFT nor Compartment - total instead
      else if(!curr_spec.pft && !curr_spec.compartment){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_a2v.innppall, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_a2v.innppall, 1, year, 1);
        }
      }
    }//end critical(outputINNPP)
  }//end INNPP
  map_itr = netcdf_outputs.end();


  //INNUPTAKE
  map_itr = netcdf_outputs.find("INNUPTAKE");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: INNUPTAKE";
    curr_spec = map_itr->second;

    #pragma omp critical(outputINNUPTAKE)
    {
      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){
        /*** STUB ***/
        //Currently unavailable. N uptake will need to be made accessible
        // by PFT compartment.
      }
      //PFT only (4 dimensions)
      else if(curr_spec.pft && !curr_spec.compartment){
        double m_innuptake[NUM_PFT], y_innuptake[NUM_PFT];

        for(int ip=0; ip<NUM_PFT; ip++){
          m_innuptake[ip] = cohort.bd[ip].m_soi2v.innuptake;
          y_innuptake[ip] = cohort.bd[ip].y_soi2v.innuptake;
        }
        //monthly 
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_innuptake[0], NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_innuptake[0], NUM_PFT, year, 1);
        }
      }
      //Compartment only
      else if(!curr_spec.pft && curr_spec.compartment){
        /*** STUB ***/
      }
      //Neither PFT nor compartment
      else if(!curr_spec.pft && !curr_spec.compartment){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_soi2v.innuptake, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_soi2v.innuptake, 1, year, 1);
        }
      }
    }//end critical(outputINNUPTAKE)
  }//end INNUPTAKE
  map_itr = netcdf_outputs.end();


  //IWCLAYER
  map_itr = netcdf_outputs.find("IWCLAYER");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: IWCLAYER";
    curr_spec = map_itr->second;

    #pragma omp critical(outputIWCLAYER)
    {
      if(curr_spec.monthly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.iwc[0], MAX_SOI_LAY, month_timestep, 1);
      }
      else if(curr_spec.yearly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.iwc[0], MAX_SOI_LAY, year, 1);
      }
    }//end critical(outputIWCLAYER)
  }//end IWCLAYER
  map_itr = netcdf_outputs.end();


  //LAI
  map_itr = netcdf_outputs.find("LAI");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LAI";
    curr_spec = map_itr->second;

    #pragma omp critical(outputLAI)
    {
      //PFT (4 dimensions)
      if(curr_spec.pft){
        std::array<double, NUM_PFT> m_lai{};
        std::array<double, NUM_PFT> y_lai{};

        for(int ip=0; ip<NUM_PFT; ip++){
          m_lai[ip] = cohort.cd.m_veg.lai[ip];
          y_lai[ip] = cohort.cd.y_veg.lai[ip];
        }

        //monthly
        if(curr_spec.monthly){
          outhold.lai_for_output.push_back(m_lai);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.lai_for_output[0], NUM_PFT, month_start_idx, months_to_output);
            outhold.lai_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.lai_for_output.push_back(y_lai);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.lai_for_output[0], NUM_PFT, year_start_idx, years_to_output);
            outhold.lai_for_output.clear();
          }
        }
      }
      //Total
      else if(!curr_spec.pft){
        double m_lai_total = 0., y_lai_total = 0.;
        for(int ip=0; ip<NUM_PFT; ip++){
          if(cohort.cd.m_veg.vegcov[ip]>0.){
            m_lai_total += cohort.cd.m_veg.lai[ip];
            y_lai_total += cohort.cd.y_veg.lai[ip];
          }
        }

        //monthly 
        if(curr_spec.monthly){
          outhold.lai_tot_for_output.push_back(m_lai_total);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.lai_tot_for_output[0], 1, month_start_idx, months_to_output);
            outhold.lai_tot_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.lai_tot_for_output.push_back(y_lai_total);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.lai_tot_for_output[0], 1, year_start_idx, years_to_output);
            outhold.lai_tot_for_output.clear();
          }
        }
      }
    }//end critical(outputLAI)
  }//end LAI
  map_itr = netcdf_outputs.end();


  //LAYERDEPTH
  map_itr = netcdf_outputs.find("LAYERDEPTH");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LAYERDEPTH";
    curr_spec = map_itr->second;

    #pragma omp critical(outputLAYERDEPTH)
    {
      std::array<double, MAX_SOI_LAY> layerdepth_arr{};

      //monthly
      if(curr_spec.monthly){
        for(int il=0; il<MAX_SOI_LAY; il++){
          layerdepth_arr[il] = cohort.cd.m_soil.z[il];
        }
        outhold.layerdepth_for_output.push_back(layerdepth_arr);

        if(output_this_timestep){
          output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.layerdepth_for_output[0], MAX_SOI_LAY, month_start_idx, months_to_output);
          outhold.layerdepth_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        for(int il=0; il<MAX_SOI_LAY; il++){
          layerdepth_arr[il] = cohort.cd.y_soil.z[il];
        }
        outhold.layerdepth_for_output.push_back(layerdepth_arr);

        if(output_this_timestep){
          output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.layerdepth_for_output[0], MAX_SOI_LAY, year_start_idx, years_to_output);
          outhold.layerdepth_for_output.clear();
        }
      }
    }//end critical(outputLAYERDEPTH)
  }//end LAYERDEPTH 
  map_itr = netcdf_outputs.end();


  //LAYERDZ
  map_itr = netcdf_outputs.find("LAYERDZ");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LAYERDZ";
    curr_spec = map_itr->second;

    #pragma omp critical(outputLAYERDZ)
    {
      std::array<double, MAX_SOI_LAY> layerdz_arr{};

      //monthly
      if(curr_spec.monthly){
        for(int il=0; il<MAX_SOI_LAY; il++){
          layerdz_arr[il] = cohort.cd.m_soil.dz[il];
        }
        outhold.layerdz_for_output.push_back(layerdz_arr);

        if(output_this_timestep){
          output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.layerdz_for_output[0], MAX_SOI_LAY, month_start_idx, months_to_output);
          outhold.layerdz_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        for(int il=0; il<MAX_SOI_LAY; il++){
          layerdz_arr[il] = cohort.cd.y_soil.dz[il];
        }
        outhold.layerdz_for_output.push_back(layerdz_arr);

        if(output_this_timestep){
          output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.layerdz_for_output[0], MAX_SOI_LAY, year_start_idx, years_to_output);
          outhold.layerdz_for_output.clear();
        }
      }
    }//end critical(outputLAYERDZ)
  }//end LAYERDZ 
  map_itr = netcdf_outputs.end();


  //LAYERTYPE
  map_itr = netcdf_outputs.find("LAYERTYPE");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LAYERTYPE";
    curr_spec = map_itr->second;

    #pragma omp critical(outputLAYERTYPE)
    {
      std::array<int, MAX_SOI_LAY> layertype_arr{};

      //monthly
      if(curr_spec.monthly){
        for(int il=0; il<MAX_SOI_LAY; il++){
          layertype_arr[il] = cohort.cd.m_soil.type[il];
        }
        outhold.layertype_for_output.push_back(layertype_arr);

        if(output_this_timestep){
          output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.layertype_for_output[0], MAX_SOI_LAY, month_start_idx, months_to_output);
          outhold.layertype_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        for(int il=0; il<MAX_SOI_LAY; il++){
          layertype_arr[il] = cohort.cd.y_soil.type[il];
        }
        outhold.layertype_for_output.push_back(layertype_arr);

        if(output_this_timestep){
          output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.layertype_for_output[0], MAX_SOI_LAY, year_start_idx, years_to_output);
          outhold.layertype_for_output.clear();
        }
      }
    }//end critical(outputLAYERTYPE)
  }//end LAYERTYPE 
  map_itr = netcdf_outputs.end();


  //LFNVC (Litterfall for Non-Vascular PFTs)
  map_itr = netcdf_outputs.find("LFNVC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LFNVC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputLFNVC)
    {
      //monthly
      if(curr_spec.monthly){
        outhold.lfnvc_for_output.push_back(cohort.bdall->m_v2soi.mossdeathc);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.lfnvc_for_output[0], 1, month_start_idx, months_to_output);
          outhold.lfnvc_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        outhold.lfnvc_for_output.push_back(cohort.bdall->y_v2soi.mossdeathc);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.lfnvc_for_output[0], 1, year_start_idx, years_to_output);
          outhold.lfnvc_for_output.clear();
        }
      }
    }//end critical(outputLFNVC)
  }//end LFNVC
  map_itr = netcdf_outputs.end();


  //LFNVN
  map_itr = netcdf_outputs.find("LFNVN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LFNVN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputLFNVN)
    {
      //monthly
      if(curr_spec.monthly){
        outhold.lfnvn_for_output.push_back(cohort.bdall->m_v2soi.mossdeathn);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.lfnvn_for_output[0], 1, month_start_idx, months_to_output);
          outhold.lfnvn_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        outhold.lfnvn_for_output.push_back(cohort.bdall->y_v2soi.mossdeathn);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.lfnvn_for_output[0], 1, year_start_idx, years_to_output);
          outhold.lfnvn_for_output.clear();
        }
      }
    }//end critical(outputLFNVN)
  }//end LFNVN
  map_itr = netcdf_outputs.end();


  //LFVC (prior LTRFALC)
  map_itr = netcdf_outputs.find("LFVC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LFVC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputLFVC)
    {
      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){
        std::array<std::array<double, NUM_PFT>, NUM_PFT_PART> m_lfvc{};
        std::array<std::array<double, NUM_PFT>, NUM_PFT_PART> y_lfvc{};

        for(int ip=0; ip<NUM_PFT; ip++){
          if(cohort.cd.m_veg.nonvascular[ip] == 0){
            for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
              m_lfvc[ipp][ip] = cohort.bd[ip].m_v2soi.ltrfalc[ipp];
              y_lfvc[ipp][ip] = cohort.bd[ip].y_v2soi.ltrfalc[ipp];
            }
          }
        }
        //monthly
        if(curr_spec.monthly){
          outhold.lfvc_for_output.push_back(m_lfvc);

          if(output_this_timestep){
            output_nc_5dim(&curr_spec, file_stage_suffix, &outhold.lfvc_for_output[0][0], NUM_PFT_PART, NUM_PFT, month_start_idx, months_to_output);
            outhold.lfvc_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.lfvc_for_output.push_back(y_lfvc);

          if(output_this_timestep){
            output_nc_5dim(&curr_spec, file_stage_suffix, &outhold.lfvc_for_output[0][0], NUM_PFT_PART, NUM_PFT, year_start_idx, years_to_output);
            outhold.lfvc_for_output.clear();
          }
        }
      }
      //PFT only (4 dimensions)
      else if(curr_spec.pft && !curr_spec.compartment){
        std::array<double, NUM_PFT> m_lfvc{};
        std::array<double, NUM_PFT> y_lfvc{};

        for(int ip=0; ip<NUM_PFT; ip++){
          if(cohort.cd.m_veg.nonvascular[ip] == 0){
            m_lfvc[ip] = cohort.bd[ip].m_v2soi.ltrfalcall;
            y_lfvc[ip] = cohort.bd[ip].y_v2soi.ltrfalcall;
          }
        }
        //monthly
        if(curr_spec.monthly){
          outhold.lfvc_pft_for_output.push_back(m_lfvc);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.lfvc_pft_for_output[0], NUM_PFT, month_start_idx, months_to_output);
            outhold.lfvc_pft_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.lfvc_pft_for_output.push_back(y_lfvc);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.lfvc_pft_for_output[0], NUM_PFT, year_start_idx, years_to_output);
            outhold.lfvc_pft_for_output.clear();
          }
        }
      }
      //Compartment only (4 dimensions)
      else if(!curr_spec.pft && curr_spec.compartment){
        std::array<double, NUM_PFT_PART> m_lfvc{};
        std::array<double, NUM_PFT_PART> y_lfvc{};

        for(int ip=0; ip<NUM_PFT; ip++){
          if(cohort.cd.m_veg.nonvascular[ip] == 0){
            for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
              m_lfvc[ipp] += cohort.bd[ip].m_v2soi.ltrfalc[ipp];
              y_lfvc[ipp] += cohort.bd[ip].y_v2soi.ltrfalc[ipp];
            }
          }
        }
        //monthly
        if(curr_spec.monthly){
          outhold.lfvc_part_for_output.push_back(m_lfvc);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.lfvc_part_for_output[0], NUM_PFT_PART, month_start_idx, months_to_output);
            outhold.lfvc_part_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.lfvc_part_for_output.push_back(y_lfvc);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.lfvc_part_for_output[0], NUM_PFT_PART, year_start_idx, years_to_output);
            outhold.lfvc_part_for_output.clear();
          }
        }
      }
      //Neither PFT nor compartment - totals
      else if(!curr_spec.pft && !curr_spec.compartment){
        double m_lfvc = 0., y_lfvc = 0.;

        for(int ip=0; ip<NUM_PFT; ip++){
          if(cohort.cd.m_veg.nonvascular[ip] == 0){
            m_lfvc += cohort.bd[ip].m_v2soi.ltrfalcall;
            y_lfvc += cohort.bd[ip].y_v2soi.ltrfalcall;
          }
        }
        //monthly
        if(curr_spec.monthly){
          outhold.lfvc_tot_for_output.push_back(m_lfvc);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.lfvc_tot_for_output[0], 1, month_start_idx, months_to_output);
            outhold.lfvc_tot_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.lfvc_tot_for_output.push_back(y_lfvc);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.lfvc_tot_for_output[0], 1, year_start_idx, years_to_output);
            outhold.lfvc_tot_for_output.clear();
          }
        }
      }
    }//end critical(outputLFVC)
  }//end LFVC
  map_itr = netcdf_outputs.end();


  //LFVN (Litterfall N for vascular PFTs)
  map_itr = netcdf_outputs.find("LFVN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LFVN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputLFVN)
    {
      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){

        double m_lfvn[NUM_PFT_PART][NUM_PFT] = {0};
        double y_lfvn[NUM_PFT_PART][NUM_PFT] = {0};

        for(int ip=0; ip<NUM_PFT; ip++){
          if(cohort.cd.m_veg.nonvascular[ip] == 0){
            for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
              m_lfvn[ipp][ip] = cohort.bd[ip].m_v2soi.ltrfaln[ipp];
              y_lfvn[ipp][ip] = cohort.bd[ip].y_v2soi.ltrfaln[ipp];
            }
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &m_lfvn[0][0], NUM_PFT_PART, NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &y_lfvn[0][0], NUM_PFT_PART, NUM_PFT, year, 1);
        }
      }
      //PFT only (4 dimensions)
      else if(curr_spec.pft && !curr_spec.compartment){

        double m_lfvn[NUM_PFT] = {0}, y_lfvn[NUM_PFT] = {0};

        for(int ip=0; ip<NUM_PFT; ip++){
          if(cohort.cd.m_veg.nonvascular[ip] == 0){
            m_lfvn[ip] = cohort.bd[ip].m_v2soi.ltrfalnall;
            y_lfvn[ip] = cohort.bd[ip].y_v2soi.ltrfalnall;
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_lfvn[0], NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_lfvn[0], NUM_PFT, year, 1);
        }
      }
      //Compartment only (4 dimensions)
      else if(!curr_spec.pft && curr_spec.compartment){

        double m_lfvn[NUM_PFT_PART] = {0};
        double y_lfvn[NUM_PFT_PART] = {0};

        for(int ip=0; ip<NUM_PFT; ip++){
          if(cohort.cd.m_veg.nonvascular[ip] == 0){
            for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
              m_lfvn[ipp] += cohort.bd[ip].m_v2soi.ltrfaln[ipp];
              y_lfvn[ipp] += cohort.bd[ip].y_v2soi.ltrfaln[ipp];
            }
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_lfvn[0], NUM_PFT_PART, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_lfvn[0], NUM_PFT_PART, year, 1);
        }
      }
      //Neither PFT nor compartment - totals
      else if(!curr_spec.pft && !curr_spec.compartment){

        double m_lfvn = 0., y_lfvn = 0.;

        for(int ip=0; ip<NUM_PFT; ip++){
          if(cohort.cd.m_veg.nonvascular[ip] == 0){
            m_lfvn += cohort.bd[ip].m_v2soi.ltrfalnall;
            y_lfvn += cohort.bd[ip].y_v2soi.ltrfalnall;
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &m_lfvn, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &y_lfvn, 1, year, 1);
        }
      }
    }//end critical(outputLFVN)
  }//end LFVN
  map_itr = netcdf_outputs.end();


  //LWCLAYER
  map_itr = netcdf_outputs.find("LWCLAYER");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LWCLAYER";
    curr_spec = map_itr->second;
    #pragma omp critical(outputLWCLAYER)
    {
      std::array<double, MAX_SOI_LAY> lwc_layer{};

      if(curr_spec.monthly){
        for(int i=0; i<MAX_SOI_LAY; i++){
          lwc_layer[i] = cohort.edall->m_soid.lwc[i];
        }
        outhold.lwclayer_for_output.push_back(lwc_layer);

        if(output_this_timestep){
          output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.lwclayer_for_output[0][0], MAX_SOI_LAY, month_start_idx, months_to_output);
          outhold.lwclayer_for_output.clear();
        }
      }
      else if(curr_spec.yearly){
        for(int i=0; i<MAX_SOI_LAY; i++){
          lwc_layer[i] = cohort.edall->y_soid.lwc[i];
        }
        outhold.lwclayer_for_output.push_back(lwc_layer);

        if(output_this_timestep){
          output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.lwclayer_for_output[0][0], MAX_SOI_LAY, year_start_idx, years_to_output);
          outhold.lwclayer_for_output.clear();
        }
      }
    }//end critical(outputLWCLAYER)
  }//end LWCLAYER
  map_itr = netcdf_outputs.end();


  //Mineral C
  map_itr = netcdf_outputs.find("MINEC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"MINEC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputMINEC)
    {
      double minec;
      //monthly
      if(curr_spec.monthly){
        minec = cohort.bdall->m_soid.mineac
                + cohort.bdall->m_soid.minebc
                + cohort.bdall->m_soid.minecc;
        outhold.minec_for_output.push_back(minec);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.minec_for_output[0], 1, month_start_idx, months_to_output);
          outhold.minec_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        minec = cohort.bdall->y_soid.mineac
                + cohort.bdall->y_soid.minebc
                + cohort.bdall->y_soid.minecc;
        outhold.minec_for_output.push_back(minec);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.minec_for_output[0], 1, year_start_idx, years_to_output);
          outhold.minec_for_output.clear();
        }
      }
    }//end critical(outputMINEC)
  }//end MINEC
  map_itr = netcdf_outputs.end();


  //MOSSDZ
  map_itr = netcdf_outputs.find("MOSSDZ");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: MOSSDZ";
    curr_spec = map_itr->second;

    #pragma omp critical(outputMOSSDZ)
    {
      double mossdz = 0;
      Layer* currL = cohort.ground.toplayer;
      while(currL!=NULL){
        if(currL->isMoss){
          mossdz += currL->dz;
        }
        currL = currL->nextl;
      }

      outhold.mossdz_for_output.push_back(mossdz);

      if(output_this_timestep){
        output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.mossdz_for_output[0], 1, year_start_idx, years_to_output);
        outhold.mossdz_for_output.clear();
      }
      //The following may never get set to anything useful?
      //y_soil.mossthick;

    }//end critical(outputMOSSDZ)
  }//end MOSSDZ
  map_itr = netcdf_outputs.end();


  //NDRAIN
  map_itr = netcdf_outputs.find("NDRAIN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: NDRAIN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputNDRAIN)
    {
      //By layer
      if(curr_spec.layer){

        if(curr_spec.monthly){
//          output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.soilbgc.bdall->m_soi2l.ndrain[0], MAX_SOI_LAY, month_timestep, 1);
        }
        else if(curr_spec.yearly){
          /*** STUB ***/
        }
      }
      //Total
      else if(!curr_spec.layer){

        double ndrain = 0;
        if(curr_spec.monthly){

          for(int il=0; il<MAX_SOI_LAY; il++){
            //ndrain += bd->m_soi2l.ndrain[il];
            /*** STUB ***/
          }

        }
        if(curr_spec.yearly){
          /*** STUB ***/
        }
      }
    }//end critical(outputNDRAIN)
  }//end NDRAIN
  map_itr = netcdf_outputs.end();


  //NETNMIN
  map_itr = netcdf_outputs.find("NETNMIN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: NETNMIN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputNETNMIN)
    {
      //By layer
      if(curr_spec.layer){
        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_soi2soi.netnmin[0], MAX_SOI_LAY, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_soi2soi.netnmin[0], MAX_SOI_LAY, year, 1);
        }
      }
      //Total, instead of by layer
      else if(!curr_spec.layer){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_soi2soi.netnminsum, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_soi2soi.netnminsum, 1, year, 1);
        }
      }
    }//end critical(outputNETNMIN)
  }//end NETNMIN
  map_itr = netcdf_outputs.end();


  //NIMMOB
  map_itr = netcdf_outputs.find("NIMMOB");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: NIMMOB";
    curr_spec = map_itr->second;

    #pragma omp critical(outputNIMMOB)
    {
      //By layer
      if(curr_spec.layer){
        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_soi2soi.nimmob[0], MAX_SOI_LAY, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_soi2soi.nimmob[0], MAX_SOI_LAY, year, 1);
        }

      }
      //Total, instead of by layer
      else if(!curr_spec.layer){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_soi2soi.nimmobsum, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_soi2soi.nimmobsum, 1, year, 1);
        }
      }
    }//end critical(outputNIMMOB)
  }//end NIMMOB
  map_itr = netcdf_outputs.end();


  //NINPUT
  map_itr = netcdf_outputs.find("NINPUT");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: NINPUT";
    curr_spec = map_itr->second;

    #pragma omp critical(outputNINPUT)
    {
      //By layer
      if(curr_spec.layer){
        /*** STUB ***/
      }
      //Total
      else if(!curr_spec.layer){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_a2soi.avlninput, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_a2soi.avlninput, 1, year, 1);
        }
      }
    }//end critical(outputNINPUT)
  }//end NINPUT
  map_itr = netcdf_outputs.end();


  //NLOST
  map_itr = netcdf_outputs.find("NLOST");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: NLOST";
    curr_spec = map_itr->second;

    #pragma omp critical(outputNLOST)
    {
      double nlost;
      //monthly
      if(curr_spec.monthly){
        nlost = cohort.bdall->m_soi2l.avlnlost
              + cohort.bdall->m_soi2l.orgnlost;
        output_nc_3dim(&curr_spec, file_stage_suffix, &nlost, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        nlost = cohort.bdall->y_soi2l.avlnlost
              + cohort.bdall->y_soi2l.orgnlost;
        output_nc_3dim(&curr_spec, file_stage_suffix, &nlost, 1, year, 1);
      }
    }//end critical(outputNLOST)
  }//end NLOST
  map_itr = netcdf_outputs.end();


  //NPP
  map_itr = netcdf_outputs.find("NPP");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: NPP";
    curr_spec = map_itr->second;

    #pragma omp critical(outputNPP)
    {
      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){
        std::array<std::array<double, NUM_PFT>, NUM_PFT_PART> m_npp{};
        std::array<std::array<double, NUM_PFT>, NUM_PFT_PART> y_npp{};

        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            m_npp[ipp][ip] = cohort.bd[ip].m_a2v.npp[ipp];
            y_npp[ipp][ip] = cohort.bd[ip].y_a2v.npp[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          outhold.npp_for_output.push_back(m_npp);

          if(output_this_timestep){
            output_nc_5dim(&curr_spec, file_stage_suffix, &outhold.npp_for_output[0][0], NUM_PFT_PART, NUM_PFT, month_start_idx, months_to_output);
            outhold.npp_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.npp_for_output.push_back(y_npp);

          if(output_this_timestep){
            output_nc_5dim(&curr_spec, file_stage_suffix, &outhold.npp_for_output[0][0], NUM_PFT_PART, NUM_PFT, year_start_idx, years_to_output);
            outhold.npp_for_output.clear();
          }
        }
      }
      //PFT only (4 dimensions)
      else if(curr_spec.pft && !curr_spec.compartment){
        std::array<double, NUM_PFT> m_npp{};
        std::array<double, NUM_PFT> y_npp{};

        for(int ip=0; ip<NUM_PFT; ip++){
          m_npp[ip] = cohort.bd[ip].m_a2v.nppall;
          y_npp[ip] = cohort.bd[ip].y_a2v.nppall;
        }

        //monthly
        if(curr_spec.monthly){
          outhold.npp_pft_for_output.push_back(m_npp);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.npp_pft_for_output[0], NUM_PFT, month_start_idx, months_to_output);
            outhold.npp_pft_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.npp_pft_for_output.push_back(y_npp);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.npp_pft_for_output[0], NUM_PFT, year_start_idx, years_to_output);
            outhold.npp_pft_for_output.clear();
          }
        }
      }
      //Compartment only (4 dimensions)
      else if(!curr_spec.pft && curr_spec.compartment){
        std::array<double, NUM_PFT_PART> m_npp{};
        std::array<double, NUM_PFT_PART> y_npp{};

        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){
            m_npp[ipp] += cohort.bd[ip].m_a2v.npp[ipp];
            y_npp[ipp] += cohort.bd[ip].y_a2v.npp[ipp];
          }
        }
        //monthly 
        if(curr_spec.monthly){
          outhold.npp_part_for_output.push_back(m_npp);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.npp_part_for_output[0], NUM_PFT_PART, month_start_idx, months_to_output);
            outhold.npp_part_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.npp_part_for_output.push_back(y_npp);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.npp_part_for_output[0], NUM_PFT_PART, year_start_idx, years_to_output);
            outhold.npp_part_for_output.clear();
          }
        }
      }
      //Neither PFT nor Compartment - total instead
      else if(!curr_spec.pft && !curr_spec.compartment){
        //monthly
        if(curr_spec.monthly){
          outhold.npp_tot_for_output.push_back(cohort.bdall->m_a2v.nppall);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.npp_tot_for_output[0], 1, month_start_idx, months_to_output);
            outhold.npp_tot_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.npp_tot_for_output.push_back(cohort.bdall->y_a2v.nppall);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.npp_tot_for_output[0], 1, year_start_idx, years_to_output);
            outhold.npp_tot_for_output.clear();
          }
        }
      }
    }//end critical(outputNPP)
  }//end NPP
  map_itr = netcdf_outputs.end();


  //NREQ
  map_itr = netcdf_outputs.find("NREQ");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: NREQ";
    curr_spec = map_itr->second;

    #pragma omp critical(outputNREQ)
    {
    //By compartment
    if(curr_spec.compartment){
      double m_nreq[NUM_PFT][NUM_PFT_PART] = {0};
     
      for(int ip=0; ip<NUM_PFT; ip++){
        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          m_nreq[ip][ipp] = cohort.vegbgc[ip].tmp_vegs.nreq[ipp];
        }
      } 
      output_nc_5dim(&curr_spec, file_stage_suffix, &m_nreq[0][0], NUM_PFT_PART, NUM_PFT, month_timestep, 1);
    }
    //Total
    else{
        //cohort.vegbgc[].tmp_vegs.nreqall;
      double m_nreq[NUM_PFT] = {0};
    }


    }//end critical(outputNREQ)
  }//end NREQ
  map_itr = netcdf_outputs.end();


  //NRESORB
  map_itr = netcdf_outputs.find("NRESORB");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: NRESORB";
    curr_spec = map_itr->second;

    #pragma omp critical(outputNRESORB)
    {
      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){

        double m_nresorb[NUM_PFT_PART][NUM_PFT];
        double y_nresorb[NUM_PFT_PART][NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            m_nresorb[ipp][ip] = cohort.bd[ip].m_v2v.nresorb[ipp];
            y_nresorb[ipp][ip] = cohort.bd[ip].y_v2v.nresorb[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &m_nresorb[0][0], NUM_PFT_PART, NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &y_nresorb[0][0], NUM_PFT_PART, NUM_PFT, year, 1);
        }
      }
      //PFT only
      else if(curr_spec.pft && !curr_spec.compartment){

        double m_nresorb[NUM_PFT], y_nresorb[NUM_PFT];

        for(int ip=0; ip<NUM_PFT; ip++){
          m_nresorb[ip] = cohort.bd[ip].m_v2v.nresorball;
          y_nresorb[ip] = cohort.bd[ip].y_v2v.nresorball;
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_nresorb[0], NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_nresorb[0], NUM_PFT, year, 1);
        }
      }
      //Compartment only
      else if(!curr_spec.pft && curr_spec.compartment){

        double m_nresorb[NUM_PFT_PART] = {0};
        double y_nresorb[NUM_PFT_PART] = {0};

        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){
            m_nresorb[ipp] += cohort.bd[ip].m_v2v.nresorb[ipp];
            y_nresorb[ipp] += cohort.bd[ip].y_v2v.nresorb[ipp];
          }
        }
        //monthly 
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_nresorb[0], NUM_PFT_PART, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_nresorb[0], NUM_PFT_PART, year, 1);
        }
      }
      //Total, instead of by PFT or compartment
      else if(!curr_spec.pft && !curr_spec.compartment){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_v2v.nresorball, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_v2v.nresorball, 1, year, 1);
        }

      }
    }
  }//end NRESORB
  map_itr = netcdf_outputs.end();


  //NUPTAKELAB
  map_itr = netcdf_outputs.find("NUPTAKELAB");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: NUPTAKELAB";
    curr_spec = map_itr->second;

    #pragma omp critical(outputNUPTAKELAB)
    {
      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){
        /*** STUB ***/
        //Currently unavailable. Labile N uptake will need to be made
        // accessible by PFT compartment.
      }
      //PFT only (4 dimensions)
      else if(curr_spec.pft && !curr_spec.compartment){
        double m_labnuptake[NUM_PFT], y_labnuptake[NUM_PFT];

        for(int ip=0; ip<NUM_PFT; ip++){
          m_labnuptake[ip] = cohort.bd[ip].m_soi2v.lnuptake;
          y_labnuptake[ip] = cohort.bd[ip].y_soi2v.lnuptake;
        }

        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_labnuptake[0], NUM_PFT, month_timestep, 1);
        } 
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_labnuptake[0], NUM_PFT, year, 1);
        }
      }
      //Compartment only
      else if(!curr_spec.pft && curr_spec.compartment){
        /*** STUB ***/
      }
      //Neither PFT nor compartment
      else if(!curr_spec.pft && !curr_spec.compartment){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_soi2v.lnuptake, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_soi2v.lnuptake, 1, year, 1);
        }
      }
    }//end critical(outputNUPTAKELAB)
  }//end NUPTAKELAB
  map_itr = netcdf_outputs.end();


  //NUPTAKEST
  map_itr = netcdf_outputs.find("NUPTAKEST");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: NUPTAKEST";
    curr_spec = map_itr->second;

    #pragma omp critical(outputNUPTAKEST)
    {
      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){
        double m_snuptake[NUM_PFT_PART][NUM_PFT];
        double y_snuptake[NUM_PFT_PART][NUM_PFT];

        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            m_snuptake[ipp][ip] = cohort.bd[ip].m_soi2v.snuptake[ipp];
            y_snuptake[ipp][ip] = cohort.bd[ip].y_soi2v.snuptake[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &m_snuptake[0][0], NUM_PFT_PART, NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &y_snuptake[0][0], NUM_PFT_PART, NUM_PFT, year, 1);
        }
      }
      //PFT only (4 dimensions)
      else if(curr_spec.pft && !curr_spec.compartment){
        double m_snuptake[NUM_PFT] = {0};
        double y_snuptake[NUM_PFT] = {0};

        for(int ip=0; ip<NUM_PFT; ip++){
          m_snuptake[ip] = cohort.bd[ip].m_soi2v.snuptakeall;
          y_snuptake[ip] = cohort.bd[ip].y_soi2v.snuptakeall;
        }
        //monthly 
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_snuptake[0], NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_snuptake[0], NUM_PFT, year, 1);
        }
      }
      //Compartment only (4 dimensions)
      else if(!curr_spec.pft && curr_spec.compartment){
        double m_snuptake[NUM_PFT_PART] = {0};
        double y_snuptake[NUM_PFT_PART] = {0};

        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){
            m_snuptake[ipp] += cohort.bd[ip].m_soi2v.snuptake[ipp]; 
            y_snuptake[ipp] += cohort.bd[ip].y_soi2v.snuptake[ipp]; 
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_snuptake[0], NUM_PFT_PART, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_snuptake[0], NUM_PFT_PART, year, 1);
        }

      }
      //Neither PFT nor compartment
      else if(!curr_spec.pft && !curr_spec.compartment){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_soi2v.snuptakeall, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_soi2v.snuptakeall, 1, year, 1);
        }
      }
    }//end critical(outputNUPTAKEST)
  }//end NUPTAKEST
  map_itr = netcdf_outputs.end();


  //ORGN
  map_itr = netcdf_outputs.find("ORGN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: ORGN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputORGN)
    {
      //By layer
      if(curr_spec.layer){
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_sois.orgn[0], MAX_SOI_LAY, month_timestep, 1);
        }
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_sois.orgn[0], MAX_SOI_LAY, year, 1);
        }
      }
      //Total, instead of by layer
      else if(!curr_spec.layer){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_soid.orgnsum, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_soid.orgnsum, 1, year, 1);
        }
      }
    }//end critical(outputORGN)
  }//end ORGN
  map_itr = netcdf_outputs.end();


  //PERCOLATION
  map_itr = netcdf_outputs.find("PERCOLATION");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: PERCOLATION";
    curr_spec = map_itr->second;

    #pragma omp critical(outputPERCOLATION)
    {
      //daily
      if(curr_spec.daily){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_percolation[0][0], MAX_SOI_LAY, day_timestep, dinm);
      }
    }//end critical(outputPERCOLATION)
  }//end PERCOLATION
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("PERMAFROST");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: PERMAFROST";
    curr_spec = map_itr->second;

    #pragma omp critical(outputPERMAFROST)
    {
      output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.permafrost, 1, year, 1);
    }//end critical(outputPERMAFROST)
  }//end PERMAFROST
  map_itr = netcdf_outputs.end();


  //PET
  map_itr = netcdf_outputs.find("PET");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: PET";
    curr_spec = map_itr->second;

    #pragma omp critical(outputPET)
    {
      //by PFT
//by PFT is disabled for now because it erroneously
// includes soil and snow evaporation per PFT, which
// throws off results if the PFT values are summed.
/*      if(curr_spec.pft){
        std::array<double, NUM_PFT> pet_arr{};

        //daily
        if(curr_spec.daily){

          for(int id=0; id<DINM[month]; id++){
            for(int ip=0; ip<NUM_PFT; ip++){
              pet_arr[ip] = cohort.ed[ip].daily_pet[id];
            }
            outhold.pet_for_output.push_back(pet_arr);
          }

          if(end_of_year){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.pet_for_output[0][0], NUM_PFT, day_timestep, DINY);
            outhold.pet_for_output.clear();
          }
        }
        //monthly
        else if(curr_spec.monthly){
          for(int ip=0; ip<NUM_PFT; ip++){
            pet_arr[ip] = cohort.ed[ip].m_l2a.pet;
          }
          outhold.pet_for_output.push_back(pet_arr);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.pet_for_output[0][0], NUM_PFT, month_start_idx, months_to_output);
            outhold.pet_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          for(int ip=0; ip<NUM_PFT; ip++){
            pet_arr[ip] = cohort.ed[ip].y_l2a.pet;
          }
          outhold.pet_for_output.push_back(pet_arr);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.pet_for_output[0][0], NUM_PFT, year_start_idx, years_to_output);
            outhold.pet_for_output.clear();
          }
        }
      }*/
      //Total, instead of by PFT
      if(!curr_spec.pft){

        //daily
        if(curr_spec.daily){

          for(int id=0; id<DINM[month]; id++){
            double daily_pet_tot = 0.;
            for(int ip=0; ip<NUM_PFT; ip++){
              daily_pet_tot += cohort.ed[ip].daily_pet[id];
            }
            outhold.pet_tot_for_output.push_back(daily_pet_tot);
          }

          if(end_of_year){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.pet_tot_for_output[0], 1, day_timestep, DINY);
            outhold.pet_tot_for_output.clear();
          }
        }
        //monthly
        else if(curr_spec.monthly){

          outhold.pet_tot_for_output.push_back(cohort.edall->m_l2a.pet);
          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.pet_tot_for_output[0], 1, month_start_idx, months_to_output);
            outhold.pet_tot_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.pet_tot_for_output.push_back(cohort.edall->y_l2a.pet);
          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.pet_tot_for_output[0], 1, year_start_idx, years_to_output);
            outhold.pet_tot_for_output.clear();
          }
        }
      }
    }//end critical(outputPET)
  }//end PET
  map_itr = netcdf_outputs.end();


  //QDRAINAGE
  map_itr = netcdf_outputs.find("QDRAINAGE");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: QDRAINAGE";
    curr_spec = map_itr->second;

    #pragma omp critical(outputQDRAINAGE)
    {
      //daily
      if(curr_spec.daily){
        for(int id=0; id<DINM[month]; id++){
          outhold.qdrain_for_output.push_back(cohort.edall->daily_qdrain[id]);
        }

        if(end_of_year){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.qdrain_for_output[0], 1, day_timestep, DINY);
          outhold.qdrain_for_output.clear();
        }
      }
      //monthly
      else if(curr_spec.monthly){
        outhold.qdrain_for_output.push_back(cohort.edall->m_soi2l.qdrain);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.qdrain_for_output[0], 1, month_start_idx, months_to_output);
          outhold.qdrain_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        outhold.qdrain_for_output.push_back(cohort.edall->y_soi2l.qdrain);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.qdrain_for_output[0], 1, year_start_idx, years_to_output);
          outhold.qdrain_for_output.clear();
        }
      }
    }//end critical(outputQDRAINAGE)
  }//end QDRAINAGE 
  map_itr = netcdf_outputs.end();


  //QDRAINLAYER
  map_itr = netcdf_outputs.find("QDRAINLAYER");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: QDRAINLAYER";
    curr_spec = map_itr->second;

    #pragma omp critical(outputQDRAINLAYER)
    {
      //daily
      if(curr_spec.daily){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_layer_drain[0][0], MAX_SOI_LAY, day_timestep, dinm);
      }
    }//end critical(outputQDRAINLAYER)
  }//end QDRAINLAYER
  map_itr = netcdf_outputs.end();


  //QINFILTRATION
  map_itr = netcdf_outputs.find("QINFILTRATION");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: QINFILTRATION";
    curr_spec = map_itr->second;

    #pragma omp critical(outputQINFILTRATION)
    {
      //daily
      if(curr_spec.daily){
        for(int id=0; id<DINM[month]; id++){
          outhold.qinfil_for_output.push_back(cohort.edall->daily_qinfl[id]);
        }

        if(end_of_year){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.qinfil_for_output[0], 1, day_timestep, DINY);
          outhold.qinfil_for_output.clear();
        }
      }
      //monthly
      else if(curr_spec.monthly){
        outhold.qinfil_for_output.push_back(cohort.edall->m_soi2l.qinfl);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.qinfil_for_output[0], 1, month_start_idx, months_to_output);
          outhold.qinfil_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        outhold.qinfil_for_output.push_back(cohort.edall->y_soi2l.qinfl);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.qinfil_for_output[0], 1, year_start_idx, years_to_output);
          outhold.qinfil_for_output.clear();
        }
      }
    }//end critical(outputQINFILTRATION)
  }//end QINFILTRATION
  map_itr = netcdf_outputs.end();


  //QRUNOFF
  map_itr = netcdf_outputs.find("QRUNOFF");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: QRUNOFF";
    curr_spec = map_itr->second;

    #pragma omp critical(outputQRUNOFF)
    {
      //daily
      if(curr_spec.daily){
        for(int id=0; id<DINM[month]; id++){
          outhold.qrunoff_for_output.push_back(cohort.edall->daily_qover[id]);
        }

        if(end_of_year){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.qrunoff_for_output[0], 1, day_timestep, DINY);
          outhold.qrunoff_for_output.clear();
        }
      }
      //monthly
      else if(curr_spec.monthly){
        outhold.qrunoff_for_output.push_back(cohort.edall->m_soi2l.qover);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.qrunoff_for_output[0], 1, month_start_idx, months_to_output);
          outhold.qrunoff_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        outhold.qrunoff_for_output.push_back(cohort.edall->y_soi2l.qover);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.qrunoff_for_output[0], 1, year_start_idx, years_to_output);
          outhold.qrunoff_for_output.clear();
        }
      }
    }//end critical(outputQRUNOFF)
  }//end QRUNOFF 
  map_itr = netcdf_outputs.end();


  //RAINFALL
  map_itr = netcdf_outputs.find("RAINFALL");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: RAINFALL";
    curr_spec = map_itr->second;

    #pragma omp critical(outputRAINFALL)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_a2l.rnfl, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_a2l.rnfl, 1, year, 1);
      }
    }//end critical(outputRAINFALL)
  }//end RAINFALL
  map_itr = netcdf_outputs.end();


  //RECO
  map_itr = netcdf_outputs.find("RECO");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: RECO";
    curr_spec = map_itr->second;

    #pragma omp critical(outputRECO)
    {

      //RHSOM, RHDWD, RM, RG
      //Needs CH4OXID added when methane is merged

      //monthly
      if(curr_spec.monthly){
        double m_reco = cohort.bdall->m_soi2a.rhsom
                      + cohort.bdall->m_soi2a.rhwdeb
                      + cohort.bdall->m_v2a.rmall
                      + cohort.bdall->m_v2a.rgall;

        outhold.reco_for_output.push_back(m_reco);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.reco_for_output[0], 1, month_start_idx, months_to_output);
          outhold.reco_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){

        double y_reco = cohort.bdall->y_soi2a.rhsom
                      + cohort.bdall->y_soi2a.rhwdeb
                      + cohort.bdall->y_v2a.rmall
                      + cohort.bdall->y_v2a.rgall;

        outhold.reco_for_output.push_back(y_reco);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.reco_for_output[0], 1, year_start_idx, years_to_output);
          outhold.reco_for_output.clear();
        }

      } 
    }//end critical(outputRECO)
  }//end RECO
  map_itr = netcdf_outputs.end();


  //RG
  map_itr = netcdf_outputs.find("RG");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: RG";
    curr_spec = map_itr->second;

    #pragma omp critical(outputRG)
    {
      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){
        std::array<std::array<double, NUM_PFT>, NUM_PFT_PART> m_rg{};
        std::array<std::array<double, NUM_PFT>, NUM_PFT_PART> y_rg{};

        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            m_rg[ipp][ip] = cohort.bd[ip].m_v2a.rg[ipp];
            y_rg[ipp][ip] = cohort.bd[ip].y_v2a.rg[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          outhold.rg_for_output.push_back(m_rg);

          if(output_this_timestep){
            output_nc_5dim(&curr_spec, file_stage_suffix, &outhold.rg_for_output[0][0][0], NUM_PFT_PART, NUM_PFT, month_start_idx, months_to_output);
            outhold.rg_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.rg_for_output.push_back(y_rg);

          if(output_this_timestep){
            output_nc_5dim(&curr_spec, file_stage_suffix, &outhold.rg_for_output[0][0][0], NUM_PFT_PART, NUM_PFT, year_start_idx, years_to_output);
            outhold.rg_for_output.clear();
          }
        }
      }
      //PFT only (4 dimensions)
      else if(curr_spec.pft && !curr_spec.compartment){
        std::array<double, NUM_PFT> m_rg{};
        std::array<double, NUM_PFT> y_rg{};

        for(int ip=0; ip<NUM_PFT; ip++){
          m_rg[ip] = cohort.bd[ip].m_v2a.rgall;
          y_rg[ip] = cohort.bd[ip].y_v2a.rgall;
        }

        //monthly
        if(curr_spec.monthly){
          outhold.rg_pft_for_output.push_back(m_rg);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.rg_pft_for_output[0][0], NUM_PFT, month_start_idx, months_to_output);
            outhold.rg_pft_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.rg_pft_for_output.push_back(y_rg);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.rg_pft_for_output[0][0], NUM_PFT, year_start_idx, years_to_output);
            outhold.rg_pft_for_output.clear();
          }
        }
      }
      //Compartment only (4 dimensions)
      else if(!curr_spec.pft && curr_spec.compartment){
        std::array<double, NUM_PFT_PART> m_rg{};
        std::array<double, NUM_PFT_PART> y_rg{};

        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){
            m_rg[ipp] += cohort.bd[ip].m_v2a.rg[ipp];
            y_rg[ipp] += cohort.bd[ip].y_v2a.rg[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          outhold.rg_part_for_output.push_back(m_rg);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.rg_part_for_output[0][0], NUM_PFT_PART, month_start_idx, months_to_output);
            outhold.rg_part_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.rg_part_for_output.push_back(y_rg);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.rg_part_for_output[0][0], NUM_PFT_PART, year_start_idx, years_to_output);
            outhold.rg_part_for_output.clear();
          }
        }
      }
      //Neither PFT nor compartment - Total
      else if(!curr_spec.pft && !curr_spec.compartment){
        //monthly
        if(curr_spec.monthly){
          outhold.rg_tot_for_output.push_back(cohort.bdall->m_v2a.rgall);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.rg_tot_for_output[0], 1, month_start_idx, months_to_output);
            outhold.rg_tot_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.rg_tot_for_output.push_back(cohort.bdall->y_v2a.rgall);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.rg_tot_for_output[0], 1, year_start_idx, years_to_output);
            outhold.rg_tot_for_output.clear();
          }
        }
      }
    }//end critical(outputRG)
  }//end RG
  map_itr = netcdf_outputs.end();


  //Dead woody debris RH
  map_itr = netcdf_outputs.find("RHDWD");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"RHDWD";
    curr_spec = map_itr->second;

    #pragma omp critical(outputRHDWD)
    {
      //monthly
      if(curr_spec.monthly){
        outhold.rhdwd_for_output.push_back(cohort.bdall->m_soi2a.rhwdeb);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.rhdwd_for_output[0], 1, month_start_idx, months_to_output);
          outhold.rhdwd_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        outhold.rhdwd_for_output.push_back(cohort.bdall->y_soi2a.rhwdeb);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.rhdwd_for_output[0], 1, year_start_idx, years_to_output);
          outhold.rhdwd_for_output.clear();
        }
      }
    }//end critical(outputRHDWD)
  }//end RHDWD
  map_itr = netcdf_outputs.end();


  //RHSOM
  map_itr = netcdf_outputs.find("RHSOM");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: RHSOM";
    curr_spec = map_itr->second;

    #pragma omp critical(outputRHSOM)
    {
      //By layer
      if(curr_spec.layer){
        std::array<double, MAX_SOI_LAY> rh_arr{};

        //monthly
        if(curr_spec.monthly){
          for(int il=0; il<MAX_SOI_LAY; il++){
            rh_arr[il] = cohort.bdall->m_soi2a.rhrawc[il]
                       + cohort.bdall->m_soi2a.rhsoma[il]
                       + cohort.bdall->m_soi2a.rhsompr[il]
                       + cohort.bdall->m_soi2a.rhsomcr[il];
          }
          outhold.rh_for_output.push_back(rh_arr);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.rh_for_output[0], MAX_SOI_LAY, month_start_idx, months_to_output);
            outhold.rh_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          for(int il=0; il<MAX_SOI_LAY; il++){
            rh_arr[il] = cohort.bdall->y_soi2a.rhrawc[il]
                       + cohort.bdall->y_soi2a.rhsoma[il]
                       + cohort.bdall->y_soi2a.rhsompr[il]
                       + cohort.bdall->y_soi2a.rhsomcr[il];
          }
          outhold.rh_for_output.push_back(rh_arr);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.rh_for_output[0], MAX_SOI_LAY, year_start_idx, years_to_output);
            outhold.rh_for_output.clear();
          }
        }
      }
      //Total, instead of by layer
      else if(!curr_spec.layer){
        //monthly
        if(curr_spec.monthly){
          outhold.rh_tot_for_output.push_back(cohort.bdall->m_soi2a.rhsom);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.rh_tot_for_output[0], 1, month_start_idx, months_to_output);
            outhold.rh_tot_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.rh_tot_for_output.push_back(cohort.bdall->y_soi2a.rhsom);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.rh_tot_for_output[0], 1, year_start_idx, years_to_output);
            outhold.rh_tot_for_output.clear();
          }
        }
      }
    }//end critical(outputRHSOM)
  }//end RHSOM
  map_itr = netcdf_outputs.end();


  //RM
  map_itr = netcdf_outputs.find("RM");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: RM";
    curr_spec = map_itr->second;

    #pragma omp critical(outputRM)
    {
      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){

        std::array<std::array<double, NUM_PFT>, NUM_PFT_PART> m_rm{};
        std::array<std::array<double, NUM_PFT>, NUM_PFT_PART> y_rm{};

        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            m_rm[ipp][ip] = cohort.bd[ip].m_v2a.rm[ipp];
            y_rm[ipp][ip] = cohort.bd[ip].y_v2a.rm[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){

          outhold.rm_for_output.push_back(m_rm);

          if(output_this_timestep){
            output_nc_5dim(&curr_spec, file_stage_suffix, &outhold.rm_for_output[0][0][0], NUM_PFT_PART, NUM_PFT, month_start_idx, months_to_output);
            outhold.rm_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){

          outhold.rm_for_output.push_back(y_rm);

          if(output_this_timestep){
            output_nc_5dim(&curr_spec, file_stage_suffix, &outhold.rm_for_output[0][0][0], NUM_PFT_PART, NUM_PFT, year_start_idx, years_to_output);
            outhold.rm_for_output.clear();
          }
        }
      }
      //PFT only (4 dimensions)
      else if(curr_spec.pft && !curr_spec.compartment){

        std::array<double, NUM_PFT> m_rm{};
        std::array<double, NUM_PFT> y_rm{};

        for(int ip=0; ip<NUM_PFT; ip++){
          m_rm[ip] = cohort.bd[ip].m_v2a.rmall;
          y_rm[ip] = cohort.bd[ip].y_v2a.rmall;
        }
        //monthly
        if(curr_spec.monthly){
          outhold.rm_pft_for_output.push_back(m_rm);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.rm_pft_for_output[0][0], NUM_PFT, month_start_idx, months_to_output);
            outhold.rm_pft_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.rm_pft_for_output.push_back(y_rm);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.rm_pft_for_output[0][0], NUM_PFT, year_start_idx, years_to_output);
            outhold.rm_pft_for_output.clear();
          }
        }
      }
      //Compartment only (4 dimensions)
      else if(!curr_spec.pft && curr_spec.compartment){

        std::array<double, NUM_PFT_PART> m_rm{};
        std::array<double, NUM_PFT_PART> y_rm{};

        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){
            m_rm[ipp] += cohort.bd[ip].m_v2a.rm[ipp];
            y_rm[ipp] += cohort.bd[ip].y_v2a.rm[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          outhold.rm_part_for_output.push_back(m_rm);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.rm_part_for_output[0][0], NUM_PFT_PART, month_start_idx, months_to_output);
            outhold.rm_part_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.rm_part_for_output.push_back(y_rm);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.rm_part_for_output[0][0], NUM_PFT_PART, year_start_idx, years_to_output);
            outhold.rm_part_for_output.clear();
          }
        }
      }
      //Neither PFT nor compartment - Total
      else if(!curr_spec.pft && !curr_spec.compartment){

        //monthly
        if(curr_spec.monthly){
          outhold.rm_tot_for_output.push_back(cohort.bdall->m_v2a.rmall);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.rm_tot_for_output[0], 1, month_start_idx, months_to_output);
            outhold.rm_tot_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.rm_tot_for_output.push_back(cohort.bdall->y_v2a.rmall);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.rm_tot_for_output[0], 1, year_start_idx, years_to_output);
            outhold.rm_tot_for_output.clear();
          }
        }
      }
    }//end critical(outputRM)
  }//end RM
  map_itr = netcdf_outputs.end();


  //ROLB
  map_itr = netcdf_outputs.find("ROLB");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: ROLB";
    curr_spec = map_itr->second;

    #pragma omp critical(outputROLB)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.year_fd[month].fire_soid.rolb, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        //TODO. This will not work if there is more than one fire per year
        // What does yearly ROLB even mean with multiple fires?
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.fd->fire_soid.rolb, 1, year, 1);
      }
    }//end critical(outputROLB)
  }//end ROLB
  map_itr = netcdf_outputs.end();


  //ROOTWATERUPTAKE
  map_itr = netcdf_outputs.find("ROOTWATERUPTAKE");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: ROOTWATERUPTAKE";
    curr_spec = map_itr->second;

    #pragma omp critical(outputROOTWATERUPTAKE)
    {
      //daily
      if(curr_spec.daily){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_root_water_uptake[0][0], MAX_SOI_LAY, day_timestep, dinm);
      }
    }//end critical(outputROOTWATERUPTAKE)
  }//end ROOTWATERUPTAKE
  map_itr = netcdf_outputs.end();


  //Shallow C
  map_itr = netcdf_outputs.find("SHLWC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"SHLWC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputSHLWC)
    {
      //monthly
      if(curr_spec.monthly){
        outhold.shlwc_for_output.push_back(cohort.bdall->m_soid.shlwc);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.shlwc_for_output[0], 1, month_start_idx, months_to_output);
          outhold.shlwc_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        outhold.shlwc_for_output.push_back(cohort.bdall->y_soid.shlwc);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.shlwc_for_output[0], 1, year_start_idx, years_to_output);
          outhold.shlwc_for_output.clear();
        }
      }
    }//end critical(outputSHLWC)
  }//end SHLWC 
  map_itr = netcdf_outputs.end();


  //SHLWDZ
  map_itr = netcdf_outputs.find("SHLWDZ");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: SHLWDZ";
    curr_spec = map_itr->second;

    #pragma omp critical(outputSHLWDZ)
    {
      double shlwdz = 0;
      Layer* currL = cohort.ground.toplayer;
      while(currL!=NULL){
        if(currL->isFibric){
          shlwdz += currL->dz;
        }
        currL = currL->nextl;
      }
      output_nc_3dim(&curr_spec, file_stage_suffix, &shlwdz, 1, year, 1);
    }//end critical(outputSHLWDZ)
  }//end SHLWDZ
  map_itr = netcdf_outputs.end();


  //SNOWEND
  map_itr = netcdf_outputs.find("SNOWEND");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: SNOWEND";
    curr_spec = map_itr->second;

    #pragma omp critical(outputSNOWEND)
    {
      output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_snws.snowend, 1, year, 1);
    }//end critical(outputSNOWEND)
  }//end SNOWEND
  map_itr = netcdf_outputs.end();


  //SNOWFALL
  map_itr = netcdf_outputs.find("SNOWFALL");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: SNOWFALL";
    curr_spec = map_itr->second;

    #pragma omp critical(outputSNOWFALL)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_a2l.snfl, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_a2l.snfl, 1, year, 1);
      }
    }//end critical(outputSNOWFALL)
  }//end SNOWFALL
  map_itr = netcdf_outputs.end();


  //Snowlayerdz - a snapshot of the time when output is called
  map_itr = netcdf_outputs.find("SNOWLAYERDZ");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: SNOWLAYERDZ";
    curr_spec = map_itr->second;

    #pragma omp critical(outputSNOWLAYERDZ)
    {
      std::array<double, MAX_SNW_LAY> snowlayerdz_arr{};

      Layer* currL = cohort.ground.toplayer;
      while(currL->isSnow){
        snowlayerdz_arr[currL->indl-1] = currL->dz;
        currL = currL->nextl;
      } 

      if(curr_spec.monthly){
        outhold.snowlayerdz_for_output.push_back(snowlayerdz_arr);

        if(output_this_timestep){
          output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.snowlayerdz_for_output[0], MAX_SNW_LAY, month_start_idx, months_to_output);
          outhold.snowlayerdz_for_output.clear();
        }
      }
      else if(curr_spec.yearly){
        outhold.snowlayerdz_for_output.push_back(snowlayerdz_arr);

        if(output_this_timestep){
          output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.snowlayerdz_for_output[0], MAX_SNW_LAY, year_start_idx, years_to_output);
          outhold.snowlayerdz_for_output.clear();
        }
      }

     }//end critical(outputSNOWLAYERDZ)
  }//end SNOWLAYERDZ
  map_itr = netcdf_outputs.end();


  //Snowlayertemp - a snapshot of the time when output is called
  map_itr = netcdf_outputs.find("SNOWLAYERTEMP");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: SNOWLAYERTEMP";
    curr_spec = map_itr->second;

    #pragma omp critical(outputSNOWLAYERTEMP)
    {
      std::array<double, MAX_SNW_LAY> snowlayertemp_arr{};

      Layer* currL = cohort.ground.toplayer;
      while(currL->isSnow){
        snowlayertemp_arr[currL->indl-1] = currL->tem;
        currL = currL->nextl;
      } 

      if(curr_spec.monthly){
        outhold.snowlayertemp_for_output.push_back(snowlayertemp_arr);

        if(output_this_timestep){
          output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.snowlayertemp_for_output[0], MAX_SNW_LAY, month_start_idx, months_to_output);
          outhold.snowlayertemp_for_output.clear();
        }
      }
      else if(curr_spec.yearly){
        outhold.snowlayertemp_for_output.push_back(snowlayertemp_arr);

        if(output_this_timestep){
          output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.snowlayertemp_for_output[0], MAX_SNW_LAY, year_start_idx, years_to_output);
          outhold.snowlayertemp_for_output.clear();
        }
      }

     }//end critical(outputSNOWLAYERTEMP)
  }//end SNOWLAYERTEMP
  map_itr = netcdf_outputs.end();


  //SNOWSTART
  map_itr = netcdf_outputs.find("SNOWSTART");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: SNOWSTART";
    curr_spec = map_itr->second;

    #pragma omp critical(outputSNOWSTART)
    {
      output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_snws.snowstart, 1, year, 1);
    }//end critical(outputSNOWSTART)
  }//end SNOWSTART
  map_itr = netcdf_outputs.end();


  //Snowthick - a snapshot of the time when output is called
  map_itr = netcdf_outputs.find("SNOWTHICK");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: SNOWTHICK";
    curr_spec = map_itr->second;

    #pragma omp critical(outputSNOWTHICK)
    {
      //This calculated value is for monthly and yearly
      double snowthick = 0.;
      Layer* currL = cohort.ground.toplayer;
      while(currL->isSnow){
        snowthick += currL->dz;
        currL = currL->nextl;
      }

      //daily
      if(curr_spec.daily){
        for(int id=0; id<DINM[month]; id++){
          outhold.snowthick_for_output.push_back(cohort.edall->daily_snowthick[id]);
        }

        if(end_of_year){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.snowthick_for_output[0], 1, day_timestep, DINY);
          outhold.snowthick_for_output.clear();
        }
      }
      //monthly
      else if(curr_spec.monthly){
        outhold.snowthick_for_output.push_back(snowthick);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.snowthick_for_output[0], 1, month_start_idx, months_to_output);
          outhold.snowthick_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        outhold.snowthick_for_output.push_back(snowthick);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.snowthick_for_output[0], 1, year_start_idx, years_to_output);
          outhold.snowthick_for_output.clear();
        }
      }
    }//end critical(outputSNOWTHICK)
  }//end SNOWTHICK
  map_itr = netcdf_outputs.end();


  // SOC
  map_itr = netcdf_outputs.find("SOC");
  if (map_itr != netcdf_outputs.end()) {
    BOOST_LOG_SEV(glg, debug) << "NetCDF output: SOC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputSOC)
    {
      // By layer
      if (curr_spec.layer) {
        // Monthly
        if (curr_spec.monthly) {
          std::array<double, MAX_SOI_LAY> m_soc;
          for (int il=0; il<MAX_SOI_LAY; il++) {
            m_soc[il] = cohort.bdall->m_sois.rawc[il]
                      + cohort.bdall->m_sois.soma[il]
                      + cohort.bdall->m_sois.sompr[il]
                      + cohort.bdall->m_sois.somcr[il];
          }
          outhold.soc_for_output.push_back(m_soc);

          if (output_this_timestep) {
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.soc_for_output[0][0], MAX_SOI_LAY, month_start_idx, months_to_output);
            outhold.soc_for_output.clear();
          }
        }
        // Yearly
        else if (curr_spec.yearly) {
          std::array<double, MAX_SOI_LAY> y_soc;
          for (int il=0; il<MAX_SOI_LAY; il++) {
            y_soc[il] = cohort.bdall->y_sois.rawc[il]
                      + cohort.bdall->y_sois.soma[il]
                      + cohort.bdall->y_sois.sompr[il]
                      + cohort.bdall->y_sois.somcr[il];
          }
          outhold.soc_for_output.push_back(y_soc);

          if (output_this_timestep) {
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.soc_for_output[0][0], MAX_SOI_LAY, year_start_idx, years_to_output);
            outhold.soc_for_output.clear();
          }
        }
      }
      // Total, instead of by layer
      else if (!curr_spec.layer) {
        // Monthly
        if (curr_spec.monthly) {

          double m_soc_tot = 0.0;
          for (int il=0; il<MAX_SOI_LAY; il++) {
            m_soc_tot += cohort.bdall->m_sois.rawc[il]
                       + cohort.bdall->m_sois.soma[il]
                       + cohort.bdall->m_sois.sompr[il]
                       + cohort.bdall->m_sois.somcr[il];
          }

          outhold.soc_tot_for_output.push_back(m_soc_tot);

          if (output_this_timestep) {
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.soc_tot_for_output[0], 1, month_start_idx, months_to_output);
            outhold.soc_tot_for_output.clear();
          }
        }
        // Yearly
        else if (curr_spec.yearly) {

          double y_soc_tot = 0.0;
          for (int il=0; il<MAX_SOI_LAY; il++) {
            y_soc_tot += cohort.bdall->y_sois.rawc[il]
                       + cohort.bdall->y_sois.soma[il]
                       + cohort.bdall->y_sois.sompr[il]
                       + cohort.bdall->y_sois.somcr[il];
          }

          outhold.soc_tot_for_output.push_back(y_soc_tot);

          if (output_this_timestep) {
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.soc_tot_for_output[0], 1, year_start_idx, years_to_output);
            outhold.soc_tot_for_output.clear();
          }
        }
      }
    } //end critical(outputSOC)
  } //end SOC
  map_itr = netcdf_outputs.end();


  //SOCFROZEN
  map_itr = netcdf_outputs.find("SOCFROZEN");
  if (map_itr != netcdf_outputs.end()) {
    BOOST_LOG_SEV(glg, debug) << "NetCDF output: SOCFROZEN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputSOCFROZEN)
    {
      double frozenC = 0.0;

      Layer* currl = this->cohort.ground.fstsoill;
      while(currl != NULL && currl != cohort.ground.lstsoill){

        double layerC = currl->rawc + currl->soma
                      + currl->sompr + currl->somcr;

        double temp_frozenC = currl->frozenfrac * layerC;

        frozenC += currl->frozenfrac * layerC;

        currl = currl->nextl;
      }

      outhold.socfrozen_for_output.push_back(frozenC);

      //Monthly
      if(curr_spec.monthly){
        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.socfrozen_for_output[0], 1, month_start_idx, months_to_output);
          outhold.socfrozen_for_output.clear();
        }
      }
      //Yearly
      else if(curr_spec.yearly){
        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.socfrozen_for_output[0], 1, year_start_idx, years_to_output);
          outhold.socfrozen_for_output.clear();
        }
      }
    } //end critical(outputSOCFROZEN)
  } //end SOCFROZEN
  map_itr = netcdf_outputs.end();


  //SOCUNFROZEN
  map_itr = netcdf_outputs.find("SOCUNFROZEN");
  if (map_itr != netcdf_outputs.end()) {
    BOOST_LOG_SEV(glg, debug) << "NetCDF output: SOCUNFROZEN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputSOCUNFROZEN)
    {
      double unfrozenC = 0.0;

      Layer* currl = this->cohort.ground.fstsoill;
      while(currl != NULL && currl != cohort.ground.lstsoill){

        double layerC = currl->rawc + currl->soma
                      + currl->sompr + currl->somcr;

        unfrozenC += (1 - currl->frozenfrac) * layerC;

        currl = currl->nextl;
      }

      outhold.socunfrozen_for_output.push_back(unfrozenC);

      //Monthly
      if(curr_spec.monthly){
        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.socunfrozen_for_output[0], 1, month_start_idx, months_to_output);
          outhold.socunfrozen_for_output.clear();
        }
      }
      //Yearly
      else if(curr_spec.yearly){

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.socunfrozen_for_output[0], 1, year_start_idx, years_to_output);
          outhold.socunfrozen_for_output.clear();
        }
      }
    } //end critical(outputSOCUNFROZEN)
  } //end SOCUNFROZEN
  map_itr = netcdf_outputs.end();


  //SOMA - soil organic matter, active
  map_itr = netcdf_outputs.find("SOMA");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: SOMA";
    curr_spec = map_itr->second;

    #pragma omp critical(outputSOMA)
    {
      //By layer
      if(curr_spec.layer){
        if(curr_spec.monthly){
          std::array<double, MAX_SOI_LAY> m_soma;
          for(int i = 0; i < MAX_SOI_LAY; i++) {
            m_soma[i] = cohort.bdall->m_sois.soma[i];
          }
          outhold.soma_for_output.push_back(m_soma);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.soma_for_output[0][0], MAX_SOI_LAY, month_start_idx, months_to_output);
            outhold.soma_for_output.clear();
          }
        }
        else if(curr_spec.yearly){
          std::array<double, MAX_SOI_LAY> y_soma;
          for(int i = 0; i < MAX_SOI_LAY; i++) {
            y_soma[i] = cohort.bdall->y_sois.soma[i];
          }
          outhold.soma_for_output.push_back(y_soma);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.soma_for_output[0][0], MAX_SOI_LAY, year_start_idx, years_to_output);
            outhold.soma_for_output.clear();
          }
        }
      }
      //Total, instead of by layer
      else if(!curr_spec.layer){
        //monthly
        if(curr_spec.monthly){
          outhold.soma_tot_for_output.push_back(cohort.bdall->m_soid.somasum);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.soma_tot_for_output[0], 1, month_start_idx, months_to_output);
            outhold.soma_tot_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.soma_tot_for_output.push_back(cohort.bdall->y_soid.somasum);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.soma_tot_for_output[0], 1, year_start_idx, years_to_output);
            outhold.soma_tot_for_output.clear();
          }
        }
      }
    }//end critical(outputSOMA)
  }//end SOMA
  map_itr = netcdf_outputs.end();


  // SOMCR - soil organic matter, chemically resistant
  map_itr = netcdf_outputs.find("SOMCR");
  if (map_itr != netcdf_outputs.end()) {
    BOOST_LOG_SEV(glg, debug) << "NetCDF output: SOMCR";
    curr_spec = map_itr->second;

    #pragma omp critical(outputSOMCR)
    {
      // By layer
      if(curr_spec.layer){

        // Monthly
        if (curr_spec.monthly) {
          std::array<double, MAX_SOI_LAY> m_somcr;
          for (int i = 0; i < MAX_SOI_LAY; i++) {
            m_somcr[i] = cohort.bdall->m_sois.somcr[i];
          }
          outhold.somcr_for_output.push_back(m_somcr);

          if (output_this_timestep) {
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.somcr_for_output[0][0], MAX_SOI_LAY, month_start_idx, months_to_output);
            outhold.somcr_for_output.clear();
          }
        }
        // Yearly
        else if (curr_spec.yearly) {
          std::array<double, MAX_SOI_LAY> y_somcr;
          for (int i = 0; i < MAX_SOI_LAY; i++) {
            y_somcr[i] = cohort.bdall->y_sois.somcr[i];
          }
          outhold.somcr_for_output.push_back(y_somcr);

          if (output_this_timestep) {
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.somcr_for_output[0][0], MAX_SOI_LAY, year_start_idx, years_to_output);
            outhold.somcr_for_output.clear();
          }
        }
      }
      // Total, instead of by layer
      else if(!curr_spec.layer){

        // Monthly
        if (curr_spec.monthly) {
          outhold.somcr_tot_for_output.push_back(cohort.bdall->m_soid.somcrsum);

          if (output_this_timestep) {
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.somcr_tot_for_output[0], 1, month_start_idx, months_to_output);
            outhold.somcr_tot_for_output.clear();
          }
        }
        // Yearly
        else if (curr_spec.yearly) {
          outhold.somcr_tot_for_output.push_back(cohort.bdall->y_soid.somcrsum);

          if (output_this_timestep) {
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.somcr_tot_for_output[0], 1, year_start_idx, years_to_output);
            outhold.somcr_tot_for_output.clear();
          }
        }
      }
    } //end critical(outputSOMCR)
  } //end SOMCR
  map_itr = netcdf_outputs.end();


  // SOMPR - soil organic matter, physically resistant
  map_itr = netcdf_outputs.find("SOMPR");
  if (map_itr != netcdf_outputs.end()) {
    BOOST_LOG_SEV(glg, debug) << "NetCDF output: SOMPR";
    curr_spec = map_itr->second;

    #pragma omp critical(outputSOMPR)
    {
      // By layer
      if (curr_spec.layer) {
        // Monthly
        if (curr_spec.monthly) {
          std::array<double, MAX_SOI_LAY> m_sompr;
          for (int i = 0; i < MAX_SOI_LAY; i++) {
            m_sompr[i] = cohort.bdall->m_sois.sompr[i];
          }
          outhold.sompr_for_output.push_back(m_sompr);

          if (output_this_timestep) {
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.sompr_for_output[0][0], MAX_SOI_LAY, month_start_idx, months_to_output);
            outhold.sompr_for_output.clear();
          }
        }
        // Yearly
        else if (curr_spec.yearly) {
          std::array<double, MAX_SOI_LAY> y_sompr;
          for (int i = 0; i < MAX_SOI_LAY; i++) {
            y_sompr[i] = cohort.bdall->y_sois.sompr[i];
          }
          outhold.sompr_for_output.push_back(y_sompr);

          if (output_this_timestep) {
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.sompr_for_output[0][0], MAX_SOI_LAY, year_start_idx, years_to_output);
            outhold.sompr_for_output.clear();
          }
        }
      }
      // Total, instead of by layer
      else if (!curr_spec.layer) {
        // Monthly
        if (curr_spec.monthly) {
          outhold.sompr_tot_for_output.push_back(cohort.bdall->m_soid.somprsum);

          if (output_this_timestep) {
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.sompr_tot_for_output[0], 1, month_start_idx, months_to_output);
            outhold.sompr_tot_for_output.clear();
          }
        }
        // Yearly
        else if (curr_spec.yearly) {
          outhold.sompr_tot_for_output.push_back(cohort.bdall->y_soid.somprsum);

          if (output_this_timestep) {
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.sompr_tot_for_output[0], 1, year_start_idx, years_to_output);
            outhold.sompr_tot_for_output.clear();
          }
        }
      }
    } //end critical(outputSOMPR)
  } //end SOMPR
  map_itr = netcdf_outputs.end();


  // SOMRAWC - soil organic matter, raw carbon
  map_itr = netcdf_outputs.find("SOMRAWC");
  if (map_itr != netcdf_outputs.end()) {
    BOOST_LOG_SEV(glg, debug) << "NetCDF output: SOMRAWC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputSOMRAWC)
    {
      // By layer
      if (curr_spec.layer) {
        // Monthly
        if (curr_spec.monthly) {
          std::array<double, MAX_SOI_LAY> m_somrawc;
          for (int i = 0; i < MAX_SOI_LAY; i++) {
            m_somrawc[i] = cohort.bdall->m_sois.rawc[i];
          }
          outhold.somrawc_for_output.push_back(m_somrawc);

          if (output_this_timestep) {
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.somrawc_for_output[0][0], MAX_SOI_LAY, month_start_idx, months_to_output);
            outhold.somrawc_for_output.clear();
          }
        }
        // Yearly
        else if (curr_spec.yearly) {
          std::array<double, MAX_SOI_LAY> y_somrawc;
          for (int i = 0; i < MAX_SOI_LAY; i++) {
            y_somrawc[i] = cohort.bdall->y_sois.rawc[i];
          }
          outhold.somrawc_for_output.push_back(y_somrawc);

          if (output_this_timestep) {
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.somrawc_for_output[0][0], MAX_SOI_LAY, year_start_idx, years_to_output);
            outhold.somrawc_for_output.clear();
          }
        }
      }
      // Total, instead of by layer
      else if (!curr_spec.layer) {
        // Monthly
        if (curr_spec.monthly) {
          outhold.somrawc_tot_for_output.push_back(cohort.bdall->m_soid.rawcsum);

          if (output_this_timestep) {
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.somrawc_tot_for_output[0], 1, month_start_idx, months_to_output);
            outhold.somrawc_tot_for_output.clear();
          }
        }
        // Yearly
        else if (curr_spec.yearly) {
          outhold.somrawc_tot_for_output.push_back(cohort.bdall->y_soid.rawcsum);

          if (output_this_timestep) {
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.somrawc_tot_for_output[0], 1, year_start_idx, years_to_output);
            outhold.somrawc_tot_for_output.clear();
          }
        }
      }
    } //end critical(outputSOMRAWC)
  } //end SOMRAWC
  map_itr = netcdf_outputs.end();


  //Snow water equivalent - a snapshot of the time when output is called
  map_itr = netcdf_outputs.find("SWE");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: SWE";
    curr_spec = map_itr->second;

    #pragma omp critical(outputSWE)
    {
      //daily
      if(curr_spec.daily){
        for(int id=0; id<DINM[month]; id++){
          outhold.swe_for_output.push_back(cohort.edall->daily_swesum[id]);
        }

        if(end_of_year){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.swe_for_output[0], 1, day_timestep, DINY);
          outhold.swe_for_output.clear();
        }
      }
      //monthly
      else if(curr_spec.monthly){
        outhold.swe_for_output.push_back(cohort.edall->m_snws.swesum);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.swe_for_output[0], 1, month_start_idx, months_to_output);
          outhold.swe_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        outhold.swe_for_output.push_back(cohort.edall->y_snws.swesum);

        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.swe_for_output[0], 1, year_start_idx, years_to_output);
          outhold.swe_for_output.clear();
        }
      }
    }//end critical(outputSWE)
  }//end SWE
  map_itr = netcdf_outputs.end();


  //TCDEEP
  map_itr = netcdf_outputs.find("TCDEEP");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TCDEEP";
    curr_spec = map_itr->second;

    #pragma omp critical(outputTCDEEP)
    {
      //daily
      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_tcdeep[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.tcdeep, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.tcdeep, 1, year, 1);
      }
    }//end critical(outputTCDEEP)
  }//end TCDEEP
  map_itr = netcdf_outputs.end();


  //TCLAYER
  map_itr = netcdf_outputs.find("TCLAYER");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TCLAYER";
    curr_spec = map_itr->second;

    #pragma omp critical(outputTCLAYER)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.tcond[0], MAX_SOI_LAY, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.tcond[0], MAX_SOI_LAY, year, 1);
      }
    }//end critical(outputTCLAYER)
  }//end TCLAYER
  map_itr = netcdf_outputs.end();


  //TCMINEA
  map_itr = netcdf_outputs.find("TCMINEA");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TCMINEA";
    curr_spec = map_itr->second;

    #pragma omp critical(outputTCMINEA)
    {
      //daily
      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_tcminea[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.tcminea, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.tcminea, 1, year, 1);
      }
    }//end critical(outputTCMINEA)
  }//end TCMINEA
  map_itr = netcdf_outputs.end();


  //TCMINEB
  map_itr = netcdf_outputs.find("TCMINEB");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TCMINEB";
    curr_spec = map_itr->second;

    #pragma omp critical(outputTCMINEB)
    {
      //daily
      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_tcmineb[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.tcmineb, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.tcmineb, 1, year, 1);
      }
    }//end critical(outputTCMINEB)
  }//end TCMINEB
  map_itr = netcdf_outputs.end();


  //TCMINEC
  map_itr = netcdf_outputs.find("TCMINEC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TCMINEC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputTCMINEC)
    {
      //daily
      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_tcminec[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.tcminec, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.tcminec, 1, year, 1);
      }
    }//end critical(outputTCMINEC)
  }//end TCMINEC
  map_itr = netcdf_outputs.end();


  //TCSHLW
  map_itr = netcdf_outputs.find("TCSHLW");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TCSHLW";
    curr_spec = map_itr->second;

    #pragma omp critical(outputTCSHLW)
    {
      //daily
      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_tcshlw[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.tcshlw, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.tcshlw, 1, year, 1);
      }
    }//end critical(outputTCSHLW)
  }//end TCSHLW
  map_itr = netcdf_outputs.end();


  //TDEEP
  map_itr = netcdf_outputs.find("TDEEP");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TDEEP";
    curr_spec = map_itr->second;

    #pragma omp critical(outputTDEEP)
    {
      //daily
      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_tdeep[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.tdeep, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.tdeep, 1, year, 1);
      }
    }//end critical(outputTDEEP)
  }//end TDEEP
  map_itr = netcdf_outputs.end();


  //TLAYER
  map_itr = netcdf_outputs.find("TLAYER");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TLAYER";
    curr_spec = map_itr->second;

    #pragma omp critical(outputTLAYER)
    {
      std::array<double, MAX_SOI_LAY> tlayer_arr{};

      //daily
      if(curr_spec.daily){
        for(int id=0; id<DINM[month]; id++){
          for(int il=0; il<MAX_SOI_LAY; il++){
            tlayer_arr[il] = cohort.edall->daily_tlayer[id][il];
          }
          outhold.tlayer_for_output.push_back(tlayer_arr);
        }
        if(end_of_year){
          output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.tlayer_for_output[0], MAX_SOI_LAY, day_timestep, DINY);
          outhold.tlayer_for_output.clear();
        }
      }

      //monthly
      else if(curr_spec.monthly){
        for(int il=0; il<MAX_SOI_LAY; il++){
          tlayer_arr[il] = cohort.edall->m_sois.ts[il];
        }
        outhold.tlayer_for_output.push_back(tlayer_arr);

        if(output_this_timestep){
          output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.tlayer_for_output[0], MAX_SOI_LAY, month_start_idx, months_to_output);
          outhold.tlayer_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        for(int il=0; il<MAX_SOI_LAY; il++){
          tlayer_arr[il] = cohort.edall->y_sois.ts[il];
        }
        outhold.tlayer_for_output.push_back(tlayer_arr);

        if(output_this_timestep){
          output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.tlayer_for_output[0], MAX_SOI_LAY, year_start_idx, years_to_output);
          outhold.tlayer_for_output.clear();
        }
      }
    }//end critical(outputTLAYER)
  }//end TLAYER
  map_itr = netcdf_outputs.end();


  //TMINEA
  map_itr = netcdf_outputs.find("TMINEA");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TMINEA";
    curr_spec = map_itr->second;

    #pragma omp critical(outputTMINEA)
    {
      //daily
      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_tminea[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.tminea, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.tminea, 1, year, 1);
      }
    }//end critical(outputTMINEA)
  }//end TMINEA
  map_itr = netcdf_outputs.end();


  //TMINEB
  map_itr = netcdf_outputs.find("TMINEB");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TMINEB";
    curr_spec = map_itr->second;

    #pragma omp critical(outputTMINEB)
    {
      //daily
      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_tmineb[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.tmineb, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.tmineb, 1, year, 1);
      }
    }//end critical(outputTMINEB)
  }//end TMINEB
  map_itr = netcdf_outputs.end();


  //TMINEC
  map_itr = netcdf_outputs.find("TMINEC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TMINEC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputTMINEC)
    {
      //daily
      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_tminec[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.tminec, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.tminec, 1, year, 1);
      }
    }//end critical(outputTMINEC)
  }//end TMINEC
  map_itr = netcdf_outputs.end();


  //TRANSPIRATION
  map_itr = netcdf_outputs.find("TRANSPIRATION");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TRANSPIRATION";
    curr_spec = map_itr->second;

    #pragma omp critical(outputTRANSPIRATION)
    {
      //By PFT
      if(curr_spec.pft){
        std::array<double, NUM_PFT> d_trans_arr{};
        std::array<double, NUM_PFT> m_trans_arr{};
        std::array<double, NUM_PFT> y_trans_arr{};

        for(int ip=0; ip<NUM_PFT; ip++){
          d_trans_arr[ip] = cohort.ed[ip].d_v2a.tran;
          m_trans_arr[ip] = cohort.ed[ip].m_v2a.tran;
          y_trans_arr[ip] = cohort.ed[ip].y_v2a.tran;
        }

        //daily
        if(curr_spec.daily){
          //TODO - this is unusual in that the daily values are not collected somewhere to be output all at once. This will just give a single value.
          outhold.trans_for_output.push_back(d_trans_arr);

          if(end_of_year){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.trans_for_output[0], NUM_PFT, day_timestep, 1);
            outhold.trans_for_output.clear();
          }
        }
        //monthly
        else if(curr_spec.monthly){
          outhold.trans_for_output.push_back(m_trans_arr);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.trans_for_output[0], NUM_PFT, month_start_idx, months_to_output);
            outhold.trans_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.trans_for_output.push_back(y_trans_arr);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.trans_for_output[0], NUM_PFT, year_start_idx, years_to_output);
            outhold.trans_for_output.clear();
          }
        }

      }
      //Total
      else{ 
        if(curr_spec.daily){
          //TODO - as above, this is a single daily value for the whole month
          outhold.trans_tot_for_output.push_back(cohort.edall->d_v2a.tran);

          if(end_of_year){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.trans_tot_for_output[0], 1, day_timestep, 1);
            outhold.trans_tot_for_output.clear();
          }
        }
        else if(curr_spec.monthly){
          outhold.trans_tot_for_output.push_back(cohort.edall->m_v2a.tran);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.trans_tot_for_output[0], 1, month_start_idx, months_to_output);
            outhold.trans_tot_for_output.clear();
          }
        }
        else if(curr_spec.yearly){
          outhold.trans_tot_for_output.push_back(cohort.edall->y_v2a.tran);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.trans_tot_for_output[0], 1, year_start_idx, years_to_output);
            outhold.trans_tot_for_output.clear();
          }
        }
      }
    }//end critical(outputTRANSPIRATION)
  }//end TRANSPIRATION
  map_itr = netcdf_outputs.end();


  //TSHLW
  map_itr = netcdf_outputs.find("TSHLW");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TSHLW";
    curr_spec = map_itr->second;

    #pragma omp critical(outputTSHLW)
    {
      //daily
      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_tshlw[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.tshlw, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.tshlw, 1, year, 1);
      }
    }//end critical(outputTSHLW)
  }//end TSHLW
  map_itr = netcdf_outputs.end();


  //VEGC
  map_itr = netcdf_outputs.find("VEGC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: VEGC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputVEGC)
    {
      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){
        std::array<std::array<double, NUM_PFT>, NUM_PFT_PART> m_vegc{};
        std::array<std::array<double, NUM_PFT>, NUM_PFT_PART> y_vegc{};

        for(int ip=0; ip<NUM_PFT; ip++){
          if(cohort.cd.m_veg.vegcov[ip]>0.){//only check PFTs that exist

            for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
                m_vegc[ipp][ip] = cohort.bd[ip].m_vegs.c[ipp];
                y_vegc[ipp][ip] = cohort.bd[ip].y_vegs.c[ipp];
            }
          }
        }
        //monthly
        if(curr_spec.monthly){
          outhold.vegc_for_output.push_back(m_vegc);

          if(output_this_timestep){
            output_nc_5dim(&curr_spec, file_stage_suffix, &outhold.vegc_for_output[0][0], NUM_PFT_PART, NUM_PFT, month_start_idx, months_to_output);
            outhold.vegc_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.vegc_for_output.push_back(y_vegc);

          if(output_this_timestep){
            output_nc_5dim(&curr_spec, file_stage_suffix, &outhold.vegc_for_output[0][0], NUM_PFT_PART, NUM_PFT, year_start_idx, years_to_output);
            outhold.vegc_for_output.clear();
          }
        }
      }
      //PFT only
      else if(curr_spec.pft && !curr_spec.compartment){
        std::array<double, NUM_PFT> m_vegc{};
        std::array<double, NUM_PFT> y_vegc{};

        for(int ip=0; ip<NUM_PFT; ip++){
          if(cohort.cd.m_veg.vegcov[ip]>0.){//only check PFTs that exist
            m_vegc[ip] = cohort.bd[ip].m_vegs.call;
            y_vegc[ip] = cohort.bd[ip].y_vegs.call;
          }
        }
        //monthly
        if(curr_spec.monthly){
          outhold.vegc_pft_for_output.push_back(m_vegc);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.vegc_pft_for_output[0], NUM_PFT, month_start_idx, months_to_output);
            outhold.vegc_pft_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.vegc_pft_for_output.push_back(y_vegc);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.vegc_pft_for_output[0], NUM_PFT, year_start_idx, years_to_output);
            outhold.vegc_pft_for_output.clear();
          }
        }
      }
      //Compartment only
      else if(!curr_spec.pft && curr_spec.compartment){
        std::array<double, NUM_PFT_PART> m_vegc{};
        std::array<double, NUM_PFT_PART> y_vegc{};

        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){
            if(cohort.cd.m_veg.vegcov[ip]>0.){//only check PFTs that exist
              m_vegc[ipp] += cohort.bd[ip].m_vegs.c[ipp];
              y_vegc[ipp] += cohort.bd[ip].y_vegs.c[ipp];
            }
          }
        }
        //monthly
        if(curr_spec.monthly){
          outhold.vegc_part_for_output.push_back(m_vegc);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.vegc_part_for_output[0], NUM_PFT_PART, month_start_idx, months_to_output);
            outhold.vegc_part_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.vegc_part_for_output.push_back(y_vegc);

          if(output_this_timestep){
            output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.vegc_part_for_output[0], NUM_PFT_PART, year_start_idx, years_to_output);
            outhold.vegc_part_for_output.clear();
          }
        }
      }
      //Neither PFT nor compartment
      else if(!curr_spec.pft && !curr_spec.compartment){
        //monthly
        if(curr_spec.monthly){
          outhold.vegc_tot_for_output.push_back(cohort.bdall->m_vegs.call);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.vegc_tot_for_output[0], 1, month_start_idx, months_to_output);
            outhold.vegc_tot_for_output.clear();
          }
        }
        //yearly
        else if(curr_spec.yearly){
          outhold.vegc_tot_for_output.push_back(cohort.bdall->y_vegs.call);

          if(output_this_timestep){
            output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.vegc_tot_for_output[0], 1, year_start_idx, years_to_output);
            outhold.vegc_tot_for_output.clear();
          }
        }
      }
    }//end critical(outputVEGC)
  }//end VEGC
  map_itr = netcdf_outputs.end();


  //VEGN
  map_itr = netcdf_outputs.find("VEGNTOT");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: VEGNTOT";
    curr_spec = map_itr->second;

    #pragma omp critical(outputVEGNTOT)
    {
      //Neither PFT nor compartment (total ecosystem)
      if(!curr_spec.pft && !curr_spec.compartment){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_vegs.nall, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_vegs.nall, 1, year, 1);
        }
      }
    }//end critical(outputVEGNTOT)
  }//end VEGN
  map_itr = netcdf_outputs.end();


  //VEGNLAB
  map_itr = netcdf_outputs.find("VEGNLAB");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: VEGNLAB";
    curr_spec = map_itr->second;

    #pragma omp critical(outputVEGNLAB)
    {
      //Neither PFT nor compartment (total ecosystem)
      if(!curr_spec.pft && !curr_spec.compartment){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_vegs.labn, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_vegs.labn, 1, year, 1);
        }
      }
    }//end critical(outputVEGNLAB)
  }//end VEGNLAB
  map_itr = netcdf_outputs.end();


  //VEGNSTR
  map_itr = netcdf_outputs.find("VEGNSTR");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: VEGNSTR";
    curr_spec = map_itr->second;

    #pragma omp critical(outputVEGNSTR)
    {
      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){
        double m_vegn[NUM_PFT_PART][NUM_PFT] = {0};
        double y_vegn[NUM_PFT_PART][NUM_PFT] = {0};
        for(int ip=0; ip<NUM_PFT; ip++){
          if(cohort.cd.m_veg.vegcov[ip]>0.){//only check PFTs that exist

            for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
                m_vegn[ipp][ip] = cohort.bd[ip].m_vegs.strn[ipp];
                y_vegn[ipp][ip] = cohort.bd[ip].y_vegs.strn[ipp];
            }
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &m_vegn[0][0], NUM_PFT_PART, NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &y_vegn[0][0], NUM_PFT_PART, NUM_PFT, year, 1);
        }
      }
      //PFT only
      else if(curr_spec.pft && !curr_spec.compartment){

        double m_vegn[NUM_PFT] = {0};
        double y_vegn[NUM_PFT] = {0};
        for(int ip=0; ip<NUM_PFT; ip++){
          if(cohort.cd.m_veg.vegcov[ip]>0.){//only check PFTs that exist
            m_vegn[ip] = cohort.bd[ip].m_vegs.strnall;
            y_vegn[ip] = cohort.bd[ip].y_vegs.strnall;
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_vegn[0], NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_vegn[0], NUM_PFT, year, 1);
        }
      }
      //Compartment only
      else if(!curr_spec.pft && curr_spec.compartment){

        double m_vegn[NUM_PFT_PART] = {0};
        double y_vegn[NUM_PFT_PART] = {0};
        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){
            if(cohort.cd.m_veg.vegcov[ip]>0.){//only check PFTs that exist
              m_vegn[ipp] += cohort.bd[ip].m_vegs.strn[ipp];
              y_vegn[ipp] += cohort.bd[ip].y_vegs.strn[ipp];
            }
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_vegn[0], NUM_PFT_PART, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_vegn[0], NUM_PFT_PART, year, 1);
        }
      }
      //Neither PFT nor compartment
      else if(!curr_spec.pft && !curr_spec.compartment){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_vegs.strnall, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_vegs.strnall, 1, year, 1);
        }
      }
    }//end critical(outputVEGNSTR)
  }//end VEGNSTR
  map_itr = netcdf_outputs.end();


  //VWCDEEP
  map_itr = netcdf_outputs.find("VWCDEEP");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: VWCDEEP";
    curr_spec = map_itr->second;

    #pragma omp critical(outputVWCDEEP)
    {
      //daily
      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_vwcdeep[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.vwcdeep, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.vwcdeep, 1, year, 1);
      }
    }//end critical(outputVWCDEEP)
  }//end VWCDEEP
  map_itr = netcdf_outputs.end();


  //VWCLAYER
  map_itr = netcdf_outputs.find("VWCLAYER");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: VWCLAYER";
    curr_spec = map_itr->second;
    #pragma omp critical(outputVWCLAYER)
    {
      std::array<double, MAX_SOI_LAY> vwclayer_arr{};

      if(curr_spec.monthly){
        for(int il=0; il<MAX_SOI_LAY; il++){
          vwclayer_arr[il] = cohort.edall->m_soid.vwc[il];
        }
        outhold.vwclayer_for_output.push_back(vwclayer_arr);

        if(output_this_timestep){
          output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.vwclayer_for_output[0], MAX_SOI_LAY, month_start_idx, months_to_output);
          outhold.vwclayer_for_output.clear();
        }
      }
      else if(curr_spec.yearly){
        for(int il=0; il<MAX_SOI_LAY; il++){
          vwclayer_arr[il] = cohort.edall->y_soid.vwc[il];
        }
        outhold.vwclayer_for_output.push_back(vwclayer_arr);

        if(output_this_timestep){
          output_nc_4dim(&curr_spec, file_stage_suffix, &outhold.vwclayer_for_output[0], MAX_SOI_LAY, year_start_idx, years_to_output);
          outhold.vwclayer_for_output.clear();
        }
      }
    }//end critical(outputVWCLAYER)
  }//end VWCLAYER
  map_itr = netcdf_outputs.end();


  //VWCMINEA
  map_itr = netcdf_outputs.find("VWCMINEA");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: VWCMINEA";
    curr_spec = map_itr->second;

    #pragma omp critical(outputVWCMINEA)
    {
      //daily
      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_vwcminea[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.vwcminea, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.vwcminea, 1, year, 1);
      }
    }//end critical(outputVWCMINEA)
  }//end VWCMINEA
  map_itr = netcdf_outputs.end();


  //VWCMINEB
  map_itr = netcdf_outputs.find("VWCMINEB");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: VWCMINEB";
    curr_spec = map_itr->second;

    #pragma omp critical(outputVWCMINEB)
    {
      //daily
      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_vwcmineb[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.vwcmineb, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.vwcmineb, 1, year, 1);
      }
    }//end critical(outputVWCMINEB)
  }//end VWCMINEB
  map_itr = netcdf_outputs.end();


  //VWCMINEC
  map_itr = netcdf_outputs.find("VWCMINEC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: VWCMINEC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputVWCMINEC)
    {
      //daily
      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_vwcminec[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.vwcminec, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.vwcminec, 1, year, 1);
      }
    }//end critical(outputVWCMINEC)
  }//end VWCMINEC
  map_itr = netcdf_outputs.end();


  //VWCSHLW
  map_itr = netcdf_outputs.find("VWCSHLW");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: VWCSHLW";
    curr_spec = map_itr->second;

    #pragma omp critical(outputVWCSHLW)
    {
      //daily
      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_vwcshlw[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.vwcshlw, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.vwcshlw, 1, year, 1);
      }
    }//end critical(outputVWCSHLW)
  }//end VWCSHLW
  map_itr = netcdf_outputs.end();


  //WATERTAB
  map_itr = netcdf_outputs.find("WATERTAB");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: WATERTAB";
    curr_spec = map_itr->second;

    #pragma omp critical(outputWATERTAB)
    {
      //daily
      if(curr_spec.daily){
        for(int id=0; id<DINM[month]; id++){
          outhold.watertab_for_output.push_back(cohort.edall->daily_watertab[id]);
        }

        if(end_of_year){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.watertab_for_output[0], 1, day_timestep, DINY);
          outhold.watertab_for_output.clear();
        }
      }
      //monthly
      else if(curr_spec.monthly){
        outhold.watertab_for_output.push_back(cohort.edall->m_sois.watertab);
        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.watertab_for_output[0], 1, month_start_idx, months_to_output);
          outhold.watertab_for_output.clear();
        }
      }
      //yearly
      else if(curr_spec.yearly){
        outhold.watertab_for_output.push_back(cohort.edall->y_sois.watertab);
        if(output_this_timestep){
          output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.watertab_for_output[0], 1, year_start_idx, years_to_output);
          outhold.watertab_for_output.clear();
        }
      }
    }//end critical(outputWATERTAB)
  }//end WATERTAB
  map_itr = netcdf_outputs.end();


  //Years since disturbance
  map_itr = netcdf_outputs.find("YSD");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: YSD";
    curr_spec = map_itr->second;

    #pragma omp critical(outputYSD)
    {
      outhold.ysd_for_output.push_back(cohort.cd.yrsdist);

      if(output_this_timestep){
        output_nc_3dim(&curr_spec, file_stage_suffix, &outhold.ysd_for_output[0], 1, year_start_idx, years_to_output);
        outhold.ysd_for_output.clear();
      }
    }//end critical(outputYSD)
  }//end YSD
  map_itr = netcdf_outputs.end();

}


