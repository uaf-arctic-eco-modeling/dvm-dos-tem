/*
 * Soil_Bgc.cpp
 *
 * Purpose: Calculating Soil C and N changes
 *
 * History:
 *   June 28, 2011, by F.-M. Yuan:
 *     (1) Recoding based on DOS-TEM's code;
 *     (2) Multiple soil layer C&N pools added
 *
 * Important:
 *   (1) Parameters are read from 'CohortLookup.cpp', and set
 *       to 'bgcpar' (struct::soipar_bgc)
 *   (2) Calibrated Parameters are also read from 'CohortLookup.cpp'
 *       initially, and set to 'calpar' (struct::soipar_cal)
 *
 *   (3) The calculation is for ONE community with multple PFT.
 *
 *   (4) FOUR (4) data pointers must be initialized by calling
 *       corresponding 'set...' methods
 *          chtlu, ed, bd, fd
 *
 */

#include "../include/TEMLogger.h"

#include "../include/Soil_Bgc.h"

extern src::severity_logger< severity_level > glg;

/** New constructor. Build it complete! Build it right! */
Soil_Bgc::Soil_Bgc(): nfeed(false), avlnflg(false), baseline(false),
                      d2wdebrisc(UIN_D), d2wdebrisn(UIN_D),
                      mossdeathc(UIN_D), mossdeathn(UIN_D), kdshlw(UIN_D),
                      kddeep(UIN_D), decay(UIN_D), nup(UIN_D), totdzliq(UIN_D),
                      totdzavln(UIN_D), totnetnmin(UIN_D), totnextract(UIN_D) {

  // all structs are value initialized to -77777
  
  for (int i = 0; i < MAX_SOI_LAY; ++i) {
    ltrflc[i] = UIN_D;
    ltrfln[i] = UIN_D;
    rtnextract[i] = UIN_D;
  }

};



Soil_Bgc::~Soil_Bgc() {
};

/** Writes Carbon values from the bd structure (BGC Data) into each soil layer 
    held in the Ground object.
*/
void Soil_Bgc::assignCarbonBd2LayerMonthly() {
  Layer* currl = ground->fstsoill;

  while(currl!=NULL) {
    if(currl->isSoil) {
      currl->rawc  =  bd->m_sois.rawc[currl->solind-1];
      currl->soma  =  bd->m_sois.soma[currl->solind-1];
      currl->sompr =  bd->m_sois.sompr[currl->solind-1];
      currl->somcr =  bd->m_sois.somcr[currl->solind-1];
    } else {
      break;
    }

    currl = currl->nextl;
  }

  ground->organic.shlwc = bd->m_soid.shlwc;
  ground->organic.deepc = bd->m_soid.deepc;

  // What about mineral C ??
}

/** Writes Carbon values from each of the Ground object's Layers into the bd 
    structure (BGC Data).
*/
void Soil_Bgc::assignCarbonLayer2BdMonthly() {
  Layer* currl = ground->fstsoill;
  int lstprocessedlayer = 0;

  while(currl!=NULL) {
    if(currl->isSoil) {
      lstprocessedlayer = currl->solind-1;
      bd->m_sois.rawc[currl->solind-1] = currl->rawc;
      bd->m_sois.soma[currl->solind-1] = currl->soma;
      bd->m_sois.sompr[currl->solind-1]= currl->sompr;
      bd->m_sois.somcr[currl->solind-1]= currl->somcr;
    } else {
      break;
    }

    currl = currl->nextl;
  }

  for(int il = lstprocessedlayer+1; il<MAX_SOI_LAY; il++) {
    bd->m_sois.rawc[il] = 0.0;
    bd->m_sois.soma[il] = 0.0;
    bd->m_sois.sompr[il] = 0.0;
    bd->m_sois.somcr[il] = 0.0;
  }

}

