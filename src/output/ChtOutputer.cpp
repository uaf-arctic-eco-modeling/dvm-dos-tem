/*! \file 
*/

#include "ChtOutputer.h"

ChtOutputer::ChtOutputer(){
	
};

ChtOutputer::~ChtOutputer(){
 	if(ncfile!=NULL){
 		ncfile->close();
 		delete ncfile;
 	}
};

void ChtOutputer::init(string & dirfile){

	//file
	ncfname = dirfile;

	ncfile = new NcFile(ncfname.c_str(), NcFile::Replace);

	//dimension
	timeD     = ncfile->add_dim("tstep");
	pftD      = ncfile->add_dim("pft", NUM_PFT);
	rotlayerD = ncfile->add_dim("rootlayer", MAX_ROT_LAY);
	snwlayerD = ncfile->add_dim("snwlayer", MAX_SNW_LAY);
	soilayerD = ncfile->add_dim("soilayer", MAX_SOI_LAY);

    //variables
  	chtidV = ncfile->add_var("CHTID", ncInt);
	yearV  = ncfile->add_var("YEAR", ncInt, timeD);
	monV   = ncfile->add_var("MONTH", ncInt, timeD);

	// veg dimension variables
   	cmttypeV  = ncfile->add_var("CMTTYPE", ncInt, timeD);
   	numpftV   = ncfile->add_var("NUMPFT", ncInt, timeD);
   	cmtfracV  = ncfile->add_var("CMTFRAC", ncDouble, timeD);

   	vegageV      = ncfile->add_var("VEGAGE", ncInt, timeD, pftD);
   	ifwoodyV     = ncfile->add_var("IFWOODY", ncInt, timeD, pftD);
   	ifdeciwoodyV = ncfile->add_var("IFDECIWOODY", ncInt, timeD, pftD);
   	ifperenialV  = ncfile->add_var("IFPERENIAL", ncInt, timeD, pftD);
   	nonvascularV = ncfile->add_var("NONVASCULAR", ncInt, timeD, pftD);

   	vegcovV  = ncfile->add_var("VEGCOV", ncDouble, timeD, pftD);
   	laiV     = ncfile->add_var("LAI", ncDouble, timeD, pftD);
   	fpcV     = ncfile->add_var("FPC", ncDouble, timeD, pftD);
   	rtfracV  = ncfile->add_var("ROOTFRAC", ncDouble, timeD, rotlayerD, pftD);
   	fleafV   = ncfile->add_var("FLEAF", ncDouble, timeD, pftD);
   	ffoliageV= ncfile->add_var("FFOLIAGE", ncDouble, timeD, pftD);

   	// snow dimension variables
   	snwageV = ncfile->add_var("SNWAGE", ncDouble, timeD);
   	snwthickV = ncfile->add_var("SNWTHICK", ncDouble, timeD);
   	snwdenseV = ncfile->add_var("SNWDENSE", ncDouble, timeD);
   	snwrhoV = ncfile->add_var("SNWRHO", ncDouble, timeD);
   	snwextramassV  = ncfile->add_var("SNWEXTRAMASS", ncDouble, timeD);   // 'snowextramass' refers to the snow mass which not enough for a a now layer (partially covered)

 	//soil dimension variables
   	soillayernumV = ncfile->add_var("SOILLAYERNO", ncInt, timeD);
   	soilmossnumV  = ncfile->add_var("MOSSLAYERNO", ncInt, timeD);
   	soilshlwnumV  = ncfile->add_var("SHLWLAYERNO", ncInt, timeD);
   	soildeepnumV  = ncfile->add_var("DEEPLAYERNO", ncInt, timeD);
   	soilminenumV  = ncfile->add_var("MINELAYERNO", ncInt, timeD);

   	soilthickV = ncfile->add_var("SOILTHICK", ncDouble, timeD);
   	mossthickV = ncfile->add_var("MOSSTHICK", ncDouble, timeD);
   	shlwthickV = ncfile->add_var("SHLWTHICK", ncDouble, timeD);
   	deepthickV = ncfile->add_var("DEEPTHICK", ncDouble, timeD);
   	mineathickV = ncfile->add_var("MINEATHICK", ncDouble, timeD);
   	minebthickV = ncfile->add_var("MINEBTHICK", ncDouble, timeD);
   	minecthickV = ncfile->add_var("MINECTHICK", ncDouble, timeD);

   	soilzV      = ncfile->add_var("SOILZ", ncDouble, timeD, soilayerD);
   	soildzV     = ncfile->add_var("SOILDZ", ncDouble, timeD, soilayerD);
   	soiltypeV   = ncfile->add_var("SOILTYPE", ncInt, timeD, soilayerD);
   	soilporoV   = ncfile->add_var("SOILPORO", ncDouble, timeD, soilayerD);
   	soiltextureV= ncfile->add_var("SOILTEXTURE", ncInt, timeD, soilayerD);
   	soilrtfracV = ncfile->add_var("SOILRTFRAC", ncDouble, timeD, soilayerD, pftD);

}

