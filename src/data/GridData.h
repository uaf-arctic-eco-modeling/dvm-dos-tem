#ifndef GRIDDATA_H_
#define GRIDDATA_H_

#include <string>
#include <list>

#include "../TEMUtilityFunctions.h"

#include "../inc/errorcode.h"
#include "../inc/timeconst.h"
#include "../inc/cohortconst.h"


using namespace std;

class GridData {
public:
  GridData();
  ~GridData();

  void clear();

  /* data for ONE grid (current) */
  float lat;
  float lon;
  float alldaylengths[365];

  int drgtype;

  int topsoil;
  int botsoil;

  int fri;
  double pfsize[NUM_FSIZE];
  double pfseason[NUM_FSEASON];

  void read_location_from_file(std::string filename, int record);
  void drainage_type_from_file(std::string filename, int rec);
  void soil_texture_from_file(std::string filename, int recid);
  void g_fire_from_file(std::string filename, int recid);



};

#endif /*GRIDDATA_H_*/
