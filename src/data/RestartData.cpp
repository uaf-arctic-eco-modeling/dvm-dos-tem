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
