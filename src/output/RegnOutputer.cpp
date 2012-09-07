/*
 * This class is for output variables in TEM regional run
 * in netcdf format
 * 
*/

#include "RegnOutputer.h"

RegnOutputer::RegnOutputer(){
	 
};

RegnOutputer::~RegnOutputer(){
 	if(rFile!=NULL){
    	rFile->close();
		delete rFile;
 	}

};

void RegnOutputer::outputCohortMissing(const int & yrind, const int & chtcount){
	regnod->year = MISSING_I;
	regnod->ysf  = MISSING_I;
  	for(int im=0; im<12; im++){

		regnod->month[im]= MISSING_I;

   		for (int ip=0; ip<NUM_PFT; ip++){
   			regnod->growstart[im][ip] = MISSING_I;
			regnod->growend[im][ip]   = MISSING_I;

			regnod->vegcov[im][ip]= MISSING_D;
			regnod->vegage[im][ip] = MISSING_D;
			regnod->lai[im][ip]  = MISSING_D;
			regnod->vegc[im][ip] = MISSING_D;
			regnod->leafc[im][ip]= MISSING_D;
			regnod->stemc[im][ip]= MISSING_D;
			regnod->rootc[im][ip]= MISSING_D;
			regnod->vegn[im][ip] = MISSING_D;
			regnod->labn[im][ip] = MISSING_D;
			regnod->leafn[im][ip]= MISSING_D;
			regnod->stemn[im][ip]= MISSING_D;
			regnod->rootn[im][ip]= MISSING_D;

			regnod->gpp[im][ip] = MISSING_D;
			regnod->npp[im][ip] = MISSING_D;
			regnod->ltrfalc[im][ip]= MISSING_D;
			regnod->ltrfaln[im][ip]= MISSING_D;

			regnod->nuptake[im][ip]= MISSING_D;
		}
        //
   		regnod->permafrost[im]= MISSING_I;

   		regnod->mossdz[im]  = MISSING_D;
   		regnod->oshlwdz[im] = MISSING_D;
   		regnod->odeepdz[im] = MISSING_D;
   		regnod->mineadz[im] = MISSING_D;
   		regnod->minebdz[im] = MISSING_D;
   		regnod->minecdz[im] = MISSING_D;

   		regnod->oshlwc[im] = MISSING_D;
   		regnod->odeepc[im] = MISSING_D;
   		regnod->mineac[im] = MISSING_D;
   		regnod->minebc[im] = MISSING_D;
   		regnod->minecc[im] = MISSING_D;
   		regnod->orgn[im]   = MISSING_D;
   		regnod->avln[im]   = MISSING_D;

		regnod->rh[im]      = MISSING_D;
   		regnod->netnmin[im] = MISSING_D;

      	regnod->orgninput[im]= MISSING_D;
      	regnod->avlninput[im]= MISSING_D;
      	regnod->orgnlost[im]= MISSING_D;
      	regnod->avlnlost[im]= MISSING_D;
      	regnod->doclost[im]= MISSING_D;

      	//
      	regnod->eet[im]= MISSING_D;
   		regnod->pet[im]= MISSING_D;
   		regnod->qinfl[im]  = MISSING_D;
   		regnod->qdrain[im] = MISSING_D;
      	regnod->qrunoff[im]= MISSING_D;

      	regnod->snwthick[im]= MISSING_D;
      	regnod->swe[im]= MISSING_D;

   		regnod->wtd[im]= MISSING_D;
   		regnod->alc[im]= MISSING_D;
      	regnod->ald[im]= MISSING_D;

   		regnod->vwcshlw[im]= MISSING_D;
   		regnod->vwcdeep[im]= MISSING_D;
   		regnod->vwcminea[im]= MISSING_D;
      	regnod->vwcmineb[im]= MISSING_D;
      	regnod->vwcminec[im]= MISSING_D;

   		regnod->tshlw[im]= MISSING_D;
   		regnod->tdeep[im]= MISSING_D;
   		regnod->tminea[im]= MISSING_D;
   		regnod->tmineb[im]= MISSING_D;
   		regnod->tminec[im]= MISSING_D;

   		regnod->hkshlw[im]= MISSING_D;
   		regnod->hkdeep[im]= MISSING_D;
   		regnod->hkminea[im]= MISSING_D;
   		regnod->hkmineb[im]= MISSING_D;
   		regnod->hkminec[im]= MISSING_D;

   		regnod->tcshlw[im]= MISSING_D;
   		regnod->tcdeep[im]= MISSING_D;
   		regnod->tcminea[im]= MISSING_D;
   		regnod->tcmineb[im]= MISSING_D;
   		regnod->tcminec[im]= MISSING_D;

   		regnod->tbotrock[im]= MISSING_D;

   		//
   		regnod->burnthick[im]= MISSING_D;
   		regnod->burnsoic[im]= MISSING_D;
   		regnod->burnvegc[im]= MISSING_D;

  	}

  	outputCohortVars(yrind, chtcount, MISSING_I);
  	
};

