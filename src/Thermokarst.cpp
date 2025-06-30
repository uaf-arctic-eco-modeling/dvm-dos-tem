/*
 * Thermokarst.cpp
 *
 * 3/12/2025
 *
 * Starting with a copy of Wildfire.cpp and adapting
 * script for thermokarst disturbance. Initially, 
 * this will focus on retrogressive thaw slump and 
 * possibly active layer detachment as a precursor.
 *
 * Thermokarst disturbance initiation will first be
 * prescribed using a similar method as the explicit
 * historic fire input forcing. Later we hope to use
 * either and external or integrated predictive model
 * to determine thermokarst type, occurrence, and 
 * severity (or extent).
 *
 * C/N pools can be updated here using 'bd' but may 
 * require additional modification in other places.
 * Changes to C/N soil and vegetation pools will vary
 * depending on thermokarst type.
 *
 * Soil layer structure needs to be updated in ground
 * though the function for this can be defined here.
 *
 * Roots will need to be considered, but not entirely 
 * sure of the best method at this point.
 */

#include <string>
#include <sstream>

#include "../include/Thermokarst.h"

#include "../include/TEMUtilityFunctions.h"
#include "../include/TEMLogger.h"

extern src::severity_logger< severity_level > glg;

Thermokarst::Thermokarst() {}

Thermokarst::~Thermokarst() {}

Thermokarst::Thermokarst(const std::string &exp_fname, const double cell_slope,
                         const double cell_aspect, const double cell_elevation,
                         const int y, const int x){

  #pragma omp critical(load_input)
  {
    BOOST_LOG_SEV(glg, info) << "Setting up explicit thermokarst data...";
    this->exp_thermokarst_mask = temutil::get_timeseries<int>(exp_fname, "exp_thermokarst_mask", y, x);
    this->exp_thermokarst_severity = temutil::get_timeseries<int>(exp_fname, "exp_thermokarst_severity", y, x);
    this->exp_jday_of_thermokarst = temutil::get_timeseries<int>(exp_fname, "exp_jday_of_thermokarst", y, x);
    this->exp_area_of_thermokarst = temutil::get_timeseries<int64_t>(exp_fname, "exp_area_of_thermokarst", y, x);
  } 

  this->slope = cell_slope;
  this->asp = cell_aspect;
  this->elev = cell_elevation;

  BOOST_LOG_SEV(glg, debug) << "Done making Thermokarst object.";

  BOOST_LOG_SEV(glg, debug) << this->report_thermokarst_inputs();
}

void Thermokarst::load_projected_explicit_data(const std::string& exp_fname, int y, int x) {
    BOOST_LOG_SEV(glg, info) << "Setting up explicit thermokarst data...";
    this->exp_thermokarst_mask = temutil::get_timeseries<int>(exp_fname, "exp_thermokarst_mask", y, x);
    this->exp_thermokarst_severity = temutil::get_timeseries<int>(exp_fname, "exp_thermokarst_severity", y, x);
    this->exp_jday_of_thermokarst = temutil::get_timeseries<int>(exp_fname, "exp_jday_of_thermokarst", y, x);
    this->exp_area_of_thermokarst = temutil::get_timeseries<int64_t>(exp_fname, "exp_area_of_thermokarst", y, x);
}

/** Assemble and return a string with a bunch of data from this class */
std::string Thermokarst::report_thermokarst_inputs() {

  std::stringstream report_string;
  report_string << "exp thermokarst vectors/data:" << std::endl;
  report_string << "explicit thermokarst year:         [" << temutil::vec2csv(this->exp_thermokarst_mask) << "]" << std::endl;
  report_string << "explicit thermokarst jday_of_thermokarst: [" << temutil::vec2csv(this->exp_jday_of_thermokarst) << "]" << std::endl;
  report_string << "explicit thermokarst area_of_thermokarst: [" << temutil::vec2csv(this->exp_area_of_thermokarst) << "]" << std::endl;
  report_string << "explicit thermokarst severity:     [" << temutil::vec2csv(this->exp_thermokarst_severity) << "]" << std::endl;

  return report_string.str();

}

// >>> Do we need parameter initialization for thermokarst? Probably.
// For now we will comment this function and use hardcoded variables
// for testing purposes.

// Looks like this is just used when setting up a Cohort...
// void WildFire::initializeParameter() {
//   for (int i=0; i<NUM_FSEVR; i++) {
//     for (int ip=0; ip<NUM_PFT; ip++) {
//       firpar.fvcomb[i][ip] = chtlu->fvcombust[i][ip];
//       firpar.fvdead[i][ip] = chtlu->fvslash[i][ip];
//     }

