/*
 * TemperatureUpdator.cpp
 *
 *  Created on: 2011-8-18 by yis
 *  Checked on: 2013-02-18 by F.-M. Yuan
 */

#include "TemperatureUpdator.h"

TemperatureUpdator::TemperatureUpdator() {
	TSTEPMAX = 1;
	TSTEPMIN = 1.0e-5;
	TSTEPORG = 0.5;

	ttole = 0.01;
	mindzlay = 0.01;

	debugging = false;  // switch for error message print out
	zerodegc = 0.001;  // a constant to represent temperature near zero in degree C

}

TemperatureUpdator::~TemperatureUpdator() {

}

void TemperatureUpdator::updateTemps(const double & tdrv, Layer *fstvalidl,	Layer *backl,
		Layer* fstsoill, Layer* fstfntl, Layer *lstfntl, const double& ts, const bool & meltsnow) {

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
//*/
	// the following 'bool' are used to how we are dealing with the 'frontl' and their boundaries
	bool usefntl = true;   // use 'frontl' as boundary (suggested!!!), otherwise use the above/below layer of 'frontl'
	                       // after-testing note: 'true' is correct, otherwise 'temperature' profile will not match with 'stefan' algorithm estimation of 'fronts'
	bool adjfntl = true;  // adjusting 'frontl' temperature by weighting 'frozenfrac' of the layer
	                       // after-testing note: not matter much

	if (fstfntl == NULL && lstfntl == NULL) {
		// no fronts in soil column
		processColumnNofront(fstvalidl, backl, tdrv, meltsnow);
		itsumall = itsum;
	} else if (fstfntl->indl == lstfntl->indl) {
		processAboveFronts(fstvalidl, fstfntl, tdrv, meltsnow, usefntl); //ALWAYS NO adjusting the temperature in the 'fstfntl'
		itsumabv = itsum;

		processBelowFronts(backl, lstfntl, adjfntl, usefntl);
		itsumblw = itsum;

		itsumall = itsumabv + itsumblw;
	} else if (fstfntl->indl != lstfntl->indl) {
		// there are two different layers which contain front(s)
		processAboveFronts(fstvalidl, fstfntl, tdrv, meltsnow, usefntl);
		itsumabv = itsum;

		processBelowFronts(backl, lstfntl, false, usefntl);  //'lstfntl' only partially updated, so cannot adjust it
		itsumblw = itsum;

		processBetweenFronts(fstfntl, lstfntl, adjfntl, usefntl);

		itsumall = itsumabv + itsumblw;

	}

	//fstvalidl->tem = tdrv;

}


void TemperatureUpdator::processColumnNofront(Layer* fstvalidl, Layer *backl, const double & tdrv, const bool & meltsnow) {

	int startind, endind;

	// the boundary of 'fstvalidl' as a virtual layer, serving as boundary condition
	int ind = fstvalidl->indl - 1;
	startind = ind;
	if (meltsnow) {
		t[ind] = 0.0;
	} else {
		t[ind] = tdrv;
	}
	e[ind]  = t[ind];
	s[ind]  = 0.;
	cn[ind] = 1.0e2; // assume very big thermal conductivity for this virtual layer (Reason for osicillation!!! from e20 to e2)
	cap[ind]= 0.; // assume no heat capacity for this virtual layer

	// actual layers, above 'frontl', invovling thermal process
	Layer* currl = fstvalidl;
	double hcap;
	double pce;
	while (currl != NULL) {

			ind++;
			dx[ind] = currl->dz;
			t[ind] = currl->tem;
			if (currl->isSnow) {
				type[ind] = 1;
			} else {
				type[ind] = 0;
			}
			tca[ind] = currl->getThermalConductivity();
			hcap = currl->getHeatCapacity();
			pce = abs(currl->pce_f - currl->pce_t);
			hca[ind] = (pce + hcap);
			cn[ind] = tca[ind] / dx[ind];
			cap[ind] = hca[ind] * dx[ind];

			currl = currl->nextl;
	}

	// bottom boundary 'virtual' layer
	ind++;
	endind = ind;
	double gflx = 0.0;  // no bottom heat flux assumed
	t[ind] = t[ind-1] + gflx/(tca[ind-1]) * dx[ind-1];
	s[ind] = 0.;
	e[ind] = t[ind];

	// iteration-solover
	iterate(startind, endind);

	// post-iteration
	//check whether is nan
	if (debugging) {
		for (int il = startind; il <= endind; il++) {
			if ((tld[il])!=(tld[il])) {
				string msg = "TemperatureUpdator::procesColumnNofront - tld is nan";
				cout << msg << "\n";
			}

			if (tld[ind]==MISSING_D) {
				string msg = "checking!";
				cout<<msg<<"\n";
			}

		}
	}

	// pass the data to double-linked structure
	ind = startind+1; // 0 is a virtual layer for top boundary condition, 1 is the first layer
	currl = fstvalidl;
	while (currl != NULL) {
		currl->tem = tld[ind];
		currl = currl->nextl;
		ind++;
		if (ind>endind-1) ind=endind-1;  // endind is a virtual layer for bottom boundary
	}

}


