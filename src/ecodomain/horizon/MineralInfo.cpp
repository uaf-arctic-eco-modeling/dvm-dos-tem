#include "MineralInfo.h"
#include "../../TEMUtilityFunctions.h" 
#include "../../TEMLogger.h"

extern src::severity_logger< severity_level > glg;

MineralInfo::MineralInfo() {}

MineralInfo::MineralInfo(const std::string& fname, const int y, const int x) {

  #pragma omp critical(load_input)
  {  
    BOOST_LOG_SEV(glg, info) << "Loading ModelInfo (soil texture) from file: " << fname;
    BOOST_LOG_SEV(glg, info) << "Loading for (y, x) point: " << "("<< y <<","<< x <<").";

    float psand = temutil::get_scalar<float>(fname, "pct_sand", y, x);
    float psilt = temutil::get_scalar<float>(fname, "pct_silt", y, x);
    float pclay = temutil::get_scalar<float>(fname, "pct_clay", y, x);
    
    for (int i = 0; i < MAX_MIN_LAY; ++i) {
      sand[i] = psand;
      silt[i] = psilt;
      clay[i] = pclay;
    }
  }//End critical(soil_texture)
  setDefaultThick(0.0);
}

MineralInfo::~MineralInfo() {}

void MineralInfo::setDefaultThick(const double & thickness) {
  // The following is the default thickness and number of mineral layers (Yuan)
  num = MAX_MIN_LAY;
  thick = 0.0;

  for (int i=0; i<MAX_MIN_LAY; i++) {
    dz[i] = MINETHICK[i]; // Default thickness
                          // (defined in MINETHICK[] in /inc/layerconst.h)
    thick += dz[i];
  }

  // If total thickness input, needs update the actual bottom layer's thickness
  if (thickness > 0.0) {
    thick = 0.0;
    num = 0;

    for (int i=0; i<MAX_MIN_LAY; i++) {
      thick += dz[i];

      if (thick >= thickness) {
        dz[i] = thick - thickness;
        thick = thickness;
        break;
      } else if (i==MAX_MIN_LAY-1) { // last layer, but still input thickness
                                     // too large
        dz[i] += thickness - thick;  // add the rest into the bottom layer
        thick = thickness;
      }

      num ++;
    }
  }
}


void MineralInfo::set5Soilprofile(int soiltype[],
                                  double soildz[],
                                  const int & maxnum) {
  num =0;
  thick =0.;

  for(int i=0; i<maxnum; i++) {
    if (soiltype[i]==3) {
      dz[num]    = soildz[i];
      num ++;
      thick += soildz[i];
    }
  }
}

