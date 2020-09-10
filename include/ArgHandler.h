#ifndef _ARGHANDLER_H
#define _ARGHANDLER_H
#include <iostream>
#include <string>

#include <boost/filesystem.hpp>
#include <boost/program_options.hpp>

//  Reminder for how to add more options:
//   1) decide what you want the option to look like and what it should do
//   2) add a variable for storing the option value to ArgHandler.h
//   3) add command line flag and description to ArgHandler.cpp
//   4) add an inline get function to ArgHandler.h for returning the options's value
//   5) add code to TEM.cpp for checking the option and taking appropriate behavior

class ArgHandler {
	boost::program_options::options_description desc;
	boost::program_options::variables_map varmap;

  int pr_yrs;
  int eq_yrs;
  int sp_yrs;
  int tr_yrs;
  int sc_yrs;

  bool cal_mode;
  int force_cmt;
  bool inter_stage_pause;
  bool archive_all_json;
  bool tar_caljson;
  int last_n_json_files;

  std::string max_output_volume;
  bool no_output_cleanup;
  bool restart_run;

  std::string pid_tag;

  bool floating_point_exp;

  std::string loop_order;

	std::string ctrl_file;

  std::string log_level;
  std::string log_scope;

  bool help;


public:
	ArgHandler();
	void parse(int argc, char** argv);
	void verify();
	void show_help();

  inline int get_pr_yrs() const {return pr_yrs;};
  inline int get_eq_yrs() const {return eq_yrs;};
  inline int get_sp_yrs() const {return sp_yrs;};
  inline int get_tr_yrs() const {return tr_yrs;};
  inline int get_sc_yrs() const {return sc_yrs;};
  inline const bool get_fpe(){return floating_point_exp;};
	
  inline const bool get_cal_mode(){return cal_mode;};
  inline const int  get_force_cmt() const {return force_cmt;};
  inline const bool get_inter_stage_pause() const {return inter_stage_pause;};
  inline const bool get_archive_all_json() const {return archive_all_json;};
  inline const bool get_tar_caljson() const {return tar_caljson;};
  inline const int get_last_n_json_files() const {return last_n_json_files;};

  inline const std::string get_pid_tag() const {return pid_tag;};
  inline const std::string get_loop_order(){return loop_order;};
	inline const std::string get_ctrl_file(){return ctrl_file;};

  inline const std::string get_max_output_volume(){return max_output_volume;};
  inline const bool get_no_output_cleanup(){return no_output_cleanup;};
  inline const bool get_restart_run(){return restart_run;};

  inline const std::string get_log_level(){return log_level;};
  inline const std::string get_log_scope(){return log_scope;};

	inline const bool get_help(){return help;};
};
#endif /* _ARGHANDLER_H */
