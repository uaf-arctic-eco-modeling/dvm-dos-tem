/*! this class is used to output the state in the netcdf format
 */
#ifndef STATUSOUTPUTER_H_
	#define STATUSOUTPUTER_H_
	
	#include "netcdfcpp.h"
	#include <iostream>
	#include <string>
	#include <sstream>
	#include <ctime>
	#include <cstdlib>
	
	using namespace std;
	using std::string;
 
	#include "../inc/timeconst.h"

	class StatusOutputer {
		public :
			StatusOutputer();
			~StatusOutputer();

	 
			void init(string& dir, string& stage);
			void  outputVariables(const int & chtcount);

			NcFile* statusFile;

    		bool runeq;
    		bool runsp;
    		bool runtr;
    
    		int chtid;
    		int errorid;
     
   	private:
   			NcDim* chtD;
			NcVar* chtidV;
			NcVar* erroridV;  	
	};

#endif /*STATUSOUTPUTER_H_*/
