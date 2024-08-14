/*
 * TemperatureUpdator.cpp
 *
 *  Created on: 2011-8-18 by yis
 *  Checked on: 2013-02-18 by F.-M. Yuan
 */

#include "../include/TemperatureUpdator.h"

#include "../include/TEMLogger.h"
#include "../include/TEMUtilityFunctions.h"

extern src::severity_logger< severity_level > glg;

void TemperatureUpdator::warn_bad_tld(const int idx){
  if (this->tld[idx] != this->tld[idx]) {
    BOOST_LOG_SEV(glg, warn) << "tld["<<idx<<"] is nan!";
  }
  if (tld[idx] == MISSING_D) {
    BOOST_LOG_SEV(glg, warn) << "tld["<<idx<<"] is " << MISSING_D << ")";
  }
}

TemperatureUpdator::TemperatureUpdator() {
  TSTEPMAX = 1;
  TSTEPMIN = 1.0e-5;
  TSTEPORG = 0.5;
  ttole = 0.01;
  mindzlay = 0.01;
  zerodegc = 0.01; //a constant to represent temperature near zero in degree C
}

TemperatureUpdator::~TemperatureUpdator() {
}

void TemperatureUpdator::updateTemps(const double & tdrv, Layer *fstvalidl,
                                     Layer *backl, Layer* fstsoill,
                                     Layer* fstfntl, Layer *lstfntl,
                                     const double& ts, const bool & meltsnow) {
  itsumall = 0;
  itsumabv = 0;
  itsumblw = 0;
  timestep = ts;

///*
  for (int i = 0; i < MAX_GRN_LAY+2; i++) {
    t[i]   = MISSING_D;
    dx[i]  = MISSING_D;
    tca[i] = MISSING_D;
    hca[i] = MISSING_D;
    cn[i]  = MISSING_D;
    cap[i] = MISSING_D;
    tid[i] = MISSING_D;
    tld[i] = MISSING_D;
    type[i]= MISSING_D;
    s[i]   = MISSING_D;
    e[i]   = MISSING_D;
    tii[i] = MISSING_D;
    tis[i] = MISSING_D;
    tit[i] = MISSING_D;
  }

  bool setfntl = true; //set frontlayer temperature by weighting
                       //  'frozenfrac' of the layer

  int front_count = ground->frontstype.size();

  if (front_count == 0) {
    // no fronts in soil column
    BOOST_LOG_SEV(glg, info) << "Adjusting temperatures in a soil stack with no fronts";
    processColumnNofront(fstvalidl, tdrv, meltsnow);
    itsumall = itsum;
  }
  else if (front_count == 1) {
    BOOST_LOG_SEV(glg, info) << "Adjusting temperatures in a soil stack with 1 front";
    processAboveFronts(fstvalidl, fstfntl, tdrv, meltsnow);
    itsumabv = itsum;
    processBelowFronts(lstfntl, false); //setfntl false because frontlayer temp set in processAboveFronts
    itsumblw = itsum;
    itsumall = itsumabv + itsumblw;
  }
  else if (front_count == 2) {
    // there are two different layers which contain front(s)
    BOOST_LOG_SEV(glg, info) << "Adjusting temperatures in a soil stack with 2 fronts";
    processAboveFronts(fstvalidl, fstfntl, tdrv, meltsnow);
    itsumabv = itsum;
    processBelowFronts(lstfntl, setfntl);
    itsumblw = itsum;
    processBetweenFronts(fstfntl, lstfntl, 0, false); //setfntl false because frontlayers' temps set in processAboveFronts and processBelowFronts
    itsumall = itsumabv + itsumblw;
  }
  else if(front_count > 2){
    BOOST_LOG_SEV(glg, info) << "Adjusting temperatures in a soil stack with "
                             << front_count << " fronts";
    //Need to find middle fronts. Cycle through layers,
    // if frozen == 0, it's a frontlayer.
    std::vector<Layer *> front_ptrs;

    Layer *iter_lay = fstfntl;
    while(iter_lay != NULL){

      if(iter_lay->frozen == 0){
        //Insert at end so the higher fronts are at the front of the vector
        front_ptrs.push_back(iter_lay);
      }
      iter_lay = iter_lay->nextl;
    }

    //For the following function calls, we assume that the first pointer
    // in front_ptrs is fstfntl, and that the last pointer is lstfntl
    processAboveFronts(fstvalidl, front_ptrs.front(), tdrv, meltsnow);
    itsumabv = itsum;
    processBelowFronts(front_ptrs.back(), false); //setfntl false because last frontlayer temp will be set in processBetweenFronts
    itsumblw = itsum;

    //Between each pair of fronts in front_ptrs. The limit must be 
    // size-1 so that it does not attempt to run with the last front
    // and a non-existent front below it. 
    for(int ii=0; ii<front_ptrs.size()-1; ii++){
      //We include ii in the following call for accessing data in Ground
      // that is not otherwise available.
      processBetweenFronts(front_ptrs.at(ii), front_ptrs.at(ii+1), ii, setfntl); //sets frontlayer temp for lower frontlayers
    }

    itsumall = itsumabv + itsumblw;
  }

  //fstvalidl->tem = tdrv;
}


