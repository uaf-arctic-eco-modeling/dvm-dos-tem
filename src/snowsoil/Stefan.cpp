#include "Stefan.h"

Stefan::Stefan(){
	 ITMAX =1;
     TSTEPMAX = 1.0;    //unit: day
     TSTEPORG = 0.5;
     TSTEPMIN = 1.e-4;
     
     ttole = 0.05;  // don't change this threshold
};

Stefan::~Stefan(){
	
};

void Stefan::setGround(Ground* grndp){
	ground = grndp;
};

void Stefan::updateFronts(const double & tdrv, Layer *toplayer, Layer *botlayer,Layer *fstfntl, Layer* lstfntl){
 	
    double tkres; // thermal conductivity for calculating resistence
 	double tkfront; // thermal conductivity for calculating part front depth
 	double tkunf, tkfrz;
 	int frozenstate; // the frozen state of a soil layer based on the driving temperature

 	// top-down propogation of front
 	// driving force
 	double tdrv0 = tdrv;
 	double dse = fabs(tdrv0 * 86400); // the extra degree second, assume using one day time step
 	double sumresabv  =0. ; // sum of resistence for above layers;

    if(tdrv0>0){
    	frozenstate =-1;
   	}else {
   		frozenstate =1;
   	}

    // find the new front
    double newfntz = 0.;
 	Layer * currl=NULL;
    currl = toplayer;
 	while(currl!=NULL && dse>0.){
 		if(currl->isRock) {
 			if (dse>0.) {
 				newfntz = currl->prevl->z+currl->prevl->dz;   // this will weep out all fronts in the soil column
 			}
 			break; // for bedrock, break
 		}
 		
 		tkunf = currl->getUnfThermCond();
 	    tkfrz = currl->getFrzThermCond();
 		if(tdrv0<0){
 		   	 tkres   = tkfrz;
 		   	 tkfront = tkunf;
 		}else {
 		   	 tkres   = tkunf;
 		   	 tkfront = tkfrz;
 		}

 		sumresabv += currl->dz/tkres;

 		if (currl->frozen != frozenstate) {    // if the layer has a different frozen status

			if(currl->isSnow){
 				processFrontSnowLayer(tkfront, dse, sumresabv, tdrv0, currl);
 			}else if(currl->isSoil){
 				processFrontSoilLayerDown(frozenstate, sumresabv, tkfront, dse, newfntz, currl);
 			}
 		}

 		currl=currl->nextl;
 	}
 	// then incorporate the new front into the two deques: 'ground->frontsz' and 'ground->frontstype'
 	if (newfntz>0.) frontsDownDeque(newfntz, frozenstate);

/*
 	// bottom-up determined front moving
 	// (1) determine the bottom driving layer
 	Layer* botdrvl = botlayer;   //initial botdrvl setting-up
 	if (lstfntl!=NULL) {
 		botdrvl = lstfntl;       // last layer with 'front'
 	} else {
 		while (!botdrvl->prevl->isSoil) {
 			botdrvl = botdrvl->prevl;        // or the first rock layer if no layer with 'front'
 		}
 	}

 	double dzbelow = 0.;        // the acutal botdrvl used is the initial one or its below 1.0 m layer
 	if(botdrvl->nextl!=NULL){
 		botdrvl = botdrvl->nextl;
 		while (botdrvl!=NULL){
 			dzbelow += botdrvl->dz;
 			if(dzbelow >= 2.0){    // the layer 1.0 meter below the 'lastfntl' or 'fstrockl'
 				break;
 			}else{
 				botdrvl = botdrvl->nextl;
 			}
 		}
 	}
 	
 	// (2) find the front
 	if(lstfntl!=NULL && botdrvl!=NULL){
 		double sumresblw=0 ;

 		currl =botdrvl;
 		//Layer * prevl = currl->prevl;
 		double tdrv1  = botdrvl->tem;
 		if(tdrv1>0){
 			frozenstate =-1;
 		}else if(tdrv1<0){
 			frozenstate =1;
 		}
 		  	   	
 		dse = fabs(tdrv1 * 86400);
 		newfntz = 0.;
 		while(currl!=NULL && dse>0.){
 			if(currl->isSnow){
				newfntz = 0.;
 			    break;
			}

 	       tkunf = currl->getUnfThermCond();
 		   tkfrz = currl->getFrzThermCond();
 		   if(tdrv1<0){
 			   tkres = tkfrz;
 			   tkfront =tkunf;
 		   }else {
 			   tkres = tkunf;
 			   tkfront = tkfrz;
 		   }
 		   
		   sumresblw += currl->dz/tkres;
 		   if (currl->frozen != frozenstate) {
 			   if(currl->isSoil){
 				   processFrontSoilLayerUp(frozenstate, sumresblw, tkfront, dse, newfntz, currl);
 			   }
 		   }

 		   currl=currl->prevl;
 		}

 		// (3) then incorporate the new front into the two deques: 'ground->frontsz' and 'ground->frontstype'
 	 	if (newfntz>=0.) frontsUpDeque(newfntz, -frozenstate);   //NOTE: bottom-up freezing front actually is the thawing front if look downward
 	
 	}
*/

};
 
