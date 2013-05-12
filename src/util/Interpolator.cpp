/*! \file
 */
 #include "Interpolator.h"

Interpolator::Interpolator(){
	
};

void Interpolator::interpolate(float x[], float y[], const int & nmax, 
					 float xx[], float yy[], const int & nnmax){
	 int m=0;
	 float slope, x1, x2, y1, y2;
	 for(int n=1; n<nmax; n++){
	 	y1=y[n-1];
	 	y2=y[n];
	 	x1 =x[n-1];
	 	x2 = x[n];
	 	slope = (y2-y1)/(x2-x1);
	 	while(m<nnmax  && xx[m]<=x2){
	 	  yy[m] = y1+slope*(xx[m]-x1);
	 	  m++;
	 	}
	 }	
};