void TemperatureUpdator::processColumnNofront(Layer* fstvalidl, const double & tdrv, const bool & meltsnow) {
  BOOST_LOG_NAMED_SCOPE("TemperatureUpdator::processColumnNofront"){

  int startind, endind;
  // The top boundary layer is an extra, virtual layer.
  // Fill solver arrays for this virtual layer:
  int ind = fstvalidl->indl - 1;
  startind = ind;

  if (meltsnow) {
    t[ind] = 0.0;
  } else {
    t[ind] = tdrv; // This tdrv has been modified by nfactor
  }
  e[ind]  = t[ind];
  s[ind]  = 0.0;
  cn[ind] = 1.0e2; //assume very big thermal conductivity for this virtual
                   //  layer (Reason for osicillation!!! from e20 to e2)
  cap[ind]= 0.0; // assume no heat capacity for this virtual layer

  // Fill solver arrays for regular layers
  Layer* currl = fstvalidl;
  while (currl != NULL) {
    ind = currl->indl;
    dx[ind] = currl->dz;
    dx[ind] = temutil::NON_ZERO(dx[ind], 1);
    t[ind] = currl->tem;
    tca[ind] = currl->getThermalConductivity();
    double hcap = currl->getHeatCapacity();
    double pce = abs(currl->pce_f - currl->pce_t);
    hca[ind] = (pce + hcap);
    cn[ind] = tca[ind] / dx[ind];
    cap[ind] = hca[ind] * dx[ind];
    currl = currl->nextl;
  }

  // The bottom boundary layer is an extra, virtual layer
  // Fill solver arrays for this virtual layer:
  ind++;
  double gflx = 0.0;  // no bottom heat flux assumed
  t[ind] = t[ind-1] + gflx/(tca[ind-1]) * dx[ind-1];
  s[ind] = 0.;
  e[ind] = t[ind];
  endind = ind;

  // Run the solver for all layers
  iterate(startind, endind);

  // Post-iteration
  // Check for nans in solver results array (tld)
  for (int il = startind; il <= endind; il++) {
    warn_bad_tld(il);
  }

  // Update layers from solver results array, skipping extra boundary layers
  currl = fstvalidl;
  while (currl != NULL) {
    ind = currl->indl;
    currl->tem = tld[ind];
    currl = currl->nextl;
  }
  }// Closes BOOST named scope
}

