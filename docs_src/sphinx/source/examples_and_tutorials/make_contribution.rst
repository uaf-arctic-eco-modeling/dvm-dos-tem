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

A very similar example to these steps is shown graphically in the accompanying
slides ~14-27

.. raw:: html

  <!-- Shared from Tobey Carman's WS2022_Lab5 Google Slides presentation -->
  <iframe src="https://docs.google.com/presentation/d/e/2PACX-1vRhJEtl1676vpHOUTxrwcaxlf3bodLLb9s4nSh9ENlzgxYzVyMbfSzSc3bssr9fDFBzZkzslVr2ROm1/embed?start=true&loop=true&delayms=3000" frameborder="0" width="480" height="286" allowfullscreen="true" mozallowfullscreen="true" webkitallowfullscreen="true"></iframe>


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

See accompanying slides (above) ~29-39.

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

