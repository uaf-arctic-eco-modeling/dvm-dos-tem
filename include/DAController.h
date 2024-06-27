#ifndef _DACONTROLLER_H_
#define _DACONTROLLER_H_

#include "util_structs.h"

class DAController {
public:

  void set_month_pause(bool new_state);
  bool get_month_pause();
  DAController();

  bool check_for_pause(timestep_id current_step);

private:
  std::vector<timestep_id> pause_dates;

  bool pause_this_year;
  bool pause_this_month;

  void print_pause_dates();
  void load_pause_dates();
};

#endif /* _DACONTROLLER_H_ */


