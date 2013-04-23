#include "EnvData.h"

EnvData::EnvData(){

};

EnvData::~EnvData(){
	
};

//re-initialize EnvData class explicitly
void EnvData::clear(){
   // daily
    d_atms = atmstate_env();
    d_vegs = vegstate_env();
    d_snws = snwstate_env();
    d_sois = soistate_env();

    d_atmd = atmdiag_env();
    d_vegd = vegdiag_env();
    d_snwd = snwdiag_env();
    d_soid = soidiag_env();

    d_l2a = lnd2atm_env();
    d_a2l = atm2lnd_env();
    d_a2v = atm2veg_env();
    d_v2a = veg2atm_env();
    d_v2g = veg2gnd_env();
    d_soi2l = soi2lnd_env();
    d_soi2a = soi2atm_env();
    d_snw2a = snw2atm_env();
    d_snw2soi = snw2soi_env();

   // monthly
    m_atms = atmstate_env();
    m_vegs = vegstate_env();
    m_snws = snwstate_env();
    m_sois = soistate_env();

    m_atmd = atmdiag_env();
    m_vegd = vegdiag_env();
    m_snwd = snwdiag_env();
    m_soid = soidiag_env();

    m_l2a = lnd2atm_env();
    m_a2l = atm2lnd_env();
    m_a2v = atm2veg_env();
    m_v2a = veg2atm_env();
    m_v2g = veg2gnd_env();
    m_soi2l = soi2lnd_env();
    m_soi2a = soi2atm_env();
    m_snw2a = snw2atm_env();
    m_snw2soi = snw2soi_env();

    // monthly
    y_atms = atmstate_env();
    y_vegs = vegstate_env();
    y_snws = snwstate_env();
    y_sois = soistate_env();

    y_atmd = atmdiag_env();
    y_vegd = vegdiag_env();
    y_snwd = snwdiag_env();
    y_soid = soidiag_env();

    y_l2a = lnd2atm_env();
    y_a2l = atm2lnd_env();
    y_a2v = atm2veg_env();
    y_v2a = veg2atm_env();
    y_v2g = veg2gnd_env();
    y_soi2l = soi2lnd_env();
    y_soi2a = soi2atm_env();
    y_snw2a = snw2atm_env();
    y_snw2soi = snw2soi_env();

    //
    monthsfrozen  = 0.;
	rtfrozendays  = 0;
	rtunfrozendays= 0;

	cd->clear();
};

// initialize yearly accumulators
void EnvData::atm_beginOfYear(){

   	y_atms.ta   = 0.;
   	y_atms.co2  = 0.;
   	y_atmd.vp   = 0.;
   	y_atmd.svp  = 0.;
   	y_atmd.vpd  = 0.;

   	//atm to land (including both veg/ground)
   	y_a2l.nirr = 0;
	y_a2l.par  = 0;
	y_a2l.prec = 0;
	y_a2l.rnfl = 0;
	y_a2l.snfl = 0;

	// atm to veg only
	y_a2v.pardown  = 0.; // for photosynthesis
	y_a2v.parabsorb= 0.;
	y_a2v.swdown  = 0.;  // for energy balance
	y_a2v.swinter = 0.;
	y_a2v.rnfl    = 0.;  // for water balance
	y_a2v.rinter  = 0.;
	y_a2v.snfl    = 0.;
	y_a2v.sinter  = 0.;

	//
	y_l2a.eet = 0.;
  	y_l2a.pet = 0.;

}

void EnvData::veg_beginOfYear(){

	y_vegs.rwater  = 0.;
	y_vegs.snow    = 0.;

	y_vegd.rc      = 0.;
	y_vegd.cc      = 0.;
	y_vegd.btran   = 0.;
	y_vegd.m_ppfd  = 0.;
	y_vegd.m_vpd   = 0.;

	y_v2a.swrefl   = 0.;
	y_v2a.evap     = 0.;
	y_v2a.tran     = 0.;
	y_v2a.evap_pet = 0.;
	y_v2a.tran_pet = 0.;
	y_v2a.sublim   = 0.;

	y_v2g.swthfl   = 0.;
	y_v2g.rdrip    = 0.;
	y_v2g.rthfl    = 0.;
	y_v2g.sdrip    = 0.;
	y_v2g.sthfl    = 0.;

};

