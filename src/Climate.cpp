#include <numeric> // for accumulate
#include <vector>
#include <algorithm>

#include <assert.h> // for assert? need C++ library?

#include "Climate.h"

#include "inc/errorcode.h"
#include "inc/timeconst.h"

#include "TEMUtilityFunctions.h"
#include "TEMLogger.h"

extern src::severity_logger< severity_level > glg;

// Should really put these in temutil and then write some test
// routines that exercise the funcitons over a wide range of values

/** Cloudiness as a function of girr and nirr */
float calculate_clouds(const float girr, const float nirr) {
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

/** GIRR as a function of latitude and month. */
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
  gross *= 0.484; // convert from cal/cm2day to W/m2
  return gross;
}


Climate::Climate() {
  BOOST_LOG_SEV(glg, note) << "--> CLIMATE --> empty ctor";
}


Climate::Climate(const std::string& fname, int y, int x) {
  BOOST_LOG_SEV(glg, note) << "--> CLIMATE --> BETTER CTOR";
  this->load_from_file(fname, y, x);
}


void Climate::load_from_file(const std::string& fname, int y, int x) {

  BOOST_LOG_SEV(glg, info) << "Loading climate from file: " << fname;
  BOOST_LOG_SEV(glg, info) << "Loading climate for (y, x) point: "
                           << "(" << y <<","<< x <<"), all timesteps.";


  BOOST_LOG_SEV(glg, info) << "Read in the base climate data timeseries ...";

  tair = temutil::get_climate_var_timeseries(fname, "tair", y, x);
  vapo = temutil::get_climate_var_timeseries(fname, "vapor_press", y, x);
  prec = temutil::get_climate_var_timeseries(fname, "precip", y, x);
  nirr = temutil::get_climate_var_timeseries(fname, "nirr", y, x);

  // Report on sizes...
  BOOST_LOG_SEV(glg, info) << "  -->sizes (tair, vapor_press, precip, nirr): ("
                           << tair.size() << ", " << vapo.size() << ", "
                           << prec.size() << ", " << nirr.size() << ")";

  // assert all sizes are the same?
  if ( !(tair.size() == prec.size() &&
         tair.size() == vapo.size() &&
         tair.size() == nirr.size()) ) {
    BOOST_LOG_SEV(glg, err) << "ERROR - your base climate datasets are not "
                            << "the same size! Very little bounds checking "
                            << "done, not sure what will happen.";

  }

  // make some space for the derived variables
  rain = std::vector<float>(prec.size(), 0);
  snow = std::vector<float>(prec.size(), 0);
  girr = std::vector<float>(12, 0); // <-- !! wow, no need for year dimesion??
  par = std::vector<float>(prec.size(), 0);
  cld = std::vector<float>(prec.size(), 0);

  // fill out rain an snow variables based on temp and precip values
  // Look into boost::zip_iterator
  for (int i = 0; i < tair.size(); ++i) {
    std::pair<float, float> rs = willmot_split(tair[i], prec[i]);
    rain[i] = rs.first;
    snow[i] = rs.second;
  }
  BOOST_LOG_SEV(glg, debug) << "tair = [" << temutil::vec2csv(tair) << "]";
  BOOST_LOG_SEV(glg, debug) << "prec = [" << temutil::vec2csv(prec) << "]";
  BOOST_LOG_SEV(glg, debug) << "rain = [" << temutil::vec2csv(rain) << "]";
  BOOST_LOG_SEV(glg, debug) << "snow = [" << temutil::vec2csv(snow) << "]";

  // find girr as a function of month and latitude
  std::pair<float, float> latlon = temutil::get_latlon("scripts/new-climate-dataset.nc", y, x);
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

  // create the simplified climate by averaging the first X years of data
  avgX_tair = avg_over(tair, 10);
  avgX_prec = avg_over(prec, 10);
  avgX_nirr = avg_over(nirr, 10);
  avgX_vapo = avg_over(vapo, 10);

  // Do we need simplifie 'avgX_' values for par, and cld??

  // Finally, need to create the daily dataset(s) by interpolating the monthly
  // --> actually looking like these should not be calculated upon construciton.
  //     instead, they shoudl get calculated each year...

}

std::vector<float> Climate::avg_over(const std::vector<float> & var, const int window) {

  assert(var.size() % 12 == 0 && "The data vector is the wrong size! var.size() should be an even multiple of 12.");
  assert(var.size() >= 12*window && "The data vector is too short to average over the window!");

  // make space for the result - one number for each month
  std::vector<float> result(12, 0);

  for (int im = 0; im < 12; ++im) {
    // make space for a month's data over the averaging window
    std::vector<float> mdata(window, 0);

    // gather up the data for this month over the averaging window
    for (int iy = 0; iy < window; ++iy) {
      mdata[iy] = var[iy*12 + im];
    }

    // average the data for the month
    float sum = std::accumulate(mdata.begin(), mdata.end(), 0.0);

    // put the value in the result vector for this month
    result[im] = sum / window; // ?? should window be a float??

    //BOOST_LOG_SEV(glg, debug) << "result = [" << temutil::vec2csv(result) << "]";

  }

  BOOST_LOG_SEV(glg, debug) << "result = [" << temutil::vec2csv(result) << "]";

  return result;

}



