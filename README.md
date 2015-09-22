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
      -p [ --pre-run-yrs ] arg (=10)        The maximum number of years to run in 
                                            equlibrium stage.
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



Tutorial on contributing 
===============================================
DVM-DOS-TEM is not distributed as a binary executable. This means that to run the program,
you must download the source code and compile the software. In addition, many of the
settings you may want to modify for running DVM-DOS-TEM require re-compiling the code.
This makes the distinction between "user" and "developer" a bit blurry. For this reason it
is important that everyone learn how to interact with DVM-DOS-TEM as a developer, even if
you do not intend to make a [public] modification to the codebase for quite a while.

The process of developing the DVM-DOS-TEM software involves managing the contributions 
from all the members of the Spatial Ecology Lab and keeping everyone up to date with the
latest additions to the code. To improve overall efficiency and productivity of the Lab, it
is important that everyone contribute to the same codebase. Over time this will
significantly reduce the amount of redundant work that everyone does to perform their
research. Contributions to the codebase can be to the scientific aspects of the model, or
simply improving the documentation or structure of the codebase so that it is easier to
work with. This tutorial will take you through the process of making a small contribution
to the documentation. At the end you will:

* Have made a meaningful addition to the the DVM-DOS-TEM codebase and will be prepared
to contribute more in the future. 
* You will know how to keep your copy of the software (source code) up to date with the
"upstream" (Spatial Ecology Lab) copy of the software.

While the actual steps of this tutorial might only take an hour or so to complete,
depending on your background with Linux and Git, you might expect to spend several days
working through the entire exercise as you explore some topics in more detail.

Setting up your computing environment
---------------------------------------------------------
The usual deployment target for DVM-DOS-TEM is a Linux cluster computer. While the code
can be compiled and run on a Mac, and possibly even a Windows machine, you might save
yourself headaches in the future by simply learning to use Linux. Linux makes a great
scientific computing environment, so while daunting in the beginning, your effort will
pay off in the long run. Take some time to do this - you are building yourself a good
platform for all your future work.

Fortunately with modern tools, it is possible to easily set up a "virtual machine" that
runs Linux, so you can use Linux "inside" whatever your normal computing environment is.
There are several virtualization software packages available. You may have heard of 
VMWare, Parallels, or Virtual Box.

If you choose to use a virtual machine, start by downloading and installing a
virtualization software. Virtual Box is free and highly recommended. Next choose a Linux
distribution to use and install as a "guest" system within your virtualization software.
Fedora is a recommended distribution because it is in the same family of distributions as
CentOS and RedHat Linux, which are the distributions likely to be used in larger
production environments. Alternatively, install the Linux distribution of your choice on a
dedicated host computer.

Next, become familiar with the basics of operating your new Linux computer via the command
line (Terminal). 

Take some time to familiarize yourself with:

* The difference between realtive paths and absolute paths.
* Hidden files, and a user's "dotfiles" to store personal settings (i.e. .bashrc).
* The concepts of "users" in a Linux environment, and what the distinciton is between a
normal user and the "root" user.
* How command line help is typically presented (i.e. a general prompt followed by a
command). 
* How to use the man pages to find out more about different Linux commands.

Take some time to learn about the "package manager" and how to install and update software
on your new Linux computer.

> TODO: add some good into linux ref. material


Version Control Tools
--------------------------------------------------------------------------------------
Getting familiar with Git, Github, and SEL's use of these tools.

Managing contributions from a wide group of people to a single codebase is a difficult
task. To help this, we use a version control system (VCS) called "Git". Git is absolutely
fundamental to the process of working with DVM-DOS-TEM. You must understand the basics of
this tool. We are hosting the DVM-DOS-TEM codebase with a service called Github. You must
understand the difference between Git and Github. 

It is important to learn the fundamentals of Git for personal development before you can
contribute to a group repository. Take a couple hours to read through the first few
chapters of the "Git Book". Perhaps make some simple repositories so you can test the
operations. At the outset, don't worry about pushing, pulling and remote repositories.
Focus on the basics and make sure you understand the concepts of the "working directory",
the "staging area", and the "repository".

Read the following articles to become acquainted with Git:

> TODO: find links to some good basic git info...

> TODO: find somethign about branching models...

> TODO: find basic info describing integration manager/director/lieutenants

> TODO: find good description about difference between git and github.

> TODO: something about markdown, and why we use markdown in this file...