void Stefan::processFrontSnowLayer(double const & tkfront, double & dse, double & sumresabv,
		         const double & tdrv, Layer* currl){

	SnowLayer* snwl; // check to see whether the dse can totally melt a snow layer
 	snwl = dynamic_cast<SnowLayer*>(currl);
 	double dz = snwl->dz;
 	double dsn;
 	if(tdrv>0){
 		
 		double volwat = snwl->ice/(snwl->rho*dz);
 		dsn = getDegSecNeeded(dz, volwat, tkfront, sumresabv);
 		if(dse>=dsn){
 			snwl->frozen =-1;               // this layer will be removed in 'Ground::constructSnowLayer()'
 			snwl->liq += snwl->ice;           // the 'liq' will be collected in 'Snow_Env::meltSnowlayerAfterT()' as melting water

 			dse -= dsn;
 		}else{
 			snwl->frozen = 0;

 			//snow ice water converted to liq water (partially melted), which used in 'snow_env.cpp':: meltSnowLayerAfterT()
 			double swereduction = 0.;
 			if (dsn > 0.) swereduction = snwl->ice*(dse/dsn);    // this layer will be reduced in 'snow_env.cpp'
 			snwl->liq += swereduction;

 			dse =0.;
		}
 	}
 	
}
 
void Stefan::processFrontSoilLayerDown(const int &frozenstate, double const & sumrescum, double const & tkfront ,
                        double & dse, double & newfntz, Layer* sl){

	newfntz = 0.;
 	double volwat; // volumetric ice/liq water content to be thawing/freezing;
 	double dz;     // thickness to be thawing/freezing
 	double dsn ;   // the degree seconds needed to fully freeze/thaw one layer of dz thickness
 	double partd;

	 dz =sl->dz;
	 if (frozenstate==1) {
		 volwat = max(0., sl->getVolLiq()-sl->minliq/DENLIQ/sl->dz);
	 } else {
		 volwat = sl->getVolIce();
	 }
	 dz *= volwat/sl->getEffVolWater();

	 dsn = getDegSecNeeded(dz, volwat, tkfront, sumrescum);

	 if(dse>=dsn){
		 newfntz = sl->z+sl->dz;

		 sl->frozen = frozenstate;  // set this layer 'frozen' state as fully frozen or unfrozen
		 if (frozenstate == 1) {    // this is needed for upwardly front processing, otherwise unstable condition may occur
			 sl->ice += (sl->liq - sl->minliq);
			 sl->liq = sl->minliq;
			 if (sl->ice>sl->maxice) sl->ice = sl->maxice;
		 } else {
			 sl->liq += sl->ice;
			 sl->ice = 0.;
		 }
		 if (sl->ice>sl->maxice) sl->ice = sl->maxice;

		 dse -= dsn;

	 } else {

		 //partd=getPartialDepth(volwat, tkfront, sumrescum, dse);  //may not be consistent
		 partd = dse/dsn*dz;

		 double newfntdz = 0.;
		 int fntnum = ground->frontsz.size();

		 if (fntnum<=0) {                                // no front at all
			 newfntdz = partd;
		 } else {
			 if (ground->frontsz[0]>=(sl->z+sl->dz)
			     || ground->frontsz[fntnum-1]<sl->z) {   // all existing front(s) above/below the current soil layer
				 newfntdz = partd;
			 } else {                                    // exiting front(s) in/containing the current soil layer
				 double partdleft = partd;
				 int fntind = 0;
				 while (fntind<fntnum && partdleft>0.){
					 int fnttype = ground->frontstype[fntind];
					 double fntz = ground->frontsz[fntind];

					 if (fntz>sl->z) {
						 if (fntz<=(sl->z+sl->dz)){  //existing 'front(s)' in the current soil layer only

							 double fntprvz = sl->z;   // the previous front's depth OR current soil layer up boundary
							 if (fntnum>=2 && fntind>0) { // if there is a previous 'front' in the deque
								 fntprvz = max(sl->z, ground->frontsz[fntind-1]);
							 }

							 double fntdz= ground->frontsz[fntind]-fntprvz;  // the distance of the 'fntind'th front from previous front

							 double newfntdzmax = sl->dz;  // the max. distance of the new front
							 if (fntnum>=2 && fntind<(fntnum-1)) { // if there is a following 'front' in the deque
								 newfntdzmax = min(sl->dz, ground->frontsz[fntind+1]-sl->z);  // and, if that neibouring 'front' is in current soil layer
							 }

							 if (fnttype==frozenstate) {   // moving the same-type front
								 newfntdz = min(newfntdzmax, (fntz-sl->z)+partdleft);  //moving the same type front down until the layer boundry or the next inside front
								 partdleft -=newfntdz;
							 } else {                     // for the opposite type front
								 if (partdleft<fntdz) {
									 newfntdz = (fntprvz-sl->z)+partdleft;      //adding a new front before the current front
									 partdleft = 0.;                            // using up all left 'partd'
								 } else {
									 newfntdz = newfntdzmax;  // sweeping the opposite type front down until the layer boundry or the next inside front
									 partdleft -= fntdz;      // but, only using up 'fntdz' of left 'partd', and the rest will be used to move/sweep the next front
								 }
							 }

						 } else {
							 if (fntind>=fntnum-1 && partdleft==partd) {  //existing fronts not in but containing the current layer
								 newfntdz = partdleft;
								 partdleft = 0.;
							 }
						 }
					 }

					 fntind++;
				 }

			 }
		 }

		 newfntz = sl->z+newfntdz;
		 if (newfntz>sl->z+0.9999*sl->dz) {
			 newfntz=sl->z+0.9999*sl->dz;     // this '0.9999' will keep the front within a layer, otherwise may cause mathmatic issue
		 }

		 sl->frozen = 0;
		 if (frozenstate == 1) {    // this is needed for phase changed water
			 sl->ice += (sl->liq-sl->minliq)*partd/sl->dz;
			 sl->liq -= (sl->liq-sl->minliq)*partd/sl->dz;
			 if (sl->ice>sl->maxice) sl->ice = sl->maxice;
		 } else {
			 sl->liq += sl->ice*partd/sl->dz;
			 sl->ice -= sl->ice*partd/sl->dz;
		 }

		 dse = 0.;

	 }
}

