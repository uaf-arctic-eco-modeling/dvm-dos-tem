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
    BOOST_LOG_SEV(glg, err) << "y: "<<this->y<<" x: "<<this->x<<" Year: "<<iy;

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
    output_netCDF_monthly(year, month, runstage);
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
    output_netCDF_yearly(year, stage);
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
    BOOST_LOG_SEV(glg, err) << "========== MONTHLY CHECKSUM ERRORS ============";
    while (!compartment_err_report.empty()) {
      BOOST_LOG_SEV(glg, err) << compartment_err_report.front();
      compartment_err_report.pop_front();
    }
    while ( !(pft_err_report.empty()) ){
      BOOST_LOG_SEV(glg, err) << pft_err_report.front();
      pft_err_report.pop_front();
    }
    BOOST_LOG_SEV(glg, err) << "========== END MONTHLY CHECKSUMMING month: " << month << " year: " << year << " ============";
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
  double litterfallCsum = 0;
  double litterfallNsum = 0;
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
    BOOST_LOG_SEV(glg, err) << "========== YEARLY CHECKSUM ERRORS ============";
    while (!compartment_err_report.empty()) {
      BOOST_LOG_SEV(glg, err) << compartment_err_report.front();
      compartment_err_report.pop_front();
    }
    while ( !(pft_err_report.empty()) ){
      BOOST_LOG_SEV(glg, err) << pft_err_report.front();
      pft_err_report.pop_front();
    }
    BOOST_LOG_SEV(glg, err) << "========== END YEARLY CHECKSUMMING year: " << year << " ============";
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

  //Calculated sums
  double litterfallCsum = 0;
  double litterfallNsum = 0;

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


void Runner::output_netCDF_monthly(int year, int month, std::string stage){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF monthly output, year: "<<year<<" month: "<<month;
    output_netCDF(md.monthly_netcdf_outputs, year, month, stage);

    BOOST_LOG_SEV(glg, debug)<<"Outputting accumulated daily data on the monthly timestep";
    output_netCDF(md.daily_netcdf_outputs, year, month, stage);
}

void Runner::output_netCDF_yearly(int year, std::string stage){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF yearly output, year: "<<year;
    output_netCDF(md.yearly_netcdf_outputs, year, 0, stage);
}

//The following two functions are the beginning of an attempt to
// generalize the output of different variables. The end goal is
// for the output_netCDF() function to be shorter, more readable,
// and have fewer redundant pieces of code.
//20181006 Currently there are only a few variables using these
// general functions, but since they include the front outputs
// we are merging this despite it being incomplete.
void Runner::output_nc_soil_layer(int ncid, int cv, int *data, int max_var_count, int start_timestep, int timesteps){

  //timestep, layer, row, col
  size_t soilstart[4];
  soilstart[0] = start_timestep;
  soilstart[1] = 0;
  soilstart[2] = this->y;
  soilstart[3] = this->x;

  size_t soilcount[4];
  //soilcount[0] = 1;
  soilcount[0] = timesteps;
  soilcount[1] = max_var_count;
  soilcount[2] = 1;
  soilcount[3] = 1;

  temutil::nc( nc_put_vara_int(ncid, cv, soilstart, soilcount, data) );
}

void Runner::output_nc_soil_layer(int ncid, int cv, double *data, int max_var_count, int start_timestep, int timesteps){

  //timestep, layer, row, col
  size_t soilstart[4];
  soilstart[0] = start_timestep;
  soilstart[1] = 0;
  soilstart[2] = this->y;
  soilstart[3] = this->x;

  size_t soilcount[4];
  //soilcount[0] = 1;
  soilcount[0] = timesteps;
  soilcount[1] = max_var_count;
  soilcount[2] = 1;
  soilcount[3] = 1;

  temutil::nc( nc_put_vara_double(ncid, cv, soilstart, soilcount, data) );
}


void Runner::output_netCDF(std::map<std::string, OutputSpec> &netcdf_outputs, int year, int month, std::string stage){
  int month_timestep = year*12 + month;

  int day_timestep = year*365;
  for(int im=0; im<month; im++){
    day_timestep += DINM[im];
  }

  //For outputting subsets of driving data arrays
  int doy = temutil::day_of_year(month, 0); 

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
  int ncid;
  int timeD; //unlimited dimension
  int xD;
  int yD;
  int pftD;
  int pftpartD;
  int layerD;
  int cv; //reusable variable handle

  std::map<std::string, OutputSpec>::iterator map_itr;

  /*** 3D variables ***/
  size_t start3[3];
  //Index 0 is set later
  start3[1] = rowidx;
  start3[2] = colidx;

  //For daily-level variables
  size_t count3[3];
  count3[0] = dinm;
  count3[1] = 1;
  count3[2] = 1;

  /*** Soil Variables ***/
  size_t soilstart4[4];
  //Index 0 is set later
  soilstart4[1] = 0;
  soilstart4[2] = rowidx;
  soilstart4[3] = colidx;

  size_t soilcount4[4];
  soilcount4[0] = 1;
  soilcount4[1] = MAX_SOI_LAY;
  soilcount4[2] = 1;
  soilcount4[3] = 1;

  /*** Fronts ***/
  size_t frontcount4[4];
  frontcount4[0] = 1; 
  frontcount4[1] = MAX_NUM_FNT;
  frontcount4[2] = 1;
  frontcount4[3] = 1;

  size_t frontstart5[5];
  //Index 0 is set later
  frontstart5[1] = 0;
  frontstart5[2] = 0;
  frontstart5[3] = rowidx;
  frontstart5[4] = colidx;

  size_t frontcount5[5];
  frontcount5[0] = 1;
  frontcount5[1] = dinm;
  frontcount5[2] = MAX_NUM_FNT;
  frontcount5[3] = 1;
  frontcount5[4] = 1;

  /*** PFT variables ***/
  size_t PFTstart4[4];
  //Index 0 is set later
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
  //Index 0 is set later
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
  //Index 0 is set later
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
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: ALD";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputALD)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "ALD", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "ALD", &cv) );
#endif
      start3[0] = year;

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &cohort.edall->y_soid.ald) );
      temutil::nc( nc_close(ncid) );
    }//end critical(outputALD)
  }//end ALD
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("DEEPDZ");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: DEEPDZ";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputDEEPDZ)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "DEEPDZ", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "DEEPDZ", &cv) );
#endif
      start3[0] = year;

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
    }//end critical(outputDEEPDZ)
  }//end DEEPDZ
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("GROWEND");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: GROWEND";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputGROWEND)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "GROWEND", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "GROWEND", &cv) );
#endif
      start3[0] = year;

      double growend = cohort.edall->y_soid.rtdpGEoutput;

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &growend) );
      temutil::nc( nc_close(ncid) );
    }//end critical(outputGROWEND)
  }//end GROWEND
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("GROWSTART");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: GROWSTART";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputGROWSTART)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "GROWSTART", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "GROWSTART", &cv) );
#endif
      start3[0] = year;

      double growstart = cohort.edall->y_soid.rtdpGSoutput;

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &growstart) );
      temutil::nc( nc_close(ncid) );
    }//end critical(outputGROWSTART)
  }//end GROWSTART
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("MOSSDZ");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: MOSSDZ";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputMOSSDZ)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "MOSSDZ", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "MOSSDZ", &cv) );
#endif
      start3[0] = year;

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
    }//end critical(outputMOSSDZ)
  }//end MOSSDZ
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("ROLB");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: ROLB";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputROLB)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "ROLB", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "ROLB", &cv) );
#endif

      double rolb;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        rolb = cohort.year_fd[month].fire_soid.rolb;
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        //FIX. This will not work if there is more than one fire per year
        // What does yearly ROLB even mean with multiple fires?
        rolb = cohort.fd->fire_soid.rolb;
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &rolb) );
      temutil::nc( nc_close(ncid) );
    }//end critical(outputROLB)
  }//end ROLB
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("PERMAFROST");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: PERMAFROST";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputPERMAFROST)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "PERMAFROST", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "PERMAFROST", &cv) );
#endif
      start3[0] = year;

      double permafrost = cohort.edall->y_soid.permafrost;

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &permafrost) );
      temutil::nc( nc_close(ncid) );
    }//end critical(outputPERMAFROST)
  }//end PERMAFROST
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("SHLWDZ");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: SHLWDZ";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputSHLWDZ)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "SHLWDZ", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "SHLWDZ", &cv) );
#endif
      start3[0] = year;

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
    }//end critical(outputSHLWDZ)
  }//end SHLWDZ
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("SNOWEND");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: SNOWEND";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputSNOWEND)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "SNOWEND", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "SNOWEND", &cv) );
#endif
      start3[0] = year;

      double snowend = cohort.edall->y_snws.snowend;

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &snowend) );
      temutil::nc( nc_close(ncid) );
    }//end critical(outputSNOWEND)
  }//end SNOWEND
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("SNOWSTART");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: SNOWSTART";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputSNOWSTART)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "SNOWSTART", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "SNOWSTART", &cv) );
#endif
      start3[0] = year;

      double snowstart = cohort.edall->y_snws.snowstart;

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &snowstart) );
      temutil::nc( nc_close(ncid) );
    }//end critical(outputSNOWSTART)
  }//end SNOWSTART
  map_itr = netcdf_outputs.end();


  //Years since disturbance
  map_itr = netcdf_outputs.find("YSD");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: YSD";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputYSD)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "YSD", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "YSD", &cv) );
#endif
      start3[0] = year;

      double ysd = cohort.cd.yrsdist;

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &ysd) );
      temutil::nc( nc_close(ncid) );
    }//end critical(outputYSD)
  }//end YSD
  map_itr = netcdf_outputs.end();


  /*** Two combination vars: (month, year) ***/
  map_itr = netcdf_outputs.find("BURNAIR2SOIN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNAIR2SOIN";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputBURNAIR2SOIN)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNAIR2SOIN", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNAIR2SOIN", &cv) );
#endif

      double burnair2soin;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        burnair2soin = cohort.year_fd[month].fire_a2soi.orgn;
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        burnair2soin = 0;
        for(int im=0; im<12; im++){
          burnair2soin += cohort.year_fd[im].fire_a2soi.orgn;
        }
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &burnair2soin) );
      temutil::nc( nc_close(ncid) );
    }//end critical(outputBURNAIR2SOIN)
  }//end BURNAIR2SOIN
  map_itr = netcdf_outputs.end();


  //Burn thickness
  map_itr = netcdf_outputs.find("BURNTHICK");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNTHICK";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputBURNTHICK)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNTHICK", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNTHICK", &cv) );
#endif

      double burnthick;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        burnthick = cohort.year_fd[month].fire_soid.burnthick;
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        burnthick = 0;
        for(int im=0; im<12; im++){
          burnthick += cohort.year_fd[im].fire_soid.burnthick;
        }
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &burnthick) );
      temutil::nc( nc_close(ncid) );
    }//end critical(outputBURNTHICK)
  }//end BURNTHICK
  map_itr = netcdf_outputs.end();


  //Standing dead C
  map_itr = netcdf_outputs.find("DEADC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: DEADC";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputDEADC)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "DEADC", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "DEADC", &cv) );
#endif

      double deadc;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        deadc = cohort.bdall->m_vegs.deadc;
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        deadc = cohort.bdall->y_vegs.deadc;
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &deadc) );
      temutil::nc( nc_close(ncid) );
    }//end critical(outputDEADC)
  }//end DEADC
  map_itr = netcdf_outputs.end();


  //Standing dead N
  map_itr = netcdf_outputs.find("DEADN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: DEADN";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputDEADN)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "DEADN", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "DEADN", &cv) );
#endif

      double deadn;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        deadn = cohort.bdall->m_vegs.deadn;
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        deadn = cohort.bdall->y_vegs.deadn;
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &deadn) );
      temutil::nc( nc_close(ncid) );
    }//end critical(outputDEADN)
  }//end DEADN
  map_itr = netcdf_outputs.end();


  //Deep C
  map_itr = netcdf_outputs.find("DEEPC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: DEEPC";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputDEEPC)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "DEEPC", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "DEEPC", &cv) );
