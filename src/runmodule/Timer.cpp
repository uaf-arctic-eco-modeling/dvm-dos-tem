/*! \file
 * Time Related Class for TEM
 */

#include "Timer.h"

Timer::Timer(){
	yearind = 0;
 	monind  = 0;
  	outyrind = 0;
 	
 	// Yuan: the following is calculated from those in timeconst.h 
	maxeqrunyrs=MAX_EQ_YR;
  
	spbegyr = BEG_SP_YR;
	spendyr = END_SP_YR;
	trbegyr = BEG_TR_YR;
	trendyr = END_TR_YR;
	scbegyr = BEG_SC_YR;
	scendyr = END_SC_YR;
	
	spnumyr = spendyr-spbegyr+1;
	trnumyr = trendyr-trbegyr+1;
	scnumyr = scendyr-scbegyr+1;
	
};
 
Timer::~Timer(){

};

void Timer::setModeldata(ModelData *mdp){
	md = mdp;
};

void Timer::reset(){
  	yearind    = 0;
  	stageyrind = 0;
  	monind     = 0;

  	eqend = false;
  	spend = false;
  	trend = false;
  	scend = false;

  	outyrind = 0;
};
 

void Timer::advanceOneMonth(){
   	monind++;
   	if(monind>=12){
   		monind =0;
   		yearind++;
   		stageyrind++;
   	}
};

int Timer::getCalendarYear(){

	if(!eqend){
	  	return stageyrind;
	} else if (!spend) {
		return stageyrind+spbegyr;
	} else if (!trend) {
		return stageyrind+trbegyr;
	} else if (!scend) {
		return stageyrind+scbegyr;
	}

	return 0;
};

int Timer::getOutputYearIndex(){

	if (md->outstartyr != MISSING_I) {
		int calyr = getCalendarYear();
		outyrind = calyr-md->outstartyr;
		if (outyrind<0) outyrind = 0;
	} else {
		outyrind = yearind;
	}
  	return outyrind;
};

int Timer::getCurrentYearIndex(){
   	return yearind;
};

int Timer::getDOYIndex(const int &mind, const int &did){
  // here the mon is month index, starting from 0 - 11 for Jan. - Dec.
  // id is day index
  	int doy = DOYINDFST[mind]+ did;
 	return doy;
};
 
int Timer::getDaysInMonth(int & monind){
   	return DINM[monind];
};
 
int Timer::getCurrentMonthIndex(){
 	return monind;
};
 
int Timer::getNextMonthIndex(){
 	int next = monind+1;
 	if(next ==-1) next =11;
 	if(next ==12) next =0;
 	return next;
};
 
