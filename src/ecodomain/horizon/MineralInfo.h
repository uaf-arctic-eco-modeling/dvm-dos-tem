/** MineralInfo object. 
 * What more is there to say?
*/
#ifndef MINERAL_INFO_H_
#define MINERAL_INFO_H_

#include <iostream>
#include <string>

#include "../layer/MineralLayer.h"

using namespace std;

class MineralInfo {
public:
  MineralInfo();

  MineralInfo(const std::string& fname, const int y, const int x);
  ~MineralInfo();

  int num;      ///> number of mineral layer. Not sure why we are not using MAX_MIN_LAY??
  double thick; ///> total thickness of mineral soils (m)

  double dz[MAX_MIN_LAY];   ///> thickness of each mineral layer (m)

  float sand[MAX_MIN_LAY];
  float silt[MAX_MIN_LAY];
  float clay[MAX_MIN_LAY];

  void setDefaultThick(const double & thickness);
  void set5Soilprofile(int soiltype[],
                       double dz[],
                       const int & maxnum);

};
#endif /* MINERAL_INFO_H_ */
