#include "Organic.h"

Organic::Organic(){
	
};

Organic::~Organic(){

};

void Organic::initShlwThicknesses(const double & thickness){

	shlwnum   = 0;
	if( thickness<=0.00){
	 shlwdz[0]=MISSING_D;
	 shlwdz[1]=MISSING_D;
	 shlwdz[2]=MISSING_D;
	 shlwnum =0;
	}else if (thickness<0.04){
	 shlwdz[0]=thickness;
	 shlwdz[1]=MISSING_D;
	 shlwdz[2]=MISSING_D;
	 shlwnum =1;		
	}else if (thickness<0.06){
	 shlwdz[0]=0.02;
	 shlwdz[1]=thickness -0.02;
	 shlwdz[2]=MISSING_D;
	 shlwnum =2;		
	}else if (thickness<0.10){
	 shlwdz[0]=0.03;
	 shlwdz[1]=thickness -0.03;
	 shlwdz[2]=MISSING_D;
	 shlwnum =2;		
	}else if (thickness<0.15){
	 shlwdz[0]=0.02;
	 shlwdz[1]=0.04;
	 shlwdz[2]=thickness -0.06;
	 shlwnum =3;		
	}else if (thickness<0.20){
	 shlwdz[0]=0.03;
	 shlwdz[1]=0.06;
	 shlwdz[2]=thickness -0.09;
	 shlwnum =3;	
	 }else if (thickness<0.28){
	 shlwdz[0]=0.04;
	 shlwdz[1]=0.08;
	 shlwdz[2]=thickness -0.12;
	 shlwnum =3;		
	}else if (thickness<0.40){
	 shlwdz[0]=0.05;
	 shlwdz[1]=0.11;
	 shlwdz[2]=thickness -0.16;
	 shlwnum =3;				
	}else if (thickness >=0.4) {
	 shlwdz[0]=0.1;
	 shlwdz[1]=0.2;
	 shlwdz[2]=thickness -0.3;
	 shlwnum =3;
	}

	shlwthick = thickness;
	if (shlwnum>0) lstshlwdz = shlwdz[shlwnum-1];
};



void Organic::initDeepThicknesses(const double & thickness){
	
	deepthick = thickness;
	if(thickness<0.0)deepthick =0.0;
	
	deepnum =0;
	if(lstshlwdz>0){
		if(deepthick < 3* lstshlwdz){
			deepdz[0]=deepthick;
			deepdz[1]=MISSING_D;
			deepdz[2]=MISSING_D;
			deepnum =1;
		}else if(deepthick >= 3* lstshlwdz && deepthick<6*lstshlwdz){
			deepdz[0]=1./3. * deepthick;
			deepdz[1]=2./3. * deepthick;
			deepdz[2]=MISSING_D;
			deepnum =2;
		}else {
			deepdz[0]=1./6. * deepthick;
			deepdz[1]=2./6. * deepthick;
			deepdz[2]=3./6. * deepthick;
			deepnum =3;
	 	
		}

	}else{
		if(deepthick <= 0.02){
			deepdz[0]=deepthick;
			deepdz[1]=MISSING_D;
			deepdz[2]=MISSING_D;
			deepnum =1;
		}else if(deepthick<=0.06){
			deepdz[0]=1./3. * deepthick;
			deepdz[1]=2./3. * deepthick;
			deepdz[2]=MISSING_D;
			deepnum =2;
		}else {
			deepdz[0]=1./6. * deepthick;
			deepdz[1]=2./6. * deepthick;
			deepdz[2]=3./6. * deepthick;
			deepnum =3;

		}
	}
	
};

// if shlw peat thickness from input soil profile
void Organic::setShlwThicknesses(int soiltype[], double soildz[], const int & soilmaxnum){
	shlwnum   = 0;
	shlwthick = 0;
   	for(int i=0; i<soilmaxnum; i++){
   	  if(soiltype[i] ==1){
   	  	shlwdz[shlwnum] = soildz[i];
   	  	shlwnum ++;
   	  	shlwthick += soildz[i];
   	  }else {
   	  	 if(soiltype[i]>2){
   	  		 break;
   	  	 }
   	  }
   	} 
};

// if deep peat thickness from input soil profile
void Organic::setDeepThicknesses(int soiltype[], double soildz[],const int & soilmaxnum){
	deepnum =0;
	deepthick =0;
	
	for(int i=0;i<soilmaxnum; i++){
   	  if(soiltype[i] ==2){
   	  	deepdz[deepnum] = soildz[i];
   	  	deepnum ++;
   	  	deepthick += soildz[i];
   	  }else {
   	  	 if(soiltype[i]>2){
   	  		 break;
   	  	 }
   	  }
   }
   
};

