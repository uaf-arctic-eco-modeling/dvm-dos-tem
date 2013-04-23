#include "BgcData.h"

BgcData::BgcData(){

};

BgcData::~BgcData(){
	
};

// re-initialize BgcData class explicitly
void BgcData::clear(){
	cd->clear();

	//monthly
	m_vegs = vegstate_bgc();
	m_sois = soistate_bgc();
	m_vegd = vegdiag_bgc();
	m_soid = soidiag_bgc();
	m_l2a  = lnd2atm_bgc();
	m_a2v  = atm2veg_bgc();
	m_v2a  = veg2atm_bgc();
	m_v2soi = veg2soi_bgc();
	m_soi2v = soi2veg_bgc();
	m_v2v   = veg2veg_bgc();
	m_soi2l = soi2lnd_bgc();
	m_soi2a = soi2atm_bgc();
	m_a2soi = atm2soi_bgc();
	m_soi2soi = soi2soi_bgc();

	//yearly
	y_vegs = vegstate_bgc();
	y_sois = soistate_bgc();
	y_vegd = vegdiag_bgc();
	y_soid = soidiag_bgc();
	y_l2a  = lnd2atm_bgc();
	y_a2v  = atm2veg_bgc();
	y_v2a  = veg2atm_bgc();
	y_v2soi = veg2soi_bgc();
	y_soi2v = soi2veg_bgc();
	y_v2v   = veg2veg_bgc();
	y_soi2l = soi2lnd_bgc();
	y_soi2a = soi2atm_bgc();
	y_a2soi = atm2soi_bgc();
	y_soi2soi = soi2soi_bgc();

	for (int il=0; il<MAX_SOI_LAY; il++){
		if (!prvltrfcnque[il].empty()) {
			prvltrfcnque[il].clear();
		};
	}

};

void BgcData::land_endOfMonth(){
	m_l2a.nep = m_a2v.nppall-m_soi2a.rhtot;

	y_l2a.nep +=m_l2a.nep;
};

void BgcData::land_beginOfYear(){
	y_l2a.nep =0.;
};

void BgcData::veg_beginOfMonth(){
//
};

void BgcData::veg_endOfMonth(){

	// average yearly status variables
 	for (int i=0; i<NUM_PFT_PART; i++){
 		y_vegs.c[i] += m_vegs.c[i]/12.;
 		y_vegs.strn[i] += m_vegs.strn[i]/12.;
 	}
 	y_vegs.labn   += m_vegs.labn/12.;
 	y_vegs.strnall+= m_vegs.strnall/12.;
 	y_vegs.call   += m_vegs.call/12.;
 	y_vegs.nall   += m_vegs.nall/12.;
 	y_vegs.deadc  += m_vegs.deadc/12.;
 	y_vegs.deadn  += m_vegs.deadn/12.;

	// average yearly diagnostic variables
 	y_vegd.fca     += m_vegd.fca/12;
 	y_vegd.fna     += m_vegd.fna/12;
 	y_vegd.ftemp   += m_vegd.ftemp/12;
 	for (int i=0; i<NUM_PFT_PART; i++){
 		y_vegd.kr[i] += m_vegd.kr[i]/12;
 	}
 	y_vegd.gv      += m_vegd.gv/12;
 	y_vegd.raq10   += m_vegd.raq10/12;

	// accumulate yearly flux variables
 	for (int i=0; i<NUM_PFT_PART; i++){
 		y_a2v.ingpp[i] += m_a2v.ingpp[i];
 		y_a2v.innpp[i] += m_a2v.innpp[i];
 		y_a2v.gpp[i]   += m_a2v.gpp[i];
 		y_a2v.npp[i]   += m_a2v.npp[i];

 		y_v2a.rg[i] += m_v2a.rg[i];
 		y_v2a.rm[i] += m_v2a.rm[i];

 		y_v2v.nmobil[i] += m_v2v.nmobil[i];
 		y_v2v.nresorb[i]+= m_v2v.nresorb[i];

 		y_v2soi.ltrfalc[i] += m_v2soi.ltrfalc[i];
 		y_v2soi.ltrfaln[i] += m_v2soi.ltrfaln[i];

 		y_soi2v.snuptake[i] += m_soi2v.snuptake[i];
 	}

 	y_a2v.ingppall += m_a2v.ingppall;
	y_a2v.innppall += m_a2v.innppall;
	y_a2v.gppall   += m_a2v.gppall;
	y_a2v.nppall   += m_a2v.nppall;

	y_v2a.rgall += m_v2a.rgall;
	y_v2a.rmall += m_v2a.rmall;

	y_v2soi.ltrfalcall += m_v2soi.ltrfalcall;
	y_v2soi.ltrfalnall += m_v2soi.ltrfalnall;
	y_v2soi.mossdeathc += m_v2soi.mossdeathc;
	y_v2soi.mossdeathn += m_v2soi.mossdeathn;

	y_v2v.nmobilall  += m_v2v.nmobilall;
	y_v2v.nresorball += m_v2v.nresorball;

	for (int il=0; il<MAX_SOI_LAY; il++) {
		y_soi2v.nextract[il]  += m_soi2v.nextract[il];
	}
	y_soi2v.innuptake += m_soi2v.innuptake;
	y_soi2v.lnuptake  += m_soi2v.lnuptake;
	y_soi2v.snuptakeall+= m_soi2v.snuptakeall;

}

