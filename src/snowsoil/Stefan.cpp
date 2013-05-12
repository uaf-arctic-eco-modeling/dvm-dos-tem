#include "Stefan.h"

Stefan::Stefan(){
	debugging = false;
};

Stefan::~Stefan(){
	
};

void Stefan::setGround(Ground* grndp){
	ground = grndp;
};

void Stefan::initpce(){
 	Layer * currl=ground->toplayer;
 	while(currl!=NULL){
 		currl->pce_f = 0.;
 		currl->pce_t = 0.;

 		currl = currl->nextl;
 	}

}

void Stefan::updateFronts(const double & tdrv, const double &timestep){

/////////////////////////////////
	// FIRST, positioning front depth and determining its type (freezing: 1; thawing: -1)

	Layer * toplayer = ground->toplayer;
 	
    double tkres; // thermal conductivity for calculating resistence
 	double tkfront; // thermal conductivity for calculating part front depth
 	double tkunf, tkfrz;

 	// top-down propogation of front
 	// driving force
 	int freezing1; // the freezing/thawing force based on the driving temperature
 	double tdrv1 = tdrv;
 	double dse = fabs(tdrv1 * timestep); // the extra degree second
 	double sumresabv  =0. ; // sum of resistence for above layers;

    if(tdrv1>0.0){
    	freezing1 = -1;
   	}else {
   		freezing1 =1;
   	}

    // find the new front
    double newfntz1 = 0.;
 	Layer * currl=NULL;
    currl = toplayer;
 	while(currl!=NULL && dse>0.){
 		if(currl->isRock) {
 			if (dse>0.) {
 				newfntz1 = currl->prevl->z+currl->prevl->dz;   // this will weep out all fronts in the soil column
 			}
 			break; // for bedrock, break
 		}
 		
 		tkunf = currl->getUnfThermCond();
 	    tkfrz = currl->getFrzThermCond();
 		if(tdrv1<0.0){
 		   	 tkres   = tkfrz;
 		   	 tkfront = tkunf;
 		}else {
 		   	 tkres   = tkunf;
 		   	 tkfront = tkfrz;
 		}

 		sumresabv += currl->dz/tkres;

 		if (currl->frozen != freezing1) {    // if the layer has a different frozen status

			if(currl->isSnow){
 				meltingSnowLayer(tkfront, dse, sumresabv, tdrv1, currl);
 			}else if(currl->isSoil){
 				processNewFrontSoilLayerDown(freezing1, sumresabv, tkfront, dse, newfntz1, currl);
 			}
 		}

 		currl=currl->nextl;
 	}
 	// then downwardly incorporate the new front into the two deques: 'ground->frontsz' and 'ground->frontstype'
 	if (newfntz1>=0.) {
 		frontsDequeDown(newfntz1, freezing1);
 	}
	// post-front-positioning adjustments
	combineExtraFronts();    // it is possible that there are too many fronts exist to hold in 'ed's 'frontz' and 'fronttype', so combine them if there are too many

	updateLayerFrozenState(ground->toplayer);     // this must be done before the following call
	updateWaterAfterFront(ground->toplayer);	  // after fronts processed, need to update 'ice' and 'liq' water in a layer due to phase change

	ground->setFstLstFrontLayers();

/*  // there exists a bug, turn off temporarily - to be checking (fmyuan: 3/22/2013)

    // After testing - the bottom-up appears having shallower ALD and colder soil T - be sure of validating this in field
 	// bottom-up determined front moving
 	// (1) determine the bottom driving layer

	double tdrv2  = prepareBottomDriving();
 	int freezing2; // the freezing/thawing force based on the driving temperature

 	// (2) find the front
 	if(botdrvl!=NULL && tdrv2!=MISSING_D){
 		//tdrv2=botdrvl->tem;
 		double sumresblw= 0.;

 		currl =botdrvl;
 		if(tdrv2>0.0){
 			freezing2 = -1;
 		}else{
 			freezing2 = 1;
 		}
 		  	   	
 		dse = fabs(tdrv2 * timestep);
 		double newfntz2 = botdrvl->z+botdrvl->dz;
 		while(dse>0.){
 			if(currl==NULL || currl->isSnow){
 	 			if (dse>0.) {
 	 				newfntz2 = 0.;   // this will weep out all fronts in the soil column
 	 			}
 	 			break; // for snow or already beyond ground, break
			}

 	       tkunf = currl->getUnfThermCond();
 		   tkfrz = currl->getFrzThermCond();
 		   if(tdrv2<0.0){
 			   tkres = tkfrz;
 			   tkfront =tkunf;
 		   }else {
 			   tkres = tkunf;
 			   tkfront = tkfrz;
 		   }
 		   
		   sumresblw += currl->dz/tkres;
 		   if (currl->frozen != freezing2) {
 			   if(currl->isSoil){
 				   processNewFrontSoilLayerUp(freezing2, sumresblw, tkfront, dse, newfntz2, currl);
 			   }
 		   }

 		   currl=currl->prevl;
 		}

 		// (3) then upwardly incorporate the new front into the two deques: 'ground->frontsz' and 'ground->frontstype'
 	 	if (newfntz2>=0.) {
 	 		frontsDequeUp(newfntz2, -freezing2);   //NOTE: bottom-up freezing front actually is the thawing front if look downward
 	 	}

 	 	// post-front-positioning adjustments
 	 	combineExtraFronts();    // it is possible that there are too many fronts exist to hold in 'ed's 'frontz' and 'fronttype', so combine them if there are too many

 	 	updateLayerFrozenState(ground->toplayer);     // this must be done before the following call
 	 	updateWaterAfterFront(ground->toplayer);	  // after fronts processed, need to update 'ice' and 'liq' water in a layer due to phase change

 	 	ground->setFstLstFrontLayers();
 	}

//*/

};
 