void Soil_Bgc::prepareIntegration(const bool &mdnfeedback,
                                  const bool &mdavlnflg,
                                  const bool &mdbaseline) {
  this->set_nfeed(mdnfeedback);
  this->set_avlnflg(mdavlnflg);
  this->set_baseline(mdbaseline);

  // moss death rate if any (from Vegetation_bgc.cpp)
  mossdeathc    = bd->m_v2soi.mossdeathc;
  mossdeathn    = bd->m_v2soi.mossdeathn;

  // litter-fall C/N from Vegetation_bgc.cpp
  double blwlfc = bd->m_v2soi.ltrfalc[I_root];
  double abvlfc = fmax(0., bd->m_v2soi.ltrfalcall - blwlfc);
  double blwlfn = bd->m_v2soi.ltrfaln[I_root];
  double abvlfn = fmax(0., bd->m_v2soi.ltrfalnall - blwlfn);

  // Maybe the "below" calc should be done like this?:
  // double abvlfc = bd->m_v2soi.ltrfalc[I_stem] + bd->m_v2soi.ltrfalc[I_leaf];
  // double abvlfn = bd->m_v2soi.ltrfaln[I_stem] + bd->m_v2soi.ltrfaln[I_leaf];

  for(int i=0; i<cd->m_soil.numsl; i++) {
    //FIX litterfall should be added to the shallow layer
    //There *must* be a shallow layer
    //if(fstshlwl!=NULL). if(currl->isShlw() && prevl != shlw)
    //  add abvlfc and this shallow layer's blwlfc fraction
    //else
    //  just root death?
    //else if fstshlwl==NULL and there is litterfall, ERROR
    //if (cd->m_soil.type[i]>0) { WRONG
    //soillayer sl = ground ;lksadjf; [i];

    if( (i==0 && cd->m_soil.type[i]==1) ||
        ((i>0 && cd->m_soil.type[i]==1) && (cd->m_soil.type[i-1]!=1)) ) {
      // always put the litterfall from vascular and moss in the
      // first non-moss soil layer
      ltrflc[i] = abvlfc + bd->m_v2soi.mossdeathc + bd->m_v2soi.rtlfalfrac[i] * blwlfc;

      ltrfln[i] = abvlfn + bd->m_v2soi.mossdeathn + bd->m_v2soi.rtlfalfrac[i] * blwlfn;
      abvlfc = 0.;
      abvlfn = 0.;
    } else if(cd->m_soil.type[i]>0) {
      // root death is directly put into each soil layer
      ltrflc[i] = bd->m_v2soi.rtlfalfrac[i] * blwlfc;

      ltrfln[i] = bd->m_v2soi.rtlfalfrac[i] * blwlfn;
    }

    if (ltrflc[i]>0. && ltrfln[i]> 0.) {
      bd->m_soid.ltrfcn[i] = ltrflc[i]/ltrfln[i];
    } else {
      bd->m_soid.ltrfcn[i] = 0.0;
    }
  }

  //SOM decompositin Kd will updated based on previous 12
  //  month accumulative littering C/N
  updateKdyrly4all();

  if (this->nfeed == 1) {
    // vegetation root N extraction
    for (int i=0; i<cd->m_soil.numsl; i++) {
      rtnextract[i] = bd->m_soi2v.nextract[i];
    }

    //soil liq. water controlling factor for soil N
    //  minralization/immobilization and root N extraction
    for (int i=0; i<cd->m_soil.numsl; i++) {
      bd->m_soid.knmoist[i] = getKnsoilmoist(ed->m_soid.sws[i]);
    }

    //prepare total liq water and available N in soil zones above drainage depth
    //In this version of model, N leaching loss is assumed to with
    // drainage flow from all above-drainage profile as the
    // drainage zone - needs improvement here!
    totdzliq     = 0.;
    totdzavln    = 0.;

    for(int i=0; i<cd->m_soil.numsl; i++) {
      if((cd->m_soil.z[i]+cd->m_soil.dz[i]) <= ed->m_sois.draindepth) { //note: z is at the top of a layer
        totdzliq += fmax(0., ed->m_sois.liq[i]);
        totdzavln += fmax(0., bd->m_sois.avln[i]);
      } else {
        if (cd->m_soil.z[i]<ed->m_sois.draindepth) { //note: z is at the top of a layer
          double fdz = (ed->m_sois.draindepth - cd->m_soil.z[i])
                       /cd->m_soil.dz[i];
          totdzliq += fmax(0., ed->m_sois.liq[i])*fdz;
          totdzavln += fmax(0., bd->m_sois.avln[i])*fdz;
        } else {
          break;
        }
      }
    }

    if(cd->yrsdist < cd->fri) {
      bd->m_a2soi.orgninput = fd->fire_a2soi.orgn/12.;
    }
  }

  // dead standing C due to fire will put into ground debris
  d2wdebrisc = bd->m_v2soi.d2wdebrisc;

  if (this->nfeed == 1) {
    d2wdebrisn = bd->m_v2soi.d2wdebrisn;
  }
};

void Soil_Bgc::afterIntegration() {
  for(int i=0; i<cd->m_soil.numsl; i++) {
    bd->m_soid.tsomc[i] = bd->m_sois.rawc[i] + bd->m_sois.soma[i]
                          + bd->m_sois.sompr[i] + bd->m_sois.somcr[i];
  }
};

void Soil_Bgc::clear_del_structs(){
  //soistate_bgc del_sois
  del_sois.wdebrisc = 0.0;
  del_sois.wdebrisn = 0.0;

  //soi2soi_bgc del_soi2soi
  del_soi2soi.netnminsum = 0.0;
  del_soi2soi.nimmobsum = 0.0;

  //soi2atm_bgc del_soi2a
  del_soi2a.rhwdeb = 0.0;
  del_soi2a.rhrawcsum = 0.0;
  del_soi2a.rhsomasum = 0.0;
  del_soi2a.rhsomprsum = 0.0;
  del_soi2a.rhsomcrsum = 0.0;
  del_soi2a.rhsom = 0.0;

  //soi2lnd_bgc del_soi2l
  del_soi2l.doclost = 0.0;
  del_soi2l.avlnlost = 0.0;
  del_soi2l.orgnlost = 0.0;

  //atm2soi_bgc del_a2soi
  del_a2soi.orgcinput = 0.0;
  del_a2soi.orgninput = 0.0;
  del_a2soi.avlninput = 0.0;

  for(int il=0; il<MAX_SOI_LAY; il++){
    del_sois.rawc[il] = 0.0;
    del_sois.soma[il] = 0.0;
    del_sois.sompr[il] = 0.0;
    del_sois.somcr[il] = 0.0;
    del_sois.orgn[il] = 0.0;
    del_sois.avln[il] = 0.0;

    del_soi2soi.netnmin[il] = 0.0;
    del_soi2soi.nimmob[il] = 0.0;

    del_soi2a.rhrawc[il] = 0.0;
    del_soi2a.rhsoma[il] = 0.0;
    del_soi2a.rhsompr[il] = 0.0;
    del_soi2a.rhsomcr[il] = 0.0;
  }
};

void Soil_Bgc::initializeState() {

  // Set initiate state variable
  double shlwc = chtlu->initshlwc;
  double deepc = chtlu->initdeepc;
  double minec = chtlu->initminec;

  initSoilCarbon(shlwc, deepc, minec);
  assignCarbonLayer2BdMonthly();

  bd->m_sois.wdebrisc = 0;

  // Initial N based on input total and SOM C profile
  double sum_total_C = shlwc + deepc + minec;

  for (int il=0; il<MAX_SOI_LAY; il++ ) {
    double total_monthly_C = bd->m_sois.rawc[il] +
                             bd->m_sois.soma[il] +
                             bd->m_sois.sompr[il] +
                             bd->m_sois.somcr[il];

    // Available N should only be calculated where roots are actively
    // turning over (ie, root zone)
    bool root_presence = false;
    double sum_root_frac = 0.0;
    for (int ipft=0; ipft<NUM_PFT; ++ipft) {
      sum_root_frac += cd->m_soil.frootfrac[il][ipft];
    }
    if (sum_root_frac > 0.0) {
      root_presence = true;
    }

    if (total_monthly_C > 0.0 && sum_total_C > 0.0) {

      if (root_presence) {
        bd->m_sois.avln[il] = chtlu->initavln * total_monthly_C/sum_total_C;
      } else {
        bd->m_sois.avln[il] = 0.0;
      }

      bd->m_sois.orgn [il] = chtlu->initsoln * total_monthly_C/sum_total_C;

    } else {
      bd->m_sois.avln [il] = 0.0;
      bd->m_sois.orgn [il] = 0.0;
    }
  } // end soil layer loop
}

