/*
 *  RestartData.cpp
 *
 * Purpose: The data structure is the starting states to run the
 *            model continuously
 *
 *  (1) if running is paused, 'RestartData' is the restart point
 *  (2) intially this is for run-stage switch
 *  (3) potentially this can be used for spatial-explicitly run TEM
 *
 * History:
 *   June 28, 2011, by F.-M. Yuan:
 *     (1) Recoding based on DOS-TEM's code;
 *     (2) DVM concepts added, with the Purpose above in mind
 *
 * Important Notes:
 *     (1)
 *
 */

#ifdef WITHMPI
#include <mpi.h>
#endif

#include "RestartData.h"
#include "../TEMUtilityFunctions.h"

#include "../TEMLogger.h"

extern src::severity_logger< severity_level > glg;

RestartData::RestartData() {
  reinitValue();
};

RestartData::~RestartData() {
};

#ifdef WITHMPI
MPI_Datatype RestartData::register_mpi_datatype() {
  
  // create types for all the dimensions in the RestartData object...
  const int elems_in_restartdata = 65;
  int counts[elems_in_restartdata] = {
    1, // int chtid;
    1, // int dsr;
    1, // double firea2sorgn;
    1, // int yrsdist;
    
    NUM_PFT, // int ifwoody[NUM_PFT];                  // - 'veg_dim'
    NUM_PFT, // int ifdeciwoody[NUM_PFT];
    NUM_PFT, // int ifperenial[NUM_PFT];
    NUM_PFT, // int nonvascular[NUM_PFT];
    NUM_PFT, // int vegage[NUM_PFT];
    NUM_PFT, // double vegcov[NUM_PFT];
    NUM_PFT, // double lai[NUM_PFT];
    
    MAX_ROT_LAY * NUM_PFT, // double rootfrac[MAX_ROT_LAY][NUM_PFT];
    
    NUM_PFT, // double vegwater[NUM_PFT];             //canopy water - 'vegs_env'
    NUM_PFT, // double vegsnow[NUM_PFT];              //canopy snow  - 'vegs_env'
    
    NUM_PFT_PART * NUM_PFT, // double vegc[NUM_PFT_PART][NUM_PFT];   // - 'vegs_bgc'
    
    NUM_PFT, // double labn[NUM_PFT];
    
    NUM_PFT_PART * NUM_PFT, // double strn[NUM_PFT_PART][NUM_PFT];
    
    NUM_PFT, // double deadc[NUM_PFT];
    NUM_PFT, // double deadn[NUM_PFT];
    NUM_PFT, // double topt[NUM_PFT];            // yearly-evolved 'topt'
    NUM_PFT, // double eetmx[NUM_PFT];           // yearly max. month 'eet'
    NUM_PFT, // double unnormleafmx[NUM_PFT];    // yearly max. unnormalized 'fleaf'
    NUM_PFT, // double growingttime[NUM_PFT];    // yearly growthing t-time
    NUM_PFT, // double foliagemx[NUM_PFT];        // this is for f(foliage) in GPP to be sure f(foliage) not going down
    
    10 * NUM_PFT, // double toptA[10][NUM_PFT];           // this is for f(temp) in GPP to calculate the mean of the 10 previous values
    10 * NUM_PFT, // double eetmxA[10][NUM_PFT];           // this is for f(phenology) in GPP to calculate the mean of the 10 previous values
    10 * NUM_PFT, // double unnormleafmxA[10][NUM_PFT];
    10 * NUM_PFT, // double growingttimeA[10][NUM_PFT];
    1, // int numsnwl;
    1, // double snwextramass;
    
    MAX_SNW_LAY, // double TSsnow[MAX_SNW_LAY];
    MAX_SNW_LAY, // double DZsnow[MAX_SNW_LAY];
    MAX_SNW_LAY, // double LIQsnow[MAX_SNW_LAY];
    MAX_SNW_LAY, // double RHOsnow[MAX_SNW_LAY];
    MAX_SNW_LAY, // double ICEsnow[MAX_SNW_LAY];
    MAX_SNW_LAY, // double AGEsnow[MAX_SNW_LAY];
    
    1, // int numsl;
    1, // double monthsfrozen;
    1, // int rtfrozendays;
    1, // int rtunfrozendays;
    1, // double watertab;
    
    MAX_SOI_LAY, // double DZsoil[MAX_SOI_LAY];
    MAX_SOI_LAY, // int TYPEsoil[MAX_SOI_LAY];
    MAX_SOI_LAY, // int AGEsoil[MAX_SOI_LAY];
    MAX_SOI_LAY, // double TSsoil[MAX_SOI_LAY];
    MAX_SOI_LAY, // double LIQsoil[MAX_SOI_LAY];
    MAX_SOI_LAY, // double ICEsoil[MAX_SOI_LAY];
    MAX_SOI_LAY, // int FROZENsoil[MAX_SOI_LAY];
    MAX_SOI_LAY, // double FROZENFRACsoil[MAX_SOI_LAY];
    MAX_SOI_LAY, // int TEXTUREsoil[MAX_SOI_LAY];
    
    MAX_ROC_LAY, // double TSrock[MAX_ROC_LAY];
    MAX_ROC_LAY, // double DZrock[MAX_ROC_LAY];
    
    MAX_NUM_FNT, // double frontZ[MAX_NUM_FNT];
    MAX_NUM_FNT, // int frontFT[MAX_NUM_FNT];
    
    1, // double wdebrisc;
    1, // double dmossc;
    
    MAX_SOI_LAY, // double rawc[MAX_SOI_LAY];
    MAX_SOI_LAY, // double soma[MAX_SOI_LAY];
    MAX_SOI_LAY, // double sompr[MAX_SOI_LAY];
    MAX_SOI_LAY, // double somcr[MAX_SOI_LAY];
    
    1, // double wdebrisn;
    1, // double dmossn;
    1, // double orgn[MAX_SOI_LAY];
    
    MAX_SOI_LAY, // double avln[MAX_SOI_LAY];
    
    12 * MAX_SOI_LAY // double prvltrfcnA[12][MAX_SOI_LAY];   //previous 12-month litterfall (root death) input C/N ratios in each soil layer for adjusting 'kd'
  };
  MPI_Datatype old_types[elems_in_restartdata] = {
    MPI_INT, // int chtid;
    MPI_INT, // int dsr;
    MPI_DOUBLE, // double firea2sorgn;
    MPI_INT, // int yrsdist;
    MPI_INT, // int ifwoody[NUM_PFT];
    MPI_INT, // int ifdeciwoody[NUM_PFT];
    MPI_INT, // int ifperenial[NUM_PFT];
    MPI_INT, // int nonvascular[NUM_PFT];
    MPI_INT, // int vegage[NUM_PFT];
    MPI_DOUBLE, // double vegcov[NUM_PFT];
    MPI_DOUBLE, // double lai[NUM_PFT];
    MPI_DOUBLE, // double rootfrac[MAX_ROT_LAY][NUM_PFT];
    MPI_DOUBLE, // double vegwater[NUM_PFT];
    MPI_DOUBLE, // double vegsnow[NUM_PFT];
    MPI_DOUBLE, // double vegc[NUM_PFT_PART][NUM_PFT];
    MPI_DOUBLE, // double labn[NUM_PFT];
    MPI_DOUBLE, // double strn[NUM_PFT_PART][NUM_PFT];
    MPI_DOUBLE, // double deadc[NUM_PFT];
    MPI_DOUBLE, // double deadn[NUM_PFT];
    MPI_DOUBLE, // double topt[NUM_PFT];
    MPI_DOUBLE, // double eetmx[NUM_PFT];
    MPI_DOUBLE, // double unnormleafmx[NUM_PFT];
    MPI_DOUBLE, // double growingttime[NUM_PFT];
    MPI_DOUBLE, // double foliagemx[NUM_PFT];
    MPI_DOUBLE, // double toptA[10][NUM_PFT];
    MPI_DOUBLE, // double eetmxA[10][NUM_PFT];
    MPI_DOUBLE, // double unnormleafmxA[10][NUM_PFT];
    MPI_DOUBLE, // double growingttimeA[10][NUM_PFT];
    MPI_INT, // int numsnwl;
    MPI_DOUBLE, // double snwextramass;
    MPI_DOUBLE, // double TSsnow[MAX_SNW_LAY];
    MPI_DOUBLE, // double DZsnow[MAX_SNW_LAY];
    MPI_DOUBLE, // double LIQsnow[MAX_SNW_LAY];
    MPI_DOUBLE, // double RHOsnow[MAX_SNW_LAY];
    MPI_DOUBLE, // double ICEsnow[MAX_SNW_LAY];
    MPI_DOUBLE, // double AGEsnow[MAX_SNW_LAY];
    MPI_INT, // int numsl;
    MPI_DOUBLE, // double monthsfrozen;
    MPI_INT, // int rtfrozendays;
    MPI_INT, // int rtunfrozendays;
    MPI_DOUBLE, // double watertab;
    MPI_DOUBLE, // double DZsoil[MAX_SOI_LAY];
    MPI_INT, // int TYPEsoil[MAX_SOI_LAY];
    MPI_INT, // int AGEsoil[MAX_SOI_LAY];
    MPI_DOUBLE, // double TSsoil[MAX_SOI_LAY];
    MPI_DOUBLE, // double LIQsoil[MAX_SOI_LAY];
    MPI_DOUBLE, // double ICEsoil[MAX_SOI_LAY];
    MPI_INT, // int FROZENsoil[MAX_SOI_LAY];
    MPI_DOUBLE, // double FROZENFRACsoil[MAX_SOI_LAY];
    MPI_INT, // int TEXTUREsoil[MAX_SOI_LAY];
    MPI_DOUBLE, // double TSrock[MAX_ROC_LAY];
    MPI_DOUBLE, // double DZrock[MAX_ROC_LAY];
    MPI_DOUBLE, // double frontZ[MAX_NUM_FNT];
    MPI_INT, // int frontFT[MAX_NUM_FNT];
    MPI_DOUBLE, // double wdebrisc;
    MPI_DOUBLE, // double dmossc;
    MPI_DOUBLE, // double rawc[MAX_SOI_LAY];
    MPI_DOUBLE, // double soma[MAX_SOI_LAY];
    MPI_DOUBLE, // double sompr[MAX_SOI_LAY];
    MPI_DOUBLE, // double somcr[MAX_SOI_LAY];
    MPI_DOUBLE, // double wdebrisn;
    MPI_DOUBLE, // double dmossn;
    MPI_DOUBLE, // double orgn[MAX_SOI_LAY];
    MPI_DOUBLE, // double avln[MAX_SOI_LAY];
    MPI_DOUBLE // double prvltrfcnA[12][MAX_SOI_LAY];
  };
  MPI_Aint displacements[elems_in_restartdata] = {
    offsetof(RestartData, chtid),
    offsetof(RestartData, dsr),
    offsetof(RestartData, firea2sorgn),
    offsetof(RestartData, yrsdist),
    offsetof(RestartData, ifwoody),
    offsetof(RestartData, ifdeciwoody),
    offsetof(RestartData, ifperenial),
    offsetof(RestartData, nonvascular),
    offsetof(RestartData, vegage),
    offsetof(RestartData, vegcov),
    offsetof(RestartData, lai),
    offsetof(RestartData, rootfrac),
    offsetof(RestartData, vegwater),
    offsetof(RestartData, vegsnow),
    offsetof(RestartData, vegc),
    offsetof(RestartData, labn),
    offsetof(RestartData, strn),
    offsetof(RestartData, deadc),
    offsetof(RestartData, deadn),
    offsetof(RestartData, topt),
    offsetof(RestartData, eetmx),
    offsetof(RestartData, unnormleafmx),
    offsetof(RestartData, growingttime),
    offsetof(RestartData, foliagemx),
    offsetof(RestartData, toptA),
    offsetof(RestartData, eetmxA),
    offsetof(RestartData, unnormleafmxA),
    offsetof(RestartData, growingttimeA),
    offsetof(RestartData, numsnwl),
    offsetof(RestartData, snwextramass),
    offsetof(RestartData, TSsnow),
    offsetof(RestartData, DZsnow),
    offsetof(RestartData, LIQsnow),
    offsetof(RestartData, RHOsnow),
    offsetof(RestartData, ICEsnow),
    offsetof(RestartData, AGEsnow),
    offsetof(RestartData, numsl),
    offsetof(RestartData, monthsfrozen),
    offsetof(RestartData, rtfrozendays),
    offsetof(RestartData, rtunfrozendays),
    offsetof(RestartData, watertab),
    offsetof(RestartData, DZsoil),
    offsetof(RestartData, TYPEsoil),
    offsetof(RestartData, AGEsoil),
    offsetof(RestartData, TSsoil),
    offsetof(RestartData, LIQsoil),
    offsetof(RestartData, ICEsoil),
    offsetof(RestartData, FROZENsoil),
    offsetof(RestartData, FROZENFRACsoil),
    offsetof(RestartData, TEXTUREsoil),
    offsetof(RestartData, TSrock),
    offsetof(RestartData, DZrock),
    offsetof(RestartData, frontZ),
    offsetof(RestartData, frontFT),
    offsetof(RestartData, wdebrisc),
    offsetof(RestartData, dmossc),
    offsetof(RestartData, rawc),
    offsetof(RestartData, soma),
    offsetof(RestartData, sompr),
    offsetof(RestartData, somcr),
    offsetof(RestartData, wdebrisn),
    offsetof(RestartData, dmossn),
    offsetof(RestartData, orgn),
    offsetof(RestartData, avln),
    offsetof(RestartData, prvltrfcnA)
  };
  
  MPI_Datatype CUSTMPI_t_RestartData;
  MPI_Type_create_struct(elems_in_restartdata,  // count of blocks
                         counts,                // array with number of elements in each block
                         displacements,         // array of starting point of each block (in bytes)
                         old_types,             // array containing types of elements in each block
                         &CUSTMPI_t_RestartData);       // new type handle
  MPI_Type_commit(&CUSTMPI_t_RestartData);
  return CUSTMPI_t_RestartData;

}
#endif