void ChtOutputer::outputCohortDimVars_mly(CohortData *dimod, const int & tstepcnt){
 	NcError err(NcError::verbose_nonfatal);

	if (tstepcnt==0) chtidV->put(&dimod->chtid);
	yearV->put_rec(&dimod->year, tstepcnt);
	monV->put_rec(&dimod->month, tstepcnt);

   	cmttypeV->put_rec(&dimod->cmttype, tstepcnt);
   	numpftV->put_rec(&dimod->numpft, tstepcnt);
   	cmtfracV->put_rec(&dimod->cmtfrac, tstepcnt);

   	vegageV->put_rec(&dimod->m_veg.vegage[0], tstepcnt);
   	ifwoodyV->put_rec(&dimod->m_veg.ifwoody[0], tstepcnt);
   	ifdeciwoodyV->put_rec(&dimod->m_veg.ifdeciwoody[0], tstepcnt);
   	ifperenialV->put_rec(&dimod->m_veg.ifperenial[0], tstepcnt);
   	nonvascularV->put_rec(&dimod->m_veg.nonvascular[0], tstepcnt);

   	vegcovV->put_rec(&dimod->m_veg.vegcov[0], tstepcnt);
   	laiV->put_rec(&dimod->m_veg.lai[0], tstepcnt);
   	fpcV->put_rec(&dimod->m_veg.fpc[0], tstepcnt);
   	rtfracV->put_rec(&dimod->m_veg.frootfrac[0][0], tstepcnt);
   	fleafV->put_rec(&dimod->m_veg.fleaf[0], tstepcnt);
   	ffoliageV->put_rec(&dimod->m_veg.ffoliage[0], tstepcnt);

   	//
   	snwthickV->put_rec(&dimod->m_snow.thick, tstepcnt);
   	snwdenseV->put_rec(&dimod->m_snow.dense, tstepcnt);
   	snwrhoV->put_rec(&dimod->m_snow.rho[0], tstepcnt);
   	snwextramassV->put_rec(&dimod->m_snow.extramass, tstepcnt);
   	snwageV->put_rec(&dimod->m_snow.age[0], tstepcnt);

   	//
   	soillayernumV->put_rec(&dimod->m_soil.numsl, tstepcnt);
   	soilmossnumV->put_rec(&dimod->m_soil.mossnum, tstepcnt);
   	soilshlwnumV->put_rec(&dimod->m_soil.shlwnum, tstepcnt);
   	soildeepnumV->put_rec(&dimod->m_soil.deepnum, tstepcnt);
   	soilminenumV->put_rec(&dimod->m_soil.minenum, tstepcnt);

   	soilthickV->put_rec(&dimod->m_soil.totthick, tstepcnt);
   	mossthickV->put_rec(&dimod->m_soil.mossthick, tstepcnt);
   	shlwthickV->put_rec(&dimod->m_soil.shlwthick, tstepcnt);
   	deepthickV->put_rec(&dimod->m_soil.deepthick, tstepcnt);
   	mineathickV->put_rec(&dimod->m_soil.mineathick, tstepcnt);
   	minebthickV->put_rec(&dimod->m_soil.minebthick, tstepcnt);
   	minecthickV->put_rec(&dimod->m_soil.minecthick, tstepcnt);
   	soilzV->put_rec(&dimod->m_soil.z[0], tstepcnt);
   	soildzV->put_rec(&dimod->m_soil.dz[0], tstepcnt);
   	soiltypeV->put_rec(&dimod->m_soil.type[0], tstepcnt);
   	soilporoV->put_rec(&dimod->m_soil.por[0], tstepcnt);
   	soiltextureV->put_rec(&dimod->m_soil.texture[0], tstepcnt);
   	soilrtfracV->put_rec(&dimod->m_soil.frootfrac[0][0], tstepcnt);

}

