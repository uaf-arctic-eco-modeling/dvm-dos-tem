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

  int pre_run_yrs;
  int max_eq;
  int sp_yrs;
  int tr_yrs;
  int sc_yrs;

  bool cal_mode;
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

  inline int get_pre_run_yrs() const {return pre_run_yrs;};
  inline int get_max_eq() const {return max_eq;};
  inline int get_sp_yrs() const {return sp_yrs;};
  inline int get_tr_yrs() const {return tr_yrs;};
  inline int get_sc_yrs() const {return sc_yrs;};
  inline const bool get_fpe(){return floating_point_exp;};
	
  inline const bool get_cal_mode(){return cal_mode;};
  inline const std::string get_loop_order(){return loop_order;};
	inline const std::string get_ctrl_file(){return ctrl_file;};
  

  inline const std::string get_log_level(){return log_level;};
  inline const std::string get_log_scope(){return log_scope;};

	inline const bool get_help(){return help;};
};
#endif /* _ARGHANDLER_H */