void RestartData::reinitValue() {
  //
  chtid = MISSING_I;
  // atm
  dsr         = MISSING_I;
  firea2sorgn = MISSING_D;
  //vegegetation
  yrsdist     = MISSING_I;

  for (int ip=0; ip<NUM_PFT; ip++) {
    ifwoody[ip]     = MISSING_I;
    ifdeciwoody[ip] = MISSING_I;
    ifperenial[ip]  = MISSING_I;
    nonvascular[ip] = MISSING_I;
    vegage[ip] = MISSING_I;
    vegcov[ip] = MISSING_D;
    lai[ip]    = MISSING_D;

    for (int i=0; i<MAX_ROT_LAY; i++) {
      rootfrac[ip][i] = MISSING_D;
    }

    vegwater[ip] = MISSING_D;
    vegsnow[ip]  = MISSING_D;

    for (int i=0; i<NUM_PFT_PART; i++) {
      vegc[i][ip] = MISSING_D;
      strn[i][ip] = MISSING_D;
    }

    labn[ip]      = MISSING_D;
    deadc[ip]     = MISSING_D;
    deadn[ip]     = MISSING_D;
    topt[ip]  = MISSING_D;
    eetmx[ip] = MISSING_D;
    unnormleafmx[ip] = MISSING_D;
    growingttime[ip] = MISSING_D;
    foliagemx[ip]    = MISSING_D;

    for (int i=0; i<10; i++) {
      toptA[i][ip] = MISSING_D;
    }

    for (int i=0; i<10; i++) {
      eetmxA[i][ip]= MISSING_D;
    }

    for (int i=0; i<10; i++) {
      unnormleafmxA[i][ip] = MISSING_D;
    }

    for (int i=0; i<10; i++) {
      growingttimeA[i][ip] = MISSING_D;
    }
  }

  // snow
  numsnwl = MISSING_I;
  snwextramass = MISSING_D;

  for(int il =0; il<MAX_SNW_LAY; il++) {
    TSsnow[il]  = MISSING_D;
    DZsnow[il]  = MISSING_D;
    LIQsnow[il] = MISSING_D;
    ICEsnow[il] = MISSING_D;
    AGEsnow[il] = MISSING_D;
    RHOsnow[il] = MISSING_D;
  }

  //ground-soil
  numsl  = MISSING_I;
  monthsfrozen   = MISSING_D;
  rtfrozendays   = MISSING_I;
  rtunfrozendays = MISSING_I;
  watertab     = MISSING_D;

  for(int il =0; il<MAX_SOI_LAY; il++) {
    DZsoil[il]   = MISSING_D;
    TYPEsoil[il] = MISSING_I;
    AGEsoil[il]  = MISSING_I;
    TSsoil[il]   = MISSING_D;
    LIQsoil[il]  = MISSING_D;
    ICEsoil[il]  = MISSING_D;
    FROZENsoil[il]= MISSING_I;
    FROZENFRACsoil[il]= MISSING_D;
    TEXTUREsoil[il]   = MISSING_I;
  }

  for(int il =0; il<MAX_ROC_LAY; il++) {
    TSrock[il] = MISSING_D;
    DZrock[il] = MISSING_D;
  }

  for(int il =0; il<MAX_NUM_FNT; il++) {
    frontZ[il]  = MISSING_D;
    frontFT[il] = MISSING_I;
  }

  wdebrisc = MISSING_D;
  wdebrisn = MISSING_D;

  for(int il =0; il<MAX_SOI_LAY; il++) {
    rawc[il]  = MISSING_D;
    soma[il]  = MISSING_D;
    sompr[il] = MISSING_D;
    somcr[il] = MISSING_D;
    orgn[il] = MISSING_D;
    avln[il] = MISSING_D;

    for (int i=0; i<12; i++) {
      prvltrfcnA[i][il]  = MISSING_D;
    }
  }
};

