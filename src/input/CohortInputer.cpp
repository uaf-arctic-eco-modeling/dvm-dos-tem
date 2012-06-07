#include "CohortInputer.h"

CohortInputer::CohortInputer(){

};

CohortInputer::~CohortInputer(){

};

void CohortInputer::init(string &chtinputdir){

  		initChtidFile(chtinputdir);

  		act_clmyr   = initClmFile(chtinputdir);
  		act_vegset  = initVegFile(chtinputdir);
		act_fireset = initFireFile(chtinputdir);

};

void CohortInputer::initChtidFile(string& dir){
	chtidfname = dir +"cohortid.nc";

	NcError err(NcError::silent_nonfatal);
	NcFile chtidFile(chtidfname.c_str(), NcFile::ReadOnly);
 	if(!chtidFile.is_valid()){
 		string msg = chtidfname+" is not valid";
 		cout<<msg+"\n";
 		exit(-1);
 	}
 	
 	NcDim* chtD = chtidFile.get_dim("CHTID");
 	if(!chtD->is_valid()){
 		string msg = "CHTD Dimension is no Valid in ChtidFile";
 		cout<<msg+"\n";
 		exit(-1);
 	}
 	
};

int CohortInputer::initClmFile(string& dir){
	//netcdf error
	NcError err(NcError::silent_nonfatal);

	clmfname = dir+"climate.nc";

	NcFile clmncFile(clmfname.c_str(), NcFile::ReadOnly);
 	if(!clmncFile.is_valid()){
 		string msg = clmfname+" is not valid";
 		cout<<msg+"\n";
 		exit(-1);
 	}

 	NcDim* clmD = clmncFile.get_dim("CLMID");
 	if(!clmD->is_valid()){
 		string msg = "CLMID Dimension is not valid in 'climate.nc' !";
 		cout<<msg+"\n";
 		exit(-1);
 	}

 	NcDim* yrD = clmncFile.get_dim("YEAR");
 	if(!yrD->is_valid()){
 		string msg = "YEAR Dimension is not valid in 'climate.nc' !";
 		cout<<msg+"\n";
 		exit(-1);
 	}


 	NcDim* monD = clmncFile.get_dim("MONTH");
 	if(!monD->is_valid()){
 		string msg = "MONTH Dimension is not valid in 'climate.nc' !";
 		cout<<msg+"\n";
 		exit(-1);
 	}

 	int act_clmyr = yrD->size();  //actual atm data years

 	return act_clmyr;

}

int CohortInputer::initVegFile(string& dir){
	vegfname = dir +"vegetation.nc";

	NcError err(NcError::silent_nonfatal);
	NcFile vegncFile(vegfname.c_str(), NcFile::ReadOnly);
 	if(!vegncFile.is_valid()){
 		string msg = vegfname+" is not valid";
 		cout<<msg+"\n";
 		exit(-1);
 	}

 	NcDim* vegD = vegncFile.get_dim("VEGID");
 	if(!vegD->is_valid()){
 		string msg = "VEGID Dimension is not valid in 'Vegtation.nc'!";
 		cout<<msg+"\n";
 		exit(-1);
 	}

 	NcDim* vegsetD = vegncFile.get_dim("VEGSET");
 	if(!vegsetD->is_valid()){
 		string msg = "VEGSET Dimension is not valid in 'Vegtation.nc'!";
 		cout<<msg+"\n";
 		exit(-1);
 	}



 	int act_vegset=vegsetD->size();  //actual vegetation data sets

 	return act_vegset;

};

int CohortInputer::initFireFile(string& dir){
	firefname = dir +"fire.nc";

	NcError err(NcError::silent_nonfatal);
	NcFile firencFile(firefname.c_str(), NcFile::ReadOnly);
 	if(!firencFile.is_valid()){
 		string msg = firefname+" is not valid";
 		cout<<msg+"\n";
 		exit(-1);
 	}

 	NcDim* chtD = firencFile.get_dim("FIREID");
 	if(!chtD->is_valid()){
 		string msg = "FIREID Dimension is not valid in 'fire.nc'!";
 		cout<<msg+"\n";
 		exit(-1);
 	}

 	NcDim* fireyrD = firencFile.get_dim("FIRESET");
 	if(!fireyrD->is_valid()){
 		string msg = "FIRESET Dimension is not valid in 'fire.nc'! ";
 		cout<<msg+"\n";
 		exit(-1);
 	}

 	int act_fireset=fireyrD->size();  //actual fire data years

 	return act_fireset;
};

