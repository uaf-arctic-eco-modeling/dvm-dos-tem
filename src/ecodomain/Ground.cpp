/*
 * Ground.cpp
 *
 * Ground is used to manipulate the structure of snow and soil layers
 *   (1) 'Ground' comprises of a few HORIZONS as following
 *        Snow, Rock, Moss, Organic, Mineral Soil
 *   (2) EACH HORIZON may have a few LAYERS (max. no are pre-defined in /inc/layerconst.h),
 *   which are defined in /layer/..
 * 
 */
 
#include "Ground.h"

Ground::Ground(){
   fstsoill = NULL;
   lstsoill = NULL;
   
   fstmossl = NULL;
   lstmossl = NULL;
   fstshlwl = NULL;
   lstshlwl = NULL;
   fstdeepl = NULL;
   lstdeepl = NULL;
   fstminel  = NULL;
   lstminel  = NULL;

   fstfntl  = NULL;
   lstfntl  = NULL;

   rocklayercreated=false;
   
};

Ground::~Ground(){
   cleanAllLayers();
}

//
void Ground::initParameter(){

	//parameters for snow dimension
	snowdimpar.denmax = chtlu->snwdenmax;   //kg/m3
	snowdimpar.newden = chtlu->snwdennew;

	//parameters for soil dimension
	soildimpar.maxmossthick = chtlu->maxmossthick;
	soildimpar.minmossthick = chtlu->maxmossthick*0.010;
	soildimpar.coefmossa  = chtlu->coefmossa;
	soildimpar.coefmossb  = chtlu->coefmossb;

	soildimpar.coefshlwa  = chtlu->coefshlwa;
	soildimpar.coefshlwb  = chtlu->coefshlwb;

	soildimpar.coefdeepa  = chtlu->coefdeepa;
	soildimpar.coefdeepb  = chtlu->coefdeepb;

	soildimpar.coefminea  = chtlu->coefminea;
	soildimpar.coefmineb  = chtlu->coefmineb;

};

//initial dimension from inputs
void Ground::initDimension(){

	snow.thick = chtlu->initsnwthick;
	snow.dense = chtlu->initsnwdense;

	moss.thick = chtlu->initmossthick;
	moss.type  = chtlu->initmosstype;

	organic.shlwthick = chtlu->initfibthick;
	organic.deepthick = chtlu->inithumthick;

	mineral.num = 0;
	mineral.thick = 0;
	for (int il=0; il<MAX_MIN_LAY; il++){
		if (chtlu->minetexture[il] > 0 && MINETHICK[il]>0.) {
			mineral.num+=1;
			mineral.thick += MINETHICK[il];
			mineral.dz[il] = MINETHICK[il];
			mineral.texture[il] = chtlu->minetexture[il];
		} else {
			break;
		}
	}

	soilparent.thick = 50.;  //meter

}

void Ground::initLayerStructure(snwstate_dim *snowdim, soistate_dim *soildim){

	//layers are constructed from bottom
	if(rocklayercreated){
		cleanSnowSoilLayers();
	}else{
		initRockLayers();               //rock in the bottom first and no-need to do again
	}

	initSnowSoilLayers();

	resortGroundLayers();

	// put the layer structure to 'cd'
	retrieveSnowDimension(snowdim);
	retrieveSoilDimension(soildim);

};

void Ground::initRockLayers(){
	soilparent.updateThicknesses(soilparent.thick); //thickness in m
	for(int il =soilparent.num-1; il>=0; il--){
		ParentLayer* rl = new ParentLayer(soilparent.dz[il]);
		insertFront(rl);

	}

	rocklayercreated=true;

};

void Ground::initSnowSoilLayers(){

	// mineral thickness must be input before calling this

	for(int il =mineral.num-1; il>=0; il--){
		MineralLayer* ml = new MineralLayer(mineral.dz[il],mineral.texture[il], &soillu);
		insertFront(ml);
	}

  //need to do shlw organic horizon division before organic deep horizon,
  //since the layers of deep are determined by the thickness of last shlw layer
   organic.initShlwThicknesses(organic.shlwthick); //fibthick in m, which needs input
   organic.initDeepThicknesses(organic.deepthick); //humthick in m, which needs input

   // but for insertation of layers into the double-linked matrix, do the deep organic first
   for(int il =organic.deepnum-1; il>=0; il--){
	   OrganicLayer* pl = new OrganicLayer(organic.deepdz[il], 2);  //2 means deep organic
	   insertFront(pl);
   }
   for(int il =organic.shlwnum-1; il>=0; il--){
	   OrganicLayer* pl = new OrganicLayer(organic.shlwdz[il], 1);   //1 means shallow organic
	   insertFront(pl);
   }

   // if nonvascular PFT exists
   if (moss.thick>0.) {
	   double initmldz[] = {0., 0.};
	   initmldz[0] = min(0.01, moss.thick);    //moss thick in m, which needs input, assuming 0.01 m is living, and the rest is dead
	   initmldz[1] = max(0., moss.thick - initmldz[0]);
	   int soiltype[] = {-1, -1};
	   if (initmldz[0] > 0.) soiltype[0] = 0;
	   if (initmldz[1] > 0.) soiltype[1] = 0;
	   moss.setThicknesses(soiltype, initmldz, 2);

	   for(int il = moss.num-1; il>=0; il--){
		   MossLayer* ml = new MossLayer(moss.dz[il], moss.type);//moss type (1- sphagnum, 2- feathermoss), which needs input
		   insertFront(ml);
	   }
   }

  // only ONE snow layer input assummed, if any
   if(snow.thick>0){
		SnowLayer* sl = new SnowLayer();
		sl->dz = snow.thick;
		insertFront(sl);
   }

};

void Ground::initLayerStructure5restart(snwstate_dim *snowdim, soistate_dim *soildim, RestartData * resin){

	//
	soilparent.num = 0;
	soilparent.thick = 0.;
	for (int i=0; i<MAX_ROC_LAY; i++) {
		soilparent.dz[i] = resin->DZrock[i];
		soilparent.type[i] = MISSING_I;    // not used now
		soilparent.num += 1;
		soilparent.thick += soilparent.dz[i];
	}
	rocklayercreated = true;
	for(int il =soilparent.num-1; il>=0; il--){
		ParentLayer* rl = new ParentLayer(soilparent.dz[il]);
		insertFront(rl);
	}

	//
	int soiltype[MAX_SOI_LAY];
	int soilage[MAX_SOI_LAY];
	double dzsoil[MAX_SOI_LAY];
	int soiltexture[MAX_SOI_LAY];
	for (int i=0; i<MAX_SOI_LAY; i++){
		soiltype[i]    = resin->TYPEsoil[i];
		soilage[i]     = resin->AGEsoil[i];
		dzsoil[i]      = resin->DZsoil[i];
		soiltexture[i] = resin->TEXTUREsoil[i];
	}

	mineral.set5Soilprofile(soiltype, dzsoil, soiltexture, MAX_SOI_LAY);
	for(int il =mineral.num-1; il>=0; il--){
		MineralLayer* ml = new MineralLayer(mineral.dz[il], mineral.texture[il], &soillu);
		ml->age = soilage[il];
		insertFront(ml);
	}

	organic.setDeepThicknesses(soiltype, dzsoil, MAX_SOI_LAY);
	for(int il = organic.deepnum-1; il>=0; il--){
		OrganicLayer* pl = new OrganicLayer(organic.deepdz[il], 2);  //2 means deep organic
		pl->age = soilage[il];
		insertFront(pl);
	}

	organic.setShlwThicknesses(soiltype, dzsoil, MAX_SOI_LAY);
	for(int il =organic.shlwnum-1; il>=0; il--){
		OrganicLayer* pl = new OrganicLayer(organic.shlwdz[il], 1);//1 means shallow organic
		pl->age = soilage[il];
		insertFront(pl);
	}

  	moss.setThicknesses(soiltype, dzsoil, MAX_SOI_LAY);
  	for(int il = moss.num-1; il>=0; il--){
  		MossLayer* ml = new MossLayer(moss.dz[il], moss.type);
		ml->age = soilage[il];
  		insertFront(ml);
  	}

	//snow
	snow.coverage  = 0.;
	snow.extramass = 0.;
	snow.numl  = 0;
	snow.thick = 0.;
  	for(int il =MAX_SNW_LAY-1; il>=0; il--){
		if(resin->DZsnow[il]>0){
			SnowLayer* snwl = new SnowLayer();
			snwl->dz = resin->DZsnow[il];
			snwl->age= resin->AGEsnow[il];
			snwl->rho= resin->RHOsnow[il];
			insertFront(snwl);

			snow.coverage = 1.;
			snow.dz[il] = resin->DZsnow[il];
			snow.numl ++;
			snow.thick += resin->DZsnow[il];
		} else {
			snow.dz[il] = MISSING_D;
		}

	}

	int frontFT[MAX_NUM_FNT];
	double frontZ[MAX_NUM_FNT];
	for (int i=0; i<MAX_NUM_FNT; i++){
		frontZ[i]=resin->frontZ[i];
		frontFT[i]=resin->frontFT[i];
	}
   	for(int ifnt = 0; ifnt<MAX_NUM_FNT; ifnt++){
   	    if(frontZ[ifnt]>0.){
   	    	frontsz.push_front(frontZ[ifnt]);
   	    	frontstype.push_front(frontFT[ifnt]);
   	    }
   	}

	//
	resortGroundLayers();

	// put the layer structure to 'cd'
	retrieveSnowDimension(snowdim);
	retrieveSoilDimension(soildim);

};

