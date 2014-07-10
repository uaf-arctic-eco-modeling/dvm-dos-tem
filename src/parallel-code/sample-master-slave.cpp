//
//  demo-master-slave.cpp
//
//  Created by Tobey Carman on 9/24/13.
//  2013 Spatial Ecology Lab.
//

#include "sample-master-slave.h"


// general C++ stuff
#include <iostream>
#include <vector>

// makes working with MPI C api easier
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// dvm-dos-tem stuff
#include "../data/RestartData.h"

// utilities...
#include "../util/tbc-debug-util.h"



// bad practice...but easier to read
using namespace std;

const int PTEM_RESTARTDATA_TAG = 25;
const int PTEM_MSG_TAG = 15;

const int NUM_COHORTS = 6;


int dummy_runSpatially(int yr, int m, int proc_rank_and_cht_num) {
  srand(getpid() + time(NULL));
  int processing_time = rand() % 2;
  printf("Crunching numbers (~%d seconds)... yr: %d, m: %d, proc/rank/cht: %d.\n",
         processing_time, yr, m, proc_rank_and_cht_num);
  sleep(processing_time);
  return 0;
}

void dispense_cohorts_to_slaves(int rank, int processors){
  
  // A list of cohorts for each processor.
  vector<vector<int> > work_alloc_table(processors);
  
  
  // Assign each cohort to a processor. O(n) for n cohorts?
  for (int cohort = 1; cohort <= 6; ++cohort) {
    int rank_to_run_on = cohort % (processors-1);
    if (rank_to_run_on == 0){
      rank_to_run_on = rank_to_run_on + (processors-1);
    }
    work_alloc_table[rank_to_run_on].push_back(cohort);
  }
  
  
  // pretty print the work allocation table
  cout << "Work Allocation Table\n";
  cout << "----------------------\n";
  for (vector<vector<int> >::iterator rit = work_alloc_table.begin(); rit != work_alloc_table.end(); ++rit) {
    int ridx = rit - work_alloc_table.begin(); // convert iterator to index
    cout << "Rank " << ridx << " will run " << work_alloc_table[ridx].size() << " cohorts (";
    for (vector<int>::iterator cit = work_alloc_table[ridx].begin(); cit != work_alloc_table[ridx].end(); ++cit) {
      int cidx = cit - work_alloc_table[ridx].begin(); // convert iterator to index
      cout << work_alloc_table[ridx][cidx] << ", ";
    }
    cout << ")"<< endl;
  }
  
  // Send cohort list to each processor.
  for (vector<vector<int> >::iterator rit = work_alloc_table.begin(); rit != work_alloc_table.end(); ++rit) {
    int ridx = rit - work_alloc_table.begin(); // convert iterator to index
    
    vector<int> chtlist = *rit;
    
    if (chtlist.size() > 0) {
      cout << "Sending cohort list to processor " << ridx << "...\n";
      MPI_Send(&chtlist[0], chtlist.size(), MPI_INT, ridx, PTEM_MSG_TAG, MPI_COMM_WORLD);
    }
  }
  
}


