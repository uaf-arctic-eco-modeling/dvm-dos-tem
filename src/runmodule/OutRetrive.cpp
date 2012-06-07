/*
 * This is for
 */

#include "OutRetrive.h"

OutRetrive::OutRetrive(){

};

OutRetrive::~OutRetrive(){

};

void OutRetrive::setCurrentDimensionData(CohortData *cdp){
	cd = cdp;
};

void OutRetrive::setCurrentProcessData(const int & ip, EnvData *edp, BgcData *bdp){
	ed[ip] = edp;
	bd[ip] = bdp;
};

void OutRetrive::setCurrentFireData(FirData *fdp){
	fd = fdp;
};

void OutRetrive::setRestartOutData(RestartData *resodp){
	resod = resodp;
};

void OutRetrive::setRegnOutData(OutDataRegn *regnodp){
    regnod = regnodp;
};

// the following is needed, because daily output is done in the last day of the month, and then
// data storing is the best choice
void OutRetrive::assignSiteDlyOutputBuffer_Env(snwstate_dim d_snow, EnvData *ed, const int &ipft, const int &iday){

	envoddly[ipft][iday].d_snow = d_snow;

    envoddly[ipft][iday].d_atms = ed->d_atms;
    envoddly[ipft][iday].d_vegs = ed->d_vegs;
    envoddly[ipft][iday].d_snws = ed->d_snws;
    envoddly[ipft][iday].d_sois = ed->d_sois;

    envoddly[ipft][iday].d_atmd = ed->d_atmd;
    envoddly[ipft][iday].d_vegd = ed->d_vegd;
    envoddly[ipft][iday].d_snwd = ed->d_snwd;
    envoddly[ipft][iday].d_soid = ed->d_soid;

    envoddly[ipft][iday].d_l2a = ed->d_l2a;
    envoddly[ipft][iday].d_a2l = ed->d_a2l;
    envoddly[ipft][iday].d_a2v = ed->d_a2v;
    envoddly[ipft][iday].d_v2a = ed->d_v2a;
    envoddly[ipft][iday].d_v2g = ed->d_v2g;
    envoddly[ipft][iday].d_soi2l = ed->d_soi2l;
    envoddly[ipft][iday].d_soi2a = ed->d_soi2a;
    envoddly[ipft][iday].d_snw2a = ed->d_snw2a;
    envoddly[ipft][iday].d_snw2soi = ed->d_snw2soi;

};