void RegnOutputer::init(string& outputdir, string & stage, int MAX_YRSTEP){

	string moncfn =outputdir+"output"+stage+".nc";

	rFile = new NcFile(moncfn.c_str(), NcFile::Replace);
	
	NcDim * chtD  = rFile->add_dim("CHTID");
	NcDim * yearD = rFile->add_dim("YEAR", MAX_YRSTEP);
	NcDim * yrmonD= rFile->add_dim("YYYYMM", MAX_YRSTEP*12);
	NcDim * pftD  = rFile->add_dim("PFTS", NUM_PFT);

 	chtidV = rFile->add_var("CHTID", ncInt, chtD);
  	statusV= rFile->add_var("STATUS", ncInt, chtD, yearD);
	yearV  = rFile->add_var("YEAR", ncInt, yearD);
	yrmonV = rFile->add_var("YYYYMM", ncInt, yrmonD);
	ysfV   = rFile->add_var("YSF", ncInt, yearD);

/////////////////* YEARLY outputs *//////////////////////////////////////////////
	//
   	if (regnod->outvarlist[I_growstart]==1)
   		growstartV = rFile->add_var("GROWSTART", ncInt, chtD, yearD, pftD);
   	if (regnod->outvarlist[I_growend]==1)
   		growendV   = rFile->add_var("GROWEND", ncInt, chtD, yearD, pftD);

   	if (regnod->outvarlist[I_vegcov]==1)
   		vegcovV   = rFile->add_var("VEGCOV", ncDouble, chtD, yearD, pftD);
   	if (regnod->outvarlist[I_vegage]==1)
   		vegageV    = rFile->add_var("VEGAGE", ncInt, chtD, yearD, pftD);

   	if (regnod->outvarlist[I_lai]==1)
   		laiV       = rFile->add_var("LAI", ncDouble, chtD, yearD, pftD);
   	if (regnod->outvarlist[I_vegc]==1)
   		vegcV      = rFile->add_var("VEGC", ncDouble, chtD, yearD, pftD);
   	if (regnod->outvarlist[I_leafc]==1)
   		leafcV     = rFile->add_var("LEAFC", ncDouble, chtD, yearD, pftD);
   	if (regnod->outvarlist[I_stemc]==1)
   		stemcV     = rFile->add_var("STEMC", ncDouble, chtD, yearD, pftD);
   	if (regnod->outvarlist[I_rootc]==1)
   		rootcV     = rFile->add_var("ROOTC", ncDouble, chtD, yearD, pftD);
   	if (regnod->outvarlist[I_vegn]==1)
   		vegnV      = rFile->add_var("VEGN", ncDouble, chtD, yearD, pftD);
   	if (regnod->outvarlist[I_labn]==1)
   		labnV      = rFile->add_var("LABN", ncDouble, chtD, yearD, pftD);
   	if (regnod->outvarlist[I_leafn]==1)
   		leafnV     = rFile->add_var("LEAFN", ncDouble, chtD, yearD, pftD);
   	if (regnod->outvarlist[I_stemn]==1)
   		stemnV     = rFile->add_var("STEMN", ncDouble, chtD, yearD, pftD);
   	if (regnod->outvarlist[I_rootn]==1)
   		rootnV     = rFile->add_var("ROOTN", ncDouble, chtD, yearD, pftD);

   	if (regnod->outvarlist[I_gpp]==1)
   		gppV       = rFile->add_var("GPP", ncDouble, chtD, yearD, pftD);
   	if (regnod->outvarlist[I_npp]==1)
   		nppV       = rFile->add_var("NPP", ncDouble, chtD, yearD, pftD);
   	if (regnod->outvarlist[I_ltrfalc]==1)
        ltrfalcV   = rFile->add_var("LTRFALC", ncDouble, chtD, yearD, pftD);
   	if (regnod->outvarlist[I_ltrfaln]==1)
        ltrfalnV   = rFile->add_var("LTRFALN", ncDouble, chtD, yearD, pftD);

   	if (regnod->outvarlist[I_nuptake]==1)
        nuptakeV   = rFile->add_var("NUPTAKE", ncDouble, chtD, yearD, pftD);

        //
   	if (regnod->outvarlist[I_permafrost]==1)
   		permafrostV = rFile->add_var("PERMAFROST", ncInt, chtD, yearD);

   	if (regnod->outvarlist[I_mossdz]==1)
   		mossdzV  = rFile->add_var("MOSSDZ", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_oshlwdz]==1)
   		oshlwdzV = rFile->add_var("OSHLWDZ", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_odeepdz]==1)
   		odeepdzV = rFile->add_var("ODEEPDZ", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_mineadz]==1)
   		mineadzV = rFile->add_var("MINEADZ", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_minebdz]==1)
   		minebdzV = rFile->add_var("MINEBDZ", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_minecdz]==1)
   		minecdzV = rFile->add_var("MINECDZ", ncDouble, chtD, yearD);

   	if (regnod->outvarlist[I_oshlwc]==1)
   		oshlwcV  = rFile->add_var("OSHLWC", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_odeepc]==1)
   		odeepcV  = rFile->add_var("ODEEPC", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_mineac]==1)
   		mineacV  = rFile->add_var("MINEAC", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_minebc]==1)
   		minebcV  = rFile->add_var("MINEBC", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_minecc]==1)
   		mineccV  = rFile->add_var("MINECC", ncDouble, chtD, yearD);

   	if (regnod->outvarlist[I_orgn]==1)
   		orgnV    = rFile->add_var("ORGN", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_avln]==1)
   		avlnV    = rFile->add_var("AVLN", ncDouble, chtD, yearD);

   	if (regnod->outvarlist[I_rh]==1)
   		rhV        = rFile->add_var("RH", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_netnmin]==1)
   		netnminV = rFile->add_var("NETNMIN", ncDouble, chtD, yearD);

   	if (regnod->outvarlist[I_orgninput]==1)
   		orgninputV = rFile->add_var("ORGNINPUT", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_avlninput]==1)
   		avlninputV = rFile->add_var("AVLNINPUT", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_orgnlost]==1)
      	orgnlostV  = rFile->add_var("ORGNLOST", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_avlnlost]==1)
      	avlnlostV  = rFile->add_var("ALVNLOST", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_doclost]==1)
      	doclostV   = rFile->add_var("dOCLOST", ncDouble, chtD, yearD);

      	//
   	if (regnod->outvarlist[I_eet]==1)
      	eetV   = rFile->add_var("EET", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_pet]==1)
   		petV   = rFile->add_var("PET", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_qinfl]==1)
   		qinflV = rFile->add_var("QINFL", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_qdrain]==1)
   		qdrainV = rFile->add_var("QDRAIN", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_qrunoff]==1)
      	qrunoffV= rFile->add_var("QRUNOFF", ncDouble, chtD, yearD);

   	if (regnod->outvarlist[I_snwthick]==1)
      	snwthickV=rFile->add_var("SNWTHICK", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_swe]==1)
      	sweV=rFile->add_var("SWE", ncDouble, chtD, yearD);

   	if (regnod->outvarlist[I_wtd]==1)
   		wtdV=rFile->add_var("WTD", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_alc]==1)
   		alcV=rFile->add_var("ALC", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_ald]==1)
      	aldV=rFile->add_var("ALD", ncDouble, chtD, yearD);

   	if (regnod->outvarlist[I_vwcshlw]==1)
   		vwcshlwV=rFile->add_var("VWCSHLW", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_vwcdeep]==1)
   		vwcdeepV=rFile->add_var("VWCDEEP", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_vwcminea]==1)
   		vwcmineaV=rFile->add_var("VWCMINEA", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_vwcmineb]==1)
      	vwcminebV=rFile->add_var("VWCMINEB", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_vwcminec]==1)
      	vwcminecV=rFile->add_var("VWCMINEC", ncDouble, chtD, yearD);

   	if (regnod->outvarlist[I_tshlw]==1)
   		tshlwV=rFile->add_var("TSHLW", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_tdeep]==1)
   		tdeepV=rFile->add_var("TDEEP", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_tminea]==1)
   		tmineaV=rFile->add_var("TMINEA", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_tmineb]==1)
   		tminebV=rFile->add_var("TMINEB", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_tminec]==1)
   		tminecV=rFile->add_var("TMINEC", ncDouble, chtD, yearD);

   	if (regnod->outvarlist[I_hkshlw]==1)
   		hkshlwV=rFile->add_var("HKSHLW", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_hkdeep]==1)
   		hkdeepV=rFile->add_var("HKDEEP", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_hkminea]==1)
   		hkmineaV=rFile->add_var("HKMINEA", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_hkmineb]==1)
   		hkminebV=rFile->add_var("HKMINEB", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_hkminec]==1)
   		hkminecV=rFile->add_var("HKMINEC", ncDouble, chtD, yearD);

   	if (regnod->outvarlist[I_tcshlw]==1)
   		tcshlwV=rFile->add_var("TCSHLW", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_tcdeep]==1)
   		tcdeepV=rFile->add_var("TCDEEP", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_tcminea]==1)
   		tcmineaV=rFile->add_var("TCMINEA", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_tcmineb]==1)
   		tcminebV=rFile->add_var("TCMINEB", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_tcminec]==1)
   		tcminecV=rFile->add_var("TCMINEC", ncDouble, chtD, yearD);

   	if (regnod->outvarlist[I_tbotrock]==1)
   		tbotrockV=rFile->add_var("TBOTROCK", ncDouble, chtD, yearD);

   		//
   	if (regnod->outvarlist[I_burnthick]==1)
   		burnthickV=rFile->add_var("BURNTHICK", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_burnsoic]==1)
   		burnsoicV=rFile->add_var("BURNSOIC", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_burnvegc]==1)
   		burnvegcV=rFile->add_var("BURNVEGC", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_burnsoin]==1)
   		burnsoinV=rFile->add_var("BURNSOIN", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_burnvegn]==1)
   		burnvegnV=rFile->add_var("BURNVEGN", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_burnretainc]==1)
   		burnretaincV=rFile->add_var("BURNRETAINC", ncDouble, chtD, yearD);
   	if (regnod->outvarlist[I_burnretainn]==1)
   		burnretainnV=rFile->add_var("BURNRETAINN", ncDouble, chtD, yearD);

