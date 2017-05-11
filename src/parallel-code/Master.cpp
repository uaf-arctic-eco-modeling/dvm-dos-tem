//
//  Master.cpp
//  dvm-dos-tem
//
//  Created by Tobey Carman on 9/25/13.
//  2013 Spatial Ecology Lab.
//
#include <mpi.h>
#include <vector>
#include <iostream>
#include <string>
#include <deque>
#include <netcdfcpp.h>
#include <algorithm>

#include "Master.h"
#include "../data/RestartData.h"
#include "../inc/tbc_mpi_constants.h"
#include "../util/tbc-debug-util.h"
//#include "../output/RestartOutputer.h"

#include "../TEMLogger.h"

extern src::severity_logger< severity_level > glg;


/** Comparision functions for ordering RestartDatas. Called by std::sort(..).
 Probably should make this a member of RestartData.
 */
bool compare_cohortids_asc(const RestartData lhs, const RestartData rhs){
  return lhs.chtid < rhs.chtid;
}
bool compare_cohortids_dec(const RestartData lhs, const RestartData rhs){
  return lhs.chtid > rhs.chtid;
}


Master::Master(int _rank, int _processors){
  rank = _rank;
  processors = _processors;
}
void Master::dispense_cohorts_to_slaves(const std::vector<int> &cohort_list){
   
  // A list of cohorts for each processor.
  std::vector<std::vector<int> > work_alloc_table(processors);
  
  // Assign each cohort to a processor
  for (std::vector<int>::const_iterator cit = cohort_list.begin(); cit != cohort_list.end(); ++cit) {
    int rank_to_run_on = ( *cit % (processors-1) );
    if (rank_to_run_on == 0){
      rank_to_run_on = rank_to_run_on + (processors-1);
    }
    work_alloc_table[rank_to_run_on].push_back(*cit);
  }

  // Not really sure if this is the best way to handle this; ends up making
  // a multi-line log statement, which may be annoying?
  std::stringstream ss;
  ss << "Work Allocation Table\n";
  ss << "----------------------\n";
  for (std::vector<std::vector<int> >::iterator rit = work_alloc_table.begin(); rit != work_alloc_table.end(); ++rit) {
    int ridx = rit - work_alloc_table.begin(); // convert iterator to index
    ss << "Rank " << ridx << " will run " << work_alloc_table[ridx].size() << " cohorts (";
    for (std::vector<int>::iterator cit = work_alloc_table[ridx].begin(); cit != work_alloc_table[ridx].end(); ++cit) {
      int cidx = cit - work_alloc_table[ridx].begin(); // convert iterator to index
      ss << work_alloc_table[ridx][cidx] << ", ";
    }
    ss << ")\n";
  }

  BOOST_LOG_SEV(glg, note) << "Showing the work allocation...\n" << ss.str();

  // Send cohort list to each processor.
  for (std::vector<std::vector<int> >::iterator rit = work_alloc_table.begin(); rit != work_alloc_table.end(); ++rit) {
    int ridx = rit - work_alloc_table.begin(); // convert iterator to index
    
    std::vector<int> chtlist = *rit;
    
    if (chtlist.size() > 0) {
      BOOST_LOG_SEV(glg, note) << "Sending cohort list to processor " << ridx << "...";
      MPI_Send(&chtlist[0], chtlist.size(), MPI_INT, ridx, PTEM_MSG_TAG, MPI_COMM_WORLD);
    }
  }

}

