
.. # with overline, for parts
   * with overline, for chapters
   =, for sections
   -, for subsections
   ^, for subsubsections
   ", for paragraphs


########
Dev Info
########

This chapter should include all the useful information that you will need to
make contributions to the ``dvmdostem`` project.

.. important:: 

  In order to keep the base repository size from growing out of control, the
  testing and sample data is tracked using `Git LFS <https://git-lfs.com>`_. If
  you need to use the testing data (i.e. to run the tests, or to build the
  documentation from source) then you should install Git LFS and run ``git lfs
  pull`` to make sure that the actual data is downloaded.

******************************
Languages, Software Structure
******************************

The core model (``dvmdostem``) is written in C++, while most of the supporting
tooling is written in Python. There are also an assortment of bash scripts, R
code, and IPython Notebooks floating around for various tasks.

The core code is compiled with a basic Makefile. This documentation is written 
in reStrutured Text and Sphinx and is also compiled with a Makefile.

***************************
Coding Conventions
***************************

Table? List? Subsections?

Here are some first things off the top of my head.

  * Indent with spaces, use 2 spaces for the tab width.
  * Aim for lines to be <80 chars long,
  * For Python write docstrings in ``numpydoc`` (Link?) format.
  * For C++ write comments in Doxygen format.
  * Favor verbose descriptive variable names.

For documentation (``*.rst`` and ``*.md`` files, ``docstring`` s, etc), please
hard wrap lines at 80 charachters before comitting. Many text editors have
settings or extensions that can help with this tedium. With VSCode, try the
Rewrap extension. For Sublime, try "Select -> Edit -> Wrap".

*************
Documentation
*************

There are several places that you will find information about ``dvmdostem``,
each with a different type of info:

 * README file(s) - overviews of a repository or project. Used as a rough 
   introduction, installation instructions and links to other resources.
 * This document (which is the formatted output of the ``.rst`` source files).
   The document is split into several chapters:

    - :ref:`"Model Overview"<model_overview:Structure>` - narrative, scientific
      description of the ``dvmdostem`` model.
    - :ref:`"Running"<Running_dvmdostem:Practical>`- info and examples for hands
      on use of the model.
    - :ref:`"Dev Info"<software_development_info:Documentation>` - (this
      chapter) which contains all the other programming, usage and workflow
      information for hands on work with the model.
    - Several other chapters, available in the table of contents.

   It is likely that you are reading this document where it has been published 
   online; if you build the documentation locally, then by default, the output
   ends up in ``docs_src/sphinx/build/html``.
 * Doxygen output. Similar to Sphinx, Doxygen is a documentation processing tool
   that scans source files and can create a variety of output formats. Doxygen
   for this project is configured to analyze the C++ source files and generate
   an interactive html page with detailed call graphs and text parsed from the
   C++ files.
 * The ``--help`` flag for ``dvmdostem`` and many of the scripts in the
   ``scripts/`` directory. This info is generally specific usage information for
   the given tool.
 * Comments in the code are helpful for implementation details.
 * Github wiki (hopefully deprecated soon). This may end up being a home for 
   assorted tutorials and examples.

In a perfect world most of the comments in the code will eventually be 
formatted in such a way that they can be picked up by tools such as Doxygen 
(for C++) and Sphinx (for Python). But because that is a work in progress it is
still helpful to browse the code especially for implementation details about 
the code.

We used the Github Wiki for several years, but we are trying to move away 
from it towards a more robust, fully featured platform that integrates better 
with CI/CD tooling. Github Wiki might be a good place to keep certain 
tutorial-like information.

To build the Sphinx documentation (this document) locally, then do the following:

.. code:: shell

    $ cd docs_src/sphinx
    $ make clean && make html

.. warning::

    Note that we need to set the ``PYTHONPATH`` in order for the ``qcal.py`` to
    be imported and documented during this build process. Not sure the best way
    /place to set this yet, so showing an example here:

    .. code:: shell

      $ make clean
      $ PYTHONPATH="/work:/work/calibration:$PYTHONPATH" make html


