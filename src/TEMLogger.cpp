#include <boost/log/expressions/formatters/named_scope.hpp>
#include <boost/log/expressions.hpp>
#include <boost/phoenix.hpp>

#include "../include/TEMLogger.h"

// Create the global logger object
src::severity_logger< severity_level > glg;


// Add a bunch of attributes to it
BOOST_LOG_ATTRIBUTE_KEYWORD(severity, "Severity", severity_level)
BOOST_LOG_ATTRIBUTE_KEYWORD(pid, "ProcessID", attrs::current_process_id::value_type)
BOOST_LOG_ATTRIBUTE_KEYWORD(named_scope, "Scope", attrs::named_scope::value_type)


/** Initialize the enum parser map from strings to the enum levels.*/
template<>
EnumParser< severity_level >::EnumParser() {
    enumMap["debug"] = debug;
    enumMap["info"] = info;
    enumMap["warn"] = warn;
    enumMap["monitor"] = monitor;
    enumMap["fatal"] = fatal;
    enumMap["disabled"] = disabled;
}

std::ostream& operator<< (std::ostream& strm, severity_level level) {
    static const char* strings[] = { 
      "debug", "info", "warn", "monitor", "fatal", "disabled"
    };

    if (static_cast< std::size_t >(level) < sizeof(strings) / sizeof(*strings))
        strm << strings[level];
    else
        strm << static_cast< int >(level);

    return strm;
}

/** This implementation will not show scopes beaneath the target scope. So for
    example if the scope stack looks like this:

      PRE-RUN->bgc->M->env

    and the target_scope is 'M' then the message will not be matched.
*/
bool log_scope_filter_A( boost::log::value_ref<boost::log::attributes::named_scope_list> const& scopes,
                         const std::string& target_scope) {

  // Start by matching everything...
  bool matched(true);

  // show un-scoped messages
  if (scopes.empty()) {
    matched = true;
  }

  // loop thru scopes, only showing
  if (!scopes.empty()) {

    bool wi_target_scope(false);

    // descend stack..
    typedef attrs::named_scope_list::const_iterator iterator_t;
    for (iterator_t iter = scopes.get().begin(); iter != scopes.get().end(); ++iter) {

      if (wi_target_scope) {                           // already too deep
        matched = false;
        break;
      } else if ( (*iter).scope_name.compare(target_scope.c_str()) == 0 ) {  // this is the target
        matched = true;
        wi_target_scope = true;
      } else {                                         // must be above target
        matched = true;
      }

    }
  }

  return matched;

}

/** This implementation will show levels down until the next "time scope".
    So for example if the scope is:

    PRE-RUN->bgc->M->env

    and the target scope is 'M', then the message will be matched.
    As in show all monthly messages, but not daily messages

*/
bool filter_time_scope( boost::log::value_ref<boost::log::attributes::named_scope_list> const& scopes,
                            const std::string& time_scope) {

  bool matched(true);

  if (time_scope.compare("all") != 0) {

    typedef attrs::named_scope_list::const_iterator iterator_t;
    for (iterator_t iter = scopes.get().begin(); iter != scopes.get().end(); ++iter) {

      std::string scope = (*iter).scope_name.c_str();

      if (time_scope.compare("Y") == 0) {
        if (scope == "M") {
          matched = false;
          break;
        }
      }
      else if (time_scope.compare("M") == 0) {
        if (scope == "D") {
          matched = false;
          break;
        }
      }
      else if (time_scope.compare("D") == 0) {
        // nothing to do - currently matches everything as
        // this is our finest resolution.
      } else {
        // nothing to do...
      }
    }
  }
  return matched;
}

/** This implementation will only match records that have the 'target_scope'
    within the scope stack.
*/
bool log_scope_filter_exclude_not_matching(
    boost::log::value_ref<boost::log::attributes::named_scope_list> const& scopes,
    const std::string& target_scope) {

  bool matched = false;

  // descend stack..
  typedef attrs::named_scope_list::const_iterator iterator_t;
  for (iterator_t iter = scopes.get().begin(); iter != scopes.get().end(); ++iter) {

    if ((*iter).scope_name.compare(target_scope.c_str()) == 0) {
      matched = true;
    }

  }

  return matched;

}

/** Handle some details for the logging component of the application - log
    attributes, filters, etc.
*/
void setup_logging(const std::string& target_severity_level, const std::string& target_scope_level) {

  // Add the attributes
  logging::core::get()->add_global_attribute(
    "ProcessID", attrs::current_process_id()
  );
  logging::core::get()->add_global_attribute(
    "Scope", attrs::named_scope()
  );

  // Setup the sink
  logging::add_console_log(
    std::clog,
    keywords::format = (
      expr::stream
        //<< expr::format_date_time< boost::posix_time::ptime >("TimeStamp", "%Y-%m-%d %H:%M:%S ")
        //<< "("<< pid << ") "
        << "[" << severity << "] "
        << "[" << named_scope << "] "
        << expr::smessage
    )
  );
  
  // Setup the filtering
  try {

    EnumParser<severity_level> parser;

    logging::core::get()->set_filter(
      (
        severity >= parser.parseEnum(target_severity_level)
            &&
        boost::phoenix::bind(
          &filter_time_scope,
          boost::log::expressions::attr<boost::log::attributes::named_scope_list>("Scope").or_none(),
          target_scope_level
        )
      ));

  } catch (std::runtime_error& e) {
    std::cout << e.what() << std::endl;
    std::cout << "'" << target_severity_level << "' is an invalid --log-level! "
              << "Must be one of [debug, info, warn, monitor, fatal, disabled]\n";
    exit(-1);
  }

  //If logging is set to disabled, set the core flag
  if(target_severity_level.find("disabled") != std::string::npos){
    std::cout << "Logging disabled\n";
    logging::core::get()->set_logging_enabled(false);
  }

}

/** Print a message for each type of log and level...*/
void test_log_and_filter_settings() {
  // print messages of each level to each global logger...
  
  BOOST_LOG_SEV(glg, debug) << "General log, debug message. A very detailed message, possibly with some internal variable data.";
  BOOST_LOG_SEV(glg, info)  << "General log, info message. A detailed operating message."; 
  BOOST_LOG_SEV(glg, warn)  << "General Log, warn message. Something is amiss, results should be checked."; 
  BOOST_LOG_SEV(glg, monitor)  << "General Log, monitor message. A high-level progress message."; 
  BOOST_LOG_SEV(glg, fatal) << "General log, fatal error message. The program cannot continue and will exit non zero."; 
}
