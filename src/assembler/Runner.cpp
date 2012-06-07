
#include "Runner.h"

Runner::Runner(){
	chtid = -1;
	error = 0;
};

Runner::~Runner(){
	
};

void Runner::initInput(const string &controlfile, const string &runmode){

		cout <<"Starting initialization ...\n";
		cout <<"control file: "+controlfile+"\n";
		cout <<"TEM run mode: "+runmode+"\n";

		//Input and processing for reading parameters and passing them to controller
 		configin.controlfile=controlfile;

 		//
 		if (runmode.compare("siter")==0) {
 		  	md.runmode = 1;
 		} else if (runmode.compare("regner1")==0) {
 			md.runmode = 2;                            //regional run - time-series
 		} else if (runmode.compare("regner2")==0) {
 			md.runmode = 3;                            //regional run - spatially (NOT yet configured!)
 		} else {
 			cout <<"TEM run mode: "+runmode+" must be ONE of:\n";
 			cout <<"'siter', 'regner1', or, 'regner2'\n";
 			exit(-1);
 		}

 		//
 		if (md.runmode!=1) md.consoledebug=false;

 		configin.ctrl4run(&md);   //read in model configure info from "config/controlfile_site.txt"
		md.checking4run();

		// timer initialization
		timer.setModeldata(&md);

		//region-level input
 		runreg.rinputer.setModelData(&md);		//for getting the directory infos from ModelData
 		runreg.rinputer.init();			        //checking data file

 		//grid-level input
 		rungrd.ginputer.setModelData(&md);      //for getting the directory infos from ModelData
 		rungrd.ginputer.init();			        //checking data file

 		//cohort-level input
 		runcht.cinputer.init(md.chtinputdir);                //checking data file
 		if (md.runmode==2 || md.runmode==3) {
 			createCohortList4Run();   // the running cohort list, if multple-cohort run mode on
 		} else if (md.runmode==1) {
 	   		runchtlist.push_back(1);   // "1" is the default chtid
 		}

 		//initial conditions
 		if (md.initmode==3){
 		 	if(md.runeq){
 		 		cout <<"cannot set initmode as restart for equlibrium run  \n";
 		 		cout <<"reset to 'lookup'\n";
 		 		md.initmode=1;
 		 	} else {
 		 		runcht.resinputer.init(md.initialfile);
 		 	}

 		} else if (md.initmode==2) {
            // will add later
 		} else if (md.initmode==1) {
 			// initial condition from 'chtlup'
 		}
 		 
 		// pass the 'md' switches/controls/options to two major running modules 'rungrd' and 'runcht'
 		rungrd.setModelData(&md);
 		runcht.setModelData(&md);

};

//output setting-up
void Runner::initOutput() {

		string stage = "-"+md.runstages;

 		// 1)for general outputs
		if (md.runmode==1) {   //very detailed output for ONE cohort ONLY

	    	string dimfname ="";
	    	string envfname ="";
	    	string bgcfname ="";

			if (md.outSiteDay){
				envfname = md.outputdir+"cmtenv_dly"+stage+".nc";
				runcht.envdlyouter.init(envfname);				// set netcdf files for output
			}

			if (md.outSiteMonth){
				dimfname = md.outputdir+"cmtdim_mly"+stage+".nc";
				runcht.dimmlyouter.init(dimfname);				// set netcdf files for output

				envfname = md.outputdir+"cmtenv_mly"+stage+".nc";
				runcht.envmlyouter.init(envfname);				// set netcdf files for output

				bgcfname = md.outputdir+"cmtbgc_mly"+stage+".nc";
				runcht.bgcmlyouter.init(bgcfname);				// set netcdf files for output
			}

			if (md.outSiteYear){
				dimfname = md.outputdir+"cmtdim_yly"+stage+".nc";
				runcht.dimylyouter.init(dimfname);				// set netcdf files for output

				envfname = md.outputdir+"cmtenv_yly"+stage+".nc";
				runcht.envylyouter.init(envfname);				// set netcdf files for output

				bgcfname = md.outputdir+"cmtbgc_yly"+stage+".nc";
				runcht.bgcylyouter.init(bgcfname);				// set netcdf files for output
			}

	     } else if (md.runmode==2 || md.runmode==3){
			 // output options (switches)
	    	 md.outRegn      = true;
			 md.outSiteYear  = false;
			 md.outSiteDay   = false;
			 md.outSiteMonth = false;

	     } else {
	    	 md.outRegn=false;
	    	 md.outSiteYear=false;
	    	 md.outSiteDay=false;
	    	 md.outSiteMonth=false;
	     }

		// 2) summarized output by a list of variables
		if (md.outRegn) {

			// varlist
			 string outlistfile = "config/outvarlist.txt";
			 createOutvarList(outlistfile);

			// output years
			int maxoutyrs = 0;
			if (md.runsp) {
				maxoutyrs += MAX_SP_YR;
			}
			if (md.runtr) {
				maxoutyrs += MAX_TR_YR;
			}
			if (md.runsc) {
				maxoutyrs += MAX_SC_YR;
			}

			runcht.regnouter.setOutData(&runcht.regnod);
			runcht.regnouter.init(md.outputdir, stage, maxoutyrs);	 //set netcdf files for output, note NOT output from "eq" run
		 }

 		// 3)for restart.nc outputs
		runcht.resouter.init(md.outputdir, stage);       //define netcdf file for restart output

};

