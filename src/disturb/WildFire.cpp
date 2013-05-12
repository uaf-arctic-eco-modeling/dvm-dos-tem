/*
 * WildFire.cpp
 *
 * This is for wildfire occurrence and C/N pool dynamics due to fire
 *   (1) Fire occurrence either by input or FRI derived
 *   (2) Fire severity either by ALFRESCO input, or determined by 'size','season' and 'landscape position'
 *
 *   (3) C/N pools updated here through operation on 'bd' - NOTE this 'bd' is for all PFTs and soil.
 *        this is to say, individual PFT's C/N pools updating need to do elsewhere
 *   (4) ROOTFRAC is updated here through operation on 'ed' - also for ALL PFTS.
 *
 *   (5) soil layer structure is NOT changed here, but will re-do in Ground::adjustSoilAfterBurn()
 *
 *   (6) NOTE: assuming ONE root pool, and its index is 'NUM_PFT_PART' (i.e. the last).
 *
 */

#include "WildFire.h"

WildFire::WildFire(){

};

WildFire::~WildFire(){
	
};

void WildFire::initializeParameter(){
	

	for (int i=0; i<NUM_FSEVR; i++){
		for (int ip=0; ip<NUM_PFT; ip++) {

			firpar.fvcomb[i][ip] = chtlu->fvcombust[i][ip];
			firpar.fvdead[i][ip] = chtlu->fvslash[i][ip];
		}

		firpar.foslburn[i] = chtlu->foslburn[i];
	}

	firpar.vsmburn     = chtlu->vsmburn; // a threshold value of VWC for burn organic layers

    firpar.r_retain_c  = chtlu->r_retain_c;
    firpar.r_retain_n  = chtlu->r_retain_n;

};

void WildFire::initializeState(){
	fd->fire_a2soi.orgn = 0.0;

};

void WildFire::initializeState5restart(RestartData *resin){
	
	fd->fire_a2soi.orgn=resin->firea2sorgn;
	
};

//Yuan: modifying the following method, return the first fire year, if any
void WildFire::prepareDrivingData(){
    //initialize with -1
	for(int in =0; in<MAX_FIR_OCRNUM; in++){
		fyear[in]        = -1;
		fseason[in]      = -1;
		fmonth[in]       = -1;
		fseverity[in]    = -1;
	    fsize[in]        = -1;
	}

	//fire season's month index order (0~11):
	int morder[12] = {1,2,3, 4,5,6, 7,8,9, 10,11,0};  //Yuan: season: 1, 2(early fire), 3(late fire), and 4 with 3 months in the order
	vector<int> firemonths;

    int calyr =0;
   	firstfireyr = END_SC_YR; // the latest possible year to have a fire

   	//from fire.nc
	for(int in =0; in<MAX_FIR_OCRNUM; in++){
    	calyr = cd->fireyear[in];
    	if(calyr != MISSING_I){   			          //Yuan: fire year may be BC, But '-9999' reserved for none

    		if (firstfireyr>=calyr) firstfireyr=calyr;

    		fyear[in]     = calyr;
    		fseason[in]   = cd->fireseason[in];
			fsize[in]     = cd->firesize[in];
    		fseverity[in] = cd->fireseverity[in];

    		int fsindx=fseason[in]-1;   //note: season category index starting from 1
    		for (int i=0; i<3; i++) firemonths.push_back(morder[fsindx*3+i]);
    		random_shuffle(firemonths.begin(),firemonths.end());  // randomize the vector of months
    		fmonth[in]=firemonths[1];                             // pick-up the middle month in the vector
    		firemonths.clear();

    	}
   	}

};

