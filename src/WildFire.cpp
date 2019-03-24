/*
 * WildFire.cpp
 *
 * This is for wildfire occurrence and C/N pool dynamics due to fire
 *   (1) Fire occurrence either by input or FRI derived
 *   (2) Fire severity either by ALFRESCO input, or determined by
 *         'size','season' and 'landscape position'
 *
 *   (3) C/N pools updated here through operation on 'bd' -
 *         NOTE this 'bd' is for all PFTs and soil.
 *         this is to say, individual PFT's C/N pools updating need to
 *         do elsewhere
 *
 *   (4) ROOTFRAC is updated here through operation on 'ed' - also for ALL PFTS.
 *
 *   (5) soil layer structure is NOT changed here, but will re-do in
 *         Ground::adjustSoilAfterBurn()
 *
 *   (6) NOTE: assuming ONE root pool, and its index is 'NUM_PFT_PART'
 *         (i.e. the last).
 *
 */

#include <string>
#include <sstream>

#include "../include/WildFire.h"

#include "../include/TEMUtilityFunctions.h"
#include "../include/TEMLogger.h"

extern src::severity_logger< severity_level > glg;

WildFire::WildFire() {}

WildFire::~WildFire() {}

WildFire::WildFire(const std::string& fri_fname,
                   const std::string& exp_fname, const double cell_slope,
                   const double cell_aspect, const double cell_elevation,
                   const int y, const int x) {

  #pragma omp critical(load_input)
  {
    BOOST_LOG_SEV(glg, info) << "Setting up FRI fire data...";
    this->fri = temutil::get_scalar<int>(fri_fname, "fri", y, x);
    this->fri_severity = temutil::get_scalar<int>(fri_fname, "fri_severity", y, x);
    this->fri_jday_of_burn = temutil::get_scalar<int>(fri_fname, "fri_jday_of_burn", y, x);
    this->fri_area_of_burn = temutil::get_scalar<int>(fri_fname, "fri_area_of_burn", y, x);
  }//End critical(fri)

  #pragma omp critical(load_input)
  {
    BOOST_LOG_SEV(glg, info) << "Setting up explicit fire data...";
    this->exp_burn_mask = temutil::get_timeseries<int>(exp_fname, "exp_burn_mask", y, x);
    this->exp_fire_severity = temutil::get_timeseries<int>(exp_fname, "exp_fire_severity", y, x);
    this->exp_jday_of_burn = temutil::get_timeseries<int>(exp_fname, "exp_jday_of_burn", y, x);
    this->exp_area_of_burn = temutil::get_timeseries<int>(exp_fname, "exp_area_of_burn", y, x);
  }//End critical(exp_fir) 

  this->slope = cell_slope;
  this->asp = cell_aspect;
  this->elev = cell_elevation;

  BOOST_LOG_SEV(glg, debug) << "Done making WildFire object.";
  BOOST_LOG_SEV(glg, debug) << this->report_fire_inputs();

}

/** Assemble and return a string with a bunch of data from this class */
std::string WildFire::report_fire_inputs() {

  std::stringstream report_string;
  report_string << "FRI based fire vectors/data:" << std::endl;
  report_string << "FRI:              " << this->fri << std::endl;
  report_string << "FRI jday_of_burn:  " << this->fri_jday_of_burn << std::endl;
  report_string << "FRI area_of_burn:  " << this->fri_area_of_burn << std::endl;
  report_string << "FRI severity:     " << this->fri_severity << std::endl;
  report_string << "exp fire vectors/data:" << std::endl;
  report_string << "explicit fire year:         [" << temutil::vec2csv(this->exp_burn_mask) << "]" << std::endl;
  report_string << "explicit fire jday_of_burn: [" << temutil::vec2csv(this->exp_jday_of_burn) << "]" << std::endl;
  report_string << "explicit fire area_of_burn: [" << temutil::vec2csv(this->exp_area_of_burn) << "]" << std::endl;
  report_string << "explicit fire severity:     [" << temutil::vec2csv(this->exp_fire_severity) << "]" << std::endl;


  return report_string.str();

}

