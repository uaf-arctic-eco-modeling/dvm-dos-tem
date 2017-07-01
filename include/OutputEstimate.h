//
//  OutputEstimate.h
//  
//
//  Created by Tobey Carman on 6/22/17.
//
//

#ifndef OutputEstimate_h
#define OutputEstimate_h

#include <iostream>

#include <string>
#include <vector>


#include <boost/assign/list_of.hpp>

#include "ModelData.h"
#include "../src/TEMUtilityFunctions.h"


struct NetcdfOutputTypes {
  double daily;
  double monthly;
  double yearly;
  NetcdfOutputTypes():daily(0), monthly(0), yearly(0) {}
};

struct JsonOutputTypes {
  double archive;
  double daily;
  double monthly;
  double yearly;

  double jcoef_archive;
  double jcoef_daily;
  double jcoef_monthly;
  double jcoef_yearly;

  JsonOutputTypes(double _jca, double _jcd, double _jcm, double _jcy):
    archive(0), daily(0), monthly(0), yearly(0),
    jcoef_archive(_jca), jcoef_daily(_jcd), jcoef_monthly(_jcm), jcoef_yearly(_jcy) {}
};

/** Holds the ouput volume estimate for a run-stage. Notes:
 *   - sizes are in bytes
 *   - for all years represented by runyears
 *   - for one cell
 */
struct StageOutputEstimate {
  std::string name;
  int runyears;
  NetcdfOutputTypes nc_out;
  JsonOutputTypes json_out;
  StageOutputEstimate(
      const std::string& _name, int _yrs,
      int _jca, int _jcd, int _jcm, int _jcy):
    name(_name),
    runyears(_yrs),
    nc_out(),
    json_out(_jca, _jcd, _jcm, _jcy){}
};

class OutputEstimate {

  /** Returns a 'human readable' size string with SI suffix */
  std::string hsize(double size);

  int active_cells;
  std::vector<StageOutputEstimate> stage_output_estimates;

public:

  OutputEstimate(const ModelData& md, bool calmode);

  std::string estimate_as_table();

  double netcdf_total();

  double json_total();

  double cell_total();

  double all_cells_total();

  double hsize2bytes(std::string sizestr);


// ideas for  API functions
//  oe.per_grid_cell()
//  oe.per_year()
//  oe.print_table()

};


#endif /* OutputEstimate.h */
