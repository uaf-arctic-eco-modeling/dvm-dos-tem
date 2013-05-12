/*
 * Vegetation_Env.cpp
 *
 * Purpose: Calculating radiation, water processes of canopy
 *
 * History:
 *     June 28, 2011, by F.-M. Yuan:
 *          (1) Recoding based on DOS-TEM's code;
 *
 * Important:
 *     (1) Parameters are read from 'CohortLookup.cpp', and set to 'envpar' (struct:: vegpar_env)
 *     (2) No calibrated Parameters at this stage
 *
 *     (3) The calculation is for ONE PFT only, so when calling it must be set ONE important index:
 *          pfttype
 *     (4) FOUR (4) data pointers must be initialized by calling corresponding 'set...' methods
 *          chtlu, cd, ed, fd
 *
 */

#include "Vegetation_Env.h"

Vegetation_Env::Vegetation_Env(){
	ipft = MISSING_I;
};

Vegetation_Env::~Vegetation_Env(){
	
};

//set the parameters from 'CohortLookup'
void Vegetation_Env::initializeParameter(){
    envpar.albvisnir = chtlu->albvisnir[ipft];
    envpar.er        = chtlu->er[ipft];
    envpar.ircoef    = chtlu->ircoef[ipft];
    envpar.iscoef    = chtlu->iscoef[ipft];

	envpar.gl_bl     = chtlu->gl_bl[ipft];
    envpar.gl_c      = chtlu->gl_c[ipft];
    
    envpar.vpd_close = chtlu->vpd_close[ipft];
    envpar.vpd_open  = chtlu->vpd_open[ipft];
    envpar.glmax     = chtlu->glmax[ipft];
    envpar.ppfd50    = chtlu->ppfd50[ipft];
    
	
};

// set the intial monthly LAI from 'CohortLookup'
void Vegetation_Env::initializeState(){

	ed->d_vegs.rwater = chtlu->initvegwater[ipft];
	ed->d_vegs.snow   = chtlu->initvegsnow[ipft];

};

void Vegetation_Env::initializeState5restart(RestartData* resin){
	
	ed->d_vegs.rwater = resin->vegwater[ipft];
	ed->d_vegs.snow   = resin->vegsnow[ipft];
	
};

//solar radiation (unit: W/m2) on canopy and its energy balance
void Vegetation_Env::updateRadiation(){

	//lai/fpc from 'cd'
	double envlai = cd->m_veg.lai[ipft];
	double fpc = cd->m_veg.fpc[ipft];

	//some constants
	double EPAR = 4.55 ;   //an average energy for PAR photon (umol/J)

	// solar radiation and its energy balance
	ed->d_v2a.swrefl = (ed->d_a2l.nirr*fpc) *envpar.albvisnir; // unit W/m2 (FPC adjusted)
	ed->d_a2v.swdown = (ed->d_a2l.nirr*fpc) - ed->d_v2a.swrefl;

	ed->d_v2g.swthfl  = ed->d_a2v.swdown * exp(-envpar.er * envlai);
	ed->d_a2v.swinter = ed->d_a2v.swdown - ed->d_v2g.swthfl;

	// PAR and its absorption by canopy
	double par = ed->d_a2l.par*fpc;   // fpc adjusted here
	
	ed->d_a2v.pardown    = par*(1.0 - envpar.albvisnir);
	ed->d_a2v.parabsorb  = ed->d_a2v.pardown*(1.0-exp(-envpar.er * envlai)) ;// absorbed PAR: W/m2
	
	double ppfd50  = envpar.ppfd50 ;//mumol/m2s, ppfd for 0.5 stomatal closure
	ed->d_vegd.m_ppfd = ed->d_a2v.pardown*EPAR/(ed->d_a2v.pardown*EPAR + ppfd50) ;//
};
	
