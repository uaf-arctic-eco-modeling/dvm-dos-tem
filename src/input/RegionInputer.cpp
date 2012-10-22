#include "RegionInputer.h"

RegionInputer::RegionInputer(){
	
};

RegionInputer::~RegionInputer(){

};

void RegionInputer::init(){

	if(md!=NULL){

  		act_co2yr = initCO2file(md->reginputdir);

  	}else{
  		string msg = "inputer in RegionInputer::init is null";
 		cout<<msg+"\n";
 		exit(-1);
  	}

};

int RegionInputer::initCO2file(string &dir){
	//netcdf error
	NcError err(NcError::silent_nonfatal);

	co2filename = dir +"co2.nc";
	if (md->runsc) co2filename = dir +"co2_sc.nc";  //Yuan: read in CO2 ppm from projection

	NcFile co2File(co2filename.c_str(), NcFile::ReadOnly);
 	if(!co2File.is_valid()){
 		string msg = co2filename + " is not valid";
 		cout << msg + "\n";
 		//exit(-1);
		co2filename = dir + "co2.nc";
 		cout << "WARNING: Running with historic co2 (" << co2filename <<")\n";
 	}
 	
 	NcDim* yrD = co2File.get_dim("YEAR");
 	if(!yrD->is_valid()){
  		string msg = "YEAR Dimension is not Valid in RegionInputer::initCO2file";
 		cout<<msg+"\n";
 		exit(-1);
 	}
 	int yrs = yrD->size();

 	return yrs;
}

void RegionInputer::getCO2(RegionData *rd){
	NcError err(NcError::silent_nonfatal);

	NcFile co2File(co2filename.c_str(), NcFile::ReadOnly);
 	NcVar* co2yrV = co2File.get_var("YEAR");
 	 	
 	NcVar* co2V = co2File.get_var("CO2");
 	if(co2yrV==NULL || co2V==NULL){
 	   string msg = "Cannot get CO2 in RegionInputer::getCO2 ";
		cout<<msg+"\n";
		exit(-1);
 	}

	NcBool nb1 = co2yrV->get(&rd->co2year[0], rd->act_co2yr);
	NcBool nb2 = co2V->get(&rd->co2[0], rd->act_co2yr);
	if(!nb1 || !nb2){
	 string msg = "problem in reading CO2 in RegionInputer::getCO2 ";
		cout<<msg+"\n";
		exit(-1);
	}

	co2File.close();
}

void RegionInputer::setModelData(ModelData* mdp){
   	md = mdp;
};