void Soil_Bgc::set_state_from_restartdata(const RestartData & rdata) {
  
  for (int il =0; il<MAX_SOI_LAY; il++) {
    
    if(rdata.rawc[il]>=0){
		  bd->m_sois.rawc[il] = rdata.rawc[il];
    } else { 
		  bd->m_sois.rawc[il] = 0;
    }
    if(rdata.soma[il]>=0){    
		  bd->m_sois.soma[il] = rdata.soma[il];
    } else { 
		  bd->m_sois.soma[il] = 0;
    }
    if(rdata.sompr[il]>=0){
		  bd->m_sois.sompr[il]= rdata.sompr[il];
    } else { 
		  bd->m_sois.sompr[il] = 0;
    }
    if(rdata.somcr[il]>=0){
		  bd->m_sois.somcr[il]= rdata.somcr[il];
    } else { 
		  bd->m_sois.somcr[il] = 0;
    }
    if(rdata.orgn[il]>=0){
		  bd->m_sois.orgn[il] = rdata.orgn[il];
    } else { 
		  bd->m_sois.orgn[il] = 0;
    }
    if(rdata.avln[il]>=0){
		  bd->m_sois.avln[il] = rdata.avln[il];
    } else { 
		  bd->m_sois.avln[il] = 0;
    }

    for(int i=0; i<10; i++) {
      bd->prvltrfcnque[il].clear();
      double tmpcn = rdata.prvltrfcnA[i][il];

      if(tmpcn!=MISSING_D) {
        bd->prvltrfcnque[il].push_back(tmpcn);
      }
    }
  }

  bd->m_sois.wdebrisc = rdata.wdebrisc;
  bd->m_sois.wdebrisn = rdata.wdebrisn;
  assignCarbonBd2LayerMonthly();
};

void Soil_Bgc::initializeParameter() {
  BOOST_LOG_SEV(glg, info) << "Initializing parameters in Soil_Bgc from chtlu (CohortLookup) values.";
  calpar.micbnup    = chtlu->micbnup;
  calpar.kdcrawc    = chtlu->kdcrawc;
  calpar.kdcsoma    = chtlu->kdcsoma;
  calpar.kdcsompr   = chtlu->kdcsompr;
  calpar.kdcsomcr   = chtlu->kdcsomcr;
  bgcpar.rhq10      = chtlu->rhq10;
  bgcpar.moistmin   = chtlu->moistmin;
  bgcpar.moistmax   = chtlu->moistmax;
  bgcpar.moistopt   = chtlu->moistopt;
  bgcpar.fsoma      = chtlu->fsoma;
  bgcpar.fsompr     = chtlu->fsompr;
  bgcpar.fsomcr     = chtlu->fsomcr;
  bgcpar.som2co2    = chtlu->som2co2;
  bgcpar.lcclnc     = chtlu->lcclnc;
  bgcpar.kn2        = chtlu->kn2;
  bgcpar.propftos   = chtlu->propftos;
  bgcpar.fnloss     = chtlu->fnloss;
  bgcpar.nmincnsoil = chtlu->nmincnsoil;

  BOOST_LOG_SEV(glg, info) << "Calculating parameter in Soil_Bgc from Jenkinson and Rayner (1977).";
  // Alternatively these can be estimated from Ks calibrated.
  // Jenkinson and Rayner (1977):
  //   1t plant C / ha / yr for 10,000yrs, will produce:
  //   0.48t RAWC + 0.28t SOMA + 11.3t SOMPR + 12.2t SOMCR = 24.26 tC
  bgcpar.eqrawc = 0.48 / (0.48 + 0.28 + 11.3 + 12.2);
  bgcpar.eqsoma = 0.28 / (0.48 + 0.28 + 11.3 + 12.2);
  bgcpar.eqsompr = 11.3 / (0.48 + 0.28 + 11.3 + 12.2);
  bgcpar.eqsomcr = 12.2 / (0.48 + 0.28 + 11.3 + 12.2);

  BOOST_LOG_SEV(glg, info) << "Calculating decay in Soil_Bgc.";
  decay = 0.26299 +
          (1.14757 * bgcpar.propftos) -
          (0.42956 * pow((double)bgcpar.propftos, 2.0));
}

void Soil_Bgc::initSoilCarbon(double & initshlwc, double & initdeepc,
                              double & initminec) {
  for(int il =0; il <MAX_SOI_LAY ; il++) {
    bd->m_sois.rawc[il]  = 0.;
    bd->m_sois.soma[il]  = 0.;
    bd->m_sois.sompr[il] = 0.;
    bd->m_sois.somcr[il] = 0.;
  }

  initOslayerCarbon(initshlwc, initdeepc);

  if (initminec<0.10) {
    initminec = 0.10;
  }

  initMslayerCarbon(initminec);
};