// Looks like this is just used when setting up a Cohort...
void WildFire::initializeParameter() {
  for (int i=0; i<NUM_FSEVR; i++) {
    for (int ip=0; ip<NUM_PFT; ip++) {
      firpar.fvcomb[i][ip] = chtlu->fvcombust[i][ip];
      firpar.fvdead[i][ip] = chtlu->fvslash[i][ip];
    }

    firpar.foslburn[i] = chtlu->foslburn[i];
  }

  firpar.vsmburn = chtlu->vsmburn; // a threshold value of VWC for burn
                                   //   organic layers
  firpar.r_retain_c = chtlu->r_retain_c;
  firpar.r_retain_n = chtlu->r_retain_n;
};

void WildFire::initializeState() {
  fd->fire_a2soi.orgn = 0.0;
};

// Looks like this is just used when setting up a Cohort from a Restart file...
void WildFire::set_state_from_restartdata(const RestartData & rdata) {
  fd->fire_a2soi.orgn = rdata.firea2sorgn;
}


/** Figure out whether or not there should be a fire, based on stage, yr, month.
 *
 *  There are two modes of operation: "FRI" (fire recurrence interval) and
 *  "exp". Pre-run, equilibrium, and spin-up stages all use the FRI settings
 *  for determining whether or not a fire should ignite, while transient and 
 *  scenario stages use explicit dates for fire occurrence.
 *
 *  The settings for FRI and the data for explicit fire dates are held in data
 *  members of this (WildFire) object. This function looks at those data
 *  and sets the "actual_severity" member accordingly.
 *
 *  NOTE: how to handle fire severity, to be determined.
 *
*/
bool WildFire::should_ignite(const int yr, const int midx, const std::string& stage) {

  BOOST_LOG_SEV(glg, note) << "determining fire ignition for yr:" << yr
                           << ", monthidx:" << midx << ", stage:" << stage;

  bool ignite = false;
  bool fri_derived = false;

  if ( stage.compare("pre-run") == 0 || stage.compare("eq-run") == 0 || stage.compare("sp-run") == 0 ) {

    this->fri_derived = true;
    BOOST_LOG_SEV(glg, debug) << "Determine fire from FRI.";

    if ( (yr % this->fri) == 0 && yr > 0 ) {
      if (midx == temutil::doy2month(this->fri_jday_of_burn)) {
        ignite = true;
      }
      // do nothing: correct year, wrong month.
    }

  } else if ( stage.compare("tr-run") == 0 || stage.compare("sc-run") == 0 ) {

    this->fri_derived = false;
    BOOST_LOG_SEV(glg, debug) << "Determine fire from explicit fire regime.";

    if ( this->exp_burn_mask[yr] == 1 ){
      if ( temutil::doy2month(this->exp_jday_of_burn[yr]) == midx ) {
        ignite = true;
      }
      // do nothing: correct year, wrong month
    }
  } else {
    BOOST_LOG_SEV(glg, err) << "Unknown stage! (" << stage << ")";
  }

  BOOST_LOG_SEV(glg, debug) << "Should we ignite a fire?:" << ignite;

  return ignite;
}

