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

   The MADS Assisted Calibration process has been a group effort led by `Helene
   Genet <UAFHG_>`_  and `Elchin Jafarov <WCRCEJ_>`_ with contributions and
   testing from the team at `Woodwell Climate Research Center <WCRC_>`_ as well
   as the `UAF Arctic Ecosystem Modeling Group <UAFAEMG_>`_, including:

    - Tobey Carman
    - Ruth Rutter
    - Aiza Kabeer
    - Andrew Mullen
    - Ben Maglio
    - Joy Clein
    - Valeria Briones
    - Eugenie Euskirchen



The description in the :ref:`Calibration Process <calibration:Calibration
Process - Conceptual>` section is a guideline from the most susccessful of the
manual calibration efforts. The new part of the approach presented here involves
using the following flow diagram to carry out each step of the process.

.. raw:: html

   <!-- From shared drawing: Documentation Embed Images "SA-CA-workflow"--> 
   <img src="https://docs.google.com/drawings/d/e/2PACX-1vS-qINFX6KDS8nkX8JtXav_5LKSsg4tX27zP3uNxlChEPRQn9nHALp1tnZbFXiV3NHk_xw_qtjvuObF/pub?w=1852&amp;h=1200">
   
   <figcaption>Fig 1. Overview of Sensitivty and Calibration workflow.</figcaption>  

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

   <figcaption>
     Fig 2. Sensitivty Analysis detail. Smiley face icon indicates that user 
     interaction or input is required.
   </figcaption>  


The first part of the SA is to setup your config file. The config file is where
you will choose which parameters to run the analysis for and which targets
(outputs) you will need for comparison. Additionally in the config file you will
specify the PFTs that will be used for each of the PFT specific parameters (and
targets).

There are other settings available to you as well concerning the number of years
to run each stages , the site to run, and the working directory to you would like
the runs to take place in.

.. note:: 
   
   We are working on defining a reccomended directory structure for organizing 
   your work. 

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
other pos hoc analysis using the ``SA_post_hoc_analysis.py`` tool. The tool
provides a number of plotting functions that will help the user assess whether
or not the modeled output is within acceptable range of the targets.

See :ref:`here <scripts_API:mads_calibration.SA_post_hoc_analysis>` for examples.


********************************
MADS Assisted Calibration (CA)
********************************

Once you have completed the SA portion, you can move on to the CA (calibration)
portion of the workflow. In this step you use a minimization algrorithm to find
an optimal set of parameters such that the discrepancy between model outputs and
target (observed) values is minimized. 

The actual minimization alrorightm is provided by the `Mads Library <MADS_>`_.

Simiar to the SA part of the workflow you will provide your settings in a config
file and then feed that file to a script that will carry out the optimization.
At the end you will have an optimal set of parameters as well as some metadata
about the optimizaiton process that you can use to reason about the quality of
the optimization.

.. raw:: html

   <!-- From shared drawing: Documentation Embed images "CA-workflow-annotated"-->
   <img src="https://docs.google.com/drawings/d/e/2PACX-1vRoEgpbmkV89HfoX7-MaTQmQBPcQFvWVMGWQUbG7mK2JrioFBVRMyEyekE8LGG7NoHaO2X9_cVMayM4/pub?w=1252&amp;h=796">

   <figcaption>
     Fig 3. Mads Calibration detail. Smiley face icon indicates that user 
     interaction or input is required.
   </figcaption>  



.. _MADS: https://www.madsjulia.github.io
.. _WCRC: https://www.woodwellclimate.org/
.. _WCRCEJ: https://www.woodwellclimate.org/staff/elchin-jafarov/ 
.. _UAFHG: https://www.uaf.edu/iab/people/faculty.php?who=Genet_Helene
.. _UAFAEMG: https://github.com/uaf-arctic-eco-modeling

