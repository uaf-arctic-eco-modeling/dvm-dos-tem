/*! \file 
*/

#include "BgcOutputer.h"

BgcOutputer::BgcOutputer(){
	
};

BgcOutputer::~BgcOutputer(){
 	if(ncfileenv!=NULL){
 		ncfileenv->close();
 		delete ncfileenv;
 	}
};

void BgcOutputer::init(string & dirfile){

	//file
	ncfname = dirfile;

	ncfileenv = new NcFile(ncfname.c_str(), NcFile::Replace);

	//dimension
	timeD    = ncfileenv->add_dim("tstep");
	pftD     = ncfileenv->add_dim("pft", NUM_PFT);
	partD    = ncfileenv->add_dim("vegpart", NUM_PFT_PART);
	soilayerD= ncfileenv->add_dim("soilayer", MAX_SOI_LAY);

    //variables
  	chtidV = ncfileenv->add_var("CHTID", ncInt);
  	errorV = ncfileenv->add_var("ERRORID", ncInt, timeD);
	yearV  = ncfileenv->add_var("YEAR", ncInt, timeD);
	monV   = ncfileenv->add_var("MONTH", ncInt, timeD);

	// veg C/N state variables
   	callV = ncfileenv->add_var("VEGCSUM", ncDouble, timeD, pftD);
   	cV = ncfileenv->add_var("VEGCPART", ncDouble, timeD, pftD, partD);
   	nallV = ncfileenv->add_var("VEGNSUM", ncDouble, timeD, pftD);
   	labnV = ncfileenv->add_var("VEGNLAB", ncDouble, timeD);
   	strnallV = ncfileenv->add_var("VEGNSTRNSUM", ncDouble, timeD, pftD);
   	strnV = ncfileenv->add_var("VEGNSTRNPART", ncDouble, timeD, pftD, partD);
   	deadcV = ncfileenv->add_var("VEGCDEAD", ncDouble, timeD, pftD);
   	deadnV = ncfileenv->add_var("VEGNDEAD", ncDouble, timeD, pftD);
   	wdebriscV = ncfileenv->add_var("WDEBRISC", ncDouble, timeD);
   	wdebrisnV = ncfileenv->add_var("WDEBRISN", ncDouble, timeD);

   	// soil C/N state variables
   	rawcV = ncfileenv->add_var("RAWC", ncDouble, timeD, soilayerD);
   	somaV = ncfileenv->add_var("SOMA", ncDouble, timeD, soilayerD);
   	somprV = ncfileenv->add_var("SOMPR", ncDouble, timeD, soilayerD);
   	somcrV = ncfileenv->add_var("SOMCR", ncDouble, timeD, soilayerD);
   	orgnV = ncfileenv->add_var("ORGN", ncDouble, timeD, soilayerD);
   	avlnV = ncfileenv->add_var("AVLN", ncDouble, timeD, soilayerD);

   	shlwcV = ncfileenv->add_var("SOMCSHLW", ncDouble, timeD);
   	deepcV = ncfileenv->add_var("SOMCDEEP", ncDouble, timeD);
   	mineacV = ncfileenv->add_var("SOMCMINEA", ncDouble, timeD);
   	minebcV = ncfileenv->add_var("SOMCMINEB", ncDouble, timeD);
   	mineccV = ncfileenv->add_var("SOMCMINEC", ncDouble, timeD);
   	rawcsumV = ncfileenv->add_var("RAWCSUM", ncDouble, timeD);
   	somasumV = ncfileenv->add_var("SOMASUM", ncDouble, timeD);
   	somprsumV = ncfileenv->add_var("SOMPRSUM", ncDouble, timeD);
   	somcrsumV = ncfileenv->add_var("SOMCRSUM", ncDouble, timeD);
   	orgnsumV = ncfileenv->add_var("ORGNSUM", ncDouble, timeD);
   	avlnsumV = ncfileenv->add_var("AVLNSUM", ncDouble, timeD);

 	//C/N fluxes
   	gppftV = ncfileenv->add_var("GPPFTEMP", ncDouble, timeD, pftD);
   	gvV = ncfileenv->add_var("GPPGV", ncDouble, timeD, pftD);
   	fnaV = ncfileenv->add_var("GPPFNA", ncDouble, timeD, pftD);
   	fcaV = ncfileenv->add_var("GPPFCA", ncDouble, timeD, pftD);
   	raq10V = ncfileenv->add_var("RAQ10", ncDouble, timeD, pftD);
   	rmkrV = ncfileenv->add_var("RMKR", ncDouble, timeD, pftD);

   	knmoistV = ncfileenv->add_var("NMITKSOIL", ncDouble, timeD, soilayerD);
   	rhmoistV = ncfileenv->add_var("RHMOIST", ncDouble, timeD, soilayerD);
   	rhq10V = ncfileenv->add_var("RHQ10", ncDouble, timeD, soilayerD);
   	soilltrfcnV = ncfileenv->add_var("SOILLTRFCN", ncDouble, timeD, soilayerD);

   	nepV = ncfileenv->add_var("NEP", ncDouble, timeD);
	ingppallV = ncfileenv->add_var("INGPPALL", ncDouble, timeD, pftD);
	ingppV = ncfileenv->add_var("INGPP", ncDouble, timeD, pftD, partD);
	innppallV = ncfileenv->add_var("INNPPALL", ncDouble, timeD, pftD);
	innppV = ncfileenv->add_var("INNPP", ncDouble, timeD, pftD, partD);
	gppallV = ncfileenv->add_var("GPPALL", ncDouble, timeD, pftD);
	gppV = ncfileenv->add_var("GPP", ncDouble, timeD, pftD, partD);
	nppallV = ncfileenv->add_var("NPPALL", ncDouble, timeD, pftD);
	nppV = ncfileenv->add_var("NPP", ncDouble, timeD, pftD, partD);
	rmallV = ncfileenv->add_var("RMALL", ncDouble, timeD, pftD);
	rmV = ncfileenv->add_var("RM", ncDouble, timeD, pftD, partD);
	rgallV = ncfileenv->add_var("RGALL", ncDouble, timeD, pftD);
	rgV = ncfileenv->add_var("RG", ncDouble, timeD, pftD, partD);
	ltrfalcallV = ncfileenv->add_var("LTRFALCALL", ncDouble, timeD, pftD);
	ltrfalcV = ncfileenv->add_var("LTRFALC", ncDouble, timeD, pftD, partD);

	ltrfalnallV = ncfileenv->add_var("LTRFALNALL", ncDouble, timeD, pftD);
	ltrfalnV = ncfileenv->add_var("LTRFALN", ncDouble, timeD, pftD, partD);
	innuptakeV = ncfileenv->add_var("INNUPTAKE", ncDouble, timeD, pftD);
	nrootextractV = ncfileenv->add_var("NROOTEXTRACT", ncDouble, timeD, pftD, soilayerD);
	luptakeV = ncfileenv->add_var("NUPTAKEL", ncDouble, timeD, pftD);
	suptakeallV = ncfileenv->add_var("NUPTAKESALL", ncDouble, timeD, pftD);
	suptakeV = ncfileenv->add_var("NUPTAKES", ncDouble, timeD, pftD, partD);
	nmobilallV = ncfileenv->add_var("NMOBILALL", ncDouble, timeD, pftD);
	nmobilV = ncfileenv->add_var("NMOBIL", ncDouble, timeD, pftD, partD);
	nresorballV = ncfileenv->add_var("NRESOBALL", ncDouble, timeD, pftD);
	nresorbV = ncfileenv->add_var("NRESORB", ncDouble, timeD, pftD, partD);

	//
	doclostV = ncfileenv->add_var("DOCLOST", ncDouble, timeD);      //DOC lost
	avlnlostV = ncfileenv->add_var("AVLNLOST", ncDouble, timeD);     // N leaching
	orgnlostV = ncfileenv->add_var("ORGNLOST", ncDouble, timeD);     // DON loss

}

