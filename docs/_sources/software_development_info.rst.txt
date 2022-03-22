
.. # with overline, for parts
   * with overline, for chapters
   =, for sections
   -, for subsections
   ^, for subsubsections
   ", for paragraphs


#########################
Software Development Info
#########################
    WRITE THIS...

******************************
Languages, Software Structure
******************************
    WRITE THIS

    Core is C++, utils python,Tutorial are ipynb, shell scripts for some utils, make, etc
    Write this section...

*************
Documentation
*************
    WRITE THIS... 

==================
Note about images
==================
    WRITE THIS....

------------------------------
Considerations for new system
------------------------------
    WRITE THIS...

=========================
Note about this document
=========================

*****************************
Software Development Patterns
*****************************
    WRITE THIS...

=============================================
Read Eval Print Loop (REPL, shell, terminal)
=============================================
    WRITE THIS...

=============================================
GUI Application
=============================================
    WRITE THIS...

=============================================
Interpreted Program (script)
=============================================
    WRITE THIS...

=============================================
Compiled Program (binary)
=============================================
    WRITE THIS...

=============================================
Integrated Development Environment (IDE)
=============================================
    WRITE THIS...

=============================================
IPython
=============================================
    WRITE THIS...

=============================================
Basic IDE
=============================================
    WRITE THIS...

=============================================
Jupyter Notebook
=============================================
    WRITE THIS...

=============================================
Virtual Machine
=============================================
    WRITE THIS...

*****************************
Version Management
*****************************
The primary reasons for using a version management system for  ``dvmdostem`` are:

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
This project is using Git for version control and Github for hosting. The primary
fork of the code (referred to as “upstream”) is currently hosted under the ua-snap 
organization [#]_, so the primary (upstream) repository address is: 
https://github.com/ua-snap/dvm-dos-tem.

.. note::
   * The Source Control Management (SCM) or Version Control software is named ``git``.
   * ``git`` is really a general tool for managing a certain type of data structure 
     (Directed Acyclic Graph or DAG for the curious). As such, there are many ways it
     can be used correctly and it is up to each group to find a pattern that works 
     for the project.
   * Github is a website that uses git and provides web hosting as well as other 
     features such as access management, wikis, issue tracking, and support for 
     automated workflow and actions.

The dvmdostem code is open source and the repository is publicly available and can 
be cloned by any interested party. However write access to the upstream repository 
is only granted to trusted collaborators. We gladly accept contributions to the code
via pull request from anyone, but the pull request will have to be merged by a 
collaborator with write access to the upstream repo. See the branching and workflow 
sections below for more details.

.. [#] As of December 2021, this is true; we anticipate moving to a new 
       Github Organization in the next 6 months or so. 

--------------
Getting Help
--------------
General Git help is beyond the scope of this document. Here a few key concepts that
this document assumes you are familiar with:

* What is a commit.
* What is a SHA id.
* Difference between a fork and a clone.
* Difference between git push, pull, fetch, and pull request (PR).
* Difference between git branch, merge and rebase.

Here are several recommendations for general Git help:

* https://git-scm.com/book/en/v2
* https://www.atlassian.com/git
* http://sethrobertson.github.io/GitBestPractices


.. note::
   It is important to make commits that are concise, organized, and readable, 
   thus fulfilling the goals of using a version control system. This comes 
   down to using git on a day-to-day basis and learning:
  
   * what is a commit,
   * how to write a good commit message,
   * how to separate different concerns into different commits,
   * how to fine tune a commit (interactive rebase, amend and when 
     to use it),
   * understanding what types of files or information should not be kept 
   * under version control,
   * how to use branches,
   * how to merge branches, and
   * the implications of making merges in an environment with multiple 
     developers.

-------
Tools
-------
    WRITE THIS...

-------
Setup
-------
    WRITE THIS...


==================
Branching Model
==================
    WRITE THIS...

===========
Workflow
===========
    WRITE THIS...

=================================
Releases and Version Management
=================================
    WRITE THIS...


==================================
Automated Testing and Deployment
==================================
    WRITE THIS...

*******************************
Setting up a dev environment
*******************************
    WRITE THIS...

===============================
Setting up with Vagrant
===============================
    WRITE THIS...

===============================
Setting up with Docker
===============================
    WRITE THIS...

===============================
Setting up with Ubuntu
===============================
    WRITE THIS...


