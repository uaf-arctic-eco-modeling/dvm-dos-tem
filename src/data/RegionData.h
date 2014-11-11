#ifndef REGIONDATA_H_
#define REGIONDATA_H_
#include <string>
#include "../inc/timeconst.h"

class RegionData {
public:
  RegionData();
  ~RegionData();

  int act_co2yr;
  int co2year[MAX_CO2_DRV_YR];
  float co2[MAX_CO2_DRV_YR];

  double initco2;

  void set_act_co2yr_from_file(std::string filename);
  void setup_co2_and_yr_from_file(std::string filename);
};

#endif /*REGIONDATA_H_*/
