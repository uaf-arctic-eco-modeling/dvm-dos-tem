/*
 * RunGrid.cpp
 *
 * Grid-level initialization, run, and output (if any)
 *    Note: the output modules are put here, so can be flexible for outputs
 *
*/

#include "RunGrid.h"
#include "../TEMUtilityFunctions.h"

RunGrid::RunGrid() {
  // grided data record ids in .nc files
  gridrecno  = MISSING_I;
  drainrecno = MISSING_I;
  soilrecno  = MISSING_I;
  gfirerecno = MISSING_I;
};

RunGrid::~RunGrid() {
};

void RunGrid::setModelData(ModelData * mdp) {
  md= mdp;
};

/** Setups up the grid ids from various input files.
*
*  Note: recno - the order (from ZERO) in the .nc file, ids - the real
*        ids in the *.nc files
*/
void RunGrid::setup_gridids_from_files(int recno) {

  this->grdids.push_back(MISSING_I);
  this->grddrgids.push_back(MISSING_I);
  this->grdsoilids.push_back(MISSING_I);
  this->grdfireids.push_back(MISSING_I);

  NcFile grid_file = temutil::open_ncfile(md->grdinputdir+"grid.nc");

  NcVar* grididV = temutil::get_ncvar(grid_file, "GRIDID");
  grididV->set_cur(recno);
  grididV->get(&this->grdids.back(), 1);

  NcVar* drgidV = temutil::get_ncvar(grid_file, "DRAINAGEID");
  drgidV->set_cur(recno);
  drgidV->get(&this->grddrgids.back(), 1);

  NcVar* soilidV = temutil::get_ncvar(grid_file, "SOILID");
  soilidV->set_cur(recno);
  soilidV->get(&this->grdsoilids.back(), 1);

  NcVar* gfireidV = temutil::get_ncvar(grid_file, "GFIREID");
  gfireidV->set_cur(recno);
  gfireidV->get(&this->grdfireids.back(), 1);
  
}

/** Reading all grid-level data ids.
*/
int RunGrid::allgridids() {
  int error = 0;

  /* NOTE: Should probbaly add some kind of error checking. Right now, the 
   * error stack-variable is doing nothing.
   */

  for (int rec_num = 0; rec_num < md->act_gridno; ++rec_num) {
    this->setup_gridids_from_files(rec_num);
  }

  for (int i = 0; i < md->act_drainno; ++i) {

    this->drainids.push_back(MISSING_I);

    NcFile f = temutil::open_ncfile(md->grdinputdir+"drainage.nc");

    NcVar* v = temutil::get_ncvar(f, "DRAINAGEID");
    v->set_cur(i);
    v->get(&this->drainids.back(), 1);

  }

  for (int i = 0; i < md->act_soilno; ++i) {

    this->soilids.push_back(MISSING_I);

    NcFile f = temutil::open_ncfile(md->grdinputdir+"soiltexture.nc");

    NcVar* v = temutil::get_ncvar(f, "SOILID");
    v->set_cur(i);
    v->get(&this->soilids.back(), 1);

  }

  for (int i = 0; i < md->act_gfireno; ++i) {

    this->gfireids.push_back(MISSING_I);

    NcFile f = temutil::open_ncfile(md->grdinputdir+"firestatistics.nc");

    NcVar* v = temutil::get_ncvar(f, "GFIREID");
    v->set_cur(i);
    v->get(&this->gfireids.back(), 1);
  }

  return error;
};

//reading data for ONE grid, using its record no (the order) in .nc files,
// which must be known before calling
int RunGrid::readData() {
  //reading the grided 'lat/lon' data
  if (gridrecno<0) {
    return -1;
  }

  this->grid.gd.read_location_from_file(md->grdinputdir + "grid.nc", gridrecno);
  //ginputer.getLatlon(grid.gd.lat, grid.gd.lon, gridrecno);

  //reading the grided 'drainage type' data
  if (drainrecno<0) {
    return -2;
  }

  ginputer.getDrainType(grid.gd.drgtype, drainrecno);

  //reading the grided 'soil texture' data
  if (soilrecno<0) {
    return -3;
  }

  ginputer.getSoilTexture(grid.gd.topsoil, grid.gd.botsoil, soilrecno);

  //reading the grided 'fire' data
  if (gfirerecno<0) {
    return -4;
  }

  ginputer.getGfire(grid.gd.fri, grid.gd.pfseason, grid.gd.pfsize, gfirerecno);
  //
  grid.reinit();          //checking grid data
  return 0;
};