/////////////////* MONTHLY outputs *//////////////////////////////////////////////

	//
   	if (regnod->outvarlist[I_growstart]==2)
   		growstartV = rFile->add_var("GROWSTART", ncInt, chtD, yrmonD, pftD);
   	if (regnod->outvarlist[I_growend]==2)
   		growendV   = rFile->add_var("GROWEND", ncInt, chtD, yrmonD, pftD);

   	if (regnod->outvarlist[I_vegcov]==2)
   		vegcovV   = rFile->add_var("VEGFRAC", ncDouble, chtD, yrmonD, pftD);
   	if (regnod->outvarlist[I_vegage]==2)
   		vegageV    = rFile->add_var("VEGAGE", ncInt, chtD, yrmonD, pftD);

   	if (regnod->outvarlist[I_lai]==2)
   		laiV       = rFile->add_var("LAI", ncDouble, chtD, yrmonD, pftD);
   	if (regnod->outvarlist[I_vegc]==2)
   		vegcV      = rFile->add_var("VEGC", ncDouble, chtD, yrmonD, pftD);
   	if (regnod->outvarlist[I_leafc]==2)
   		leafcV     = rFile->add_var("LEAFC", ncDouble, chtD, yrmonD, pftD);
   	if (regnod->outvarlist[I_stemc]==2)
   		stemcV     = rFile->add_var("STEMC", ncDouble, chtD, yrmonD, pftD);
   	if (regnod->outvarlist[I_rootc]==2)
   		rootcV     = rFile->add_var("ROOTC", ncDouble, chtD, yrmonD, pftD);
   	if (regnod->outvarlist[I_vegn]==2)
   		vegnV      = rFile->add_var("VEGN", ncDouble, chtD, yrmonD, pftD);
   	if (regnod->outvarlist[I_labn]==2)
   		labnV      = rFile->add_var("LABN", ncDouble, chtD, yrmonD, pftD);
   	if (regnod->outvarlist[I_leafn]==2)
   		leafnV     = rFile->add_var("LEAFN", ncDouble, chtD, yrmonD, pftD);
   	if (regnod->outvarlist[I_stemn]==2)
   		stemnV     = rFile->add_var("STEMN", ncDouble, chtD, yrmonD, pftD);
   	if (regnod->outvarlist[I_rootn]==2)
   		rootnV     = rFile->add_var("ROOTN", ncDouble, chtD, yrmonD, pftD);

   	if (regnod->outvarlist[I_gpp]==2)
   		gppV       = rFile->add_var("GPP", ncDouble, chtD, yrmonD, pftD);
   	if (regnod->outvarlist[I_npp]==2)
   		nppV       = rFile->add_var("NPP", ncDouble, chtD, yrmonD, pftD);
   	if (regnod->outvarlist[I_ltrfalc]==2)
        ltrfalcV   = rFile->add_var("LTRFALC", ncDouble, chtD, yrmonD, pftD);
   	if (regnod->outvarlist[I_ltrfaln]==2)
        ltrfalnV   = rFile->add_var("LTRFALN", ncDouble, chtD, yrmonD, pftD);

   	if (regnod->outvarlist[I_nuptake]==2)
        nuptakeV   = rFile->add_var("NUPTAKE", ncDouble, chtD, yrmonD, pftD);

        //
   	if (regnod->outvarlist[I_permafrost]==2)
   		permafrostV = rFile->add_var("PERMAFROST", ncInt, chtD, yrmonD);

   	if (regnod->outvarlist[I_mossdz]==2)
   		mossdzV  = rFile->add_var("MOSSDZ", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_oshlwdz]==2)
   		oshlwdzV = rFile->add_var("OSHLWDZ", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_odeepdz]==2)
   		odeepdzV = rFile->add_var("ODEEPDZ", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_mineadz]==2)
   		mineadzV = rFile->add_var("MINEADZ", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_minebdz]==2)
   		minebdzV = rFile->add_var("MINEBDZ", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_minecdz]==2)
   		minecdzV = rFile->add_var("MINECDZ", ncDouble, chtD, yrmonD);

   	if (regnod->outvarlist[I_oshlwc]==2)
   		oshlwcV  = rFile->add_var("OSHLWC", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_odeepc]==2)
   		odeepcV  = rFile->add_var("ODEEPC", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_mineac]==2)
   		mineacV  = rFile->add_var("MINEAC", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_minebc]==2)
   		minebcV  = rFile->add_var("MINEBC", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_minecc]==2)
   		mineccV  = rFile->add_var("MINECC", ncDouble, chtD, yrmonD);

   	if (regnod->outvarlist[I_orgn]==2)
   		orgnV    = rFile->add_var("ORGN", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_avln]==2)
   		avlnV    = rFile->add_var("AVLN", ncDouble, chtD, yrmonD);

   	if (regnod->outvarlist[I_rh]==2)
   		rhV        = rFile->add_var("RH", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_netnmin]==2)
   		netnminV = rFile->add_var("NETNMIN", ncDouble, chtD, yrmonD);

   	if (regnod->outvarlist[I_orgninput]==2)
   		orgninputV = rFile->add_var("ORGNINPUT", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_avlninput]==2)
   		avlninputV = rFile->add_var("AVLNINPUT", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_orgnlost]==2)
      	orgnlostV  = rFile->add_var("ORGNLOST", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_avlnlost]==2)
      	avlnlostV  = rFile->add_var("ALVNLOST", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_doclost]==2)
      	doclostV   = rFile->add_var("dOCLOST", ncDouble, chtD, yrmonD);

      	//
   	if (regnod->outvarlist[I_eet]==2)
      	eetV   = rFile->add_var("EET", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_pet]==2)
   		petV   = rFile->add_var("PET", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_qinfl]==2)
   		qinflV = rFile->add_var("QINFL", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_qdrain]==2)
   		qdrainV = rFile->add_var("QDRAIN", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_qrunoff]==2)
      	qrunoffV= rFile->add_var("QRUNOFF", ncDouble, chtD, yrmonD);

   	if (regnod->outvarlist[I_snwthick]==2)
      	snwthickV=rFile->add_var("SNWTHICK", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_swe]==2)
      	sweV=rFile->add_var("SWE", ncDouble, chtD, yrmonD);

   	if (regnod->outvarlist[I_wtd]==2)
   		wtdV=rFile->add_var("WTD", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_alc]==2)
   		alcV=rFile->add_var("ALC", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_ald]==2)
      	aldV=rFile->add_var("ALD", ncDouble, chtD, yrmonD);

   	if (regnod->outvarlist[I_vwcshlw]==2)
   		vwcshlwV=rFile->add_var("VWCSHLW", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_vwcdeep]==2)
   		vwcdeepV=rFile->add_var("VWCDEEP", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_vwcminea]==2)
   		vwcmineaV=rFile->add_var("VWCMINEA", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_vwcmineb]==2)
      	vwcminebV=rFile->add_var("VWCMINEB", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_vwcminec]==2)
      	vwcminecV=rFile->add_var("VWCMINEC", ncDouble, chtD, yrmonD);

   	if (regnod->outvarlist[I_tshlw]==2)
   		tshlwV=rFile->add_var("TSHLW", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_tdeep]==2)
   		tdeepV=rFile->add_var("TDEEP", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_tminea]==2)
   		tmineaV=rFile->add_var("TMINEA", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_tmineb]==2)
   		tminebV=rFile->add_var("TMINEB", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_tminec]==2)
   		tminecV=rFile->add_var("TMINEC", ncDouble, chtD, yrmonD);

   	if (regnod->outvarlist[I_hkshlw]==2)
   		hkshlwV=rFile->add_var("HKSHLW", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_hkdeep]==2)
   		hkdeepV=rFile->add_var("HKDEEP", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_hkminea]==2)
   		hkmineaV=rFile->add_var("HKMINEA", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_hkmineb]==2)
   		hkminebV=rFile->add_var("HKMINEB", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_hkminec]==2)
   		hkminecV=rFile->add_var("HKMINEC", ncDouble, chtD, yrmonD);

   	if (regnod->outvarlist[I_tcshlw]==2)
   		tcshlwV=rFile->add_var("TCSHLW", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_tcdeep]==2)
   		tcdeepV=rFile->add_var("TCDEEP", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_tcminea]==2)
   		tcmineaV=rFile->add_var("TCMINEA", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_tcmineb]==2)
   		tcminebV=rFile->add_var("TCMINEB", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_tcminec]==2)
   		tcminecV=rFile->add_var("TCMINEC", ncDouble, chtD, yrmonD);

   	if (regnod->outvarlist[I_tbotrock]==2)
   		tbotrockV=rFile->add_var("TBOTROCK", ncDouble, chtD, yrmonD);

   		//
   	if (regnod->outvarlist[I_burnthick]==2)
   		burnthickV=rFile->add_var("BURNTHICK", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_burnsoic]==2)
   		burnsoicV=rFile->add_var("BURNSOIC", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_burnvegc]==2)
   		burnvegcV=rFile->add_var("BURNVEGC", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_burnsoin]==2)
   		burnsoinV=rFile->add_var("BURNSOIN", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_burnvegn]==2)
   		burnvegnV=rFile->add_var("BURNVEGN", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_burnretainc]==2)
   		burnretaincV=rFile->add_var("BURNRETAINC", ncDouble, chtD, yrmonD);
   	if (regnod->outvarlist[I_burnretainn]==2)
   		burnretainnV=rFile->add_var("BURNRETAINN", ncDouble, chtD, yrmonD);

};

