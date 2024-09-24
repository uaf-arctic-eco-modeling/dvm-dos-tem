#ifndef MINERALLAYER_H_
#define MINERALLAYER_H_
#include "SoilLayer.h"
#include "CohortLookup.h"
#include "cohortconst.h"

class MineralLayer: public SoilLayer {
public:
  MineralLayer(const double &pdz, float psand, float psilt, float pclay,
               const CohortLookup *chtlu
               /*int sttype */);

  ~MineralLayer();

  float pctsand;
  float pctsilt;
  float pctclay;

  double getDryThermCond(const double & bulkden);
  double getDryThermCond(const double & tcsolid,
                         const double & bulkden,
                         const double & partden);

private:
  void  updateProperty5Lookup(const CohortLookup *chtlu);

};
#endif /*MINERALLAYER_H_*/