//set up data connection and data pointer initialization
void Runner::setupData(){

		// input data connection
		rungrd.grid.setRegionData(&runreg.region.rd);

 		runcht.cht.setModelData(&md);
 		runcht.cht.setTime(&timer);
 		runcht.cht.setInputData(&runreg.region.rd, &rungrd.grid.gd);

 		// process data connection
 		runcht.cht.setProcessData(&chted, &chtbd, &chtfd);  //

 		// initializing pointers data connection used in 'runcht' and parameters/default initial condition
 		string cmtname = "cmt";
 		runcht.initData(cmtname);

 		//initializing pointers used in called modules in one 'cht'
 		runcht.cht.initSubmodules();

};

void Runner::run(){

	//read-in region-level data (Yuan: this is the portal for multiple region run, if needed in the future)
	error = runreg.reinit(0);          //can be modified, if more than 1 record of data
	if (error!=0){
  		cout <<"problem in reinitialize regional-module in Runner::run\n";
  		exit(-1);
	}
	
	//loop through cohorts
	list<int>::iterator jj ;
	for ( jj=runchtlist.begin() ; jj!=runchtlist.end(); jj++){
		chtid = *jj;
		setupIDs();

		//getting the grided data for a cohort
		error = rungrd.reinit(runcht.cht.cd.grdid);
		if (error!=0){
			cout <<"problem in reinitialize grid-module in Runner::run\n";
			exit(-1);
		}
			
		//getting the cohort data
		error = runcht.readData();

		error = runcht.reinit(chtid);

		if (error!=0) {
			cout<<"Error for reinit cohort: "<<chtid<<" - EXITS! \n";
			exit(-3);
		} else {
			cout<<"cohort: "<<chtid<<" - running! \n";
			runcht.run();
		}

		runcht.cohortcount++;
	}

};

// make IDs consistent through all data sets
int Runner::setupIDs(){

		// NOTE: 'chtid' must be assigned a value before
		runcht.cht.cd.chtid = chtid;
		int chtrec=runcht.cinputer.getChtDataids(runcht.cht.cd.inichtid, runcht.cht.cd.grdid,
				runcht.cht.cd.clmid, runcht.cht.cd.vegid, runcht.cht.cd.fireid, chtid);
	  	if (chtrec<0) return -4;

	    return 0;

};

void Runner::createCohortList4Run(){
	// read in a list of cohorts to run

	//netcdf error
	NcError err(NcError::silent_nonfatal);

	//open file and check if valid
	string filename = md.runchtfile;
	NcFile runFile(filename.c_str(), NcFile::ReadOnly);
 	if(!runFile.is_valid()){
 		string msg = filename+" is not valid";
 		cout<<msg+"\n";
 		exit(-1);
 	}

 	NcDim* chtD = runFile.get_dim("CHTID");
 	if(!chtD->is_valid()){
 		string msg="CHT Dimension is not valid in createCohortList4Run";
 		cout<<msg+"\n";
 		exit(-1);
 	}

 	NcVar* chtV = runFile.get_var("CHTID");
 	if(chtV==NULL){
 		string msg="Cannot get CHTID in createCohortList4Run";
 		cout<<msg+"\n";
 		exit(-1);
 	}

 	int numcht = chtD->size();

	int chtid  = -1;
	int chtid0 = -1;
	int chtidx = -1;
	for (int i=0; i<numcht; i++){
		chtV->set_cur(i);
   		chtV->get(&chtid, 1);
   		runchtlist.push_back(chtid);

	   	if (i==0) chtid0=chtid;
	   	if (i==numcht-1) chtidx=chtid;
   	}

	cout <<md.casename << ": " <<numcht <<"  cohorts to be run @" <<md.runstages<< "\n";
	cout <<"   from:  " <<chtid0<<"  to:  " <<chtidx <<"\n";

};

void Runner::createOutvarList(string & txtfile){

	string outvarfile = txtfile;

 	ifstream fctr;
 	fctr.open(outvarfile.c_str(),ios::in );
 	bool isOpen = fctr.is_open();
    if ( !isOpen ) {
      	cout << "\nCannot open " << outvarfile << "  \n" ;
      	exit( -2 );
    }

    string comments;

	getline(fctr, comments);
	getline(fctr, comments);

	int varno = I_outvarno;
	for (int ivar=0; ivar<varno; ivar++) {
		fctr >> runcht.regnod.outvarlist[ivar];
		getline(fctr, comments);
	}

 	fctr.close();

};



