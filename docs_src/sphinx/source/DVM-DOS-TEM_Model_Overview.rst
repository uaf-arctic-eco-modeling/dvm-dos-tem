.. # with overline, for parts
   * with overline, for chapters
   =, for sections
   -, for subsections
   ^, for subsubsections
   ", for paragraphs


#############################
``dvmdostem`` Model Overview
#############################

*********
Structure
*********

`dvmdostem` is multi-dimensional.

=======
Spatial
=======
TEM is a spatially explicit model. The run domain is divided into grid cells,
or pixels. There is no communication between the grid cells. TEM itself is 
agnostic to the spatial resolution - the resolution is controlled by the 
input files provided. Recent work has been done with 1km spatial resolution.

========
Temporal
========
TEM is a temporal model in the sense that a run operates processes at consecutive
time-steps. In addition, with TEM, the concept of a "run stage" is used to run 
the model over different climatic periods of generally increasing complexity.
There are 5 possible “run stages”:

* Pre-run (pr)
* Equilibrium (eq)
* Spinup (sp)
* Transient (tr)
* Scenario (sn)

The primary difference between the run stages is the nature of the input climate
dataset, and specifically whether there is annual variability in the driving 
climate data that the model uses. A complete, future-projecting, simulation is 
usually only made after advancing the model through several of the previous run 
stages to stabilize the system. Typically the ending state from each stage is 
used as the beginning state for each subsequent stage.

------------
pre-run (pr)
------------

    WRITE THIS

----------------
equilibrium (eq)
----------------
In the equilibrium stage, the climate is fixed. That is, the climate does not 
vary from year to year. There will be intra-annual variability to represent the 
seasons, but from year to year the calculations will be carried out using the 
same annual cycles. Equilibrium run stage is used in the calibration mode, 
and is typically the first stage run for any complete simulation. During the 
eq stage, the annual climate inputs used are actually calculated as the mean 
of the first 30 years of the historic climate dataset, so the mean of the 
values from 1901-1930.

    Special Note: automatic equilibrium detection
    TEM does not have an internal test for whether or not equilibrium has
    been reached. In other words, if you specify ``--max-eq=20000``, the model 
    will run for 20,000 years no matter what internal state it reached. It 
    appears that some of the variable and constant names and the command 
    line flag ``--max-eq`` are vestigial remains of an attempt at "automatic 
    equilibrium detection".

-----------
spinup (sp)
-----------
In the spinup stage, the climate is not fixed. In the sp stage, the driving climate is used from the first 30 years of the historic climate dataset. Should the spstage be set to run longer than 30 years, the 30 year climate period is re-used. Another difference between eq and sp stages is that the sp stage is set to run for a fixed number of years, regardless of the internal state that the model reaches. In the sp stage the fire date is fixed, occuring at an interval equal to the Fire Recurrence Interval (FRI).

--------------
transient (tr)
--------------
In the transient stage, the climate varies from year to year. The tr stage is used to run the model over the period of historical record. The input climate data for the tr stage should be the historic climate. This is typically the climate data for the 20th century, so roughly 1901-2009.
scenario (sc)
In the scenario stage, the climate also varies from year to year, but rather than observed variability, a predicted climate scenario is used.

A complete run utilizes all 5 stages. It is possible to work with any subset of the stages.

=======================
Community Types (CMTs)
=======================
    WRITE THIS...

=======================
Vegetation Types (PFTs)
=======================
    WRITE THIS...

=======================
Soil (Layers)
=======================
    WRITE THIS...

***********
Processes
***********
    WRITE THIS...

==========
Carbon
==========
    WRITE THIS...

==========
Water
==========
    WRITE THIS...

==========
Nitrogen
==========
    WRITE THIS...

=================
Energy Balance
=================
    WRITE THIS...

==========
Permafrost
==========
    WRITE THIS...

==============
Disturbance
==============
    WRITE THIS...

==========
Methane
==========
    WRITE THIS...

*********************
Inputs/Outputs (IO)
*********************
    WRITE THIS...

==========
Inputs
==========
    WRITE THIS...

==========
Outputs
==========
    WRITE THIS...

------------------
Output Selection
------------------
    WRITE THIS...

-------------
Process
-------------
    WRITE THIS...

------------------------------
Variable Output Combinations
------------------------------
    WRITE THIS...