// called at the time of restructuring or initializing soil layers
void Ground::resortGroundLayers(){

	setFstLstSoilLayer();       // This must be called at first

	updateLayerIndex();
	updateSoilLayerZ();
	updateSnowLayerZ();

	setFstLstMineLayers();
	setFstLstMossLayers();
	setFstLstShlwLayers();
	setFstLstDeepLayers();

	setFstLstFrontLayers();

};

void Ground::setFstLstSoilLayer(){
	fstsoill = NULL;
	lstsoill = NULL;
	Layer* currl = toplayer;
	while(currl!=NULL){
	  if(currl->isSoil){
		  fstsoill =currl;
		  break;
	  }
	  currl = currl->nextl;
	}

	currl = botlayer;
	while(currl!=NULL){
	  if(currl->isSoil){
		  lstsoill =currl;
		  break;
	  }
	  currl = currl->prevl;
	}

};

// only perform this at initialization of cohort
// the mineral layer will never be removed/added
void Ground::setFstLstMineLayers(){

	fstminel = NULL;
	fstminel = NULL;

	Layer* currl = toplayer;
  	while(currl!=NULL){
    	if(currl->isSoil && currl->isMineral){
    	   	fstminel = currl;
    	   	break;
    	}
  		currl = currl->nextl;
  	}

  	currl =botlayer;
  	while(currl!=NULL){
    	if(currl->isSoil && currl->isMineral){
    	   	lstminel = currl;
    	   	break;
    	}
  		currl=currl->prevl;
  	}

};

void Ground::setFstLstMossLayers(){
	fstmossl =NULL;
	lstmossl =NULL;

	Layer* currl = fstsoill;
	while(currl!=NULL){
		if(currl->isMoss){

			// first moss layer
			if (currl->prevl==NULL || !currl->prevl->isMoss) fstmossl = currl;

			// last moss layer
			if (currl->nextl==NULL || !currl->nextl->isMoss) {
				lstmossl = currl;
				break;
			}

		} else {
			break;    //So, 'moss' layer always stay on the top soil
		}

		currl = currl->nextl;
	}

};

void Ground::setFstLstShlwLayers(){
	fstshlwl =NULL;
	lstshlwl =NULL;

	Layer* currl = fstsoill;
	while(currl!=NULL){
		if(currl->isFibric){

			// first fibric layer
			if (currl->prevl==NULL || !currl->prevl->isFibric) fstshlwl = currl;

			// last fibric layer
			if (currl->nextl==NULL || !currl->nextl->isFibric) {
				lstshlwl = currl;
				organic.lstshlwdz = currl->dz;
				break;
			}

		} else {
			if (currl->isMineral) break;    //So, No burried organic horizon exists in the model
		}

		currl = currl->nextl;
	}

}

void Ground::setFstLstDeepLayers(){
	fstdeepl =NULL;
	lstdeepl =NULL;

	Layer* currl = fstsoill;

	while(currl!=NULL){
		if(currl->isHumic){

			// first humic layer
			if (currl->prevl==NULL || !currl->prevl->isHumic) fstdeepl = currl;

			// last humic layer
			if (currl->nextl==NULL || !currl->nextl->isHumic) {
				lstdeepl = currl;
				break;
			}

		} else {
			if (currl->isMineral) break;    //So, No burried organic horizon exists in the model
		}

		currl = currl->nextl;
	}

};

void Ground::setFstLstFrontLayers(){
	// determine the first and last soil layer with thawing/freezing fronts
  	 fstfntl=NULL;
  	 lstfntl=NULL;

  	 Layer* currl=fstsoill;

  	 while(currl!=NULL){
   	 	if(currl->frozen==0 && currl->isSoil){
   	 		fstfntl=currl;
   	 		break;
   	 	}
  	   	currl=currl->nextl;
  	 }

  	 if(fstfntl!=NULL){
  	 	currl=botlayer;
  	 	while(currl!=NULL){
  	  		if(currl->isSoil && currl->frozen==0){
  	   	 		lstfntl=currl;
  	   	 		break;
  	  		}
  	  		currl=currl->prevl;
  	 	}
  	 }

  	 //
  	 checkFrontsValidity();
};

void Ground::updateLayerIndex(){
	Layer* currl = toplayer;
	int ind =0;
	int sind=0;

	while (currl!=NULL){
		ind++;
		currl->indl =ind;

		if(currl->isSoil){
			sind++;

		}

		currl->solind = sind;

		currl =currl->nextl;
	}
};

// update the z, which is the distance between soil surface and top of a soil layer
// note that the dz for each soil layer already known.
void Ground::updateSoilLayerZ(){

	Layer* currl = fstsoill;     // 'fstsoill' must be first set up or updated
	while(currl!=NULL){
		if (currl==fstsoill) {
			currl->z = 0.0;
		} else {
			currl->z = currl->prevl->z + currl->prevl->dz;
		}

		currl = currl->nextl;
	}

};