void EnvData::grnd_beginOfYear(){

	//snow
	for (int i=0; i<MAX_SNW_LAY; i++){
		y_snws.swe[i]   = 0.;
		y_snws.snwice[i]= 0.;
		y_snws.snwliq[i]= 0.;
		y_snws.tsnw[i]  = 0.;
	}
	y_snws.swesum  = 0.;
	y_snws.tsnwave = 0.;

	y_snwd.snowfreeFst= MISSING_I;
 	y_snwd.snowfreeLst= MISSING_I;

	y_snw2a.swrefl = 0.;
	y_snw2a.sublim = 0.;

	y_snw2soi.melt = 0.;

 	//soil
   	y_soid.icesum  = 0.;
   	y_soid.liqsum  = 0.;
   	y_soid.vwcshlw = 0.;
   	y_soid.vwcdeep = 0.;
   	y_soid.vwcminea= 0.;
   	y_soid.vwcmineb= 0.;
   	y_soid.vwcminec= 0.;

   	y_soid.tsave = 0.;
   	y_soid.tshlw = 0.;
   	y_soid.tdeep = 0.;
   	y_soid.tminea= 0.;
   	y_soid.tmineb= 0.;
   	y_soid.tminec= 0.;

   	y_soid.tcshlw = 0.;
   	y_soid.tcdeep = 0.;
   	y_soid.tcminea= 0.;
   	y_soid.tcmineb= 0.;
   	y_soid.tcminec= 0.;

   	y_soid.hkshlw = 0.;
   	y_soid.hkdeep = 0.;
   	y_soid.hkminea= 0.;
   	y_soid.hkmineb= 0.;
   	y_soid.hkminec= 0.;

   	for (int il=0; il<MAX_SOI_LAY; il++){
  		y_sois.frozenfrac[il]  = 0.;

   		y_sois.ts[il]      = 0.;
   		y_sois.liq[il]     = 0.;
   		y_sois.ice[il]     = 0.;
   	}
	y_sois.watertab   = 0.;
	y_sois.draindepth = 0.;

   	for (int il=0; il<MAX_SOI_LAY; il++){
		y_soid.vwc[il] = 0.;
		y_soid.lwc[il] = 0.;
		y_soid.iwc[il] = 0.;
		y_soid.sws[il] = 0.;
		y_soid.aws[il] = 0.;

		y_soid.fbtran[il] = 0.;
	}

	y_soid.permafrost  = 1;
	y_soid.unfrzcolumn = 0;
	y_soid.alc = 0.;
	y_soid.ald = MISSING_D;

   	y_soid.frasat = 0.;

	y_soid.rtdpthawpct  = 0.;
	y_soid.rtdpts   = 0.;
 	y_soid.rtdpgdd  = 0.;
 	d_soid.rtdpgrowstart  =MISSING_I;
 	m_soid.rtdpgrowstart  =MISSING_I;
 	y_soid.rtdpgrowstart  =MISSING_I;
 	d_soid.rtdpgrowend    =MISSING_I;
 	m_soid.rtdpgrowend    =MISSING_I;
 	y_soid.rtdpgrowend    =MISSING_I;

	y_soid.tbotrock = 0.;

	//
 	y_soi2a.swrefl   = 0.;
	y_soi2a.evap     = 0.;
	y_soi2a.evap_pet = 0.;

   	y_soi2l.qover =0.;
   	y_soi2l.qinfl =0.;
   	y_soi2l.qdrain=0.;

}

// initialize monthly accumulators before daily-processes start
void EnvData::atm_beginOfMonth(){

   	m_atms.ta   = 0.;
   	m_atms.co2  = 0.;

   	m_atmd.vp   = 0.;
   	m_atmd.svp  = 0.;
   	m_atmd.vpd  = 0.;

   	//atm to land (including both veg/ground)
   	m_a2l.nirr = 0;
	m_a2l.par  = 0;
	m_a2l.prec = 0;
	m_a2l.rnfl = 0;
	m_a2l.snfl = 0;

	// atm to veg only
	m_a2v.pardown  = 0.; // for photosynthesis
	m_a2v.parabsorb= 0.;
	m_a2v.swdown  = 0.;  // for energy balance
	m_a2v.swinter = 0.;
	m_a2v.rnfl    = 0.;  // for water balance
	m_a2v.rinter  = 0.;
	m_a2v.snfl    = 0.;
	m_a2v.sinter  = 0.;

	//
	m_l2a.eet = 0.;
  	m_l2a.pet = 0.;

};

