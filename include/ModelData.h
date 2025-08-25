#ifndef MODELDATA_H_
#define MODELDATA_H_
#include <string>
#include <iostream>
#include <fstream>
#include <sstream>
#include <cstdlib>
#include <json/value.h>

#include "ArgHandler.h"
#include "util_structs.h"
#include "layerconst.h"
#include "errorcode.h"

#ifdef WITHMPI
#include <mpi.h>
#include <netcdf_par.h>
#else
#include <netcdf.h>
#endif

using namespace std;

class ModelData {
public:

  ModelData(Json::Value controldata);

  ModelData();
  ~ModelData();

  void update(ArgHandler const * arghandler);
  std::string describe_module_settings();

  void create_netCDF_output_files(int ysize, int xsize, const std::string & stage, int stage_year_count, bool copy_grid_mapping);

  string loop_order; // time-major or space-major

  int force_cmt; // used to override the veg map (calibration mode only)

  int eq_yrs;
  int pr_yrs;
  int sp_yrs;
  int tr_yrs;
  int sc_yrs;

  //General config settings
  std::string run_name;
  std::string run_description;

  //Config Stage Settings
  bool inter_stage_pause; // Controls pauses between EQ, SP, TR, SC
  //PR modules
  bool pr_env, pr_bgc, pr_nfeed, pr_avln;
  bool pr_baseline, pr_dsb, pr_dsl, pr_dyn_lai;
  //EQ modules
  bool eq_env, eq_bgc, eq_nfeed, eq_avln;
  bool eq_baseline, eq_dsb, eq_dsl, eq_dyn_lai;
  //SP modules
  bool sp_env, sp_bgc, sp_nfeed, sp_avln;
  bool sp_baseline, sp_dsb, sp_dsl, sp_dyn_lai;
  //TR modules
  bool tr_env, tr_bgc, tr_nfeed, tr_avln;
  bool tr_baseline, tr_dsb, tr_dsl, tr_dyn_lai;
  //SC modules
  bool sc_env, sc_bgc, sc_nfeed, sc_avln;
  bool sc_baseline, sc_dsb, sc_dsl, sc_dyn_lai;

  //Config IO settings
  string parameter_dir;
  string hist_climate_file;
  string proj_climate_file;
  string veg_class_file;
  string topo_file;
  string fri_fire_file;
  string hist_exp_fire_file;
  string proj_exp_fire_file;
  string soil_texture_file;
  string drainage_file;
  string co2_file;
  string proj_co2_file;
  string runmask_file;
  string output_dir;
  string restart_from;      // Restart from a previous run
  string output_spec_file;
  bool output_monthly;
  bool nc_eq; // NetCDF output flags for each stage
  bool nc_sp;
  bool nc_tr;
  bool nc_sc;
  int output_interval; //How many years to store for output
  //The following two config values are temporarily stored in
  // ModelData, to be transferred to Climate.
  int baseline_start;//Start year for baseline EQ climate
  int baseline_end;//End year for baseline EQ climate

  // Maps holding data about variables to be output at specific timesteps
  // C++11 would allow the use of unordered_maps, which have a faster
  // by-key access time.
  std::map<std::string, OutputSpec> daily_netcdf_outputs;
  std::map<std::string, OutputSpec> monthly_netcdf_outputs;
  std::map<std::string, OutputSpec> yearly_netcdf_outputs;

  std::string pid_tag;
  std::string caldata_tree_loc;
  int last_n_json_files;
  bool archive_all_json;
  bool tar_caljson;

  int changeclimate; // 0: default (up to run stage); 1: dynamical; -1: static
  int changeco2; // 0: default (up to run stage); 1: dynamical; -1: static
  bool dynamic_LAI; // True: calculate LAI as a function of vegc, False: use static_lai from CohortLookup 
  bool useseverity; // using fire severity inputs

  int cell_timelimit; //Time limit in seconds for cell computation time
  time_t cell_stime; //Start time per cell. Move to Runner?

  bool outSiteDay;

  bool get_envmodule();
  void set_envmodule(const std::string &s);
  void set_envmodule(const bool v);

  bool get_bgcmodule();
  void set_bgcmodule(const std::string &s);
  void set_bgcmodule(const bool v);

  bool get_dynamic_lai_module();
  void set_dynamic_lai_module(const std::string &s);
  void set_dynamic_lai_module(const bool v);

  bool get_dslmodule();
  void set_dslmodule(const std::string &s);
  void set_dslmodule(const bool v);

  bool get_dsbmodule();
  void set_dsbmodule(const std::string &s);
  void set_dsbmodule(const bool v);

  bool get_nfeed();
  void set_nfeed(const std::string &s);
  void set_nfeed(const bool v);

  bool get_avlnflg();
  void set_avlnflg(const std::string &s);
  void set_avlnflg(const bool v);

  bool get_baseline();
  void set_baseline(const std::string &s);
  void set_baseline(const bool v);


private:

  // the following 3 switches will control N modules in BGC
  bool avlnflg; // inorganic N in/out module - partial open N cycle

  bool nfeed; // when true, allows N uptake to be limited by soil conditions
  // which then controls plant growth. Basically its a switch
  // for soil-plant N process module.

  bool baseline;   // When true allowing ninput and nlost to be used for
  // adjusting c/n of soil - partial open N cycle


  bool envmodule;             // (Bio?)physical module on/off
  bool bgcmodule;             // BGC module on/off
  bool dynamic_lai_module;    // dynamic lai module on/off

  bool dslmodule;  // dynamic soil layer module on/off
  bool dsbmodule;  // disturbance module on/off

  // Note: the dsl module ON lets the thickness, number and type of layers
  //       change. With dsl module OFF, the C and N content will change, but
  //       the thickness and number of layers should not change.

};

#endif /*MODELDATA_H_*/
