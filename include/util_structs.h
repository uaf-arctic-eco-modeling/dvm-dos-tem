/*
 * Provides simple utility structs.
 */
#ifndef UTIL_STRUCTS_H_
#define UTIL_STRUCTS_H_

#include "errorcode.h"

struct OutputSpec{
  std::string file_path; // Subjective file path, not including filename
  std::string filename_prefix; //example: ALD_monthly
  std::string var_name; //example: "ALD"
  int data_type; //Integer value of NC data type
  int dim_count;

  // Which dimensions to define
  bool pft;
  bool compartment;
  bool layer;
  bool yearly;
  bool monthly;
  bool daily;
};

//temporo-spatial pause
struct timestep_id{
  int x, y; //
  std::string stage;
  int year;
  int month;
  //int day;//currently unused while we produce a proof of concept.

  timestep_id(): x(), y(), stage("unset"), year(UIN_I), month(UIN_I){}
  timestep_id(int new_x, int new_y, std::string new_stage, int new_year, int new_month): x(new_x), y(new_y), stage(new_stage), year(new_year), month(new_month){}
};

#endif /* UTIL_STRUCTS_H_ */