int CohortInputer::getChtDataids(int & inichtid, int & grdid, int & clmid,  int & vegid,
		int & fireid, const int &chtid){
	NcError err(NcError::silent_nonfatal);

	NcFile chtidFile(chtidfname.c_str(), NcFile::ReadOnly);
 	NcVar* chtidV = chtidFile.get_var("CHTID");
 	if(chtidV==NULL){
 	   string msg = "Cannot get CHTID in 'cohortid.nc' file! ";
		cout<<msg+"\n";
		exit(-1);
 	}

 	NcVar* inichtidV = chtidFile.get_var("INITCHTID");
 	if(inichtidV==NULL){
 	   string msg = "Cannot get INITCHTID in 'cohortid.nc' file! ";
		cout<<msg+"\n";
		exit(-1);
 	}

 	NcVar* grdidV = chtidFile.get_var("GRIDID");
 	if(grdidV==NULL){
 	   string msg = "Cannot get GRIDID in 'cohortid.nc' file! ";
		cout<<msg+"\n";
		exit(-1);
 	}

 	NcVar* clmidV = chtidFile.get_var("CLMID");
 	if(clmidV==NULL){
 	   string msg = "Cannot get CLMID in 'cohortid.nc' file! ";
		cout<<msg+"\n";
		exit(-1);
 	}

 	NcVar* vegidV = chtidFile.get_var("VEGID");
 	if(vegidV==NULL){
 	   string msg = "Cannot get VEGID in 'cohortid.nc' file! ";
		cout<<msg+"\n";
		exit(-1);
 	}

 	NcVar* fireidV = chtidFile.get_var("FIREID");
 	if(fireidV==NULL){
 	   string msg = "Cannot get FIREID in 'cohortid.nc' file! ";
		cout<<msg+"\n";
		exit(-1);
 	}

 	int id =-1;
	for (int i=0; i<(int)chtidV->num_vals(); i++){
		chtidV->set_cur(i);
		chtidV->get(&id, 1);
		if(id==chtid) {
			inichtidV->get(&inichtid, 1);
			grdidV->get(&grdid, 1);
			clmidV->get(&clmid, 1);
			vegidV->get(&vegid, 1);
			fireidV->get(&fireid, 1);

			return i;                // return a record index i for no error
		}
	}

	return -1;                       // return -1 for error

};

int CohortInputer::getClmRec(const int &clmid){
	NcError err(NcError::silent_nonfatal);

	NcFile clmFile(clmfname.c_str(), NcFile::ReadOnly);
 	NcVar* clmidV = clmFile.get_var("CLMID");
 	if(clmidV==NULL){
 	   string msg = "Cannot get CLMID in 'climate.nc' file! ";
		cout<<msg+"\n";
		exit(-1);
 	}

	int id=-1;
	for (int i=0; i<(int)clmidV->num_vals(); i++){
		clmidV->set_cur(i);
		clmidV->get(&id, 1);
		if(id==clmid) return i;
	}

	return -1;
};

int CohortInputer::getVegRec(const int &vegid){
	NcError err(NcError::silent_nonfatal);

	NcFile vegFile(vegfname.c_str(), NcFile::ReadOnly);
 	NcVar* vegidV = vegFile.get_var("VEGID");
 	if(vegidV==NULL){
 	   string msg = "Cannot get VEGID in 'vegetation.nc' file! ";
		cout<<msg+"\n";
		exit(-1);
 	}

	int id=-1;
	for (int i=0; i<(int)vegidV->num_vals(); i++){
		vegidV->set_cur(i);
		vegidV->get(&id, 1);
		if(id==vegid) return i;
	}

	return -1;
};

int CohortInputer::getFireRec(const int &fireid){
	NcError err(NcError::silent_nonfatal);

	NcFile fireFile(firefname.c_str(), NcFile::ReadOnly);
 	NcVar* fireidV = fireFile.get_var("FIREID");
 	if(fireidV==NULL){
 	   string msg = "Cannot get FIREID in 'fire.nc' file! ";
		cout<<msg+"\n";
		exit(-1);
 	}

	int id=-1;
	for (int i=0; i<(int)fireidV->num_vals(); i++){
		fireidV->set_cur(i);
		fireidV->get(&id, 1);
		if(id==fireid) return i;
	}

	return -1;
};

// read-in clm data for ONE year and ONE record only
void CohortInputer::getClimate(float tair[], float prec[], float nirr[], float vapo[],
		const int & yrs, const int & recid){

	int nummon = 12;

	//read the data from netcdf file
	NcError err(NcError::silent_nonfatal);
	NcFile clmFile(clmfname.c_str(), NcFile::ReadOnly);

 	NcVar* taV = clmFile.get_var("TAIR");
 	if(taV==NULL){
 	    string msg = "Cannot get TAIR in 'climate.nc' \n";
 		cout<<msg+"\n";
 		exit(-1);
 	}

 	NcVar* nirrV = clmFile.get_var("NIRR");
 	if(nirrV==NULL){
 	    string msg = "Cannot get NIRR in 'climate.nc' \n";
 		cout<<msg+"\n";
 		exit(-1);
 	}

 	NcVar* precV = clmFile.get_var("PREC");
 	if(precV==NULL){
 	   string msg = "Cannot get PREC in 'climate.nc' \n";
		cout<<msg+"\n";
		exit(-1);
 	}

 	NcVar* vapV = clmFile.get_var("VAPO");
 	if(vapV==NULL){
 	    string msg = "Cannot get VAPO in 'climate.nc' ";
 		cout<<msg+"\n";
 		exit(-1);
 	}

 	//get the data for ONE recid
	taV->set_cur(recid, 0, 0);
	NcBool nb1 = taV->get(&tair[0], 1, yrs, nummon);
	if(!nb1){
	 	string msg = "problem in reading TAIR in CohortInputer::getClimate";
 		cout<<msg+"\n";
 		exit(-1);
	}

	precV->set_cur(recid, 0, 0);
	NcBool nb2 = precV->get(&prec[0], 1, yrs, nummon);
	if(!nb2){
		string msg = "problem in reading PREC in CohortInputer::getClimate ";
 		cout<<msg+"\n";
 		exit(-1);
	}

	nirrV->set_cur(recid, 0, 0);
	NcBool nb3 = nirrV->get(&nirr[0], 1, yrs, nummon);
	if(!nb3){
		string msg = "problem in reading NIRR in CohortInputer::getClimate";
 		cout<<msg+"\n";
 		exit(-1);
	}

	vapV->set_cur(recid, 0, 0);
	NcBool nb4 = vapV->get(&vapo[0], 1, yrs, nummon);
	if(!nb4){
	 	string msg = "problem in reading VAPO in CohortInputer::getClimate";
 		cout<<msg+"\n";
 		exit(-1);
	}

};