//Yuan: the fire occurrence month (and data) is input (cohort-level info),or FRI derived (grid-level info)
//Yuan: almost rewriting the code, called in the begining of a year
int WildFire::getOccur(const int &yrind, const bool & friderived){

	int error = 0;
	oneyear    = MISSING_I;
	onemonth   = MISSING_I;
	onesize    = MISSING_I;
  	oneseason  = MISSING_I;
	oneseverity= MISSING_I;

	if(friderived){
		if(yrind%cd->gd->fri==0 && yrind>0){
			//fire size, dervied from input probability of grid fire sizes
		//*
		 	double pdf = 0.;
    		for (int i=0; i<NUM_FSIZE; i++) {
    		if (cd->gd->pfsize[i]>=pdf) {
    				pdf=cd->gd->pfsize[i];
    				onesize = i;                     //find the size index with the most frequent fire size (need further modification using a randomness generator)
    			}
    		}
   		//*/

			//fire season, dervied from input probability of grid fire seasons
			//fire season's month index order (0~11):
			vector<int> firemonths;
   		//*
   		 	double pf = 0.;
    		for (int i=0; i<NUM_FSEASON; i++) {
    			if (cd->gd->pfseason[i]>=pf) {
    				pf=cd->gd->pfseason[i];
    				oneseason = i+1;                     //find the season index with the most frequent fire occurrence (need further modification using a randomness generator)
    			}
    		}
    	//*/

    		// get the fire month based on 'season'
			//Yuan: season: 1(pre-fireseason), 2(early fire), 3(late fire), and 4 (post-fireseason), with 3 months in the order
			int morder[12] = {1,2,3, 4,5,6, 7,8,9, 10,11,0};
    		int fsindx = oneseason-1;         // 'season' category starting from 1
    		for (int i=0; i<3; i++) firemonths.push_back(morder[fsindx*3+i]);
    		random_shuffle(firemonths.begin(),firemonths.end());  //randomly pick-up a month for fire occurence
    		int firetime= firemonths[1];
    		firemonths.clear();
    		onemonth = firetime;

    		// fire year
    		oneyear = yrind;

    		// fire severity based on 'season' and 'size' (and landscape position - drainage type)
    		deriveFireSeverity();
		}

	}else {
		for (int i=0; i<MAX_FIR_OCRNUM; i++){
			if(fyear[i]==yrind){
				oneyear   = fyear[i];
				onemonth  = fmonth[i];
				onesize   = fsize[i];
			  	oneseason = fseason[i];

			  	// directly use input 'fire severity'
			  	if(fd->useseverity){
			  		oneseverity = fseverity[i];

			  		if(cd->gd->drgtype==1){  //if poorly-drained condition
			  			oneseverity = 1;
			  		}

			  	// 'fire severity' derived from landscape drainage condition, fire size (area), and fire season
			  	} else {
			  		deriveFireSeverity();
			  	}

			}
		}
	}

	return error;

};
    