#endif

      double deepc;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        deepc = cohort.bdall->m_soid.deepc;
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        deepc = cohort.bdall->y_soid.deepc;
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &deepc) );
      temutil::nc( nc_close(ncid) ); 
    }//end critical(outputDEEPC)
  }//end DEEPC
  map_itr = netcdf_outputs.end();


  //Woody debris C
  map_itr = netcdf_outputs.find("DWDC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: DWDC";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputDWDC)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "DWDC", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "DWDC", &cv) );
#endif

      double woodyc;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        woodyc = cohort.bdall->m_sois.wdebrisc;
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        woodyc = cohort.bdall->y_sois.wdebrisc;
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &woodyc) );
      temutil::nc( nc_close(ncid) );
    }//end critical(outputDWDC)
  }//end DWDC
  map_itr = netcdf_outputs.end();


  //Woody debris N
  map_itr = netcdf_outputs.find("DWDN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"DWDN";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputDWDN)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "DWDN", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "DWDN", &cv) );
#endif

      double woodyn;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        woodyn = cohort.bdall->m_sois.wdebrisn;
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        woodyn = cohort.bdall->y_sois.wdebrisn;
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &woodyn) );
      temutil::nc( nc_close(ncid) );
    }//end critical(outputDWDN)
  }//end DWDN
  map_itr = netcdf_outputs.end();


  //Mineral C
  map_itr = netcdf_outputs.find("MINEC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"MINEC";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputMINEC)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "MINEC", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "MINEC", &cv) );
#endif

      double minec;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        minec = cohort.bdall->m_soid.mineac
                + cohort.bdall->m_soid.minebc
                + cohort.bdall->m_soid.minecc;
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        minec = cohort.bdall->y_soid.mineac
                + cohort.bdall->y_soid.minebc
                + cohort.bdall->y_soid.minecc;
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &minec) );
      temutil::nc( nc_close(ncid) ); 
    }//end critical(outputMINEC)
  }//end MINEC
  map_itr = netcdf_outputs.end();


  //MOSSDEATHC
  map_itr = netcdf_outputs.find("MOSSDEATHC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: MOSSDEATHC";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputMOSSDEATHC)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "MOSSDEATHC", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "MOSSDEATHC", &cv) );
#endif

      double mossdeathc = 0;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        mossdeathc = cohort.bdall->m_v2soi.mossdeathc; 
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        mossdeathc = cohort.bdall->y_v2soi.mossdeathc; 
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &mossdeathc) ); 
      temutil::nc( nc_close(ncid) ); 
    }//end critical(outputMOSSDEATHC)
  }//end MOSSDEATHC
  map_itr = netcdf_outputs.end();


  //MOSSDEATHN
  map_itr = netcdf_outputs.find("MOSSDEATHN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: MOSSDEATHN";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputMOSSDEATHN)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "MOSSDEATHN", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "MOSSDEATHN", &cv) );
#endif

      double mossdeathn = 0;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        mossdeathn = cohort.bdall->m_v2soi.mossdeathn; 
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        mossdeathn = cohort.bdall->y_v2soi.mossdeathn; 
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &mossdeathn) ); 
      temutil::nc( nc_close(ncid) ); 
    }//end critical(outputMOSSDEATHN)
  }//end MOSSDEATHN
  map_itr = netcdf_outputs.end();


  //QDRAINAGE
  map_itr = netcdf_outputs.find("QDRAINAGE");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: QDRAINAGE";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputQDRAINAGE)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
#endif
      temutil::nc( nc_inq_varid(ncid, "QDRAINAGE", &cv) );

      double qdrainage = 0;
      if(curr_spec.daily){
        output_nc_soil_layer(ncid, cv, &cohort.edall->daily_qdrain[0], 1, day_timestep, dinm);
      }
      else if(curr_spec.monthly){
        output_nc_soil_layer(ncid, cv, &cohort.edall->m_soi2l.qdrain, 1, month_timestep, 1);
      }
      else if(curr_spec.yearly){
        output_nc_soil_layer(ncid, cv, &cohort.edall->y_soi2l.qdrain, 1, year, 1);
      }
      temutil::nc( nc_close(ncid) ); 
    }//end critical(outputQDRAINAGE)
  }//end QDRAINAGE 
  map_itr = netcdf_outputs.end();


  //QINFILTRATION
  map_itr = netcdf_outputs.find("QINFILTRATION");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: QINFILTRATION";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputQINFILTRATION)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
#endif
      temutil::nc( nc_inq_varid(ncid, "QINFILTRATION", &cv) );

      double qinfil = 0;
      if(curr_spec.daily){
        output_nc_soil_layer(ncid, cv, &cohort.edall->daily_qinfl[0], 1, day_timestep, dinm);
      }
      else if(curr_spec.monthly){
        output_nc_soil_layer(ncid, cv, &cohort.edall->m_soi2l.qinfl, 1, month_timestep, 1);
      }
      else if(curr_spec.yearly){
        output_nc_soil_layer(ncid, cv, &cohort.edall->y_soi2l.qinfl, 1, year, 1);
      }
      temutil::nc( nc_close(ncid) ); 
    }//end critical(outputQINFILTRATION)
  }//end QINFILTRATION
  map_itr = netcdf_outputs.end();


  //QRUNOFF
  map_itr = netcdf_outputs.find("QRUNOFF");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: QRUNOFF";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputQRUNOFF)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
#endif
      temutil::nc( nc_inq_varid(ncid, "QRUNOFF", &cv) );

      double qrunoff = 0;
      if(curr_spec.daily){
        output_nc_soil_layer(ncid, cv, &cohort.edall->daily_qover[0], 1, day_timestep, dinm);
      }
      else if(curr_spec.monthly){
        output_nc_soil_layer(ncid, cv, &cohort.edall->m_soi2l.qover, 1, month_timestep, 1);
      }
      else if(curr_spec.yearly){
        output_nc_soil_layer(ncid, cv, &cohort.edall->y_soi2l.qover, 1, year, 1);
      }
      temutil::nc( nc_close(ncid) ); 
    }//end critical(outputQRUNOFF)
  }//end QRUNOFF 
  map_itr = netcdf_outputs.end();


  //Shallow C
  map_itr = netcdf_outputs.find("SHLWC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"SHLWC";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputSHLWC)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "SHLWC", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "SHLWC", &cv) );
#endif

      double shlwc;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        shlwc = cohort.bdall->m_soid.shlwc;
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        shlwc = cohort.bdall->y_soid.shlwc;
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &shlwc) );
      temutil::nc( nc_close(ncid) ); 
    }//end critical(outputSHLWC)
  }//end SHLWC 
  map_itr = netcdf_outputs.end();


  //Woody debris RH
  map_itr = netcdf_outputs.find("WDRH");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"WDRH";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputWDRH)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "WDRH", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "WDRH", &cv) );
#endif

      double woodyrh;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        woodyrh = cohort.bdall->m_soi2a.rhwdeb;
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        woodyrh = cohort.bdall->y_soi2a.rhwdeb;
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &woodyrh) );
      temutil::nc( nc_close(ncid) ); 
    }//end critical(outputWDRH)
  }//end WDRH
  map_itr = netcdf_outputs.end();


  /*** Three combination vars: (year, month, day) ***/
  //HKDEEP
  map_itr = netcdf_outputs.find("HKDEEP");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: HKDEEP";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputHKDEEP)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "HKDEEP", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "HKDEEP", &cv) );
#endif

      double hkdeep;
      if(curr_spec.daily){
        start3[0] = day_timestep; 
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_hkdeep[0]) );
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        hkdeep = cohort.edall->m_soid.hkdeep;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &hkdeep) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        hkdeep = cohort.edall->y_soid.hkdeep;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &hkdeep) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputHKDEEP)
  }//end HKDEEP 
  map_itr = netcdf_outputs.end();


  //HKLAYER
  map_itr = netcdf_outputs.find("HKLAYER");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: HKLAYER";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputHKLAYER)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "HKLAYER", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "HKLAYER", &cv) );
#endif

      if(curr_spec.monthly){
        soilstart4[0] = month_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, soilstart4, soilcount4, &cohort.edall->m_soid.hcond[0]) );
      }
      else if(curr_spec.yearly){
        soilstart4[0] = year;
        temutil::nc( nc_put_vara_double(ncid, cv, soilstart4, soilcount4, &cohort.edall->y_soid.hcond[0]) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputHKLAYER)

  }//end HKLAYER
  map_itr = netcdf_outputs.end();


  //HKMINEA
  map_itr = netcdf_outputs.find("HKMINEA");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: HKMINEA";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputHKMINEA)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "HKMINEA", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "HKMINEA", &cv) );
#endif

      double hkminea;
      if(curr_spec.daily){
        start3[0] = day_timestep; 
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_hkminea[0]) );
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        hkminea = cohort.edall->m_soid.hkminea;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &hkminea) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        hkminea = cohort.edall->y_soid.hkminea;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &hkminea) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputHKMINEA)
  }//end HKMINEA
  map_itr = netcdf_outputs.end();


  //HKMINEB
  map_itr = netcdf_outputs.find("HKMINEB");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: HKMINEB";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputHKMINEB)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "HKMINEB", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "HKMINEB", &cv) );
#endif

      double hkmineb;
      if(curr_spec.daily){
        start3[0] = day_timestep; 
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_hkmineb[0]) );
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        hkmineb = cohort.edall->m_soid.hkmineb;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &hkmineb) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        hkmineb = cohort.edall->y_soid.hkmineb;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &hkmineb) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputHKMINEB)
  }//end HKMINEB
  map_itr = netcdf_outputs.end();


  //HKMINEC
  map_itr = netcdf_outputs.find("HKMINEC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: HKMINEC";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputHKMINEC)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "HKMINEC", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "HKMINEC", &cv) );
#endif

      double hkminec;
      if(curr_spec.daily){
        start3[0] = day_timestep; 
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_hkminec[0]) );
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        hkminec = cohort.edall->m_soid.hkminec;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &hkminec) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        hkminec = cohort.edall->y_soid.hkminec;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &hkminec) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputHKMINEC)
  }//end HKMINEC
  map_itr = netcdf_outputs.end();


  //HKSHLW
  map_itr = netcdf_outputs.find("HKSHLW");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: HKSHLW";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputHKSHLW)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "HKSHLW", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "HKSHLW", &cv) );
#endif

      double hkshlw;
      if(curr_spec.daily){
        start3[0] = day_timestep; 
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_hkshlw[0]) );
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        hkshlw = cohort.edall->m_soid.hkshlw;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &hkshlw) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        hkshlw = cohort.edall->y_soid.hkshlw;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &hkshlw) );
      }

      temutil::nc( nc_close(ncid) );
    }
  }//end HKSHLW 
  map_itr = netcdf_outputs.end();


  //Snowthick - a snapshot of the time when output is called
  map_itr = netcdf_outputs.find("SNOWTHICK");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: SNOWTHICK";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputSNOWTHICK)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "SNOWTHICK", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "SNOWTHICK", &cv) );
#endif

      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_snowthick[0]) );
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        double snowthick=0.0;
        Layer* currL = cohort.ground.toplayer;
        while(currL->isSnow){
          snowthick += currL->dz;
          currL = currL->nextl;
        }

        temutil::nc( nc_put_var1_double(ncid, cv, start3, &snowthick) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        double snowthick=0.0;
        Layer* currL = cohort.ground.toplayer;
        while(currL->isSnow){
          snowthick += currL->dz;
          currL = currL->nextl;
        }
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &snowthick) );
      }

      temutil::nc( nc_close(ncid) ); 
    }//end critical(outputSNOWTHICK)
  }//end SNOWTHICK
  map_itr = netcdf_outputs.end();


  //SNOWFALL
  map_itr = netcdf_outputs.find("SNOWFALL");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: SNOWFALL";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputSNOWFALL)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "SNOWFALL", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "SNOWFALL", &cv) );
