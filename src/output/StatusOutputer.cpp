#include "StatusOutputer.h"

/*! constructor */
StatusOutputer::StatusOutputer(){
 
};

StatusOutputer::~StatusOutputer(){
 	if(statusFile!=NULL){
    	statusFile->close();
		delete statusFile;
 	}
};

void StatusOutputer::init(string& outputdir, string& stage){
	
	string moncfn =outputdir+"status"+stage+".nc";
	statusFile = new NcFile(moncfn.c_str(), NcFile::Replace);
	chtD = statusFile->add_dim("CHTID");
	chtidV =statusFile->add_var("CHTID", ncInt,chtD);
	erroridV =statusFile->add_var("ERRORID", ncInt,chtD);
 	 
};

void StatusOutputer::outputVariables(const int & chtcount){
     
	chtidV->put_rec(&chtid, chtcount);
	erroridV->put_rec(&errorid, chtcount);
 
}



