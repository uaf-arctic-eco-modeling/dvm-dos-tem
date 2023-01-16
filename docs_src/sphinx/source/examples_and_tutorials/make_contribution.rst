.. # with overline, for parts
   * with overline, for chapters
   =, for sections
   -, for subsections
   ^, for subsubsections
   ", for paragraphs

######################################
Contributing to the Codebase
######################################

This lab takes you through one possible workflow using Git and Github to make a
modification to the codebase and have it included upstream. This is a somewhat
simplified case and does not cover every situation you will run into. This is
also not a basic Git tutorial and it assumes that you already are familiar with:
 
 - Installing Git on your system. 
 - Working with the command line on your system.
 - Making commits using Git.
 - Browsing repositories on the Github website.
 - Viewing Git history, either with git log or a GUI program.
 - Rough understanding of the following git concepts: 
   commits, staging, branches, merging, rebasing, repositories, 
   remote repositories, and Git vs Github. 

This tutorial also assumes that you have: 
 
 - Cloned a copy of the dvm-dos-tem repository to your system. 
 - A functioning development environment with your cloned copy of the code. 
 - A Github account. 
 - The ability to set up ssh keys for access to your Github account. (optional)
 - Been added as a collaborator with write access to the 
   http://github.com/uaf-arctic-eco-modeling/dvm-dos-tem repository.

Begin by reading the :ref:`Version Management <software_development_info:Version
Management>` section of this document for an overview of how the ``dvmdostem``
project uses Git and Github.

*************************
Why use version control?
*************************

As mentioned in the :ref:`Version Management <software_development_info:Version
Management>` section, using version control in a project really serves several
purposes: 

   #. Provenance - being able to understand (and trust) where the code came
      from. 
   #. Facilitating contributions from multiple people.
   #. Backup - being able to
      revert the code to a previous state in case of an error or other need.

These needs can of course be met without a full fledged version control system
and as you struggle to learn Git you will almost certainly be tempted to just go
back to periodically emailing yourself backups or printing out the code and
locking it in your gun safe. However I would encourage you to persevere as once
you have the basics of Git under your belt, it will fundamentally change the way
you think about programming and will enable you to interact with a wide variety
of software projects as well as having great control over your own projects.

As you work with Git it is valuable to keep in mind the reasons you are using
version control: backup, collaboration, and provenance. Cultivating a clean,
readable, traceable history frequently requires extra steps and care that will
seem extraneous in the moment. However with a multi-person project this care is
essential to making the project history useful. When you are stuck and wondering
what to do, it is often helpful to think in terms of how you want the code
history (commit graph) to look when you are finished. With the idea of the
history you want to achieve in mind, you can then find a path forward. 

***********************
General Workflow Loops
***********************

According to the IEEE, Software Engineering is the systematic, disciplined,
quantifiable approach to the design, development and maintenance of software
systems. As such software engineers are frequently obsessed with processes -
understanding the processes at play and figuring out how to make them consistent
is one key to achieving the systematic, disciplined, and quantifiable approach
that is called for. 

Below we cover several core processes before assembling them to a full workflow.

Core Development Process Loop
=============================

The core development process loop is shown in the diagram.

.. image:: ../images/workshop_march_2022/lab5/edit-compile-run-check.png
   
These four steps are at the heart of any software work. In different
environments, some of the steps might be automated or hidden, but the steps must
be carried out in order for software to be created. With a single person this is
straightforward. The individual may elect to add additional steps such as
“backup work” or “publish finished code”. 

Loop with individual version control
=====================================

The most basic version control process loop is simply: edit, stage, commit.

.. image:: ../images/workshop_march_2022/lab5/edit-stage-commit.png
   :width: 200
   :alt: core process loop with individual version control

By itself this loop is not particularly useful - it doesn’t even involve running
the code, let alone checking it! But if we add the compile, run and check steps
we are getting closer to a robust development process:

.. image:: ../images/workshop_march_2022/lab5/edit-compile-run-check-stage-commit.png
   :width: 200
   :alt: core process loop with compile run check

There are a number of other steps that might be added:

 * checkout branch,
 * stash changes not ready to be committed
 * merge branch(es)
 * pull from another repo,
 * push to another repo,
 * rebase changes

Also note that the loop doesn’t not strictly need to happen in the above order.
Sometimes you might want to commit code before it runs or you might want to
cycle through the edit → compile → run → check loop many times before
committing.

Incorporating more people
==========================

When multiple people are involved their efforts must be synchronized so that
their changes to the system are compatible and so the people do not interfere
with each other. Git does not specify exactly how this should be done and leaves
many of the details up to the end users. Git provides the general tools to
accomplish collaborative (or individual) work in a wide variety of ways. When
you are interacting with other people you will need to be pushing your changes
to a remote repository and pulling changes from remote repositories. When things
are working smoothly, there are rarely changes that need to be reconciled (merge
conflicts). This leads to a clean and readable history.

There are many complexities and possible scenarios that can come up as this
process is carried out amongst multiple people. It is hard to describe the
scenarios and the implications of different choices without the folks involved
having a pretty solid handle on the basic core developer workflow as well as the
mechanics of the following Git fundamentals:
 
 * Making a commit.
 * Checking out branches.
 * A clone vs a fork.
 * Git vs Github.
 * Viewing git log information (either via command line or GUI app like gitk).
 * Interacting with remote repositories.
 * Browsing a repository on Github

******************************************************
Single person topic branch and pull request process
******************************************************

