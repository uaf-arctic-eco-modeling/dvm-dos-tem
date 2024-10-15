#include "../include/Organic.h"

Organic::Organic() {
};

Organic::~Organic() {
};

void Organic::ShlwThickScheme(const double & shlw_totthickness, const double & deep_totthickness) {
  // Maglio, B. (2024) - implementing a new dynamic layer scheme based on the results of work presented
  // at AGU 2023 (manuscript in preparation) with the dsl off forcing the number of layers in each horizon
  // to equal MAX_LAY in layerconst.h. Then varying MAX_LAY from 1 - 10 and analyzing the results of 
  // equilibrium run. Sites analyzed included: heath, wet-sedge, tussock tundra at Imnavait, a black spruce
  // peatland (based on parameterization developed by Mullen, A.) at Caribou-Poker Creek Research Watershed,
  // a deciduous forest at Murphy Dome, and black spruce peat plateau and thermokarst bog at Bonanza Creek
  // LTER. This yielded a range of organic layer thickness from ~ 4 - 90 cm. We examined stability by 
  // analyzing the root mean square deviation between annual, summer, and winter soil temperature and 
  // moisture profiles between a preceeding and subsequent number of forced layers. This allowed us to 
  // estimate minimum and maximum numbers of layers required to give stable solutions to the heat equation
  // and to Richard's equation.    

  // Calculate total thickness organic layer
  double totthickness = shlw_totthickness + deep_totthickness;

  // Define the maximum number of layers given in MAX_LAY values from layerconst.h
  int shlwnum_max = sizeof(shlwdz) / sizeof(double);
  int deepnum_max = sizeof(deepdz) / sizeof(double);

  // Define the number of layers in each horizon based on stability study:

  // define a range of thickness and correspoding number of layers required.
  array range_of_thicknesses = {}
  array range_of_layerNumbers ={}

  int shlwnum = something;
  int deepnum = something;

  // catch if shlwnum is greater than shlwnum_max
  //catch if deepnum is greater than deepnum_max

  //Creating uniform shlw thickness, uniform_deep used for scaling factor
  double uniform_shlw = shlw_totthickness / shlwnum;
  double uniform_deep = deep_totthickness / deepnum;
  //Creating linear thickness relation (y = mx + c, y=shlwdz, x=layer index, m=increase (gradient), c=fstshlwdz = (1 * m))
  double gradient_shlw = shlw_totthickness / (0.5 * shlwnum * (shlwnum + 1));
  double intercept_shlw = gradient_shlw;//redefined for assignment clarity
  //Creating linear relationships between lstshlwdz and fstdeep for scaling factor
  double linear_shlw = gradient_shlw * shlwnum;
  double linear_deep = deep_totthickness / (0.5 * deepnum * (deepnum + 1));

  // Scaling factor between uniform and linear thickness based on full organic layer properties (shlwnum, deepnum, shlw_totthickness, deep_totthickness)
  // This is calculated by assuming y=lstshlwdz=fstdeepdz, and shlw uniform = Us, linear = Ls, and deep uniform = Ud, linear = Ld. scaling_factor = F
  // for lstshlw and fstdeep, y = F * Us + (1-F)*Ls = F * Ud + (1-F)*Ld - then solving for F = Ld - Ls / (Us - Ls + Ld - Ud)
  double scaling_factor = (linear_deep - linear_shlw) / (uniform_shlw - linear_shlw + linear_deep - uniform_deep);
  
  //Defining double for storing cumulative thickness to calculate final layer thickness without encountering rounding errors:
  double final_layer = 0.0;

  // Looping through layer assigning thickness (excluding final layer to avoid rounding errors)
  for (int i = 0; i < (shlwnum-1); i++) {
    shlwdz[i] = (scaling_factor * uniform_shlw) + (1 - scaling_factor) * (i * gradient_shlw + intercept_shlw);
    final_layer += shlwdz[i];
  }

  // Assigning final layer by subtracting total preassigned layer thicknesses
  shlwdz[shlwnum - 1] = shlw_totthickness - final_layer;

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