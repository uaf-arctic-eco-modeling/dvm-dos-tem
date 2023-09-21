#include "../include/Organic.h"

Organic::Organic() {
};

Organic::~Organic() {
};

void Organic::ShlwThickScheme(const double & totthickness) {
  //BM: implementing a layer "forcing" scheme to test organic layer resolution on soil thermal and hydrological regimes

  // Initialize total thickness of shlw horizon
  shlwthick = totthickness;

  // Initialize shlw thicknesses as fill values
  std::fill(begin(shlwdz), end(shlwdz), MISSING_D);

  // Initialize shlwnum=0 prior to assignment
  shlwnum = 0;

  // Force number of shlw layers to MAX_SLW_LAY from layerconst.h
  shlwnum = sizeof(shlwdz) / sizeof(double);

  // Creating ratios based on the number of shlw layers for layer division
  // layDenominator used to determine minimum fraction of layers based on shlwnum
  // layNumerator used to find ratio, excluding final layer, to avoid rounding errors 
  // (e.g. shlwnum=2, layNumerator=1, layDenominator=3, shlwdz[0]=1/3 * shlwthick, shlwdz[1]=shlwthick - 1/3 * shlwthick=2/3 * shlwthick)
  int layNumerator = (shlwnum - 1) * (shlwnum) / 2;
  int layDenominator = shlwnum * (shlwnum + 1) / 2;

  // Looping through layer assigning thickness (excluding final layer to avoid rounding errors)
  for (int i = 0; i < (shlwnum-1); i++) {
    shlwdz[i]= (i+1) * (shlwthick / layDenominator);
  }

  // Assigning final layer by subtracting total preassigned layer thicknesses
  shlwdz[shlwnum-1] = shlwthick - layNumerator*shlwthick/layDenominator;

  // Assigning lstshlwdz to be used in DeepThickScheme
  if (shlwnum>0) {
    lstshlwdz = shlwdz[shlwnum-1];
  }
};

void Organic::DeepThickScheme(const double & totthickness) {
  //BM: implementing a layer "forcing" scheme to test organic layer resolution on soil thermal and hydrological regimes

  // Initialize total thickness of deep horizon 
  deepthick = totthickness;

  // Initialize deep thicknesses as fill values
  std::fill(begin(deepdz), end(deepdz), MISSING_D);

  // Initialize deepnum=0 prior to assignment
  deepnum = 0;

  // Force number of deep layers to MAX_DEP_LAY from layerconst.h
  deepnum = sizeof(deepdz) / sizeof(double);              

  // Creating ratios for layer thickness assignment based on a linear extrapolation from lstshlwdz
  // Equivalent to y=mx+c, where y is deepdz and x is layer number in deep horizon
  // Used to create a linearly increasing deepdz while conserving deepthick 
  //layDenominator used to determine minimum fraction of layers based on deepnum
  double layDenominator = deepnum * (deepnum + 1) / 2; //layer ratio denominator

  // layScalar is used to set the ratio between lstshlwdz and deepthick - this may need to be multiplied if fstdeepdz>lstshlwdz (i.e. layScalar * 1.05, 5% increase)
  double layScalar = (lstshlwdz / deepthick);
  // layGradient is used to define the rate of thickness increase between deep layers based on deepnum, layDenominator, and layScalar (equivalent to m in y=mx+c)  
  double layGradient = ((deepnum/layDenominator) - (2 * layScalar) + (1/layDenominator)) / (deepnum - 1);
  // layIntercept is used to set zeroth layer thickness ratio of deepthick (equivalent to c in y=mx+c)
  double layIntercept = layScalar - layGradient;
  // layRemainder initialized to zero and assigned to as deepdz is assigned for subtraction at final layer and avoiding rounding errors
  double layRemainder = 0.0;

  // Looping through layer assigning thickness (excluding final layer to avoid rounding errors)
  for (int i = 0; i < (deepnum-1); i++) {
    deepdz[i]= ((i+1) * layGradient + layIntercept) * deepthick;

    layRemainder += deepdz[i];

    }

  // Assigning final layer by subtracting layRemainder (assigned thicknesses) to avoid rounding errors
  deepdz[deepnum-1] = deepthick - layRemainder;
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

