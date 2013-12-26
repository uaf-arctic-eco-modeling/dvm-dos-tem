#include "TEMLogger.h"

BOOST_LOG_INLINE_GLOBAL_LOGGER_INIT(my_general_logger, severity_channel_logger_t) {
  return severity_channel_logger_t(keywords::channel = "GENER");
}
BOOST_LOG_INLINE_GLOBAL_LOGGER_INIT(my_cal_logger, severity_channel_logger_t) {
  return severity_channel_logger_t(keywords::channel = "CALIB");
}

std::ostream& operator<< (std::ostream& strm, general_severity_level level) {
    static const char* strings[] = { 
      "debug",
      "info",
      "note",
      "warn",
      "rterror",
      "fatal"
    };

    if (static_cast< std::size_t >(level) < sizeof(strings) / sizeof(*strings))
        strm << strings[level];
    else
        strm << static_cast< int >(level);

    return strm;
}


void HELPME(){
  severity_channel_logger_t& glg = my_general_logger::get();
  severity_channel_logger_t& clg = my_cal_logger::get();
}