#endif

      if(curr_spec.monthly){
        start3[0] = month_timestep;

        temutil::nc( nc_put_var1_double(ncid, cv, start3, &cohort.edall->m_a2l.snfl) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;

        temutil::nc( nc_put_var1_double(ncid, cv, start3, &cohort.edall->y_a2l.snfl) );
      }

      temutil::nc( nc_close(ncid) ); 
    }//end critical(outputSNOWFALL)
  }//end SNOWFALL
  map_itr = netcdf_outputs.end();


  //DRIVINGSNOWFALL
  map_itr = netcdf_outputs.find("DRIVINGSNOWFALL");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: DRIVINGSNOWFALL";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputDRIVINGSNOWFALL)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
#endif
      temutil::nc( nc_inq_varid(ncid, "DRIVINGSNOWFALL", &cv) );

      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_float(ncid, cv, start3, count3, &cohort.climate.snow_d[doy]) );
      }

      temutil::nc( nc_close(ncid) ); 
    }//end critical(outputDRIVINGSNOWFALL)
  }//end DRIVINGSNOWFALL
  map_itr = netcdf_outputs.end();


  //DRIVINGRAINFALL
  map_itr = netcdf_outputs.find("DRIVINGRAINFALL");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: DRIVINGRAINFALL";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputDRIVINGRAINFALL)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
#endif
      temutil::nc( nc_inq_varid(ncid, "DRIVINGRAINFALL", &cv) );

      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_float(ncid, cv, start3, count3, &cohort.climate.rain_d[doy]) );
      }

      temutil::nc( nc_close(ncid) ); 
    }//end critical(outputDRIVINGRAINFALL)
  }//end DRIVINGRAINFALL
  map_itr = netcdf_outputs.end();


  //DRIVINGTAIR
  map_itr = netcdf_outputs.find("DRIVINGTAIR");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: DRIVINGTAIR";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputDRIVINGTAIR)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
#endif
      temutil::nc( nc_inq_varid(ncid, "DRIVINGTAIR", &cv) );

      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_float(ncid, cv, start3, count3, &cohort.climate.tair_d[doy]) );
      }

      temutil::nc( nc_close(ncid) ); 
    }//end critical(outputDRIVINGTAIR)
  }//end DRIVINGTAIR
  map_itr = netcdf_outputs.end();


  //DRIVINGVAPO
  map_itr = netcdf_outputs.find("DRIVINGVAPO");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: DRIVINGVAPO";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputDRIVINGVAPO)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
#endif
      temutil::nc( nc_inq_varid(ncid, "DRIVINGVAPO", &cv) );

      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_float(ncid, cv, start3, count3, &cohort.climate.vapo_d[doy]) );
      }

      temutil::nc( nc_close(ncid) ); 
    }//end critical(outputDRIVINGVAPO)
  }//end DRIVINGVAPO
  map_itr = netcdf_outputs.end();


  //DRIVINGNIRR
  map_itr = netcdf_outputs.find("DRIVINGNIRR");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: DRIVINGNIRR";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputDRIVINGNIRR)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
#endif
      temutil::nc( nc_inq_varid(ncid, "DRIVINGNIRR", &cv) );

      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_float(ncid, cv, start3, count3, &cohort.climate.nirr_d[doy]) );
      }

      temutil::nc( nc_close(ncid) ); 
    }//end critical(outputDRIVINGNIRR)
  }//end DRIVINGNIRR
  map_itr = netcdf_outputs.end();


  //RAINFALL
  map_itr = netcdf_outputs.find("RAINFALL");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: RAINFALL";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputRAINFALL)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "RAINFALL", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "RAINFALL", &cv) );
#endif

      if(curr_spec.monthly){
        start3[0] = month_timestep;

        temutil::nc( nc_put_var1_double(ncid, cv, start3, &cohort.edall->m_a2l.rnfl) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;

        temutil::nc( nc_put_var1_double(ncid, cv, start3, &cohort.edall->y_a2l.rnfl) );
      }

      temutil::nc( nc_close(ncid) ); 
    }//end critical(outputRAINFALL)
  }//end RAINFALL
  map_itr = netcdf_outputs.end();


  //Snow water equivalent - a snapshot of the time when output is called
  map_itr = netcdf_outputs.find("SWE");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: SWE";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputSWE)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "SWE", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "SWE", &cv) );
#endif

      double swe;
      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_swesum[0]) );
      }

      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &cohort.edall->m_snws.swesum) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &cohort.edall->y_snws.swesum) );
      }

      temutil::nc( nc_close(ncid) ); 
    }//end critical(outputSWE)
  }//end SWE
  map_itr = netcdf_outputs.end();


  //TCDEEP
  map_itr = netcdf_outputs.find("TCDEEP");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TCDEEP";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputTCDEEP)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TCDEEP", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TCDEEP", &cv) );
#endif

      double tcdeep;
      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_tcdeep[0]) );
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        tcdeep = cohort.edall->m_soid.tcdeep;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &tcdeep) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        tcdeep = cohort.edall->y_soid.tcdeep;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &tcdeep) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputTCDEEP)
  }//end TCDEEP
  map_itr = netcdf_outputs.end();


  //TCLAYER
  map_itr = netcdf_outputs.find("TCLAYER");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TCLAYER";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputTCLAYER)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TCLAYER", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TCLAYER", &cv) );
#endif

      if(curr_spec.monthly){
        soilstart4[0] = month_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, soilstart4, soilcount4, &cohort.edall->m_soid.tcond[0]) );
      }
      else if(curr_spec.yearly){
        soilstart4[0] = year;
        temutil::nc( nc_put_vara_double(ncid, cv, soilstart4, soilcount4, &cohort.edall->y_soid.tcond[0]) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputTCLAYER)
  }//end TCLAYER
  map_itr = netcdf_outputs.end();


  //TCMINEA
  map_itr = netcdf_outputs.find("TCMINEA");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TCMINEA";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputTCMINEA)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TCMINEA", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TCMINEA", &cv) );
#endif

      double tcminea;
      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_tcminea[0]) );
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        tcminea = cohort.edall->m_soid.tcminea;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &tcminea) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        tcminea = cohort.edall->y_soid.tcminea;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &tcminea) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputTCMINEA)
  }//end TCMINEA
  map_itr = netcdf_outputs.end();


  //TCMINEB
  map_itr = netcdf_outputs.find("TCMINEB");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TCMINEB";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputTCMINEB)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TCMINEB", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TCMINEB", &cv) );
#endif

      double tcmineb;
      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_tcmineb[0]) );
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        tcmineb = cohort.edall->m_soid.tcmineb;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &tcmineb) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        tcmineb = cohort.edall->y_soid.tcmineb;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &tcmineb) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputTCMINEB)
  }//end TCMINEB
  map_itr = netcdf_outputs.end();


  //TCMINEC
  map_itr = netcdf_outputs.find("TCMINEC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TCMINEC";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputTCMINEC)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TCMINEC", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TCMINEC", &cv) );
#endif

      double tcminec;
      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_tcminec[0]) );
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        tcminec = cohort.edall->m_soid.tcminec;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &tcminec) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        tcminec = cohort.edall->y_soid.tcminec;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &tcminec) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputTCMINEC)
  }//end TCMINEC
  map_itr = netcdf_outputs.end();


  //TCSHLW
  map_itr = netcdf_outputs.find("TCSHLW");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TCSHLW";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputTCSHLW)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TCSHLW", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TCSHLW", &cv) );
#endif

      double tcshlw;
      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_tcshlw[0]) );
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        tcshlw = cohort.edall->m_soid.tcshlw;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &tcshlw) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        tcshlw = cohort.edall->y_soid.tcshlw;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &tcshlw) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputTCSHLW)
  }//end TCSHLW
  map_itr = netcdf_outputs.end();


  //TDEEP
  map_itr = netcdf_outputs.find("TDEEP");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TDEEP";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputTDEEP)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TDEEP", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TDEEP", &cv) );
#endif

      double tdeep;
      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_tdeep[0]) );
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        tdeep = cohort.edall->m_soid.tdeep;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &tdeep) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        tdeep = cohort.edall->y_soid.tdeep;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &tdeep) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputTDEEP)
  }//end TDEEP
  map_itr = netcdf_outputs.end();


  //TLAYER
  map_itr = netcdf_outputs.find("TLAYER");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TLAYER";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputTLAYER)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
#endif
      temutil::nc( nc_inq_varid(ncid, "TLAYER", &cv) );

      if(curr_spec.daily){
        output_nc_soil_layer(ncid, cv, &cohort.edall->daily_tlayer[0][0], MAX_SOI_LAY, day_timestep, dinm);
      }
      else if(curr_spec.monthly){
        output_nc_soil_layer(ncid, cv, &cohort.edall->m_sois.ts[0], MAX_SOI_LAY, month_timestep, 1);
      }
      else if(curr_spec.yearly){
        output_nc_soil_layer(ncid, cv, &cohort.edall->y_sois.ts[0], MAX_SOI_LAY, year, 1);
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputTLAYER)
  }//end TLAYER
  map_itr = netcdf_outputs.end();


  //FRONTSTYPE
  map_itr = netcdf_outputs.find("FRONTSTYPE");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: ";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputFRONTSTYPE)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "FRONTSTYPE", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "FRONTSTYPE", &cv) );
#endif

    //This uses the summary structs, but might be more accurate
    // if the deque of fronts was checked directly.
    if(curr_spec.daily){
      output_nc_soil_layer(ncid, cv, &cohort.edall->daily_frontstype[0][0], MAX_NUM_FNT, day_timestep, dinm);
    }
    else if(curr_spec.monthly){
      soilstart4[0] = month_timestep;
      temutil::nc( nc_put_vara_int(ncid, cv, soilstart4, frontcount4, &cohort.ground.frnttype[0]) );
      //nc_output_soil(ncid, cv, &cohort.ground.frnttype[0], MAX_NUM_FNT, month_timestep)
    }
    else if(curr_spec.yearly){
      soilstart4[0] = year;
      temutil::nc( nc_put_vara_int(ncid, cv, soilstart4, frontcount4, &cohort.ground.frnttype[0]) );
      //nc_output_soil(ncid, cv, &cohort.ground.frnttype[0], MAX_NUM_FNT, year)
    }

    }//end critical(outputFRONTSTYPE)
  }//end FRONTSTYPE
  map_itr = netcdf_outputs.end();


  //FRONTSDEPTH
  map_itr = netcdf_outputs.find("FRONTSDEPTH");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: FRONTSDEPTH";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputFRONTSDEPTH)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "FRONTSDEPTH", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "FRONTSDEPTH", &cv) );
#endif

    //This uses the summary structs, but might be more accurate
    // if the deque of fronts was checked directly.
    if(curr_spec.daily){
      output_nc_soil_layer(ncid, cv, &cohort.edall->daily_frontsdepth[0][0], MAX_NUM_FNT, day_timestep, dinm);
    }
    else if(curr_spec.monthly){
      soilstart4[0] = month_timestep;
      temutil::nc( nc_put_vara_double(ncid, cv, soilstart4, frontcount4, &cohort.ground.frntz[0]) );
    }
    else if(curr_spec.yearly){
      soilstart4[0] = year;
      temutil::nc( nc_put_vara_double(ncid, cv, soilstart4, frontcount4, &cohort.ground.frntz[0]) );
    }

    }//end critical(outputFRONTSDEPTH)
  }//end FRONTSDEPTH
  map_itr = netcdf_outputs.end();


  //TMINEA
  map_itr = netcdf_outputs.find("TMINEA");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TMINEA";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputTMINEA)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TMINEA", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TMINEA", &cv) );
#endif

      double tminea;
      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_tminea[0]) );
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        tminea = cohort.edall->m_soid.tminea;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &tminea) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        tminea = cohort.edall->y_soid.tminea;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &tminea) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputTMINEA)
  }//end TMINEA
  map_itr = netcdf_outputs.end();


  //TMINEB
  map_itr = netcdf_outputs.find("TMINEB");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TMINEB";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputTMINEB)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TMINEB", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TMINEB", &cv) );
