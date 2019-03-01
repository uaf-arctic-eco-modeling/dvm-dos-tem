/*
 * Provides simple utility structs.
 */
#ifndef UTIL_STRUCTS_H_
#define UTIL_STRUCTS_H_


struct OutputSpec{
  std::string file_path; // Subjective file path, not including filename
  std::string filename_prefix; //example: ALD_monthly
  std::string var_name; //example: "ALD"
  int dim_count;

  // Which dimensions to define
  bool pft;
  bool compartment;
  bool layer;
  bool yearly;
  bool monthly;
  bool daily;
};


#endif /* UTIL_STRUCTS_H_ */
