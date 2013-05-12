/*! \file
*
*  Yuan: 1) modified for 3 plant C pools (leaf, wood, root), 1 non-living plant C
*                     4 plant N pools (labile, leaf, wood, root), 1 non-living plant N
*                and, 4 soil C pools (raw materials, active SOM, phyiscally-resistant SOM,
*                                     chemically-resistant SOM)
*                     1 woody debris C pools
*                     2 soil N pools (organic N, available N)
*
*        2) vegetation, soil are integrated separately, because vegetation may have multple PFTs,
*        but all of which share ONE soil. Here, the code only deals with ONE PFT and/or ONE SOIL, by setting
*        the following switches:
*            bool vbgc, bool sbgc
*
*            And, the 'bd' (BgcData) for veg and soil may not be same - be cautious here!
*
*/

#include "Integrator.h"

float Integrator::a1  =   0.115740741;
float Integrator::a3  =   0.548927875;
float Integrator::a31 =   0.09375;
float Integrator::a32 =   0.28125;

float Integrator::a4  =   0.535331384;
float Integrator::a41 =   0.879380974; 
float Integrator::a42 =  -3.277196177;
float Integrator::a43 =   3.320892126;

float Integrator::a5  =  -0.20;
float Integrator::a51 =   2.032407407;
float Integrator::a52 =  -8.0;
float Integrator::a53 =   7.173489279;
float Integrator::a54 =  -0.2058966866;

float Integrator::b1 =   0.118518519;
float Integrator::b3 =   0.518986355;
float Integrator::b4 =   0.50613149;
float Integrator::b5 =  -0.18;
float Integrator::b6 =   0.036363636;
float Integrator::b61 =  -0.296296296;
float Integrator::b62 =   2.0;
float Integrator::b63 =  -1.381676413;
float Integrator::b64 =   0.45297271;
float Integrator::b65 =  -0.275;

int REJECT =0;
int ACCEPT=1;

