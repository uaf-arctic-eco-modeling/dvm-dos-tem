/*
 * This class is used to run processes at region-level
 *  
 */
 
#ifndef RUNREGION_H_
#define RUNREGION_H_

#include <iostream>

#include "../input/RegionInputer.h"
#include "../runmodule/Region.h"

class RunRegion {
	public:
	 	RunRegion();
	 	~RunRegion();

	    int reinit(const int &recid);
	 	
	 	RegionInputer rinputer;
 		Region region;

	private :
 	  		 	 
 		
};
#endif /*RUNREGION_H_*/
