#ifndef _CALCONTROLLER_H_
#define _CALCONTROLLER_H_

#include <string>
#include <map>

#include <boost/assign/list_of.hpp> // for map_list_of()
#include <boost/function.hpp>
#include <boost/filesystem.hpp>

#include <boost/asio.hpp>
#include <boost/asio/signal_set.hpp>
#include <boost/shared_ptr.hpp>

#include <json/value.h>

#include "Cohort.h"
#include "ModelData.h"

//For readline
#include <readline/readline.h>
#include <readline/history.h>

class CalCommand {
public:

  std::string desc;
  
  typedef boost::function< void(const std::string&) > Executor1Str;
  
  Executor1Str executor;
  
  CalCommand() {} // won't compile w/o this declared - not sure why
  CalCommand( std::string adesc, Executor1Str an_executor ) :
    desc(adesc), executor(an_executor) {}
  
};

class CalController {
public:

  CalController(Cohort* cht_p);
  
  void auto_run(int simulation_year);
  void run_config(int simulation_year, const std::string& stage);
  
  void show_cal_control_menu();
  void check_for_signals();
  void async_pause(); // pauses, but thru the io_service, so may not be immediate.
  void pause();       // forces pause immediately


  // 12/7/2015:
  // clear_and_create_json_storage was originally a static member
  // to allow using function w/o object instantiated. Does not seem
  // to be necessary. Perhaps this should actually be part of temutil??
  // cleans up calibration json files
  void clear_and_create_json_storage();
  void archive_stage_JSON(const std::string& stage);
  void tar_caljson_for_stage(const std::string& stage);

  void clear_archived_json();


  void handle_stage_start();
  void handle_stage_end(const std::string& stage);

  boost::filesystem::path base_dir;
  boost::filesystem::path monthly_json;
  boost::filesystem::path daily_json;
  boost::filesystem::path yearly_json;

private:
  boost::shared_ptr< boost::asio::io_service > io_service;
  boost::asio::signal_set pause_sigs;

  Cohort* cohort_ptr;

  std::map<std::string, CalCommand> cmd_map;
  

  Json::Value run_configuration;

  void pause_handler(const boost::system::error_code& error,
                     int signal_number);
  void control_loop();

  void operate_on_directive_str(const std::string& line);

  Json::Value load_directives_from_file(const std::string& f);

  void set_caljson_storage_paths();

  void quit_at(const std::string& exit_year);
  void pause_at(const std::string& pause_year);

  void quit();
  void reload_all_cmt_files();
  void reload_calparbgc_file();
  void continue_simulation();
  void show_full_menu();
  void show_short_menu();

  void print_directive_settings();
  void print_calparbgc();
  void print_modules_settings();

  void cmd_wrapper(void (ModelData::*fn)(bool), const std::string& mn, const std::string& s);

  void env_cmd(const std::string& s);
  void bgc_cmd(const std::string& s);
  void avln_cmd(const std::string& s);
  void dsb_cmd(const std::string& s);


  void dsl_cmd(const std::string& s);
  void dynlai_cmd(const std::string& s);
  void nfeed_cmd(const std::string& s);
  void baseline_cmd(const std::string& s);

};

#endif /* _CALCONTROLLER_H_ */


