#include "TEMLogger.h"

BOOST_LOG_INLINE_GLOBAL_LOGGER_INIT(my_general_logger, severity_channel_logger_t) {
  return severity_channel_logger_t(keywords::channel = "GENER");
}
BOOST_LOG_INLINE_GLOBAL_LOGGER_INIT(my_cal_logger, severity_channel_logger_t) {
  return severity_channel_logger_t(keywords::channel = "CALIB");
}


/** Initialize the enum parser map from strings to the enum levels.*/
template<>
EnumParser< general_severity_level >::EnumParser() {
    enumMap["debug"] = debug;
    enumMap["info"] = info;
    enumMap["note"] = note;
    enumMap["warn"] = warn;
    enumMap["err"] = err;
    enumMap["fatal"] = fatal;
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

/** Use the Enum parser to find the level, and set up the logging filter. */
// void set_log_severity_level(std::string lvl) {
//   EnumParser<general_severity_level> parser;
//   logging::core::get()->set_filter(
//     severity >= parser.parseEnum(lvl)
//     
//   );
// 
//   // example of more complicated filter:
//   // severity >= debug || (expr::has_attr(channel) && channel == "CALIB")
// }



void setup_logging(std::string lvl, std::string calMode) {

  boost::shared_ptr< logging::core > core = logging::core::get();

  //
  // CALIBRATION LOGGER
  //
  
  // backend: everything else related to a sink (writing to a file in this case)
  boost::shared_ptr< sinks::text_file_backend > cal_backend = 
      boost::make_shared< sinks::text_file_backend >(
        keywords::file_name = "CAL_LOG_%5N.log"
      );
  
  // add a stream to the backend
  //cal_backend->add_stream( boost::shared_ptr< std::ostream >(new std::ofstream("cal.log")));
  
  // frontend: tasks common to all sinks - filtering, sync model, formatting
  typedef sinks::synchronous_sink< sinks::text_file_backend > log_sink_type;
  boost::shared_ptr< log_sink_type > cal_sink(new log_sink_type(cal_backend));
  
  // filtering
  //cal_sink->set_filter(expr::has_attr(channel) && channel == "CALIB");

  // formatting
  cal_sink->set_formatter (
    expr::stream
      << "(" << channel << ") " 
      << "[" << severity << "] REALLY? ONLY FILE FOR THIS>>> " 
      << expr::smessage
  );
  
  logging::core::get()->add_sink(cal_sink);

  //
  // NOW THE GENERAL LOGGER
  // 
  
  // backend
  boost::shared_ptr< sinks::text_ostream_backend > gen_backend = boost::make_shared< sinks::text_ostream_backend >();
  
  // add stream to sink (We have to provide an empty deleter to avoid destroying the global stream object)
  gen_backend->add_stream(boost::shared_ptr< std::ostream >(&std::cout, boost::empty_deleter()));
 
  // frontend to the sink
  typedef sinks::synchronous_sink< sinks::text_ostream_backend > lst;
  boost::shared_ptr< lst > gen_sink = boost::make_shared< lst >();

  //gen_sink->set_filter(expr::has_attr(channel) && channel == "GENER");

  // formatting
  gen_sink->set_formatter (
    expr::stream
      << "(" << channel << ") " 
      << "[" << severity << "] " << "WHERE ARE MY GEENERAL MSGS GOING??? " 
      << expr::smessage
  );

  
  core->add_sink(gen_sink);
  
  
  if ( calMode.compare("off") == 0 ) {
    core->remove_sink(cal_sink);
  }

  EnumParser<general_severity_level> parser;
  logging::core::get()->set_filter(
    ( severity >= parser.parseEnum(lvl) )
  );

}

/** This will be the "application log".
 * Writes to standard error. 
 *
 * For info on cout, std::out, std::err, std::clog etc:  
 * http://stackoverflow.com/questions/2404221/the-question-regarding-cerr-cout-and-clog
 * from an answer part way down:
 *
 * > So, cout writes to standard output, and is buffered. Use this 
 * > for normal output. cerr writes to the standard error stream, and is 
 * > unbuffered. Use this for error messages. clog writes to the standard 
 * > error stream, but is buffered. This is useful for execution logging,
 * > as it doesn't interfere with standard output, but is efficient (at the 
 * > cost that the end of the log is likely to be lost if the program crashes).
 * 
*/
/*
void setup_general_console_log_sink() {

  logging::add_common_attributes();

  //logging::core::get()->add_global_attribute(
  //    "ThreadID", boost::log::attributes::current_thread_id()
  //); 

  logging::add_console_log (
    std::clog,
    (expr::has_attr(channel) && channel == "GENER"),
    keywords::format = (
      expr::stream
        //<< expr::format_date_time< boost::posix_time::ptime >("TimeStamp", "%Y-%m-%d %H:%M:%S ")
        << "(" << channel << ") "
        << "[" << severity << "] " 
        //<< expr::attr< attrs::current_thread_id::value_type >("ThreadID") << "  "
        << expr::smessage
    )
  );


  // for info on formatting thread id
  // http://sourceforge.net/p/boost-log/discussion/710021/thread/e90226f5/
  
  // MAYBE USEFUL?
  //<< std::setw(3) << std::setfill(' ')
}
*/

/** Print a message for each type of log and level...*/
void test_log_and_filter_settings() {
  
  // get handles to all the global logger objects...
  severity_channel_logger_t& glg = my_general_logger::get();
  severity_channel_logger_t& clg = my_cal_logger::get();

  // print messages of each level to each global logger...
  BOOST_LOG_SEV(glg, debug) << "General log, debug message. A very detailed message, possibly with some internal variable data.";
  BOOST_LOG_SEV(glg, info) << "General log, info message. A detailed operating message."; 
  BOOST_LOG_SEV(glg, note) << "General log, note message. A general operating message."; 
  BOOST_LOG_SEV(glg, warn) << "General Log, warn message. Something is amiss, but results should be ok."; 
  BOOST_LOG_SEV(glg, err) << "General log, error message. The program may keep running, but results should be suspect."; 
  BOOST_LOG_SEV(glg, fatal) << "General log, fatal error message. The program cannot continue and will exit non zero."; 

  BOOST_LOG_SEV(clg, debug) << "Calibration log, debug message. Boring details."; 
  BOOST_LOG_SEV(clg, info) << "Calibration log, info message. Data for scripts."; 
  BOOST_LOG_SEV(clg, note) << "Calibration log, note message. General operating messages.";
  BOOST_LOG_SEV(clg, warn) << "Calibration log, warn message."; 
  BOOST_LOG_SEV(clg, err) << "Calibration log, err message."; 
  BOOST_LOG_SEV(clg, fatal) << "Calibration log, fatal message."; 
}




