/*! \file
 * 
 */
#include "Atmosphere.h"

Atmosphere::Atmosphere(){
   	// if in the mode of spinup or spintransient
   	// initialize with spinup condition for prev
   	// here atmin is NULL , cause a runtime error which is hard to find

	wetdays = 10.; // cru has wetdays output from 1901 to 2002, but not for scenario run
	// temperarily assume wetdays = 10;

};

Atmosphere::~Atmosphere(){
	
};

// calculating daily 'atm' data for all driving years - called in 'RunCohort::reinit()'
void Atmosphere::prepareMonthDrivingData(){
     float lat = cd->gd->lat;

     //ta degC, prec mm/mon, nirr w/m2, vap mbar, 
     for(int iy =0; iy<cd->act_atm_drv_yr; iy++){
       	for (int im=0; im<12; im++){
            int iyim =iy*12+im;
       		tair[iy][im] = cd->tair[iyim];
       		prec[iy][im] = cd->prec[iyim];
       		nirr[iy][im] = cd->nirr[iyim];
       		vapo[iy][im] = cd->vapo[iyim]*=100.; // convert from mbar to pa
       	}	
     }
     
     for(int iy =0; iy<cd->act_atm_drv_yr; iy++){
       	for (int im=0; im<12; im++){
       		precsplt(tair[iy][im], prec[iy][im], snow[iy][im],rain[iy][im]); // distinguish prec as snow or rainfall
       	}	
     }

   	// prepare other variables
   	for(int iy=0; iy<cd->act_atm_drv_yr; iy++){
   		yrsumday=0; //Yi: may 17, 2010
   		for(int im=0; im<12;im++){
   		   girr[iy][im]= getGIRR(lat, DINM[im]);
	       cld[iy][im] = getCLDS(girr[iy][im], nirr[iy][im]);
	       par[iy][im] = getPAR(cld[iy][im],  nirr[iy][im] );
    	}
   	}

    // for normalized (mean) climate data
    for(int im =0; im<12; im++){
   		yrsumday=0; //Yi: may 17, 2010
    	eq_tair[im]=0.;
    	eq_prec[im]=0.;
    	eq_rain[im]=0.;
    	eq_snow[im]=0.;
    	eq_nirr[im]=0.;
    	eq_vapo[im]=0.;
    			
    	int max_yr = fmin(MAX_ATM_NOM_YR, cd->act_atm_drv_yr);
    	for(int iy=0; iy<max_yr; iy++){    //Yuan: average over the first 30 yrs atm data
    		eq_tair[im] += tair[iy][im]/max_yr;
    		eq_prec[im] += prec[iy][im]/max_yr;
    		eq_rain[im] += rain[iy][im]/max_yr;
    		eq_snow[im] += snow[iy][im]/max_yr;
    		eq_nirr[im] += nirr[iy][im]/max_yr;
    		eq_vapo[im] += vapo[iy][im]/max_yr;

    		eq_girr[im] += girr[iy][im]/max_yr;
    		eq_cld[im]  += cld[iy][im]/max_yr;
    		eq_par[im]  += par[iy][im]/max_yr;
		}
	}

};
 