//     firpar.foslburn[i] = chtlu->foslburn[i];
//   }

//   firpar.vsmburn = chtlu->vsmburn; // a threshold value of VWC for burn
//                                    //   organic layers
//   firpar.r_retain_c = chtlu->r_retain_c;
//   firpar.r_retain_n = chtlu->r_retain_n;
// };

void Thermokarst::initializeState() {
  // this is set from wildfire changes, what state do we
  // need to initialize in the case of a thermokarst
  // disturbance occurrence?
  tkdata->thermokarst_a2soi.orgn = 0.0;
};

// Looks like this is just used when setting up a Cohort from a Restart file...
void Thermokarst::set_state_from_restartdata(const RestartData & rdata) {
  tkdata->thermokarst_a2soi.orgn = rdata.thermokarsta2sorgn;
}

/** Figure out whether or not there should be thermokarst, based on stage, yr, month.
 *
 *  The data for explicit thermokarst dates are held in data
 *  members of this (Thermokarst) object. This function looks at those data
 *  and sets the "actual_severity" member accordingly. -- if we end up
 *  using "severity" for thermokarst processes.
 *
 *  THIS WOULD BE A PRIME LOCATION TO COUPLE WITH A STATE AND TRANSITION MODEL.
 *  Alternatively, it might be possible to link this with inputs (ground ice)
 *  and organic layer thickness (as well as other variables perhaps).
 */
bool Thermokarst::should_initiate(const int yr, const int midx, const std::string& stage) { 

  BOOST_LOG_SEV(glg, info) << "determining thermokarst initiation for yr:" << yr
                           << ", monthidx:" << midx << ", stage:" << stage;

  bool initiate = false;

  if ( stage.compare("tr-run") == 0 || stage.compare("sc-run") == 0 ) {

    BOOST_LOG_SEV(glg, debug) << "Determine thermokarst from explicit thermokarst regime.";

    if ( this->exp_thermokarst_mask[yr] == 1 ){
      if ( temutil::doy2month(this->exp_jday_of_thermokarst[yr]) == midx ) {
        initiate = true;
      }
      // do nothing: correct year, wrong month
    }
  } else {
    BOOST_LOG_SEV(glg, warn) << "Unknown stage! (" << stage << ")";
  }

  BOOST_LOG_SEV(glg, debug) << "Should we initiate thermokarst?:" << initiate;

  return initiate;
}