void Stefan::processFrontSoilLayerUp(const int &frozenstate, double const & sumrescum, double const & tkfront ,
                        double & dse, double & newfntz, Layer* sl){

	newfntz = 0.;
 	double volwat; // volumetric water content;
 	double dz;     // thickness
 	double dsn ;   // the degree seconds needed to fully freeze/thaw one layer
 	double partd;

	 dz =sl->dz;
//	 volwat = sl->getEffVolWater();
///*
	 if (frozenstate==1) {
		 volwat = sl->getVolLiq()-sl->minliq/DENLIQ/sl->dz * sl->poro;
	 } else {
		 volwat = sl->getVolIce();
	 }
	 if (volwat<0.) volwat = 0.;
	 dz *= volwat/sl->getEffVolWater();

//*/
	 dsn = getDegSecNeeded(dz, volwat, tkfront, sumrescum);

	 if(dse>=dsn){
		 newfntz = sl->z;           // NOTE: 'newfntz' is the depth from zero ground surface

		 sl->frozen = frozenstate;  // set this layer 'frozen' state as fully frozen or unfrozen
		 if (frozenstate == 1) {    // may not be needed here, but just for in case
			 sl->ice += sl->liq - sl->minliq;
			 sl->liq = sl->minliq;
		 } else {
			 sl->liq += sl->ice;
			 sl->ice = 0.;
		 }
		 dse -= dsn;

	 } else {
		 partd=getPartialDepth(volwat, tkfront, sumrescum, dse);   // note: everything is UPwardly processing

		 double newfntdz = partd;
		 int fntnum = ground->frontsz.size();
		 int fntind = fntnum-1;
		 while (fntind>=0 && partd>0.){
			double fntz = ground->frontsz[fntind];
			int fnttype = ground->frontstype[fntind];

			if (fntz<=sl->z+sl->dz && fntz>sl->z){

				 	double fntdz = (sl->z+sl->dz)-fntz;                  // the distance of the 'fntind'th front from the 'sl->z+sl->dz'
					if (fnttype==frozenstate) {
						newfntdz = fntdz+partd;
					} else {
						if (partd<fntdz) {
							newfntdz = partd;
						} else if (fntind==0 || ground->frontsz[fntind-1]<=sl->z){
							newfntdz = sl->z;
						}

						partd -=newfntdz;
					}

			} else if (fntz<=sl->z) {
					break;
			}

			fntind--;

		 }

		 newfntz = sl->z+sl->dz-newfntdz;     // Note: 'newfntz' is from top, but 'newfntdz' is from bottom here
		 if (newfntz<=sl->z+0.01*sl->dz) {
			 newfntz=sl->z+0.01*sl->dz;     // this will keep the front within a layer, otherwise may cause mathmatic issue
			 newfntdz = 0.99*sl->dz;
		 }

		 sl->frozen = 0;
		 if (frozenstate == 1) {    // may not be needed, but just for in case
			 sl->ice += sl->liq*newfntdz/sl->dz;
			 sl->liq -= sl->liq*newfntdz/sl->dz;
		 } else {
			 sl->liq += sl->ice*newfntdz/sl->dz;
			 sl->ice -= sl->ice*newfntdz/sl->dz;
		 }

		 dse = 0.;
	 }
}