// read-in vegetation data for ONE record only
void CohortInputer::getVegetation(int vsetyr[], int vtype[], double vfrac[], const int &recid){
	NcError err(NcError::silent_nonfatal);

	NcFile vegFile(vegfname.c_str(), NcFile::ReadOnly);

	NcVar* vegsetyrV = vegFile.get_var("VEGSETYR");
 	if(vegsetyrV==NULL){
  	   string msg = "Cannot get vegetation fraction VEGSETYR in 'vegetation.nc'! ";
		cout<<msg+"\n";
		exit(-1);
 	}

 	NcVar* vegtypeV = vegFile.get_var("VEGTYPE");
 	if(vegtypeV==NULL){
  	   string msg = "Cannot get vegetation type VEGTYPE in 'vegetation.nc'! ";
		cout<<msg+"\n";
		exit(-1);
 	}

 	NcVar* vegfracV = vegFile.get_var("VEGFRAC");
 	if(vegfracV==NULL){
  	   string msg = "Cannot get vegetation type VEGTYPE in 'vegetation.nc'! ";
		cout<<msg+"\n";
		exit(-1);
 	}

	vegsetyrV->set_cur(recid);
	vegsetyrV->get(&vsetyr[0], act_vegset, 1);

	vegtypeV->set_cur(recid);
	vegtypeV->get(&vtype[0], act_vegset, 1);

	vegfracV->set_cur(recid);
	vegfracV->get(&vfrac[0], act_vegset, 1);

};

// read-in fire data, except for 'severity', for ONE record only
void CohortInputer::getFire(int fyear[], int fseason[], int fsize[], const int & recid){

	NcError err(NcError::silent_nonfatal);
	NcFile fireFile(firefname.c_str(), NcFile::ReadOnly);

	NcVar* yearV = fireFile.get_var("YEAR");
 	if(yearV==NULL){
 	   string msg = "Cannot get fire YEAR in 'fire.nc'! ";
		cout<<msg+"\n";
		exit(-1);
 	}
	yearV->set_cur(recid);
	NcBool nb1 = yearV->get(&fyear[0], 1, act_fireset);
	if(!nb1){
	    string msg = "problem in reading fire year data";
 		cout<<msg+"\n";
 		exit(-1);
	}

 	NcVar* seasonV = fireFile.get_var("SEASON");
 	if(seasonV==NULL){
  	   string msg = "Cannot get fire SEASON in 'fire.nc'! ";
		cout<<msg+"\n";
		exit(-1);
  	}
	seasonV->set_cur(recid);
	NcBool nb2 = seasonV->get(&fseason[0], 1, act_fireset);
	if(!nb2){
	    string msg = "problem in reading fire season data";
 		cout<<msg+"\n";
 		exit(-1);
	}

	NcVar* sizeV = fireFile.get_var("SIZE");
	if(sizeV==NULL){
	 	string msg = "Cannot get fire SIZE in 'fire.nc'! ";
 		cout<<msg+"\n";
 		exit(-1);
	}
	sizeV->set_cur(recid);
	NcBool nb3 = sizeV->get(&fsize[0], 1, act_fireset);
	if(!nb3){
	    string msg = "problem in reading fire size data";
 		cout<<msg+"\n";
 		exit(-1);
	}

};

// read-in fire 'severity', for ONE record only
void CohortInputer::getFireSeverity(int fseverity[], const int & recid){
	NcError err(NcError::silent_nonfatal);
	NcFile fireFile(firefname.c_str(), NcFile::ReadOnly);

	NcVar* fsevV = fireFile.get_var("SEVERITY");
	if(fsevV==NULL){
	 	string msg = "Cannot get fire SEVERITY in 'fire.nc'! ";
 		cout<<msg+"\n";
 		exit(-1);
	}
	fsevV->set_cur(recid);
	NcBool nb = fsevV->get(&fseverity[0], 1, act_fireset);
	if(!nb){
	    string msg = "problem in reading fire SEVERITY in 'fire.nc'! ";
 		cout<<msg+"\n";
 		exit(-1);
	}

};
