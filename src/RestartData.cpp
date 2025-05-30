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

#include "../include/RestartData.h"
#include "../include/TEMUtilityFunctions.h"

#include "../include/TEMLogger.h"

extern src::severity_logger< severity_level > glg;

RestartData::RestartData() {
  reinitValue();
};

RestartData::~RestartData() {
};

#ifdef WITHMPI
MPI_Datatype RestartData::register_mpi_datatype() {

  // create types for all the dimensions in the RestartData object...
  const int elems_in_restartdata = 63;
  int counts[elems_in_restartdata] = {
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

    NUM_PFT_PART * NUM_PFT, // double vegC2N[NUM_PFT_PART][NUM_PFT];
    
    NUM_PFT, // double deadc[NUM_PFT];
    NUM_PFT, // double deadn[NUM_PFT];
    NUM_PFT, // double topt[NUM_PFT];            // yearly-evolved 'topt'
    NUM_PFT, // double eetmx[NUM_PFT];           // yearly max. month 'eet'
    NUM_PFT, // double unnormleaf[NUM_PFT];
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
    
    MAX_ROC_LAY, // double TSrock[MAX_ROC_LAY];
    MAX_ROC_LAY, // double DZrock[MAX_ROC_LAY];
    
    MAX_NUM_FNT, // double frontZ[MAX_NUM_FNT];
    MAX_NUM_FNT, // int frontFT[MAX_NUM_FNT];
    
    1, // double wdebrisc;
    
    MAX_SOI_LAY, // double rawc[MAX_SOI_LAY];
    MAX_SOI_LAY, // double soma[MAX_SOI_LAY];
    MAX_SOI_LAY, // double sompr[MAX_SOI_LAY];
    MAX_SOI_LAY, // double somcr[MAX_SOI_LAY];
    
    1, // double wdebrisn;
    MAX_SOI_LAY, // double orgn[MAX_SOI_LAY];
    
    MAX_SOI_LAY, // double avln[MAX_SOI_LAY];
    
    12 * MAX_SOI_LAY // double prvltrfcnA[12][MAX_SOI_LAY];   //previous 12-month litterfall (root death) input C/N ratios in each soil layer for adjusting 'kd'
  };
  MPI_Datatype old_types[elems_in_restartdata] = {
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
    MPI_DOUBLE, // double vegC2N[NUM_PFT_PART][NUM_PFT];
    MPI_DOUBLE, // double deadc[NUM_PFT];
    MPI_DOUBLE, // double deadn[NUM_PFT];
    MPI_DOUBLE, // double topt[NUM_PFT];
    MPI_DOUBLE, // double eetmx[NUM_PFT];
    MPI_DOUBLE, // double unnormleaf[NUM_PFT];
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
    MPI_DOUBLE, // double TSrock[MAX_ROC_LAY];
    MPI_DOUBLE, // double DZrock[MAX_ROC_LAY];
    MPI_DOUBLE, // double frontZ[MAX_NUM_FNT];
    MPI_INT, // int frontFT[MAX_NUM_FNT];
    MPI_DOUBLE, // double wdebrisc;
    MPI_DOUBLE, // double rawc[MAX_SOI_LAY];
    MPI_DOUBLE, // double soma[MAX_SOI_LAY];
    MPI_DOUBLE, // double sompr[MAX_SOI_LAY];
    MPI_DOUBLE, // double somcr[MAX_SOI_LAY];
    MPI_DOUBLE, // double wdebrisn;
    MPI_DOUBLE, // double orgn[MAX_SOI_LAY];
    MPI_DOUBLE, // double avln[MAX_SOI_LAY];
    MPI_DOUBLE // double prvltrfcnA[12][MAX_SOI_LAY];
  };
  MPI_Aint displacements[elems_in_restartdata] = {
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
    offsetof(RestartData, vegC2N),
    offsetof(RestartData, deadc),
    offsetof(RestartData, deadn),
    offsetof(RestartData, topt),
    offsetof(RestartData, eetmx),
    offsetof(RestartData, unnormleaf),
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
    offsetof(RestartData, TSrock),
    offsetof(RestartData, DZrock),
    offsetof(RestartData, frontZ),
    offsetof(RestartData, frontFT),
    offsetof(RestartData, wdebrisc),
    offsetof(RestartData, rawc),
    offsetof(RestartData, soma),
    offsetof(RestartData, sompr),
    offsetof(RestartData, somcr),
    offsetof(RestartData, wdebrisn),
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
  // atmosphere
  dsr         = MISSING_I;
  firea2sorgn = MISSING_D;
  // vegetation
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
      rootfrac[i][ip] = MISSING_D;
    }

    vegwater[ip] = MISSING_D;
    vegsnow[ip]  = MISSING_D;

    for (int i=0; i<NUM_PFT_PART; i++) {
      vegc[i][ip] = MISSING_D;
      strn[i][ip] = MISSING_D;
      vegC2N[i][ip] = MISSING_D;
    }

    labn[ip]      = MISSING_D;
    deadc[ip]     = MISSING_D;
    deadn[ip]     = MISSING_D;
    topt[ip]  = MISSING_D;
    eetmx[ip] = MISSING_D;
    unnormleaf[ip] = MISSING_D;
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
void RestartData::write_pixel_to_ncfile(const std::string& fname, const int rowidx, const int colidx) {

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

/** Checks a given variable against an extreme negative value. 
 *  FIX: should be more flexible
 */
template<typename T> void check_bounds(std::string var_name, T value){
  if(value<-4000){
    BOOST_LOG_SEV(glg, warn) << var_name << " is out of bounds: " << value;
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
    check_bounds("eetmx", eetmx[ii]);
    check_bounds("unnormleaf", unnormleaf[ii]);
    check_bounds("unnormleafmx", unnormleafmx[ii]);
    check_bounds("growingttime", growingttime[ii]);
    check_bounds("foliagemx", foliagemx[ii]);
    for(int jj=0; jj<NUM_PFT_PART; jj++){
      check_bounds("vegc", vegc[jj][ii]);
      check_bounds("strn", strn[jj][ii]);
      check_bounds("vegC2N", vegC2N[jj][ii]);
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
  for(int ii=0; ii<MAX_SOI_LAY; ii++){
    check_bounds("DZsoil", DZsoil[ii]);
    check_bounds("TYPEsoil", TYPEsoil[ii]);
    check_bounds("AGEsoil", AGEsoil[ii]);
    check_bounds("TSsoil", TSsoil[ii]);
    check_bounds("LIQsoil", LIQsoil[ii]);
    check_bounds("ICEsoil", ICEsoil[ii]);
    check_bounds("FROZENsoil", FROZENsoil[ii]);
    check_bounds("FROZENFRACsoil", FROZENFRACsoil[ii]);
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
 
  BOOST_LOG_SEV(glg, debug) << "Opening restart: " << fname;
 
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

  temutil::nc( nc_close(ncid) );

  // Also works to use the nc_get_vara_TYPE(...) variation
  //size_t count[2];
  //count[0] = 1;
  //count[1] = 1;
  //temutil::nc( nc_get_vara_int(ncid, cv, start, count, &dsr) );   // write an array
}

/** Reads arrays of values for variables that have dimensions (Y, X, pft). */
void RestartData::read_px_pft_vars(const std::string& fname, const int rowidx, const int colidx) {

  BOOST_LOG_SEV(glg, debug) << "Opening restart: " << fname;

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
  
  temutil::nc( nc_inq_varid(ncid, "vegcov", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &vegcov[0]) );
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
  temutil::nc( nc_inq_varid(ncid, "unnormleaf", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &unnormleaf[0]) );
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

  BOOST_LOG_SEV(glg, debug) << "Opening restart: " << fname;

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

  temutil::nc( nc_inq_varid(ncid, "vegC2N", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &vegC2N[0][0]) );
  
  temutil::nc( nc_close(ncid) );

}

/**  Reads arrays for variables with dimensions (Y, X, snowlayer) */
void RestartData::read_px_snow_vars(const std::string& fname, const int rowidx, const int colidx) {

  BOOST_LOG_SEV(glg, debug) << "Opening restart: " << fname;

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

  BOOST_LOG_SEV(glg, debug) << "Opening restart: " << fname;

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

  BOOST_LOG_SEV(glg, debug) << "Opening restart: " << fname;

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

  temutil::nc( nc_inq_varid(ncid, "DZsoil", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &DZsoil[0]) );
  temutil::nc( nc_inq_varid(ncid, "TSsoil", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &TSsoil[0]) );
  temutil::nc( nc_inq_varid(ncid, "LIQsoil", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &LIQsoil[0]) );
  temutil::nc( nc_inq_varid(ncid, "ICEsoil", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &ICEsoil[0]) );
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

  BOOST_LOG_SEV(glg, debug) << "Opening restart: " << fname;

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

  BOOST_LOG_SEV(glg, debug) << "Opening restart: " << fname;

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

/**  Reads arrays for variables with dimensions (Y, X, prev<XX>, pft). Used for
* variables that need the previous 10 or 12 values. 
*
* Note: The name of this function is somewhat misleading as it also handles one
* soil variable!
*/
void RestartData::read_px_prev_pft_vars(const std::string& fname, const int rowidx, const int colidx) {

  BOOST_LOG_SEV(glg, debug) << "Opening restart: " << fname;

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

  // Adjust offsets for use with monthly soil variable.
  count[2] = 12;        // <-- previous 12 months
  count[3] = MAX_SOI_LAY;

  temutil::nc( nc_inq_varid(ncid, "prvltrfcnA", &cv) );
  temutil::nc( nc_get_vara_double(ncid, cv, start, count, &prvltrfcnA[0][0]) );


  temutil::nc( nc_close(ncid) );

}


/** Creates (overwrites) an empty restart file. */
void RestartData::create_empty_file(const std::string& fname,
    const int ysize, const int xsize) {

  BOOST_LOG_SEV(glg, debug) << "Opening new file: "<<fname<<" with 'NC_CLOBBER'";
  int ncid;

#ifdef WITHMPI
  BOOST_LOG_SEV(glg, debug) << "Creating new parallel restart file: "<<fname;
  temutil::nc( nc_create_par(fname.c_str(), NC_CLOBBER|NC_NETCDF4|NC_MPIIO, MPI_COMM_WORLD, MPI_INFO_NULL, &ncid) );
#else
  temutil::nc( nc_create(fname.c_str(), NC_CLOBBER, &ncid) );
#endif

  //int old_fill_mode;
  //temutil::nc( nc_set_fill(ncid, NC_NOFILL, &old_fill_mode) );
  //BOOST_LOG_SEV(glg, debug) << "The old fill mode was: " << old_fill_mode;

  // Define handles for dimensions
  int yD;
  int xD;
  int pftD;
  int pftpartD;
  int snowlayerD;
  int rootlayerD;
  int soillayerD;
  int rocklayerD;
  int frontsD;
  int prevtenD;
  int prevtwelveD;

  BOOST_LOG_SEV(glg, debug) << "Creating dimensions...";
  temutil::nc( nc_def_dim(ncid, "Y", ysize, &yD) );
  temutil::nc( nc_def_dim(ncid, "X", xsize, &xD) );
//  temutil::nc( nc_def_dim(ncid, "pft", 10, &pftD) );
//  temutil::nc( nc_def_dim(ncid, "pftpart", 3, &pftpartD) );
//  temutil::nc( nc_def_dim(ncid, "snowlayer", 6, &snowlayerD) );
//  temutil::nc( nc_def_dim(ncid, "rootlayer", 10, &rootlayerD) );
//  temutil::nc( nc_def_dim(ncid, "soillayer", 23, &soillayerD) );
//  temutil::nc( nc_def_dim(ncid, "rocklayer", 5, &rocklayerD) );
//  temutil::nc( nc_def_dim(ncid, "fronts", 10, &frontsD) );
//  temutil::nc( nc_def_dim(ncid, "prevten", 10, &prevtenD) );
//  temutil::nc( nc_def_dim(ncid, "prevtwelve", 12, &prevtwelveD) );

  temutil::nc( nc_def_dim(ncid, "pft", NUM_PFT, &pftD) );
  temutil::nc( nc_def_dim(ncid, "pftpart", NUM_PFT_PART, &pftpartD) );
  temutil::nc( nc_def_dim(ncid, "snowlayer", MAX_SNW_LAY, &snowlayerD) );
  temutil::nc( nc_def_dim(ncid, "rootlayer", MAX_ROT_LAY, &rootlayerD) );
  temutil::nc( nc_def_dim(ncid, "soillayer", MAX_SOI_LAY, &soillayerD) );
  temutil::nc( nc_def_dim(ncid, "rocklayer", MAX_ROC_LAY, &rocklayerD) );
  temutil::nc( nc_def_dim(ncid, "fronts", 10, &frontsD) );
  temutil::nc( nc_def_dim(ncid, "prevten", 10, &prevtenD) );
  temutil::nc( nc_def_dim(ncid, "prevtwelve", 12, &prevtwelveD) );

//  BOOST_LOG_SEV(glg, monitor) << " NUM_PFT = " << NUM_PFT ;
//  BOOST_LOG_SEV(glg, monitor) << " NUM_PFT_PART = " << NUM_PFT_PART ;
//  BOOST_LOG_SEV(glg, monitor) << " MAX_ROT_LAY = " << MAX_ROT_LAY ;
//  BOOST_LOG_SEV(glg, monitor) << " MAX_SNW_LAY = " << MAX_SNW_LAY ;
//  BOOST_LOG_SEV(glg, monitor) << " MAX_SOI_LAY = " << MAX_SOI_LAY ;
//  BOOST_LOG_SEV(glg, monitor) << " MAX_ROC_LAY = " << MAX_ROC_LAY ;


  // Setup arrays holding dimids for different "types" of variables
  // --> will re-arrange these later to define variables with different dims
  int vartype2D_dimids[2];
  vartype2D_dimids[0] = yD;
  vartype2D_dimids[1] = xD;

  int vartype3D_dimids[3];
  vartype3D_dimids[0] = yD;
  vartype3D_dimids[1] = xD;
  vartype3D_dimids[2] = pftD;

  int vartype4D_dimids[4];
  vartype4D_dimids[0] = yD;
  vartype4D_dimids[1] = xD;
  vartype4D_dimids[2] = pftpartD;
  vartype4D_dimids[3] = pftD;

  // Setup 2D vars, integer
  int dsrV;
  int numslV;
  int numsnwlV;
  int rtfrozendaysV;
  int rtunfrozendaysV;
  int yrsdistV;
  temutil::nc( nc_def_var(ncid, "dsr", NC_INT, 2, vartype2D_dimids, &dsrV) );
  temutil::nc( nc_put_att_int(ncid, dsrV, "_FillValue", NC_INT, 1, &MISSING_I) );
  temutil::nc( nc_def_var(ncid, "numsl", NC_INT, 2, vartype2D_dimids, &numslV) );
  temutil::nc( nc_put_att_int(ncid, numslV, "_FillValue", NC_INT, 1, &MISSING_I) );
  temutil::nc( nc_def_var(ncid, "numsnwl", NC_INT, 2, vartype2D_dimids, &numsnwlV) );
  temutil::nc( nc_put_att_int(ncid, numsnwlV, "_FillValue", NC_INT, 1, &MISSING_I) );
  temutil::nc( nc_def_var(ncid, "rtfrozendays", NC_INT, 2, vartype2D_dimids, &rtfrozendaysV) );
  temutil::nc( nc_put_att_int(ncid, rtfrozendaysV, "_FillValue", NC_INT, 1, &MISSING_I) );
  temutil::nc( nc_def_var(ncid, "rtunfrozendays", NC_INT, 2, vartype2D_dimids, &rtunfrozendaysV) );
  temutil::nc( nc_put_att_int(ncid, rtunfrozendaysV, "_FillValue", NC_INT, 1, &MISSING_I) );
  temutil::nc( nc_def_var(ncid, "yrsdist", NC_INT, 2, vartype2D_dimids, &yrsdistV) );
  temutil::nc( nc_put_att_int(ncid, yrsdistV, "_FillValue", NC_INT, 1, &MISSING_I) );

  // Setup 2D vars, double
  int firea2sorgnV;
  int snwextramasV;
  int monthsfrozenV;
  int watertabV;
  int wdebriscV;
  int wdebrisnV;
  temutil::nc( nc_def_var(ncid, "firea2sorgn", NC_DOUBLE, 2, vartype2D_dimids, &firea2sorgnV) );
  temutil::nc( nc_put_att_double(ncid, firea2sorgnV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "snwextramass", NC_DOUBLE, 2, vartype2D_dimids, &snwextramasV) );
  temutil::nc( nc_put_att_double(ncid, snwextramasV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "monthsfrozen", NC_DOUBLE, 2, vartype2D_dimids, &monthsfrozenV) );
  temutil::nc( nc_put_att_double(ncid, monthsfrozenV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "watertab", NC_DOUBLE, 2, vartype2D_dimids, &watertabV) );
  temutil::nc( nc_put_att_double(ncid, watertabV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "wdebrisc", NC_DOUBLE, 2, vartype2D_dimids, &wdebriscV) );
  temutil::nc( nc_put_att_double(ncid, wdebriscV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "wdebrisn", NC_DOUBLE, 2, vartype2D_dimids, &wdebrisnV) );
  temutil::nc( nc_put_att_double(ncid, wdebrisnV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );

  // Setup 3D vars, integer
  int ifwoodyV;
  int ifdeciwoodyV;
  int ifperenialV;
  int nonvascularV;
  int vegageV;
  temutil::nc( nc_def_var(ncid, "ifwoody", NC_INT, 3, vartype3D_dimids, &ifwoodyV) );
  temutil::nc( nc_put_att_int(ncid, ifwoodyV, "_FillValue", NC_INT, 1, &MISSING_I) );
  temutil::nc( nc_def_var(ncid, "ifdeciwoody", NC_INT, 3, vartype3D_dimids, &ifdeciwoodyV) );
  temutil::nc( nc_put_att_int(ncid, ifdeciwoodyV, "_FillValue", NC_INT, 1, &MISSING_I) );
  temutil::nc( nc_def_var(ncid, "ifperenial", NC_INT, 3, vartype3D_dimids, &ifperenialV) );
  temutil::nc( nc_put_att_int(ncid, ifperenialV, "_FillValue", NC_INT, 1, &MISSING_I) );
  temutil::nc( nc_def_var(ncid, "nonvascular", NC_INT, 3, vartype3D_dimids, &nonvascularV) );
  temutil::nc( nc_put_att_int(ncid, nonvascularV, "_FillValue", NC_INT, 1, &MISSING_I) );
  temutil::nc( nc_def_var(ncid, "vegage", NC_INT, 3, vartype3D_dimids, &vegageV) );
  temutil::nc( nc_put_att_int(ncid, vegageV, "_FillValue", NC_INT, 1, &MISSING_I) );

  // Setup 3D vars, double
  int vegcovV;
  int laiV;
  int vegwaterV;
  int vegsnowV;
  int labnV;
  int deadcV;
  int deadnV;
  int toptV;
  int eetmxV;
  int unnormleafV;
  int unnormleafmxV;
  int growingttimeV;
  int foliagemxV;
  temutil::nc( nc_def_var(ncid, "vegcov", NC_DOUBLE, 3, vartype3D_dimids, &vegcovV) );
  temutil::nc( nc_put_att_double(ncid, vegcovV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "lai", NC_DOUBLE, 3, vartype3D_dimids, &laiV) );
  temutil::nc( nc_put_att_double(ncid, laiV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "vegwater", NC_DOUBLE, 3, vartype3D_dimids, &vegwaterV) );
  temutil::nc( nc_put_att_double(ncid, vegwaterV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "vegsnow", NC_DOUBLE, 3, vartype3D_dimids, &vegsnowV) );
  temutil::nc( nc_put_att_double(ncid, vegsnowV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "labn", NC_DOUBLE, 3, vartype3D_dimids, &labnV) );
  temutil::nc( nc_put_att_double(ncid, labnV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "deadc", NC_DOUBLE, 3, vartype3D_dimids, &deadcV) );
  temutil::nc( nc_put_att_double(ncid, deadcV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "deadn", NC_DOUBLE, 3, vartype3D_dimids, &deadnV) );
  temutil::nc( nc_put_att_double(ncid, deadnV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "topt", NC_DOUBLE, 3, vartype3D_dimids, &toptV) );
  temutil::nc( nc_put_att_double(ncid, toptV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "eetmx", NC_DOUBLE, 3, vartype3D_dimids, &eetmxV) );
  temutil::nc( nc_put_att_double(ncid, eetmxV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "unnormleaf", NC_DOUBLE, 3, vartype3D_dimids, &unnormleafV) );
  temutil::nc( nc_put_att_double(ncid, unnormleafV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "unnormleafmx", NC_DOUBLE, 3, vartype3D_dimids, &unnormleafmxV) );
  temutil::nc( nc_put_att_double(ncid, unnormleafmxV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "growingttime", NC_DOUBLE, 3, vartype3D_dimids, &growingttimeV) );
  temutil::nc( nc_put_att_double(ncid, growingttimeV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "foliagemx", NC_DOUBLE, 3, vartype3D_dimids, &foliagemxV) );
  temutil::nc( nc_put_att_double(ncid, foliagemxV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );

  // Setup 4D vars, double
  int vegcV;
  int strnV;
  int vegC2NV;
  temutil::nc( nc_def_var(ncid, "vegc", NC_DOUBLE, 4, vartype4D_dimids, &vegcV) );
  temutil::nc( nc_put_att_double(ncid, vegcV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "strn", NC_DOUBLE, 4, vartype4D_dimids, &strnV) );
  temutil::nc( nc_put_att_double(ncid, strnV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "vegC2N", NC_DOUBLE, 4, vartype4D_dimids, &vegC2NV) );
  temutil::nc( nc_put_att_double(ncid, vegC2NV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );

  // re-arrange dims in vartype
  vartype3D_dimids[0] = yD;
  vartype3D_dimids[1] = xD;
  vartype3D_dimids[2] = soillayerD;

  // Setup 3D vars, integer
  int FROZENsoilV;
  int TYPEsoilV;
  int AGEsoilV;
  temutil::nc( nc_def_var(ncid, "FROZENsoil", NC_INT, 3, vartype3D_dimids, &FROZENsoilV) );
  temutil::nc( nc_put_att_int(ncid, FROZENsoilV, "_FillValue", NC_INT, 1, &MISSING_I) );
  temutil::nc( nc_def_var(ncid, "TYPEsoil", NC_INT, 3, vartype3D_dimids, &TYPEsoilV) );
  temutil::nc( nc_put_att_int(ncid, TYPEsoilV, "_FillValue", NC_INT, 1, &MISSING_I) );
  temutil::nc( nc_def_var(ncid, "AGEsoil", NC_INT, 3, vartype3D_dimids, &AGEsoilV) );
  temutil::nc( nc_put_att_int(ncid, AGEsoilV, "_FillValue", NC_INT, 1, &MISSING_I) );

  // Setup 3D vars, double
  int TSsoilV;
  int DZsoilV;
  int LIQsoilV;
  int ICEsoilV;
  int FROZENFRACsoilV;
  int rawcV;
  int somaV;
  int somprV;
  int somcrV;
  int orgnV;
  int avlnV;
  temutil::nc( nc_def_var(ncid, "TSsoil", NC_DOUBLE, 3, vartype3D_dimids, &TSsoilV) );
  temutil::nc( nc_put_att_double(ncid, TSsoilV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "DZsoil", NC_DOUBLE, 3, vartype3D_dimids, &DZsoilV) );
  temutil::nc( nc_put_att_double(ncid, DZsoilV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "LIQsoil", NC_DOUBLE, 3, vartype3D_dimids, &LIQsoilV) );
  temutil::nc( nc_put_att_double(ncid, LIQsoilV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "ICEsoil", NC_DOUBLE, 3, vartype3D_dimids, &ICEsoilV) );
  temutil::nc( nc_put_att_double(ncid, ICEsoilV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "FROZENFRACsoil", NC_DOUBLE, 3, vartype3D_dimids, &FROZENFRACsoilV) );
  temutil::nc( nc_put_att_double(ncid, FROZENFRACsoilV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "rawc", NC_DOUBLE, 3, vartype3D_dimids, &rawcV) );
  temutil::nc( nc_put_att_double(ncid, rawcV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "soma", NC_DOUBLE, 3, vartype3D_dimids, &somaV) );
  temutil::nc( nc_put_att_double(ncid, somaV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "sompr", NC_DOUBLE, 3, vartype3D_dimids, &somprV) );
  temutil::nc( nc_put_att_double(ncid, somprV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "somcr", NC_DOUBLE, 3, vartype3D_dimids, &somcrV) );
  temutil::nc( nc_put_att_double(ncid, somcrV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "orgn", NC_DOUBLE, 3, vartype3D_dimids, &orgnV) );
  temutil::nc( nc_put_att_double(ncid, orgnV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "avln", NC_DOUBLE, 3, vartype3D_dimids, &avlnV) );
  temutil::nc( nc_put_att_double(ncid, avlnV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );

  // %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  // NOTE: Seems odd, that these variables are defined in terms of soillayer
  // dimension and not the snowlayer dimension??? If this changes, will have
  // to update the custom MPI Type! (And for consistency, update the
  // create_region_inpuy.py script, although the --crtf-only feature will
  // probably be deprecated after adding the ability to create these files in
  // the C++ code.
  // The old files that we've been using prior to 11/2016 seem to have been
  // using number of soil layers, so I left it at that for now....
  // NOTE: As of spring 2023 I am not sure how much of this applies. The
  // `fix_restart` branch may have addressed this in part; not sure if it fixed
  // the MPI type?
  // %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

  // re-arrange dims in vartype
  vartype3D_dimids[0] = yD;
  vartype3D_dimids[1] = xD;
  vartype3D_dimids[2] = snowlayerD;
 
  int TSsnowV;
  int DZsnowV;
  int LIQsnowV;
  int RHOsnowV;
  int ICEsnowV;
  int AGEsnowV;
  temutil::nc( nc_def_var(ncid, "TSsnow", NC_DOUBLE, 3, vartype3D_dimids, &TSsnowV) );
  temutil::nc( nc_put_att_double(ncid, TSsnowV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "DZsnow", NC_DOUBLE, 3, vartype3D_dimids, &DZsnowV) );
  temutil::nc( nc_put_att_double(ncid, DZsnowV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "LIQsnow", NC_DOUBLE, 3, vartype3D_dimids, &LIQsnowV) );
  temutil::nc( nc_put_att_double(ncid, LIQsnowV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "RHOsnow", NC_DOUBLE, 3, vartype3D_dimids, &RHOsnowV) );
  temutil::nc( nc_put_att_double(ncid, RHOsnowV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "ICEsnow", NC_DOUBLE, 3, vartype3D_dimids, &ICEsnowV) );
  temutil::nc( nc_put_att_double(ncid, ICEsnowV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "AGEsnow", NC_DOUBLE, 3, vartype3D_dimids, &AGEsnowV) );
  temutil::nc( nc_put_att_double(ncid, AGEsnowV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );

  // re-arrange dims in vartype
  vartype3D_dimids[0] = yD;
  vartype3D_dimids[1] = xD;
  vartype3D_dimids[2] = rocklayerD;

  int TSrockV;
  int DZrockV;
  temutil::nc( nc_def_var(ncid, "TSrock", NC_DOUBLE, 3, vartype3D_dimids, &TSrockV) );
  temutil::nc( nc_put_att_double(ncid, TSrockV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "DZrock", NC_DOUBLE, 3, vartype3D_dimids, &DZrockV) );
  temutil::nc( nc_put_att_double(ncid, DZrockV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );


  // re-arrange dims in vartype
  vartype3D_dimids[0] = yD;
  vartype3D_dimids[1] = xD;
  vartype3D_dimids[2] = frontsD;

  int frontFTV;
  int frontZV;
  temutil::nc( nc_def_var(ncid, "frontFT", NC_INT, 3, vartype3D_dimids, &frontFTV) );
  temutil::nc( nc_put_att_int(ncid, frontFTV, "_FillValue", NC_INT, 1, &MISSING_I) );
  temutil::nc( nc_def_var(ncid, "frontZ", NC_DOUBLE, 3, vartype3D_dimids, &frontZV) );
  temutil::nc( nc_put_att_double(ncid, frontZV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );

  // re-arrange dims in vartype
  vartype4D_dimids[0] = yD;
  vartype4D_dimids[1] = xD;
  vartype4D_dimids[2] = rootlayerD;
  vartype4D_dimids[3] = pftD;

  int rootfracV;
  temutil::nc( nc_def_var(ncid, "rootfrac", NC_DOUBLE, 4, vartype4D_dimids, &rootfracV) );
  temutil::nc( nc_put_att_double(ncid, rootfracV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );


  // re-arrange dims in vartype
  vartype4D_dimids[0] = yD;
  vartype4D_dimids[1] = xD;
  vartype4D_dimids[2] = prevtenD;
  vartype4D_dimids[3] = pftD;

  int toptAV;
  int eetmxAV;
  int unnormleafmxAV;
  int growingttimeAV;
  temutil::nc( nc_def_var(ncid, "toptA", NC_DOUBLE, 4, vartype4D_dimids, &toptAV) );
  temutil::nc( nc_put_att_double(ncid, toptAV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "eetmxA", NC_DOUBLE, 4, vartype4D_dimids, &eetmxAV) );
  temutil::nc( nc_put_att_double(ncid, eetmxAV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "unnormleafmxA", NC_DOUBLE, 4, vartype4D_dimids, &unnormleafmxAV) );
  temutil::nc( nc_put_att_double(ncid, unnormleafmxAV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );
  temutil::nc( nc_def_var(ncid, "growingttimeA", NC_DOUBLE, 4, vartype4D_dimids, &growingttimeAV) );
  temutil::nc( nc_put_att_double(ncid, growingttimeAV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );

  // re-arrange dims in vartype
  vartype4D_dimids[0] = yD;
  vartype4D_dimids[1] = xD;
  vartype4D_dimids[2] = prevtwelveD;
  vartype4D_dimids[3] = soillayerD;

  int prvltrfcnAV;
  temutil::nc( nc_def_var(ncid, "prvltrfcnA", NC_DOUBLE, 4, vartype4D_dimids, &prvltrfcnAV) );
  temutil::nc( nc_put_att_double(ncid, prvltrfcnAV, "_FillValue", NC_DOUBLE, 1, &MISSING_D) );

  /* Global Attributes */
  temutil::nc( nc_put_att_text(ncid, NC_GLOBAL, "Git_SHA", strlen(GIT_SHA), GIT_SHA ) );

  /* End Define Mode (not strictly necessary for netcdf 4) */
  BOOST_LOG_SEV(glg, debug) << "Trying to leaving 'define mode'...";
  try {
    temutil::nc( nc_enddef(ncid) );
  } catch (const temutil::NetCDFDefineModeException& e) {
    BOOST_LOG_SEV(glg, info) << "Error ending define mode: " << e.what();
  }

  /* Close file. */
  BOOST_LOG_SEV(glg, debug) << "Closing new file...";
  temutil::nc( nc_close(ncid) );

}


/** Writes single values for variables have dimensions (Y, X).*/
void RestartData::write_px_vars(const std::string& fname, const int rowidx, const int colidx) {
  
  BOOST_LOG_SEV(glg, debug) << "Opening restart: " << fname;
  int ncid;

#ifdef WITHMPI
  temutil::nc( nc_open_par(fname.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
#else
  temutil::nc( nc_open(fname.c_str(), NC_WRITE, &ncid) );
#endif

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

  temutil::nc( nc_close(ncid) );

  // Also works to use the nc_put_vara_TYPE(...) variation
  //size_t count[2];
  //count[0] = 1;
  //count[1] = 1;
  //temutil::nc( nc_put_vara_int(ncid, cv, start, count, &dsr) );   // write an array
}

/** Writes arrays of values for variables that have dimensions (Y, X, pft). */
void RestartData::write_px_pft_vars(const std::string& fname, const int rowidx, const int colidx) {

  BOOST_LOG_SEV(glg, debug) << "Opening restart: " << fname;
  int ncid;

#ifdef WITHMPI
  temutil::nc( nc_open_par(fname.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
#else
  temutil::nc( nc_open(fname.c_str(), NC_WRITE, &ncid) );
#endif

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
  
  temutil::nc( nc_inq_varid(ncid, "vegcov", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &vegcov[0]) );
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
  temutil::nc( nc_inq_varid(ncid, "unnormleaf", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &unnormleaf[0]) );
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

  BOOST_LOG_SEV(glg, debug) << "Opening restart: " << fname;
  int ncid;

#ifdef WITHMPI
  temutil::nc( nc_open_par(fname.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
#else
  temutil::nc( nc_open(fname.c_str(), NC_WRITE, &ncid) );
#endif

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

  temutil::nc( nc_inq_varid(ncid, "vegC2N", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &vegC2N[0][0]) );
  
  temutil::nc( nc_close(ncid) );

}

/** Writes arrays for variables with dimensions (Y, X, snowlayer) */
void RestartData::write_px_snow_vars(const std::string& fname, const int rowidx, const int colidx) {

  BOOST_LOG_SEV(glg, debug) << "Opening restart: " << fname;
  int ncid;

#ifdef WITHMPI
  temutil::nc( nc_open_par(fname.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
#else
  temutil::nc( nc_open(fname.c_str(), NC_WRITE, &ncid) );
#endif

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

  BOOST_LOG_SEV(glg, debug) << "Opening restart: " << fname;
  int ncid;

#ifdef WITHMPI
  temutil::nc( nc_open_par(fname.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
#else
  temutil::nc( nc_open(fname.c_str(), NC_WRITE, &ncid) );
#endif

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

  BOOST_LOG_SEV(glg, debug) << "Opening restart: " << fname;
  int ncid;

#ifdef WITHMPI
  temutil::nc( nc_open_par(fname.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
#else
  temutil::nc( nc_open(fname.c_str(), NC_WRITE, &ncid) );
#endif

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
  
  temutil::nc( nc_inq_varid(ncid, "DZsoil", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &DZsoil[0]) );
  temutil::nc( nc_inq_varid(ncid, "TSsoil", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &TSsoil[0]) );
  temutil::nc( nc_inq_varid(ncid, "LIQsoil", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &LIQsoil[0]) );
  temutil::nc( nc_inq_varid(ncid, "ICEsoil", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &ICEsoil[0]) );
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

  BOOST_LOG_SEV(glg, debug) << "Opening restart: " << fname;
  int ncid;

#ifdef WITHMPI
  temutil::nc( nc_open_par(fname.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
#else
  temutil::nc( nc_open(fname.c_str(), NC_WRITE, &ncid) );
#endif

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

  BOOST_LOG_SEV(glg, debug) << "Opening restart: " << fname;
  int ncid;

#ifdef WITHMPI
  temutil::nc( nc_open_par(fname.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
#else
  temutil::nc( nc_open(fname.c_str(), NC_WRITE, &ncid) );
#endif

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
*
* Note: This function name is somewhat misleading as it also handles one soil 
* variable!
*/
void RestartData::write_px_prev_pft_vars(const std::string& fname, const int rowidx, const int colidx) {

  BOOST_LOG_SEV(glg, debug) << "Opening restart: " << fname;
  int ncid;

#ifdef WITHMPI
  temutil::nc( nc_open_par(fname.c_str(), NC_WRITE|NC_MPIIO, MPI_COMM_SELF, MPI_INFO_NULL, &ncid) );
#else
  temutil::nc( nc_open(fname.c_str(), NC_WRITE, &ncid) );
#endif

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

  // Adjust offsets for working with the a monthly soil variable.
  count[2] = 12;        // <-- previous 10 years?...
  count[3] = MAX_SOI_LAY;

  temutil::nc( nc_inq_varid(ncid, "prvltrfcnA", &cv) );
  temutil::nc( nc_put_vara_double(ncid, cv, start, count, &prvltrfcnA[0][0]) );

  temutil::nc( nc_close(ncid) );

}


/**Writes this RestartData to the log stream. Should be replaced with templating eventually.*/
void RestartData::restartdata_to_log(){
  //PFT and PFT part loops are repeated in order to keep variable
  //types together for initial debugging. This may change in the future.

  BOOST_LOG_SEV(glg, debug) << "***** RESTARTDATA *****";

  //atm
  BOOST_LOG_SEV(glg, debug) << "dsr: " << dsr;
  BOOST_LOG_SEV(glg, debug) << "firea2sorgn: " << firea2sorgn;

  //vegetation
  BOOST_LOG_SEV(glg, debug) << "yrsdist: " << yrsdist;

  for(int ii=0; ii<NUM_PFT; ii++){
    BOOST_LOG_SEV(glg, debug) << "ifwoody[" << ii << "]: " << ifwoody[ii];
    BOOST_LOG_SEV(glg, debug) << "ifdeciwoody[" << ii << "]: " << ifdeciwoody[ii];
    BOOST_LOG_SEV(glg, debug) << "ifperenial[" << ii << "]: " << ifperenial[ii];
    BOOST_LOG_SEV(glg, debug) << "nonvascular[" << ii << "]: " << nonvascular[ii];
    BOOST_LOG_SEV(glg, debug) << "vegage[" << ii << "]: " << vegage[ii];
    BOOST_LOG_SEV(glg, debug) << "vegcov[" << ii << "]: " << vegcov[ii];
    BOOST_LOG_SEV(glg, debug) << "lai[" << ii << "]: " << lai[ii];
    BOOST_LOG_SEV(glg, debug) << "vegwater[" << ii << "]: " << vegwater[ii];
    BOOST_LOG_SEV(glg, debug) << "vegsnow[" << ii << "]: " << vegsnow[ii];
    BOOST_LOG_SEV(glg, debug) << "labn[" << ii << "]: " << labn[ii];
    BOOST_LOG_SEV(glg, debug) << "deadc[" << ii << "]: " << deadc[ii];
    BOOST_LOG_SEV(glg, debug) << "deadn[" << ii << "]: " << deadn[ii];
    BOOST_LOG_SEV(glg, debug) << "topt[" << ii << "]: " << topt[ii];
    BOOST_LOG_SEV(glg, debug) << "eetmx[" << ii << "]: " << eetmx[ii];
    BOOST_LOG_SEV(glg, debug) << "unnormleaf[" << ii << "]: " << unnormleaf[ii];
    BOOST_LOG_SEV(glg, debug) << "unnormleafmx[" << ii << "]: " << unnormleafmx[ii];
    BOOST_LOG_SEV(glg, debug) << "growingttime[" << ii << "]: " << growingttime[ii];
    BOOST_LOG_SEV(glg, debug) << "foliagemx[" << ii << "]: " << foliagemx[ii];

    for(int jj=0; jj<MAX_ROT_LAY; jj++){
      BOOST_LOG_SEV(glg, debug) << "rootfrac[" << jj << "][" << ii << "]: " << rootfrac[jj][ii];
    }

    for(int jj=0; jj<NUM_PFT_PART; jj++){
      BOOST_LOG_SEV(glg, debug) << "vegc[" << jj << "][" << ii << "]: " << vegc[jj][ii];
      BOOST_LOG_SEV(glg, debug) << "strn[" << jj << "][" << ii << "]: " << strn[jj][ii];
      BOOST_LOG_SEV(glg, debug) << "vegC2N[" << jj << "][" << ii << "]: " << vegC2N[jj][ii];
    }

    for(int jj=0; jj<10; jj++){
      BOOST_LOG_SEV(glg, debug) << "toptA[" << jj << "][" << ii << "]: " << toptA[jj][ii];
      BOOST_LOG_SEV(glg, debug) << "eetmxA[" << jj << "][" << ii << "]: " << eetmxA[jj][ii];
      BOOST_LOG_SEV(glg, debug) << "unnormleafmxA[" << jj << "][" << ii << "]: " << unnormleafmxA[jj][ii];
      BOOST_LOG_SEV(glg, debug) << "growingttimeA[" << jj << "][" << ii << "]: " << growingttimeA[jj][ii];
    }

  }

  //snow
  BOOST_LOG_SEV(glg, debug) << "numsnwl: " << numsnwl;
  BOOST_LOG_SEV(glg, debug) << "snwextramass: " << snwextramass;
  for(int ii; ii<MAX_SNW_LAY; ii++){
    BOOST_LOG_SEV(glg, debug) << "TSsnow[" << ii << "]: " << TSsnow[ii];
    BOOST_LOG_SEV(glg, debug) << "DZsnow[" << ii << "]: " << DZsnow[ii];
    BOOST_LOG_SEV(glg, debug) << "LIQsnow[" << ii << "]: " << LIQsnow[ii];
    BOOST_LOG_SEV(glg, debug) << "RHOsnow[" << ii << "]: " << RHOsnow[ii];
    BOOST_LOG_SEV(glg, debug) << "ICEsnow[" << ii << "]: " << ICEsnow[ii];
    BOOST_LOG_SEV(glg, debug) << "AGEsnow[" << ii << "]: " << AGEsnow[ii];
  }

  //ground/soil
  BOOST_LOG_SEV(glg, debug) << "numsl: " << numsl;
  BOOST_LOG_SEV(glg, debug) << "monthsfrozen: " << monthsfrozen;
  BOOST_LOG_SEV(glg, debug) << "rtfrozendays: " << rtfrozendays;
  BOOST_LOG_SEV(glg, debug) << "rtunfrozendays: " << rtunfrozendays;
  BOOST_LOG_SEV(glg, debug) << "watertab: " << watertab;
  BOOST_LOG_SEV(glg, debug) << "wdebrisc: " << wdebrisc;
  BOOST_LOG_SEV(glg, debug) << "wdebrisn: " << wdebrisn;

  for(int ii=0; ii<MAX_SOI_LAY; ii++){
    BOOST_LOG_SEV(glg, debug) << "DZsoil[" << ii << "]: " << DZsoil[ii];
    BOOST_LOG_SEV(glg, debug) << "TYPEsoil[" << ii << "]: " << TYPEsoil[ii];
    BOOST_LOG_SEV(glg, debug) << "AGEsoil[" << ii << "]: " << AGEsoil[ii];
    BOOST_LOG_SEV(glg, debug) << "TSsoil[" << ii << "]: " << TSsoil[ii];
    BOOST_LOG_SEV(glg, debug) << "LIQsoil[" << ii << "]: " << LIQsoil[ii];
    BOOST_LOG_SEV(glg, debug) << "ICEsoil[" << ii << "]: " << ICEsoil[ii];
    BOOST_LOG_SEV(glg, debug) << "FROZENsoil[" << ii << "]: " << FROZENsoil[ii];
    BOOST_LOG_SEV(glg, debug) << "FROZENFRACsoil[" << ii << "]: " << FROZENFRACsoil[ii];
    BOOST_LOG_SEV(glg, debug) << "rawc[" << ii << "]: " << rawc[ii];
    BOOST_LOG_SEV(glg, debug) << "soma[" << ii << "]: " << soma[ii];
    BOOST_LOG_SEV(glg, debug) << "sompr[" << ii << "]: " << sompr[ii];
    BOOST_LOG_SEV(glg, debug) << "somcr[" << ii << "]: " << somcr[ii];
    BOOST_LOG_SEV(glg, debug) << "orgn[" << ii << "]: " << orgn[ii];
    BOOST_LOG_SEV(glg, debug) << "avln[" << ii << "]: " << avln[ii];

    for(int jj=0; jj<12; jj++){
      BOOST_LOG_SEV(glg, debug) << "prvltrfcnA[" << jj << "][" << ii << "]: " << prvltrfcnA[jj][ii];
    }
  }

  for(int ii=0; ii<MAX_ROC_LAY; ii++){
    BOOST_LOG_SEV(glg, debug) << "TSrock[" << ii << "]: " << TSrock[ii];
    BOOST_LOG_SEV(glg, debug) << "DZrock[" << ii << "]: " << DZrock[ii];
  }

  for(int ii=0; ii<MAX_NUM_FNT; ii++){
    BOOST_LOG_SEV(glg, debug) << "frontZ[" << ii << "]: " << frontZ[ii];
    BOOST_LOG_SEV(glg, debug) << "frontFT[" << ii << "]: " << frontFT[ii];
  }

  BOOST_LOG_SEV(glg, debug) << "***** END RESTARTDATA *****";
}


