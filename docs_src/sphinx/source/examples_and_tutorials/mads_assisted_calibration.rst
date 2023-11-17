.. # with overline, for parts
   * with overline, for chapters
   =, for sections
   -, for subsections
   ^, for subsubsections
   ", for paragraphs

###########################
MADS Assisted Calibration
###########################

This is an new and evolving approach to calibraton. The process described here
generally follows the conceptual outline described in the :ref:`Calibration
Process <calibration:Calibration Process - Conceptual>` section, but with some
portions being done iteratively and or in an automated fashion.

.. note:: 

   The MADS Assisted Calibration process has been a group effort led by Elchin
   Jafarov with contributions and testing from the team at Woodwell Climate Research Center as well as the UAF Team, including:

    - Tobey Carman
    - Helene Genet
    - Ruth Rutter
    - Aiza Kabeer
    - Andrew Mullen
    - Ben Maglio
    - Joy Clein
    - Valeria Briones
    - 


The description in the :ref:`Calibration Process <calibration:Calibration
Process - Conceptual>` section is a guideline from the most susccessful of the
manual calibration efforts. The new part of the approach presented here involves
using the following flow diagram to carry out each step of the process.

.. raw:: html

   <!-- From shared drawing: Documentation Embed Images "SA-CA-workflow"--> 
   <img src="https://docs.google.com/drawings/d/e/2PACX-1vS-qINFX6KDS8nkX8JtXav_5LKSsg4tX27zP3uNxlChEPRQn9nHALp1tnZbFXiV3NHk_xw_qtjvuObF/pub?w=1852&amp;h=1200">
   
   <figcaption>Caption?</figcaption>  

There are two distinct parts of the workflow: the Sensitivity Analysis (SA;
orange boxes, left side) and the MADS Assist (MADS; blue boxes, right side). In
many cases it is reccomened to use Sensitivity Analysis before MADS to better
constrain the search space. Conducting a full calibration of a new site will
involve going through this flow chart many times with different config files
and settings that increase the ecosystem complexity - following the steps in
:ref:`Calibration Process <calibration:Calibration Process - Conceptual>`.


**************************
Sensitivity Analysis (SA)
**************************

.. raw:: html

   <!-- From shared drawing: Documentation Emebd images "SA-workflow-annotated"-->
   <img src="https://docs.google.com/drawings/d/e/2PACX-1vSTCt5ajys-SvFIz8Kqkgx2O-cN28rN3UwozPBJ32v4yID5RnyZyj1y1kYwwwntkKI1sz36jiLL52N1/pub?w=1257&amp;h=798">

The first part of the SA is to setup your config file. The config file is where
you will choose which parameters to run the analysis for and which targets
(outputs) you will need for comparison. Additionally in the config file you will
specify the PFTs that will be used for each of the PFT specific parameters (and
targets).

There are other settings available to you as well concerning the number of years
to run each stages , the site to run, and the working directory to you. Thus far
a common orgnaizational patterns is to ... DESCRIBE THIS .....

Once you have adjusted the config file to your liking, then next step is using
the ``SA_setup_and_run.py`` tool. There are several command line options with
this script allowing you to control the number of samples and the sampling
method used to generate the parameter samples.

When the ``SA_setup_and_run.py`` tool has completed, you will have the following
files:

 * sample_matrix.csv
 * targets.csv
 * param_props.csv
 * results.csv

With the above files in hand the user can conduct an equlibrium check and any
other pos hoc analysis using the ``SA_post_hoc_analysis.py``. The tool provides
a number of plotting functions that will help the  user assess whether or not
the modeled output is within acceptable range of the targets.

Examples of the plots are here:




***************************
MADS Assist
***************************

STILL nEED TO DO THIS REFACTOR...

.. .. image:: picture.jpeg
..    :height: 100px
..    :width: 200 px
..    :scale: 50 %
..    :alt: alternate text
..    :align: right



.. .. figure:: picture.png
..    :scale: 50 %
..    :alt: map to buried treasure

..    This is the caption of the figure (a simple paragraph).

..    The legend consists of all elements after the caption.  In this
..    case, the legend consists of this paragraph and the following
..    table:

..    +-----------------------+-----------------------+
..    | Symbol                | Meaning               |
..    +=======================+=======================+
..    | .. image:: tent.png   | Campground            |
..    +-----------------------+-----------------------+
..    | .. image:: waves.png  | Lake                  |
..    +-----------------------+-----------------------+
..    | .. image:: peak.png   | Mountain              |
..    +-----------------------+-----------------------+