// calculating daily 'atm' data for ONE year at yearly time-step - called in 'RunCohort.cpp'
void Atmosphere::prepareDayDrivingData(const int & yrcount, const int & usedatmyr, const bool & changeclm, const bool &changeco2){

	float tad1[31], vapd1[31], precd1[31];
    float pvalt, cvalt, nvalt;
    float pvalv, cvalv, nvalv;
    float pvalp, cvalp, nvalp;
    int dinmprev, dinmcurr, dinmnext;

    //
    if (!changeclm) {
    	for(int im =0; im<12;im++){
    		cvalt = eq_tair[im];
    		cvalv = eq_vapo[im];
    		cvalp = eq_prec[im];
    		dinmcurr = DINM[im];
    		if(im==0){
    		  	  pvalt = eq_tair[11];
    		  	  pvalv = eq_vapo[11];
    		  	  pvalp = eq_prec[11];
    		  	  
    		  	  nvalt = eq_tair[im+1];
    		  	  nvalv = eq_vapo[im+1];
    		  	  nvalp = eq_prec[im+1];
    		  	  
    		  	  dinmprev = DINM[11];
    		  	  dinmnext = DINM[im+1];

    		  	  
    		}else if (im==11){
    		  	  pvalt = eq_tair[im-1];
    		  	  pvalv = eq_vapo[im-1];
    		  	  pvalp = eq_prec[im-1];
    		  	  
    		  	  nvalt = eq_tair[0];
    		  	  nvalv = eq_vapo[0];
    		  	  nvalp = eq_prec[0];
    		  	  
    		  	  dinmnext = DINM[0];
    		  	  dinmprev = DINM[im-1];
    		  	  
    		}else{
    		  	  pvalt = eq_tair[im-1];
    		  	  pvalv = eq_vapo[im-1];
    		  	  pvalp = eq_prec[im-1];
    		  	  
    		  	  nvalt = eq_tair[im+1];
    		  	  nvalv = eq_vapo[im+1];
    		  	  nvalp = eq_prec[im+1];
    		  	  
    		  	  dinmprev = DINM[im-1];
    		  	  dinmnext = DINM[im+1];
    		  	  
    		}
              
            autil.updateDailyDriver(tad1, pvalt ,cvalt, nvalt,
                       dinmprev, dinmcurr, dinmnext);
  			autil.updateDailyDriver(vapd1,  pvalv ,cvalv, nvalv,
                    dinmprev, dinmcurr, dinmnext);
  			autil.updateDailyPrec(precd1, dinmcurr, cvalt, cvalp);
  		   	
  		   	for (int id =0; id<31; id++){
  		      	ta_d[im][id]  = tad1[id];
  		      	vap_d[im][id] = vapd1[id];
  		      	precsplt(ta_d[im][id], precd1[id], snow_d[im][id], rain_d[im][id]);
  		      
  		      	rhoa_d[im][id]= getDensity(tad1[id]);
  		      	svp_d[im][id] = getSatVP(tad1[id]);
  		       	vpd_d[im][id] = getVPD(svp_d[im][id], vap_d[im][id]);
  		       
  		      	dersvp_d[im][id]= getDerSVP(tad1[id], svp_d[im][id]);
  		      	abshd_d[im][id] = getAbsHumDeficit(svp_d[im][id], vap_d[im][id], tad1[id]);

  				//not yet interpolated variable
	      		par_d[im][id]  = eq_par[im];
  				nirr_d[im][id] = eq_nirr[im];

  		   	}
  		   
    	}

    } else { // for spinup/transient/scenario

			int iy= yrcount;

    	    iy = yrcount%usedatmyr;    //this will reuse the first 'usedatmyr' period of whole atm data set

      		for(int im =0; im<12;im++){
    		 	cvalt = tair[iy][im];
    		 	cvalv = vapo[iy][im];
    		 	cvalp = prec[iy][im];
    		 	dinmcurr = DINM[im];
    		  	if(im==0){
    		  	  	if(iy==0){
    		  	  		pvalt = tair[0][0];
    		  	  		pvalv = vapo[0][0];
    		  	  		pvalp = prec[0][0];
    		  	  	}else{
    		  	  		pvalt = tair[iy-1][11];
    		  	  		pvalv = vapo[iy-1][11];
    		  	  		pvalp = prec[iy-1][11];
    		  	  	}
    		  	  	nvalt = tair[iy][im+1];
    		  	  	nvalv = vapo[iy][im+1];
    		  	  	nvalp = prec[iy][im+1];
    		  	  	dinmnext = DINM[im+1];
    		  	  	dinmprev = DINM[11];
    		  	  
    		  	  
    		  	}else if (im==11){
    		  	  	pvalt = tair[iy][im-1];
    		  	  	pvalv = vapo[iy][im-1];
    		  	  	pvalp = prec[iy][im-1];
    		  	 	if(iy==usedatmyr-1){
    		  	  		nvalt = tair[iy][11];
    		  	  		nvalv = vapo[iy][11];
    		  	  		nvalp = prec[iy][11];
    		  	  	}else{
    		  	  		nvalt = tair[iy+1][0];
    		  	  		nvalv = vapo[iy+1][0];
    		  	  		nvalp = prec[iy+1][0];
    		  	  	}
    		  	  	dinmnext = DINM[0];
    		  	  	dinmprev = DINM[im-1];
    		  	  
    		  	}else{
    		  	  	pvalt = tair[iy][im-1];
    		  	  	pvalv = vapo[iy][im-1];
    		  	  	pvalp = prec[iy][im-1];
    		  	  
    		  	  	nvalt = tair[iy][im+1];
    		  	  	nvalv = vapo[iy][im+1];
    		  	  	nvalp = prec[iy][im+1];
    		  	  
    		  	  	dinmnext = DINM[im+1];
    		  	  	dinmprev = DINM[im-1];
    		  	  
    		  	}
                autil.updateDailyDriver(tad1, pvalt ,cvalt, nvalt,
                       dinmprev, dinmcurr, dinmnext);
  				autil.updateDailyDriver(vapd1,  pvalv ,cvalv, nvalv,
                     dinmprev, dinmcurr, dinmnext);
  				autil.updateDailyPrec(precd1, dinmcurr, cvalt, cvalp);
  		   		
  		   		for (int id =0; id<dinmcurr; id++){
  		      		ta_d[im][id] = tad1[id];
  		      		vap_d[im][id] = vapd1[id];
  		      		precsplt(ta_d[im][id], precd1[id],snow_d[im][id], rain_d[im][id]);
  		      
  		      		rhoa_d[im][id] = getDensity(tad1[id]);
  		      		svp_d[im][id] = getSatVP(tad1[id]);
  		      		vpd_d[im][id] = getVPD(svp_d[im][id], vap_d[im][id]);
  		      		dersvp_d[im][id] = getDerSVP(tad1[id], svp_d[im][id]);
  		      		abshd_d[im][id] = getAbsHumDeficit(svp_d[im][id], vap_d[im][id] , tad1[id]);

  	  				//not yet interpolated variable
  		      		par_d[im][id]  = par[iy][im];
  	  				nirr_d[im][id] = nirr[iy][im];

  		   		} //id
    		}//im
    }

	if (changeco2) {
		if (yrcount<MAX_CO2_DRV_YR) {
			co2  = cd->rd->co2[yrcount];
		} else {
			co2  = cd->rd->co2[MAX_CO2_DRV_YR-1];	//this reuse the last CO2 data
		}
	} else {
	   	co2  = cd->rd->initco2;
	}

}; 