// initialize Organic Soil layers' carbon based on input layer thickness
void Soil_Bgc::initOslayerCarbon(double & shlwc, double & deepc) {
  Layer* currl = ground->fstsoill;
  double dbmtop = 0.0;
  double dbmbot = 0.0;
  double cumcarbontop = 0.0;
  double cumcarbonbot = 0.0;
  double cumcarbonshlw = 0.0;
  double cumcarbondeep = 0.0;

  while(currl!=NULL) {
    if(currl->isSoil) {
      if (currl->isMineral || currl->isRock) {
        break;
      }

      if (currl==ground->fstmossl
          || currl==ground->fstshlwl
          || currl==ground->fstdeepl) {
        dbmtop = 0.0;
        cumcarbontop = 0.0;
      }

      dbmbot = dbmtop+currl->dz;

      if(currl->isFibric) {
        cumcarbonbot = ground->soildimpar.coefshlwa
                       * pow(dbmbot*100., ground->soildimpar.coefshlwb*1.)
                       * 10000; //from gC/cm2 to gC/m2
        cumcarbonshlw += cumcarbonbot - cumcarbontop;
      } else if(currl->isHumic) {
        cumcarbonbot = ground->soildimpar.coefdeepa
                       * pow(dbmbot*100., ground->soildimpar.coefdeepb*1.)
                       * 10000; //from gC/cm2 to gC/m2
        cumcarbondeep += cumcarbonbot - cumcarbontop;
      }

      if( cumcarbonbot - cumcarbontop > 0.0 ) {
        if (currl->isOrganic) {
          currl->rawc  = bgcpar.eqrawc * (cumcarbonbot - cumcarbontop); //note: those eq-fractions of SOM pools must be estimated before
          currl->soma  = bgcpar.eqsoma * (cumcarbonbot - cumcarbontop);
          currl->sompr = bgcpar.eqsompr * (cumcarbonbot - cumcarbontop);
          currl->somcr = bgcpar.eqsomcr * (cumcarbonbot - cumcarbontop);
        } else if (currl->isMoss) {

          // moss layers are not 'normal' soil organic layers, so contain
          // no C in the normal soil C pools
          currl->rawc  = 0.0;
          currl->soma  = 0.0;
          currl->sompr = 0.0;
          currl->somcr = 0.0;

        } else {
          currl->rawc  = 0.0;
          currl->soma  = 0.0;
          currl->sompr = 0.0;
          currl->somcr = 0.0;
        }
      } else {
        currl->rawc  = 0.0;
        currl->soma  = 0.0;
        currl->sompr = 0.0;
        currl->somcr = 0.0;
      }

      cumcarbontop = cumcarbonbot;
      dbmtop = dbmbot;
    } else {
      break;
    }

    currl = currl->nextl;
  }

  //Above calculation will give all soil organic layer C content UPON two
  //  parameters and thickness, the following will adjust that by
  //  actual initial SOMC amount as an input
  double adjfactor = 1.0;
  currl = ground->fstshlwl;

  while(currl!=NULL) {
    if(currl->isSoil) {
      if(currl->isOrganic) {
        if (currl->isFibric) {
          adjfactor = shlwc/cumcarbonshlw;
        } else if (currl->isHumic) {
          adjfactor = deepc/cumcarbondeep;
        }

        currl->rawc  *= adjfactor;
        currl->soma  *= adjfactor;
        currl->sompr *= adjfactor;
        currl->somcr *= adjfactor;
      } else {
        break;
      }
    }

    currl = currl->nextl;
  }
};

void Soil_Bgc::initMslayerCarbon(double & minec) {
  double dbm = 0.;
  double prevcumcarbon = 0.;
  double cumcarbon = 0.;
  double ca =  ground->soildimpar.coefminea;
  double cb = ground->soildimpar.coefmineb;
  Layer* currl = ground->fstminel;
  double totsomc = 0.0;

  while(currl!=NULL) {
    if(currl->isSoil) {
      dbm += currl->dz;
      cumcarbon = ca*(pow(dbm*100,cb))*10000;

      if(cumcarbon-prevcumcarbon>0.01 && dbm<=2.0) {  // somc will not exist more than 2 m intially
        currl->rawc  = bgcpar.eqrawc * (cumcarbon -prevcumcarbon);
        currl->soma  = bgcpar.eqsoma * (cumcarbon -prevcumcarbon);
        currl->sompr = bgcpar.eqsompr * (cumcarbon -prevcumcarbon);
        currl->somcr = bgcpar.eqsomcr * (cumcarbon -prevcumcarbon);
      } else {
        currl->rawc  = 0.0;    //
        currl->soma  = 0.0;
        currl->sompr = 0.0;
        currl->somcr = 0.0;
      }

      prevcumcarbon = cumcarbon;
      totsomc += currl->rawc+currl->soma+currl->sompr+currl->somcr;
    } else {
      break;
    }

    currl =currl->nextl;
  }

  //Above calculation will give all soil mineral layer C content UPON
  //  two parameters, the following will adjust that by actual
  //  initial MINEC amount as an input
  double adjfactor = 1.0;

  if (totsomc>0.) {
    adjfactor=minec/totsomc;
  }

  currl = ground->fstminel;

  while(currl!=NULL) {
    if(currl->isSoil) {
      currl->rawc *= adjfactor;
      currl->soma *= adjfactor;
      currl->sompr *= adjfactor;
      currl->somcr *= adjfactor;
    }

    currl =currl->nextl;
  }
};

