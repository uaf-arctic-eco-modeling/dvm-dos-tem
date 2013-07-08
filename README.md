README for dvm-dos-tem
===========================================
The dvm-dos-tem is a process based bio-geo-chemical ecosystem model.

There are two main parts that make up dvm-dos-tem: the "Calibration Version" and the 
"Extrapolation Version". The Calibration Version is used to adjust parameters. The
Extrapolation Version is used to make projections or other simulations.

Both the Calibration Version and Extrapolation Version rely on the same underlying C++ 
code, but each version "drives" the code differently. It might be helpful to think of 
the Calibration and Extrapolation Versions as providing different interfaces to the 
underlying calculator.

The code for the Extrapolation Version is not separated from the underlying calculator - 
all the code is within the `src/` directory. The Calibration Version (interface) is 
written is Java. This code is contained within the `calibration/` directory. The 
Calibration Version points to C++ code in the `src/` directory in order to compile.

Downloading
-------------
There are several options for downloading or obtaining the model depending on your 
particular usecase. Dvm-dos-tem is not distributed as a binary file, so to run the 
program, you must compile from source code. 

* If you anticipate contributing to the code, you should use github to create
your own fork and then git to "clone" the code.
* How to: ...download version, keep up to date with sel version...
* How to: ...download specific commit, no need to contribute or keep up to date...

Requirements / Dependencies
---------------------------
The following tools/libraries are necessary in order to build and run dvm-dos-tem

