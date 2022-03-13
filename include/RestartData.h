#ifndef RESTARTDATA_H_
#define RESTARTDATA_H_

#include <string>

#ifdef WITHMPI
#include <mpi.h> // for "exporting" an MPI derived type...
#endif

#include "errorcode.h"
#include "cohortconst.h"
#include "layerconst.h"

class RestartData {
public :
  RestartData();
  ~RestartData();

  #ifdef WITHMPI
  MPI_Datatype register_mpi_datatype();
  #endif

  void reinitValue();
  void write_pixel_to_ncfile(const std::string& fname, const int rowidx, const int colidx);
  void update_from_ncfile(const std::string& fname, const int rowidx, const int colidx);
  //The following two functions should probably be replaced with
  //something that does not require manually adding new members.
  void verify_logical_values();
  void restartdata_to_log();

  void read_px_vars(const std::string& fname, const int rowidx, const int colidx);
  void read_px_pft_vars(const std::string& fname, const int rowidx, const int colidx);
  void read_px_pftpart_pft_vars(const std::string& fname, const int rowidx, const int colidx);
  void read_px_snow_vars(const std::string& fname, const int rowidx, const int colidx);
  void read_px_root_pft_vars(const std::string& fname, const int rowidx, const int colidx);
  void read_px_soil_vars(const std::string& fname, const int rowidx, const int colidx);
  void read_px_rock_vars(const std::string& fname, const int rowidx, const int colidx);
  void read_px_front_vars(const std::string& fname, const int rowidx, const int colidx);
  void read_px_prev_pft_vars(const std::string& fname, const int rowidx, const int colidx);

  void write_px_vars(const std::string& fname, const int rowidx, const int colidx);
  void write_px_pft_vars(const std::string& fname, const int rowidx, const int colidx);
  void write_px_pftpart_pft_vars(const std::string& fname, const int rowidx, const int colidx);
  void write_px_snow_vars(const std::string& fname, const int rowidx, const int colidx);
  void write_px_root_pft_vars(const std::string& fname, const int rowidx, const int colidx);
  void write_px_soil_vars(const std::string& fname, const int rowidx, const int colidx);
  void write_px_rock_vars(const std::string& fname, const int rowidx, const int colidx);
  void write_px_front_vars(const std::string& fname, const int rowidx, const int colidx);
  void write_px_prev_pft_vars(const std::string& fname, const int rowidx, const int colidx);

  static void create_empty_file(const std::string& fname, const int ysize, const int xsize);

  int chtid;

  // atm
  int dsr;
  double firea2sorgn;

  // vegetation
  int yrsdist;

  int ifwoody[NUM_PFT]; // - 'veg_dim'
  int ifdeciwoody[NUM_PFT];
  int ifperenial[NUM_PFT];
  int nonvascular[NUM_PFT];
  int vegage[NUM_PFT];
  double vegcov[NUM_PFT];
  double lai[NUM_PFT];
  double rootfrac[MAX_ROT_LAY][NUM_PFT];

  double vegwater[NUM_PFT]; // canopy water - 'vegs_env'
  double vegsnow[NUM_PFT];  // canopy snow  - 'vegs_env'

  double vegc[NUM_PFT_PART][NUM_PFT]; // - 'vegs_bgc'
  double labn[NUM_PFT];
  double strn[NUM_PFT_PART][NUM_PFT];
  double vegC2N[NUM_PFT_PART][NUM_PFT];
  double deadc[NUM_PFT];
  double deadn[NUM_PFT];

  double topt[NUM_PFT]; // yearly-evolved 'topt'
  double eetmx[NUM_PFT]; // yearly max. month 'eet'
  double unnormleaf[NUM_PFT];
  double unnormleafmx[NUM_PFT]; // yearly max. unnormalized 'fleaf'
  double growingttime[NUM_PFT]; // yearly growthing t-time

  // This is for f(foliage) in GPP to be sure f(foliage) not going down
  double foliagemx[NUM_PFT];

  // This is for f(temp) in GPP to calculate the mean of the 10 previous values
  double toptA[10][NUM_PFT];

  // This is for f(phenology) in GPP to calculate the mean of the 10
  // previous values
  double eetmxA[10][NUM_PFT];
  double unnormleafmxA[10][NUM_PFT];
  double growingttimeA[10][NUM_PFT];

  // snow
  int numsnwl;
  double snwextramass;
  double TSsnow[MAX_SNW_LAY];
  double DZsnow[MAX_SNW_LAY];
  double LIQsnow[MAX_SNW_LAY];
  double RHOsnow[MAX_SNW_LAY];
  double ICEsnow[MAX_SNW_LAY];
  double AGEsnow[MAX_SNW_LAY];

  // ground-soil
  int numsl;
  double monthsfrozen;
  int rtfrozendays;
  int rtunfrozendays;
  double watertab;

  double DZsoil[MAX_SOI_LAY];
  int TYPEsoil[MAX_SOI_LAY];
  int AGEsoil[MAX_SOI_LAY];
  double TSsoil[MAX_SOI_LAY];
  double LIQsoil[MAX_SOI_LAY];
  double ICEsoil[MAX_SOI_LAY];
  int FROZENsoil[MAX_SOI_LAY];
  double FROZENFRACsoil[MAX_SOI_LAY];
  int TEXTUREsoil[MAX_SOI_LAY];

  double TSrock[MAX_ROC_LAY];
  double DZrock[MAX_ROC_LAY];

  double frontZ[MAX_NUM_FNT];
  int frontFT[MAX_NUM_FNT];

  double wdebrisc;
  double rawc[MAX_SOI_LAY];
  double soma[MAX_SOI_LAY];
  double sompr[MAX_SOI_LAY];
  double somcr[MAX_SOI_LAY];

  double wdebrisn;
  double orgn[MAX_SOI_LAY];
  double avln[MAX_SOI_LAY];

  // previous 12-month litterfall (root death) input C/N ratios in each
  // soil layer for adjusting 'kd'
  double prvltrfcnA[12][MAX_SOI_LAY];


};

#endif /*RESTARTDATA_H_*/