void BgcOutputer::outputCohortBgcVars_mly(BgcData *bgcod, const int &calyr, const int &calmon, const int &ipft, const int & tstepcnt){
 	NcError err(NcError::verbose_nonfatal);

 	if (ipft==0) {
 		if (tstepcnt==0) chtidV->put(&bgcod->cd->chtid);
 		yearV->put_rec(&calyr, tstepcnt);
 		monV->put_rec(&calmon, tstepcnt);
 	}

	// veg C/N state variables
 	callV->set_cur(tstepcnt, ipft);
   	callV->put(&bgcod->m_vegs.call, 1, 1);

 	cV->set_cur(tstepcnt, ipft, 0);
 	cV->put(&bgcod->m_vegs.c[0], 1, 1, NUM_PFT_PART);

 	nallV->set_cur(tstepcnt, ipft);
   	nallV->put(&bgcod->m_vegs.nall, 1, 1);

   	labnV->set_cur(tstepcnt, ipft);
   	labnV->put(&bgcod->m_vegs.labn, 1, 1);

   	strnallV->set_cur(tstepcnt, ipft);
   	strnallV->put(&bgcod->m_vegs.strnall, 1, 1);

   	strnV->set_cur(tstepcnt, ipft, 0);
   	strnV->put(&bgcod->m_vegs.strn[0], 1, 1, NUM_PFT_PART);

   	deadcV->set_cur(tstepcnt, ipft);
   	deadcV->put(&bgcod->m_vegs.deadc, 1, 1);

   	callV->set_cur(tstepcnt, ipft);
   	deadnV->put(&bgcod->m_vegs.deadn, 1, 1);

   	// soil C/N state variables
   	if (ipft==0) {
   		wdebriscV->put_rec(&bgcod->m_sois.wdebrisc, tstepcnt);
   		wdebrisnV->put_rec(&bgcod->m_sois.wdebrisn, tstepcnt);
   		rawcV->put_rec(&bgcod->m_sois.rawc[0], tstepcnt);
   		somaV->put_rec(&bgcod->m_sois.soma[0], tstepcnt);
   		somprV->put_rec(&bgcod->m_sois.sompr[0], tstepcnt);
   		somcrV->put_rec(&bgcod->m_sois.somcr[0], tstepcnt);
   		orgnV->put_rec(&bgcod->m_sois.orgn[0], tstepcnt);
   		avlnV->put_rec(&bgcod->m_sois.avln[0], tstepcnt);

   		shlwcV->put_rec(&bgcod->m_soid.shlwc, tstepcnt);
   		deepcV->put_rec(&bgcod->m_soid.deepc, tstepcnt);
   		mineacV->put_rec(&bgcod->m_soid.mineac, tstepcnt);
   		minebcV->put_rec(&bgcod->m_soid.minebc, tstepcnt);
   		mineccV->put_rec(&bgcod->m_soid.minecc, tstepcnt);
   		rawcsumV->put_rec(&bgcod->m_soid.rawcsum, tstepcnt);
   		somasumV->put_rec(&bgcod->m_soid.somasum, tstepcnt);
   		somprsumV->put_rec(&bgcod->m_soid.somprsum, tstepcnt);
   		somcrsumV->put_rec(&bgcod->m_soid.somcrsum, tstepcnt);
   		orgnsumV->put_rec(&bgcod->m_soid.orgnsum, tstepcnt);
   		avlnsumV->put_rec(&bgcod->m_soid.avlnsum, tstepcnt);
   	}

 	//C/N fluxes

 	gppftV->set_cur(tstepcnt, ipft);
   	gppftV->put(&bgcod->m_vegd.ftemp, 1, 1);

   	gvV->set_cur(tstepcnt, ipft);
   	gvV->put(&bgcod->m_vegd.gv, 1, 1);

   	fnaV->set_cur(tstepcnt, ipft);
   	fnaV->put(&bgcod->m_vegd.fna, 1, 1);

   	fcaV->set_cur(tstepcnt, ipft);
   	fcaV->put(&bgcod->m_vegd.fca, 1, 1);

   	raq10V->set_cur(tstepcnt, ipft);
   	raq10V->put(&bgcod->m_vegd.raq10, 1, 1);

   	rmkrV->set_cur(tstepcnt, ipft, 0);
   	rmkrV->put(&bgcod->m_vegd.kr[0], 1, 1, NUM_PFT_PART);

   	if (ipft==0) {
   		knmoistV->put_rec(&bgcod->m_soid.knmoist[0], tstepcnt);
   		rhmoistV->put_rec(&bgcod->m_soid.rhmoist[0], tstepcnt);

   		rhq10V->put_rec(&bgcod->m_soid.rhq10[0], tstepcnt);
   		soilltrfcnV->put_rec(&bgcod->m_soid.ltrfcn[0], tstepcnt);
   	}

   	// C/N fluxes
 	ingppallV->set_cur(tstepcnt, ipft);
	ingppallV->put(&bgcod->m_a2v.ingppall, 1, 1);

	ingppV->set_cur(tstepcnt, ipft, 0);
	ingppV->put(&bgcod->m_a2v.ingpp[0], 1, 1, NUM_PFT_PART);

	innppallV->set_cur(tstepcnt, ipft);
	innppallV->put(&bgcod->m_a2v.innppall, 1, 1);

	innppV->set_cur(tstepcnt, ipft, 0);
	innppV->put(&bgcod->m_a2v.innpp[0], 1, 1, NUM_PFT_PART);

	gppallV->set_cur(tstepcnt, ipft);
	gppallV->put(&bgcod->m_a2v.gppall, 1, 1);

	gppV->set_cur(tstepcnt, ipft, 0);
	gppV->put(&bgcod->m_a2v.gpp[0], 1, 1, NUM_PFT_PART);

	nppallV->set_cur(tstepcnt, ipft);
	nppallV->put(&bgcod->m_a2v.nppall, 1, 1);

	nppV->set_cur(tstepcnt, ipft, 0);
	nppV->put(&bgcod->m_a2v.npp[0], 1, 1, NUM_PFT_PART);

	rmallV->set_cur(tstepcnt, ipft);
	rmallV->put(&bgcod->m_v2a.rmall,  1, 1);

	rmV->set_cur(tstepcnt, ipft, 0);
	rmV->put(&bgcod->m_v2a.rm[0], 1, 1, NUM_PFT_PART);

 	rgallV->set_cur(tstepcnt, ipft);
	rgallV->put(&bgcod->m_v2a.rgall,  1, 1);

 	rgV->set_cur(tstepcnt, ipft, 0);
 	rgV->put(&bgcod->m_v2a.rg[0], 1, 1, NUM_PFT_PART);

 	ltrfalcallV->set_cur(tstepcnt, ipft);
 	if (bgcod->cd->m_veg.nonvascular[ipft]>0) {
 		ltrfalcallV->put(&bgcod->m_v2soi.mossdeathc,  1, 1);
 	} else {
 		ltrfalcallV->put(&bgcod->m_v2soi.ltrfalcall,  1, 1);
 	}

	ltrfalcV->set_cur(tstepcnt, ipft, 0);
	ltrfalcV->put(&bgcod->m_v2soi.ltrfalc[0], 1, 1, NUM_PFT_PART);

	//
	if (ipft==0) nepV->put_rec(&bgcod->m_l2a.nep, tstepcnt);
	//
 	ltrfalnallV->set_cur(tstepcnt, ipft);
 	if (bgcod->cd->m_veg.nonvascular[ipft]>0) {
 		ltrfalnallV->put(&bgcod->m_v2soi.mossdeathn,  1, 1);
 	} else {
 		ltrfalnallV->put(&bgcod->m_v2soi.ltrfalnall,  1, 1);
 	}

	ltrfalnV->set_cur(tstepcnt, ipft, 0);
	ltrfalnV->put(&bgcod->m_v2soi.ltrfaln[0], 1, 1, NUM_PFT_PART);

	innuptakeV->set_cur(tstepcnt, ipft);
	innuptakeV->put(&bgcod->m_soi2v.innuptake,  1, 1);

	nrootextractV->set_cur(tstepcnt, ipft, 0);
	nrootextractV->put(&bgcod->m_soi2v.nextract[0], 1, 1, MAX_SOI_LAY);

	luptakeV->set_cur(tstepcnt, ipft);
	luptakeV->put(&bgcod->m_soi2v.lnuptake,  1, 1);

	suptakeallV->set_cur(tstepcnt, ipft);
	suptakeallV->put(&bgcod->m_soi2v.snuptakeall,  1, 1);

	suptakeV->set_cur(tstepcnt, ipft);
	suptakeV->put(&bgcod->m_soi2v.snuptake[0], 1, 1, NUM_PFT_PART);

	nmobilallV->set_cur(tstepcnt, ipft);
	nmobilallV->put(&bgcod->m_v2v.nmobilall, 1, 1);

	nmobilV->set_cur(tstepcnt, ipft);
	nmobilV->put(&bgcod->m_v2v.nmobil[0], 1, 1, NUM_PFT_PART);

	nresorballV->set_cur(tstepcnt, ipft);
	nresorballV->put(&bgcod->m_v2v.nresorball, 1, 1);

	nresorbV->set_cur(tstepcnt, ipft);
	nresorbV->put(&bgcod->m_v2v.nresorb[0], 1, 1, NUM_PFT_PART);

	//
	if (ipft==0) {
		doclostV->put_rec(&bgcod->m_soi2l.doclost, tstepcnt);      //DOC lost
		avlnlostV->put_rec(&bgcod->m_soi2l.avlnlost, tstepcnt);     // N leaching
		orgnlostV->put_rec(&bgcod->m_soi2l.orgnlost, tstepcnt);     // DON loss
	}
}

