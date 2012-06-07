/*! \file
 * can photosynthesize
 */
#ifndef MOSSLAYER_H_
#define MOSSLAYER_H_
#include "SoilLayer.h"

#include <string>
#include <cmath>
using namespace std;
class MossLayer: public SoilLayer{
	public:
		 MossLayer(const double &pdz, const int & mosstype);
	 
		 int mosstype;  //=1 sphagnum, 2= feathermoss

};
#endif /*MOSSLAYER_H_*/
