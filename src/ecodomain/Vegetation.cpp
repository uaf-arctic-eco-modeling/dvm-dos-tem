/*
 * Vegetation.cpp
 *
 * Purpose: Defining vegetation structure
 *
 * History:
 *     June 28, 2011, by F.-M. Yuan:
 *          (1) added for constructing vegetation domain (plant community)
 *
 * Important:
 *     (1) Parameters are read from 'CohortLookup.cpp', and set to 'vegdimpar' (struct:: vegpar_dim)
 *     (2) Here, all functions are on ALL pfts for ONE community. In this way, some complicated PFT interaction
 *      and dynamics/structure changing may be put here in the future.
 *
 */

#include "Vegetation.h"

Vegetation::Vegetation(){
	
};

Vegetation::~Vegetation(){
	
};

// set the bgc parameters from inputs stored in 'chtlu' - reuseable
// Note: here will remove those PFT with no greater than zero 'fpc'
//       and initialize the total actual pft number

void Vegetation::initializeParameter(){
	int ipft = 0;
    for (int ip=0; ip<NUM_PFT; ip++) {
    	if (chtlu->vegcov[ipft] > 0.){    //this will remove those PFTs with 0 ground coverage. So be cautious the index consistent with 'state' variables

    		vegdimpar.sla[ipft]      = chtlu->sla[ip];
    		vegdimpar.klai[ipft]     = chtlu->klai[ip];
  
    		vegdimpar.minleaf[ipft] = chtlu->minleaf[ip];
    		vegdimpar.aleaf[ipft]   = chtlu->aleaf[ip];
    		vegdimpar.bleaf[ipft]   = chtlu->bleaf[ip];
    		vegdimpar.cleaf[ipft]   = chtlu->cleaf[ip];

    		vegdimpar.kfoliage[ipft] = chtlu->kfoliage[ip];
    		vegdimpar.cov[ipft]      = chtlu->cov[ip];
    		vegdimpar.m1[ipft] = chtlu->m1[ip];
    		vegdimpar.m2[ipft] = chtlu->m2[ip];
    		vegdimpar.m3[ipft] = chtlu->m3[ip];
    		vegdimpar.m4[ipft] = chtlu->m4[ip];

    	}

    	ipft++;
	}

};

// set the initial states from inputs
// Note: here will remove those PFT with no greater than zero 'fpc'
//       and initialize the total actual pft number
void Vegetation::initializeState(){

	int ipft = 0;
	cd->hasnonvascular = false;

    for (int i=0; i<NUM_PFT; i++) {
    	if (chtlu->vegcov[i] > 0.){
    		cd->m_veg.vegcov[ipft]      = chtlu->vegcov[i];

    		cd->m_veg.ifwoody[ipft]     = chtlu->ifwoody[i];
    		cd->m_veg.ifdeciwoody[ipft] = chtlu->ifdeciwoody[i];
    		cd->m_veg.ifperenial[ipft]  = chtlu->ifperenial[i];
    		cd->m_veg.nonvascular[ipft] = chtlu->nonvascular[i];
    		if (cd->m_veg.nonvascular[ipft] > 0) cd->hasnonvascular = true;
    		cd->m_veg.lai[ipft]         = chtlu->lai[i];

    		for (int il=0; il<MAX_ROT_LAY; il++) {
    			cd->m_veg.frootfrac[il][ipft] = chtlu->frootfrac[il][i]/100.;   //chtlu - in %
    		}

    		ipft++;

    	}

    }

    cd->numpft = ipft;

    updateFpc(cd->m_veg.lai);

    updateFrootfrac();

};

//set the initial states from restart inputs:
// Note: NOT same as 'chtlu', 'resin' must have the actual PFT number stored
// CAUTIOUS: Must be sure the index consistence between 'resin' and 'vegdimpar' (which from 'chtlu' after removal)
void Vegetation::initializeState5restart(RestartData *resin){

    cd->numpft = resin->numpft;

    for (int ip=0; ip<cd->numpft; ip++) {

    	cd->m_veg.vegcov[ip]      = resin->vegcov[ip];
    	cd->m_veg.ifwoody[ip]     = resin->ifwoody[ip];
    	cd->m_veg.ifdeciwoody[ip] = resin->ifdeciwoody[ip];
    	cd->m_veg.ifperenial[ip]  = resin->ifperenial[ip];
    	cd->m_veg.nonvascular[ip] = resin->nonvascular[ip];
    	cd->m_veg.lai[ip]         = resin->lai[ip];

    	for (int il=0; il<MAX_ROT_LAY; il++) {
          cd->m_veg.frootfrac[il][ip] = resin->rootfrac[il][ip];
    	}

    	for(int i=0; i<10; i++){
    		double unleafmxa = resin->unnormleafmxA[i][ip];    //note: older value is, lower in the deque
    		if(unleafmxa!=MISSING_D){
    			cd->prvunnormleafmxque[ip].push_back(unleafmxa);
    		}
    	}

    	for(int i=0; i<10; i++){
    		double growingttimea = resin->growingttimeA[i][ip];    //note: older value is, lower in the deque
    		if(growingttimea!=MISSING_D){
    			cd->prvgrowingttimeque[ip].push_back(growingttimea);
    		}
    	}

    	for(int i=0; i<10; i++){
    		double topta = resin->toptA[i][ip];    //note: older value is, lower in the deque
    		if(topta!=MISSING_D){
    			cd->toptque[ip].push_back(topta);
    		}

    	}

    }

    updateFpc(cd->m_veg.lai);

    updateFrootfrac();

};

