/*! \file provides crank-nicholson scheme for snow and soil column temperature calculation
 * */
#ifndef CRANKNICHOLSON_H_
#define CRANKNICHOLSON_H_
#include <cmath>
#include <iostream>
using namespace std;
 
class CrankNicholson{
	 public:

	 	 CrankNicholson();
	 	 ~CrankNicholson();

	 	 // Gaussian Elimination Backward method to calculate Arrays E and S
	 	 void geBackward(const int  &startind, const int & endind, double  t[], double dx[], double  cn[],
	 			double cap[],double  s[], double e[], double & dt);
	 	 // using the updated Arrays E and S to update the soil temperature
	 	 void cnForward(const int & startind, const int & endind ,double tii[], double tit[], double s[], double e[]);

	 	 void geForward(const int  &startind, const int & endind, double  t[], double dx[], double  cn[],
	 			double cap[], double  s[], double e[], double & dt);
	 
	 	 // using the updated Arrays E and S to update the soil temperature*/
	 	 void cnBackward(const int & startind, const int & endind ,double tii[], double tit[], double s[], double e[]);

	 	 void tridiagonal(const int ind, const int numsl, double a[], double b[], double c[],double r[],  double u[]);
};

#endif /*CRANKNICHOLSON_H_*/
