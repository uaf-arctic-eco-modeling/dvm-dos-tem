#include "Snow_Env.h"

Snow_Env::Snow_Env(){
	
};

Snow_Env::~Snow_Env(){
	
};

void Snow_Env::updateDailyM(const double & tdrv){

    //update tsurface with nfactor
	double tsurface;
	tsurface = tdrv *ed->d_soid.nfactor;

    // dsmass is the total snowfall during one timestep:
    double dsmass = ed->d_v2g.sthfl + ed->d_v2g.sdrip   //these 2 items has already been adjusted by FPC
    		        + (1.- cd->m_vegd.fpcsum)* ed->d_a2l.snfl;
     //Note unit converstion: 1 mm H2O = 1 kgH2O/m2

	bool slchg1 = false;
	if (!ground->toplayer->isSnow && ground->toplayer->tem>0.01) {   //melting all snowfalling ('dsmass')
    	ed->d_snw2soi.melt = dsmass;
    	ground->snow.extramass = 0.;
    } else {    // otherwise, construct a new snow layer, if any
    	slchg1 = ground->constructSnowLayers(dsmass, tsurface);  //add a new snow layer as the new toplayer
    	if(slchg1)	{
    		ground->resortGroundLayers();
       		initializeNewSnowState();   //for new snow layer when it is a front layer
    	}
    }

	// snow-melting/sublimating
	bool slchg2 = false;
    if(ground->toplayer->isSnow){

	 	// sublimating of existed surface snow layers accompanying snow surface energy budget process (Yuan: need further thinking here ???)
	 	updateDailySurfFlux(ground->toplayer, tsurface);

	 	// melting below snow layers, if any
 		ed->d_snw2soi.melt = meltSnowLayersAfterT(ground->toplayer);

    }
	dsmass=ed->d_snw2a.sublim+ed->d_snw2soi.melt;   // here 'dsmass' is for snow-melting and sublimating
    //Note unit converstion: 1 mm H2O = 1 kgH2O/m2

	slchg2 = ground->constructSnowLayers(-dsmass, tsurface);  // removal of melted snow layers
	if(slchg2)	{
		ground->resortGroundLayers();
	}

	// snow layer adjusting, if needed
   	bool slchg3 = ground->combineSnowLayers();
   	if(slchg3){
		ground->resortGroundLayers();
	}

   	bool slchg4 = ground->divideSnowLayers();
    if(slchg4){
		ground->resortGroundLayers();
    }

    // after snow layer adding/removal/adjusting, needs updating thickness
	ground->updateSnowLayerPropertiesDaily();   // each layer
	ground->updateSnowHorizon();                // all snow horizon
	ground->checkWaterValidity();

	updateSnowEd(ground->toplayer);

};

void Snow_Env::updateDailySurfFlux( Layer* toplayer, const double & tdrv){
	
	if (toplayer->isSnow) {
		double albnir = getAlbedoNir(toplayer->tem);
		double albvis = getAlbedoVis(toplayer->tem);
	
		double insw =  ed->d_v2g.swthfl * cd->m_vegd.fpcsum
			     + ed->d_a2l.nirr *(1.- cd->m_vegd.fpcsum);

		ed->d_snw2a.swrefl = insw *0.5 * albnir + insw *0.5 * albvis;
	 
		double rn = insw- ed->d_snw2a.swrefl;
		double sublim = getSublimation(rn, ed->d_snws.swesum, tdrv); //mm SWE/day, or kgSW/day

		Layer * currl=toplayer;
		double actsub = 0.;
		while (currl!=NULL){
			if (currl->isSnow && sublim>0.) {
				double layicermv = fmin(sublim, currl->ice);
				actsub += layicermv;
				sublim -= layicermv;

				currl->ice -= layicermv;
			} else {
				break;
			}
			currl = currl->nextl;
		}

		ed->d_snw2a.sublim = actsub;

	}

/*  // the following will cause confusion OR duplicated snowmelting process
    //see Zhuang et al., 2004 D4 not sure whether equation D8 is right, when compared with the one from
    //Brubaker et al., 1996
   // double melt = 2.99*rn/0.2388 *86400/10000.+2.0*tdrv; //mm/day
    double melt =0.26*rn +2.0*tdrv;//mm/day
    
    if(melt>0 && melt<=sublim){
    	 ed->d_snw2soi.melt = melt;
    	 ed->d_snw2a.sublim = sublim-melt;
    	 
    }else if(melt<=0){
         ed->d_snw2soi.melt = 0.;
         ed->d_snw2a.sublim = sublim;
    }else if (melt>sublim){
         ed->d_snw2a.sublim = 0.;
     	 ed->d_snw2soi.melt = sublim;
    }
*/
    
};

// get albedo of visible radition on snow
double Snow_Env::getAlbedoVis(const double & tem){
    double vis;

    if(tem<-10){
    	vis =0.9;
    }else{
    	vis = snowenvpar.albmax - (snowenvpar.albmax -snowenvpar.albmin) * (tem+10)/10;
    	vis = fmin(snowenvpar.albmax, vis);
    	vis = fmax(snowenvpar.albmin, vis);
    }

    return vis;
};

// get albedo of invisible radition
double Snow_Env::getAlbedoNir(const double & tem){
    double nir;
    nir = getAlbedoVis(tem);

    return nir;
};

// modified - called after 'Stefan.cpp:: processFrontSnowLayers()'
// Here, the 'liq' in snowlayer will be collected as melting water and removed from the layer