> TODO: add something about why it is important to keep personal / platform specific / 
          absolute paths out of the codebase...

> TODO: add link to this awesome tutorial: http://pcottle.github.io/learnGitBranching/


Once you have some basic familiarity with Git and Github, you should understand how and
why you must use the following procedures to get your copy of DVM-DOS-TEM.

The following procedure will allow you to:

* Stay up to date with other developments that happen to the codebase.
* Add your own contribution to the codebase.
* Keep the codebase on different computers that you use and keep each computer up to date
with the other computers and the main SEL codebase.

So with that out of the way, lets get going.

Actually getting a copy of DVM-DOS-TEM
-------------------------------------------------------------
First:

* You need to create a (free) account with Github.
* You need to ask the administrator of the SEL Github account to add you to the SEL
workgroup so that you can view the repositories.

Now sign into Github. Spend some time familiarizing yourself with the interface. Explore
some repositories.

If you have been added to the SEL Github team, you should be able to see a variety of SEL
owned repositories in your Github account. Pay particular attention to which repository
you are viewing in the Github account (i.e. yours, vs. the SEL "fork" of the code). Pay
attention to the URL in the address bar of your browser - it is usually quite clear and a
good indication of what repository you are actually looking at.

Next, find the "sel-help" repository on Github and look for the "github-flowchart" PDF
files.

Download and read these documents and decide the way in which you will plan on interacting
with the code. The .pdfs are designed to be printed in two normal sized sheets of paper
and hung somewhere convenient for your quick reference.

The remainder of this tutorial will take you through actually contributing to the source
code (well actually the documentation - which you will discover should lives with(in) the
source code), so make sure you find and understand that path through the flow chart that
supports making a contribution. The steps in this tutorial should follow that path on the
flowchart.

For DVM-DOS-TEM we are using the "Integration Manager" workflow. This is also sometimes
referred to as the "Fork and Pull" model. We do not have a dedicated person who serves as
the Integration Manager. We all have the rights to merge code into the trunk, but the
workflow encourages review of changes by the group before they are merged into the trunk.

> TODO: find link to description of fork/pull and or integration manager.

If you have not done so already, create your own "fork" of the codebase. This operation
happens on Github. Look for the button on the Github website. The result is that your
Github account now contains a copy of the DVM-DOS-TEM codebase. You should be able to
identify this based on several cues in the Github web interface, not the least of which is
the URL in your browser's address bar.

