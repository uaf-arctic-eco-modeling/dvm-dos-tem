#include "ModelData.h"

ModelData::ModelData(){
  	consoledebug = true;
  	runmode = 1;

  	runeq = false;
  	runsp = false;
  	runtr = false;
  	runsc = false;

  	initmode =-1;

  	changeclimate= 0;
  	changeco2    = 0;
  	updatelai    = false;
  	useseverity  = false;

	//some options for parallel-computing in the future (but not here)
	myid = 0;
	numprocs = 1;

	// module switches
	envmodule = false;
	bgcmodule = false;
	dslmodule = false;
	dsbmodule = false;
 	friderived= false;
	dvmmodule = false;

	// the data record numbers of all input datasets
	act_gridno = 0;
    act_drainno= 0;
	act_soilno = 0;
	act_gfireno= 0;

	act_chtno    = 0;
	act_initchtno= 0;
	act_clmno    = 0;
	act_clmyr    = 0;
	act_vegno    = 0;
	act_vegset   = 0;
	act_fireno   = 0;
	act_fireset  = 0;


};

ModelData::~ModelData(){

}

void ModelData::checking4run(){

 	//run stage
 	if(runstages == "eq"){
   		runeq = true;
 	}else if(runstages == "sp"){
   		runsp = true;
 	}else if(runstages == "tr"){
   		runtr = true;
 	}else if(runstages == "sc"){
   		runsc = true;
 	}else if(runstages == "eqsp"){
   		runeq = true;
   		runsp = true;
 	}else if(runstages == "sptr"){
   		runsp = true;
   		runtr = true;
 	}else if(runstages == "eqsptr"){
   		runeq = true;
   		runsp = true;
   		runtr = true;
 	}else if(runstages == "all"){
   		runeq = true;
   		runsp = true;
   		runtr = true;
   		runsc = false;
 	}else {
 		cout <<"the run stage " << runstages << "  was not recoganized  \n";
		cout <<"should be one of 'eq', 'sp', 'tr','sc', 'eqsp', 'sptr', 'eqsptr', or 'all'";
    	exit(-1);
 	}

 	//initilization modes for state variables
 	if(initmodes =="default"){
 		initmode =1;
 	}else if(initmodes =="sitein"){
 		initmode =2;
 	}else if(initmodes =="restart"){
 		initmode =3;
 	}else{
    	cout <<"the initialize mode " << initmodes << "  was not recoganized  \n";
		cout <<"should be one of 'default', 'sitein', or 'restart'";
    	exit(-1);
 	}

	//model run I/O directory checking
 	if (outputdir == "") {
 		cout <<"directory for output was not recoganized  \n";
    	exit(-1);
 	}
 	if (reginputdir == "") {
 		cout <<"directory for Region-level iutput was not recoganized  \n";
    	exit(-1);
 	}
 	if (grdinputdir == "") {
 		cout <<"directory for Grided data iutput was not recoganized  \n";
    	exit(-1);
 	}

 	if (chtinputdir == "") {
 		cout <<"directory for cohort data iutput was not recoganized  \n";
    	exit(-1);
 	}

 	if (initialfile == "" && initmode==2) {
 		cout <<"directory for sitein file was not recoganized  \n";
    	exit(-1);
 	}

 	if (initialfile == "" && initmode==3) {
 		cout <<"directory for restart file was not recoganized  \n";
    	exit(-1);
 	}

};