void OutRetrive::updateRegnOutputBuffer(const int & im){

	if (im==0) {
		regnod->chtid = cd->chtid;
		regnod->year  = cd->year;
	}
	regnod->month[im] = im;

	if (im==11) {
		regnod->ysf =fd->ysf;
	}

	//
	for (int ip=0; ip<cd->numpft; ip++) {

		if (im==11 && regnod->outvarlist[I_growstart]==1) {   // yearly
			regnod->growstart[0][ip]=ed[ip]->y_soid.growstart;
		} else if (regnod->outvarlist[I_growstart]==2) {      // monthly
			regnod->growstart[im][ip]=ed[ip]->m_soid.growstart;
		}

		if (im==11 && regnod->outvarlist[I_growend]==1) {
			regnod->growend[0][ip]=ed[ip]->y_soid.growend;
		} else if (regnod->outvarlist[I_growend]==2) {
			regnod->growend[im][ip]=ed[ip]->m_soid.growend;
		}

		if (im==11 && regnod->outvarlist[I_vegcov]==1) {
			regnod->vegcov[0][ip]=cd->y_veg.vegcov[ip];
		} else if (regnod->outvarlist[I_vegcov]==2) {
			regnod->vegcov[im][ip]=cd->m_veg.vegcov[ip];
		}

		if (im==11 && regnod->outvarlist[I_vegage]==1) {
			regnod->vegage[0][ip]=cd->y_veg.vegage[ip];
		} else if (regnod->outvarlist[I_vegage]==2) {
			regnod->vegage[im][ip]=cd->m_veg.vegage[ip];
		}

		if (im==11 && regnod->outvarlist[I_lai]==1) {
			regnod->lai[0][ip] = cd->y_veg.lai[ip];
		} else if (regnod->outvarlist[I_lai]==2) {
			regnod->lai[im][ip] = cd->m_veg.lai[ip];
		}

		//
		if (im==11 && regnod->outvarlist[I_vegc]==1){
			regnod->vegc[0][ip] = bd[ip]->y_vegs.call;
		} else if (regnod->outvarlist[I_vegc]==2) {
			regnod->vegc[im][ip]= bd[ip]->m_vegs.call;
		}

		if (im==11 && regnod->outvarlist[I_leafc]==1){
			regnod->leafc[0][ip] = bd[ip]->y_vegs.c[I_leaf];
		} else if (regnod->outvarlist[I_leafc]==2) {
			regnod->leafc[im][ip]= bd[ip]->m_vegs.c[I_leaf];
		}

		if (im==11 && regnod->outvarlist[I_stemc]==1){
			regnod->stemc[0][ip] = bd[ip]->y_vegs.c[I_stem];
		} else if (regnod->outvarlist[I_stemc]==2) {
			regnod->stemc[im][ip]= bd[ip]->m_vegs.c[I_stem];
		}

		if (im==11 && regnod->outvarlist[I_rootc]==1){
			regnod->rootc[0][ip] = bd[ip]->y_vegs.c[I_root];
		} else if (regnod->outvarlist[I_rootc]==2) {
			regnod->rootc[im][ip]= bd[ip]->m_vegs.c[I_root];
		}

		if (im==11 && regnod->outvarlist[I_vegn]==1){
			regnod->vegn[0][ip] = bd[ip]->y_vegs.nall;
		} else if (regnod->outvarlist[I_vegn]==2) {
			regnod->vegn[im][ip] = bd[ip]->m_vegs.nall;
		}

		if (im==11 && regnod->outvarlist[I_labn]==1){
			regnod->labn[0][ip] = bd[ip]->y_vegs.labn;
		} else if (regnod->outvarlist[I_labn]==2) {
			regnod->labn[im][ip] = bd[ip]->m_vegs.labn;
		}

		if (im==11 && regnod->outvarlist[I_leafn]==1){
			regnod->leafn[0][ip] = bd[ip]->y_vegs.strn[I_leaf];
		} else if (regnod->outvarlist[I_leafn]==2) {
			regnod->leafn[im][ip] = bd[ip]->m_vegs.strn[I_leaf];
		}

		if (im==11 && regnod->outvarlist[I_stemn]==1){
			regnod->stemn[0][ip] = bd[ip]->y_vegs.strn[I_stem];
		} else if (regnod->outvarlist[I_stemn]==2) {
			regnod->stemn[im][ip] = bd[ip]->m_vegs.strn[I_stem];
		}

		if (im==11 && regnod->outvarlist[I_rootn]==1){
			regnod->rootn[0][ip] = bd[ip]->y_vegs.strn[I_root];
		} else if (regnod->outvarlist[I_rootn]==2) {
			regnod->rootn[im][ip] = bd[ip]->m_vegs.strn[I_root];
		}

		if (im==11 && regnod->outvarlist[I_gpp]==1){
			regnod->gpp[0][ip] = bd[ip]->y_a2v.gppall;
		} else if (regnod->outvarlist[I_gpp]==2) {
			regnod->gpp[im][ip] = bd[ip]->m_a2v.gppall;
		}
		if (im==11 && regnod->outvarlist[I_npp]==1){
			regnod->npp[0][ip] = bd[ip]->y_a2v.nppall;
		} else if (regnod->outvarlist[I_npp]==2) {
			regnod->npp[im][ip] = bd[ip]->m_a2v.nppall;
		}

		if (im==11 && regnod->outvarlist[I_ltrfalc]==1){
			regnod->ltrfalc[0][ip] = bd[ip]->y_v2soi.ltrfalcall;
		} else if (regnod->outvarlist[I_ltrfalc]==2) {
			regnod->ltrfalc[im][ip] = bd[ip]->m_v2soi.ltrfalcall;
		}

		if (im==11 && regnod->outvarlist[I_ltrfaln]==1){
			regnod->ltrfaln[0][ip] = bd[ip]->y_v2soi.ltrfalnall;
		} else if (regnod->outvarlist[I_ltrfaln]==2) {
			regnod->ltrfaln[im][ip] = bd[ip]->m_v2soi.ltrfalnall;
		}

		if (im==11 && regnod->outvarlist[I_nuptake]==1){
			regnod->nuptake[0][ip] = bd[ip]->y_soi2v.lnuptake+bd[ip]->y_soi2v.snuptakeall;
		} else if (regnod->outvarlist[I_nuptake]==2) {
			regnod->nuptake[im][ip] = bd[ip]->m_soi2v.lnuptake+bd[ip]->m_soi2v.snuptakeall;
		}
	}

	//
	if (im==11 && regnod->outvarlist[I_rh]==1){
		regnod->rh[0] = bd[0]->y_soi2a.rhrawcsum             //note: 'bd' soil portion MUST BE exactly SAME for all PFTs
				       +bd[0]->y_soi2a.rhsomasum
				       +bd[0]->y_soi2a.rhsomprsum
				       +bd[0]->y_soi2a.rhsomcrsum;
	} else if (regnod->outvarlist[I_rh]==2) {
		regnod->rh[im] = bd[0]->m_soi2a.rhrawcsum
			                +bd[0]->m_soi2a.rhsomasum
			                +bd[0]->m_soi2a.rhsomprsum
			                +bd[0]->m_soi2a.rhsomcrsum;
	}

	if (im==11 && regnod->outvarlist[I_permafrost]==1) {
		regnod->permafrost[0] = ed[0]->y_soid.permafrost;
	} else if (regnod->outvarlist[I_permafrost]==2) {
		regnod->permafrost[im]= ed[0]->m_soid.permafrost;
	}

	if (im==11 && regnod->outvarlist[I_mossdz]==1){
		regnod->mossdz[0] = cd->y_soil.mossthick;
	} else if (regnod->outvarlist[I_mossdz]==2) {
		regnod->mossdz[im] = cd->m_soil.mossthick;
	}

	if (im==11 && regnod->outvarlist[I_oshlwdz]==1){
		regnod->oshlwdz[0] = cd->y_soil.shlwthick;
	} else if (regnod->outvarlist[I_oshlwdz]==2) {
		regnod->oshlwdz[im]= cd->m_soil.shlwthick;
	}

	if (im==11 && regnod->outvarlist[I_odeepdz]==1){
		regnod->odeepdz[0] = cd->y_soil.deepthick;
	} else if (regnod->outvarlist[I_odeepdz]==2) {
		regnod->odeepdz[im] = cd->m_soil.deepthick;
	}

	///////////////////
	if (im==11 && regnod->outvarlist[I_mineadz]==1){
		regnod->mineadz[0] = cd->y_soil.mineathick;
	} else if (regnod->outvarlist[I_mineadz]==2) {
		regnod->mineadz[im]= cd->m_soil.mineathick;
	}

	if (im==11 && regnod->outvarlist[I_minebdz]==1){
		regnod->minebdz[0] = cd->y_soil.minebthick;
	} else if (regnod->outvarlist[I_minebdz]==2) {
		regnod->minebdz[im]= cd->m_soil.minebthick;
	}

	if (im==11 && regnod->outvarlist[I_minecdz]==1){
		regnod->minecdz[0] = cd->y_soil.minecthick;
	} else if (regnod->outvarlist[I_minecdz]==2) {
		regnod->minecdz[im]= cd->m_soil.minecthick;
	}

	if (im==11 && regnod->outvarlist[I_oshlwc]==1){
		regnod->oshlwc[0] = bd[0]->y_soid.shlwc;
	} else if (regnod->outvarlist[I_oshlwc]==2) {
		regnod->oshlwc[im]= bd[0]->m_soid.shlwc;
	}

	if (im==11 && regnod->outvarlist[I_odeepc]==1){
		regnod->odeepc[0] = bd[0]->y_soid.deepc;
	} else if (regnod->outvarlist[I_odeepc]==2) {
		regnod->odeepc[im]= bd[0]->m_soid.deepc;
	}

	if (im==11 && regnod->outvarlist[I_mineac]==1){
		regnod->mineac[0] = cd->y_soil.shlwthick;
	} else if (regnod->outvarlist[I_mineac]==2) {
		regnod->mineac[im] = ed[0]->m_soid.permafrost;
	}

	if (im==11 && regnod->outvarlist[I_minebc]==1){
		regnod->minebc[0] = cd->y_soil.shlwthick;
	} else if (regnod->outvarlist[I_minebc]==2) {
		regnod->minebc[im] = ed[0]->m_soid.permafrost;
	}

	if (im==11 && regnod->outvarlist[I_minecc]==1){
		regnod->minecc[0] = cd->y_soil.shlwthick;
	} else if (regnod->outvarlist[I_minecc]==2) {
		regnod->minecc[im] = ed[0]->m_soid.permafrost;
	}

	if (im==11 && regnod->outvarlist[I_orgn]==1){
		regnod->orgn[0] = bd[0]->y_soid.orgnsum;
	} else if (regnod->outvarlist[I_orgn]==2) {
		regnod->orgn[im]= bd[0]->m_soid.orgnsum;
	}

	if (im==11 && regnod->outvarlist[I_avln]==1){
		regnod->avln[0] = bd[0]->y_soid.avlnsum;
	} else if (regnod->outvarlist[I_avln]==2) {
		regnod->avln[im]= bd[0]->m_soid.avlnsum;
	}

	if (im==11 && regnod->outvarlist[I_netnmin]==1){
		regnod->netnmin[0] = bd[0]->y_soi2soi.netnminsum;
	} else if (regnod->outvarlist[I_netnmin]==2) {
		regnod->netnmin[im]= bd[0]->m_soi2soi.netnminsum;
	}

	if (im==11 && regnod->outvarlist[I_orgninput]==1){
		regnod->orgninput[0] = bd[0]->y_a2soi.orgninput;
	} else if (regnod->outvarlist[I_orgninput]==2) {
		regnod->orgninput[im]= bd[0]->m_a2soi.orgninput;
	}

	if (im==11 && regnod->outvarlist[I_avlninput]==1){
		regnod->avlninput[0] = bd[0]->y_a2soi.avlninput;
	} else if (regnod->outvarlist[I_avlninput]==2) {
		regnod->avlninput[im]= bd[0]->m_a2soi.avlninput;
	}

	if (im==11 && regnod->outvarlist[I_doclost]==1){
		regnod->doclost[0] = bd[0]->y_soi2l.doclost;
	} else if (regnod->outvarlist[I_doclost]==2) {
		regnod->doclost[im]= bd[0]->m_soi2l.doclost;
	}

	if (im==11 && regnod->outvarlist[I_orgnlost]==1){
		regnod->orgnlost[0] = bd[0]->y_soi2l.orgnlost;
	} else if (regnod->outvarlist[I_orgnlost]==2) {
		regnod->orgnlost[im]= bd[0]->m_soi2l.orgnlost;
	}

	if (im==11 && regnod->outvarlist[I_avlnlost]==1){
		regnod->avlnlost[0] = bd[0]->y_soi2l.avlnlost;
	} else if (regnod->outvarlist[I_avlnlost]==2) {
		regnod->avlnlost[im]= bd[0]->m_soi2l.avlnlost;
	}

  	//
	if (im==11 && regnod->outvarlist[I_eet]==1){
		regnod->eet[0] = ed[0]->y_l2a.eet;
	} else if (regnod->outvarlist[I_eet]==2) {
		regnod->eet[im]= ed[0]->m_l2a.eet;
	}

	if (im==11 && regnod->outvarlist[I_pet]==1){
		regnod->pet[0] = ed[0]->y_l2a.pet;
	} else if (regnod->outvarlist[I_pet]==2) {
		regnod->pet[im]= ed[0]->m_l2a.pet;
	}

	if (im==11 && regnod->outvarlist[I_qinfl]==1){
		regnod->qinfl[0] = ed[0]->y_soi2l.qinfl;
	} else if (regnod->outvarlist[I_qinfl]==2) {
		regnod->qinfl[im]= ed[0]->m_soi2l.qinfl;
	}

	if (im==11 && regnod->outvarlist[I_qdrain]==1){
		regnod->qdrain[0] = ed[0]->y_soi2l.qdrain;
	} else if (regnod->outvarlist[I_qdrain]==2) {
		regnod->qdrain[im]= ed[0]->m_soi2l.qdrain;
	}

	if (im==11 && regnod->outvarlist[I_qrunoff]==1){
		regnod->qrunoff[0] = ed[0]->y_soi2l.qover;
	} else if (regnod->outvarlist[I_qrunoff]==2) {
		regnod->qrunoff[im]= ed[0]->m_soi2l.qover;
	}

	if (im==11 && regnod->outvarlist[I_snwthick]==1){
		regnod->snwthick[0] = cd->y_snow.thick;
	} else if (regnod->outvarlist[I_snwthick]==2) {
		regnod->snwthick[im]= cd->m_snow.thick;
	}

	if (im==11 && regnod->outvarlist[I_swe]==1){
		regnod->swe[0] = ed[0]->y_snws.swesum;
	} else if (regnod->outvarlist[I_swe]==2) {
		regnod->swe[im] = ed[0]->m_snws.swesum;
	}

	if (im==11 && regnod->outvarlist[I_wtd]==1){
		regnod->wtd[0] = ed[0]->y_sois.watertab;
	} else if (regnod->outvarlist[I_wtd]==2) {
		regnod->wtd[im]= ed[0]->m_sois.watertab;
	}

	if (im==11 && regnod->outvarlist[I_alc]==1){
		regnod->alc[0] = ed[0]->y_soid.alc;
	} else if (regnod->outvarlist[I_alc]==2) {
		regnod->alc[im]= ed[0]->m_soid.alc;
	}

	if (im==11 && regnod->outvarlist[I_ald]==1){
		regnod->ald[0] = ed[0]->y_soid.ald;
	} else if (regnod->outvarlist[I_ald]==2) {
		regnod->ald[im]= ed[0]->m_soid.ald;
	}

///
	if (im==11 && regnod->outvarlist[I_vwcshlw]==1){
		regnod->vwcshlw[0] = ed[0]->y_soid.vwcshlw;
	} else if (regnod->outvarlist[I_vwcshlw]==2) {
		regnod->vwcshlw[im]= ed[0]->m_soid.vwcshlw;
	}

	if (im==11 && regnod->outvarlist[I_vwcdeep]==1){
		regnod->vwcdeep[0] = ed[0]->y_soid.vwcdeep;
	} else if (regnod->outvarlist[I_vwcdeep]==2) {
		regnod->vwcdeep[im] = ed[0]->m_soid.vwcdeep;
	}

	if (im==11 && regnod->outvarlist[I_vwcminea]==1){
		regnod->vwcminea[0] = ed[0]->y_soid.vwcminea;
	} else if (regnod->outvarlist[I_vwcminea]==2) {
		regnod->vwcminea[im]= ed[0]->m_soid.vwcminea;
	}

	if (im==11 && regnod->outvarlist[I_vwcmineb]==1){
		regnod->vwcmineb[0] = ed[0]->y_soid.vwcmineb;
	} else if (regnod->outvarlist[I_vwcmineb]==2) {
		regnod->vwcmineb[im]= ed[0]->m_soid.vwcmineb;
	}

	if (im==11 && regnod->outvarlist[I_vwcminec]==1){
		regnod->vwcminec[0] = ed[0]->y_soid.vwcminec;
	} else if (regnod->outvarlist[I_vwcminec]==2) {
		regnod->vwcminec[im]= ed[0]->m_soid.vwcminec;
	}

	if (im==11 && regnod->outvarlist[I_tshlw]==1){
		regnod->tshlw[0] = ed[0]->y_soid.tshlw;
	} else if (regnod->outvarlist[I_tshlw]==2) {
		regnod->tshlw[im] = ed[0]->y_soid.tshlw;
	}

	if (im==11 && regnod->outvarlist[I_tdeep]==1){
		regnod->tdeep[0] = ed[0]->y_soid.tdeep;
	} else if (regnod->outvarlist[I_tdeep]==2) {
		regnod->tdeep[im] = ed[0]->m_soid.tdeep;
	}

	if (im==11 && regnod->outvarlist[I_tminea]==1){
		regnod->tminea[0] = ed[0]->y_soid.tminea;
	} else if (regnod->outvarlist[I_tminea]==2) {
		regnod->tminea[im] = ed[0]->m_soid.tminea;
	}

	if (im==11 && regnod->outvarlist[I_tmineb]==1){
		regnod->tmineb[0] = ed[0]->y_soid.tmineb;
	} else if (regnod->outvarlist[I_tmineb]==2) {
		regnod->tmineb[im] = ed[0]->m_soid.tmineb;
	}

	if (im==11 && regnod->outvarlist[I_tminec]==1){
		regnod->tminec[0] = ed[0]->y_soid.tminec;
	} else if (regnod->outvarlist[I_tminec]==2) {
		regnod->tminec[im] = ed[0]->m_soid.tminec;
	}

	if (im==11 && regnod->outvarlist[I_hkshlw]==1){
		regnod->hkshlw[0] = ed[0]->y_soid.hkshlw;
	} else if (regnod->outvarlist[I_hkshlw]==2) {
		regnod->hkshlw[im] = ed[0]->m_soid.hkshlw;
	}

	if (im==11 && regnod->outvarlist[I_hkdeep]==1){
		regnod->hkdeep[0] = ed[0]->y_soid.hkdeep;
	} else if (regnod->outvarlist[I_hkdeep]==2) {
		regnod->hkdeep[im] = ed[0]->m_soid.hkdeep;
	}

	if (im==11 && regnod->outvarlist[I_hkminea]==1){
		regnod->hkminea[0] = ed[0]->y_soid.hkminea;
	} else if (regnod->outvarlist[I_hkminea]==2) {
		regnod->hkminea[im] = ed[0]->m_soid.hkminea;
	}

	if (im==11 && regnod->outvarlist[I_hkmineb]==1){
		regnod->hkmineb[0] = ed[0]->y_soid.hkmineb;
	} else if (regnod->outvarlist[I_hkmineb]==2) {
		regnod->hkmineb[im] = ed[0]->m_soid.hkmineb;
	}

	if (im==11 && regnod->outvarlist[I_hkminec]==1){
		regnod->hkminec[0] = ed[0]->y_soid.hkminec;
	} else if (regnod->outvarlist[I_hkminec]==2) {
		regnod->hkminec[im] = ed[0]->m_soid.hkminec;
	}

	if (im==11 && regnod->outvarlist[I_tcshlw]==1){
		regnod->tcshlw[0] = ed[0]->y_soid.tcshlw;
	} else if (regnod->outvarlist[I_tcshlw]==2) {
		regnod->tcshlw[im] = ed[0]->m_soid.tcshlw;
	}

	if (im==11 && regnod->outvarlist[I_tcdeep]==1){
		regnod->tcdeep[0] = ed[0]->y_soid.tcdeep;
	} else if (regnod->outvarlist[I_tcdeep]==2) {
		regnod->tcdeep[im] = ed[0]->m_soid.tcdeep;
	}

	if (im==11 && regnod->outvarlist[I_tcminea]==1){
		regnod->tcminea[0] = ed[0]->y_soid.tcminea;
	} else if (regnod->outvarlist[I_tcminea]==2) {
		regnod->tcminea[im] = ed[0]->m_soid.tcminea;
	}

	if (im==11 && regnod->outvarlist[I_tcmineb]==1){
		regnod->tcmineb[0] = ed[0]->y_soid.tcmineb;
	} else if (regnod->outvarlist[I_tcmineb]==2) {
		regnod->tcmineb[im] = ed[0]->m_soid.tcmineb;
	}

	if (im==11 && regnod->outvarlist[I_tcminec]==1){
		regnod->tcminec[0] = ed[0]->y_soid.tcminec;
	} else if (regnod->outvarlist[I_tcminec]==2) {
		regnod->tcminec[im] = ed[0]->m_soid.tcminec;
	}

	if (im==11 && regnod->outvarlist[I_tbotrock]==1){
		regnod->tbotrock[0] = ed[0]->y_soid.tbotrock;
	} else if (regnod->outvarlist[I_tbotrock]==2) {
		regnod->tbotrock[im] = ed[0]->m_soid.tbotrock;
	}

///////////////////////
	if (im==11 && regnod->outvarlist[I_burnthick]==1){
		regnod->burnthick[0] = fd->fire_soid.burnthick;
	} else if (regnod->outvarlist[I_burnthick]==2) {
		regnod->burnthick[im]= fd->fire_soid.burnthick;
	}

	if (im==11 && regnod->outvarlist[I_burnsoic]==1){
		regnod->burnsoic[0] = fd->fire_soi2a.orgc;
	} else if (regnod->outvarlist[I_burnsoic]==2) {
		regnod->burnsoic[im] = fd->fire_soi2a.orgc;
	}

	if (im==11 && regnod->outvarlist[I_burnvegc]==1){
		regnod->burnvegc[0] = fd->fire_v2a.orgc;
	} else if (regnod->outvarlist[I_burnvegc]==2) {
		regnod->burnvegc[im]= fd->fire_v2a.orgc;
	}

	if (im==11 && regnod->outvarlist[I_burnsoin]==1){
		regnod->burnsoin[0] = fd->fire_soi2a.orgn;
	} else if (regnod->outvarlist[I_burnsoin]==2) {
		regnod->burnsoin[im]= fd->fire_soi2a.orgn;
	}

	if (im==11 && regnod->outvarlist[I_burnvegn]==1){
		regnod->burnvegn[0] = fd->fire_v2a.orgn;
	} else if (regnod->outvarlist[I_burnvegn]==2) {
		regnod->burnvegn[im]= fd->fire_v2a.orgn;
	}

	if (im==11 && regnod->outvarlist[I_burnretainc]==1){
		regnod->burnretainc[0] = fd->fire_v2soi.abvc+fd->fire_v2soi.blwc;   //retained abvc is burned residue, retained blwc is burn-caused root death
	} else if (regnod->outvarlist[I_burnretainc]==2) {
		regnod->burnretainc[im]= fd->fire_v2soi.abvc+fd->fire_v2soi.blwc;
	}

	if (im==11 && regnod->outvarlist[I_burnretainn]==1){
		regnod->burnretainn[0] = fd->fire_v2soi.abvn+fd->fire_v2soi.blwn;
	} else if (regnod->outvarlist[I_burnretainn]==2) {
		regnod->burnretainn[im]= fd->fire_v2soi.abvn+fd->fire_v2soi.blwn;
	}

};