//Burning vegetation and soil organic C
void WildFire::burn(){

	fd->burn();

///////////////////////////////////////////////////////////////////////////////////////////////////
// for soil part and root burning

 	//NOTE: here we operates on soil portion of 'bdall', later will copy that to other PFTs if any
 	double burndepth = getBurnOrgSoilthick();

 	double totbotdepth =0.;
 	double burnedsolc=0.;
 	double burnedsoln=0.;

 	double r_burn2bg_cn[NUM_PFT]; //ratio of dead veg. after burning
 	for (int ip=0; ip<NUM_PFT; ip++) {
 		r_burn2bg_cn[ip] = 0.; //used for vegetation below-ground (root) loss, and calculated below
 	}

 	for (int il =0; il <cd->m_soil.numsl; il++){
	  	if(cd->m_soil.type[il]<=2){ //dead moss is 0, shlw peat is 1 and deep org is 2

	  		// dead moss layer (burn all dead moss biomass)
	  		if (bdall->m_sois.dmossc>0.) {
	  			burnedsolc +=bdall->m_sois.dmossc;
	  			burnedsoln +=bdall->m_sois.dmossn;

	  			bdall->m_sois.dmossc = 0.;
	  			bdall->m_sois.dmossn = 0.;

	  		}

	  		totbotdepth += cd->m_soil.dz[il];

	  		double ilsolc =  bdall->m_sois.rawc[il]+bdall->m_sois.soma[il]
	  		       +bdall->m_sois.sompr[il]+bdall->m_sois.somcr[il];
	  		double ilsoln =  bdall->m_sois.orgn[il]+bdall->m_sois.avln[il];
	  		
	  		if(totbotdepth<=burndepth){ //remove all the orgc/n in this layer

	  			burnedsolc += ilsolc;
	  			burnedsoln += ilsoln;

	  	  		bdall->m_sois.rawc[il] =0.;
	  	  		bdall->m_sois.soma[il] =0.;
	  	  		bdall->m_sois.sompr[il]=0.;
	  	  		bdall->m_sois.somcr[il]=0.;
	  	  		
	  	  		bdall->m_sois.orgn[il]=0.;
	  	  		bdall->m_sois.avln[il]=0.;

	  	  		for (int ip=0; ip<NUM_PFT; ip++) {
	  		    	if (cd->m_veg.vegcov[ip]>0.){

	  		    		r_burn2bg_cn[ip] += cd->m_soil.frootfrac[il][ip];
	  		    		cd->m_soil.frootfrac[il][ip]=0.;

	  		    	}
	  	  		}
	  		}else{
	  	  		double partleft = totbotdepth -burndepth;
	  	  		//calculate the left c/n
	  	  		if(partleft<cd->m_soil.dz[il]){

	  	  			burnedsolc += (1.0-partleft/cd->m_soil.dz[il]) * ilsolc;
	  	  			burnedsoln += (1.0-partleft/cd->m_soil.dz[il]) * ilsoln;

	  	  			bdall->m_sois.rawc[il] *= partleft/cd->m_soil.dz[il];
	  	  			bdall->m_sois.soma[il] *= partleft/cd->m_soil.dz[il];
	  	  			bdall->m_sois.sompr[il] *= partleft/cd->m_soil.dz[il];
	  	  			bdall->m_sois.somcr[il] *= partleft/cd->m_soil.dz[il];

	  	  			bdall->m_sois.orgn[il] *= partleft/cd->m_soil.dz[il];
	  	  			bdall->m_sois.avln[il] *= partleft/cd->m_soil.dz[il];

		  	  		for (int ip=0; ip<NUM_PFT; ip++) {
		  		    	if (cd->m_veg.vegcov[ip]>0.){
		  		    		r_burn2bg_cn[ip] += (1-partleft/cd->m_soil.dz[il])* cd->m_soil.frootfrac[il][ip];
		  		    		cd->m_soil.frootfrac[il][ip] *=partleft/cd->m_soil.dz[il];
		  		    	}
		  	  		}

	  	  		}else{
	  	  			//nothing can happen here
	  	  			break;
	  	  		}	  	 	
	  		}
	   
	   	} else {   //non-organic soil layers or moss layers
	  		if(totbotdepth<=burndepth){ //may not be needed, but just in case
	  			fd->fire_soid.burnthick = totbotdepth;
	  		}
	  		break;
	  	
	  	}	
		
	}

    // needs to re-do the soil rootfrac for each pft which was modified above (in burn soil layer)
 	for (int ip=0; ip<NUM_PFT; ip++){
 		double rootfracsum = 0.;
 		for (int il =0; il <cd->m_soil.numsl; il++){
 			rootfracsum += cd->m_soil.frootfrac[il][ip];
 		}
 		for (int il =0; il <cd->m_soil.numsl; il++){
 			cd->m_soil.frootfrac[il][ip] /=rootfracsum;
 		}
 	}

     // all woody debris will burn out
	double wdebrisc = bdall->m_sois.wdebrisc; //
	double wdebrisn = bdall->m_sois.wdebrisn; //
	bdall->m_sois.wdebrisc = 0.;
	bdall->m_sois.wdebrisn = 0.;

	// summarize
	double vola_solc = (burnedsolc+wdebrisc)* (1.0- firpar.r_retain_c);
	double vola_soln = (burnedsoln+wdebrisn) * (1.0- firpar.r_retain_n);

	double reta_solc = burnedsolc * firpar.r_retain_c;   //together with veg.-burned N return, This will be put into soil later
	double reta_soln = burnedsoln * firpar.r_retain_n;   //together with veg.-burned N return, This will be put into soil later
	
//////////////////////VEG burning and mortality ///////////////////////////////////////////////////////////////

	double comb_vegc = 0.;  //summed for all PFTs
	double comb_vegn = 0.;
	double comb_deadc = 0.;
	double comb_deadn = 0.;

	double dead_bg_vegc = 0.;
	double dead_bg_vegn = 0.;

	for (int ip=0; ip<NUM_PFT; ip++) {
    	if (cd->m_veg.vegcov[ip]>0.){

    		// vegetation burning/dead/living fraction for above-ground
    		getBurnAbgVegetation(ip);

    		//root death ratio: must be called after both above-ground and below-ground burning
    		double r_dead2bg_cn = 1.0-r_burn2bg_cn[ip]- r_live_cn;   //r_live_cn is same for both above-ground and below-ground

    		// dead veg c/n
    		comb_deadc += bd[ip]->m_vegs.deadc*cd->m_veg.vegcov[ip];         //assuming all previous deadc burned
    		comb_deadn += bd[ip]->m_vegs.deadn*cd->m_veg.vegcov[ip];         //assuming all previous deadn burned
    		bd[ip]->m_vegs.deadc = 0.;
    		bd[ip]->m_vegs.deadn = 0.;

    		// above-ground veg. burning/death during fire
    		comb_vegc += bd[ip]->m_vegs.c[I_leaf]*r_burn2ag_cn*cd->m_veg.vegcov[ip];     // when summing, needs adjusting by 'vegcov'
    		bd[ip]->m_vegs.deadc = bd[ip]->m_vegs.c[I_leaf]*r_dead2ag_cn;   // we define deadc/n as the not-falling veg (or binding with living veg) during fire,
		                                                        // which then is the source of ground debris (this is for woody plants only, others could be set deadc/n to zero)
    		bd[ip]->m_vegs.c[I_leaf] *= (1.0-r_burn2ag_cn-r_dead2ag_cn);

    		comb_vegc += bd[ip]->m_vegs.c[I_stem]*r_burn2ag_cn*cd->m_veg.vegcov[ip];
    		bd[ip]->m_vegs.deadc += bd[ip]->m_vegs.c[I_stem]*r_dead2ag_cn;
    		bd[ip]->m_vegs.c[I_stem] *= (1.0-r_burn2ag_cn-r_dead2ag_cn);

    		comb_vegn += bd[ip]->m_vegs.strn[I_leaf]*r_burn2ag_cn*cd->m_veg.vegcov[ip];
    		bd[ip]->m_vegs.deadn += bd[ip]->m_vegs.strn[I_leaf]*r_dead2ag_cn;
    		bd[ip]->m_vegs.strn[I_leaf] *= (1.0-r_burn2ag_cn-r_dead2ag_cn);

    		comb_vegn += bd[ip]->m_vegs.strn[I_stem]*r_burn2ag_cn;
    		bd[ip]->m_vegs.deadn += bd[ip]->m_vegs.strn[I_stem]*r_dead2ag_cn;
    		bd[ip]->m_vegs.strn[I_stem] *= (1.0-r_burn2ag_cn-r_dead2ag_cn);

    		// below-ground veg. (root) burning/death during fire
    		comb_vegc += bd[ip]->m_vegs.c[I_root]*r_burn2bg_cn[ip]*cd->m_veg.vegcov[ip];
    		double deadc_tmp = bd[ip]->m_vegs.c[I_root]*r_dead2bg_cn*cd->m_veg.vegcov[ip];
    		for (int il =0; il <cd->m_soil.numsl; il++){
	    	// for the dead below-ground C/N caused by fire, they are put into original layer
    			if (cd->m_soil.frootfrac[il][ip]>0.)
	    		bdall->m_sois.somcr[il] += deadc_tmp*cd->m_soil.frootfrac[il][ip];   //'rootfrac' must be updated above
    		}
    		dead_bg_vegc +=deadc_tmp;

    		bd[ip]->m_vegs.c[I_root] *= (1.0-r_burn2bg_cn[ip]-r_dead2bg_cn);

    		comb_vegn += bd[ip]->m_vegs.strn[I_root]*r_burn2bg_cn[ip]*cd->m_veg.vegcov[ip];
    		double deadn_tmp = bd[ip]->m_vegs.strn[I_root]*r_dead2bg_cn*cd->m_veg.vegcov[ip];   // this is needed below
    		for (int il =0; il <cd->m_soil.numsl; il++){
    			// for the dead below-ground C/N caused by fire, they are put into original layer
    			if (cd->m_soil.frootfrac[il][ip]>0.)
	    		bdall->m_sois.somcr[il] += deadn_tmp*cd->m_soil.frootfrac[il][ip];   //'rootfrac' must be updated above
    		}
    		dead_bg_vegn +=deadn_tmp;
    		bd[ip]->m_vegs.strn[I_root] *= (1.0-r_burn2bg_cn[ip]-r_dead2bg_cn);

    		// one more veg N pool (labile N)
    		comb_vegn += bd[ip]->m_vegs.labn*(1.-r_live_cn)*cd->m_veg.vegcov[ip];  //assuming all labn emitted, leaving none into deadn
    		bd[ip]->m_vegs.labn *= r_live_cn;

    		// finally, we have:
    		bd[ip]->m_vegs.call = bd[ip]->m_vegs.c[I_leaf]+bd[ip]->m_vegs.c[I_stem]+bd[ip]->m_vegs.c[I_root];
    		bd[ip]->m_vegs.nall = bd[ip]->m_vegs.strn[I_leaf]+bd[ip]->m_vegs.strn[I_stem]+bd[ip]->m_vegs.strn[I_root]+bd[ip]->m_vegs.labn;

    	}// end of 'vegcov[ip]>0.'
	}

	double reta_vegc = (comb_vegc+comb_deadc) * firpar.r_retain_c;
	double reta_vegn = (comb_vegn+comb_deadn) * firpar.r_retain_n;

/////////////////////////////////////////////////////////////////////////////////

    // save the fire emission and return data into 'fd'
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
	//- this will let the system -N balanced in a long-term, if NO open-N cycle included
	fd->fire_a2soi.orgn = (fd->fire_soi2a.orgn+ fd->fire_v2a.orgn)/cd->gd->fri;
    	
   //put the retained C/N into the first unburned soil layer's chemically-resistant SOMC pool
   // Note - this 'retained C' could be used as char-coal, if need to do so. Then define the 'r_retain_c' in the model shall be workable
    for (int il =0; il <cd->m_soil.numsl; il++){
	    double tsomc = bdall->m_sois.rawc[il]+bdall->m_sois.soma[il]+bdall->m_sois.sompr[il]+bdall->m_sois.somcr[il];
  		if(tsomc > 0. || il==cd->m_soil.numsl-1){
  		// this may possibly put retac/n in the first mineral soil
  			bdall->m_sois.somcr[il] += reta_vegc + reta_solc;
  			bdall->m_sois.orgn[il]  += reta_vegn + reta_soln;

  			break;
  		}
	}

    //Need to copy 'bdall->m_soils' to other PFTs, because above soil portion of 'bd' is done on 'bdall'
    for (int ip=1; ip<NUM_PFT; ip++) {
    	if (cd->m_veg.vegcov[ip]>0.){
    		bd[ip]->m_sois = bdall->m_sois;
    	}
    }

	
};

