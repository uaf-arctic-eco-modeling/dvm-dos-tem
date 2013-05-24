#include "RestartOutputer.h"

/*! constructor */
RestartOutputer::RestartOutputer(){
 
};

RestartOutputer::~RestartOutputer(){
	if (restartFile!=NULL) {
		restartFile->close();
		delete restartFile;
	}

};

void RestartOutputer::init(string& outputdir,string& stage){
	
 	NcError err(NcError::verbose_nonfatal);
 	
	restartfname = outputdir+"restart"+stage+".nc";

	restartFile=new NcFile(restartfname.c_str(), NcFile::Replace);

	//dimension definition
	chtD = restartFile->add_dim("CHTID");

	pftD     = restartFile->add_dim("PFT", NUM_PFT);
	pftpartD = restartFile->add_dim("PFTPART", NUM_PFT_PART);

	rootlayerD = restartFile->add_dim("ROOTLAYER", MAX_ROT_LAY);
	snowlayerD = restartFile->add_dim("SNOWLAYER", MAX_SNW_LAY);
	soillayerD = restartFile->add_dim("SOILLAYER", MAX_SOI_LAY);
	rocklayerD = restartFile->add_dim("ROCKLAYER", MAX_ROC_LAY);
	frontD     = restartFile->add_dim("FRONTNUM", MAX_NUM_FNT);
	prvyearD   = restartFile->add_dim("PRVYEAR", 10);
	prvmonthD  = restartFile->add_dim("PRVMONTH", 12);
	
	//variable definition
    chtidV   =restartFile->add_var("CHTID", ncInt, chtD);
    errcodeV =restartFile->add_var("ERRCODE", ncInt, chtD);

    // - atm
	dsrV         =restartFile->add_var("DSR", ncInt, chtD);           //days since rainfall
	firea2sorgnV =restartFile->add_var("FIREA2SORGN", ncInt, chtD);   //fire-emitted N deposition

	// - veg
	ysfV         =restartFile->add_var("YSF", ncInt, chtD);  // years since fire

	ifwoodyV     =restartFile->add_var("IFWOODY", ncInt, chtD, pftD);
	ifdeciwoodyV =restartFile->add_var("IFDECIWOODY", ncInt, chtD, pftD);
	ifperenialV  =restartFile->add_var("IFPERENIAL", ncInt, chtD, pftD);
	nonvascularV =restartFile->add_var("NONVASCULAR", ncInt, chtD, pftD);

	vegageV  =restartFile->add_var("VEGAGE", ncInt, chtD, pftD);
	vegcovV  =restartFile->add_var("VEGCOV", ncDouble, chtD, pftD);
	laiV     =restartFile->add_var("LAI", ncDouble, chtD, pftD);
	rootfracV=restartFile->add_var("ROOTFRAC", ncDouble, chtD, rootlayerD, pftD);
    vegwaterV=restartFile->add_var("VEGWATER", ncDouble, chtD, pftD);
    vegsnowV =restartFile->add_var("VEGSNOW", ncDouble, chtD, pftD);

    vegcV   =restartFile->add_var("VEGC", ncDouble, chtD, pftpartD, pftD);
    strnV   =restartFile->add_var("STRN", ncDouble, chtD, pftpartD, pftD);
    labnV   =restartFile->add_var("LABN", ncDouble, chtD, pftD);
    deadcV  =restartFile->add_var("DEADC", ncDouble, chtD, pftD);
    deadnV  =restartFile->add_var("DEADN", ncDouble, chtD, pftD);

 	toptV         =restartFile->add_var("TOPT", ncDouble, chtD, pftD);
	eetmxV        =restartFile->add_var("EETMX", ncDouble, chtD, pftD);
 	growingttimeV =restartFile->add_var("GROWINGTTIME", ncDouble, chtD, pftD);
	unnormleafmxV =restartFile->add_var("UNNORMLEAFMX", ncDouble, chtD, pftD);
	foliagemxV =restartFile->add_var("FOLIAGEMX", ncDouble, chtD, pftD);

	toptAV         =restartFile->add_var("TOPTA", ncDouble, chtD, prvyearD, pftD);
	eetmxAV        =restartFile->add_var("EETMXA", ncDouble, chtD, prvyearD, pftD);
 	growingttimeAV =restartFile->add_var("GROWINGTTIMEA", ncDouble, chtD, prvyearD, pftD);
	unnormleafmxAV =restartFile->add_var("UNNORMLEAFMXA", ncDouble, chtD, prvyearD, pftD);

    //snow
    numsnwlV =restartFile->add_var("NUMSNWL", ncInt, chtD);
    snwextramassV =restartFile->add_var("SNWEXTRAMASS", ncDouble, chtD);
    TSsnowV  =restartFile->add_var("TSsnow", ncDouble, chtD, snowlayerD);
    DZsnowV  =restartFile->add_var("DZsnow", ncDouble, chtD, snowlayerD);
    LIQsnowV =restartFile->add_var("LIQsnow", ncDouble, chtD, snowlayerD);
    ICEsnowV =restartFile->add_var("ICEsnow", ncDouble, chtD, snowlayerD);
 	AGEsnowV =restartFile->add_var("AGEsnow", ncDouble, chtD, snowlayerD);
    RHOsnowV =restartFile->add_var("RHOsnow", ncDouble, chtD, snowlayerD);
 
    //ground-soil
    numslV         =restartFile->add_var("NUMSL", ncInt, chtD);
    monthsfrozenV  =restartFile->add_var("MONTHSFROZEN", ncDouble, chtD);
    rtfrozendaysV  =restartFile->add_var("RTFROZENDAYS", ncInt, chtD);
    rtunfrozendaysV=restartFile->add_var("RTUNFROZENDAYS", ncInt, chtD);

    watertabV      =restartFile->add_var("WATERTAB", ncDouble, chtD);

    DZsoilV   =restartFile->add_var("DZsoil", ncDouble, chtD, soillayerD);
    AGEsoilV  =restartFile->add_var("AGEsoil", ncInt, chtD, soillayerD);
    TYPEsoilV =restartFile->add_var("TYPEsoil", ncInt, chtD, soillayerD);
	TSsoilV   =restartFile->add_var("TSsoil", ncDouble, chtD, soillayerD);
    LIQsoilV  =restartFile->add_var("LIQsoil", ncDouble, chtD, soillayerD);
    ICEsoilV  =restartFile->add_var("ICEsoil", ncDouble, chtD, soillayerD);
    FROZENsoilV=restartFile->add_var("FROZENsoil", ncInt, chtD, soillayerD);
    FROZENFRACsoilV=restartFile->add_var("FROZENFRACsoil", ncDouble, chtD, soillayerD);
    TEXTUREsoilV   =restartFile->add_var("TEXTUREsoil", ncInt, chtD, soillayerD);
        
    TSrockV =restartFile->add_var("TSrock", ncDouble, chtD, rocklayerD);
    DZrockV =restartFile->add_var("DZrock", ncDouble, chtD, rocklayerD);
   
	frontZV =restartFile->add_var("frontZ", ncDouble, chtD, frontD);  //front depth
    frontFTV=restartFile->add_var("frontFT", ncInt, chtD, frontD);    //freezing/thawing front
    
    wdebriscV =restartFile->add_var("WDEBRISC", ncDouble, chtD);
    wdebrisnV =restartFile->add_var("WDEBRISN", ncDouble, chtD);

    dmosscV =restartFile->add_var("DMOSSC", ncDouble, chtD);
    dmossnV =restartFile->add_var("DMOSSN", ncDouble, chtD);

    rawcV  =restartFile->add_var("RAWC", ncDouble, chtD, soillayerD);
    somaV  =restartFile->add_var("SOMA", ncDouble, chtD, soillayerD);
    somprV =restartFile->add_var("SOMPR", ncDouble, chtD, soillayerD);
    somcrV =restartFile->add_var("SOMCR", ncDouble, chtD, soillayerD);
    solnV  =restartFile->add_var("SOLN", ncDouble, chtD, soillayerD);
    avlnV  =restartFile->add_var("AVLN", ncDouble, chtD, soillayerD);

    prvltrfcnAV  =restartFile->add_var("PRVLTRFCNA", ncDouble, chtD, prvmonthD, soillayerD);

}

