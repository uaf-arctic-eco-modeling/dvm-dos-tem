
/*!\file
 * Implementation of Richard's law for soil water dynamics*/
 
#ifndef RICHARDS_H_
#define RICHARDS_H_

#include <cmath>
#include <limits>

#include "../data/CohortData.h"
#include "../data/EnvData.h"

#include "../ecodomain/layer/Layer.h"
#include "../ecodomain/layer/SoilLayer.h"
#include "../util/CrankNicholson.h"

class Richards{
	public :
		Richards();
		~Richards();
	
		bool debugging;
		int itsum;

		int indx0sl; // first soil layer index applied for Richards Equation
		int indx0al; // active layers' first layer index
		int numal;   // active layers' layer numbers
		double qdrain; // mm/day
	
		void update(Layer *fstsoill, Layer* bdrainl, const double & bdraindepth, const double & fbaseflow,
		 	       double trans[MAX_SOI_LAY], const double & evap, const double & infil, const double &ts);

		void setCohortData(CohortData* cdp);
		void setEnvData(EnvData* edp);

		CrankNicholson cn;
	
	private:

		void prepareSoilNodes(Layer *currsoill, const double & draindepth);

		void iterate(const double trans[], const double & evap,
	               const double & infil, const double & fbaseflow);
	    int updateOnethTimeStep(const double &fbaseflow);
	    int updateOneIteration(const double &fbaseflow);

	    Layer * drainl;

		double qinfil;
		double qevap;
	    double qtrans[MAX_SOI_LAY+1];    // +1, is for easily match-up of soil layer index (starting from 1 in 'ground')
                                         // var[0] will not used here
		double dzmm[MAX_SOI_LAY+1];      // layer thickness in mm
		double zmm[MAX_SOI_LAY+1];       // layer top depth in mm
		double effporo[MAX_SOI_LAY+1];   //effective porosity (minus minliq volume)
		double effliq[MAX_SOI_LAY+1];
		double effminliq[MAX_SOI_LAY+1];
		double effmaxliq[MAX_SOI_LAY+1];
		double psisat[MAX_SOI_LAY+1];
		double hksat[MAX_SOI_LAY+1];
		double bsw[MAX_SOI_LAY+1];

		double hk[MAX_SOI_LAY+1];
		double dhkdw[MAX_SOI_LAY+1];
		double smp[MAX_SOI_LAY+1];
		double dsmpdw[MAX_SOI_LAY+1];
		double qin[MAX_SOI_LAY+1];
		double qout[MAX_SOI_LAY+1];

		double liqii[MAX_SOI_LAY+1];
		double liqit[MAX_SOI_LAY+1];
		double liqis[MAX_SOI_LAY+1];
		double liqid[MAX_SOI_LAY+1];
		double liqld[MAX_SOI_LAY+1];

		double amx[MAX_SOI_LAY+1];
		double bmx[MAX_SOI_LAY+1];
		double cmx[MAX_SOI_LAY+1];
		double rmx[MAX_SOI_LAY+1];
		double dwat[MAX_SOI_LAY+1];

    	double timestep;  // one timestep in seconds
		double tleft;     // the amount of time left for update (fraction of one timestep)

		bool tschanged;   // whether the time step has been changed for last factional time step
		double tstep;     // actual fraction of one timestep for iteration
    	double LIQTOLE;	  // tolerance of difference
		double TSTEPMIN;  // min. fraction of one timestep
		double TSTEPMAX;  // max. fraction of one timestep
		double TSTEPORG;  // the original time step

	 	 double mindzlay; // min. layer thickness (meters) for stable Richards' solution

 
};

#endif /*RICHARD_H_*/