Integrator::Integrator(){
	inittol = 0.01;
   	maxit = 20;
    maxitmon = 100;
    syint = 1;

	//vegetation C & N state variables
  	for(int i =0; i<NUM_PFT_PART; i++){     //Yuan: here is the reason that the "temconst.h" is needed
		stringstream ipart;
		ipart <<" " <<i;
		string str1 = ipart.str();

		// C and N pools, except not in individual veg. parts
		strcpy(predstr_veg[I_VEGC+i],(string("VEGC") +str1).c_str());   //  vegetation carbon pools
		strcpy(predstr_veg[I_STRN+i],(string("STRN") +str1).c_str());   //  vegetation nitrogen pools

  	}
  	strcpy(predstr_veg[I_LABN],"LABN" );    // vegetation labile nitrogen
  	strcpy(predstr_veg[I_DEADC],"DEADC" );  // non-living veg C
  	strcpy(predstr_veg[I_DEADN],"DEADN" );  // non-living veg N

	// vegetation C&N flux variables
	for(int i =0; i<NUM_PFT_PART; i++){     //Yuan: here is the reason that the "temconst.h" is needed
			stringstream ipart;
			ipart <<" " <<i;
			string str2 = ipart.str();

			strcpy(predstr_veg[I_INGPP+i],(string("INGPP") +str2).c_str());  	// GPP not limited by nutrient availability
			strcpy(predstr_veg[I_INNPP+i],(string("INNPP") +str2).c_str());  	// NPP not limited by nutrient availability
			strcpy(predstr_veg[I_GPP+i],(string("GPP") +str2).c_str());       // actual GPP
			strcpy(predstr_veg[I_NPP+i],(string("NPP") +str2).c_str());      // actual NPP
			strcpy(predstr_veg[I_RM+i],(string("RM") +str2).c_str());      // plant maintainence respiration
			strcpy(predstr_veg[I_RG+i],(string("RG") +str2).c_str());      // plant growth respiration
			strcpy(predstr_veg[I_LTRC+i],(string("LTRC") +str2).c_str());    // litterfall carbon

			strcpy(predstr_veg[I_SNUP+i],(string("SNUP") +str2).c_str());   // vegetation nitrogen uptake for structural components
		  	strcpy(predstr_veg[I_NMBOL+i],(string("NMBOL") +str2).c_str());   // nitrogen mobilization by vegetation
		  	strcpy(predstr_veg[I_NRSRB+i],(string("NRSRB") +str2).c_str()); // nitrogen resorption by vegetation
		  	strcpy(predstr_veg[I_LTRN+i],(string("LTRN") +str2).c_str());       // litterfall nitrogen

	}
	strcpy(predstr_veg[I_INNUP],"INNUP");  // vegetation N uptake at full capacity without interaction from C
	strcpy(predstr_veg[I_LNUP],"LNUP" );     // vegetation nitrogen uptake for labile components

	//soil C&N state variables
	for(int il =0; il<MAX_SOI_LAY; il++){     //Yuan: here is the reason that the "temconst.h" is needed
		stringstream ilayer;
		ilayer <<" " <<il;
		string str2 = ilayer.str();
		strcpy(predstr_soi[I_L_RAWC+il],(string("RAWC") +str2).c_str() );   //  soil raw material carbon
		strcpy(predstr_soi[I_L_SOMA+il],(string("SOMA") +str2).c_str() );   // soil active som carbon
		strcpy(predstr_soi[I_L_SOMPR+il],(string("SOMPR") +str2).c_str() );   // soil physically-resistant som carbon
		strcpy(predstr_soi[I_L_SOMCR+il],(string("SOMCR") +str2).c_str() );   // soil chemically-resistant som carbon
	}
  	strcpy(predstr_soi[I_WDEBRISC],"WDEBRISC"); // wood debris C
  	strcpy(predstr_soi[I_WDEBRISN],"WDEBRISN"); // wood debris N
  	strcpy(predstr_soi[I_DMOSSC],"DMOSSC"); // dead moss C
  	strcpy(predstr_soi[I_DMOSSN],"DMOSSN"); // dead moss N

	// soil C&N flux variables
	for(int il =0; il<MAX_SOI_LAY; il++){     //Yuan: here is the reason that the "temconst.h" is needed
		stringstream ilayer;
		ilayer <<" " <<il;
		string str2 = ilayer.str();

		strcpy(predstr_soi[I_L_RH_RAW+il],(string("RHRAW") +str2).c_str() );     // soil rh
		strcpy(predstr_soi[I_L_RH_SOMA+il],(string("RHSOMA") +str2).c_str() );   // soil rh
		strcpy(predstr_soi[I_L_RH_SOMPR+il],(string("RHSOMPR") +str2).c_str() );   // soil rh
		strcpy(predstr_soi[I_L_RH_SOMCR+il],(string("RHSOMCR") +str2).c_str() );   // soil rh

		strcpy(predstr_soi[I_L_ORGN+il],(string("ORGN") +str2).c_str() );  // soil organic nitrogen
	    strcpy(predstr_soi[I_L_AVLN+il],(string("AVLN") +str2).c_str() );  // soil available nitrogen

	    strcpy(predstr_soi[I_L_NMIN+il],(string("NMIN") +str2).c_str() );   // soil net N minerization
	    strcpy(predstr_soi[I_L_NIMMOB+il],(string("NIMMOB") +str2).c_str() );   // soil net N minerization

	}
	strcpy(predstr_soi[I_RH_WD],"RHWD" );   // woody debris respiration
	strcpy(predstr_soi[I_RH_DMOSS],"RHDMOSS" );   // dead moss respiration

  	// Total Ecosystem N loss
	strcpy(predstr_soi[I_AVLNLOSS],"AVLNLOSS" );   // total inorganic nitrogen loss
	strcpy(predstr_soi[I_ORGNLOSS],"ORGNLOSS" );   // total organic nitrogen loss

};

Integrator::~Integrator(){

};

void Integrator::setBgcData(BgcData * bdp){
   	 bd = bdp;
};

void Integrator::setSoil_Bgc(Soil_Bgc * soip){
   	 ssl = soip;
};

void Integrator::setVegetation_Bgc(Vegetation_Bgc * vegp){
   	 veg = vegp;
};
 
void Integrator::updateMonthlyVbgc(){
	 vegbgc = true;      // these two switches will only allow vegetation_bgc call in 'delta'
	 soibgc = false;

	// first reset all the variables to zero
     for (int iv = 0; iv < NUMEQ; iv++){
     	y[iv] = 0.0;
     }

     // initialize the state from 'bd'
     c2ystate_veg(y);

     // integration
	 adapt(y, NUMEQ_VEG);

    // after integration , save results back to 'bd';
	 y2cstate_veg(y);
	 y2cflux_veg(y);

};