void RestartOutputer::outputVariables(const int & chtcount){
 	NcError err(NcError::verbose_nonfatal);

	chtidV->put_rec(&resod->chtid, chtcount);
	int errcode=errorChecking();
	errcodeV->put_rec(&errcode, chtcount);

	//atm
	dsrV->put_rec(&resod->dsr, chtcount);
	firea2sorgnV->put_rec(&resod->firea2sorgn, chtcount);

	//veg
	ysfV->put_rec(&resod->yrsdist, chtcount);

	ifwoodyV->put_rec(&resod->ifwoody[0], chtcount);
	ifdeciwoodyV->put_rec(&resod->ifdeciwoody[0], chtcount);
	ifperenialV->put_rec(&resod->ifperenial[0], chtcount);
	nonvascularV->put_rec(&resod->nonvascular[0], chtcount);
	vegageV->put_rec(&resod->vegage[0], chtcount);
	vegcovV->put_rec(&resod->vegcov[0], chtcount);
	laiV->put_rec(&resod->lai[0], chtcount);
	rootfracV->put_rec(&resod->rootfrac[0][0], chtcount);

	vegwaterV->put_rec(&resod->vegwater[0], chtcount);
	vegsnowV->put_rec(&resod->vegsnow[0], chtcount);

	vegcV->put_rec(&resod->vegc[0][0], chtcount);
	strnV->put_rec(&resod->strn[0][0], chtcount);
	labnV->put_rec(&resod->labn[0], chtcount);
	deadcV->put_rec(&resod->deadc[0], chtcount);
	deadnV->put_rec(&resod->deadn[0], chtcount);

    toptV->put_rec(&resod->topt[0], chtcount);
	eetmxV->put_rec(&resod->eetmx[0], chtcount);
	growingttimeV->put_rec(&resod->growingttime[0], chtcount);
	unnormleafmxV->put_rec(&resod->unnormleafmx[0], chtcount);
	foliagemxV->put_rec(&resod->foliagemx[0], chtcount);

	toptAV->put_rec(&resod->toptA[0][0], chtcount);
	eetmxAV->put_rec(&resod->eetmxA[0][0], chtcount);
	growingttimeAV->put_rec(&resod->growingttimeA[0][0], chtcount);
	unnormleafmxAV->put_rec(&resod->unnormleafmxA[0][0], chtcount);

	//snow
	numsnwlV->put_rec(&resod->numsnwl, chtcount);
	snwextramassV->put_rec(&resod->snwextramass, chtcount);
	DZsnowV->put_rec(&resod->DZsnow[0], chtcount);
	TSsnowV->put_rec(&resod->TSsnow[0], chtcount);
	LIQsnowV->put_rec(&resod->LIQsnow[0], chtcount);
	ICEsnowV->put_rec(&resod->ICEsnow[0], chtcount);
	AGEsnowV->put_rec(&resod->AGEsnow[0], chtcount);
	RHOsnowV->put_rec(&resod->RHOsnow[0], chtcount);
	
	//ground-soil
	numslV->put_rec(&resod->numsl, chtcount);
	monthsfrozenV->put_rec(&resod->monthsfrozen, chtcount);
	rtfrozendaysV->put_rec(&resod->rtfrozendays, chtcount);
	rtunfrozendaysV->put_rec(&resod->rtunfrozendays, chtcount);

	watertabV->put_rec(&resod->watertab, chtcount);

	DZsoilV->put_rec(&resod->DZsoil[0], chtcount);
	AGEsoilV->put_rec(&resod->AGEsoil[0], chtcount);
	TYPEsoilV->put_rec(&resod->TYPEsoil[0], chtcount);
	TSsoilV->put_rec(&resod->TSsoil[0], chtcount);
	LIQsoilV->put_rec(&resod->LIQsoil[0], chtcount);
	ICEsoilV->put_rec(&resod->ICEsoil[0], chtcount);
	FROZENsoilV->put_rec(&resod->FROZENsoil[0], chtcount);
	FROZENFRACsoilV->put_rec(&resod->FROZENFRACsoil[0], chtcount);
	TEXTUREsoilV->put_rec(&resod->TEXTUREsoil[0], chtcount);

	TSrockV->put_rec(&resod->TSrock[0], chtcount);
	DZrockV->put_rec(&resod->DZrock[0], chtcount);
	
	frontZV->put_rec(&resod->frontZ[0], chtcount);
	frontFTV->put_rec(&resod->frontFT[0], chtcount);
	
	wdebriscV->put_rec(&resod->wdebrisc, chtcount);
	wdebrisnV->put_rec(&resod->wdebrisn, chtcount);

	dmosscV->put_rec(&resod->dmossc, chtcount);
	dmossnV->put_rec(&resod->dmossn, chtcount);

	rawcV->put_rec(&resod->rawc[0], chtcount);
	somaV->put_rec(&resod->soma[0], chtcount);
	somprV->put_rec(&resod->sompr[0], chtcount);
	somcrV->put_rec(&resod->somcr[0], chtcount);
	solnV->put_rec(&resod->orgn[0], chtcount);
	avlnV->put_rec(&resod->avln[0], chtcount);

	prvltrfcnAV->put_rec(&resod->prvltrfcnA[0][0], chtcount);
		
}

