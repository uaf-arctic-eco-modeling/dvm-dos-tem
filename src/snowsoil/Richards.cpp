#include "Richards.h"


Richards::Richards(){
     TSTEPMIN = 1.e-6;      //
     TSTEPMAX = 0.2;
     TSTEPORG = 0.1;
          
     ITMAX = 10;
     liqtole = 0.1;  // tolearance is in fraction of 'maxliq' in a layer
};

Richards::~Richards(){
	
};

//
void Richards::update(Layer *fstsoill, Layer* drainl, const double & draindepth, const double & fbaseflow,
		double trans[], const double & evap, const double & infil){

	// prepare arrays for calling Richards Equation's solver
	if (draindepth<=0.) {
		return;           // the drainage occurs in the surface, no need to update the SM
	}
	prepareSoilNodes(fstsoill, drainl, draindepth);


	if (numal==1){			// one layer: no need to iterate, tip-bucket approach enough
		int ind =0;

		qin[ind] = infil - evap;

		double s1 = (liq[ind]-minliq[ind])/dzmm[ind]/poro[ind];
		double s2 = hksat[ind] * exp (-2*(zmm[ind]/1000.))
					* pow((double)s1, (double)2*bsw[ind] +2);
		hk[ind] = s1*s2;
		qout[ind] = -hk[ind]*fbaseflow - trans[ind];

		liqld[ind] += (qin[ind]+qout[ind]);
		qdrain = -hk[ind]*fbaseflow*86400.;            //bottom drainage: mm/day

	} else {    // iteration

		iterate(trans, evap, infil, fbaseflow);

	}

    //Yuan: post-iteration
    Layer *currl = fstsoill;
    int ind =-1;      // liqld[MAX_SOI_LAY], starting from 0
    while(currl!=NULL){
    	if (currl->isSoil) {
    		ind++;
    		if(ind >=numal){
    			liqld[ind] = currl->liq;
    		}

    		currl->liq = liqld[ind];

    		if(currl->liq<currl->minliq){
    			currl->liq=currl->minliq;
    		}

    		if(currl->liq>currl->maxliq){
    			currl->liq=currl->maxliq;
    		}

    		// Yuan: for output of hydraulic conductivity
    		SoilLayer* sl=dynamic_cast<SoilLayer*>(currl);
    		double ss = (sl->getVolLiq()-sl->minliq)/(sl->poro-sl->getVolIce());
    		double hcond = sl->hksat * pow((double)ss, (double)2*sl->bsw +2);
    		currl->hcond = hcond*86400.; //unit: mm/day (hksat: mm/sec)

    	} else {
    		break;
    	}

     	currl=currl->nextl;
    };

};

void Richards::prepareSoilNodes(Layer* fstsoill, Layer * drainl, const double & draindepth){
    // it is assumed that all layers in Richards will be unfrozen, i.e., from 'fstsoill' to ''drainl'
	Layer* currl = fstsoill;                         // the first soil layer is 'fstsoill'
	int ind = 0;
	numal = 0;
	while(currl!=NULL){
		if(currl->isSoil && !currl->isMoss){   //excluding 'moss' horizon
			if (currl->solind <= drainl->solind) {   // the last soil layer is 'drainl'
				numal++;

				double dzadj = 1.;
				if (currl->solind == drainl->solind) {
					dzadj = (draindepth-currl->z)/currl->dz;     //if 'draindepth' is inside of 'drainl'
					drainldzadj = dzadj;       //saved for later use
				}

				poro[ind] = currl->poro;
				effporo[ind] = max(currl->minliq/DENLIQ/currl->dz, currl->poro-currl->getVolIce());
				dzmm[ind] = currl->dz *1.e3 *dzadj;
				zmm[ind]  = currl->z *1.e3 + 0.5 *dzmm[ind]; // the node depth (middle point of a layer)
				minliq[ind] = currl->minliq *dzadj;
				maxliq[ind] = (currl->maxliq - currl->ice) *dzadj;

				liq[ind] = currl->liq *dzadj;

				psisat[ind] = currl->psisat;
				hksat[ind] = currl->hksat;
				bsw[ind]   = currl->bsw;

				if (liq[ind]>maxliq[ind]){
					liq[ind]=maxliq[ind];
//					cout<<"'liq' is greater than 'maxliq' - please checking! \n";
				}
				if (liq[ind]<minliq[ind]){
					liq[ind]=minliq[ind];
//					cout<<"'liq' is less than 'minliq' - please checking! \n";
				}

			  	ind++;

			}


		}else{
			break;	
		}

		currl= currl->nextl;
	}

};

