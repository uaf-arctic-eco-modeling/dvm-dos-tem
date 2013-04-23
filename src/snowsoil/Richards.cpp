#include "Richards.h"


Richards::Richards(){
     TSTEPMIN = 1.e-5;      //
     TSTEPMAX = 0.2;
     TSTEPORG = 0.1;
          
     LIQTOLE = 0.05;  // tolearance is in fraction of 'maxliq' in a layer
 	 mindzlay = 0.005;

     debugging = false;
};

Richards::~Richards(){
	
};

//
void Richards::update(Layer *fstsoill, Layer* bdrainl, const double & bdraindepth, const double & fbaseflow,
		double trans[], const double & evap, const double & infil, const double &ts){

	timestep = ts;
	drainl = bdrainl;
	if (bdraindepth<=0.) {
		return;           // the drainage occurs in the surface, no need to update the SM
	}

	//all fluxes already in mm/sec as input
	qinfil = infil;
	qevap  = evap;
	for(int il=1; il<=MAX_SOI_LAY; il++){
		qtrans[il] = trans[il-1];       // trans[] starting from 0, while here all arrays starting from 1
	}

	// initializing the arrays for use below
	for(int il=0; il<=MAX_SOI_LAY; il++){ // although starting 1, initialization from 0

		dzmm[il]    = MISSING_D;
		zmm[il]     = MISSING_D;
		effporo[il] = MISSING_D;
		effliq[il]  = MISSING_D;
		effminliq[il]=MISSING_D;
		effmaxliq[il]=MISSING_D;
		psisat[il]  = MISSING_D;
		hksat[il]   = MISSING_D;
		bsw[il]     = MISSING_D;

		hk[il]   = MISSING_D;
		dhkdw[il]= MISSING_D;
		smp[il]  = MISSING_D;
		dsmpdw[il]=MISSING_D;
		qin[il]  = MISSING_D;
		qout[il] = MISSING_D;

		liqii[il] = MISSING_D;
		liqit[il] = MISSING_D;
		liqis[il] = MISSING_D;
		liqid[il] = MISSING_D;
		liqld[il] = MISSING_D;

		amx[il] = MISSING_D;
		bmx[il] = MISSING_D;
		cmx[il] = MISSING_D;
		rmx[il] = MISSING_D;
		dwat[il]= MISSING_D;
	}
	qdrain = 0.;

	// loop for continuous unfrozen soil column section
	// in a soil profile, there may be a few or none
	Layer* currl=fstsoill;
	while (currl!=NULL && currl->isMoss) {   // excluding dead moss layer(s) for hydrological process due to hydraulic parameters not validated, which causes oscilation
		currl=currl->nextl;                  // if no exclusion of dead moss layer, comment out this 'while' loop
	}
	indx0sl = currl->solind;
	Layer* topsoill = currl;

	while (currl!=NULL && currl->solind<=drainl->solind) {
		// prepare arrays for calling Richards Equation's solver
		// for one continuous section of unfrozen soil column: 'soilind' from indx0al:indx0al+numal
		prepareSoilNodes(currl, bdraindepth);

		//
		if (numal==1){			// one layer: no need to iterate, tip-bucket approach enough
			int ind = indx0al;

			qin[ind]=0.;
			if (indx0al==fstsoill->solind) qin[ind] = infil - evap;

			double s1 = effliq[ind]/dzmm[ind]/effporo[ind];
			double s2 = hksat[ind] * exp (-2*(zmm[ind]/1000.))
					* pow((double)s1, (double)2*bsw[ind] +2);
			hk[ind] = s1*s2;
			if (ind==drainl->solind) {
				qout[ind] = hk[ind]*fbaseflow + trans[ind];
			} else {  //no drainage occurs if not in 'drainl'
				qout[ind] = trans[ind];
			}

			liqld[ind] += (qin[ind]-qout[ind]);

			if (ind==drainl->solind) {
				qdrain += hk[ind]*fbaseflow*timestep/86400.;            //bottom drainage: mm/day->mm/sec
			}
		} else if(numal>1) {    // iteration for unfrozen column with multiple layers
			iterate(trans, evap, infil, fbaseflow);

		} else { // if frozen (numal = 0), keep the current liq. water content
			liqld[currl->solind] = currl->liq;
		}

		//post-iteration
		// note: if not found a section of unfrozen soil column, indx0al=-1 and numal=0,
		//       then following 'while' and 'for' loops will not implement
		while (currl->solind<indx0al) currl = currl->nextl;
		for (int ind=indx0al; ind<indx0al+numal; ind++){

			currl->liq = liqld[ind]+effminliq[ind];

//*
 		    double minliq = effminliq[ind];
			if(currl->liq<minliq){
				currl->liq=minliq;
			}

 		    double maxliq = effmaxliq[ind];
 		    if(currl->liq>maxliq){
				currl->liq=maxliq;
			}
//*/
			// for output of hydraulic conductivity at each layer
			SoilLayer* sl=dynamic_cast<SoilLayer*>(currl);
			double ss = sl->getVolLiq()/(sl->poro-sl->getVolIce());
			double hcond = sl->hksat * pow((double)ss, (double)2*sl->bsw+2);
			currl->hcond = hcond*86400.; //unit: output in mm/day (hksat: mm/sec)

			// the following will move the 'currl' downward ONLY for 'numal' when the 'for' loop goes
     		currl=currl->nextl;

    	}// end of post-iteration

		// the following will move the 'currl' downward one layer for 'active layers' not find
    	if (numal<1) currl=currl->nextl;

	} // end of whole soil layers loop for unfrozen column sections

	// for layers above 'topsoill', e.g., 'dead moss', if excluded from hydrological process
	currl = topsoill->prevl;
	while (currl!=NULL && currl->nextl!=NULL){

		if (currl->indl<fstsoill->indl) break;    // if no layer excluded, the 'while' loop will break here

		double lwc = currl->nextl->getVolLiq();
		currl->liq = currl->dz*(1.0-currl->frozenfrac)*lwc*DENLIQ; //assuming same 'VWC' in the unfrozen portion as below
		currl=currl->prevl;

	}

};

