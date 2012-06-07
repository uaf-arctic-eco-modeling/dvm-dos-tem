#include "CohortData.h"

CohortData::CohortData(){

};

CohortData::~CohortData(){

};

void CohortData::init(){
	for (int ip=0; ip<NUM_PFT; ip++){
		m_veg.prvfoliagemx[ip]  = 0.;
		m_veg.vegage[ip]  = 0;

	}
};

//accumulators for yearly-averaged/-summed variables from the monthly ones
void CohortData::beginOfYear(){

	// At first, we set the yealy to the monthly,
	// so that if not varies within a year, set them same as the monthly all the time
	// this will avoid non-data just in case, although essentiall all data operating is at monthly
	// ALSO be sure the initialization was done on monthly data sets (i.e., m_veg, m_snow, m_soil)
	y_veg  = m_veg;
	y_snow = m_snow;
	y_soil = m_soil;

	// then, initialize the accumulators ONLY for those varies within a year

	// 1) for vegetation dimension/structure variables
	y_veg.fpcsum = 0.;
	for (int ip=0; ip<numpft; ip++){

		y_veg.lai[ip]  = 0.;
		y_veg.fpc[ip]  = 0.;

		y_veg.fleaf[ip]    = 0.;
		y_veg.ffoliage[ip] = 0.;

		for (int il=0; il<MAX_ROT_LAY; il++){
			y_veg.frootfrac[il][ip] = 0.;
		}
	}

	// 2) snow
	y_snow.numsnwl = MISSING_I;
	y_snow.thick = 0.;
	y_snow.dense = 0.;
	y_snow.extramass = 0.;
	for (int i=0; i<MAX_SNW_LAY; i++) {
		y_snow.age[i] = MISSING_D;          //yearly layered data make no sense
		y_snow.dz[i]  = MISSING_D;
		y_snow.por[i] = MISSING_D;
		y_snow.rho[i] = MISSING_D;
	}

	// 3) soil
	for (int ip=0; ip<NUM_PFT; ip++){
		for (int il=0; il<MAX_SOI_LAY; il++){
			y_soil.frootfrac[il][ip] = 0.;
		}
	}

	y_soil.mossthick  = 0.;
	y_soil.shlwthick  = 0.;
	y_soil.deepthick  = 0.;
	y_soil.totthick   = 0.;

}

//accumulators for those monthly-averaged/-summed variables from the daily ones
void CohortData::beginOfMonth(){

	m_snow.thick = 0.;
	m_snow.dense = 0.;
	m_snow.extramass = 0.;

	m_snow.numsnwl = MISSING_I;
	for (int i=0; i<MAX_SNW_LAY; i++) {
		m_snow.age[i] = MISSING_D;          //monthly layered data make no sense
		m_snow.dz[i]  = MISSING_D;
		m_snow.por[i] = MISSING_D;
		m_snow.rho[i] = MISSING_D;
	}

}

// set the daily dimension variables for veg/soil
void CohortData::beginOfDay(){

	d_veg  = m_veg;       // daily veg dimension will not change within a month, and 'm_veg' will be always set-up or updated
	d_soil = m_soil;      // daily soil dimension will not change within a month, and 'm_soil' will be always set-up or updated

}

// accumulating monthly variables from the daily ones after the daily process is done
void CohortData::endOfDay(const int & dinm){

	m_snow.thick += d_snow.thick/dinm;
	m_snow.dense += d_snow.dense/dinm;
	m_snow.extramass += d_snow.extramass/dinm;

}

// this is called when monthly calculation is done
// then, accumulating the yearly variables from the monthly
void CohortData::endOfMonth(){

	// 1) for vegetation dimension/structure variables
	y_veg.fpcsum += m_veg.fpcsum/12.;
	for (int ip=0; ip<numpft; ip++){

		y_veg.lai[ip] += m_veg.lai[ip]/12.;
		y_veg.fpc[ip] += m_veg.fpc[ip]/12.;

		y_veg.fleaf[ip]   += m_veg.fleaf[ip]/12.;
		y_veg.prvunnormleafmx[ip]= m_veg.prvunnormleafmx[ip];

		y_veg.ffoliage[ip]+= m_veg.ffoliage[ip]/12.;
		y_veg.prvfoliagemx[ip]= m_veg.prvfoliagemx[ip];

		for (int il=0; il<MAX_ROT_LAY; il++){
			y_veg.frootfrac[il][ip] += m_veg.frootfrac[il][ip]/12.;
		}
	}

	// 2) snow
	y_snow.thick += m_snow.thick/12.;
	y_snow.dense += m_snow.dense/12.;
	y_snow.extramass += m_snow.extramass/12.;

	// 3) soil: constant within a year, except for the root distribution
	y_soil = m_soil;
	for (int ip=0; ip<NUM_PFT; ip++){
		for (int il=0; il<MAX_SOI_LAY; il++){
			y_soil.frootfrac[il][ip] += m_soil.frootfrac[il][ip]/12.;    // need to update 'rootfrac' in soil monthly
		}
	}

};

void CohortData::endOfYear(){

};