void master(int rank, int processors) {
  // FOR EVERY COHORT, ASK A SLAVE TO RUN THE COHORT!
  dispense_cohorts_to_slaves(rank, processors);
  
  // request handles and status objects...
  MPI_Request incoming_requests[2];          // two kinds of request...
  MPI_Status incoming_req_statuses[2];       // and a status for each
  
  // a place to store the actual data...
  int incoming_genmsg_buffer[3];     // general messages send three integers
  int incoming_donedata_buffer[1];   // "done" messages send one value
  
  
  /* non blocking listen for general messages */
  MPI_Irecv(&incoming_genmsg_buffer,   // where to put the shit
            3,                         // how much of it; (yr, month, cht)
            MPI_INT,                   // data type
            MPI_ANY_SOURCE,            // from who
            PTEM_MSG_TAG,              // tag
            MPI_COMM_WORLD,            // communicator
            &incoming_requests[0]);    // put it in the first slot of the requests array
  
  
  /* non blocking listen for finished data messages */
  MPI_Irecv(&incoming_donedata_buffer,
            1,
            MPI_INT,
            MPI_ANY_SOURCE,
            PTEM_RESTARTDATA_TAG,
            MPI_COMM_WORLD,
            &incoming_requests[1]);
  
  /* Loop until we have got the data from each cohort.
   Every time we recieve a done message (restart data) from a slave, increment
   the completed cohort count.
   */
  int cht_count = 0;
  while (cht_count < NUM_COHORTS) {
    
    /* Now test all requests */
    int len_incoming_requests = sizeof(incoming_requests)/sizeof(incoming_requests[0]);
    //int len_incoming_requests = 2;
    //printf("len_incoming_requests: %d\n", len_incoming_requests);
    /* Upon completion of process any finished requests */
    //cout << "Length of incoming requests list: " << len_incoming_requests << "\n";
    //MPI_Status completed_req_stat_obj[100];
    int a_wait_error;
    int completed_req_idx[2];
    int number_completed = 0;
    
    a_wait_error = MPI_Waitsome(len_incoming_requests,  // number in request list
                                incoming_requests,       // the list of requests to look at
                                &number_completed,
                                completed_req_idx,       // the index of the completed requests in the list.. MPI_UNDEFINED if none are completed..
                                incoming_req_statuses);  // a status object - empty if there are no competed requests...
    
    //printf("Code returned from MPI_Waitsome: ");
    //tbc_mpi_pp_error(a_wait_error);
    
    
    printf("NUMBER OF COMPLETED REQUESTS: %d\n", number_completed);
    printf("completed_req_idx[0..1]: %d, %d\n", completed_req_idx[0], completed_req_idx[1]);
    //for (int i = 0; i < number_completed; ++i) {
    //  printf("completed_req_idx[%d]: %d\n", i, completed_req_idx[i]); //"    (MPI_UNDEFINED: " << MPI_UNDEFINED << ")\n";
    //  printf("completed_req_stat_obj[%d].MPI_TAG: %d\n", i, incoming_req_statuses[i].MPI_TAG);
    //}
    //cout << "PTEM_RESTARTDATA_TAG: " << PTEM_RESTARTDATA_TAG << "\n";
    //cout << "PTEM_MSG_TAG: " << PTEM_MSG_TAG << "\n";
    //printf("cht_count/totcohort: %d/%d\n", cht_count,NUM_COHORTS);
    
    if (number_completed > 0) {
      for (int i = 0; i < number_completed; ++i) {
        switch (incoming_req_statuses[i].MPI_TAG) {
            
          case PTEM_RESTARTDATA_TAG: {
            cout << "DONE. Rank " << incoming_req_statuses[i].MPI_SOURCE << " has sent " << incoming_donedata_buffer[0] << "\n";
            cht_count += 1;
            /* non blocking listen for finished data messages */
            MPI_Irecv(&incoming_donedata_buffer,
                      1,
                      MPI_INT,
                      MPI_ANY_SOURCE,
                      PTEM_RESTARTDATA_TAG,
                      MPI_COMM_WORLD,
                      &incoming_requests[1]);
            break;
          }
          case PTEM_MSG_TAG: {
            cout << "MESSAGE from rank " << incoming_req_statuses[i].MPI_SOURCE << ". Message: " << incoming_genmsg_buffer[0] << ", "<< incoming_genmsg_buffer[1] << ", " << incoming_genmsg_buffer[2] << endl; // << msg;
            /* non blocking listen for general messages */
            MPI_Irecv(&incoming_genmsg_buffer,  // where to put the shit
                      3,                         // how much of it; (yr, month, cht)
                      MPI_INT,                   // data type
                      MPI_ANY_SOURCE,            // from who
                      PTEM_MSG_TAG,              // tag
                      MPI_COMM_WORLD,            // communicator
                      &incoming_requests[0]);             // put it in the first slot of the requests array
            
            
            break;
          }
          default: {
            cout << "Unknown message tag?\n";
            cout << "Possible Error (MPI_Status.MPI_ERROR): " << incoming_req_statuses[i].MPI_ERROR << "\n";
            break;
          }
        }
      }
      
      
      
    } else {
      printf("NOTHING HAS COMPLETED...LOOPING AGAIN...\n");
    }
  }
}