#endif

      double tmineb;
      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_tmineb[0]) );
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        tmineb = cohort.edall->m_soid.tmineb;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &tmineb) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        tmineb = cohort.edall->y_soid.tmineb;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &tmineb) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputTMINEB)
  }//end TMINEB
  map_itr = netcdf_outputs.end();


  //TMINEC
  map_itr = netcdf_outputs.find("TMINEC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TMINEC";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputTMINEC)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TMINEC", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TMINEC", &cv) );
#endif

      double tminec;
      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_tminec[0]) );
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        tminec = cohort.edall->m_soid.tminec;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &tminec) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        tminec = cohort.edall->y_soid.tminec;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &tminec) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputTMINEC)
  }//end TMINEC
  map_itr = netcdf_outputs.end();


  //TSHLW
  map_itr = netcdf_outputs.find("TSHLW");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: TSHLW";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputTSHLW)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TSHLW", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "TSHLW", &cv) );
#endif

      double tshlw;
      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_tshlw[0]) );
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        tshlw = cohort.edall->m_soid.tshlw;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &tshlw) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        tshlw = cohort.edall->y_soid.tshlw;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &tshlw) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputTSHLW)
  }//end TSHLW
  map_itr = netcdf_outputs.end();


  //VWCDEEP
  map_itr = netcdf_outputs.find("VWCDEEP");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: VWCDEEP";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputVWCDEEP)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
#endif
      temutil::nc( nc_inq_varid(ncid, "VWCDEEP", &cv) );

      if(curr_spec.daily){
        output_nc_soil_layer(ncid, cv, &cohort.edall->daily_vwcdeep[0], 1, day_timestep, dinm);
      }
      else if(curr_spec.monthly){
        output_nc_soil_layer(ncid, cv, &cohort.edall->m_soid.vwcdeep, 1, month_timestep, 1);
      }
      else if(curr_spec.yearly){
        output_nc_soil_layer(ncid, cv, &cohort.edall->y_soid.vwcdeep, 1, year, 1);
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputVWCDEEP)
  }//end VWCDEEP
  map_itr = netcdf_outputs.end();


  //VWCLAYER
  map_itr = netcdf_outputs.find("VWCLAYER");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: VWCLAYER";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputVWCLAYER)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
#endif
      temutil::nc( nc_inq_varid(ncid, "VWCLAYER", &cv) );

      if(curr_spec.monthly){
        output_nc_soil_layer(ncid, cv, &cohort.edall->m_soid.vwc[0], MAX_SOI_LAY, month_timestep, 1);
      }
      else if(curr_spec.yearly){
        output_nc_soil_layer(ncid, cv, &cohort.edall->y_soid.vwc[0], MAX_SOI_LAY, year, 1);
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputVWCLAYER)
  }//end VWCLAYER
  map_itr = netcdf_outputs.end();


  //IWCLAYER
  map_itr = netcdf_outputs.find("IWCLAYER");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: IWCLAYER";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputIWCLAYER)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
#endif
      temutil::nc( nc_inq_varid(ncid, "IWCLAYER", &cv) );

      if(curr_spec.monthly){
        output_nc_soil_layer(ncid, cv, &cohort.edall->m_soid.iwc[0], MAX_SOI_LAY, month_timestep, 1);
      }
      else if(curr_spec.yearly){
        output_nc_soil_layer(ncid, cv, &cohort.edall->y_soid.iwc[0], MAX_SOI_LAY, year, 1);
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputIWCLAYER)
  }//end IWCLAYER
  map_itr = netcdf_outputs.end();


  //LWCLAYER
  map_itr = netcdf_outputs.find("LWCLAYER");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LWCLAYER";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputLWCLAYER)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
#endif
      temutil::nc( nc_inq_varid(ncid, "LWCLAYER", &cv) );

      if(curr_spec.monthly){
        soilstart4[0] = month_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, soilstart4, soilcount4, &cohort.edall->m_soid.lwc[0]) );
      }
      else if(curr_spec.yearly){
        soilstart4[0] = year;
        temutil::nc( nc_put_vara_double(ncid, cv, soilstart4, soilcount4, &cohort.edall->y_soid.lwc[0]) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputLWCLAYER)
  }//end LWCLAYER
  map_itr = netcdf_outputs.end();


  //VWCMINEA
  map_itr = netcdf_outputs.find("VWCMINEA");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: VWCMINEA";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputVWCMINEA)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "VWCMINEA", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "VWCMINEA", &cv) );
#endif

      double vwcminea;
      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_vwcminea[0]) );
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        vwcminea = cohort.edall->m_soid.vwcminea;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &vwcminea) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        vwcminea = cohort.edall->y_soid.vwcminea;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &vwcminea) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputVWCMINEA)
  }//end VWCMINEA
  map_itr = netcdf_outputs.end();


  //VWCMINEB
  map_itr = netcdf_outputs.find("VWCMINEB");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: VWCMINEB";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputVWCMINEB)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "VWCMINEB", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "VWCMINEB", &cv) );
#endif

      double vwcmineb;
      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_vwcmineb[0]) );
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        vwcmineb = cohort.edall->m_soid.vwcmineb;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &vwcmineb) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        vwcmineb = cohort.edall->y_soid.vwcmineb;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &vwcmineb) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputVWCMINEB)
  }//end VWCMINEB
  map_itr = netcdf_outputs.end();


  //VWCMINEC
  map_itr = netcdf_outputs.find("VWCMINEC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: VWCMINEC";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputVWCMINEC)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "VWCMINEC", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "VWCMINEC", &cv) );
#endif

      double vwcminec;
      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_vwcminec[0]) );
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        vwcminec = cohort.edall->m_soid.vwcminec;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &vwcminec) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        vwcminec = cohort.edall->y_soid.vwcminec;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &vwcminec) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputVWCMINEC)
  }//end VWCMINEC
  map_itr = netcdf_outputs.end();


  //VWCSHLW
  map_itr = netcdf_outputs.find("VWCSHLW");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: VWCSHLW";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputVWCSHLW)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "VWCSHLW", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "VWCSHLW", &cv) );
#endif

      double vwcshlw;
      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_vwcshlw[0]) );      
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        vwcshlw = cohort.edall->m_soid.vwcshlw;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &vwcshlw) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        vwcshlw = cohort.edall->y_soid.vwcshlw;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &vwcshlw) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputVWCSHLW)
  }//end VWCSHLW
  map_itr = netcdf_outputs.end();


  //WATERTAB
  map_itr = netcdf_outputs.find("WATERTAB");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: WATERTAB";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputWATERTAB)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "WATERTAB", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "WATERTAB", &cv) );
#endif

      double watertab;
      if(curr_spec.daily){
        start3[0] = day_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &cohort.edall->daily_watertab[0]) );      
      }
      else if(curr_spec.monthly){
        start3[0] = month_timestep;
        watertab = cohort.edall->m_sois.watertab;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &watertab) );
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        watertab = cohort.edall->y_sois.watertab;
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &watertab) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputWATERTAB)
  }//end WATERTAB
  map_itr = netcdf_outputs.end();


  /*** Three combination vars. (year, month)x(layer) ***/
  //LAYERDEPTH
  map_itr = netcdf_outputs.find("LAYERDEPTH");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LAYERDEPTH";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputLAYERDEPTH)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "LAYERDEPTH", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "LAYERDEPTH", &cv) );
#endif

      if(curr_spec.monthly){
        soilstart4[0] = month_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, soilstart4, soilcount4, &cohort.cd.m_soil.z[0]) );
      }
      else if(curr_spec.yearly){
        soilstart4[0] = year;
        temutil::nc( nc_put_vara_double(ncid, cv, soilstart4, soilcount4, &cohort.cd.y_soil.z[0]) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputLAYERDEPTH)
  }//end LAYERDEPTH 
  map_itr = netcdf_outputs.end();


  //LAYERDZ
  map_itr = netcdf_outputs.find("LAYERDZ");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LAYERDZ";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputLAYERDZ)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "LAYERDZ", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "LAYERDZ", &cv) );
#endif

      if(curr_spec.monthly){
        soilstart4[0] = month_timestep;
        temutil::nc( nc_put_vara_double(ncid, cv, soilstart4, soilcount4, &cohort.cd.m_soil.dz[0]) );
      }
      else if(curr_spec.yearly){
        soilstart4[0] = year;
        temutil::nc( nc_put_vara_double(ncid, cv, soilstart4, soilcount4, &cohort.cd.y_soil.dz[0]) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputLAYERDZ)
  }//end LAYERDZ 
  map_itr = netcdf_outputs.end();


  //LAYERTYPE
  map_itr = netcdf_outputs.find("LAYERTYPE");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LAYERTYPE";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputLAYERTYPE)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "LAYERTYPE", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "LAYERTYPE", &cv) );
#endif

      if(curr_spec.monthly){
        soilstart4[0] = month_timestep;
        temutil::nc( nc_put_vara_int(ncid, cv, soilstart4, soilcount4, &cohort.cd.m_soil.type[0]) );
      }
      else if(curr_spec.yearly){
        soilstart4[0] = year;
        temutil::nc( nc_put_vara_int(ncid, cv, soilstart4, soilcount4, &cohort.cd.y_soil.type[0]) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputLAYERTYPE)
  }//end LAYERTYPE 
  map_itr = netcdf_outputs.end();


  /*** Four combination vars. (year, month)x(layer, tot)  ***/
  //AVLN
  map_itr = netcdf_outputs.find("AVLN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: AVLN";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputAVLN)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "AVLN", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "AVLN", &cv) );
#endif

      if(curr_spec.layer){

        double avln[MAX_SOI_LAY];
        if(curr_spec.monthly){
          soilstart4[0] = month_timestep;
          for(int il=0; il<MAX_SOI_LAY; il++){
            avln[il] = cohort.bdall->m_sois.avln[il];
          }
        }
        else if(curr_spec.yearly){
          soilstart4[0] = year;
          for(int il=0; il<MAX_SOI_LAY; il++){
            avln[il] = cohort.bdall->y_sois.avln[il];
          }
        }
        temutil::nc( nc_put_vara_double(ncid, cv, soilstart4, soilcount4, &avln[0]) );
      }
      else if(!curr_spec.layer){

        double avln;
        if(curr_spec.monthly){
          start3[0] = month_timestep;
          avln = cohort.bdall->m_soid.avlnsum;
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          avln = cohort.bdall->y_soid.avlnsum;
        }
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &avln) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputAVLN)
  }//end AVLN
  map_itr = netcdf_outputs.end();


  //Burned soil carbon
  map_itr = netcdf_outputs.find("BURNSOIC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNSOIC";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputBURNSOIC)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNSOIC", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNSOIC", &cv) );
#endif

      if(curr_spec.layer){
        /*** STUB ***/
        //By-layer may not be feasible yet.
      }
      else if(!curr_spec.layer){

        double burnsoilC = 0.0;
        if(curr_spec.monthly){
          start3[0] = month_timestep;
          burnsoilC = cohort.year_fd[month].fire_soi2a.orgc;
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          burnsoilC = 0;
          for(int im=0; im<12; im++){
            burnsoilC += cohort.year_fd[im].fire_soi2a.orgc;
          }
        }
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &burnsoilC) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputBURNSOIC)
  }//end BURNSOIC
  map_itr = netcdf_outputs.end();


  //Burned soil nitrogen 
  map_itr = netcdf_outputs.find("BURNSOILN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNSOILN";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputBURNSOILN)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNSOILN", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNSOILN", &cv) );
#endif

      if(curr_spec.layer){
        /*** STUB ***/
      }
      else if(!curr_spec.layer){

        double burnSoilN = 0.0;
        if(curr_spec.monthly){
          start3[0] = month_timestep;
          burnSoilN = cohort.year_fd[month].fire_soi2a.orgn;
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          burnSoilN = 0;
          for(int im=0; im<12; im++){
            burnSoilN += cohort.year_fd[im].fire_soi2a.orgn;
          }
        }
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &burnSoilN) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputBURNSOILN)
  }//end BURNSOILN
  map_itr = netcdf_outputs.end();


  //NDRAIN
  map_itr = netcdf_outputs.find("NDRAIN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: NDRAIN";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputNDRAIN)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "NDRAIN", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "NDRAIN", &cv) );