void Stefan::meltingSnowLayer(double const & tkfront, double & dse, double & sumresabv,
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

 			dse = 0.;
		}
 	}
 	
}
 
// looking for the new front depth ONLY.
// note: NO layer 'frozen' states and 'water phase change' done here, which are done later
void Stefan::processNewFrontSoilLayerDown(const int &freezing, double const & sumrescum, double const & tkfront ,
                        double & dse, double & newfntz, Layer* sl){

	newfntz = 0.;
 	double volwat=0.;  // volumetric ice/liq water (meters) to be thawing/freezing;
 	double dz=0.;      // soil thickness (meters) to be thawing/freezing
 	double dsn=0.;     // the degree seconds needed to fully freeze/thaw one layer of soil

	 dz =sl->dz;  // this is the max. thickness
	 if (freezing==1) {
		 dz *= fmax(0., 1.0-sl->frozenfrac); //assuming frozen/unfrozen soil segments not mixed
		 volwat = fmax(0.0, sl->getVolLiq())*sl->dz;
	 } else {
		 dz *= sl->frozenfrac; //assuming frozen/unfrozen soil segments not mixed
		 volwat = fmax(0.0, sl->getVolIce())*sl->dz;
	 }

	 if (dz<=0.0001*sl->dz) {    // this will avoid 'front' exactly falling on the boundary between layers that causes a lot of mathmatic issues
		 newfntz = sl->z;
		 return;
	 }

	 dsn = getDegSecNeeded(dz, volwat, tkfront, sumrescum);

	 if(dse>=dsn){

		 // whole layer will be frozen or unfrozen, and a new front will add at the bottom
		 newfntz = sl->z+sl->dz;
		 dse -= dsn;

	 } else {

		 double partdz=0.;
		 //partdz=getPartialDepth(volwat, tkfront, sumrescum, dse);  //may not be consistent
		 partdz = dse/dsn*dz;

		 // find the existing front(s) within the layer
		 int fntnum = ground->frontsz.size();
		 vector<int> fntsintype;
		 vector<double> fntsindz;  // front distance from layer top
		 for (int i=0; i<fntnum; i++){
			 if(ground->frontsz[i]>sl->z && ground->frontsz[i]<=sl->z+sl->dz) {
				 fntsintype.push_back(ground->frontstype[i]);
				 fntsindz.push_back(ground->frontsz[i]-sl->z);
			 }
		 }

		 // find new front dz from the layer top
		 double newfntdz = 0.;
		 int fntinnum = fntsintype.size();
		 if (fntinnum<=0) {                     // no front at all, add one
			 newfntdz = partdz;

		 } else {

			 // moving existed same-type front or dissolving existing opposite-type front in the current soil layer
			 double partdleft  = partdz;
			 double newfntdzmax= sl->dz;
			 for (int i=0; i<fntinnum; i++){
				 int fnttype = fntsintype[i];
				 double fntdz = fntsindz[i];

				 if (i<fntinnum-1) newfntdzmax=fmin(newfntdzmax, fntsindz[i+1]);
				 if (fnttype == freezing) {
					 // moving the same-type front
					 newfntdz = fmin(newfntdzmax, fntdz+partdleft);  //moving the same type front down until the layer boundry or the next inside front
					 partdleft -=newfntdz;
				 } else {
					 // for the opposite type front
					 if (partdleft<fntdz) {
						 newfntdz = fntdz+partdleft;      //adding a new front before the current front
						 partdleft = 0.;                  // using up all left 'partd'
					 } else {
						 newfntdz = newfntdzmax;  // sweeping the opposite type front down until the layer boundry or the next inside front
						 partdleft -= fntdz;      // but, only using up 'fntdz' of left 'partd', and the rest will be used to move/sweep the next front
					 }

				 }

				 if (partdleft<=0.) break;

			 }
		 }
		 fntsintype.clear();
		 fntsindz.clear();

		 // new front depth
		 if (newfntdz>=0.9999*sl->dz) {    // this will avoid 'front' exactly falling on the boundary between layers
			 newfntdz=0.9999*sl->dz;
		 }
		 newfntz = sl->z+newfntdz;

		 dse = 0.;

	 }
}

