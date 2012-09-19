/**
 *  TEM.cpp
 *  main program for running DVM-DOS-TEM
 *  
 *  It runs at 3 run-mods:
 *      (1) site-specific
 *      (2) regional - time series
 * 		(3) regional - spatially (not yet available)
 * 
 * Authors: Shuhua Yi - the original codes
 * 		    Fengming Yuan - re-designing and re-coding for (1) easily code managing;
 *                                        (2) java interface developing for calibration;
 *                                        (3) stand-alone application of TEM (java-c++)
 *                                        (4) inputs/outputs using netcdf format, have to be modified
 *                                        to fix memory-leaks
 *                                        (5) fix the snow/soil thermal/hydraulic algorithms
 *                                        (6) DVM coupled
 * 			Tobey Carman - modifications and maintenance
 *            1) update application entry point with boost command line arg. handling.
 *
 * Affilation: Spatial Ecology Lab, University of Alaska Fairbanks 
 *
 * started: 11/01/2010
 * last modified: 09/18/2012
*/

#include <string>
#include <iostream>
#include <fstream>
#include <sstream>
#include <ctime>
#include <cstdlib>
#include <exception>
using namespace std;

#include "assembler/Runner.h"
#include "ArgHandler.h"

ArgHandler* args = new ArgHandler();

int main(int argc, char* argv[]){
	args->parse(argc, argv);
	if (args->getHelp()){
		args->showHelp();
		return 0;
	}
	
	setvbuf(stdout, NULL, _IONBF, 0);
	setvbuf(stderr, NULL, _IONBF, 0);

	if (args->getMode() == "siterun") {
		time_t stime;
		time_t etime;
		stime=time(0);
		cout<<"run TEM stand-alone - start @"<<ctime(&stime)<<"\n";

		string controlfile = args->getCtrlfile();
		string chtid = args->getChtid();

		Runner siter;

		siter.chtid = atoi(chtid.c_str());

		siter.initInput(controlfile, "siter");

		siter.initOutput();

 		siter.setupData();

 		siter.setupIDs();

 		siter.runmode1();
 
 		etime=time(0);
		cout <<"run TEM stand-alone - done @"<<ctime(&etime)<<"\n";
		cout <<"total seconds: "<<difftime(etime, stime)<<"\n";

	} else if (args->getMode() == "regnrun") {

		time_t stime;
		time_t etime;
		stime=time(0);
		cout <<"run TEM regionally - start @"<<ctime(&stime)<<"\n";

		string controlfile = args->getCtrlfile();
		string runmode = args->getRegrunmode();

		Runner regner;

		regner.initInput(controlfile, runmode);

		regner.initOutput();

		regner.setupData();

		regner.setupIDs();

 		if (runmode.compare("regner1")==0) {
 			regner.runmode2();
 		} else if (runmode.compare("regner2")==0){
 			regner.runmode3();
		} else {

			// Should move this to the ArgHandler class.
			cout <<"run-mode for TEM regional run must be: \n";
			cout <<" EITHER 'regner1' OR 'regner2' \n";
			exit(-1);
		}

		etime=time(0);
		cout <<"run TEM regionally - done @"<<ctime(&etime)<<"\n";
		cout <<"total seconds: "<<difftime(etime, stime)<<"\n";

	}
	
	return 0;

};