* Boost, including [Boost.Program_options](http://www.boost.org/doc/libs/1_53_0/doc/html/program_options.html)
* NetCDF, v4.1.3 or less. [NetCDF/Unidata](http://www.unidata.ucar.edu/software/netcdf/)
* Java Development Kit (JDK) v??


Compiling / Building
-----------------------
This project requires a version of NetCDF and Boost's program options to be installed on 
your path. Assuming both of those exist, this should work to compile:

    $ make

or 

    $ make dvm
    
There are some helpful scripts provided in the `env-setup-scripts/` folder that will set 
a few environment variables for you for specific systems. For instance on aeshna, the 
correct version of NetCDF is not provided as a system package, but the user tobey has
made it available so that you don't have to compile it yourself. You must set an
environment variable so that when you compile and run it will look in tobey's directory 
for the NetCDF library files.

You can either remember to run the setup commands/script each time you logon to the 
computer where are you are interacting with the model or add a line to your ~/.bashrc 
or ~/.bash_profile that "sources" the setup script. This makes sure the setup commands
are run each time you log on. 
E.g.

    $ vim ~/.bash_profile
    # Add a line like this at the end:
    source /path/to/your/dvm-dos-tem/env-setup-scripts/setup-env-for-aeshna.sh
    
If you are successful getting dvm-dos-tem to compile and run on a different system
it would be appreciated if you submit the appropriate setup commands so that other's
don't have to spend time figuring out those details.

Running
---------
The program is partially controlled by a set of command line options. The `--help`
provides some info and shows the defaults:

    $ ./DVMDOSTEM --help
      -m [ --mode ] arg (=siterun)          change mode between siterun and regnrun
      -f [ --control-file ] arg (=config/controlfile_site.txt)
                                            choose a control file to use
      -c [ --cohort-id ] arg (=1)           choose a specific cohort to run
      -s [ --space-time-config ] arg        choose spatial or temporal running mode
      -h [ --help ]                         produces helps message
      -v [ --version ]                      show the version information
      -d [ --debug ]                        enable debug mode

The DATA/ directory of this project contains some sample data for single site runs and 
some multi-site runs (multiple grid cells or cohorts). To use the default values, simply
run the program like this:

    $ ./DVMDOSTEM


Developing
-----------
This project is maintained using Git (an open source distributed version control system) 
and github (a web service that provides hosting for code projects and has tools and idioms
for collaborative working on code-related projects).

This project is maintained using the "Fork and Pull" workflow. Following are several 
common use-cases:

* To simply download and use a certain version of the software, no special tools or 
programs are necessary.
    
    Navigate to the project's "Code" view on github, select the branch or tag of the code
    to get and use the download link.

* If you plan to make changes to the source code that should be incorporated into the 
Spatial Ecology Lab's main repository, then you will need the program Git on your
computer. 

Git is, at heart, a command line tool, but there are numerous graphic front-ends (GUIs)
available for Mac, Windows and Linux. If you are using SEL's aeshna cluster, Git is 
already installed along with two helpful graphical tools, gitk and git-gui. There are 
Git plugins for many other software development tools as well (e.g. Eclipse). Using the
graphical tools may be easier if you have a basic familiarity with using Git from the
command line.

Here are two resources for getting and installing git on your computer:

* Github, how to setup Git <https://help.github.com/articles/set-up-git>
* Git Book, installing git <http://git-scm.com/book/en/Getting-Started-Installing-Git>

In general, the Git Book <http://git-scm.com/book/en/> is a good reference.

Then you will need to follow the ideas described here to be able to keep your code
up-to-date and to be able to contribute changes: <https://help.github.com/articles/fork-a-repo>.

After installing git on your computer and downloading the source code, here are a number 
of settings, configurations, and "tweaks" that may be helpful for working with Git and 
github.

* Maybe start with this (Git Book again): <http://git-scm.com/book/en/Customizing-Git-Git-Configuration>.
    
    The settings concerning pager, external editors, and color are particularly useful.

* Install and use gitk and git-gui (These come default with most installations of Git).
    
    * Gitk is a history viewer
    * Git Gui allows you to add changes and commit them to the repository.

* It is helpful if the prompt in your terminal program displays which branch you currently
have checked out when you enter a directory with a git repository. To do this, you add a
function to your `.bashrc` file. The `.bashrc` file is a setting file that is present in
every user's home directory on most Linux like computers. The '.' in the file name makes
the file "hidden"; use `ls -a` to see the file. If it is not present in your directory,
you can create it. Add this to your `.bashrc` file:

        # function to find the current git branch
        function parse_git_branch {
            git branch --no-color 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/[\1] /'
        }
        
        # use parse_git_branch to add the git branch to your terminal prompt
        PS1=$PS1: $(parse_git_branch)

**NOTE:** You have to remember to reload the `.bashrc` file, either by closing and
re-opening your terminal window, or typing:

    $ source ~/.bashrc

### Branching Model

### Workflow

For starters we will try the "integration manager" workflow. This is what is described
[here](https://help.github.com/articles/fork-a-repo). This means that to get started you
should first "fork" the project from the github.com/ua-snap/dvm-dos-tem.git repository. 
This will give you your own dvm-dos-tem repository in your own github account 
(github.com/YOU/dvm-dos-tem.git). Next you will "clone" from your account to your own 
machine (where ever you perform your coding work). Finally when you have made changes on 
your own working machine you will "push" those changes back to _your_ fork. If you would 
like the changes you made to be incorporated into the shared project
(github.com/ua-snap/dvm-dos-tem.git), then issue a "pull request" from your github 
account.

Documentation
-------------
There is a Doxygen file (Doxyfile) included with this project. The current settings are
for the Doxygen output to be generated in the docs/dvm-dos-tem/ directory.

The file is setup to build a very comprehensive set of documents, including as many 
diagrams as possible (call graphs, dependency diagrams, etc). To build the diagrams, 
Doxygen requires a few extra packages, such as the dot package. This is not available on 
aeshna, so running Doxygen on aeshna will produce a bunch of errors.



Tutorial for working with DVM-DOS-TEM
=====================================
DVM-DOS-TEM is not distributed as a binary executable. This means that to run the program, 
you must download the source code and compile the software. In addition, many of the 
settings you may want to modify for running DVM-DOS-TEM require re-compiling the code. 
This makes the distinction between "user" and "developer" a bit blurry. For this reason it
is important that everyone learn how to interact with DVM-DOS-TEM as a developer, even if 
you do not intend to make a [public] modification to the codebase for quite a while.

The process of developing the DVM-DOS-TEM software involves managing the contributions 
from all the members of the Spatial Ecology Lab. To improve overall efficiency and 
productivity of the Lab, it is important that everyone contribute to the same codebase. 
Over time this will significantly reduce the amount of redundant work that everyone does 
to perform their research. Contributions to the codebase can be to the scientific aspects 
of the model, or simply the improving the documentation or structure of the codebase so 
that it is easier to work with. This tutorial will take you through the process of making 
a small contribution to the documentation. At the end you will have made a meaningful 
addition to the the DVM-DOS-TEM codebase and will be prepared to contribute more in the 
future. You will know how to keep your copy of the software (source code) up to date with
the "upstream" (Spatial Ecology Lab) copy of the software.

While the actual steps of this tutorial might only take an hour or so to complete, 
depending on your background with Linux and git, you might expect to spend several days 
working through the entire exercise as you explore some topics in more detail.

Setting up your computing environment
-------------------------------------
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
virtualization software. Virtual Box is free and highly recommended.

Next choose a Linux distribution to use and install as a "guest" system within your 
virtualization software. Fedora is a recommended distribution.

Alternatively, install the Linux distribution of your choice on a dedicated host computer.

Become familiar with the basics of operating your new Linux computer via the command line 
(Terminal). 

Take some time to familiarize yourself with:
* the difference between realtive paths and absolute paths
* hidden files, and a user's "dotfiles" to store personal settings (i.e. .bashrc)
* the concepts of "users" in a Linux environment, and what the distinciton is between a 
normal user and the "root" user

* how command line help is typically presented (i.e. a general prompt followed by a 
command) 
* how to use the man pages to find out more about different Linux commands.

Take some time to learn about the "package manager" and how to install and update  
software on your new Linux computer.

> TODO: add some nice ref. material


Getting familiar with Git, Github, and SEL's use of these tools 
---------------------------------------------------------------
Managing contributions from a wide group of people to a single codebase is a difficult 
task. To help this, we use a version control system (VCS) called "Git". Git is absolutely 
fundamental to the process of working with DVM-DOS-TEM. You must understand the basics of 
this tool. We are hosting the DVM-DOS-TEM codebase with a service called Github. You must 
understand the difference between Git and Github. 

It is important to learn the fundamentals of Git for personal development before you can 
contribute to a group repository. Take a couple hours to read through the first few 
chapters of the "Git Book". Perhaps make some simple repositories so you can test the 
operations.

Read the following articles to become acquainted with Git:
> TODO: find links to some good basic git info...
> TODO: find somethign about branching models...
> TODO: find basic info describing integration manager/director/lieutenants
> TODO: find good description about difference between git and github.
> TODO: something about markdown, and why we use markdown in this file...
> TODO: add something about why it is important to keep personal / platform specific / 
> absolute paths out of the codebase...

Once you have some basic familiarity with Git and Github, you should understand how and 
why you must follow these procedures to get your copy of DVM-DOS-TEM.

Following this procedure will allow you to:
* stay up to date with other developments that happen to the codebase
* add your own contribution to the codebase
* keep the codebase on different computers that you use and keep each computer up to date
with the other computers and the main SEL codebase.

So with that out of the way, lets get going.

* You need to create a (free) account with github.
* You need to ask the administrator of the SEL gitbub account to add you to the SEL 
workgroup so that you can view the repositories.

Now sign into Github. Spend some time familiarizing yourself with the interface.

If you have been added to the SEL Github team, you should be able to see a variety of SEL
owned repositories in your github account. Pay particular attention to which repository 
you are viewing in the github account (i.e. yours, vs the SEL "fork" of the code). Pay 
attention to the URL in the address bar of your browser - it is usually quite clear and a
good indication of what you are looking at.

Actually getting a copy of DVM-DOS-TEM
----------------------------------------
First, find the sel-help repository on github and look for the "github-flowchart" PDF
files.

Read these documents and decide the way in which you will plan on interacting with the 
code.

The remainder of this tutorial will take you through actually contributing to the source 
code (well actually the documentation), so make sure you find and understand that path 
through the flow chart.

DVM-DOS-TEM is using the "integration manager" workflow. This is also sometimes refered 
to as the "Fork and Pull" model. 

> TODO: find link to description of fork/pull and or integration manager.

If you have not done so already, create your own "fork" of the codebase. This operation 
happens on Github. The result is that your Github account now contains a copy of the 
DVM-DOS-TEM codebase. You should be able to identify this based on several cues in the 
github web interface, not the least of which is the URL in your browser's address bar.

Next, you need to get a copy of the code onto your local computer where you plan to work.
(likely your new virtual machine, but this could also be a dedicated Linux computer, or
perhaps your account one of the UAF cluster computers (aeshna, or atlas).

* Navigate to a location on your Linux computer where you would like to store the model.
* On Github, navigate to your fork of the model.
* On Github, find the clone address for the code. Either the HTTP, or SSH address will 
work, but in the long run, it will be worth your while to make the ssh work. This can be 
done later. For now, choose one of the methods...
* copy the clone address from github and issue the cloning command on your Linux computer.
This will create a directory named "dvm-dos-tem" and will grab all the information from 
Github (all the source code, all the history, some sample data, and a good chunk of 
documentation) to your Linux computer. Because we bundle some sample test data with 
DVM-DOS-TEM, this is actually a fairly large download, so it might take a few seconds.

Congratulations, now you have DVM-DOS-TEM on your computer! Now it is time to make a 
change and submit that change back to the "upstream" codebase for inclusion there.

> NOTE: The upstream repository refers to the main, Spatial Ecology Lab repository. Your
> goal with this tutorial is to make modifications in your codebase and then request that 
> your changes are included in the upstream repository. An additional goal is to keep your 
> repository up to date with the upstream repository, so that you have the most recent 
> modifications that anyone else has made.

Making a modification...
-------------------------
For this tutorial, you will be making a small modification to improve the documentation of 
DVM-DOS-TEM.

> TODO: add notes on setting up your personal computing environment for working with git. 
> Specifically:
> * adding to your bashrc file to add the current git branch to your prompt
> * helpful git config settings, (like adding color)
> * gitk, and git gui

First, notice that you are on the master branch. For the SEL maintained dvm-dos-tem, we 
follow a specific "branching model" (TODO: add link to branching model section...) which 
helps keep an clear understandable history for the project. The branching model gives 
specific semantic value to differnet points in the history tree.

Acoording to the branching model, the `master` branch might not have the most recent code.
We would like our modification to be based off the `devel` branch, and eventually to be
pulled into the SEL repository's `devel` branch.

> NOTE: might be good to add some details about git, remotes, origin, and upstream...

> TODO: add remote "upstream" to point toward github/ua-snap/dvm-dos-tem?

> TODO: add some history about why sel's code is stored at github/ua-snap account...

To do this, first checkout a local `devel` branch which is based off your fork's `devel`
branch.

    $ git checkout --track remotes/origin/devel
    
Now you have, locally, all the most recent code from your fork's `devel` branch. Next you
need to make a change that you wish to be included in the upstream repo.

Although not strictly necessary, we will further isolate this change in a topic branch.
For a small modifications, such as the typo we are going to fix, this is a bit of extra 
complexity, but for a larger changeset, such as a new feature, or addition of a new 
scientific concept, using a separate topic branch is important.

    $ git checkout -b improve-docs

Finally, we are ready to get down to work. Read the documentation (this file, the main 
README.md, or comments in the code itself) and find an error in the documentation. This 
should be easy! Your error can be as small as a typo, or as large as a paragraph that you 
re-work or decide needs to be added or deleted.

Make the modification using the text editor of your choice.

Ok, you should have changed the file. Use Git to see if you can get a concise summary of 
the changes you made (using git diff, or Git Gui).

Now you need to commit your change. You can use Git Gui for this or the command line: 

    $ git add <path/to/the/file/you/just/changed>
    $ git commit -m "Update documentation; my first contribution to dvm-dos-tem"
    
Now the modifacation you have made is a part of your local history. Next steps are to: 
a) make sure you are up to date with all the developments that have happened in the 
upstream repository, 
b) push your changes up to your fork, 
c) request that your awesome modification is incorporated to the upstream version

> TODO: add some discussion about why you need to make sure you are up to date with 
> the upstream repo (merging locally, handling merge conflicts locally)

So to start, make sure you are up to date with the upstream repo, probably the devel 
branch:

    $ git fetch upstream/devel
    $ git merge upstream/devel
    
    
Now if there are any merge conflicts, you will need to fix them. This is pretty
unlikely, but possible. It would only occur if someone else had changed the same lines of
the same file as you since you checked it out. In that case, you would have to decide
whose modification to accept - this process is known as resolving merge conflicts.

After you have addressed (and fixed locally) any conflicts, it is time to push your 
changes up to your fork on github.

    $ git push origin improve-docs
    
Now if you go back to the git hub web site, you should be able to view your modification. 
Try the "Network View" to see this. You should see a new commit dot with your changes
labeled on your fork as `improve-docs`.

Requesting that your modification be included in the upstream
-------------------------------------------------------------
Ok, finally, you are ready to have your modification incorporated into the upstream 
codebase. On the github interface, find the button for "pull request". Make sure that you 
have the settings correct. You want to pull the new branch you just created, 
`improve-docs`, into the upstream/devel branch.

> TODO: add link to this awesome tutorial: http://pcottle.github.io/learnGitBranching/




Branching Model
-----------------
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


Now you need to follow the Git workflow you should have learned about earlier in the 
tutorial to commit the change.














Wrapup
-------------
Congratulations. Now you are almost a software developer and are ready to start working 
with DVM-DOS-TEM.
You should now understand:
* the basics of setting up a computing environment for use with DVM-DOS-TEM
* the difference between Git and Github
* why we are using Git and Github
* why it is important to follow this procedure for getting DVM-DOS-TEM 
* how to get a copy of DVM-DOS-TEM
* the basic workflow for making a modification to DVM-DOS-TEM and submitting it for 
inclusion "upstream"
* how to keep your codebase up to date with the modifications that are happening in the 
"upstream" repository





> TODO: this is not quite right - I think first you actually want to checkout devel...
> then make a topic branch off devel. Then you will request that your mod get pulled into
> the devel branch...   if it is, then there will be a merge commit " merge pull req. xx
> "improve docs" into devel. Then you the upstream will have a commit on devel that you
> don't have...so then you will need to update your devel from upstream??

