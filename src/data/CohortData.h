#ifndef COHORTDATA_H_
#define COHORTDATA_H_

#include "../inc/errorcode.h"
#include "../inc/timeconst.h"
#include "../inc/cohortconst.h"

#include "../inc/states.h"
#include "../inc/diagnostics.h"

#include "RegionData.h"
#include "GridData.h"

#include <deque>
using namespace std;

class CohortData{
  	public:
  		CohortData();
  		~CohortData();

  		void clear();
  
  		int chtid;
	 	int year;
	 	int month;
	 	int day;

  		int cmttype;   // vegetation community type
  		int yrsdist;    // years since last disturbance

  		bool hasnonvascular;  //if exists non-vascular PFT(s) within the vegetation community

  		int act_vegset;
		int vegyear[MAX_VEG_SET];
		int vegtype[MAX_VEG_SET];
		double vegfrac[MAX_VEG_SET];

		int act_fireset;
		int fireyear[MAX_FIR_OCRNUM];
		int fireseason[MAX_FIR_OCRNUM];
		int firesize[MAX_FIR_OCRNUM];
		int fireseverity[MAX_FIR_OCRNUM];

	    int act_atm_drv_yr;
	    float tair[MAX_ATM_DRV_YR*12];
	    float prec[MAX_ATM_DRV_YR*12];
		float nirr[MAX_ATM_DRV_YR*12];
		float vapo[MAX_ATM_DRV_YR*12];

  	  	// community dimension
  	    vegstate_dim d_veg;   //at daily-interval   - 'd' is for daily
  	    vegstate_dim m_veg;   //at monthly-interval - 'm' is for monthly
  	    vegstate_dim y_veg;   //at yearly-interval  - 'y' is for yearly

  	    vegdiag_dim d_vegd;   //at daily-interval   - 'd' is for monthly
  	    vegdiag_dim m_vegd;   //at monthly-interval - 'm' is for monthly
  	    vegdiag_dim y_vegd;   //at yearly-interval  - 'y' is for yearly

  	    snwstate_dim d_snow;   //at daily-interval   - 'd' is for daily
  	    snwstate_dim m_snow;   //at monthly-interval - 'm' is for monthly
  	    snwstate_dim y_snow;   //at yearly-interval  - 'y' is for yearly

  	    soistate_dim d_soil;   //at daily-interval   - 'd' is for daily
  	    soistate_dim m_soil;   //at monthly-interval - 'm' is for monthly
  	    soistate_dim y_soil;   //at yearly-interval  - 'y' is for yearly

  		deque <double> prveetmxque[NUM_PFT];   //the last 10 years eet/ppt for long-lasting effect of drought on GPP, through f(phenology)
		deque <double> prvunnormleafmxque[NUM_PFT];      // deque to store 'unnormleafmx' of at-most previous 10 years
		deque <double> prvgrowingttimeque[NUM_PFT];      // deque to store 'thermal time (degree-day)' of at-most previous 10 years
		deque <double> toptque[NUM_PFT];                 // a deque-array to store previous 10 year 'topt'

        RegionData * rd;
		GridData * gd;

  	    void beginOfYear();
  	    void beginOfMonth();
  	    void beginOfDay();

  	    void endOfDay(const int & dinm);
  	    void endOfMonth();
  	    void endOfYear();

};

#endif /*COHORTDATA_H_*/