/** Set values in this RestartData object from a NetCDF file. */
void RestartData::update_from_ncfile(const std::string& fname, const int rowidx, const int colidx) {
  BOOST_LOG_SEV(glg, debug) << "Opening dataset: " << fname << " to READ value into RestartData for pixel (y, x): (" << rowidx << "," << colidx << ")";
  BOOST_LOG_SEV(glg, debug) << temutil::report_yx_pixel_dims2str(fname);

  read_px_vars(fname, rowidx, colidx);

  read_px_pft_vars(fname, rowidx, colidx);

  read_px_pftpart_pft_vars(fname, rowidx, colidx);

  read_px_snow_vars(fname, rowidx, colidx);

  read_px_root_pft_vars(fname, rowidx, colidx);

  read_px_soil_vars(fname, rowidx, colidx);

  read_px_rock_vars(fname, rowidx, colidx);

  read_px_front_vars(fname, rowidx, colidx);

  read_px_prev_pft_vars(fname, rowidx, colidx);

  BOOST_LOG_SEV(glg, debug) << "Done reading data from file into RestartData.";
}

/** Copies values from this RestartData object to a NetCDF file. */
void RestartData::append_to_ncfile(const std::string& fname, const int rowidx, const int colidx) {

  BOOST_LOG_SEV(glg, debug) << "Opening dataset: " << fname
                            << " to WRITE RestartData for pixel (y, x): ("
                            << rowidx << "," << colidx << ")";

  BOOST_LOG_SEV(glg, debug) << temutil::report_yx_pixel_dims2str(fname);
  BOOST_LOG_SEV(glg, debug) << temutil::report_on_netcdf_file(fname, "dsr");

  write_px_vars(fname, rowidx, colidx);

  write_px_pft_vars(fname, rowidx, colidx);

  write_px_pftpart_pft_vars(fname, rowidx, colidx);

  write_px_snow_vars(fname, rowidx, colidx);

  write_px_root_pft_vars(fname, rowidx, colidx);

  write_px_soil_vars(fname, rowidx, colidx);

  write_px_rock_vars(fname, rowidx, colidx);

  write_px_front_vars(fname, rowidx, colidx);

  write_px_prev_pft_vars(fname, rowidx, colidx);

  BOOST_LOG_SEV(glg, debug) << "Done writing RestartData.";

}

