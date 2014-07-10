//
//  tbc-debug-util.cpp
//  dvm-dos-tem
//
//  Created by Tobey Carman on 9/13/13.
//  2013 Spatial Ecology Lab.
//

#include <iostream>
#include <unistd.h> // for hostname stuff...
#ifdef WITHMPI
#include <mpi.h>
#endif

#include "tbc-debug-util.h"

#ifdef WITHMPI
// For now, not using any of these funcitons w/o MPI, so have
// included all of them in the #ifdef to make compiling easier.

void tbc_mpi_pp_error(int err) {
  switch (err) {
    case MPI_SUCCESS: {
      std::cout << "MPI_SUCCESS\n";
      break;
    }
    case MPI_ERR_REQUEST: {
      std::cout << "MPI_ERR_REQUEST\n";
      break;
    }
    case MPI_ERR_ARG: {
      std::cout << "MPI_ERR_ARG\n";
      break;
    }
    default: {
      std::cout << "Hmmm.? Unknown MPI Return Code?\n";
      break;
    }
  }
}

void PAUSE_to_attach_gdb(int myrank, int stop_in_rank) {
  /* Debugging help from here:
   http://www.open-mpi.org/faq/?category=debugging
   basically, compile the program and start it like normal. Will get a 
   messages to console from each process...
   
   in another console, cd to dvm-dos-tem and type e.g.:
   $ gdb --pid 94206 DVMDOSTEM
   
   Then in that window, do
   (gdb) bt
   
   and you shoudl see stack
   then move up stack with
   (gdb) frame <whatever number>
   
   then set the i to a non-zero value
   (gdb) set var i = 7
   
   then set a breakpoint after this pause
  */
   
  if (myrank == stop_in_rank) {
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


/* another version that will stop on all ranks */
void PAUSE_to_attach_gdb() {
  int i = 0;
  char hostname[256];
  gethostname(hostname, sizeof(hostname));
  printf("PID %d on %s ready for attach\n", getpid(), hostname);
  fflush(stdout);
  while (0 == i) {
    sleep(5);
  }
}

#endif
