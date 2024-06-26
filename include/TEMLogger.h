#ifndef _TEMLOGGER_H_
#define _TEMLOGGER_H_

#include <string>
#include <iostream>
#include <sstream>
#include <cstdlib>
#include <exception>
#include <map>
#include <iomanip>

#include <boost/log/core.hpp>
#include <boost/log/trivial.hpp>
#include <boost/log/sources/global_logger_storage.hpp>
#include <boost/log/sources/severity_feature.hpp>
#include <boost/log/sources/severity_logger.hpp>
#include <boost/log/expressions.hpp>
#include <boost/log/utility/setup/console.hpp>

#include <boost/log/attributes/current_process_id.hpp>
#include <boost/log/attributes/scoped_attribute.hpp>


namespace logging = boost::log;
namespace src = boost::log::sources;
namespace attrs = boost::log::attributes;
namespace keywords = boost::log::keywords;
namespace expr = boost::log::expressions;
namespace sinks = boost::log::sinks;

/** Define the "severity levels" for Boost::Log's severity logger. */
enum severity_level {
  debug, info, warn, monitor, fatal, disabled
};

/** Convert from string to enum integer value.
 *
 * Inspired by: http://stackoverflow.com/questions/726664/string-to-enum-in-c
 */
template <typename T>
class EnumParser {
    std::map <std::string, T> enumMap;
public:
    EnumParser(){};

    T parseEnum(const std::string &value) { 
        typename std::map<std::string, T>::const_iterator iValue = enumMap.find(value);
        if (iValue == enumMap.end())
            throw std::runtime_error("Value not found in enum!");
        return iValue->second;
    }
    
};


BOOST_LOG_GLOBAL_LOGGER(my_logger, src::severity_logger< severity_level >);

/** Send string representing an enum value to stream 
 */
std::ostream& operator<< (std::ostream& strm, severity_level lvl);

void setup_logging(const std::string& target_severity_level, const std::string& target_scope_level);

void test_log_and_filter_settings();


#endif /* _TEMLOGGER_H_ */