/** Checks a given variable against an extreme negative value. FIX: should be more flexible*/
template<typename T> void check_bounds(std::string var_name, T value){
  if(value<-4000){
    BOOST_LOG_SEV(glg, err) << var_name << " is out of bounds: " << value;
  }
}

/** Checks values in this RestartData for out-of-range or nonsensical values. FIX: incomplete*/
void RestartData::verify_logical_values(){
  BOOST_LOG_SEV(glg, info) << "Checking RestartData for out-of-range values";
  BOOST_LOG_SEV(glg, info) << "NOTE: Currently this only checks for extreme negative values.";
  BOOST_LOG_SEV(glg, info) << "This should be replaced in the future with a more sensible approach, perhaps with templating";

  //FIX Currently checking all values against a low negative number,
  //whether or not it makes sense for that value to have been initialized
  //to a low negative.

  check_bounds("chtid", chtid);
  check_bounds("dsr", dsr);
  check_bounds("firea2sorgn", firea2sorgn);
  check_bounds("yrsdist", yrsdist);
  for(int ii=0; ii<NUM_PFT; ii++){
    check_bounds("ifwoody", ifwoody[ii]);
    check_bounds("ifdeciwoody", ifdeciwoody[ii]);
    check_bounds("ifperenial", ifperenial[ii]);
    check_bounds("nonvascular", nonvascular[ii]);
    check_bounds("vegage", vegage[ii]);
    check_bounds("vegcov", vegcov[ii]);
    check_bounds("lai", lai[ii]);
    check_bounds("vegwater", vegwater[ii]);
    check_bounds("vegsnow", vegsnow[ii]);
    check_bounds("labn", labn[ii]);
    check_bounds("deadc", deadc[ii]);
    check_bounds("deadn", deadn[ii]);
    check_bounds("topt", topt[ii]);
    check_bounds("eetmx", topt[ii]);
    check_bounds("unnormleafmx", unnormleafmx[ii]);
    check_bounds("growingttime", growingttime[ii]);
    check_bounds("foliagemx", foliagemx[ii]);
    for(int jj=0; jj<NUM_PFT_PART; jj++){
      check_bounds("vegc", vegc[jj][ii]);
      check_bounds("strn", strn[jj][ii]);
    }
    for(int jj=0; jj<MAX_ROT_LAY; jj++){
      check_bounds("rootfrac", rootfrac[jj][ii]);
    }
    for(int jj=0; jj<10; jj++){
      check_bounds("toptA", toptA[jj][ii]);
      check_bounds("eetmxA", eetmxA[jj][ii]);
      check_bounds("unnormleafmxA", unnormleafmxA[jj][ii]);
      check_bounds("growingttimeA", growingttimeA[jj][ii]);
    }
  }

  check_bounds("numsnwl", numsnwl);
  check_bounds("snwextramass", snwextramass);
  for(int ii=0; ii<MAX_SNW_LAY; ii++){
    check_bounds("TSsnow", TSsnow[ii]);
    check_bounds("DZsnow", DZsnow[ii]);
    check_bounds("LIQsnow", LIQsnow[ii]);
    check_bounds("RHOsnow", RHOsnow[ii]);
    check_bounds("ICEsnow", ICEsnow[ii]);
    check_bounds("AGEsnow", AGEsnow[ii]);
  }

  check_bounds("numsl", numsl);
  check_bounds("monthsfrozen", monthsfrozen);
  check_bounds("rtfrozendays", rtfrozendays);
  check_bounds("rtunfrozendays", rtunfrozendays);
  check_bounds("watertab", watertab);
  check_bounds("wdebrisc", wdebrisc);
  check_bounds("wdebrisn", wdebrisn);
  check_bounds("dmossc", dmossc);
  check_bounds("dmossn", dmossn);
  for(int ii=0; ii<MAX_SOI_LAY; ii++){
    check_bounds("DZsoil", DZsoil[ii]);
    check_bounds("TYPEsoil", TYPEsoil[ii]);
    check_bounds("AGEsoil", AGEsoil[ii]);
    check_bounds("TSsoil", TSsoil[ii]);
    check_bounds("LIQsoil", LIQsoil[ii]);
    check_bounds("ICEsoil", ICEsoil[ii]);
    check_bounds("FROZENsoil", FROZENsoil[ii]);
    check_bounds("FROZENFRACsoil", FROZENFRACsoil[ii]);
    check_bounds("TEXTUREsoil", TEXTUREsoil[ii]);
    check_bounds("rawc", rawc[ii]);
    check_bounds("soma", soma[ii]);
    check_bounds("sompr", sompr[ii]);
    check_bounds("somcr", somcr[ii]);
    check_bounds("orgn", orgn[ii]);
    check_bounds("avln", avln[ii]);
    for(int jj=0; jj<12; jj++){
      check_bounds("prvltrfcnA", prvltrfcnA[jj][ii]);
    }
  }

  for(int ii=0; ii<MAX_ROC_LAY; ii++){
    check_bounds("TSrock", TSrock[ii]);
    check_bounds("DZrock", DZrock[ii]);
  }

  for(int ii=0; ii<MAX_NUM_FNT; ii++){
    check_bounds("frontZ", frontZ[ii]);
    check_bounds("frontFT", frontFT[ii]);
  }

  BOOST_LOG_SEV(glg, debug) << "";
}