// fronts moving downward
void Stefan::frontsDownDeque(const double &newfntz, const int &newfnttype){

	int numfnt = ground->frontsz.size();

	if (numfnt<=0){
		if (newfntz<ground->lstsoill->z+ground->lstsoill->dz){
			ground->frontsz.push_front(newfntz);
			ground->frontstype.push_front(newfnttype);
		}
	} else {

		// first, sweep all fronts, if any, above the new front, which assummed to penetrate through the soil profile downwardly
		double dzres = 0.;    // the difference of new front and its closest upper existing front
		while (ground->frontsz.size()>0 && newfntz>=ground->frontsz[0]) {
				dzres = newfntz - ground->frontsz[0];      // this will update when do the loop
				ground->frontsz.pop_front();
				ground->frontstype.pop_front();
		}

		// then, only need to deal with the updated top front, which always lower than the new front
		if ((ground->frontsz.size()<=0) || (newfnttype!=ground->frontstype[0])) {
			if (newfntz<ground->lstsoill->z+ground->lstsoill->dz){
				ground->frontsz.push_front(newfntz);
				ground->frontstype.push_front(newfnttype);
			}
		} else {   // same front type, then need to move the front down
			ground->frontsz[0] += dzres;              // this 'dzres' actually is the residue after new front swept all its above fronts
			                                          // which used to move same-type front down, but no need for different-type front
			                                          // because a new front has already added above.
		}

	 }
}