// before delta and afterdelta are considered in Integrator
void Soil_Bgc::deltac() {
  double krawc = 0.0;     // for littering materials (in model, rawc)
  double ksoma = 0.0;     // for active SOM (in model, soma)
  double ksompr = 0.0;    // for PR SOM (in model, sompr)
  double ksomcr = 0.0;    // for CR SOM (in model, somcr)

  for (int il =0; il<cd->m_soil.numsl; il++) {
    //HG: 01122023 - this condition allows for winter respiration
    //(Natali et al. 2019, Nature Climate Change)
    if (ed->m_sois.ts[il] <0.) {
      bd->m_soid.rhmoist[il] = 1;
    } else {
      // Yuan: vwc normalized by total pore - this will allow
      // respiration (methane/oxidation) implicitly
      bd->m_soid.rhmoist[il] = getRhmoist( ed->m_soid.sws[il],
                                           bgcpar.moistmin,
                                           bgcpar.moistmax,
                                           bgcpar.moistopt );
    }
    bd->m_soid.rhq10[il] = getRhq10(ed->m_sois.ts[il]);
    krawc  = bgcpar.kdrawc[il];
    ksoma  = bgcpar.kdsoma[il];
    ksompr = bgcpar.kdsompr[il];
    ksomcr = bgcpar.kdsomcr[il];

    if(tmp_sois.rawc[il]>0.) {
      del_soi2a.rhrawc[il] = (krawc * tmp_sois.rawc[il]
                              * bd->m_soid.rhmoist[il] * bd->m_soid.rhq10[il]);
    } else {
      del_soi2a.rhrawc[il] = 0.;
    }

    if(tmp_sois.soma[il]>0) {
      del_soi2a.rhsoma[il] = ksoma*tmp_sois.soma[il]
                             * bd->m_soid.rhmoist[il] * bd->m_soid.rhq10[il];
    } else {
      del_soi2a.rhsoma[il] = 0.;
    }

    if(tmp_sois.sompr[il]>0) {
      del_soi2a.rhsompr[il] = ksompr*tmp_sois.sompr[il]
                              * bd->m_soid.rhmoist[il] * bd->m_soid.rhq10[il];
    } else {
      del_soi2a.rhsompr[il] = 0.;
    }

    if(tmp_sois.somcr[il]>0) {
      del_soi2a.rhsomcr[il] = ksomcr*tmp_sois.somcr[il]
                              * bd->m_soid.rhmoist[il] * bd->m_soid.rhq10[il];
    } else {
      del_soi2a.rhsomcr[il] = 0.;
    }
  } // loop for each soil layer

  // for wood debris at ground surface
  del_soi2a.rhwdeb = 0.;

  if(tmp_sois.wdebrisc > 0) {
    double rhmoist_wd = 0.0;
    double rhq10_wd = 0.0;
    double wdkd = 0.0;

    for (int il =0; il<cd->m_soil.numsl; il++) {
      if(cd->m_soil.type[il] > 0) { // 0 moss 1 shlw, and 2 deep
        rhmoist_wd = bd->m_soid.rhmoist[il];
        rhq10_wd = bd->m_soid.rhq10[il];
        wdkd = bgcpar.kdrawc[il];
        break; // Taking the first non-moss layer's only for wood debris
      }
    }

    del_soi2a.rhwdeb = wdkd * tmp_sois.wdebrisc * rhmoist_wd * rhq10_wd;
  }
};

/** soil N budget */
void Soil_Bgc::deltan() {
  if (this->nfeed == 1) { // soil-plant N cycle switched on
    // Total N immobilization and net mineralization
    totnetnmin = 0.0;

    for(int i=0; i<cd->m_soil.numsl; i++) {
      double totc = tmp_sois.rawc[i] +
                    tmp_sois.soma[i] +
                    tmp_sois.sompr[i] +
                    tmp_sois.somcr[i];

      double rhsum = del_soi2a.rhrawc[i] +
                     del_soi2a.rhsoma[i] +
                     del_soi2a.rhsompr[i]+
                     del_soi2a.rhsomcr[i];

      double nimmob = getNimmob(ed->m_sois.liq[i], totc,
                                tmp_sois.orgn[i], tmp_sois.avln[i],
                                bd->m_soid.knmoist[i], bgcpar.kn2);

      del_soi2soi.nimmob[i] = nimmob;
      del_soi2soi.netnmin[i] = getNetmin(nimmob, totc, tmp_sois.orgn[i],
                                         rhsum ,bgcpar.nmincnsoil,
                                         decay, calpar.micbnup, ed->m_sois.ts[i]);

      totnetnmin += del_soi2soi.netnmin[i];
    }

    //m_soi2v.nuptake IS calculated in Vegetation_Bgc.cpp and
    //  integrated in 'Cohort.cpp'
    totnextract = 0.;

    for (int il=0; il<MAX_SOI_LAY; il++) {
      totnextract += bd->m_soi2v.nextract[il];
    }

    if (this->avlnflg == 1) { // open-N (inorganic) swithed on - note here ONLY 'lost' considered, while 'input' shall be from outside if any
      del_soi2l.avlnlost = 0.;  // N leaching out with drainage water

      if(totdzliq>0) {
        del_soi2l.avlnlost = totdzavln / totdzliq * bgcpar.fnloss
                             * ed->m_soi2l.qdrain;
      }

      if(ed->m_sois.liq[0]>0) { // N loss with surface runoff water
        del_soi2l.avlnlost += tmp_sois.avln[0] / ed->m_sois.liq[0]
                              * bgcpar.fnloss * ed->m_soi2l.qover;
      }

      if( del_soi2l.avlnlost > totdzavln - totnextract
          + totnetnmin + bd->m_a2soi.avlninput) {
        del_soi2l.avlnlost = totdzavln - totnextract
                             + totnetnmin + bd->m_a2soi.avlninput;
      }

      if (del_soi2l.avlnlost < 0) {
        del_soi2l.avlnlost = 0.0;
        double nminadj = del_soi2l.avlnlost +
                         totnextract - bd->m_a2soi.avlninput - totdzavln;

        for(int i=0; i<cd->m_soil.numsl; i++) {
          del_soi2soi.netnmin[i] *=nminadj/totnetnmin;
        }
      }
    } else { // End (this->avlnflg == 1)
      // N budget estimation of inorganic N loss
      del_soi2l.avlnlost = bd->m_a2soi.avlninput -
                           totnextract + totnetnmin;
    }

    if ( !this->baseline ) {
      del_soi2l.orgnlost = 0.0; // Dynamic Organic N lost - not yet done.
                                // this is the portal for future development.
    } else {
      // note: this will re-estimate the fire-emission re-deposition
      del_a2soi.orgninput = 0.;
      del_soi2l.orgnlost = 0.;
      double tsomcsum=bd->m_soid.rawcsum+bd->m_soid.somasum
                      +bd->m_soid.somprsum+bd->m_soid.somcrsum;
      double orgneven = tsomcsum/bgcpar.nmincnsoil;

      if ( orgneven >= bd->m_soid.orgnsum) {
        //This forces the C:N ratio in all the soil layers to be
        //equal to the C:N ratio in the parameter file.
        del_a2soi.orgninput += orgneven - bd->m_soid.orgnsum;
      } else {
        del_soi2l.orgnlost  += bd->m_soid.orgnsum - orgneven;
      }
    } // End baseline
  } // end if (nfeed)
};

