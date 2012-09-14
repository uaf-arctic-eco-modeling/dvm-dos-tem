/*
 * This class is used to run a cohort: from input to output
 *  
 */
 
#ifndef RUNCOHORT_H_
#define RUNCOHORT_H_

#include <iostream>
#include <vector>
using namespace std;

//local headers
#include "../input/CohortInputer.h"
#include "../input/RestartInputer.h"
//#include "../input/SiteInputer.h"

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

		/* all cohort data id lists
		 * ids are labeling the datasets, which exist in 5 *.nc files
	 	 * and, the order (index, staring from 0) in these lists are actually record no. in the *.nc files
	 	 */
		vector<int> chtids;   // 'cohortid.nc'
		vector<int> chtinitids;
		vector<int> chtgridids;
		vector<int> chtclmids;
		vector<int> chtvegids;
		vector<int> chtfireids;

		vector<int> chtdrainids;  // from 'grid.nc' to 'cohortid.nc', related by 'GRIDID'
		vector<int> chtsoilids;
		vector<int> chtgfireids;

		vector<int> initids;  // 'restart.nc' or 'sitein.nc'
		vector<int> clmids;   // 'climate.nc'
		vector<int> vegids;   // 'vegetation.nc'
		vector<int> fireids;  // 'fire.nc'

		/* the following is FOR one cohort only (current cohort)
		 *
		 */
	 	int cohortcount;
	 	int initrecno;
	 	int clmrecno;
	 	int vegrecno;
	 	int firerecno;

	 	int used_atmyr;
	    int yrstart;
	    int yrend;

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
 		int allchtids();

 		void init();
	    int readData();
	    int reinit();

     	void run_cohortly();

		void run_monthly();

	private :
 	  		 	 
		ModelData *md;

		int dstepcnt;   //day timesteps since starting output
	    int mstepcnt;   //month timesteps since starting output
	    int ystepcnt;   //year timesteps since starting output

		void runEnvmodule();
 		void run_timeseries();

};
#endif /*RUNCOHORT_H_*/