void TemperatureUpdator::processAboveFronts(Layer* fstvalidl, Layer*fstfntl,
                                            const double & tdrv,
                                            const bool & meltsnow) {
  BOOST_LOG_NAMED_SCOPE("TemperatureUpdator::processAboveFronts"){

  if(fstfntl == fstvalidl){ // Front is in the top layer, so nothing to iterate. Just set frontlayer temp.
    //Scale frontlayer temp between -zerodegc and zerodegc based on frozenfrac
    fstfntl->tem = -zerodegc + (1.0-fstfntl->frozenfrac) * (2.0* zerodegc);
    return;
  }

  // The top boundary layer is an extra, virtual layer
  // Fill solver arrays for the virtual layer:
  int ind,startind, endind;
  ind = fstvalidl->indl - 1;
  startind = ind;

  if (meltsnow) {
    t[ind] = 0.0;
  } else {
    t[ind] = tdrv; // This tdrv has been modified by nfactor
  }
  e[ind]  = t[ind];
  s[ind]  = 0.;
  cn[ind] = 1.0e2; //assume very big thermal conductivity for this virtual layer
  cap[ind]= 0.; //assume no heat capacity for this virtual layer

  // Fill solver arrays for regular layers above first frontlayer
  Layer* currl = fstvalidl;
  while (currl != NULL) {
    if (currl->indl >= fstfntl->indl) {
      break;
    }
    ind = currl->indl;
    dx[ind] = currl->dz;
    dx[ind] = temutil::NON_ZERO(dx[ind], 1);
    t[ind] = currl->tem;
    tca[ind] = currl->getThermalConductivity();
    double hcap = currl->getHeatCapacity();
    double pce = abs(currl->pce_f - currl->pce_t);
    hca[ind] = (pce + hcap);
    cn[ind] = tca[ind] / dx[ind];
    cap[ind] = hca[ind] * dx[ind];
    currl = currl->nextl;
  }

  // Bottom boundary: the upper portion of the first frontlayer
  // Fill arrays for this frontlayer
  ind = fstfntl->indl;
  int frnttype = ground->frontstype[0];
  if (frnttype == 1) { // Assume that the frontlayer temp is near zero
    t[ind] = -zerodegc;  // freezing front, so top of layer < 0
  } else {
    t[ind] = zerodegc;  // thawing front, so top of layer > 0
  }
  double frntdz = ground->frontsz[0] - fstfntl->z; // Thickness of portion of layer above the front
  dx[ind] = frntdz;
  if (dx[ind] < mindzlay) {
    dx[ind] = mindzlay;
  }
  dx[ind] = temutil::NON_ZERO(dx[ind], 1);
  double hcap;
  if (frnttype == 1) {
    tca[ind] = fstfntl->getFrzThermCond();
    hcap = fstfntl->getFrzVolHeatCapa();
  } else {
    tca[ind] = fstfntl->getUnfThermCond();
    hcap = fstfntl->getUnfVolHeatCapa();
  }
  double pce = abs(fstfntl->pce_f-fstfntl->pce_t);
  hca[ind] = (pce + hcap);
  cn[ind] = tca[ind]  / dx[ind];
  cap[ind] = hca[ind] * dx[ind];
  s[ind] = 0.;
  e[ind] = t[ind];
  endind = ind;

  // Run the solver for these layers:
  iterate(startind, endind);

  // Post-iteration: check for nans in the solver results array (tld)
  for (int il = startind; il <= endind; il++) {
    warn_bad_tld(il);
  }

  // Update regular layers from solver results array, skipping extra virtual layer and frontlayer
  currl = fstvalidl;
  while (currl != NULL) {
    if (currl->indl >= fstfntl->indl) {
      break;
    }
    ind = currl->indl;
    currl->tem = tld[ind];
    currl = currl->nextl;
  }

  // Set the frontlayer temp based on zerodegc and frozenfrac
  fstfntl->tem = -zerodegc + (1.0-fstfntl->frozenfrac) * (2.0* zerodegc); //Scale temp between -zerodegc and zerodegc based on frozenfrac

  }// Closes BOOST named scope
}