// this will generate a conintuous unfrozen column for soil water update
void Richards::prepareSoilNodes(Layer* currsoill, const double & draindepth){
    // it is assumed that all layers in Richards will be unfrozen, i.e., from unfrozen 'topsoill' to ''drainl'
	Layer* currl = currsoill;                         // the first soil layer is 'topsoill'
	int ind = -1;
	indx0al = -1;
	numal = 0;
	while(currl!=NULL && currl->isSoil){
		if(currl->solind>=indx0sl){
			double dzunfrozen = currl->dz*(1.0-currl->frozenfrac);
			if (dzunfrozen>=mindzlay &&
				currl->solind <= drainl->solind) {   // the last soil layer is 'drainl'

				if (indx0al<0) indx0al=currl->solind;
				ind = currl->solind;
				numal++;

				// if partially unfrozen layer: need to adjust 'dz', 'z' for at top while not for bottom,
				// but not 'liq' (which always in unfrozen portion of layer)
				double frntdzadj = 1.;
				double frntzadj = 0.;
				// if drainage layer with watertable in it, 'dz' and 'liq' need to be adjusted, but not 'z'
				double drdzadj = 1.;
				if (currl->frozen==0) {
					frntdzadj=1.0-currl->frozenfrac; //fraction of unfrozen thickness for both top/bottom partially-frozen layers
					if (currl->solind==indx0al || currl->solind==drainl->solind) {
						frntzadj = fmax(0., currl->dz*currl->frozenfrac);   // depth adding of unfrozen section of top partially-frozen layer
					}
				} else if (currl->solind == drainl->solind) {  //unfrozen layer but drainl, indicates a watertable in the layer
					drdzadj = (draindepth-currl->z)/currl->dz;     //if 'draindepth' is inside of 'drainl'
				}

				double minvolliq = currl->minliq/DENLIQ/currl->dz;
				effporo[ind] = fmax(0., currl->poro-minvolliq);
				dzmm[ind] = currl->dz*1.e3*fmin(frntdzadj, drdzadj);
				zmm[ind]  = (currl->z+frntzadj)*1.e3 + 0.5 *dzmm[ind]; // the node depth (middle point of a layer)

				effminliq[ind] = currl->minliq*fmin(frntdzadj, drdzadj);
				effmaxliq[ind] = (effporo[ind]*dzmm[ind])*fmin(frntdzadj, drdzadj);
				effliq[ind] = fmax(0.0, currl->liq*drdzadj-effminliq[ind]);

				if (effliq[ind]<0. || effminliq[ind]<0. || effmaxliq[ind]<0.) {
					if (debugging) cout<<"effective liq is less than 0!";
				}

				psisat[ind] = currl->psisat;
				hksat[ind] = currl->hksat;
				bsw[ind]   = currl->bsw;

			} else {
				break;
			}

		}else{
			break;
		}

		currl= currl->nextl;
	}

};

