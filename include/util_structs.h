/*
 * Provides simple utility structs.
 */
#ifndef UTIL_STRUCTS_H_
#define UTIL_STRUCTS_H_


struct output_spec{
  std::string filename;
  std::string filestr; //subjective filepath with filename.
  int dim_count;

  //Which dimensions to define
  bool pft;
  bool compartment;
  bool layer;
  bool yearly;
  bool monthly;
  bool daily;
};


#endif