// Put the new front in two 'deque', if moving downwardly
void Stefan::frontsDequeDown(const double &newfntz, const int &newfnttype){

	// new front deeper than column depth, it will sweep all fronts
	if (newfntz>=ground->botlayer->z+ground->botlayer->dz) {
		ground->frontstype.clear();
		ground->frontsz.clear();
		return;
	}
	// if new front at the surface, do nothing
	if (newfntz<=0.) {
		return;
	}

	int numfnt = ground->frontsz.size();

	if (numfnt<=0){
		if (newfntz<ground->lstsoill->z+ground->lstsoill->dz){
			ground->frontsz.push_front(newfntz);
			ground->frontstype.push_front(newfnttype);
		}
	} else {

		// first, sweep all fronts, if any, above the new front, which assummed to penetrate through the soil profile downwardly
		double dzres = 0.;    // the difference of new front and its closest upper existing front
		int lstfrnttype = ground->frontstype[numfnt-1];
		while (ground->frontsz.size()>0 && newfntz>=ground->frontsz[0]) {
				dzres = newfntz - ground->frontsz[0];      // this will update 2 'deque's when do the loop
				ground->frontsz.pop_front();
				ground->frontstype.pop_front();
		}

		// then, only need to deal with the updated top front, which always lower than the new front
		if (ground->frontsz.size()>0 &&                          // there is existing front(s), AND,
			newfntz<ground->lstsoill->z+ground->lstsoill->dz) {  // new front within soil column bottom

			if (newfnttype!=ground->frontstype[0]) {   // different from old front
				ground->frontsz.push_front(newfntz);
				ground->frontstype.push_front(newfnttype);

			} else {   // same front type, then need to move the front down if new one is deeper
				if (ground->frontsz[0]<dzres) ground->frontsz[0] = dzres;

			}

		} else { // new front sweeps every front

			if (newfnttype == lstfrnttype) { // new front will move the last old front, if they're same type
				double fntz= fmin(newfntz, ground->lstsoill->z+0.9999*ground->lstsoill->dz);
				ground->frontsz.push_front(fntz);
				ground->frontstype.push_front(newfnttype);

			}  // otherwise, all fronts are really sweeped out (nothing to do here)
		}

	 }
}

