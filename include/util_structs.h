/*
 * Provides simple utility structs.
 */
#ifndef UTIL_STRUCTS_H_
#define UTIL_STRUCTS_H_


struct output_spec{
  std::string filename;
  std::string filestr; //subjective filepath with filename.
  std::string units;
  bool veg;
  bool soil;
  int dim_count;
};


#endif
