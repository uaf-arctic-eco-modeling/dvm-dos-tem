#include <numeric> // for accumulate
#include <vector>
#include <algorithm>

#include <assert.h> // for assert? need C++ library?

#include <boost/filesystem.hpp>

#include "../include/Climate.h"

#include "../include/errorcode.h"
#include "../include/timeconst.h"

#include "../include/TEMUtilityFunctions.h"
#include "../include/TEMLogger.h"

extern src::severity_logger< severity_level > glg;

// Should really put these in temutil and then write some test
// routines that exercise the funcitons over a wide range of values

/** Find "Vapor Pressure Density"??? as a funciton of svp and vp ?? 
*/
float calculate_vpd (const float svp, const float vp) {
  float vpd = svp - vp;

  if (vpd < 0) {
    vpd = 0;
  }

  return vpd; // unit Pa
}

/** Find saturated vapor pressure as a function of temperature.

Guide to Meteorological Instruments and Methods of Observation (CIMO Guide)
  %      (WMO, 2008), for saturation vapor pressure
  %      (1) ew = 6.112 e(17.62 t/(243.12 + t))                [2]
  %      with t in [deg C] and ew in [hPa, mbar]

  %      (2) ei = 6.112 e(22.46 t/(272.62 + t))                [14]
  %      with t in [deg C] and ei in [hPa]
*/
float calculate_saturated_vapor_pressure(const float tair) {

  float svp; // saturated vapor pressure (Pa)

  if( tair > 0 ) {
    svp = 6.112 * exp(17.63 * tair / (243.12 + tair) ) * 100.0;
  } else {
    svp = 6.112 * exp(17.27 * tair / (272.62 + tair) ) * 100.0;
  }

  return svp;
}

/** Cloudiness as a function of girr and nirr */
float calculate_clouds(const float girr, const float nirr) {
  assert (nirr >= 0.0 && "Invalid nirr in Climate::calculate_clouds(..)!");
  assert (girr >= 0.0 && "Invalid girr in Climate::calculate_clouds(..)!");

  float clouds;

  if ( nirr >= (0.76 * girr) ) {
    clouds = 0.0;
  } else {
    clouds = 1.0 - (((nirr/girr) - 0.251)/0.509);
    clouds *= 100.0;
  }

  if ( clouds > 100.0 ) {
    clouds = 100.0;
  }

  return clouds;
}

/** PAR (watts per meter squared) as a function of cloudiness and nirr. */
float calculate_par(const float clds, const float nirr) {

  float par;  //  W/m2

  if ( clds >= 0.0 ) {
    par = nirr * ((0.2 * clds / 100.0) + 0.45);
  } else {
    par = MISSING_D;
  }

  return par;
}

/** The rain/snow split as a function of temperatore and precip.

Willmott's assumption. Returns a pair: (rain, snow).
*/
std::pair<float, float> willmot_split(const float t, const float p) {
  float r, s = 0.0;
  if ( t > 0.0 ) {
    r = p;
    s = 0.0;
  } else  {
    r = 0.0;
    s = p;
  }
  return std::make_pair(r,s);
}

/** GIRR (W/m^2) as a function of latitude and month.
*
*  More information and formulas can be found here:
*  http://www.fao.org/docrep/X0490E/x0490e07.htm
*  (section "Extraterrestrial radiation for daily periods")
* 
*  And a table of expected values here:
*  http://www.fao.org/docrep/X0490E/x0490e0j.htm#annex%202.%20meteorological%20tables
* 
*  NOTE: To convert from MJ/m^2/day to W/m^2:
*        multiply by (1,000,000)/(60*60*24) or ~11.57
*/
float calculate_girr(const float lat, const int im) {
  const float pi = 3.141592654;                // Greek "pi" TODO: fix this to use constant from math library?
  const float sp = 1368.0 * 3600.0 / 41860.0;  // solar constant
  float lambda;
  float sumd;
  float sig;
  float eta;
  float sinbeta;
  float sb;
  float sotd;
  int hour;
  lambda = lat * pi / 180.0;
  float gross = 0.0;

  for ( int day = 0; day < DINM[im]; ++day ) {

    // find julian day
    // http://www.fao.org/docrep/X0490E/x0490e0j.htm#annex%202.%20meteorological%20tables
    float jd = 0.0;
    jd = (275 * (im+1)/9) - 30 + (day+1);
    if( (im+1) < 3 ) {
      jd = jd + 2;
    }
    int julianday = int(jd);

    sumd = 0;
    sig = -23.4856*cos(2 * pi * (julianday + 10.0)/365.25);
    sig *= pi / 180.0;

    for ( hour = 0; hour < 24; hour++ ) {
      eta = (float) ((hour+1) - 12) * pi / 12.0;
      sinbeta = sin(lambda)*sin(sig) + cos(lambda)*cos(sig)*cos(eta);
      sotd = 1 - (0.016729 * cos(0.9856 * (julianday - 4.0)
                                 * pi / 180.0));
      sb = sp * sinbeta / pow((double)sotd,2.0);

      if (sb >= 0.0) {
        sumd += sb;
      }
    }

    gross += sumd;
  }

  gross /= (float)DINM[im];
  gross *= 0.484; // convert from cal/cm2day to W/m^2
  return gross;
}