void TemperatureUpdator::processAboveFronts(Layer* fstvalidl, Layer*fstfntl, const double & tdrv, const bool & meltsnow,
		const bool &usefntl) {

	double hcap;
	int startind, endind;

	// the boundary of 'fstvalidl' as a virtual layer, serving as boundary condition
	int ind = fstvalidl->indl - 1;
	startind = ind;
	if (meltsnow) {
		t[ind] = 0.0;
	} else {
		t[ind] = tdrv;
	}
	e[ind]  = t[ind];
	s[ind]  = 0.;
	cn[ind] = 1.0e2; // assume very big thermal conductivity for this virtual layer
	cap[ind]= 0.; // assume no heat capacity for this virtual layer

	// actual layers, above 'frontl', involving thermal process
	Layer* currl = fstvalidl;
	double pce = 0.;
	while (currl != NULL) {
			if (currl->indl >= fstfntl->indl) break;

			ind++;
			dx[ind] = currl->dz;
			t[ind] = currl->tem;
			if (currl->isSnow) {
				type[ind] = 1;
			} else {
				type[ind] = 0;
			}
			tca[ind] = currl->getThermalConductivity();
			hcap = currl->getHeatCapacity();
			pce = abs(currl->pce_f - currl->pce_t);
			hca[ind] = (pce + hcap);
			cn[ind] = tca[ind] / dx[ind];
			cap[ind] = hca[ind] * dx[ind];

			currl = currl->nextl;
	}

	// the upper portion of the first front layer
	double frntdz = ground->frontsz[0] - fstfntl->z;
	int frnttype = ground->frontstype[0];
	ind++;
	t[ind] = fstfntl->tem;
	dx[ind] = frntdz;
	if (dx[ind] < mindzlay) dx[ind] = mindzlay;
	if (frnttype == 1) {
			tca[ind] = fstfntl->getFrzThermCond();
			hcap = fstfntl->getFrzVolHeatCapa();
	} else {
			tca[ind] = fstfntl->getUnfThermCond();
			hcap = fstfntl->getUnfVolHeatCapa();
	}
	pce = abs(fstfntl->pce_f-fstfntl->pce_t);
	hca[ind] = (pce + hcap);
	cn[ind] = tca[ind]  / dx[ind];
	cap[ind] = hca[ind] * dx[ind];

	// bottom boundary layer - 'front' or 'frontl->nextl'
	bool usefstfntl = usefntl;
	if (fstfntl->nextl==NULL) usefstfntl=true;  //if there's no layer below 'fstfntl'
	ind++;
	if (usefstfntl) {
		if (frnttype == 1) {  // 'freezing' front: above -, below +
			t[ind] = -zerodegc;
		} else {
			t[ind] = zerodegc;
		}
	} else {
		t[ind] = fstfntl->nextl->tem;
	}
	endind = ind;
	s[ind] = 0.;
	e[ind] = t[ind];

	// iteration
	iterate(startind, endind);

	// pass the data to double-linked structure
	ind = startind+1; // 0 is a virtual layer for top boundary condition, 1 is the first layer
	currl = fstvalidl;
	while (currl != NULL) {
		if (ind>endind-1) break;

		currl->tem = tld[ind];
		currl = currl->nextl;
		ind++;
	}

	// checking
	if (debugging) {
		for (int il = startind; il <= endind; il++) {
			if (tld[il]!=tld[il]) {
				string msg = "TemperatureUpdator::processAboveFronts - tld is nan";
				cout << msg << "\n";
			}

			if (tld[il]==MISSING_D) {
				string msg = "checking!";
				cout<<msg<<"\n";
			}

		}
	}

}