// for bottom-up forcing front moving/adding
// note that: freezing/thawing force is in opposite direction, so forcing is in opposite from 'front' type.
//            front type: freezing - frozen(up)/unfrozen(down); thawing - unfrozen(up)/frozen(down)
void Stefan::processNewFrontSoilLayerUp(const int &freezing, double const & sumrescum, double const & tkfront ,
                        double & dse, double & newfntz, Layer* sl){

	newfntz = MISSING_D;
 	double volwat=0.;  // volumetric ice/liq water (meters) to be thawing/freezing;
 	double dz=0.;      // soil thickness (meters) to be thawing/freezing
 	double dsn=0.;     // the degree seconds needed to fully freeze/thaw one layer of soil

	 dz =sl->dz;  // this is the max. thickness of water to be freezing/thawing
	 if (freezing==1) {
		 dz *= fmax(0., 1.0-sl->frozenfrac); //assuming frozen/unfrozen soil segments not mixed
		 volwat = fmax(0.0, sl->getVolLiq())*sl->dz;
	 } else {
		 dz *= sl->frozenfrac; //assuming frozen/unfrozen soil segments not mixed
		 volwat = fmax(0.0, sl->getVolIce())*sl->dz;
	 }

	 if (dz<=0.0001*sl->dz) {    // this will avoid 'front' exactly falling on the boundary between layers that causes a lot of mathmatic issues
		 newfntz = sl->z+sl->dz;
		 return;
	 }

	 dsn = getDegSecNeeded(dz, volwat, tkfront, sumrescum);

	 if(dse>=dsn){

		 // whole layer will be frozen or unfrozen, and a new front will add at the layer top
		 newfntz = sl->z;
		 dse -= dsn;

	 } else {

		 double partdz=0.;
		 //partdz=getPartialDepth(volwat, tkfront, sumrescum, dse);  //may not be consistent
		 partdz = dse/dsn*dz;

		 // find the existing front(s) within the layer
		 int fntnum = ground->frontsz.size();
		 vector<int> fntsintype;
		 vector<double> fntsindz;  // front distance from layer bottom
		 for (int i=0; i<fntnum; i++){
			 if(ground->frontsz[i]>sl->z && ground->frontsz[i]<=sl->z+sl->dz) {
				 fntsintype.push_back(ground->frontstype[i]);
				 fntsindz.push_back(sl->z+sl->dz-ground->frontsz[i]);
			 }
		 }

		 // find new front dz from the layer bottom
		 double newfntdz = 0.;
		 int fntinnum = fntsintype.size();
		 if (fntinnum<=0) {                     // no front at all, add one
			 newfntdz = partdz;

		 } else {

			 // moving existed same-type front or dissolving existing opposite-type front in the current soil layer
			 double partdleft  = partdz;
			 double newfntdzmax= sl->dz;
			 for (int i=0; i<fntinnum; i++){
				 int fnttype = fntsintype[i];
				 double fntdz = fntsindz[i];

				 if (i<fntinnum-1) newfntdzmax=fmin(newfntdzmax, fntsindz[i+1]);
				 if (fnttype != freezing) {   //note: opposite of front type and 'freezing/thawing' force
					 // moving the same-type front
					 newfntdz = fmin(newfntdzmax, fntdz+partdleft);  //moving the same type front up until the layer boundry or the next inside front
					 partdleft -=newfntdz;
				 } else {
					 // for the opposite type front
					 if (partdleft<fntdz) {
						 newfntdz = fntdz+partdleft;      //adding a new front before the current front
						 partdleft = 0.;                  // using up all left 'partd'
					 } else {
						 newfntdz = newfntdzmax;  // sweeping the opposite type front up until the layer boundry or the next inside front
						 partdleft -= fntdz;      // but, only using up 'fntdz' of left 'partd', and the rest will be used to move/sweep the next front
					 }

				 }

				 if (partdleft<=0.) break;

			 }
		 }
		 fntsintype.clear();
		 fntsindz.clear();

		 // new front depth
		 if (newfntdz>=0.9999*sl->dz) {    // this will avoid 'front' exactly falling on the boundary between layers
			 newfntdz=0.9999*sl->dz;
		 }
		 newfntz = sl->z+sl->dz-newfntdz;  // the distance from ground surface ('newfntdz' is from layer bottom)

		 dse = 0.;

	 }
}

