#ifndef _CALCONTROLLER_H_
#define _CALCONTROLLER_H_

#include <string>
#include <map>

#include <boost/assign/list_of.hpp> // for map_list_of()
#include <boost/function.hpp>

#include <boost/asio.hpp>
#include <boost/asio/signal_set.hpp>
#include <boost/shared_ptr.hpp>

#include <json/value.h>

#include "runmodule/Cohort.h"

//For readline
#include <readline/readline.h>
#include <readline/history.h>

//template<typename R, typename P1, typename P2>
//struct Executor {
//  boost::function<R (P1,P1) >
//}

class CalCommand {
public:

  std::string desc;
  
  //typedef boost::function<void(int, int, int)> Executor3;
  
  typedef boost::function< void(const std::string&) > Executor1Str;
  
  Executor1Str executor;
  
  CalCommand() {} // won't compile w/o this declared - not sure why
  CalCommand( std::string adesc, Executor1Str an_executor ) :
    desc(adesc), executor(an_executor) {}
  
};

class CalController {
public:

  CalController(Cohort* cht_p, Json::Value config_obj);
  
  void auto_run(int simulation_year);
  void run_config(int simulation_year);
  
  void show_cal_control_menu();
  void check_for_signals();
  void async_pause(); // pauses, but thru the io_service, so may not be immediate.
  void pause();       // forces pause immediately
  static void clear_and_create_json_storage(); // cleans /tmp directory
  
  void execute(boost::function<void()> selected_function);

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

  void quit_at(const std::string& exit_year);
  void pause_at(const std::string& pause_year);

  void quit();
  void reload_all_cmt_files();
  void reload_calparbgc_file();
  void continue_simulation();
  void show_full_menu();
  void show_short_menu();

  void env_cmd(const std::string& s);
  void bgc_cmd(const std::string& s);
  void avln_cmd(const std::string& s);


  void dsb_ON();
  void dsb_OFF();
  void dsl_ON();
  void dsl_OFF();
  void dvm_ON();
  void dvm_OFF();

  void nfeed_ON();
  void nfeed_OFF();

  void avlnflg_ON();
  void avlnflg_OFF();

  void baseline_ON();
  void baseline_OFF();

  void print_calparbgc();
  void print_modules_settings();
};



//class Command {
//public:
//  virtual ~Command();
//  virtual void Execute() = 0;
//protected:
//  Command();
//};
//
//class AvlnCommand : public Command {
//public:
//  AvlnCommand(CalController*);
//  virtual void Execute();
//protected:
//  virtual bool AskUser();
//private:
//  CalController  _calcontroller;
//  bool _response;
//};
//
//AvlnCommand::AvlnCommand (CalController* cc) {
//  _calcontroller = cc;
//}
//void AvlnCommand::Execute() {
//  bool resp = AskUser();
//  if (resp) {
//    _calcontroller.avlnflg_ON();
//  } else {
//    _calcontroller.avlnflg_OFF();
//  }
//
//}


#endif /* _CALCONTROLLER_H_ */


