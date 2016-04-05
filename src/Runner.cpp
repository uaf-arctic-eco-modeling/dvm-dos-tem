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

  // Experiment - place for daily debugging output...
  boost::filesystem::path folder("/tmp/debug-dvmdostem/");

  //FIX - we check for dir/file existence and then create or not
  //  in several places. Should probably move to a utility function.
  if( !(boost::filesystem::exists(folder)) ) {
    BOOST_LOG_SEV(glg, info) << "Creating folder: " << folder;
    boost::filesystem::create_directory(folder);
  } else {
    BOOST_LOG_SEV(glg, info) << "'" << folder << "'" << "already exists; delete and recreate!";
    boost::filesystem::remove_all(folder);
    boost::filesystem::create_directory(folder);
  }

  /** YEAR TIMESTEP LOOP */
  for (int iy = start_year; iy < end_year; ++iy) {
    BOOST_LOG_SEV(glg, debug) << "(Beginning of year loop) " << cohort.ground.layer_report_string();
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

    this->output_debug_daily_drivers(iy);

    if (this->calcontroller_ptr) { // should be null unless we are in "calibration mode"

      // Run any pre-configured directives
      this->calcontroller_ptr->run_config(iy, stage);

      // See if a signal has arrived (possibly from user
      // hitting Ctrl-C) and if so, stop the simulation
      // and drop into the calibration "shell".
      this->calcontroller_ptr->check_for_signals();

    }

    /** MONTH TIMESTEP LOOP */
    for (int im = 0; im < 12; ++im) {

      BOOST_LOG_SEV(glg, debug) << "(Begining of month loop, iy:"<<iy<<", im:"<<im<<") " << cohort.ground.layer_report_string();

      this->cohort.updateMonthly(iy, im, DINM[im]);


      // Monthly output control needs to be determined by a parameter
      // or from the control file. It should default to false given
      // the number of files it produces.
      if(this->calcontroller_ptr && md.output_monthly) {
        BOOST_LOG_SEV(glg, debug) << "Write monthly calibration data to json files...";
        this->output_caljson_monthly(iy, im, stage);
      }

    } /* end month loop */

    //BOOST_LOG_SEV(glg, debug) << "(END OF YEAR) " << cohort.ground.layer_report_string();

    if(this->calcontroller_ptr) { // check args->get_cal_mode() or calcontroller_ptr? ??
      BOOST_LOG_SEV(glg, debug) << "Send yearly calibration data to json files...";
      this->output_caljson_yearly(iy, stage);
    }

    BOOST_LOG_SEV(glg, note) << "Completed year " << iy << " for cohort/cell (row,col): (" << this->y << "," << this->x << ")";

  } /* end year loop */
}

