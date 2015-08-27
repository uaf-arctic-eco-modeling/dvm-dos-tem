/*  Runner.h
 *
 *  Runner is a general class used to:
 *
 *  1) Initialize all the necessary classes
 *  2) get I/O
 *  3) run one or more cohort(s)
 *
 */

#ifndef RUNNER_H_
#define RUNNER_H_
#include <string>
#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <deque>

#ifdef WITHMPI
#include <mpi.h>
#endif


#include "../runmodule/Cohort.h"
#include "../runmodule/ModelData.h"
#include "../CalController.h"
#include "../ArgHandler.h"

using namespace std;

class Runner {
public:
  Runner(ModelData md, bool cal_mode, int y, int x);
  Runner();
  ~Runner();

  int y;
  int x;
  
  Cohort cohort;

  // Should end up as a null pointer if calibrationMode is off.
  boost::shared_ptr<CalController> calcontroller_ptr;
  int chtid;    /* currently-running 'cohort' id */
  int error;    /* error index */


  void run_years(int year_start, int year_end, const std::string& stage);
  void modeldata_module_settings_from_args(const ArgHandler &args);
  void output_caljson_yearly(int year);
  void output_caljson_monthly(int year, int month);


private:
  bool calibrationMode;

  std::string loop_order;

  //data classes
  ModelData md;     /* model controls, options, switches and so on */

  // Unused?? as of 8/19/2015
  //EnvData  grded;   // grid-aggregated 'ed' (not yet done)
  //BgcData  grdbd;   // grid-aggregared 'bd' (not yet done)

  EnvData  chted;   // withing-grid cohort-level aggregated 'ed'
                    //   (i.e. 'edall in 'cht')
  BgcData  chtbd;
  FirData  chtfd;

  deque<RestartData> mlyres;

};
#endif /*RUNNER_H_*/