void slave(int rank, int processors) {
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
  
  printf("I am a slave and just recieved my list of cohorts to run: ");
  for (int i = 0 ; i < number_of_ints_to_recieve; ++i) {
    cout << cohorts[i] << ", ";
  }
  cout << endl;
  
  for (int cht = 0 ; cht < number_of_ints_to_recieve; ++cht) {
    // then run that cohort over each year and month...
    for (int icalyr=1800; icalyr<=1805; icalyr++){
      //cout << "In YEAR loop." << " yr: " << icalyr << "\n";
      
      int ifover = 0;
      
      for (int im=0; im<12; im++) {
        //cout << "In MONTH loop... " << " (yr, month, cohort): (" << icalyr << ", " << im << ", " << proc_rank_and_cht_num << ")\n";
        
        
        ifover = dummy_runSpatially(icalyr, im, cohorts[cht]); //<-- ERROR HERE!!! This is the
        // correct rank and proc number
        // but cohort needs to be passed seperately...
        
        
        //ifover = runSpatially(icalyr, im, proc_rank_and_cht_num);// may need to -1 from proc_rank_and_cht_num...
        // I think the cht index needs to be zero based internally, but
        // for this MPI stuff, I think it needs to be 1 based to account
        
        // send a message to the master saying what we are about to run...
        int yr_mon_cht[3];
        yr_mon_cht[0] = icalyr;
        yr_mon_cht[1] = im;
        yr_mon_cht[2] = cohorts[cht];
        
        MPI_Send(&yr_mon_cht, 3, MPI_INT, 0, PTEM_MSG_TAG, MPI_COMM_WORLD);
        
      } // end monthly...
      
      // no matter what initmode set in control file, must be 'restart' after the first time-step
      
      //md.initmode=4;   // this will set 'initmode' as 'restart', but from 'mlyres' rather than from restart file (initmode=3).
      
      // ticking timer once
      
      //timer.advanceOneMonth();
    } // end yearly...
    
    
    printf("Done with ALL years for cohort %d, sending message to master...\n", cohorts[cht]);
    // send a message to the master saying we are done...
    int my_restart_data = 12345;
    MPI_Send(&my_restart_data, 1, MPI_INT, 0, PTEM_RESTARTDATA_TAG, MPI_COMM_WORLD);
    printf("Message has been sent to master (cohort %d)!\n", cohorts[cht]);
    
  } // end cht loop
  
  return; // allow processor to quit.
}


void check_available_processors(int rank, int processors) {
  if (processors < 2) {
    MPI_Finalize();
    printf("This is a master/slave program and requires more than one ");
    printf("processor to run when compiled with the WITHMPI flag.\n");
    printf("EXITING...\n");
    exit(-1);
  }
}

void pause_to_attach_debugger(int rank, int processors){
  if (rank < 6) { // Note: not flexible...
    int i = 0;
    char hostname[256];
    gethostname(hostname, sizeof(hostname));
    printf("PID %d on %s ready for attach\n", getpid(), hostname);
    fflush(stdout);
    while (0 == i) {
      sleep(5);
    }
  }
}

int main(int argc, char** argv) {
  int rank;
  int processors;
  MPI_Init(&argc, &argv); // requires default args...empty?
  MPI_Comm_size(MPI_COMM_WORLD, &processors);
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  printf("You are processor %d of %d available on this system.\n",rank, processors);
  
  check_available_processors(rank, processors);
  
  // custom datatypes...for RestartData
  // http://stackoverflow.com/questions/9864510/struct-serialization-in-c-and-sending-over-mpi
  // http://stackoverflow.com/questions/18992701/mpi-c-derived-types-struct-of-vectors
  
  
  
  
  //pause_to_attach_debugger(rank, processors);
  
  if (rank == 0) {
    printf("This is the master process...\n");
    master(rank, processors);
  } else { // rank != 0
    // do slave work...
    slave(rank, processors);
  }
  MPI_Finalize();
  return 0;
}

