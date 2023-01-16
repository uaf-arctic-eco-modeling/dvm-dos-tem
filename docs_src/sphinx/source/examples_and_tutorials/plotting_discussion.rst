.. # with overline, for parts
   * with overline, for chapters
   =, for sections
   -, for subsections
   ^, for subsubsections
   ", for paragraphs

##################
Plotting 
##################

Plotting is a natural and essential step in the modelling process. There use
-cases and limitations are numerous and there is not a single silver bullet plotting
solution that is sure to work for you.

When working on or with plotting code, it is helpful to remember that problems
can arise in two overlapping spheres: *capability* and *environment*.

*Capability* refers to whether or not the analysis and visualisation you seek are
implemented in the code you are working with.

*Environment* referes to whether the computing environment(s) you work with have
the appropriate hardware, software, tools, etc to carry out the capabilities of
the code you are working with.

These concerns are sometimes totally distinct and sometimes arise in conflict
with each other. Ideally code is written to work with a wide variety of
environments as this makes it easier for other people to use the code in their
circumstances.

***********************************
Existing Tools, Code and Patterns
***********************************

 - existing code in the scripts directory 

  - assumption is generally that you can display interactive windows (Xquartz,
    X11, Xwindows, native windowing environment, etc)

  - directory is getting messy - need to re-factor in to some better patterns
    (i.e. move tests, move stuff into sub-directories) - means figuring
    out/understanding implicaitons with respect to packaging and ``import``

 - sometimes options exist to save to static files 

  - usually it is easy to adjust the code slightly to achieve this (i.e.
    ``plt.show(...)`` -> ``plt.savefig(..)``) - problems with version control
    when you have constant small customizaitons, i.e. file naming, or paths

 - table of existing tools columns: name, CLI implemented?, tests?, save?, show?

 - Notebooks

  - problems with version control

  - problems with out of order execution


***************************
Approches using webserver
***************************

This approach gets around the issue of needing a windowing system by using a
web-browser for display, and a web-server for generating the visualization. In
addition to de-coupling the generation and display conerns, this approach allows
for networking and enables plotting using and Docker container run-time or any
other network-accessible run-time!

Bokeh
=================
This is the current preferred approach - or rather the only approach that has
been tried in any significant capacity.


Other options
=================

 - RStudio, plotly, notebook server


********************
Third party tools
********************

 - ``ncview`` https://cirrus.ucsd.edu/ncview/
 - ``panlopy`` https://www.giss.nasa.gov/tools/panoply/