void TemperatureUpdator::processBetweenFronts(Layer*fstfntl, Layer*lstfntl, const bool&adjfntl, const bool&usefntl) {

	int startind, endind;

	if (lstfntl->indl - fstfntl->indl < 2) {
		double ffstfntl = fstfntl->dz/(fstfntl->dz+lstfntl->dz);
		fstfntl->nextl->tem = ffstfntl*fstfntl->tem+(1.0-ffstfntl)*lstfntl->tem;  // at this point, both 'fst-/lstfntl->tem' already known
		return;
	}

	// pre-iteration
	double frntdz1 = (fstfntl->z+fstfntl->dz) - ground->frontsz[0];
	int frnttype1 = ground->frontstype[0];
	double hcap = 0.;
	double pce = 0.;
	pce = abs(fstfntl->pce_f-fstfntl->pce_t);

	// top boundary: a 'virtual' layer
	int ind;
	bool usefstfntl = usefntl;
	if (fstfntl->prevl==NULL) usefstfntl=true;
	ind = fstfntl->indl-1;
	if (usefstfntl) {
		if (frnttype1 == 1) {  // 'freezing' front: above -, below +
			t[ind] = zerodegc;
		} else {
			t[ind] = -zerodegc;
		}

	} else {
		Layer *prevl = fstfntl; //->prevl;
		t[ind]  = prevl->tem;
		cn[ind] = 1.0e2f; // assume very big thermal conductivity for this virtual layer
		cap[ind]= 0.; // assume no heat capacity for this virtual layer
	}
	startind = ind;
	e[ind] = t[ind];
	s[ind] = 0.;

	// the bottom portion of the first front
	if (!usefstfntl) {
		ind++;
		t[ind] = fstfntl->tem;
	}
	dx[ind] = frntdz1;
	if (dx[ind] < mindzlay)	dx[ind] = mindzlay;
	if (frnttype1 == 1) {
		tca[ind] = fstfntl->getUnfThermCond();     // freezing front's bottom is 'Unfrozen'
		cn[ind] = tca[ind] / dx[ind];
		hca[ind] = (pce + fstfntl->getUnfVolHeatCapa());
		cap[ind] = hca[ind] * dx[ind];
	} else {      // thawing front's bottom is 'Frozen'
		tca[ind] = fstfntl->getFrzThermCond();
		cn[ind] = tca[ind] / dx[ind];
		hca[ind] = (pce + fstfntl->getFrzVolHeatCapa());
		cap[ind] = hca[ind] * dx[ind];
	}

	// layers of non-front containing, if any
	Layer* currl = fstfntl->nextl;
	while (currl != NULL) {
			if (currl->indl >= lstfntl->indl) break;

			ind++;
			t[ind] = currl->tem;
			dx[ind] = currl->dz;
			tca[ind] = currl->getThermalConductivity();
			hcap = currl->getHeatCapacity();
			pce = abs(currl->pce_f - currl->pce_t);
			hca[ind] = pce + hcap;
		 	cn[ind] = tca[ind]/dx[ind];
			cap[ind] = hca[ind] * dx[ind];

			currl = currl->nextl;
	}

	// the upper portion of 'lstfntl'
	ind++;
	int numfnt = ground->frontstype.size();
	double frntdz2 = ground->frontsz[numfnt-1] - lstfntl->z;   //the upper portion of the last front
	int frnttype2 = ground->frontstype[numfnt-1];
	dx[ind] = frntdz2;
	if (dx[ind] < mindzlay)	dx[ind] = mindzlay;
	if (frnttype2 == 1) {
		tca[ind] = lstfntl->getFrzThermCond();   // freezing front's above is 'Frozen'
		cn[ind] = tca[ind] / dx[ind];
		hca[ind] = (pce + lstfntl->getFrzVolHeatCapa());
		cap[ind] = hca[ind] * dx[ind];
	} else {  //thawing front's above is 'Unfrozen'
		tca[ind] = lstfntl->getUnfThermCond();
		cn[ind] = tca[ind] / dx[ind];
		hca[ind] = (pce + lstfntl->getUnfVolHeatCapa());
		cap[ind] = hca[ind] * dx[ind];
	}
	t[ind] = lstfntl->tem;

	// bottom boundary layer - 'front' or 'frontl->nextl'
	bool uselstfntl = usefntl;
	if(lstfntl->nextl==NULL) uselstfntl=true;
	ind++;
	if (uselstfntl) {
		if (frnttype2 == 1) {  // 'freezing' front: above -, below +
			t[ind] = -zerodegc;
		} else {
			t[ind] = zerodegc;
		}
	} else {
		t[ind] = lstfntl->nextl->tem;
	}
	endind = ind;
	s[ind] = 0.;
	e[ind] = t[ind];

	//iteration
	iterate(startind, endind);

	// post-iteration
	if (!usefstfntl) {
		ind = startind+1; //'startind' is for top boundary, so exclusively for actual layers
	} else {
		ind = startind;
	}
	currl = fstfntl;
	if (adjfntl) {
		 // 'fstfntl' upper portion has already temporarily assigned to the whole layer by this moment in 'processAboveFronts()'
		if (frnttype1==1) {
			currl->tem *= currl->frozenfrac;
			currl->tem += tld[ind]*(1.-currl->frozenfrac);  // frozen/unfrozen fraction weighted for the 'fstfntl'
		} else if (frnttype1==-1) {
			currl->tem *= (1.0-currl->frozenfrac);
			currl->tem += tld[ind]*currl->frozenfrac;  // frozen/unfrozen fraction weighted for the 'fstfntl'
		}
	} else {
		currl->tem = tld[ind];
	}

	currl = fstfntl->nextl;
	while (currl != NULL) {
		if (currl->indl >= lstfntl->indl) break; // temperature for layers in between two 'front' containing layers only
		ind++;
		currl->tem = tld[ind];

		currl = currl->nextl;

	}

	currl = lstfntl;
	ind++;     // if above 'ind' counts well, no need to use 'lstfntl->indl' to avoid array boundary issue
	if (adjfntl) {
		 // 'lstfntl' bottom portion has already temporarily assigned to the whole layer by this moment in 'processBelowFronts()'
		if (frnttype2==1) {   //freezing front: upper portion is frozen
			currl->tem *= currl->frozenfrac;
			currl->tem += tld[ind]*(1.-currl->frozenfrac);  // frozen/unfrozen fraction weighted for the 'lstfntl'
		} else if (frnttype2==-1) {
			currl->tem *= (1.0-currl->frozenfrac);
			currl->tem += tld[ind]*currl->frozenfrac;  // frozen/unfrozen fraction weighted for the 'lstfntl'
		}
	} else {
		currl->tem = tld[ind];
	}

	// checking
	if (debugging) {
		for (int il = startind; il <= endind; il++) {
			if (tld[il]!=tld[il]) {
				string msg = "TemperatureUpdator::processBetweenFronts - tld is nan";
				cout << msg << "\n";
			}

			if (tld[il]==MISSING_D) {
				string msg = "checking!";
				cout<<msg<<"\n";
			}

		}
	}

}