void TemperatureUpdator::processBetweenFronts(Layer*fstfntl, Layer*lstfntl,
                                              int fstfntindex,
                                              const bool&setfntl) {
  BOOST_LOG_NAMED_SCOPE("TemperatureUpdator::processBetweenFronts"){

  if (lstfntl->indl - fstfntl->indl <= 1) { // Fronts are in adjacent layers or in the same layer; i.e. no layers between frontlayers
    fstfntl->tem = -zerodegc + (1.0-fstfntl->frozenfrac) * (2.0* zerodegc); //Scale temps between -zerodegc and zerodegc based on frozenfrac
    lstfntl->tem = -zerodegc + (1.0-lstfntl->frozenfrac) * (2.0* zerodegc);
    return;
  }

  // Top boundary is the bottom part of the upper frontlayer
  // Fill solver arrays for this frontlayer
  int ind, startind, endind;
  ind = fstfntl->indl;

  startind = ind;
  int frnttype1 = ground->frontstype[fstfntindex];
  if (frnttype1 == 1) {  // Assume that the frontlayer temp is near zero
    t[ind] = zerodegc; // Freezing front: bottom of layer is > 0
  } else {
    t[ind] = -zerodegc; // Thawing front: bottom of layer is < 0
  }
  e[ind] = t[ind];
  s[ind] = 0.;
  double frntdz1 = (fstfntl->z+fstfntl->dz) - ground->frontsz[fstfntindex];
  dx[ind] = frntdz1; // Thickness of the portion of layer below the front
  if (dx[ind] < mindzlay) {
    dx[ind] = mindzlay;
  }
  dx[ind] = temutil::NON_ZERO(dx[ind], 1);
  double hcap;
  if (frnttype1 == 1) {
    tca[ind] = fstfntl->getUnfThermCond();
    hcap = fstfntl->getUnfVolHeatCapa();
  } else {
    tca[ind] = fstfntl->getFrzThermCond();
    hcap = fstfntl->getFrzVolHeatCapa();
  }
  double pce = abs(fstfntl->pce_f-fstfntl->pce_t);
  hca[ind] = (pce + hcap);
  cn[ind] = tca[ind]  / dx[ind];
  cap[ind] = hca[ind] * dx[ind];

  // Middle layers:
  // Fill solver arrays for regular layers between frontlayers
  Layer* currl = fstfntl->nextl;
  while (currl != NULL) {
    if (currl->indl >= lstfntl->indl) {
      break;
    }
    ind = currl->indl;
    t[ind] = currl->tem;
    dx[ind] = currl->dz;
    dx[ind] = temutil::NON_ZERO(dx[ind], 1);
    tca[ind] = currl->getThermalConductivity();
    hcap = currl->getHeatCapacity();
    pce = abs(currl->pce_f - currl->pce_t);
    hca[ind] = pce + hcap;
    cn[ind] = tca[ind]/dx[ind];
    cap[ind] = hca[ind] * dx[ind];
    currl = currl->nextl;
  }

  // Bottom boundary is the top part of the lower frontlayer
  // Fill solver arrays for this frontlayer
  ind++;
  int frnttype2 = ground->frontstype[fstfntindex+1];
  if (frnttype2 == 1) {  // 'freezing' front: above < 0, below >0
    t[ind] = -zerodegc;
  } else {
    t[ind] = zerodegc;
  }
  double frntdz2 = ground->frontsz[fstfntindex+1] - lstfntl->z;
  dx[ind] = frntdz2; // Thickness of the portion of layer above the front
  if (dx[ind] < mindzlay) {
    dx[ind] = mindzlay;
  }
  dx[ind] = temutil::NON_ZERO(dx[ind], 1);
  if (frnttype2 == 1) {
    tca[ind] = lstfntl->getFrzThermCond();
    hcap = lstfntl->getFrzVolHeatCapa();
  } else {
    tca[ind] = lstfntl->getUnfThermCond();
    hcap = lstfntl->getUnfVolHeatCapa();
  }
  pce = abs(lstfntl->pce_f-lstfntl->pce_t);
  hca[ind] = (pce + hcap);
  cn[ind] = tca[ind]  / dx[ind];
  cap[ind] = hca[ind] * dx[ind];
  s[ind] = 0.;
  e[ind] = t[ind];
  endind = ind;

  // Run the solver for these layers:
  iterate(startind, endind);

  // Post-iteration: check for nans in the solver results array (tld)
  for (int il = startind; il <= endind; il++) {
    warn_bad_tld(il);
  }

  // Update layer temperatures from solver results array.
  // Note that upper frontlayer tem has already been updated by either
  // processAboveFronts or by a previous pass of processBetweenFronts
  // so it is not updated here.

  // Update temps of regular middle layers between frontlayers
  currl = fstfntl->nextl;
  while (currl != NULL) {
    if (currl->indl >= lstfntl->indl) {
      break;
    }
    ind = currl->indl;
    currl->tem = tld[ind];
    currl = currl->nextl;
  }

  // Set lstfntl->tem based on frozenfrac
  // If setfntl is false, frontlayer temp was already updated by processBelowFronts.
  if (setfntl) {
    currl = lstfntl;
    currl->tem = -zerodegc + (1.0-currl->frozenfrac) * (2.0* zerodegc); //Scale temps between -zerodegc and zerodegc based on frozenfrac
  }
  }// Closes BOOST named scope
}