void EnvData::veg_beginOfMonth(){

	m_vegs.rwater  = 0.;
	m_vegs.snow    = 0.;

	m_vegd.rc      = 0.;
	m_vegd.cc      = 0.;
	m_vegd.btran   = 0.;
	m_vegd.m_ppfd  = 0.;
	m_vegd.m_vpd   = 0.;

	m_v2a.swrefl   = 0.;
	m_v2a.evap     = 0.;
	m_v2a.tran     = 0.;
	m_v2a.evap_pet = 0.;
	m_v2a.tran_pet = 0.;
	m_v2a.sublim   = 0.;

	m_v2g.swthfl   = 0.;
	m_v2g.rdrip    = 0.;
	m_v2g.rthfl    = 0.;
	m_v2g.sdrip    = 0.;
	m_v2g.sthfl    = 0.;

};

void EnvData::grnd_beginOfMonth(){

	//snow
	for (int i=0; i<MAX_SNW_LAY; i++){
		m_snws.swe[i]   = 0.;
		m_snws.snwice[i]= 0.;
		m_snws.snwliq[i]= 0.;
		m_snws.tsnw[i]  = 0.;
	}
	m_snws.swesum  = 0.;
	m_snws.tsnwave = 0.;

	m_snw2a.swrefl = 0.;
	m_snw2a.sublim = 0.;

	m_snw2soi.melt = 0.;

 	//soil
   	m_soid.icesum = 0.;
   	m_soid.liqsum = 0.;
   	m_soid.vwcshlw = 0.;
   	m_soid.vwcdeep = 0.;
   	m_soid.vwcminea= 0.;
   	m_soid.vwcmineb= 0.;
   	m_soid.vwcminec= 0.;

   	m_soid.tsave = 0.;
   	m_soid.tshlw = 0.;
   	m_soid.tdeep = 0.;
   	m_soid.tminea= 0.;
   	m_soid.tmineb= 0.;
   	m_soid.tminec= 0.;

   	m_soid.tcshlw = 0.;
   	m_soid.tcdeep = 0.;
   	m_soid.tcminea= 0.;
   	m_soid.tcmineb= 0.;
   	m_soid.tcminec= 0.;

   	m_soid.hkshlw = 0.;
   	m_soid.hkdeep = 0.;
   	m_soid.hkminea= 0.;
   	m_soid.hkmineb= 0.;
   	m_soid.hkminec= 0.;

   	for (int il=0; il<MAX_SOI_LAY; il++){
		m_sois.frozenfrac[il]  = 0.;

   		m_sois.ts[il]      = 0.;
   		m_sois.liq[il]     = 0.;
   		m_sois.ice[il]     = 0.;
   	}
   	m_sois.watertab   = 0.;
   	m_sois.draindepth = 0.;

   	for (int il=0; il<MAX_SOI_LAY; il++){
		m_soid.vwc[il] = 0.;
		m_soid.lwc[il] = 0.;
		m_soid.iwc[il] = 0.;
		m_soid.sws[il] = 0.;
		m_soid.aws[il] = 0.;

		m_soid.fbtran[il] = 0.;
	}
   	m_soid.frasat = 0.;

	m_soid.permafrost  = MISSING_I;
	m_soid.unfrzcolumn = 0.;
	m_soid.alc = 0.;
	m_soid.ald = MISSING_D;

	m_soid.rtdpthawpct= 0.;
	m_soid.rtdpts     = 0.;

	//
 	m_soi2a.swrefl   = 0.;
	m_soi2a.evap     = 0.;
	m_soi2a.evap_pet = 0.;

   	m_soi2l.qover  = 0.;
   	m_soi2l.qinfl  = 0.;
   	m_soi2l.qdrain = 0.;

};

void EnvData::grnd_beginOfDay(){

	// need to set some diagnostic variables to zero
    d_snw2soi.melt =0.;
};

