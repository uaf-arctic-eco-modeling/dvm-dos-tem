#include <numeric> // for accumulate
#include <vector>

#include "Climate.h"

#include "TEMUtilityFunctions.h"
#include "TEMLogger.h"

extern src::severity_logger< severity_level > glg;

Climate::Climate() {
  BOOST_LOG_SEV(glg, note) << "--> ATMOSPHERE 2 <-- empty ctor";
}

Climate::Climate(const std::string& fname, int y, int x) {
  BOOST_LOG_SEV(glg, note) << "--> ATMOSPHERE 2 <-- BETTER CTOR";
  this->load_from_file(fname, y, x);
  this->buildout_avgX_data(30);
}

//get_single_year(float[] variable, int length) {
//  // bounds check??
//
//  std::vector<float> data;
//  for (int i=0; i < 12; ++i) {
//    data.push_back(this->variable[12*iy + im]);
//  }
//  return data;
//}

std::vector<float> Climate::tair_y(int iy) {
  std::vector<float> data;
  for (int im = 0; im < 12; ++im) {
    data.push_back(this->tair[12*iy + im]);
  }
  return data;
}
std::vector<float> Climate::tair_m(int im) {
  std::vector<float> data;
  return data;
}

//std::vector<float> Climate::tair_d(int iy);

void Climate::buildout_avgX_data(int averaging_window) {
  
  // tair is a list of all consecutive months, I need every 12th one
  // so


// worked
//  for (int im = 0; im < 12; ++im) {
//
//    std::vector<float> vals;
//
//    for (int iy = 0; iy < averaging_window; ++iy) {
//      vals.push_back(this->YM_tair(iy, im));
//    }
//
//    float sum = std::accumulate(vals.begin(), vals.end(), 0);
//    
//    BOOST_LOG_SEV(glg, debug) << im << " SHIT YEAH, SUM: " << sum;
//    BOOST_LOG_SEV(glg, debug) << im << " SHIT YEAH, MEAN: " << sum/vals.size();
//    this->avgX_tair[im] = sum/vals.size();
//
//  }
  
//  float avgX_tair[12];
//  float avgX_prec[12];
//  float avgX_nirr[12];
//  float avgX_vapo[12];
  
}


void Climate::load_from_file(const std::string& fname, int y, int x) {

  BOOST_LOG_SEV(glg, info) << "Loading climate from file: " << fname;
  BOOST_LOG_SEV(glg, info) << "Loading climate for (y, x) point: ("<< x <<","<< y <<"), all timesteps.";

  std::vector<float> temps =
      temutil::get_climate_var_timeseries(fname, "tair", y, x);
  
  std::vector<float> vapos =
      temutil::get_climate_var_timeseries(fname, "vapor_press", y, x);
  
  std::vector<float> precips =
      temutil::get_climate_var_timeseries(fname, "precip", y, x);

  std::vector<float> nirrs =
      temutil::get_climate_var_timeseries(fname, "nirr", y, x);


  BOOST_LOG_SEV(glg, info) << "Assign climate timeseries to actual internal datastructures...";

  // Report on sizes...
  BOOST_LOG_SEV(glg, info) << "  -->sizes (tair, vapor_press, precip, nirr): ("
                           << temps.size() << ", " << vapos.size() << ", "
                           << precips.size() << ", " << nirrs.size() << ")";
  BOOST_LOG_SEV(glg, info) << "  -->sizes of climate::tair, nirr, prec, "
                           << "vapo appears to be: " << MAX_ATM_DRV_YR * 12;

  std::copy(temps.begin(), temps.end(), this->tair);
  std::copy(vapos.begin(), vapos.end(), this->vapo);
  std::copy(precips.begin(), precips.end(), this->prec);
  std::copy(nirrs.begin(), nirrs.end(), this->nirr);
  
}
