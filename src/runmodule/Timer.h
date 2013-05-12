#ifndef TIMER_H_
#define TIMER_H_
/*! \file
 * Time Related Class for TEM
 */

#include <iostream>

#include "ModelData.h"
#include "../inc/timeconst.h"
#include "../inc/cohortconst.h"
#include "../inc/errorcode.h"

class Timer{
	public:
		Timer();
		~Timer();

		ModelData *md;

	 	int yearind;
		int monind;
		int stageyrind;
		int outyrind;

		bool eqend;
		bool spend;
		bool trend;
		bool scend;

		int maxeqrunyrs;		/*! number of eq-run years*/

		int spbegyr;		/*! beginning year of spinup*/
		int spendyr;		/*! end year of spin up*/
		int spnumyr;      /*! number of spin years*/

		int trbegyr;
		int trendyr;
		int trnumyr;
				
		int scbegyr;		/*! beginning year of scenrio simulation*/
		int scendyr;		/*! end year of scenrio simulation*/
		int scnumyr;		/*! number of scenrio simulation year*/

		void setModeldata(ModelData *mdp);
		void reset();

		int getOutputYearIndex();
	    int getCalendarYear();

	    int getDOYIndex(const int &mon, const int &id);
		int getDaysInMonth(int & mon);
		int getCurrentMonthIndex();
		int getNextMonthIndex();
		int getCurrentYearIndex();

		void advanceOneMonth();
	
	private:

};

#endif /*TIMER_H_*/