int RestartOutputer::errorChecking(){
	int errcode = 0;

/*
	for(int il =0;il<MAX_SNW_LAY; il++){
		if (isnan(resod->TSsnow[il]) || isinf(resod->TSsnow[il])) errcode = -1;	
		if (isnan(resod->DZsnow[il]) || isinf(resod->DZsnow[il])) errcode = -1;	
		if (isnan(resod->LIQsnow[il]) || isinf(resod->LIQsnow[il])) errcode = -1;	
		if (isnan(resod->ICEsnow[il]) || isinf(resod->ICEsnow[il])) errcode = -1;	
		if (isnan(resod->AGEsnow[il]) || isinf(resod->AGEsnow[il])) errcode = -1;	
		if (isnan(resod->RHOsnow[il]) || isinf(resod->RHOsnow[il])) errcode = -1;	
	}
	
	for(int il =0;il<MAX_SOI_LAY; il++){
		if (isnan(resod->TSsoil[il]) || isinf(resod->TSsoil[il])) errcode = -1;	
		if (isnan(resod->DZsoil[il]) || isinf(resod->DZsoil[il])) errcode = -1;	
		if (isnan(resod->LIQsoil[il]) || isinf(resod->LIQsoil[il])) errcode = -1;	
		if (isnan(resod->ICEsoil[il]) || isinf(resod->ICEsoil[il])) errcode = -1;	
		if (isnan(resod->FROZENsoil[il]) || isinf(resod->FROZENsoil[il])) errcode = -1;	
		if (isnan(resod->TYPEsoil[il]) || isinf(resod->TYPEsoil[il])) errcode = -1;	
		//if (isnan(resod->NONCsoil[il]) || isinf(resod->NONCsoil[il])) errcode = -1;
		//if (isnan(resod->REACsoil[il]) || isinf(resod->REACsoil[il])) errcode = -1;
	}
	
	for(int il =0;il<MAX_MIN_LAY; il++){
		if (isnan(resod->TYPEmin[il]) || isinf(resod->TYPEmin[il])) errcode = -1;	
	}
   
	for(int il =0;il<MAX_ROC_LAY; il++){
		if (isnan(resod->TSrock[il]) || isinf(resod->TSrock[il])) errcode = -1;	
		if (isnan(resod->DZrock[il]) || isinf(resod->DZrock[il])) errcode = -1;	
	}

	for(int il =0;il<MAX_NUM_FNT; il++){
		if (isnan(resod->frontZ[il]) || isinf(resod->frontZ[il])) errcode = -1;	
		if (isnan(resod->frontFT[il]) || isinf(resod->frontFT[il])) errcode = -1;	
	}
     
    for(int i=0; i<10; i++){
		if (isnan(resod->toptA[0][i]) || isinf(resod->toptA[0][i])) errcode = -1;
		if (isnan(resod->eetmxA[i][0]) || isinf(resod->eetmxA[i][0])) errcode = -1;
		if (isnan(resod->petmxA[i][0]) || isinf(resod->petmxA[i][0])) errcode = -1;
		if (isnan(resod->unnormleafmxA[i][0]) || isinf(resod->unnormleafmxA[i][0])) errcode = -1;
    }
     
	//if (isnan(resod->soln) || isinf(resod->soln)) errcode = -1;
	//if (isnan(resod->avln) || isinf(resod->avln)) errcode = -1;
	if (isnan(resod->wdebris) || isinf(resod->wdebris)) errcode = -1;	
	//if (isnan(resod->strnl[0]) || isinf(resod->strnl[0])) errcode = -1;
	if (isnan(resod->labn[0]) || isinf(resod->labn[0])) errcode = -1;
	//if (isnan(resod->vegcl[0]) || isinf(resod->vegcl[0])) errcode = -1;
	if (isnan(resod->deadc[0]) || isinf(resod->deadc[0])) errcode = -1;
	if (isnan(resod->deadn[0]) || isinf(resod->deadn[0])) errcode = -1;
	if (isnan(resod->prveetmx[0]) || isinf(resod->prveetmx[0])) errcode = -1;
	if (isnan(resod->prvpetmx[0]) || isinf(resod->prvpetmx[0])) errcode = -1;
	if (isnan(resod->prvunnormleafmx[0]) || isinf(resod->prvunnormleafmx[0])) errcode = -1;
	if (isnan(resod->prvtopt[0]) || isinf(resod->prvtopt[0])) errcode = -1;
	//if (isnan(resod->vc2nl[0]) || isinf(resod->vc2nl[0])) errcode = -1;
	if (isnan(resod->kdfib) || isinf(resod->kdfib)) errcode = -1;	
	if (isnan(resod->kdhum) || isinf(resod->kdhum)) errcode = -1;	
	if (isnan(resod->kdmin) || isinf(resod->kdmin)) errcode = -1;
	if (isnan(resod->kdslow) || isinf(resod->kdslow)) errcode = -1;
	if (isnan(resod->foliagemx[0]) || isinf(resod->foliagemx[0])) errcode = -1;
	if (isnan(resod->ysf) || isinf(resod->ysf)) errcode = -1;	
	if (isnan(resod->burnedn) || isinf(resod->burnedn)) errcode = -1;
	if (isnan(resod->lai[0]) || isinf(resod->lai[0])) errcode = -1;
*/
	return errcode;
}

void RestartOutputer::setRestartOutData(RestartData * resodp){
	resod = resodp;
}


