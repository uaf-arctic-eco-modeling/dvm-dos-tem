/*
 * Vegetation.cpp
 *
 * Purpose: Defining vegetation structure
 *
 * History:
 *   June 28, 2011, by F.-M. Yuan:
 *     (1) added for constructing vegetation domain (plant community)
 *
 * Important:
 *   (1) Parameters are read from 'CohortLookup.cpp', and set to
 *       'vegdimpar' (struct::vegpar_dim)
 *   (2) Here, all functions are on ALL pfts for ONE community. In this way,
 *       some complicated PFT interaction and dynamics/structure changing
 *       may be put here in the future.
 *
 */

#include "../include/Vegetation.h"

#include "../include/TEMUtilityFunctions.h"

#include "../include/TEMLogger.h"
extern src::severity_logger< severity_level > glg;

Vegetation::Vegetation() {


}

/** New style constructor. Building the right thing.

   Since we have the modelData (for config directory/file) and the cmtnumber
   we can lookup the appropriate values from the configuration file.
 */
Vegetation::Vegetation(int cmtnum, const ModelData* mdp) {


  // This seems horribly brittle now as it really depends on the order and
  // presence of the lines in the parameter file...

  BOOST_LOG_SEV(glg, note) << "Vegetation constructor. Community type: " << cmtnum;

  BOOST_LOG_SEV(glg, note) << "Setting Vegetation internal values from file: "
                           << mdp->parameter_dir << "cmt_dimvegetation.txt";


  // MAYBE WE DON'T NEED TO SET PARAMETERS HERE? -
  // They are set later in CohortLookup, and then read into the veg structure.

  // get a list of data for the cmt number
  std::list<std::string> l = temutil::parse_parameter_file(
      mdp->parameter_dir + "cmt_dimvegetation.txt", cmtnum, 40
  );


  // FIX THIS?? Why are some parameters not being set?? (ifwoody, etc..)

  // pop each line off the front of the list
  // and assign to the right data member.
  temutil::pfll2data_pft(l, vegdimpar.cov);
  l.pop_front(); // ifwoody
  l.pop_front(); // ifdeciwoody
  l.pop_front(); // ifperenial
  l.pop_front(); // nonvascular
  temutil::pfll2data_pft(l, vegdimpar.sla);
  temutil::pfll2data_pft(l, vegdimpar.klai);
  temutil::pfll2data_pft(l, vegdimpar.minleaf);
  temutil::pfll2data_pft(l, vegdimpar.aleaf);
  temutil::pfll2data_pft(l, vegdimpar.bleaf);
  temutil::pfll2data_pft(l, vegdimpar.cleaf);
  temutil::pfll2data_pft(l, vegdimpar.kfoliage);
  l.front();
  temutil::pfll2data_pft(l, vegdimpar.cov);
  temutil::pfll2data_pft(l, vegdimpar.m1);
  temutil::pfll2data_pft(l, vegdimpar.m2);
  temutil::pfll2data_pft(l, vegdimpar.m3);
  temutil::pfll2data_pft(l, vegdimpar.m4);

//  for (int i = 0; i < MAX_ROT_LAY; i++) {
//    temutil::pfll2data_pft(l, vegdimpar.frootfrac[i]);
//  }
//
//  temutil::pfll2data_pft(l, vegdimpar.lai);
//
//  for (int im = 0; im < MINY; im++) {
//    temutil::pfll2data_pft( l, vegdimpar.static_lai[im]);
//  }
}

Vegetation::~Vegetation() {
}

/**
 Set the bgc parameters from inputs stored in 'chtlu' - reuseable
 Note: here will remove those PFT with no greater than zero 'fpc'
       and initialize the total actual pft number
*/
void Vegetation::initializeParameter() {

  // This should probably be in the Ctor for a Vegetation object.
  
  for (int ip=0; ip<NUM_PFT; ip++) {
    // This will remove those PFTs with 0 ground coverage. So be cautious
    // the index consistent with 'state' variables!!
    if (chtlu->vegcov[ip] > 0.0) {
      vegdimpar.sla[ip] = chtlu->sla[ip];
      vegdimpar.klai[ip] = chtlu->klai[ip];
      vegdimpar.minleaf[ip] = chtlu->minleaf[ip];
      vegdimpar.aleaf[ip] = chtlu->aleaf[ip];
      vegdimpar.bleaf[ip] = chtlu->bleaf[ip];
      vegdimpar.cleaf[ip] = chtlu->cleaf[ip];
      vegdimpar.kfoliage[ip] = chtlu->kfoliage[ip];
      vegdimpar.cov[ip] = chtlu->cov[ip];
      vegdimpar.m1[ip] = chtlu->m1[ip];
      vegdimpar.m2[ip] = chtlu->m2[ip];
      vegdimpar.m3[ip] = chtlu->m3[ip];
      vegdimpar.m4[ip] = chtlu->m4[ip];
    }
  }
}

