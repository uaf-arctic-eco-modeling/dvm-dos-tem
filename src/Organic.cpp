#include "../include/Organic.h"

Organic::Organic() {
};

Organic::~Organic() {
};

void Organic::ShlwThickScheme(const double & totthickness) {

//BM: forcing via MAX_SLW_LAY test
                                                         //BM:
shlwthick = totthickness;                                // initialize total thickness of shlw 
std::fill(begin(shlwdz), end(shlwdz), MISSING_D);        // initialize all fill values
shlwnum = 0;                                              // initialize zero shlw layer prior to assigment

shlwnum = sizeof(shlwdz) / sizeof(double);              // length of array = MAX_SLW_LAY, used for constructing
                                                        //ratios of layers
int layNumerator = (shlwnum - 1) * (shlwnum) / 2; //layer ratio numerator
int layDenominator = shlwnum * (shlwnum + 1) / 2; //layer ratio denominator

for (int i = 0; i < (shlwnum-1); i++) {
    
    shlwdz[i]= (i+1) * (shlwthick / layDenominator);
  
}

shlwdz[shlwnum-1] = shlwthick - layNumerator*shlwthick/layDenominator;

/*

  shlwthick = totthickness;

          //BM: adding a zero initialization value and commenting first if statement
  // shlwdz[0]=MISSING_D;
  // shlwdz[1]=MISSING_D;
  // shlwdz[2]=MISSING_D;
  shlwnum =0;  

  //if (totthickness<0.) {
  //  shlwthick = 0.;
  //}

  //shlwnum   = 0;

  //These values are from Shuhua Yi's paper, 2010

          //BM: commenting if statement below due to initialization
          //    and redundancy from first if statement (also commented)

  //if(totthickness<=0.00) {
  //  shlwdz[0]=MISSING_D;
  //  shlwdz[1]=MISSING_D;
  //  shlwdz[2]=MISSING_D;
  //  shlwnum =0;
  //} else 
  
          //BM: added "shlwthick>0.00 & shlwthick<0.4"

  if (shlwthick>0.00 & shlwthick<0.04) {
    shlwdz[0]=shlwthick;
    shlwdz[1]=MISSING_D;
    shlwdz[2]=MISSING_D;
    shlwnum =1;
  } 
          //BM: Simplifying else if's to a 2-layer and 3-layer solution

  else if (shlwthick>=0.04 & shlwthick<0.10){
    shlwdz[0]=shlwthick/3;
    shlwdz[1]=shlwthick - shlwthick/3;
    shlwdz[2]=MISSING_D;
    shlwnum =2;
  } else if (shlwthick>=0.10){
    shlwdz[0]=shlwthick/6;
    shlwdz[1]=shlwthick/3;
    shlwdz[2]=shlwthick - shlwthick/3 - shlwthick/6;
    shlwnum =3;
  } 

          //BM: commenting remaining original else if's

  //else if (totthickness>=0.04 & totthickness<0.06) {
  //  shlwdz[0]=0.02;
  //  shlwdz[1]=totthickness-0.02;
  //  shlwdz[2]=MISSING_D;
  //  shlwnum =2;
  //} else if (totthickness<0.10) {
  //  shlwdz[0]=0.03;
  //  shlwdz[1]=totthickness-0.03;
  //  shlwdz[2]=MISSING_D;
  //  shlwnum =2;
  //} else if (totthickness<0.15) {
  //  shlwdz[0]=0.02;
  //  shlwdz[1]=0.04;
  //  shlwdz[2]=totthickness-0.06;
  //  shlwnum =3;
  //} else if (totthickness<0.20) {
  //  shlwdz[0]=0.03;
  //  shlwdz[1]=0.06;
  //  shlwdz[2]=totthickness -0.09;
  //  shlwnum =3;
  //} else if (totthickness<0.28) {
  //  shlwdz[0]=0.04;
  //  shlwdz[1]=0.08;
  //  shlwdz[2]=totthickness -0.12;
  //  shlwnum =3;
  //} else if (totthickness<0.40) {
  //  shlwdz[0]=0.05;
  //  shlwdz[1]=0.11;
  //  shlwdz[2]=totthickness -0.16;
  //  shlwnum =3;
  //} else if (totthickness >=0.4) {
  //  shlwdz[0]=0.1;
  //  shlwdz[1]=0.2;
  //  shlwdz[2]=totthickness -0.3;
  //  shlwnum =3;
  //}
*/
  if (shlwnum>0) {
    lstshlwdz = shlwdz[shlwnum-1];
  }
};

void Organic::DeepThickScheme(const double & totthickness) {

                                                           //BM:
deepthick = totthickness;                                // initialize total thickness of shlw 
std::fill(begin(deepdz), end(deepdz), MISSING_D);        // initialize all fill values
deepnum = 0;                                              // initialize zero shlw layer prior to assigment

deepnum = sizeof(deepdz) / sizeof(double);              // length of array = MAX_SLW_LAY, used for constructing
                                                        //ratios of layers
//int layNumerator = (deepnum - 1) * (deepnum) / 2; //layer ratio numerator
double layDenominator = deepnum * (deepnum + 1) / 2; //layer ratio denominator

double layScalar = (lstshlwdz / totthickness) * 1.05; // 5% increase from lstshlwdz
double layGradient = ((deepnum/layDenominator) - (2 * layScalar) + (1/layDenominator)) / (deepnum - 1);
double layIntercept = layScalar - layGradient;
double layRemainder = 0.0;

for (int i = 0; i < (deepnum-1); i++) {
    
    deepdz[i]= ((i+1) * layGradient + layIntercept) * deepthick;
    layRemainder += deepdz[i];
}

deepdz[deepnum-1] = deepthick - layRemainder;

//   deepthick = totthickness;

//         //BM: commenting initial if statement and setting zero-thickness initialization
//   deepdz[0]=MISSING_D;
//   deepdz[1]=MISSING_D;
//   deepdz[2]=MISSING_D;
//   deepnum = 0;

// //  if(totthickness<=0.0) {
// //    deepthick =0.0;
// //    deepdz[0]=MISSING_D;
// //    deepdz[1]=MISSING_D;
// //    deepdz[2]=MISSING_D;
// //    deepnum =0;
// //    return;
// //  }

//   if(lstshlwdz>0.0) {
//     if(deepthick < 3* lstshlwdz) {
//       deepdz[0]=deepthick;
//       deepdz[1]=MISSING_D;
//       deepdz[2]=MISSING_D;
//       deepnum =1;
//     } else if(deepthick >= 3* lstshlwdz && deepthick<6*lstshlwdz) {
//       deepdz[0]=1./3. * deepthick;
//       deepdz[1]=2./3. * deepthick;
//       deepdz[2]=MISSING_D;
//       deepnum =2;
//     } else {
//       deepdz[0]=1./6. * deepthick;
//       deepdz[1]=2./6. * deepthick;
//       deepdz[2]=3./6. * deepthick;
//       deepnum =3;
//     }
//   } else {
//     if(deepthick <= 0.02) {
//       deepdz[0]=deepthick;
//       deepdz[1]=MISSING_D;
//       deepdz[2]=MISSING_D;
//       deepnum =1;
//     } else if(deepthick<=0.06) {
//       deepdz[0]=1./3. * deepthick;
//       deepdz[1]=2./3. * deepthick;
//       deepdz[2]=MISSING_D;
//       deepnum =2;
//     } else {
//       deepdz[0]=1./6. * deepthick;
//       deepdz[1]=2./6. * deepthick;
//       deepdz[2]=3./6. * deepthick;
//       deepnum =3;
//     }
//   }


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

