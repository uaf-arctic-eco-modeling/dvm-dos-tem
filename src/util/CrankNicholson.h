/*! \file provides crank-nicholson scheme for snow and soil column temperature calculation
 * */
#ifndef CRANKNICHOLSON_H_
#define CRANKNICHOLSON_H_
#include <cmath>
#include <iostream>
using namespace std;
 
class CrankNicholson{
	 public :
	    
		 CrankNicholson();
		 ~CrankNicholson();
	/*! Gaussian Elimination Backward method
	 * to calculate Arrays E and S
	 * \arg \c t temperature array
	 * \arg \c dx thickness array
	 * \arg \c cn array of thermal conductivity/ thickness
	 * \arg \c cap array of volumetric capacity * thickness
	 * \arg \c s  array of s
	 * \arg \c e  array of e
	 */
	void geBackward(const int  &startind, const int & endind, double t[], double cn[],
	 			double cap[], double s[], double e[], double & dt, const double & endlayergflux);
	void cnForward(const int & startind, const int & endind ,double tii[], double tit[], double s[], double e[]);

	void tridiagonal(const int ind, const int numsl, double a[], double b[], double c[],double r[],  double u[]);
};
#endif /*CRANKNICHOLSON_H_*/