void Ground::updateSoilHorizons(){

	moss.num = 0;
	moss.thick = 0.;
	moss.type  = MISSING_I;
	for (int i=0; i<MAX_MOS_LAY; i++) {
		moss.dz[i] = MISSING_D;
	}

	organic.shlwnum = 0;
	organic.shlwthick = 0.;
	for (int i=0; i<MAX_SLW_LAY; i++) {
		organic.shlwdz[i] = MISSING_D;
	}

	organic.deepnum = 0;
	organic.deepthick = 0.;
	for (int i=0; i<MAX_DEP_LAY; i++) {
		organic.deepdz[i] = MISSING_D;
	}

	mineral.num = 0;
	mineral.thick = 0.;
	for (int i=0; i<MAX_MIN_LAY; i++) {
		mineral.dz[i] = MISSING_D;
		mineral.texture[i] = MISSING_I;
	}

	///
	Layer* currl = toplayer;
	int ind = -1;
	while(currl!=NULL){

		if(currl->isMoss){
			ind +=1;

			moss.num +=1;
			moss.thick +=currl->dz;
			moss.dz[ind] = currl->dz;
			moss.type = dynamic_cast<MossLayer*>(currl)->mosstype;

			if (currl->nextl==NULL || (!currl->nextl->isMoss)) ind = -1;

		} else if(currl->isFibric){
			ind +=1;

			organic.shlwnum +=1;
			organic.shlwthick +=currl->dz;
			organic.shlwdz[ind] = currl->dz;

			if (currl->nextl==NULL || (!currl->nextl->isFibric)) ind = -1;

		} else if(currl->isHumic){
			ind +=1;

			organic.deepnum +=1;
			organic.deepthick +=currl->dz;
			organic.deepdz[ind] = currl->dz;

			if (currl->nextl==NULL || (!currl->nextl->isHumic)) ind = -1;

		}else if(currl->isMineral){
			ind +=1;

			mineral.num +=1;
			mineral.thick +=currl->dz;
			mineral.dz[ind] = currl->dz;
			mineral.texture[ind] = currl->stkey;

			if (currl->nextl==NULL || (!currl->nextl->isMineral)) ind = -1;

		} else if (currl->isRock){
			break;
		}

		currl = currl->nextl;
	}

};

void Ground::cleanSnowSoilLayers(){
	Layer* currl = toplayer;
	Layer* templ;

	while(currl!=NULL){
	  	templ = currl->nextl;
	  	if (!currl->isRock) {
	  		removeLayer(currl);
	  	} else {
	  		break;
	  	}
	  	currl = templ ;

	}

}

void Ground::cleanAllLayers(){
	Layer* currl = toplayer;
	Layer* templ;

	while(currl!=NULL){
	  	templ = currl->nextl;

	  	removeLayer(currl);

	  	currl = templ ;

	}

}

///////////////////////////////////////////////////////////////////////
//update the snowlayer z, which is the distance between soil surface and top of a snow layer
void Ground::updateSnowLayerZ(){
		snow.reset();
		Layer* curr = fstsoill;
		int snowind = 0;
		double oldz = 0.;
		while(curr!=NULL){
		  if(curr->isSnow){
			  curr->z = oldz + curr->dz;
			  oldz = curr->z;

			  snow.numl++;
			  snow.dz[snowind] = curr->dz;
			  snow.thick += curr->dz;
			  snowind ++;
		  }

		  curr = curr->prevl;   //Note: 'snow', the index is ordered upward
		}

};


// Snow Layers construction (+ 'extramass') or ablation (-'extramass')

bool Ground::constructSnowLayers(const double & dsmass, const double & tdrv){
	 bool layerchanged=false;
	 snow.extramass += dsmass;   //Note: 'dsmass' + for snow-adding, - for snow-melting/sublimating when calling this function

	 if(snow.extramass>0){ // accumlate
		 double density = snowdimpar.newden;
	 	 double thick = snow.extramass/density;
		 if(toplayer->isSnow){

			 SnowLayer * snwl = new SnowLayer();
			 snwl->age = 0.;
			 snwl->rho = snowdimpar.newden;
			 snwl->dz = thick;

			 snwl->ice = snow.extramass;
			 snow.extramass = 0.;
			 snwl->frozen =1;
		 	 snwl->tem = tdrv;

			 insertFront(snwl);

		 	 return  true;
		 }else{ // snow layer does not exist
		 	 double tsno =toplayer->tem;
		 	 if(tsno<=0){
		 	   SnowLayer * snwl = new SnowLayer();

			   snwl->rho    = snowdimpar.newden;

			   snwl->dz  = thick;
			   snwl->ice = snow.extramass;
			   snow.extramass = 0.;
			   snwl->frozen =1;
		 	   snwl->tem = tdrv;

		 	   insertFront(snwl);
	           return true;
		 	 }

		 }

	 } else if (snow.extramass<0.){ // ablate
		double ablat = -snow.extramass;
		snow.extramass = 0.;

		//remove whole snow layer, if ablation meets
		if(toplayer->isSnow){
			while(ablat>= toplayer->ice){
		 	  	ablat -= toplayer->ice;
		 	  	removeFront();                      //NOTE: here after calling removeFront(), the 'toplayer' will be updated!
		 	  	layerchanged =true;

		 	  	if(toplayer->isSoil) break;

			}
		 }

		// partially remove snow layer, if any, after above whole layer removal process
		if(toplayer->isSnow){
		 	toplayer->dz *= ((toplayer->ice -ablat)/(toplayer->ice));
		    toplayer->ice -= ablat;
		}
	 }

	 return layerchanged;

};

bool Ground::combineSnowLayers(){
	bool layerchanged =false;
	Layer* currl;
	Layer* tempnext;

	STARTCOMBINE:
		currl= toplayer;

		while(currl!=NULL && currl->nextl!=NULL){
			// for case of first layer
			tempnext = currl->nextl;
			if(currl==toplayer){
				if(currl->isSnow){
					if(currl->dz < snow.mindz[currl->indl]){
						if(currl->nextl->isSnow){
							currl->nextl->liq += currl->liq;
							currl->nextl->ice += currl->ice;
							currl->nextl->dz  += currl->dz;
							currl->nextl->rho = currl->nextl->ice/currl->nextl->dz;
							currl->nextl->age = currl->nextl->age/2. + currl->age/2.;

						}else{ // set extramass
							snow.extramass += currl->ice;
						}

						//remove current layer
						removeLayer(currl);

						updateLayerIndex();

						layerchanged =true;

						goto STARTCOMBINE;
					}
				}

			}else{ // for other layers
				if(currl->isSnow){
					if(currl->dz < snow.mindz[currl->indl]){
						if(currl->nextl->isSnow){
							//find the thinest layer
							if(currl->nextl->dz<currl->prevl->dz){
								currl->nextl->liq += currl->liq;
								currl->nextl->ice += currl->ice;
								currl->nextl->dz +=currl->dz;
								currl->nextl->rho = currl->nextl->ice/currl->nextl->dz;
							}else{
								currl->prevl->liq += currl->liq;
								currl->prevl->ice += currl->ice;
								currl->prevl->dz  +=currl->dz;
								currl->prevl->rho = currl->prevl->ice/currl->prevl->dz;
							}

						}else{ // combine to upper snow layer
							currl->prevl->liq += currl->liq;
							currl->prevl->ice += currl->ice;
							currl->prevl->dz  +=currl->dz;
							currl->prevl->rho = currl->prevl->ice/currl->prevl->dz;
						}

						//remove current layer
						removeLayer(currl);
						updateLayerIndex();
						layerchanged = true;

						goto STARTCOMBINE;
					}
				}

			}

		currl= tempnext;

		if(currl->isSoil)break;
    }

	return layerchanged;
};