#endif

      if(curr_spec.layer){

        if(curr_spec.monthly){
          soilstart4[0] = month_timestep;
          //temutil::nc( nc_put_vara_double(ncid, cv, soilstart4, soilcount4, &cohort.soilbgc.bd->m_soi2l.ndrain[0]) );
        }
        else if(curr_spec.yearly){
          /*** STUB ***/
        }
      }
      else if(!curr_spec.layer){

        double ndrain = 0;
        if(curr_spec.monthly){
          start3[0] = month_timestep;

          for(int il=0; il<MAX_SOI_LAY; il++){
            //ndrain += bd->m_soi2l.ndrain[il];
            /*** STUB ***/
          }

        }
        if(curr_spec.yearly){
          start3[0] = year;
          /*** STUB ***/
        }

        //temutil::nc( nc_put_var1_double(ncid, cv, start3, &ndrain) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputNDRAIN)
  }//end NDRAIN
  map_itr = netcdf_outputs.end();


  //NETNMIN
  map_itr = netcdf_outputs.find("NETNMIN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: NETNMIN";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputNETNMIN)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "NETNMIN", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "NETNMIN", &cv) );
#endif

      if(curr_spec.layer){

        double netnmin[MAX_SOI_LAY];
        for(int il=0; il<MAX_SOI_LAY; il++){
          if(curr_spec.monthly){
            soilstart4[0] = month_timestep;
            netnmin[il] = cohort.bdall->m_soi2soi.netnmin[il];
          }
          else if(curr_spec.yearly){
            soilstart4[0] = year;
            netnmin[il] = cohort.bdall->y_soi2soi.netnmin[il];
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, soilstart4, soilcount4, &netnmin[0]) );
      }
      //Total, instead of by layer
      else if(!curr_spec.layer){

        double netnmin;
        if(curr_spec.monthly){
          start3[0] = month_timestep;
          netnmin = cohort.bdall->m_soi2soi.netnminsum;
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          netnmin = cohort.bdall->y_soi2soi.netnminsum;
        }

        temutil::nc( nc_put_var1_double(ncid, cv, start3, &netnmin) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputNETNMIN)
  }//end NETNMIN
  map_itr = netcdf_outputs.end();


  //NIMMOB
  map_itr = netcdf_outputs.find("NIMMOB");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: NIMMOB";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputNIMMOB)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "NIMMOB", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "NIMMOB", &cv) );
#endif

      if(curr_spec.layer){

        double nimmob[MAX_SOI_LAY];
        for(int il=0; il<MAX_SOI_LAY; il++){
          if(curr_spec.monthly){
            soilstart4[0] = month_timestep;
            nimmob[il] = cohort.bdall->m_soi2soi.nimmob[il];
          }
          else if(curr_spec.yearly){
            soilstart4[0] = year;
            nimmob[il] = cohort.bdall->y_soi2soi.nimmob[il];
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, soilstart4, soilcount4, &nimmob[0]) );
      }
      else if(!curr_spec.layer){

        double nimmob;
        if(curr_spec.monthly){
          start3[0] = month_timestep;
          nimmob = cohort.bdall->m_soi2soi.nimmobsum;
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          nimmob = cohort.bdall->y_soi2soi.nimmobsum;
        }

        temutil::nc( nc_put_var1_double(ncid, cv, start3, &nimmob) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputNIMMOB)
  }//end NIMMOB
  map_itr = netcdf_outputs.end();


  //NINPUT
  map_itr = netcdf_outputs.find("NINPUT");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: NINPUT";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputNINPUT)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "NINPUT", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "NINPUT", &cv) );
#endif

      if(curr_spec.layer){
        /*** STUB ***/
      }
      else if(!curr_spec.layer){

        double ninput;
        if(curr_spec.monthly){
          start3[0] = month_timestep;
          ninput = cohort.bdall->m_a2soi.avlninput;
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          ninput = cohort.bdall->y_a2soi.avlninput;
        }

        temutil::nc( nc_put_var1_double(ncid, cv, start3, &ninput) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputNINPUT)
  }//end NINPUT
  map_itr = netcdf_outputs.end();


  //NLOST
  map_itr = netcdf_outputs.find("NLOST");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: NLOST";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputNLOST)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "NLOST", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "NLOST", &cv) );
#endif

      double nlost;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        nlost = cohort.bdall->m_soi2l.avlnlost
              + cohort.bdall->m_soi2l.orgnlost;
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        nlost = cohort.bdall->y_soi2l.avlnlost
              + cohort.bdall->y_soi2l.orgnlost;
   
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &nlost) );
      temutil::nc( nc_close(ncid) );
    }//end critical(outputNLOST)
  }//end NLOST
  map_itr = netcdf_outputs.end();


  //ORGN
  map_itr = netcdf_outputs.find("ORGN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: ORGN";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputORGN)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "ORGN", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "ORGN", &cv) );
#endif

      if(curr_spec.layer){

        if(curr_spec.monthly){
          soilstart4[0] = month_timestep;
        }
        else if(curr_spec.yearly){
          soilstart4[0] = year;
        }

        double orgn[MAX_SOI_LAY];
        int il = 0;
        Layer* currL = this->cohort.ground.toplayer;
        while(currL != NULL){
          orgn[il] = currL->orgn;
          il++;
          currL = currL->nextl;
        }

        temutil::nc( nc_put_vara_double(ncid, cv, soilstart4, soilcount4, &orgn[0]) );
      }
      //Total, instead of by layer
      else if(!curr_spec.layer){

        double orgn;
        if(curr_spec.monthly){
          start3[0] = month_timestep;
          orgn = cohort.bdall->m_soid.orgnsum;
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          orgn = cohort.bdall->y_soid.orgnsum;
        }

        temutil::nc( nc_put_var1_double(ncid, cv, start3, &orgn) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputORGN)
  }//end ORGN
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("RH");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: RH";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputRH)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "RH", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "RH", &cv) );
#endif

      if(curr_spec.layer){

        double rh[MAX_SOI_LAY];
        if(curr_spec.monthly){
          soilstart4[0] = month_timestep;
          for(int il=0; il<MAX_SOI_LAY; il++){
            rh[il] = cohort.bdall->m_soi2a.rhrawc[il]
                   + cohort.bdall->m_soi2a.rhsoma[il]
                   + cohort.bdall->m_soi2a.rhsompr[il]
                   + cohort.bdall->m_soi2a.rhsomcr[il];
          }
        }
        else if(curr_spec.yearly){
          soilstart4[0] = year;
          for(int il=0; il<MAX_SOI_LAY; il++){
            rh[il] = cohort.bdall->y_soi2a.rhrawc[il]
                   + cohort.bdall->y_soi2a.rhsoma[il]
                   + cohort.bdall->y_soi2a.rhsompr[il]
                   + cohort.bdall->y_soi2a.rhsomcr[il];
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, soilstart4, soilcount4, &rh[0]) );
      }

      else if(!curr_spec.layer){

        double rh;
        if(curr_spec.monthly){
          start3[0] = month_timestep;
          rh = cohort.bdall->m_soi2a.rhtot;
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          rh = cohort.bdall->y_soi2a.rhtot;
        }

        temutil::nc( nc_put_var1_double(ncid, cv, start3, &rh) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputRH)
  }//end RH 
  map_itr = netcdf_outputs.end();


  //SOC
  map_itr = netcdf_outputs.find("SOC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: SOC";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputSOC)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "SOC", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "SOC", &cv) );
#endif

      if(curr_spec.layer){

        if(curr_spec.monthly){
          soilstart4[0] = month_timestep;
        }
        else if(curr_spec.yearly){
          soilstart4[0] = year;
        }

        double soilc[MAX_SOI_LAY];
        int il = 0;
        Layer* currL = this->cohort.ground.toplayer;
        while(currL != NULL){
          soilc[il] = currL->rawc;
          il++;
          currL = currL->nextl;
        }

        temutil::nc( nc_put_vara_double(ncid, cv, soilstart4, soilcount4, &soilc[0]) );
      }
      //Total, instead of by layer
      else if(!curr_spec.layer){

        double soilc;
        if(curr_spec.monthly){
          start3[0] = month_timestep;
          soilc = cohort.bdall->m_soid.rawcsum;
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          soilc = cohort.bdall->y_soid.rawcsum;
        }

        temutil::nc( nc_put_var1_double(ncid, cv, start3, &soilc) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputSOC)
  }//end SOC
  map_itr = netcdf_outputs.end();


  /*** Six combination vars: (year,month)x(PFT,Comp,Both)***/
  //BURNVEG2AIRC
  map_itr = netcdf_outputs.find("BURNVEG2AIRC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNVEG2AIRC";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputBURNVEG2AIRC)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNVEG2AIRC", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNVEG2AIRC", &cv) );
#endif

      double burnveg2airc;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        burnveg2airc = cohort.year_fd[month].fire_v2a.orgc;
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        burnveg2airc = cohort.fd->fire_v2a.orgc;
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &burnveg2airc) );

      temutil::nc( nc_close(ncid) );
    }//end critical(outputBURNVEG2AIRC)
  }//end BURNVEG2AIRC
  map_itr = netcdf_outputs.end();


  //BURNVEG2AIRN
  map_itr = netcdf_outputs.find("BURNVEG2AIRN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNVEG2AIRN";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputBURNVEG2AIRN)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNVEG2AIRN", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNVEG2AIRN", &cv) );
#endif

      double burnveg2airn;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        burnveg2airn = cohort.year_fd[month].fire_v2a.orgn;
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        burnveg2airn = cohort.fd->fire_v2a.orgn;
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &burnveg2airn) );

      temutil::nc( nc_close(ncid) );
    }//end critical(outputBURNVEG2AIRN)
  }//end BURNVEG2AIRN
  map_itr = netcdf_outputs.end();


  //BURNVEG2DEADC
  map_itr = netcdf_outputs.find("BURNVEG2DEADC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNVEG2DEADC";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputBURNVEG2DEADC)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNVEG2DEADC", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNVEG2DEADC", &cv) );
#endif

      double burnveg2deadc;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        burnveg2deadc = cohort.year_fd[month].fire_v2dead.vegC;
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        burnveg2deadc = cohort.fd->fire_v2dead.vegC;
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &burnveg2deadc) );

      temutil::nc( nc_close(ncid) );
    }//end critical(outputBURNVEG2DEADC)
  }//end BURNVEG2DEADC
  map_itr = netcdf_outputs.end();


  //BURNVEG2DEADN
  map_itr = netcdf_outputs.find("BURNVEG2DEADN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNVEG2DEADN";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputBURNVEG2DEADN)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNVEG2DEADN", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNVEG2DEADN", &cv) );
#endif

      double burnveg2deadn;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        burnveg2deadn = cohort.year_fd[month].fire_v2dead.strN;
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        burnveg2deadn = cohort.fd->fire_v2dead.strN;
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &burnveg2deadn) );

      temutil::nc( nc_close(ncid) );
    }//end critical(outputBURNVEG2DEADN)
  }//end BURNVEG2DEADN
  map_itr = netcdf_outputs.end();


  //BURNVEG2SOIABVC
  map_itr = netcdf_outputs.find("BURNVEG2SOIABVC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNVEG2SOIABVC";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputBURNVEG2SOIABVC)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNVEG2SOIABVC", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNVEG2SOIABVC", &cv) );
#endif

      double burnveg2soiabvc;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        burnveg2soiabvc = cohort.year_fd[month].fire_v2soi.abvc;
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        burnveg2soiabvc = cohort.fd->fire_v2soi.abvc;
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &burnveg2soiabvc) );

      temutil::nc( nc_close(ncid) );
    }//end critical(outputBURNVEG2SOIABVC)
  }//end BURNVEG2SOIABVC
  map_itr = netcdf_outputs.end();


  //BURNVEG2SOIABVN
  map_itr = netcdf_outputs.find("BURNVEG2SOIABVN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNVEG2SOIABVN";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputBURNVEG2SOIABVN)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNVEG2SOIABVN", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNVEG2SOIABVN", &cv) );