std::vector<float> calculate_daily_prec(const int midx, const float mta, const float mprec) {
                                  
  // input are monthly precipitation, monthly temperature
  // output are daily precipitation
  // this function is based on the code provided Qianlai on Feb. 19, 2007
  
  float RT, RS, R ;
  RT=1.778;
  RS=0.635;
  R=0.5;
  float TEMP, PREC, DURT, DURS;
  PREC = mprec/10.0/2.54; //comvert mm to cm, then to in.
  DURT=RT/R;
  DURS=RS/R;
  float B=1.0, T=0.0, S=1.0, RB, DURB;

  float RAINDUR[DINM[midx]];
  float RAININTE[DINM[midx]];
  for(int id = 0; id < DINM[midx]; id++) {
    RAININTE[id] =0.;
    RAINDUR[id] = 0.;
  }

  TEMP = mta;
  
  //  Case 1, TEMP<0.
  if (TEMP <= 0.0) {
    if (PREC <= 1.0) {
      B=1.0;
      T=0.0;
      S=1.0;
    } else {
      B=1.0;
      T=1.0;
      S=1.0;
    }
  }
  //   Case 2, PREC<1.0 inch.
  else if (PREC <= 1.0) {
    B=1.0;
    T=0.0;
    S=1.0;
  }
  //   Case 3, 1.0<PREC<2.5 inches.
  else if ((2.5 >= PREC) && (PREC > 1.0)) {
    B=1.0;
    T=1.0;
    S=1.0;
  }
  //   Case 4, 2.5<PREC<4.0 inches.
  else if ((4.0 >= PREC) && (PREC > 2.5)) {
    B=1.0;
    S=4.0;

    if (PREC < 3.7) {
      T=1.0;
    } else {
      T=2.0;
    }
  }
  //   Case 5, 4.0<PREC<5.0 inches.
  else if ((5.0 >= PREC) && (PREC > 4.0)) {
    B=1.0;
    S=4.0;

    if (PREC < 4.43) {
      T=1.0;
    } else {
      T=2.0;
    }
  }
  //   Case 6, 5.0<PREC<7.0 inches.
  else if ((7.0 >= PREC) && (PREC > 5.0)) {
    B=2.0;
    S=4.0;

    if (PREC < 5.65) {
      T=1.0;
    } else {
      T=2.0;
    }
  }
  //   Case 7, 7.0<PREC<9.0 inches.
  else if ((9.0 >= PREC) && (PREC > 7.0)) {
    B=2.0;
    S=6.0;

    if (PREC < 8.21) {
      T=3.0;
    } else {
      T=4.0;
    }
  }
  //   Case 8, 9.0<PREC<11.0 inches.
  else if ((11.0 >= PREC) && (PREC > 9.0)) {
    B=3.0;
    S=6.0;

    if (PREC < 10.0) {
      T=4.0;
    } else {
      T=5.0;
    }
  }
  //   Case 9, PREC>11.0 inches.
  else if (PREC > 11.0) {
    B=4.0;
    S=7.0;

    if (PREC < 13.0) {
      T=4.0;
    } else {
      T=5.0;
    }
  }
  
  RB = ( PREC*2.54 - RS*S - RT*T ) / B;   // Yuan
  DURB = RB / R;    // Yuan

  if (DURB <= 0.01) {
    DURB = 0.01;  // !added //changed from zero to 0.01 by shuhua
  }

  PREC = PREC * 2.54 * 10.0;  // convert back to cm, and then to mm
  float BB, TT;
  int KTT, KDD, KTD, KKTD;
  int NN, DT;
  DT = DINM[midx];
  KTT = (int)(B+T);
  KTD = DT / KTT;
  KDD = DT - KTT * KTD;
  BB = B;
  TT = T;
  NN = 0;
  
  for (int JJ=1; JJ<=KTT; JJ++) {
    if (BB > 0.0) {
      BB = BB - 1.0;

      for (int L=1; L<=KTD; L++) {
        NN = NN+1;
        RAININTE[NN] = 0.0;
        RAINDUR[NN] = 0.0;

        if (L == KTD) {
          RAININTE[NN] = 5.0; // unit with mm /hr
          RAINDUR[NN] = DURB;
        }
      }
    }

    if (TT > 0.0) {
      TT = TT - 1.0;

      if (JJ == 1) {
        KKTD = KTD+KDD;
      } else {
        KKTD = KTD;
      }

      for (int L=1; L <= KKTD; L++) {
        NN = NN+1;
        RAININTE[NN] = 0.0;
        RAINDUR[NN] = 0.0;

        if (L == KKTD) {
          RAININTE[NN] = 5.0; //unit mm/hr
          RAINDUR[NN] = DURT;
        }
      }
    }
  }  // end of for J
  
  // in winter season, DURT was always zero, so put the precipitation
  //   on the day with RAININTE>0;
  int numprec = 0;
  double tothour = 0.;

  for (int id = 0; id < DINM[midx]; id++) {
    if (RAINDUR[id+1] > 0) {
      numprec++;
      tothour += RAINDUR[id+1];
    }
  }
  
  float sumprec = 0.;


  std::vector<float> precip_daily (DINM[midx], 0);
  if(numprec > 0) {
    double rainrate = mprec / tothour;

    for (int id = 0; id < DINM[midx]; id++) {
      precip_daily[id] = RAINDUR[id+1] * rainrate;
      sumprec += precip_daily[id];
    }
  }
  
  return precip_daily;
}