void Soil_Bgc::deltastate() {
  /////////////// Carbon pools in soil ///////////////////////////////////
  // (I) soil respiration and C pool internal transformation
  //Yuan: the following is modified, assuming that -
  // 1) Jenkinson et al, 1977, soil science 123: 298 - 305
  //    when C is respired, 1 C will produce:
  //      0.076 microbial biomass C,
  //      0.125 physically-resistant C,
  //      0.0035 chemically-resistant C
  //    and the rest are released as CO2
  //In this code, those fractions can be as inputs
  // the ratio of SOM products per unit of CO2 respired
  double somtoco2 = (double)bgcpar.som2co2;
  // the fraction of SOMA in total SOM product
  double fsoma    = (double)bgcpar.fsoma;
  // the fraction of SOMPR in total SOM product
  double fsompr   = (double)bgcpar.fsompr;
  // the fraction of SOMCR in total SOM product
  double fsomcr   = (double)bgcpar.fsomcr;

  //2) If soil respiration known, then internal C pool transformation
  //     can be estimated as following
  for(int il=0; il<cd->m_soil.numsl; il++) {
    double rhsum = del_soi2a.rhrawc[il] +
                   del_soi2a.rhsoma[il] +
                   del_soi2a.rhsompr[il] +
                   del_soi2a.rhsomcr[il];


    // Only calculate these pools for non-moss layers...
    if (cd->m_soil.type[il] > 0) {
      // So note that: root death is the reason for deep SOM increment
      del_sois.rawc[il] = ltrflc[il] - del_soi2a.rhrawc[il] * (1.0+somtoco2);

      del_sois.soma[il] = (rhsum * somtoco2 * fsoma) -
                          del_soi2a.rhsoma[il] * (1.0+somtoco2);

      del_sois.sompr[il] = (rhsum * somtoco2 * fsompr) -
                           del_soi2a.rhsompr[il] * (1.0+somtoco2);

      del_sois.somcr[il] = rhsum * somtoco2 * fsomcr -
                           del_soi2a.rhsomcr[il] * (1.0+somtoco2);
    }
  }

  //ground surface wood debris decrement, if any
  del_sois.wdebrisc = d2wdebrisc- del_soi2a.rhwdeb;
  //(II) moving/mixing portion of C among layers
  //fibric-C (rawc) will NOT to move between layers
  double s2dfraction = 1.0;
  double mobiletoco2 = (double)bgcpar.fsoma*(double)bgcpar.som2co2;
  double xtopdlthick  = fmin(0.10, cd->m_soil.deepthick);  //Yuan: the max. thickness of deep-C layers, which shallow-C can move into
  double xtopmlthick  = 0.20;                              //Yuan: the max. thickness of mineral-C layers, which deep-C can move into
  double s2dcarbon1 = 0.0;  // read "soil to deep"?
  double s2dcarbon2 = 0.0;
  double s2dorgn    = 0.0;
  double d2mcarbon = 0.0;   // read "deep to mineral"?
  double d2morgn   = 0.0;
  double dlleft    = xtopdlthick;
  double mlleft    = xtopmlthick;
  double dcaddfrac = 0.0;
  double thickadded= 0.0;
  double del_orgn[MAX_SOI_LAY]= {0.0}; // soil org. N change with SOMC transformation and/or allocation

  for(int il=0; il<cd->m_soil.numsl; il++) {
    // 1) most of resistant-C increment into the fibric-horizon (generated
    //      above) will move down so that fibric horizon will be
    //      coarse-material dominated (active SOM will remain)
    if (cd->m_soil.type[il]<=1) {
      if (del_sois.sompr[il] > 0.) {
        s2dcarbon1 += del_sois.sompr[il]*s2dfraction;   //
        del_sois.sompr[il] *= (1.0-s2dfraction); // <<-- NOTE: may set delta sompr to zero?
      }

      if (del_sois.somcr[il] > 0.) {
        s2dcarbon2 += del_sois.somcr[il]*s2dfraction;   //
        del_sois.somcr[il] *= (1.0-s2dfraction);
      }

      if (this->nfeed == 1) {  // move orgn with SOMC as well
        double totsomc = tmp_sois.rawc[il] + tmp_sois.soma[il]
                         + tmp_sois.sompr[il] + tmp_sois.somcr[il];

        if (totsomc > (s2dcarbon1 + s2dcarbon2)) {
          del_orgn[il] = - (s2dcarbon1+s2dcarbon2) / totsomc
                          * tmp_sois.orgn[il]; //assuming C/N same for all
                                               //  SOM components
        } else {
          del_orgn[il] = 0.0;
        }

        s2dorgn += (-del_orgn[il]); //note: del_orgn[il] above is not positive
      }

      // In case there is no existing deep humific layer
      if (il<(cd->m_soil.numsl-1) && cd->m_soil.type[il+1]>2) {
        // NOTE:
        // Should this been 'cd->m_soil.type[il+1] > 1'??
        // Also, not sure how this is supposed to work, since we are w/in the
        // fibric layer check - not sure how this code will ever execute...

        del_sois.sompr[il] += s2dcarbon1; // Let the humified SOM C staying
                                          // in the last fibrous layer,
        del_sois.somcr[il] += s2dcarbon2; // Which later on, if greater than a
                                          // min. value, will form a new
                                          // humic layer

        if (this->nfeed == 1) {
          del_orgn[il] += s2dorgn;
        }
      }
    // end soil type 0 or 1
    } else if (cd->m_soil.type[il]==2 && dlleft>0) {
      // Humic layers...
      // 2) s2dcarbon from above will move into the 'xtopdlthick';
      thickadded = fmin(cd->m_soil.dz[il], dlleft);
      dcaddfrac = thickadded / xtopdlthick;
      dlleft -= thickadded;
      del_sois.sompr[il] += dcaddfrac * s2dcarbon1;
      del_sois.somcr[il] += dcaddfrac * s2dcarbon2;

      if (this->nfeed == 1) {
        del_orgn[il]+=s2dorgn;
      }

      // 3) meanwhile, the most mobilable portion of increment in
      //    deep-C layers will move down
      //    Here,
      //    (1) the mobilable portion is assumed to equal the SOMA
      //        production ONLY in value
      //    if any suggestion on this fraction (i.e., mobiletoco2) from
      //    field work, it should be modified;
      //
      //    (2) the mobilable portion is assumed to be related to
      //        decomposition activity, rather than directly to the
      //        substrate itself, because theorectically this mobile SOM C
      //        should be related to microbial activity
      double rhsum = del_soi2a.rhrawc[il] + del_soi2a.rhsoma[il]
                     + del_soi2a.rhsompr[il] + del_soi2a.rhsomcr[il];

      if (rhsum > 0.0) {
        double totmobile = rhsum*mobiletoco2;
        d2mcarbon += totmobile;
        del_sois.rawc[il]  -= del_soi2a.rhrawc[il]*mobiletoco2;
        del_sois.soma[il]  -= del_soi2a.rhsoma[il]*mobiletoco2;
        del_sois.sompr[il] -= del_soi2a.rhsompr[il]*mobiletoco2;
        del_sois.somcr[il] -= del_soi2a.rhsomcr[il]*mobiletoco2;

        if (this->nfeed == 1) {
          double totsomc = tmp_sois.rawc[il] + tmp_sois.soma[il]
                           + tmp_sois.sompr[il] + tmp_sois.somcr[il];

          if (totsomc > totmobile) {
            del_orgn [il] = - totmobile/totsomc*tmp_sois.orgn[il]; //assuming C/N same for all SOM components
          } else {
            del_orgn[il] = 0.0;
          }

          d2morgn += (-del_orgn[il]); //note: del_orgn[il] above is not positive
        }
      }

    // end soil type 2 and 'dlleft>0'
    } else if (cd->m_soil.type[il]==3) { // mineral layers...
      // 4) d2mcarbon from above will move into the 'xtopmlthick';
      thickadded = fmin(cd->m_soil.dz[il], mlleft);
      dcaddfrac = thickadded/xtopmlthick;
      mlleft -= thickadded;
      double tsom = tmp_sois.soma[il] + tmp_sois.sompr[il] + tmp_sois.somcr[il];

      if (tsom > 0.0) {
        del_sois.soma[il]+= dcaddfrac*d2mcarbon*(tmp_sois.soma[il]/tsom);
        del_sois.sompr[il]+= dcaddfrac*d2mcarbon*(tmp_sois.sompr[il]/tsom);
        del_sois.somcr[il]+= dcaddfrac*d2mcarbon*(tmp_sois.somcr[il]/tsom);
      } else {
        del_sois.soma[il]+= dcaddfrac*d2mcarbon*fsoma;
        del_sois.sompr[il]+= dcaddfrac*d2mcarbon*fsompr;
        del_sois.somcr[il]+= dcaddfrac*d2mcarbon*fsomcr;
      }

      if (this->nfeed == 1) {
        del_orgn[il] = d2morgn * dcaddfrac;
      }

      if (mlleft<=0.0) {
        break;
      }
    } // end soil type 3
  }

  /////////////// Nitrogen pools in soil ///////////////////////////////////
  if (this->nfeed == 1) {
    for(int il = 0; il<cd->m_soil.numsl; il++) {
      // organic N pools
      //del_orgn[il] is from above SOM C mixing and moving
      del_sois.orgn[il] = ltrfln[il] - del_soi2soi.netnmin[il] + del_orgn[il];

      if (il==0) { //put the deposited orgn (here, mainly fire emitted
                   //  or budget estimation) into the first soil layer
        del_sois.orgn[il] += bd->m_a2soi.orgninput;
      }

//      double dondrain = 0.0; // dissolved organic N drainage??
//
//      if (totdzliq > 0.01) {
//        if((cd->m_soil.z[il]+cd->m_soil.dz[il]) <= ed->m_sois.draindepth) { //note: z is at the top of a layer
//          dondrain = del_soi2l.orgnlost
//                     * (ed->m_sois.liq[il]/totdzliq);
//        } else {
//          if (cd->m_soil.z[il]<ed->m_sois.draindepth) { // note: z is at the top of a layer
//            double fdz = (ed->m_sois.draindepth - cd->m_soil.z[il]) / cd->m_soil.dz[il];
//            dondrain = del_soi2l.orgnlost * (ed->m_sois.liq[il]/totdzliq) * fdz;
//          }
//        }
//      }
//
//      del_sois.orgn[il] -= dondrain; // <==== When orgn ends up negative, the
//                                     // Integrator has a hard time converging!
//
//      // If del_sosi.orgn is a "pool" variable and not a "change in pool"
//      // variable, then it might be appropriate to force the values to zero:
//      // with something like this:
//      //if (del_sois.orgn[il] < 0) { del_sois.orgn[il] = 0.0; }

      // Inorganic N pools
      double ninput = 0.;

      if (il == 0) {
        ninput = bd->m_a2soi.avlninput;
      }

      //Note: the internal N transport not estimated, but assuming that all
      //        N leaching loss are from all above-drainage zone upon liq
      //         water fraction
      //  This is not good for daily N process, but shall be reasonble
      //    for longer intervals, e.g. monthly
      double ndrain = 0.;

      if (totdzliq>0.01) {
        if((cd->m_soil.z[il]+cd->m_soil.dz[il]) <= ed->m_sois.draindepth) { //note: z is at the top of a layer
          ndrain = del_soi2l.avlnlost
                   *(ed->m_sois.liq[il]/totdzliq*ed->m_soi2l.qdrain);
        } else {
          if (cd->m_soil.z[il]<ed->m_sois.draindepth) { // note: z is at the top of a layer
            double fdz = (ed->m_sois.draindepth - cd->m_soil.z[il])
                         /cd->m_soil.dz[il];
            ndrain = del_soi2l.avlnlost
                     *(ed->m_sois.liq[il]/totdzliq*ed->m_soi2l.qdrain)*fdz;
          }
        }
      }
      if(bd->m_v2soi.rtlfalfrac[il] > 0.){
        del_sois.avln[il] = ninput + del_soi2soi.netnmin[il]
                            - ndrain - rtnextract[il];
      } else {
        del_sois.avln[il] = 0;
        del_soi2soi.netnmin[il] = 0.0;
      }
    } // end of soil layer loop


    // wood debris
    if (tmp_sois.wdebrisc > 0.) {
      del_sois.wdebrisn = d2wdebrisn;
      del_sois.wdebrisn -=del_soi2a.rhwdeb*tmp_sois.wdebrisn/tmp_sois.wdebrisc;
    }
  } // end of 'if (this->nfeed == 1)'
};

