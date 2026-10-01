#ifndef ERRORCODE_H_
#define ERRORCODE_H_
enum ERRORKEY { I_VAR_NULL =1, I_INPUT_INVALID,
                I_TEM_TSTEP_SMALL=20, I_BOTTOM_NEW_FRONT, I_NAN_TLD, I_NAN_TIT,
                I_NAN_TII,I_TOO_BIG_TII,I_TOO_SMALL_TII,
                I_WAT_TSTEP_SMALL=30, I_NAN_WATER, I_NEG_WATER,
                I_TOO_MANY_FRZ_FRONTS=41,  I_TOO_MANY_THW_FRONTS,
                I_FRONT_INCONSISTENT, I_FROZEN_STATE, I_GROW_START, I_SNOW_AGE,
                I_NIMMOB_RANGE=50,I_NUPTAKE_RANGE,
                I_BURN_ZERO =60,
                I_LAYER_FIRST_DEEP=70, I_FRONT_STATE_INCON,  I_FRONT_POSITION,
                I_NCFILE_NOT_EXIST=100, I_NCDIM_NOT_EXIST, I_NCVAR_NOT_EXIST,
                I_NCVAR_GET_ERROR
              };

// Codes for writing to the run status file
const int STATUS_SUCCESS = 100;
const int STATUS_MASKED = 0;
const int STATUS_TIMEOUT = -5;
const int STATUS_FAIL = -100;

const int MISSING_I    = -9999;    //missing value (INT) used in the code
const float MISSING_F  = -9999.f;  //missing value (FLOAT) used in the code
const double MISSING_D = -9999.;   //missing value (DOUBLE) used in the code

// Idea here is that everything should be explicitly set to the appropriate
// "uninitialized" value by constructors. This way we have easily recognizeable
// value so it is readily apparent if the data structure has been touched
// later in the program.
//
// Hopefully as the constructors get smarter we will need
// to use these values less frequently.
//
// 4-6-2016 Note: Setting these to 'flag' values (e.g. -999999.0) results in
// many broken model dynamics. May be useful for debugging, but for now,
// setting all value to zero seems to fix the dynamics issues. We
// are not sure if initializing everything to zero is exactly correct, but it
// seems to be an improvement over other 'flag' initialization values.
const int UIN_I = 0;
const float UIN_F = 0.0;
const double UIN_D = 0.0;

#ifndef NULL
#define NULL   ((void *) 0)
#endif

#endif /*ERRORCODE_H_*/