Climate::Climate() {
  BOOST_LOG_SEV(glg, info) << "--> CLIMATE --> empty ctor";
}


Climate::Climate(const std::string& fname, const std::string& co2fname, int y, int x) {
  BOOST_LOG_SEV(glg, info) << "--> CLIMATE --> BETTER CTOR";
  this->load_from_file(fname, y, x);

  // co2 is not spatially explicit
  #pragma omp critical(load_input)
  {
    this->co2 = temutil::get_timeseries(co2fname, "co2");
  }
}

void Climate::load_from_file(const std::string& fname, int y, int x) {

  if(!boost::filesystem::exists(fname)){
    BOOST_LOG_SEV(glg, fatal) << "Input file "<<fname<<" does not exist";
  }

  #pragma omp critical(load_input)
  {
    BOOST_LOG_SEV(glg, info) << "Loading climate from file: " << fname;
    BOOST_LOG_SEV(glg, info) << "Loading climate for (y, x) point: "
                             << "(" << y <<","<< x <<"), all timesteps.";

    BOOST_LOG_SEV(glg, info) << "Read in the base climate data timeseries ...";

    tair = temutil::get_timeseries<float>(fname, "tair", y, x);
    vapo = temutil::get_timeseries<float>(fname, "vapor_press", y, x);
    prec = temutil::get_timeseries<float>(fname, "precip", y, x);
    nirr = temutil::get_timeseries<float>(fname, "nirr", y, x);

    tseries_start_year = temutil::get_timeseries_start_year(fname);
    tseries_end_year = temutil::get_timeseries_end_year(fname);

  }//End critical(load_climate)

  // Report on sizes...
  BOOST_LOG_SEV(glg, info) << "  -->sizes (tair, vapor_press, precip, nirr): ("
                           << tair.size() << ", " << vapo.size() << ", "
                           << prec.size() << ", " << nirr.size() << ")";

  // assert all sizes are the same?
  if ( !(tair.size() == prec.size() &&
         tair.size() == vapo.size() &&
         tair.size() == nirr.size()) ) {
    BOOST_LOG_SEV(glg, warn) << "ERROR - your base climate datasets are not "
                            << "the same size! Very little bounds checking "
                            << "done, not sure what will happen.";

  }

  // make some space for the derived variables
  girr = std::vector<float>(12, 0); // <-- !! wow, no need for year dimension??
  par = std::vector<float>(prec.size(), 0);
  cld = std::vector<float>(prec.size(), 0);

  BOOST_LOG_SEV(glg, debug) << "tair = [" << temutil::vec2csv(tair) << "]";
  BOOST_LOG_SEV(glg, debug) << "prec = [" << temutil::vec2csv(prec) << "]";

  // find girr as a function of month and latitude
  std::pair<float, float> latlon = temutil::get_latlon(fname, y, x);
  for (int im = 0; im < 12; ++im) {
    float g = calculate_girr(latlon.first, im);
    girr[im] = g;
  }
  BOOST_LOG_SEV(glg, debug) << "nirr = [" << temutil::vec2csv(nirr) << "]";
  BOOST_LOG_SEV(glg, debug) << "girr = [" << temutil::vec2csv(girr) << "]";

  // determine "cloudiness" based on ratio of girr and nirr
  for (int i = 0; i < nirr.size(); ++i) {
    int midx = i % 12;
    cld[i] = calculate_clouds(girr[midx], nirr[i]);
  }
  BOOST_LOG_SEV(glg, debug) << "cld = [" << temutil::vec2csv(cld) << "]";

  // find par based on cloudiness and nirr
  for (int i = 0; i < cld.size(); ++i) {
    par[i] = calculate_par(cld[i], nirr[i]);
  }
  BOOST_LOG_SEV(glg, debug) << "par = [" << temutil::vec2csv(par) << "]";

  // Create a simplified historic climate for EQ by averaging input data
  // over a year range specified here.
//Commenting out but leaving temporarily for easier comparison with
// the currently in-progress daily data ingestion branch. 20240429
//  if(fname.find("historic") != std::string::npos){
//    avgX_tair = avg_over(tair, baseline_start, baseline_end);
//    avgX_prec = avg_over(prec, 1901, 1931);
//    avgX_nirr = avg_over(nirr, 1901, 1931);
//    avgX_vapo = avg_over(vapo, 1901, 1931);
//  }

  // Do we need simplified 'avgX_' values for par, and cld??
  // ===> YES: the derived variables should probably be based off the avgX
  //      containers...


  // Finally, need to create the daily dataset(s) by interpolating the monthly
  // --> actually looking like these should not be calculated upon construction.
  //     instead, they should get calculated each year...

}

