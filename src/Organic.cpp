#include "../include/Organic.h"

Organic::Organic() {
};

Organic::~Organic() {
};

void Organic::ShlwThickScheme(const double & shlw_totthickness, const double & deep_totthickness) {
  //BM: implementing a layer "forcing" scheme to test organic layer resolution on soil thermal and hydrological regimes
  //    This is based on assuming uniform or linearly increasing layers. A scaling factor is used to find an optimum between uniform and linear schemes.

  // Initialize total thickness of shlw horizon - do I even need to initialize these?
  shlwthick = shlw_totthickness;
  deepthick = deep_totthickness;
  
  // Force number of layers to MAX_LAY values from layerconst.h - not necessary if dsl on (non-forced)
  shlwnum = sizeof(shlwdz) / sizeof(double);
  deepnum = sizeof(deepdz) / sizeof(double);

  //Creating uniform shlw thickness, uniform_deep used for scaling factor
  double uniform_shlw = shlwthick / shlwnum;
  double uniform_deep = deepthick / deepnum;
  //Creating linear thickness relation (y = mx + c, y=shlwdz, x=layer index, m=increase (gradient), c=fstshlwdz = (1 * m))
  double gradient_shlw = shlwthick / (0.5*shlwnum*(shlwnum+1));
  double intercept_shlw = gradient_shlw;//redefined for assignment clarity
  //Creating linear relationships between lstshlwdz and fstdeep for scaling factor
  double linear_shlw = gradient_shlw * shlwnum;
  double linear_deep = deepthick / (0.5*deepnum*(deepnum+1));

  //Scaling factor between uniform and linear thickness based on full organic layer properties (shlwnum, deepnum, shlwthick, deepthick)
  //This is calculated by assuming y=lstshlwdz=fstdeepdz, and shlw uniform = Us, linear = Ls, and deep uniform = Ud, linear = Ld. scaling_factor = F
  //for lstshlw and fstdeep, y = F * Us + (1-F)*Ls = F * Ud + (1-F)*Ld - then solving for F = Ld - Ls / (Us - Ls + Ld - Ud)
  double scaling_factor = (linear_deep - linear_shlw) / (uniform_shlw - linear_shlw + linear_deep - uniform_deep);
  
  //Defining double for storing cumulative thickness to calculate final layer thickness without encountering rounding errors:
  double final_layer = 0.0;

  // Looping through layer assigning thickness (excluding final layer to avoid rounding errors)
  for (int i = 0; i < (shlwnum-1); i++) {
    shlwdz[i] = (scaling_factor * uniform_shlw) + (1 - scaling_factor) * (i * gradient_shlw + intercept_shlw);
    final_layer += shlwdz[i];
  }

  // Assigning final layer by subtracting total preassigned layer thicknesses
  shlwdz[shlwnum-1] = shlwthick - final_layer;

  // Assigning lstshlwdz to be used in DeepThickScheme - not currently used for forcing but leaving for final scheme
  if (shlwnum>0) {
    lstshlwdz = shlwdz[shlwnum-1];
  }

};

void Organic::DeepThickScheme(const double & shlw_totthickness, const double & deep_totthickness) {
   //BM: implementing a layer "forcing" scheme to test organic layer resolution on soil thermal and hydrological regimes
  //    This is based on assuming uniform or linearly increasing layers. A scaling factor is used to find an optimum between uniform and linear schemes.

  // Initialize total thickness of shlw horizon - do I even need to initialize these?
  shlwthick = shlw_totthickness;
  deepthick = deep_totthickness;

  // Force number of layers to MAX_LAY values from layerconst.h - not necessary if dsl on (non-forced)
  shlwnum = sizeof(shlwdz) / sizeof(double);
  deepnum = sizeof(deepdz) / sizeof(double);

  //Creating uniform shlw thickness, uniform_deep used for scaling factor
  double uniform_shlw = shlwthick / shlwnum;
  double uniform_deep = deepthick / deepnum;
  //Creating linear thickness relation (y = mx + c, y=shlwdz, x=layer index, m=increase (gradient), c=fstshlwdz = (1 * m))
  double gradient_deep = deepthick / (0.5*deepnum*(deepnum+1));
  double intercept_deep = gradient_deep;//redefined for assignment clarity
  //Creating linear relationships between lstshlwdz and fstdeep for scaling factor
  double linear_shlw = shlwthick / (0.5*(shlwnum+1));
  double linear_deep = gradient_deep;

  //Scaling factor between uniform and linear thickness based on full organic layer properties (shlwnum, deepnum, shlwthick, deepthick)
  //This is calculated by assuming y=lstshlwdz=fstdeepdz, and shlw uniform = Us, linear = Ls, and deep uniform = Ud, linear = Ld. scaling_factor = F
  //for lstshlw and fstdeep, y = F * Us + (1-F)*Ls = F * Ud + (1-F)*Ld - then solving for F = Ld - Ls / (Us - Ls + Ld - Ud)
  double scaling_factor = (linear_deep - linear_shlw) / (uniform_shlw - linear_shlw + linear_deep - uniform_deep);
  
  //Defining double for storing cumulative thickness to calculate final layer thickness without encountering rounding errors:
  double final_layer = 0.0;

  // Looping through layer assigning thickness (excluding final layer to avoid rounding errors)
  for (int i = 0; i < (deepnum-1); i++) {
    deepdz[i] = (scaling_factor * uniform_deep) + (1 - scaling_factor) * (i * gradient_deep + intercept_deep);
    final_layer += deepdz[i];
  }

  // Assigning final layer by subtracting total preassigned layer thicknesses
  deepdz[deepnum-1] = deepthick - final_layer;
};

// if shlw peat thickness from input soil profile
void Organic::assignShlwThicknesses(int soiltype[], double soildz[],
                                    const int & soilmaxnum) {
  shlwnum   = 0;
  shlwthick = 0;

  for(int i=0; i<soilmaxnum; i++) {
    if(soiltype[i] ==1) {
      shlwdz[shlwnum] = soildz[i];
      shlwnum ++;
      shlwthick += soildz[i];
    } else {
      if(soiltype[i]>2) {
        break;
      }
    }
  }
};

// if deep peat thickness from input soil profile
void Organic::assignDeepThicknesses(int soiltype[], double soildz[],
                                    const int & soilmaxnum) {
  deepnum =0;
  deepthick =0;

  for(int i=0; i<soilmaxnum; i++) {
    if(soiltype[i] ==2) {
      deepdz[deepnum] = soildz[i];
      deepnum ++;
      deepthick += soildz[i];
    } else {
      if(soiltype[i]>2) {
        break;
      }
    }
  }
};