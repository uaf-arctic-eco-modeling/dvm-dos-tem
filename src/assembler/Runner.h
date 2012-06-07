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

#include "RunRegion.h"
#include "RunGrid.h"
#include "RunCohort.h"

#include "../runmodule/Controller.h"
#include "../runmodule/ModelData.h"

#include <list>
using namespace std;

class Runner {
	public:
		Runner();
		~Runner();

		list<int> runchtlist;
		int chtid;
		int error;

		void initInput(const string &controlfile, const string &runmode); // set pointer between classes
		void initOutput();
		void setupData();

    	void run();



    private:
    	//TEM domains (hiarchy)
    	RunRegion runreg;
		RunGrid rungrd;
    	RunCohort runcht;

    	//Inptuer
    	Controller configin;
        
    	//data classes
    	ModelData md;

    	EnvData  grded;   // all-grid level 'ed'
    	BgcData  grdbd;

    	EnvData  chted;   // all-cht level 'ed' (i.e. 'edall in 'cht')
    	BgcData  chtbd;
    	FirData  chtfd;

		//util
		Timer timer;

		int setupIDs();
    	void createCohortList4Run();
		void createOutvarList(string & txtfile);
	
};
#endif /*RUNNER_H_*/