void Integrator::updateMonthlySbgc(const int & numsoillayer){
	 vegbgc = false;
	 soibgc = true;      // these two switches will only allow soil_bgc call in 'delta'

     numsl = numsoillayer;

	// first reset all the variables to zero
     for (int iv = 0; iv < NUMEQ; iv++ ){
     	y[iv] = 0.0; 
     }

     // initialize the state from 'bd';
     c2ystate_soi(y);
	
     // integration
	 adapt(y, NUMEQ_SOI);

    // after integration , save results back to 'bd';
	 y2cstate_soi(y);
	 y2cflux_soi(y);
     
};

void Integrator::c2ystate_veg(float y[]){

	for (int i=0; i<NUM_PFT_PART; i++) {
		y[I_VEGC+i] = bd->m_vegs.c[i];
		y[I_STRN+i] = bd->m_vegs.strn[i];
	}

    y[I_LABN]       = bd->m_vegs.labn;

    y[I_DEADC]      = bd->m_vegs.deadc;
    y[I_DEADN]      = bd->m_vegs.deadn;
};

void Integrator::c2ystate_soi(float y[]){
    for(int il =0; il<numsl; il++){
      	y[I_L_RAWC+il] = bd->m_sois.rawc[il];
      	y[I_L_SOMA+il] = bd->m_sois.soma[il];
      	y[I_L_SOMPR+il]= bd->m_sois.sompr[il];
      	y[I_L_SOMCR+il]= bd->m_sois.somcr[il];
        y[I_L_ORGN+il] = bd->m_sois.orgn[il];
        y[I_L_AVLN+il] = bd->m_sois.avln[il];
    }
    y[I_WDEBRISC] = bd->m_sois.wdebrisc;
    y[I_WDEBRISN] = bd->m_sois.wdebrisn;
    y[I_DMOSSC] = bd->m_sois.dmossc;
    y[I_DMOSSN] = bd->m_sois.dmossn;

};

int Integrator::adapt(float pstate[], const int & numeq){
  	int i;
  	float ipart;
  	float fpart;
  	float time = 0.0;
  	float dt = 1.0;
  	int mflag = 0;
  	int nintmon = 0;
  	float oldstate[numeq];
  	float  ptol =0.01;

   	blackhol = 0;
  	while ( time != 1.0 ){
    	test = REJECT;
    	if ( syint == 1 ){
      		while ( test != ACCEPT ){

      			bool testavln = rkf45(numeq,pstate,dt);

				if(testavln){
					test = boundcon( dum4,error,ptol );
				}else{
	 				test = testavln;
				}
				
				//if(test>1)cout <<predstr[test-1] << " error is " << error[test-1] <<"------Integrator-------\n";
				if ( dt <= pow(0.5,maxit) ){
	  				test = ACCEPT;
	  				mflag = 1;
          			if ( nintmon == 0 ){
            			for( i = 0; i < numeq;i++ ) { oldstate[i] = pstate[i]; }
          			}
	  				++nintmon;
				}

        		if ( test == ACCEPT ){
          			for( i = 0; i < numeq;i++ ) { pstate[i] = dum4[i]; }
          			time += dt;
          			fpart = modf( (0.01 + (time/(2.0*dt))),&ipart );
          			if ( fpart < 0.1 && dt < 1.0) { dt *= 2.0; }
        		}else {
        			dt *= 0.500; 
        		}

        		if ( nintmon == maxitmon ){
          			time = 1.0;
          			blackhol = 1;
          			for( i = 0; i < numeq;i++ ) { pstate[i] = oldstate[i]; }
        		}
      		}
    	}    /* end rkf integrator (if) */
  	}      /* end time while */

  	return mflag;

};