// fronts moving upward
void Stefan::frontsUpDeque(const double &newfntz, const int &newfnttype){

	int numfnt = ground->frontsz.size();

	if (numfnt<=0) {
		if (newfntz>ground->fstsoill->z){
			ground->frontsz.push_back(newfntz);
			ground->frontstype.push_back(newfnttype);
		}
	} else {

		// first, sweep all fronts, if any, below the new front, which assummed to penetrate through the soil profile upwardly
		double dzres = 0.;    // the difference of new front and its closest lower existing front
		while (ground->frontsz.size()>0 && newfntz<=ground->frontsz[numfnt-1]) {
			dzres = newfntz - ground->frontsz[numfnt];      // this will update when do the loop
			ground->frontsz.pop_back();
			ground->frontstype.pop_back();
			numfnt = ground->frontsz.size();      // this is needed for 'while' loop
		}

		// then, only need to deal with the updated uppest front, which always higher than the new front
		numfnt = ground->frontsz.size();
		if ((numfnt<=0) || (newfnttype!=ground->frontstype[numfnt-1])) {
			if (newfntz>ground->fstsoill->z){
				ground->frontsz.push_back(newfntz);
				ground->frontstype.push_back(newfnttype);
			}
		} else {   // same front type, then need to move the front down
			ground->frontsz[numfnt-1] += dzres;              // this 'dzres' actually is the residue after new front swept all its below fronts
			                                          // which used to move same-type front up, but no need for different-type front
			                                          // because a new front has already added above.
		}

	 }
};

double Stefan::getDegSecNeeded(const double & dz,
 				const double & volwat,  const double & tk, const double & sumresabv){
 	/*input
 	 * 	   dz: the thickness of  fraction of (or whole)  soil layer: 
 	 *     volwat: volumetric water content, either ice or liquid water
 	 *     tk: thermal conductivity of that part of (or whole) layer
 	 *     sumresabv: the sum of resistance for all the layers above
 	 */
 	 double needed=0.;
 	 
 	 double effvolwat = volwat;
 	 double lhfv = 3.34e8;
 	 needed = lhfv * effvolwat * dz * (sumresabv +0.5 * dz/tk);
 	 
 	 return needed;
};
 
//calculate partial depth based on extra degree seconds
double Stefan::getPartialDepth(const double & volwat, const double & tk,
 								const double & sumresabv, const double & dse){
	/* input
	 *  dse: extra degree second
	 */
 	double partd;
 	double effvolwat = volwat;
 
 	double lhfv = 3.34e8;
 	double firstp = tk * sumresabv;
 	double second1 = tk * tk * sumresabv * sumresabv;
 	double second2 = 2 * tk * dse/(lhfv * effvolwat);
 	partd = -1 * firstp  + sqrt(second1 + second2);
 	
 	return partd;
 };
 
 ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
 // update soil temperatures
 