void ChtOutputer::outputCohortDimVars_yly(CohortData *dimod, const int & tstepcnt){
 	NcError err(NcError::verbose_nonfatal);

	if (tstepcnt==0) chtidV->put(&dimod->chtid);
	yearV->put_rec(&dimod->year, tstepcnt);
	monV->put_rec(&MISSING_I, tstepcnt);

   	cmttypeV->put_rec(&dimod->cmttype, tstepcnt);
   	numpftV->put_rec(&dimod->numpft, tstepcnt);
   	cmtfracV->put_rec(&dimod->cmtfrac, tstepcnt);

   	vegageV->put_rec(&dimod->y_veg.vegage[0], tstepcnt);
   	ifwoodyV->put_rec(&dimod->y_veg.ifwoody[0], tstepcnt);
   	ifdeciwoodyV->put_rec(&dimod->y_veg.ifdeciwoody[0], tstepcnt);
   	ifperenialV->put_rec(&dimod->y_veg.ifperenial[0], tstepcnt);
   	nonvascularV->put_rec(&dimod->y_veg.nonvascular[0], tstepcnt);

   	vegcovV->put_rec(&dimod->y_veg.vegcov[0], tstepcnt);
   	laiV->put_rec(&dimod->y_veg.lai[0], tstepcnt);
   	fpcV->put_rec(&dimod->y_veg.fpc[0], tstepcnt);
   	rtfracV->put_rec(&dimod->y_veg.frootfrac[0][0], tstepcnt);
   	fleafV->put_rec(&dimod->y_veg.fleaf[0], tstepcnt);
   	ffoliageV->put_rec(&dimod->y_veg.ffoliage[0], tstepcnt);

   	//
   	snwthickV->put_rec(&dimod->y_snow.thick, tstepcnt);
   	snwdenseV->put_rec(&dimod->y_snow.dense, tstepcnt);
   	snwrhoV->put_rec(&dimod->y_snow.rho[0], tstepcnt);
   	snwextramassV->put_rec(&dimod->y_snow.extramass, tstepcnt);
   	snwageV->put_rec(&dimod->y_snow.age[0], tstepcnt);

   	//
   	soillayernumV->put_rec(&dimod->y_soil.numsl, tstepcnt);
   	soilmossnumV->put_rec(&dimod->y_soil.mossnum, tstepcnt);
   	soilshlwnumV->put_rec(&dimod->y_soil.shlwnum, tstepcnt);
   	soildeepnumV->put_rec(&dimod->y_soil.deepnum, tstepcnt);
   	soilminenumV->put_rec(&dimod->y_soil.minenum, tstepcnt);

   	soilthickV->put_rec(&dimod->y_soil.totthick, tstepcnt);
   	mossthickV->put_rec(&dimod->y_soil.mossthick, tstepcnt);
   	shlwthickV->put_rec(&dimod->y_soil.shlwthick, tstepcnt);
   	deepthickV->put_rec(&dimod->y_soil.deepthick, tstepcnt);
   	mineathickV->put_rec(&dimod->y_soil.mineathick, tstepcnt);
   	minebthickV->put_rec(&dimod->y_soil.minebthick, tstepcnt);
   	minecthickV->put_rec(&dimod->y_soil.minecthick, tstepcnt);
   	soilzV->put_rec(&dimod->y_soil.z[0], tstepcnt);
   	soildzV->put_rec(&dimod->y_soil.dz[0], tstepcnt);
   	soiltypeV->put_rec(&dimod->y_soil.type[0], tstepcnt);
   	soilporoV->put_rec(&dimod->y_soil.por[0], tstepcnt);
   	soiltextureV->put_rec(&dimod->y_soil.texture[0], tstepcnt);
   	soilrtfracV->put_rec(&dimod->y_soil.frootfrac[0][0], tstepcnt);

}