/** Read single values for variables have dimensions (Y, X).*/
void RestartData::read_px_vars(const std::string& fname, const int rowidx, const int colidx) {
  
  int ncid;
  temutil::nc( nc_open(fname.c_str(), NC_NOWRITE, &ncid) );

  // Check dimension presence? length? size?

  int cv; // a reusable variable handle

  size_t start[2];
  start[0] = rowidx;
  start[1] = colidx;

  // atmosphere stuff
  temutil::nc( nc_inq_varid(ncid, "dsr", &cv) );
  temutil::nc( nc_get_var1_int(ncid, cv, start, &dsr) );
  temutil::nc( nc_inq_varid(ncid, "firea2sorgn", &cv) );
  temutil::nc( nc_get_var1_double(ncid, cv, start, &firea2sorgn) );

  // vegegetation stuff
  temutil::nc( nc_inq_varid(ncid, "yrsdist", &cv) );
  temutil::nc( nc_get_var1_int(ncid, cv, start, &yrsdist) );

  // snow stuff
  temutil::nc( nc_inq_varid(ncid, "numsnwl", &cv) );
  temutil::nc( nc_get_var1_int(ncid, cv, start, &numsnwl) );
  temutil::nc( nc_inq_varid(ncid, "snwextramass", &cv) );
  temutil::nc( nc_get_var1_double(ncid, cv, start, &snwextramass) );

  // ground / soil stuff
  temutil::nc( nc_inq_varid(ncid, "numsl", &cv) );
  temutil::nc( nc_get_var1_int(ncid, cv, start, &numsl) );
  temutil::nc( nc_inq_varid(ncid, "monthsfrozen", &cv) );
  temutil::nc( nc_get_var1_double(ncid, cv, start, &monthsfrozen) );
  temutil::nc( nc_inq_varid(ncid, "rtfrozendays", &cv) );
  temutil::nc( nc_get_var1_int(ncid, cv, start, &rtfrozendays) );
  temutil::nc( nc_inq_varid(ncid, "rtunfrozendays", &cv) );
  temutil::nc( nc_get_var1_int(ncid, cv, start, &rtunfrozendays) );
  temutil::nc( nc_inq_varid(ncid, "watertab", &cv) );
  temutil::nc( nc_get_var1_double(ncid, cv, start, &watertab) );

  // other stuff?
  temutil::nc( nc_inq_varid(ncid, "wdebrisc", &cv) );
  temutil::nc( nc_get_var1_double(ncid, cv, start, &wdebrisc) );
  temutil::nc( nc_inq_varid(ncid, "wdebrisn", &cv) );
  temutil::nc( nc_get_var1_double(ncid, cv, start, &wdebrisn) );
  temutil::nc( nc_inq_varid(ncid, "dmossc", &cv) );
  temutil::nc( nc_get_var1_double(ncid, cv, start, &dmossc) );
  temutil::nc( nc_inq_varid(ncid, "dmossn", &cv) );
  temutil::nc( nc_get_var1_double(ncid, cv, start, &dmossn) );

  temutil::nc( nc_close(ncid) );

  // Also works to use the nc_get_vara_TYPE(...) variation
  //size_t count[2];
  //count[0] = 1;
  //count[1] = 1;
  //temutil::nc( nc_get_vara_int(ncid, cv, start, count, &dsr) );   // write an array
}

/** Reads arrays of values for variables that have dimensions (Y, X, pft). */
void RestartData::read_px_pft_vars(const std::string& fname, const int rowidx, const int colidx) {

  int ncid;
  temutil::nc( nc_open(fname.c_str(), NC_NOWRITE, &ncid) );

  // Check dimension presence? length? size?

  int cv; // a reusable variable handle
  
  size_t start[3];
  start[0] = rowidx;
  start[1] = colidx;
  start[2] = 0;

  size_t count[3];
  count[0] = 1;
  count[1] = 1;
  count[2] = NUM_PFT;
  
  temutil::nc( nc_inq_varid(ncid, "ifwoody", &cv) );
  temutil::nc( nc_get_vara_int(ncid, cv, start, count, &ifwoody[0]) );
  temutil::nc( nc_inq_varid(ncid, "ifdeciwoody", &cv) );
  temutil::nc( nc_get_vara_int(ncid, cv, start, count, &ifdeciwoody[0]) );
  temutil::nc( nc_inq_varid(ncid, "ifperenial", &cv) );
  temutil::nc( nc_get_vara_int(ncid, cv, start, count, &ifperenial[0]) );
  temutil::nc( nc_inq_varid(ncid, "nonvascular", &cv) );
  temutil::nc( nc_get_vara_int(ncid, cv, start, count, &nonvascular[0]) );
  temutil::nc( nc_inq_varid(ncid, "vegage", &cv) );
  temutil::nc( nc_get_vara_int(ncid, cv, start, count, &vegage[0]) );
  
  temutil::nc( nc_inq_varid(ncid, "lai", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &lai[0]) );
  temutil::nc( nc_inq_varid(ncid, "vegwater", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &vegwater[0]) );
  temutil::nc( nc_inq_varid(ncid, "vegsnow", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &vegsnow[0]) );
  temutil::nc( nc_inq_varid(ncid, "labn", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &labn[0]) );
  temutil::nc( nc_inq_varid(ncid, "deadc", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &deadc[0]) );
  temutil::nc( nc_inq_varid(ncid, "deadn", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &deadn[0]) );
  temutil::nc( nc_inq_varid(ncid, "topt", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &topt[0]) );
  temutil::nc( nc_inq_varid(ncid, "eetmx", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &eetmx[0]) );
  temutil::nc( nc_inq_varid(ncid, "unnormleafmx", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &unnormleafmx[0]) );
  temutil::nc( nc_inq_varid(ncid, "growingttime", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &growingttime[0]) );
  temutil::nc( nc_inq_varid(ncid, "foliagemx", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &foliagemx[0]) );

  temutil::nc( nc_close(ncid) );

}

/** Read arrays for variables that have dimensions (Y, X, pftpart, pft). */
void RestartData::read_px_pftpart_pft_vars(const std::string& fname, const int rowidx, const int colidx) {

  int ncid;
  temutil::nc( nc_open(fname.c_str(), NC_NOWRITE, &ncid) );

  int cv; // a reusable variable handle
  
  size_t start[4];
  start[0] = rowidx;
  start[1] = colidx;
  start[2] = 0;
  start[3] = 0;

  size_t count[4];
  count[0] = 1;
  count[1] = 1;
  count[2] = NUM_PFT_PART;
  count[3] = NUM_PFT;
  
  temutil::nc( nc_inq_varid(ncid, "vegc", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &vegc[0][0]) );
  
  temutil::nc( nc_inq_varid(ncid, "strn", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &strn[0][0]) );
  
  temutil::nc( nc_close(ncid) );

}

/**  Reads arrays for variables with dimensions (Y, X, snowlayer) */
void RestartData::read_px_snow_vars(const std::string& fname, const int rowidx, const int colidx) {

  int ncid;
  temutil::nc( nc_open(fname.c_str(), NC_NOWRITE, &ncid) );

  // Check dimension presence? length? size?

  int cv; // a reusable variable handle

  size_t start[3];
  start[0] = rowidx;
  start[1] = colidx;
  start[2] = 0;

  size_t count[3];
  count[0] = 1;
  count[1] = 1;
  count[2] = MAX_SNW_LAY;

  temutil::nc( nc_inq_varid(ncid, "TSsnow", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &TSsnow[0]) );

  temutil::nc( nc_inq_varid(ncid, "DZsnow", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &DZsnow[0]) );
  temutil::nc( nc_inq_varid(ncid, "LIQsnow", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &LIQsnow[0]) );
  temutil::nc( nc_inq_varid(ncid, "RHOsnow", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &RHOsnow[0]) );
  temutil::nc( nc_inq_varid(ncid, "ICEsnow", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &ICEsnow[0]) );
  temutil::nc( nc_inq_varid(ncid, "AGEsnow", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &AGEsnow[0]) );

  temutil::nc( nc_close(ncid) );
}