void Stefan::updateTemps(const double & tdrv, Layer *toplayer, Layer *botlayer,
  						Layer* fstfntl, Layer *lstfntl ){
  	   
    Layer* currl=toplayer;
    while(currl!=NULL){
    	temold[currl->indl-1] = currl->tem;          // 'currl->indl' starting from 1
    	currl=currl->nextl;
    }

	 itsumall =0;
  	
  	 if(fstfntl ==NULL && lstfntl==NULL){
  		 // no fronts in soil column
  		 processLayersNofront(toplayer, tdrv);
  		 itsumall =itsum;

  	 }else if(fstfntl->indl ==lstfntl->indl){     // only one layer with fronts
  		  //added
  		  processLayersAbvfront(toplayer, fstfntl, tdrv);
   		 itsumall =itsum;

  		  if(lstfntl->indl<botlayer->indl){
  			  processLayersBlwfront(toplayer, lstfntl);
  			  itsumall +=itsum;
  		  }

  	 }else if(fstfntl->indl !=lstfntl->indl){  		 // there are at least two different layers which contain front(s)

  		 processLayersAbvfront(toplayer, fstfntl, tdrv);
  		 itsumall = itsum;
  	  
  		 if(lstfntl->indl<botlayer->indl){
  			 processLayersBlwfront(toplayer, lstfntl);
  			 itsumall += itsum;
  	  	
  			 processLayersBtnfront(toplayer, fstfntl, lstfntl);
  	  		 itsumall += itsum;
  		 }

  	  
  	 }

     //
  	 currl=toplayer;
     while(currl!=NULL){

    	 currl->tem   = tld[currl->indl];
    	 currl->tcond = currl->getThermalConductivity();

    	 currl=currl->nextl;
     }

     //check whether is nan
/*  	 for(int il=0 ; il<MAX_GRN_LAY+2; il++){

  		 if(isnan(tld[il])){

  			 string msg = "tld is nan";
  			 cout<<msg+"\n";
			 tld[il]=tid[il];       //Yuan: rather the initial values (this is a temperary settle!!!!)
  			 //break;
  		 }
  	 }
*/
};

void Stefan::processLayersNofront(Layer* toplayer, const double & tdrv){
     double tc, hcap;
  	 int startind, endind;

     int ind=0;
  	 t[ind] = tdrv;
  	 s[ind] = 0.;
  	 e[ind] = tdrv;
  	 cn[ind]  = 1e20f;// assume very big thermal conductivity for this virtual layer
  	 cap[ind] = 0.; // assume no heat capacity for this virtual layer

  	 Layer* currl =toplayer;
  	 while(currl!=NULL){
  	 	ind++;

  	 	t[ind] =currl->tem;      // NOTE: t[ind] starting from 1 here
  	 	dx[ind] = currl->dz;
  	 	tc = currl->getThermalConductivity();
  	 	hcap= currl->getHeatCapacity();
  	 	cn[ind] = tc/dx[ind];
  	 	cap[ind] = hcap * dx[ind];
  	 	currl=currl->nextl;

  	 }

  	 ind++;
  	 t[ind] = t[ind-1];
 	 s[ind] = 0.;
 	 e[ind]= t[ind];

 	 startind =0; //always zero
     endind= ind; //
     iterate(startind, endind, true, true, toplayer);

};

void Stefan::processLayersAbvfront(Layer* toplayer, Layer*fstfntl, const double & tdrv){
	double tc, hcap;
  	int startind, endind;

  	int ind=0;         // a virtual layer containing Tair information
  	t[ind] = tdrv;
  	e[ind] = tdrv;
  	s[ind] = 0.;
  	cn[ind]  = 1e20f;// assume very big thermal conductivity for this virtual layer
  	cap[ind] = 0.; // assume no heat capacity for this virtual layer

  	Layer* currl =toplayer;
  	while(currl!=NULL){
  	 	ind++;
  	 	t[ind] =currl->tem;
  	 	dxold[ind] = dx[ind];
  	 	dx[ind] = currl->dz;
  	 	tc = currl->getThermalConductivity();
  	 	hcap= currl->getHeatCapacity();
  	 	cn[ind] = tc/dx[ind];
  	 	cap[ind] = hcap * dx[ind];

  	 	currl=currl->nextl;
  	 	if(currl!=NULL){
  	 		if(currl->indl >fstfntl->indl) break;
  	 	}


  	 }

  	 ind++;
  	 if(fstfntl->frozen==1){   // the first front layer as the bottom of this column
  		 t[ind] = -0.01; // front tem can be assumed to be near zero
  	 }else{
  		 t[ind] = 0.01;
  	 }
 	 s[ind] = 0.;
 	 e[ind]= t[ind];

     startind = 0;
     endind   = ind;
     iterate(startind, endind, false, true, ground->toplayer);

};