void TemperatureUpdator::processBelowFronts(Layer*lstfntl,
                                            const bool &setfntl) {
  BOOST_LOG_NAMED_SCOPE("TemperatureUpdator::processBelowFronts"){

  if(lstfntl == ground->lstsoill){ // Front is in the bottom layer, so nothing to iterate. Just set frontlayer temp.
    //Scale frontlayer temp between -zerodegc and zerodegc based on frozenfrac
    lstfntl->tem = -zerodegc + (1.0-lstfntl->frozenfrac) * (2.0* zerodegc);
    return;
  }

  // Top boundary is the bottom part of the lowest frontlayer
  // Fill solver arrays for this layer
  int ind, startind, endind;
  ind = lstfntl->indl;

  startind = ind;
  int numfnt = ground->frontsz.size();
  int frnttype = ground->frontstype[numfnt-1];
  if (frnttype == 1) {  // Assume that the frontlayer temp is near zero
    t[ind] = zerodegc; // Freezing front: bottom of layer is > 0
  } else {
    t[ind] = -zerodegc; // Thawing front: bottom of layer is < 0
  }
  e[ind] = t[ind];
  s[ind] = 0.;
  double frntdz = (lstfntl->z+lstfntl->dz) - ground->frontsz[numfnt-1];
  dx[ind] = frntdz; // Thickness of the portion of layer below the front
  if (dx[ind] < mindzlay) {
    dx[ind] = mindzlay;
  }
  dx[ind] = temutil::NON_ZERO(dx[ind], 1);
  double hcap;
  if (frnttype == 1) {
    tca[ind] = lstfntl->getUnfThermCond();
    hcap = lstfntl->getUnfVolHeatCapa();
  } else {
    tca[ind] = lstfntl->getFrzThermCond();
    hcap = lstfntl->getFrzVolHeatCapa();
  }
  double pce = abs(lstfntl->pce_f-lstfntl->pce_t);
  hca[ind] = (pce + hcap);
  cn[ind] = tca[ind] / dx[ind];
  cap[ind] = hca[ind] * dx[ind];

  // Lower layers:
  // Fill solver arrays for regular layers below frontlayer
  Layer* currl = lstfntl->nextl;
  while (currl != NULL) {
    ind = currl->indl;
    t[ind] = currl->tem;
    dx[ind] = currl->dz;
    dx[ind] = temutil::NON_ZERO(dx[ind], 1);
    tca[ind] = currl->getThermalConductivity();
    hcap = currl->getHeatCapacity();
    pce = abs(currl->pce_f - currl->pce_t);
    hca[ind] = pce + hcap;
    cn[ind] = tca[ind]/dx[ind];
    cap[ind] = hca[ind] * dx[ind];
    currl = currl->nextl;
  }

  // The bottom boundary layer is an extra, virtual layer
  // Fill solver arrays for this layer:
  ind++;
  double gflx = 0.0;  // no bottom heat flux assumed
  t[ind] = t[ind-1] + gflx/(tca[ind-1]) * dx[ind-1];
  s[ind] = 0.;
  e[ind] = t[ind];
  endind = ind;

  // Run these layers in the solver
  iterate(startind, endind);

  // Post-iteration: check for nans in the solver results array
  for (int il = startind; il <= endind; il++) {
    warn_bad_tld(il);
  }

  // Update layer temperatures from solver results array.
  // First, set lstfntl->tem based on frozenfrac
  // If setnftl is false, the frontlayer temp was already updated
  // by processAboveFronts or processBetweenFronts.
  if (setfntl) {
    currl = lstfntl;
    currl->tem = -zerodegc + (1.0-currl->frozenfrac) * (2.0* zerodegc); //Scale temps between -zerodegc and zerodegc based on frozenfrac
  }
  // Update temps of regular layers below frontlayer
  currl = lstfntl->nextl;
  while (currl != NULL) {
    ind = currl->indl;
    currl->tem = tld[ind];
    currl = currl->nextl;
  }
  }// Closes BOOST named scope
}

