//
//  Slave.cpp
//  dvm-dos-tem
//
//  Created by Tobey Carman on 9/26/13.
//  2013 Spatial Ecology Lab.
//

#include <mpi.h>
#include <sstream>

#include "Slave.h"
#include "../data/RestartData.h"
#include "../inc/tbc_mpi_constants.h"

#include "../TEMLogger.h"

extern src::severity_logger< severity_level > glg;

Slave::Slave(){}
Slave::Slave(int rank): rank(rank) {}

void Slave::pp_cohort_list(){
  std::cout << "This slaves cohort list: ";
  for (std::vector<int>::const_iterator cit = cohort_list.begin(); cit != cohort_list.end(); ++cit) {
    std::cout << *cit << ", ";
  }
  std::cout << "\n";
}
std::string Slave::cl_to_string(){
  std::stringstream ss;
  for (std::vector<int>::const_iterator cit = cohort_list.begin(); cit != cohort_list.end(); ++cit) {
    ss << *cit << ", ";
  }
  return ss.str();
}
void Slave::recv_cohort_list_from_master(){
  // listen for incoming message with cohort number to run
  MPI_Status status;
  int number_of_ints_to_recieve;
  
  // listen for anything from the master...
  MPI_Probe(0, MPI_ANY_TAG, MPI_COMM_WORLD, &status);
  
  // When probe returns, the status object has the size and other
  // attributes of the incoming message. Get the size of the message
  MPI_Get_count(&status, MPI_INT, &number_of_ints_to_recieve);
  
  // finally, get the message. It should have a number telling us which cohort to run,
  // (based on our processor number)
  int cohorts[number_of_ints_to_recieve];
  MPI_Recv(&cohorts,
           number_of_ints_to_recieve,
           MPI_INT,
           0,               // listening for messages from master
           MPI_ANY_TAG,
           MPI_COMM_WORLD,
           &status);

  std::stringstream ss;
  ss << "I am a slave (rank " << this->rank << ") and just recieved my list of cohorts to run: ";
  for (int i = 0 ; i < number_of_ints_to_recieve; ++i) {
    ss << cohorts[i] << ", ";
    cohort_list.push_back(cohorts[i]);
  }
  BOOST_LOG_SEV(glg, note) << ss.str();
}


void Slave::send_restartdata_to_master(RestartData rd){
  MPI_Datatype MPI_t_RestartData;
  MPI_t_RestartData = rd.register_mpi_datatype();

  BOOST_LOG_SEV(glg, info) << "SHOULD BE SENDING RESTART DATA TO MASTER?"; // send rd
  // send a message to the master saying we are done...
  //int my_restart_data = 12345;
  MPI_Send(&rd, 1, MPI_t_RestartData, 0, PTEM_RESTARTDATA_TAG, MPI_COMM_WORLD);
  BOOST_LOG_SEV(glg, info) << "Message (with custom restart data type) has been sent to master!";
  
  MPI_Type_free(&MPI_t_RestartData); // not sure if this is the best place to
  // call this...seems easy to forget to
  // to do this...

  
}


void Slave::send_progress_update_to_master(int yr, int month, int cohort){

  int yr_mon_cht[3];
  yr_mon_cht[0] = yr;
  yr_mon_cht[1] = month;
  yr_mon_cht[2] = cohort;
  
  MPI_Send(&yr_mon_cht, 3, MPI_INT, 0, PTEM_MSG_TAG, MPI_COMM_WORLD);

}