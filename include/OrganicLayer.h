/*! \file
 *
 */
#ifndef ORGANICLAYER_H_
#define ORGANICLAYER_H_
#include "SoilLayer.h"

#include <string>
#include <cmath>
using namespace std;

class OrganicLayer: public SoilLayer {
public:

  OrganicLayer(const double & pdz, const int & type);
  ~OrganicLayer();
  void humify();

};
#endif /*ORGANICLAYER_H_*/
