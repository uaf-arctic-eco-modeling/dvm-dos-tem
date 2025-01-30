#ifndef _CLIMATE_H_
#define _CLIMATE_H_

#include <string>
#include <vector>

class Climate {
public:

  Climate();
  Climate(const std::string& fname, const std::string& co2fname, int y, int x);

  // Misc. climate variables
  // The following two values determine the span of historic climate
  //  years used to produce a baseline average climate for EQ
  //  TODO: SP repeated climate is not currently affected by these.
  int baseline_start;
  int baseline_end;
  // These values will change during a run when switching from
  //  historic to projected climate data
  int tseries_start_year;
  int tseries_end_year;

  // driving variables
  std::vector<float> co2;
  std::vector<float> tair;
  std::vector<float> prec;
  std::vector<float> nirr;
  std::vector<float> vapo;

  // calculated driving variables
  std::vector<float> girr;
  std::vector<float> cld;
  std::vector<float> par;

  // Supplemental variables, only loaded if module is specified
  std::vector<float> ch4;

  // simplified climate, averaged over some number of years
  std::vector<float> avgX_tair;
  std::vector<float> avgX_prec;
  std::vector<float> avgX_nirr;
  std::vector<float> avgX_vapo;

  // repetitive climate, repeated over a specified number of years
  //std::vector<float> rptX_tair;
  //std::vector<float> rptX_prec;
  //std::vector<float> rptX_nirr;
  //std::vector<float> rptX_vapo;

  // Daily containers

  // this is not really a daily value, but for scope/access
  // reasons it is easier to treat it as such. Every day of the year has the same co2 value...
  float co2_d;

  float ch4_d;

  //  ->> should be interpolated from the monthly containers
  std::vector<float> tair_d;
  std::vector<float> prec_d;
  std::vector<float> nirr_d;
  std::vector<float> vapo_d;
  std::vector<float> rain_d;
  std::vector<float> snow_d;
  std::vector<float> girr_d;
  std::vector<float> cld_d;
  std::vector<float> par_d;

  // More daily containers, but unlike the others, these are not
  // ever stored at the monthly level.
  std::vector<float> rhoa_d;
  std::vector<float> svp_d;
  std::vector<float> vpd_d;
  std::vector<float> dersvp_d;
  std::vector<float> abshd_d;
  
  std::vector<float> monthly2daily(const std::vector<float>& mly_vals);

  void prepare_eq_daily_driving_data(int iy, const std::string& stage);
  void prepare_daily_driving_data(int, const std::string&);

  void monthlycontainers2log();
  void dailycontainers2log();

  void load_proj_climate(const std::string&, int, int);
  void load_proj_co2(const std::string&);

  void load_ch4(const std::string&);

  void prep_avg_climate();

private:

  void load_from_file(const std::string& fname, int y, int x);

  void split_precip();

  std::vector<float> avg_over(const std::vector<float> & var, const int start_yr, const int end_yr);
  std::vector<float> rpt_years(const std::vector<float> &, const int);

  std::vector<float> interpolate_daily(const std::vector<float> & var);

  std::vector<float> eq_range(const std::vector<float>& data);
  std::vector<float> interpolation_range(const std::vector<float>& data, int year);

};

#endif /* _CLIMATE_H_ */


