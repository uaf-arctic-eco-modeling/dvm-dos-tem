#include "GridInputer.h"

GridInputer::GridInputer(){
	
};

GridInputer::~GridInputer(){

}

int GridInputer::init(){

	if(md!=NULL){

	  md->act_gridno  = initGrid(md->grdinputdir);
	  md->act_drainno = initDrainType(md->grdinputdir);
	  md->act_soilno  = initSoilTexture(md->grdinputdir);
	  md->act_gfireno = initFireStatistics(md->grdinputdir);

    }else{
	  std::string msg ="GridInputer::init - ModelData is NULL";
	  cout<<msg+"\n";
	  return -1;
    }
	
	return 0;
}

int GridInputer::initGrid(string& dir){
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

 	int act_gridno = grdD->size();  //actual grid number

 	return act_gridno;

}

int GridInputer::initSoilTexture(string& dir){
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

 	int act_soilidno = soilD->size();  //actual soil dataset number

 	return act_soilidno;

}

int GridInputer::initDrainType(string& dir){
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

 	int act_drainno = drainD->size();  //actual drainage type datset number

 	return act_drainno;

}

int GridInputer::initFireStatistics(string & dir){
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

 	int act_gfireno = gfireD->size();  //actual grid fire dataset number

 	return act_gfireno;

}

//recno - the order (from ZERO) in the .nc file, ids - the real ids in the *.nc files
int GridInputer::getGridids(int & grdid, int &grddrgid, int &grdsoilid,
		int &grdfireid,	const int & recno){
	//netcdf error
	NcError err(NcError::silent_nonfatal);
	NcFile gridFile(gridfname.c_str(), NcFile::ReadOnly);

	NcVar* grdidV = gridFile.get_var("GRIDID");
	if(grdidV==NULL){
		string msg="Cannot get GRIDID in 'grid.nc'! ";
 		cout<<msg+"\n";
 		return -1;
	}
	grdidV->set_cur(recno);
	grdidV->get(&grdid, 1);

	NcVar* drgidV = gridFile.get_var("DRAINAGEID");
	if(drgidV==NULL){
		string msg="Cannot get DRAINAGEID in 'grid.nc'! ";
 		cout<<msg+"\n";
 		return -1;
	}
	drgidV->set_cur(recno);
	drgidV->get(&grddrgid, 1);

	NcVar* soilidV = gridFile.get_var("SOILID");
	if(soilidV==NULL){
		string msg="Cannot get SOILID in 'grid.nc'! ";
 		cout<<msg+"\n";
 		return -1;
	}
	soilidV->set_cur(recno);
	soilidV->get(&grdsoilid, 1);

	NcVar* gfireidV = gridFile.get_var("GFIREID");
	if(gfireidV==NULL){
		string msg="Cannot get GFIREID in 'grid.nc'! ";
 		cout<<msg+"\n";
 		return -1;
	}
	gfireidV->set_cur(recno);
	gfireidV->get(&grdfireid, 1);

	return 0;
}

int GridInputer::getDrainId(int & drainid, const int & recno){
	//netcdf error
	NcError err(NcError::silent_nonfatal);

	NcFile drainFile(drainfname.c_str(), NcFile::ReadOnly);

	NcVar* drainidV = drainFile.get_var("DRAINAGEID");
	if(drainidV==NULL){
		string msg="Cannot get DRAINAGEID in 'drainage.nc'! ";
 		cout<<msg+"\n";
 		return -1;
	}

	drainidV->set_cur(recno);
	drainidV->get(&drainid, 1);

	return 0;
}

int GridInputer::getSoilId(int & soilid, const int & recno){
	//netcdf error
	NcError err(NcError::silent_nonfatal);
	NcFile soilFile(soilfname.c_str(), NcFile::ReadOnly);

	NcVar* soilidV = soilFile.get_var("SOILID");
	if(soilidV==NULL){
		string msg="Cannot get SOILID in 'soiltexture.nc'! ";
 		cout<<msg+"\n";
 		return -1;
	}

	soilidV->set_cur(recno);
	soilidV->get(&soilid, 1);

	return 0;
}

int GridInputer::getGfireId(int &gfireid, const int & recno){
	//netcdf error
	NcError err(NcError::silent_nonfatal);
	NcFile gfireFile(gfirefname.c_str(), NcFile::ReadOnly);

	NcVar* gfireidV = gfireFile.get_var("GFIREID");
	if(gfireidV==NULL){
		string msg="Cannot get GFIREID in 'firestatistics.nc'! ";
 		cout<<msg+"\n";
 		return -1;
	}

	gfireidV->set_cur(recno);
	gfireidV->get(&gfireid, 1);

	return 0;
}

//recid - the order (from ZERO) in the .nc file, gridid - the grid id user-defined in the dataset
void GridInputer::getLatlon(float & lat, float & lon, const int & recid ){

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