// initializing yearly accumulating variables
void BgcData::veg_beginOfYear(){
	for (int i=0; i<NUM_PFT_PART; i++){
		y_vegs.c[i]    = 0.;
		y_vegs.strn[i] = 0.;

		y_vegd.kr[i]   = 0.;

		y_a2v.ingpp[i] = 0.;
		y_a2v.innpp[i] = 0.;
		y_a2v.gpp[i]   = 0.;
		y_a2v.npp[i]   = 0.;
		y_v2a.rg[i]    = 0.;
 		y_v2a.rm[i]    = 0.;

 		y_v2v.nmobil[i]  = 0.;
 		y_v2v.nresorb[i] = 0.;

 		y_v2soi.ltrfalc[i] = 0.;
		y_v2soi.ltrfaln[i] = 0.;

		y_soi2v.snuptake[i] = 0.;
	}

	y_vegs.call    = 0.;
	y_vegs.nall    = 0.;
 	y_vegs.labn    = 0.;
	y_vegs.strnall = 0.;

 	y_vegd.fca     = 0.;
 	y_vegd.fna     = 0.;
 	y_vegd.ftemp   = 0.;
 	y_vegd.gv      = 0.;
 	y_vegd.raq10   = 0.;

	y_a2v.ingppall = 0.;
	y_a2v.innppall = 0.;
	y_a2v.gppall   = 0.;
	y_a2v.nppall   = 0.;
	y_v2a.rgall    = 0.;
	y_v2a.rmall    = 0.;

	y_v2soi.ltrfalcall = 0.;
	y_v2soi.ltrfalnall = 0.;
	y_v2soi.mossdeathc = 0.;
	y_v2soi.mossdeathn = 0.;

	y_v2v.nmobilall  = 0.;
	y_v2v.nresorball = 0.;

 	for (int il=0; il<MAX_SOI_LAY; il++){
 		y_soi2v.nextract[il]   = 0.;
 	}

 	y_soi2v.innuptake = 0.;
 	y_soi2v.lnuptake   = 0.;
 	y_soi2v.snuptakeall= 0.;
 
}

void BgcData::veg_endOfYear(){

}

void BgcData::soil_beginOfMonth(){
/*
	for(int il=0; il<MAX_SOI_LAY; il++){
		m_sois.rawc[il] = 0.;
		m_sois.soma[il] = 0.;
		m_sois.sompr[il]= 0.;
		m_sois.somcr[il]= 0.;

		m_sois.orgn[il] = 0.;
		m_sois.avln[il] = 0.;

		m_soi2a.rhrawc[il] = 0.;
	  	m_soi2a.rhsoma[il] = 0.;
	  	m_soi2a.rhsoma[il] = 0.;
	  	m_soi2a.rhsompr[il]= 0.;
	  	m_soi2a.rhsomcr[il]= 0.;

	}
*/
};

