#ifndef _TEMLOGGER_H_
#define _TEMLOGGER_H_

#include <string>
#include <iostream>
#include <fstream>
#include <sstream>
#include <ctime>
#include <cstdlib>
#include <exception>
#include <map>
#include <iomanip>

#include <boost/date_time/posix_time/ptime.hpp>

#include <boost/log/core.hpp>
#include <boost/log/trivial.hpp>
#include <boost/log/sources/record_ostream.hpp>
#include <boost/log/sources/logger.hpp>
#include <boost/log/sources/global_logger_storage.hpp>
#include <boost/log/sources/severity_feature.hpp>
#include <boost/log/sources/severity_logger.hpp>
#include <boost/log/sources/severity_channel_logger.hpp>
#include <boost/log/expressions.hpp>
#include <boost/log/attributes.hpp>
#include <boost/log/attributes/current_thread_id.hpp>
#include <boost/log/support/date_time.hpp>
#include <boost/log/utility/setup/common_attributes.hpp>
#include <boost/log/utility/formatting_ostream.hpp>
#include <boost/log/utility/setup/console.hpp>
#include <boost/log/utility/setup/file.hpp>
#include <boost/utility/empty_deleter.hpp>
#include <boost/log/sinks/unlocked_frontend.hpp>
#include <boost/log/sinks/text_file_backend.hpp>


namespace logging = boost::log;
namespace src = boost::log::sources;
namespace attrs = boost::log::attributes;
namespace keywords = boost::log::keywords;
namespace expr = boost::log::expressions;
namespace sinks = boost::log::sinks;

/** Define the "severity levels" for Boost::Log's severity logger. */
enum general_severity_level {
  debug, info, note, warn, err, fatal
};

/** A small helper to class to convert from string to enum integer value 
*   Inspiration lifted from here:
*   http://stackoverflow.com/questions/726664/string-to-enum-in-c
*/
template <typename T>
class EnumParser {
    std::map <std::string, T> enumMap;
public:
    EnumParser(){};

    T parseEnum(const std::string &value) { 
        typename std::map<std::string, T>::const_iterator iValue = enumMap.find(value);
        if (iValue == enumMap.end())
            throw std::runtime_error("");
        return iValue->second;
    }
};


// The operator is used for regular stream formatting
// i.e. printing the flag instead of the enum value..
std::ostream& operator<< (std::ostream& strm, general_severity_level level);

BOOST_LOG_ATTRIBUTE_KEYWORD(severity, "Severity", general_severity_level)
BOOST_LOG_ATTRIBUTE_KEYWORD(channel, "Channel", std::string)
BOOST_LOG_ATTRIBUTE_KEYWORD(timestamp, "TimeStamp", boost::posix_time::ptime)

typedef src::severity_channel_logger< general_severity_level, 
                                      std::string > severity_channel_logger_t;

// get a handle for the global "general logger" object...
BOOST_LOG_INLINE_GLOBAL_LOGGER_DEFAULT(stubb_logger, severity_channel_logger_t)
BOOST_LOG_INLINE_GLOBAL_LOGGER_DEFAULT(stubb_cal_logger, severity_channel_logger_t)

void setup_logging(std::string lvl, std::string calMode);

//void setup_calibration_log_sink();
//void setup_general_console_log_sink();

void test_log_and_filter_settings();


#endif /* _TEMLOGGER_H_ */


