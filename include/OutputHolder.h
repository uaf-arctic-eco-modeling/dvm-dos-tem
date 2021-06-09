
#ifndef OUTPUTHOLDER_H
#define OUTPUTHOLDER_H

#include "temconst.h"
#include "layerconst.h"

class OutputHolder{
public:

//  OutputHolder();
//  ~OutputHolder();

  void clear();

  int months_held;
  int years_held;

  std::vector<double> ald_for_output;
////  std::vector<int> ysd_for_output;
//  std::vector<double> snowthick_for_output;
//  std::vector<double> swe_for_output;
//  std::vector<double> trans_for_output;
//  std::vector<double> watertab_for_output;

  std::vector<std::vector<double>> eet_for_output;
  std::vector<std::array<double, NUM_PFT>> eet_test_vector;

  std::vector<double> pet_tot_for_output;
  std::vector<std::array<double, NUM_PFT>> pet_for_output;

  std::vector<std::array<double, MAX_SOI_LAY>> tlayer_for_output;
//  std::vector<std::array<double, MAX_SOI_LAY>> vwclayer_for_output;

  std::vector<std::array<std::array<double, NUM_PFT_PART>, NUM_PFT>> gpp_for_output; 

};


#endif /* OUTPUTHOLDER_H */
