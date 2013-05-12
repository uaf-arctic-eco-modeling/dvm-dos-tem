#include "Controller.h"

Controller::Controller(){

};

Controller::~Controller(){

};

void Controller::ctrl4run(ModelData *md){
 
    ifstream fctr;
 	fctr.open(controlfile.c_str(),ios::in );
 	bool isOpen = fctr.is_open();
    if ( !isOpen ) {
      	cout << "\nCannot open " << controlfile << " in controller\n" ;
      	exit( -1 );
    }

    string comments;

	fctr >> md->casename;   getline(fctr,comments);
  	fctr >> md->configdir;  getline(fctr,comments);
	fctr >> md->runchtfile;  getline(fctr,comments);
	fctr >> md->outputdir;  getline(fctr,comments);
  	fctr >> md->reginputdir;  getline(fctr,comments);
  	fctr >> md->grdinputdir;  getline(fctr,comments);
  	fctr >> md->chtinputdir;  getline(fctr,comments);
  
  	fctr >> md->runstages;    getline(fctr,comments);
  	fctr >> md->initmodes;    getline(fctr,comments);
  	fctr >> md->initialfile;  getline(fctr,comments);

   	fctr >> md->changeclimate;  getline(fctr,comments);
	fctr >> md->changeco2;      getline(fctr,comments);
	fctr >> md->updatelai;      getline(fctr,comments);
	fctr >> md->useseverity;     getline(fctr,comments);

	fctr >> md->outstartyr;     getline(fctr,comments);

	if (md->runmode==1) {
		fctr >> md->outSiteDay;     getline(fctr,comments);
		fctr >> md->outSiteMonth;     getline(fctr,comments);
		fctr >> md->outSiteYear;     getline(fctr,comments);
		fctr >> md->outRegn;     getline(fctr,comments);
	}

  	fctr.close();

};

//BELOW is for java interface
void Controller::assignJcontrolfile (char* jcontrolfile){
    controlfile = string(jcontrolfile);
};

