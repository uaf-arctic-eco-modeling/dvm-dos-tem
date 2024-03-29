.. # with overline, for parts
   * with overline, for chapters
   =, for sections
   -, for subsections
   ^, for subsubsections
   ", for paragraphs

###################
Command Cheat Sheet
###################
This is strictly a reference document - the following commands do not define
a specific process.

===
Git
===
This is a selection of Git commands most useful for working with dvmdostem.
For more thorough coverage, visit the Git documentation:
https://git-scm.com/doc

------
Status
------
These commands print information to the console and change nothing.

.. list-table::
   :width: 100%
   :widths: 40 60

   * - ``$ git status``
     - See the current state of your local repository
   * - ``$ git branch``
     - List all local branches, including the active one
   * - ``$ git branch -r``
     - List all remote branches
   * - ``$ git remote -v``
     - List all remote repositories

-----------------
Branch Management
-----------------
.. list-table::

   * - ``$ git checkout -b [branch-name]``
     - Create a new branch
   * - ``$ git checkout [remote-branch-name]``
     - Check out a remote branch
   * - ``$ git checkout --track [remote-name]/[branch-name]``
     - Force a new local branch to track a remote branch
   * - ``$ git checkout [branch-name]``
     - Move to another branch
   * - ``$ git branch -d [branch-name]``
     - Delete a merged branch
   * - ``$ git branch -D [branch-name]``
     - Force delete a branch, even if Git warns you

.. _staying_udpated:

-------------------------------
Keeping ``master`` up to date
-------------------------------

.. list-table::

   * - **Command Sequence**
     - **Notes**
   * - | ``$ git checkout master``  
       | ``$ git remote update`` 
       | ``$ git pull upstream master``
     - | Make sure you are on the master branch
       | Update remote refs
       | Fetch and merge the upstream changes


--------------------------------------------------------------
Keeping ``master`` up to date while retaining local changes
--------------------------------------------------------------

.. list-table::

   * - **Command Sequence**
     - **Notes**
   * - | ``$ git remote update``
       | ``$ git stash``
       | ``$ git checkout master``
       | ``$ git pull upstream master``
       | ``$ git checkout [PREVIOUS BRANCH]``
       | ``$ git stash pop``
     - | See what has changed upstream
       | Set aside local changes
       | Checkout the master branch
       | Fetch and merge code from upstream
       | Go back to the branch you were working on
       | Re-apply your local changes

-------------------------------
Changing branches
-------------------------------

.. list-table::

   * - **Command Sequence**
     - **Notes**
   * - | ``$ git status``  
       | ``# address changes (e.g. stash, commit, or revert)`` 
       | ``$ git checkout [BRANCH]``
     - | See if you have any local changes
       | Deal with your local changes
       | Change branches

-------------------------------
Making a commit
-------------------------------

.. list-table::

   * - **Command Sequence**
     - **Notes**
   * - | ``# edit files...make changes``  
       | ``$ git status`` 
       | ``$ git diff``
       | ``$ git add [PATH TO FILE TO ADD]``
       | ``$ git commit -m "Your message..."``
     - | Do your coding work, whatever it may be...
       | See what you've changed
       | Evaluate what changed
       | Add changes to the staging area
       | Actually make the commit.

.. note:: 

   Most of the time in order to make simple, clear, consise commits, you need
   granular control over which lines of each file shoud be comitted. This is
   possible using the command line interface to Git but is frequently easier
   using a graphical client such as Git Cola or Git Gui. Thre are many other
   graphical clients available as well. 




---------------
Code Management
---------------
.. list-table::

   * - ``$ git fetch``
     - Fetch all new commits from all remotes
   * - ``$ git pull [remote]``
     - Update the current branch from the remote repository
   * - ``$ git add [filename]``
     - Stage the changes made to `filename` for committing
   * - ``$ git restore [filename]``
     - Discard changes made to `filename`
   * - ``$ git restore --staged [filename]``
     - Unstage changes made to `filename` but don't discard them
   * - ``$ git commit``
     - Commit all staged changes
   * - ``$ git push [remote] [local branch]:[remote branch]``
     - Push your local branch to the specified remote repository

======
Docker
======
Depending on your setup, you may need to replace ``docker-compose`` with
``docker compose`` in the following commands.

.. list-table::

   * - ``$ docker-compose up -d``
     - Start the container(s)
   * - ``$ docker-compose exec [container name] [command]``
     - Run a one-off command inside a container
   * - ``$ docker-compose exec dvmdostem-run bash``
     - Run ``bash`` inside the container ``dvmdostem-run`` so all further
       commands are executed in the container
   * - ``$ docker-compose exec -u root dvmdostem-run bash``
     - Run ``bash`` inside ``dvmdostem-run`` as the root user. This will avoid
       permission errors but should be used with care.
   * - ``$ exit``
     - Exit the container
   * - ``$ docker-compose down``
     - Shut down the container(s)

=========
dvmdostem
=========
These are a few of the most common script calls and commands related to
running ``dvmdostem``. More complete instructions can be found by using the
``--help`` option with each program.

.. list-table::

   * - ``$ ./scripts/util/setup_working_directory.py [output_dir] --input-data-path
       [input_dir]``
     - Set up a working directory
   * - ``$ ./scripts/util/runmask.py --reset [run-mask file]``
     - Disable all cells in the run mask
   * - ``$ ./scripts/util/runmask.py --yx 0 0 [run-mask file]``
     - Enable cell 0,0 in the run mask
   * - ``$ ./scripts/util/outspec.py [output spec file] --reset``
     - Disable all outputs
   * - ``$ ./scripts/util/outspec.py [output spec file] --on [var] [timestep]
       [granularity]``
     - Enable an output (generic)
   * - ``$ ./scripts/util/outspec.py [output spec file] --on GPP m pft``
     - Enable GPP output by month and pft
   * - ``$ ./dvmdostem -l err -f [config file] -p 50 -e 100 -s 250 -t 115 -n 85``
     - Run `dvmdostem` with error level logging and a specified config file