void Richards::iterate(const double trans[], const double & evap,
		               const double & infil, const double & baseflow){

	//all fluxes in mm/sec
	qinfil = infil;
	qevap  = evap;
	fbaseflow = baseflow;
	for(int il =0; il<MAX_SOI_LAY; il++){
		qtrans[il] = trans[il]; // liq at the begin of one day
	}
  	
	//
	tschanged = true;
	tmld  = 0;    // tmld is time that is last determined	
	itsum = 0;
	tleft = 1;  // at beginning of update, tleft is one day
	if(infil>0){
		TSTEPORG =TSTEPMAX/5.;	
	}else{
		TSTEPORG =TSTEPMAX;
	}
	tstep = TSTEPORG;
	

	for(int il =0; il<numal; il++){
		liqid[il] = liq[il]; // liq at the begin of one day
		liqld[il] = liq[il]; // the last determined liq
	}

	qdrain = 0.;   // for accumulate bottom drainage (mm/day)
	while(tmld<1){
		for(int i=0; i<numal; i++){
	 		liqis[i] = liqld[i];	
		}
		
		//find one solution for one timestep
		int st = updateOneTimeStep();
		if(st<0) {
			tstep = tstep/2;   // half the time step
			if(tstep < TSTEPMIN){
				string msg = "tstep is too small in richard2 ";
				return;
			}
			tschanged = true;
		
		} else if(st==0){   //advance to next timestep
			
			qdrain +=qout[numal-1]*tstep*86400.; //unit: mm/s*secs

			tleft -= tstep;
			tmld += tstep;
		 
			// find the proper timestep for rest period		 
			if(!tschanged){ // if timestep has not been changed during last time step 
				if(tstep<TSTEPMAX){
					tstep = TSTEPORG;  //*=2;   //Yuan:
					tschanged = true;
				}		    
			}else{
				tschanged =false;	
			}
			
			// make sure tleft is greater than zero
			tstep = min(tleft, tstep);	
			if(tstep==0) {
				tmld=1;
				qdrain = 0.;
			}
		}
	} // end of while
  	
};
    
int Richards::updateOneTimeStep(){
	int status =-1;
	
	for(int i=0; i<numal; i++){
	 	liqii[i] = liqis[i];	
	}

   	status = updateOneIteration();
    	
   	if(status==0){// success
    	
   		for(int i=0; i<numal; i++){
    		liqld[i] = liqit[i];
    	}
    		
    }
	
    return status;
	  
}; 
  
