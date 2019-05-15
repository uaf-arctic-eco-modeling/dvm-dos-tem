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

#ifdef WITHMPI
  temutil::nc( nc_open_par(output_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
  temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
  temutil::nc( nc_open(output_filename.c_str(), NC_WRITE, &ncid) );
#endif

  temutil::nc( nc_inq_varid(ncid, out_spec->var_name.c_str(), &cv) );
  BOOST_LOG_SEV(glg, debug)<<"inq_varid completed";

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

#ifdef WITHMPI
  temutil::nc( nc_open_par(output_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
  temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
  temutil::nc( nc_open(output_filename.c_str(), NC_WRITE, &ncid) );
#endif

  temutil::nc( nc_inq_varid(ncid, out_spec->var_name.c_str(), &cv) );

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

#ifdef WITHMPI
  temutil::nc( nc_open_par(output_filename.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
  temutil::nc( nc_var_par_access(ncid, cv, NC_INDEPENDENT) );
#else
  temutil::nc( nc_open(output_filename.c_str(), NC_WRITE, &ncid) );
#endif

  temutil::nc( nc_inq_varid(ncid, out_spec->var_name.c_str(), &cv) );

  temutil::nc( nc_put_vara(ncid, cv, datastart, datacount, data) );

  temutil::nc( nc_close(ncid) );
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
  std::map<std::string, OutputSpec>::iterator map_itr;

  //ALD
  map_itr = netcdf_outputs.find("ALD");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: ALD";
    curr_spec = map_itr->second;

    #pragma omp critical(outputALD)
    {
      output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.ald, 1, year, 1);
    }//end critical(outputALD)
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
        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_sois.avln[0], MAX_SOI_LAY, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_sois.avln[0], MAX_SOI_LAY, year, 1);
        }
      }
      //Total
      else if(!curr_spec.layer){

        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_soid.avlnsum, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_soid.avlnsum, 1, year, 1);
        }
      }
    }//end critical(outputAVLN)
  }//end AVLN
  map_itr = netcdf_outputs.end();


  map_itr = netcdf_outputs.find("BURNAIR2SOIN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNAIR2SOIN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputBURNAIR2SOIN)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.year_fd[month].fire_a2soi.orgn, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        double burnair2soin = 0.;
        for(int im=0; im<12; im++){
          burnair2soin += cohort.year_fd[im].fire_a2soi.orgn;
        }
        output_nc_3dim(&curr_spec, file_stage_suffix, &burnair2soin, 1, year, 1);
      }
    }//end critical(outputBURNAIR2SOIN)
  }//end BURNAIR2SOIN
  map_itr = netcdf_outputs.end();


  //Burned soil carbon
  map_itr = netcdf_outputs.find("BURNSOIC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNSOIC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputBURNSOIC)
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
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.year_fd[month].fire_soi2a.orgc, 1, month_timestep, 1);
        }
        else if(curr_spec.yearly){
          double burnsoilC = 0.;
          for(int im=0; im<12; im++){
            burnsoilC += cohort.year_fd[im].fire_soi2a.orgc;
          }
          output_nc_3dim(&curr_spec, file_stage_suffix, &burnsoilC, 1, year, 1);
        }
      }
    }//end critical(outputBURNSOIC)
  }//end BURNSOIC
  map_itr = netcdf_outputs.end();


  //Burned soil nitrogen 
  map_itr = netcdf_outputs.find("BURNSOILN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNSOILN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputBURNSOILN)
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
    }//end critical(outputBURNSOILN)
  }//end BURNSOILN
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
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.year_fd[month].fire_soid.burnthick, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        double burnthick = 0.;
        for(int im=0; im<12; im++){
          burnthick += cohort.year_fd[im].fire_soid.burnthick;
        }
        output_nc_3dim(&curr_spec, file_stage_suffix, &burnthick, 1, year, 1);
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
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.year_fd[month].fire_v2a.orgc, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.fd->fire_v2a.orgc, 1, year, 1);
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
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.year_fd[month].fire_v2dead.vegC, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.fd->fire_v2dead.vegC, 1, year, 1);
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


  //BURNVEG2SOIABVC
  map_itr = netcdf_outputs.find("BURNVEG2SOIABVC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNVEG2SOIABVC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputBURNVEG2SOIABVC)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.year_fd[month].fire_v2soi.abvc, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.fd->fire_v2soi.abvc, 1, year, 1);
      }
    }//end critical(outputBURNVEG2SOIABVC)
  }//end BURNVEG2SOIABVC
  map_itr = netcdf_outputs.end();


  //BURNVEG2SOIABVN
  map_itr = netcdf_outputs.find("BURNVEG2SOIABVN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNVEG2SOIABVN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputBURNVEG2SOIABVN)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.year_fd[month].fire_v2soi.abvn, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.fd->fire_v2soi.abvn, 1, year, 1);
      }
    }//end critical(outputBURNVEG2SOIABVN)
  }//end BURNVEG2SOIABVN
  map_itr = netcdf_outputs.end();


  //BURNVEG2SOIBLWC
  map_itr = netcdf_outputs.find("BURNVEG2SOIBLWC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNVEG2SOIBLWC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputBURNVEG2SOIBLWC)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.year_fd[month].fire_v2soi.blwc, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.fd->fire_v2soi.blwc, 1, year, 1);
      }
    }//end critical(outputBURNVEG2SOIBLWC)
  }//end BURNVEG2SOIBLWC
  map_itr = netcdf_outputs.end();


  //BURNVEG2SOIBLWN
  map_itr = netcdf_outputs.find("BURNVEG2SOIBLWN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: BURNVEG2SOIBLWN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputBURNVEG2SOIBLWN)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.year_fd[month].fire_v2soi.blwn, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.fd->fire_v2soi.blwn, 1, year, 1);
      }
    }//end critical(outputBURNVEG2SOIBLWN)
  }//end BURNVEG2SOIBLWN
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
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_vegs.deadc, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_vegs.deadc, 1, year, 1);
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
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_soid.deepc, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_soid.deepc, 1, year, 1);
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

      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.climate.nirr_d[doy], 1, day_timestep, dinm);
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
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.climate.rain_d[doy], 1, day_timestep, dinm);
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
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.climate.snow_d[doy], 1, day_timestep, dinm);
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

      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.climate.tair_d[doy], 1, day_timestep, dinm);
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

      if(curr_spec.daily){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.climate.vapo_d[doy], 1, day_timestep, dinm);
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
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_sois.wdebrisc, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_sois.wdebrisc, 1, year, 1);
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
      //By PFT
      if(curr_spec.pft){

        double m_EET[NUM_PFT], y_EET[NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          m_EET[ip] = cohort.ed[ip].m_l2a.eet;
          y_EET[ip] = cohort.ed[ip].y_l2a.eet;
        }

        //daily
        if(curr_spec.daily){

          double d_EET[dinm][NUM_PFT];
          for(int ip=0; ip<NUM_PFT; ip++){
            for(int id=0; id<dinm; id++){
              d_EET[id][ip] = cohort.ed[ip].daily_eet[id];
            }
          }

          output_nc_4dim(&curr_spec, file_stage_suffix, &d_EET[0][0], NUM_PFT, day_timestep, dinm);
        }
        //monthly
        else if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_EET[0], NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_EET[0], NUM_PFT, year, 1);
        }
      }
      //Total, instead of by PFT
      else if(!curr_spec.pft){
        //daily
        if(curr_spec.daily){
          double eet[31] = {0};
          for(int ii=0; ii<31; ii++){
            for(int ip=0; ip<NUM_PFT; ip++){
              eet[ii] += cohort.ed[ip].daily_eet[ii];
            }
          }
          output_nc_3dim(&curr_spec, file_stage_suffix, &eet[0], 1, day_timestep, dinm);
        }
        //monthly
        else if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_l2a.eet, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_l2a.eet, 1, year, 1);
        }
      }
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

        double m_gpp[NUM_PFT_PART][NUM_PFT];
        double y_gpp[NUM_PFT_PART][NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            m_gpp[ipp][ip] = cohort.bd[ip].m_a2v.gpp[ipp];
            y_gpp[ipp][ip] = cohort.bd[ip].y_a2v.gpp[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &m_gpp[0][0], NUM_PFT_PART, NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &y_gpp[0][0], NUM_PFT_PART, NUM_PFT, year, 1);
        }
      }
      //PFT only (4 dimensions)
      else if(curr_spec.pft && !curr_spec.compartment){

        double m_gpp[NUM_PFT], y_gpp[NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          m_gpp[ip] = cohort.bd[ip].m_a2v.gppall;
          y_gpp[ip] = cohort.bd[ip].y_a2v.gppall;
        }

        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_gpp[0], NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_gpp[0], NUM_PFT, year, 1);
        }
      }
      //Compartment only (4 dimensions)
      else if(!curr_spec.pft && curr_spec.compartment){

        double m_gpp[NUM_PFT_PART] = {0};
        double y_gpp[NUM_PFT_PART] = {0};
        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){

            m_gpp[ipp] += cohort.bd[ip].m_a2v.gpp[ipp];
            y_gpp[ipp] += cohort.bd[ip].y_a2v.gpp[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_gpp[0], NUM_PFT_PART, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_gpp[0], NUM_PFT_PART, year, 1);
        }
      }
      //Neither PFT nor Compartment - total instead (3 dimensions)
      else if(!curr_spec.pft && !curr_spec.compartment){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_a2v.gppall, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_a2v.gppall, 1, year, 1);
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
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: INGPP";
    curr_spec = map_itr->second;

    #pragma omp critical(outputINGPP)
    {
      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){

        double m_ingpp[NUM_PFT_PART][NUM_PFT];
        double y_ingpp[NUM_PFT_PART][NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            m_ingpp[ipp][ip] = cohort.bd[ip].m_a2v.ingpp[ipp];
            y_ingpp[ipp][ip] = cohort.bd[ip].y_a2v.ingpp[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &m_ingpp[0][0], NUM_PFT_PART, NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &y_ingpp[0][0], NUM_PFT_PART, NUM_PFT, year, 1);
        }

      }
      //PFT only (4 dimensions)
      else if(curr_spec.pft && !curr_spec.compartment){

        double m_ingpp[NUM_PFT], y_ingpp[NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          m_ingpp[ip] = cohort.bd[ip].m_a2v.ingppall;
          y_ingpp[ip] = cohort.bd[ip].y_a2v.ingppall;
        }

        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_ingpp[0], NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_ingpp[0], NUM_PFT, year, 1);
        }

      }
      //Compartment only (4 dimensions)
      else if(!curr_spec.pft && curr_spec.compartment){

        double m_ingpp[NUM_PFT_PART] = {0};
        double y_ingpp[NUM_PFT_PART] = {0};

        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){
            m_ingpp[ipp] += cohort.bd[ip].m_a2v.ingpp[ipp];
            y_ingpp[ipp] += cohort.bd[ip].y_a2v.ingpp[ipp];
          }
        }

        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_ingpp[0], NUM_PFT_PART, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_ingpp[0], NUM_PFT_PART, year, 1);
        }

      }
      //Neither PFT nor Compartment - total instead
      else if(!curr_spec.pft && !curr_spec.compartment){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_a2v.ingppall, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_a2v.ingppall, 1, year, 1);
        }

      }
    }//end critical(outputINGPP)
  }//end INGPP
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

        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.cd.m_veg.lai[0], NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.cd.y_veg.lai[0], NUM_PFT, year, 1);
        }

      }
      //Total
      else if(!curr_spec.pft){

        double m_lai = 0., y_lai = 0.;
        for(int ip=0; ip<NUM_PFT; ip++){
          if(cohort.cd.m_veg.vegcov[ip]>0.){
            m_lai += cohort.cd.m_veg.lai[ip];
            y_lai += cohort.cd.y_veg.lai[ip];
          }
        }
        //monthly 
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &m_lai, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &y_lai, 1, year, 1);
        }
      }
    }//end critical(outputLAI)
  }//end LAI
  map_itr = netcdf_outputs.end();


  //LATERALDRAINAGE
  map_itr = netcdf_outputs.find("LATERALDRAINAGE");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LATERALDRAINAGE";
    curr_spec = map_itr->second;

    #pragma omp critical(outputLATERALDRAINAGE)
    {
      //daily
      if(curr_spec.daily){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_layer_drain[0][0], MAX_SOI_LAY, day_timestep, dinm);
      }
    }//end critical(outputLATERALDRAINAGE)
  }//end LATERALDRAINAGE 
  map_itr = netcdf_outputs.end();


  //LAYERDEPTH
  map_itr = netcdf_outputs.find("LAYERDEPTH");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LAYERDEPTH";
    curr_spec = map_itr->second;

    #pragma omp critical(outputLAYERDEPTH)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.cd.m_soil.z[0], MAX_SOI_LAY, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.cd.y_soil.z[0], MAX_SOI_LAY, year, 1);
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
      //monthly
      if(curr_spec.monthly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.cd.m_soil.dz[0], MAX_SOI_LAY, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.cd.y_soil.dz[0], MAX_SOI_LAY, year, 1);
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
      //monthly
      if(curr_spec.monthly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.cd.m_soil.type[0], MAX_SOI_LAY, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.cd.y_soil.type[0], MAX_SOI_LAY, year, 1);
      }
    }//end critical(outputLAYERTYPE)
  }//end LAYERTYPE 
  map_itr = netcdf_outputs.end();


  //LTRFALC
  map_itr = netcdf_outputs.find("LTRFALC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LTRFALC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputLTRFALC)
    {
      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){

        double m_ltrfalc[NUM_PFT_PART][NUM_PFT];
        double y_ltrfalc[NUM_PFT_PART][NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            m_ltrfalc[ipp][ip] = cohort.bd[ip].m_v2soi.ltrfalc[ipp];
            y_ltrfalc[ipp][ip] = cohort.bd[ip].y_v2soi.ltrfalc[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &m_ltrfalc[0][0], NUM_PFT_PART, NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &y_ltrfalc[0][0], NUM_PFT_PART, NUM_PFT, year, 1);
        }
      }
      //PFT only (4 dimensions)
      else if(curr_spec.pft && !curr_spec.compartment){

        double y_ltrfalc[NUM_PFT], m_ltrfalc[NUM_PFT];

        for(int ip=0; ip<NUM_PFT; ip++){
          m_ltrfalc[ip] = cohort.bd[ip].m_v2soi.ltrfalcall;
          y_ltrfalc[ip] = cohort.bd[ip].y_v2soi.ltrfalcall;
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_ltrfalc[0], NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_ltrfalc[0], NUM_PFT, year, 1);
        }
      }
      //Compartment only (4 dimensions)
      else if(!curr_spec.pft && curr_spec.compartment){

        double y_ltrfalc[NUM_PFT_PART] = {0};
        double m_ltrfalc[NUM_PFT_PART] = {0};

        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            m_ltrfalc[ipp] += cohort.bd[ip].m_v2soi.ltrfalc[ipp];
            y_ltrfalc[ipp] += cohort.bd[ip].y_v2soi.ltrfalc[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_ltrfalc[0], NUM_PFT_PART, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_ltrfalc[0], NUM_PFT_PART, year, 1);
        }
      }
      //Neither PFT nor compartment - totals
      else if(!curr_spec.pft && !curr_spec.compartment){

        double m_ltrfalc = 0., y_ltrfalc = 0.;
        for(int ip=0; ip<NUM_PFT; ip++){
          m_ltrfalc += cohort.bd[ip].m_v2soi.ltrfalcall;
          y_ltrfalc += cohort.bd[ip].y_v2soi.ltrfalcall;
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &m_ltrfalc, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &y_ltrfalc, 1, year, 1);
        }
      }
    }//end critical(outputLTRFALC)
  }//end LTRFALC
  map_itr = netcdf_outputs.end();


  //LTRFALN
  map_itr = netcdf_outputs.find("LTRFALN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LTRFALN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputLTRFALN)
    {
      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){

        double m_ltrfaln[NUM_PFT_PART][NUM_PFT];
        double y_ltrfaln[NUM_PFT_PART][NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            m_ltrfaln[ipp][ip] = cohort.bd[ip].m_v2soi.ltrfaln[ipp];
            y_ltrfaln[ipp][ip] = cohort.bd[ip].y_v2soi.ltrfaln[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &m_ltrfaln[0][0], NUM_PFT_PART, NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &y_ltrfaln[0][0], NUM_PFT_PART, NUM_PFT, year, 1);
        }
      }
      //PFT only (4 dimensions)
      else if(curr_spec.pft && !curr_spec.compartment){

        double m_ltrfaln[NUM_PFT], y_ltrfaln[NUM_PFT];

        for(int ip=0; ip<NUM_PFT; ip++){
          m_ltrfaln[ip] = cohort.bd[ip].m_v2soi.ltrfalnall;
          y_ltrfaln[ip] = cohort.bd[ip].y_v2soi.ltrfalnall;
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_ltrfaln[0], NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_ltrfaln[0], NUM_PFT, year, 1);
        }
      }
      //Compartment only (4 dimensions)
      else if(!curr_spec.pft && curr_spec.compartment){

        double m_ltrfaln[NUM_PFT_PART] = {0};
        double y_ltrfaln[NUM_PFT_PART] = {0};

        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            m_ltrfaln[ipp] += cohort.bd[ip].m_v2soi.ltrfaln[ipp];
            y_ltrfaln[ipp] += cohort.bd[ip].y_v2soi.ltrfaln[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_ltrfaln[0], NUM_PFT_PART, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_ltrfaln[0], NUM_PFT_PART, year, 1);
        }
      }
      //Neither PFT nor compartment - totals
      else if(!curr_spec.pft && !curr_spec.compartment){

        double m_ltrfaln = 0., y_ltrfaln = 0.;
        for(int ip=0; ip<NUM_PFT; ip++){
          m_ltrfaln += cohort.bd[ip].m_v2soi.ltrfalnall;
          y_ltrfaln += cohort.bd[ip].y_v2soi.ltrfalnall;
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &m_ltrfaln, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &y_ltrfaln, 1, year, 1);
        }
      }
    }//end critical(outputLTRFALN)
  }//end LTRFALN
  map_itr = netcdf_outputs.end();


  //LWCLAYER
  map_itr = netcdf_outputs.find("LWCLAYER");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: LWCLAYER";
    curr_spec = map_itr->second;
    #pragma omp critical(outputLWCLAYER)
    {
      if(curr_spec.monthly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.lwc[0], MAX_SOI_LAY, month_timestep, 1);
      }
      else if(curr_spec.yearly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.lwc[0], MAX_SOI_LAY, year, 1);
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
        output_nc_3dim(&curr_spec, file_stage_suffix, &minec, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        minec = cohort.bdall->y_soid.mineac
                + cohort.bdall->y_soid.minebc
                + cohort.bdall->y_soid.minecc;
        output_nc_3dim(&curr_spec, file_stage_suffix, &minec, 1, year, 1);
      }
    }//end critical(outputMINEC)
  }//end MINEC
  map_itr = netcdf_outputs.end();


  //MOSSDEATHC
  map_itr = netcdf_outputs.find("MOSSDEATHC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: MOSSDEATHC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputMOSSDEATHC)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_v2soi.mossdeathc, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_v2soi.mossdeathc, 1, year, 1);
      }
    }//end critical(outputMOSSDEATHC)
  }//end MOSSDEATHC
  map_itr = netcdf_outputs.end();


  //MOSSDEATHN
  map_itr = netcdf_outputs.find("MOSSDEATHN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: MOSSDEATHN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputMOSSDEATHN)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_v2soi.mossdeathn, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_v2soi.mossdeathn, 1, year, 1);
      }
    }//end critical(outputMOSSDEATHN)
  }//end MOSSDEATHN
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
      output_nc_3dim(&curr_spec, file_stage_suffix, &mossdz, 1, year, 1);
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

        double m_npp[NUM_PFT_PART][NUM_PFT];
        double y_npp[NUM_PFT_PART][NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            m_npp[ipp][ip] = cohort.bd[ip].m_a2v.npp[ipp];
            y_npp[ipp][ip] = cohort.bd[ip].y_a2v.npp[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &m_npp[0][0], NUM_PFT_PART, NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &y_npp[0][0], NUM_PFT_PART, NUM_PFT, year, 1);
        }
      }
      //PFT only (4 dimensions)
      else if(curr_spec.pft && !curr_spec.compartment){

        double m_npp[NUM_PFT], y_npp[NUM_PFT];

        for(int ip=0; ip<NUM_PFT; ip++){
          m_npp[ip] = cohort.bd[ip].m_a2v.nppall;
          y_npp[ip] = cohort.bd[ip].y_a2v.nppall;
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_npp[0], NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_npp[0], NUM_PFT, year, 1);
        }
      }
      //Compartment only (4 dimensions)
      else if(!curr_spec.pft && curr_spec.compartment){

        double m_npp[NUM_PFT_PART] = {0};
        double y_npp[NUM_PFT_PART] = {0};

        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){
            m_npp[ipp] += cohort.bd[ip].m_a2v.npp[ipp];
            y_npp[ipp] += cohort.bd[ip].y_a2v.npp[ipp];
          }
        }
        //monthly 
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_npp[0], NUM_PFT_PART, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_npp[0], NUM_PFT_PART, year, 1);
        }
      }
      //Neither PFT nor Compartment - total instead
      else if(!curr_spec.pft && !curr_spec.compartment){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_a2v.nppall, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_a2v.nppall, 1, year, 1);
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

        double orgn[MAX_SOI_LAY] = {0};
        int il = 0;
        Layer* currL = this->cohort.ground.toplayer;
        while(currL != NULL){
          orgn[il] = currL->orgn;
          il++;
          currL = currL->nextl;
        }

        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &orgn[0], MAX_SOI_LAY, month_timestep, 1);
        }
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &orgn[0], MAX_SOI_LAY, year, 1);
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
      //By PFT
      if(curr_spec.pft){

        double m_PET[NUM_PFT], y_PET[NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          m_PET[ip] = cohort.ed[ip].m_l2a.pet;
          y_PET[ip] = cohort.ed[ip].y_l2a.pet;
        }
        //daily
        if(curr_spec.daily){

          double d_PET[dinm][NUM_PFT];
          for(int ip=0; ip<NUM_PFT; ip++){
            for(int id=0; id<dinm; id++){
              d_PET[id][ip] = cohort.ed[ip].daily_pet[id];
            }
          }

          output_nc_4dim(&curr_spec, file_stage_suffix, &d_PET[0], NUM_PFT, day_timestep, dinm);
        }
        //monthly
        else if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_PET[0], NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_PET[0], NUM_PFT, year, 1);
        }
      }
      //Total, instead of by PFT
      else if(!curr_spec.pft){

        if(curr_spec.daily){
          double pet[31] = {0};
          for(int ii=0; ii<31; ii++){
            for(int ip=0; ip<NUM_PFT; ip++){
              pet[ii] += cohort.ed[ip].daily_pet[ii];
            }
          }
          output_nc_3dim(&curr_spec, file_stage_suffix, &pet[0], 1, day_timestep, dinm);
        }
        //monthly
        else if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_l2a.pet, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_l2a.pet, 1, year, 1);
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
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_qdrain[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soi2l.qdrain, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soi2l.qdrain, 1, year, 1);
      }
    }//end critical(outputQDRAINAGE)
  }//end QDRAINAGE 
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
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_qinfl[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soi2l.qinfl, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soi2l.qinfl, 1, year, 1);
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
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_qover[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soi2l.qover, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soi2l.qover, 1, year, 1);
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


  //RG
  map_itr = netcdf_outputs.find("RG");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: RG";
    curr_spec = map_itr->second;

    #pragma omp critical(outputRG)
    {
      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){

        double m_rg[NUM_PFT_PART][NUM_PFT], y_rg[NUM_PFT_PART][NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            m_rg[ipp][ip] = cohort.bd[ip].m_v2a.rg[ipp];
            y_rg[ipp][ip] = cohort.bd[ip].y_v2a.rg[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &m_rg[0][0], NUM_PFT_PART, NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &y_rg[0][0], NUM_PFT_PART, NUM_PFT, year, 1);
        }
      }
      //PFT only (4 dimensions)
      else if(curr_spec.pft && !curr_spec.compartment){

        double m_rg[NUM_PFT], y_rg[NUM_PFT];

        for(int ip=0; ip<NUM_PFT; ip++){
            m_rg[ip] = cohort.bd[ip].m_v2a.rgall;
            y_rg[ip] = cohort.bd[ip].y_v2a.rgall;
        }

        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_rg[0], NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_rg[0], NUM_PFT, year, 1);
        }
      }
      //Compartment only (4 dimensions)
      else if(!curr_spec.pft && curr_spec.compartment){

        double m_rg[NUM_PFT_PART] = {0};
        double y_rg[NUM_PFT_PART] = {0};

        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){
            m_rg[ipp] += cohort.bd[ip].m_v2a.rg[ipp];
            y_rg[ipp] += cohort.bd[ip].y_v2a.rg[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_rg[0], NUM_PFT_PART, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_rg[0], NUM_PFT_PART, year, 1);
        }
      }
      //Neither PFT nor compartment - Total
      else if(!curr_spec.pft && !curr_spec.compartment){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_v2a.rgall, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_v2a.rgall, 1, year, 1);
        }
      }
    }//end critical(outputRG)
  }//end RG
  map_itr = netcdf_outputs.end();


  //RH
  map_itr = netcdf_outputs.find("RH");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: RH";
    curr_spec = map_itr->second;

    #pragma omp critical(outputRH)
    {
      //By layer
      if(curr_spec.layer){

        double rh[MAX_SOI_LAY];
        //monthly
        if(curr_spec.monthly){
          for(int il=0; il<MAX_SOI_LAY; il++){
            rh[il] = cohort.bdall->m_soi2a.rhrawc[il]
                   + cohort.bdall->m_soi2a.rhsoma[il]
                   + cohort.bdall->m_soi2a.rhsompr[il]
                   + cohort.bdall->m_soi2a.rhsomcr[il];
          }
          output_nc_4dim(&curr_spec, file_stage_suffix, &rh[0], MAX_SOI_LAY, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          for(int il=0; il<MAX_SOI_LAY; il++){
            rh[il] = cohort.bdall->y_soi2a.rhrawc[il]
                   + cohort.bdall->y_soi2a.rhsoma[il]
                   + cohort.bdall->y_soi2a.rhsompr[il]
                   + cohort.bdall->y_soi2a.rhsomcr[il];
          }
          output_nc_4dim(&curr_spec, file_stage_suffix, &rh[0], MAX_SOI_LAY, year, 1);
        }
      }
      //Total, instead of by layer
      else if(!curr_spec.layer){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_soi2a.rhtot, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_soi2a.rhtot, 1, year, 1);
        }
      }
    }//end critical(outputRH)
  }//end RH 
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

        double m_rm[NUM_PFT_PART][NUM_PFT], y_rm[NUM_PFT_PART][NUM_PFT];
        for(int ip=0; ip<NUM_PFT; ip++){
          for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
            m_rm[ipp][ip] = cohort.bd[ip].m_v2a.rm[ipp];
            y_rm[ipp][ip] = cohort.bd[ip].y_v2a.rm[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &m_rm[0][0], NUM_PFT_PART, NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &y_rm[0][0], NUM_PFT_PART, NUM_PFT, year, 1);
        }
      }
      //PFT only (4 dimensions)
      else if(curr_spec.pft && !curr_spec.compartment){

        double m_rm[NUM_PFT], y_rm[NUM_PFT];

        for(int ip=0; ip<NUM_PFT; ip++){
          m_rm[ip] = cohort.bd[ip].m_v2a.rmall;
          y_rm[ip] = cohort.bd[ip].y_v2a.rmall;
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_rm[0], NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_rm[0], NUM_PFT, year, 1);
        }
      }
      //Compartment only (4 dimensions)
      else if(!curr_spec.pft && curr_spec.compartment){

        double m_rm[NUM_PFT_PART] = {0};
        double y_rm[NUM_PFT_PART] = {0};
        for(int ipp=0; ipp<NUM_PFT_PART; ipp++){
          for(int ip=0; ip<NUM_PFT; ip++){
            m_rm[ipp] += cohort.bd[ip].m_v2a.rm[ipp];
            y_rm[ipp] += cohort.bd[ip].y_v2a.rm[ipp];
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_rm[0], NUM_PFT_PART, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_rm[0], NUM_PFT_PART, year, 1);
        }
      }
      //Neither PFT nor compartment - Total
      else if(!curr_spec.pft && !curr_spec.compartment){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_v2a.rmall, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_v2a.rmall, 1, year, 1);
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
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_soid.shlwc, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_soid.shlwc, 1, year, 1);
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
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_snowthick[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &snowthick, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &snowthick, 1, year, 1);
      }
    }//end critical(outputSNOWTHICK)
  }//end SNOWTHICK
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

        double soilc[MAX_SOI_LAY];
        int il = 0;
        Layer* currL = this->cohort.ground.toplayer;
        while(currL != NULL){
          soilc[il] = currL->soma;
          il++;
          currL = currL->nextl;
        }

        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &soilc[0], MAX_SOI_LAY, month_timestep, 1);
        }
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &soilc[0], MAX_SOI_LAY, year, 1);
        }
      }
      //Total, instead of by layer
      else if(!curr_spec.layer){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_soid.somasum, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_soid.somasum, 1, year, 1);
        }

      }
    }//end critical(outputSOMA)
  }//end SOMA
  map_itr = netcdf_outputs.end();


  //SOMCR - soil organic matter, chemically resistant
  map_itr = netcdf_outputs.find("SOMCR");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: SOMCR";
    curr_spec = map_itr->second;

    #pragma omp critical(outputSOMCR)
    {
      //By layer
      if(curr_spec.layer){

        double soilc[MAX_SOI_LAY];
        int il = 0;
        Layer* currL = this->cohort.ground.toplayer;
        while(currL != NULL){
          soilc[il] = currL->somcr;
          il++;
          currL = currL->nextl;
        }

        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &soilc[0], MAX_SOI_LAY, month_timestep, 1);
        }
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &soilc[0], MAX_SOI_LAY, year, 1);
        }
      }
      //Total, instead of by layer
      else if(!curr_spec.layer){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_soid.somcrsum, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_soid.somcrsum, 1, year, 1);
        }

      }
    }//end critical(outputSOMCR)
  }//end SOMCR
  map_itr = netcdf_outputs.end();


  //SOMPR - soil organic matter, physically resistant
  map_itr = netcdf_outputs.find("SOMPR");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: SOMPR";
    curr_spec = map_itr->second;

    #pragma omp critical(outputSOMPR)
    {
      //By layer
      if(curr_spec.layer){

        double soilc[MAX_SOI_LAY];
        int il = 0;
        Layer* currL = this->cohort.ground.toplayer;
        while(currL != NULL){
          soilc[il] = currL->sompr;
          il++;
          currL = currL->nextl;
        }

        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &soilc[0], MAX_SOI_LAY, month_timestep, 1);
        }
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &soilc[0], MAX_SOI_LAY, year, 1);
        }
      }
      //Total, instead of by layer
      else if(!curr_spec.layer){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_soid.somprsum, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_soid.somprsum, 1, year, 1);
        }

      }
    }//end critical(outputSOMPR)
  }//end SOMPR
  map_itr = netcdf_outputs.end();


  //SOMRAWC
  map_itr = netcdf_outputs.find("SOMRAWC");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: SOMRAWC";
    curr_spec = map_itr->second;

    #pragma omp critical(outputSOMRAWC)
    {
      //By layer
      if(curr_spec.layer){

        double soilc[MAX_SOI_LAY];
        int il = 0;
        Layer* currL = this->cohort.ground.toplayer;
        while(currL != NULL){
          soilc[il] = currL->rawc;
          il++;
          currL = currL->nextl;
        }

        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &soilc[0], MAX_SOI_LAY, month_timestep, 1);
        }
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &soilc[0], MAX_SOI_LAY, year, 1);
        }
      }
      //Total, instead of by layer
      else if(!curr_spec.layer){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_soid.rawcsum, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_soid.rawcsum, 1, year, 1);
        }

      }
    }//end critical(outputSOMRAWC)
  }//end SOMRAWC
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
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_swesum[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_snws.swesum, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_snws.swesum, 1, year, 1);
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
      //daily
      if(curr_spec.daily){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_tlayer[0][0], MAX_SOI_LAY, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.edall->m_sois.ts[0], MAX_SOI_LAY, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.edall->y_sois.ts[0], MAX_SOI_LAY, year, 1);
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
        double d_trans[NUM_PFT], m_trans[NUM_PFT], y_trans[NUM_PFT];

        for(int ip=0; ip<NUM_PFT; ip++){
          d_trans[ip] = cohort.ed[ip].d_v2a.tran;
          m_trans[ip] = cohort.ed[ip].m_v2a.tran;
          y_trans[ip] = cohort.ed[ip].y_v2a.tran;
        }

        //daily
        if(curr_spec.daily){
          //TODO - this is unusual in that the daily values are not collected somewhere to be output all at once. This will just give a single value.
          output_nc_4dim(&curr_spec, file_stage_suffix, &d_trans[0], NUM_PFT, day_timestep, 1);
        }
        //monthly
        else if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_trans[0], NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_trans[0], NUM_PFT, year, 1);
        }

      }
      //Total
      else{ 
        if(curr_spec.daily){
          //TODO - as above, this is a single daily value for the whole month
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->d_v2a.tran, 1, day_timestep, 1);
        }
        else if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_v2a.tran, 1, month_timestep, 1);
        }
        else if(curr_spec.daily){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_v2a.tran, 1, year, 1);
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
        double m_vegc[NUM_PFT_PART][NUM_PFT];
        double y_vegc[NUM_PFT_PART][NUM_PFT];
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
          output_nc_5dim(&curr_spec, file_stage_suffix, &m_vegc[0][0], NUM_PFT_PART, NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_5dim(&curr_spec, file_stage_suffix, &y_vegc[0][0], NUM_PFT_PART, NUM_PFT, year, 1);
        }
      }
      //PFT only
      else if(curr_spec.pft && !curr_spec.compartment){

        double m_vegc[NUM_PFT] = {0};
        double y_vegc[NUM_PFT] = {0};
        for(int ip=0; ip<NUM_PFT; ip++){
          if(cohort.cd.m_veg.vegcov[ip]>0.){//only check PFTs that exist
            m_vegc[ip] = cohort.bd[ip].m_vegs.call;
            y_vegc[ip] = cohort.bd[ip].y_vegs.call;
          }
        }
        //monthly
        if(curr_spec.monthly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_vegc[0], NUM_PFT, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_vegc[0], NUM_PFT, year, 1);
        }
      }
      //Compartment only
      else if(!curr_spec.pft && curr_spec.compartment){

        double m_vegc[NUM_PFT_PART] = {0};
        double y_vegc[NUM_PFT_PART] = {0};
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
          output_nc_4dim(&curr_spec, file_stage_suffix, &m_vegc[0], NUM_PFT_PART, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_4dim(&curr_spec, file_stage_suffix, &y_vegc[0], NUM_PFT_PART, year, 1);
        }
      }
      //Neither PFT nor compartment
      else if(!curr_spec.pft && !curr_spec.compartment){
        //monthly
        if(curr_spec.monthly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_vegs.call, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_vegs.call, 1, year, 1);
        }
      }
    }//end critical(outputVEGC)
  }//end VEGC
  map_itr = netcdf_outputs.end();


  //VEGN
  map_itr = netcdf_outputs.find("VEGN");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: VEGN";
    curr_spec = map_itr->second;

    #pragma omp critical(outputVEGN)
    {
      //PFT and compartment
      if(curr_spec.pft && curr_spec.compartment){
        double m_vegn[NUM_PFT_PART][NUM_PFT];
        double y_vegn[NUM_PFT_PART][NUM_PFT];
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
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_vegs.nall, 1, month_timestep, 1);
        }
        //yearly
        else if(curr_spec.yearly){
          output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_vegs.nall, 1, year, 1);
        }
      }
    }//end critical(outputVEGN)
  }//end VEGN
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
      if(curr_spec.monthly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.edall->m_soid.vwc[0], MAX_SOI_LAY, month_timestep, 1);
      }
      else if(curr_spec.yearly){
        output_nc_4dim(&curr_spec, file_stage_suffix, &cohort.edall->y_soid.vwc[0], MAX_SOI_LAY, year, 1);
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
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->daily_watertab[0], 1, day_timestep, dinm);
      }
      //monthly
      else if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->m_sois.watertab, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.edall->y_sois.watertab, 1, year, 1);
      }
    }//end critical(outputWATERTAB)
  }//end WATERTAB
  map_itr = netcdf_outputs.end();


  //Woody debris RH
  map_itr = netcdf_outputs.find("WDRH");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"WDRH";
    curr_spec = map_itr->second;

    #pragma omp critical(outputWDRH)
    {
      //monthly
      if(curr_spec.monthly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->m_soi2a.rhwdeb, 1, month_timestep, 1);
      }
      //yearly
      else if(curr_spec.yearly){
        output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.bdall->y_soi2a.rhwdeb, 1, year, 1);
      }
    }//end critical(outputWDRH)
  }//end WDRH
  map_itr = netcdf_outputs.end();


  //Years since disturbance
  map_itr = netcdf_outputs.find("YSD");
  if(map_itr != netcdf_outputs.end()){
    BOOST_LOG_SEV(glg, debug)<<"NetCDF output: YSD";
    curr_spec = map_itr->second;

    #pragma omp critical(outputYSD)
    {
      output_nc_3dim(&curr_spec, file_stage_suffix, &cohort.cd.yrsdist, 1, year, 1);
    }//end critical(outputYSD)
  }//end YSD
  map_itr = netcdf_outputs.end();

}