void BgcOutputer::outputCohortBgcVars_yly(BgcData *bgcod, const int &calyr, const int &ipft, const int & tstepcnt){
 	NcError err(NcError::verbose_nonfatal);

 	if (ipft==0) {
 		if (tstepcnt==0) chtidV->put(&bgcod->cd->chtid);
		yearV->put_rec(&calyr, tstepcnt);
 		monV->put_rec(&MISSING_I, tstepcnt);
 	}

	// veg C/N state variables
 	callV->set_cur(tstepcnt, ipft);
   	callV->put(&bgcod->y_vegs.call, 1, 1);

 	cV->set_cur(tstepcnt, ipft, 0);
 	cV->put(&bgcod->y_vegs.c[0], 1, 1, NUM_PFT_PART);

 	nallV->set_cur(tstepcnt, ipft);
   	nallV->put(&bgcod->y_vegs.nall, 1, 1);

   	labnV->set_cur(tstepcnt, ipft);
   	labnV->put(&bgcod->y_vegs.labn, 1, 1);

   	strnallV->set_cur(tstepcnt, ipft);
   	strnallV->put(&bgcod->y_vegs.strnall, 1, 1);

   	strnV->set_cur(tstepcnt, ipft, 0);
   	strnV->put(&bgcod->y_vegs.strn[0], 1, 1, NUM_PFT_PART);

   	deadcV->set_cur(tstepcnt, ipft);
   	deadcV->put(&bgcod->y_vegs.deadc, 1, 1);

   	callV->set_cur(tstepcnt, ipft);
   	deadnV->put(&bgcod->y_vegs.deadn, 1, 1);

   	// soil C/N state variables
   	if (ipft==0) {
   		wdebriscV->put_rec(&bgcod->y_sois.wdebrisc, tstepcnt);
   		wdebrisnV->put_rec(&bgcod->y_sois.wdebrisn, tstepcnt);
   		rawcV->put_rec(&bgcod->y_sois.rawc[0], tstepcnt);
   		somaV->put_rec(&bgcod->y_sois.soma[0], tstepcnt);
   		somprV->put_rec(&bgcod->y_sois.sompr[0], tstepcnt);
   		somcrV->put_rec(&bgcod->y_sois.somcr[0], tstepcnt);
   		orgnV->put_rec(&bgcod->y_sois.orgn[0], tstepcnt);
   		avlnV->put_rec(&bgcod->y_sois.avln[0], tstepcnt);

   		shlwcV->put_rec(&bgcod->y_soid.shlwc, tstepcnt);
   		deepcV->put_rec(&bgcod->y_soid.deepc, tstepcnt);
   		mineacV->put_rec(&bgcod->y_soid.mineac, tstepcnt);
   		minebcV->put_rec(&bgcod->y_soid.minebc, tstepcnt);
   		mineccV->put_rec(&bgcod->y_soid.minecc, tstepcnt);
   		rawcsumV->put_rec(&bgcod->y_soid.rawcsum, tstepcnt);
   		somasumV->put_rec(&bgcod->y_soid.somasum, tstepcnt);
   		somprsumV->put_rec(&bgcod->y_soid.somprsum, tstepcnt);
   		somcrsumV->put_rec(&bgcod->y_soid.somcrsum, tstepcnt);
   		orgnsumV->put_rec(&bgcod->y_soid.orgnsum, tstepcnt);
   		avlnsumV->put_rec(&bgcod->y_soid.avlnsum, tstepcnt);
   	}

 	//C/N fluxes

 	gppftV->set_cur(tstepcnt, ipft);
   	gppftV->put(&bgcod->y_vegd.ftemp, 1, 1);

   	gvV->set_cur(tstepcnt, ipft);
   	gvV->put(&bgcod->y_vegd.gv, 1, 1);

   	fnaV->set_cur(tstepcnt, ipft);
   	fnaV->put(&bgcod->y_vegd.fna, 1, 1);

   	fcaV->set_cur(tstepcnt, ipft);
   	fcaV->put(&bgcod->y_vegd.fca, 1, 1);

   	raq10V->set_cur(tstepcnt, ipft);
   	raq10V->put(&bgcod->y_vegd.raq10, 1, 1);

   	rmkrV->set_cur(tstepcnt, ipft, 0);
   	rmkrV->put(&bgcod->y_vegd.kr[0], 1, 1, NUM_PFT_PART);

   	if (ipft==0) {
   		knmoistV->put_rec(&bgcod->y_soid.knmoist[0], tstepcnt);
   		rhmoistV->put_rec(&bgcod->y_soid.rhmoist[0], tstepcnt);

   		rhq10V->put_rec(&bgcod->y_soid.rhq10[0], tstepcnt);
   		soilltrfcnV->put_rec(&bgcod->y_soid.ltrfcn[0], tstepcnt);
   	}

   	// C/N fluxes
 	ingppallV->set_cur(tstepcnt, ipft);
	ingppallV->put(&bgcod->y_a2v.ingppall, 1, 1);

	ingppV->set_cur(tstepcnt, ipft, 0);
	ingppV->put(&bgcod->y_a2v.ingpp[0], 1, 1, NUM_PFT_PART);

	innppallV->set_cur(tstepcnt, ipft);
	innppallV->put(&bgcod->y_a2v.innppall, 1, 1);

	innppV->set_cur(tstepcnt, ipft, 0);
	innppV->put(&bgcod->y_a2v.innpp[0], 1, 1, NUM_PFT_PART);

	gppallV->set_cur(tstepcnt, ipft);
	gppallV->put(&bgcod->y_a2v.gppall, 1, 1);

	gppV->set_cur(tstepcnt, ipft, 0);
	gppV->put(&bgcod->y_a2v.gpp[0], 1, 1, NUM_PFT_PART);

	nppallV->set_cur(tstepcnt, ipft);
	nppallV->put(&bgcod->y_a2v.nppall, 1, 1);

	nppV->set_cur(tstepcnt, ipft, 0);
	nppV->put(&bgcod->y_a2v.npp[0], 1, 1, NUM_PFT_PART);

	rmallV->set_cur(tstepcnt, ipft);
	rmallV->put(&bgcod->y_v2a.rmall,  1, 1);

	rmV->set_cur(tstepcnt, ipft, 0);
	rmV->put(&bgcod->y_v2a.rm[0], 1, 1, NUM_PFT_PART);

 	rgallV->set_cur(tstepcnt, ipft);
	rgallV->put(&bgcod->y_v2a.rgall,  1, 1);

 	rgV->set_cur(tstepcnt, ipft, 0);
 	rgV->put(&bgcod->y_v2a.rg[0], 1, 1, NUM_PFT_PART);

 	ltrfalcallV->set_cur(tstepcnt, ipft);
	ltrfalcallV->put(&bgcod->y_v2soi.ltrfalcall,  1, 1);

	ltrfalcV->set_cur(tstepcnt, ipft, 0);
	ltrfalcV->put(&bgcod->y_v2soi.ltrfalc[0], 1, 1, NUM_PFT_PART);

	//
	if (ipft==0) nepV->put_rec(&bgcod->y_l2a.nep, tstepcnt);
	//
 	ltrfalnallV->set_cur(tstepcnt, ipft);
	ltrfalnallV->put(&bgcod->y_v2soi.ltrfalnall,  1, 1);

	ltrfalnV->set_cur(tstepcnt, ipft, 0);
	ltrfalnV->put(&bgcod->y_v2soi.ltrfaln[0], 1, 1, NUM_PFT_PART);

	innuptakeV->set_cur(tstepcnt, ipft);
	innuptakeV->put(&bgcod->y_soi2v.innuptake,  1, 1);

	nrootextractV->set_cur(tstepcnt, ipft, 0);
	nrootextractV->put(&bgcod->y_soi2v.nextract[0], 1, 1, MAX_SOI_LAY);

	luptakeV->set_cur(tstepcnt, ipft);
	luptakeV->put(&bgcod->y_soi2v.lnuptake,  1, 1);

	suptakeallV->set_cur(tstepcnt, ipft);
	suptakeallV->put(&bgcod->y_soi2v.snuptakeall,  1, 1);

	suptakeV->set_cur(tstepcnt, ipft);
	suptakeV->put(&bgcod->y_soi2v.snuptake[0], 1, 1, NUM_PFT_PART);

	nmobilallV->set_cur(tstepcnt, ipft);
	nmobilallV->put(&bgcod->y_v2v.nmobilall, 1, 1);

	nmobilV->set_cur(tstepcnt, ipft);
	nmobilV->put(&bgcod->y_v2v.nmobil[0], 1, 1, NUM_PFT_PART);

	nresorballV->set_cur(tstepcnt, ipft);
	nresorballV->put(&bgcod->y_v2v.nresorball, 1, 1);

	nresorbV->set_cur(tstepcnt, ipft);
	nresorbV->put(&bgcod->y_v2v.nresorb[0], 1, 1, NUM_PFT_PART);

	//
	if (ipft==0) {
		doclostV->put_rec(&bgcod->y_soi2l.doclost, tstepcnt);      //DOC lost
		avlnlostV->put_rec(&bgcod->y_soi2l.avlnlost, tstepcnt);     // N leaching
		orgnlostV->put_rec(&bgcod->y_soi2l.orgnlost, tstepcnt);     // DON loss
	}
}
