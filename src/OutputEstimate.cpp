//
//  OutputEstimate.cpp
//  
//
//  Created by Tobey Carman on 6/22/17.
//
//

#include <map>
#include <boost/algorithm/string.hpp>

#include "../include/OutputEstimate.h"
#include "../include/TEMUtilityFunctions.h"

#include "../include/TEMLogger.h"

extern src::severity_logger< severity_level > glg;

OutputEstimate::OutputEstimate(const ModelData& md, bool calmode) {

  stage_output_estimates = { 
      // Table of coefficients for bytes per year of run-time for
      // each stage and different types of json output (archive, daily, etc).
      {StageOutputEstimate("pr", md.pr_yrs, 22000,  41000,  200000,  20000)},
      {StageOutputEstimate("eq", md.eq_yrs, 56000,  41000,  240000,  24000)},
      {StageOutputEstimate("sp", md.sp_yrs, 15000,  36000,  199000,  16000)},
      {StageOutputEstimate("tr", md.tr_yrs, 15000,  36000,  199000,  16000)},
      {StageOutputEstimate("sc", md.sc_yrs, 15000,  36000,  199000,  16000)},
  };

  // Open the run mask (spatial mask) and count all the non-zero cells.
  std::vector< std::vector<int> > run_mask = temutil::read_run_mask(md.runmask_file);

  this->active_cells = 0;

  // Use a few type definitions to save some typing.
  typedef std::vector<int> vec;
  typedef std::vector<vec> vec2D;

  vec2D::const_iterator row;
  vec::const_iterator col;
  for (row = run_mask.begin(); row != run_mask.end() ; ++row) {
    for (col = row->begin(); col != row->end(); ++col) {
      bool mask_value = *col;
      if (mask_value) {this->active_cells++;}
    }
  }

  BOOST_LOG_SEV(glg, debug) << "Number of active cells in run-mask: " << this->active_cells;

  std::vector<StageOutputEstimate>::iterator itr;
  for (itr = stage_output_estimates.begin(); itr != stage_output_estimates.end(); itr++){

    BOOST_LOG_SEV(glg, debug) << "Estimating output for stage: " << itr->name;
    // handle all the calibration/json stuff
    if (calmode) {
      // cal mode means at least yearly and daily
      BOOST_LOG_SEV(glg, debug) << "  Estimating JSON CALIBRATION output";
      itr->json_out.yearly = itr->runyears * itr->json_out.jcoef_yearly;
      itr->json_out.daily = itr->runyears * itr->json_out.jcoef_daily;

      // setting in config file
      if (md.output_monthly) {
        itr->json_out.monthly = itr->runyears * itr->json_out.jcoef_monthly;
      } else {
        itr->json_out.monthly = 0;
      }
      // could be an overestimate if user does not have monthly enabled too?
      if (md.tar_caljson) {
        itr->json_out.archive = itr->runyears * itr->json_out.jcoef_archive;
      } else {
        itr->json_out.archive = 0;
      }
    }

    // Handle the NetCDF stuff...
    double D_est = 0; double M_est = 0; double Y_est = 0;

    // yearly
    BOOST_LOG_SEV(glg, debug) << "  Estimating YEARLY NC output for stage: " << itr->name;
    std::map<std::string, OutputSpec>::const_iterator map_itr;
    for(map_itr = md.yearly_netcdf_outputs.begin(); map_itr != md.yearly_netcdf_outputs.end(); ++map_itr ){

      double output_estimate = 8;
      OutputSpec os = map_itr->second;

      (os.pft) ? (output_estimate *= NUM_PFT) : output_estimate *= 1;
      (os.compartment) ? (output_estimate *= NUM_PFT_PART) : output_estimate *= 1;
      (os.layer) ? (output_estimate *= MAX_SOI_LAY) : output_estimate *= 1;
      (os.yearly) ? (output_estimate *= (1 * itr->runyears)) : output_estimate *= 1;

      Y_est += output_estimate;
    }
    map_itr = md.yearly_netcdf_outputs.end();

    // monthly
    BOOST_LOG_SEV(glg, debug) << "  Estimating MONTHLY NC output for stage: " << itr->name;
    for(map_itr = md.monthly_netcdf_outputs.begin(); map_itr != md.monthly_netcdf_outputs.end(); ++map_itr ){

      double output_estimate = 8;
      OutputSpec os = map_itr->second;

      (os.pft) ? (output_estimate *= NUM_PFT) : output_estimate *= 1;
      (os.compartment) ? (output_estimate *= NUM_PFT_PART) : output_estimate *= 1;
      (os.layer) ? (output_estimate *= MAX_SOI_LAY) : output_estimate *= 1;
      (os.monthly) ? (output_estimate *= (12 * itr->runyears)) : output_estimate *= 1;

      M_est += output_estimate;
    }
    map_itr = md.monthly_netcdf_outputs.end();

    // daily
    BOOST_LOG_SEV(glg, debug) << "  Estimating DAILY NC output for stage: " << itr->name;
    for(map_itr = md.daily_netcdf_outputs.begin(); map_itr != md.daily_netcdf_outputs.end(); ++map_itr ){

      double output_estimate = 8;
      OutputSpec os = map_itr->second;

      (os.pft) ? (output_estimate *= NUM_PFT) : output_estimate *= 1;
      (os.compartment) ? (output_estimate *= NUM_PFT_PART) : output_estimate *= 1;
      (os.layer) ? (output_estimate *= MAX_SOI_LAY) : output_estimate *= 1;
      (os.daily) ? (output_estimate *= (365 * itr->runyears)) : output_estimate *= 1;

      D_est += output_estimate;
    }
    map_itr = md.daily_netcdf_outputs.end();

    itr->nc_out.yearly = Y_est;
    itr->nc_out.monthly = M_est;
    itr->nc_out.daily = D_est;

  }

}

