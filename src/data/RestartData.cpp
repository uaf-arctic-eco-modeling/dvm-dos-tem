/*
 *  RestartData.cpp
 *
 * Purpose: The data structure is the starting states to run the model continuously
 *         (1) if running is paused, 'RestartData' is the restart point
 *         (2) intially this is for run-stage switch
 *         (3) potentially this can be used for spatial-explicitly run TEM
 *
 * History:
 *     June 28, 2011, by F.-M. Yuan:
 *          (1) Recoding based on DOS-TEM's code;
 *          (2) DVM concepts added, with the Purpose above in mind
 *
 * Important Notes:
 *     (1)
 *
 *
 */

#include "RestartData.h"

RestartData::RestartData(){
	reinitValue();
};

RestartData::~RestartData(){

};

void RestartData::reinitValue(){
	//
	chtid = MISSING_I;

	// atm
	dsr         = MISSING_I;
    firea2sorgn = MISSING_D;     //this is 'fire_a2soi.orgn' to re-deposit fire-emitted N in one FRI

	//vegegetation
    numpft= MISSING_I;
    ysf   = MISSING_I;

    for (int ip=0; ip<NUM_PFT; ip++) {
    	ifwoody[ip]     = MISSING_I;
    	ifdeciwoody[ip] = MISSING_I;
    	ifperenial[ip]  = MISSING_I;
    	nonvascular[ip] = MISSING_I;

    	vegage[ip] = MISSING_I;
    	vegcov[ip] = MISSING_D;
    	lai[ip]    = MISSING_D;
    	for (int i=0; i<MAX_ROT_LAY; i++) {
    		rootfrac[ip][i] = MISSING_D;
    	}

    	vegwater[ip] = MISSING_D;             //canopy water - 'vegs_env'
    	vegsnow[ip]  = MISSING_D;              //canopy snow  - 'vegs_env'

    	for (int i=0; i<NUM_PFT_PART; i++) {
    		vegc[i][ip] = MISSING_D;   // - 'vegs_bgc'
    		strn[i][ip] = MISSING_D;
    	}
    	labn[ip]      = MISSING_D;
    	deadc[ip]     = MISSING_D;
    	deadn[ip]     = MISSING_D;

    	for (int i=0; i<10; i++) {
    		toptA[i][ip] = MISSING_D;
    	}

    	for (int i=0; i<10; i++) {
    		eetmxA[i][ip]= MISSING_D;
    	}
    	for (int i=0; i<10; i++) {
    		unnormleafmxA[i][ip] = MISSING_D;
    	}
    	for (int i=0; i<10; i++) {
    		growingttimeA[i][ip] = MISSING_D;
    	}

		prvfoliagemx[ip] = MISSING_D;        // this is for f(foliage) in GPP to be sure f(foliage) not going down
    }

    // snow
    numsnwl = MISSING_I;
    snwextramass = MISSING_D;
    for(int il =0;il<MAX_SNW_LAY; il++){
		TSsnow[il]  = MISSING_D;
		DZsnow[il]  = MISSING_D;
		LIQsnow[il] = MISSING_D;
		ICEsnow[il] = MISSING_D;
		AGEsnow[il] = MISSING_D;
		RHOsnow[il] = MISSING_D;
	}
	
    //ground-soil
    numsl  = MISSING_I;     //actual number of soil layers
    monthsfrozen = MISSING_D;
    watertab     = MISSING_D;
	for(int il =0;il<MAX_SOI_LAY; il++){
		DZsoil[il]   = MISSING_D;
		TYPEsoil[il] = MISSING_I;
		AGEsoil[il]  = MISSING_I;
		TSsoil[il]   = MISSING_D;
		LIQsoil[il]  = MISSING_D;
		ICEsoil[il]  = MISSING_D;
		FROZENFRACsoil[il]= MISSING_D;
		TEXTUREsoil[il]   = MISSING_I;
	}
   
	for(int il =0;il<MAX_ROC_LAY; il++){
		TSrock[il] = MISSING_D;
		DZrock[il] = MISSING_D;
	}

	for(int il =0;il<MAX_NUM_FNT; il++){
		frontZ[il]  = MISSING_D;
		frontFT[il] = MISSING_I;
	}

	wdebrisc = MISSING_D;
	wdebrisn = MISSING_D;
	for(int il =0;il<MAX_SOI_LAY; il++){
		rawc[il]  = MISSING_D;
		soma[il]  = MISSING_D;
		sompr[il] = MISSING_D;
		somcr[il] = MISSING_D;

		orgn[il] = MISSING_D;
		avln[il] = MISSING_D;

		prvltrfcn[il]  = MISSING_D;
	}

};