bool Integrator::rkf45( const int& numeq, float pstate[], float& pdt) {
  	int negativepool = -1;
  	int i;
  	float ptdt = 0;

  	for ( i = 0; i < numeq;i++ ) {
    	dum4[i] = dum5[i] = pstate[i];
    	yprime[i] = rk45[i] = error[i] = 0.0;
    	f11[i]=f3[i]=f4[i]=f5[i]=f6[i] = 0.0;
  	}

  	//
  	ptdt = pdt * 0.25;
  	delta(dum4,f11);
  	
  	step( numeq,yprime,f11,yprime,a1 );
  	step( numeq,rk45,f11,rk45,b1 );
  	step( numeq,dum4,f11,ydum,ptdt );
  	negativepool = checkPools();
  	if(negativepool>=0){
  	  	return false;	
  	}
  	
  	delta(ydum,f2);
  	for ( i = 0; i < numeq; i++ ) {
    	f13[i] = a31*f11[i] + a32*f2[i];
  	}
  
  	step( numeq,dum4,f13,ydum,pdt );
 	negativepool = checkPools();
  	if(negativepool>=0){
  	  return false;	
  	}
  	
  	delta(ydum,f3 );
  	step( numeq,yprime,f3,yprime,a3 );
  	step( numeq,rk45,f3,rk45,b3 );
  	for ( i = 0; i < numeq; i++ ){
    	f14[i] = a41*f11[i] + a42*f2[i] + a43*f3[i];
  	}
  	
  	step( numeq,dum4,f14,ydum,pdt );
  	negativepool = checkPools();
  	if(negativepool>=0){
  	  return false;	
  	}
  	
  	delta(ydum,f4 );
  	step( numeq,yprime,f4,yprime,a4 );
  	step( numeq,rk45,f4,rk45,b4 );
  	for ( i = 0; i < numeq; i++ ) {
    	f15[i] = a51*f11[i] + a52*f2[i] + a53*f3[i] + a54*f4[i];
  	}
  	
  	step( numeq,dum4,f15,ydum,pdt );
  	negativepool = checkPools();
  	if(negativepool>=0){
  	  return false;	
  	}
  	
  	delta(ydum,f5 );
  	step( numeq,yprime,f5,yprime,a5 );
  	step( numeq,rk45,f5,rk45,b5 );
  	for ( i = 0; i < numeq; i++ ){
    	f16[i] = b61*f11[i] + b62*f2[i] + b63*f3[i] + b64*f4[i] + b65*f5[i];
  	}
  	
  	step( numeq,dum4,f16,ydum,pdt );
  	negativepool = checkPools();
  	if(negativepool>=0){
  	  return false;	
  	}
  	
  	delta(ydum,f6 );
  	step( numeq,rk45,f6,rk45,b6 );
  	step( numeq,dum4,yprime,dum4,pdt );
  	step( numeq,dum5,rk45,dum5,pdt );
  	for ( i = 0; i < numeq; i++ ) {
    	error[i] = fabs( dum4[i] - dum5[i] );
  	}
  
    return true;
};

void Integrator::y2cstate_veg(float y[]){

	for (int i=0; i<NUM_PFT_PART; i++) {
		bd->m_vegs.c[i] = y[I_VEGC+i];
		bd->m_vegs.strn[i] = y[I_STRN+i] ;
	}

    if(y[I_LABN]<0){
    	 y[I_STRN] += y[I_LABN] -0.001;
    	 y[I_LABN]= 0.001;
	}
    bd->m_vegs.labn  = y[I_LABN] ;

	bd->m_vegs.deadc = y[I_DEADC];
    bd->m_vegs.deadn = y[I_DEADN];

};

void Integrator::y2cstate_soi(float y[]){

    for(int il=0; il<numsl; il++){
     	bd->m_sois.rawc[il] = y[I_L_RAWC +il];
        bd->m_sois.soma[il] = y[I_L_SOMA +il];
        bd->m_sois.sompr[il]= y[I_L_SOMPR +il];
        bd->m_sois.somcr[il]= y[I_L_SOMCR +il];

        if(y[I_L_AVLN+il]<0){//add by shuhua Dec 8 2007
        	y[I_L_ORGN+il]+=y[I_L_AVLN+il] -0.001;
        	y[I_L_AVLN+il]=0.001;
        }
        bd->m_sois.orgn[il] = y[I_L_ORGN+il];
        bd->m_sois.avln[il] = y[I_L_AVLN+il];
    }

	bd->m_sois.wdebrisc = y[I_WDEBRISC];
	bd->m_sois.wdebrisn = y[I_WDEBRISN];
	bd->m_sois.dmossc   = y[I_DMOSSC];
	bd->m_sois.dmossn   = y[I_DMOSSN];

};

void Integrator::y2cflux_veg(float y[]){

	for (int i=0; i<NUM_PFT_PART; i++) {
		bd->m_a2v.ingpp[i] = y[I_INGPP+i];
		bd->m_a2v.innpp[i] = y[I_INNPP+i];
		bd->m_a2v.gpp[i]   = y[I_GPP+i];
		bd->m_a2v.npp[i]   = y[I_NPP+i];

		bd->m_v2a.rm[i] = y[I_RM+i];
		bd->m_v2a.rg[i] = y[I_RG+i];

		bd->m_v2soi.ltrfalc[i] = y[I_LTRC+i];

		bd->m_soi2v.snuptake[i]  = y[I_SNUP+i];
		bd->m_v2v.nmobil[i]      = y[I_NMBOL+i];
		bd->m_v2v.nresorb[i]     = y[I_NRSRB+i];

		bd->m_v2soi.ltrfaln[i]   = y[I_LTRN+i];
	}

	bd->m_soi2v.innuptake = y[I_INNUP];
	bd->m_soi2v.lnuptake  = y[I_LNUP];

};

