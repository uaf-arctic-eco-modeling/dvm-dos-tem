#ifndef _DACONTROLLER_H_
#define _DACONTROLLER_H_

#include "util_structs.h"
#include "Cohort.h"

class Cohort;

class DAController {
public:

  DAController();

  OutputSpec lai_outspec;
  OutputSpec vegc_outspec;
  OutputSpec strn_outspec;

  OutputSpec lwc_outspec;
  OutputSpec rawc_outspec;
  OutputSpec soma_outspec;
  OutputSpec sompr_outspec;
  OutputSpec somcr_outspec;

  void set_month_pause(bool new_state);
  bool get_month_pause();

  double read_scalar_var(const std::string& varname);
  bool check_for_pause(timestep_id current_step);

  void run_DA(timestep_id current_step);

  Cohort* cohort;

private:

  std::vector<timestep_id> pause_dates;

  std::string da_filename;

  bool pause_this_year;
  bool pause_this_month;

  void print_pause_dates();
  void load_pause_dates();
  void create_da_nc_file();
};

#endif /* _DACONTROLLER_H_ */


