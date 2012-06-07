/*! \file 
*/

#include "EnvOutputer.h"

EnvOutputer::EnvOutputer(){
	
};

EnvOutputer::~EnvOutputer(){
 	if(ncfileenv!=NULL){
 		ncfileenv->close();
 		delete ncfileenv;
 	}
};

void EnvOutputer::init(string & dirfile){

	//file
	ncfname = dirfile;

	ncfileenv = new NcFile(ncfname.c_str(), NcFile::Replace);

	//dimension
	timeD    = ncfileenv->add_dim("tstep");
	pftD     = ncfileenv->add_dim("pft", NUM_PFT);
	snwlayerD= ncfileenv->add_dim("snwlayer", MAX_SNW_LAY);
	soilayerD= ncfileenv->add_dim("soilayer", MAX_SOI_LAY);
	frontD  = ncfileenv->add_dim("frontnum", MAX_NUM_FNT);

    //variables
  	chtidV = ncfileenv->add_var("CHTID", ncInt);
  	errorV = ncfileenv->add_var("ERRORID", ncInt, timeD);
	yearV  = ncfileenv->add_var("YEAR", ncInt, timeD);
	monV   = ncfileenv->add_var("MONTH", ncInt, timeD);
	dayV   = ncfileenv->add_var("DAY", ncInt, timeD);

	// atm variables
   	co2V = ncfileenv->add_var("CO2", ncDouble, timeD);
   	tairV= ncfileenv->add_var("TAIR", ncDouble, timeD);
   	nirrV= ncfileenv->add_var("NIRR", ncDouble, timeD);
   	precV= ncfileenv->add_var("PREC", ncDouble, timeD);
  	vpV  = ncfileenv->add_var("VAPO", ncDouble, timeD);
   	svpV = ncfileenv->add_var("SVP", ncDouble, timeD);
   	vpdV = ncfileenv->add_var("VPD", ncDouble, timeD);
   	parV = ncfileenv->add_var("PAR", ncDouble, timeD);
   	rnflV= ncfileenv->add_var("RAINFALL", ncDouble, timeD);
   	snflV= ncfileenv->add_var("SNOWFALL", ncDouble, timeD);

   	// land-surface variables
   	pardownV= ncfileenv->add_var("PARDOWN", ncDouble, timeD);
   	parabsorbV= ncfileenv->add_var("PARABSORB", ncDouble, timeD);
   	swdownV= ncfileenv->add_var("SWDOWN", ncDouble, timeD);
   	swinterV= ncfileenv->add_var("SWINTER", ncDouble, timeD);
   	rinterV= ncfileenv->add_var("RAININTER", ncDouble, timeD);
   	sinterV= ncfileenv->add_var("SNOWINTER", ncDouble, timeD);
   	eetV= ncfileenv->add_var("EETTOTAL", ncDouble, timeD);
   	petV= ncfileenv->add_var("PETTOTAL", ncDouble, timeD);

   	// canopy-env variables
   	vegwaterV= ncfileenv->add_var("CANOPYRAIN", ncDouble, timeD, pftD);
   	vegsnowV= ncfileenv->add_var("CANOPYSNOW", ncDouble, timeD, pftD);
   	vegrcV= ncfileenv->add_var("CANOPYRC", ncDouble, timeD, pftD);
   	vegccV= ncfileenv->add_var("CANOPYCC", ncDouble, timeD, pftD);
   	vegbtranV= ncfileenv->add_var("CANOPYBTRAN", ncDouble, timeD, pftD);
   	vegm_ppfdV= ncfileenv->add_var("CANOPYM_PPFD", ncDouble, timeD, pftD);
   	vegm_vpdV= ncfileenv->add_var("CANOPYM_VPD", ncDouble, timeD, pftD);

   	vegswreflV= ncfileenv->add_var("CANOPYSWREFL", ncDouble, timeD, pftD);
   	vegswthflV= ncfileenv->add_var("CANOPYSWTHFL", ncDouble, timeD, pftD);

   	vegevapV= ncfileenv->add_var("CANOPYEVAP", ncDouble, timeD, pftD);
   	vegtranV= ncfileenv->add_var("CANOPYTRAN", ncDouble, timeD, pftD);
   	vegevap_pV= ncfileenv->add_var("CANOPYPEVAP", ncDouble, timeD, pftD);
   	vegtran_pV= ncfileenv->add_var("CANOPYPTRAN", ncDouble, timeD, pftD);
   	vegsublimV= ncfileenv->add_var("CANOPYSUBLIM", ncDouble, timeD, pftD);

   	vegrdripV= ncfileenv->add_var("CANOPYRDRIP", ncDouble, timeD, pftD);
   	vegrthflV= ncfileenv->add_var("CANOPYRTHFL", ncDouble, timeD, pftD);
   	vegsdripV= ncfileenv->add_var("CANOPYSDRIP", ncDouble, timeD, pftD);
   	vegsthflV= ncfileenv->add_var("CANOPYSTHFL", ncDouble, timeD, pftD);

	//snow
	snwlnumV= ncfileenv->add_var("SNWLNUM", ncDouble, timeD);
	snwthickV= ncfileenv->add_var("SNWTHICK", ncDouble, timeD);
	snwdenseV= ncfileenv->add_var("SNWDENSITY", ncDouble, timeD);
	snwextramassV= ncfileenv->add_var("SNWEXTRAMASS", ncDouble, timeD);
	snwdzV= ncfileenv->add_var("SNWDZ", ncDouble, timeD, snwlayerD);
	snwageV= ncfileenv->add_var("SNWAGE", ncDouble, timeD, snwlayerD);
	snwrhoV= ncfileenv->add_var("SNWRHO", ncDouble, timeD, snwlayerD);
	snwporV= ncfileenv->add_var("SNWPOR", ncDouble, timeD, snwlayerD);

   	sweV= ncfileenv->add_var("SNWWE", ncDouble, timeD, snwlayerD);
   	tsnwV= ncfileenv->add_var("SNWT", ncDouble, timeD, snwlayerD);
   	swesumV= ncfileenv->add_var("SNWWESUM", ncDouble, timeD);
   	tsnwaveV= ncfileenv->add_var("SNWTAVE", ncDouble, timeD);
   	snwswreflV= ncfileenv->add_var("SNWSWREFL", ncDouble, timeD);
   	snwsublimV= ncfileenv->add_var("SNWSUBLIM", ncDouble, timeD);

 	//soil
   	soilicesumV  = ncfileenv->add_var("SOILICESUM", ncDouble, timeD);
   	soilliqsumV  = ncfileenv->add_var("SOILLIQSUM", ncDouble, timeD);
   	soilvwcshlwV = ncfileenv->add_var("SOILVWCSHLW", ncDouble, timeD);
   	soilvwcdeepV = ncfileenv->add_var("SOILVWCDEEP", ncDouble, timeD);
   	soilvwcmineaV= ncfileenv->add_var("SOILVWCMINEA", ncDouble, timeD);
   	soilvwcminebV= ncfileenv->add_var("SOILVWCMINEB", ncDouble, timeD);
   	soilvwcminecV= ncfileenv->add_var("SOILVWCMINEC", ncDouble, timeD);

   	soiltaveV  = ncfileenv->add_var("SOILTAVE", ncDouble, timeD);
   	soiltshlwV = ncfileenv->add_var("SOILTSHLW", ncDouble, timeD);
   	soiltdeepV = ncfileenv->add_var("SOILTDEEP", ncDouble, timeD);
   	soiltmineaV= ncfileenv->add_var("SOILTMINEA", ncDouble, timeD);
   	soiltminebV= ncfileenv->add_var("SOILTMINEB", ncDouble, timeD);
   	soiltminecV= ncfileenv->add_var("SOILTMINEC", ncDouble, timeD);

   	soiltsV= ncfileenv->add_var("SOILTEM", ncDouble, timeD, soilayerD);
	soilliqV= ncfileenv->add_var("SOILLIQ", ncDouble, timeD, soilayerD);
	soiliceV= ncfileenv->add_var("SOILICE", ncDouble, timeD, soilayerD);
	soilvwcV= ncfileenv->add_var("SOILVWC", ncDouble, timeD, soilayerD);
	soillwcV= ncfileenv->add_var("SOILLWC", ncDouble, timeD, soilayerD);
	soiliwcV= ncfileenv->add_var("SOILIWC", ncDouble, timeD, soilayerD);
	soilfrontzV= ncfileenv->add_var("FRONTZ", ncDouble, timeD, frontD);
	soilfronttypeV= ncfileenv->add_var("FRONTTYPE", ncDouble, timeD, frontD);

	soilwatertabV= ncfileenv->add_var("WATERTABLE", ncDouble, timeD);
	permafrostV= ncfileenv->add_var("PERMAFROST", ncDouble, timeD);
	soilaldV= ncfileenv->add_var("ALD", ncDouble, timeD);
	soilalcV= ncfileenv->add_var("ALC", ncDouble, timeD);

	soilgrowstartV= ncfileenv->add_var("RZGROWSTART", ncDouble, timeD);
	soilgrowendV= ncfileenv->add_var("RZGROWEND", ncDouble, timeD);
	soiltsrtdpV= ncfileenv->add_var("RZTEM", ncDouble, timeD);
	soiltsdegdayV= ncfileenv->add_var("RZDEGDAY", ncDouble, timeD);
	soilrtthawpctV= ncfileenv->add_var("RZTHAWPCT", ncDouble, timeD);

	soilswreflV= ncfileenv->add_var("SOILSWREFL", ncDouble, timeD);
	soilevapV= ncfileenv->add_var("SOILEVAP", ncDouble, timeD);
	soilevap_pV= ncfileenv->add_var("SOILPEVAP", ncDouble, timeD);

	qoverV= ncfileenv->add_var("RUNOFF", ncDouble, timeD);
	qdrainV= ncfileenv->add_var("DRINAGE", ncDouble, timeD);

}