bool Ground::divideSnowLayers(){
	bool layerchanged =false;
	Layer* currl;
	STARTOFDIVIDE:
	currl= toplayer;

	while(currl!=NULL){
		if(currl->isSoil)break;
		if(currl->dz>snow.maxdz[currl->indl]){
			if(currl->nextl->isSnow){//assume that the nextl meets the dz requirement
				currl->dz /=2;
				currl->liq /=2;
				currl->ice /=2;
				currl->nextl->liq += currl->liq;
	  			currl->nextl->ice += currl->ice;
	  			currl->nextl->dz  += currl->dz;
	  			currl->nextl->rho  = currl->nextl->ice/currl->nextl->dz;

			}else{//create new layer
				if(currl->indl+1 <MAX_SNW_LAY-1){
					if(currl->dz/2>snow.mindz[currl->indl+1]){
						currl->dz  /=2;
			    		currl->liq /=2;
			    		currl->ice /=2;
			    		SnowLayer* sl = new SnowLayer();

			    		sl->clone(dynamic_cast<SnowLayer*>(currl));
			    		sl->tem = currl->tem;
			    		insertAfter(sl, currl);

						updateLayerIndex();
			    		layerchanged =true;
			    		goto STARTOFDIVIDE;
					}else if(currl->dz- snow.maxdz[currl->indl]>= snow.mindz[currl->indl+1]){
						double tempdz = currl->dz;
						double tempice = currl->ice;
						double templiq = currl->liq;

						currl->dz = snow.maxdz[currl->indl];
			    		currl->liq *= currl->dz/tempdz ;
			    		currl->ice *= currl->dz/tempdz ;
			    		SnowLayer* sl = new SnowLayer();

			    		sl->tem = currl->tem;

			    		sl->clone(dynamic_cast<SnowLayer*>(currl));
			    		sl->dz  = tempdz - currl->dz;
			    		sl->liq = templiq -currl->liq;
			    		sl->ice = tempice -currl->ice;
			    		insertAfter(sl, currl);

			    		updateLayerIndex();
			    		layerchanged =true;
						goto STARTOFDIVIDE;
					}
				}else{
			  		break;
				}

			}

		}

		currl= currl->nextl;
    }

	return layerchanged;
};

void Ground::updateSnowLayerProperties(){
   	Layer* currl=toplayer;

   	while(currl!= NULL){
   		if(currl->isSnow){

   	   		currl->advanceOneDay();

   	   		dynamic_cast<SnowLayer*>(currl)->updateDensity(&snowdimpar);   // this will compact snow layer basd on snowlayer age
       		dynamic_cast<SnowLayer*>(currl)->updateThick();

   		} else {
   			break;
   		}

   		currl=currl->nextl;
   	}
};

// Basically, here will not do thickness change, which will carry out in 'updateOslThickness5Carbon',
// therefore, any new layer creation, will have to originate from neibouring layer, otherwise mathematic error will occur
// execept for create new moss/fibrous organic layer from none.
void  Ground::redivideSoilLayers(){

	redivideMossLayers(moss.type);
    redivideShlwLayers();
    redivideDeepLayers();

};

//
void  Ground::redivideMossLayers(const int &mosstype){

	//before adjusting moss layer, needs checking if Moss layer exists
	setFstLstMossLayers();

	// if no moss layer existed, but moss.thick has beem prescribed or dynamically known
	// create a new moss layer of pre-known thickness above the first soil layer for containing the C in
	if(fstmossl==NULL && moss.thick > 0.) {

		moss.type = mosstype;
		moss.num = 1;
		moss.dz[0] = moss.thick;
		moss.dz[1] = MISSING_D;

		MossLayer* ml = new MossLayer(moss.thick, moss.type);
		ml->tem = fstsoill->tem;
		insertBefore(ml, fstsoill);   // create the new moss layer above the first soil layer

		if(ml->tem>0.){
			ml->liq = ml->maxliq;      // assuming that moss layer initially saturated - usually moss exists in wet condition
			ml->ice = 0.;
			ml->frozen = 0;
		}else{
			ml->liq = ml->minliq;
			ml->ice = ml->maxice;
			ml->frozen = 1;
		}

		getOslCarbon5Thickness(ml, 0., ml->dz);

		// because a new layer insert, 'fronts' needs adjustment
		adjustFrontsAfterThickchange(0., moss.thick);

	    resortGroundLayers();

	}

	// moss.thick is too small
	// remove the moss layer, and put C into  next soil layer for C mass conservation
	if(fstmossl!=NULL && moss.thick < soildimpar.minmossthick) {
		SoilLayer *upsl = dynamic_cast<SoilLayer*>(fstmossl);
		SoilLayer *lwsl = dynamic_cast<SoilLayer*>(fstmossl->nextl);

		combineTwoSoilLayersU2L(upsl, lwsl);  //combine this upper layer into next layer
		removeLayer(upsl);   // and remove the upper moss-layer

	    resortGroundLayers();

	}

};

void Ground::redivideShlwLayers(){

	organic.shlwchanged = false;

	////////// IF there exists 'shlw' layer(s) ////////////////
	if(fstshlwl!=NULL){
		// checking the existing double-linked layer structure for 'shlw' layers
		double thick = 0.;

		Layer* currl =fstshlwl;
		while(currl!=NULL){
			if(currl->indl<=lstshlwl->indl){
				thick +=currl->dz;
			}else{
		 		break;	
			}
			currl =currl->nextl;
		}

		SoilLayer* upsl ;
		SoilLayer* lwsl;

		organic.shlwchanged =true;

		// first, comine all layer into one
		COMBINEBEGIN:
			currl =fstshlwl;
			while(currl!=NULL){
		
					if(currl->indl<lstshlwl->indl && currl->nextl->isFibric){
						upsl = dynamic_cast<SoilLayer*>(currl);
						lwsl = dynamic_cast<SoilLayer*>(currl->nextl);

						combineTwoSoilLayersL2U(lwsl,upsl);  //combine this layer and next layer

						upsl->indl = lwsl->indl;
						removeLayer(currl->nextl);
						goto COMBINEBEGIN;
					} else {
						break;
					}
					currl =currl->nextl;
			}
			updateSoilHorizons();   //all 'shlwl' are merged at this point


			// then, re-do the thickness division
			organic.initShlwThicknesses(thick);

			// restructure the double-linked 'shlw layer'
			if(organic.shlwnum==0){  // just in case
				removeLayer(fstshlwl);
		
			} else if (organic.shlwnum ==1){    //only change the properties of layer
				fstshlwl->dz = organic.shlwdz[0];
				SoilLayer* shlwsl = dynamic_cast<SoilLayer*>(fstshlwl);
				shlwsl->updateProperty4LayerChange();

			}else if (organic.shlwnum ==2){//split shlw layer into two
				OrganicLayer* plnew1 = new OrganicLayer(organic.shlwdz[1], 1);
				SoilLayer* shlwsl = dynamic_cast<SoilLayer*>(fstshlwl);
				splitOneSoilLayer(shlwsl, plnew1, 0., organic.shlwdz[1]);

				insertAfter(plnew1, shlwsl);

			}else if (organic.shlwnum ==3){//split shlw layer into 3 layers
				OrganicLayer* plnew2 = new OrganicLayer(organic.shlwdz[2],1);
				SoilLayer* shlwsl = dynamic_cast<SoilLayer*>(fstshlwl);
				splitOneSoilLayer(shlwsl, plnew2, 0., organic.shlwdz[2]);   //the bottom one first cut off
				insertAfter(plnew2, shlwsl);
		
				OrganicLayer* plnew1 = new OrganicLayer(organic.shlwdz[1],1);
				splitOneSoilLayer(shlwsl, plnew1, 0., organic.shlwdz[1]);   // the middle one cut off
				insertAfter(plnew1, shlwsl);
			}

			updateSoilHorizons();

	
		// end of adjusting existing layer structure
	
	////////////////// no existing fibric layer, MUST create a new one from the following layer
	} else {
		SoilLayer *nextsl;
		if (fstdeepl !=NULL) {
			nextsl = dynamic_cast<SoilLayer*>(fstdeepl);
		} else {
			nextsl = dynamic_cast<SoilLayer*>(fstminel);
		}

		double rawcmin = soildimpar.coefshlwa * pow(MINSLWTHICK*100., soildimpar.coefshlwb*1.)*10000.;  //Note: in Yi et al.(2009) - C in gC/cm2, depth in cm

		if (nextsl->rawc>=rawcmin) {
			organic.shlwchanged =true;
			organic.initShlwThicknesses(MINSLWTHICK);

			OrganicLayer* plnew = new OrganicLayer(organic.shlwdz[0], 1);
			plnew->dz= MINSLWTHICK;
			double frac = MINSLWTHICK/nextsl->dz;

			// assign properties for the new-created 'shlw' layer
			plnew->ice = max(0., nextsl->ice*frac);
			plnew->liq = max(plnew->minliq, nextsl->liq*frac);
			if (plnew->ice>plnew->maxice) plnew->ice = plnew->maxice;
			if (plnew->liq>plnew->maxliq) plnew->liq = plnew->maxliq;

			plnew->tem = nextsl->tem;
			getLayerFrozenstatusByFronts(plnew);

			plnew->rawc  = rawcmin;
			plnew->soma  = 0.;
			plnew->sompr = 0.;
			plnew->somcr = 0.;

			plnew->updateProperty4LayerChange();
			insertBefore(plnew, nextsl);

			// adjust properties for the following layer
			nextsl->ice -= plnew->ice;
			nextsl->liq -= plnew->liq;
			nextsl->rawc-=rawcmin;

			if (nextsl->isHumic) {  //additional changes needed for if the following layer is 'humic'
				nextsl->dz *=(1.-frac);
			}

			nextsl->updateProperty4LayerChange();

			updateSoilHorizons();

		}

	}

	resortGroundLayers();

}