void Atmosphere::updateDailyAtm(const int & mid, const int & dayid){

	ed->d_atms.co2 = co2;
	ed->d_atms.ta  = ta_d[mid][dayid];
	ed->d_a2l.rnfl = rain_d[mid][dayid];
	ed->d_a2l.snfl = snow_d[mid][dayid];
	ed->d_a2l.prec = rain_d[mid][dayid]+snow_d[mid][dayid];
	ed->d_a2l.par  = par_d[mid][dayid];
	ed->d_a2l.nirr = nirr_d[mid][dayid];
	ed->d_atmd.vp  = vap_d[mid][dayid];
	ed->d_atmd.svp = svp_d[mid][dayid];
	ed->d_atmd.vpd = vpd_d[mid][dayid];
	
	if(ed->d_a2l.prec >0.0){
	  	ed->d_atms.dsr = 0;
	}else{
	  	ed->d_atms.dsr++;	
	}
	
};


void Atmosphere::precsplt(const float & tair,const float & prec, float & snfl, float & rnfl){
  /* *************************************************************
  Willmott's assumptions on snow/rain split:
  ************************************************************** */
  	if ( tair > 0.0 ) { // monthly use -1.0
    	rnfl = prec;
    	snfl = 0.0;
  	} else  {
    	rnfl = 0.0;
    	snfl = prec;
  	}

};
   
float Atmosphere::getDensity(const float & ta){
 	float rhoa ; // atmosphere density 
 	rhoa =1.292 - (0.00428 *ta);	
 	return rhoa;	
};

float Atmosphere::getSatVP(const float & tair){
 	float svp; // saturated vapor pressure (Pa)
/* 	% Guide to Meteorological Instruments and Methods of Observation (CIMO Guide)
 	%      (WMO, 2008), for saturation vapor pressure
 	%      (1) ew = 6.112 e(17.62 t/(243.12 + t))                                                                  [2]
 	%      with t in [°C] and ew in [hPa, mbar]

 	%      (2) ei = 6.112 e(22.46 t/(272.62 + t))                                                                      [14]
 	%      with t in [°C] and ei in [hPa]
*/
 	if(tair>0){
 		svp = 6.112 * exp(17.63 * tair/ (243.12 + tair) ) * 100.0;
 	} else {
 		svp = 6.112 * exp(17.27 * tair/ (272.62 + tair) ) * 100.0;
 	}
 	
 	
 	return svp;
};
 