void BgcData::soil_beginOfYear(){

 	y_sois.wdebrisc= 0.;
 	y_sois.wdebrisn= 0.;
 	y_sois.dmossc  = 0.;
 	y_sois.dmossn  = 0.;

 	y_soid.shlwc   = 0.;
 	y_soid.deepc   = 0.;
 	y_soid.mineac  = 0.;  // top mineral SOMC
 	y_soid.minebc  = 0.;  // middle mineral SOMC
 	y_soid.minecc  = 0.;  // middle mineral SOMC
 	y_soid.rawcsum = 0.;
 	y_soid.somasum = 0.;
 	y_soid.somprsum= 0.;
 	y_soid.somcrsum= 0.;
 	y_soid.orgnsum = 0.;
 	y_soid.avlnsum = 0.;

 	y_soi2a.rhtot  =0.;
 	y_soi2a.rhwdeb    =0.;
	y_soi2a.rhrawcsum =0.;
	y_soi2a.rhsomasum =0.;
	y_soi2a.rhsomprsum=0.;
	y_soi2a.rhsomcrsum=0.;

	y_soi2soi.netnminsum = 0.;
	y_soi2soi.nimmobsum  = 0.;

	for (int il =0; il<MAX_SOI_LAY; il++){
 		//
 		y_sois.rawc[il]=0.;
 		y_sois.soma[il]=0.;
 		y_sois.sompr[il]=0.;
 		y_sois.somcr[il]=0.;

 		y_sois.orgn[il]=0.;
 		y_sois.avln[il]=0.;

 	 	y_soid.tsomc[il] =0.;

 		y_soid.ltrfcn[il] = 0.;
   		y_soid.knmoist[il]= 0.;
   		y_soid.rhmoist[il]= 0.;
   		y_soid.rhq10[il]  = 0.;

   		//
   		y_soi2a.rhrawc[il] = 0.;
   		y_soi2a.rhsoma[il] = 0.;
   		y_soi2a.rhsompr[il]= 0.;
   		y_soi2a.rhsomcr[il]= 0.;

   		//
   		y_soi2soi.netnmin[il] = 0.;
   		y_soi2soi.nimmob[il]  = 0.;

 	}
 
	//
	y_a2soi.orgninput = 0.0;
	y_a2soi.avlninput = 0.0;
    y_soi2l.orgnlost  = 0.0;
    y_soi2l.avlnlost = 0.0;

};