void Master::get_restartdata_and_progress_from_slaves(int total_num_cohorts){
  
  std::deque<RestartData> rd_deque;
  
  // request handles and status objects...
  MPI_Request incoming_requests[2];          // two kinds of request...
  MPI_Status incoming_req_statuses[2];       // and a status for each
  
  // a place to store the actual data...
  int incoming_genmsg_buffer[3];                // general messages send three integers (year, month, cht)
  RestartData incoming_restartdata_buffer[1];   // "done" messages send one value
  
  RestartData rd = RestartData(); // default construct a RestartData object to
                                  // we can get the "shape" of it for MPI
                                  // all values set to MISSING_I or MISSING_D
  // call rd member to register the mpi type
  MPI_Datatype MPI_t_RestartData;
  MPI_t_RestartData = rd.register_mpi_datatype();
  
  /* non blocking listen for general messages */
  MPI_Irecv(&incoming_genmsg_buffer,   // where to put the stuff
            3,                         // how much of it; (yr, month, cht)
            MPI_INT,                   // data type
            MPI_ANY_SOURCE,            // from who
            PTEM_MSG_TAG,              // tag
            MPI_COMM_WORLD,            // communicator
            &incoming_requests[0]);    // put it in the first slot of the requests array
  
  
  /* non blocking listen for finished data messages */
  MPI_Irecv(&incoming_restartdata_buffer,
            1,
            MPI_t_RestartData,
            MPI_ANY_SOURCE,
            PTEM_RESTARTDATA_TAG,
            MPI_COMM_WORLD,
            &incoming_requests[1]);  // second slot of the requests array
  

  /* Loop until we have got the data from each cohort.
   Every time we recieve a done message (restart data) from a slave, increment
   the completed cohort count.
   */
  int cht_count = 0;
  while (cht_count < total_num_cohorts) {
    
    /* Now test all requests */
    int len_incoming_requests = sizeof(incoming_requests)/sizeof(incoming_requests[0]);
    //int len_incoming_requests = 2;
    //printf("len_incoming_requests: %d\n", len_incoming_requests);
    /* Upon completion of process any finished requests */
    //std::cout << "Length of incoming requests list: " << len_incoming_requests << "\n";
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
    
    
    //printf("NUMBER OF COMPLETED REQUESTS: %d\n", number_completed);
    
    //for (int i = 0; i < number_completed; ++i) {
    //  printf("completed_req_idx[%d]: %d\n", i, completed_req_idx[i]); //"    (MPI_UNDEFINED: " << MPI_UNDEFINED << ")\n";
    //  printf("completed_req_stat_obj[%d].MPI_TAG: %d\n", i, incoming_req_statuses[i].MPI_TAG);
    //}
    //std::cout << "PTEM_RESTARTDATA_TAG: " << PTEM_RESTARTDATA_TAG << "\n";
    //std::cout << "PTEM_MSG_TAG: " << PTEM_MSG_TAG << "\n";
    //printf("cht_count/totcohort: %d/%d\n", cht_count,NUM_COHORTS);
    
    if (number_completed > 0) {
      for (int i = 0; i < number_completed; ++i) {
        switch (incoming_req_statuses[i].MPI_TAG) {
            
          case PTEM_RESTARTDATA_TAG: {
            BOOST_LOG_SEV(glg, note) << "DONE. Rank "
                                     << incoming_req_statuses[i].MPI_SOURCE
                                     << " has sent some RestartData! Need to extract it? write to a file???";
            //PAUSE_to_attach_gdb();
            
            // make a real RestartData object from the incoming data buffer
            RestartData recv_rd = incoming_restartdata_buffer[0];

            rd_deque.push_back(recv_rd);

            // setup a file to write it to...
//            std::string outputdir = std::string("DATA/test_06_cohorts/output/");
//            std::string stage = std::string("-eq.nc");

            // write the data out to the file...
//            RestartOutputer ro;
//            ro.init(outdir, stage);
//            ro.outputVariables(rd.chtid);
            
            
            cht_count += 1;
            /* post another non blocking listen for finished data messages */
            MPI_Irecv(&incoming_restartdata_buffer,
                      1,
                      MPI_t_RestartData,
                      MPI_ANY_SOURCE,
                      PTEM_RESTARTDATA_TAG,
                      MPI_COMM_WORLD,
                      &incoming_requests[1]);
            break;
          }
          case PTEM_MSG_TAG: {
            BOOST_LOG_SEV(glg, info) << "MESSAGE from rank "
                                     << incoming_req_statuses[i].MPI_SOURCE
                                     << ". Message: "
                                     << incoming_genmsg_buffer[0] << ", "
                                     << incoming_genmsg_buffer[1] << ", "
                                     << incoming_genmsg_buffer[2];

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
            BOOST_LOG_SEV(glg, warn) << "Unknown MPI message tag??";
            BOOST_LOG_SEV(glg, warn) << "Possible Error (MPI_Status.MPI_ERROR): " << incoming_req_statuses[i].MPI_ERROR;
            break;
          }
        }
      }
    } else {
      printf("NOTHING HAS COMPLETED...LOOPING AGAIN...\n");
    }
  } // end while listending for cohorts - we got 'em all
  PAUSE_to_attach_gdb();
  
  std::sort(rd_deque.begin(), rd_deque.end(), compare_cohortids_asc);
  
  NcFile rf = setup_restartnc_file(rd_deque.size());
  int rec = 0;
  for (std::deque<RestartData>::iterator it = rd_deque.begin(); it != rd_deque.end(); ++it) {
    RestartData cur_rd = *it;
    write_cohort_record_to_restartnc_file(rf, cur_rd, rec);
    rec++;
  }
  BOOST_LOG_SEV(glg, debug) << "Just wrote " << rec << " records in the restart netcdf file...";
  rf.close();

  MPI_Type_free(&MPI_t_RestartData); // not sure if this is the best place to
                                     // call this...seems easy to forget to
                                     // to do this...
}