//derive fire severity based on landscape drainage condition, fire season and fire size
void WildFire::deriveFireSeverity(){
	oneseverity = 0;
	if(cd->gd->drgtype==0){
		if(oneseason==1 ||oneseason==2 || oneseason==4){          //Yuan:  (fireseason: 1, 2(early), 3(late), 4)
			if(onesize==1){                     //Yuan: (firesize: 0, 1, 2, 3, 4)
		        oneseverity = 1;
			}else if(onesize==2){
				oneseverity = 2;
			}else if(onesize>2){
				oneseverity = 3;
			}

		}else if (oneseason==3){ //late season fire
			oneseverity = 4;
		}

	}else if(cd->gd->drgtype==1){
		oneseverity = 1;
	}
};

// above ground burning ONLY, based on fire severity indirectly or directly
void WildFire::getBurnAbgVegetation(const int &ip) {

	//Yuan: the severity categories are from ALFRESCO:
	// 0 - no burning; 1 - low; 2 - moderate; 3 - high + low surface; 4 - high + high surface
	// so, 1, 2, and 3/4 correspond to original TEM's low, moderate, and high.
	if (oneseverity==0) {
			r_burn2ag_cn = firpar.fvcomb[0][ip];
			r_dead2ag_cn = firpar.fvdead[0][ip];
	}else if (oneseverity==1) {
			r_burn2ag_cn = firpar.fvcomb[1][ip];
			r_dead2ag_cn = firpar.fvdead[1][ip];
	}else if (oneseverity==2) {
			r_burn2ag_cn = firpar.fvcomb[2][ip];
			r_dead2ag_cn = firpar.fvdead[2][ip];
	}else if (oneseverity==3) {
			r_burn2ag_cn = firpar.fvcomb[3][ip];
			r_dead2ag_cn = firpar.fvdead[3][ip];
	}else if (oneseverity==4) {
			r_burn2ag_cn = firpar.fvcomb[4][ip];
			r_dead2ag_cn = firpar.fvdead[4][ip];
	}

	r_live_cn = 1.-r_burn2ag_cn-r_dead2ag_cn;


};

