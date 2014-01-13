#include "TEMLogger.h"

BOOST_LOG_INLINE_GLOBAL_LOGGER_INIT(my_general_logger, severity_channel_logger_t) {
  return severity_channel_logger_t(keywords::channel = "GENER");
}
BOOST_LOG_INLINE_GLOBAL_LOGGER_INIT(my_cal_logger, severity_channel_logger_t) {
  return severity_channel_logger_t(keywords::channel = "CALIB");
}

std::ostream& operator<< (std::ostream& strm, general_severity_level level) {
    static const char* strings[] = { 
      "debug", "info", "note", "warn", "err", "fatal"
    };

    if (static_cast< std::size_t >(level) < sizeof(strings) / sizeof(*strings))
        strm << strings[level];
    else
        strm << static_cast< int >(level);

    return strm;
}


void setup_console_log_filters(std::string gen_settings, std::string cal_settings){

  logging::core::get()->set_filter(
    severity >= debug || (expr::has_attr(channel) && channel == "CALIB")
  );
}

void setup_console_log_sink(){

  logging::add_common_attributes();

  logging::add_console_log (
    std::clog,
    keywords::format = (
      expr::stream
        // works, just don't need timestamp right now...        
        //<< expr::format_date_time< boost::posix_time::ptime >("TimeStamp", "%Y-%m-%d %H:%M:%S ")
        << "(" << channel << ") "
        << "[" << severity << "] " << expr::smessage
    )
  );
  
  // MAYBE USEFUL?
  //<< std::setw(3) << std::setfill(' ')
}


/** Print a message for each type of log and level...*/
void test_log_and_filter_settings() {
  
  // get handles to all the global logger objects...
  severity_channel_logger_t& glg = my_general_logger::get();
  severity_channel_logger_t& clg = my_cal_logger::get();

  // print messages of each level to each global logger...
  BOOST_LOG_SEV(glg, debug) << "General Log; debug message...";
  BOOST_LOG_SEV(glg, info) << "General Log; info message..."; 
  BOOST_LOG_SEV(glg, note) << "General Log; note message..."; 
  BOOST_LOG_SEV(glg, warn) << "General Log; warn message..."; 
  BOOST_LOG_SEV(glg, err) << "General Log; err message..."; 
  BOOST_LOG_SEV(glg, fatal) << "General Log; fatal message..."; 

  BOOST_LOG_SEV(clg, debug) << "Calibration Log; debug message..."; 
  BOOST_LOG_SEV(clg, info) << "Calibration Log; info message..."; 
  BOOST_LOG_SEV(clg, note) << "Calibration Log; note message...";
  BOOST_LOG_SEV(clg, warn) << "Calibration Log; warn message..."; 
  BOOST_LOG_SEV(clg, err) << "Calibration Log; err message..."; 
  BOOST_LOG_SEV(clg, fatal) << "Calibration Log; fatal message..."; 
}




