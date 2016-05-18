//
//  Slave.h
//  dvm-dos-tem
//
//  Created by Tobey Carman on 9/26/13.
//  2013 Spatial Ecology Lab.
//

#ifndef _SLAVE_
#define _SLAVE_

#include <iostream>
#include <vector>
#include <sstream>

#include "../data/RestartData.h"

class Slave{
public:

  std::vector<int> cohort_list;

  Slave();
  Slave(int rank);
  void recv_cohort_list_from_master();
  void send_progress_update_to_master(int year, int month, int cohort);
  void send_restartdata_to_master(RestartData rd);
  void pp_cohort_list();
  std::string cl_to_string();

private:
  int rank;
  
};


#endif /* _SLAVE_ */