/** Burning vegetation and soil organic C */
void WildFire::burn(int year) {
  BOOST_LOG_NAMED_SCOPE("burning");
  BOOST_LOG_SEV(glg, note) << "HELP!! - WILD FIRE!! RUN FOR YOUR LIFE!";

  BOOST_LOG_SEV(glg, debug) << fd->report_to_string("Before WildFire::burn(..)");
  BOOST_LOG_SEV(glg, note) << "Burning (simply clearing?) the 'FireData object...";
  fd->burn();
  BOOST_LOG_SEV(glg, debug) << fd->report_to_string("After FirData::burn(..)");
  
  // for soil part and root burning
  // FIX: there isn't really a reason for getBurnOrgSoilthick to return a value
  // as it has already set the "burn thickness" value in FirData...
  double burndepth = getBurnOrgSoilthick(year);
  BOOST_LOG_SEV(glg, debug) << fd->report_to_string("After WildFire::getBurnOrgSoilthick(..)");

  BOOST_LOG_SEV(glg, note) << "Setup some temporary pools for tracking various burn related attributes (depths, C, N)";
  double totbotdepth = 0.0;
  double burnedsolc = 0.0;
  double burnedsoln = 0.0;
  double r_burn2bg_cn[NUM_PFT]; // ratio of dead veg. after burning
  for (int ip=0; ip<NUM_PFT; ip++) {
    r_burn2bg_cn[ip] = 0.; //  used for vegetation below-ground (root) loss,
                           //  and calculated below
  }

  BOOST_LOG_SEV(glg, debug) << "Handle burning the soil (loop over all soil layers)...";
  for (int il = 0; il < cd->m_soil.numsl; il++) {

    BOOST_LOG_SEV(glg, debug) << "== Layer Info == "
                              << "   type:" << cd->m_soil.type[il] // 0:moss 1:shlwpeat 2:deeppeat 3:mineral
                              << "   dz:" << cd->m_soil.dz[il]
                              << "   top:" << cd->m_soil.z[il]
                              << "   bottom:"<< cd->m_soil.z[il] + cd->m_soil.dz[il];

    if(cd->m_soil.type[il] <= 2) {

      totbotdepth += cd->m_soil.dz[il];

      double ilsolc =  bdall->m_sois.rawc[il] + bdall->m_sois.soma[il] +
                       bdall->m_sois.sompr[il] + bdall->m_sois.somcr[il];

      double ilsoln =  bdall->m_sois.orgn[il] + bdall->m_sois.avln[il];

      if(totbotdepth <= burndepth) { //remove all the orgc/n in this layer
        BOOST_LOG_SEV(glg, debug) << "Haven't reached burndepth (" << burndepth << ") yet. Remove all org C and N in this layer";
        burnedsolc += ilsolc;
        burnedsoln += ilsoln;
        bdall->m_sois.rawc[il] = 0.0;
        bdall->m_sois.soma[il] = 0.0;
        bdall->m_sois.sompr[il]= 0.0;
        bdall->m_sois.somcr[il]= 0.0;
        bdall->m_sois.orgn[il] = 0.0;
        bdall->m_sois.avln[il] = 0.0;

        for (int ip=0; ip<NUM_PFT; ip++) {
          if (cd->m_veg.vegcov[ip]>0.) {
            r_burn2bg_cn[ip] += cd->m_soil.frootfrac[il][ip];
            cd->m_soil.frootfrac[il][ip] = 0.0;
          }
        }
      } else {
        BOOST_LOG_SEV(glg, debug) << "The bottom of this layer (il: " << il << ") is past the 'burndepth'. Find the remaining C and N as a fraction of layer thickness";
        double partleft = totbotdepth - burndepth;

        // Calculate the remaining C, N
        if (partleft < cd->m_soil.dz[il]) { // <-- Maybe this should be an assert instead of an if statement??
          BOOST_LOG_SEV(glg, debug) << "Burning all but "<<partleft<<"of layer "<<il;
          burnedsolc += (1.0-partleft/cd->m_soil.dz[il]) * ilsolc;
          burnedsoln += (1.0-partleft/cd->m_soil.dz[il]) * ilsoln;
          bdall->m_sois.rawc[il] *= partleft/cd->m_soil.dz[il];
          bdall->m_sois.soma[il] *= partleft/cd->m_soil.dz[il];
          bdall->m_sois.sompr[il] *= partleft/cd->m_soil.dz[il];
          bdall->m_sois.somcr[il] *= partleft/cd->m_soil.dz[il];
          bdall->m_sois.orgn[il] *= partleft/cd->m_soil.dz[il];
          bdall->m_sois.avln[il] *= partleft/cd->m_soil.dz[il];

          for (int ip=0; ip<NUM_PFT; ip++) {
            if (cd->m_veg.vegcov[ip] > 0.0) {
              r_burn2bg_cn[ip] += (1-partleft/cd->m_soil.dz[il])
                                * cd->m_soil.frootfrac[il][ip];
              cd->m_soil.frootfrac[il][ip] *= partleft/cd->m_soil.dz[il];
            }
          }
        } else {
          // should never get here??
          BOOST_LOG_SEV(glg, err) << "The remaining soil after a burn is greater than the thickness of this layer. Something is wrong??";
          BOOST_LOG_SEV(glg, err) << "partleft: " << partleft << "cd->m_soil.dz["<<il<<"]: " << cd->m_soil.dz[il];
          break;
        }
      }
    } else {   //Mineral soil layers
      BOOST_LOG_SEV(glg, note) << "Layer type:" << cd->m_soil.type[il] << ". Should be a non-organic soil layer? (greater than type 2)";
      BOOST_LOG_SEV(glg, note) << "Not much to do here. Can't really burn non-organic layers.";

      if(totbotdepth <= burndepth) { //may not be needed, but just in case
        BOOST_LOG_SEV(glg, note) << "For some reason totbotdepth <= burndepth, so we are setting fd->fire_soid.burnthick = totbotdepth??";
        fd->fire_soid.burnthick = totbotdepth;
      }
    }
  } // end soil layer loop

  //Setting relative organic layer burn (rolb) value
  fd->fire_soid.rolb = fd->fire_soid.burnthick / totbotdepth;

  // needs to re-do the soil rootfrac for each pft which was modified above
  //   (in burn soil layer)
  BOOST_LOG_SEV(glg, note) << "Re-do the soil root fraction for each PFT modified by burning?";
  for (int ip = 0; ip < NUM_PFT; ip++) {
    double rootfracsum = 0.0;

    for (int il = 0; il < cd->m_soil.numsl; il++) {
      rootfracsum += cd->m_soil.frootfrac[il][ip];
    }

    for (int il =0; il <cd->m_soil.numsl; il++) {
      cd->m_soil.frootfrac[il][ip] /= rootfracsum;
    }
  }

  // all woody debris will burn out
  BOOST_LOG_SEV(glg, note) << "Handle burnt woody debris...";
  double wdebrisc = bdall->m_sois.wdebrisc; //
  double wdebrisn = bdall->m_sois.wdebrisn; //
  bdall->m_sois.wdebrisc = 0.0;
  bdall->m_sois.wdebrisn = 0.0;

  // summarize
  BOOST_LOG_SEV(glg, note) << "Summarize...?";
  double vola_solc = burnedsolc * (1.0 - firpar.r_retain_c) + wdebrisc;
  double vola_soln = burnedsoln * (1.0 - firpar.r_retain_n) + wdebrisn;
  double reta_solc = burnedsolc * firpar.r_retain_c;   //together with veg.-burned C return, This will be put into soil later
  double reta_soln = burnedsoln * firpar.r_retain_n;   //together with veg.-burned N return, This will be put into soil later

  BOOST_LOG_SEV(glg, note) << "Handle Vegetation burning and mortality...";
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
      BOOST_LOG_SEV(glg, note) << "Some of PFT"<<ip<<" exists (coverage > 0). Burn it!";

      // vegetation burning/dead/living fraction for above-ground
      getBurnAbgVegetation(ip, year);

      // root death ratio: must be called after both above-ground and
      // below-ground burning. r_live_cn is same for both above-ground
      // and below-ground
      double r_dead2bg_cn = 1.0-r_burn2bg_cn[ip]-r_live_cn;

      // Dead veg C, N. Assuming all previous deadc burned.
      comb_deadc += bd[ip]->m_vegs.deadc;
      // Assuming all previous deadn burned
      comb_deadn += bd[ip]->m_vegs.deadn;
      
      //Zeroing the standing dead pools
      bd[ip]->m_vegs.deadc0 = 0.0;
      bd[ip]->m_vegs.deadn0 = 0.0;

      veg_2_dead_C = (bd[ip]->m_vegs.c[I_leaf] + bd[ip]->m_vegs.c[I_stem]) * r_dead2ag_cn;
      veg_2_dead_N = (bd[ip]->m_vegs.strn[I_leaf] + bd[ip]->m_vegs.strn[I_stem]) * r_dead2ag_cn;

      // Above-ground veg. burning/death during fire
      // when summing, needs adjusting by 'vegcov'
      comb_vegc += bd[ip]->m_vegs.c[I_leaf] * r_burn2ag_cn;

      // We define dead c/n as the not-falling veg (or binding with living veg)
      // during fire,
      bd[ip]->m_vegs.deadc = bd[ip]->m_vegs.c[I_leaf] * r_dead2ag_cn;
      // Which then is the source of ground debris (this is for woody plants
      // only, others could be set deadc/n to zero)
      bd[ip]->m_vegs.c[I_leaf] *= (1.0 - r_burn2ag_cn - r_dead2ag_cn);

      comb_vegc += bd[ip]->m_vegs.c[I_stem] * r_burn2ag_cn;
      bd[ip]->m_vegs.deadc += bd[ip]->m_vegs.c[I_stem] * r_dead2ag_cn;
      bd[ip]->m_vegs.c[I_stem] *= (1.0 - r_burn2ag_cn-r_dead2ag_cn);

      comb_vegn += bd[ip]->m_vegs.strn[I_leaf] * r_burn2ag_cn;
      bd[ip]->m_vegs.deadn += bd[ip]->m_vegs.strn[I_leaf] * r_dead2ag_cn;
      bd[ip]->m_vegs.strn[I_leaf] *= (1.0 - r_burn2ag_cn-r_dead2ag_cn);

      comb_vegn += bd[ip]->m_vegs.strn[I_stem] * r_burn2ag_cn;
      bd[ip]->m_vegs.deadn += bd[ip]->m_vegs.strn[I_stem] * r_dead2ag_cn;
      bd[ip]->m_vegs.strn[I_stem] *= (1.0 - r_burn2ag_cn - r_dead2ag_cn);

      // Below-ground veg. (root) burning/death during fire
      comb_vegc += bd[ip]->m_vegs.c[I_root] * r_burn2bg_cn[ip];
      comb_vegn += bd[ip]->m_vegs.strn[I_root] * r_burn2bg_cn[ip];

      // For the dead below-ground C caused by fire, they are put into original layer
      double deadc_tmp = bd[ip]->m_vegs.c[I_root]*r_dead2bg_cn;
      for (int il = 0; il < cd->m_soil.numsl; il++) {
        if (cd->m_soil.frootfrac[il][ip] > 0.0) {
          //for this, 'rootfrac' must be updated above
          bdall->m_sois.somcr[il] += deadc_tmp * cd->m_soil.frootfrac[il][ip];
        }
      }
      dead_bg_vegc += deadc_tmp;
      bd[ip]->m_vegs.c[I_root] *= (1.0 - r_burn2bg_cn[ip] - r_dead2bg_cn);

      // For the dead below-ground N caused by fire, they are put into original layer
      double deadn_tmp = bd[ip]->m_vegs.strn[I_root] * r_dead2bg_cn; //this is needed below
      for (int il =0; il <cd->m_soil.numsl; il++) {
        if (cd->m_soil.frootfrac[il][ip] > 0.0) {
          //for this, 'rootfrac' must be updated above
          bdall->m_sois.somcr[il] += deadn_tmp*cd->m_soil.frootfrac[il][ip];
        }
      }
      dead_bg_vegn +=deadn_tmp;
      bd[ip]->m_vegs.strn[I_root] *= (1.0 - r_burn2bg_cn[ip] - r_dead2bg_cn);

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

  double reta_vegc = (comb_vegc + comb_deadc) * firpar.r_retain_c;
  double reta_vegn = (comb_vegn + comb_deadn) * firpar.r_retain_n;

  //Writing out initial standing dead pools. These values will be
  //used to compute the rate of decomposition of the standing dead - 
  //1/9th of the original value per year.
  //bdall->m_vegs.deadc0 = veg_2_dead_C;
  //bdall->m_vegs.deadn0 = veg_2_dead_N;

  //Writing out initial values of standing dead pools to the pools
  //actually used for computation. These values will be decremented
  //by 1/9th the original value per year.
  //bdall->m_vegs.deadc = veg_2_dead_C;
  //bdall->m_vegs.deadn = veg_2_dead_N;

  BOOST_LOG_SEV(glg, note) << "Save the fire emission and return data into 'fd'...";
  //Summing the PFT specific fluxes to dead standing
  for(int ip=0; ip<NUM_PFT; ip++){
    fd->fire_v2dead.vegC += bd[ip]->m_vegs.deadc;
    fd->fire_v2dead.strN += bd[ip]->m_vegs.deadn;
  }
  //fd->fire_v2dead.vegC = veg_2_dead_C; 
  //fd->fire_v2dead.strN = veg_2_dead_N;
  fd->fire_v2a.orgc =  comb_vegc - reta_vegc;
  fd->fire_v2a.orgn =  comb_vegn - reta_vegn;
  fd->fire_v2soi.abvc = reta_vegc;
  fd->fire_v2soi.abvn = reta_vegn;
  fd->fire_v2soi.blwc = dead_bg_vegc;
  fd->fire_v2soi.blwn = dead_bg_vegn;
  fd->fire_soi2a.orgc = vola_solc;
  fd->fire_soi2a.orgn = vola_soln;

  // the above 'v2a.orgn' and 'soi2a.orgn', will be as one of N source,
  // which is depositing into soil evenly in one FRI
  //- this will let the system -N balanced in a long-term, if NO
  //  open-N cycle included
  //This should occur every month post-fire. FIX
  fd->fire_a2soi.orgn = (fd->fire_soi2a.orgn + fd->fire_v2a.orgn) / this->fri;


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


// above ground burning ONLY, based on fire severity indirectly or directly
void WildFire::getBurnAbgVegetation(const int ipft, const int year) {
  
  BOOST_LOG_SEV(glg, note) << "Lookup the above ground vegetation burned as a funciton of severity.";
  BOOST_LOG_SEV(glg, note) << " - Set the ratios for 'burn to above ground C,N' and 'dead to above ground C,N' member variables.";
  BOOST_LOG_SEV(glg, note) << " - Set the 'ratio live cn' member variable";

  // Yuan: the severity categories are from ALFRESCO:
  // 0 - no burning
  // 1 - low
  // 2 - moderate
  // 3 - high + low surface
  // 4 - high + high surface

//  this->r_burn2ag_cn = firpar.fvcomb[severity][ip];
//  this->r_dead2ag_cn = firpar.fvdead[severity][ip];

  if ( this->fri_derived ) {                    // FRI-derived fire regime
    if (this->fri_severity >= 0) {              // fire severity is available from the input files - so get fvcomb and fvdead from the parameter file;
      this->r_burn2ag_cn = firpar.fvcomb[this->fri_severity][ipft];
      this->r_dead2ag_cn = firpar.fvdead[this->fri_severity][ipft];
    }else {                                     // fire severity is available from the input files - apply the lookup table from Yi et al. 2010;
      if( cd->drainage_type == 0 ) {            // 0: well-drained; 1: poorly-drained;
        if ( this->fri_jday_of_burn <= 212 ) {   // Early fire, before July 31st (from Turetsly et al. 2011);
          if ( this->fri_area_of_burn < 1.0 ) { // Small fire year (less that 1% of the area burned);
            this->r_burn2ag_cn = 0.16;
            this->r_dead2ag_cn = 0.76;
          } else {
            this->r_burn2ag_cn = 0.24;
            this->r_dead2ag_cn = 0.75;
          }
        } else {                                // late fire (after July 31st);
          this->r_burn2ag_cn = 0.32;
          this->r_dead2ag_cn = 0.67;
        } 
      } else {                                  // lowland;
        this->r_burn2ag_cn = 0.16;
        this->r_dead2ag_cn = 0.76;
      } 
    }
  } else {                                      // Explicit fire regime;
    if (this->exp_fire_severity[year] >= 0) {    // fire severity is available from the input files - so get folb from the parameter file;
      this->r_burn2ag_cn = firpar.fvcomb[this->exp_fire_severity[year]][ipft];
      this->r_dead2ag_cn = firpar.fvdead[this->exp_fire_severity[year]][ipft];
    } else {  
      if( cd->drainage_type == 0 ) {            // 0: well-drained; 1: poorly-drained;
        if ( this->fri_jday_of_burn <= 212 ) {   // Early fire, before July 31st (from Turetsly et al. 2011);
          if ( this->fri_area_of_burn < 1.0 ) { // Small fire year (less that 1% of the area burned);
            this->r_burn2ag_cn = 0.16;
            this->r_dead2ag_cn = 0.76;
          } else {
            this->r_burn2ag_cn = 0.24;
            this->r_dead2ag_cn = 0.75;
          }
        } else {                                // late fire (after July 31st);
          this->r_burn2ag_cn = 0.32;
          this->r_dead2ag_cn = 0.67;
        } 
      } else {                                  // lowland;
        this->r_burn2ag_cn = 0.16;
        this->r_dead2ag_cn = 0.76;
      } 
    }
  }

  this->r_live_cn = 1.0 - this->r_burn2ag_cn - this->r_dead2ag_cn;
}


/** Find the thickness of organic soil to burn.
* Use severity (lookup? or derive?) and soil moisture prpoperties
* (volumetric soil moisture).
* Three rules:
*   1. only organic layer can be burned
*   2. can't exceed a pixel specified 'max burn thickness'
*   3. should not burn into "wet" organic soil layers
*/
double WildFire::getBurnOrgSoilthick(const int year) {


  BOOST_LOG_SEV(glg, info) << "Find the amount of organic soil that is burned as a function of fire severity.";
//assert((0 <= severity && severity < 5) && "Invalid fire severity! ");

  double burn_thickness = 0.0;

  //  For now, severity class is based on ALFRESCO:
  //  0 - no burning
  //  1 - low
  //  2 - moderate
  //  3 - high + low surface
  //  4 = high + high surface

  double total_organic_thickness =  cd->m_soil.mossthick
                                    + cd->m_soil.shlwthick
                                    + cd->m_soil.deepthick ;

  BOOST_LOG_SEV(glg, debug) << "Total organic thickness: " << total_organic_thickness;

  //compute the fraction of OL to burn FOLB
  double folb = 0.0;

  if ( this->fri_derived ) {                    // FRI-derived fire regime
    if (this->fri_severity >= 0) {              // fire severity is available from the input files - so get folb from the parameter file;
      folb = firpar.foslburn[this->fri_severity];
    }else {                                     // fire severity is available from the input files - apply the lookup table from Yi et al. 2010;
      if( cd->drainage_type == 0 ) {            // 0: well-drained; 1: poorly-drained;
        if ( this->fri_jday_of_burn <= 212 ) {   // Early fire, before July 31st (from Turetsly et al. 2011);
          if ( this->fri_area_of_burn < 1.0 ) { // Small fire year (less that 1% of the area burned);
            folb = 0.54;
          } else {
            folb = 0.69;
          }
        } else {                                // late fire (after July 31st);
          folb = 0.80;
        } 
      } else {                                  // lowland;
        folb = 0.48;
      } 
    }
  } else {                                      // Explicit fire regime;
    if (this->exp_fire_severity[year] >= 0) {    // fire severity is available from the input files - so get folb from the parameter file;
      folb = firpar.foslburn[this->exp_fire_severity[year]];
    } else {  
      if ( cd->cmttype > 3) {                   // tundra ecosystems: Mack et al. 2011;
        folb = 0.01*((21.5-6.1)/21.5);
      } else {                                  // boreal forest: Genet et al.2013;
         if(this->slope<2){
          folb = 0.1276966713-0.0319397467*this->slope+0.0020914862*this->exp_jday_of_burn[year]+0.0127016155* log(this->exp_area_of_burn[year]);
        } else {
          folb = -0.2758306315+0.0117609336*this->slope-0.0744057680*cos(this->asp * 3.14159265 / 180 ) +0.0260221684*edall->m_soid.tshlw+0.0011413114*this->exp_jday_of_burn[year]+0.0336302905*log (this->exp_area_of_burn[year]);
        }
      }
    }
  }

  if (folb > 1.0) folb=1.0;
  if (folb < 0.0) folb=0.0;


  //  Lookup burn thickness, based on severity and
  //  'fraction organic soil layer burned' parameter.
  //  (foslburn ==> "fraction organic soil layer burned")
  //burn_thickness = firpar.foslburn[severity] * total_organic_thickness;


  burn_thickness = folb * total_organic_thickness;

  BOOST_LOG_SEV(glg, debug) << "Calc burn thickness (severity): " << burn_thickness;

  //  VSM constrained burn thickness
  //  Find all layers where there is not much volumentric water - infact, less
  //  water than specified in the fire parameters for 'vmsburn'
  double total_dry_organic_thickness = 0.0;

  for (int i = 0; i < cd->m_soil.numsl; i++) {
    // 0:moss, 1:shlw peat, 2:deep peat, 3:mineral
    if( cd->m_soil.type[i] <= 2 ) {
      if (edall->m_soid.vwc[i] <= (firpar.vsmburn * cd->m_soil.por[i]) ) {
        total_dry_organic_thickness += cd->m_soil.dz[i];
      }
      // layer is too wet to burn
      // will all layers below this be too wet?
      // should we break the layer loop here?

    } else {
      break; // can't burn mineral soil
    }
  }
  if ( burn_thickness > total_dry_organic_thickness ) {
    burn_thickness = total_dry_organic_thickness;
    BOOST_LOG_SEV(glg, debug) << "Whoops! Burn thickness was greater than the thickness of dry organic material. Constraining burn thickness...";
  }
  BOOST_LOG_SEV(glg, debug) << "Calculated burn thickness using VSM constraint: " << burn_thickness;


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

  BOOST_LOG_SEV(glg, debug) << "Setting the burn thickness in FirData...";
  fd->fire_soid.burnthick = burn_thickness;

  BOOST_LOG_SEV(glg, info) << "Final Calculated Organic Burn Thickness: " << burn_thickness;
  return burn_thickness;
};

void WildFire::setCohortLookup(CohortLookup* chtlup) {
  chtlu = chtlup;
};

void WildFire::setCohortData(CohortData* cdp) {
  cd = cdp;
};

void WildFire::setAllEnvBgcData(EnvData* edp, BgcData *bdp) {
  edall = edp;
  bdall = bdp;
};

void WildFire::setBgcData(BgcData* bdp, const int &ip) {
  bd[ip] = bdp;
};

void WildFire::setFirData(FirData* fdp) {
  fd =fdp;
}

int WildFire::getFRI(){
  return fri;
}