/** Prepares simplified average climate, intended for EQ stage
*
* Assumes that averaged climate is produced shortly after
*  the tseries values have been loaded from the intended
*  input file.
*/
void Climate::prep_avg_climate(){
  BOOST_LOG_SEV(glg, debug) << "Climate baseline from config: "
                            << baseline_start << ":" << baseline_end;

  if(   baseline_start > tseries_end_year
     || baseline_start < tseries_start_year
     || baseline_end > tseries_end_year
     || baseline_end < tseries_start_year){

    BOOST_LOG_SEV(glg, fatal) << "Baseline year value exceeds range"
             << " of input file.\n" << "Acceptable range: "
             << tseries_start_year << ":" << tseries_end_year << std::endl;
    exit(EXIT_FAILURE);
  }

  if(baseline_end < baseline_start){
    BOOST_LOG_SEV(glg, fatal) << "Baseline end year " << baseline_end
                              << " is less than baseline start year "
                              << baseline_start;
    exit(EXIT_FAILURE);
  }

  avgX_tair = avg_over(tair, baseline_start, baseline_end);
  avgX_prec = avg_over(prec, baseline_start, baseline_end);
  avgX_nirr = avg_over(nirr, baseline_start, baseline_end);
  avgX_vapo = avg_over(vapo, baseline_start, baseline_end);
}