// Put the new front in two 'deque', if moving upwardly
void Stefan::frontsDequeUp(const double &newfntz, const int &newfnttype){

	// if the new front moving up to the ground surface, sweep all fronts
	if (newfntz<=0.0) {
		ground->frontstype.clear();
		ground->frontsz.clear();
		return;
	}
	if (newfntz>=ground->botlayer->z+ground->botlayer->dz) { // if new front lower than column depth, do nothing
		return;
	}

	int numfnt = ground->frontsz.size();

	if (numfnt<=0){
		if (newfntz<ground->lstsoill->z+ground->lstsoill->dz){
			ground->frontsz.push_front(newfntz);
			ground->frontstype.push_front(newfnttype);
		}
	} else {

		// first, sweep all fronts, if any, below the new front, which assummed to penetrate through the soil profile upwardly
		double dzres = 0.;    // the difference of new front and its closest lower existing front
		int fstfrnttype = ground->frontstype[0];
		while (ground->frontsz.size()>0 && newfntz<=ground->frontsz[numfnt-1]) {
				dzres = ground->frontsz[numfnt-1]-newfntz;      // this will update 2 'deque's when do the loop
				ground->frontsz.pop_back();
				ground->frontstype.pop_back();
				numfnt = ground->frontsz.size();
		}

		// then, only need to deal with the updated bottom front, which always higher than the new front
		if (ground->frontsz.size()>0 &&                          // there is existing front(s), AND,
			newfntz>ground->fstsoill->z) {                       // new front within soil column top

			if (newfnttype!=ground->frontstype[numfnt-1]) {   // different from old front
				ground->frontsz.push_back(newfntz);
				ground->frontstype.push_back(newfnttype);

			} else {   // same front type, then need to move the front up if new one is shallower
				if (ground->frontsz[numfnt-1]>dzres) ground->frontsz[numfnt-1] = dzres;

			}

		} else { // new front sweeps every front

			if (newfnttype == fstfrnttype) { // new front will move upwardly the first old front, if they're same type
				double fntz= fmax(newfntz, ground->fstsoill->z+0.0001*ground->lstsoill->dz);
				ground->frontsz.push_back(fntz);
				ground->frontstype.push_back(newfnttype);

			}  // otherwise, all fronts are really sweeped out (nothing to do here)
		}

	 }
}