void Integrator::y2cflux_soi(float y[]){

  	for(int il =0; il<numsl; il++){
  		bd->m_soi2a.rhrawc[il]    = y[I_L_RH_RAW +il];
  		bd->m_soi2a.rhsoma[il]    = y[I_L_RH_SOMA +il];
  		bd->m_soi2a.rhsompr[il]   = y[I_L_RH_SOMPR +il];
  		bd->m_soi2a.rhsomcr[il]   = y[I_L_RH_SOMCR +il];
  	  	bd->m_soi2soi.nimmob[il]  = y[I_L_NIMMOB+il];
  	  	bd->m_soi2soi.netnmin[il] = y[I_L_NMIN+il];
  	}
  	bd->m_soi2a.rhwdeb   = y[I_RH_WD];
  	bd->m_soi2a.rhmossc  = y[I_RH_DMOSS];

  	//
    bd->m_soi2l.avlnlost = y[I_AVLNLOSS];
    bd->m_soi2l.orgnlost = y[I_ORGNLOSS];

};

/****************************************************************/
void Integrator::delta(float pstate[], float pdstate[]){

	if (vegbgc) {
		// assign value from pstate to temporate variables in veg
		// only state variabls are needed, since fluxes and diagnostic variables will
		// be recalculated again based on state variabels
		y2tcstate_veg(pstate);

		// calculate the fluxes
		veg->delta();
		veg->deltanfeed();

		// update the delta of state variables
		veg->deltastate();

		// assign fluxes and state back to pdstate
		dc2ystate_veg(pdstate);
		dc2yflux_veg(pdstate);
	}

//   ssl->del_soi2v = veg->del_soi2v;  // These two will be done out of this module, because veg-> has to integrate
//   ssl->del_v2soi = veg->del_v2soi;

	if (soibgc) {
		// assign value from pstate to temporate variables in ssl
		// only state variabls are needed, since fluxes and diagnostic variables will
		// be recalculated again based on state variabels
		y2tcstate_soi(pstate);

		// calculate the fluxes
		ssl->deltac();
		ssl->deltan();

		// update the delta of state
		ssl->deltastate();

		// assign fluxes and state back to pdstate
		dc2ystate_soi(pdstate);
		dc2yflux_soi(pdstate);
	}

};

void Integrator::y2tcstate_veg(float pstate[]){

	for (int i=0; i<NUM_PFT_PART; i++){
     veg->tmp_vegs.c[i]   = pstate[I_VEGC+i];
     veg->tmp_vegs.strn[i]= pstate[I_STRN+i];
	}

    veg->tmp_vegs.labn  = pstate[I_LABN];
    veg->tmp_vegs.deadc = pstate[I_DEADC];
    veg->tmp_vegs.deadn = pstate[I_DEADN];

};

void Integrator::y2tcstate_soi(float pstate[]){

     for(int il =0; il<numsl; il++){
     	ssl->tmp_sois.rawc[il] = pstate[I_L_RAWC+il];
        ssl->tmp_sois.soma[il] = pstate[I_L_SOMA+il];
        ssl->tmp_sois.sompr[il]= pstate[I_L_SOMPR+il];
        ssl->tmp_sois.somcr[il]= pstate[I_L_SOMCR+il];

        ssl->tmp_sois.orgn[il] = pstate[I_L_ORGN+il];
        ssl->tmp_sois.avln[il] = pstate[I_L_AVLN+il];

     }
     ssl->tmp_sois.wdebrisc= pstate[I_WDEBRISC];
     ssl->tmp_sois.wdebrisn= pstate[I_WDEBRISN];
     ssl->tmp_sois.dmossc  = pstate[I_DMOSSC];
     ssl->tmp_sois.dmossn  = pstate[I_DMOSSN];

};

// assign fluxes and state back to pdstate
void Integrator::dc2ystate_veg(float pdstate[]){

	for (int i=0; i<NUM_PFT_PART; i++){
		pdstate[I_VEGC+i] = veg->del_vegs.c[i];
		pdstate[I_STRN+i] = veg->del_vegs.strn[i];
	}

    pdstate[I_LABN]       = veg->del_vegs.labn;
	pdstate[I_DEADC]      = veg->del_vegs.deadc;
	pdstate[I_DEADN]      = veg->del_vegs.deadn;

};