#endif

      double burnveg2soiabvn;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        burnveg2soiabvn = cohort.year_fd[month].fire_v2soi.abvn;
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        burnveg2soiabvn = cohort.fd->fire_v2soi.abvn;
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &burnveg2soiabvn) );

      temutil::nc( nc_close(ncid) );
    }//end critical(outputBURNVEG2SOIABVN)
  }//end BURNVEG2SOIABVN
  map_itr = netcdf_outputs.end();


  //BURNVEG2SOIBLWC
  map_itr = netcdf_outputs.find("BURNVEG2SOIBLWC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNVEG2SOIBLWC";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputBURNVEG2SOIBLWC)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNVEG2SOIBLWC", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNVEG2SOIBLWC", &cv) );
#endif

      double burnveg2soiblwc;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        burnveg2soiblwc = cohort.year_fd[month].fire_v2soi.blwc;
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        burnveg2soiblwc = cohort.fd->fire_v2soi.blwc;
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &burnveg2soiblwc) );

      temutil::nc( nc_close(ncid) );
    }//end critical(outputBURNVEG2SOIBLWC)
  }//end BURNVEG2SOIBLWC
  map_itr = netcdf_outputs.end();


  //BURNVEG2SOIBLWN
  map_itr = netcdf_outputs.find("BURNVEG2SOIBLWN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNVEG2SOIBLWN";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputBURNVEG2SOIBLWN)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNVEG2SOIBLWN", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "BURNVEG2SOIBLWN", &cv) );
#endif

      double burnveg2soiblwn;
      if(curr_spec.monthly){
        start3[0] = month_timestep;
        burnveg2soiblwn = cohort.year_fd[month].fire_v2soi.blwn;
      }
      else if(curr_spec.yearly){
        start3[0] = year;
        burnveg2soiblwn = cohort.fd->fire_v2soi.blwn;
      }

      temutil::nc( nc_put_var1_double(ncid, cv, start3, &burnveg2soiblwn) );

      temutil::nc( nc_close(ncid) );
    }//end critical(outputBURNVEG2SOIBLWN)
  }//end BURNVEG2SOIBLWN
  map_itr = netcdf_outputs.end();


  //GPP
  map_itr = netcdf_outputs.find("GPP");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: GPP";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputGPP)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "GPP", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "GPP", &cv) );
#endif

      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){

        double gpp[NUM_PFT_PART][NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){

            if(curr_spec.monthly){
              start5[0] = month_timestep;
              gpp[ipp][ip] = cohort.bd[ip].m_a2v.gpp[ipp];
            }
            else if(curr_spec.yearly){
              start5[0] = year;
              gpp[ipp][ip] = cohort.bd[ip].y_a2v.gpp[ipp];
            }
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, start5, count5, &gpp[0][0]) );
      }
      //PFT only
      else if(curr_spec.pft && !curr_spec.compartment){

        double gpp[NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){

          if(curr_spec.monthly){
            PFTstart4[0] = month_timestep;
            gpp[ip] = cohort.bd[ip].m_a2v.gppall; 
          }
          else if(curr_spec.yearly){
            PFTstart4[0] = year;
            gpp[ip] = cohort.bd[ip].y_a2v.gppall; 
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &gpp[0]) );
      }
      //Compartment only
      else if(!curr_spec.pft && curr_spec.compartment){

        double gpp[NUM_PFT_PART] = {0};
        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){

            if(curr_spec.monthly){
              CompStart4[0] = month_timestep;
              gpp[ipp] += cohort.bd[ip].m_a2v.gpp[ipp];
            }
            else if(curr_spec.yearly){
              CompStart4[0] = year;
              gpp[ipp] += cohort.bd[ip].m_a2v.gpp[ipp];
            }
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, CompStart4, CompCount4, &gpp[0]) );
      }
      //Neither PFT nor Compartment - total instead
      else if(!curr_spec.pft && !curr_spec.compartment){

        double gpp;
        if(curr_spec.monthly){
          start3[0] = month_timestep;
          gpp = cohort.bdall->m_a2v.gppall;
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          gpp = cohort.bdall->y_a2v.gppall;
        }

        temutil::nc( nc_put_var1_double(ncid, cv, start3, &gpp) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputGPP)
  }//end GPP
  map_itr = netcdf_outputs.end();


  //INGPP
  map_itr = netcdf_outputs.find("INGPP");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: INGPP";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputINGPP)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "INGPP", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "INGPP", &cv) );
#endif

      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){

        double ingpp[NUM_PFT_PART][NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){

            if(curr_spec.monthly){
              start5[0] = month_timestep;
              ingpp[ipp][ip] = cohort.bd[ip].m_a2v.ingpp[ipp];
            }
            else if(curr_spec.yearly){
              start5[0] = year;
              ingpp[ipp][ip] = cohort.bd[ip].y_a2v.ingpp[ipp];
            }
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, start5, count5, &ingpp[0][0]) );
      }
      //PFT only
      else if(curr_spec.pft && !curr_spec.compartment){

        double ingpp[NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){

          if(curr_spec.monthly){
            PFTstart4[0] = month_timestep;
            ingpp[ip] = cohort.bd[ip].m_a2v.ingppall; 
          }
          else if(curr_spec.yearly){
            PFTstart4[0] = year;
            ingpp[ip] = cohort.bd[ip].y_a2v.ingppall; 
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &ingpp[0]) );
      }
      //Compartment only
      else if(!curr_spec.pft && curr_spec.compartment){

        double ingpp[NUM_PFT_PART] = {0};
        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){

            if(curr_spec.monthly){
              CompStart4[0] = month_timestep;
              ingpp[ipp] += cohort.bd[ip].m_a2v.ingpp[ipp];
            }
            else if(curr_spec.yearly){
              CompStart4[0] = year;
              ingpp[ipp] += cohort.bd[ip].m_a2v.ingpp[ipp];
            }
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, CompStart4, CompCount4, &ingpp[0]) );
      }
      //Neither PFT nor Compartment - total instead
      else if(!curr_spec.pft && !curr_spec.compartment){

        double ingpp;
        if(curr_spec.monthly){
          start3[0] = month_timestep;
          ingpp = cohort.bdall->m_a2v.ingppall;
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          ingpp = cohort.bdall->y_a2v.ingppall;
        }

        temutil::nc( nc_put_var1_double(ncid, cv, start3, &ingpp) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputINGPP)
  }//end INGPP
  map_itr = netcdf_outputs.end();


  //INNPP
  map_itr = netcdf_outputs.find("INNPP");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: INNPP";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputINNPP)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "INNPP", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "INNPP", &cv) );
#endif

      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){

        double innpp[NUM_PFT_PART][NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){

            if(curr_spec.monthly){
              start5[0] = month_timestep;
              innpp[ipp][ip] = cohort.bd[ip].m_a2v.innpp[ipp];
            }
            else if(curr_spec.yearly){
              start5[0] = year;
              innpp[ipp][ip] = cohort.bd[ip].y_a2v.innpp[ipp];
            }
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, start5, count5, &innpp[0][0]) );
      }
      //PFT only
      else if(curr_spec.pft && !curr_spec.compartment){

        double innpp[NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){

          if(curr_spec.monthly){
            PFTstart4[0] = month_timestep;
            innpp[ip] = cohort.bd[ip].m_a2v.innppall; 
          }
          else if(curr_spec.yearly){
            PFTstart4[0] = year;
            innpp[ip] = cohort.bd[ip].y_a2v.innppall; 
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &innpp[0]) );
      }
      //Compartment only
      else if(!curr_spec.pft && curr_spec.compartment){

        double innpp[NUM_PFT_PART] = {0};
        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){

            if(curr_spec.monthly){
              CompStart4[0] = month_timestep;
              innpp[ipp] += cohort.bd[ip].m_a2v.innpp[ipp];
            }
            else if(curr_spec.yearly){
              CompStart4[0] = year;
              innpp[ipp] += cohort.bd[ip].m_a2v.innpp[ipp];
            }
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, CompStart4, CompCount4, &innpp[0]) );
      }
      //Neither PFT nor Compartment - total instead
      else if(!curr_spec.pft && !curr_spec.compartment){

        double innpp;
        if(curr_spec.monthly){
          start3[0] = month_timestep;
          innpp = cohort.bdall->m_a2v.innppall;
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          innpp = cohort.bdall->y_a2v.innppall;
        }

        temutil::nc( nc_put_var1_double(ncid, cv, start3, &innpp) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputINNPP)
  }//end INNPP
  map_itr = netcdf_outputs.end();


  //LAI
  map_itr = netcdf_outputs.find("LAI");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LAI";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputLAI)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "LAI", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "LAI", &cv) );
#endif

      //PFT
      if(curr_spec.pft){

        if(curr_spec.monthly){
          PFTstart4[0] = month_timestep;
          temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &cohort.cd.m_veg.lai[0]) );
        }
        else if(curr_spec.yearly){
          PFTstart4[0] = year;
          temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &cohort.cd.y_veg.lai[0]) );
        }

      }
      //Total
      else if(!curr_spec.pft){

        double lai = 0;
        if(curr_spec.monthly){
          start3[0] = month_timestep;
          for(int ip=0; ip<NUM_PFT; ip++){
            if(cohort.cd.m_veg.vegcov[ip]>0.){
              lai += cohort.cd.m_veg.lai[ip];
            }
          }
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          for(int ip=0; ip<NUM_PFT; ip++){
            if(cohort.cd.y_veg.vegcov[ip]>0.){
              lai += cohort.cd.y_veg.lai[ip];
            }
          }
        }
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &lai) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputLAI)
  }//end LAI
  map_itr = netcdf_outputs.end();


  //LTRFALC
  map_itr = netcdf_outputs.find("LTRFALC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LTRFALC";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputLTRFALC)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "LTRFALC", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "LTRFALC", &cv) );
#endif

      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){

        double ltrfalc[NUM_PFT_PART][NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){

            if(curr_spec.monthly){
              start5[0] = month_timestep;
              ltrfalc[ipp][ip] = cohort.bd[ip].m_v2soi.ltrfalc[ipp];
            }
            else if(curr_spec.yearly){
              start5[0] = year;
              ltrfalc[ipp][ip] = cohort.bd[ip].y_v2soi.ltrfalc[ipp];
            }
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, start5, count5, &ltrfalc[0][0]) );
      }
      //PFT only
      else if(curr_spec.pft && !curr_spec.compartment){

        double ltrfalc[NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){

          if(curr_spec.monthly){
            PFTstart4[0] = month_timestep;
            ltrfalc[ip] = cohort.bd[ip].m_v2soi.ltrfalcall;
          }
          else if(curr_spec.yearly){
            PFTstart4[0] = year;
            ltrfalc[ip] = cohort.bd[ip].y_v2soi.ltrfalcall;
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &ltrfalc[0]) );
      }
      //Compartment only
      else if(!curr_spec.pft && curr_spec.compartment){

        double ltrfalc[NUM_PFT_PART] = {0};
        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){

            if(curr_spec.monthly){
              CompStart4[0] = month_timestep;
              ltrfalc[ipp] += cohort.bd[ip].m_v2soi.ltrfalc[ipp];
            }
            else if(curr_spec.yearly){
              CompStart4[0] = year;
              ltrfalc[ipp] += cohort.bd[ip].y_v2soi.ltrfalc[ipp];
            }
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, CompStart4, CompCount4, &ltrfalc[0]) );
      }
      //Neither PFT nor compartment - totals
      else if(!curr_spec.pft && !curr_spec.compartment){

        double ltrfalc = 0;
        for(int ip=0; ip<NUM_PFT; ip++){

          if(curr_spec.monthly){
            start3[0] = month_timestep;
            ltrfalc += cohort.bd[ip].m_v2soi.ltrfalcall;
          }
          else if(curr_spec.yearly){
            start3[0] = year;
            ltrfalc += cohort.bd[ip].y_v2soi.ltrfalcall;
          }
        }
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &ltrfalc) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputLTRFALC)
  }//end LTRFALC
  map_itr = netcdf_outputs.end();


  //LTRFALN
  map_itr = netcdf_outputs.find("LTRFALN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LTRFALN";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputLTRFALN)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "LTRFALN", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "LTRFALN", &cv) );
