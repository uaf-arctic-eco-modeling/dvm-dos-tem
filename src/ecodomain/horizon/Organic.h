/*! \file
 */
#ifndef ORGANIC_H_
#define ORGANIC_H_
 
#include "iostream"
using namespace std;

#include "../layer/OrganicLayer.h"

class Organic{
	public:
		Organic();
		~Organic();
	
		int shlwnum;
		double shlwthick;
		double shlwc;   // used as a tracker to determine if a shallow Organic horizon exists.
	
		int deepnum;
		double deepthick;
		double deepc;   // used as a tracker to determine if a deep Organic horizon exists.
	
		double shlwdz[MAX_SLW_LAY];
		double deepdz[MAX_DEP_LAY];
	
		bool shlwchanged;
		double lstshlwdz;
	
		void ShlwThickScheme(const double & totthickness);
		void DeepThickScheme(const double & totthickness);
	
		void assignShlwThicknesses(int type[], double dz[],const int & maxnum);
		void assignDeepThicknesses(int type[], double dz[],const int & maxnum);

	private:
	
};
#endif /*ORGANIC_H_*/