// set the initial states from inputs
void Vegetation::initializeState() {
  //
  for (int i=0; i<NUM_PFT; i++) {
    cd->m_veg.vegage[i]  = 0;
  }

  // from 'lookup'
  cd->hasnonvascular = false;

  for (int i=0; i<NUM_PFT; i++) {
    if (chtlu->vegcov[i] > 0.) {
      cd->m_veg.vegcov[i]      = chtlu->vegcov[i];
      cd->m_veg.ifwoody[i]     = chtlu->ifwoody[i];
      cd->m_veg.ifdeciwoody[i] = chtlu->ifdeciwoody[i];
      cd->m_veg.ifperenial[i]  = chtlu->ifperenial[i];
      cd->m_veg.nonvascular[i] = chtlu->nonvascular[i];

      if (cd->m_veg.nonvascular[i]>0) {  //checking and resetting
        cd->m_veg.ifwoody[i]     = 0;
        cd->m_veg.ifdeciwoody[i] = 0;
        cd->m_veg.ifperenial[i]  = 0;
      }

      if (cd->m_veg.nonvascular[i] > 0) {
        cd->hasnonvascular = true;
      }

      cd->m_veg.lai[i] = chtlu->initial_lai[i];

      for (int il=0; il<MAX_ROT_LAY; il++) {
        cd->m_veg.frootfrac[il][i] = chtlu->frootfrac[il][i]/100.0; // chtlu - in %
      }
    }
  }

  updateFpc();
  updateFrootfrac();
};

//set the initial states from restart inputs:
void Vegetation::set_state_from_restartdata(const RestartData & rd) {
  for (int ip=0; ip<NUM_PFT; ip++) {
    cd->m_veg.vegage[ip]      = rd.vegage[ip];
    cd->m_veg.vegcov[ip]      = rd.vegcov[ip];
    cd->m_veg.ifwoody[ip]     = rd.ifwoody[ip];
    cd->m_veg.ifdeciwoody[ip] = rd.ifdeciwoody[ip];
    cd->m_veg.ifperenial[ip]  = rd.ifperenial[ip];
    cd->m_veg.nonvascular[ip] = rd.nonvascular[ip];
    cd->m_veg.lai[ip]         = rd.lai[ip];

    for (int il=0; il<MAX_ROT_LAY; il++) {
      cd->m_veg.frootfrac[il][ip] = rd.rootfrac[il][ip];
    }

    cd->m_vegd.eetmx[ip]        = rd.eetmx[ip];
    cd->m_vegd.unnormleafmx[ip] = rd.unnormleafmx[ip];
    cd->m_vegd.growingttime[ip] = rd.growingttime[ip];
    cd->m_vegd.topt[ip]         = rd.topt[ip];
    cd->m_vegd.foliagemx[ip]    = rd.foliagemx[ip];
    cd->prveetmxque[ip].clear();

    for(int i=0; i<10; i++) {
      double eetmxa = rd.eetmxA[i][ip];
      // note: older value is in the lower position in the deque

      if(eetmxa!=MISSING_D) {
        cd->prveetmxque[ip].push_back(eetmxa);
      }
    }

    cd->prvunnormleafmxque[ip].clear();

    for(int i=0; i<10; i++) {
      double unleafmxa = rd.unnormleafmxA[i][ip];
      // note: older value is in the lower position in the deque

      if(unleafmxa!=MISSING_D) {
        cd->prvunnormleafmxque[ip].push_back(unleafmxa);
      }
    }

    cd->prvgrowingttimeque[ip].clear();

    for(int i=0; i<10; i++) {
      double growingttimea = rd.growingttimeA[i][ip];
      //note: older value is lower in the deque

      if(growingttimea!=MISSING_D) {
        cd->prvgrowingttimeque[ip].push_back(growingttimea);
      }
    }

    cd->toptque[ip].clear();

    for(int i=0; i<10; i++) {
      double topta = rd.toptA[i][ip];
      //note: older value is, lower in the deque

      if(topta!=MISSING_D) {
        cd->toptque[ip].push_back(topta);
      }
    }
  }

  updateFpc();
  updateFrootfrac();
};