/** This loads data from a projected climate data file, overwriting any old climate data*/
void Climate::load_proj_climate(const std::string& fname, int y, int x){
  BOOST_LOG_SEV(glg, info) << "Climate, loading projected data";

  this->load_from_file(fname, y, x);
}
void Climate::load_proj_co2(const std::string& fname){
  BOOST_LOG_SEV(glg, info) << "CO2, loading projected data!";
  this->co2 = temutil::get_timeseries(fname, "co2");
}

std::vector<float> Climate::avg_over(const std::vector<float> & var, const int start_yr, const int end_yr) {

  int window_length = end_yr - start_yr;

  int start_idx = start_yr - tseries_start_year;
  int end_idx = end_yr - tseries_start_year;

  assert(var.size() % 12 == 0 && "The data vector is the wrong size! var.size() should be an even multiple of 12.");
  assert(var.size() >= 12*window_length && "The data vector is too short to average over the window!");

  // make space for the result - one number for each month
  std::vector<float> result(12, 0);

  for (int im = 0; im < 12; ++im) {
    // make space for a month's data over the averaging window
    std::vector<float> mdata(window_length, 0);

    // gather up the data for this month over the averaging window
    for (int iy = start_idx; iy < end_idx; ++iy) {
      mdata[iy-start_idx] = var[iy*12 + im];
    }

    // average the data for the month
    float sum = std::accumulate(mdata.begin(), mdata.end(), 0.0);

    // put the value in the result vector for this month
    result[im] = sum / window_length; // ?? should window be a float??

    //BOOST_LOG_SEV(glg, debug) << "result = [" << temutil::vec2csv(result) << "]";

  }

  BOOST_LOG_SEV(glg, debug) << "result = [" << temutil::vec2csv(result) << "]";
  return result;
}


// Interpolate from monthly values to daily. Does NOT account for leap years!
std::vector<float> Climate::monthly2daily(const std::vector<float>& mly_vals) {

  // setup a container for the daily data
  std::vector<float> daily_container;

  // set up the "month midpoint to relative days" vector
  static const float arr[] = { -15.5, 15.5, 45.0, 74.5, 105.0,
                                135.5, 166, 196.5, 227.5, 258, 288.5,
                                319, 349.5, 380.5 };
  std::vector<float> rel_days;
  rel_days.assign( arr, arr + sizeof(arr) / sizeof(arr[0]) );

  assert(mly_vals.size() == 14 && "Monthly values must be size 14 (D J F M A M J J A S O N D J)");
  assert(rel_days.size() == 14 && "Relative days vector must be size 14: (D J F M A M J J A S O N D J)");

  for (std::vector<float>::iterator it = rel_days.begin()+1; it != rel_days.end(); ++it) {
    int idx = it - rel_days.begin();

    // find our range to work over
    float x0 = *(it-1);
    float x1 = *it;

    std::vector<float> psd = temutil::resample(
        std::make_pair( x0, mly_vals.at(idx-1) ),   // first point on line
        std::make_pair( x1, mly_vals.at(idx) ),                // second point on line
        int(floor(x0)),     // begining of interval to interpolate
        int(floor(x1)),     // end of iterval to interpolate
        1                   // step size
    );

    // Add this month's interpolated values to the back of the
    // temporary storage...
    daily_container.insert(daily_container.end(), psd.begin(), psd.end());
  }

  // TODO: Probably need to fix this? mostly works, but returns a container
  // that has 366 elements, even on non-leap years. Also when plotting, there
  // appears to be a slight discontinutiy in the interpolation from month to month
  std::vector<float> cal_yr_daily(daily_container.begin()+16, daily_container.end()-14);

  return cal_yr_daily;
}

// rough draft method to get "prev" Dec, this year, and "next" Jan that are
// needed for monthly2daily interpolation...
std::vector<float> Climate::eq_range(const std::vector<float>& data) {
  std::vector<float> foo;

  // recycle Dec as the "previous" Dec
  foo.push_back(data.at(11));

  // get Jan - Dec values
  foo.insert(foo.end(), data.begin(), data.begin()+12);

  // use this Jan as "next" Jan
  foo.push_back(data.at(0));

  return foo;
}

