/*!
 * Carefully checked and corrected by F.-M. Yuan
 * On Oct. 10, 2011
 */
 
#include "CrankNicholson.h"

CrankNicholson::CrankNicholson(){
	
};
  
CrankNicholson::~CrankNicholson(){
	
};

void CrankNicholson::geBackward(const int  &startind, const int & endind, double  t[], 
		        double  cn[], double cap[], double  s[], double e[], double & dt,
		        const double & endlayergflux) {

	double coni;
	double denm;
	double r;
	double rc;
	double rhs;

	//loop from last layer ('endind') to first layer ('startind'), NOTE: layer index starts from 1
	int iu;
	int id;
	
	double gflux = endlayergflux;   // heat flux at the bottom of ending layer (+ upward, - downward) as input
	coni = cn[endind-1];
	rc   = cap[endind-1]*0.5/dt;
	denm = rc+coni;
	s[endind] = coni/denm;
	e[endind]= (rc*t[endind]+gflux)/denm;

	for (int i=endind-1; i>startind+1; i--){
		iu    = i - 1;
		id    = i + 1;

		rc = (cap[i] + cap[iu]) / dt;
		r  = cn[iu] + rc + cn[id];
		denm = r - cn[id] * s[id];
		rhs = (rc - cn[iu] - cn[id]) * t[i]
		      + cn[iu] * t[iu] + cn[id] * t[id];

		s[i] = cn[iu] / denm;
		e[i] = (rhs + cn[id] * e[id]) / denm;
	 
	}

	rc = cap[startind+1] *0.5/ dt;
	rhs = rc * t[startind+1] ; // +sflux + ht[dnode];
	r = cn[startind] + rc + cn[startind+1];
	denm = r -cn[startind] *s[startind];

	s[startind+1] = cn[startind+1]/denm;
	e[startind+1] = (rhs + cn[startind] * e[startind])/ denm;

};

void CrankNicholson::cnForward(const int & startind, const int & endind ,
		double tii[], double tit[], double s[], double e[]) {

	tit[startind]= tii[startind];
	for ( int il = startind+1; il <= endind; il++ ) {
  	
		tit[il] = s[il] * tit[il-1] + e[il];
  
	}

};

void CrankNicholson::tridiagonal(const int ind, const int numsl, 
		double a[], double b[], double c[], double r[], double u[]){
	/* input: a, b, c
	 * input: ind, numsl
	 * output: u
	 */
	
	double gam[numsl-ind];
	double tempg, tg;
	double bet = b[ind];
	for(int il =ind; il<numsl; il++){
		if(il == ind){
			u[il] = r[il]/bet;
		}else{
			tempg = c[il-1] /bet;
			gam[il]= tempg;
			bet = b[il] - a[il] *gam[il];
			u[il] = (r[il] - a[il]*u[il-1])/bet;	
		}	
	}
	
	for(int il=numsl-2; il>=ind;il--){
	   tg = gam[il+1];
	   u[il] = u[il] - gam[il+1] *u[il+1];	
	}
	
};

