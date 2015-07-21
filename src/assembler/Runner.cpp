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

void Runner::run_years(int start_year, int end_year, const std::string& stage,
    boost::shared_ptr<CalController> cal_ctrl_ptr) {

  /** YEAR TIMESTEP LOOP */
  for (int iy = start_year; iy < end_year; ++iy) {
    BOOST_LOG_SEV(glg, debug) << "(Begining of year loop) " << cohort.ground.layer_report_string();

    /* Interpolate all the monthly values...? */
    this->cohort.climate.prepare_daily_driving_data(iy, stage);

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

      this->cohort.updateMonthly(iy, im, DINM[im]);


      // Monthly output control needs to be determined by a parameter
      // or from the control file. It should default to false given
      // the number of files it produces.
      if(cal_ctrl_ptr && md.output_monthly) {
        BOOST_LOG_SEV(glg, debug) << "Write monthly calibration data to json files...";
        this->output_caljson_monthly(iy, im);
      }

    } /* end month loop */

    //BOOST_LOG_SEV(glg, debug) << "(END OF YEAR) " << cohort.ground.layer_report_string();

    if(cal_ctrl_ptr) { // check args->get_cal_mode() or calcontroller_ptr? ??
      BOOST_LOG_SEV(glg, debug) << "Send yearly calibration data to json files...";
      this->output_caljson_yearly(iy);
    }

    BOOST_LOG_SEV(glg, note) << "Completed year " << iy << " for cohort/cell (row,col): (" << this->y << "," << this->x << ")";

  } /* end year loop */
}

void Runner::output_caljson_monthly(int year, int month){
  Json::Value data;
  std::ofstream out_stream;

  /* Not PFT dependent */
  data["Year"] = year;
  data["Month"] = month;
  data["TAir"] = cohort.ed->m_atms.ta;
  data["Snowfall"] = cohort.ed->m_a2l.snfl;
  data["Rainfall"] = cohort.ed->m_a2l.rnfl;
  data["WaterTable"] = cohort.ed->m_sois.watertab;
  data["ActiveLayerDepth"] = cohort.ed->m_soid.ald;
  data["CO2"] = cohort.ed->m_atms.co2;
  data["VPD"] = cohort.ed->m_atmd.vpd;
  data["EET"] = cohort.ed->m_l2a.eet;
  //PAR?
  //PARAbsorb

  data["VWCShlw"] = cohort.ed->m_soid.vwcshlw; 
  data["VWCDeep"] = cohort.ed->m_soid.vwcdeep;
  data["VWCMineA"] = cohort.ed->m_soid.vwcminea;
  data["VWCMineB"] = cohort.ed->m_soid.vwcmineb;
  data["VWCMineC"] = cohort.ed->m_soid.vwcminec;
  data["TShlw"] = cohort.ed->m_soid.tshlw;
  data["TDeep"] = cohort.ed->m_soid.tdeep;
  data["TMineA"] = cohort.ed->m_soid.tminea;
  data["TMineB"] = cohort.ed->m_soid.tmineb;
  data["TMineC"] = cohort.ed->m_soid.tminec;

  data["StNitrogenUptakeAll"] = cohort.bd->m_soi2v.snuptakeall;
  data["AvailableNitrogenSum"] = cohort.bd->m_soid.avlnsum;
  data["OrganicNitrogenSum"] = cohort.bd->m_soid.orgnsum;
  data["CarbonShallow"] = cohort.bd->m_soid.shlwc;
  data["CarbonDeep"] = cohort.bd->m_soid.deepc;
  data["CarbonMineralSum"] = cohort.bd->m_soid.mineac
                             + cohort.bd->m_soid.minebc
                             + cohort.bd->m_soid.minecc;
  data["MossdeathCarbon"] = cohort.bdall->m_v2soi.mossdeathc;
  data["MossdeathNitrogen"] = cohort.bdall->m_v2soi.mossdeathn;

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
    data["PFT" + pft_str]["GPPAll"] = cohort.bd[pft].m_a2v.gppall;
    data["PFT" + pft_str]["NPPAll"] = cohort.bd[pft].m_a2v.nppall;
    data["PFT" + pft_str]["GPPAllIgnoringNitrogen"] = cohort.bd[pft].m_a2v.ingppall;
    data["PFT" + pft_str]["NPPAllIgnoringNitrogen"] = cohort.bd[pft].m_a2v.innppall;
    data["PFT" + pft_str]["LitterfallCarbonAll"] = cohort.bd[pft].m_v2soi.ltrfalcall;
    data["PFT" + pft_str]["LitterfallNitrogenAll"] = cohort.bd[pft].m_v2soi.ltrfalnall;
    data["PFT" + pft_str]["PARDown"] = cohort.ed[pft].m_a2v.pardown;
    parDownSum+=cohort.ed[pft].m_a2v.pardown;
    data["PFT" + pft_str]["PARAbsorb"] = cohort.ed[pft].m_a2v.parabsorb;
    parAbsorbSum+=cohort.ed[pft].m_a2v.parabsorb;
    data["PFT" + pft_str]["StNitrogenUptake"] = cohort.bd[pft].m_soi2v.snuptakeall;
  }

  data["PARAbsorbSum"] = parAbsorbSum;
  data["PARDownSum"] = parDownSum;
  data["GPPSum"] = cohort.bdall->m_a2v.gppall;
  data["NPPSum"] = cohort.bdall->m_a2v.nppall;

  std::stringstream filename;
  filename.fill('0');
  filename << "/tmp/cal-dvmdostem/" << std::setw(4) << year << "_"
           << std::setw(2) << month << ".json";
  out_stream.open(filename.str().c_str(), std::ofstream::out);
  out_stream << data << std::endl;
  out_stream.close();
}


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