std::string OutputEstimate::estimate_as_table(){

  std::stringstream ss;
  std::vector<StageOutputEstimate>::iterator itr;

  ss << "-- calibration json output data volume estimates: " << hsize(json_total()) << std::endl;
  ss << std::setw(10) << " "
     << std::setw(10) << "run years"
     << std::setw(10) << "archive"
     << std::setw(10) << "daily"
     << std::setw(10) << "monthly"
     << std::setw(10) << "yearly"
     << std::endl;
  for (itr = stage_output_estimates.begin(); itr != stage_output_estimates.end(); itr++) {
    ss << std::setw(10) << (*itr).name
       << std::setw(10) << (*itr).runyears
       << std::setw(10) << hsize((*itr).json_out.archive)
       << std::setw(10) << hsize((*itr).json_out.daily)
       << std::setw(10) << hsize((*itr).json_out.monthly)
       << std::setw(10) << hsize((*itr).json_out.yearly)
       << std::endl;
  }
  itr = stage_output_estimates.end();
  ss << std::endl;

  ss << "-- netcdf output data volume estimate: " << hsize(netcdf_total()) << std::endl;
  ss << std::setw(10) << " "
     << std::setw(10) << "run years"
     << std::setw(10) << "daily"
     << std::setw(10) << "monthly"
     << std::setw(10) << "yearly"
     << std::endl;

  for (itr = stage_output_estimates.begin(); itr != stage_output_estimates.end(); itr++) {
    ss << std::setw(10) << (*itr).name;
    ss << std::setw(10) << (*itr).runyears;
    ss << std::setw(10) << hsize((*itr).nc_out.daily);
    ss << std::setw(10) << hsize((*itr).nc_out.monthly);
    ss << std::setw(10) << hsize((*itr).nc_out.yearly);
    ss << std::endl;
  }
  itr = stage_output_estimates.end();
  ss << std::endl;

  ss << "Cell Total: " << hsize(this->cell_total());
  ss << std::endl;
  ss << "All cells: " << hsize(this->all_cells_total());

  return ss.str();

}

double OutputEstimate::netcdf_total() {
  double t = 0;
  std::vector<StageOutputEstimate>::iterator itr;
  for (itr = stage_output_estimates.begin(); itr != stage_output_estimates.end(); itr++) {
    t += (*itr).nc_out.daily;
    t += (*itr).nc_out.monthly;
    t += (*itr).nc_out.yearly;
  }
  return t;
}

double OutputEstimate::json_total() {
  // This will probably over-estimate, as the yearly/monthly/daily outputs
  // are deleted for each stage. Maybe should find the stage with the max
  // runyears and use that for the yearly/monthly/daily estimates.
  double t = 0;
  std::vector<StageOutputEstimate>::iterator itr;
  for (itr = stage_output_estimates.begin(); itr != stage_output_estimates.end(); itr++) {
    t += (*itr).json_out.archive;
    t += (*itr).json_out.daily;
    t += (*itr).json_out.monthly;
    t += (*itr).json_out.yearly;
  }
  return t;
}

double OutputEstimate::cell_total() {
  double t = 0;
    t += json_total();
    t += netcdf_total();
  return t;
}

double OutputEstimate::all_cells_total() {
  return active_cells * (json_total() + netcdf_total());
}

/** Returns a 'human readable' size string with SI suffix */
std::string OutputEstimate::hsize(double size) {
  int i = 0;
  const std::string units[] = {"B","kB","MB","GB","TB","PB","EB","ZB","YB"};
  while (size > 1024) {
    size /= 1024;
    i++;
  }
  std::stringstream ss;
  ss.precision(0);
  (size < 0.5) ? size = 0 : size=size;
  ss << fixed << size << " " << units[i];
  std::string size_string = ss.str();
  return size_string;
}


/** Given a string like "1.5 MB" should return a double in bytes. 
*
* Function is reasonably tolerant to strange input string formatting as 
* all leading and trailing whitespace should be stripped before conversion
* is attempted. The function will exit with an error message if the units 
* are invalid, or if the string to number conversion fails.
*/
double OutputEstimate::hsize2bytes(std::string sizestr) {

  std::vector<std::string> units = boost::assign::list_of("B")("kB")("MB")("GB")("TB")("PB")("EB")("ZB")("YB");

  // strip any whitespace....
  boost::algorithm::trim(sizestr);

  // split the string up into the numeric portion and the units suffix
  std::string hrunit = sizestr.substr(sizestr.size()-2, std::string::npos);
  std::string numeric_part = sizestr.substr(0, sizestr.size()-2);

  // strip any remaining whitespace...
  boost::algorithm::trim(numeric_part);

  bool found = (std::find(units.begin(), units.end(), hrunit) != units.end());
  if ( !found ) {
    BOOST_LOG_SEV(glg, fatal) << "INVALID UNIT SPECIFICATION!: " << hrunit;
    exit(-1);
  }

  double size;
  try {
    size = boost::lexical_cast<double>(numeric_part);
  } catch (boost::bad_lexical_cast &) {
    BOOST_LOG_SEV(glg, fatal) << "Problem casting '" << numeric_part << "' to double!";
    exit(-1);
  }

  int i = 0;
  while ( (!(hrunit.compare(units[i]))) == 0 && (i < units.size()) )  {
    size *= 1024;
    i++;
  }
  return size; // in bytes
}

// ideas for  API functions
//  oe.per_grid_cell()
//  oe.per_year()
//  oe.print_table()