/* not sure about passing by const ref to the NcFile...the compiler doesn't 
 complain, so this function apparently doesn't change the NcFile object (number 
 of vars, dims, etc) but it does put more values into the file (using its own 
 member function..). In any event, it seems to be working, but could be really 
 confusing to make assumptions based on the call signature...*/
void Master::write_cohort_record_to_restartnc_file(const NcFile & rfile, const RestartData rd, int record){
  NcError err(NcError::verbose_nonfatal);

  NcDim * chtD = rfile.get_dim("CHTID");
  NcDim * pftD = rfile.get_dim("PFT");

	NcDim * pftpartD = rfile.get_dim("PFTPART");
  
	NcDim * rootlayerD = rfile.get_dim("ROOTLAYER");
	NcDim * snowlayerD = rfile.get_dim("SNOWLAYER");
	NcDim * soillayerD = rfile.get_dim("SOILLAYER");
	NcDim * rocklayerD = rfile.get_dim("ROCKLAYER");
	NcDim * frontD     = rfile.get_dim("FRONTNUM");
	NcDim * prvyearD   = rfile.get_dim("PRVYEAR");
	NcDim * prvmonthD  = rfile.get_dim("PRVMONTH");

  NcVar * chtidV          = rfile.get_var("CHTID");
  NcVar * errcodeV        = rfile.get_var("ERRCODE");
  NcVar * dsrV            = rfile.get_var("DSR");           //days since rainfall
  NcVar * firea2sorgnV    = rfile.get_var("FIREA2SORGN");   //fire-emitted N deposition
  NcVar * ysfV            = rfile.get_var("YSF");           // years since fire
  NcVar * ifwoodyV        = rfile.get_var("IFWOODY");
  NcVar * ifdeciwoodyV    = rfile.get_var("IFDECIWOODY");
  NcVar * ifperenialV     = rfile.get_var("IFPERENIAL");
	NcVar * nonvascularV    = rfile.get_var("NONVASCULAR");
	NcVar * vegageV         = rfile.get_var("VEGAGE");
	NcVar * vegcovV         = rfile.get_var("VEGCOV");
	NcVar * laiV            = rfile.get_var("LAI");
	NcVar * rootfracV       = rfile.get_var("ROOTFRAC");
  NcVar * vegwaterV       = rfile.get_var("VEGWATER");
  NcVar * vegsnowV        = rfile.get_var("VEGSNOW");
  NcVar * vegcV           = rfile.get_var("VEGC");
  NcVar * strnV           = rfile.get_var("STRN");
  NcVar * labnV           = rfile.get_var("LABN");
  NcVar * deadcV          = rfile.get_var("DEADC");
  NcVar * deadnV          = rfile.get_var("DEADN");
 	NcVar * toptV           = rfile.get_var("TOPT");
	NcVar * eetmxV          = rfile.get_var("EETMX");
 	NcVar * growingttimeV   = rfile.get_var("GROWINGTTIME");
	NcVar * unnormleafmxV   = rfile.get_var("UNNORMLEAFMX");
	NcVar * foliagemxV      = rfile.get_var("FOLIAGEMX");
	NcVar * toptAV          = rfile.get_var("TOPTA");
	NcVar * eetmxAV         = rfile.get_var("EETMXA");
 	NcVar * growingttimeAV  = rfile.get_var("GROWINGTTIMEA");
	NcVar * unnormleafmxAV  = rfile.get_var("UNNORMLEAFMXA");
  NcVar * numsnwlV        = rfile.get_var("NUMSNWL");
  NcVar * snwextramassV   = rfile.get_var("SNWEXTRAMASS");
  NcVar * TSsnowV         = rfile.get_var("TSsnow");
  NcVar * DZsnowV         = rfile.get_var("DZsnow");
  NcVar * LIQsnowV        = rfile.get_var("LIQsnow");
  NcVar * ICEsnowV        = rfile.get_var("ICEsnow");
 	NcVar * AGEsnowV        = rfile.get_var("AGEsnow");
  NcVar * RHOsnowV        = rfile.get_var("RHOsnow");
  NcVar * numslV          = rfile.get_var("NUMSL");
  NcVar * monthsfrozenV   = rfile.get_var("MONTHSFROZEN");
  NcVar * rtfrozendaysV   = rfile.get_var("RTFROZENDAYS");
  NcVar * rtunfrozendaysV = rfile.get_var("RTUNFROZENDAYS");
  NcVar * watertabV       = rfile.get_var("WATERTAB");
  NcVar * DZsoilV         = rfile.get_var("DZsoil");
  NcVar * AGEsoilV        = rfile.get_var("AGEsoil");
  NcVar * TYPEsoilV       = rfile.get_var("TYPEsoil");
	NcVar * TSsoilV         = rfile.get_var("TSsoil");
  NcVar * LIQsoilV        = rfile.get_var("LIQsoil");
  NcVar * ICEsoilV        = rfile.get_var("ICEsoil");
  NcVar * FROZENsoilV     = rfile.get_var("FROZENsoil");
  NcVar * FROZENFRACsoilV = rfile.get_var("FROZENFRACsoil");
  NcVar * TEXTUREsoilV    = rfile.get_var("TEXTUREsoil");
  NcVar * TSrockV         = rfile.get_var("TSrock");
  NcVar * DZrockV         = rfile.get_var("DZrock");
	NcVar * frontZV         = rfile.get_var("frontZ");  //front depth
  NcVar * frontFTV        = rfile.get_var("frontFT");    //freezing/thawing front
  NcVar * wdebriscV       = rfile.get_var("WDEBRISC");
  NcVar * wdebrisnV       = rfile.get_var("WDEBRISN");
  NcVar * rawcV           = rfile.get_var("RAWC");
  NcVar * somaV           = rfile.get_var("SOMA");
  NcVar * somprV          = rfile.get_var("SOMPR");
  NcVar * somcrV          = rfile.get_var("SOMCR");
  NcVar * solnV           = rfile.get_var("SOLN");
  NcVar * avlnV           = rfile.get_var("AVLN");
  NcVar * prvltrfcnAV     = rfile.get_var("PRVLTRFCNA");

  //----------------------------
  chtidV->put_rec(&rd.chtid, record);
  //errcodeV->put_rec(, record);
  dsrV->put_rec(&rd.dsr, record);
  firea2sorgnV->put_rec(&rd.firea2sorgn, record);
  ysfV->put_rec(&rd.yrsdist, record);
  ifwoodyV->put_rec(rd.ifwoody, record);
  ifdeciwoodyV->put_rec(rd.ifdeciwoody, record);
  ifperenialV->put_rec(rd.ifperenial, record);
	nonvascularV->put_rec(rd.nonvascular, record);
	vegageV->put_rec(rd.vegage, record);
	vegcovV->put_rec(rd.vegcov, record);
	laiV->put_rec(rd.lai, record);
	
  rootfracV->put_rec(&rd.rootfrac[0][0], record);
  vegwaterV->put_rec(rd.vegwater  , record);
  vegsnowV->put_rec(rd.vegsnow  , record);
  vegcV->put_rec(&rd.vegc[0][0]  , record);
  strnV->put_rec(&rd.strn[0][0]  , record);
  labnV->put_rec(rd.labn  , record);
  deadcV->put_rec(rd.deadc  , record);
  deadnV->put_rec(rd.deadn  , record);
 	toptV->put_rec(rd.topt , record);
	eetmxV->put_rec(rd.eetmx  , record);
 	growingttimeV->put_rec(rd.growingttime , record);
	unnormleafmxV->put_rec(rd.unnormleafmx , record);
	foliagemxV->put_rec(rd.foliagemx, record);
	toptAV->put_rec(&rd.toptA[0][0] , record);
	eetmxAV->put_rec(&rd.eetmxA[0][0] , record);
 	growingttimeAV->put_rec(&rd.growingttimeA[0][0] , record);
	unnormleafmxAV->put_rec(&rd.unnormleafmxA[0][0] , record);
  numsnwlV->put_rec(&rd.numsnwl , record);
  snwextramassV->put_rec(&rd.snwextramass , record);
  TSsnowV->put_rec(rd.TSsnow , record);
  DZsnowV->put_rec(rd.DZsnow, record);
  LIQsnowV->put_rec(rd.LIQsnow, record);
  ICEsnowV->put_rec(rd.ICEsnow, record);
 	AGEsnowV->put_rec(rd.AGEsnow , record);
  RHOsnowV->put_rec(rd.RHOsnow , record);
  
  numslV->put_rec(&rd.numsl , record);
  monthsfrozenV->put_rec(&rd.monthsfrozen , record);
  rtfrozendaysV->put_rec(&rd.rtfrozendays , record);
  rtunfrozendaysV->put_rec(&rd.rtunfrozendays , record);
  watertabV->put_rec(&rd.watertab , record);
  DZsoilV->put_rec(rd.DZsoil , record);
  AGEsoilV->put_rec(rd.AGEsoil, record);
  TYPEsoilV->put_rec(rd.TYPEsoil , record);
	TSsoilV->put_rec(rd.TSsoil, record);
  LIQsoilV->put_rec(rd.LIQsoil , record);
  ICEsoilV->put_rec(rd.ICEsoil , record);
  FROZENsoilV->put_rec(rd.FROZENsoil , record);
  FROZENFRACsoilV->put_rec(rd.FROZENFRACsoil , record);
  TEXTUREsoilV->put_rec(rd.TEXTUREsoil , record);
  TSrockV->put_rec(rd.TSrock , record);
  DZrockV->put_rec(rd.DZrock , record);
	frontZV->put_rec(rd.frontZ , record);
  frontFTV->put_rec(rd.frontFT , record);
  wdebriscV->put_rec(&rd.wdebrisc , record);
  wdebrisnV->put_rec(&rd.wdebrisn , record);
  rawcV->put_rec(rd.rawc , record);
  somaV->put_rec(rd.soma , record);
  somprV->put_rec(rd.sompr , record);
  somcrV->put_rec(rd.somcr , record);
  solnV->put_rec(rd.orgn , record);
  avlnV->put_rec(rd.avln , record);
  prvltrfcnAV->put_rec(&rd.prvltrfcnA[0][0] , record);
  
  
//  
//  //----------------------------
//  chtidV->put_rec(&rd.chtid, record);
//  
//  dsrV->put_rec(&rd.dsr, record);
//  firea2sorgnV->put_rec(&rd.firea2sorgn, record);
//  
//  ysfV->put_rec(&rd.yrsdist, record); // confusing variable names...
//  ifwoodyV->put_rec(rd.ifwoody, record);
//  ifdeciwoodyV->put_rec(rd.ifdeciwoody, record);

}