// must be called after 'foliage' and 'leaf' updated
void Vegetation::updateLai(const int &currmind){
	for(int ip=0; ip<cd->numpft; ip++)	{
		if(!updateLAI5vegc){
			cd->m_veg.lai[ip] = chtlu->envlai[currmind][ip];     //So, this will give a portal for input LAI

		}else {
			cd->m_veg.lai[ip] = vegdimpar.sla[ip] * bd[ip]->m_vegs.c[I_leaf];
		}
	}
};

// sum of all PFTs' fpc must be not greater than 1.0
void Vegetation::updateFpc(double lai[NUM_PFT]){
	double fpcmx = 0.;
	double fpcsum = 0.;
	double fpc[NUM_PFT];
	for(int ip=0; ip<cd->numpft; ip++)	{
		double ilai = lai[ip];
		fpc[ip] = 1.0 - exp(-vegdimpar.klai[ip] * ilai);
		if (fpc[ip]>fpcmx) {
			fpcmx = fpc[ip];
		}
		fpcsum +=fpc[ip];
		cd->m_veg.fpc[ip] = fpc[ip];

	}
	if (fpcsum > 1.0) {
		for(int ip=0; ip<cd->numpft; ip++)	{
			cd->m_veg.fpc[ip] /= fpcsum;
		}
		fpcsum = 1.0;
	}
	cd->m_veg.fpcsum = fpcsum;

};

// vegetation coverage update (note - this is not same as FPC)
// and Here it's simply assumed as the max. foliage coverage projected on ground throughout the whole plant lift-time
// shall be more working on this in future
void Vegetation::updateVegcov(double lai[NUM_PFT]){
	double foliagecov = 0.;
	cd->hasnonvascular = false;
	for(int ip=0; ip<cd->numpft; ip++)	{
		double ilai = lai[ip];
		foliagecov = 1.0 - exp(-vegdimpar.klai[ip] * ilai);
		if (cd->m_veg.vegcov[ip]<foliagecov) {
			cd->m_veg.vegcov[ip]=foliagecov;
		}

		if (cd->m_veg.vegcov[ip]>1.e-5) {
			cd->m_veg.ifwoody[ip]     = chtlu->ifwoody[ip];
			cd->m_veg.ifdeciwoody[ip] = chtlu->ifdeciwoody[ip];
			cd->m_veg.ifperenial[ip]  = chtlu->ifperenial[ip];
			cd->m_veg.nonvascular[ip] = chtlu->nonvascular[ip];

			if (cd->m_veg.nonvascular[ip] > 0) cd->hasnonvascular = true;
		}
	}

};

//leaf phenology - moved from 'Vegetation_Bgc.cpp' for easy modification, if needed in the future
void Vegetation::phenology(const int &currmind){

	for(int ip=0; ip<cd->numpft; ip++)	{

    	cd->m_veg.prvunnormleafmx[ip] = 0.;   // previous 10 years' average as below
    	deque <double> prvdeque = cd->prvunnormleafmxque[ip];
    	int dequeno = prvdeque.size();
    	for (int i=0; i<dequeno; i++) {
    		cd->m_veg.prvunnormleafmx[ip] +=prvdeque[i]/dequeno;
    	}

		if (cd->m_veg.fpc[ip] > 0.) {
			// 1) current EET and previous max. EET controlled
			double tempunnormleaf;

			double eet = ed[ip]->m_l2a.eet;
			tempunnormleaf = getUnnormleaf(ip, ed[ip]->prveetmx, eet, cd->m_veg.prvunnormleafmx[ip]);
			cd->m_veg.fleaf[ip] = getFleaf(ip, tempunnormleaf);

			// get the yearly phenological variables of the year
			if (currmind == 0) {
				unnormleafmx[ip] = tempunnormleaf;
				growingttime[ip] = 0.;
				topt[ip] = ed[ip]->m_atms.ta;
			} else {
				if (unnormleafmx[ip] < tempunnormleaf) {
					unnormleafmx[ip] = tempunnormleaf;
					topt[ip] = ed[ip]->m_atms.ta;
				}

				if (growingttime[ip]<ed[ip]->m_soid.tsdegday) {  // here, we take the top root zone degree-days since growing started
					growingttime[ip]=ed[ip]->m_soid.tsdegday;
				}
			}

			// save the yearly max. 'unnormaleaf', 'growing thermal time', and 'topt' into the deque
			if (currmind == 11) {
				double tmpmx = unnormleafmx[ip];
				cd->prvunnormleafmxque[ip].push_front(tmpmx);
				if (cd->prvunnormleafmxque[ip].size()>10) {
					cd->prvunnormleafmxque[ip].pop_back();
				}

				double tmpttimex = growingttime[ip];
				cd->prvgrowingttimeque[ip].push_front(tmpttimex);
				if (cd->prvgrowingttimeque[ip].size()>10) {
					cd->prvgrowingttimeque[ip].pop_back();
				}

				double tmptopt = topt[ip];
				cd->toptque[ip].push_front(tmptopt);
				if (cd->toptque[ip].size()>10) {
					cd->toptque[ip].pop_back();
				}

			}

			// 2) plant size (biomass C) or age controlled foliage fraction rative to the max. leaf C
			if (currmind ==0) {
				cd->m_veg.ffoliage[ip] = getFfoliage(ip, cd->m_veg.ifwoody[ip], cd->m_veg.ifperenial[ip], bd[ip]->m_vegs.call);
			}

		} else {
			cd->m_veg.fleaf[ip] = 0.;
			cd->m_veg.ffoliage[ip] = 0.;
		}
	}
};