/** Disturbing vegetation and soil organic C to to thermokarst */
void Thermokarst::initiate(int year) {
  // initiate slump / subsidence, etc for different methods
  BOOST_LOG_NAMED_SCOPE("Thermokarsting");
  BOOST_LOG_SEV(glg, info) << "HELP!! - THERMOKARST!! RUN FOR YOUR LIFE!";

  BOOST_LOG_SEV(glg, debug) << tkdata->report_to_string("Before Thermokarst::initiate(..)");
  BOOST_LOG_SEV(glg, info) << "Clearing the ThermokarstData object...";
  tkdata->clearing();
  BOOST_LOG_SEV(glg, debug) << tkdata->report_to_string("After ThermokarstData::clearing(..)");

  // What do we want this to be called / do?
  // changing burn to thermokarst, referring to OL soil
  // lost through thermokarst disturbance (either slump or
  // detachment).
  double thermokarstdepth = getThermokarstOrgSoilRemoval(year);
  // we might want to think about mineral soil removal as well
  // but also how to handle different thermokarst types in the
  // future

  BOOST_LOG_SEV(glg, debug) << tkdata->report_to_string("After Thermokarst::getThermokarstOrgSoilthick(..)");

  BOOST_LOG_SEV(glg, info) << "Setup some temporary pools for tracking various thermokarst related attributes (depths, C, N)";
  // Do we need other variables for tracking? ALSO RENAME appropriately
  // totbotdepth is used for accumulating layers and comparing to thermokarst depth 
  double totbotdepth = 0.0;
  // lost soil carbon and nitrogen. Some parameterization may be needed for a 
  // more mechanistic approach but for now this will act as a first approximation
  double lostsolc = 0.0;
  double lostsoln = 0.0;
  // ratio of dead veg. (roots) after thermokarst
  double r_thermokarst2bg_cn[NUM_PFT]; 

  for (int ip=0; ip<NUM_PFT; ip++) {
    r_thermokarst2bg_cn[ip] = 0.; //  used for vegetation below-ground (root) loss,
                                  //  and calculated below
  }

  BOOST_LOG_SEV(glg, debug) << "Handle thermokarst in the soil (loop over all soil layers)...";
  for (int il = 0; il < cd->m_soil.numsl; il++) {

    BOOST_LOG_SEV(glg, debug) << "== Layer Info == "
                              << "   type:" << cd->m_soil.type[il] // 0:moss 1:shlwpeat 2:deeppeat 3:mineral
                              << "   dz:" << cd->m_soil.dz[il]
                              << "   top:" << cd->m_soil.z[il]
                              << "   bottom:"<< cd->m_soil.z[il] + cd->m_soil.dz[il];

    // Only organic soils - for thermokarst do we want to affect mineral soil at all?
    // For now maybe we can ignore that part.
    if(cd->m_soil.type[il] <= 2) {

      totbotdepth += cd->m_soil.dz[il];

      double ilsolc =  bdall->m_sois.rawc[il] + bdall->m_sois.soma[il] +
                       bdall->m_sois.sompr[il] + bdall->m_sois.somcr[il];

      double ilsoln =  bdall->m_sois.orgn[il] + bdall->m_sois.avln[il];

      if(totbotdepth <= thermokarstdepth) { //remove all the orgc/n in this layer
        BOOST_LOG_SEV(glg, debug) << "Haven't reached thermokarst depth (" << thermokarstdepth << ") yet. Remove all org C and N in this layer";
        lostsolc += ilsolc;
        lostsoln += ilsoln;
        bdall->m_sois.rawc[il] = 0.0;
        bdall->m_sois.soma[il] = 0.0;
        bdall->m_sois.sompr[il]= 0.0;
        bdall->m_sois.somcr[il]= 0.0;
        bdall->m_sois.orgn[il] = 0.0;
        bdall->m_sois.avln[il] = 0.0;

        for (int ip=0; ip<NUM_PFT; ip++) {
          if (cd->m_veg.vegcov[ip]>0.) {
            r_thermokarst2bg_cn[ip] += cd->m_soil.frootfrac[il][ip];
            cd->m_soil.frootfrac[il][ip] = 0.0;
          }
        }
      } else {
        BOOST_LOG_SEV(glg, debug) << "The bottom of this layer (il: " << il << ") is past the 'thermokarstdepth'. Find the remaining C and N as a fraction of layer thickness";
        double partleft = totbotdepth - thermokarstdepth;

        // Calculate the remaining C, N
        if (partleft < cd->m_soil.dz[il]) { // <-- Maybe this should be an assert instead of an if statement??
          BOOST_LOG_SEV(glg, debug) << "Thermokarst removed all but "<<partleft<<"of layer "<<il;
          lostsolc += (1.0-partleft/cd->m_soil.dz[il]) * ilsolc;
          lostsoln += (1.0-partleft/cd->m_soil.dz[il]) * ilsoln;
          bdall->m_sois.rawc[il] *= partleft/cd->m_soil.dz[il];
          bdall->m_sois.soma[il] *= partleft/cd->m_soil.dz[il];
          bdall->m_sois.sompr[il] *= partleft/cd->m_soil.dz[il];
          bdall->m_sois.somcr[il] *= partleft/cd->m_soil.dz[il];
          bdall->m_sois.orgn[il] *= partleft/cd->m_soil.dz[il];
          bdall->m_sois.avln[il] *= partleft/cd->m_soil.dz[il];

          for (int ip=0; ip<NUM_PFT; ip++) {
            if (cd->m_veg.vegcov[ip] > 0.0) {
              r_thermokarst2bg_cn[ip] += (1-partleft/cd->m_soil.dz[il])
                                * cd->m_soil.frootfrac[il][ip];
              cd->m_soil.frootfrac[il][ip] *= partleft/cd->m_soil.dz[il];
            }
          }
        } else {
          BOOST_LOG_SEV(glg, warn) << "The remaining soil after thermokarst is greater than the thickness of this layer. Something is wrong??";
          BOOST_LOG_SEV(glg, warn) << "partleft: " << partleft << "cd->m_soil.dz["<<il<<"]: " << cd->m_soil.dz[il];
          break;
        }
      }
    // Thermokarst could affect mineral soil layers. This will need to be an additional set of new processes 
    } else {   //Mineral soil layers
      BOOST_LOG_SEV(glg, info) << "Layer type:" << cd->m_soil.type[il] << ". Should be a non-organic soil layer? (greater than type 2)";
      BOOST_LOG_SEV(glg, info) << "Not much to do here. Can't really thermokarst non-organic layers. but maybe we will in the future";

      if(totbotdepth <= thermokarstdepth) { //may not be needed, but just in case
        BOOST_LOG_SEV(glg, info) << "For some reason totbotdepth <= thermokarstdepth, so we are setting tkdata->thermokarst_soid.removal_thickness = totbotdepth??";
        tkdata->thermokarst_soid.removal_thickness = totbotdepth;
      }
    }
  } // end soil layer loop

  //Setting relative organic layer removed (rolr) value
  tkdata->thermokarst_soid.rolr = tkdata->thermokarst_soid.removal_thickness / totbotdepth;

  // needs to re-do the soil rootfrac for each pft which was modified above
  //   (in burn soil layer)
  BOOST_LOG_SEV(glg, info) << "Re-do the soil root fraction for each PFT modified by thermokarst?";
  for (int ip = 0; ip < NUM_PFT; ip++) {
    double rootfracsum = 0.0;

    for (int il = 0; il < cd->m_soil.numsl; il++) {
      rootfracsum += cd->m_soil.frootfrac[il][ip];
    }

    for (int il =0; il <cd->m_soil.numsl; il++) {
      cd->m_soil.frootfrac[il][ip] /= rootfracsum;
    }
  }

  // all woody debris will burn out - Do we assume this is lost through mudflow or detachment?
  BOOST_LOG_SEV(glg, info) << "Handle lost woody debris...";
  double wdebrisc = bdall->m_sois.wdebrisc; //
  double wdebrisn = bdall->m_sois.wdebrisn; //
  bdall->m_sois.wdebrisc = 0.0;
  bdall->m_sois.wdebrisn = 0.0;

  // summarize
  BOOST_LOG_SEV(glg, info) << "Summarize...?";
  // How to parameterize "retained" C and N? for thermokarst disturbance
  double vola_solc = lostsolc * (1.0 - firpar.r_retain_c) + wdebrisc;
  double vola_soln = lostsoln * (1.0 - firpar.r_retain_n) + wdebrisn;
  double reta_solc = lostsolc * firpar.r_retain_c;   //together with veg.-burned C return, This will be put into soil later
  double reta_soln = lostsoln * firpar.r_retain_n;   //together with veg.-burned N return, This will be put into soil later

  // For now we are assuming standing dead is removed during mudflow or detachment
  BOOST_LOG_SEV(glg, info) << "Handle Vegetation loss and mortality...";
  double comb_vegc = 0.0;  // summed for all PFTs
  double comb_vegn = 0.0;
  double comb_deadc = 0.0;
  double comb_deadn = 0.0;
  double dead_bg_vegc = 0.0;
  double dead_bg_vegn = 0.0;
  double veg_2_dead_C = 0.0;
  double veg_2_dead_N = 0.0;

  bdall->m_vegs.deadc0 = 0.0;//Zeroing the standing dead pools
  bdall->m_vegs.deadn0 = 0.0;

  for (int ip = 0; ip < NUM_PFT; ip++) {

    if (cd->m_veg.vegcov[ip] > 0.0) {
      BOOST_LOG_SEV(glg, info) << "Some of PFT"<<ip<<" exists (coverage > 0). Remove it due to thermokarst!";

      // vegetation removed/dead/living fraction for above-ground
      getThermokarstAbgVegetation(ip, year);

      // root death ratio: must be called after both above-ground and
      // below-ground loss. r_live_cn is same for both above-ground
      // and below-ground
      double r_dead2bg_cn = 1.0-r_thermokarst2bg_cn[ip]-r_live_cn;

      // Dead veg C, N. Assuming all previous deadc burned.
      comb_deadc += bd[ip]->m_vegs.deadc;
      // Assuming all previous deadn burned
      comb_deadn += bd[ip]->m_vegs.deadn;
      
      //Zeroing the standing dead pools
      bd[ip]->m_vegs.deadc0 = 0.0;
      bd[ip]->m_vegs.deadn0 = 0.0;

      // Do we need both r_dead2ag_cn and r_thermokarst2ag_cn? These are declared in
      // Thermokarst.h but may be used for determining C and N removed from the gridcell
      // through mudflow or active layer detachment opposed to vegetation killed but 
      // remaining within the cell. If so maybe change the names to be more descriptive
      // for this purpose
      veg_2_dead_C = (bd[ip]->m_vegs.c[I_leaf] + bd[ip]->m_vegs.c[I_stem]) * r_dead2ag_cn;
      veg_2_dead_N = (bd[ip]->m_vegs.strn[I_leaf] + bd[ip]->m_vegs.strn[I_stem]) * r_dead2ag_cn;

      // Above-ground veg. removal/death during thermokarst
      // when summing, needs adjusting by 'vegcov'
      comb_vegc += bd[ip]->m_vegs.c[I_leaf] * r_thermokarst2ag_cn;

      // We define dead c/n as the not-falling veg (or binding with living veg)
      // during fire,
      bd[ip]->m_vegs.deadc = bd[ip]->m_vegs.c[I_leaf] * r_dead2ag_cn;
      // Which then is the source of ground debris (this is for woody plants
      // only, others could be set deadc/n to zero)
      bd[ip]->m_vegs.c[I_leaf] *= (1.0 - r_thermokarst2ag_cn - r_dead2ag_cn);

      comb_vegc += bd[ip]->m_vegs.c[I_stem] * r_thermokarst2ag_cn;
      bd[ip]->m_vegs.deadc += bd[ip]->m_vegs.c[I_stem] * r_dead2ag_cn;
      bd[ip]->m_vegs.c[I_stem] *= (1.0 - r_thermokarst2ag_cn-r_dead2ag_cn);

      comb_vegn += bd[ip]->m_vegs.strn[I_leaf] * r_thermokarst2ag_cn;
      bd[ip]->m_vegs.deadn += bd[ip]->m_vegs.strn[I_leaf] * r_dead2ag_cn;
      bd[ip]->m_vegs.strn[I_leaf] *= (1.0 - r_thermokarst2ag_cn-r_dead2ag_cn);

      comb_vegn += bd[ip]->m_vegs.strn[I_stem] * r_thermokarst2ag_cn;
      bd[ip]->m_vegs.deadn += bd[ip]->m_vegs.strn[I_stem] * r_dead2ag_cn;
      bd[ip]->m_vegs.strn[I_stem] *= (1.0 - r_thermokarst2ag_cn - r_dead2ag_cn);

      // Below-ground veg. (root) removal/death during thermokarst
      comb_vegc += bd[ip]->m_vegs.c[I_root] * r_thermokarst2bg_cn[ip];
      comb_vegn += bd[ip]->m_vegs.strn[I_root] * r_thermokarst2bg_cn[ip];

      // For the dead below-ground C caused by thermokarst, they are put into original layer
      double deadc_tmp = bd[ip]->m_vegs.c[I_root]*r_dead2bg_cn;
      for (int il = 0; il < cd->m_soil.numsl; il++) {
        if (cd->m_soil.frootfrac[il][ip] > 0.0) {
          //for this, 'rootfrac' must be updated above
          bdall->m_sois.somcr[il] += deadc_tmp * cd->m_soil.frootfrac[il][ip];
        }
      }
      dead_bg_vegc += deadc_tmp;
      bd[ip]->m_vegs.c[I_root] *= (1.0 - r_thermokarst2bg_cn[ip] - r_dead2bg_cn);

      // For the dead below-ground N caused by fire, they are put into original layer
      double deadn_tmp = bd[ip]->m_vegs.strn[I_root] * r_dead2bg_cn; //this is needed below
      for (int il =0; il <cd->m_soil.numsl; il++) {
        if (cd->m_soil.frootfrac[il][ip] > 0.0) {
          //for this, 'rootfrac' must be updated above
          bdall->m_sois.somcr[il] += deadn_tmp*cd->m_soil.frootfrac[il][ip];
        }
      }
      dead_bg_vegn +=deadn_tmp;
      bd[ip]->m_vegs.strn[I_root] *= (1.0 - r_thermokarst2bg_cn[ip] - r_dead2bg_cn);

      // one more veg N pool (labile N)
      comb_vegn += bd[ip]->m_vegs.labn * (1.0 - r_live_cn);//assuming all labn emitted, leaving none into deadn
      bd[ip]->m_vegs.labn *= r_live_cn;

      // finally, we have:
      bd[ip]->m_vegs.call = bd[ip]->m_vegs.c[I_leaf]
                            + bd[ip]->m_vegs.c[I_stem]
                            + bd[ip]->m_vegs.c[I_root];
      bd[ip]->m_vegs.nall = bd[ip]->m_vegs.strn[I_leaf]
                            + bd[ip]->m_vegs.strn[I_stem]
                            + bd[ip]->m_vegs.strn[I_root]
                            + bd[ip]->m_vegs.labn;

    } // end of 'cd->m_veg.vegcov[ip] > 0.0' (no coverage, nothing to do)

    //Writing out initial standing dead pools. These values will be
    //used to compute the rate of decomposition of the standing dead - 
    //1/9th of the original value per year.
    bd[ip]->m_vegs.deadc0 = veg_2_dead_C;
    bd[ip]->m_vegs.deadn0 = veg_2_dead_N;

    //Writing out initial values of standing dead pools to the pools
    //actually used for computation. These values will be decremented
    //by 1/9th the original value per year.
    bd[ip]->m_vegs.deadc = veg_2_dead_C;
    bd[ip]->m_vegs.deadn = veg_2_dead_N;

  } // end pft loop

  // How do we want to consider retention? Maybe these can be hardcoded initially?
  double reta_vegc = (comb_vegc + comb_deadc) * firpar.r_retain_c;
  double reta_vegn = (comb_vegn + comb_deadn) * firpar.r_retain_n;

  // There was commented code here, but has now been removed. See Wildfire.cpp 
  // if this maybe needed here. Modifying bdall.

  BOOST_LOG_SEV(glg, info) << "Save the thermokarst emission and return data into 'td'...";
  //Summing the PFT specific fluxes to dead standing
  for(int ip=0; ip<NUM_PFT; ip++){
    tkdata->thermokarst_v2dead.vegC += bd[ip]->m_vegs.deadc;
    tkdata->thermokarst_v2dead.strN += bd[ip]->m_vegs.deadn;
  }
  //fd->fire_v2dead.vegC = veg_2_dead_C; 
  //fd->fire_v2dead.strN = veg_2_dead_N;
  tkdata->thermokarst_v2a.orgc =  comb_vegc - reta_vegc;
  tkdata->thermokarst_v2a.orgn =  comb_vegn - reta_vegn;
  tkdata->thermokarst_v2soi.abvc = reta_vegc;
  tkdata->thermokarst_v2soi.abvn = reta_vegn;
  tkdata->thermokarst_v2soi.blwc = dead_bg_vegc;
  tkdata->thermokarst_v2soi.blwn = dead_bg_vegn;
  tkdata->thermokarst_soi2a.orgc = vola_solc;
  tkdata->thermokarst_soi2a.orgn = vola_soln;

  // the above 'v2a.orgn' and 'soi2a.orgn', will be as one of N source,
  // which is depositing into soil evenly in one FRI
  //- this will let the system -N balanced in a long-term, if NO
  //  open-N cycle included
  // This should occur every month post-fire. FIX
  // tkdata->thermokarst_a2soi.orgn = (tkdata->thermokarst_soi2a.orgn + tkdata->thermokarst_v2a.orgn);

  //put the retained C/N into the first unburned soil layer's
  //  chemically-resistant SOMC pool
  // Note - this 'retained C' could be used as char-coal, if need to do so.
  //        Then define the 'r_retain_c' in the model shall be workable
  for (int il = 0; il < cd->m_soil.numsl; il++) {
    double tsomc = bdall->m_sois.rawc[il] + bdall->m_sois.soma[il]
                   + bdall->m_sois.sompr[il] + bdall->m_sois.somcr[il];

    if(tsomc > 0. || il==cd->m_soil.numsl-1) {
      // this may possibly put retac/n in the first mineral soil
      bdall->m_sois.somcr[il] += reta_vegc + reta_solc;
      bdall->m_sois.orgn[il]  += reta_vegn + reta_soln;
      break;
    }
  }

  //Need to copy 'bdall->m_soils' to other PFTs, because above
  //  soil portion of 'bd' is done on 'bdall'
  for (int ip=1; ip<NUM_PFT; ip++) {
    if (cd->m_veg.vegcov[ip]>0.) {
      bd[ip]->m_sois = bdall->m_sois;
    }
  }
};

