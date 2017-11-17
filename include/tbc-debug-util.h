//
//  tbc-debug-util.h
//  dvm-dos-tem
//
//  Created by Tobey Carman on 9/13/13.
//  2013 Spatial Ecology Lab.
//

#ifndef tbc_debug_util_h
#define tbc_debug_util_h

void tbc_mpi_pp_error(int err);

void PAUSE_to_attach_gdb(int myrank, int stop_in_rank);
void PAUSE_to_attach_gdb();

#endif /* tbc_debug_util_h */