//VEGETATION DAILY WATER BALANCE CALCULATION
void Vegetation_Env::updateWaterBalance(const double & daylhr){

	//lai/fpc from 'cd'
	double envlai = cd->m_veg.lai[ipft];
	double fpc = cd->m_veg.fpc[ipft];

	//
	double daylsec = daylhr* 3600.;// from hour to sec
	double EPAR = 4.55 ;           //an average energy for PAR photon (umol/J)
	
	// variables calculated in 'atmosphere.cpp'
   	double vpd  = ed->d_atmd.vpd;
   	double ta   = ed->d_atms.ta;
   	double snfl = ed->d_a2l.snfl;  // this is the total atm to land
   	double rnfl = ed->d_a2l.rnfl;
	ed->d_a2v.snfl = snfl*fpc;   //note: FPC adjusted here
	ed->d_a2v.rnfl = rnfl*fpc;

   	double downpar = ed->d_a2v.pardown;   //note: already FPC adjusted

	if(envlai >0){

		//precipitation interception and throughfall
		ed->d_a2v.rinter = getRainInterception(ed->d_a2v.rnfl, envlai);
		ed->d_a2v.sinter = getSnowInterception(ed->d_a2v.snfl, envlai);

		ed->d_v2g.rthfl = ed->d_a2v.rnfl- ed->d_a2v.rinter;
		ed->d_v2g.sthfl = ed->d_a2v.snfl -ed->d_a2v.sinter;
	
		//evaportranspiration
		//temperature and pressure correction factor for conductances
		double gcorr = 1.; //pow( (atmsd->ta +273.15)/293.15, 1.75); // * 101300/pa;
		double gl_st = 0.;
		ed->d_vegd.m_vpd=0.;
		
		if(ed->d_vegd.btran>0){
     		gl_st = getLeafStomaCond(ta,downpar*EPAR, vpd, ed->d_vegd.btran,
					ed->d_vegd.m_ppfd, ed->d_vegd.m_vpd);
		}
		
		gl_st *= gcorr; 
		double gl_bl = envpar.gl_bl; //boundary layer conductance (projected area basis) m/s
		gl_bl *= gcorr;
		double gl_c  = envpar.gl_c; // cuticular conductance m/s
		gl_c *=gcorr;
	
		double gl_t_wv = (gl_bl *gl_st)/(gl_bl+gl_st+gl_c);
		double gl_sh = gl_bl;
		double gl_e_wv = gl_bl;
		double gc_e_wv = gl_e_wv * envlai;
		double gc_sh =gl_sh * envlai;
		double gl_t_wv_pet = (gl_bl *envpar.glmax)/(gl_bl+envpar.glmax+gl_c);
		double gl_sh_pet = gl_bl;
		double gl_e_wv_pet = gl_bl;
		double gc_e_wv_pet = gl_e_wv_pet * envlai;
		double gc_sh_pet =gl_sh_pet * envlai;
	
		double sw =ed->d_a2v.swinter;
		double daytimesw = sw;
		double rainsw = sw;
		double rv, rh;
		double rv_pet, rh_pet;
		double vpdpa = vpd; //Pa
	
		if(ed->d_a2v.rinter>0.){
		
			rv = 1./gc_e_wv;
			rh = 1./gc_sh;
			rv_pet = 1./gc_e_wv_pet;
			rh_pet = 1./gc_sh_pet;
		
			double et1 = getPenMonET(ta,vpdpa, rainsw, rv, rh);
			double et1_pet= getPenMonET(ta,vpdpa, rainsw, rv_pet, rh_pet);
			double dayl1 = ed->d_a2v.rinter/et1;
			
			if(dayl1>daylsec){
		  		if(daylsec>0.){
		  			ed->d_v2a.tran = 0.;
		  			ed->d_v2a.evap = et1 *daylsec;
		  		} else{
		  			ed->d_v2a.tran=0.;
		  			ed->d_v2a.evap=0.;
		  		}
			} else {
		  		ed->d_v2a.evap = ed->d_a2v.rinter;
		  		daylsec -= dayl1;
		  		rv = 1.0/gl_t_wv;
		  		rh =1.0/gl_sh;
		  		double et2= getPenMonET(ta, vpdpa, rainsw, rv, rh);
		  		ed->d_v2a.tran = et2 * daylsec;
			}
		
			double dayl1_pet = ed->d_a2v.rinter/et1_pet;
			if(dayl1_pet>daylsec){
		  		if(daylsec>0.){
		  			ed->d_v2a.tran_pet = 0.;
		  			ed->d_v2a.evap_pet = ed->d_v2a.evap;
		  		} else {
		  			ed->d_v2a.tran_pet = 0.;
		  			ed->d_v2a.evap_pet = 0.;
		  		}
			} else {
		  		ed->d_v2a.evap_pet = ed->d_a2v.rinter;
		  		daylsec -= dayl1_pet;
		  		rv_pet = 1.0/gl_t_wv_pet;
		  		rh_pet =1.0/gl_sh_pet;
		  		double et2_pet= getPenMonET(ta,vpdpa, rainsw, rv_pet, rh_pet);
		  		ed->d_v2a.tran_pet = et2_pet * daylsec;
			}
	
		} else { // no interception
		  
		  	ed->d_v2a.evap = 0.;
		  	rv = 1.0/gl_t_wv;
		  	rh =1.0/gl_sh;
		  	double et3= getPenMonET(ta, vpdpa, daytimesw, rv, rh);
		  	ed->d_v2a.tran = et3 * daylsec;

		  	ed->d_v2a.evap_pet = 0.;
		  	rv_pet = 1.0/gl_t_wv_pet;
		  	rh_pet =1.0/gl_sh_pet;
		  	double et3_pet= getPenMonET(ta, vpdpa, daytimesw, rv_pet, rh_pet);
		  	ed->d_v2a.tran_pet = et3_pet * daylsec;
		  
		} 
	
		ed->d_v2a.sublim = getCanopySubl(ed->d_a2v.swdown,ed->d_a2v.sinter, envlai);
		ed->d_vegd.cc = gc_e_wv;
		ed->d_vegd.rc = 1./ed->d_vegd.cc;

	 	ed->d_vegs.snow  += (ed->d_a2v.sinter - ed->d_v2a.sublim);
	 	ed->d_vegs.rwater+= (ed->d_a2v.rinter - ed->d_v2a.evap);

	 	ed->d_v2g.sdrip = 0.0;
	 	double maxvegsnow = 0.10*envlai;   // that 0.10 LAI mm snow on vegetation is arbitrary - needs more mechanism to do this
	 	if (ed->d_vegs.snow>maxvegsnow) {
		 	ed->d_v2g.sdrip = ed->d_vegs.snow - maxvegsnow;
	 	}
	 	ed->d_vegs.snow -= ed->d_v2g.sdrip;

	 	ed->d_v2g.rdrip = 0.0;
	 	double maxvegrain = 0.05*envlai;   // that 0.05 LAI mm rain storage is arbitrary - needs more mechanism to do this
	 	if (ed->d_vegs.rwater>maxvegrain) {
		 	ed->d_v2g.rdrip = ed->d_vegs.rwater - maxvegrain;
	 	}
	 	ed->d_vegs.rwater -= ed->d_v2g.rdrip;
	 
	} else {   //envlai <=0, i.e., no vegetation?
		ed->d_vegd.cc =0.;
		ed->d_vegd.rc =0.;
		ed->d_a2v.rinter =0.;
		ed->d_a2v.sinter =0.;
		ed->d_v2a.sublim =0.;
		ed->d_v2a.tran   =0.;
		ed->d_v2a.evap   =0.;
		
		ed->d_v2a.tran_pet =0.;
		ed->d_v2a.evap_pet =0.;
		
		ed->d_v2a.sublim =0.;
	    ed->d_v2g.rdrip = 0;
	    ed->d_v2g.sdrip = 0;
	    ed->d_v2g.rthfl = rnfl;
	    ed->d_v2g.sthfl = snfl ;
	    ed->d_vegs.snow  =0.;
	    ed->d_vegs.rwater=0.;
	    	
	}
 	         
};

