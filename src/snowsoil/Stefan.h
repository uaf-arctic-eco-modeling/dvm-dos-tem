/*! \file
 * this class updates the position of freezing and thawing fronts using Stefan Algorithm (ATWoo42004a)
 */
#ifndef STEFAN_H_
#define STEFAN_H_

#include <cmath>
#include <vector>

#include "../ecodomain/Ground.h"
#include "../inc/errorcode.h"
#include "../inc/layerconst.h"

#include "../util/CrankNicholson.h"

class Stefan{
	  public:
		Stefan();
		~Stefan();

		bool debugging;
	    int itsumall;

	    void setGround(Ground* grndp);
	    void initpce();
		void updateFronts(const double & tdrv, const double &timestep);

	  private:

		Ground *ground;
		Layer *botdrvl;

	 	void meltingSnowLayer(double const & tkfront, double & dse,
                        double & sumresabv, const double & tdrv, Layer* currl);
	 	void processNewFrontSoilLayerDown(const int &frozenstate, double const & sumrescum, double const & tkfront ,
	 	                double & dse, double & newfntdz, Layer* currl);
	 	void frontsDequeDown(const double & newfntz, const int & newfnttype);
	 	void processNewFrontSoilLayerUp(const int &frozenstate, double const & sumrescum, double const & tkfront ,
	 	                double & dse, double & newfntdz, Layer* currl);
	 	void frontsDequeUp(const double & newfntz, const int & newfnttype);

	 	double prepareBottomDriving();

	 	//get the degree seconds needed to fully freeze/thaw  one or part of one layer
	 	double getDegSecNeeded( const double & dz, const double & volwat, const double & tk , const double & sumresabv);
	 	//calculate partial depth based on extra degree seconds
	 	double getPartialDepth(const double & volwat,const double & tk,
 								const double & sumresabv, const double & dse);

        void combineExtraFronts();
        void updateLayerFrozenState(Layer* toplayer);
        void updateWaterAfterFront(Layer* toplayer);

 		
};

#endif /*STEFAN_H_*/
