/*! \file
 */
#ifndef ORGANIC_H_
#define ORGANIC_H_
 
#include "iostream"
using namespace std;

#include "../inc/ErrorCode.h"
#include "../inc/cohortconst.h"
#include "../inc/layerconst.h"

class Organic{
	public:
		Organic();
		~Organic();
	
		int shlwnum;
		double shlwthick;
	
		int deepnum;
		double deepthick;
	
		double shlwdz[MAX_SLW_LAY];
		double deepdz[MAX_DEP_LAY];
	
		bool shlwchanged;
		double lstshlwdz;
	
		void initShlwThicknesses(const double & thickness);
		void initDeepThicknesses(const double & thickness);
	
		void setShlwThicknesses(int type[], double dz[],const int & maxnum);
		void setDeepThicknesses(int type[], double dz[],const int & maxnum);

		bool sameShlwThickRange(const double & thickness);
		bool sameDeepThickRange(const double & thickness);

	private:
	
};
#endif /*ORGANIC_H_*/
