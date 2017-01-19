/*
 * Provides simple utility structs.
 */
#ifndef UTIL_STRUCTS_H_
#define UTIL_STRUCTS_H_


struct output_spec{
  std::string filename;
  std::string filestr; //subjective filepath with filename.
  bool pft;
  bool compartment;
  bool soil;
  bool yearly;
  bool monthly;
  bool daily;
  int dim_count;
};


#endif
