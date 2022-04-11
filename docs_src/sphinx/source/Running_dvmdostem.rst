.. # with overline, for parts
   * with overline, for chapters
   =, for sections
   -, for subsections
   ^, for subsubsections
   ", for paragraphs

######################
Running ``dvmdostem``
######################
    WRITE THIS...

*****************************
Modeling Method and Workflow
*****************************
    WRITE THIS...

The modeling process is multifaceted and can be approached in a number of ways
and for different reasons. A schematic overview of the entire process is given
in the following image:

.. raw:: html
  
    <!-- This is an embed link to a Google Drawing created by Tobey Carman --> 
    <img src="https://docs.google.com/drawings/d/e/2PACX-1vQc-OuFaMSpaMA05Q_ah9q_Rm5of7cF3uuPRjQ7-d7bJofkahwQ5VLRFYk69KnuoooKl8kWM1xW6t6e/pub?w=720&amp;h=540">

===============
Develop goals
===============
    WRITE THIS...

====================
Conceptualization
====================
    WRITE THIS...

====================
Formulation
====================
    WRITE THIS...

====================
Implementation
====================
    WRITE THIS...

====================
Parameterization
====================
    WRITE THIS...

====================
Model Testing
====================
    WRITE THIS...

====================
Model Analysis
====================
    WRITE THIS...

=========================
Pre- and Post- Processing
=========================
    WRITE THIS...

*************
Practical
*************
    WRITE THIS...

==================
Control Options
==================
    WRITE THIS...

--------------
Command line
--------------
    WRITE THIS...

--------------
Configuration
--------------
    WRITE THIS...

--------------
Parameters
--------------
    WRITE THIS...

=======================
Running a single site
=======================
    WRITE THIS...

========================
Running multiple sites
========================
    WRITE THIS...

=============================
Running from restart files
=============================
``Dvmdostem`` can be stopped at and restarted from any inter-stage pause. The
most useful point to do so will be after either EQ or SP, so the bulk of the
computing does not need to be repeated and experimental TR+SC runs can be
completed quickly.

The files needed to do this are automatically created and named after the stage
that they hold data from: ``restart-[stage].nc``.

------
Set up
------
Complete an initial run through to the point you wish to restart from. If you
want the outputs from later stages for comparison purposes, running those as
well will not disrupt the process.

If you produced output files in your initial run that you want to retain, you
will need to manually move them elsewhere. Leave the restart files in the output
directory.

-------
Restart
-------
Two flags are necessary in order to restart: ``--no-output-cleanup`` and
``--restart-run``. The first keeps dvmdostem from re-creating the output
directory (and therefore deleting its contents) and the second prevents it from
creating new ``restart-[stage].nc`` files that would overwrite the ones needed
to restart.

Where to restart from is controlled by how many years are specified per stage.
If 0, a stage is skipped and dvmdostem attempts to continue from the next stage.
For example, to restart after spinup and only run transient and scenario, the
year counts would be something like this: ``-p 0 -e 0 -s 0 -t 115 -n 85``

==================================
Running a Sensitivity Analysis
==================================
    WRITE THIS...

==================================
Parallel Options
==================================
    WRITE THIS...

==================================
Processing Outputs
==================================
    WRITE THIS...

==================================
Processing Inputs
==================================
    WRITE THIS...

----------------------
From IEM/SNAP data
----------------------
    WRITE THIS...

-----------
From ERA5
-----------
    WRITE THIS...
