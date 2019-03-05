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
#include <map>

#ifdef WITHMPI
#include <mpi.h>
#endif


#include "Cohort.h"
#include "ModelData.h"
#include "CalController.h"
#include "ArgHandler.h"
#include "util_structs.h"

using namespace std;


class Runner {
public:
  Runner(ModelData md, bool cal_mode, int y, int x);
  Runner();
  ~Runner();

  int y;
  int x;
  
  Cohort cohort;

  std::list<std::string> check_sum_over_compartments();
  std::list<std::string> check_sum_over_PFTs();
  std::string report_not_equal(const std::string& a_desc, const std::string& b_desc, int PFT, double A, double B);
  std::string report_not_equal(double A, double B, const std::string& msg);

  // Should end up as a null pointer if calibrationMode is off.
  boost::shared_ptr<CalController> calcontroller_ptr;
  int chtid;    /* currently-running 'cohort' id */
  int error;    /* error index */


  void run_years(int year_start, int year_end, const std::string& stage);
  void modeldata_module_settings_from_args(const ArgHandler &args);
  void output_caljson_yearly(int year, std::string, boost::filesystem::path p);
  void output_caljson_monthly(int year, int month, std::string, boost::filesystem::path p);
  void output_debug_daily_drivers(int iy, boost::filesystem::path p);

  //void output_netCDF(int year, boost::filesystem::path p);
  void output_netCDF_monthly(int year, int month, std::string stage);
  void output_netCDF_yearly(int year, std::string stage);
  void output_netCDF(std::map<std::string, OutputSpec> &outputs, int year, int month, std::string stage);

  void output_nc_soil(int ncid, int cv, int *data, int max_var_count, int timestep);


  template<typename PTYPE>
  void output_nc_3dim(OutputSpec* out_spec, std::string stage_suffix, PTYPE data, int max_var_count, int start_timestep, int timesteps);

  template<typename PTYPE>
  void output_nc_4dim(OutputSpec* out_spec, std::string stage_suffix, PTYPE data, int max_var_count, int start_timestep, int timesteps);

  template<typename PTYPE>
  void output_nc_5dim(OutputSpec* out_spec, std::string stage_suffix, PTYPE data, int max_var_count_1, int max_var_count_2, int start_timestep, int timesteps);


  void output_nc_soil_layer(int ncid, int cv, int *data, int max_var_count, int start_timestep, int timesteps);
  void output_nc_soil_layer(int ncid, int cv, double *data, int max_var_count, int start_timestep, int timesteps);

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

  void monthly_output(const int year, const int month, const std::string& runstage);
  void yearly_output(const int year, const std::string& stage, const int startyr, const int endyr);

};
#endif /* RUNNER_H_ */