Next, you need to get a copy of the code onto your local computer where you plan to work.
(likely your new virtual machine, but this could also be a dedicated Linux computer, or
perhaps your account on one of the UAF cluster computers (aeshna, or atlas).

* Navigate to a location on your Linux computer where you would like to store the model.
* On Github, navigate to your fork of the model.
* On Github, find the clone address for the code. Either the HTTP, or SSH address will
work, but in the long run, it will be worth your while to make the SSH work because it
allows secure access without having to constantly type in your password. However SSH can
be configured later. For now, choose one of the methods...
* Copy the clone address from Github and issue the cloning command on your Linux computer.
This will create a directory named "dvm-dos-tem" and will grab all the information from
Github (all the source code, all the history, some sample data, and a good chunk of
documentation) and download it to your Linux computer. Because we bundle some sample test
data with DVM-DOS-TEM, this is actually a fairly large download, so it might take a few
seconds.

Congratulations! Now you have DVM-DOS-TEM on your computer!

Now it is time to make a change and submit that change back to the "upstream" codebase for
inclusion there.

> NOTE: The upstream repository refers to the main, Spatial Ecology Lab repository. Your
> goal with this tutorial is to make modifications in your codebase and then request that
> your changes are included in the upstream repository.

> An additional goal is to keep your repository up to date with the upstream repository,
so that you have the most recent modifications that anyone else has made.

Making your modification...
--------------------------------------
For this tutorial, you will be making a small modification to improve the documentation of
DVM-DOS-TEM.

> TODO: add notes on setting up your personal computing environment for working with git.

> Specifically:

> * adding to your bashrc file to add the current git branch to your prompt
> * helpful git config settings, (like adding color)
> * gitk, and git gui

First, notice that you are on the master branch. For the SEL maintained dvm-dos-tem, we
follow a specific "branching model". The branching  model helps keep an clear
understandable history for the project. The branching model gives specific semantic value
to differnet points in the history tree.

> TODO: add link to branching model section 

Acoording to the branching model, the `master` branch might not have the most recent code.
We would like our modification to be based off the `devel` branch, and eventually to be
pulled into the SEL repository's `devel` branch.

> NOTE: might be good to add some details about git, remotes, origin, and upstream...

> TODO: Determine how to manage development and master branches on individual forks.

> TODO: add remote "upstream" to point toward github/ua-snap/dvm-dos-tem?

> TODO: add some history about why sel's code is stored at github/ua-snap account...

To do this, first checkout a local `devel` branch which is based off your fork's `devel`
branch.

    $ git checkout --track remotes/origin/devel
    
Now you have, locally, all the most recent code from your fork's `devel` branch. Next you
need to make a change that you wish to be included in the upstream repo.

Although not strictly necessary, we will further isolate this change in a topic branch.
For a small modification, such as the typo we are going to fix, this is a bit of extra
complexity, but for a larger changeset, such as a new feature, or addition of a new 
scientific concept, using a separate topic branch is important.

    $ git checkout -b improve-docs

Finally, we are ready to get down to work. Read the documentation (this tutorial, the main
README.md, or comments in the code itself) and find an error. This should be easy! Your
error can be as small as a typo, or as large as a paragraph that you re-work or decide
needs to be added or deleted.

Make the modification using the text editor of your choice....

After you have modified and saved the file, use Git to see if you can get a concise
summary of the changes you made (using the command line `git diff`, or some graphical tool
such as Git Gui.

Now you need to commit your change. You can use Git Gui for this or the command line:

    $ git add <path/to/the/file/you/just/changed>
    $ git commit -m "Update documentation; my first contribution to dvm-dos-tem"
    
Now the modifacation you have made is a part of your *local* history. The next steps are
to:
 
1. Make sure you are up to date with all the developments that have happened in the
upstream repository. 
2. Push your changes up to your fork. 
3. Request that your awesome modification is incorporated to the upstream version.

> TODO: add some discussion about why you need to make sure you are up to date with
the upstream repo (merging locally, handling merge conflicts locally)

## Making sure you are up to date...

So to start, make sure you are up to date with the upstream repository's devel branch

    $ git fetch upstream/devel
    $ git merge upstream/devel
    
> TODO: Address why "git fetch, get merge" vs just "git pull"?

Now if there are any merge conflicts, you will need to fix them. This is pretty
unlikely, but possible. A merge conflict would only occur if someone else had changed the
same lines of the same file as you in the time frame since you checked it out the file. In
that case, you would have to decide whose modification to accept - this process is known
as resolving merge conflicts.

After you have addressed (and fixed locally) any conflicts, it is time to push your
changes up to your fork on github.

## Pushing your changes...

    $ git push origin improve-docs

> NOTE: Read about Git and remote repositories. You should have cloned from your fork, so
the remote `origin` should point toward your fork, *not* the upstream repository!
    
Now if you go back to the Github web site, you should be able to view your modification.
Try the "Network View" to see this. You should see a new commit dot with your changes
labeled on your fork as `improve-docs`.

## Requesting that your modification be included in the upstream

OK, finally, you are ready to have your modification incorporated into the upstream
codebase. On the Github interface, find the button for "Pull Request". Make sure that you
have the settings correct: you want to pull the new branch you just created, 
(`improve-docs`), into the `upstream/devel branch`.

OK, you are finished! The next step is that someone in the SEL group (the "Integration
Manager") must accept the pull request. Because we all have rights to do this, you can
actually do this yourself, but it is a good habit to get feedback from the group before
merging code into the upstream repository. To merge the pull request, navigate to the
ua-snap/dvm-dos-tem repository, navigate to the "Pull Requests" section, and find your
request. Then look for the button to merge this request. This will create a new commit on
the `ua-snap/dvm-dos-tem/devel` branch.

Final Thoughts
----------------------
Congratulations. Now you are almost a software developer and are ready to start working
with DVM-DOS-TEM. You should now understand:

* The basics of setting up a computing environment for use with DVM-DOS-TEM.
* The difference between Git and Github.
* Why we are using Git and Github.
* Why it is important to follow this procedure for getting DVM-DOS-TEM.
* How to get a copy of DVM-DOS-TEM.
* The basic workflow for making a modification to DVM-DOS-TEM and submitting it for
inclusion "upstream".
* How to keep your codebase up to date with the modifications that are happening in the
"upstream" repository.
