// NOTE: 'resod', restartoutput data, a dataset to resume a complete model run if model is paused
// This is useful and very needed for carrying out a series of model implementation, i.e., from eq->spinup->transient->scenario  runs
// OR, potentially the model can run spatially for one time-step (rather than in time series for ONE cohort)
void OutRetrive::updateRestartOutputBuffer(){

 		resod->reinitValue();
 	
 		//
 		resod->chtid = cd->chtid;

 		// atm
 		resod->dsr         = ed[0]->d_atms.dsr;
 		resod->firea2sorgn = fd->fire_a2soi.orgn;     //this is 'fire_a2soi.orgn' to re-deposit fire-emitted N in one FRI

 		//vegegetation
 		resod->numpft= cd->numpft;
 		resod->ysf   = fd->ysf;

 	    for (int ip=0; ip<NUM_PFT; ip++) {
 	    	resod->ifwoody[ip]    = cd->m_veg.ifwoody[ip];
 	    	resod->ifdeciwoody[ip]= cd->m_veg.ifdeciwoody[ip];
 	    	resod->ifperenial[ip] = cd->m_veg.ifperenial[ip];
 	    	resod->nonvascular[ip]= cd->m_veg.nonvascular[ip];

 	    	resod->vegage[ip] = cd->m_veg.vegage[ip];
 	    	resod->vegcov[ip] = cd->m_veg.vegcov[ip];
 	    	resod->lai[ip]    = cd->m_veg.lai[ip];
 	    	for (int i=0; i<MAX_ROT_LAY; i++) {
 	    		resod->rootfrac[i][ip] = cd->m_veg.frootfrac[i][ip];
 	    	}

 	    	resod->vegwater[ip] = ed[ip]->m_vegs.rwater;             //canopy water - 'vegs_env'
 	    	resod->vegsnow[ip]  = ed[ip]->m_vegs.snow;              //canopy snow  - 'vegs_env'

 	    	for (int i=0; i<NUM_PFT_PART; i++) {
 	    		resod->vegc[i][ip] = bd[ip]->m_vegs.c[i];   // - 'vegs_bgc'
 	    		resod->strn[i][ip] = bd[ip]->m_vegs.strn[i];
 	    	}
 	    	resod->labn[ip]      = bd[ip]->m_vegs.labn;
 	    	resod->deadc[ip]     = bd[ip]->m_vegs.deadc;
 	    	resod->deadn[ip]     = bd[ip]->m_vegs.deadn;

    		deque<double> tmpdeque1 = cd->toptque[ip];
 	    	int recnum = tmpdeque1.size();
 	    	for (int i=0; i<recnum; i++) {
 	    		resod->toptA[i][ip] = tmpdeque1[i];
 	    	}

 	    	deque<double> tmpdeque2 = cd->prvunnormleafmxque[ip];
 	    	recnum = tmpdeque2.size();
 	    	for (int i=0; i<recnum; i++) {
 	    		resod->unnormleafmxA[i][ip] = tmpdeque2[i];
 	    	}

  	    	deque<double> tmpdeque3 = cd->prvgrowingttimeque[ip];
 	    	recnum = tmpdeque3.size();
 	    	for (int i=0; i<recnum; i++) {
 	    		resod->growingttimeA[i][ip]= tmpdeque3[i];
 	    	}

 	    	resod->prvfoliagemx[ip] = cd->m_veg.prvfoliagemx[ip];        // this is for f(foliage) in GPP to be sure f(foliage) not going down

 	    	deque<double> tmpdeque4 = ed[ip]->eetmxque;
 	    	recnum = tmpdeque4.size();
 	    	for (int i=0; i<recnum; i++) {
 	    		resod->eetmxA[i][ip]= tmpdeque4[i];
 	    	}


	    }

 	    // snow
 	    resod->numsnwl = cd->d_snow.numsnwl;
 	    resod->snwextramass = cd->d_snow.extramass;
 	    for(int il =0;il<cd->d_snow.numsnwl; il++){
 	    	resod->DZsnow[il]  = cd->d_snow.dz[il];
 	    	resod->AGEsnow[il] = cd->d_snow.age[il];
 	    	resod->RHOsnow[il] = cd->d_snow.rho[il];

 	    	resod->TSsnow[il]  = ed[0]->d_snws.tsnw[il];  // NOTE: for all PFT, ground 'ed' is same, BE sure that is done
 	    	resod->LIQsnow[il] = ed[0]->d_snws.snwliq[il];
 	    	resod->ICEsnow[il] = ed[0]->d_snws.snwice[il];
 		}
 		
 	    //ground-soil
 	    resod->numsl  = cd->d_soil.numsl;     //actual number of soil layers
 	    resod->monthsfrozen = ed[0]->monthsfrozen;
 	    resod->watertab   = ed[0]->d_sois.watertab;
 		for(int il =0;il<cd->d_soil.numsl; il++){
 			resod->DZsoil[il]   = cd->d_soil.dz[il];
 			resod->AGEsoil[il]  = cd->d_soil.age[il];
 			resod->TYPEsoil[il] = cd->d_soil.type[il];
 			resod->TEXTUREsoil[il]= cd->d_soil.texture[il];

 			resod->TSsoil[il]    = ed[0]->d_sois.ts[il];
 			resod->LIQsoil[il]   = ed[0]->d_sois.liq[il];
 			resod->ICEsoil[il]   = ed[0]->d_sois.ice[il];
 			resod->FROZENFRACsoil[il]= ed[0]->d_sois.frozenfrac[il];


 		}

 		for(int il =0;il<MAX_ROC_LAY; il++){
 			resod->TSrock[il] = ed[0]->d_sois.trock[il];
 			resod->DZrock[il] = ROCKTHICK[il];
 		}

 		for(int il =0;il<MAX_NUM_FNT; il++){
 			resod->frontZ[il]  = ed[0]->d_sois.frontsz[il];
 			resod->frontFT[il] = ed[0]->d_sois.frontstype[il];
 		}

 		//
 		resod->wdebrisc = bd[0]->m_sois.wdebrisc;
 		resod->wdebrisn = bd[0]->m_sois.wdebrisn;
 		for(int il =0;il<cd->m_soil.numsl; il++){
 			resod->rawc[il]  = bd[0]->m_sois.rawc[il];
 			resod->soma[il]  = bd[0]->m_sois.soma[il];
 			resod->sompr[il] = bd[0]->m_sois.sompr[il];
 			resod->somcr[il] = bd[0]->m_sois.somcr[il];

 			resod->orgn[il] = bd[0]->m_sois.orgn[il];
 			resod->avln[il] = bd[0]->m_sois.avln[il];

 			resod->prvltrfcn[il] = bd[0]->prvltrfcn[il];
 		}

};