/////////////////////////////////////////////////////////////////////////
// at end of day, accumulate/average daily to monthly
// accumulate fluxes, average state and diagnostics
void EnvData::atm_endOfDay(const int & dinm){
	//states/dignostics

   	m_atms.ta   += d_atms.ta/dinm;
   	m_atms.co2  += d_atms.co2/dinm;

   	m_atmd.vp   += d_atmd.vp/dinm;
   	m_atmd.svp  += d_atmd.svp/dinm;
   	m_atmd.vpd  += d_atmd.vpd/dinm;

   	//atm to land (including both veg/ground)
   	m_a2l.nirr += d_a2l.nirr/dinm;    //radiation unit is fluxes
	m_a2l.par  += d_a2l.par/dinm;
	m_a2l.prec += d_a2l.prec;          // precipation unit is amount
	m_a2l.rnfl += d_a2l.rnfl;
	m_a2l.snfl += d_a2l.snfl;

	// atm to veg only
	m_a2v.pardown  += d_a2v.pardown/dinm; // for photosynthesis
	m_a2v.parabsorb+= d_a2v.parabsorb/dinm;
	m_a2v.swdown   += d_a2v.swdown/dinm;  // for energy balance
	m_a2v.swinter  += d_a2v.swinter/dinm;
	m_a2v.rnfl     += d_a2v.rnfl;  // for water balance
	m_a2v.rinter   += d_a2v.rinter;
	m_a2v.snfl     += d_a2v.snfl;
	m_a2v.sinter   += d_a2v.sinter;

	// total land to atm
	m_l2a.eet += d_l2a.eet;
	m_l2a.pet += d_l2a.pet;
};

void EnvData::veg_endOfDay(const int & dinm){

	m_vegs.rwater  += d_vegs.rwater/dinm;     // canopy-contained rainfall water
	m_vegs.snow    += d_vegs.snow/dinm;

	m_vegd.rc      += d_vegd.rc/dinm;
	m_vegd.cc      += d_vegd.cc/dinm;
	m_vegd.btran   += d_vegd.btran/dinm;
	m_vegd.m_ppfd  += d_vegd.m_ppfd/dinm;
	m_vegd.m_vpd   += d_vegd.m_vpd/dinm;

	m_v2a.swrefl   += d_v2a.swrefl/dinm;
	m_v2a.evap     += d_v2a.evap;
	m_v2a.tran     += d_v2a.tran;
	m_v2a.evap_pet += d_v2a.evap_pet;
	m_v2a.tran_pet += d_v2a.tran_pet;
	m_v2a.sublim   += d_v2a.sublim;

	m_v2g.swthfl+= d_v2g.swthfl/dinm;
	m_v2g.rdrip += d_v2g.rdrip;
	m_v2g.sdrip += d_v2g.sdrip;
	m_v2g.rthfl += d_v2g.rthfl;
	m_v2g.sthfl += d_v2g.sthfl;

};