void Richards::iterate(const double trans[], const double & evap,
		 const double & infil, const double & fbaseflow){
  	
	//
	tschanged = true;
	itsum = 0;
	tleft = 1.;    // at beginning of update, tleft is one timestep
	if(infil>0.){
		TSTEPORG =TSTEPMAX/20.;
	}else{
		TSTEPORG =TSTEPMAX;
	}
	tstep = TSTEPORG;
	
	for(int il=indx0al; il<indx0al+numal; il++){
		liqid[il] = effliq[il]; // liq at the begin of one day
		liqld[il] = effliq[il]; // the last determined liq
	}

	qdrain = 0.;   // for accumulate bottom drainage (mm/day)
	while(tleft>0.0){
		for(int il=indx0al; il<indx0al+numal; il++){
	 		liqis[il] = liqld[il];
		}
		
		//find one solution for one fraction of timestep
		int st = updateOnethTimeStep(fbaseflow);
		
		if(st==0 || (st!=0 && tstep<=TSTEPMIN)){   //advance to next timestep
			
			qdrain += qout[numal]*tstep*timestep; //unit: mm/s*secs

			tleft -= tstep;
		 
			// find the proper timestep for rest period		 
			if(!tschanged){ // if timestep has not been changed during last time step 
				if(tstep<TSTEPMAX){
					tstep = TSTEPORG;
					tschanged = true;
				}		    
			}else{
				tschanged =false;	
			}
			
			// make sure tleft is greater than zero
			tstep = fmin(tleft, tstep);
			if(tstep<=0) {  //starting the next iterative-interval
				qdrain = 0.;
			}

		} else {
			tstep = tstep/2.0;   // half the iterative-interval
			if(tstep < TSTEPMIN){
				tstep = TSTEPMIN;
			}
			tschanged = true;
		}

	} // end of while
  	
};
    
int Richards::updateOnethTimeStep(const double &fbaseflow){
	int status =-1;
	
	for(int i=indx0al; i<indx0al+numal; i++){
	 	liqii[i] = liqis[i];	
	}

   	status = updateOneIteration(fbaseflow);
    	
   	if(status==0 || tstep<=TSTEPMIN){ // success OR at the min. tstep allowed
    	
   		for(int i=indx0al; i<indx0al+numal; i++){
    		liqld[i] = liqit[i];
    	}
    		
    }
	
    return status;
	  
}; 
  