/**  Reads arrays for variables with dimensions (Y, X, rootlayer, pft) */
void RestartData::read_px_root_pft_vars(const std::string& fname, const int rowidx, const int colidx) {
  int ncid;
  temutil::nc( nc_open(fname.c_str(), NC_NOWRITE, &ncid) );

  int cv; // a reusable variable handle

  size_t start[4];
  start[0] = rowidx;
  start[1] = colidx;
  start[2] = 0;
  start[3] = 0;

  size_t count[4];
  count[0] = 1;
  count[1] = 1;
  count[2] = MAX_ROT_LAY;
  count[3] = NUM_PFT;

  temutil::nc( nc_inq_varid(ncid, "rootfrac", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &rootfrac[0][0]) );

  temutil::nc( nc_close(ncid) );

}

/**  Reads arrays for variables with dimensions (Y, X, soillayer) */
void RestartData::read_px_soil_vars(const std::string& fname, const int rowidx, const int colidx) {

  int ncid;
  temutil::nc( nc_open(fname.c_str(), NC_NOWRITE, &ncid) );

  int cv; // a reusable variable handle

  size_t start[3];
  start[0] = rowidx;
  start[1] = colidx;
  start[2] = 0;

  size_t count[3];
  count[0] = 1;
  count[1] = 1;
  count[2] = MAX_SOI_LAY;

  temutil::nc( nc_inq_varid(ncid, "TYPEsoil", &cv) );
  temutil::nc( nc_get_vara_int(ncid, cv, start, count, &TYPEsoil[0]) );
  temutil::nc( nc_inq_varid(ncid, "AGEsoil", &cv) );
  temutil::nc( nc_get_vara_int(ncid, cv, start, count, &AGEsoil[0]) );
  temutil::nc( nc_inq_varid(ncid, "FROZENsoil", &cv) );
  temutil::nc( nc_get_vara_int(ncid, cv, start, count, &FROZENsoil[0]) );
  temutil::nc( nc_inq_varid(ncid, "TEXTUREsoil", &cv) );
  temutil::nc( nc_get_vara_int(ncid, cv, start, count, &TEXTUREsoil[0]) );

  temutil::nc( nc_inq_varid(ncid, "DZsoil", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &DZsoil[0]) );
  temutil::nc( nc_inq_varid(ncid, "TSsoil", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &TSsoil[0]) );
  temutil::nc( nc_inq_varid(ncid, "LIQsoil", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &LIQsoil[0]) );
  temutil::nc( nc_inq_varid(ncid, "FROZENFRACsoil", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &FROZENFRACsoil[0]) );
  temutil::nc( nc_inq_varid(ncid, "rawc", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &rawc[0]) );
  temutil::nc( nc_inq_varid(ncid, "soma", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &soma[0]) );
  temutil::nc( nc_inq_varid(ncid, "sompr", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &sompr[0]) );
  temutil::nc( nc_inq_varid(ncid, "somcr", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &somcr[0]) );
  temutil::nc( nc_inq_varid(ncid, "orgn", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &orgn[0]) );
  temutil::nc( nc_inq_varid(ncid, "avln", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &avln[0]) );

  temutil::nc( nc_close(ncid) );
}

/**  Reads arrays of values for variables that have dimensions (Y, X, rocklayer). */
void RestartData::read_px_rock_vars(const std::string& fname, const int rowidx, const int colidx) {

  int ncid;
  temutil::nc( nc_open(fname.c_str(), NC_NOWRITE, &ncid) );

  // Check dimension presence? length? size?

  int cv; // a reusable variable handle

  size_t start[3];
  start[0] = rowidx;
  start[1] = colidx;
  start[2] = 0;

  size_t count[3];
  count[0] = 1;
  count[1] = 1;
  count[2] = MAX_ROC_LAY;

  temutil::nc( nc_inq_varid(ncid, "TSrock", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &TSrock[0]) );
  temutil::nc( nc_inq_varid(ncid, "DZrock", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &DZrock[0]) );

  temutil::nc( nc_close(ncid) );

}

/**  Reads arrays of values for variables that have dimensions (Y, X, fronts). */
void RestartData::read_px_front_vars(const std::string& fname, const int rowidx, const int colidx) {

  int ncid;
  temutil::nc( nc_open(fname.c_str(), NC_NOWRITE, &ncid) );

  int cv; // a reusable variable handle

  size_t start[3];
  start[0] = rowidx;
  start[1] = colidx;
  start[2] = 0;

  size_t count[3];
  count[0] = 1;
  count[1] = 1;
  count[2] = MAX_NUM_FNT;

  temutil::nc( nc_inq_varid(ncid, "frontFT", &cv) );
  temutil::nc( nc_get_vara_int(ncid, cv, start, count, &frontFT[0]) );

  temutil::nc( nc_inq_varid(ncid, "frontZ", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &frontZ[0]) );

  temutil::nc( nc_close(ncid) );

}

/**  Reads arrays for variables with dimensions (Y, X, prev<XX>, pft).
* Used for variables that need the previous 10 or 12 values.
*/
void RestartData::read_px_prev_pft_vars(const std::string& fname, const int rowidx, const int colidx) {
  int ncid;
  temutil::nc( nc_open(fname.c_str(), NC_NOWRITE, &ncid) );

  int cv; // a reusable variable handle

  size_t start[4];
  start[0] = rowidx;
  start[1] = colidx;
  start[2] = 0;
  start[3] = 0;

  size_t count[4];
  count[0] = 1;
  count[1] = 1;
  count[2] = 10;        // <-- previous 10 years?...
  count[3] = NUM_PFT;

  temutil::nc( nc_inq_varid(ncid, "toptA", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &toptA[0][0]) );
  temutil::nc( nc_inq_varid(ncid, "eetmxA", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &eetmxA[0][0]) );
  temutil::nc( nc_inq_varid(ncid, "growingttimeA", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &growingttimeA[0][0]) );
  temutil::nc( nc_inq_varid(ncid, "unnormleafmxA", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &unnormleafmxA[0][0]) );

  count[2] = 12;           // <-- previous 12 months?...
  temutil::nc( nc_inq_varid(ncid, "prvltrfcnA", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &prvltrfcnA[0][0]) );

  temutil::nc( nc_close(ncid) );

}