// fire severity based organic soil burn thickness, and adjustment based on soil water condition
double WildFire::getBurnOrgSoilthick(){

	double bthick=0;
  	//////////////////////////////////
  	///Rule 1: only organic layer can be burned (Site Related)
  	///Rule 2: should be less than the burn thickness max (Cohort Related)
  	///Rule 3: should be less than the wet organic soil layer depth

    double totorgthick = cd->m_soil.mossthick + cd->m_soil.shlwthick +cd->m_soil.deepthick ;

     //Yuan: the severity categories are from ALFRESCO:
 		// 0 - no burning; 1 - low; 2 - moderate; 3 - high + low surface; 4 - high + high surface
 		// so, 1, 2, and 3/4 correspond to TEM's low, moderate, and high. But needs further field data supports
    if (oneseverity<=0) {        // no burning
    	 bthick = 0.;

    } else if (oneseverity==1) {   //low
    	 bthick = firpar.foslburn[1] * totorgthick;

     }else if (oneseverity==2) {   //moderate
    	 bthick = firpar.foslburn[2] * totorgthick;

    } else if (oneseverity==3) {
    	 bthick = firpar.foslburn[3] * totorgthick;

    } else if (oneseverity==4) {    //high
    	 bthick = firpar.foslburn[4] * totorgthick;

    }

    //
 	//get the total orgnic depth with less than VSMburn soil water
   	double totorg = 0.;
   	for (int i =0; i<cd->m_soil.numsl; i++){
   		if(cd->m_soil.type[i]<=2
   		  && edall->m_soid.vwc[i]<=(firpar.vsmburn*cd->m_soil.por[i])){ //Yuan: VSM constrained burn thickness
   	  		totorg += cd->m_soil.dz[i];
   		}else{
   	  		break;
   		}

   	}
  	if (bthick>totorg) bthick=totorg;

    //
    if(bthick <cd->m_soil.mossthick){
      	bthick =cd->m_soil.mossthick;   //burn all moss layers
    }

  	fd->fire_soid.burnthick = bthick;

    return bthick;
};

void WildFire::setCohortLookup(CohortLookup* chtlup){
  	 chtlu = chtlup;
};

void WildFire::setCohortData(CohortData* cdp){
	cd = cdp;
};

void WildFire::setAllEnvBgcData(EnvData* edp, BgcData *bdp){
	edall = edp;
	bdall = bdp;
};

void WildFire::setBgcData(BgcData* bdp, const int &ip){
	bd[ip] = bdp;
};

void WildFire::setFirData(FirData* fdp){
  	fd =fdp;
}
  