int Richards::updateOneIteration(const double &fbaseflow){
	
	double effporo0;
	double effporo2;
	double volliq  = 0.;
	double volliq2 = 0.;;
	double s1;
	double s2;
	double s_node;
    double wimp = 0.001; // mimumum pore for water to exchange between two layers
    double smpmin = -1.e8;
    double dt =tstep*timestep;
	
	itsum++;
    
	//Yuan: k-dk/dw-h relationships for all soil layers
	for (int indx=indx0al; indx<indx0al+numal; indx++) {
			
		effporo0 = effporo[indx];
		volliq = fmax(0., liqii[indx]/dzmm[indx]);
		volliq = fmin(volliq, effporo0);
			
		if(indx==indx0al+numal-1){
			s1 = volliq/fmax(wimp, effporo0);
			s2 = hksat[indx] * exp (-2.0*(zmm[indx]/1000.0))
					* pow(s1, 2.0*bsw[indx]+2.0);
			hk[indx] = s1*s2;
			dhkdw[indx] = (2.0*bsw[indx]+3.0)*s2*0.5/fmax(wimp, effporo0);
		} else {			

			effporo2 = effporo[indx+1];
			volliq2 = fmax(0., liqii[indx+1]/dzmm[indx+1]);
			volliq2 = fmin(volliq2, effporo2);
			
			if(effporo0<wimp || effporo2<wimp){
				hk[indx] = 0.;
				dhkdw[indx] = 0.;
			} else {
				s1 =(volliq2+volliq)/(effporo2+effporo0);
				s2 = hksat[indx+1] * exp (-2.0*(zmm[indx+1]/1000.0))
						* pow(s1, 2.0*bsw[indx+1]+2.0);

				hk[indx] = s1*s2;
				dhkdw[indx] = (2.*bsw[indx]+3.0)*s2*0.5/effporo2;

			}			
		}
			
		//
		if (hk[indx]>=numeric_limits<double>::infinity() || dhkdw[indx]>=numeric_limits<double>::infinity()){
			if (debugging) cout<<"hk is out of bound!";
		}
		if (volliq>1. || volliq2>1.0){
			if (debugging) cout<<"vwc is out of bound!";
		}

		//
		s_node = volliq/fmax(wimp, effporo0);
		s_node = fmax(0.001, (double)s_node);
		s_node = fmin(1.0, (double)s_node);
		smp[indx] = psisat[indx]*pow(s_node, -bsw[indx]);
		smp[indx] = fmax(smpmin, smp[indx]);
		dsmpdw[indx]= -bsw[indx]*smp[indx]/(s_node*fmax(wimp,effporo0));

		//
		if (smp[indx]>=numeric_limits<double>::infinity() || dsmpdw[indx]>=numeric_limits<double>::infinity()){
			if (debugging) cout<<"smp is out of bound!";
		}

    }
	
	// preparing matrice for solution
	double den, num;
	double dqodw1, dqodw2, dqidw0, dqidw1;	
	double sdamp =0.;

	int ind=indx0al;
	if(numal>=2){

		// layer 1
		qin[ind] = 0.;
		if (ind == indx0sl){     // for first soil layer: infiltration/evaporation occurs
			qin[ind] = qinfil -qevap;
		}
		den = zmm[ind+1]-zmm[ind];
		num = smp[ind+1]-smp[ind]-den;
		qout[ind] = -hk[ind] * num/den;
		dqodw1 = -(-hk[ind]*dsmpdw[ind] + num*dhkdw[ind])/den;
		dqodw2 = -(hk[ind]*dsmpdw[ind+1] + num*dhkdw[ind])/den;
		
		rmx[ind] = qin[ind] - qout[ind] - qtrans[ind];
		amx[ind] = 0.;
		bmx[ind] = dzmm[ind] *(sdamp +1/dt) + dqodw1;
		cmx[ind] = dqodw2;
		
		if (numal>2) {
			for(ind=indx0al+1; ind<indx0al+numal-1; ind++){  // layer 2 ~ the second last bottom layer
				den = zmm[ind]-zmm[ind-1];
				num = smp[ind]-smp[ind-1] -den;
				qin[ind] = -hk[ind-1]*num/den;
				dqidw0 = -(-hk[ind-1]*dsmpdw[ind-1] + num* dhkdw[ind-1])/den;
				dqidw1 = -(hk[ind-1]*dsmpdw[ind] + num* dhkdw[ind-1])/den;
		
				den = zmm[ind+1]-zmm[ind];
				num = smp[ind+1]-smp[ind] -den;
				qout[ind] = -hk[ind] * num/den;
				dqodw1 = -(-hk[ind]*dsmpdw[ind] + num* dhkdw[ind])/den;
				dqodw2 = -(hk[ind]*dsmpdw[ind+1] + num* dhkdw[ind])/den;
			
				rmx[ind] = qin[ind] -qout[ind] -qtrans[ind];
				amx[ind] =-dqidw0;
				bmx[ind] = dzmm[ind] /dt - dqidw1 + dqodw1;
				cmx[ind] = dqodw2;

				if (debugging) {
					if (amx[ind] != amx[ind] || bmx[ind] != bmx[ind] || cmx[ind] != cmx[ind] || rmx[ind] != rmx[ind]) {
						cout<<"checking here!";
					}
				}
			}
		}

		//bottom layer
		ind = indx0al+numal-1;
		den = zmm[ind]-zmm[ind-1];
		num = smp[ind]-smp[ind-1]-den;
		qin[ind] = -hk[ind-1]*num/den;
		dqidw0 = -(-hk[ind-1]*dsmpdw[ind-1] + num* dhkdw[ind-1])/den;
		dqidw1 = -(hk[ind-1]*dsmpdw[ind] + num* dhkdw[ind-1])/den;
		dqodw1 = dhkdw[ind];
		qout[ind] = 0.;   //no drainage occurs if not in 'drainl'
		if (ind==drainl->solind) {
			qout[ind] = hk[ind]*fbaseflow;    //free bottom drainage assumed
		}

		rmx[ind] = qin[ind] -qout[ind] -qtrans[ind];
		amx[ind] = -dqidw0;
		bmx[ind] = dzmm[ind]/dt - dqidw1 + dqodw1;
		cmx[ind] = 0.;
	}
		
	cn.tridiagonal(indx0al, numal, amx, bmx,cmx,rmx, dwat);  //solution
	
	// soil water for each layer after one iteration
    for(int il=indx0al; il<indx0al+numal; il++){
    	liqit[il] = liqii[il] + dzmm[il] * dwat[il];

    	if (debugging) {
    		if(liqit[il]!=liqit[il]){
    			string msg = "water is nan ";
    			cout << msg + " - in Richardss::updateOneIteration\n";
    		}

    		if (liqit[il]>=numeric_limits<double>::infinity()){
    			cout<<"checking!";
    		}

    	}

    }	
        
    //check the iteration result to determine if need to continue
    for(int il=indx0al; il<indx0al+numal; il++){
/* // the '-1' and '-2' status appear causing yearly unstablitity - so removed
    	if(liqit[il]<0.0){
     		return -1;    // apparently slow down the iteration very much during drying
    	}
    	if(liqit[il]>effmaxliq[il]){
    		return -2;    // apparently slow down the iteration very much during wetting
    	}
//*/
    	if(fabs((liqit[il]-liqii[il])/effmaxliq[il])>LIQTOLE){
    		return -3;
    	}
   }
     
   return 0;
	
};