void TemperatureUpdator::processBelowFronts(Layer* backl, Layer*lstfntl, const bool &adjfntl, const bool &usefntl) {

	int startind, endind;

	// pre-iteration
	int numfnt = ground->frontsz.size();
	double frntdz = (lstfntl->z+lstfntl->dz) - ground->frontsz[numfnt-1];
	int frnttype = ground->frontstype[numfnt-1];
	double hcap = 0.;
	double pce = 0.;
	pce = abs(lstfntl->pce_f-lstfntl->pce_t);

	// top boundary: a 'virtual' layer
	int ind;
	bool uselstfntl = usefntl;
	if (lstfntl->prevl==NULL) uselstfntl=true;
	ind = lstfntl->indl-1;
	if (uselstfntl) {
		if (frnttype == 1) {  // 'freezing' front: above -, below +
			t[ind] = zerodegc;
		} else {
			t[ind] = -zerodegc;
		}
	} else {
		Layer *prevl = lstfntl; //->prevl;
		t[ind]   = prevl->tem;
		cn[ind] = 1.0e2; // assume very big thermal conductivity for this virtual layer
		cap[ind]= 0.; // assume no heat capacity for this virtual layer
	}
	startind = ind;
	e[ind] = 0.;
	s[ind] = t[ind];

	// bottom portion of 'lstfntl'
	if (!uselstfntl) {
		ind++;
		t[ind] = lstfntl->tem;
	}
	dx[ind] = lstfntl->dz*frntdz;
	if (dx[ind] < mindzlay) dx[ind] = mindzlay;
	if (frnttype == 1) {
		tca[ind] = lstfntl->getUnfThermCond();
		cn[ind] = tca[ind] / dx[ind];
		hca[ind] = (pce + lstfntl->getUnfVolHeatCapa());
		cap[ind] = hca[ind] * dx[ind];
	} else if (frnttype == -1) {
		tca[ind] = lstfntl->getFrzThermCond();
		cn[ind] = tca[ind] / dx[ind];
		hca[ind] = (pce + lstfntl->getFrzVolHeatCapa());
		cap[ind] = hca[ind] * dx[ind];
	}

	// non-front containing layer(s), if any
	Layer* currl = lstfntl->nextl;
	while (currl != NULL) {
		ind++;
		t[ind] = currl->tem;
		dx[ind] = currl->dz;
		tca[ind] = currl->getThermalConductivity();
		hcap = currl->getHeatCapacity();
		pce = abs(currl->pce_f - currl->pce_t);
		hca[ind] = pce + hcap;
		cn[ind] = tca[ind] / dx[ind];
		cap[ind] = hca[ind] * dx[ind];

		currl = currl->nextl;
	}

	// bottom boundary 'virtual' layer
	ind++;
	endind = ind;
	double gflx = 0.0;  // no bottom heat flux assumed
	t[ind] = t[ind-1] + gflx/(tca[ind-1]) * dx[ind-1];
	s[ind] = 0.;
	e[ind] = t[ind];

	//iteration
	iterate(startind, endind);

	// post-iteration process
	if (!uselstfntl) {
		ind = startind+1; //'startind' is for top boundary, so exclusively for actual layers
	} else {
		ind = startind;
	}
	currl = lstfntl;
	if (adjfntl) {
		// 'lstfntl' upper portion has already temporarily assigned to the whole layer by this moment in 'processAboveFronts'
		// ONLY if 'fstfntl' and 'lstfntl' are exactly one layer, so be cautious when input 'adjfntl'
		int frntnum = ground->frontstype.size();
		if (ground->frontstype[frntnum-1]==1) {   //freezing front: upper portion is frozen
			currl->tem *= currl->frozenfrac;
			currl->tem += tld[ind]*(1.-currl->frozenfrac);  // frozen/unfrozen fraction weighted for the 'lstfntl'

		} else if (ground->frontstype[frntnum-1]==-1) {
			currl->tem *= (1.0-currl->frozenfrac);
			currl->tem += tld[ind]*currl->frozenfrac;  // frozen/unfrozen fraction weighted for the 'lstfntl'
		}

	} else {
		currl->tem = tld[ind];
	}

	ind++;
	currl = lstfntl->nextl;
	while (currl != NULL) {
		currl->tem = tld[ind];
		currl = currl->nextl;
		ind++;
		if (ind>endind-1) ind=endind-1;  // endind is a virtual layer for bottom boundary, so any layer below just taking the 'tld[ending-1]' all the ime

	}

	// checking
	if (debugging) {
		for (int il = startind; il <= endind; il++) {
			if (tld[il]!=tld[il]) {
				string msg = "TemperatureUpdator::processBelowFronts - tld is nan";
				cout << msg << "\n";
			}

			if (tld[il]==MISSING_D) {
				string msg = "checking missing tld!";
				cout<<msg<<"\n";
			}

		}
	}

}