void EnvData::grnd_endOfDay(const int & dinm, const int & doy){

	// snow
	int numsnw = cd->d_snow.numsnwl;
	if (numsnw>0){
		for (int i=0; i<numsnw; i++){
			m_snws.swe[i]   += d_snws.swe[i]/dinm;
			m_snws.snwliq[i]+= d_snws.snwliq[i]/dinm;
			m_snws.snwice[i]+= d_snws.snwice[i]/dinm;
			m_snws.tsnw[i]  += d_snws.tsnw[i]/dinm;

			m_snws.swesum  += d_snws.swe[i]/dinm;
			m_snws.tsnwave += d_snws.tsnw[i]/numsnw/dinm;

		}
	}

	m_snw2a.swrefl += d_snw2a.swrefl/dinm;   // short-wave radiation reflection

	m_snw2a.sublim += d_snw2a.sublim;
	m_snw2soi.melt += d_snw2soi.melt;

	// soils
	int numsoi = cd->m_soil.numsl;
	for(int il =0; il<numsoi; il++){
		m_sois.frozenfrac[il] += d_sois.frozenfrac[il]/dinm;   //so, if some days frozen, some day not, its value shall be between -1 and 1.

		m_sois.ts[il]  += d_sois.ts[il]/dinm;
		m_sois.liq[il] += d_sois.liq[il]/dinm;
		m_sois.ice[il] += d_sois.ice[il]/dinm;

	}
	m_sois.watertab += d_sois.watertab/dinm;
	m_sois.draindepth += d_sois.draindepth/dinm;

	d_soid.vwcshlw = 0.;  d_soid.vwcdeep = 0.;
	d_soid.vwcminea = 0.; d_soid.vwcmineb = 0.; d_soid.vwcminec = 0.;
	d_soid.tshlw = 0.;    d_soid.tdeep = 0.;
	d_soid.tminea = 0.;   d_soid.tmineb = 0.;   d_soid.tminec = 0.;
	d_soid.tcshlw = 0.;   d_soid.tcdeep = 0.;
	d_soid.tcminea = 0.;  d_soid.tcmineb = 0.;  d_soid.tcminec = 0.;
	d_soid.hkshlw = 0.;   d_soid.hkdeep = 0.;
	d_soid.hkminea = 0.;  d_soid.hkmineb = 0.;  d_soid.hkminec = 0.;
	int mlind = 0;
	for(int il=0; il<numsoi; il++){
		if (cd->d_soil.type[il]==1) {
			d_soid.vwcshlw += d_soid.vwc[il]*cd->d_soil.dz[il]/cd->d_soil.shlwthick;
			d_soid.tshlw   += d_sois.ts[il]*cd->d_soil.dz[il]/cd->d_soil.shlwthick;
			d_soid.tcshlw  += d_soid.tcond[il]*cd->d_soil.dz[il]/cd->d_soil.shlwthick;
			d_soid.hkshlw  += d_soid.hcond[il]*cd->d_soil.dz[il]/cd->d_soil.shlwthick;
		} else if (cd->d_soil.type[il]==2) {
			d_soid.vwcdeep += d_soid.vwc[il]*cd->d_soil.dz[il]/cd->d_soil.deepthick;
			d_soid.tdeep   += d_sois.ts[il]*cd->d_soil.dz[il]/cd->d_soil.deepthick;
			d_soid.tcdeep  += d_soid.tcond[il]*cd->d_soil.dz[il]/cd->d_soil.deepthick;
			d_soid.hkdeep  += d_soid.hcond[il]*cd->d_soil.dz[il]/cd->d_soil.deepthick;
		} else if (cd->d_soil.type[il]==3) {
			if (mlind>=0 && mlind<=MINEZONE[0]) {
				d_soid.vwcminea += d_soid.vwc[il]*cd->d_soil.dz[il]/cd->d_soil.mineathick;
				d_soid.tminea   += d_sois.ts[il]*cd->d_soil.dz[il]/cd->d_soil.mineathick;
				d_soid.tcminea  += d_soid.tcond[il]*cd->d_soil.dz[il]/cd->d_soil.mineathick;
				d_soid.hkminea  += d_soid.hcond[il]*cd->d_soil.dz[il]/cd->d_soil.mineathick;
			} else if (mlind>MINEZONE[0] && mlind<=MINEZONE[1]) {
				d_soid.vwcmineb += d_soid.vwc[il]*cd->d_soil.dz[il]/cd->d_soil.minebthick;
				d_soid.tmineb   += d_sois.ts[il]*cd->d_soil.dz[il]/cd->d_soil.minebthick;
				d_soid.tcmineb  += d_soid.tcond[il]*cd->d_soil.dz[il]/cd->d_soil.minebthick;
				d_soid.hkmineb  += d_soid.hcond[il]*cd->d_soil.dz[il]/cd->d_soil.minebthick;
			} else if (mlind>MINEZONE[1] && mlind<=MINEZONE[2]) {
				d_soid.vwcminec += d_soid.vwc[il]*cd->d_soil.dz[il]/cd->d_soil.minecthick;
				d_soid.tminec   += d_sois.ts[il]*cd->d_soil.dz[il]/cd->d_soil.minecthick;
				d_soid.tcminec  += d_soid.tcond[il]*cd->d_soil.dz[il]/cd->d_soil.minecthick;
				d_soid.hkminec  += d_soid.hcond[il]*cd->d_soil.dz[il]/cd->d_soil.minecthick;
			}

			mlind++;

		}

	}

	for(int il=0; il<numsoi; il++){
	   	m_soid.vwc[il] += d_soid.vwc[il]/dinm;
	   	m_soid.lwc[il] += d_soid.lwc[il]/dinm;
	   	m_soid.iwc[il] += d_soid.iwc[il]/dinm;
	   	m_soid.sws[il] += d_soid.sws[il]/dinm;
	   	m_soid.aws[il] += d_soid.aws[il]/dinm;

	   	m_soid.fbtran[il] += d_soid.fbtran[il]/dinm;

		m_soid.liqsum += d_sois.liq[il]/dinm;
		m_soid.icesum += d_sois.ice[il]/dinm;
		m_soid.tsave  += d_sois.ts[il]/numsoi/dinm;

	}
   	m_soid.frasat += d_soid.frasat/dinm;

    m_soid.tbotrock    += d_soid.tbotrock/dinm;
    m_soid.unfrzcolumn += d_soid.unfrzcolumn/dinm;

	m_soid.vwcshlw += d_soid.vwcshlw/dinm;
   	m_soid.vwcdeep += d_soid.vwcdeep/dinm;
   	m_soid.vwcminea+= d_soid.vwcminea/dinm;
   	m_soid.vwcmineb+= d_soid.vwcmineb/dinm;
   	m_soid.vwcminec+= d_soid.vwcminec/dinm;

	m_soid.tshlw += d_soid.tshlw/dinm;
   	m_soid.tdeep += d_soid.tdeep/dinm;
   	m_soid.tminea+= d_soid.tminea/dinm;
   	m_soid.tmineb+= d_soid.tmineb/dinm;
   	m_soid.tminec+= d_soid.tminec/dinm;

	m_soid.tcshlw += d_soid.tcshlw/dinm;
   	m_soid.tcdeep += d_soid.tcdeep/dinm;
   	m_soid.tcminea+= d_soid.tcminea/dinm;
   	m_soid.tcmineb+= d_soid.tcmineb/dinm;
   	m_soid.tcminec+= d_soid.tcminec/dinm;

	m_soid.hkshlw += d_soid.hkshlw/dinm;
   	m_soid.hkdeep += d_soid.hkdeep/dinm;
   	m_soid.hkminea+= d_soid.hkminea/dinm;
   	m_soid.hkmineb+= d_soid.hkmineb/dinm;
   	m_soid.hkminec+= d_soid.hkminec/dinm;

    // determine if a permafrost or not
    if (d_soid.permafrost==0){    // d_soid.permafrost is ONLY for indicating if the soil frozen, not really a permafrost
    	m_soid.permafrost = 0;    // if no frozen soil, set both monthly permafrost to NO
    	monthsfrozen = 0;         // and, reset the frozen-soil-month counts to zero
    } else {
    	monthsfrozen +=1./dinm;

    	if (monthsfrozen>=24.) {  // permafrost is frozen soil for at least 24 months
    		m_soid.permafrost = 1;
    	} else {
    		m_soid.permafrost = 0;
    	}

    }

    // determine the active layer depth for monthly (daily value is in 'Soil_Env.cpp')
	if (m_soid.permafrost ==1){
		if (m_soid.ald < d_soid.ald){          // assuming the max. daily value
			m_soid.ald = d_soid.ald;
		}
		if (m_soid.alc < d_soid.alc){          // assuming the max. daily value
			m_soid.alc = d_soid.alc;
		}
	} else {
		m_soid.ald = cd->m_soil.totthick;     // NOTE: monthly 'ald' is for permafrost ONLY, but daily 'ald' for both seasonal and permafrost
		m_soid.alc = 0.;                      // NOTE: monthly 'alc' is for permafrost ONLY, but daily 'alc' for both seasonal and permafrost
	}

    // determine the growing season based on top rootzone unfrozen time
    m_soid.rtdpts   += d_soid.rtdpts/dinm;

	if(d_soid.rtdpthawpct<=0){
		rtunfrozendays = 0;
		rtfrozendays += 1;
	} else {
		rtfrozendays = 0;
		rtunfrozendays += 1;
	}

	if (d_soid.rtdpgrowstart <= 0){
	    if(rtunfrozendays >= 5){    //top soil root zone is unfrozen for continuous 5 days, marking the begining of growing
	      d_soid.rtdpgrowstart = doy;
	      m_soid.rtdpgrowstart = doy;
	      y_soid.rtdpgrowstart = doy;

	      d_soid.rtdpgdd = 0.;
	      m_soid.rtdpgdd = 0.;

	      d_soid.rtdpgrowend = MISSING_I;
	      m_soid.rtdpgrowend = MISSING_I;
	      y_soid.rtdpgrowend = MISSING_I;
	    }

	} else if (d_soid.rtdpgrowend <= 0){

		if (rtfrozendays>=5) {    //top soil root zone is frozen for continuous 5 days, marking the end of growing
			d_soid.rtdpgrowend = doy;
			m_soid.rtdpgrowend = doy;
			y_soid.rtdpgrowend = doy;

			d_soid.rtdpgdd = 0.;
			m_soid.rtdpgdd = 0.;

			d_soid.rtdpgrowstart= MISSING_I;
			m_soid.rtdpgrowstart= MISSING_I;
			y_soid.rtdpgrowstart= MISSING_I;
		}

	}

	// growing season soil root zone degree day: used in TEM phenology for seasonal litter-falling variation
	if (d_soid.rtdpgrowstart>=0 && d_soid.rtdpgrowend <=0) {
		d_soid.rtdpgdd += d_soid.rtdpts*1.0;
	}
	m_soid.rtdpgdd = d_soid.rtdpgdd;
	y_soid.rtdpgdd = d_soid.rtdpgdd;

	// growing season adjusting factor for monthly GPP
    m_soid.rtdpthawpct  += d_soid.rtdpthawpct/dinm;     // m_soid.growpct: growing days percentage of a month, used in monthly GPP function
    										    // d_soid.growpct: 1 or 0
	//
 	m_soi2a.swrefl  += d_soi2a.swrefl/dinm;
	m_soi2a.evap    += d_soi2a.evap;
	m_soi2a.evap_pet+= d_soi2a.evap_pet;

    m_soi2l.qover  += d_soi2l.qover;
	m_soi2l.qdrain += d_soi2l.qdrain;

};

