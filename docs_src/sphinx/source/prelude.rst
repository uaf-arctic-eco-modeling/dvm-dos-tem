.. # with overline, for parts
   * with overline, for chapters
   =, for sections
   -, for subsections
   ^, for subsubsections
   ", for para

##########
Prelude
##########

All the stuff you should know for the rest of the documentation to make sense.

When possible point towards official sources rather than re-writing
documentation!

**********************
General Programming
**********************


General Workflow Loops
==========================

According to the IEEE, Software Engineering is the systematic, disciplined,
quantifiable approach to the design, development and maintenance of software
systems. As such software engineers are frequently obsessed with processes -
understanding the processes at play and figuring out how to make them consistent
is one key to achieving the systematic, disciplined, and quantifiable approach
that is called for. 

Below we cover several core processes before assembling them to a full workflow.

Core Development Process Loop
-------------------------------

The core development process loop is shown in the diagram.

.. image:: images/workshop_march_2022/lab5/edit-compile-run-check.png
   
These four steps are at the heart of any software work. In different
environments, some of the steps might be automated or hidden, but the steps must
be carried out in order for software to be created. With a single person this is
straightforward. The individual may elect to add additional steps such as
“backup work” or “publish finished code”. 

Loop with individual version control
---------------------------------------

The most basic version control process loop is simply: edit, stage, commit.

.. image:: images/workshop_march_2022/lab5/edit-stage-commit.png
   :width: 200
   :alt: core process loop with individual version control

By itself this loop is not particularly useful - it doesn’t even involve running
the code, let alone checking it! But if we add the compile, run and check steps
we are getting closer to a robust development process:

.. image:: images/workshop_march_2022/lab5/edit-compile-run-check-stage-commit.png
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
---------------------------

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



********************
Version Control
********************


*********************
Documentation Types
*********************



**********************
Docker
**********************
