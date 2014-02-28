#include "TEMLogger.h"

/** Initialize the enum parser map from strings to the enum levels.*/
template<>
EnumParser< severity_level >::EnumParser() {
    enumMap["debug"] = debug;
    enumMap["info"] = info;
    enumMap["note"] = note;
    enumMap["warn"] = warn;
    enumMap["err"] = err;
    enumMap["fatal"] = fatal;
}

std::ostream& operator<< (std::ostream& strm, severity_level level) {
    static const char* strings[] = { 
      "debug", "info", "note", "warn", "err", "fatal"
    };

    if (static_cast< std::size_t >(level) < sizeof(strings) / sizeof(*strings))
        strm << strings[level];
    else
        strm << static_cast< int >(level);

    return strm;
}


BOOST_LOG_GLOBAL_LOGGER_INIT(my_logger, src::severity_logger<severity_level>)
{
    src::severity_logger<severity_level> lg;
    //lg.add_attribute("StopWatch", boost::make_shared< attrs::timer >());
    return lg;
}


void setup_logging(std::string lvl) {


  /** This will be the "application log".
  * Writes to standard error. 
  *
  * For info on cout, std::out, std::err, std::clog etc:  
  * http://stackoverflow.com/questions/2404221/the-question-regarding-cerr-cout-and-clog
  * from an answer part way down:
  *
  *   > So, cout writes to standard output, and is buffered. Use this 
  *   > for normal output. cerr writes to the standard error stream, and is 
  *   > unbuffered. Use this for error messages. clog writes to the standard 
  *   > error stream, but is buffered. This is useful for execution logging,
  *   > as it doesn't interfere with standard output, but is efficient (at the 
  *   > cost that the end of the log is likely to be lost if the program crashes).
  * 
  */

  logging::add_console_log(
    std::clog,
    keywords::format = (
      expr::stream
        //<< expr::format_date_time< boost::posix_time::ptime >("TimeStamp", "%Y-%m-%d %H:%M:%S ")
        << "[" << severity << "] " 
        << expr::smessage
    )
  );

  // set the severity level...
  EnumParser<severity_level> parser;
  logging::core::get()->set_filter(
    ( severity >= parser.parseEnum(lvl) )
  );

}


/** Print a message for each type of log and level...*/
void test_log_and_filter_settings() {
  
  // get handles to all the global logger objects...
  //src::severity_logger< severity_level > glg;

  // print messages of each level to each global logger...
  BOOST_LOG_SEV(glg, debug) << "General log, debug message. A very detailed message, possibly with some internal variable data.";
  BOOST_LOG_SEV(glg, info) << "General log, info message. A detailed operating message."; 
  BOOST_LOG_SEV(glg, note) << "General log, note message. A general operating message."; 
  BOOST_LOG_SEV(glg, warn) << "General Log, warn message. Something is amiss, but results should be ok."; 
  BOOST_LOG_SEV(glg, err) << "General log, error message. The program may keep running, but results should be suspect."; 
  BOOST_LOG_SEV(glg, fatal) << "General log, fatal error message. The program cannot continue and will exit non zero."; 
}