void TemperatureUpdator::iterate(const int &startind, const int &endind) {
  BOOST_LOG_NAMED_SCOPE("TemperatureUpdator::iterate"){

  // besides 'top'/'bottom', there is ONLY 1 actual layer for iteration
  if (endind - startind ==2) {
    for (int il = startind; il <= endind; il++) {
      tid[il] = t[il]; // temperature at the begin of one day

      tld[il] = t[il]; // the last determined temperature
      warn_bad_tld(il);
    }

    tld[startind+1] = (tid[startind]+tid[endind])/2.0;
    warn_bad_tld(startind+1);

    return;
  }

  tschanged = true;
  tmld = 0; // tmld is time that is last determined
  itsum = 0;
  tleft = 1; // at beginning of update, tleft is one day
  tstep = TSTEPORG;

  for (int il = startind; il <= endind; il++) {
    tid[il] = t[il]; // temperature at the begin of one day

    tld[il] = t[il]; // the last determined temperature
    warn_bad_tld(il);

  }

  for (int i = startind; i <= endind; i++) {
    tis[i] = tld[i];
  }

  while (tmld < 1) {
    int st = updateOneTimeStep(startind, endind);

    if (st == -1) {
      // half the time step
      tstep = tstep / 2;

      if (tstep < TSTEPMIN) {
        tstep = TSTEPMIN;
      }

      tschanged = true;
    } else if (st == 0) {
      // find one solution for one timestep, advance to next one
      for (int i = startind; i <= endind; i++) {
        tis[i] = tld[i];
      }

      tleft -= tstep;
      tmld += tstep;

      // find the proper timestep for rest period

      if (!tschanged) { //if timestep has not been changed during last time step
        if (tstep < TSTEPMAX) {
          tstep *= 2;
          tschanged = true;
        }
      } else {
        tschanged = false;
      }

      // make sure tleft is greater than zero
      tstep = fmin(tleft, tstep);

      if (tstep == 0) {
        tmld = 1;
      }
    }
  } // end of while
  } // Closes BOOST named scope
}


int TemperatureUpdator::updateOneTimeStep(const int &startind,
                                          const int & endind) {
  BOOST_LOG_NAMED_SCOPE("TemperatureUpdator::updateOneTimeStep"){

  int status = -1;
  int is;

  for (int i = startind; i <= endind; i++) {
    tii[i] = tis[i];
  }

  is = updateOneIteration(startind, endind);

  if (is == 0 || tstep<=TSTEPMIN) { // success or min. iterative time-interval
    status = is;

    for (int i = startind; i <= endind; i++) {
      tld[i] = tit[i];
      warn_bad_tld(i);
    }

    return 0; //status;

  } else if (is == -1) { //the difference between iteration is too big,
                         //  iterate again
    for (int i = startind; i <= endind; i++) {
      tii[i] = tis[i]; //syiawi, previous tii[i] = tit[i]; bug
    }

    status = is;
  }

  return status;

  }// Closes BOOST named scope
}

// the main calculation will be done here
int TemperatureUpdator::updateOneIteration(const int &startind,
                                           const int & endind) {
  itsum++;
  double dt = tstep * timestep;
  cns.geBackward(startind, endind, tii, dx, cn, cap, s, e, dt);
  cns.cnForward(startind, endind, tii, tit, s, e);

  for (int il = startind; il <= endind; il++) {
    if (fabs(tii[il] - tit[il]) > ttole) {
      return -1;
    }
  }

  return 0;
}

void TemperatureUpdator::setGround(Ground* groundp) {
  ground = groundp;
}