float Atmosphere::getDerSVP( const float & tair){//Pa/degC
   float beta ;
   float deltat =0.2;
   float t1, t2;
   float svp1, svp2;
   t1 = tair +deltat;
   t2 = tair -deltat;
   svp1 = getSatVP(t1);
   svp2 = getSatVP(t2);
   
   beta = (svp1-svp2)/(t1-t2);
   return beta;	
};	
 
float Atmosphere::getDerSVP( const float & tair, const float & svp){//not used
   float beta ;
   beta = 4099. * svp /pow((tair +237.3),2.);
   return beta;	
};	
 
float Atmosphere::getAirDensity(float const & ta){
	// input air temperature, ta (degC)
	// output air density , rhoa (kg/m3)
	float rhoa;
	rhoa = 1.292 - (0.00428 * ta);
	return rhoa;
}; 
 
float Atmosphere::getAbsHumDeficit(const float & svp, const float &vp, const float & ta){
	const float Mw = 18; // g/mol;
	const float R = 8.3143; // J/mol/k
	float dewpnt; //degC
	float ashd;
  	
  	float temp = (17.502 - log(vp/0.611));	
  	if(temp>0 || temp< 0){
  		dewpnt = (240.97 * log(vp/0.611))/temp;
  	}else{
  		dewpnt = ta;
  	}
  	
  	ashd = fabs((Mw/R) * ((svp * 1000./(273.2 + dewpnt)) - (vp *1000/(273.2 + ta))));
  	return ashd;
};

float Atmosphere::getVPD (const float & svp, const float vp){
	float vpd =svp -vp;
	if (vpd<0) {vpd =0;}
  	return vpd; // unit Pa	
};

float Atmosphere::getGIRR(const float &lat, const int& dinm){

  	const float pi = 3.141592654;                // Greek "pi"
  	const float sp = 1368.0 * 3600.0 / 41860.0;  // solar constant

  	float lambda;
  	float sumd;
  	float sig;
  	float eta;
  	float sinbeta;
  	float sb;
  	float sotd;
  	int day;
  	int hour;
  	float gross;

  	lambda = lat * pi / 180.0;
  	gross = 0.0;
  	for ( day = 0; day < dinm; day++ ) {
    	++yrsumday;
    	sumd = 0;
    	sig = -23.4856*cos(2 * pi * (yrsumday + 10.0)/365.25);
    	sig *= pi / 180.0;

    	for ( hour = 0; hour < 24; hour++ ){
      		eta = (float) ((hour+1) - 12) * pi / 12.0;
      		sinbeta = sin(lambda)*sin(sig) + cos(lambda)*cos(sig)*cos(eta);
      		sotd = 1 - (0.016729 * cos(0.9856 * (yrsumday - 4.0)
             * pi / 180.0));

      		sb = sp * sinbeta / pow((double)sotd,2.0);
      		if (sb >= 0.0) { sumd += sb; }
    	}

    	gross += sumd;
  	}

  	gross /= (float) dinm;
  	gross *= 0.484; // convert from cal/cm2day to W/m2

  	return gross;

};

float Atmosphere::getNIRR( const float& clds, const float& girr ){
	//W/m2
  	float nirr;

  	if ( clds >= 0.0 ) {
    	nirr = girr * (0.251 + (0.509*(1.0 - clds/100.0)));
  	} else { 
  		nirr = MISSING_D;
  	}

  	return nirr;

};


float Atmosphere::getCLDS( const float & girr, const float& nirr ){

  	float clouds;

  	if ( nirr >= (0.76 * girr) ) {
  		clouds = 0.0;
  	}else {
    	clouds = 1.0 - (((nirr/girr) - 0.251)/0.509);
    	clouds *= 100.0;
  	}

  	if ( clouds > 100.0 ) { clouds = 100.0; }

  	return clouds;

};

float Atmosphere::getPAR( const float& clds, const float& nirr ){
	//W/m2
  	float par;

  	if ( clds >= 0.0 ) {
      	par = nirr * ((0.2 * clds / 100.0) + 0.45);
  	} else { 
  		par = MISSING_D;
  	}

  	return par;
};

void Atmosphere::setCohortData(CohortData* cdp){
	cd = cdp;
};

void Atmosphere::setEnvData(EnvData* edp){
	ed = edp;
};