#endif

      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){

        double ltrfaln[NUM_PFT_PART][NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){

            if(curr_spec.monthly){
              start5[0] = month_timestep;
              ltrfaln[ipp][ip] = cohort.bd[ip].m_v2soi.ltrfaln[ipp];
            }
            else if(curr_spec.yearly){
              start5[0] = year;
              ltrfaln[ipp][ip] = cohort.bd[ip].y_v2soi.ltrfaln[ipp];
            }
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, start5, count5, &ltrfaln[0][0]) );
      }
      //PFT only
      else if(curr_spec.pft && !curr_spec.compartment){

        double ltrfaln[NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){

          if(curr_spec.monthly){
            PFTstart4[0] = month_timestep;
            ltrfaln[ip] = cohort.bd[ip].m_v2soi.ltrfalnall;
          }
          else if(curr_spec.yearly){
            PFTstart4[0] = year;
            ltrfaln[ip] = cohort.bd[ip].y_v2soi.ltrfalnall;
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &ltrfaln[0]) );
      }
      //Compartment only
      else if(!curr_spec.pft && curr_spec.compartment){

        double ltrfaln[NUM_PFT_PART] = {0};
        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){

            if(curr_spec.monthly){
              CompStart4[0] = month_timestep;
              ltrfaln[ipp] += cohort.bd[ip].m_v2soi.ltrfaln[ipp];
            }
            else if(curr_spec.yearly){
              CompStart4[0] = year;
              ltrfaln[ipp] += cohort.bd[ip].y_v2soi.ltrfaln[ipp];
            }
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, CompStart4, CompCount4, &ltrfaln[0]) );
      }
      //Neither PFT nor compartment - totals
      else if(!curr_spec.pft && !curr_spec.compartment){

        double ltrfaln = 0;
        for(int ip=0; ip<NUM_PFT; ip++){

          if(curr_spec.monthly){
            start3[0] = month_timestep;
            ltrfaln += cohort.bd[ip].m_v2soi.ltrfalnall;
          }
          else if(curr_spec.yearly){
            start3[0] = year;
            ltrfaln += cohort.bd[ip].y_v2soi.ltrfalnall;
          }
        }
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &ltrfaln) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputLTRFALN)
  }//end LTRFALN
  map_itr = netcdf_outputs.end();


  //NPP
  map_itr = netcdf_outputs.find("NPP");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: NPP";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputNPP)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "NPP", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "NPP", &cv) );
#endif

      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){

        double npp[NUM_PFT_PART][NUM_PFT];
        if(curr_spec.monthly){
          start5[0] = month_timestep;
          for(int ip=0; ip<NUM_PFT; ip++){
            for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
              npp[ipp][ip] = cohort.bd[ip].m_a2v.npp[ipp];
            }
          }
        }
        else if(curr_spec.yearly){
          start5[0] = year;
          for(int ip=0; ip<NUM_PFT; ip++){
            for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
              npp[ipp][ip] = cohort.bd[ip].y_a2v.npp[ipp];
            }
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, start5, count5, &npp[0][0]) );
      }
      //PFT only
      else if(curr_spec.pft && !curr_spec.compartment){

        double npp[NUM_PFT];
        if(curr_spec.monthly){
          PFTstart4[0] = month_timestep;
          for(int ip=0; ip<NUM_PFT; ip++){
            npp[ip] = cohort.bd[ip].m_a2v.nppall; 
          }
        }
        else if(curr_spec.yearly){
          PFTstart4[0] = year;
          for(int ip=0; ip<NUM_PFT; ip++){
            npp[ip] = cohort.bd[ip].y_a2v.nppall; 
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &npp[0]) );
      }
      //Compartment only
      else if(!curr_spec.pft && curr_spec.compartment){

        double npp[NUM_PFT_PART] = {0};
        if(curr_spec.monthly){
          CompStart4[0] = month_timestep;
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            for(int ip=0; ip<NUM_PFT; ip++){
              npp[ipp] += cohort.bd[ip].m_a2v.npp[ipp];
            }
          }
        }
        else if(curr_spec.yearly){
          CompStart4[0] = year;
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            for(int ip=0; ip<NUM_PFT; ip++){
              npp[ipp] += cohort.bd[ip].y_a2v.npp[ipp];
            }
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, CompStart4, CompCount4, &npp[0]) );
      }
      //Neither PFT nor Compartment - total instead
      else if(!curr_spec.pft && !curr_spec.compartment){

        double npp;
        if(curr_spec.monthly){
          start3[0] = month_timestep;
          npp = cohort.bdall->m_a2v.nppall;
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          npp = cohort.bdall->y_a2v.nppall;
        }

        temutil::nc( nc_put_var1_double(ncid, cv, start3, &npp) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputNPP)
  }//end NPP
  map_itr = netcdf_outputs.end();


  //NUPTAKEIN
  map_itr = netcdf_outputs.find("NUPTAKEIN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: NUPTAKEIN";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputNUPTAKEIN)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "NUPTAKEIN", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "NUPTAKEIN", &cv) );
#endif

      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){
        /*** STUB ***/
        //Currently unavailable. N uptake will need to be made accessible
        // by PFT compartment.
      }
      //PFT only
      else if(curr_spec.pft && !curr_spec.compartment){
        double innuptake[NUM_PFT];

        if(curr_spec.monthly){
          PFTstart4[0] = month_timestep;

          for(int ip=0; ip<NUM_PFT; ip++){
            innuptake[ip] = cohort.bd[ip].m_soi2v.innuptake;
          }
        }
        else if(curr_spec.yearly){
          PFTstart4[0] = year;

          for(int ip=0; ip<NUM_PFT; ip++){
            innuptake[ip] = cohort.bd[ip].y_soi2v.innuptake;
          }
        }
        temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &innuptake[0]) );
      }
      //Compartment only
      else if(!curr_spec.pft && curr_spec.compartment){
        /*** STUB ***/
      }
      //Neither PFT nor compartment
      else if(!curr_spec.pft && !curr_spec.compartment){
        double innuptake = 0;

        if(curr_spec.monthly){
          start3[0] = month_timestep;
          innuptake = cohort.bdall->m_soi2v.innuptake;
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          innuptake = cohort.bdall->y_soi2v.innuptake;
        }
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &innuptake) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputNUPTAKEIN)
  }//end NUPTAKEIN
  map_itr = netcdf_outputs.end();


  //NUPTAKELAB
  map_itr = netcdf_outputs.find("NUPTAKELAB");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: NUPTAKELAB";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputNUPTAKELAB)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "NUPTAKELAB", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "NUPTAKELAB", &cv) );
#endif

      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){
        /*** STUB ***/
        //Currently unavailable. Labile N uptake will need to be made
        // accessible by PFT compartment.
      }
      //PFT only
      else if(curr_spec.pft && !curr_spec.compartment){
        double labnuptake[NUM_PFT];

        if(curr_spec.monthly){
          PFTstart4[0] = month_timestep;

          for(int ip=0; ip<NUM_PFT; ip++){
            labnuptake[ip] = cohort.bd[ip].m_soi2v.lnuptake;
          }
        }
        else if(curr_spec.yearly){
          PFTstart4[0] = year;

          for(int ip=0; ip<NUM_PFT; ip++){
            labnuptake[ip] = cohort.bd[ip].y_soi2v.lnuptake;
          }
        }
        temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &labnuptake[0]) );
      }
      //Compartment only
      else if(!curr_spec.pft && curr_spec.compartment){
        /*** STUB ***/
      }
      //Neither PFT nor compartment
      else if(!curr_spec.pft && !curr_spec.compartment){
        double labnuptake = 0;

        if(curr_spec.monthly){
          start3[0] = month_timestep;
          labnuptake = cohort.bdall->m_soi2v.lnuptake;
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          labnuptake = cohort.bdall->y_soi2v.lnuptake;
        }
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &labnuptake) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputNUPTAKELAB)
  }//end NUPTAKELAB
  map_itr = netcdf_outputs.end();


  //NUPTAKEST
  map_itr = netcdf_outputs.find("NUPTAKEST");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: NUPTAKEST";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputNUPTAKEST)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "NUPTAKEST", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "NUPTAKEST", &cv) );
#endif

      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){
        double snuptake[NUM_PFT_PART][NUM_PFT];

        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            if(curr_spec.monthly){
              start5[0] = month_timestep;
              snuptake[ipp][ip] = cohort.bd[ip].m_soi2v.snuptake[ipp];
            }
            else if(curr_spec.yearly){
              start5[0] = year;
              snuptake[ipp][ip] = cohort.bd[ip].y_soi2v.snuptake[ipp];
            }
          }
        }
        temutil::nc( nc_put_vara_double(ncid, cv, start5, count5, &snuptake[0][0]) );
      }
      //PFT only
      else if(curr_spec.pft && !curr_spec.compartment){
        double snuptake[NUM_PFT] = {0};

        if(curr_spec.monthly){
          PFTstart4[0] = month_timestep;

          for(int ip=0; ip<NUM_PFT; ip++){
            snuptake[ip] = cohort.bd[ip].m_soi2v.snuptakeall;
          }
        }
        else if(curr_spec.yearly){
          PFTstart4[0] = year;

          for(int ip=0; ip<NUM_PFT; ip++){
            snuptake[ip] = cohort.bd[ip].y_soi2v.snuptakeall;
          }
        }
        temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &snuptake[0]) );
      }
      //Compartment only
      else if(!curr_spec.pft && curr_spec.compartment){
        double snuptake[NUM_PFT_PART] = {0};
        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){
            if(curr_spec.monthly){
              CompStart4[0] = month_timestep;
              snuptake[ipp] += cohort.bd[ip].m_soi2v.snuptake[ipp]; 
            }
            else if(curr_spec.yearly){
              CompStart4[0] = year;
              snuptake[ipp] += cohort.bd[ip].y_soi2v.snuptake[ipp]; 
            }
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, CompStart4, CompCount4, &snuptake[0]) );
      }
      //Neither PFT nor compartment
      else if(!curr_spec.pft && !curr_spec.compartment){
        double snuptakeall = 0;

        if(curr_spec.monthly){
          start3[0] = month_timestep;
          snuptakeall = cohort.bdall->m_soi2v.snuptakeall;
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          snuptakeall = cohort.bdall->y_soi2v.snuptakeall;
        }
        temutil::nc( nc_put_var1_double(ncid, cv, start3, &snuptakeall) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputNUPTAKEST)
  }//end NUPTAKEST
  map_itr = netcdf_outputs.end();


  //RG
  map_itr = netcdf_outputs.find("RG");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: RG";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputRG)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "RG", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "RG", &cv) );