NcFile Master::setup_restartnc_file(int num_records){
  NcError err(NcError::verbose_nonfatal);

  // create netcdf file
  std::string restartfname("DATA/test_06_cohorts/output/parallel-restart-eq.nc");
  NcFile restartFile = NcFile(restartfname.c_str(), NcFile::Replace);
  
  // dimension definition
	NcDim * chtD = restartFile.add_dim("CHTID");
  
	NcDim * pftD     = restartFile.add_dim("PFT", NUM_PFT);
	NcDim * pftpartD = restartFile.add_dim("PFTPART", NUM_PFT_PART);
  
	NcDim * rootlayerD = restartFile.add_dim("ROOTLAYER", MAX_ROT_LAY);
	NcDim * snowlayerD = restartFile.add_dim("SNOWLAYER", MAX_SNW_LAY);
	NcDim * soillayerD = restartFile.add_dim("SOILLAYER", MAX_SOI_LAY);
	NcDim * rocklayerD = restartFile.add_dim("ROCKLAYER", MAX_ROC_LAY);
	NcDim * frontD     = restartFile.add_dim("FRONTNUM", MAX_NUM_FNT);
	NcDim * prvyearD   = restartFile.add_dim("PRVYEAR", 10);
	NcDim * prvmonthD  = restartFile.add_dim("PRVMONTH", 12);
	
	// variable definition
  restartFile.add_var("CHTID", ncInt, chtD);
  restartFile.add_var("ERRCODE", ncInt, chtD);
  
  // - atm
  restartFile.add_var("DSR", ncInt, chtD);           //days since rainfall
  restartFile.add_var("FIREA2SORGN", ncInt, chtD);   //fire-emitted N deposition
  
	// - veg
  restartFile.add_var("YSF", ncInt, chtD);  // years since fire
  
	restartFile.add_var("IFWOODY", ncInt, chtD, pftD);
	restartFile.add_var("IFDECIWOODY", ncInt, chtD, pftD);
	restartFile.add_var("IFPERENIAL", ncInt, chtD, pftD);
	restartFile.add_var("NONVASCULAR", ncInt, chtD, pftD);
  
	restartFile.add_var("VEGAGE", ncInt, chtD, pftD);
	restartFile.add_var("VEGCOV", ncDouble, chtD, pftD);
	restartFile.add_var("LAI", ncDouble, chtD, pftD);
	restartFile.add_var("ROOTFRAC", ncDouble, chtD, rootlayerD, pftD);
  restartFile.add_var("VEGWATER", ncDouble, chtD, pftD);
  restartFile.add_var("VEGSNOW", ncDouble, chtD, pftD);
  
  restartFile.add_var("VEGC", ncDouble, chtD, pftpartD, pftD);
  restartFile.add_var("STRN", ncDouble, chtD, pftpartD, pftD);
  restartFile.add_var("LABN", ncDouble, chtD, pftD);
  restartFile.add_var("DEADC", ncDouble, chtD, pftD);
  restartFile.add_var("DEADN", ncDouble, chtD, pftD);
  
 	restartFile.add_var("TOPT", ncDouble, chtD, pftD);
	restartFile.add_var("EETMX", ncDouble, chtD, pftD);
 	restartFile.add_var("GROWINGTTIME", ncDouble, chtD, pftD);
	restartFile.add_var("UNNORMLEAFMX", ncDouble, chtD, pftD);
	restartFile.add_var("FOLIAGEMX", ncDouble, chtD, pftD);
  
	restartFile.add_var("TOPTA", ncDouble, chtD, prvyearD, pftD);
	restartFile.add_var("EETMXA", ncDouble, chtD, prvyearD, pftD);
 	restartFile.add_var("GROWINGTTIMEA", ncDouble, chtD, prvyearD, pftD);
	restartFile.add_var("UNNORMLEAFMXA", ncDouble, chtD, prvyearD, pftD);
  
  //snow
  restartFile.add_var("NUMSNWL", ncInt, chtD);
  restartFile.add_var("SNWEXTRAMASS", ncDouble, chtD);
  restartFile.add_var("TSsnow", ncDouble, chtD, snowlayerD);
  restartFile.add_var("DZsnow", ncDouble, chtD, snowlayerD);
  restartFile.add_var("LIQsnow", ncDouble, chtD, snowlayerD);
  restartFile.add_var("ICEsnow", ncDouble, chtD, snowlayerD);
 	restartFile.add_var("AGEsnow", ncDouble, chtD, snowlayerD);
  restartFile.add_var("RHOsnow", ncDouble, chtD, snowlayerD);
  
  //ground-soil
  restartFile.add_var("NUMSL", ncInt, chtD);
  restartFile.add_var("MONTHSFROZEN", ncDouble, chtD);
  restartFile.add_var("RTFROZENDAYS", ncInt, chtD);
  restartFile.add_var("RTUNFROZENDAYS", ncInt, chtD);
  
  restartFile.add_var("WATERTAB", ncDouble, chtD);
  
  restartFile.add_var("DZsoil", ncDouble, chtD, soillayerD);
  restartFile.add_var("AGEsoil", ncInt, chtD, soillayerD);
  restartFile.add_var("TYPEsoil", ncInt, chtD, soillayerD);
	restartFile.add_var("TSsoil", ncDouble, chtD, soillayerD);
  restartFile.add_var("LIQsoil", ncDouble, chtD, soillayerD);
  restartFile.add_var("ICEsoil", ncDouble, chtD, soillayerD);
  restartFile.add_var("FROZENsoil", ncInt, chtD, soillayerD);
  restartFile.add_var("FROZENFRACsoil", ncDouble, chtD, soillayerD);
  restartFile.add_var("TEXTUREsoil", ncInt, chtD, soillayerD);
  
  restartFile.add_var("TSrock", ncDouble, chtD, rocklayerD);
  restartFile.add_var("DZrock", ncDouble, chtD, rocklayerD);
  
	restartFile.add_var("frontZ", ncDouble, chtD, frontD);  //front depth
  restartFile.add_var("frontFT", ncInt, chtD, frontD);    //freezing/thawing front
  
  restartFile.add_var("WDEBRISC", ncDouble, chtD);
  restartFile.add_var("WDEBRISN", ncDouble, chtD);
  
  restartFile.add_var("RAWC", ncDouble, chtD, soillayerD);
  restartFile.add_var("SOMA", ncDouble, chtD, soillayerD);
  restartFile.add_var("SOMPR", ncDouble, chtD, soillayerD);
  restartFile.add_var("SOMCR", ncDouble, chtD, soillayerD);
  restartFile.add_var("SOLN", ncDouble, chtD, soillayerD);
  restartFile.add_var("AVLN", ncDouble, chtD, soillayerD);
  
  restartFile.add_var("PRVLTRFCNA", ncDouble, chtD, prvmonthD, soillayerD);

  return restartFile;
}











