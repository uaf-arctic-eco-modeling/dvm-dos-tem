/*! \file
 * provides interpolate function
 */
#ifndef INTERPOLATOR_H_
#define INTERPOLATOR_H_
class Interpolator{
	public:
	Interpolator();
	
	void interpolate(float x[], float y[], const int & nmax, 
					 float xx[], float yy[], const int & nnmax);
	
	
};
#endif /*INTERPOLATOR_H_*/