void Ground::redivideDeepLayers(){

	////////// IF there exists 'deep' layer(s) ////////////////
	if(fstdeepl!=NULL){
		Layer * currl =fstdeepl;

		//first check the 'double-linked' if needs structural adjusting
		double thick = 0.;
		int num = 0;
		while(currl!=NULL){
			if(currl->indl<=lstdeepl->indl){
				thick +=currl->dz;
				num +=1;
			
			}else{
		 		break;	
			}
			currl =currl->nextl;
		}

		// Then adjusting the OS horion's layer division/combination
			SoilLayer* upsl ;
			SoilLayer* lwsl;
	
			//combine all deep layers into ONE for re-structuring
			COMBINEBEGIN:
			currl =fstdeepl;
			while(currl!=NULL){
		
				if(currl->indl<lstdeepl->indl){
					upsl = dynamic_cast<SoilLayer*>(currl);
					lwsl = dynamic_cast<SoilLayer*>(currl->nextl);


					combineTwoSoilLayersL2U(lwsl,upsl); //combine this layer and next layer
					upsl->indl = lwsl->indl;
					removeLayer(currl->nextl);
	      	
					goto COMBINEBEGIN;
				}else{
					break;
				}

				currl =currl->nextl;
			}
			updateSoilHorizons();   //all 'deepl' are merged at this point
	
			//Divide this one layer into up to 3 layers
			organic.initDeepThicknesses(thick);   //

			if(num>0 && organic.deepnum==0){ //remove all layer(s) from the double-linked structure

				currl = fstdeepl;
				while (currl!=NULL && currl->isHumic) {
					Layer * next = currl->nextl;
					removeLayer(currl);      //Note: here acutally the double-linked structure has changed
					currl = next;
				}

			}else if(organic.deepnum ==1){
				//only change the properties of layer
				fstdeepl->dz = organic.deepdz[0];
				SoilLayer* deepsl = dynamic_cast<SoilLayer*>(fstdeepl);
				deepsl->updateProperty4LayerChange();

			}else if (organic.deepnum ==2){//split deep layer into two
				OrganicLayer* plnew1 = new OrganicLayer(organic.deepdz[1],2);
				SoilLayer* deepsl = dynamic_cast<SoilLayer*>(fstdeepl);
				splitOneSoilLayer(deepsl, plnew1, 0., organic.deepdz[1]);   // cut from bottom
				insertAfter(plnew1, deepsl);

			}else if (organic.deepnum ==3){//split deep layer into 3 layers
				OrganicLayer* plnew2 = new OrganicLayer(organic.deepdz[2], 2);
				SoilLayer* deepsl = dynamic_cast<SoilLayer*>(fstdeepl);
				splitOneSoilLayer(deepsl, plnew2, 0., organic.deepdz[2]);   // the bottom one cut off first
				insertAfter(plnew2, deepsl);
		
				OrganicLayer* plnew1 = new OrganicLayer(organic.deepdz[1],2);
				splitOneSoilLayer(deepsl, plnew1, 0., organic.deepdz[1]);   // the middle one cut off secondly
				insertAfter(plnew1, deepsl);
			}
			updateSoilHorizons();

	
	/////////// THERE NO Existing deep amorphous OS layer //////////////////////
	} else {
		SoilLayer *lfibl;
		if (lstshlwl !=NULL) {
			lfibl = dynamic_cast<SoilLayer*>(lstshlwl);
		} else {
			return;
		}

		double deepcmin = soildimpar.coefdeepa * pow(MINDEPTHICK*100., soildimpar.coefdeepb*1.)*10000.;  //Note: in Yi et al.(2009) - C in gC/cm2, depth in cm
		double somc = 0.5*lfibl->soma+lfibl->sompr+lfibl->somcr;   //assuming those SOMC available for forming a deep humific OS layer

		if (somc>=deepcmin) {
			organic.initDeepThicknesses(MINDEPTHICK);

			OrganicLayer* plnew = new OrganicLayer(organic.deepdz[0], 2);
			double frac = plnew->dz/lfibl->dz;

			// assign properties for the new-created 'deep' layer
			plnew->ice = lfibl->ice*frac;
			plnew->liq = lfibl->liq*frac;
			plnew->tem = lfibl->tem;
			plnew->frozen = lfibl->frozen;

			plnew->rawc  = 0.;
			plnew->soma  = 0.5*lfibl->soma;
			plnew->sompr = lfibl->sompr;
			plnew->somcr = lfibl->somcr;

			plnew->updateProperty4LayerChange();
			insertAfter(plnew, lfibl);

			// adjust properties for the above fibrous layer
			organic.shlwchanged =true;
			lfibl->ice *= (1.-frac);
			lfibl->liq *= (1.-frac);
			lfibl->soma *=0.5;
			lfibl->sompr = 0.;
			lfibl->somcr = 0.;

			lfibl->updateProperty4LayerChange();

			updateSoilHorizons();

		}

	}

    resortGroundLayers();

};

// Note: here properties updated when do re-structuring double-linked layer matrix
// the 'usl' is the original layer, which will be divided into a new 'usl' (upper) and a new 'lsl' (lower)
// 'updeptop' - the 'usl' top depth of same soil horizon type (needed for estimating C content from depth)
// 'lsldz' - the new 'lsl' thickness
void Ground::splitOneSoilLayer(SoilLayer*usl, SoilLayer* lsl, const double & updeptop, const double &lsldz){

	 double lslfrac = lsldz/usl->dz;

	 // dividing depth/thickness
     usl->dz -= lsldz;    // the upper one will not change its depth from the surface
	 lsl->z   = usl->z + usl->dz;
	 lsl->dz  = lsldz;

	 //update layer water contents
	 lsl->liq = usl->liq*lslfrac;   //may need a better way to split 'water' ?
	 lsl->ice = usl->ice*lslfrac;

	 usl->liq *= (1.- lslfrac);
	 usl->ice *= (1.- lslfrac);

	 //update layer temperature
	 if(usl->nextl==NULL){
		lsl->tem = usl->tem;
	 }else{
	 	double ntem = usl->nextl->tem;
	 	double gradient = (usl->tem - ntem)/(- usl->dz -lsl->dz);   //linearly interpolated
	 	lsl->tem = usl->dz * gradient + usl->tem;
	 }

	 // after division, needs to update 'usl' and 'lsl'- 'frozen' status based on 'fronts' if given
	  getLayerFrozenstatusByFronts(lsl);
	  getLayerFrozenstatusByFronts(usl);
	  	 	
	 lsl->updateProperty4LayerChange();
	 usl->updateProperty4LayerChange();
	  	 	
	 //update C in new 'lsl' and 'usl' - note: at this point, 'usl' C must be not updated
	 	 //first, assign 'lsl' C with original 'usl', then update it using actual thickness and depth
	 lsl->rawc =usl->rawc;
	 lsl->soma =usl->soma;
	 lsl->sompr=usl->sompr;
	 lsl->somcr=usl->somcr;

	 if (usl->isOrganic) {
		 double pldtop = updeptop + usl->dz;   //usl->dz must have been updated above
		 double pldbot = pldtop + lsl->dz;
		 getOslCarbon5Thickness(lsl, pldtop, pldbot);
	 } else {
		 lsl->rawc  *= lslfrac;
		 lsl->soma  *= lslfrac;
		 lsl->sompr *= lslfrac;
		 lsl->somcr *= lslfrac;
	 }

	  // then update C for new 'usl'
	  usl->rawc -= lsl->rawc;
	  usl->soma -= lsl->soma;
	  usl->sompr-= lsl->sompr;
	  usl->somcr-= lsl->somcr;

};

