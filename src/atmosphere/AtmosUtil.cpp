#include "AtmosUtil.h"

AtmosUtil::AtmosUtil(){
	
};


AtmosUtil::~AtmosUtil(){
	
};


void AtmosUtil::updateDailyPrec(float precd[], const int & dinmcurr , 
                                const float & mta, const float & mprec){
 // input are monthly precipitation, monthly temperature
 // output are daily precpitation
 // this function is based on the code provided Qianlai on Feb. 19, 2007
	float RT, RS, R ;
    RT=1.778;
    RS=0.635;
    R=0.5;
   
	float TEMP, PREC, DURT, DURS;
    PREC = mprec/10.0/2.54; //comvert mm to cm, then to in.
    DURT=RT/R;
    DURS=RS/R;
	
	float B=1.0, T=0.0, S=1.0, RB, DURB;
	for(int id =0;id<32;id++){
		RAININTE[id] =0.;
		RAINDUR[id] = 0.; 
	}
    
    TEMP = mta;
//  Case 1, TEMP<0.
    if (TEMP <= 0.0) {
        if (PREC <= 1.0) {
          B=1.0;
          T=0.0;
          S=1.0;
        } else {
          B=1.0;
          T=1.0;
          S=1.0;
        }
        
     }
     
//   Case 2, PREC<1.0 inch.
     else if (PREC <= 1.0) {
          B=1.0;
          T=0.0;
          S=1.0;
     }

//   Case 3, 1.0<PREC<2.5 inches.
     else if ((2.5 >= PREC) && (PREC > 1.0)) {
           B=1.0;
           T=1.0;
           S=1.0;
     }

//   Case 4, 2.5<PREC<4.0 inches.
     else if ((4.0 >= PREC) && (PREC > 2.5)) {
           B=1.0;
           S=4.0;
           if (PREC < 3.7)
             T=1.0;
           else
             T=2.0;
     }

//   Case 5, 4.0<PREC<5.0 inches.
     else if ((5.0 >= PREC) && (PREC > 4.0)) {
           B=1.0;
           S=4.0;
           if (PREC < 4.43)
             T=1.0;
           else
             T=2.0;
     }

//   Case 6, 5.0<PREC<7.0 inches.
     else if ((7.0 >= PREC) && (PREC > 5.0)) {
           B=2.0;
           S=4.0;
           if (PREC < 5.65)
             T=1.0;
           else
             T=2.0;
     }

//   Case 7, 7.0<PREC<9.0 inches.
     else if ((9.0 >= PREC) && (PREC > 7.0)) {
           B=2.0;
           S=6.0;
           if (PREC < 8.21)
             T=3.0;
           else
             T=4.0;
     }

//   Case 8, 9.0<PREC<11.0 inches.
     else if ((11.0 >= PREC) && (PREC > 9.0)) {
           B=3.0;
           S=6.0;
           if (PREC < 10.0)
              T=4.0;
           else
              T=5.0;
     }

//   Case 9, PREC>11.0 inches.
     else if (PREC > 11.0) {
           B=4.0;
           S=7.0; 
           if (PREC < 13.0)
             	T=4.0;
           else
             	T=5.0;
     }

    RB=(PREC*2.54-RS*S-RT*T)/B;   //Yuan
    DURB=RB/R;    //Yuan

    if (DURB <= 0.01) DURB=0.01;    // !added //changed from zero to 0.01 by shuhua
   	PREC=PREC*2.54 * 10.0;  // convert back to cm, and then to mm
  
  	float BB, TT;
  	int KTT, KDD, KTD, KKTD;
  	int NN, DT;
  	
  	DT = dinmcurr;
        
    KTT= (int)(B+T);
    KTD=DT/KTT;
    KDD=DT-KTT*KTD;
    BB=B;
    TT=T;
    NN =0;    
    for (int JJ=1; JJ<=KTT; JJ++) {
		if (BB > 0.0) {
           	BB=BB-1.0;
            for (int L=1; L<=KTD; L++) {
            	NN=NN+1;
                RAININTE[NN]=0.0;
                RAINDUR[NN]=0.0;
                if (L == KTD) {
                	RAININTE[NN]=5.0; // unit with mm /hr
                    RAINDUR[NN]=DURB;
                }
            }
        }

        if (TT > 0.0) {
            TT=TT-1.0;
            if (JJ == 1){
                KKTD=KTD+KDD;
            } else {
                KKTD=KTD;
            }

            for (int L=1; L <= KKTD; L++) {
                NN=NN+1;
                RAININTE[NN]=0.0;
                RAINDUR[NN]=0.0;
                if (L == KKTD) {
                     RAININTE[NN]=5.0; //unit mm/hr
                     RAINDUR[NN]=DURT;
                }
            }
         }

     }  // end of for J
  
  // in winter season, DURT was always zero, so put the precipitation on the day with RAININTE>0;     
     
     int numprec=0;
     double tothour =0.;
     for (int id =0; id<dinmcurr; id++){
       	if (RAINDUR[id+1]>0){
       	 	numprec++;
       	 	tothour+= RAINDUR[id+1];
       	}	
     }
     
     float sumprec=0.;
     if(numprec>0){
     	double rainrate = mprec/tothour;
     	
     	for (int id =0; id<dinmcurr; id++){
        	precd[id] = RAINDUR[id+1] * rainrate;
        	sumprec+=precd[id];
     	}
     		
     }

}; 

void AtmosUtil::updateDailyDriver(float tad[],const float prevta, const float curta, 
                                  const float nextta, const int & dinmprev, 
		                          const int & dinmcurr, const int & dinmnext){
	int dmax = int(dinmprev/2)+dinmcurr+int(dinmnext/2);
	float temp[dmax],timind[dmax];

	int mmax=3;
	float tamon[mmax], timmon[mmax];
	tamon[0]=prevta;
	tamon[1]=curta;
	tamon[2]=nextta;

	timmon[0] = 1;
	timmon[1] = int(dinmprev/2)+int(dinmcurr/2);
	timmon[2] = dmax;

	for(int ihd=0; ihd <dmax ;ihd++){
		timind[ihd] = ihd+1;
	}
	itp.interpolate(timmon,tamon,mmax, timind,temp,dmax);

	for (int id=0; id<dinmcurr ;id++){
         tad[id]=temp[int(dinmprev/2)+id];
    }
  
}; 