void EnvOutputer::outputCohortEnvVars_dly(EnvDataDly * envod, const int&iy, const int&im, const int &id, const int &ipft, const int & tstepcnt){
 	NcError err(NcError::verbose_nonfatal);

 	if (ipft==0) {

 		if (tstepcnt==0) chtidV->put(&envod->chtid);

 		yearV->put_rec(&iy, tstepcnt);
 		monV->put_rec(&im, tstepcnt);
 		dayV->put_rec(&id, tstepcnt);

 		// atm variables
 		co2V->put_rec(&envod->d_atms.co2, tstepcnt);
 		tairV->put_rec(&envod->d_atms.ta, tstepcnt);
 		nirrV->put_rec(&envod->d_a2l.nirr, tstepcnt);
 		precV->put_rec(&envod->d_a2l.prec, tstepcnt);
 		vpV->put_rec(&envod->d_atmd.vp, tstepcnt);
 		svpV->put_rec(&envod->d_atmd.svp, tstepcnt);
 		vpdV->put_rec(&envod->d_atmd.vpd, tstepcnt);
 		parV->put_rec(&envod->d_a2l.par, tstepcnt);
 		rnflV->put_rec(&envod->d_a2l.rnfl, tstepcnt);
 		snflV->put_rec(&envod->d_a2l.snfl, tstepcnt);

 		// land-surface variables
 		pardownV->put_rec(&envod->d_a2v.pardown, tstepcnt);
 		parabsorbV->put_rec(&envod->d_a2v.parabsorb, tstepcnt);
 		swdownV->put_rec(&envod->d_a2v.swdown, tstepcnt);
 		swinterV->put_rec(&envod->d_a2v.swinter, tstepcnt);
 		rinterV->put_rec(&envod->d_a2v.rinter, tstepcnt);
 		sinterV->put_rec(&envod->d_a2v.sinter, tstepcnt);
 		eetV->put_rec(&envod->d_l2a.eet, tstepcnt);
 		petV->put_rec(&envod->d_l2a.pet, tstepcnt);
 	}

   	//canopy-env variables for ipft
 	vegwaterV->set_cur(tstepcnt, ipft);
   	vegwaterV->put(&envod->d_vegs.rwater, 1, 1);

 	vegsnowV->set_cur(tstepcnt, ipft);
   	vegsnowV->put(&envod->d_vegs.snow, 1, 1);

 	vegrcV->set_cur(tstepcnt, ipft);
 	vegrcV->put(&envod->d_vegd.rc, 1, 1);

 	vegccV->set_cur(tstepcnt, ipft);
 	vegccV->put(&envod->d_vegd.cc, 1, 1);

 	vegbtranV->set_cur(tstepcnt, ipft);
   	vegbtranV->put(&envod->d_vegd.btran, 1, 1);

   	vegm_ppfdV->set_cur(tstepcnt, ipft);
   	vegm_ppfdV->put(&envod->d_vegd.m_ppfd, 1, 1);

   	vegm_vpdV->set_cur(tstepcnt, ipft);
   	vegm_vpdV->put(&envod->d_vegd.m_vpd, 1, 1);

 	vegswreflV->set_cur(tstepcnt, ipft);
   	vegswreflV->put(&envod->d_v2a.swrefl, 1, 1);

   	vegswthflV->set_cur(tstepcnt, ipft);
   	vegswthflV->put(&envod->d_v2g.swthfl, 1, 1);

 	vegevapV->set_cur(tstepcnt, ipft);
   	vegevapV->put(&envod->d_v2a.evap, 1, 1);

   	vegtranV->set_cur(tstepcnt, ipft);
   	vegtranV->put(&envod->d_v2a.tran, 1, 1);

   	vegevap_pV->set_cur(tstepcnt, ipft);
   	vegevap_pV->put(&envod->d_v2a.evap_pet, 1, 1);

   	vegtran_pV->set_cur(tstepcnt, ipft);
   	vegtran_pV->put(&envod->d_v2a.tran_pet, 1, 1);

   	vegsublimV->set_cur(tstepcnt, ipft);
   	vegsublimV->put(&envod->d_v2a.sublim, 1, 1);

 	vegrdripV->set_cur(tstepcnt, ipft);
   	vegrdripV->put(&envod->d_v2g.rdrip, 1, 1);

   	vegrthflV->set_cur(tstepcnt, ipft);
   	vegrthflV->put(&envod->d_v2g.rthfl, 1, 1);

   	vegsdripV->set_cur(tstepcnt, ipft);
   	vegsdripV->put(&envod->d_v2g.sdrip, 1, 1);

   	vegsthflV->set_cur(tstepcnt, ipft);
   	vegsthflV->put(&envod->d_v2g.sthfl, 1, 1);

	if (ipft==0) {
		//snow

		snwlnumV->put_rec(&envod->d_snow.numsnwl, tstepcnt);
		snwthickV->put_rec(&envod->d_snow.thick, tstepcnt);
		snwdenseV->put_rec(&envod->d_snow.dense, tstepcnt);
		snwextramassV->put_rec(&envod->d_snow.extramass, tstepcnt);
		snwdzV->put_rec(&envod->d_snow.dz[0], tstepcnt);
		snwageV->put_rec(&envod->d_snow.age[0], tstepcnt);
		snwrhoV->put_rec(&envod->d_snow.rho[0], tstepcnt);
		snwporV->put_rec(&envod->d_snow.por[0], tstepcnt);

		sweV->put_rec(&envod->d_snws.swe[0], tstepcnt);
		tsnwV->put_rec(&envod->d_snws.tsnw[0], tstepcnt);
		swesumV->put_rec(&envod->d_snws.swesum, tstepcnt);
		tsnwaveV->put_rec(&envod->d_snws.tsnwave, tstepcnt);
		snwswreflV->put_rec(&envod->d_snw2a.swrefl, tstepcnt);
		snwsublimV->put_rec(&envod->d_snw2a.sublim, tstepcnt);

		//soil
		soilicesumV->put_rec(&envod->d_soid.icesum, tstepcnt);
		soilliqsumV->put_rec(&envod->d_soid.liqsum, tstepcnt);
		soilvwcshlwV->put_rec(&envod->d_soid.vwcshlw, tstepcnt);
		soilvwcdeepV->put_rec(&envod->d_soid.vwcdeep, tstepcnt);
		soilvwcmineaV->put_rec(&envod->d_soid.vwcminea, tstepcnt);
		soilvwcminebV->put_rec(&envod->d_soid.vwcmineb, tstepcnt);
		soilvwcminecV->put_rec(&envod->d_soid.vwcminec, tstepcnt);
		soiltaveV->put_rec(&envod->d_soid.tsave, tstepcnt);
		soiltshlwV->put_rec(&envod->d_soid.tshlw, tstepcnt);
		soiltdeepV->put_rec(&envod->d_soid.tdeep, tstepcnt);
		soiltmineaV->put_rec(&envod->d_soid.tminea, tstepcnt);
		soiltminebV->put_rec(&envod->d_soid.tmineb, tstepcnt);
		soiltminecV->put_rec(&envod->d_soid.tminec, tstepcnt);

		soiltsV->put_rec(&envod->d_sois.ts[0], tstepcnt);
		soilliqV->put_rec(&envod->d_sois.liq[0], tstepcnt);
		soiliceV->put_rec(&envod->d_sois.ice[0], tstepcnt);
		soilvwcV->put_rec(&envod->d_soid.vwc[0], tstepcnt);
		soillwcV->put_rec(&envod->d_soid.lwc[0], tstepcnt);
		soiliwcV->put_rec(&envod->d_soid.iwc[0], tstepcnt);
		soilfrontzV->put_rec(&envod->d_sois.frontsz[0], tstepcnt);
		soilfronttypeV->put_rec(&envod->d_sois.frontstype[0], tstepcnt);

		soilwatertabV->put_rec(&envod->d_sois.watertab, tstepcnt);
		permafrostV->put_rec(&envod->d_soid.permafrost, tstepcnt);
		soilaldV->put_rec(&envod->d_soid.ald, tstepcnt);
		soilalcV->put_rec(&envod->d_soid.alc, tstepcnt);

		soilgrowstartV->put_rec(&envod->d_soid.growstart, tstepcnt);
		soilgrowendV->put_rec(&envod->d_soid.growend, tstepcnt);
		soiltsrtdpV->put_rec(&envod->d_soid.tsrtdp, tstepcnt);
		soiltsdegdayV->put_rec(&envod->d_soid.tsdegday, tstepcnt);
		soilrtthawpctV->put_rec(&envod->d_soid.growpct, tstepcnt);

		soilswreflV->put_rec(&envod->d_soi2a.swrefl, tstepcnt);
		soilevapV->put_rec(&envod->d_soi2a.evap, tstepcnt);
		soilevap_pV->put_rec(&envod->d_soi2a.evap_pet, tstepcnt);

		qoverV->put_rec(&envod->d_soi2l.qover, tstepcnt);
		qdrainV->put_rec(&envod->d_soi2l.qdrain, tstepcnt);
	}

}