double Vegetation_Env::getPenMonET(const double & ta, const double& vpd, const double &irad,
				const double &rv, const double & rh){
		double et; // out , mmH2O/m2s
		double CP =1004.64 ; // specific heat capacity of dry air [J/kgK)
		double tk = ta+273.15;
		double pa = 101300;// pressure , Pa
		double rho = 1.292- (0.00428 * ta); // air density	kg/m3
		double EPS=0.6219; // ratio of mole weights
		double SBC= 5.67e-8; //Stefan-boltzmann constant W/m2K4
		/*resistance to raiative heat transfer through air*/
		double rr = rho * CP /(4.0 * SBC * tk* tk*tk);		
		/* resistance to convective heat tranfer: rh*/
		/*resistance to latent heat transfer rv*/
		/*combined resistance to convectie and radiative heat transfer,
		 * parallel resistances:rhr= (rh*rr)/(rh+rr)*/
		 double rhr = (rh*rr)/(rh+rr);
		/*latent heat of vaporization as a function of ta*/
		double lhvap = 2.5023e6 -2430.54 *ta;
		double dt =0.2;
		double t1 = ta+dt;
		double t2 =ta-dt;
		/*saturated vapor pressure at t1, t2*/
		double pvs1 = 610.7 *exp(17.38 *t1/(239.+t1));
		double pvs2 = 610.7 *exp(17.38 *t2/(239.+t2));
		/*slope of pvs vs. T curve at T*/
		double slope = (pvs1-pvs2)/(t1-t2);	
		/*evapotranspiration*/
		et = (slope*irad+ rho*CP *vpd/rhr)/((pa * CP *rv)/(lhvap*EPS *rhr)+slope);
		return et/lhvap;		
};

