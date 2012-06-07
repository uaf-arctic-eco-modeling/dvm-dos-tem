#include "GridInputer.h"

GridInputer::GridInputer(){
	
};

GridInputer::~GridInputer(){

}

void GridInputer::init(){
  if(md!=NULL){

	  initGrid(md->grdinputdir);
	  initDrainType(md->grdinputdir);
	  initSoilTexture(md->grdinputdir);
	  initFireStatistics(md->grdinputdir);

  }else{
	  std::string msg ="GridInputer::init - ModelData is NULL";
		cout<<msg+"\n";
		exit(-1);
  }
	
}

void GridInputer::initGrid(string& dir){
	//netcdf error
	NcError err(NcError::silent_nonfatal);

	gridfname = dir +"grid.nc";
	NcFile gridFile(gridfname.c_str(), NcFile::ReadOnly);
 	if(!gridFile.is_valid()){
 		string msg = gridfname+" is not valid";
 		cout<<msg+"\n";
 		exit(-1);
 	}

 	NcDim* grdD = gridFile.get_dim("GRIDID");
 	if(!grdD->is_valid()){
 		string msg = "GRIDID Dimension is not valid in 'grid.nc'! ";
 		cout<<msg+"\n";
 		exit(-1);

 	}

}

void GridInputer::initSoilTexture(string& dir){
	//netcdf error
	NcError err(NcError::silent_nonfatal);

	soilfname = dir +"soiltexture.nc";
	NcFile soilFile(soilfname.c_str(), NcFile::ReadOnly);
 	if(!soilFile.is_valid()){
 		string msg = soilfname+" is not valid";
 		cout<<msg+"\n";
 		exit(-1);
 	}
 	
 	NcDim* soilD = soilFile.get_dim("SOILID");
 	if(!soilD->is_valid()){
 		string msg ="SOILID Dimension is not valid in 'soiltexture.nc'!";
 		cout<<msg+"\n";
 		exit(-1);

 	}

}

void GridInputer::initDrainType(string& dir){
	drainfname = dir +"drainage.nc";

	NcError err(NcError::silent_nonfatal);
	NcFile drainFile(drainfname.c_str(), NcFile::ReadOnly);
 	if(!drainFile.is_valid()){
 		string msg = drainfname+" is not valid";
 		cout<<msg+"\n";
 		exit(-1);
 	}

 	NcDim* drainD = drainFile.get_dim("DRAINAGEID");
 	if(!drainD->is_valid()){
 		string msg = "DRAINAGEID Dimension is not valid in 'drainage.nc'! ";
 		cout<<msg+"\n";
 		exit(-1);

 	}

}

void GridInputer::initFireStatistics(string & dir){
	//netcdf error
	NcError err(NcError::silent_nonfatal);

	gfirefname = dir+"firestatistics.nc";
	NcFile fireFile(gfirefname.c_str(), NcFile::ReadOnly);
 	if(!fireFile.is_valid()){
 		string msg = gfirefname+" is not valid";
 		cout<<msg+"\n";
 		exit(-1);
 	}

 	NcDim* gfireD = fireFile.get_dim("GFIREID");
 	if(!gfireD->is_valid()){
 		string msg="GFIREID Dimension is not valid in grid 'firestatistics.nc' ! ";
 		cout<<msg+"\n";
 		exit(-1);

 	}

 	NcDim* gfsizeD = fireFile.get_dim("GFSIZENO");
 	if(!gfsizeD->is_valid()){
 		string msg="GFSIZE Dimension is not valid in grid 'firestatistics.nc' ! ";
 		cout<<msg+"\n";
 		exit(-1);
 	}

 	NcDim* gfseasonD = fireFile.get_dim("GFSEASONNO");
 	if(!gfseasonD->is_valid()){
 		string msg="GFSEASONNO Dimension is not valid in grid 'firestatistics.nc' ! ";
 		cout<<msg+"\n";
 		exit(-1);
 	}

}

