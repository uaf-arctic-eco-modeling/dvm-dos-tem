#include <string>

#include <netcdfcpp.h>

#include "GridData.h"

GridData::GridData() {
};

GridData::~GridData() {
};

void GridData::clear() {
  lat = MISSING_F;
  lon = MISSING_F;
  fill_n(alldaylengths, 365, MISSING_F);
  drgtype = MISSING_I;
  topsoil = MISSING_I;
  botsoil = MISSING_I;
  fri = MISSING_I;
  fill_n(pfsize, NUM_FSIZE, MISSING_D);
  fill_n(pfseason, NUM_FSEASON, MISSING_D);
}

/* Given a file name and "grid record id", sets members lat, lon from file.
 *
 * Note: recid - the order (from ZERO) in the .nc file,
 *       v.s.
 *       gridid - the grid id user-defined in the dataset
 */
void GridData::read_location_from_file(std::string filename, int recid) {

  NcFile grid_file = temutil::open_ncfile(filename);

  NcVar* latV = temutil::get_ncvar(grid_file, "LAT");
  latV->set_cur(recid);
  latV->get(&this->lat, 1);

  NcVar* lonV = temutil::get_ncvar(grid_file, "LON");
  lonV->set_cur(recid);
  lonV->get(&this->lon, 1);

}

/** Given a file name, and "drainage record number", sets drainage member 
* from file.
*/
void GridData::drainage_type_from_file(std::string filename, int rec) {

  NcFile drainage_file = temutil::open_ncfile(filename);

  NcVar* v = temutil::get_ncvar(drainage_file, "DRAINAGETYPE");
  v->set_cur(rec);
  v->get(&this->drgtype, 1);

}

/** Given a file name and "soil record number", sets top and bottom 
* soil members.
*/
void GridData::soil_texture_from_file(std::string filename, int recid) {

  NcFile soil_file = temutil::open_ncfile(filename);
  
  NcVar* topsoilV = temutil::get_ncvar(soil_file, "TOPSOIL");
  topsoilV->set_cur(recid);
  topsoilV->get(&this->topsoil, 1);
  
  NcVar* botsoilV = temutil::get_ncvar(soil_file, "BOTSOIL");
  botsoilV->set_cur(recid);
  botsoilV->get(&this->botsoil, 1);
}


void GridData::g_fire_from_file(std::string filename, int recid) {
  //the following are the currently used in model, and can be
  //  modified (actually suggested)
  int fseasonno = 4; //fire season class no.: 0 - pre-fireseason; 1 - early;
  //                       2 - late; 3 - post-fireseason
  int fsizeno   = 5; //fire-size year class no.: 0 - small; 1 - intermediate;
  //           2 - large; 3 - very large; 4 - ultra-large
  
  // Have to set the error to non-fatal, or things break here in
  // single site run while trying to deal with PFSEASON...
  NcError err(NcError::verbose_nonfatal);
  
  NcFile fire_file = temutil::open_ncfile(filename);
  
  NcVar* friV = temutil::get_ncvar(fire_file, "FRI");
  friV->set_cur(recid);
  friV->get(&this->fri, 1);
  
  NcVar* fseasonV = temutil::get_ncvar(fire_file, "PFSEASON");
  fseasonV->set_cur(recid);
  fseasonV->get(&this->pfseason[0], fseasonno);
  
  NcVar* pfsizeV = temutil::get_ncvar(fire_file, "PFSIZE");
  pfsizeV->set_cur(recid);
  pfsizeV->get(&this->pfsize[0], fsizeno);
  
}