// Note: here properties updated when do combining two double-linked layers
// from upper 'usl' to lower layer 'lsl'
// after calling this, 'usl' must be removed

void Ground::combineTwoSoilLayersU2L(SoilLayer* usl, SoilLayer* lsl){

	  // update water content
	  lsl->z    = usl->z;   //note - z is the top of a layer from ground surface
	  lsl->dz  += usl->dz;
  	  lsl->liq += usl->liq;
  	  lsl->ice += usl->ice;

  	  // update temperature
  	  double upfrac = usl->dz/lsl->dz;
  	  lsl->tem *= (1.-upfrac);
  	  lsl->tem += usl->tem*upfrac;

  	  // update C content:
	  lsl->rawc +=usl->rawc;
	  lsl->soma +=usl->soma;
	  lsl->sompr+=usl->sompr;
	  lsl->somcr+=usl->somcr;
	  	 	
	  // after combination, needs to update 'lsl'- 'frozen' status based on 'fronts' if given
	  getLayerFrozenstatusByFronts(lsl);
	  checkFrontsValidity();

	  lsl->updateProperty4LayerChange();


};

void Ground::combineTwoSoilLayersL2U(SoilLayer* lsl, SoilLayer* usl){
 
	  // update water content
   	  usl->dz  +=lsl->dz;
   	  usl->liq +=lsl->liq;
   	  usl->ice +=lsl->ice;

  	  // update temperature
  	  double lsfrac = lsl->dz/usl->dz;
  	  usl->tem *= (1.-lsfrac);
  	  usl->tem += lsl->tem*lsfrac;

   	  // update C content:
   	  usl->rawc +=lsl->rawc;
   	  usl->soma +=lsl->soma;
   	  usl->sompr+=lsl->sompr;
   	  usl->somcr+=lsl->somcr;

	  // after combination, needs to update 'usl'- 'frozen' status based on 'fronts' if given
	  getLayerFrozenstatusByFronts(usl);

	  usl->updateProperty4LayerChange();

};

// The following module will re-constructure double-linked layer matrix based on C content change after fire
// So, it must be called after 'bd' layerd C content was assigned to the orginal double-linked layer matrix
double Ground::adjustSoilAfterburn(){

	double bdepthadj = 0.;  // this is used to check if thickness change here would be modifying burn thickness in 'WildFire.cpp'
	                        // and 'frontz'

  	Layer *currl  = toplayer;
  	// if there is snow, remove it
  	while(currl!=NULL){
  		if(currl->isSnow){
  	  		removeLayer(currl);
  	  		currl = toplayer;        // then the new toplayer is currl->nextl(otherwise, bug here)
  		}else{
  	  		break;
  		}
	}

  	// remove all moss/organic layers, if C is zero, after fire
  	currl = fstsoill;
  	while (currl!=NULL){
  		if(currl->isMoss || currl->isOrganic){
  			double tsomc = currl->rawc+currl->soma+currl->sompr+currl->somcr;
	  		if(tsomc<=0.){
	  	  		bdepthadj += currl->dz;  // adding the removed moss layer thickness to that 'err' counting
	  	    	adjustFrontsAfterThickchange(0, -currl->dz);  // need to adjust 'freezing/thawing front depth' due to top layer removal below
	  	  		removeLayer(currl);

	  	  		currl = toplayer;          // then the new toplayer is currl->nextl (otherwise, bug here)
	  		}else{
	  			break;
	  		}

  		}else {
  	 		break;
  		}
  	}
  	// Note: at this point, the toplayer(s) may have been moved up due to snow/moss horizons removal above, so need resort the double-linked structure
 	resortGroundLayers();

  	// The left organic layer(s) after fire should all be turned into humified organic layer
  	currl = toplayer;
  	while (currl!=NULL){
  		if(currl->isFibric){
  			OrganicLayer * pl = dynamic_cast<OrganicLayer*>(currl);
			pl->humify();   // here only updated 'physical' properties

			pl->somcr += pl->rawc;  //assuming all 'raw material' converted into 'chemically-resistant' SOM
			pl->rawc = 0.;

  		}else if (currl->isHumic || currl->isMineral || currl->isRock){

  			break;
  		}

  		currl = currl->nextl;
  	}

  	// re-do thickness of deep organic layers, because of changing of its original type is not humic
 	currl = toplayer;
 	double deepctop = 0.;  //cumulative C for deep OSL horizon at the top of a layer, initialzed as 0
 	double deepcbot;
  	while(currl!=NULL){
 	  	if(currl->isHumic){
 			double olddz;
 			olddz= currl->dz;
 	  		OrganicLayer *pl=dynamic_cast<OrganicLayer*>(currl);
 			double plcarbon = pl->rawc+pl->soma+pl->sompr+pl->somcr;
 			if (plcarbon > 0.) { // this may not be needed, if we do things carefully above. But just in case
				 // update 'dz' for 'pl' from its C content
				 double olddz = currl->dz;
				 deepcbot = deepctop+pl->rawc+currl->soma+currl->sompr+currl->somcr;
				 getOslThickness5Carbon(currl, deepctop, deepcbot);

				 deepctop = deepcbot;
				 bdepthadj += (olddz - currl->dz);  // adjuting the difference to that 'err' counting

				 pl->updateProperty4LayerChange(); //update soil physical property after thickness change from C is done

 			}

 		}else if (currl->isMineral || currl->isRock){
 		  	 break;
 		}

 		currl =currl->nextl;
 	}
	resortGroundLayers();

	// finally, checking if further needed to divide/combine double-linked layer matrix,
	// in case that some layers may be getting too thick or too thin due to layer adjustion above
	// then, re-do layer division or combination is necessary for better thermal/hydrological simulation
	redivideSoilLayers();

  	// for checking the adjusted burned thickness
	return bdepthadj;
};

/////////////////////////////////////////////////////////////////////////////////

