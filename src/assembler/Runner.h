/*  Runner.h
 *
 *  Runner is a general class used to:
 *
 *  1) Initialize all the necessary classes
 *  2) get I/O
 *  3) run one or more cohort(s)
 *
 */

#ifndef RUNNER_H_
#define RUNNER_H_
#include <string>
#include <iostream>
#include <fstream>
#include <sstream>

#include "RunRegion.h"
#include "RunGrid.h"
#include "RunCohort.h"

#include "../runmodule/Controller.h"
#include "../runmodule/ModelData.h"

#include <vector>
#include <deque>

using namespace std;

class Runner {
	public:
		Runner();
		~Runner();

		int chtid;    /* currently-running 'cohort' id */
		int error;    /* error index */

		void initInput(const string &controlfile, const string &runmode); /* general initialization */
		void initOutput();
		void setupData();
		void setupIDs();

		/* three settings for running TEM */
    	void runmode1();  /* one site run-mode, used for stand-alone TEM for any purpose */
    	void runmode2();  /* multi-site (regional) run-mode 1, i.e., time series */
    	void runmode3();  /* multi-site (regional) run-mode 2, i.e., spatially */
    	int runSpatially(const int icalyr, const int im, const int jj);

    	vector<int> runchtlist;  //a vector listing all cohort id
 	    vector<float> runchtlats;  //a vector of latitudes for all cohorts in order of 'runchtlist'
 	    vector<float> runchtlons;  //a vector of longitudes for all cohorts in order of 'runchtlist'

    	/* all data record no. lists FOR all cohorts in 'runchtlist', IN EXACTLY SAME ORDER, for all !
    	 * the 'record' no. (starting from 0) is the order in the netcdf files
    	 * for all 'chort (cell)' in the 'runchtlist',
    	 * so, the length of all these lists are same as that of 'runchtlist'
    	 * will save time to search those real data ids if do the ordering in the first place
    	 * */

    	/* from grided-data (geo-referenced only, or grid-level)*/
    	vector<int> reclistgrid;
    	vector<int> reclistdrain;
    	vector<int> reclistsoil;
    	vector<int> reclistgfire;

    	/* from grided-/non-grided and time-series data (cohort-level)*/
    	vector<int> reclistinit;
    	vector<int> reclistclm;
    	vector<int> reclistveg;
    	vector<int> reclistfire;

	private:

    	//TEM domains (hiarchy)
    	RunRegion runreg;
		RunGrid rungrd;
    	RunCohort runcht;

    	//Inptuer
    	Controller configin;
        
    	//data classes
    	ModelData md;     /* model controls, options, switches and so on */

    	EnvData  grded;   // grid-aggregated 'ed' (not yet done)
    	BgcData  grdbd;   // grid-aggregared 'bd' (not yet done)

    	EnvData  chted;   // withing-grid cohort-level aggregated 'ed' (i.e. 'edall in 'cht')
    	BgcData  chtbd;
    	FirData  chtfd;

    	deque<RestartData> mlyres;

		//util
		Timer timer;

    	void createCohortList4Run();
		void createOutvarList(string & txtfile);
	
};
#endif /*RUNNER_H_*/
