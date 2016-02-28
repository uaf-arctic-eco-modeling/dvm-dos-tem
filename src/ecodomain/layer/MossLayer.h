/*! \file
 * can photosynthesize
 */
#ifndef MOSSLAYER_H_
#define MOSSLAYER_H_
#include "SoilLayer.h"
#include "../../inc/cohortconst.h"

using namespace std;
class MossLayer: public SoilLayer {
public:
  MossLayer(const double &pdz, const int & mosstype);
  ~MossLayer();

  int mosstype;  // moss types: 1: sphagnum; 2: feathermoss; 3: other (including lichen)

};
#endif /* MOSSLAYER_H_ */