void EnvOutputer::outputCohortEnvVars_mly(snwstate_dim *m_snow, EnvData* envod, const int&iy, const int&im, const int &ipft, const int & tstepcnt){
 	NcError err(NcError::verbose_nonfatal);

 	if (ipft==0) {
 		if (tstepcnt==0) chtidV->put(&envod->cd->chtid);

 		yearV->put_rec(&iy, tstepcnt);
 		monV->put_rec(&im, tstepcnt);
 		dayV->put_rec(&MISSING_I, tstepcnt);

 		// atm variables
 		co2V->put_rec(&envod->m_atms.co2, tstepcnt);
 		tairV->put_rec(&envod->m_atms.ta, tstepcnt);
 		nirrV->put_rec(&envod->m_a2l.nirr, tstepcnt);
 		precV->put_rec(&envod->m_a2l.prec, tstepcnt);
 		vpV->put_rec(&envod->m_atmd.vp, tstepcnt);
 		svpV->put_rec(&envod->m_atmd.svp, tstepcnt);
 		vpdV->put_rec(&envod->m_atmd.vpd, tstepcnt);
 		parV->put_rec(&envod->m_a2l.par, tstepcnt);
 		rnflV->put_rec(&envod->m_a2l.rnfl, tstepcnt);
 		snflV->put_rec(&envod->m_a2l.snfl, tstepcnt);

 		// land-surface variables
 		pardownV->put_rec(&envod->m_a2v.pardown, tstepcnt);
 		parabsorbV->put_rec(&envod->m_a2v.parabsorb, tstepcnt);
 		swdownV->put_rec(&envod->m_a2v.swdown, tstepcnt);
 		swinterV->put_rec(&envod->m_a2v.swinter, tstepcnt);
 		rinterV->put_rec(&envod->m_a2v.rinter, tstepcnt);
 		sinterV->put_rec(&envod->m_a2v.sinter, tstepcnt);
 		eetV->put_rec(&envod->m_l2a.eet, tstepcnt);
 		petV->put_rec(&envod->m_l2a.pet, tstepcnt);
 	}

   	//canopy-env variables for ipft
 	vegwaterV->set_cur(tstepcnt, ipft);
   	vegwaterV->put(&envod->m_vegs.rwater, 1, 1);

 	vegsnowV->set_cur(tstepcnt, ipft);
   	vegsnowV->put(&envod->m_vegs.snow, 1, 1);

 	vegrcV->set_cur(tstepcnt, ipft);
 	vegrcV->put(&envod->m_vegd.rc, 1, 1);

 	vegccV->set_cur(tstepcnt, ipft);
 	vegccV->put(&envod->m_vegd.cc, 1, 1);

 	vegbtranV->set_cur(tstepcnt, ipft);
   	vegbtranV->put(&envod->m_vegd.btran, 1, 1);

   	vegm_ppfdV->set_cur(tstepcnt, ipft);
   	vegm_ppfdV->put(&envod->m_vegd.m_ppfd, 1, 1);

   	vegm_vpdV->set_cur(tstepcnt, ipft);
   	vegm_vpdV->put(&envod->m_vegd.m_vpd, 1, 1);

 	vegswreflV->set_cur(tstepcnt, ipft);
   	vegswreflV->put(&envod->m_v2a.swrefl, 1, 1);

   	vegswthflV->set_cur(tstepcnt, ipft);
   	vegswthflV->put(&envod->m_v2g.swthfl, 1, 1);

 	vegevapV->set_cur(tstepcnt, ipft);
   	vegevapV->put(&envod->m_v2a.evap, 1, 1);

   	vegtranV->set_cur(tstepcnt, ipft);
   	vegtranV->put(&envod->m_v2a.tran, 1, 1);

   	vegevap_pV->set_cur(tstepcnt, ipft);
   	vegevap_pV->put(&envod->m_v2a.evap_pet, 1, 1);

   	vegtran_pV->set_cur(tstepcnt, ipft);
   	vegtran_pV->put(&envod->m_v2a.tran_pet, 1, 1);

   	vegsublimV->set_cur(tstepcnt, ipft);
   	vegsublimV->put(&envod->m_v2a.sublim, 1, 1);

 	vegrdripV->set_cur(tstepcnt, ipft);
   	vegrdripV->put(&envod->m_v2g.rdrip, 1, 1);

   	vegrthflV->set_cur(tstepcnt, ipft);
   	vegrthflV->put(&envod->m_v2g.rthfl, 1, 1);

   	vegsdripV->set_cur(tstepcnt, ipft);
   	vegsdripV->put(&envod->m_v2g.sdrip, 1, 1);

   	vegsthflV->set_cur(tstepcnt, ipft);
   	vegsthflV->put(&envod->m_v2g.sthfl, 1, 1);

	if (ipft==0) {
		//snow
		snwlnumV->put_rec(&m_snow->numsnwl, tstepcnt);
		snwthickV->put_rec(&m_snow->thick, tstepcnt);
		snwdenseV->put_rec(&m_snow->dense, tstepcnt);
		snwextramassV->put_rec(&m_snow->extramass, tstepcnt);
		snwdzV->put_rec(&m_snow->dz[0], tstepcnt);
		snwageV->put_rec(&m_snow->age[0], tstepcnt);
		snwrhoV->put_rec(&m_snow->rho[0], tstepcnt);
		snwporV->put_rec(&m_snow->por[0], tstepcnt);

		sweV->put_rec(&envod->m_snws.swe[0], tstepcnt);
		tsnwV->put_rec(&envod->m_snws.tsnw[0], tstepcnt);
		swesumV->put_rec(&envod->m_snws.swesum, tstepcnt);
		tsnwaveV->put_rec(&envod->m_snws.tsnwave, tstepcnt);
		snwswreflV->put_rec(&envod->m_snw2a.swrefl, tstepcnt);
		snwsublimV->put_rec(&envod->m_snw2a.sublim, tstepcnt);

		//soil
		soilicesumV->put_rec(&envod->m_soid.icesum, tstepcnt);
		soilliqsumV->put_rec(&envod->m_soid.liqsum, tstepcnt);
		soilvwcshlwV->put_rec(&envod->m_soid.vwcshlw, tstepcnt);
		soilvwcdeepV->put_rec(&envod->m_soid.vwcdeep, tstepcnt);
		soilvwcmineaV->put_rec(&envod->m_soid.vwcminea, tstepcnt);
		soilvwcminebV->put_rec(&envod->m_soid.vwcmineb, tstepcnt);
		soilvwcminecV->put_rec(&envod->m_soid.vwcminec, tstepcnt);
		soiltaveV->put_rec(&envod->m_soid.tsave, tstepcnt);
		soiltshlwV->put_rec(&envod->m_soid.tshlw, tstepcnt);
		soiltdeepV->put_rec(&envod->m_soid.tdeep, tstepcnt);
		soiltmineaV->put_rec(&envod->m_soid.tminea, tstepcnt);
		soiltminebV->put_rec(&envod->m_soid.tmineb, tstepcnt);
		soiltminecV->put_rec(&envod->m_soid.tminec, tstepcnt);

		soiltsV->put_rec(&envod->m_sois.ts[0], tstepcnt);
		soilliqV->put_rec(&envod->m_sois.liq[0], tstepcnt);
		soiliceV->put_rec(&envod->m_sois.ice[0], tstepcnt);
		soilvwcV->put_rec(&envod->m_soid.vwc[0], tstepcnt);
		soillwcV->put_rec(&envod->m_soid.lwc[0], tstepcnt);
		soiliwcV->put_rec(&envod->m_soid.iwc[0], tstepcnt);
		soilfrontzV->put_rec(&envod->m_sois.frontsz[0], tstepcnt);
		soilfronttypeV->put_rec(&envod->m_sois.frontstype[0], tstepcnt);

		soilwatertabV->put_rec(&envod->m_sois.watertab, tstepcnt);
		permafrostV->put_rec(&envod->m_soid.permafrost, tstepcnt);
		soilaldV->put_rec(&envod->m_soid.ald, tstepcnt);
		soilalcV->put_rec(&envod->m_soid.alc, tstepcnt);

		soilgrowstartV->put_rec(&envod->m_soid.growstart, tstepcnt);
		soilgrowendV->put_rec(&envod->m_soid.growend, tstepcnt);
		soiltsrtdpV->put_rec(&envod->m_soid.tsrtdp, tstepcnt);
		soiltsdegdayV->put_rec(&envod->m_soid.tsdegday, tstepcnt);
		soilrtthawpctV->put_rec(&envod->m_soid.growpct, tstepcnt);

		soilswreflV->put_rec(&envod->m_soi2a.swrefl, tstepcnt);
		soilevapV->put_rec(&envod->m_soi2a.evap, tstepcnt);
		soilevap_pV->put_rec(&envod->m_soi2a.evap_pet, tstepcnt);

		qoverV->put_rec(&envod->m_soi2l.qover, tstepcnt);
		qdrainV->put_rec(&envod->m_soi2l.qdrain, tstepcnt);
	}

}

