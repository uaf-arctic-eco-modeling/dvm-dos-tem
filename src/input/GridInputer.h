#ifndef GRIDINPUTER_H_
#define GRIDINPUTER_H_

/*! this class is used to readin input of parameters, forcings for TEM
 * \file
 *
 * Modified by F-M Yuan, due to memory-leaking
 *
 */

#include <iostream>
#include <fstream>
#include <cstdio>
#include <string>
#include <cmath>
using namespace std;

#include <netcdfcpp.h>

#include "../inc/layerconst.h"
#include "../inc/errorcode.h"
#include "../data/GridData.h"

//local header
#include "../runmodule/ModelData.h"

class GridInputer {
public:
  GridInputer();
  ~GridInputer();

  void setModelData(ModelData* mdp);
  int init();

  // grid data
  void getDrainType(int & drgtype, const int & recno);
  void getSoilTexture(int & topsoil, int & botsoil, const int & recno);
  void getGfire(int &fri, double pfseason[], double pfsize[],const int & recno);

private:

  int initGrid(string& dir);
  int initDrainType(string& dir);
  int initSoilTexture(string& dir);
  int initFireStatistics(string& dir);

  string gridfname;
  string drainfname;
  string soilfname;
  string gfirefname;

  ModelData* md;

};

#endif /*GRIDINPUTER_H_*/