// must be called after 'foliage' and 'leaf' updated
void Vegetation::updateLai(const int &currmind) {
  for(int ip=0; ip<NUM_PFT; ip++) {
    if (cd->m_veg.vegcov[ip]>0.) {
      if(!update_LAI_from_vegc) {
        cd->m_veg.lai[ip] = chtlu->static_lai[currmind][ip];
      } else {
        if (bd[ip]->m_vegs.c[I_leaf] > 0.0) {
          cd->m_veg.lai[ip] = vegdimpar.sla[ip] * bd[ip]->m_vegs.c[I_leaf];
        } else {
          if (ed[ip]->m_soid.rtdpgrowstart>0 && ed[ip]->m_soid.rtdpgrowend<0) {
            cd->m_veg.lai[ip] = 0.001; // this is needed for leaf emerging
          }
        }
      } 
    }
  }
}

// sum of all PFTs' fpc must be not greater than 1.0
void Vegetation::updateFpc() {
  double fpcmx = 0.;
  double fpcsum = 0.;
  double fpc[NUM_PFT];

  for(int ip=0; ip<NUM_PFT; ip++) {
    if (cd->m_veg.vegcov[ip]>0.) {
      double ilai = cd->m_veg.lai[ip];
      fpc[ip] = 1.0 - exp(-vegdimpar.klai[ip] * ilai);

      if (fpc[ip]>fpcmx) {
        fpcmx = fpc[ip];
      }

      fpcsum +=fpc[ip];
      cd->m_veg.fpc[ip] = fpc[ip];
    }
  }

  if (fpcsum > 1.0) {
    for(int ip=0; ip<NUM_PFT; ip++) {
      if (cd->m_veg.vegcov[ip]>0.) {
        cd->m_veg.fpc[ip] /= fpcsum;
      }
    }

    fpcsum = 1.0;
  }

  cd->m_vegd.fpcsum = fpcsum;
};

// vegetation coverage update (note - this is not same as FPC)
// and Here it's simply assumed as the max. foliage coverage projected on
//   ground throughout the whole plant lift-time shall be more working on
//   this in future
void Vegetation::updateVegcov() {
  double foliagecov = 0.;
  cd->hasnonvascular = false;

  for(int ip=0; ip<NUM_PFT; ip++) {
    double ilai = cd->m_veg.lai[ip];
    foliagecov = 1.0 - exp(-vegdimpar.klai[ip] * ilai);

    if (cd->m_veg.vegcov[ip]<foliagecov) {
      cd->m_veg.vegcov[ip]=foliagecov;
    }

    if (cd->m_veg.vegcov[ip]>1.e-5) {
      cd->m_veg.ifwoody[ip]     = chtlu->ifwoody[ip];
      cd->m_veg.ifdeciwoody[ip] = chtlu->ifdeciwoody[ip];
      cd->m_veg.ifperenial[ip]  = chtlu->ifperenial[ip];
      cd->m_veg.nonvascular[ip] = chtlu->nonvascular[ip];

      if (cd->m_veg.nonvascular[ip] > 0) {
        cd->hasnonvascular = true;
      }
    }
  }
};