// functions for eet adjusted foliage growth index
// 'prvunleaf' is the unnormalized leaf from last time period
// 'prveetmx' is monthly eetmx of previous simulation period (year)

double Vegetation::getUnnormleaf(const int& ipft, double &prveetmx, const double & eet, const double & prvunleaf){
  	double normeet;
  	double unnormleaf;

  	if (prveetmx <= 0.0) {
  		prveetmx = 1.0;
  	}

  	normeet = eet/prveetmx;
  	if(normeet>1) normeet =1;

  	unnormleaf = (vegdimpar.aleaf[ipft] * normeet)
  			    +(vegdimpar.bleaf[ipft] * prvunleaf)
                + vegdimpar.cleaf[ipft];

  	if (unnormleaf < (0.5 * vegdimpar.minleaf[ipft])) {
    	unnormleaf = 0.5 * vegdimpar.minleaf[ipft];
  	}

  	return unnormleaf;
};

//fleaf is normalized EET and previous EET determined phenology index 0~1
//i.e., f(phenology) in gpp calculation
double Vegetation::getFleaf(const int &ipft, const double & unnormleaf){
  	double fleaf;

  	if (cd->m_veg.prvunnormleafmx[ipft] <= 0.0) {
  	 	fleaf = 0.0;
  	} else {
  	 	fleaf= unnormleaf/cd->m_veg.prvunnormleafmx[ipft];
   	}

  	if (fleaf < vegdimpar.minleaf[ipft] ){
    	fleaf = vegdimpar.minleaf[ipft];
  	} else  if (fleaf > 1.0 ) {
   		fleaf = 1.0;
   	}

  	return fleaf;
};

// function for biomass C adjusted foliage growth index
double Vegetation::getFfoliage(const int &ipft, const bool & ifwoody, const bool &ifperenial, const double &vegc){

	double ffoliage =0;

  	if(!ifwoody){
  		if (!ifperenial) {
  			ffoliage = 1.0;    //annual: yearly max. not controlled by current plant C biomass (because it dies every year)
  		} else {
  			ffoliage = 1.0/(1.0 + vegdimpar.kfoliage[ipft] * exp(vegdimpar.cov[ipft]* vegc));
  		}

 	} else {

 		//from Zhuang et al., 2003
 		double m1 = vegdimpar.m1[ipft];
 		double m2 = vegdimpar.m2[ipft];
 		double m3 = vegdimpar.m3[ipft];
 		double m4 = vegdimpar.m4[ipft];

 		double fcv = m3*vegc /(1+m4*vegc);
 		ffoliage =  1./(1+m1*exp(m2*sqrt(fcv)));
	}

    //it is assumed that foliage will not go down during a growth cycle
  	if(ffoliage>cd->m_veg.prvfoliagemx[ipft]){
  		cd->m_veg.prvfoliagemx[ipft] = ffoliage;
  	}else{
 		ffoliage = cd->m_veg.prvfoliagemx[ipft];
  	}

  	return ffoliage;
};

// the following can be developed further for dynamical fine root distribution
// currently, it's only do some checking
void Vegetation::updateFrootfrac(){

	for (int ip=0; ip<cd->numpft; ip++){
		double totrootfrac = 0.;
		for (int il=0; il<MAX_ROT_LAY; il++){
			if (cd->m_veg.frootfrac[il][ip]>0.) {
				totrootfrac+=cd->m_veg.frootfrac[il][ip];
			}
		}

		//
		if (totrootfrac>0.) {
			for (int il=0; il<MAX_ROT_LAY; il++){
				cd->m_veg.frootfrac[il][ip] /= totrootfrac;
			}

		} else {
			for (int il=1; il<MAX_ROT_LAY; il++){
				cd->m_veg.frootfrac[il][ip] = 0.;
			}

		}

	}

};


void Vegetation::setCohortLookup(CohortLookup* chtlup){
  	 chtlu = chtlup;
};

void Vegetation::setCohortData(CohortData* cdp){
  	 cd = cdp;
};

void Vegetation::setEnvData(const int &ip, EnvData* edp){
  	 ed[ip] = edp;
};

void Vegetation::setBgcData(const int &ip, BgcData* bdp){
	 bd[ip] = bdp;
};