// >>> This function maybe a good place to export above ground vegetation.
// For slumps this could move to a pool considered with mudflow. For IW
// degradation perhaps we can consider a drowning or flooding pool.

// above ground burning ONLY, based on fire severity indirectly or directly
void Thermokarst::getThermokarstAbgVegetation(const int ipft, const int year) {
  
  // BOOST_LOG_SEV(glg, info) << "Lookup the above ground vegetation burned as a funciton of severity.";
  // BOOST_LOG_SEV(glg, info) << " - Set the ratios for 'burn to above ground C,N' and 'dead to above ground C,N' member variables.";
  // BOOST_LOG_SEV(glg, info) << " - Set the 'ratio live cn' member variable";

  // Yuan: the severity categories are from ALFRESCO:
  // 0 - no burning
  // 1 - low
  // 2 - moderate
  // 3 - high + low surface
  // 4 - high + high surface

  //Fire severity, both FRI and explicit, is loaded from input files.
  //The input file severities are 1-based, and must be converted
  // to 0-based to look up the related parameter values.
  // int fri_severity_idx = max((this->fri_severity - 1), 0);
  // int exp_severity_idx = max((this->exp_fire_severity[year] - 1), 0);

  // FRI-derived fire regime
  // if ( this->fri_derived ) {
  //   //Get fvcomb and fvdead from the parameters
  //   this->r_thermokarst2ag_cn = firpar.fvcomb[fri_severity_idx][ipft];
  //   this->r_dead2ag_cn = firpar.fvdead[fri_severity_idx][ipft];
  // }
  // //Explicit fire regime
  // else {
  //   //Get fvcomb and fvdead from the parameters
  //   this->r_thermokarst2ag_cn = firpar.fvcomb[exp_severity_idx][ipft];
  //   this->r_dead2ag_cn = firpar.fvdead[exp_severity_idx][ipft];
  // }

  double fraction_veg_removed = 0.9;

  // this->r_thermokarst2ag_cn = firpar.fvcomb[exp_severity_idx][ipft];
  // this->r_dead2ag_cn = firpar.fvdead[exp_severity_idx][ipft];

  // this->r_live_cn = 1.0 - this->r_thermokarst2ag_cn - this->r_dead2ag_cn;

  this->r_live_cn = 1.0 - fraction_veg_removed;
}