void Integrator::dc2ystate_soi(float pdstate[]){

    for (int il =0; il<numsl; il++){
    	pdstate[I_L_RAWC+il]  = ssl->del_sois.rawc[il];
        pdstate[I_L_SOMA+il]  = ssl->del_sois.soma[il];
        pdstate[I_L_SOMPR+il] = ssl->del_sois.sompr[il];
        pdstate[I_L_SOMCR+il] = ssl->del_sois.somcr[il];
        pdstate[I_L_ORGN+il]  = ssl->del_sois.orgn[il];
        pdstate[I_L_AVLN+il]  = ssl->del_sois.avln[il];

    }

	pdstate[I_WDEBRISC] = ssl->del_sois.wdebrisc;
	pdstate[I_WDEBRISN] = ssl->del_sois.wdebrisn;
	pdstate[I_DMOSSC]   = ssl->del_sois.dmossc;
	pdstate[I_DMOSSN]   = ssl->del_sois.dmossn;

};

void Integrator::dc2yflux_veg(float pdstate[]){

	for (int i=0; i<NUM_PFT_PART; i++){
		pdstate[I_INGPP+i] = veg->del_a2v.ingpp[i];
		pdstate[I_INNPP+i] = veg->del_a2v.innpp[i];
		pdstate[I_GPP+i]   = veg->del_a2v.gpp[i];
		pdstate[I_NPP+i]   = veg->del_a2v.npp[i];
		pdstate[I_RG+i]    = veg->del_v2a.rg[i];
		pdstate[I_RM+i]    = veg->del_v2a.rm[i];
		pdstate[I_LTRC+i]  = veg->del_v2soi.ltrfalc[i];
		pdstate[I_SNUP+i]  = veg->del_soi2v.snuptake[i];
		pdstate[I_NMBOL+i] = veg->del_v2v.nmobil[i];
		pdstate[I_NRSRB+i] = veg->del_v2v.nresorb[i];
		pdstate[I_LTRN+i]  = veg->del_v2soi.ltrfaln[i];
	}

  	pdstate[I_INNUP] = veg->del_soi2v.innuptake;
    pdstate[I_LNUP]  = veg->del_soi2v.lnuptake;

};

void Integrator::dc2yflux_soi(float pdstate[]){

	 for (int il =0; il<numsl; il++){
		pdstate[I_L_RH_RAW +il]  = ssl->del_soi2a.rhrawc[il];
		pdstate[I_L_RH_SOMA +il] = ssl->del_soi2a.rhsoma[il];
		pdstate[I_L_RH_SOMPR+il] = ssl->del_soi2a.rhsompr[il];
		pdstate[I_L_RH_SOMCR+il] = ssl->del_soi2a.rhsomcr[il];

		pdstate[I_L_NIMMOB+il]   = ssl->del_soi2soi.nimmob[il];
		pdstate[I_L_NMIN+il]     = ssl->del_soi2soi.netnmin[il];
	 }

 	 pdstate[I_RH_WD]    = ssl->del_soi2a.rhwdeb;
 	 pdstate[I_RH_DMOSS] = ssl->del_soi2a.rhmossc;

	 pdstate[I_ORGNLOSS] = ssl->del_soi2l.orgnlost;
     pdstate[I_AVLNLOSS] = ssl->del_soi2l.avlnlost;

};

void Integrator::step( const int& numeq, float pstate[], 
                    float pdstate[], float ptstate[],
			        float& pdt ) {
 
  	for ( int i = 0; i < numeq; i++ ) {
    	ptstate[i] = pstate[i] + (pdt * pdstate[i]);
  	}
	
};

