#ifndef TIMECONST_H_
#define TIMECONST_H_

const int DINY = 365;
const int MINY = 12;
const int DINM[12] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
const int DOYINDFST[12] = {0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334};

const double SEC_IN_DAY = 86400.0;

// driving data set dimension
// maximum number of years of fire size history at regional-scale (YUAN);
// (unused) const int MAX_FSIZE_DRV_YR = 109;

// maximum number of years of CO2 at regional-scale (YUAN);
// (unused) const int MAX_CO2_DRV_YR = 109;

// maximum number of years of atmospheric driving data
// (unused) const int MAX_ATM_DRV_YR = 109;

// maximum number of years of NORMAL atmospheric driving data
// (YUAN: used for spin-up)
// (unused) const int MAX_ATM_NOM_YR = 30;

//vegetation data set dimension
const int MAX_VEG_SET = 15; // maximum number of vegetation datasets

//YUAN: moving the constants in Timer here
// UNUSED! const int MIN_EQ_YR = 2000; // minimum number of years for equilibrium run
// UNUSED! const int MAX_EQ_YR; // now setting this from cmdline args... = 500; // maximum number of years for equilibrium run

// UNUSED! const int MAX_SP_YR = 1000; // maximum number of years of spinup run;

// UNUSED! const int BEG_TR_YR = 1901;
// UNUSED! const int END_TR_YR = 2009;
// UNUSED! const int BEG_SC_YR = 2010;
// UNUSED! const int END_SC_YR = 2100;

//YUAN: the following is upon the above and modified from the
//        original definition
// UNUSED! const int END_SP_YR = BEG_TR_YR - 1;
// UNUSED! const int BEG_SP_YR = END_SP_YR - MAX_SP_YR+1; //NOTE: not -1, which reserved
                                               //        for non fire year

// maximum number of years of transient run;
// UNUSED! const int MAX_TR_YR = END_TR_YR-BEG_TR_YR+1;
// maximum number of years of scenario run;
// UNUSED! const int MAX_SC_YR = END_SC_YR-BEG_SC_YR+1;

// (unused) const int MAX_FIR_OCRNUM  = 30;// maximum number of fire occurrence in model run

#endif /*TIMECONST_H_*/