void Stefan::processLayersBlwfront(Layer* toplayer, Layer* lstfntl){
    double tc, hcap;
  	int startind, endind;

     int ind=lstfntl->indl;;
  	 t[ind] = -0.1; //assume the front is the top interface of virtual layer
  	 e[ind] = 0.;
  	 s[ind] = 0.;

     dx[ind] = lstfntl->dz;
 	 cn[ind]  = lstfntl->getThermalConductivity()/dx[ind];
  	 cap[ind] = lstfntl->getHeatCapacity()*dx[ind];

     Layer*	 currl =lstfntl->nextl;
  	 while(currl!=NULL){
  	 	ind++;
  	 	t[ind] =currl->tem;
  	 	if(currl->frozen ==1 && t[ind]>0){
  	 		t[ind] =-0.01;
  	 	}else if(currl->frozen ==-1 && t[ind]<0){
  	 		t[ind] =0.01;
  	 	}

  	 	dx[ind] = currl->dz;
  	 	tc = currl->getThermalConductivity();
  	 	hcap = currl->getHeatCapacity();
  	 	cn[ind] = tc/dx[ind];
  	 	cap[ind] = hcap * dx[ind];
  	 	currl=currl->nextl;
  	 }

  	 ind =ind+1;
  	 double deltat = t[ind-1]-t[ind-2];
  	 t[ind] = t[ind-1] +deltat;
 	 s[ind] = 0.;
 	 e[ind]= t[ind];

 	 startind =lstfntl->indl;
     endind= ind; //
     iterate(startind, endind, true, false, toplayer);

};


void Stefan::processLayersBtnfront(Layer *toplayer, Layer*fstfntl, Layer*lstfntl){

	double tc, hcap;
  	int startind, endind;
    if(lstfntl->indl - fstfntl->indl <2){
        return;
    }

     int ind=fstfntl->indl;
  	 t[ind] = 0; //assume the front is the top interface of virtual layer
  	 if(fstfntl->nextl->frozen ==1){
  		 t[ind] = -0.1;
  	 }else  if(fstfntl->nextl->frozen ==-1){
  		 t[ind] = 0.1;
  	 }
  	 e[ind] = 0.;
  	 s[ind] = 0.;

  	 Layer*	 currl =fstfntl->nextl;
  	 while(currl!=NULL){
  	 	ind++;
  	 	t[ind] =currl->tem;
  	 	dx[ind] = currl->dz;
  	 	tc = currl->getThermalConductivity();
  	 	hcap= currl->getHeatCapacity();
  	 	cn[ind] = tc/dx[ind];
  	 	cap[ind] = hcap * dx[ind];
  	 	currl=currl->nextl;

  	 	if(currl->indl >= lstfntl->indl) break;
  	 }

  	 ind =ind+1;
  	 t[ind] = t[ind-1];
 	 s[ind] = 0.;
 	 e[ind]= t[ind];

 	 startind =fstfntl->indl;
     endind= ind; //
     iterate(startind, endind, false, false, toplayer);

};