double Vegetation_Env::getCanopySubl(const double & rac, const double & sinter, const double & lai ){
    double sub;
    double psub; //potential sub
    double snow_int =envpar.iscoef;
    double lamdaw = 2.501e6; // latent heat of vaporization J/kg
    double lf = 3.337e5 ;// latent heat of fusion J/kg	
    //rac in unit W/m2
    // change the unit from J/kg to MJ/mm
    double phasechange = (lamdaw+lf)/10e6 ;
    double sub1 = (rac*86400)/phasechange; 
    //double sub2 = lai/envpar.all2prj * snow_int;
    double sub2 = lai * snow_int;
    
    if(sub1 <sub2){
      psub = sub1;	
    }else{
      psub =sub2;	
    }
    if(sinter<=psub){
      sub =sinter;	
    }else{
      sub = psub;
    }
    return sub;
};

double Vegetation_Env::getLeafStomaCond(const double & ta, const double &  ppfdabsorb,
		 const double & vpdin, const double& btran, double & m_ppfd, double & m_vpd ){

	double gl; // leaf conductance m/s, per unit LAI
	double m_psi; // soil water matric potential effect
	double m_co2;
	double m_tmin;
	
	double m_tot; // total effect of different factos
	 
	double vpd_open = envpar.vpd_open ; //Pa , start of conductance reduction
	double vpd_close =envpar.vpd_close; //Pa , complete conductance reduction
	double glmax = envpar.glmax; //m/s, maximum stomata conductance
	
	m_ppfd= ppfdabsorb/(ppfdabsorb+envpar.ppfd50);
	
	double vpd = vpdin; //
	if(vpd <vpd_open) {
		m_vpd = 1.0;
	} else if(vpd>vpd_close){
		m_vpd = 0.;
	}else {
		m_vpd =(vpd_close-vpd)/(vpd_close-vpd_open);
	}

	m_psi = btran;
	
	m_co2=1;
	
	double tmin = ta-5;  
	// here ta is average air temperature (degC)  ;
	// 5 is derived from mean air temperature and minimum air temeperature difference from station data of Fairbanks
	if(tmin>0) {
		m_tmin=1;
	}else if(tmin<-8){
		m_tmin=0.;
	}else{
		m_tmin = 1.0 +(0.125*tmin);
	}

	m_tot = m_ppfd * m_vpd * m_co2* m_tmin*m_psi;	
	gl =  m_tot * glmax;
	
	return gl;
};

double Vegetation_Env::getRainInterception(const double & rain, const double & lai){
   // input: rain mm/day
   double rinter;
            
   double raincm = rain/10.; // convert to cm
   double max_int = raincm - ((raincm*0.77-0.05)+0.02 * raincm);

   // may need to add LAI adjustment?

   //
   max_int *= 10. ; // convert back to mm;
   if(rain <= max_int){ // all intercepted
   	 rinter = rain;
   }else{ //partly intercepted
   	 rinter= max_int;
   }              

   return rinter; 
  	
};

double Vegetation_Env::getSnowInterception(const double & snow, const double & lai){
    double sinter;
    double psinter; // potential snow interception
    double ISmax = envpar.iscoef ; // this is parameter for snow interception by canopy
                  // it should be vegetation specific [mm /LAI /day ], e.g., for tussock tundra set to 0
                  
    psinter = ISmax * lai;
              
    if(psinter >= snow){
       	sinter = snow;
    }else{
       	sinter = psinter;
    }

    return sinter;
  	
};

void Vegetation_Env::setCohortLookup(CohortLookup * chtlup){
    chtlu = chtlup;
};

void Vegetation_Env::setCohortData(CohortData* cdp){
	cd = cdp;
};

void Vegetation_Env::setEnvData(EnvData* edatap){
	ed = edatap;	
};

void Vegetation_Env::setFirData(FirData* fdp){
  	fd =fdp;
};