/** Writes single values for variables have dimensions (Y, X).*/
void RestartData::write_px_vars(const std::string& fname, const int rowidx, const int colidx) {
  
  int ncid;
  temutil::nc( nc_open(fname.c_str(), NC_WRITE, &ncid) );

  // Check dimension presence? length? size?

  int cv; // a reusable variable handle

  size_t start[2];
  start[0] = rowidx;
  start[1] = colidx;

  // atmosphere stuff
  temutil::nc( nc_inq_varid(ncid, "dsr", &cv) );
  temutil::nc( nc_put_var1_int(ncid, cv, start, &dsr) );
  temutil::nc( nc_inq_varid(ncid, "firea2sorgn", &cv) );
  temutil::nc( nc_put_var1_double(ncid, cv, start, &firea2sorgn) );

  // vegegetation stuff
  temutil::nc( nc_inq_varid(ncid, "yrsdist", &cv) );
  temutil::nc( nc_put_var1_int(ncid, cv, start, &yrsdist) );

  // snow stuff
  temutil::nc( nc_inq_varid(ncid, "numsnwl", &cv) );
  temutil::nc( nc_put_var1_int(ncid, cv, start, &numsnwl) );
  temutil::nc( nc_inq_varid(ncid, "snwextramass", &cv) );
  temutil::nc( nc_put_var1_double(ncid, cv, start, &snwextramass) );

  // ground / soil stuff
  temutil::nc( nc_inq_varid(ncid, "numsl", &cv) );
  temutil::nc( nc_put_var1_int(ncid, cv, start, &numsl) );
  temutil::nc( nc_inq_varid(ncid, "monthsfrozen", &cv) );
  temutil::nc( nc_put_var1_double(ncid, cv, start, &monthsfrozen) );
  temutil::nc( nc_inq_varid(ncid, "rtfrozendays", &cv) );
  temutil::nc( nc_put_var1_int(ncid, cv, start, &rtfrozendays) );
  temutil::nc( nc_inq_varid(ncid, "rtunfrozendays", &cv) );
  temutil::nc( nc_put_var1_int(ncid, cv, start, &rtunfrozendays) );
  temutil::nc( nc_inq_varid(ncid, "watertab", &cv) );
  temutil::nc( nc_put_var1_double(ncid, cv, start, &watertab) );

  // other stuff?
  temutil::nc( nc_inq_varid(ncid, "wdebrisc", &cv) );
  temutil::nc( nc_put_var1_double(ncid, cv, start, &wdebrisc) );
  temutil::nc( nc_inq_varid(ncid, "wdebrisn", &cv) );
  temutil::nc( nc_put_var1_double(ncid, cv, start, &wdebrisn) );
  temutil::nc( nc_inq_varid(ncid, "dmossc", &cv) );
  temutil::nc( nc_put_var1_double(ncid, cv, start, &dmossc) );
  temutil::nc( nc_inq_varid(ncid, "dmossn", &cv) );
  temutil::nc( nc_put_var1_double(ncid, cv, start, &dmossn) );

  temutil::nc( nc_close(ncid) );

  // Also works to use the nc_put_vara_TYPE(...) variation
  //size_t count[2];
  //count[0] = 1;
  //count[1] = 1;
  //temutil::nc( nc_put_vara_int(ncid, cv, start, count, &dsr) );   // write an array
}

/** Writes arrays of values for variables that have dimensions (Y, X, pft). */
void RestartData::write_px_pft_vars(const std::string& fname, const int rowidx, const int colidx) {

  int ncid;
  temutil::nc( nc_open(fname.c_str(), NC_WRITE, &ncid) );

  // Check dimension presence? length? size?

  int cv; // a reusable variable handle
  
  size_t start[3];
  start[0] = rowidx;
  start[1] = colidx;
  start[2] = 0;

  size_t count[3];
  count[0] = 1;
  count[1] = 1;
  count[2] = NUM_PFT;
  
  temutil::nc( nc_inq_varid(ncid, "ifwoody", &cv) );
  temutil::nc( nc_put_vara_int(ncid, cv, start, count, &ifwoody[0]) );
  temutil::nc( nc_inq_varid(ncid, "ifdeciwoody", &cv) );
  temutil::nc( nc_put_vara_int(ncid, cv, start, count, &ifdeciwoody[0]) );
  temutil::nc( nc_inq_varid(ncid, "ifperenial", &cv) );
  temutil::nc( nc_put_vara_int(ncid, cv, start, count, &ifperenial[0]) );
  temutil::nc( nc_inq_varid(ncid, "nonvascular", &cv) );
  temutil::nc( nc_put_vara_int(ncid, cv, start, count, &nonvascular[0]) );
  temutil::nc( nc_inq_varid(ncid, "vegage", &cv) );
  temutil::nc( nc_put_vara_int(ncid, cv, start, count, &vegage[0]) );
  
  temutil::nc( nc_inq_varid(ncid, "lai", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &lai[0]) );
  temutil::nc( nc_inq_varid(ncid, "vegwater", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &vegwater[0]) );
  temutil::nc( nc_inq_varid(ncid, "vegsnow", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &vegsnow[0]) );
  temutil::nc( nc_inq_varid(ncid, "labn", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &labn[0]) );
  temutil::nc( nc_inq_varid(ncid, "deadc", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &deadc[0]) );
  temutil::nc( nc_inq_varid(ncid, "deadn", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &deadn[0]) );
  temutil::nc( nc_inq_varid(ncid, "topt", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &topt[0]) );
  temutil::nc( nc_inq_varid(ncid, "eetmx", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &eetmx[0]) );
  temutil::nc( nc_inq_varid(ncid, "unnormleafmx", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &unnormleafmx[0]) );
  temutil::nc( nc_inq_varid(ncid, "growingttime", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &growingttime[0]) );
  temutil::nc( nc_inq_varid(ncid, "foliagemx", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &foliagemx[0]) );

  temutil::nc( nc_close(ncid) );

}

/** Writes arrays for variables that have dimensions (Y, X, pftpart, pft). */
void RestartData::write_px_pftpart_pft_vars(const std::string& fname, const int rowidx, const int colidx) {

  int ncid;
  temutil::nc( nc_open(fname.c_str(), NC_WRITE, &ncid) );

  int cv; // a reusable variable handle
  
  size_t start[4];
  start[0] = rowidx;
  start[1] = colidx;
  start[2] = 0;
  start[3] = 0;

  size_t count[4];
  count[0] = 1;
  count[1] = 1;
  count[2] = NUM_PFT_PART;
  count[3] = NUM_PFT;
  
  temutil::nc( nc_inq_varid(ncid, "vegc", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &vegc[0][0]) );
  
  temutil::nc( nc_inq_varid(ncid, "strn", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &strn[0][0]) );
  
  temutil::nc( nc_close(ncid) );

}

/** Writes arrays for variables with dimensions (Y, X, snowlayer) */
void RestartData::write_px_snow_vars(const std::string& fname, const int rowidx, const int colidx) {

  int ncid;
  temutil::nc( nc_open(fname.c_str(), NC_WRITE, &ncid) );

  // Check dimension presence? length? size?

  int cv; // a reusable variable handle
  
  size_t start[3];
  start[0] = rowidx;
  start[1] = colidx;
  start[2] = 0;

  size_t count[3];
  count[0] = 1;
  count[1] = 1;
  count[2] = MAX_SNW_LAY;
  
  temutil::nc( nc_inq_varid(ncid, "TSsnow", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &TSsnow[0]) );

  temutil::nc( nc_inq_varid(ncid, "DZsnow", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &DZsnow[0]) );
  temutil::nc( nc_inq_varid(ncid, "LIQsnow", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &LIQsnow[0]) );
  temutil::nc( nc_inq_varid(ncid, "RHOsnow", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &RHOsnow[0]) );
  temutil::nc( nc_inq_varid(ncid, "ICEsnow", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &ICEsnow[0]) );
  temutil::nc( nc_inq_varid(ncid, "AGEsnow", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &AGEsnow[0]) );

  temutil::nc( nc_close(ncid) );
}

