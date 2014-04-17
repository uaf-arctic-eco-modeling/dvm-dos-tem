#ifndef _CALCONTROLLER_H_
#define _CALCONTROLLER_H_

#include <string>
#include <map>

#include <boost/assign/list_of.hpp> // for map_list_of()
#include <boost/function.hpp>

#include <boost/asio.hpp>
#include <boost/asio/signal_set.hpp>
#include <boost/shared_ptr.hpp>

#include "runmodule/Cohort.h"

//For readline
#include <readline/readline.h>
#include <readline/history.h>

typedef struct CalCommand {
  std::string desc;
  boost::function<void ()> executor;
  
  CalCommand(){} // won't compile w/o this declared - not sure why
  CalCommand( std::string adesc, boost::function<void ()> aexecutor ) :
      desc(adesc), executor(aexecutor) {}
  
} CalCommand;

class CalController {
public:
  
  CalController(Cohort* cht_p);
  std::string get_user_command();
  void show_cal_control_menu();
  void check_for_signals();
  void async_pause(); // pauses, but thru the io_service, so may not be immediate.
  void pause();       // forces pause immediately

private:
  boost::shared_ptr< boost::asio::io_service > io_service;
  boost::asio::signal_set pause_sigs;

  Cohort* cohort_ptr;
  
  std::map<std::string, CalCommand> cmd_map; 

  void pause_handler( const boost::system::error_code& error, int signal_number);
  void control_loop();

  void quit();
  void reload_all_cmt_files();
  void reload_calparbgc_file();
  void continue_simulation();
  void show_full_menu();
  void show_short_menu();
  //static to allow passing as a function pointer
  static void cb_linehandler(char*);

  void env_ON();
  void env_OFF();
  void bgc_ON();
  void bgc_OFF();
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

#endif /* _CALCONTROLLER_H_ */