//leaf phenology - moved from 'Vegetation_Bgc.cpp' for easy modification,
//  if needed in the future
void Vegetation::phenology(const int &currmind) {
  for(int ip=0; ip<NUM_PFT; ip++) {
    if (cd->m_veg.vegcov[ip]>0.) {
      double prvunnormleafmx = 0.;   // previous 10 years' average as below
      deque <double> prvdeque = cd->prvunnormleafmxque[ip];
      int dequeno = prvdeque.size();

      for (int i=0; i<dequeno; i++) {
        prvunnormleafmx +=prvdeque[i]/dequeno;
      }

      double prveetmx=0;
      prvdeque = cd->prveetmxque[ip];
      dequeno = prvdeque.size();

      for (int i=0; i<dequeno; i++) {
        prveetmx +=prvdeque[i]/dequeno;
      }

      // 1) current EET and previous max. EET controlled
      double tempunnormleaf = 0.;;
      double eet = ed[ip]->m_v2a.tran;//originally it's using 'l2a.eet', which
                                      //  includes soil/veg evaporation - that
                                      //  may not relate to leaf phenology
      tempunnormleaf = getUnnormleaf(ip, prveetmx, eet, cd->m_vegd.unnormleaf[ip]);
      cd->m_vegd.unnormleaf[ip] = tempunnormleaf;//prior to here, the
                                                 //  'unnormleaf[ip]' is from
                                                 //  the previous month
      double fleaf = getFleaf(ip, tempunnormleaf, prvunnormleafmx);

      if (cd->m_veg.lai[ip]<=0.) {
        fleaf = 0.;
      }

      cd->m_vegd.fleaf[ip] = fleaf;

      // set the phenological variables of the year
      if (currmind == 0) {
        cd->m_vegd.eetmx[ip] = eet;
        cd->m_vegd.unnormleafmx[ip] = tempunnormleaf;
        cd->m_vegd.growingttime[ip] = ed[ip]->m_soid.rtdpgdd;
        cd->m_vegd.topt[ip] = ed[ip]->m_atms.ta;
        cd->m_vegd.maxleafc[ip] = getYearlyMaxLAI(ip)/vegdimpar.sla[ip];
      } else {
        if (eet>cd->m_vegd.eetmx[ip]) {
          cd->m_vegd.eetmx[ip] = eet;
        }

        if (cd->m_vegd.unnormleafmx[ip] < tempunnormleaf) {
          cd->m_vegd.unnormleafmx[ip] = tempunnormleaf;

          /// The optimum temperature is set to be the month of maximum leaf area, 
          /// to allow for local adaptation/acclimation of photosynthesis. This allows the
          /// vegetation to optimize the temperature response of photosynthesis for each 
          /// grid cell based on the month of maximum leaf area for that grid cell. 
          /// A.D. McGuire thinks we first introduced this into TEM 4.0, but it wasn't 
          /// fully described until the publication of an application of TEM 4.1 in 
          /// Tian et al. (1999). See the paragraph that spans pages 445-446  in the 
          /// appendix of that paper. 
          /// Ref: H. Tian, J. M. Melillo, D. W. Kicklighter, A. D. McGuire & J. Helfrich (1999)
          /// The sensitivity of terrestrial carbon storage to historical climate variability and 
          /// atmospheric CO2 in the United States, Tellus B: Chemical and Physical Meteorology, 51:2, 414-452, 
          /// DOI: 10.3402/tellusb.v51i2.16318
          cd->m_vegd.topt[ip] = ed[ip]->m_atms.ta;
        }

        if (cd->m_vegd.growingttime[ip]<ed[ip]->m_soid.rtdpgdd) {
          //here, we take the top root zone degree-days since growing started
          cd->m_vegd.growingttime[ip]=ed[ip]->m_soid.rtdpgdd;
        }
      }

      //2) plant size (biomass C) or age controlled foliage fraction rative
      //   to the max. leaf C
      cd->m_vegd.ffoliage[ip] = getFfoliage(ip, cd->m_veg.ifwoody[ip],
                                            cd->m_veg.ifperenial[ip],
                                            bd[ip]->m_vegs.call);
    } else { // 'vegcov' is 0
      cd->m_vegd.unnormleaf[ip] = MISSING_D;
      cd->m_vegd.fleaf[ip] = MISSING_D;
      cd->m_vegd.eetmx[ip] = MISSING_D;
      cd->m_vegd.unnormleafmx[ip] = MISSING_D;
      cd->m_vegd.topt[ip] = MISSING_D;
      cd->m_vegd.maxleafc[ip] = MISSING_D;
      cd->m_vegd.growingttime[ip] = MISSING_D;
      cd->m_vegd.ffoliage[ip] = MISSING_D;
    }
  }
};

// functions for eet adjusted foliage growth index
// 'prvunleaf' is the unnormalized leaf from last time period
// 'prveetmx' is monthly eetmx of previous simulation period (year)

double Vegetation::getUnnormleaf(const int& ipft, double &prveetmx,
                                 const double & eet,
                                 const double & prvunleaf) {
  double normeet;
  double unnormleaf;

  if (prveetmx <= 0.0) {
    prveetmx = 1.0;
  }

  normeet = eet/prveetmx;

  if(normeet>1) {
    normeet =1;
  }

  unnormleaf = (vegdimpar.aleaf[ipft] * normeet)
               +(vegdimpar.bleaf[ipft] * prvunleaf)
               +vegdimpar.cleaf[ipft];

  if (unnormleaf < (0.5 * vegdimpar.minleaf[ipft])) {
    unnormleaf = 0.5 * vegdimpar.minleaf[ipft];
  }

  return unnormleaf;
};

