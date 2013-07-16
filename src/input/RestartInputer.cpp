#include "RestartInputer.h"

/*! constructor */
RestartInputer::RestartInputer(){
 
};

RestartInputer::~RestartInputer(){
 	//cout<< "closing output files in RestartInputer \n";
   
    if(restartFile!=NULL){
    	restartFile->close();
    	delete restartFile;
    }

};

void RestartInputer::init(string & dirfile){
 	
	string filename =dirfile;    //Yuan: input file name with dir 

	restartFile = new NcFile(filename.c_str(), NcFile::ReadOnly);
	if(!restartFile->is_valid()){
 		string msg = filename+" is not valid";
 		cout<<msg+"\n";
 		exit(-1);
 	}
	
	//dimension definition
	chtD = restartFile->get_dim("CHTID");

	pftD     = restartFile->get_dim("PFT");
	pftpartD = restartFile->get_dim("PFTPART");

	rootlayerD = restartFile->get_dim("ROOTLAYER");
	snowlayerD = restartFile->get_dim("SNOWLAYER");
	soillayerD = restartFile->get_dim("SOILLAYER");
	rocklayerD = restartFile->get_dim("ROCKLAYER");
	frontD     = restartFile->get_dim("FRONTNUM");
	prvyearD   = restartFile->get_dim("PRVYEAR");

	//variable definition
    chtidV   =restartFile->get_var("CHTID");
    errcodeV =restartFile->get_var("ERRCODE");

    // - atm
	dsrV         =restartFile->get_var("DSR");           //days since rainfall
	firea2sorgnV =restartFile->get_var("FIREA2SORGN");   //fire-emitted N deposition

	// - veg
	ysfV         =restartFile->get_var("YSF");  // years since fire

	ifwoodyV     =restartFile->get_var("IFWOODY");
	ifdeciwoodyV =restartFile->get_var("IFDECIWOODY");
	ifperenialV  =restartFile->get_var("IFPERENIAL");
	nonvascularV  =restartFile->get_var("NONVASCULAR");

	vegageV  =restartFile->get_var("VEGAGE");
	vegcovV  =restartFile->get_var("VEGCOV");
	laiV     =restartFile->get_var("LAI");
	rootfracV=restartFile->get_var("ROOTFRAC");
    vegwaterV=restartFile->get_var("VEGWATER");
    vegsnowV =restartFile->get_var("VEGSNOW");

    vegcV   =restartFile->get_var("VEGC");
    strnV   =restartFile->get_var("STRN");
    labnV   =restartFile->get_var("LABN");
    deadcV  =restartFile->get_var("DEADC");
    deadnV  =restartFile->get_var("DEADN");

 	toptV         =restartFile->get_var("TOPT");
	eetmxV        =restartFile->get_var("EETMX");
	unnormleafmxV =restartFile->get_var("UNNORMLEAFMX");
 	growingttimeV =restartFile->get_var("GROWINGTTIME");
	foliagemxV =restartFile->get_var("FOLIAGEMX");

 	toptAV         =restartFile->get_var("TOPTA");
	eetmxAV        =restartFile->get_var("EETMXA");
	unnormleafmxAV =restartFile->get_var("UNNORMLEAFMXA");
 	growingttimeAV =restartFile->get_var("GROWINGTTIMEA");

    //snow
    numsnwlV =restartFile->get_var("NUMSNWL");
    snwextramassV =restartFile->get_var("SNWEXTRAMASS");
    TSsnowV  =restartFile->get_var("TSsnow");
    DZsnowV  =restartFile->get_var("DZsnow");
    LIQsnowV =restartFile->get_var("LIQsnow");
    ICEsnowV =restartFile->get_var("ICEsnow");
 	AGEsnowV =restartFile->get_var("AGEsnow");
    RHOsnowV =restartFile->get_var("RHOsnow");

    //ground-soil
    numslV         =restartFile->get_var("NUMSL");
    monthsfrozenV  =restartFile->get_var("MONTHSFROZEN");
	rtfrozendaysV  =restartFile->get_var("RTFROZENDAYS");
	rtunfrozendaysV=restartFile->get_var("RTUNFROZENDAYS");
    watertabV    =restartFile->get_var("WATERTAB");

    DZsoilV   =restartFile->get_var("DZsoil");
    AGEsoilV  =restartFile->get_var("AGEsoil");
    TYPEsoilV =restartFile->get_var("TYPEsoil");
	TSsoilV   =restartFile->get_var("TSsoil");
    LIQsoilV  =restartFile->get_var("LIQsoil");
    ICEsoilV  =restartFile->get_var("ICEsoil");
    FROZENsoilV=restartFile->get_var("FROZENsoil");
    FROZENFRACsoilV=restartFile->get_var("FROZENFRACsoil");
    TEXTUREsoilV   =restartFile->get_var("TEXTUREsoil");

    TSrockV =restartFile->get_var("TSrock");
    DZrockV =restartFile->get_var("DZrock");

	frontZV =restartFile->get_var("frontZ");
    frontFTV=restartFile->get_var("frontFT");

    wdebriscV =restartFile->get_var("WDEBRISC");
    wdebrisnV =restartFile->get_var("WDEBRISN");

    dmosscV =restartFile->get_var("DMOSSC");
    dmossnV =restartFile->get_var("DMOSSN");

    rawcV  =restartFile->get_var("RAWC");
    somaV  =restartFile->get_var("SOMA");
    somprV =restartFile->get_var("SOMPR");
    somcrV =restartFile->get_var("SOMCR");
    solnV  =restartFile->get_var("SOLN");
    avlnV  =restartFile->get_var("AVLN");

    prvltrfcnAV  =restartFile->get_var("PRVLTRFCNA");

};

