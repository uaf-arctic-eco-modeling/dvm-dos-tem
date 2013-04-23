#ifndef INTEGRATOR_H_
#define INTEGRATOR_H_

/* \file 
 * This class is used to implement
 * Runge-Kutta Method for integration of TEM equations
 * (see ATPress42005a, Numerical Recipes in C++, The art of scientific computing, 2nd edition
 *  W.H. Press, S.A. Teukolsky, W.T. Vetterling and B.P. Flannery, 2005, Cambridge University Press)
 * Page 712-727
 * 
 * Low-order classical Runge-Kutta Formulas with step size control and their application
 * to some heat transfer problems
 * by Erwin Feblberg
 * NASA TR R-315, 1969
 * REPORT TL 521 A3312 no.315 in GI-IARC 1st floor
 * see also http://www.ece.uwaterloo.ca/~ece204/TheBook/14IVPs/rkf45/
 */

#include <cstring>
#include <iostream>
#include <sstream>
#include <string>
#include <cmath>
using namespace std;

#include "../snowsoil/Soil_Bgc.h"
#include "../vegetation/Vegetation_Bgc.h"
#include "../inc/temconst.h"

class Integrator{
	public :
		Integrator();
		~Integrator();

        enum vegvarkey {I_VEGC = 0,              //index starts from zero
						I_STRN = NUM_PFT_PART,
        				I_LABN = 2*NUM_PFT_PART,
        				I_DEADC, I_DEADN,       // 0 ~ NUM_VEG_STATE-1 for veg state variables

        				I_INGPP = NUM_VEG_STATE,                         // NUM_VEG_STATE is the starting index for flux variables
        				I_INNPP = NUM_VEG_STATE + NUM_PFT_PART,
        				I_GPP   = NUM_VEG_STATE + 2*NUM_PFT_PART,
        				I_NPP   = NUM_VEG_STATE + 3*NUM_PFT_PART,
        				I_RM    = NUM_VEG_STATE + 4*NUM_PFT_PART,
        				I_RG    = NUM_VEG_STATE + 5*NUM_PFT_PART,
        				I_LTRC  = NUM_VEG_STATE + 6*NUM_PFT_PART,

        				I_SNUP  = NUM_VEG_STATE + 7*NUM_PFT_PART,
        				I_NMBOL = NUM_VEG_STATE + 8*NUM_PFT_PART,
        				I_NRSRB = NUM_VEG_STATE + 9*NUM_PFT_PART,
        				I_LTRN  = NUM_VEG_STATE + 10*NUM_PFT_PART,      // 11*NUM_PFT_PART veg C/N flux variables

        				I_INNUP = NUM_VEG_STATE + 11*NUM_PFT_PART,      //because indexed from zero, so here is the sum of all above
        				I_LNUP

                  };

        // after change the keys here , remember to update the NUMEQ_VEG and NUM_VEG_STATE in temconst.h
        enum soivarkey {
                     I_L_RAWC  = 0,
                     I_L_SOMA  = MAX_SOI_LAY,
                     I_L_SOMPR = 2*MAX_SOI_LAY,
                     I_L_SOMCR = 3*MAX_SOI_LAY,     // (4*LAYERS) these 4 lines - Layered Soil C state variables
                     I_L_ORGN  = 4*MAX_SOI_LAY,
                     I_L_AVLN  = 5*MAX_SOI_LAY,     // (4*LAYERS) these 2 lines - Layered Soil N state variables

                     I_WDEBRISC= 6*MAX_SOI_LAY,    //because indexed from zero, so here is the sum of all above
                     I_WDEBRISN,
                     I_DMOSSC, I_DMOSSN,

                     I_L_RH_RAW  = NUM_SOI_STATE,
                     I_L_RH_SOMA = NUM_SOI_STATE + MAX_SOI_LAY,
                     I_L_RH_SOMPR= NUM_SOI_STATE + 2*MAX_SOI_LAY,
                     I_L_RH_SOMCR= NUM_SOI_STATE + 3*MAX_SOI_LAY,
                     I_L_NMIN    = NUM_SOI_STATE + 4*MAX_SOI_LAY,
                     I_L_NIMMOB  = NUM_SOI_STATE + 5*MAX_SOI_LAY,   // 6*MAX_SOI_LAY soil C/N flux variables

                     I_RH_WD = NUM_SOI_STATE + 6*MAX_SOI_LAY,       //because indexed from zero, so here is the sum of all above
                     I_RH_DMOSS,

                     I_ORGNLOSS, I_AVLNLOSS

                  };  
        // after change the keys here , remember to update the NUMEQ and MAXSTATE in temconst.h

       char predstr_veg[NUMEQ_VEG][11];
       char predstr_soi[NUMEQ_SOI][11];

       bool vegbgc;
       bool soibgc;
                    
       void setBgcData(BgcData *bdp);
       void setSoil_Bgc(Soil_Bgc * soib);
       void setVegetation_Bgc(Vegetation_Bgc * vegb);
       
       void updateMonthlyVbgc();
       void updateMonthlySbgc(const int &numsl);

  private:

       int numsl;  //actual number of soil layers

  	   void c2ystate_veg(float y[]);
  	   void c2ystate_soi(float y[]);
       int adapt(float pstate[], const int &numeq);
       void y2cstate_veg(float y[]);
       void y2cstate_soi(float y[]);
       void y2cflux_veg(float y[]);
       void y2cflux_soi(float y[]);

        bool rkf45(const int& numeq, float pstate[], float& pdt);
        void delta(float pstate[], float pdstate[]);

 	   void dc2yflux_veg(float pdstate[]);
 	   void dc2yflux_soi(float pdstate[]);
 	   void dc2ystate_veg(float pdstate[]);
 	   void dc2ystate_soi(float pdstate[]);
 	   void y2tcstate_veg(float pdstate[]);// t stands for temporary
 	   void y2tcstate_soi(float pdstate[]);// t stands for temporary

 	   int checkPools();
       void step(const int& numeq, float pstate[], float pdstate[],
                 float ptstate[], float& pdt);
       int boundcon( float ptstate[], float err[], float& ptol) ;

       int blackhol;
       float inittol;
       int maxit;
       int maxitmon;
       int retry;

       int syint;
       int test;
      
       float y[NUMEQ];
       float dum4[NUMEQ];
       float error[NUMEQ];

      float dum5[NUMEQ];
      float dumy[NUMEQ];

      float ydum[NUMEQ];
      float yprime[NUMEQ];
      float rk45[NUMEQ];

      float f11[NUMEQ];
      float f2[NUMEQ];
      float f13[NUMEQ];
      float f3[NUMEQ];
      float f14[NUMEQ];
      float f4[NUMEQ];
      float f15[NUMEQ];
      float f5[NUMEQ];
      float f16[NUMEQ];
      float f6[NUMEQ];

      static float  a1;
      static float  a3, a31, a32;
      static float  a4, a41, a42, a43;
      static float  a5, a51, a52, a53, a54;
      static float  b1, b3, b4, b5;
      static float  b6, b61, b62, b63, b64, b65;
	 
      Soil_Bgc * ssl;
	  Vegetation_Bgc * veg;
	  BgcData *bd;
	  
};
#endif /*INTEGRATOR_H_*/


