#ifndef CONTROLLER_H_
	#define CONTROLLER_H_
	#include <string>
	#include <iostream>
	#include <fstream>
	#include <sstream>

	using namespace std;

	#include "ModelData.h"

	class Controller {
 		public:
 
    		Controller();
    		~Controller();
    		
    		string controlfile;
    		void ctrl4run(ModelData *md);

    		//BELOW is for java interface
    		void assignJcontrolfile (char* jcontrolfile);
 				
	};

#endif /*CONTROLLER_H_*/
