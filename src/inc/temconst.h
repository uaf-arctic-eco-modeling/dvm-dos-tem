/*! \file 
 * this header provides variable numbers used in Integrator
 * It mainly used in indexing enumtype 'temkey' in Integrator.h
 * So, any modification in 'temkey', it should be done here as well
 * */
 
#ifndef TEMCONST_H_
#define TEMCONST_H_
#include "layerconst.h"
#include "cohortconst.h"

    // number of vegetation BGC state variables
	const int NUM_VEG_STATE = 2*NUM_PFT_PART    // C & structrual N content in defined-no. of tissues
	                          +	3;              // labible N, C & N in dead veg
	// number of layered soil BGC state variables
	const int NUM_SOI_STATE = 6*MAX_SOI_LAY     // 4 soil C pools, orgn, and avln
                              +4;               // wderis C and N, dmoss C and N

	// number of state variables
	const int MAXSTATE = NUM_VEG_STATE + NUM_SOI_STATE;

	// number of vegetation C/N flux variables
	const int NUM_VEG_FLUX = 11*NUM_PFT_PART   // GPP, (IN)NPP, RM, RG, LTRFC, VINNUP, VSUP, VNMBOL, VNRSRB, LTRFN
			                 +2;             // INGPP, N uptake for labile N pool

	// number of soil C/N flux variables
	const int NUM_SOI_FLUX = 6*MAX_SOI_LAY    // RHRAWC, RHSOMA, RHSOMPR, RHSOMCR, NNETMIN, NIMMOB
							+4;               // RH_WDERIS, AVLNIN, ORGNIN, AVLNLOST

	// number of ODE equations
	const int NUMEQ_VEG = NUM_VEG_STATE + NUM_VEG_FLUX;
	const int NUMEQ_SOI = NUM_SOI_STATE + NUM_SOI_FLUX;
	const int NUMEQ = NUMEQ_SOI;    //NOTE: in this case, NUMEQ must be the larger number of NUMEQ_VEG, NUMEQ_SOI


#endif /*TEMCONST_H_*/