This part of the tutorial is designed to walk you through a basic case of making
a small modification to the code and getting that change merged into the
upstream codebase. Understand that in the “real world” as you are working on
more complicated changes sets, unique file formats (e.g. Jupyter Notebooks) or
changes that affect other people's environments (e.g. modifying the Dockerfile),
you will frequently need to take additional steps or considerations beyond what
is shown here!

A very similar example to these steps is shown graphically in the accompanying slides ~14-27

:download:`Workshop 2022 Lab 5 <../slides/WS2022_Lab5.pdf>`

The steps:

#. Clone repo to your machine (you may already have a copy in which case
   you don’t need to clone again)

#. Browse the code to find one (or more) of the following:

   #. Find an error or omission in the dvmdostem project’s documentation -
      this should be easy 😉!

      #. Read the section of this document on
         :ref:`software_development_info:Documentation` and documentation systems
         so that you will understand what part of the docs you are improving
         (i.e. just a comment in the code or something that will need to be
         parsed by ``doxygen`` or ``pydoc`` or Python’s ``argparse`` or
         whatever)

      #. Extra credit: find a typo in the Doxygen documentation - then you
         will need to re-build the doxygen outputs to see your modification
         and will get to know about ``.gitignore``

   #. A bug or missing feature in the program.

#. Make sure you have the master branch checked out and are up-to-date
   with the ``upstream/master``.

#. Checkout a topic branch for your fix.

#. Engage in the core development process loop as much as necessary to
   make your modification and verify that it works. For fixing a simple
   typo in a comment string, this might be trivial - there is nothing to
   compile and run or check. For modifying the code this might take many
   cycles of the loop and many commits.

#. Once you have committed changes on your topic branch, you can push
   your topic branch to the upstream repository. You might wait until
   you are finished with the topic branch, or you might push sooner in
   order to back up your work, or to share your work.

#. Once you have finished your work, use the Github website to Create a
   Pull Request. You want to request that your topic branch be merged
   into the uaf-arctic-eco-modeling/dvm-dos-tem master branch.

#. Engage in discussion with other folks using Github’s comments on the
   PR, Slack, or other communications.

   #. Group reviews indicate work is complete: Go to next step
   #. Group reviews indicate more work to be done: continue coding, and
      committing. When you push the topic branch upstream, the Github Pull
      Request will track the updated commits.

#.  In the meantime while waiting on this PR to be merged, you may go
    back to your master branch and checkout a new topic branch to start
    another project. It is fine to have several topic branches going at
    one time.

#. Once your PR has been merged, you need to update your repository to reflect
   the changes: ``git checkout master && git pull upstream master``

#. You are ready to start again!

Discuss:

  * What to do if there is interdependence between topic branches?
  * How to choose a branch?
  * What if you work for a long time and realize you have one branch with many topics in it?


*********************************
Multi-person topic branch process
*********************************

Lets have two people: Y and Z who are both working on the project, and in fact
they both need to work on the same topic branch. This example is harder to write
prescriptive steps for, so instead an example sequence will be enumerated and it
will be up to the reader to translate that into their own concrete steps. This
example is shown graphically in the associated slides.

#. Both people start with the master branch checked out.

#. Person Y checks out a new topic branch and makes several commits.

#. Person Y pushes their topic branch to the upstream repo.

#. Person Z pulls the new topic branch.

#. Person Y makes additional commits.

#. Person Z makes additional commits.

#. Person Y checks to make sure Person Z has not pushed anything.

#. Person Y pushes their new commits.

#. Person Z checks to make sure Person Y has not pushed - but they have!

#. Person Z does a ``git pull - rebase`` which carries out the following
   steps more or less automatically:

   #. takes Person Z's recent commits on top of the topic branch and sets
      them aside

   #. pulls (fetch + merge) Person Y's commits from the upstream topic
      branch and (fast forward) merges the commits on top of the existing
      branch; after this step Person Y and Z's branches are effectively the
      same

   #. replays Person Z's commits on top of the topic branch (which now has
      everything from Person Y)

#. Person Z pushes to upstream topic branch

#. Person Y pulls from upstream topic branch

#. Now Person Y and Z's repositories are identical - each repo has the
   work of both people!

DISCUSS:

-  Why use ``--rebase``

   -  Puts conflict resolution on the coder who is most familiar with the
      section.

   -  Avoids merge commits in the history which can be ard to read.

   -  Makes it likely that topic branch will merge cleanly into
      ``upstream/master``

   -  Provides opportunity for commits to be rearranged and cleaned up
      before being pushed

-  What is appropriate for committing vs keep personal?

.. _Maintaining a personal fork:
.. note::

   Should you maintain a personal fork?
   
   This is situationally dependent. If you are not granted access to the
   upstream repo (https://github.com/uaf-arctic-eco-modeling/dvm-dos-tem.git),
   then you will need to maintain your own fork on GIthub in order to submit
   pull requests. If you do have write access to the upstream repo, then
   maintaining a personal fork is optional. For branches where you are actively
   committing with other people it is simpler to keep the branch o the upstream
   repo, but sometimes a personal fork is nice for additional separation or to
   test ideas that you want backed up to the cloud (by pushing to your fork) but
   are not comfortable having in the upstream repository.

.. _What should I commit:
.. note::

   An initial reaction with version control is to simply commit everything. This
   is a great instinct when working as an individual, and aside from being
   tedious doesn’t really have any drawbacks. However when working with multiple
   people, “over committing” can be a real problem.

.. _Setting up ssh keys:
.. note::

   Some help here about how to setup ``ssh`` keys...