The resulting files are in the ``docs_src/sphinx/build/html`` directory and can
be viewed locally with a web browser.

To build the Doxygen documentation locally, then do the following:

.. code:: shell

    $ cd docs_src/doxygen
    $ doxygen

The resulting files are in the ``docs_src/doxygen/doxygen_build`` directory and 
can be viewed locally with a web browser.

=====================================
Preview -> Editing -> Contributing
=====================================

Previewing
-----------

Here are the steps to preview documentation changes (perhaps made by someone
else) in your local environment. Assuming you have a development environment, a
cloned copy of the repo, and a "clean" working state:

 1. Checkout the branch you are interested in previewing. For example someone
    else has pushed to the ``upstream/<BRANCH-NAME>`` branch and you'd like to
    see what they have written or how it all looks: ``$ git remote update && git
    checkout <BRANCH-NAME>``.
  
 2. Clean the existing docs and build them: ``$ cd docs_src/sphinx && make clean
    && make html``

 3. Preview the results in your browser
    (``file:///path/to/your/repo/docs_src/sphinx/build/html``).

.. note:: 

  It is generally easiest to run the documentation build using the
  ``dvmdostem-dev`` Docker container so that the build environment (Sphinx
  version, etc) match the environment used to publish.


Editing
---------

The writing and editing process for the docuemtation ends up looking essentially
like the general coding or programing process:

 1. setup a development environment of your choice
 2. clone the repository to your development environment
 3. checkout a new or existing topic branc to work on
 4. edit the source files (``docs_src/sphinx/*.rst``)
 5. process the ``.rst`` files: ``cd docs_src/sphinx && make clean && make html``
 6. preview the results in your browser
 7. (``file:///path/to/your/repo/docs_src/sphinx/build/html``)
 8. commit your changes

For more details about the coding process see the `Workflow`_ section.


Contributing
------------

If you would like to contribute your edits use a Pull Request. 

To make a Pull Request, you must push your commits to Github (either your fork)
or the ``uaf-arctic-eco-modeling/dvm-dos-tem``, depending on your choice of
workflow and your status as a collaborator.

==============
Publishing
==============

Publishing (updating the live website at github.io) is reserved for the
maintainers, ``tcarman2`` and ``rarutter``.

In the current implementation with Sphinx (used to format this document), we
have a ``docs_src`` folder within which is a subdirectory for each documentation
tool (presently Doxygen and Sphinx). Each tool is setup to put its outputs in
its own directory. To publish outputs, the contents are copied to the ``docs/``
directory in the root of the repo and then pushed to the ``gh-pages`` branch of
the upstream repo. Pushing to the ``gh-pages`` branch leverages the free
publishing available from Github and is a simple way to make the documentation
publicly available. See the ``publish_github_pages.sh`` for more details.
Automated publishing (e.g. for each release) is still a work in progress. 

Currently the Sphinx documentation is designed to be published to Github
Pagesand the Doxygen documentation is only intended for local use.

==================
Note about images
==================

Including images in documentation presents similar challenges for raw, 
rendered, and word processing systems. One choice is whether to embed the 
image directly or provide a link to it. And another choice has to do with how 
to version control the image and make it easy to update in the future.

The simplest solution is to simply not worry about it and commit the ``.png`` 
or ``.jpg`` files directly to the repo. This certainly works, but imagine a 
scenario where you need to update the image, say to fix a typo. If you were
the original creator, then you open the drawing file (e.g. Photoshop, Visio, 
Open Office Draw; whatever you used to create the image) edit the image, 
export it, move it into the documentation structure, overwriting the original, 
and commit the result to version control. This assumes that you have the 
original image. If you don’t (either because you lost it, or perhaps you were 
not the original creator, then you must completely redraw the image from 
scratch, which is ridiculous in many cases.

One way to solve this is to commit the original image file to version 
control (e.g. the ``.ps`` or ``.dwg`` file) alongside the exported image that
will be included in the documentation. This is essentially the same dilemma 
as with the raw → generated text documentation. However drawing files 
typically don’t read well with file diffs, so it is hard to tell what changed
with the images, making it important to have good commit messages and keep 
the exported files as well. And keeping all these binary files uses quite a 
bit more space than plain text files, so it is easy for the size of the 
repository to get out of control.

A novel solution that we discovered for this problem is to use linked 
Google Drawing documents roughly as follows:

 #. Make a Google Drawing and save it (with a name)
 #. Click the Share button
 #. Edit the preferences so that the drawing is viewable to anybody with 
    the link
 #. Under File menu select "Publish to Web"
 #. Select "Embed"
 #. Copy the embed link 
 #. Paste the link into the appropriate place in your document

For each type of document there might be a different way to render the link, 
and this may not be possible in all languages/environments. In the Github 
wiki, which uses, Markdown, including something like this will allow the 
image to render, directly from Google Docs when someone loads the page:

.. code:: html

   <!-- From Tobey Carman's google drawing "dvmdostem-general-idea-science"-->
   <img src="https://docs.google.com/drawings/d/17AWgyjGv3fWRLhEPX7ayJKSZt3AXcBILXN2S-FGQHeY/pub?w=960&amp;h=720">

If the original Google Drawing is updated, then the drawing seen in the wiki 
will be updated too. Take caution with the permissions granted for editing 
on the original drawing!

.. warning::

   When you are editing an image that is embedded, the edits are automatically
   live on the published website! This is fine for quick edits such as fixing a
   typo, but for anything more substantial, it is reccomended that you make a
   duplicate of the Google Drawing, edit the duplicate and then copy it back
   over the original. This will keep your edits from showing up on the live site
   until you are done with them!

.. warning:: 
   
   Soure drawings for this document should probably be stored in the 
   Shared Google Drive so that they are not tied to an individual's account.

In Google Docs, there is a way to insert a Google Drawing from a menu: 
Insert > Drawing > From Drive.

With Sphinx, use the ``:raw:: html`` directive. The Sphinx documentation warns
against abusing the ``:raw::`` directive, so this might not be a good long 
term solution but it could be useful for creating a bunch of the drawings 
while they are in draft stages. 

We have not tested this approach with a system such as Doxygen but assume it 
should work. This solution is not perfect, downsides include:

 * Drawing is not strictly version controlled along with other content 
   (Google Drawings offers some version control but this would not be 
   linked to the ``dvmdostem`` git repository).
 * The end user must have web connectivity to see the drawings.


*****************************
Version Management
*****************************
The primary reasons for using a version management system for  ``dvmdostem`` 
are:

 * To maintain a meaningful history of the codebase so that the provenance
   of the code is not in question.
 * To facilitate the addition or modification of code by many developers.
 * To maintain the ability to revert to or recover specific points in the 
   history of the codebase. This may be for the purpose of duplicating prior
   work, or to recover a lost behavior of the software, or both.

There are two (related) parts to fulfilling the above goals:

 * Making the commits (file diffs) easy to read and understand.
 * Having a strategy or pattern for bringing different lines of development
   together.

If the file diffs are unreadable or the lines of development are not brought 
together in an organized fashion, then the project history is harder to trust
which brings into question the provenance of the code, and makes it harder for
people to contribute.

===========================
Version Control and Hosting
===========================
This project is using Git for version control and Github for hosting. The
primary fork of the code (referred to as “upstream”) is currently hosted under
the uaf-arctic-eco-modeling organization, so the primary (upstream)
repository address is: https://uaf-arctic-eco-modeling.github.io/dvm-dos-tem.

.. note::
   * The Source Control Management (SCM) or Version Control software is 
     named ``git``.
   * ``git`` is really a general tool for managing a certain type of data 
     structure (Directed Acyclic Graph or DAG for the curious). As such, there 
     are many ways it can be used correctly and it is up to each group to find
     a pattern that works for the project.
   * Github is a website that uses git and provides web hosting as well as other 
     features such as access management, wikis, issue tracking, and support for 
     automated workflow and actions.

The ``dvmdostem`` code is open source and the repository is publicly available 
and can be cloned by any interested party. However write access to the 
upstream repository is only granted to trusted collaborators. We gladly 
accept contributions to the code via pull request from anyone, but the pull 
request will have to be merged by a collaborator with write access to the 
upstream repo. See the branching and workflow sections below for more details.
 


==================
Branching Model
==================

A generalized view of our branching model can be seen in the diagram:

.. raw:: html

    <!--From Google Drawing in
    Shared Drive > DVM-DOS-TEM Documentation > drawings > branching_model
    -->
    <img src="https://docs.google.com/drawings/d/e/2PACX-1vRnnwNqLaMeWfcvUPI1BK47KVBAYJSGnOWoD_0fqoBwx27oRM1idQvZ0sS1Yaebr6bl7AcmNB1oAAjw/pub?w=960&amp;h=720">

The image shows one long-running branch (red commits; ``master``), three topic
branches (green commits; ``issue-47``, ``modify-dvm``, and ``bugfix-4``) and
three “experiment branches'' (gray commits; ``exp-iem-0``, ``exp-akyrb-0``,
``exp-QCF-SA``). 

Two of the topic branches have been merged (blue arrows). One of the topic
branches (``modify-dvm``) will be merged in the future (dotted blue arrow). The
dark red commits on the master branch have been tagged to make an official
release of the code. The gray commits are for “experiment branches” which are
used to track a specific model run or set of model runs. Often the changes on
these branches are only to config and parameter files, but some experiments
might require code changes as well.

This diagram does not explicitly show interaction between multiple developers;
assume that each commit in the drawing could be made by any of the trusted
collaborators with push access to the upstream repository.

As a basic safety feature we have placed a restriction on the master branch of
the upstream repository such that only the administrators (tcarman2@alaska.edu
and rarutter@alaska.edu ) are allowed push access. This restriction makes it
unlikely that a trusted collaborator can accidentally push something that breaks
the master branch. The best way for trusted collaborators to get code into the
``upstream/master`` is to open a pull request from their topic branch (e.g.
``upstream/topic-foo-bar``) into ``upstream/master`` using the Github web
interface for pull requests. All interested parties then have an opportunity to
review the code, comment on Github, and push new commits to the topic branch (if
necessary). Only the administrators can merge the pull request. 

As a general practice we try to have most work done in topic branches and merged
into master using Github pull requests. For some small changes (usually for
details that were inadvertently excluded from a recent pull request) we will
make commits directly on the master branch without using the topic branch/pull
request process. Using the topic branch/pull request process helps to organize
work and will provide a convenient place to run Github Actions, for example an
action to run the test suite before green-lighting a pull request for merging.

Recently (2022 and the several years prior) we have been using a single
long-running branch (``master``) and have been able to manage all contributions
by periodically merging topic branches. If the need arises we can switch back to
using an additional long-running branch. This would allow different levels of
stability as described in the `Git Book Branching Workflows
section <https://git-scm.com/book/en/v2/Git-Branching-Branching-Workflows>`_.

In the event that you need work from ``upstream/master`` in order to continue
the work on your topic branch, you can periodically merge ``upstream/master``
into your topic branch. However please only use this when absolutely necessary
as it can make the history harder to read and the pull requests harder to
review. See this :ref:`Note <merge or rebase>` for a description of one
potential problem with merges.

.. _merge or rebase:
.. note:: 
    One problem with casually using merges in a workflow as opposed to using
    rebase is that the default merge messages can: 

     * Clutter the history.
     * Be very confusing if you end up changing a branch name at a later date.

    For instance if you have a long-running branch with a large feature you are
    working on and you need to get updates from upstream, if you choose to merge
    into your "long-running-branch": 

    .. code:: shell
        
        $ git checkout long-running-branch
        (long-running-branch)$ git pull upstream master

    Then you will get a merge message by default that starts with something like this:

    .. code:: shell

        Merge branch 'master' from github.com:uaf-arctic-eco-modeling/dvm-dos-tem into 'long-running-branch'

    All well and good, but later, once you work has evolved, you may decide to
    change the name of long-running-branch to something more relevant:

    .. code:: shell
        
        (long-running-branch)$ git checkout -b more-descriptive-name
        (more-descriptive-name)$ git branch -D long-running-branch

    While renaming the branch is not a problem in and of itself, the merge commit
    title will contain "...into 'long-running-branch'". The long- running-branch no
    longer exists! So the merge commit message will be confusing to anyone who was
    not involved with long-running-branch or forgot about it. Without good commit
    messages, it is harder to understand the history and without a good
    understanding of the history it is easy to lose control of the project. So
    please learn to use rebase and merge appropriately!


===========
Workflow
===========

We are primarily using the “Centralized Workflow” described in the Git Book
`Distributed Workflows
<https://git-scm.com/book/en/v2/Distributed-Git-Distributed-Workflows>`_. We have
a number of trusted developers at collaborating institutions and we grant them
write (push) access to the upstream repository. With this model, each developer
can push directly from their local repository to the upstream repository -
developers do not need to maintain their personal forks on Github (but are free
to do so if they wish).

If you are not one of our trusted collaborators and have contributions to make,
then you will need to follow the Git Book “Integration Manager Workflow”. You
will simply fork the upstream repository on Github, clone to your computer and
push changes back to your fork. You can then make a pull request from your fork
into the ``upstream/master``.

When two or more developers want or need to work contemporaneously on a topic
branch, it is up to the developers to communicate and make sure that they do not
step on each other's toes. In practice this simply amounts to communicating with
other folks via email, the `Arctic Eco Modeling Slack`_, or `Github Issues`_ and
remembering to run ``git pull --rebase``. Using ``--rebase`` prevents
unnecessary merge commits that can make the history confusing and harder to
trust. 

.. _What not to track:
.. note::
    A big part of maintaining a low friction workflow revolves around
    understanding what types of files or information should not be included in
    version control and figuring out how to exclude these files. The general
    idea is that you don't want to keep generated files (e.g.: ``*.o``, or
    Doxygen output), but you do want to track code that can generate certain
    outputs. If you need the outputs, then you run the generating code to
    produce it. The general rule is don’t track files that you can generate,
    track the code to generate them.


.. _Personal settings:
.. note::
    Another common sticking point is figuring out how to track host specific
    settings, such as specific environment variables, build settings, or the
    project settings files generated by many IDEs. You may need to devise your
    own way to track these settings locally on an individual developer or
    workstation level without pushing them to the central shared repository.


.. _git stash:
.. note::
    Learn to use ``git-stash``, it is very handy for setting aside work before 
    pulling or rebasing from upstream so as to prevent unnecessary merge 
    commits!


.. _git pull with rebase:
.. note:: 

    See the following helpful discussions:
     
     * https://stackoverflow.com/questions/13193787/why-would-i-want-to-do-git-rebase
     * https://blog.sourcetreeapp.com/2012/08/21/merge-or-rebase/


================================
Releases and Version Numbering
================================

Begining in 2021, we started using the "Releases" feature of Github to package
and distribute specific versions of ``dvmdostem``. We would like to make this a
fully or nearly fully automated process but for the time being it is rather
manual.

As described in the ``HOWTO_RELEASE.md`` document in the repo, the project uses
a three part version number: vMAJOR.MINOR.PATCH.

We use the following rules for incrementing the version number:
 * The PATCH number (farthest right) will be incremented for changes 
   that do not affect the general scientific concepts in the 
   software.
 * The MINOR number (middle) will be updated when changes have been made 
   to science concepts, major implementation changes for scienctifc aspects 
   of the code calibration numbers are updated, or large new features are added.
 * The MAJOR (left) number will be updated for major milestones. This will
   likely be points where the model is run for "production" or major testing and
   validation steps are completed and documented.

This project is not using traditional `Semantic Versioning`_, however we have
borrowed some concepts.

Until the project reaches ``v1.0.0``, we will not make any guarantees about
backwards compatibility. Once the project reaches ``v1.0.0``, we may decide to
handle the rules for incrementing version numbers differently.

Releases are currently made on an as-needed basis by tcarman2@alaska.edu or
rarutter@alaska.edu. 

The steps are described in the ``HOWTO_RELEASE.md`` document and the result is 
that release is visible here: https://github.com/uaf-arctic-eco-modeling/dvm-dos-tem/releases

================================================
Keeping your repo up to date with ``upstream``
================================================

See the :ref:`"Command Cheat Sheet"<staying_udpated>`.

.. note::

  A common developer issue is that you may have installed custom libraries that
  are not available yet inside the dvmdostem Docker image. When you shutdown
  your Docker containers, then any custom libraries you have installed will be
  lost. When you start your containers again, you will have to re-install these
  libraries. This can be somewhat tedious. One solution for this is that you
  keep a custom requirements file and ask pip to install packages from that when
  you start up your Docker containers. For example if you need the Python
  package ``BeautifulSoup``, and ``PyDemux`` (don't ask why) you might make a
  file in your repository ``requirements_custom.txt`` with the following lines:

  .. code::

    BeautifulSoup==4.8.1
    PyDemux=1.0

  And then when you start up your Docker container, you can run the following to
  install your custom pacakges:

  .. code::

    develop@263004fd19aa:/work$ pip install -r requirements_custom.txt

  Your ``requirements_custom.txt`` should not be tracked with Git. If you have
  further customizations beyond this there is likely a way to inject your
  specific environment needs into the Docker container using custom ``.bashrc``
  files or the docker compose ``.env`` file or some combination thereof.



.. note::

  A common issue that comes up when you have multiple branches that you are
  working on is that you checkout a different branch and try to run something in
  your docker container and it fails because a library is not installed. For
  example:

  .. code::

    docker compose exec dvmdostem-dev bokeh serve scripts/bk_timeslider.py --port 7001
    2023-02-09 23:16:41,834 Starting Bokeh server version 2.4.2 (running on Tornado 6.2)
    2023-02-09 23:16:41,835 User authentication hooks NOT provided (default user enabled)
    2023-02-09 23:16:41,838 Bokeh app running at: http://localhost:7001/bk_timeslider
    2023-02-09 23:16:41,838 Starting Bokeh server with process id: 5351
    2023-02-09 23:16:48,986 Error running application handler <bokeh.application.handlers.script.ScriptHandler object at 0x7fdd8517b910>: No module named 'xarray'
    File 'bk_timeslider.py', line 7, in <module>:
    import xarray as xr Traceback (most recent call last):
      File "/home/develop/.pyenv/versions/3.8.6/lib/python3.8/site-packages/bokeh/application/handlers/code_runner.py", line 231, in run
        exec(self._code, module.__dict__)
      File "/work/scripts/bk_timeslider.py", line 7, in <module>
        import xarray as xr
    ModuleNotFoundError: No module named 'xarray'

  This happens when one of the branches introduces a library requirement that is
  not yet in the upstream codebase. Ideally the library has been added to the
  requirements file, but this is an easy step to forget. If the library is in
  the requirements file, then all you usually need to do is ask pip to install
  everything again:

  .. code::

    develop@a2d3e3cb5a55:/work$ pip install --upgrade -r requirements_general_dev.txt

  If the offending library is not yet in the requirements file, then it is
  usually a good idea to add it and make a commit first. 

*******************************
Testing and Deployment
*******************************

There is currently (Sept 2022) a very limited set of tests and their execution
is not automated. It is a goal to increase the test coverage and automate the
test exectution in the near future. We are hoping to setup a CI/CD pipeline
using Github Actions that can automatically test and deploy the ``dvmdostem``
model and supporting tooling.

Testing is currently implemented for some of the Python scripts in the
``scripts/`` directory using the Python ``doctest`` module. The style and
structure of tests reflects the challenges we have had getting testing intgrated
into this project. The ``doctest`` module has a nice feature that allows tests
to be written in a literate fashion with much explanatory text. This allows us
to hit several goals with one set of testing material:
 
 - explanations and examples of code/script usage; 
 - testing across a wide range of encapsulation; for example some of the tests
   are very granular unit tests of single functions in the script files, while
   others test comprehensive behavior of entire modules and command line
   interfaces;
 - basic regression testing.

There are two primary places that the ``doctests`` will show up:
 
 #. In the ``__docstring__`` of a given Python script or function.
 #. In a standalone markdown (.md) or reStructuredText (.rst) file with
    specially formatted test code.

The tests that are in the docstrings of a given file or function should be very
narrow in their scope and should only check the functionality of that specific
function, independant from everything else, whereas tests in a standalone file
can be much broader and more flexible in their design - i.e. module level tests. 

At present we have had much more luck writing the broader tests (that also serve
as examples of usage) in stand alone files named with the following pattern:
``scripts/tests/doctests/doctests_*[.md | .rst]``. The files are markdown or
reStructuredText formatted with embedded code that is executed by the
``doctest`` module. The execution context and other ``doctest`` particulars are
described here:
https://docs.python.org/3/library/doctest.html#what-s-the-execution-context

To run the tests that are in ``__docstring__`` s of a function or file:

.. code:: shell

    $ PYTHONPATH="/work/scripts" python -m doctest scripts/util/param.py   # <-- script name!

To run the tests that are in an independent file:

.. code:: shell

    $ PYTHONPATH="/work/scripts" python -m doctest scripts/tests/doctests/doctests_param_util.md  # <-- test file name!

In either case, if all the tests execute successfully, then the command exits
silently. If there errors, the ``doctest`` package tries to point you towards
the tests that fail.

Note that in both cases, the ``PYTHONPATH`` variable is set so that the module
imports work properly in the scripts and tests. Many of the test currently use
the demo-data, config files and parameter files in the main repo. The paths for
these in the tests are assumed to be relative to the repo root. So you will
likely have the best luck running the tests from the repo-root. For this reason
you need to specify ``PYTHONPATH`` so that inside the test scripts, imports can
be made of scripts and tools in the scripts folder.

In order to run all the tests, this loop should work:

.. code:: shell

    for i in $(ls scripts/tests/doctests/);
    do
        PYTHONPATH="/work/scripts" python -m doctest scripts/tests/doctests/$i;
    done


*******************************
Setting up a dev environment
*******************************

There are many paths to setting up a development environment and the specific
path you choose will depend on your experience and needs. Over the years we have
tried all of the following:

 * Local installation.
 * Hand managed Virtual Box VM.
 * Vagrant managed VM.
 * Docker container stack.

The current (2022) preference is generally for the Docker container stack,
although on some systems a local installation is still preferable.

===============================
Setting up with Vagrant
===============================
    WRITE THIS...

===============================
Setting up with Docker
===============================
    WRITE THIS...
    Install docker desktop 
    Make sure you have docker and docker compose available on the command line
    Find a place on your computer for:
    Your dvmdostem repo
    Your catalog of inputs
    Your catalog of “workflows”


===============================
Setting up with Ubuntu
===============================
    WRITE THIS...


.. _Arctic Eco Modeling Slack: https://arctic-eco-modeling.slack.com
.. _Github Issues: https://github.com/uaf-arctic-eco-modeling/dvm-dos-tem/issues
.. _Semantic Versioning: https://semver.org

*********************
Debugging strategies
*********************

For problems with running `dvmdostem` itself, the first thing to do is generally
run with a higher log level. This is available as a command line flag with both
long and short forms (``--log-level``, ``-l``).

You will imediately notice that with the more verbose levels the amount of stuff
printed to your console will be overwhelming and likely saturate your scrollback
buffer, making it impossible to read messages from the beginning of the run,
which is where you usually want to look to diagnose initialization errors. One
trick to overcome this is to redirect the standard output (``stdout``, ``1``)
and standard error (``stderr``, ``2```) streams to a file which you can search
thru post-hoc using ``less`` or a text editor. For example:

.. code:: shell

    $ dvmdostem --log-level debug > MY_OUTPUT.txt 2>&1

Nothing will be output to your console and you should have a file that you 
can search through when the run is done. See the ``tee`` command if you want to 
see the output on your console as well as save it to a file.

