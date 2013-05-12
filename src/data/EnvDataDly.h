#ifndef ENVDATADLY_H_
#define ENVDATADLY_H_

#include "../inc/diagnostics.h"
#include "../inc/fluxes.h"
#include "../inc/states.h"

#include "../inc/errorcode.h"
#include "../inc/layerconst.h"
#include "../inc/timeconst.h"
#include "../inc/physicalconst.h"
#include "../inc/cohortconst.h"

class EnvDataDly{
  public:
  	EnvDataDly();
  	~EnvDataDly();

  	int chtid;

  	// for daily  - 'd' is daily
  	snwstate_dim d_snow;

    atmstate_env d_atms;  // last 's' - state variable
    vegstate_env d_vegs;
    snwstate_env d_snws;
    soistate_env d_sois;
    
    atmdiag_env d_atmd;   // last 'd' - diagnostic variable
    vegdiag_env d_vegd;
    snwdiag_env d_snwd;
    soidiag_env d_soid;
    
    lnd2atm_env d_l2a;    // 'l' - land, '2' - 'to', 'a' - atm
    atm2lnd_env d_a2l;
    atm2veg_env d_a2v;    // 'v' - veg
    veg2atm_env d_v2a;
    veg2gnd_env d_v2g;    // 'g' - ground
    soi2lnd_env d_soi2l;  // 'soi' - soil
    soi2atm_env d_soi2a;
    snw2atm_env d_snw2a;  // 'snw' - snow
    snw2soi_env d_snw2soi;
    
  private:
	
};

#endif /*ENVDATA_H_*/