void EnvData::atm_endOfMonth(){

	y_atms.ta  += m_atms.ta/12.;
    y_atms.co2 += m_atms.co2/12.;

    y_atmd.vp  += m_atmd.vp/12.;
   	y_atmd.svp += m_atmd.svp/12.;
   	y_atmd.vpd += m_atmd.vpd/12.;

   	//atm to land (including both veg/ground)
   	y_a2l.nirr += m_a2l.nirr/12.;
	y_a2l.par  += m_a2l.par/12.;
	y_a2l.prec += m_a2l.prec;
	y_a2l.rnfl += m_a2l.rnfl;
	y_a2l.snfl += m_a2l.snfl;

	// atm to veg only
	y_a2v.pardown  += m_a2v.pardown/12.; // for photosynthesis
	y_a2v.parabsorb+= m_a2v.parabsorb/12.;
	y_a2v.swdown   += m_a2v.swdown/12.;  // for energy balance
	y_a2v.swinter  += m_a2v.swinter/12.;
	y_a2v.rnfl     += m_a2v.rnfl;  // for water balance
	y_a2v.rinter   += m_a2v.rinter;
	y_a2v.snfl     += m_a2v.snfl;
	y_a2v.sinter   += m_a2v.sinter;

	//
    y_l2a.eet += m_l2a.eet;
    y_l2a.pet += m_l2a.pet;

};

