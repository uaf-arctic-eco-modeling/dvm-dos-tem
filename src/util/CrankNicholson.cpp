/*! \file
 */
 
#include "CrankNicholson.h"

CrankNicholson::CrankNicholson(){

}

CrankNicholson::~CrankNicholson(){
	//
}

void CrankNicholson::geBackward(const int  &startind, const int & endind, double  t[], double dx[], double  cn[], 
	 			double cap[], double  s[], double e[], double & dt) {

	double condth;
	double conuth;
	double denm;
	double r;
	double rc;
	double rhs;

	//loop from last layer to first layer
	int iu;
	int id;
	double sil;
	double eil;

	for (int il = endind-1 ;il>=startind+1; il--){
		iu =il-1;
		id =il+1;
		conuth = cn[iu];
		condth = cn[il] ;
		rc = (cap[il] + cap[iu]) / dt;
		r = conuth + rc + condth;
		denm = r - condth * s[id];
		rhs = (rc - conuth - condth) * t[il] + conuth* t[iu] + condth * t[id];

		sil = conuth / denm;
		eil = (rhs + condth * e[id]) / denm;

		s[il] = sil;
		e[il] = eil;
	 
	}

}

void CrankNicholson::geForward(const int  &startind, const int & endind, double  t[], double dx[], double  cn[], 
	 			double cap[], double  s[], double e[], double & dt) {

	double condth;
	double conuth;
	double denm;

	double r;
	double rc;
	double rhs;

	int im1;
	int ip1;
	for (int il =startind+1 ;il<=endind-1;il++){
		im1 =il -1;
		ip1 =il +1;
		conuth = cn[im1];
		condth = cn[il] ;
		rc = (cap[il] + cap[im1]) / dt;
		r = conuth + rc + condth;
		denm = r - conuth * s[im1];
		rhs = (rc - conuth - condth) * t[il] + conuth
          * t[im1] + condth * t[ip1];

		s[il] = condth / denm;
		e[il] = (rhs + conuth * e[im1]) / denm;
	
	}

}

void CrankNicholson::cnForward(const int & startind, const int & endind ,double tii[], double tit[],
		double s[], double e[]) {

	tit[startind]= tii[startind];
	for ( int il =startind+1; il <= endind-1; il++ ) {
  	
		tit[il] = s[il] * tit[il-1] + e[il];
  
	}

	tit[endind] = tii[endind];
  
}

void CrankNicholson::cnBackward(const int & startind, const int & endind ,double tii[], double tit[],
		double s[], double e[]) {
	
	tit[endind]= tii[endind];
	for ( int il =endind-1; il >= startind+1; il--) {
		tit[il] = s[il] * tit[il+1] + e[il];
  
	}

	tit[endind]= tii[endind];
  
}

void CrankNicholson::tridiagonal(const int ind, const int numsl, double a[], double b[], double c[], double r[], double u[]){
	/* input: a, b, c
	 * input: ind, numsl: first layer index, and total number of layers
	 * output: u
	 */

	double gam[numsl];
	double tempg;
	double bet = b[ind];
	for(int il=ind; il<ind+numsl; il++){
		if(il == ind){
			u[il] = r[il]/bet;

		}else{
	   
			tempg = c[il-1] /bet;
			gam[il-ind]= tempg;
			bet = b[il] - a[il] *gam[il-ind];
			u[il] = (r[il] - a[il]*u[il-1])/bet;
		}
	}
	
	for(int il=ind+numsl-1; il>ind; il--){
		// the first layer (il==ind) is done above: basically to say liq. water not move upward from the first layer

		double uil  = u[il];
		double uild = u[il+1];
		if (il==ind+numsl-1) uild = 0.;
		double g = gam[il+1-ind];
		if (il==ind+numsl-1) g = gam[il-ind];

		//u[il] = u[il] - gam[il+1-ind]*u[il+1];
		u[il] = uil - g*uild;

	}
	
}