double Soil_Bgc::getRhmoist(const double &vsm, const double &moistmin,
                            const double &moistmax, const double &moistopt) {
  double rhmoist;
  //set moistlim always 1
  rhmoist = (vsm - moistmin) * (vsm - moistmax);
  rhmoist /= rhmoist - (vsm-moistopt)*(vsm-moistopt);

  if ( rhmoist < 0.0 ) {
    rhmoist = 0.0;
  }

  return rhmoist;
};

double Soil_Bgc::getRhq10(const  double & tsoil) {
  double rhq10;
  rhq10 =  pow( (double)bgcpar.rhq10, tsoil/10.0);
  return rhq10;
};

double Soil_Bgc::getNimmob(const double & soilh2o, const double & soilorgc,
                           const double & soilorgn, const double & availn,
                           const double & ksoil, const double kn2) {
  double nimmob     = 0.0;
  double tempnimmob = 0.0;
  double tempkn2    = kn2;

  //what if put && availn>0 here
  if(soilorgc>0.0 && soilorgn>0.0 && soilh2o>0 && availn>0) {
    nimmob = (availn * ksoil) / soilh2o;
    tempnimmob = nimmob;
    nimmob /= (tempkn2 + nimmob);
  }

  return nimmob;
};

double Soil_Bgc::getNetmin(const double & nimmob, const double & soilorgc,
                           const double & soilorgn, const double & rh,
                           const double & tcnsoil,
                           const double & decay, const double & nup, 
			   const double & soilts) {
  double nmin = 0.0;
  if ( soilts > 0.0 ) {

    if ( soilorgc > 0.0 && soilorgn > 0.0 ) {
      nmin   = ((soilorgn / soilorgc) - (nup * nimmob * decay)) * rh;

      if ( nmin >= 0.0 ) {
        nmin *= (soilorgn/soilorgc) * tcnsoil;
      } else {
        nmin *= (soilorgc/soilorgn) / tcnsoil;
      }
    }
  }
  return nmin;
};

