/*! \file
 * this class updates the position of freezing and thawing fronts using Stefan Algorithm (ATWoo42004a)
 */
#ifndef STEFAN_H_
#define STEFAN_H_

#include <math.h>

#include "../ecodomain/Ground.h"
#include "../inc/ErrorCode.h"
#include "../inc/layerconst.h"

#include "../util/CrankNicholson.h"

class Stefan{
	  public:
		Stefan();
		~Stefan();

	    int itsumall;

	    void setGround(Ground* grndp);

		void updateFronts(const double & tdrv, Layer *topl, Layer *botl,Layer *fstfntl, Layer* lstfntl);

		void updateTemps(const double & tdrv, Layer *topl, Layer *botl, Layer* fstfntl, Layer*lstfntl);

	  private:

		Ground *ground;

		CrankNicholson cns;
	    double ttole;         /*! tolerance of difference*/
	    int ITMAX;            /*! the maximum number of iteration for one time step*/

	    double tleft;         /*! the amount of time left for update (day)*/
	    double tmld;          /*!the last determined time, short for time-last-determined*/

	    /* whether the time step has been changed for last fractional time step
	      * the upper temps should be updated only one time, when the freezing/thawing front first moved,
	      * otherwise, if the temps of upper layers updated everytime the FTFs moved,
	      * the soil temperature would be lower than actual, so put a flag to indicate
	      * that the upper temperature has been updated.
	      * while for the rest soil layers above FTFs, use the lefted degree second
	      *
	      * */
	     bool upperTemps5FrontUpdated;

	     int itsum;
	     double tstep;
	     bool tschanged;

	     double TSTEPMAX;
	     double TSTEPMIN;
	     double TSTEPORG;              /*! the original time step*/

		double temold[MAX_GRN_LAY];

	 	double s[MAX_GRN_LAY+2];
	 	double e[MAX_GRN_LAY+2];
	 	double cn[MAX_GRN_LAY+2];
	 	double cap[MAX_GRN_LAY+2];
	 	double t[MAX_GRN_LAY+2];
	 	double dx[MAX_GRN_LAY+2];
	 	double dxold[MAX_GRN_LAY+2];

	 	double tld[MAX_GRN_LAY+2];
	 	double tid[MAX_GRN_LAY+2];
	 	double tis[MAX_GRN_LAY+2];
	 	double tii[MAX_GRN_LAY+2];
	 	double tit[MAX_GRN_LAY+2];

	 	void processFrontSnowLayer(double const & tkfront, double & dse,
                        double & sumresabv, const double & tdrv, Layer* currl);
	 	void processFrontSoilLayerDown(const int &frozenstate, double const & sumrescum, double const & tkfront ,
	 	                double & dse, double & newfntdz, Layer* currl);
	 	void processFrontSoilLayerUp(const int &frozenstate, double const & sumrescum, double const & tkfront ,
	 	                double & dse, double & newfntdz, Layer* currl);
	 	void frontsDownDeque(const double & newfntz, const int & newfnttype);
	 	void frontsUpDeque(const double & newfntz, const int & newfnttype);

	 	/*get the degree seconds needed to fully freeze/thaw  one or part of one layer*/
	 	double getDegSecNeeded( const double & dz, const double & volwat, const double & tk , const double & sumresabv);
	 
	 	//calculate partial depth based on extra degree seconds
	 	double getPartialDepth(const double & volwat,const double & tk,
 								const double & sumresabv, const double & dse);
 		
	 	void processLayersNofront(Layer* toplayer, const double & tdrv);
	 	void processLayersAbvfront(Layer* toplayer, Layer*fstfntl, const double & tdrv);
	 	void processLayersBlwfront(Layer* toplayer, Layer*lstfntl);
	 	void processLayersBtnfront(Layer *toplayer, Layer*fstfntl, Layer*lstfntl);
    
	 	void iterate(const int &startind, const int &endind, const bool & lstlaybot, const bool & fstlaytop, Layer *toplayer);
	 	int updateOneTimeStep(const int startind, const int & endind, const bool & lstlaybot, const bool & fstlaytop, Layer *toplayer);
	 	int updateOneIteration( const int startind, const int & endind, const bool & lstlaybot, const bool & fstlaytop, Layer *toplayer);
    							
};

#endif /*STEFAN_H_*/
