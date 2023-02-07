.. # with overline, for parts
   * with overline, for chapters
   =, for sections
   -, for subsections
   ^, for subsubsections
   ", for paragraphs

########################
Using Github's Features
########################

Github has grown into a multi-featured platform with offerings for many aspects
of the software development process. This mini guide will describe some of the
features that the ``dvmdostem`` project is using.

Comprehensive Github documentation: https://docs.github.com

.. warning:: 

  Github's front-end web interface is constantly changing so your screens may
  look different from any images shown here.


**********************************
Repository Hosting, Organizations
**********************************

Code hosting was the original core offering from Github. They store a Git repo
in the cloud and manage access to it. Most of the other tools are built around
this core service. One of the tools is the ability to create organizations, or
teams of people who can own repositories.

The ``dvmdostem`` repository is hosted under the ``uaf-arctic-eco-modelling``
organization. The organization is owned by Tobey Carman, Ruth Rutter, Helene
Genet and Eugenie Euskirchen and mirrors the working group at Univeristy of
Alaska Fairbanks that has been driving the primary TEM development for the last
10 years or so.


*****************
Code Browsing
*****************

The website is very convenient for browsing the code in its current form and at
other points in the history of the project.  Notice that the landing page
usually shows you the list of files in the project as well as a way to switch
branches. The default branch is usually ``master`` or ``main``. If you scroll
down you can see the project's README.md file.

As you change branches and click on particular commits, notice that the URL
changes in the browser window. The URL can indicate that you are looking at a
general location (such as a branch) or a specific commit. Pay attention to this
if you are trying to direct someone to a particlar place in the code/history.

****************
Releases
****************

We are using Github's "Releases" feature primarily to facilitate DOI creation
and make it easier to cite the project. This works through a webhook that sends
a notification to https://zenodo.org which is an organization that can mint DOI
numbers. When Zenodo recieves a notifcation that a new Github Release has been
created, Zenodo takes a snapshot of the repository, archives the state of the
code at that release (on Zenodo.org) and creates a DOI number which allows
people to cite to the exact version of the code, in perpetuity.

.. note::

  We do not have an explicit method or workflow for creating DOIs from a commit
  that is not tagged as a Github Release.

You can navigate to a list of the Releases and download the code for that
release.

.. note:: 
  
  Downloading the ``.zip`` file for a particular release is not the same as 
  checking out that release in a repository. When you download the files you
  do not get any of the project history, your directory will not be under 
  version control and you won't have access to any of the other project history
  (other branches) from within the downloaded directory.


******************************
Documentation
******************************

Github has several major features that the ``dvmdostem`` project is using to 
help with documentation:

  * Rendering ``*.md`` (Markdown) and ``*.rst`` (ReStructuredText) files on the
    website as nicely formatted ``html``.
  * Hosting a wiki.
  * Publishing web pages on ``github.io``.

Notice that the README text you see at the bottom of the landing page for a
repository is the formatted version of the ``README.md`` file in the root of the 
repository. This is helpful for any other ``*.md`` files in the project as well.

.. warning::

  Avoid the temptation to edit files directly on Github. The web interface
  provides buttons and a text editor that allow you to edit files directly on
  the website. This is dangerous because it subverts the :ref:`Core Development
  Process Loop<prelude:Core Development Process Loop>` by skipping the compile,
  run check steps! It is very easy to introduce bugs by skipping these steps!
  
We were using the wiki that is included with a Github repo for several years,
but as of 2022 we've moved most of the content to a ``github.io`` website built
with Sphinx. The wiki content will be phased out over the next year or so.

Github provides a service whereby pushing to a particular branch makes a website
available at ``https://<orgname>.github.io/<repo-name>``. In our case we are
using the ``gh-pages`` branch and we are pushing a complete website built with
the Sphinx documentation tool. The source code of the website is stored in the
``docs_src/sphinx`` directory. The build process reads the source files and
generates ``html``, which is then pushed to the ``gh-pages`` branch. Github
handles the hosting and serving of these files as well as the domain name
resolution, making the files publicly viewable. 


********************
Pull requests
********************

We are using the "Pull Request" (PR) feature as a way to manage and organize the
addition or modification of the project's code. From `Github
<https://docs.github.com/en/get-started/quickstart/github-glossary#pull-request>`_
:

  "Pull requests are proposed changes to a repository submitted by a user and
  accepted or rejected by a repository's collaborators. Like issues, pull requests
  each have their own discussion forum." 

It is possible to work without pull requests (i.e. working on a shared branch)
but the Pull Request concept and workflow gives several advantages:
 
 * visibility
 * code review
 * access control
 * history organization

Using the Pull Request features of Github allows discussion about the proposed
modifications to take place next to the changes themselves. Each Pull Request
has a discussion thread attached to it and users can put in images, code
snippets and link to other areas of Github's ecosystem (Issues, other PRs,
etc.). THis allows for code review to take place by one or more people in a way
that is transparent and visible to the group.

Pull Requests also provide a way for users that don't have write access to a
repository to get their changes merged into the main repo. The user with out
write access makes changes and pushes them to their personal fork. The Pull
Request is from the user's personal fork to the main repo and a maintainer of
the main repo can merge the request.

For organization of the code base history we are performing all substantive work
on topic branches and merging the branches into ``master`` using Github's Pull
Requests. The result of this is that the commits to ``master`` are all merge
commits and the message should summarize the changes from the topic branch. This
provides a level of organization that allows users to easily see and trust what
code is included in the ``master`` branch.


**********************
Issue tracker
**********************

Github also provides an Issue Tracker (bug tracker) database.
  * making new issues - what info to include 
  * curation of the issue list, tagging, labeling, deleting
  * linking/cross referencing



* Setting up ``ssh`` keys

  * maybe move this to the prelude > version control > setup section.


******************************
Tools we have not used (yet)
******************************

* "Discussions" 
  * we've been using slack
* Container registry
* Github Actions
* Github CLI