void Runner::output_caljson_monthly(int year, int month, std::string stage){

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
  data["DeadMossCarbon"] = cohort.bdall->m_sois.dmossc;
  data["DeadMossNitrogen"] = cohort.bdall->m_sois.dmossn;
  // fluxes
  data["MossdeathCarbon"] = cohort.bdall->m_v2soi.mossdeathc;
  data["MossdeathNitrogen"] = cohort.bdall->m_v2soi.mossdeathn;

  data["NetNMin"] = cohort.bdall->m_soi2soi.netnminsum;
  data["NetNImmob"] = cohort.bdall->m_soi2soi.nimmobsum;
  data["OrgNInput"] = cohort.bdall->m_a2soi.orgninput;
  data["AvlNInput"] = cohort.bdall->m_a2soi.avlninput;
  data["AvlNLost"] = cohort.bdall->m_soi2l.avlnlost;
  data["RHraw"] = cohort.bdall->m_soi2a.rhrawcsum;
  data["RHsoma"] = cohort.bdall->m_soi2a.rhsomasum;
  data["RHsompr"] = cohort.bdall->m_soi2a.rhsomprsum;
  data["RHsomcr"] = cohort.bdall->m_soi2a.rhsomcrsum;
  data["RH"] = cohort.bdall->m_soi2a.rhtot;

  data["Burnthick"] = cohort.fd->fire_soid.burnthick;
  data["BurnVeg2AirC"] = cohort.fd->fire_v2a.orgc;
  data["BurnVeg2AirN"] = cohort.fd->fire_v2a.orgn;
  data["BurnVeg2SoiAbvVegC"] = cohort.fd->fire_v2soi.abvc;
  data["BurnVeg2SoiBlwVegC"] = cohort.fd->fire_v2soi.blwc;
  data["BurnVeg2SoiAbvVegN"] = cohort.fd->fire_v2soi.abvn;
  data["BurnVeg2SoiBlwVegN"] = cohort.fd->fire_v2soi.blwn;
  data["BurnSoi2AirC"] = cohort.fd->fire_soi2a.orgc;
  data["BurnSoi2AirN"] = cohort.fd->fire_soi2a.orgn;

  /* PFT dependent variables */
  double parDownSum = 0;
  double parAbsorbSum = 0;

  for(int pft=0; pft<NUM_PFT; pft++) {
    char pft_chars[5];
    sprintf(pft_chars, "%d", pft);
    std::string pft_str = std::string(pft_chars);
    //c++0x equivalent: std::string pftvalue = std::to_string(pft);
    data["PFT" + pft_str]["VegCarbon"]["Leaf"] = cohort.bd[pft].m_vegs.c[I_leaf];
    data["PFT" + pft_str]["VegCarbon"]["Stem"] = cohort.bd[pft].m_vegs.c[I_stem];
    data["PFT" + pft_str]["VegCarbon"]["Root"] = cohort.bd[pft].m_vegs.c[I_root];
    data["PFT" + pft_str]["VegStructuralNitrogen"]["Leaf"] = cohort.bd[pft].m_vegs.strn[I_leaf];
    data["PFT" + pft_str]["VegStructuralNitrogen"]["Stem"] = cohort.bd[pft].m_vegs.strn[I_stem];
    data["PFT" + pft_str]["VegStructuralNitrogen"]["Root"] = cohort.bd[pft].m_vegs.strn[I_root];
    data["PFT" + pft_str]["VegLabileNitrogen"] = cohort.bd[pft].m_vegs.labn;
    data["PFT" + pft_str]["GPPAll"] = cohort.bd[pft].m_a2v.gppall;
    data["PFT" + pft_str]["NPPAll"] = cohort.bd[pft].m_a2v.nppall;
    data["PFT" + pft_str]["GPPAllIgnoringNitrogen"] = cohort.bd[pft].m_a2v.ingppall;
    data["PFT" + pft_str]["NPPAllIgnoringNitrogen"] = cohort.bd[pft].m_a2v.innppall;
    data["PFT" + pft_str]["LitterfallCarbonAll"] = cohort.bd[pft].m_v2soi.ltrfalcall;
    data["PFT" + pft_str]["LitterfallNitrogenPFT"] = cohort.bd[pft].m_v2soi.ltrfalnall;
    data["PFT" + pft_str]["LitterfallNitrogen"]["Leaf"] = cohort.bd[pft].m_v2soi.ltrfaln[I_leaf];
    data["PFT" + pft_str]["LitterfallNitrogen"]["Stem"] = cohort.bd[pft].m_v2soi.ltrfaln[I_stem];
    data["PFT" + pft_str]["LitterfallNitrogen"]["Root"] = cohort.bd[pft].m_v2soi.ltrfaln[I_root];
    data["PFT" + pft_str]["PARDown"] = cohort.ed[pft].m_a2v.pardown;
    parDownSum+=cohort.ed[pft].m_a2v.pardown;
    data["PFT" + pft_str]["PARAbsorb"] = cohort.ed[pft].m_a2v.parabsorb;
    parAbsorbSum+=cohort.ed[pft].m_a2v.parabsorb;
    data["PFT" + pft_str]["StNitrogenUptake"] = cohort.bd[pft].m_soi2v.snuptakeall;
    data["PFT" + pft_str]["InNitrogenUptake"] = cohort.bd[pft].m_soi2v.innuptake;
    data["PFT" + pft_str]["LuxNitrogenUptake"] = cohort.bd[pft].m_soi2v.lnuptake;
    data["PFT" + pft_str]["TotNitrogenUptake"] = cohort.bd[pft].m_soi2v.snuptakeall + cohort.bd[pft].m_soi2v.lnuptake;
  }

  data["PARAbsorbSum"] = parAbsorbSum;
  data["PARDownSum"] = parDownSum;
  data["GPPSum"] = cohort.bdall->m_a2v.gppall;
  data["NPPSum"] = cohort.bdall->m_a2v.nppall;


  // Writes files like this:
  //  0000000.json, 0000001.json, 0000002.json

  std::stringstream filename;
  filename.fill('0');
  filename << md.monthly_cal_json.c_str()
           << "/" << std::setw(7) << (12 * year) + month << ".json";
  out_stream.open(filename.str().c_str(), std::ofstream::out);
  out_stream << data << std::endl;
  out_stream.close();

}


void Runner::output_caljson_yearly(int year, std::string stage) {

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
  data["DeadMossCarbon"] = cohort.bdall->y_sois.dmossc;
  data["DeadMossNitrogen"] = cohort.bdall->y_sois.dmossn;
  // fluxes
  data["MossdeathCarbon"] = cohort.bdall->y_v2soi.mossdeathc;
  data["MossdeathNitrogen"] = cohort.bdall->y_v2soi.mossdeathn;

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

  // Writes files like this:
  //  00000.json, 00001.json, 00002.json

  std::stringstream filename;
  filename.fill('0');
  filename << md.yearly_cal_json.c_str()
           << "/" << std::setw(5) << year << ".json";
  out_stream.open(filename.str().c_str(), std::ofstream::out);
  out_stream << data << std::endl;
  out_stream.close();

}

void Runner::output_debug_daily_drivers(int iy) {

  // Writes files like this:
  //  year_00000_daily_drivers.json
  //  year_00001_daily_drivers.json
  //  year_00002_daily_drivers.json

  std::stringstream filename;
  filename.fill('0');
  filename << md.daily_cal_json.c_str()
           << "/year_" << std::setw(5) << iy << "_daily_drivers.text";

  // NOTE: (FIX?) This may not be the best place for these files as they are
  // not exactly the same format/layout as the normal "calibration" json files

  std::ofstream out_stream;
  out_stream.open(filename.str().c_str(), std::ofstream::out);

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