//fleaf is normalized EET and previous EET determined phenology index 0~1
//i.e., f(phenology) in gpp calculation
double Vegetation::getFleaf(const int &ipft, const double & unnormleaf,
                            const double &prvunnormleafmx) {
  double fleaf;

  if (prvunnormleafmx <= 0.0) {
    fleaf = 0.0;
  } else {
    fleaf= unnormleaf/prvunnormleafmx;
  }

  if (fleaf < vegdimpar.minleaf[ipft] ) {
    fleaf = vegdimpar.minleaf[ipft];
  } else  if (fleaf > 1.0 ) {
    fleaf = 1.0;
  }

  return fleaf;
};

// function for biomass C adjusted foliage growth index (0 - 1.0)
double Vegetation::getFfoliage(const int &ipft, const bool & ifwoody,
                               const bool &ifperenial, const double &vegc) {
  double ffoliage =0;

  //if(!ifwoody) {
    if (!ifperenial) {
      ffoliage = 1.0; //annual: yearly max. not controlled by current plant
                      //  C biomass (because it dies every year)
    } else {
      ffoliage = 1.0 / (1.0 + vegdimpar.kfoliage[ipft] * exp(vegdimpar.cov[ipft] * vegc));
    }
  //  } else {
  //    //from Zhuang et al., 2003
  //    double m1 = vegdimpar.m1[ipft];
  //    double m2 = vegdimpar.m2[ipft];
  //    double m3 = vegdimpar.m3[ipft];
  //    double m4 = vegdimpar.m4[ipft];
  //    double fcv = m3*vegc /(1+m4*vegc);
  //    ffoliage =  1./(1+m1*exp(m2*sqrt(fcv)));
  //  }

  //it is assumed that foliage will not go down during a growth cycle
  if(ffoliage>cd->m_vegd.foliagemx[ipft]) {
    cd->m_vegd.foliagemx[ipft] = ffoliage;
  } else {
    ffoliage = cd->m_vegd.foliagemx[ipft];
  }

  return ffoliage;
};

// plant max. LAI function
double Vegetation::getYearlyMaxLAI(const int &ipft) {

  double laimax = 0.0;

  for (int im=0; im<12; im++) {//taking the max. of input 'static_lai[12]'
                               //  adjusted by 'vegcov'
//    double covlai = chtlu->static_lai[im][ipft]*cd->m_veg.vegcov[ipft];
      double covlai = chtlu->static_lai[im][ipft];
    if (laimax <= covlai) {
      laimax = covlai;
    }
  }

  laimax *= cd->m_vegd.ffoliage[ipft];
  return laimax;
}


// the following can be developed further for dynamical fine root distribution
// currently, it's only do some checking
void Vegetation::updateFrootfrac() {

  // Apparently loops over all PFTs and each PFT's 'artifical' soil layers
  // and then reset the frootfrac for the 'artifical' soil layers so that
  // the sum is up to 100%?
  // Not sure how useful this code is....

  for (int ip=0; ip<NUM_PFT; ip++) {
    if (cd->m_veg.vegcov[ip]>0.) {
      double totrootfrac = 0.;

      for (int il=0; il<MAX_ROT_LAY; il++) {
        if (cd->m_veg.frootfrac[il][ip]>0.) {
          totrootfrac += cd->m_veg.frootfrac[il][ip];
        }
      }

      if (totrootfrac > 0.0) {
        for (int il=0; il<MAX_ROT_LAY; il++) {
          cd->m_veg.frootfrac[il][ip] /= totrootfrac;
        }
      } else {
        for (int il=1; il<MAX_ROT_LAY; il++) {
          cd->m_veg.frootfrac[il][ip] = 0.0;
        }
      }
    } // end of 'vegcov[ip]>0'
  }
};


void Vegetation::setCohortLookup(CohortLookup* chtlup) {
  chtlu = chtlup;
};

void Vegetation::setCohortData(CohortData* cdp) {
  cd = cdp;
};

void Vegetation::setEnvData(const int &ip, EnvData* edp) {
  ed[ip] = edp;
};

void Vegetation::setBgcData(const int &ip, BgcData* bdp) {
  bd[ip] = bdp;
};