int Integrator::checkPools(){

	int negativepool = -1;

	/////
   	if (vegbgc) {
   		for (int i=0; i<NUM_PFT_PART; i++) {
   			if(ydum[I_VEGC+i]<0) return I_VEGC+i;

   			if (veg->nfeed) {
   				if(ydum[I_STRN+i]<0) return I_STRN+i;
   			}
   		}

   		if(ydum[I_DEADC]<0)	return I_DEADC;

		if (veg->nfeed) {
			if(ydum[I_LABN]<0) return I_LABN;
			if(ydum[I_DEADN]<0) return I_DEADN;
   		}

   	}

   	////
   	if (soibgc) {

   		for (int il=0; il<numsl; il++){
   			if(ydum[I_L_RAWC+il]<0) {
   				return I_L_RAWC+il;
   			}

   			if(ydum[I_L_SOMA+il]<0) {
   				return I_L_SOMA+il;
   			}

   			if(ydum[I_L_SOMPR+il]<0) {
   				return I_L_SOMPR+il;
   			}

   			if(ydum[I_L_SOMCR+il]<0) {
   				return I_L_SOMCR+il;
   			}

   			if (ssl->nfeed) {
   				if(ydum[I_L_AVLN+il]<0) {
   					return I_L_AVLN+il;
   				}

   				if(ydum[I_L_ORGN+il]<0) {
   					return I_L_ORGN+il;
   				}
   			}

   		}

   		if(ydum[I_WDEBRISC]<0.) {
			return I_WDEBRISC;
		}

   		if(ydum[I_WDEBRISN]<0.) {
			return I_WDEBRISN;
		}

   		if(ydum[I_DMOSSC]<0.) {
			return I_DMOSSC;
		}

   		if(ydum[I_DMOSSN]<0.) {
			return I_DMOSSN;
		}

   	}

   	return negativepool;
};

