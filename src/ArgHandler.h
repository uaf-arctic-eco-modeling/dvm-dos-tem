#ifndef _ARGHANDLER_H
#define _ARGHANDLER_H
#include <iostream>
#include <string>

#include <boost/filesystem.hpp>
#include <boost/program_options.hpp>


class ArgHandler {
	boost::program_options::options_description desc;
	boost::program_options::variables_map varmap;

  bool cal_mode;
  std::string loop_order;
	std::string ctrl_file;

  std::string log_level;
  bool help;


public:
	ArgHandler();
	void parse(int argc, char** argv);
	void verify();
	void show_help();
	
  inline const bool get_cal_mode(){return cal_mode;};
  inline const std::string get_loop_order(){return loop_order;};
	inline const std::string get_ctrl_file(){return ctrl_file;};
  

  inline const std::string get_log_level(){return log_level;};
	inline const bool get_help(){return help;};
};
#endif /* _ARGHANDLER_H */