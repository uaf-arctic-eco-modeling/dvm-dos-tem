dvm-dos-tem
============
A process based bio-geo-chemical ecosystem model. 

Workflow
-----------
For starters we will try the "integration manager" workflow [ref to git docs?]. This means that to get started you should first "fork" the project from the github.com/ua-snap/dvm-dos-tem.git repository. This will give you your own dvm-dos-tem repository in your own github account (github.com/YOU/dvm-dos-tem.git). Next you will "clone" from your account to your own machine (where ever you perform your coding work). Finally when you have made changes on your own working machine you will "push" those changes back to your fork. If you would like the changes you made to be incorporated into the shared project (github.com/ua-snap/dvm-dos-tem.git), then issue a "pull request" from your github account.

Documentation
-------------
There is a Doxygen file (Doxyfile) included with this project. The current settings are for the Doxygen output to be generated in the docs/dvm-dos-tem/ directory.

The file is setup to build a very comprehensive set of documents, including as many diagrams as possible (call graphs, dependency diagrams, etc). To build the diagrams, Doxygen requires a few extra packages, such as the dot package. This is not available on aeshna, so running Doxygen on aeshna will produce a bunch of errors.

Compile
---------
This project has few external dependencies and should be relatively easy to build.

$ make

or 

$ make dvm

Run
---------
The project is provided with enough data in the DATA/ to run a single test site. It should work out of the box.
$ ./DVMDOSTEM config/controlfile_site.txt