void RegnOutputer::outputCohortVars(const int & yrind, const int & chtcount, const int & status){
 
   	chtidV->set_cur(chtcount);
   	chtidV->put(&regnod->chtid, 1);

   	statusV->set_cur(chtcount, yrind);
   	statusV->put(&status, 1, 1);

   	ysfV->set_cur(chtcount, yrind);
   	ysfV->put(&regnod->ysf, 1, 1);

   	yearV->set_cur(chtcount, yrind);
   	yearV->put(&regnod->year, 1, 1);

   	yrmonV->set_cur(chtcount, yrind);
   	yrmonV->put(&regnod->month[0], 1, 12);

/////// YEARLY OUTPUT /////////////////////////////////////////////////////////////////
   	if (regnod->outvarlist[I_growstart]==1){
   	   	growstartV->set_cur(chtcount, yrind);
		growstartV->put(&regnod->growstart[0][0], 1, 1, NUM_PFT);
   	}

   	if (regnod->outvarlist[I_growend]==1){
   	   	growendV->set_cur(chtcount, yrind);
		growendV->put(&regnod->growend[0][0], 1, 1, NUM_PFT);
   	}

   	if (regnod->outvarlist[I_vegcov]==1){
   	   	vegcovV->set_cur(chtcount, yrind);
		vegcovV->put(&regnod->vegcov[0][0], 1, 1, NUM_PFT);
   	}

   	if (regnod->outvarlist[I_vegage]==1){
   	   	vegageV->set_cur(chtcount, yrind);
		vegageV->put(&regnod->vegage[0][0], 1, 1, NUM_PFT);
   	}

   	if (regnod->outvarlist[I_lai]==1){
   	   	laiV->set_cur(chtcount, yrind);
		laiV->put(&regnod->lai[0][0], 1, 1, NUM_PFT);
   	}

   	if (regnod->outvarlist[I_vegc]==1){
   	   	vegcV->set_cur(chtcount, yrind);
		vegcV->put(&regnod->vegc[0][0], 1, 1, NUM_PFT);
   	}

   	if (regnod->outvarlist[I_leafc]==1){
   	   	leafcV->set_cur(chtcount, yrind);
		leafcV->put(&regnod->leafc[0][0], 1, 1, NUM_PFT);
   	}

   	if (regnod->outvarlist[I_stemc]==1){
   	   	stemcV->set_cur(chtcount, yrind);
		stemcV->put(&regnod->stemc[0][0], 1, 1, NUM_PFT);
   	}

   	if (regnod->outvarlist[I_rootc]==1){
   	   	rootcV->set_cur(chtcount, yrind);
		rootcV->put(&regnod->rootc[0][0], 1, 1, NUM_PFT);
   	}

   	if (regnod->outvarlist[I_vegn]==1){
   	   	vegnV->set_cur(chtcount, yrind);
		vegnV->put(&regnod->vegn[0][0], 1, 1, NUM_PFT);
   	}

   	if (regnod->outvarlist[I_labn]==1){
   	   	labnV->set_cur(chtcount, yrind);
		labnV->put(&regnod->labn[0][0], 1, 1, NUM_PFT);
   	}

   	if (regnod->outvarlist[I_leafn]==1){
   	   	leafnV->set_cur(chtcount, yrind);
		leafnV->put(&regnod->leafn[0][0], 1, 1, NUM_PFT);
   	}

   	if (regnod->outvarlist[I_stemn]==1){
   	   	stemnV->set_cur(chtcount, yrind);
		stemnV->put(&regnod->stemn[0][0], 1, 1, NUM_PFT);
   	}

   	if (regnod->outvarlist[I_rootn]==1){
   	   	rootnV->set_cur(chtcount, yrind);
		rootnV->put(&regnod->rootn[0][0], 1, 1, NUM_PFT);
   	}

   	if (regnod->outvarlist[I_gpp]==1){
   	   	gppV->set_cur(chtcount, yrind);
		gppV->put(&regnod->gpp[0][0], 1, 1, NUM_PFT);
   	}

   	if (regnod->outvarlist[I_npp]==1){
   	   	nppV->set_cur(chtcount, yrind);
		nppV->put(&regnod->npp[0][0], 1, 1, NUM_PFT);
   	}

   	if (regnod->outvarlist[I_ltrfalc]==1){
   	   	ltrfalcV->set_cur(chtcount, yrind);
   	   	ltrfalcV->put(&regnod->ltrfalc[0][0], 1, 1, NUM_PFT);
   	}

   	if (regnod->outvarlist[I_ltrfaln]==1){
   	   	ltrfalnV->set_cur(chtcount, yrind);
   	   	ltrfalnV->put(&regnod->ltrfaln[0][0], 1, 1, NUM_PFT);
   	}

   	if (regnod->outvarlist[I_nuptake]==1){
   	   	nuptakeV->set_cur(chtcount, yrind);
   	   	nuptakeV->put(&regnod->nuptake[0][0], 1, 1, NUM_PFT);
   	}

   	//
   	if (regnod->outvarlist[I_permafrost]==1){
   	   	permafrostV->set_cur(chtcount, yrind);
		permafrostV->put(&regnod->permafrost[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_mossdz]==1){
   	   	mossdzV->set_cur(chtcount, yrind);
		mossdzV->put(&regnod->mossdz[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_oshlwdz]==1){
   	   	oshlwdzV->set_cur(chtcount, yrind);
		oshlwdzV->put(&regnod->oshlwdz[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_odeepdz]==1){
   	   	odeepdzV->set_cur(chtcount, yrind);
		odeepdzV->put(&regnod->odeepdz[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_mineadz]==1){
   	   	mineadzV->set_cur(chtcount, yrind);
		mineadzV->put(&regnod->mineadz[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_minebdz]==1){
   	   	minebdzV->set_cur(chtcount, yrind);
		minebdzV->put(&regnod->minebdz[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_minecdz]==1){
   	   	minecdzV->set_cur(chtcount, yrind);
		minecdzV->put(&regnod->minecdz[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_oshlwc]==1){
   	   	oshlwcV->set_cur(chtcount, yrind);
		oshlwcV->put(&regnod->oshlwc[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_odeepc]==1){
   	   	odeepcV->set_cur(chtcount, yrind);
		odeepcV->put(&regnod->odeepc[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_mineac]==1){
   	   	mineacV->set_cur(chtcount, yrind);
		mineacV->put(&regnod->mineac[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_minebc]==1){
   	   	minebcV->set_cur(chtcount, yrind);
		minebcV->put(&regnod->minebc[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_minecc]==1){
   	   	mineccV->set_cur(chtcount, yrind);
		mineccV->put(&regnod->minecc[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_orgn]==1){
   	   	orgnV->set_cur(chtcount, yrind);
		orgnV->put(&regnod->orgn[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_avln]==1){
   	   	avlnV->set_cur(chtcount, yrind);
		avlnV->put(&regnod->avln[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_rh]==1){
   	   	rhV->set_cur(chtcount, yrind);
		rhV->put(&regnod->rh[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_netnmin]==1){
   	   	netnminV->set_cur(chtcount, yrind);
		netnminV->put(&regnod->netnmin[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_orgninput]==1){
   	   	orgninputV->set_cur(chtcount, yrind);
   	   	orgninputV->put(&regnod->orgninput[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_avlninput]==1){
   	   	avlninputV->set_cur(chtcount, yrind);
		avlninputV->put(&regnod->avlninput[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_orgnlost]==1){
   	   	orgnlostV->set_cur(chtcount, yrind);
		orgnlostV->put(&regnod->orgnlost[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_avlnlost]==1){
   	   	avlnlostV->set_cur(chtcount, yrind);
		avlnlostV->put(&regnod->avlnlost[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_doclost]==1){
   	   	doclostV->set_cur(chtcount, yrind);
   	   	doclostV->put(&regnod->doclost[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_eet]==1){
   	   	eetV->set_cur(chtcount, yrind);
   	   	eetV->put(&regnod->eet[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_pet]==1){
   	   	petV->set_cur(chtcount, yrind);
		petV->put(&regnod->pet[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_qinfl]==1){
   	   	qinflV->set_cur(chtcount, yrind);
		qinflV->put(&regnod->qinfl[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_qdrain]==1){
   	   	qdrainV->set_cur(chtcount, yrind);
		qdrainV->put(&regnod->qdrain[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_qrunoff]==1){
   	   	qrunoffV->set_cur(chtcount, yrind);
   	   	qrunoffV->put(&regnod->qrunoff[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_snwthick]==1){
   	   	snwthickV->set_cur(chtcount, yrind);
   	   	snwthickV->put(&regnod->snwthick[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_swe]==1){
   	   	sweV->set_cur(chtcount, yrind);
   	   	sweV->put(&regnod->swe[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_wtd]==1){
   	   	wtdV->set_cur(chtcount, yrind);
		wtdV->put(&regnod->wtd[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_alc]==1){
   	   	alcV->set_cur(chtcount, yrind);
		alcV->put(&regnod->alc[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_ald]==1){
   	   	aldV->set_cur(chtcount, yrind);
   	   	aldV->put(&regnod->ald[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_vwcshlw]==1){
   	   	vwcshlwV->set_cur(chtcount, yrind);
		vwcshlwV->put(&regnod->vwcshlw[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_vwcdeep]==1){
   	   	vwcdeepV->set_cur(chtcount, yrind);
		vwcdeepV->put(&regnod->vwcdeep[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_vwcminea]==1){
   	   	vwcmineaV->set_cur(chtcount, yrind);
		vwcmineaV->put(&regnod->vwcminea[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_vwcmineb]==1){
   	   	vwcminebV->set_cur(chtcount, yrind);
   	   	vwcminebV->put(&regnod->vwcmineb[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_vwcminec]==1){
   	   	vwcminecV->set_cur(chtcount, yrind);
   	   	vwcminecV->put(&regnod->vwcminec[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_tshlw]==1){
   	   	tshlwV->set_cur(chtcount, yrind);
		tshlwV->put(&regnod->tshlw[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_tdeep]==1){
   	   	tdeepV->set_cur(chtcount, yrind);
		tdeepV->put(&regnod->tdeep[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_tminea]==1){
   	   	tmineaV->set_cur(chtcount, yrind);
		tmineaV->put(&regnod->tminea[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_tmineb]==1){
   	   	tminebV->set_cur(chtcount, yrind);
		tminebV->put(&regnod->tmineb[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_tminec]==1){
   	   	tminecV->set_cur(chtcount, yrind);
		tminecV->put(&regnod->tminec[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_hkshlw]==1){
   	   	hkshlwV->set_cur(chtcount, yrind);
		hkshlwV->put(&regnod->hkshlw[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_hkdeep]==1){
   	   	hkdeepV->set_cur(chtcount, yrind);
		hkdeepV->put(&regnod->hkdeep[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_hkminea]==1){
   	   	hkmineaV->set_cur(chtcount, yrind);
		hkmineaV->put(&regnod->hkminea[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_hkmineb]==1){
   	   	hkminebV->set_cur(chtcount, yrind);
		hkminebV->put(&regnod->hkmineb[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_hkminec]==1){
   	   	hkminecV->set_cur(chtcount, yrind);
		hkminecV->put(&regnod->hkminec[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_tcshlw]==1){
   	   	tcshlwV->set_cur(chtcount, yrind);
		tcshlwV->put(&regnod->tcshlw[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_tcdeep]==1){
   	   	tcdeepV->set_cur(chtcount, yrind);
		tcdeepV->put(&regnod->tcdeep[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_tcminea]==1){
   	   	tcmineaV->set_cur(chtcount, yrind);
		tcmineaV->put(&regnod->tcminea[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_tcmineb]==1){
   	   	tcminebV->set_cur(chtcount, yrind);
		tcminebV->put(&regnod->tcmineb[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_tcminec]==1){
   	   	tcminecV->set_cur(chtcount, yrind);
		tcminecV->put(&regnod->tcminec[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_tbotrock]==1){
   	   	tbotrockV->set_cur(chtcount, yrind);
		tbotrockV->put(&regnod->tbotrock[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_burnthick]==1){
   	   	burnthickV->set_cur(chtcount, yrind);
		burnthickV->put(&regnod->burnthick[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_burnsoic]==1){
   	   	burnsoicV->set_cur(chtcount, yrind);
		burnsoicV->put(&regnod->burnsoic[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_burnvegc]==1){
   	   	burnvegcV->set_cur(chtcount, yrind);
		burnvegcV->put(&regnod->burnvegc[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_burnsoin]==1){
   	   	burnsoinV->set_cur(chtcount, yrind);
		burnsoinV->put(&regnod->burnsoin[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_burnvegn]==1){
   	   	burnvegnV->set_cur(chtcount, yrind);
		burnvegnV->put(&regnod->burnvegn[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_burnretainc]==1){
   	   	burnretaincV->set_cur(chtcount, yrind);
		burnretaincV->put(&regnod->burnretainc[0], 1, 1);
   	}

   	if (regnod->outvarlist[I_burnretainn]==1){
   	   	burnretainnV->set_cur(chtcount, yrind);
		burnretainnV->put(&regnod->burnretainn[0], 1, 1);
   	}

/////// MONTHLY OUTPUT /////////////////////////////////////////////////////////////////
   	   	if (regnod->outvarlist[I_growstart]==2){
   	   	   	growstartV->set_cur(chtcount, yrind*12);
   			growstartV->put(&regnod->growstart[0][0], 1, 12, NUM_PFT);
   	   	}

   	   	if (regnod->outvarlist[I_growend]==2){
   	   	   	growendV->set_cur(chtcount, yrind*12);
   			growendV->put(&regnod->growend[0][0], 1, 12, NUM_PFT);
   	   	}

   	   	if (regnod->outvarlist[I_vegcov]==2){
   	   	   	vegcovV->set_cur(chtcount, yrind*12);
   			vegcovV->put(&regnod->vegcov[0][0], 1, 12, NUM_PFT);
   	   	}

   	   	if (regnod->outvarlist[I_vegage]==2){
   	   	   	vegageV->set_cur(chtcount, yrind*12);
   			vegageV->put(&regnod->vegage[0][0], 1, 12, NUM_PFT);
   	   	}

   	   	if (regnod->outvarlist[I_lai]==2){
   	   	   	laiV->set_cur(chtcount, yrind*12);
   			laiV->put(&regnod->lai[0][0], 1, 12, NUM_PFT);
   	   	}

   	   	if (regnod->outvarlist[I_vegc]==2){
   	   	   	vegcV->set_cur(chtcount, yrind*12);
   			vegcV->put(&regnod->vegc[0][0], 1, 12, NUM_PFT);
   	   	}

   	   	if (regnod->outvarlist[I_leafc]==2){
   	   	   	leafcV->set_cur(chtcount, yrind*12);
   			leafcV->put(&regnod->leafc[0][0], 1, 12, NUM_PFT);
   	   	}

   	   	if (regnod->outvarlist[I_stemc]==2){
   	   	   	stemcV->set_cur(chtcount, yrind*12);
   			stemcV->put(&regnod->stemc[0][0], 1, 12, NUM_PFT);
   	   	}

   	   	if (regnod->outvarlist[I_rootc]==2){
   	   	   	rootcV->set_cur(chtcount, yrind*12);
   			rootcV->put(&regnod->rootc[0][0], 1, 12, NUM_PFT);
   	   	}

   	   	if (regnod->outvarlist[I_vegn]==2){
   	   	   	vegnV->set_cur(chtcount, yrind*12);
   			vegnV->put(&regnod->vegn[0][0], 1, 12, NUM_PFT);
   	   	}

   	   	if (regnod->outvarlist[I_labn]==2){
   	   	   	labnV->set_cur(chtcount, yrind*12);
   			labnV->put(&regnod->labn[0][0], 1, 12, NUM_PFT);
   	   	}

   	   	if (regnod->outvarlist[I_leafn]==2){
   	   	   	leafnV->set_cur(chtcount, yrind*12);
   			leafnV->put(&regnod->leafn[0][0], 1, 12, NUM_PFT);
   	   	}

   	   	if (regnod->outvarlist[I_stemn]==2){
   	   	   	stemnV->set_cur(chtcount, yrind*12);
   			stemnV->put(&regnod->stemn[0][0], 1, 12, NUM_PFT);
   	   	}

   	   	if (regnod->outvarlist[I_rootn]==2){
   	   	   	rootnV->set_cur(chtcount, yrind*12);
   			rootnV->put(&regnod->rootn[0][0], 1, 12, NUM_PFT);
   	   	}

   	   	if (regnod->outvarlist[I_gpp]==2){
   	   	   	gppV->set_cur(chtcount, yrind*12);
   			gppV->put(&regnod->gpp[0][0], 1, 12, NUM_PFT);
   	   	}

   	   	if (regnod->outvarlist[I_npp]==2){
   	   	   	nppV->set_cur(chtcount, yrind*12);
   			nppV->put(&regnod->npp[0][0], 1, 12, NUM_PFT);
   	   	}

   	   	if (regnod->outvarlist[I_ltrfalc]==2){
   	   	   	ltrfalcV->set_cur(chtcount, yrind*12);
   	   	   	ltrfalcV->put(&regnod->ltrfalc[0][0], 1, 12, NUM_PFT);
   	   	}

   	   	if (regnod->outvarlist[I_ltrfaln]==2){
   	   	   	ltrfalnV->set_cur(chtcount, yrind*12);
   	   	   	ltrfalnV->put(&regnod->ltrfaln[0][0], 1, 12, NUM_PFT);
   	   	}

   	   	if (regnod->outvarlist[I_nuptake]==2){
   	   	   	nuptakeV->set_cur(chtcount, yrind*12);
   	   	   	nuptakeV->put(&regnod->nuptake[0][0], 1, 12, NUM_PFT);
   	   	}

   	   	//
   	   	if (regnod->outvarlist[I_permafrost]==2){
   	   	   	permafrostV->set_cur(chtcount, yrind*12);
   			permafrostV->put(&regnod->permafrost[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_mossdz]==2){
   	   	   	mossdzV->set_cur(chtcount, yrind*12);
   			mossdzV->put(&regnod->mossdz[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_oshlwdz]==2){
   	   	   	oshlwdzV->set_cur(chtcount, yrind*12);
   			oshlwdzV->put(&regnod->oshlwdz[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_odeepdz]==2){
   	   	   	odeepdzV->set_cur(chtcount, yrind*12);
   			odeepdzV->put(&regnod->odeepdz[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_mineadz]==2){
   	   	   	mineadzV->set_cur(chtcount, yrind*12);
   			mineadzV->put(&regnod->mineadz[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_minebdz]==2){
   	   	   	minebdzV->set_cur(chtcount, yrind*12);
   			minebdzV->put(&regnod->minebdz[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_minecdz]==2){
   	   	   	minecdzV->set_cur(chtcount, yrind*12);
   			minecdzV->put(&regnod->minecdz[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_oshlwc]==2){
   	   	   	oshlwcV->set_cur(chtcount, yrind*12);
   			oshlwcV->put(&regnod->oshlwc[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_odeepc]==2){
   	   	   	odeepcV->set_cur(chtcount, yrind*12);
   			odeepcV->put(&regnod->odeepc[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_mineac]==2){
   	   	   	mineacV->set_cur(chtcount, yrind*12);
   			mineacV->put(&regnod->mineac[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_minebc]==2){
   	   	   	minebcV->set_cur(chtcount, yrind*12);
   			minebcV->put(&regnod->minebc[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_minecc]==2){
   	   	   	mineccV->set_cur(chtcount, yrind*12);
   			mineccV->put(&regnod->minecc[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_orgn]==2){
   	   	   	orgnV->set_cur(chtcount, yrind*12);
   			orgnV->put(&regnod->orgn[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_avln]==2){
   	   	   	avlnV->set_cur(chtcount, yrind*12);
   			avlnV->put(&regnod->avln[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_rh]==2){
   	   	   	rhV->set_cur(chtcount, yrind*12);
   			rhV->put(&regnod->rh[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_netnmin]==2){
   	   	   	netnminV->set_cur(chtcount, yrind*12);
   			netnminV->put(&regnod->netnmin[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_orgninput]==2){
   	   	   	orgninputV->set_cur(chtcount, yrind*12);
   	   	   	orgninputV->put(&regnod->orgninput[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_avlninput]==2){
   	   	   	avlninputV->set_cur(chtcount, yrind*12);
   			avlninputV->put(&regnod->avlninput[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_orgnlost]==2){
   	   	   	orgnlostV->set_cur(chtcount, yrind*12);
   			orgnlostV->put(&regnod->orgnlost[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_avlnlost]==2){
   	   	   	avlnlostV->set_cur(chtcount, yrind*12);
   			avlnlostV->put(&regnod->avlnlost[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_doclost]==2){
   	   	   	doclostV->set_cur(chtcount, yrind*12);
   	   	   	doclostV->put(&regnod->doclost[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_eet]==2){
   	   	   	eetV->set_cur(chtcount, yrind*12);
   	   	   	eetV->put(&regnod->eet[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_pet]==2){
   	   	   	petV->set_cur(chtcount, yrind*12);
   			petV->put(&regnod->pet[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_qinfl]==2){
   	   	   	qinflV->set_cur(chtcount, yrind*12);
   			qinflV->put(&regnod->qinfl[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_qdrain]==2){
   	   	   	qdrainV->set_cur(chtcount, yrind*12);
   			qdrainV->put(&regnod->qdrain[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_qrunoff]==2){
   	   	   	qrunoffV->set_cur(chtcount, yrind*12);
   	   	   	qrunoffV->put(&regnod->qrunoff[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_snwthick]==2){
   	   	   	snwthickV->set_cur(chtcount, yrind*12);
   	   	   	snwthickV->put(&regnod->snwthick[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_swe]==2){
   	   	   	sweV->set_cur(chtcount, yrind*12);
   	   	   	sweV->put(&regnod->swe[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_wtd]==2){
   	   	   	wtdV->set_cur(chtcount, yrind*12);
   			wtdV->put(&regnod->wtd[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_alc]==2){
   	   	   	alcV->set_cur(chtcount, yrind*12);
   			alcV->put(&regnod->alc[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_ald]==2){
   	   	   	aldV->set_cur(chtcount, yrind*12);
   	   	   	aldV->put(&regnod->ald[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_vwcshlw]==2){
   	   	   	vwcshlwV->set_cur(chtcount, yrind*12);
   			vwcshlwV->put(&regnod->vwcshlw[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_vwcdeep]==2){
   	   	   	vwcdeepV->set_cur(chtcount, yrind*12);
   			vwcdeepV->put(&regnod->vwcdeep[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_vwcminea]==2){
   	   	   	vwcmineaV->set_cur(chtcount, yrind*12);
   			vwcmineaV->put(&regnod->vwcminea[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_vwcmineb]==2){
   	   	   	vwcminebV->set_cur(chtcount, yrind*12);
   	   	   	vwcminebV->put(&regnod->vwcmineb[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_vwcminec]==2){
   	   	   	vwcminecV->set_cur(chtcount, yrind*12);
   	   	   	vwcminecV->put(&regnod->vwcminec[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_tshlw]==2){
   	   	   	tshlwV->set_cur(chtcount, yrind*12);
   			tshlwV->put(&regnod->tshlw[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_tdeep]==2){
   	   	   	tdeepV->set_cur(chtcount, yrind*12);
   			tdeepV->put(&regnod->tdeep[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_tminea]==2){
   	   	   	tmineaV->set_cur(chtcount, yrind*12);
   			tmineaV->put(&regnod->tminea[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_tmineb]==2){
   	   	   	tminebV->set_cur(chtcount, yrind*12);
   			tminebV->put(&regnod->tmineb[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_tminec]==2){
   	   	   	tminecV->set_cur(chtcount, yrind*12);
   			tminecV->put(&regnod->tminec[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_hkshlw]==2){
   	   	   	hkshlwV->set_cur(chtcount, yrind*12);
   			hkshlwV->put(&regnod->hkshlw[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_hkdeep]==2){
   	   	   	hkdeepV->set_cur(chtcount, yrind*12);
   			hkdeepV->put(&regnod->hkdeep[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_hkminea]==2){
   	   	   	hkmineaV->set_cur(chtcount, yrind*12);
   			hkmineaV->put(&regnod->hkminea[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_hkmineb]==2){
   	   	   	hkminebV->set_cur(chtcount, yrind*12);
   			hkminebV->put(&regnod->hkmineb[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_hkminec]==2){
   	   	   	hkminecV->set_cur(chtcount, yrind*12);
   			hkminecV->put(&regnod->hkminec[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_tcshlw]==2){
   	   	   	tcshlwV->set_cur(chtcount, yrind*12);
   			tcshlwV->put(&regnod->tcshlw[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_tcdeep]==2){
   	   	   	tcdeepV->set_cur(chtcount, yrind*12);
   			tcdeepV->put(&regnod->tcdeep[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_tcminea]==2){
   	   	   	tcmineaV->set_cur(chtcount, yrind*12);
   			tcmineaV->put(&regnod->tcminea[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_tcmineb]==2){
   	   	   	tcminebV->set_cur(chtcount, yrind*12);
   			tcminebV->put(&regnod->tcmineb[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_tcminec]==2){
   	   	   	tcminecV->set_cur(chtcount, yrind*12);
   			tcminecV->put(&regnod->tcminec[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_tbotrock]==2){
   	   	   	tbotrockV->set_cur(chtcount, yrind*12);
   			tbotrockV->put(&regnod->tbotrock[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_burnthick]==2){
   	   	   	burnthickV->set_cur(chtcount, yrind*12);
   			burnthickV->put(&regnod->burnthick[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_burnsoic]==2){
   	   	   	burnsoicV->set_cur(chtcount, yrind*12);
   			burnsoicV->put(&regnod->burnsoic[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_burnvegc]==2){
   	   	   	burnvegcV->set_cur(chtcount, yrind*12);
   			burnvegcV->put(&regnod->burnvegc[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_burnsoin]==2){
   	   	   	burnsoinV->set_cur(chtcount, yrind*12);
   			burnsoinV->put(&regnod->burnsoin[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_burnvegn]==2){
   	   	   	burnvegnV->set_cur(chtcount, yrind*12);
   			burnvegnV->put(&regnod->burnvegn[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_burnretainc]==2){
   	   	   	burnretaincV->set_cur(chtcount, yrind*12);
   			burnretaincV->put(&regnod->burnretainc[0], 1, 12);
   	   	}

   	   	if (regnod->outvarlist[I_burnretainn]==2){
   	   	   	burnretainnV->set_cur(chtcount, yrind*12);
   			burnretainnV->put(&regnod->burnretainn[0], 1, 12);
   	   	}

};

void RegnOutputer::setOutData(OutDataRegn *regnodp) {
	regnod = regnodp;
};