void EnvOutputer::outputCohortEnvVars_yly(snwstate_dim* y_snow, EnvData *envod, const int&iy, const int &ipft, const int & tstepcnt){
 	NcError err(NcError::verbose_nonfatal);

 	if (ipft==0) {

 		if (tstepcnt==0) chtidV->put(&envod->cd->chtid);

 		yearV->put_rec(&iy, tstepcnt);
 		monV->put_rec(&MISSING_I, tstepcnt);
 		dayV->put_rec(&MISSING_I, tstepcnt);

 		// atm variables
 		co2V->put_rec(&envod->y_atms.co2, tstepcnt);
 		tairV->put_rec(&envod->y_atms.ta, tstepcnt);
 		nirrV->put_rec(&envod->y_a2l.nirr, tstepcnt);
 		precV->put_rec(&envod->y_a2l.prec, tstepcnt);
 		vpV->put_rec(&envod->y_atmd.vp, tstepcnt);
 		svpV->put_rec(&envod->y_atmd.svp, tstepcnt);
 		vpdV->put_rec(&envod->y_atmd.vpd, tstepcnt);
 		parV->put_rec(&envod->y_a2l.par, tstepcnt);
 		rnflV->put_rec(&envod->y_a2l.rnfl, tstepcnt);
 		snflV->put_rec(&envod->y_a2l.snfl, tstepcnt);

 		// land-surface variables
 		pardownV->put_rec(&envod->y_a2v.pardown, tstepcnt);
 		parabsorbV->put_rec(&envod->y_a2v.parabsorb, tstepcnt);
 		swdownV->put_rec(&envod->y_a2v.swdown, tstepcnt);
 		swinterV->put_rec(&envod->y_a2v.swinter, tstepcnt);
 		rinterV->put_rec(&envod->y_a2v.rinter, tstepcnt);
 		sinterV->put_rec(&envod->y_a2v.sinter, tstepcnt);
 		eetV->put_rec(&envod->y_l2a.eet, tstepcnt);
 		petV->put_rec(&envod->y_l2a.pet, tstepcnt);
 	}

   	//canopy-env variables for ipft
 	vegwaterV->set_cur(tstepcnt, ipft);
   	vegwaterV->put(&envod->y_vegs.rwater, 1, 1);

 	vegsnowV->set_cur(tstepcnt, ipft);
   	vegsnowV->put(&envod->y_vegs.snow, 1, 1);

 	vegrcV->set_cur(tstepcnt, ipft);
 	vegrcV->put(&envod->y_vegd.rc, 1, 1);

 	vegccV->set_cur(tstepcnt, ipft);
 	vegccV->put(&envod->y_vegd.cc, 1, 1);

 	vegbtranV->set_cur(tstepcnt, ipft);
   	vegbtranV->put(&envod->y_vegd.btran, 1, 1);

   	vegm_ppfdV->set_cur(tstepcnt, ipft);
   	vegm_ppfdV->put(&envod->y_vegd.m_ppfd, 1, 1);

   	vegm_vpdV->set_cur(tstepcnt, ipft);
   	vegm_vpdV->put(&envod->y_vegd.m_vpd, 1, 1);

 	vegswreflV->set_cur(tstepcnt, ipft);
   	vegswreflV->put(&envod->y_v2a.swrefl, 1, 1);

   	vegswthflV->set_cur(tstepcnt, ipft);
   	vegswthflV->put(&envod->y_v2g.swthfl, 1, 1);

 	vegevapV->set_cur(tstepcnt, ipft);
   	vegevapV->put(&envod->y_v2a.evap, 1, 1);

   	vegtranV->set_cur(tstepcnt, ipft);
   	vegtranV->put(&envod->y_v2a.tran, 1, 1);

   	vegevap_pV->set_cur(tstepcnt, ipft);
   	vegevap_pV->put(&envod->y_v2a.evap_pet, 1, 1);

   	vegtran_pV->set_cur(tstepcnt, ipft);
   	vegtran_pV->put(&envod->y_v2a.tran_pet, 1, 1);

   	vegsublimV->set_cur(tstepcnt, ipft);
   	vegsublimV->put(&envod->y_v2a.sublim, 1, 1);

 	vegrdripV->set_cur(tstepcnt, ipft);
   	vegrdripV->put(&envod->y_v2g.rdrip, 1, 1);

   	vegrthflV->set_cur(tstepcnt, ipft);
   	vegrthflV->put(&envod->y_v2g.rthfl, 1, 1);

   	vegsdripV->set_cur(tstepcnt, ipft);
   	vegsdripV->put(&envod->y_v2g.sdrip, 1, 1);

   	vegsthflV->set_cur(tstepcnt, ipft);
   	vegsthflV->put(&envod->y_v2g.sthfl, 1, 1);

	if (ipft==0) {
		//snow
		snwlnumV->put_rec(&y_snow->numsnwl, tstepcnt);
		snwthickV->put_rec(&y_snow->thick, tstepcnt);
		snwdenseV->put_rec(&y_snow->dense, tstepcnt);
		snwextramassV->put_rec(&y_snow->extramass, tstepcnt);
		snwdzV->put_rec(&y_snow->dz[0], tstepcnt);
		snwageV->put_rec(&y_snow->age[0], tstepcnt);
		snwrhoV->put_rec(&y_snow->rho[0], tstepcnt);
		snwporV->put_rec(&y_snow->por[0], tstepcnt);

		sweV->put_rec(&envod->y_snws.swe[0], tstepcnt);
		tsnwV->put_rec(&envod->y_snws.tsnw[0], tstepcnt);
		swesumV->put_rec(&envod->y_snws.swesum, tstepcnt);
		tsnwaveV->put_rec(&envod->y_snws.tsnwave, tstepcnt);
		snwswreflV->put_rec(&envod->y_snw2a.swrefl, tstepcnt);
		snwsublimV->put_rec(&envod->y_snw2a.sublim, tstepcnt);

		//soil
		soilicesumV->put_rec(&envod->y_soid.icesum, tstepcnt);
		soilliqsumV->put_rec(&envod->y_soid.liqsum, tstepcnt);
		soilvwcshlwV->put_rec(&envod->y_soid.vwcshlw, tstepcnt);
		soilvwcdeepV->put_rec(&envod->y_soid.vwcdeep, tstepcnt);
		soilvwcmineaV->put_rec(&envod->y_soid.vwcminea, tstepcnt);
		soilvwcminebV->put_rec(&envod->y_soid.vwcmineb, tstepcnt);
		soilvwcminecV->put_rec(&envod->y_soid.vwcminec, tstepcnt);
		soiltaveV->put_rec(&envod->y_soid.tsave, tstepcnt);
		soiltshlwV->put_rec(&envod->y_soid.tshlw, tstepcnt);
		soiltdeepV->put_rec(&envod->y_soid.tdeep, tstepcnt);
		soiltmineaV->put_rec(&envod->y_soid.tminea, tstepcnt);
		soiltminebV->put_rec(&envod->y_soid.tmineb, tstepcnt);
		soiltminecV->put_rec(&envod->y_soid.tminec, tstepcnt);

		soiltsV->put_rec(&envod->y_sois.ts[0], tstepcnt);
		soilliqV->put_rec(&envod->y_sois.liq[0], tstepcnt);
		soiliceV->put_rec(&envod->y_sois.ice[0], tstepcnt);
		soilvwcV->put_rec(&envod->y_soid.vwc[0], tstepcnt);
		soillwcV->put_rec(&envod->y_soid.lwc[0], tstepcnt);
		soiliwcV->put_rec(&envod->y_soid.iwc[0], tstepcnt);
		soilfrontzV->put_rec(&envod->y_sois.frontsz[0], tstepcnt);
		soilfronttypeV->put_rec(&envod->y_sois.frontstype[0], tstepcnt);

		soilwatertabV->put_rec(&envod->y_sois.watertab, tstepcnt);
		permafrostV->put_rec(&envod->y_soid.permafrost, tstepcnt);
		soilaldV->put_rec(&envod->y_soid.ald, tstepcnt);
		soilalcV->put_rec(&envod->y_soid.alc, tstepcnt);

		soilgrowstartV->put_rec(&envod->y_soid.growstart, tstepcnt);
		soilgrowendV->put_rec(&envod->y_soid.growend, tstepcnt);
		soiltsrtdpV->put_rec(&envod->y_soid.tsrtdp, tstepcnt);
		soiltsdegdayV->put_rec(&envod->y_soid.tsdegday, tstepcnt);
		soilrtthawpctV->put_rec(&envod->y_soid.growpct, tstepcnt);

		soilswreflV->put_rec(&envod->y_soi2a.swrefl, tstepcnt);
		soilevapV->put_rec(&envod->y_soi2a.evap, tstepcnt);
		soilevap_pV->put_rec(&envod->y_soi2a.evap_pet, tstepcnt);

		qoverV->put_rec(&envod->y_soi2l.qover, tstepcnt);
		qdrainV->put_rec(&envod->y_soi2l.qdrain, tstepcnt);
	}

}