void BgcData::soil_endOfMonth(){
 
	// status variable (diagnostics)
 	m_soid.shlwc   = 0.;
 	m_soid.deepc   = 0.;
 	m_soid.mineac  = 0.;
 	m_soid.minebc  = 0.;
 	m_soid.minecc  = 0.;

 	m_soid.orgnsum = 0.;
 	m_soid.avlnsum = 0.;

 	m_soid.rawcsum = 0.;
 	m_soid.somasum = 0.;
 	m_soid.somprsum= 0.;
 	m_soid.somcrsum= 0.;

 	int mlind = 0;
 	for (int il =0; il<MAX_SOI_LAY; il++){
 		m_soid.tsomc[il]= m_sois.rawc[il]+m_sois.soma[il]+m_sois.sompr[il]+m_sois.somcr[il];
 		if(cd->m_soil.type[il]==1){
   	 		m_soid.shlwc += m_soid.tsomc[il];
   		} else if(cd->m_soil.type[il]==2){
   	 		m_soid.deepc += m_soid.tsomc[il];
   		} else if(cd->m_soil.type[il]==3){
   			if (mlind>=0 && mlind<=MINEZONE[0])
   				m_soid.mineac += m_soid.tsomc[il];

   			if (mlind>MINEZONE[0] && mlind<=MINEZONE[1])
   				m_soid.minebc += m_soid.tsomc[il];

   			if (mlind>MINEZONE[1] && mlind<=MINEZONE[2])
   				m_soid.minecc += m_soid.tsomc[il];

   			mlind ++;
   		}

   		m_soid.rawcsum += m_sois.rawc[il];
   		m_soid.somasum += m_sois.soma[il];
   		m_soid.somprsum+= m_sois.sompr[il];
   		m_soid.somcrsum+= m_sois.somcr[il];

   		m_soid.orgnsum += m_sois.orgn[il];
   		m_soid.avlnsum += m_sois.avln[il];
 	}

 	// previous monthly accumulating variables
 	for (int il =0; il<MAX_SOI_LAY; il++){
 		double mltrfcn = m_soid.ltrfcn[il];
 		prvltrfcnque[il].push_front(mltrfcn);
 		if (prvltrfcnque[il].size()>12) {
 			prvltrfcnque[il].pop_back();
 		}

 	}

 	//annually mean variables
 	for (int il =0; il<MAX_SOI_LAY; il++){
 	   	y_soid.tsomc[il]  += m_soid.tsomc[il]/12;

 	    y_soid.rhmoist[il]+= m_soid.rhmoist[il]/12;
 	   	y_soid.rhq10[il]  += m_soid.rhq10[il]/12;
 	   	y_soid.ltrfcn[il] += m_soid.ltrfcn[il]/12;

 	    y_soid.knmoist[il]+= m_soid.knmoist[il]/12;

 	   	y_sois.rawc[il] += m_sois.rawc[il]/12.;
   		y_sois.soma[il] += m_sois.soma[il]/12.;
   		y_sois.sompr[il]+= m_sois.sompr[il]/12.;
   		y_sois.somcr[il]+= m_sois.somcr[il]/12.;
   		y_sois.orgn[il] += m_sois.orgn[il]/12.;
   		y_sois.avln[il] += m_sois.avln[il]/12.;
 	}
   	y_sois.dmossc += m_sois.dmossc/12.;
   	y_sois.dmossn += m_sois.dmossn/12.;

   	y_sois.wdebrisc += m_sois.wdebrisc/12.;
   	y_sois.wdebrisn += m_sois.wdebrisn/12.;

   	y_soid.shlwc += m_soid.shlwc/12;
   	y_soid.deepc += m_soid.deepc/12;
   	y_soid.mineac += m_soid.mineac/12;
   	y_soid.minebc += m_soid.minebc/12;
   	y_soid.minecc += m_soid.minecc/12;
   
 	y_soid.rawcsum += m_soid.rawcsum/12.;
 	y_soid.somasum += m_soid.somasum/12.;
 	y_soid.somprsum+= m_soid.somprsum/12.;
 	y_soid.somcrsum+= m_soid.somcrsum/12.;

 	y_soid.avlnsum += m_soid.avlnsum/12.;
 	y_soid.orgnsum += m_soid.orgnsum/12.;

   	// fluxes
   	m_soi2a.rhrawcsum = 0.;
 	m_soi2a.rhsomasum = 0.;
 	m_soi2a.rhsomprsum= 0.;
 	m_soi2a.rhsomcrsum= 0.;
 	m_soi2soi.netnminsum= 0.;
 	m_soi2soi.nimmobsum = 0.;

 	for (int il =0; il<MAX_SOI_LAY; il++){

   		m_soi2a.rhrawcsum += m_soi2a.rhrawc[il];
   		m_soi2a.rhsomasum += m_soi2a.rhsoma[il];
   		m_soi2a.rhsomprsum+= m_soi2a.rhsompr[il];
   		m_soi2a.rhsomcrsum+= m_soi2a.rhsomcr[il];

   	 	m_soi2soi.netnminsum+= m_soi2soi.netnmin[il];
   	 	m_soi2soi.nimmobsum += m_soi2soi.nimmob[il];

 	}
 	m_soi2a.rhtot = m_soi2a.rhrawcsum + m_soi2a.rhsomasum
 			    +m_soi2a.rhsomprsum + m_soi2a.rhsomcrsum
 			    +m_soi2a.rhwdeb + m_soi2a.rhmossc;

 	//cumulative annually
 	y_soi2a.rhwdeb    += m_soi2a.rhwdeb;
 	y_soi2a.rhrawcsum += m_soi2a.rhrawcsum;
 	y_soi2a.rhsomasum += m_soi2a.rhsomasum;
 	y_soi2a.rhsomprsum+= m_soi2a.rhsomprsum;
 	y_soi2a.rhsomcrsum+= m_soi2a.rhsomcrsum;
 	y_soi2a.rhtot     += m_soi2a.rhtot;
 	for (int il =0; il<MAX_SOI_LAY; il++){
   		y_soi2a.rhrawc[il] += m_soi2a.rhrawc[il]/12.;
   		y_soi2a.rhsoma[il] += m_soi2a.rhsoma[il]/12.;
   		y_soi2a.rhsompr[il]+= m_soi2a.rhsompr[il]/12.;
   		y_soi2a.rhsomcr[il]+= m_soi2a.rhsomcr[il]/12.;

   	 	y_soi2soi.netnmin[il]+= m_soi2soi.netnmin[il]/12.;
   	 	y_soi2soi.nimmob[il] += m_soi2soi.nimmob[il]/12.;
 	}
	y_soi2soi.netnminsum+= m_soi2soi.netnminsum/12.;
	y_soi2soi.nimmobsum += m_soi2soi.nimmobsum/12.;

    // connection to open-N cycle
	y_a2soi.orgninput += m_a2soi.orgninput;
	y_soi2l.orgnlost += m_soi2l.orgnlost;
	y_a2soi.avlninput += m_a2soi.avlninput;
	y_soi2l.avlnlost += m_soi2l.avlnlost;

};





