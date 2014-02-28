#include <exception>

#include "ModelData.h"

#include "../TEMLogger.h"

/** Returns true for 'on' and false for 'off'.
 * Throws exception if s is not "on" or "off".
 * might want to inherit from std exception or do something else?
 */
bool onoffstr2bool(const std::string &s) {
  if (s.compare("on") == 0) {
    return true;
  } else if (s.compare("off") == 0) {
    return false;
  } else {
    throw std::runtime_error("Invalid string! Must be 'on' or 'off'.");
  }
}

/** Returns a string with first colum r justified and 
 * of with 'w'. Can be used to build tables likle this:
 * 
 *       somestr: 0
 *       somestr: 0
 *       somestr: 0
 * 
 *  with a newline, for use in a table.     
 */
std::string table_row(int w, std::string d, bool v) {
  std::stringstream s;
  s << std::setw(w) << std::setfill(' ') << d << ": " << v << "\n"; 
  return s.str();
}


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
	set_envmodule(false);
	set_bgcmodule(false);
  set_dvmmodule(false);
	set_dslmodule(false);
	set_dsbmodule(false);
 	set_friderived(false);

	// the data record numbers of all input datasets
	act_gridno = 0;
    act_drainno= 0;
	act_soilno = 0;
	act_gfireno= 0;

	act_chtno    = 0;
	act_initchtno= 0;
	act_clmno    = 0;
	act_clmyr_beg= 0;
	act_clmyr_end= 0;
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

bool ModelData::get_envmodule() {
  return this->envmodule; 
}
void ModelData::set_envmodule(const std::string &s) {
  BOOST_LOG_SEV(glg, info) << "Setting envmodule to " << s;
  this->envmodule = onoffstr2bool(s);
}
void ModelData::set_envmodule(const bool v) {
  BOOST_LOG_SEV(glg, info) << "Setting envmodule to " << v;
  this->envmodule = v;
}

bool ModelData::get_bgcmodule() {
  return this->bgcmodule; 
}
void ModelData::set_bgcmodule(const std::string &s) {
  BOOST_LOG_SEV(glg, info) << "Setting bgcmodule to " << s;
  this->bgcmodule = onoffstr2bool(s);
}
void ModelData::set_bgcmodule(const bool v) {
  BOOST_LOG_SEV(glg, info) << "Setting bgcmodule to " << v;
  this->bgcmodule = v;
}

bool ModelData::get_dvmmodule() {
  return this->dvmmodule; 
}
void ModelData::set_dvmmodule(const std::string &s) {
  BOOST_LOG_SEV(glg, info) << "Setting dvmmodule to " << s;
  this->dvmmodule = onoffstr2bool(s);
}
void ModelData::set_dvmmodule(const bool v) {
  BOOST_LOG_SEV(glg, info) << "Setting dvmmodule to " << v;
  this->dvmmodule = v;
}

bool ModelData::get_dslmodule() {
  return this->dslmodule; 
}
void ModelData::set_dslmodule(const std::string &s) {
  BOOST_LOG_SEV(glg, info) << "Setting dslmodule to " << s;
  this->dslmodule = onoffstr2bool(s);
}
void ModelData::set_dslmodule(const bool v) {
  BOOST_LOG_SEV(glg, info) << "Setting dslmodule to " << v;
  this->dslmodule = v;
}

bool ModelData::get_dsbmodule() {
  return this->dsbmodule; 
}
void ModelData::set_dsbmodule(const std::string &s) {
  BOOST_LOG_SEV(glg, info) << "Setting dsbmodule to " << s;
  this->dsbmodule = onoffstr2bool(s);
}
void ModelData::set_dsbmodule(const bool v) {
  BOOST_LOG_SEV(glg, info) << "Setting dsbmodule to " << v;
  this->dsbmodule = v;
}

bool ModelData::get_friderived() {
  return this->friderived; 
}
void ModelData::set_friderived(const std::string &s) {
  BOOST_LOG_SEV(glg, info) << "Setting friderived to " << s;
  this->friderived = onoffstr2bool(s);
}
void ModelData::set_friderived(const bool v) {
  BOOST_LOG_SEV(glg, info) << "Setting friderived to " << v;
  this->friderived = v;
}


std::string ModelData::describe_module_settings(){
  std::stringstream s;
  s << table_row(15, "envmodule", this->get_envmodule());
  s << table_row(15, "bgcmodule", this->bgcmodule);
  s << table_row(15, "dvmmodule", this->dvmmodule);

  s << table_row(15, "dslmodule", this->dslmodule);
  s << table_row(15, "dsbmodule", this->dsbmodule);

  s << table_row(15, "friderived", this->friderived);
  s << table_row(15, "nfeed", this->nfeed);
  s << table_row(15, "avlnflg", this->avlnflg);
  return s.str();  
}


