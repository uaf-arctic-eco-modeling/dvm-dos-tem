# README for dvm-dos-tem CALIBRATION VERSION  
(This file is written in a plain text format called "markdown": 
[http://github.github.com/github-flavored-markdown/])

These notes concern the calibration version. The extrapolation version is in the 
directory above this one.

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