////////////////////////////////////////////////////////////////////////////////////////
//NOTE: the cid in the following is actually the record order number (starting 0)
void RestartInputer::getReschtId(int &reschtid, const int &recno){
	
	chtidV->set_cur(recno);
	NcBool nb1 = chtidV->get(&reschtid, 1);
	if(!nb1){	 
	 string msg = "problem in reading chtid in  RestartInputer";
		cout<<msg+"\n";
		exit(-1);
	}
}

void RestartInputer::getErrcode(int & errcode, const int &recno){
	
	errcodeV->set_cur(recno);
	NcBool nb1 = errcodeV->get(&errcode, 1);
	if(!nb1){	 
	 string msg = "problem in reading errcode in  RestartInputer";
		cout<<msg+"\n";
		exit(-1);
	}
}

void RestartInputer::getRestartData(RestartData *resid, const int &cid){

	NcBool varbool;

	dsrV->set_cur(cid);
	varbool = dsrV->get(&resid->dsr,1);
	if(!varbool){
		string msg = "problem in reading 'DSR' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	firea2sorgnV->set_cur(cid);
	varbool = firea2sorgnV->get(&resid->firea2sorgn,1);
	if(!varbool){
		string msg = "problem in reading 'FIREA2SORGN' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	// - veg
	ysfV->set_cur(cid);
	varbool = ysfV->get(&resid->yrsdist,1);
	if(!varbool){
		string msg = "problem in reading 'YSF' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	ifwoodyV->set_cur(cid, 0);
	varbool = ifwoodyV->get(&resid->ifwoody[0], 1, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'IFWOODY' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	ifdeciwoodyV->set_cur(cid, 0);
	varbool = ifdeciwoodyV->get(&resid->ifdeciwoody[0], 1, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'IFDECIWOODY' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	ifperenialV->set_cur(cid, 0);
	varbool = ifperenialV->get(&resid->ifperenial[0], 1, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'IFPERENIAL' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	nonvascularV->set_cur(cid, 0);
	varbool = nonvascularV->get(&resid->nonvascular[0], 1, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'NONVASCULAR' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	vegageV->set_cur(cid, 0);
	varbool = vegageV->get(&resid->vegage[0], 1, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'VEGAGE' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	vegcovV->set_cur(cid, 0);
	varbool = vegcovV->get(&resid->vegcov[0], 1, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'VEGFRAC' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	laiV->set_cur(cid, 0);
	varbool = laiV->get(&resid->lai[0], 1, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'LAI' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	rootfracV->set_cur(cid, 0);
	varbool = rootfracV->get(&resid->rootfrac[0][0], 1, MAX_ROT_LAY, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'ROOTFRAC' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	vegwaterV->set_cur(cid, 0);
	varbool = vegwaterV->get(&resid->vegwater[0], 1, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'VEGWATER' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	vegsnowV->set_cur(cid, 0);
	varbool = vegsnowV->get(&resid->vegsnow[0], 1, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'VEGSNOW' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	vegcV->set_cur(cid, 0, 0);
	varbool = vegcV->get(&resid->vegc[0][0], 1, NUM_PFT_PART, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'VEGC' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	strnV->set_cur(cid, 0, 0);
	varbool = strnV->get(&resid->strn[0][0], 1, NUM_PFT_PART, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'STRN' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	labnV->set_cur(cid, 0);
	varbool = labnV->get(&resid->labn[0], 1, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'LABN' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	deadcV->set_cur(cid, 0);
	varbool = deadcV->get(&resid->deadc[0], 1, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'DEADC' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	deadnV->set_cur(cid, 0);
	varbool = deadnV->get(&resid->deadn[0], 1, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'DEADN' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	toptV->set_cur(cid, 0);
	varbool = toptV->get(&resid->topt[0], 1, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'TOPT' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	eetmxV->set_cur(cid, 0);
	varbool = eetmxV->get(&resid->eetmx[0], 1, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'EETMX' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	growingttimeV->set_cur(cid, 0);
	varbool = growingttimeV->get(&resid->growingttime[0], 1, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'GROWINGTTIME' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	unnormleafmxV->set_cur(cid, 0);
	varbool = unnormleafmxV->get(&resid->unnormleafmx[0], 1, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'UNNORMLEAFMX' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	toptAV->set_cur(cid, 0, 0);
	varbool = toptAV->get(&resid->toptA[0][0], 1, 10, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'TOPTA' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	eetmxAV->set_cur(cid, 0, 0);
	varbool = eetmxAV->get(&resid->eetmxA[0][0], 1, 10, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'EETMXA' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	growingttimeAV->set_cur(cid, 0, 0);
	varbool = growingttimeAV->get(&resid->growingttimeA[0][0], 1, 10, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'GROWINGTTIMEA' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	unnormleafmxAV->set_cur(cid, 0, 0);
	varbool = unnormleafmxAV->get(&resid->unnormleafmxA[0][0], 1, 10, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'UNNORMLEAFMXA' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	foliagemxV->set_cur(cid, 0);
	varbool = foliagemxV->get(&resid->foliagemx[0], 1, NUM_PFT);
	if(!varbool){
		string msg = "problem in reading 'FOLIAGEMX' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

    //snow
	numsnwlV->set_cur(cid);
	varbool = numsnwlV->get(&resid->numsnwl,1);
	if(!varbool){
		string msg = "problem in reading 'NUMSNWL' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	snwextramassV->set_cur(cid);
	varbool = snwextramassV->get(&resid->snwextramass,1);
	if(!varbool){
		string msg = "problem in reading 'SNWEXTRAMASS' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	TSsnowV->set_cur(cid, 0);
	varbool = TSsnowV->get(&resid->TSsnow[0], 1, MAX_SNW_LAY);
	if(!varbool){
		string msg = "problem in reading 'TSsnow' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	DZsnowV->set_cur(cid, 0);
	varbool = DZsnowV->get(&resid->DZsnow[0], 1, MAX_SNW_LAY);
	if(!varbool){
		string msg = "problem in reading 'DZsnow' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	LIQsnowV->set_cur(cid, 0);
	varbool = LIQsnowV->get(&resid->LIQsnow[0], 1, MAX_SNW_LAY);
	if(!varbool){
		string msg = "problem in reading 'LIQsnow' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	ICEsnowV->set_cur(cid, 0);
	varbool = ICEsnowV->get(&resid->ICEsnow[0], 1, MAX_SNW_LAY);
	if(!varbool){
		string msg = "problem in reading 'ICEsnow' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	AGEsnowV->set_cur(cid, 0);
	varbool = AGEsnowV->get(&resid->AGEsnow[0], 1, MAX_SNW_LAY);
	if(!varbool){
		string msg = "problem in reading 'AGEsnow' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	RHOsnowV->set_cur(cid, 0);
	varbool = RHOsnowV->get(&resid->RHOsnow[0], 1, MAX_SNW_LAY);
	if(!varbool){
		string msg = "problem in reading 'RHOsnow' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

    //ground-soil
	numslV->set_cur(cid);
	varbool = numslV->get(&resid->numsl, 1);
	if(!varbool){
		string msg = "problem in reading 'NUMSL' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	monthsfrozenV->set_cur(cid);
	varbool = monthsfrozenV->get(&resid->monthsfrozen, 1);
	if(!varbool){
		string msg = "problem in reading 'MONTHSFROZEN' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	rtfrozendaysV->set_cur(cid);
	varbool = rtfrozendaysV->get(&resid->rtfrozendays, 1);
	if(!varbool){
		string msg = "problem in reading 'RTFROZENDAYS' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	rtunfrozendaysV->set_cur(cid);
	varbool = rtunfrozendaysV->get(&resid->rtunfrozendays,1);
	if(!varbool){
		string msg = "problem in reading 'RTUNFROZENDAYS' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	watertabV->set_cur(cid);
	varbool = watertabV->get(&resid->watertab,1);
	if(!varbool){
		string msg = "problem in reading 'WATERTAB' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	DZsoilV->set_cur(cid, 0);
	varbool = DZsoilV->get(&resid->DZsoil[0], 1, MAX_SOI_LAY);
	if(!varbool){
		string msg = "problem in reading 'DZsoil' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	AGEsoilV->set_cur(cid, 0);
	varbool = AGEsoilV->get(&resid->AGEsoil[0], 1, MAX_SOI_LAY);
	if(!varbool){
		string msg = "problem in reading 'AGEsoil' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	TYPEsoilV->set_cur(cid, 0);
	varbool = TYPEsoilV->get(&resid->TYPEsoil[0], 1, MAX_SOI_LAY);
	if(!varbool){
		string msg = "problem in reading 'TYPEsoil' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	TSsoilV->set_cur(cid, 0);
	varbool = TSsoilV->get(&resid->TSsoil[0], 1, MAX_SOI_LAY);
	if(!varbool){
		string msg = "problem in reading 'TSsoil' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	LIQsoilV->set_cur(cid, 0);
	varbool = LIQsoilV->get(&resid->LIQsoil[0], 1, MAX_SOI_LAY);
	if(!varbool){
		string msg = "problem in reading 'LIQsoil' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	ICEsoilV->set_cur(cid, 0);
	varbool = ICEsoilV->get(&resid->ICEsoil[0], 1, MAX_SOI_LAY);
	if(!varbool){
		string msg = "problem in reading 'ICEsoil' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	FROZENsoilV->set_cur(cid, 0);
	varbool = FROZENsoilV->get(&resid->FROZENsoil[0], 1, MAX_SOI_LAY);
	if(!varbool){
		string msg = "problem in reading 'FROZENsoil' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	FROZENFRACsoilV->set_cur(cid, 0);
	varbool = FROZENFRACsoilV->get(&resid->FROZENFRACsoil[0], 1, MAX_SOI_LAY);
	if(!varbool){
		string msg = "problem in reading 'FROZENFRACsoil' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	TEXTUREsoilV->set_cur(cid, 0);
	varbool = TEXTUREsoilV->get(&resid->TEXTUREsoil[0], 1, MAX_SOI_LAY);
	if(!varbool){
		string msg = "problem in reading 'TEXTUREsoil' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	TSrockV->set_cur(cid, 0);
	varbool = TSrockV->get(&resid->TSrock[0], 1, MAX_ROC_LAY);
	if(!varbool){
		string msg = "problem in reading 'TSrock' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	DZrockV->set_cur(cid, 0);
	varbool = DZrockV->get(&resid->DZrock[0], 1, MAX_ROC_LAY);
	if(!varbool){
		string msg = "problem in reading 'DZrock' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	frontZV->set_cur(cid, 0);
	varbool = frontZV->get(&resid->frontZ[0], 1, MAX_NUM_FNT);
	if(!varbool){
		string msg = "problem in reading 'frontZ' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	frontFTV->set_cur(cid, 0);
	varbool = frontFTV->get(&resid->frontFT[0], 1, MAX_NUM_FNT);
	if(!varbool){
		string msg = "problem in reading 'frontFT' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	wdebriscV->set_cur(cid);
	varbool = wdebriscV->get(&resid->wdebrisc,1);
	if(!varbool){
		string msg = "problem in reading 'WDEBRISC' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	wdebrisnV->set_cur(cid);
	varbool = wdebrisnV->get(&resid->wdebrisn,1);
	if(!varbool){
		string msg = "problem in reading 'WDEBRISN' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	dmosscV->set_cur(cid);
	varbool = dmosscV->get(&resid->dmossc,1);
	if(!varbool){
		string msg = "problem in reading 'DMOSSC' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	dmossnV->set_cur(cid);
	varbool = dmossnV->get(&resid->dmossn,1);
	if(!varbool){
		string msg = "problem in reading 'DMOSSN' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	rawcV->set_cur(cid, 0);
	varbool = rawcV->get(&resid->rawc[0], 1, MAX_SOI_LAY);
	if(!varbool){
		string msg = "problem in reading 'RAWC' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	somaV->set_cur(cid, 0);
	varbool = somaV->get(&resid->soma[0], 1, MAX_SOI_LAY);
	if(!varbool){
		string msg = "problem in reading 'SOMA' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	somprV->set_cur(cid, 0);
	varbool = somprV->get(&resid->sompr[0], 1, MAX_SOI_LAY);
	if(!varbool){
		string msg = "problem in reading 'SOMPR' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	somcrV->set_cur(cid, 0);
	varbool = somcrV->get(&resid->somcr[0], 1, MAX_SOI_LAY);
	if(!varbool){
		string msg = "problem in reading 'SOMCR' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	solnV->set_cur(cid, 0);
	varbool = solnV->get(&resid->orgn[0], 1, MAX_SOI_LAY);
	if(!varbool){
		string msg = "problem in reading 'SOLN' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	avlnV->set_cur(cid, 0);
	varbool = avlnV->get(&resid->avln[0], 1, MAX_SOI_LAY);
	if(!varbool){
		string msg = "problem in reading 'AVLN' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

	prvltrfcnAV->set_cur(cid, 0, 0);
	varbool = prvltrfcnAV->get(&resid->prvltrfcnA[0][0], 1, 12, MAX_SOI_LAY);
	if(!varbool){
		string msg = "problem in reading 'PRVLTRFCNA' in RestartInputer";
 		cout<<msg+"\n";
 		exit(-1);
	}

}