//recid - the order (from ZERO) in the .nc file, gid - the grid id
// if given gid, search for corresponding lat/lon, drainid, soilid, and gfireid
int GridInputer::getGridDataids(float &lat, float &lon, int &drainid, int &soilid,
		int &gfireid, const int &gid){
	//netcdf error
	NcError err(NcError::silent_nonfatal);

	NcFile gridFile(gridfname.c_str(), NcFile::ReadOnly);

	NcVar* grdidV = gridFile.get_var("GRIDID");
	if(grdidV==NULL){
		string msg="Cannot get GRIDID in 'grid.nc'! ";
 		cout<<msg+"\n";
 		exit(-1);
	}

	NcVar* drainidV = gridFile.get_var("DRAINAGEID");
	if(drainidV==NULL){
		string msg="Cannot get DRAINAGEID in 'grid.nc'! ";
 		cout<<msg+"\n";
 		exit(-1);
	}

	NcVar* soilidV = gridFile.get_var("SOILID");
	if(soilidV==NULL){
		string msg="Cannot get SOILID in 'grid.nc'! ";
 		cout<<msg+"\n";
 		exit(-1);
	}

	NcVar* gfireidV = gridFile.get_var("GFIREID");
	if(gfireidV==NULL){
		string msg="Cannot get GFIREID in 'grid.nc'! ";
 		cout<<msg+"\n";
 		exit(-1);
	}

	int id=-1;
	for (int i=0; i<(int)grdidV->num_vals(); i++){
		grdidV->set_cur(i);
		grdidV->get(&id,1);
		if(id==gid) {
			getLatLon(lat, lon, i);

			drainidV->set_cur(i);
			drainidV->get(&drainid,1);

			soilidV->set_cur(i);
			soilidV->get(&soilid,1);

			gfireidV->set_cur(i);
			gfireidV->get(&gfireid,1);

			return i;
		}
	}

	return -1;
}

int GridInputer::getDrainRecid(const int &drainid){
	//netcdf error
	NcError err(NcError::silent_nonfatal);

	NcFile drainFile(drainfname.c_str(), NcFile::ReadOnly);

	NcVar* drainidV = drainFile.get_var("DRAINAGEID");
	if(drainidV==NULL){
		string msg="Cannot get DRAINAGEID in 'drainage.nc'! ";
 		cout<<msg+"\n";
 		exit(-1);
	}

	int id=-1;
	for (int i=0; i<(int)drainidV->num_vals(); i++){
		drainidV->set_cur(i);
		drainidV->get(&id,1);
		if(id==drainid) return i;
	}

	return -1;
}

int GridInputer::getSoilRecid(const int &soilid){
	//netcdf error
	NcError err(NcError::silent_nonfatal);
	NcFile soilFile(soilfname.c_str(), NcFile::ReadOnly);

	NcVar* soilidV = soilFile.get_var("SOILID");
	if(soilidV==NULL){
		string msg="Cannot get SOILID in 'soiltexture.nc'! ";
 		cout<<msg+"\n";
 		exit(-1);
	}

	int id=-1;
	for (int i=0; i<(int)soilidV->num_vals(); i++){
		soilidV->set_cur(i);
		soilidV->get(&id,1);
		if(id==soilid) return i;
	}

	return -1;
}

int GridInputer::getGfireRecid(const int &gfireid){
	//netcdf error
	NcError err(NcError::silent_nonfatal);
	NcFile gfireFile(gfirefname.c_str(), NcFile::ReadOnly);

	NcVar* gfireidV = gfireFile.get_var("GFIREID");
	if(gfireidV==NULL){
		string msg="Cannot get GFIREID in 'firestatistics.nc'! ";
 		cout<<msg+"\n";
 		exit(-1);
	}

	int id=-1;
	for (int i=0; i<(int)gfireidV->num_vals(); i++){
		gfireidV->set_cur(i);
		gfireidV->get(&id,1);
		if(id==gfireid) return i;
	}

	return -1;
}