//check the validity of fronts in soil column
void Ground::checkFrontsValidity(){

	if (frontsz.size()>0) {
		// checking if the 'front' may be out of the top soil layer
		while (frontsz[0]<=fstsoill->z) {
			frontsz.pop_front();
			frontstype.pop_front();    // this will update the 'deque'
		}

		// checking if the 'front' may be out of soil bottom
		while (frontsz[frontsz.size()-1]>=(lstsoill->z+lstsoill->dz*0.9999)) {
			frontsz.pop_back();
			frontstype.pop_back();    // this will update the 'deque'
		}
	}

 	int frntnum = frontsz.size();

	for(int i=0; i<MAX_NUM_FNT; i++){
		if (i<frntnum) {
			frontz[i] = frontsz[i];
			fronttype[i] = frontstype[i];

			if (i>0){
				if (fronttype[i]==fronttype[i-1]) {
					string msg = "adjacent fronts should be different";
//					cout<< msg <<" in Ground::checkFrontsValidity! \n";
				}
			}
		} else {
			frontz[i] = MISSING_D;
			fronttype[i] = MISSING_I;

		}
	}

	int fntind = 0;
 	Layer*currl=fstsoill;
 	while (currl!=NULL && fntind<frntnum) {

		if(currl->isSoil){
			while (frontsz[fntind]>currl->z &&
					frontsz[fntind]<=currl->z+currl->dz) {

				if (currl->frozen!=0) {
					string msg = "soil layer with front shall be have 0 for its frozen state";
//					cout << msg + ":: in Soil Layer "<<currl->indl<< "\n";
				}

				fntind++;
				if (fntind>=frntnum) break;
			}
		}

 		currl=currl->nextl;
	}
};

//if OS thickness changes, the following needs to be called
void Ground::adjustFrontsAfterThickchange(const double &depth, const double &thickadding){

 	int frntnum = frontsz.size();

	for(int i=0; i<frntnum; i++){
		if (frontsz[i]>=depth)                // only need to adjust 'fronts' below 'depth'
		frontsz[i] += thickadding;            //thickadding CAN be negative
	}

	// checking if the 'front' may be removed, e.g., due to fire removal of top layers
	while (frontsz.size()>0 && frontsz[0]<=0.) {
		frontsz.pop_front();
		frontstype.pop_front();    // this will update the 'deque'
	}

};

// update the fraction of frozen portion (thickness), and frozen status for ONE layer, if known 'fronts' dequeue given
// this is useful if re-do soil layer construction/division, but not change the total thickness
void Ground::getLayerFrozenstatusByFronts(Layer * soill){

	if (soill==NULL) return;

	int fntnum = frontsz.size();
	int fntind = 0;

	if (fntnum>0 &&
		soill->z >= frontsz.back() &&
		((soill->z+soill->dz) <= frontsz.front())) {  //at least the layer within fronts

			double fracfrozen = 0.;
			double dzabvfnt   = 0.;

			while (fntind<fntnum){

				double fntz = frontsz[fntind];
				int fnttype = frontstype[fntind];

				if (fntz>soill->z && fntz<=soill->z+soill->dz){

					soill->frozen = 0;
					double dzfnt = fntz-soill->z; // the distance of the 'fntind'th front from the 'currl->z'
					if (fnttype==1) {                             //freezing front: from this front up to the neibored previous front IS frozen portion
 						fracfrozen += (dzfnt - dzabvfnt);
					} else if (fnttype==-1 &&    // thawing front without following freezing front in the 'currl'
 						( (fntind==fntnum-1) ||                      // thawing front already the last one in the deque
 						  (fntind<fntnum-1 && frontsz[fntind+1]>(soill->z+soill->dz)))){  //   // the following (freezing) front out of 'currl'
						fracfrozen += soill->dz - dzfnt;
					}

					dzabvfnt = dzfnt;    //update the upper front 'dz' for following front

				} else {

					if (fntz<=soill->z) soill->frozen = -fnttype;

					if (fntz>soill->z+soill->dz) break;
				}

				fntind++;
			}

			soill->frozenfrac = fracfrozen/soill->dz;

 	} else {  // not possible for a layer containing fronts
 			if (soill->tem > 0.) {
 				soill->frozen = -1;
 				soill->frozenfrac = 0.;
 			} else {
 				soill->frozen = 1;
				soill->frozenfrac = 1.;
 			}
 	}

};


void Ground::setDrainL(Layer* lstsoill, double & barrierdepth, double & watertab){


	double watab  = watertab;           // water table depth (from surface)
	double ald    = barrierdepth;       // barrier depth, e.g. ALD or uppermost frozen depth (from surface)
	draindepth    = watab;
	if (draindepth>=ald) draindepth = ald;     // the min. of watertable and barrierdepth

	if (draindepth<=0) {
		drainl = NULL;
	} else {
		drainl = lstsoill;
		Layer* currl = lstsoill;
		double laytop = currl->z;
		double laybot = currl->z+currl->dz;
		while(currl!=NULL){
			if(currl->isSoil){
				laytop = currl->z;
				laybot = currl->z+currl->dz;

				if(draindepth<=laybot && draindepth>laytop){
					drainl = currl;  // the drainage layer is the soil layer with drainage depth inside
					break;
				}

			}else{
				break;
			}

			currl = currl->prevl;
		}
	}

};

void Ground::retrieveSnowDimension(snwstate_dim * snowdim){

	Layer * curr=toplayer;
    int snwind = 0;

	while(curr!=NULL){
	  if(curr->isSnow){

	  	//dimension output here as well
		  snowdim->dz[snwind] = curr->dz;
		  snowdim->age[snwind]= curr->age;
		  snowdim->rho[snwind]= curr->rho;
		  snowdim->por[snwind]= curr->poro;

		  curr = curr->nextl;

	  }else{
		  if (snwind>=MAX_SNW_LAY) break;
		  snowdim->dz[snwind] = MISSING_D;
		  snowdim->age[snwind]= MISSING_D;
		  snowdim->rho[snwind]= MISSING_D;
		  snowdim->por[snwind]= MISSING_D;

	  }

	  snwind++;

	}

	snowdim->thick  = snow.thick;
	snowdim->numsnwl= snow.numl;
	snowdim->dense  = snow.dense;
	snowdim->extramass = snow.extramass;

}

///save 'soil' information in double-linked layer into struct in 'cd'
void Ground::retrieveSoilDimension(soistate_dim * soildim){
	Layer * curr;

	curr= toplayer;

	//initializing
	soildim->mossthick =0;
	soildim->shlwthick =0;
	soildim->deepthick =0;
	soildim->mineathick =0;
	soildim->minebthick =0;
	soildim->minecthick =0;
	soildim->totthick  =0;

	soildim->mossnum =0;
	soildim->shlwnum =0;
	soildim->deepnum =0;
	soildim->minenum =0;
	soildim->numsl   =0;

    for(int il=0; il<MAX_SOI_LAY; il++){
      soildim->age[il]  = MISSING_I;
      soildim->z[il]    = MISSING_D;
      soildim->dz[il]   = MISSING_D;
      soildim->type[il] = MISSING_I;
      soildim->por[il]  = MISSING_D;
      soildim->texture[il]  = MISSING_I;
    }

  	int slind=0;
  	int mlind=0;
	while(curr!=NULL) {

		if(curr->isSoil){
			soildim->age[slind] = (int)curr->age;
			soildim->dz[slind]  = curr->dz;
			soildim->z[slind]   = curr->z;
			soildim->por[slind] = curr->poro;

			if(curr->isMoss){
				soildim->type[slind] = 0;
				soildim->mossthick +=curr->dz;
				soildim->mossnum+=1;
			} else if(curr->isOrganic){
				if(curr->isFibric){
					soildim->type[slind] = 1;
					soildim->shlwthick +=curr->dz;
					soildim->shlwnum+=1;

				}else if(curr->isHumic){
					soildim->type[slind] = 2;
					soildim->deepthick +=curr->dz;
					soildim->deepnum+=1;
				}
			}else if(curr->isMineral){
				soildim->type[slind] = 3;
				soildim->texture[slind] = mineral.texture[mlind];
				soildim->minenum+=1;

				if (mlind>=0 && mlind<=MINEZONE[0]) soildim->mineathick +=curr->dz;
				if (mlind>MINEZONE[0] && mlind<=MINEZONE[1]) soildim->minebthick +=curr->dz;
				if (mlind>MINEZONE[1] && mlind<=MINEZONE[2]) soildim->minecthick +=curr->dz;

				mlind++;

			}

			slind++;
		}

		curr= curr->nextl;
	};

	//
	soildim->numsl= soildim->mossnum+soildim->shlwnum+soildim->deepnum+soildim->minenum;

	soildim->totthick = soildim->mossthick+soildim->shlwthick+soildim->deepthick
			             +soildim->mineathick+soildim->minebthick+soildim->minecthick;

};

