/*! this class contains the bgc at monthly and annually time steps.
 *  It also provides fuctions for sum/avg short timestep data to long timestep.
 * 
 */
#ifndef BGCDATA_H_
#define BGCDATA_H_

#include "../inc/errorcode.h"
#include "../inc/diagnostics.h"
#include "../inc/fluxes.h"
#include "../inc/states.h"

#include <iostream>
#include <math.h>

#include "EnvData.h"
#include "RegionData.h"
#include "GridData.h"
#include "CohortData.h"

#include <deque>

class BgcData{
 	public:
  		BgcData();
  		~BgcData();	

  		void clear();
	
		CohortData * cd;

		//monthly
		vegstate_bgc m_vegs;
		soistate_bgc m_sois;
		vegdiag_bgc m_vegd;
		soidiag_bgc m_soid;
		lnd2atm_bgc m_l2a;
		atm2veg_bgc m_a2v;
		veg2atm_bgc m_v2a;
		veg2soi_bgc m_v2soi;
		soi2veg_bgc m_soi2v;
		veg2veg_bgc m_v2v;
		soi2lnd_bgc m_soi2l;
		soi2atm_bgc m_soi2a;
		atm2soi_bgc m_a2soi;
		soi2soi_bgc m_soi2soi;

		//annually
		vegstate_bgc y_vegs;
		soistate_bgc y_sois;
		vegdiag_bgc y_vegd;
		soidiag_bgc y_soid;
		lnd2atm_bgc y_l2a;
		atm2veg_bgc y_a2v;
		veg2atm_bgc y_v2a;
		veg2soi_bgc y_v2soi;
		soi2veg_bgc y_soi2v;
		veg2veg_bgc y_v2v;
		soi2lnd_bgc y_soi2l;
		soi2atm_bgc y_soi2a;
		atm2soi_bgc y_a2soi;
		soi2soi_bgc y_soi2soi;

		deque <double> prvltrfcnque[MAX_SOI_LAY];

    	void land_beginOfYear();
   		void land_endOfMonth();

   		void veg_beginOfYear();
   		void veg_beginOfMonth();
   		void veg_endOfMonth();
   		void veg_endOfYear();

   		void soil_beginOfYear();
   		void soil_beginOfMonth();
   		void soil_endOfMonth();
    
    private:

};

#endif /*BGCDATA_H_*/