// >>> Instead of calculating how much organic soil is 'burnt' this function
// can be used to estimate the amount of organic soil removed through active
// layer detachment slide or slump related mudflow. See rules below, may need
// ammending or editing.

/// >>> Some notes and pseudo code for what is expected to happen here:
/// How much organic layer is removed? Is this dependent on slope? Other factors?
/// To begin with we could remove ALL OL (or all but a small seed so model can run).
/// 

/** Find the thickness of organic soil to burn.
* Use severity (lookup? or derive?) and soil moisture prpoperties
* (volumetric soil moisture).
* Three rules:
*   1. only organic layer can be burned
*   2. can't exceed a pixel specified 'max burn thickness'
*   3. should not burn into "wet" organic soil layers
*/
double Thermokarst::getThermokarstOrgSoilRemoval(const int year) {


  BOOST_LOG_SEV(glg, info) << "Find the amount of organic soil that is removed due to thermokarst.";
//assert((0 <= severity && severity < 5) && "Invalid fire severity! ");

  // >>> thickness removed from thermokarst disturbance
  double removal_thickness = 0.0;

  // >>> There was a severity index based on ALFRESCO. For now there will
  // only be one severity, but this is subject to development of state
  // and transition model

  double total_organic_thickness =  cd->m_soil.mossthick
                                    + cd->m_soil.shlwthick
                                    + cd->m_soil.deepthick;

  BOOST_LOG_SEV(glg, debug) << "Total organic thickness: " << total_organic_thickness;

  // >>> compute: Fraction Organic Layer Removed (FOLR)
  double folr = 0.0;

  // >>> All of the below is depending on severity and whether FRI
  // or explicit inputs are implemented. Ingoring for now.

  // if ( this->fri_derived ) {                    // FRI-derived fire regime
  //   if (this->fri_severity >= 0) {              // fire severity is available from the input files - so get folb from the parameter file;
  //     folb = firpar.foslburn[this->fri_severity];
  //   }else {                                     // fire severity is available from the input files - apply the lookup table from Yi et al. 2010;
  //     if( cd->drainage_type == 0 ) {            // 0: well-drained; 1: poorly-drained;
  //       if ( this->fri_jday_of_burn <= 212 ) {   // Early fire, before July 31st (from Turetsly et al. 2011);
  //         if ( this->fri_area_of_burn < 1.0 ) { // Small fire year (less that 1% of the area burned);
  //           folb = 0.54;
  //         } else {
  //           folb = 0.69;
  //         }
  //       } else {                                // late fire (after July 31st);
  //         folb = 0.80;
  //       } 
  //     } else {                                  // lowland;
  //       folb = 0.48;
  //     } 
  //   }
  // } else {                                      // Explicit fire regime;
  //   if (this->exp_fire_severity[year] >= 0) {    // fire severity is available from the input files - so get folb from the parameter file;
  //     folb = firpar.foslburn[this->exp_fire_severity[year]];
  //   } else {  
  //     if ( cd->cmttype > 3) {                   // tundra ecosystems: Mack et al. 2011;
  //       folb = 0.01*((21.5-6.1)/21.5);
  //     } else {                                  // boreal forest: Genet et al.2013;
  //        if(this->slope<2){
  //         // AOB in km-2, see coefficient and paper.
  //         folb = 0.1276966713-0.0319397467*this->slope+0.0020914862*this->exp_jday_of_burn[year]+0.0127016155* log(this->exp_area_of_burn[year]);
  //       } else {
  //         folb = -0.2758306315+0.0117609336*this->slope-0.0744057680*cos(this->asp * 3.14159265 / 180 ) +0.0260221684*edall->m_soid.tshlw+0.0011413114*this->exp_jday_of_burn[year]+0.0336302905*log (this->exp_area_of_burn[year]);
  //       }
  //     }
  //   }
  // }

  // >>> for now remove 99% of organic layer
  folr = 0.99;

  // >>> not sure if we want to fix anything to 0 or 1 yet
  // if (folb > 1.0) folb=1.0;
  // if (folb < 0.0) folb=0.0;


  //  Lookup burn thickness, based on severity and
  //  'fraction organic soil layer burned' parameter.
  //  (foslburn ==> "fraction organic soil layer burned")
  //burn_thickness = firpar.foslburn[severity] * total_organic_thickness;

  removal_thickness = folr * total_organic_thickness;

  BOOST_LOG_SEV(glg, debug) << "Calculated organic thickness removed: " << removal_thickness;
  
  // >>> Below is calculating volumetric soil moisture constrained burning or layers
  // For a slump, this may work inversely, i.e. greater moisture more removal of 
  // organic matter. For now we will make these fixed and hardcoded for testing. 

  //  VSM constrained burn thickness
  //  Find all layers where there is not much volumentric water - infact, less
  //  water than specified in the fire parameters for 'vmsburn'
  // double total_dry_organic_thickness = 0.0;

  // for (int i = 0; i < cd->m_soil.numsl; i++) {
  //   // 0:moss, 1:shlw peat, 2:deep peat, 3:mineral
  //   if( cd->m_soil.type[i] <= 2 ) {
  //     if (edall->m_soid.vwc[i] <= (firpar.vsmburn * cd->m_soil.por[i]) ) {
  //       total_dry_organic_thickness += cd->m_soil.dz[i];
  //     }
  //     // layer is too wet to burn
  //     // will all layers below this be too wet?
  //     // should we break the layer loop here?

  //   } else {
  //     break; // can't burn mineral soil
  //   }
  // }
  // if ( burn_thickness > total_dry_organic_thickness ) {
  //   burn_thickness = total_dry_organic_thickness;
  //   BOOST_LOG_SEV(glg, debug) << "Whoops! Burn thickness was greater than the thickness of dry organic material. Constraining burn thickness...";
  // }
  // BOOST_LOG_SEV(glg, debug) << "Calculated burn thickness using VSM constraint: " << burn_thickness;

// always burn all moss, even if the severity is really low.
//  if( burn_thickness < cd->m_soil.mossthick ) {
//    BOOST_LOG_SEV(glg, debug) << "Whoops! Shallow burn, but we always burn all the moss!";
//    burn_thickness = cd->m_soil.mossthick;   //burn all moss layers
//  }

  // Not sure that this will work in all circumstances?
  //// there are at least 2 cm orgnanic left
  //if( (total_dry_organic_thickness - burn_thickness) < 0.02 ){
  //  BOOST_LOG_SEV(glg, debug) << "Whoops! Can't burn everything. Always leave a few cm of organic material.";
  //  burn_thickness = total_dry_organic_thickness - 0.02;
  //}

  // >>> Here we need to add OL removal thickness to ThermokarstData
  // writing out what we THINK these will be named
  BOOST_LOG_SEV(glg, debug) << "Setting the organic thickness removed in ThermokarstData...";
  // >>> need to name td, and thermokarst_soid.removal_thickness
  tkdata->thermokarst_soid.removal_thickness = removal_thickness;

  BOOST_LOG_SEV(glg, info) << "Final calculated organic thickness removed: " << removal_thickness;
  return removal_thickness;
};

void Thermokarst::setCohortLookup(CohortLookup* chtlup) {
  chtlu = chtlup;
};

void Thermokarst::setCohortData(CohortData* cdp) {
  cd = cdp;
};

void Thermokarst::setAllEnvBgcData(EnvData* edp, BgcData *bdp) {
  edall = edp;
  bdall = bdp;
};

void Thermokarst::setBgcData(BgcData* bdp, const int &ip) {
  bd[ip] = bdp;
};

// >>> This needs to be changed to fit thermokarst data
void Thermokarst::setThermokarstData(ThermokarstData* tdp) {
  tkdata = tdp;
}