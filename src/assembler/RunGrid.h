/*
 * This class is used to run a cohort: from input to output
 *  
 */
 
#ifndef RUNGRID_H_
#define RUNGRID_H_

#include <iostream>

#include "../input/GridInputer.h"
#include "../runmodule/Grid.h"

class RunGrid {
	public:
	 	RunGrid();
	 	~RunGrid();
	 	
 		Grid grid;
 		GridInputer ginputer;

 		void setModelData(ModelData * mdp);

 		int reinit(const int &grdid);

	private:
 		ModelData *md;

};
#endif /*RUNGRID_H_*/