void EnvData::veg_endOfMonth(const int & currmind){

	y_vegs.rwater  += m_vegs.rwater/12.;     // canopy-contained rainfall water
	y_vegs.snow    += m_vegs.snow/12.;

	y_vegd.rc      += m_vegd.rc/12.;
	y_vegd.cc      += m_vegd.cc/12.;
	y_vegd.btran   += m_vegd.btran/12.;
	y_vegd.m_ppfd  += m_vegd.m_ppfd/12.;
	y_vegd.m_vpd   += m_vegd.m_vpd/12.;

	y_v2a.swrefl   += m_v2a.swrefl/12;
	y_v2a.evap     += m_v2a.evap;
	y_v2a.tran     += m_v2a.tran;
	y_v2a.evap_pet += m_v2a.evap_pet;
	y_v2a.tran_pet += m_v2a.tran_pet;
	y_v2a.sublim   += m_v2a.sublim;

	y_v2g.swthfl+= m_v2g.swthfl/12.;
	y_v2g.rdrip += m_v2g.rdrip;
	y_v2g.sdrip += m_v2g.sdrip;
	y_v2g.rthfl += m_v2g.rthfl;
	y_v2g.sthfl += m_v2g.sthfl;

};

void EnvData::grnd_endOfMonth(){
    
	// snow
	y_snws.swesum  += m_snws.swesum/12.;    // it's not practical to calculate the yearly-averaged layered snow variables
	y_snws.tsnwave += m_snws.tsnwave/12.;

	y_snw2a.swrefl += m_snw2a.swrefl/12;   // short-wave radiation reflection

	y_snw2a.sublim += m_snw2a.sublim;
	y_snw2soi.melt += m_snw2soi.melt;

	// soils
	int numsoi = cd->m_soil.numsl;
	for(int il =0; il<numsoi; il++){
		y_sois.frozenfrac[il] += m_sois.frozenfrac[il]/12;   //so, if some months frozen, some months not, its value shall be between -1 and 1.

		y_sois.ts[il]  += m_sois.ts[il]/12.;
		y_sois.liq[il] += m_sois.liq[il]/12.;
		y_sois.ice[il] += m_sois.ice[il]/12.;

	}
	y_sois.watertab  += m_sois.watertab/12.;
	y_sois.draindepth+= m_sois.draindepth/12.;

	for(int il=0; il<numsoi; il++){
		y_soid.liqsum += m_sois.liq[il]/12.;
		y_soid.icesum += m_sois.ice[il]/12.;
		y_soid.tsave  += m_sois.ts[il]/numsoi/12.;

		y_soid.vwc[il] += m_soid.vwc[il]/12.;
	   	y_soid.lwc[il] += m_soid.lwc[il]/12.;
	   	y_soid.iwc[il] += m_soid.iwc[il]/12.;
	   	y_soid.sws[il] += m_soid.sws[il]/12.;
	   	y_soid.aws[il] += m_soid.aws[il]/12.;

	   	y_soid.fbtran[il] += m_soid.fbtran[il]/12.;

	}
   	y_soid.frasat    += m_soid.frasat/12.;

    y_soid.tbotrock    += m_soid.tbotrock/12.;
    y_soid.unfrzcolumn += m_soid.unfrzcolumn/12.;

	y_soid.vwcshlw += m_soid.vwcshlw/12.;
   	y_soid.vwcdeep += m_soid.vwcdeep/12.;
   	y_soid.vwcminea+= m_soid.vwcminea/12;
   	y_soid.vwcmineb+= m_soid.vwcmineb/12.;
   	y_soid.vwcminec+= m_soid.vwcminec/12.;

	y_soid.tshlw += m_soid.tshlw/12.;
   	y_soid.tdeep += m_soid.tdeep/12.;
   	y_soid.tminea+= m_soid.tminea/12.;
   	y_soid.tmineb+= m_soid.tmineb/12.;
   	y_soid.tminec+= m_soid.tminec/12.;

	y_soid.tcshlw += m_soid.tcshlw/12.;
   	y_soid.tcdeep += m_soid.tcdeep/12.;
   	y_soid.tcminea+= m_soid.tcminea/12.;
   	y_soid.tcmineb+= m_soid.tcmineb/12.;
   	y_soid.tcminec+= m_soid.tcminec/12.;

	y_soid.hkshlw += m_soid.hkshlw/12.;
   	y_soid.hkdeep += m_soid.hkdeep/12.;
   	y_soid.hkminea+= m_soid.hkminea/12.;
   	y_soid.hkmineb+= m_soid.hkmineb/12.;
   	y_soid.hkminec+= m_soid.hkminec/12.;

    // determine if a permafrost or not
    y_soid.permafrost = m_soid.permafrost;

    // determine the active layer depth for daily/monthly
	if (y_soid.permafrost ==1){
		if (y_soid.ald < m_soid.ald){          // assuming the max. daily value
			y_soid.ald = m_soid.ald;
		}

		if (y_soid.alc < m_soid.alc){          // assuming the max. daily value
			y_soid.alc = m_soid.alc;
		}
	} else {
		y_soid.ald = cd->m_soil.totthick;
		y_soid.alc = 0.;
	}

	//
    y_soid.rtdpts     += m_soid.rtdpts/12.;
    y_soid.rtdpthawpct+= m_soid.rtdpthawpct/12.;

	//
 	y_soi2a.swrefl  += m_soi2a.swrefl/12.;
	y_soi2a.evap    += m_soi2a.evap;
	y_soi2a.evap_pet+= m_soi2a.evap_pet;

    y_soi2l.qover  += m_soi2l.qover;
    y_soi2l.qinfl  += m_soi2l.qinfl;
	y_soi2l.qdrain += m_soi2l.qdrain;

};