void Stefan::iterate(const int &startind, const int &endind, const bool & lstlaybot, const bool & fstlaytop, Layer *toplayer){
  	
	itsum =0;
	tschanged = true;
	tmld =0; // tmld is time that is last determined

	tleft = 1.0;          /* at beginning of update, tleft is one day*/
	tstep = TSTEPORG;
	
	for(int il =startind ; il<=endind; il++){
	  tid[il] = t[il];      // temperature at the begin of one day
	  tld[il] = t[il];      // the last determined temperature
	}

	while(tmld<1.0){

		for(int i=startind; i<=endind; i++){
	 		tis[i] = tld[i];	
		}
		int st = updateOneTimeStep(startind, endind, lstlaybot, fstlaytop, toplayer);

		if(st==-1 && tstep >= TSTEPMIN) {
			// half the time step
			tstep = tstep/2;
			tschanged = true;
		}else if(st==0 || tstep<TSTEPMIN){
			// find one solution for one timestep, advance to next one
			tleft -= tstep;
			tmld += tstep;
		 
			// find the proper timestep for rest period
			if(!tschanged){ // if timestep has not been changed during last time step
				if(tstep<TSTEPMAX){
					tstep *=2;
					tschanged = true;
				}
			}else{
				tschanged =false;
			}
		 
			// make sure tleft is greater than zero
			tstep = min(tleft, tstep);

			if(tstep==0)tmld=1;
		}
	}// end of while
  	
};

int Stefan::updateOneTimeStep(const int startind, const int & endind, const bool & lstlaybot, const bool & fstlaytop, Layer *toplayer){
	int status =-1;
	
	for(int i=startind; i<=endind; i++){
	     tii[i] = tis[i];
	}
		 
	for (int it=1; it<=ITMAX; it++){
		status = updateOneIteration(startind, endind, lstlaybot, fstlaytop, toplayer);
		if(status==0 || it==ITMAX){// success or max. iterative times
			for(int i=startind; i<=endind; i++){
				tld[i] = tit[i];
			}

			return status;
		}else if(status ==-1){// the difference between iteration is too big, iterate again
			for(int i=startind; i<=endind; i++){
				tii[i] = tit[i];
			}

		}
	  
	}

	return status;
}; 
  
int Stefan::updateOneIteration(const int startind, const int & endind, const bool & lstlaybot ,const bool & fstlaytop, Layer *toplayer){
	itsum++;
	double tself, tdown, tup, t1, t2;
	double hclat;
    double dt = tstep *86400.;

    // adjusting snow-layers' heat capacity (Yuan: but why?)
    if(fstlaytop){
    	Layer* currl =toplayer;
    	int il=0;
    	while(currl!=NULL){
    		if(currl->isSnow){
    			il =currl->indl;
    			if(currl->indl==1){
    				tself = tii[1];
    				tdown = tii[2];
    				t1 = tself;
    				t2 = (tdown + tself)/2.;
    				if(t1>0 || t2>0){
    					hclat =3.337e5 *(currl->ice)/currl->dz;
    					cap[1] = ( currl->getHeatCapacity()+hclat)*currl->dz;
    				}else{
    					cap[1] = currl->getHeatCapacity()*currl->dz;
    				}
    			}else{
    				tself = tii[il];
    				tup = tii[il-1];
    				t2 = tself;
    				t1 = (tup + tself)/2.;
    				if(t1*t2<0){
    					hclat =3.337e5 *(currl->ice)/currl->dz;
    					cap[il] = (currl->getHeatCapacity()+hclat)*currl->dz;
    				}else{
    					cap[il] = currl->getHeatCapacity()*currl->dz;
    				}
      			
    			}

    		} else if(currl->isSoil){
    			break;
    		}

    		currl=currl->nextl;

    	}
    }

    double endlayergflux=0.;
    if (lstlaybot) endlayergflux = 0.50; // bottom soil layer heat flux assumed as 0 (be careful here!)
    cns.geBackward(startind, endind, tii, cn, cap, s, e, dt, endlayergflux);
	cns.cnForward(startind, endind, tii, tit, s, e);

	int numl = 0;
	double tdiff = 0.;
	for(int il =startind; il<=endind ; il++){
	  	tdiff+=fabs(tii[il]-tit[il]);
	  	numl++;

/*    	if(isnan(tii[il])){
    		return -1;
    	}
	  	if(isnan(tit[il])){
    		return -1;
    	}
*/
	} 	
  	if(tdiff>ttole*numl){
		return -1;         // return for further iteration
  	}
  
	return 0; 
};