void Soil_Bgc::updateKdyrly4all() {
  double kdrawc  = calpar.kdcrawc;
  double kdsoma  = calpar.kdcsoma;
  double kdsompr = calpar.kdcsompr;
  double kdsomcr = calpar.kdcsomcr;

  for(int il=0; il<cd->m_soil.numsl; il++) {
    //adjust SOM component respiration rate (kdc) due to 
    //  literfall C/N ratio changing
    if (this->nfeed == 1) {
      double ltrfalcn = 0.;
      deque <double> ltrfcnque = bd->prvltrfcnque[il];
      int numrec = ltrfcnque.size();

      for (int i=0; i<numrec; i++) {
        ltrfalcn += ltrfcnque[i]/numrec;
      }

      if (ltrfalcn > 0.0) {
        kdrawc  = getKdyrly(ltrfalcn, bgcpar.lcclnc, calpar.kdcrawc);
        kdsoma  = getKdyrly(ltrfalcn, bgcpar.lcclnc, calpar.kdcsoma);
        kdsompr = getKdyrly(ltrfalcn, bgcpar.lcclnc, calpar.kdcsompr);
        kdsomcr = getKdyrly(ltrfalcn, bgcpar.lcclnc, calpar.kdcsomcr);
      } else {
        kdrawc  = calpar.kdcrawc;
        kdsoma  = calpar.kdcsoma;
        kdsompr = calpar.kdcsompr;
        kdsomcr = calpar.kdcsomcr;
      }
    }

    bgcpar.kdrawc[il]  = kdrawc;
    bgcpar.kdsoma[il]  = kdsoma;
    bgcpar.kdsompr[il] = kdsompr;
    bgcpar.kdsomcr[il] = kdsomcr;
  }

};

double Soil_Bgc::getKdyrly(double & yrltrcn, const double lcclnc,
                           const double & kdc) {
  double kd = kdc;
  kd = kdc * pow( (yrltrcn),-0.784 ) / pow( lcclnc,-0.784 );
  return kd;
};

double Soil_Bgc::getKnsoilmoist(const double & vsm) {
  double ksoil = 0.;

  if (vsm > 0.) {
    ksoil = pow(vsm, 3.0);
  }

  return ksoil;
};

void Soil_Bgc::setGround(Ground* groundp) {
  ground = groundp;
};

void Soil_Bgc::setCohortLookup(CohortLookup* chtlup) {
  chtlu = chtlup;
};

void Soil_Bgc::setCohortData(CohortData* cdp) {
  cd = cdp;
};

void Soil_Bgc::setEnvData(EnvData* edp) {
  ed = edp;
};

void Soil_Bgc::setBgcData(BgcData* bdp) {
  bd = bdp;
};

void Soil_Bgc::setFirData(FirData* fdp) {
  fd = fdp;
};

void Soil_Bgc::set_nfeed(int value) {
  BOOST_LOG_SEV(glg, info) << "Setting Soil_Bgc.nfeed to " << value;
  this->nfeed = value;
}

int Soil_Bgc::get_nfeed() {
  return this->nfeed;
}

void Soil_Bgc::set_avlnflg(int value) {
  BOOST_LOG_SEV(glg, info) << "Setting Soil_Bgc.avlnflg to " << value;
  this->avlnflg = value;
}

int Soil_Bgc::get_avlnflg() {
  return this->avlnflg;
}

void Soil_Bgc::set_baseline(int value) {
  BOOST_LOG_SEV(glg, info) << "Setting Soil_Bgc.baseline to " << value;
  this->baseline = value;
}

int Soil_Bgc::get_baseline() {
  return this->baseline;
}


