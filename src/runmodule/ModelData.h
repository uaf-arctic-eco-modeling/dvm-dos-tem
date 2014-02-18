#ifndef MODELDATA_H_
	#define MODELDATA_H_
	#include <string>
	#include <iostream>
	#include <fstream>
	#include <sstream>
    #include <cstdlib>
    #include "../TEMLogger.h"

	using namespace std;

	class ModelData{
 		public:

    		ModelData();
    		~ModelData();
    std::string describe_module_settings();
    		int myid;            // these two are for parallel model run (NOT USED)
    		int numprocs;

    		int runmode;  //1: site; 2: region - time-series; 3: region - spatially
    		bool consoledebug;   // more info will display when running


			// the following 3 switches will control N modules in BGC
	     	bool nfeed;      //=true allowing N uptake limited by soil conditions, which then controls plant growth,
	     	                 //   basically it's a switch for soil-plant N process modules
   		    bool avlnflg;    // inorganic N in/out module on (true) or not (false) - partial open N cycle
	     	bool baseline;   //=true allowing ninput and nlost to be used for adjusting c/n of soil - partial open N cycle

			// the following are from Controller.cpp (reading from '????control.txt')
    		bool runeq;
    		bool runsp;
    		bool runtr;
    		bool runsc;
     		int initmode;

   			string casename;
  			string configdir;
  			string runchtfile;       //must be *.nc format file
 			string outputdir;
  			string reginputdir;
  			string grdinputdir;
  			string chtinputdir;
 			string runstages;

  			string initmodes;
  			string initialfile;      //either the restart.nc, or sitein.nc file, upon initmodes

    		int changeclimate;      // 0: default (up to run stage); 1: dynamical; -1: static
     		int changeco2;          // 0: default (up to run stage); 1: dynamical; -1: static
    		bool updatelai;         // dynamical LAI in model or static LAI (from 'chtlu')
    		bool useseverity;       // using fire severity inputs

    		int  outstartyr;        // output starting calendar year (-9999 is for model starting year)
   			bool outSiteDay;
   			bool outSiteMonth;
   			bool outSiteYear;
   			bool outRegn;
   			bool outSoilClm;

   	 		// the data record numbers of all input datasets
   			// grided data (1D)
   	 		int act_gridno;
   	 		int act_drainno;
   	 		int act_soilno;
   	 		int act_gfireno;

   	 		// chort-level data (2D or 3D)
   	 		int act_chtno;
   	 		int act_initchtno;
   	 		int act_clmno;  // climate data in clmid-year-month(12) (3D)
   	 		int act_clmyr_beg;
   	 		int act_clmyr_end;
   	 		int act_clmyr;
   	 		int act_vegno;  // vegetation community data in vegid-yearset (2D)
   			int act_vegset;
   	 		int act_fireno; // fire data in fireid-yearset (2D)
   			int act_fireset;

   			//
    		void checking4run();

    bool get_envmodule();
    void set_envmodule(const std::string &s);
    void set_envmodule(const bool v);

    bool get_bgcmodule();
    void set_bgcmodule(const std::string &s);
    void set_bgcmodule(const bool v);

    bool get_dvmmodule();
    void set_dvmmodule(const std::string &s);
    void set_dvmmodule(const bool v);

    bool get_dslmodule();
    void set_dslmodule(const std::string &s);
    void set_dslmodule(const bool v);
    
    bool get_dsbmodule();
    void set_dsbmodule(const std::string &s);
    void set_dsbmodule(const bool v);

    bool get_friderived();
    void set_friderived(const std::string &s);
    void set_friderived(const bool v);
    
  private:
      bool envmodule;   // (Bio)physical module on/off
      bool bgcmodule;   // BGC module on/off
      bool dvmmodule;   // dynamic vegetation module on/off

      bool dslmodule;   // dynamic soil layer module on/off
      bool dsbmodule;   // disturbance module on/off
      bool friderived;  // option for switching Grid-level fire occurrence (upon FRI)

      static severity_channel_logger_t& glg;

	};

#endif /*MODELDATA_H_*/