//recid - the order (from ZERO) in the .nc file, gridid - the grid id user-defined in the dataset
void GridInputer::getLatLon(float & lat, float & lon, const int & recid ){

	NcError err(NcError::silent_nonfatal);
	NcFile gridFile(gridfname.c_str(), NcFile::ReadOnly);

	NcVar* latV = gridFile.get_var("LAT");
 	if(latV==NULL){
 	   string msg="Cannot get LAT in 'grid.nc'! ";
		cout<<msg+"\n";
		exit(-1);
 	}

 	latV->set_cur(recid);
	latV->get(&lat, 1);

 	NcVar* lonV = gridFile.get_var("LON");
 	if(lonV==NULL){
 	   string msg="Cannot get LON in 'grid.nc' ! ";
		cout<<msg+"\n";
		exit(-1);
 	}

 	lonV->set_cur(recid);
	lonV->get(&lon, 1);
} 

void GridInputer::getDrainType(int & dtype, const int & recid){
	NcError err(NcError::silent_nonfatal);

	NcFile drainageFile(drainfname.c_str(), NcFile::ReadOnly);
 	NcVar* drainV = drainageFile.get_var("DRAINAGETYPE");
 	if(drainV==NULL){
  	   string msg="Cannot get DRAINAGETYPE in 'drainage.nc' ! ";
		cout<<msg+"\n";
		exit(-1);
 	}

	drainV->set_cur(recid);
	drainV->get(&dtype, 1);

};

void GridInputer::getSoilTexture(int & topsoil, int & botsoil, const int & recid ){

	NcError err(NcError::silent_nonfatal);
	NcFile soilFile(soilfname.c_str(), NcFile::ReadOnly);

	NcVar* topsoilV = soilFile.get_var("TOPSOIL");
 	if(topsoilV==NULL){
 	   string msg="Cannot get TOPSOIL in 'soiltexture.nc' ! ";
		cout<<msg+"\n";
		exit(-1);
 	}

 	topsoilV->set_cur(recid);
	topsoilV->get(&topsoil, 1);

	NcVar* botsoilV = soilFile.get_var("BOTSOIL");
 	if(botsoilV==NULL){
 	   string msg="Cannot get BOTSOIL in 'soiltexture.nc' ! ";
		cout<<msg+"\n";
		exit(-1);
  	}

 	botsoilV->set_cur(recid);
	botsoilV->get(&botsoil, 1);
} 

void GridInputer::getGfire(int &fri, double pfseason[], double pfsize[], const int & recid ){

	// the following are the currently used in model, and can be modified (actually suggested)
	int fseasonno = 4;   //fire season class no.: 0 - pre-fireseason; 1 - early; 2 - late; 3 - post-fireseason
	int fsizeno   = 5;   //fire-size year class no.: 0 - small; 1 - intermediate; 2 - large; 3 - very large; 4 - ultra-large

	NcError err(NcError::silent_nonfatal);
	NcFile fireFile(gfirefname.c_str(), NcFile::ReadOnly);

	NcVar* friV = fireFile.get_var("FRI");
 	if(friV==NULL){
 	   string msg="Cannot get FRI in 'firestatistics.nc'! ";
		cout<<msg+"\n";
		exit(-1);
 	}
 	friV->set_cur(recid);
	friV->get(&fri, 1);

  	NcVar* fseasonV = fireFile.get_var("PFSEASON");
 	if(fseasonV==NULL){
 	   string msg="Cannot get PFSEASON 'firestatistics.nc'! ";
		cout<<msg+"\n";
		exit(-1);
 	}
	fseasonV->set_cur(recid);
	fseasonV->get(&pfseason[0], fseasonno);

	NcVar* pfsizeV = fireFile.get_var("PFSIZE");
 	if(pfsizeV==NULL){
 	   string msg="Cannot get PFSIZE in 'firestatistics.nc'! ";
		cout<<msg+"\n";
		exit(-1);
 	}
	pfsizeV->set_cur(recid);
	pfsizeV->get(&pfsize[0], fsizeno);

};

void GridInputer::setModelData(ModelData* mdp){
	md = mdp;
};




