/*
 * This class is used to run a cohort: from input to output
 *  
 */
 
#ifndef RUNCOHORT_H_
#define RUNCOHORT_H_

#include <iostream>

//local headers
#include "../input/CohortInputer.h"
#include "../input/RestartInputer.h"
//#include "../input/SiteInputer.h"

#include "../output/StatusOutputer.h"
#include "../output/ChtOutputer.h"
#include "../output/EnvOutputer.h"
#include "../output/BgcOutputer.h"
#include "../output/RestartOutputer.h"
#include "../output/RegnOutputer.h"

#include "../runmodule/Cohort.h"

class RunCohort {
	public:
	 	RunCohort();
	 	~RunCohort();

	 	int cohortcount;
	 	// the index (from 0) of data for a chort in their .nc input files
	 	int inichtind;

 		Cohort cht;

 		// Output data (extracted from model's data structure)
    	OutDataRegn regnod;
    	RestartData resod;

    	//I/O operators
  		CohortInputer cinputer;
 		RestartInputer resinputer;
 		//SiteInputer *sinputer;

 		ChtOutputer dimmlyouter;
 		ChtOutputer dimylyouter;

 		EnvOutputer envdlyouter;
 		EnvOutputer envmlyouter;
 		EnvOutputer envylyouter;
 		
 		BgcOutputer bgcmlyouter;
 		BgcOutputer bgcylyouter;

 		RegnOutputer regnouter;
        RestartOutputer resouter;

 		void setModelData(ModelData * mdp);
 		void initData(string & cmttype);

	    int readData();
	    int reinit(const int &cid);

     	void run();

	private :
 	  		 	 
		ModelData *md;

	    int usedatmyr;

	    int yrstart;
	    int yrend;
	    int dstepcnt;
	    int mstepcnt;
	    int ystepcnt;

		void runEquilibrium();
 		void runSpinup();
 		void runTransit();
 		void runScenario();

 		void modulerun();

};
#endif /*RUNCOHORT_H_*/