#endif

      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){

        double rg[NUM_PFT_PART][NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            if(curr_spec.monthly){
              start5[0] = month_timestep;
              rg[ipp][ip] = cohort.bd[ip].m_v2a.rg[ipp];
            }
            else if(curr_spec.yearly){
              start5[0] = year;
              rg[ipp][ip] = cohort.bd[ip].y_v2a.rg[ipp];
            }
          }
        }
        temutil::nc( nc_put_vara_double(ncid, cv, start5, count5, &rg[0][0]) ); 
      }
      //PFT only
      else if(curr_spec.pft && !curr_spec.compartment){

        double rg[NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          if(curr_spec.monthly){
            PFTstart4[0] = month_timestep;
            rg[ip] = cohort.bd[ip].m_v2a.rgall;
          }
          else if(curr_spec.yearly){
            PFTstart4[0] = year;
            rg[ip] = cohort.bd[ip].y_v2a.rgall;
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &rg[0]) ); 
      }
      //Compartment only
      else if(!curr_spec.pft && curr_spec.compartment){

        double rg[NUM_PFT_PART] = {0};
        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){
            if(curr_spec.monthly){
              CompStart4[0] = month_timestep;
              rg[ipp] += cohort.bd[ip].m_v2a.rg[ipp];
            }
            else if(curr_spec.yearly){
              CompStart4[0] = year;
              rg[ipp] += cohort.bd[ip].y_v2a.rg[ipp];
            }
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, CompStart4, CompCount4, &rg[0]) );
   
      }
      //Neither PFT nor compartment - Total
      else if(!curr_spec.pft && !curr_spec.compartment){

        double rg;
        if(curr_spec.monthly){
          start3[0] = month_timestep;
          rg = cohort.bdall->m_v2a.rgall;
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          rg = cohort.bdall->y_v2a.rgall;
        }

        temutil::nc( nc_put_var1_double(ncid, cv, start3, &rg) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputRG)
  }//end RG
  map_itr = netcdf_outputs.end();


  //RM
  map_itr = netcdf_outputs.find("RM");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: RM";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputRM)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "RM", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "RM", &cv) );
#endif

      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){

        double rm[NUM_PFT_PART][NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            if(curr_spec.monthly){
              start5[0] = month_timestep;
              rm[ipp][ip] = cohort.bd[ip].m_v2a.rm[ipp];
            }
            else if(curr_spec.yearly){
              start5[0] = year;
              rm[ipp][ip] = cohort.bd[ip].y_v2a.rm[ipp];
            }
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, start5, count5, &rm[0][0]) ); 
      }
      //PFT only
      else if(curr_spec.pft && !curr_spec.compartment){

        double rm[NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          if(curr_spec.monthly){
            PFTstart4[0] = month_timestep;
            rm[ip] = cohort.bd[ip].m_v2a.rmall;
          }
          else if(curr_spec.yearly){
            PFTstart4[0] = year;
            rm[ip] = cohort.bd[ip].y_v2a.rmall;
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &rm[0]) ); 
      }
      //Compartment only
      else if(!curr_spec.pft && curr_spec.compartment){

        double rm[NUM_PFT_PART] = {0};
        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){
            if(curr_spec.monthly){
              CompStart4[0] = month_timestep;
              rm[ipp] += cohort.bd[ip].m_v2a.rm[ipp];
            }
            else if(curr_spec.yearly){
              CompStart4[0] = year;
              rm[ipp] += cohort.bd[ip].y_v2a.rm[ipp];
            }
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, CompStart4, CompCount4, &rm[0]) );
   
      }
      //Neither PFT nor compartment - Total
      else if(!curr_spec.pft && !curr_spec.compartment){

        double rm;
        if(curr_spec.monthly){
          start3[0] = month_timestep;
          rm = cohort.bdall->m_v2a.rmall;
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          rm = cohort.bdall->y_v2a.rmall;
        }

        temutil::nc( nc_put_var1_double(ncid, cv, start3, &rm) );
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputRM)
  }//end RM
  map_itr = netcdf_outputs.end();


  //VEGC
  map_itr = netcdf_outputs.find("VEGC");
 if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: VEGC";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputVEGC)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "VEGC", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "VEGC", &cv) );
#endif

      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){
        double vegc[NUM_PFT_PART][NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          if(cohort.cd.m_veg.vegcov[ip]>0.){//only check PFTs that exist

            for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
              if(curr_spec.monthly){
                start5[0] = month_timestep;
                vegc[ipp][ip] = cohort.bd[ip].m_vegs.c[ipp];
              }
              else if(curr_spec.yearly){
                start5[0] = year;
                vegc[ipp][ip] = cohort.bd[ip].y_vegs.c[ipp];
              }
            }

          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, start5, count5, &vegc[0][0]) );
      }
      //PFT only
      else if(curr_spec.pft && !curr_spec.compartment){

        double vegc[NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          if(cohort.cd.m_veg.vegcov[ip]>0.){//only check PFTs that exist

            if(curr_spec.monthly){
              PFTstart4[0] = month_timestep;
              vegc[ip] = cohort.bd[ip].m_vegs.call;
            }
            else if(curr_spec.yearly){
              PFTstart4[0] = year;
              vegc[ip] = cohort.bd[ip].y_vegs.call;
            }

          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &vegc[0]) );
      }
      //Compartment only
      else if(!curr_spec.pft && curr_spec.compartment){

        double vegc[NUM_PFT_PART] = {0};
        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){
            if(cohort.cd.m_veg.vegcov[ip]>0.){//only check PFTs that exist

              if(curr_spec.monthly){
                CompStart4[0] = month_timestep;
                vegc[ipp] += cohort.bd[ip].m_vegs.c[ipp];
              }
              else if(curr_spec.yearly){
                CompStart4[0] = year;
                vegc[ipp] += cohort.bd[ip].y_vegs.c[ipp];
              }

            }
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, CompStart4, CompCount4, &vegc[0]) );
      }
      //Neither PFT nor compartment
      else if(!curr_spec.pft && !curr_spec.compartment){

        double vegc;
        if(curr_spec.monthly){
          start3[0] = month_timestep;
          vegc = cohort.bdall->m_vegs.call;
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          vegc = cohort.bdall->y_vegs.call;
        }

        temutil::nc( nc_put_var1_double(ncid, cv, start3, &vegc) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputVEGC)
  }//end VEGC
  map_itr = netcdf_outputs.end();


  //VEGN
  map_itr = netcdf_outputs.find("VEGN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: VEGN";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputVEGN)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "VEGN", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "VEGN", &cv) );
#endif

      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){

        double vegn[NUM_PFT_PART][NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          if(cohort.cd.m_veg.vegcov[ip]>0.){//only check PFTs that exist

            for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
              if(curr_spec.monthly){
                start5[0] = month_timestep;
                vegn[ipp][ip] = cohort.bd[ip].m_vegs.strn[ipp];
              }
              else if(curr_spec.yearly){
                start5[0] = year;
                vegn[ipp][ip] = cohort.bd[ip].y_vegs.strn[ipp];
              }
            }

          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, start5, count5, &vegn[0][0]) );
      }
      //PFT only
      else if(curr_spec.pft && !curr_spec.compartment){

        double vegn[NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          if(cohort.cd.m_veg.vegcov[ip]>0.){//only check PFTs that exist

            if(curr_spec.monthly){
              PFTstart4[0] = month_timestep;
              vegn[ip] = cohort.bd[ip].m_vegs.strnall;
            }
            else if(curr_spec.yearly){
              PFTstart4[0] = year;
              vegn[ip] = cohort.bd[ip].y_vegs.strnall;
            }

          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &vegn[0]) );
      }
      //Compartment only
      else if(!curr_spec.pft && curr_spec.compartment){

        double vegn[NUM_PFT_PART] = {0};
        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){
            if(cohort.cd.m_veg.vegcov[ip]>0.){//only check PFTs that exist

              if(curr_spec.monthly){
                CompStart4[0] = month_timestep;
                vegn[ipp] += cohort.bd[ip].m_vegs.strn[ipp];
              }
              else if(curr_spec.yearly){
                CompStart4[0] = year;
                vegn[ipp] += cohort.bd[ip].y_vegs.strn[ipp];
              }

            }
          }
        }

        temutil::nc( nc_put_vara_double(ncid, cv, CompStart4, CompCount4, &vegn[0]) );
      }
      //Neither PFT nor compartment
      else if(!curr_spec.pft && !curr_spec.compartment){

        double vegn;
        if(curr_spec.monthly){
          start3[0] = month_timestep;
          vegn = cohort.bdall->m_vegs.nall;
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          vegn = cohort.bdall->y_vegs.nall;
        }

        temutil::nc( nc_put_var1_double(ncid, cv, start3, &vegn) );
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputVEGN)
  }//end VEGN
  map_itr = netcdf_outputs.end();


  /*** Six combination vars: (year,month,day)x(PFT,total) ***/

  //EET
  map_itr = netcdf_outputs.find("EET");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: EET";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputEET)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "EET", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "EET", &cv) );
#endif

      //PFT
      if(curr_spec.pft){

        if(curr_spec.daily){
          PFTstart4[0] = day_timestep;
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
          PFTstart4[0] = month_timestep;
          double EET[NUM_PFT];
          for(int ip=0; ip<NUM_PFT; ip++){
            EET[ip] = cohort.ed[ip].m_l2a.eet;
          }

          temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &EET[0]) );
        }
        else if(curr_spec.yearly){
          PFTstart4[0] = year;
          double EET[NUM_PFT];
          for(int ip=0; ip<NUM_PFT; ip++){
            EET[ip] = cohort.ed[ip].y_l2a.eet;
          }

          temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &EET[0]) );
        }
      }
      //Not PFT. Total
      else if(!curr_spec.pft){

        if(curr_spec.daily){
          start3[0] = day_timestep;
          double eet[31] = {0};
          for(int ii=0; ii<31; ii++){
            for(int ip=0; ip<NUM_PFT; ip++){
              eet[ii] += cohort.ed[ip].daily_eet[ii];
            }
          }
          temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &eet[0]) );
        }
        else if(curr_spec.monthly){
          start3[0] = month_timestep;
          double eet = cohort.edall->m_l2a.eet;
          temutil::nc( nc_put_var1_double(ncid, cv, start3, &eet) );
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          double eet = cohort.edall->y_l2a.eet;
          temutil::nc( nc_put_var1_double(ncid, cv, start3, &eet) );
        }
      }
      temutil::nc( nc_close(ncid) );
    }//end critical(outputEET)
  }//end EET
  map_itr = netcdf_outputs.end();


  //PET
  map_itr = netcdf_outputs.find("PET");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: PET";
    curr_spec = map_itr->second;
    curr_filename = curr_spec.file_path + curr_spec.filename_prefix + file_stage_suffix;

    #pragma omp critical(outputPET)
    {
#ifdef WITHMPI
      temutil::nc( nc_open_par(curr_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "PET", &cv) );
      temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
      temutil::nc( nc_open(curr_filename.c_str(), NC_WRITE, &ncid) );
      temutil::nc( nc_inq_varid(ncid, "PET", &cv) );
#endif

      //PFT
      if(curr_spec.pft){

        if(curr_spec.daily){
          PFTstart4[0] = day_timestep;
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
          PFTstart4[0] = month_timestep;
          double PET[NUM_PFT];
          for(int ip=0; ip<NUM_PFT; ip++){
            PET[ip] = cohort.ed[ip].m_l2a.pet;
          }

          temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &PET[0]) );
        }
        else if(curr_spec.yearly){
          PFTstart4[0] = year;
          double PET[NUM_PFT];
          for(int ip=0; ip<NUM_PFT; ip++){
            PET[ip] = cohort.ed[ip].y_l2a.pet;
          }

          temutil::nc( nc_put_vara_double(ncid, cv, PFTstart4, PFTcount4, &PET[0]) );
        }
      }
      //Not PFT. Total
      else if(!curr_spec.pft){

        if(curr_spec.daily){
          start3[0] = day_timestep;
          double pet[31] = {0};
          for(int ii=0; ii<31; ii++){
            for(int ip=0; ip<NUM_PFT; ip++){
              pet[ii] += cohort.ed[ip].daily_pet[ii];
            }
          }
          temutil::nc( nc_put_vara_double(ncid, cv, start3, count3, &pet[0]) );
        }
        else if(curr_spec.monthly){
          start3[0] = month_timestep;
          double pet = cohort.edall->m_l2a.pet;
          temutil::nc( nc_put_var1_double(ncid, cv, start3, &pet) );
        }
        else if(curr_spec.yearly){
          start3[0] = year;
          double pet = cohort.edall->y_l2a.pet;
          temutil::nc( nc_put_var1_double(ncid, cv, start3, &pet) );
        }
      }

      temutil::nc( nc_close(ncid) );
    }//end critical(outputPET)
  }//end PET
  map_itr = netcdf_outputs.end();

}


