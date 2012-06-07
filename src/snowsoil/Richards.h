
/*!\file
 * Implementation of Richard's law for soil water dynamics*/
 
#ifndef RICHARDS_H_
#define RICHARDS_H_

#include <math.h>

#include "../data/CohortData.h"
#include "../data/EnvData.h"

#include "../ecodomain/layer/Layer.h"
#include "../ecodomain/layer/SoilLayer.h"
#include "../util/CrankNicholson.h"

class Richards{
	public :
		Richards();
		~Richards();
	
		int itsum;
		int itsumabv;
		int itsumblw;

		int numal;
		double qdrain;
	
		void update(Layer *fstsoill, Layer* drainl, const double & draindepth, const double & fbaseflow,
		 	       double trans[MAX_SOI_LAY], const double & evap, const double & infil);

		void setCohortData(CohortData* cdp);
		void setEnvData(EnvData* edp);

		CrankNicholson cn;
	
	private:
		void prepareSoilNodes(Layer *fstsoill, Layer *drainl, const double & draindepth);

		void iterate(const double trans[], const double & evap,
	               const double & infil, const double & fbaseflow);
	    int updateOneTimeStep();
	    int updateOneIteration();

		double qinfil;
		double qevap;
	    double qtrans[MAX_SOI_LAY];
	    double fbaseflow;

		double dzmm[MAX_SOI_LAY];   // layer thickness in mm
		double zmm[MAX_SOI_LAY];   // layer top depth in mm
		double poro[MAX_SOI_LAY];      //porosity
		double effporo[MAX_SOI_LAY];   //effective porosity (minus ice volume)
		double liq[MAX_SOI_LAY];
		double minliq[MAX_SOI_LAY];
		double maxliq[MAX_SOI_LAY];
		double psisat[MAX_SOI_LAY];
		double hksat[MAX_SOI_LAY];
		double bsw[MAX_SOI_LAY];

		double drainldzadj;      //adjusting factor (0 - 1) for the drainage layer's thickness
		double qin[MAX_SOI_LAY];
		double qout[MAX_SOI_LAY];

		double amx[MAX_SOI_LAY];
		double bmx[MAX_SOI_LAY];	
		double cmx[MAX_SOI_LAY];
		double rmx[MAX_SOI_LAY];		
		double dwat[MAX_SOI_LAY];    
		double hk[MAX_SOI_LAY];    
		double dhkdw[MAX_SOI_LAY];     
		double smp[MAX_SOI_LAY];       
		double dsmpdw[MAX_SOI_LAY];
		double liqii[MAX_SOI_LAY];
		double liqit[MAX_SOI_LAY];
		double liqis[MAX_SOI_LAY];
		double liqid[MAX_SOI_LAY];
		double liqld[MAX_SOI_LAY];

    	double liqtole;	/*! tolerance of difference*/
		int ITMAX; /*! the maximum number of iteration for one time step*/      
		double tleft; /*! the amount of time left for update (day)*/     
		double tmld;    /*!the last determined time, short for time-last-determined*/    

		bool tschanged;   // whether the time step has been changed for last factional time step
		double tstep;     
		double  TSTEPMIN;
		double  TSTEPMAX;
    
		double TSTEPORG; /*! the original time step*/
 
};

#endif /*RICHARD_H_*/
