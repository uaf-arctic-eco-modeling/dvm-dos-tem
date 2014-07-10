//
//  Master.h
//  dvm-dos-tem
//
//  Created by Tobey Carman on 9/25/13.
//  2013 Spatial Ecology Lab.
//

#ifndef _MASTER_
#define _MASTER_

#include <iostream>
#include <vector>
#include <netcdfcpp.h>

#include "../data/RestartData.h"

class Master {
public:
  
  Master();
  Master(int, int);
  
  void dispense_cohorts_to_slaves(const std::vector<int>& cohort_list);
  void get_restartdata_and_progress_from_slaves(int total_num_cohorts);
  
  
  //void listen_for_progress_update();
  
  //RestartData * listen_for_restart_data();
  
private:
  int rank;
  int processors;
  
  NcFile setup_restartnc_file(int num_records);
  void write_cohort_record_to_restartnc_file(const NcFile &rfile, const RestartData rd, int record);
  
  //bool compare_cohortids_asc(const RestartData lhs, const RestartData rhs);
  //bool compare_cohortids_dec(const RestartData lhs, const RestartData rhs);

};


#endif /* _MASTER_) */