/** Writes arrays for variables with dimensions (Y, X, rootlayer, pft) */
void RestartData::write_px_root_pft_vars(const std::string& fname, const int rowidx, const int colidx) {
  int ncid;
  temutil::nc( nc_open(fname.c_str(), NC_WRITE, &ncid) );

  int cv; // a reusable variable handle
  
  size_t start[4];
  start[0] = rowidx;
  start[1] = colidx;
  start[2] = 0;
  start[3] = 0;

  size_t count[4];
  count[0] = 1;
  count[1] = 1;
  count[2] = MAX_ROT_LAY;
  count[3] = NUM_PFT;
  
  temutil::nc( nc_inq_varid(ncid, "rootfrac", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &rootfrac[0][0]) );
  
  temutil::nc( nc_close(ncid) );

}

/** Writes arrays for variables with dimensions (Y, X, soillayer) */
void RestartData::write_px_soil_vars(const std::string& fname, const int rowidx, const int colidx) {

  int ncid;
  temutil::nc( nc_open(fname.c_str(), NC_WRITE, &ncid) );

  int cv; // a reusable variable handle
  
  size_t start[3];
  start[0] = rowidx;
  start[1] = colidx;
  start[2] = 0;

  size_t count[3];
  count[0] = 1;
  count[1] = 1;
  count[2] = MAX_SOI_LAY;
  
  temutil::nc( nc_inq_varid(ncid, "TYPEsoil", &cv) );
  temutil::nc( nc_put_vara_int(ncid, cv, start, count, &TYPEsoil[0]) );
  temutil::nc( nc_inq_varid(ncid, "AGEsoil", &cv) );
  temutil::nc( nc_put_vara_int(ncid, cv, start, count, &AGEsoil[0]) );
  temutil::nc( nc_inq_varid(ncid, "FROZENsoil", &cv) );
  temutil::nc( nc_put_vara_int(ncid, cv, start, count, &FROZENsoil[0]) );
  temutil::nc( nc_inq_varid(ncid, "TEXTUREsoil", &cv) );
  temutil::nc( nc_put_vara_int(ncid, cv, start, count, &TEXTUREsoil[0]) );
  
  temutil::nc( nc_inq_varid(ncid, "DZsoil", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &DZsoil[0]) );
  temutil::nc( nc_inq_varid(ncid, "TSsoil", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &TSsoil[0]) );
  temutil::nc( nc_inq_varid(ncid, "LIQsoil", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &LIQsoil[0]) );
  temutil::nc( nc_inq_varid(ncid, "FROZENFRACsoil", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &FROZENFRACsoil[0]) );
  temutil::nc( nc_inq_varid(ncid, "rawc", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &rawc[0]) );
  temutil::nc( nc_inq_varid(ncid, "soma", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &soma[0]) );
  temutil::nc( nc_inq_varid(ncid, "sompr", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &sompr[0]) );
  temutil::nc( nc_inq_varid(ncid, "somcr", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &somcr[0]) );
  temutil::nc( nc_inq_varid(ncid, "orgn", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &orgn[0]) );
  temutil::nc( nc_inq_varid(ncid, "avln", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &avln[0]) );

  temutil::nc( nc_close(ncid) );
}

/** Writes arrays of values for variables that have dimensions (Y, X, rocklayer). */
void RestartData::write_px_rock_vars(const std::string& fname, const int rowidx, const int colidx) {

  int ncid;
  temutil::nc( nc_open(fname.c_str(), NC_WRITE, &ncid) );

  // Check dimension presence? length? size?

  int cv; // a reusable variable handle
  
  size_t start[3];
  start[0] = rowidx;
  start[1] = colidx;
  start[2] = 0;

  size_t count[3];
  count[0] = 1;
  count[1] = 1;
  count[2] = MAX_ROC_LAY;
  
  temutil::nc( nc_inq_varid(ncid, "TSrock", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &TSrock[0]) );
  temutil::nc( nc_inq_varid(ncid, "DZrock", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &DZrock[0]) );

  temutil::nc( nc_close(ncid) );

}

/** Writes arrays of values for variables that have dimensions (Y, X, fronts). */
void RestartData::write_px_front_vars(const std::string& fname, const int rowidx, const int colidx) {

  int ncid;
  temutil::nc( nc_open(fname.c_str(), NC_WRITE, &ncid) );

  int cv; // a reusable variable handle
  
  size_t start[3];
  start[0] = rowidx;
  start[1] = colidx;
  start[2] = 0;

  size_t count[3];
  count[0] = 1;
  count[1] = 1;
  count[2] = MAX_NUM_FNT;
  
  temutil::nc( nc_inq_varid(ncid, "frontFT", &cv) );
  temutil::nc( nc_put_vara_int(ncid, cv, start, count, &frontFT[0]) );

  temutil::nc( nc_inq_varid(ncid, "frontZ", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &frontZ[0]) );

  temutil::nc( nc_close(ncid) );

}

/** Writes arrays for variables with dimensions (Y, X, prev<XX>, pft).
* Used for variables that need the previous 10 or 12 values.
*/
void RestartData::write_px_prev_pft_vars(const std::string& fname, const int rowidx, const int colidx) {
  int ncid;
  temutil::nc( nc_open(fname.c_str(), NC_WRITE, &ncid) );

  int cv; // a reusable variable handle

  size_t start[4];
  start[0] = rowidx;
  start[1] = colidx;
  start[2] = 0;
  start[3] = 0;

  size_t count[4];
  count[0] = 1;
  count[1] = 1;
  count[2] = 10;        // <-- previous 10 years?...
  count[3] = NUM_PFT;

  temutil::nc( nc_inq_varid(ncid, "toptA", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &toptA[0][0]) );
  temutil::nc( nc_inq_varid(ncid, "eetmxA", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &eetmxA[0][0]) );
  temutil::nc( nc_inq_varid(ncid, "growingttimeA", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &growingttimeA[0][0]) );
  temutil::nc( nc_inq_varid(ncid, "unnormleafmxA", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &unnormleafmxA[0][0]) );

  count[2] = 12;           // <-- previous 12 months?...
  temutil::nc( nc_inq_varid(ncid, "prvltrfcnA", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &prvltrfcnA[0][0]) );

  temutil::nc( nc_close(ncid) );

}