double  Snow_Env::meltSnowLayersAfterT(Layer* toplayer){

	double melt=0;   // unit: mm H2O
	Layer* currl ;

	currl= toplayer;
	while(currl!=NULL){
		if(currl->isSnow){

			if(currl->frozen==-1){
				melt += currl->liq;
				currl->liq = 0.;
			}else {
				if(currl->frozen==0){
					melt += currl->liq;   // Note: 'liq' here is the conversion of 'ice' due to partial snow-melting
					currl->liq = 0.;      // restore 'liq' to zero
					if (currl->tem <0.) {
						currl->frozen=1;
					} else {
						currl->frozen=-1;
					}
				}
			}

			currl=currl->nextl;

		}else{
			break;
		}

	}

	return melt;    //Note: 1kgH2O/m2 = 1 mm H2O
};

// assign double-linked snow horizon data to 'ed'
void Snow_Env::updateSnowEd(Layer *toplayer){
	ed->d_snws.swesum = 0.;
	Layer* currl=toplayer;
	int snowind = 0;
	while(currl!=NULL){
	  	if(currl->isSnow){
	  		ed->d_snws.snwice[snowind] = currl->ice;
	  		ed->d_snws.snwliq[snowind] = currl->liq;

	  		ed->d_snws.swe[snowind] = currl->ice;
	  		ed->d_snws.swesum += currl->ice;
			currl=currl->nextl;
	  	}else{
	  		if (snowind>=MAX_SNW_LAY) break;
	  		ed->d_snws.swe[snowind] = MISSING_D;        // in this way, 'swe' will be refreshed for all
	  		ed->d_snws.snwice[snowind] = MISSING_D;        // in this way, 'swe' will be refreshed for all
	  		ed->d_snws.snwliq[snowind] = MISSING_D;        // in this way, 'swe' will be refreshed for all
	  	}
  		snowind++;
	}

	ed->d_snws.extraswe= ground->snow.extramass;
	ed->d_snws.swesum += ground->snow.extramass;

	if (ed->d_snws.swesum>0.){
		// assuming no evap and reflection from soil surface, if snow layer still exists or is constructed
		ed->d_soi2a.evap   = 0.;  // Yuan: these might not be needed? but no harmless here to do so
		ed->d_soi2a.swrefl = 0.;
		ed->d_soi2l.qover  = 0.;
	}

};

void Snow_Env::initializeParameter(){
	snowenvpar.albmax = chtlu->snwalbmax;
	snowenvpar.albmin = chtlu->snwalbmin;
};

void Snow_Env::initializeNewSnowState(){

	Layer *toplayer = ground->toplayer;
	while(toplayer!=NULL){
		if(toplayer->isSnow){
			// other 'Layer' properties already updated in 'Ground.cpp', when constructing this layer

			toplayer->frozen = 1;
			toplayer->maxliq = 0.;
			toplayer->maxice = toplayer->dz*ground->snowdimpar.denmax;

			toplayer->liq = 0.;
			toplayer->ice = toplayer->dz*toplayer->rho;
			break;
		}else{
		  break;
		}
	}

};


void Snow_Env::initializeState5restart(RestartData* resin){
	//set the parameters
	double TSsnow[MAX_SNW_LAY];
	double ICEsnow[MAX_SNW_LAY];

	for (int i=0; i<MAX_SNW_LAY; i++){
		TSsnow[i] =resin->TSsnow[i];
		ICEsnow[i]=resin->ICEsnow[i];
	}
	
	Layer* currl = ground->toplayer;
	
	int snind =-1;
	ed->d_snws.swesum=0;
	while(currl!=NULL){
		if(currl->isSnow){
		  snind ++;
		  currl->tem = TSsnow[snind];
		  currl->ice = ICEsnow[snind];
		  currl->liq = 0.;
		  currl->frozen = 1;
		  currl->maxliq = 0.;
		  currl->maxice = currl->dz*ground->snowdimpar.denmax;
	 		  
		}else{
		  break;
		}
		
		currl = currl->nextl; 
	}

	//
	ground->checkWaterValidity();

};

double Snow_Env::getSublimation(double const & rn, double const & swe, double const & ta){ 
	// rn unit  W/m2,  radiation
	// swe  snow water equivlent mm
	// output sublimation mm/day
	
	double sub = 0.;
	
	double sabsorb =0.6;     //  radiation asorbtivity of snow, Zhuang 0.6 ?
	double lamdaw = 2.501e6; // latent heat of vaporization J/kg
    double lf = 3.337e5 ;    // latent heat of fusion J/kg

    double rabs = rn * sabsorb; //W/m2
	
    if( swe>0. && ta<=-1){
    	double psub= rabs*86400/(lamdaw + lf);
    	if(psub>swe){
    		sub = swe;
    	}else{
    		sub = psub;
    	}

	} else if(swe>0. && ta>=-1){
		double pmelt= rabs*86400/(lf);
		if(pmelt>swe){
			sub = swe;
		}else{
			sub = pmelt;
		}

	} else {
		sub = 0.;
	}
 
	return sub;
};

void Snow_Env::checkSnowLayersT(Layer* toplayer){
 	Layer* currl = toplayer;
 	SnowLayer* sl;

 	while(currl!=NULL){
    	if (currl->isSnow){
      		sl = dynamic_cast<SnowLayer*>(currl);
       		if(currl->tem>0){
           		currl->tem =-0.01;
         	}
    	}

    	currl=currl->nextl;
 	}
};

void Snow_Env::setGround(Ground* grndp){
	ground = grndp;
};

void Snow_Env::setCohortLookup(CohortLookup* chtlup){
	chtlu = chtlup;
};

void Snow_Env::setCohortData(CohortData* cdp){
	cd = cdp;
};

void Snow_Env::setEnvData(EnvData* edp){
	ed = edp;
};


