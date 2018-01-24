/*
 * Provides simple utility structs.
 */
#ifndef UTIL_STRUCTS_H_
#define UTIL_STRUCTS_H_

#include <boost/archive/text_oarchive.hpp>
#include <boost/archive/text_iarchive.hpp>

struct OutputSpec{
  std::string file_path; // Subjective file path, not including filename
  std::string filename_prefix; //example: ALD_monthly
  int dim_count;

  // Which dimensions to define
  bool pft;
  bool compartment;
  bool layer;
  bool yearly;
  bool monthly;
  bool daily;
};


namespace boost {
namespace serialization {

template<class Archive>
void serialize(Archive & ar, OutputSpec & os, const unsigned int version){

  ar & os.file_path;
  ar & os.filename_prefix;
  ar & os.dim_count;

  ar & os.pft;
  ar & os.compartment;
  ar & os.layer;
  ar & os.yearly;
  ar & os.monthly;
  ar & os.daily;
}

}//namespace serialization
}//namespace boost

#endif /* UTIL_STRUCTS_H_ */