void TemperatureUpdator::iterate(const int &startind, const int &endind) {

	// besides 'top'/'bottom', there is ONLY 1 actual layer for iteration
	if (endind - startind ==2) {
		for (int il = startind; il <= endind; il++) {
			tid[il] = t[il]; // temperature at the begin of one day
			tld[il] = t[il]; // the last determined temperature
		}
		tld[startind+1] = (tid[startind]+tid[endind])/2.0;

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

			if (!tschanged) { // if timestep has not been changed during last time step
				if (tstep < TSTEPMAX) {
					tstep *= 2;
					tschanged = true;
				}
			} else {
				tschanged = false;
			}

			// make sure tleft is greater than zero
			tstep = fmin(tleft, tstep);
			if (tstep == 0)
				tmld = 1;
		}

	} // end of while

}


int TemperatureUpdator::updateOneTimeStep(const int &startind, const int & endind) {

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
		}

		return 0; //status;
	} else if (is == -1) { // the difference between iteration is too big, iterate again
		for (int i = startind; i <= endind; i++) {
			tii[i] = tis[i]; //syiawi, previous tii[i] = tit[i]; bug
		}
		status = is;
	}

	return status;
}

// the main calculation will be done here
int TemperatureUpdator::updateOneIteration(const int &startind, const int & endind) {

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

void TemperatureUpdator::setGround(Ground* groundp){
	ground = groundp;
}
