/*! \file
 */

#include "../include/CrankNicholson.h"

CrankNicholson::CrankNicholson() {
}

CrankNicholson::~CrankNicholson() {
  //
}

void CrankNicholson::geBackward(const int &startind, const int & endind,
                                double t[], double dx[], double cn[],
                                double cap[], double  s[],
                                double e[], double & dt) {
  double condth;
  double conuth;
  double denm;
  double r;
  double rc;
  double rhs;
  //loop from last layer to first layer
  int iu;
  int id;
  double sil;
  double eil;
  //invert values to replace division with multiplication for speed
  //rar 20140503
  double dt_inv = 1 / dt;
  double denm_inv;

  for (int il = endind-1 ; il>=startind+1; il--) {
    iu =il-1;
    id =il+1;
    conuth = cn[iu];
    condth = cn[il] ;
    rc = (cap[il] + cap[iu]) * dt_inv;
    //rc = (cap[il] + cap[iu]) / dt;
    r = conuth + rc + condth;
    denm = r - condth * s[id];
    denm_inv = 1 / denm;
    rhs = (rc - conuth - condth) * t[il] + conuth* t[iu] + condth * t[id];
    //sil = conuth / denm;
    sil = conuth * denm_inv;
    //eil = (rhs + condth * e[id]) / denm;
    eil = (rhs + condth * e[id]) * denm_inv;
    s[il] = sil;
    e[il] = eil;
  }
}

void CrankNicholson::geForward(const int  &startind, const int & endind,
                               double t[], double dx[], double cn[],
                               double cap[], double  s[], double e[],
                               double & dt) {
  double condth;
  double conuth;
  double denm;
  double r;
  double rc;
  double rhs;
  int im1;
  int ip1;
  //invert values to replace division with multiplication for speed
  //rar 20140503
  double dt_inv = 1 / dt;
  double denm_inv;

  for (int il =startind+1 ; il<=endind-1; il++) {
    im1 =il - 1;
    ip1 =il + 1;
    conuth = cn[im1];
    condth = cn[il] ;
    rc = (cap[il] + cap[im1]) * dt_inv;
    //rc = (cap[il] + cap[im1]) / dt;
    r = conuth + rc + condth;
    denm = r - conuth * s[im1];
    denm_inv = 1 / denm;
    rhs = (rc - conuth - condth) * t[il] + conuth
          * t[im1] + condth * t[ip1];
    //s[il] = condth / denm;
    s[il] = condth * denm_inv;
    //e[il] = (rhs + conuth * e[im1]) / denm;
    e[il] = (rhs + conuth * e[im1]) * denm_inv;
  }
}

void CrankNicholson::cnForward(const int & startind, const int & endind,
                               double tii[], double tit[],
                               double s[], double e[]) {
  tit[startind]= tii[startind];

  for ( int il =startind+1; il <= endind-1; il++ ) {
    tit[il] = s[il] * tit[il-1] + e[il];
  }

  tit[endind] = tii[endind];
}

void CrankNicholson::cnBackward(const int & startind, const int & endind,
                                double tii[], double tit[],
                                double s[], double e[]) {
  tit[endind]= tii[endind];

  for ( int il =endind-1; il >= startind+1; il--) {
    tit[il] = s[il] * tit[il+1] + e[il];
  }

  tit[endind]= tii[endind];
}

void CrankNicholson::tridiagonal(const int ind, const int numsl, double a[],
                                 double b[], double c[],
                                 double r[], double u[]) {
  /* input coefficient arrays: a, b, c
   * input: ind, numsl: first layer index, and total number of layers
   * output: u: change in volumetric water content per layer
   */
  //placeholder for intermediate values
  double gamma[ind+numsl];
  //set beta for use in first and second layers
  double beta = b[ind];
  //forward pass
  for(int ii = ind; ii < ind + numsl; ii++){
    if(ii == ind){ //first layer
      u[ii] = r[ii] / beta;
    } else { //remaining layers
      gamma[ii] = c[ii-1] / beta;
      beta = b[ii] - a[ii] * gamma[ii]; //reset beta
      u[ii] = (r[ii] - a[ii] * u[ii-1]) / beta;
    }
  }
  //backward pass, skips bottom layer
  for(int ii = ind + numsl - 2; ii >= ind; --ii){
    u[ii] = u[ii] - gamma[ii+1] * u[ii+1];
  }
}

//void CrankNicholson::tridiagonal(const int ind, const int numsl, double a[],
//                                 double b[], double c[],
//                                 double r[], double u[]) {
  /* input: a, b, c
   * input: ind, numsl: first layer index, and total number of layers
   * output: u
   */
/*  double gam[numsl];
  double tempg;
  double bet = b[ind];
  //invert values to replace division with multiplication for speed
  //rar 20140503
  double bet_inv = 1 / bet;

  for(int il=ind; il<ind+numsl; il++) {
    if(il == ind) {
      u[il] = r[il] * bet_inv;
      //u[il] = r[il] / bet;
    } else {
      tempg = c[il-1] * bet_inv;
      //tempg = c[il-1] / bet;
      gam[il-ind]= tempg;
      bet = b[il] - a[il] *gam[il-ind];//bet is changed here, so at next line,
      bet_inv = 1 / bet;
      //u[il] = (r[il] - a[il]*u[il-1]) / bet;//bet_inv is no longer valid
      u[il] = (r[il] - a[il]*u[il-1]) * bet_inv;//bet_inv is no longer valid
    }
  }

  for(int il=ind+numsl-1; il>ind; il--) {
    //the first layer (il==ind) is done above: basically to say
    //  liq. water not move upward from the first layer
    double uil  = u[il];
    double uild = u[il+1];

    if (il==ind+numsl-1) {
      uild = 0.;
    }

    double g = gam[il+1-ind];

    if (il==ind+numsl-1) {
      g = gam[il-ind];
    }

    //u[il] = u[il] - gam[il+1-ind]*u[il+1];
    u[il] = uil - g*uild;
  }
}
*/