/** Method to build a vector of 14 monthly data points for interpolation.
* In order to interpolate out to the ends of the year, you need the 12 months
* of data, plus the preceeding Dec and following Jan.
*/
std::vector<float> Climate::interpolation_range(const std::vector<float>& data, int year){
  //BOOST_LOG_SEV(glg, fatal) << "interpolation_range, year: "<<year;

  std::vector<float> foo;

  int curr_jan = year*12;

  // Copy in previous Dec, unless in year 0
  if(year==0){
    foo.push_back(data.at(11));
  }
  else{
    foo.push_back(data.at(curr_jan-1));
  }

  // Get Jan - Dec values
  foo.insert(foo.end(), &data[curr_jan], &data[curr_jan+12]);

  // Copy in next Jan, unless it is the last year's worth of data
  if(year == data.size()/12-1){
    foo.push_back(data.at(curr_jan));
  }
  else{
    foo.push_back(data.at(curr_jan+13));
  }

  return foo;
}


/** Prepares a single year of daily driving data. 
* 
* iy is the run's index year, not the calendar year!
* stage is a 2 letter code for the run stage, one of: pr, eq, sp, tr, sc.
*/
void Climate::prepare_daily_driving_data(int iy, const std::string& stage) {

  if( (stage.find("pre") != std::string::npos)
      || (stage.find("eq") != std::string::npos) ){

    // Constant co2! Always use the first year in the input data, and use it
    // for all days!
    co2_d = co2.at(0);

    // Create daily data by interpolating
    tair_d = monthly2daily(eq_range(avgX_tair));
    vapo_d = monthly2daily(eq_range(avgX_vapo));
    nirr_d = monthly2daily(eq_range(avgX_nirr));

    // Not totally sure if this is right to interpolate (girr and par) 
    par_d = monthly2daily(eq_range(par));

  } else {

    // Spin-up, Transient, Scenario
    // Uses the same value of CO2 every day of the year
    co2_d = co2.at(iy);

    // Create daily data by interpolating
    // straight up interpolated....
    tair_d = monthly2daily(interpolation_range(tair, iy));
    vapo_d = monthly2daily(interpolation_range(vapo, iy));
    nirr_d = monthly2daily(interpolation_range(nirr, iy));

    // Not totally sure if this is right to interpolate (girr and par) 
    par_d = monthly2daily(interpolation_range(par, iy));
  }

  //BOOST_LOG_SEV(glg, debug) << stage << " tair_d = [" << temutil::vec2csv(tair_d) << "]";

  // Not totally sure if this is right to interpolate (girr and par)
  // GIRR is passed to eq_range for all stages as it has only twelve values.
  girr_d = monthly2daily(eq_range(girr));

  // The interpolation is slightly broken, so it 'overshoots' when the
  // slope is negative, and can result in negative values.
  BOOST_LOG_SEV(glg, info) << "Forcing negative values to zero in girr and nirr daily containers...";
  std::for_each(nirr_d.begin(), nirr_d.end(), temutil::force_negative2zero);
  std::for_each(girr_d.begin(), girr_d.end(), temutil::force_negative2zero);

  // much more complicated than straight interpolation...
  prec_d.clear();
  for (int i=0; i < 12; ++i) {
    std::vector<float> v;
    if( (stage.find("pre") != std::string::npos)
        || (stage.find("eq") != std::string::npos) ){
      v = calculate_daily_prec(i, avgX_tair.at(i), avgX_prec.at(i));
    }
    else{// Spin-Up, Transient, Scenario
      int month_timestep = iy*12 + i;
      v = calculate_daily_prec(i, tair.at(month_timestep), prec.at(month_timestep));
    }

    prec_d.insert( prec_d.end(), v.begin(), v.end() );
  }

  // derive rain and snow from precip...
  // Look into boost::zip_iterator
  rain_d.clear();
  snow_d.clear();
  for (int i = 0; i < prec_d.size(); ++i) {
    std::pair<float, float> rs = willmot_split(tair_d[i], prec_d[i]);
    rain_d.push_back(rs.first);
    snow_d.push_back(rs.second);
  }

  svp_d.resize(tair_d.size());
  std::transform( tair_d.begin(), tair_d.end(), svp_d.begin(), calculate_saturated_vapor_pressure );

  vpd_d.resize(tair_d.size());
  std::transform( svp_d.begin(), svp_d.end(), vapo_d.begin(), vpd_d.begin(), calculate_vpd );

  cld_d.resize(tair_d.size());
  std::transform( girr_d.begin(), girr_d.end(), nirr_d.begin(), cld_d.begin(), calculate_clouds );

  // THESE MAY NEVER BE USED??
  // rhoa_d;
  // dersvp_d;
  // abshd_d;

  // Dump data to log stream for debugging analysis 
  //this->dailycontainers2log();
}