int Richards::updateOneIteration(){
	
	double poro1, effporo1, volliq1, s1;
	double poro2, effporo2, volliq2, s2;
	double s_node;
    double wimp=0.0001; // mimumum pore for water to exchange between two layers
    double smpmin = -1.e8;
    double dt =tstep*86400;
	
	itsum++;
	for(int il =0; il<MAX_SOI_LAY; il++){
		dwat[il]=0.;	

	}
    
	//Yuan: k-dk/dw-h relationships for all soil layers
	for (int indx=0; indx<numal; indx++) {
			
		poro1 = poro[indx];
		effporo1 = effporo[indx];
		volliq1 = (liqii[indx]-minliq[indx])/dzmm[indx];
			
		if(indx==numal-1){  //the last layer: free drainage
			s1 = volliq1/poro1;
			s2 = hksat[indx] * exp (-2*(zmm[indx]/1000.))
					* pow((double)s1, (double)2*bsw[indx] +2);
			hk[indx] = s1*s2;
			dhkdw[indx] = (2.*bsw[indx]+3)*s2*0.5/poro1;
		} else {			
			poro2 = poro[indx+1];
			effporo2 = effporo[indx+1];
			volliq2 = (liqii[indx+1]-minliq[indx+1])/dzmm[indx+1];
			
			if(effporo1<wimp || effporo2<wimp){
				hk[indx] = 0.;
				dhkdw[indx] =0.;
			} else {
				s1 =(volliq2+volliq1)/(poro2+poro1);
				s2 = hksat[indx+1] * exp (-2*(zmm[indx+1]/1000.))
						* pow((double)s1, (double)2*bsw[indx+1] +2);

				hk[indx] = s1*s2;
				dhkdw[indx] = (2.*bsw[indx]+3)*s2*0.5/poro2;

			}			
		}
			
		s_node = volliq1/poro1;
		s_node = max(0.01, (double)s_node);
		s_node = min(1., (double)s_node);
		smp[indx] = psisat[indx] *pow(s_node, -bsw[indx]);
		smp[indx] = max(smpmin, smp[indx]);

		dsmpdw[indx]= -bsw[indx] * smp[indx] /(s_node*poro1);

    }
	
	//
	int ind;
	double den, num;
	double dqodw1, dqodw2, dqidw0, dqidw1;	
	double sdamp =0.;

	if(numal>=2){

		ind = 0;            // for first layer
		qin[ind] = qinfil -qevap;
		den = zmm[ind+1]-zmm[ind];
		num = smp[ind+1]-smp[ind] -den;
		qout[ind] = -hk[ind] * num/den;
		dqodw1 = -(-hk[ind]*dsmpdw[ind] + num* dhkdw[ind])/den;
		dqodw2 = -(hk[ind]*dsmpdw[ind+1] + num* dhkdw[ind])/den;
		
		rmx[ind] = qin[ind] - qout[ind] - qtrans[ind];
		amx[ind] = 0.;
		bmx[ind] = dzmm[ind] *(sdamp +1/dt) + dqodw1;
		cmx[ind] = dqodw2;
		
		if (numal>2) {
			for(ind=1; ind<numal-1; ind++){  // layer 2 ~ the second last bottom layer
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
			}
		}

		ind = numal-1;   //bottom layer
		den = zmm[ind]-zmm[ind-1];
		num = smp[ind]-smp[ind-1] -den;
		qin[ind] = -hk[ind-1]*num/den;
		dqidw0 = -(-hk[ind-1]*dsmpdw[ind-1] + num* dhkdw[ind-1])/den;
		dqidw1 = -(hk[ind-1]*dsmpdw[ind] + num* dhkdw[ind-1])/den;
		
		qout[ind] = hk[ind]*fbaseflow;     //fbaseflow: fraction of free bottom water drainage condition (0 - 1, indicating drainage condition)
		dqodw1 = dhkdw[ind];
		rmx[ind] = qin[ind] -qout[ind] -qtrans[ind];
		amx[ind] = -dqidw0;
		bmx[ind] = dzmm[ind]/dt - dqidw1 + dqodw1;
		cmx[ind] = 0.;
	}
		
	ind =0;
	cn.tridiagonal(ind, numal, amx, bmx,cmx,rmx, dwat);  //solution
	
	// soil water for each layer after one iteration
    for(int il =0; il<numal; il++){
    	liqit[il] = liqii[il] + dzmm[il] * dwat[il];
/*    	if(isnan(liqit[il])){
    		string msg = "water is nan ";
	  	    cout << msg + " - in Richardss::updateOneIteration\n";
    		exit(-2);
    	}
*/
    }	
        
    //check the change of liquid water
    for(int il=0; il<numal; il++){

     	if(liqit[il]<minliq[il]){
    		return -1;
    	} else if(liqit[il]>maxliq[il]){
    		return -2;
    	} else if(fabs((liqit[il]-liqii[il])/maxliq[il])>liqtole){ //if change more than 50% of maxliq
    		return -3;
    	}
   }
     
   return 0;
	
};


