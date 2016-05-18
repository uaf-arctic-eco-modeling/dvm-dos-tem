README for dvm-dos-tem
===========================================
The dvm-dos-tem is a process based bio-geo-chemical ecosystem model.

There are two ways in which you might interact with dvmdostem: 
performaing an _extrapolation_, or performing a _calibration_. 

When performing a calibration, you will evaluate the simulation as it is 
running. You will also likely be pausing the simulation to adjusting parameters 
and settings. Calibrations are performed for a single spatial location (a single 
cohort or grid cell).

When performing an extrapolation the program progresses to completion,
typically over one or more spatial locations (multiple cohorts, or grid cells). 
The outputs are analyzed only once the simulation has completed for all
time-steps and spatial locations.

Requirements and Dependencies
-----------------------------------------------------------------------------------------
The following tools/libraries are necessary in order to compile and run dvm-dos-tem

* Boost, including [Boost.Program_options](http://www.boost.org/doc/libs/1_53_0/doc/html/program_options.html)
* NetCDF, C++ Interface, [NetCDF/Unidata](http://www.unidata.ucar.edu/software/netcdf/)
* Jsoncpp [https://github.com/open-source-parsers/jsoncpp](https://github.com/open-source-parsers/jsoncpp)

Downloading 
-----------------------------------------------------------
We (the Spatial Ecology Lab) are maintaining the main fork of dvm-dos-tem on 
Github: [https://github.com/ua-snap/dvm-dos-tem](https://github.com/ua-snap/dvm-dos-tem)

The dvm-dos-tem program is not distributed as a binary file, so to run the 
program, you must download the source code and compile it yourself. 

 * The `master` branch will always contain the latest production version of the
model. 
 * The `devel` branch will contain recent developments to the code. We try to 
 maintain a stable `devel` branch: the code merged into `devel` should always compile 
 and run, and typically has been reviewed by or discussed with several people in 
 the lab.
 
We are using Github's Pull Requests to manage contributins to the code.


Compiling / Building
-----------------------------------------------------------------------------
You have two options for compling the source code:

 * make (and Makefile)
 * scons (and SConstruct file)
 
Make is a old, widely availabe, powerful program with a somewhat arcane syntax. 
The Makefile is not setup for partial-compilation, so editing a single file 
requires and re-making the project will result in re-compiling every single
file.

Scons is a build program that is written in Python, and designed to be a easier
to use than make. The scons and the SConstruct file are smart enough to do
partial builds, so that some changes result in much faster builds.

Both programs can take a flag specifying parallel builds and the number of 
processors to use (e.g.: `-j4`) for parallel builds.

This project requires a number of libraries are installed and available on your 
path. For a complete list, see the install commands in `bootstrap-system.sh`

If you have all the requsite libraries installed and available on your path, 
then either of these commands should work:

    $ make

or 

    $ scons

### Notes on build environments
    
There are some helpful scripts provided in the `env-setup-scripts/` folder that will set
a few environment variables for you for specific systems. For instance on atlas, the
correct version of NetCDF is not provided as a system package, but the user tobey has
made it available so that you don't have to compile it yourself. You must set an
environment variable so that when you compile and run it will look in tobey's directory
for the NetCDF library files.

You can either remember to run the setup commands/script each time you logon to the
computer where are you are interacting with the model or add a line to your `~/.bashrc`
or `~/.bash_profile` that "sources" the setup script. This makes sure the setup commands
are run each time you log on. 
E.g.

    $ vim ~/.bash_profile
    # Add a line like this at the end:
    source /path/to/your/dvm-dos-tem/env-setup-scripts/setup-env-for-aeshna.sh
    
If you are successful getting dvm-dos-tem to compile and run on a different system
it would be appreciated if you submit the appropriate setup commands so that other's
don't have to spend time figuring out those details.

Running 
---------------------------------------------

Running `dvmdostem` (operating the model) requires 3 types of "input" information:

1. Driving data (input data)
2. Parameter values
3. Configuration options 

Sample driving data is provided in the `DATA/` directory, sample parameters are 
provided in the `parameters/` directory, and sample configuraiton options are 
provided in the `config/` directory. More configuration options are available
via options supplied on the command line when starting the program. The `--help`
flag provides some info and shows the defaults:

    $ ./dvmdostem --help
      -c [ --cal-mode ]                     Switch for calibration mode. When this 
                                            flag is preset, the program will be 
                                            forced to run a single site and with 
                                            --loop-order=space-major. The program 
                                            will generate yearly and monthly 
                                            '.json' files in your /tmp  directory 
                                            that are intended to be read by other 
                                            programs or scripts.
      -p [ --pre-run-yrs ] arg (=10)        The number of 'pre-run' years.
      -m [ --max-eq ] arg (=1000)           The maximum number of years to run in 
                                            equlibrium stage.
      -o [ --loop-order ] arg (=space-major)
                                            Which control loop is on the outside: 
                                            'space-major' or 'time-major'. For 
                                            example 'space-major' means 'for each 
                                            cohort, for each year'.
      -f [ --ctrl-file ] arg (=config/config.js)
                                            choose a control file to use
      -l [ --log-level ] arg (=warn)        Control the verbositiy of the console 
                                            log statements. Choose one of the 
                                            following: debug, info, note, warn, 
                                            err, fatal.
      -x [ --fpe ]                          Switch for enabling floating point 
                                            exceptions. If present, the program 
                                            will crash when NaN or Inf are 
                                            generated.
      -h [ --help ]                         produces helps message, then quits


Documentation
-----------------------------------------------------------------
There is a Doxygen file (Doxyfile) included with this project. The current settings are
for the Doxygen output to be generated in the docs/dvm-dos-tem/ directory.

The file is setup to build a very comprehensive set of documents, including as many
diagrams as possible (call graphs, dependency diagrams, etc). To build the diagrams,
Doxygen requires a few extra packages, such as the dot package. This is not available on
aeshna, so running Doxygen on aeshna will produce a bunch of errors.

Developing 
----------------------------------------------------
This project is maintained using Git (an open source distributed version control system)
and Github (a web service that provides hosting for code projects and has tools and idioms
for collaborative working on code-related projects).

This project is maintained using the "Fork and Pull" workflow. For more 
on git, forking, pulling, etc, see the wiki.

### Branching Model

The SEL maintained repository for dvm-dos-tem uses two special branches: "`master`" and
"`devel`". The `master` branch is considered the main, stable trunk of the code base. Each
commit on the `master` branch is considered a "stable" release and will have a version
number associated with it. The `devel` branch is used for holding recent developments
that are ready to be shared amongst the SEL group, but for whatever the reason are not yet
fit for including in the next "version" (release) of the model.

Generally changes are made on topic branches. Then the person who does the change requests
that their modification be pulled into the SEL `devel` branch. Eventually when the group
is happy with the `devel` branch, it is merged into `master`, creating the next "version"
of dvm-dos-tem. This stable `master` branch is an integration point for other projects,
such as the Alaska Integrated Ecosystem Model project.

### Coding Style

> TODO: add coding style info...why important, standards, makes diffs easier to read etc.

* line width max 80 chars
* use spaces instead of tabs
* documentation: doxygen style comments
* commit messages...
* line endings...


### Workflow

This project is using the "Integration Manager" workflow described [here](https://help.github.com/articles/fork-a-repo).
This means that to get started you should first "fork" the project from the 
github.com/ua-snap/dvm-dos-tem.git repository. This will give you your own dvm-dos-tem
repository in your own github account (github.com/YOU/dvm-dos-tem.git). Next you will
"clone" from your account to your own machine (where ever you perform your coding work).
Finally when you have made changes on your own working machine you will "push" those
changes back to _your_ fork. If you would like the changes you made to be incorporated
into the shared project (github.com/ua-snap/dvm-dos-tem.git), then issue a "pull request"
from your github account. This process is described in detail in the Tutorial

