/** Print the contents of the monthly containers to the log stream.
* Format is intendend to be copy/pastable into python.
*/
void Climate::monthlycontainers2log() {
  BOOST_LOG_SEV(glg, debug) << "co2 = [" << temutil::vec2csv(co2) << "]";
  BOOST_LOG_SEV(glg, debug) << "tair = [" << temutil::vec2csv(tair) << "]";
  BOOST_LOG_SEV(glg, debug) << "prec = [" << temutil::vec2csv(prec) << "]";
  BOOST_LOG_SEV(glg, debug) << "nirr = [" << temutil::vec2csv(nirr) << "]";
  BOOST_LOG_SEV(glg, debug) << "vapo = [" << temutil::vec2csv(vapo) << "]";
  BOOST_LOG_SEV(glg, debug) << "girr = [" << temutil::vec2csv(girr) << "]";
  BOOST_LOG_SEV(glg, debug) << "cld = [" << temutil::vec2csv(cld) << "]";
  BOOST_LOG_SEV(glg, debug) << "par = [" << temutil::vec2csv(par) << "]";
}

/** Print the contents of the daily containers to the log stream. 
* Format is intendend to be copy/pastable into python.
*/
void Climate::dailycontainers2log() {

    BOOST_LOG_SEV(glg, debug) << "tair_d = [" << temutil::vec2csv(tair_d) << "]";
    BOOST_LOG_SEV(glg, debug) << "nirr_d = [" << temutil::vec2csv(nirr_d) << "]";
    BOOST_LOG_SEV(glg, debug) << "vapo_d = [" << temutil::vec2csv(vapo_d) << "]";
    BOOST_LOG_SEV(glg, debug) << "prec_d = [" << temutil::vec2csv(prec_d) << "]";
    BOOST_LOG_SEV(glg, debug) << "rain_d = [" << temutil::vec2csv(rain_d) << "]";
    BOOST_LOG_SEV(glg, debug) << "snow_d = [" << temutil::vec2csv(snow_d) << "]";
    BOOST_LOG_SEV(glg, debug) << "svp_d = [" << temutil::vec2csv(svp_d) << "]";
    BOOST_LOG_SEV(glg, debug) << "vpd_d = [" << temutil::vec2csv(vpd_d) << "]";
    BOOST_LOG_SEV(glg, debug) << "girr_d = [" << temutil::vec2csv(girr_d) << "]";
    BOOST_LOG_SEV(glg, debug) << "cld_d = [" << temutil::vec2csv(cld_d) << "]";
    BOOST_LOG_SEV(glg, debug) << "par_d = [" << temutil::vec2csv(par_d) << "]";

    BOOST_LOG_SEV(glg, debug) << "tair_d.size() = " << tair_d.size();
    BOOST_LOG_SEV(glg, debug) << "nirr_d.size() = " << nirr_d.size();
    BOOST_LOG_SEV(glg, debug) << "vapo_d.size() = " << vapo_d.size();
    BOOST_LOG_SEV(glg, debug) << "prec_d.size() = " << prec_d.size();
    BOOST_LOG_SEV(glg, debug) << "rain_d.size() = " << rain_d.size();
    BOOST_LOG_SEV(glg, debug) << "snow_d.size() = " << snow_d.size();
    BOOST_LOG_SEV(glg, debug) << "vpd_d.size() = " << vpd_d.size();
    BOOST_LOG_SEV(glg, debug) << "svp_d.size() = " << svp_d.size();
    BOOST_LOG_SEV(glg, debug) << "girr_d.size() = " << girr_d.size();
    BOOST_LOG_SEV(glg, debug) << "cld_d.size() = " << cld_d.size();
    BOOST_LOG_SEV(glg, debug) << "par_d.size() = " << par_d.size();

}
