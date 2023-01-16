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
-cases and limitations are numerous and there is not a single silver bullet
plotting solution that is sure to work for you.

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



......................

*****************
Plotting outputs
*****************

There are several plotting tools buried in the ``scripts/`` directory but none
of them are particularly polished or fine tuned. Many, but not all, of the
scripts have decent info with the ``--help`` flag. There is not a consistent
pattern for whether plots are saved or shown in an interactive window, and in
the cases where the plots are saved, the file names are not standardized. In
other words, as a user, you will likely need to look at the script code to
determine whether your plot will be displayed or saved. For example, looking at
script ``plot_output_var.py`` with a text editor, approximately lines 250-252,
we can see that in fact both ``plt.savefig()`` and ``plt.show()`` are being
called. 

.. image:: ../images/workshop_march_2022/lab1/plot_output_var.png
   :width: 600
   :alt: plot_output_var script


This actually works nicely because when the command is run on the Docker
container, the ``plt.show()`` call is essentially ignored and the resulting plot
is saved to a file. The name of the saved plot is not currently configurable, so
it would be up to the user to rename the file and move it somewhere appropriate.

Also note that there is a script, ``output_utils.py``, that is designed to be
imported into other Python scripts and has a bunch of functions for summarizing
variables over various dimensions (layers, pfts, etc).

The existing plotting tools rely on a variety of specific Python libraries, and
not everything has been tested with the versions specified in the
``requirements.txt`` file, so you might encounter small issues with the scripts
that have to be resolved before they will run. Frequently this is just a matter
of updating deprecated function calls for libraries like ``matplotlib`` or
``pandas`` that have been changed since we first wrote the plotting tools.
Please submit a Github pull request if you encounter and fix any of these
issues!

While all of the existing plotting tools are written in Python, users are free
(and encouraged!) to write their own plotting tools using whatever language they
prefer. We have made a lot of effort to make our outputs conform to the `CF
Conventions`_, especially with respect to the time dimensions, data units, and
geo-referencing. The output files are generally viewable at a basic level using
standard tools like `ncview`_ as well.

.. _docker interactive plotting:
.. note::

  Working with Docker provides advantages for standardizing the Python
  environment and folder structure amongst developers, but provides one
  significant hurdle for plotting: it is difficult to display the standard
  Matplotlib interactive plotting window due to the need for the XWindows system
  to be installed on your host computer and the ``DISPLAY`` environment variable to
  be set correctly. Typically when plotting with ``matplotlib`` natively on your
  computer, when you run ``plt.show(...)`` you are presented with a window showing
  the plot and including some panning and zooming controls. From inside a Docker
  container this will not work - nothing will show up and you may get error
  messages.

  There several possible solutions/workarounds we have discovered:

  #. Avoid using ``plt.show(...)`` and instead modify plotting scripts to use
     ``plt.savefig(...)``.

  #. Install XWindows on the host system, Python TKinter inside Docker container
     and set the ``DISPLAY`` environment variable appropriately when executing
     commands in Docker container. See more info here:
     https://stackoverflow.com/questions/46018102/how-can-i-use-matplotlib-pyplot-in-a-docker-container.
  #. Run a Jupyter Notebook Server inside the Docker container and do plotting
     inline in Jupyter Notebook.
  #. Perform plotting and analysis on your host system.

Before we get to plotting we should first review the outputs that we have
specified for this model run and look at the files that were created. During the
setup, we requested three variables, GPP, RH and VEGC. We requested GPP and RH
at yearly resolution, and VEGC at monthly and PFT resolution. We also indicated
that we did not want output for the equilibrium stage, but we did want output
for all other run stages. We can easily verify these settings by looking at the
``config.js`` file for the run and using the ``--summary`` option for
``outspec_utils.py``, which you are encouraged to do on your own.

We can start by looking at the output files that were created by our run:

.. code:: bash

  $ docker compose exec dvmdostem-dev ls /data/workflows/ws2022_lab1/output
  GPP_yearly_sc.nc  RH_yearly_sp.nc     VEGC_monthly_tr.nc  restart-sp.nc
  GPP_yearly_sp.nc  RH_yearly_tr.nc     restart-eq.nc	  restart-tr.nc
  GPP_yearly_tr.nc  VEGC_monthly_sc.nc  restart-pr.nc	  run_status.nc
  RH_yearly_sc.nc   VEGC_monthly_sp.nc  restart-sc.nc

You can ignore the ``restart-*.nc`` files - these files help the model transition
from one stage to the next. And we can see that we have three files for each
variable - one file for each run-stage. If we inspect the GPP file we can see
that there is a single data variable (GPP), the dimensions are (time, y, x), and
the length of the time dimension is 25 which corresponds to the number of spinup
years we ran for.

.. code::bash

  $ docker compose exec dvmdostem-dev ncdump -h /data/workflows/ws2022_lab1/output/GPP_yearly_sp.nc 
  netcdf GPP_yearly_sp {
  dimensions:
    time = 25 ;
    y = 10 ;
    x = 10 ;
  variables:
    double GPP(time, y, x) ;
      GPP:units = "g/m2/year" ;
      GPP:long_name = "GPP" ;
      GPP:_FillValue = -9999. ;
  ...

One of the easiest things we might want to look at is a time series plot of GPP
for one of the pixels we ran. This can easily be done with ncview, but you will
almost certainly encounter the problems described in the note about Docker and
interactive plotting `docker interactive plotting`_. If you run ``ncview`` on
your host machine (from which the output files should be accessible thanks to
the Docker volume), you will see something like this:

.. image:: ../images/workshop_march_2022/lab1/ncview.png
  :width: 600
  :alt: example ncview


Note that while the ncview interface appears a bit antiquated, it is an
extremely functional program that allows exploration of NetCDF files.

We can create a very similar plot to the ``ncview`` plot using our
``plot_output_var.py`` script, for example. Notice that we have used the one-off
style of command here, and that we are viewing the saved file after the script
has exited. 

.. image:: ../images/workshop_march_2022/lab1/plot_output_var_example.png
  :width: 600
  :alt: example output plot



