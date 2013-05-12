#ifndef ATMOSPHERE_H_
#define ATMOSPHERE_H_

#include "../inc/timeconst.h"

#include "AtmosUtil.h"
#include "../data/EnvData.h"
#include "../data/GridData.h"
#include "../data/RegionData.h"

#include <iostream>
#include <cmath>
using namespace std;
class Atmosphere{
   public:
   		Atmosphere();
   		~Atmosphere();
	
		void updateDailyAtm(const int & mid, const int & dayid);
	
    	void prepareMonthDrivingData();
    	void prepareDayDrivingData(const int & mid, const int & usedatmyr, const bool & changeclm, const bool &changeco2);

    	void setCohortData(CohortData* cdp);
    	void setEnvData(EnvData* edp);
 	
	private:

    // yearly
    	float co2;
	
	// monthly
     
		float tair[MAX_ATM_DRV_YR][12];      //
		float prec[MAX_ATM_DRV_YR][12];
        float vapo[MAX_ATM_DRV_YR][12];
        float nirr[MAX_ATM_DRV_YR][12];

        float cld[MAX_ATM_DRV_YR][12];
		float snow[MAX_ATM_DRV_YR][12];
		float rain[MAX_ATM_DRV_YR][12];
		float par[MAX_ATM_DRV_YR][12];
		float ppfd[MAX_ATM_DRV_YR][12];
		float girr[MAX_ATM_DRV_YR][12];

	// daily
		float ta_d[12][31];
		float rain_d[12][31];
		float snow_d[12][31];
		float vap_d[12][31];
		float par_d[12][31];
		float nirr_d[12][31];
	
		float rhoa_d[12][31];
		float svp_d[12][31];
		float dersvp_d[12][31];
		float abshd_d[12][31];
		float vpd_d[12][31];

	// for Equilibrium run, using the first 30 yrs-averaged
		float eq_tair[12];
		float eq_prec[12];
		float eq_cld[12];
		float eq_vapo[12];
		float eq_rain[12];
		float eq_snow[12];
	
		float eq_par[12];
		float eq_ppfd[12];
		float eq_nirr[12];
		float eq_girr[12];
	
		float wetdays ;
		float yrsumday;
		
		AtmosUtil autil;
   		CohortData * cd;
   		EnvData * ed;
	
		float getAirDensity(float const & ta);
		float getVPD (const float & svp, const float vp);
		float getAbsHumDeficit(const float & svp, const float &vp, const float & ta);
		void precsplt(const float & tair,const float & prec, float & snfl, float & rnfl);
   	         
    	float getPET( const float & nirr, const float & tair,const int & dinm);
		float getGIRR( const float &lat, const int& dinm);			
		float getNIRR( const float& clds, const float& girr );				
		float getPAR( const float& clds, const float& nirr );	
		float getCLDS( const float& girr, const float& nirr );
 		float getSatVP(const float & t);		
	 
		float getDensity(const float & ta);
		float getDerSVP( const float & t); 	
		float getDerSVP( const float & tair, const float & svp);
   	
};

#endif /*ATMOSPHERE_H_*/