double Stefan::getDegSecNeeded(const double & dz,
 				const double & volwat,  const double & tk, const double & sumresabv){
 	/*input
 	 * 	   dz: the thickness of  fraction of (or whole)  soil layer: 
 	 *     volwat: volumetric water thickness, either ice or liquid water
 	 *     tk: thermal conductivity of that part of (or whole) layer
 	 *     sumresabv: the sum of resistance for all the layers above
 	 */
 	 double needed=0.;
 	 
 	 double effvolwat = volwat;
 	 double lhfv = 3.34e8;
 	 needed = lhfv * effvolwat * (sumresabv +0.5 * dz/tk);
 	 
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

//determine the layer, where the bottom driving position locates and 'tdrvbot' for driving force
double Stefan::prepareBottomDriving(){

	 botdrvl=NULL;
	 double tdrvbot = MISSING_D;

	 Layer *lstfrontl = ground->lstfntl;
	 if(lstfrontl==NULL){
		 return MISSING_D;
	 }
	 double dzthreshold = 0.05;  // unit: meters. This's the depth below front where soil T is interpolated for 'tdrvbot'
	                             // AND, the layer where this depth locates is regarded as 'botdrvl' layer

	 int numfnt = ground->frontstype.size();
	 double diffdz = lstfrontl->z+lstfrontl->dz-ground->frontsz[numfnt-1];
	 if(diffdz >= dzthreshold){
		 double dz2front  = dzthreshold;
		 Layer* nxtl=lstfrontl->nextl;
		 if(nxtl!=NULL){
			 botdrvl = nxtl;
			 double ntem = nxtl->tem;
			 double dz2laybot = diffdz-dzthreshold+0.5*nxtl->dz;
			 double gradient = (ntem - 0.0)/(dz2front+dz2laybot);
			 double drvtemp =dz2front * gradient + 0.;

			 tdrvbot = drvtemp;
		 }

	 }else{
		 Layer* currl = lstfrontl->nextl;
		 double olddiffdz = diffdz;
		 while(currl!=NULL){

			 diffdz +=currl->dz;
			 if(diffdz>dzthreshold){
				 botdrvl= currl;
				 break;
			 }
			 olddiffdz = diffdz;
			 currl=currl->nextl;
		 }

		 if(botdrvl!=NULL){
			 //double dz2laytop = dzthreshold-olddiffdz;
			 Layer* nxtl=botdrvl->nextl;
			 if(nxtl==NULL){
				 botdrvl=NULL;
			 }else{
				 double ntem = nxtl->tem;
				 double gradient = (ntem - botdrvl->tem)/(0.5*nxtl->dz+0.5*botdrvl->dz);
				 double drvtemp = dzthreshold * gradient + 0.;

				 tdrvbot = drvtemp;
			 }
		 } else {
			 return MISSING_D;
		 }

	 }

	 return tdrvbot;

}

 
// it is possible that there are too many fronts exist (e.g., freezing and thawing alternatively occur from day to day)
// combine them if there are too many (here, not less than 2*MAX_FNT_NUM - so that in 'ed', 'frzfnt' and 'thwfnt' can hold them all)
void Stefan::combineExtraFronts() {

	int frntnum  = ground->frontsz.size();
	double mindz = 1000.;     // (unit: meter) a number bigger enough to do the following comparison

	while (frntnum >MAX_NUM_FNT) {       // because freezing and thawing fronts are alternatively ordered in 'ground->frontsz'

		int removefntid = -1;

		// find the nearest two fronts
		for(int i=0; i<frntnum-1; i++){
			double dz = ground->frontsz[i+1] - ground->frontsz[i];   // Note: the distance is in order in the fronts 'deque'
   			if(dz < mindz){
   				mindz = dz;
   				removefntid = i;
   			}
   	   }

	   // remove these two fronts (NOTE: not one front, otherwise fronts are not alternatively ordered)
   	   if(removefntid >=0){
   		   ground->frontsz.erase(ground->frontsz.begin()+removefntid+1);
   		   ground->frontsz.erase(ground->frontsz.begin()+removefntid);

   		   ground->frontstype.erase(ground->frontstype.begin()+removefntid+1);
   		   ground->frontstype.erase(ground->frontstype.begin()+removefntid);
   	   }

   	   frntnum = ground->frontsz.size();

   	}

};

// update frozen status and the fraction of frozen portion (thickness) for each layer in a column,
// based on two fronts deques: 'ground->frontsz' and 'ground->frontstype'
void Stefan::updateLayerFrozenState(Layer * toplayer){

	int fntnum = ground->frontsz.size();

	Layer *currl = toplayer;
	while (currl!=NULL) {
	 	double fracfrozen = 0.;

		 // find the existing front(s) within the layer, AND, closest front beyond the layer
		 vector<int> fntintype;
		 vector<double> fntindz;       // the distance of the front from the 'currl->z'
		 int fntouttype  = MISSING_I;   // if no front within layer, this is used to determine the 'frozen' status and thus 'frozenfrac'
		 double fntoutdz = MISSING_D;
		 for (int i=0; i<fntnum; i++){
			 double dz=ground->frontsz[i]-currl->z;
			 if (dz>0. && dz<=currl->dz) {
				 fntintype.push_back(ground->frontstype[i]);
				 fntindz.push_back(ground->frontsz[i]-currl->z);

			 } else {
				 if (fabs(dz)<=fabs(fntoutdz)) {
					 fntoutdz   = dz;
					 fntouttype = ground->frontstype[i];
				 }
			 }

		 }

		 //
		 int fntinnum    = fntintype.size();
		 if (fntinnum>0) {      // front(s) within the layer
			currl->frozen = 0;
			double dzabvfnt = 0.;
			for (int i=0; i<fntinnum; i++){
				double fntdz = fntindz[i];
				int fnttype = fntintype[i];

				if (fnttype==1) {                     //freezing front: from this front up to the neibored previous front IS frozen portion
					fracfrozen += (fntdz - dzabvfnt);
				} else if (fnttype==-1 && (i==fntinnum-1)){   // thawing front, AND, it's the last one
 					fracfrozen += currl->dz - fntdz;
				}
				dzabvfnt = fntdz;    //update the upper front 'dz' for following front

			}
 			currl->frozenfrac = fracfrozen/currl->dz;

		 } else {            // no front within the layer
			 //
			 if (fntouttype!=MISSING_I) {     // nearby front exists
				 if (fntoutdz>=currl->dz) {
					 currl->frozen = fntouttype;    // layer's frozen status is SAME as the nearest below front type
				 } else if (fntoutdz<=0.){
					 currl->frozen = -fntouttype;    // layer's frozen status is OPPOSITE as the nearset above front type
				 }

			 } else {                        // no front at all
				 if (currl->tem>0.) currl->frozen = -1;
				 if (currl->tem<=0.) currl->frozen = 1;
			 }

			 //
			 if (currl->frozen==1) currl->frozenfrac = 1.0;
			 if (currl->frozen==-1) currl->frozenfrac = 0.0;
		 }

 		 currl=currl->nextl;
	}

}

// when a front moves through or in a layer
// the corresponding liq and ice content should be changed due to phase change (no total water amount change)
void Stefan::updateWaterAfterFront(Layer* toplayer){
	Layer * currl = toplayer;
    double tice = 0.;
 	double tliq = 0.;

 	while (currl!=NULL) {
 		tice = currl->ice;
 		tliq = currl->liq;
 		currl->ice = (tice +tliq ) * currl->frozenfrac;  // NOTE: 'frozenfrac' must be updated already
 		currl->liq = (tice +tliq ) * (1. - currl->frozenfrac);

 		// there may be a situation that freezing may cause ice 'expansion' over the maxice -
 		double icebylwc = currl->getVolLiq()*DENICE*currl->dz;
 		if (currl->ice>=(currl->maxice-icebylwc)) {
 			currl->ice=fmax(0., currl->maxice-icebylwc);   // what to do about the 'extra' water??? - next step
 		}

 		// phase change energy
 		double dliq = currl->liq - tliq;
 		if (dliq>0.0) {  // thawing, because 'liq' increased
 			currl->pce_t += (dliq*LHFUS);
 		} else if (dliq<0.0){    // freezing, because 'liq' decreased
 			currl->pce_f += (-dliq*LHFUS);
 		}

 		currl = currl->nextl;
 	}

};
