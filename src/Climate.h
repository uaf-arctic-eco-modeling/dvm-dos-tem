#ifndef _CLIMATE_H_
#define _CLIMATE_H_

#include <string>
#include "inc/timeconst.h"




class Climate {
public:

  Climate();
  Climate(const std::string& fname, int y, int x);

  void load_from_file(const std::string& fname, int y, int x);
  
  std::vector<float> tair_y(int iy);
  std::vector<float> tair_m(int iy);
  std::vector<float> tair_d(int iy);

//  float YM_tair(int iy, int im);
//
//
//  // a years worth of data, all months
//  // [0,1,2,3,4,5,6,7,8,9,10,11]
//  std::vector<float> get_month(int year);
//  
//  // a single month, along the year axis...
//  // [0,1,2,3,4,....n Years]
//  std::vector<float> get_month(int month);
//
//
//  climate.tair_y(iy);
//  climate.tair_m(im);
//  climate.tair_d(id);
//
//  climate.get_month(tair, im);
//  climate.get_year(tair, iy);
  
private:

  // base data - should be loaded from .nc file
  float tair[MAX_ATM_DRV_YR * 12];
  float prec[MAX_ATM_DRV_YR * 12];
  float nirr[MAX_ATM_DRV_YR * 12];
  float vapo[MAX_ATM_DRV_YR * 12];

  // a simplified climate, created from the base data
  // by using buildout_avgX_data(..)
  float avgX_tair[12];
  float avgX_prec[12];
  float avgX_nirr[12];
  float avgX_vapo[12];
  
  // Other values that are calculated from the base data
  float cld [MAX_ATM_DRV_YR * 12];
  float snow[MAX_ATM_DRV_YR * 12];
  float rain[MAX_ATM_DRV_YR * 12];
  float par [MAX_ATM_DRV_YR * 12];
  float ppfd[MAX_ATM_DRV_YR * 12];
  float girr[MAX_ATM_DRV_YR * 12];

  void buildout_avgX_data(int averageOver);
  void buildout_daily_data();
  void buildout_derived_data();

};

#endif /* _CLIMATE_H_ */


