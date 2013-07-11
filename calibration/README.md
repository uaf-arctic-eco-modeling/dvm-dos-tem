# README for dvm-dos-tem CALIBRATION VERSION  
(This file is written in a plain text format called "markdown": 
[http://github.github.com/github-flavored-markdown/])

These notes concern the calibration version. The extrapolation version is in the 
directory above this one.

## Dependency Notes 
Compiling and running this software requires the following software be installed on your 
machine:
* ant
* java (so far only tested with Sun Java, v1.6.0.xx)
* javac (java compiler)
* jar (tool for creating java jar files
(All this stuff is usually included with the "JDKs" (Java Development Kits)

* g++ compiler
* SWIG
* ?? more??
 

The calibration version (Java code that wraps C++ providing a GUI and various I/O
routines) is in this `calibration/` subdirectory of the main project. The calibration 
code uses the same C++ files for its core calculations as the extrapolation version. 
This accomplished by compiling the C++ code into a shared library. The Java application 
is then linked against this shared library and can control the C++ code.

To ensure that the calibration version is always built with the most current extrapolation
codes, the compile script is designed to simply point toward the main C++ codes (in the 
directory above this one).

To build and run the calibration version, use these commands:

    $ ant distclean
    $ ant
    $ java -Djava.library.path="lib" -jar dvm-dos-tem-calibrator.jar

The build is done with a tool called "ant" and the commands are provided in `build.xml`
script.

If source files are added or removed from the project, the following files may need to be
updated:

* The main project Makefile (controls how the extrapolation version is built).
* The `calibration/build.xml` script (controls how the calibration version is built).
* The `calibration/cpp-wrapper/*.i` files that SWIG uses to build the Java/C++ interface.

So far the codes have been successfully built on aeshna.

The general steps of the build process are:

* Some operating system specific properties are set
* SWIG reads the C++ code and generates Java wrapper code
* The C++ code is compiled as a "shared library"
* The Java code is compiled using the SWIG generated code to "point into"
the C++ shared library.
* The java code is packaged into a jar

Finally to run the program:

* The java virtual machine is started with the right jar and told where to 
look for the shared C++ library.

# Debugging Info
Generally the steps to debug are:

* Compile in debug mode.
* Launching the program in debug mode.
* Attach the debugger.
* Use the debugger to interact with the program...

## Compile in debug mode
In order to use the debugger, the code must be compiled in debug mode. This includes 
special symbols in the final files so that the debugger can provide useful information 
while stepping through the program. For now we are simply leaving the debug flags in the 
build.xml file, so the build will always be in debug mode. If performance becomes an 
issue, a different, non-debug step could be added to build.xml.

## Launching the program in debug mode.
In a terminal window, start the JVM (Java Virtual Machine) with a variety of options
 that allow a debugger to be attached to the code.

    $ java -Xdebug -Xrunjdwp:transport=dt_socket,server=y,suspend=y,address=5005 \
    -Djava.library.path="lib" -jar dvm-dos-tem-calibrator.jar

## Attaching the debugger
In another terminal window, attach jdb (Java command line Debugger tool) to the JVM you 
just started in the first terminal window.

    $ jdb -attach 5005 -sourcepath java-code
    Set uncaught java.lang.Throwable
    Set deferred uncaught java.lang.Throwable
    Initializing jdb ...
    >
    VM Started: No frames on the current call stack
    
    main[1] step
    >
    Step completed: "thread=main", TEMCalibrator.<clinit>(), line=19 bci=0

The `-sourcepath` flag tells the debugger where to look for source code.

## Interact with the debugger
Type the help command to see a list of available commands for jdb.

    > main[1] help
    ** command list **
    connectors                -- list available connectors and transports in this VM
    
    run [class [args]]        -- start execution of application's main class
    
    threads [threadgroup]     -- list threads
    thread <thread id>        -- set default thread
    suspend [thread id(s)]    -- suspend threads (default: all)
    resume [thread id(s)]     -- resume threads (default: all)
    where [<thread id> | all] -- dump a thread's stack
    wherei [<thread id> | all]-- dump a thread's stack, with pc info
    ....
    ....etc (many more commands available)
    
One thing to remember is that to set breakpoints it is necessary to specify the fully
qualified path, including the package hierarchy. So for instance to stop in a method of 
the TemCalGUI class you would type:

    > main[1] stop in GUI.TemCalGUI.readInitparFromFile
    