int Integrator::boundcon( float ptstate[], float err[], float& ptol ) {

  	int test = ACCEPT;

  	double same = 0.;
  	double zero = 1.e-10;

	// Check carbon and nitrogen state/flux variables
   	if (vegbgc) {
   		//veg C
   		for (int i=0; i<NUM_PFT_PART; i++) {

 //  			if (err[I_VEGC+i] > fabs( ptol * ptstate[I_VEGC+i] ) ){ // this may have issues if the err is very small while ptstate is 0
   	   		same = err[I_VEGC+i] - fabs(ptol * ptstate[I_VEGC+i]);
   			if (same>zero) return test = vegvarkey(I_VEGC)+1+i;

   		    same = err[I_INGPP+i] - fabs(ptol * ptstate[I_INGPP+i]);
   		    if (same>zero) return test = vegvarkey(I_INGPP)+1+i;

   		    same = err[I_INNPP+i] - fabs(ptol * ptstate[I_INNPP+i]);
   		    if (same>zero) return test = vegvarkey(I_INNPP)+1+i;

   		    same = err[I_GPP+i] - fabs(ptol * ptstate[I_GPP+i]);
   		    if (same>zero) return test = vegvarkey(I_GPP)+1+i;

   		    same = err[I_NPP+i] - fabs(ptol * ptstate[I_NPP+i]);
   		    if (same>zero) return test = vegvarkey(I_NPP)+1+i;

   		    same = err[I_RM+i] - fabs(ptol * ptstate[I_RM+i]);
   		    if (same>zero) return test = vegvarkey(I_RM)+1+i;

   		    same = err[I_RG+i] - fabs(ptol * ptstate[I_RG+i]);
   		    if (same>zero) return test = vegvarkey(I_RG)+1+i;

   		    same = err[I_LTRC+i] - fabs(ptol * ptstate[I_LTRC+i]);
   		    if (same>zero) return test = vegvarkey(I_LTRC)+1+i;

   		}

   		same = err[I_DEADC] - fabs( ptol * ptstate[I_DEADC]);
   		if (same>zero) return test = vegvarkey(I_DEADC)+1;

   		//Veg N
   		if (veg->nfeed) {
   			for (int i=0; i<NUM_PFT_PART; i++) {
   				same = err[I_STRN+i] - fabs( ptol * ptstate[I_STRN+i]);
   				if (same>zero) return test = vegvarkey(I_STRN)+1+i;

   				same = err[I_SNUP+i] - fabs( ptol * ptstate[I_SNUP+i]);
   				if (same>zero) return test = vegvarkey(I_SNUP)+1+i;

   				same = err[I_NMBOL+i] - fabs( ptol * ptstate[I_NMBOL+i]);
   				if (same>zero) return test = vegvarkey(I_NMBOL)+1+i;

   				same = err[I_NRSRB+i] - fabs( ptol * ptstate[I_NRSRB+i]);
   				if (same>zero) return test = vegvarkey(I_NRSRB)+1+i;

   				same = err[I_LTRN+i] - fabs( ptol * ptstate[I_LTRN+i]);
   				if (same>zero) return test = vegvarkey(I_LTRN)+1+i;

   			}

   			same = err[I_LABN] - fabs( ptol * ptstate[I_LABN]);
   			if (same>zero) return test = vegvarkey(I_LABN)+1;

   			same = err[I_DEADN] - fabs( ptol * ptstate[I_DEADN]);
   			if (same>zero) return test = vegvarkey(I_DEADN)+1;

   			same = err[I_INNUP] - fabs( ptol * ptstate[I_INNUP]);
   			if (same>zero) return test = vegvarkey( I_INNUP )+1;

   			same = err[I_LNUP] - fabs(ptol * ptstate[I_LNUP]);
  			if (same>zero) return test = vegvarkey( I_LNUP )+1;

   		}
   	} // end of veg_bgc checking

  
    //soil_bgc
   	if (soibgc) {
   		//soil C
   		for(int il =0; il<numsl; il++){

   			same = err[I_L_RAWC+il] - fabs( ptol * ptstate[I_L_RAWC+il]);
   			if (same>zero) return test = soivarkey( I_L_RAWC)+1 +il;

   			same = err[I_L_SOMA+il] - fabs( ptol * ptstate[I_L_SOMA+il]);
   			if (same>zero) return test = soivarkey(I_L_SOMA)+1 +il;

   			same = err[I_L_SOMPR+il] - fabs( ptol * ptstate[I_L_SOMPR+il]);
   			if (same>zero) return test = soivarkey(I_L_SOMPR) +1 + il;

   			same = err[I_L_SOMCR+il] - fabs( ptol * ptstate[I_L_SOMCR+il]);
   			if (same>zero) return test = soivarkey(I_L_SOMCR)+1 + il;

   		    //
   			same = err[I_L_RH_RAW+il] - fabs( ptol * ptstate[I_L_RH_RAW+il]);
   		    if (same>zero) return test = soivarkey(I_L_RH_RAW)+1+il;

   			same = err[I_L_RH_SOMA+il] - fabs( ptol * ptstate[I_L_RH_SOMA+il]);
   		    if (same>zero) return test = soivarkey( I_L_RH_SOMA)+1+il;

   		    same = err[I_L_RH_SOMPR+il] - fabs( ptol * ptstate[I_L_RH_SOMPR+il]);
   		    if (same>zero) return test = soivarkey( I_L_RH_SOMPR)+1+il;

   		    same = err[I_L_RH_SOMCR+il] - fabs( ptol * ptstate[I_L_RH_SOMCR+il]);
   		    if (same>zero) return test = soivarkey( I_L_RH_SOMCR)+1+il;

   		}

   		same = err[I_WDEBRISC] - fabs( ptol * ptstate[I_WDEBRISC]);
		if (same>zero) return test = soivarkey(I_WDEBRISC)+1;

   		same = err[I_WDEBRISN] - fabs( ptol * ptstate[I_WDEBRISN]);
		if (same>zero) return test = soivarkey(I_WDEBRISN)+1;

   		same = err[I_DMOSSC] - fabs( ptol * ptstate[I_DMOSSC]);
		if (same>zero) return test = soivarkey(I_DMOSSN)+1;

   		same = err[I_DMOSSN] - fabs( ptol * ptstate[I_DMOSSN]);
		if (same>zero) return test = soivarkey(I_DMOSSN)+1;

		same = err[I_RH_WD] - fabs( ptol * ptstate[I_RH_WD]);
		if (same>zero) return test = soivarkey(I_RH_WD)+1;

		same = err[I_RH_DMOSS] - fabs( ptol * ptstate[I_RH_DMOSS]);
		if (same>zero) return test = soivarkey(I_RH_DMOSS)+1;

   		// soil N
   		if (ssl->nfeed) {
   			for(int il =0; il<numsl; il++){
   				same = err[I_L_ORGN+il] - fabs(ptol * ptstate[I_L_ORGN+il]);
   				if (same>zero) return test = soivarkey(I_L_ORGN)+1+il;

   				same = err[I_L_AVLN+il] - fabs(ptol * ptstate[I_L_AVLN+il]);
   				if (same>zero) return test = soivarkey(I_L_AVLN)+1+il;

   				//
   				same = err[I_L_NIMMOB+il] - fabs( ptol * ptstate[I_L_NIMMOB+il]);
   				if (same>zero) return test = soivarkey(I_L_NIMMOB)+1+il;

   				same = err[I_L_NMIN+il] - fabs( ptol * ptstate[I_L_NMIN+il]);
   				if (same>zero) {
   					return test = soivarkey(I_L_NMIN)+1+il;
   				}

   			}
		} // end of soil N module

   	} // end of soil_bgc checking

    return test;

};
                            