void Ground::updateWholeFrozenStatus(){

	if(fstfntl==NULL && lstfntl==NULL){
	 	ststate = fstsoill->frozen;
	} else {
	  	ststate = 0; // partitally frozen
	}
};

///////////////////////////////////////////////////////////////////////

// update OSL thickness for all organic horizons if C content known
void Ground::updateOslThickness5Carbon(Layer* fstsoil){

	if(fstsoil->isMineral || fstsoil->isRock){
		return;
 	}

 	double mosscbot = 0.;
 	double mossctop = 0.;

 	double shlwcbot = 0.;
 	double shlwctop = 0.;

 	double deepcbot = 0.;
 	double deepctop = 0.;

 	double olddz = 0.;
 	double newdz = 0.;

 	Layer* currl=fstsoil;
 	while(currl!=NULL){
 	  	if(currl->isSoil && (currl->isOrganic || currl->isMoss)){
 	  	 	SoilLayer* sl = dynamic_cast<SoilLayer*>(currl) ;
 	  	 	olddz = sl->dz;
			if(sl->isHumic){
				 deepcbot = deepctop+sl->rawc+sl->soma+sl->sompr+sl->somcr;
 				 getOslThickness5Carbon(sl, deepctop, deepcbot);
 			     deepctop = deepcbot;

  			} else if(sl->isFibric){
 				 shlwcbot = shlwctop+sl->rawc+sl->soma+sl->sompr+sl->somcr;
 				 getOslThickness5Carbon(sl, shlwctop, shlwcbot);
 				 shlwctop = shlwcbot;

 			} else if(sl->isMoss){
				 mosscbot = mossctop+sl->rawc+sl->soma+sl->sompr+sl->somcr;
				 getOslThickness5Carbon(sl, mossctop, mosscbot);
				 mossctop = mosscbot;

			}

			updateSoilLayerZ();   //'dz' changes, so 'z' needs update for all (index will not change).

 			sl->updateProperty4LayerChange();

 			newdz = sl->dz;

 		}else{
 			break;

 	  	}
 		currl =currl->nextl;
 	}

 	//
 	checkFrontsValidity();
};

// conversion from OSL C to thickness
void Ground::getOslThickness5Carbon(Layer* sl, const double &plctop, const double &plcbot){

	// NOTE: the OSL C - thickness relationship is for the whole same-type OSL horizon
	// the estimation here is for ONE layer only in the whole horizon
	// it means that C cannot be calculated using the layer thickness
	// but using the bottom depth of a layer from the top of the whole horizon

	double pltop = 0.;
	double plbot = 0.;
	double cumcarbon    = plcbot; //Cumulative C from the top of the whole horizon
	double prevcumcarbon= plctop; //Cumulative C until the layer top

	double osdzold = sl->dz;

	if(sl->isMoss){
		pltop = pow((prevcumcarbon/10000.)/soildimpar.coefmossa, 1./soildimpar.coefmossb)/100.;  //Note: in Yi et al.(2009) - C in gC/cm2, depth in cm
		plbot = pow((cumcarbon/10000.)/soildimpar.coefmossa, 1./soildimpar.coefmossb)/100.;  //Note: in Yi et al.(2009) - C in gC/cm2, depth in cm
	} else if(sl->isFibric){
		pltop = pow((prevcumcarbon/10000.)/soildimpar.coefshlwa, 1./soildimpar.coefshlwb)/100.;  //Note: in Yi et al.(2009) - C in gC/cm2, depth in cm
		plbot = pow((cumcarbon/10000.)/soildimpar.coefshlwa, 1./soildimpar.coefshlwb)/100.;  //Note: in Yi et al.(2009) - C in gC/cm2, depth in cm
	} else if (sl->isHumic){
		pltop = pow((prevcumcarbon/10000.)/soildimpar.coefdeepa, 1./soildimpar.coefdeepb)/100.;  //Note: in Yi et al.(2009) - C in gC/cm2, depth in cm
		plbot = pow((cumcarbon/10000.)/soildimpar.coefdeepa, 1./soildimpar.coefdeepb)/100.;  //Note: in Yi et al.(2009) - C in gC/cm2, depth in cm
	}

	sl->dz=plbot-pltop;
	double osdznew = sl->dz;

  	// need to adjust 'freezing/thawing front depth', if 'fronts' depth below 'sl->z'
  	adjustFrontsAfterThickchange(sl->z, osdznew - osdzold);

};

// conversion from OSL thickness to C content
// note- only for thickness changing, i.e. previous fraction of SOM C pools must be known
void Ground::getOslCarbon5Thickness(Layer* sl, const double &plztop, const double &plzbot){

	// NOTE: the OSL C - thickness relationship is for the whole OSL horizon
	// the estimation here is for ONE layer only in the whole horizon
	// it means that C cannot be calculated using the layer thickness
	// but using the bottom depth of a layer from the top of the whole horizon
	double dbot = plzbot;   //the bottom depth of a layer from the top of the whole horizon
	double dtop = plztop;  // the top depth of the layer

	double cumcarbon    =0.;
	double prevcumcarbon=0.;

	if(sl->isMoss){
		prevcumcarbon = soildimpar.coefmossa * pow(dtop*100., soildimpar.coefmossb*1.)*10000.;  //Note: in Yi et al.(2009) - C in gC/cm2, depth in cm
		cumcarbon     = soildimpar.coefmossa * pow(dbot*100., soildimpar.coefmossb*1.)*10000.;  //Note: in Yi et al.(2009) - C in gC/cm2, depth in cm
	} else if(sl->isFibric){
		prevcumcarbon = soildimpar.coefshlwa * pow(dtop*100., soildimpar.coefshlwb*1.)*10000.;  //Note: in Yi et al.(2009) - C in gC/cm2, depth in cm
		cumcarbon     = soildimpar.coefshlwa * pow(dbot*100., soildimpar.coefshlwb*1.)*10000.;  //Note: in Yi et al.(2009) - C in gC/cm2, depth in cm
	} else if (sl->isHumic){
		prevcumcarbon = soildimpar.coefdeepa * pow(dtop*100., soildimpar.coefdeepb*1.)*10000.;
		cumcarbon     = soildimpar.coefdeepa * pow(dbot*100., soildimpar.coefdeepb*1.)*10000.;
	}

	if (sl->isMoss) {
		sl->rawc = cumcarbon-prevcumcarbon;
		sl->soma = 0.;
		sl->sompr= 0.;
		sl->somcr= 0.;
	} else if (sl->isOrganic) {
		double tsomc=sl->rawc+sl->soma+sl->sompr+sl->somcr;
		if(tsomc>0.){
			sl->rawc  *= (cumcarbon-prevcumcarbon)/tsomc; //because thickness change, C pools need update
			sl->soma  *= (cumcarbon-prevcumcarbon)/tsomc;
			sl->sompr *= (cumcarbon-prevcumcarbon)/tsomc;
			sl->somcr *= (cumcarbon-prevcumcarbon)/tsomc;
		}
	}
};

//////////////////////////////////////////////////////////////////////
void Ground::setCohortLookup(CohortLookup* chtlup){
	chtlu = chtlup;
};

