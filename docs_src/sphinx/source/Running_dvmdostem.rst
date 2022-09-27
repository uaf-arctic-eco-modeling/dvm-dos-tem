.. # with overline, for parts
   * with overline, for chapters
   =, for sections
   -, for subsections
   ^, for subsubsections
   ", for paragraphs

#######
Running
#######
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


=================
Running the Model
=================
------------
Spatial Size
------------
The size of your run is controlled by the dimensions of your input set and
the contents of the ``run-mask.nc`` file. If your input set is larger than
1x1, simply mark the cells you're interested in as active in the
``run-mask.nc`` file and the model will run them, by default sequentially.

----------------------------
Single Site or Small Regions
----------------------------
Smaller regions, perhaps no more than a couple dozen cells, can be reasonably
run on a standard workstation. Sequentially would be easiest, although it
could be run in parallel using MPI if the NetCDF output file accesses were
modified to be per-cell and not parallel.

-------------------
Large Regions (HPC)
-------------------
For larger regional areas we utilize an HPC cluster and OpenMPI.

Due to space limitations, we break regional runs into ‘batches’, which are
subsets of the region with a specified number of cells marked in the run
mask. There are a few example scripts in ``/scripts/chinook`` to help with
splitting, running, and merging these regional runs. They will need to be
adapted to run in another environment.

Each batch outputs in parallel to a set of output files shared by all cells
in that batch. This means that currently running with MPI requires a file
system that supports parallel file access.

^^^^^^^^^^^^
Requirements
^^^^^^^^^^^^
* Boost 1.55 built with mpi
* jsoncpp 0.5.0
* lapack 3.8.0
* OpenMPI 4.1.0 built with slurm
* HDF5 1.8.19 with parallel enabled
* NetCDF4 4.4.1.1 linked with hdf5
* Python 2.7 (for examples in ``/scripts/chinook``)
* Python 3 (for general ``dvmdostem`` scripts)

^^^^^^^^^
Splitting
^^^^^^^^^
The batch splitting script pulls from the ``config/config.js`` file, so make
sure that is set up before running. Active cells per batch is set in the
splitting script itself - for a smaller regional run (50x50), we usually do 25
cells per batch. The scriptlet near the bottom of the script holds a few SLURM
settings, including:

* Which email notifications to send
* The email address to send those notifications to
* A timeout limit, after which SLURM will kill the job

When you run the script it will create a subdirectory for each batch in the
specified output directory. Each subdirectory will have a copy of the config.js
file and customized run-mask.nc and slurm_runner.sh files.

^^^^^^^^^^^^^^
Starting a run
^^^^^^^^^^^^^^
By default the batch running script runs a set of batches from an inclusive
range defined by values provided in the call. Example call to run batches 0-9:

``$ ./scripts/chinook/batch_run_on_chinook.sh [path to batch dir] 0 9``

It can instead run a set of batches with indexes manually specified in an array
if needed.

Manually set the number of concurrent batches (in this example ‘3’) to submit to
the SLURM queue in the following statement:

``while [ $(squeue | grep -c [username]) -ge 3 ];``

^^^^^^^
Merging
^^^^^^^
The merging script will attempt to merge all files matching the output file name
format (e.g. GPP_monthly_sc.nc) for each variable in the output_spec file, from
the specified directory and several subdirectory levels below.

There are a few values at the beginning of the batch merging file that you will
need to set:

* OUTPUT_DIR_PREFIX - The parent directory of the batch-run subdirectory
* OUTPUT_SPEC_PATH - The output_spec.csv file used for the run
* FINAL_DIR="${OUTPUT_DIR_PREFIX}/[subdirectory name for merged files]"
* mkdir -p "${OUTPUT_DIR_PREFIX}/[subdirectory name for merged files]"

This script will take quite a long time to run - several hours for a large
regional run. If it produces an incomplete merged file for a variable or two, it
can be re-run for a single variable at a time.

=============================
Running from Restart Files
=============================
``Dvmdostem`` can be stopped at and restarted from any inter-stage pause. The
most useful point to do so will be after either EQ or SP, so the bulk of the
computing does not need to be repeated and experimental TR+SC runs can be
completed quickly.

The files needed to do this are automatically created and named after the stage
that they hold data from: ``restart-[stage].nc``.

.. raw:: html

    <!-- This is an embed link to a Google Drawing created by Ruth Rutter and Tobey Carman -->
    <img src="https://docs.google.com/drawings/d/e/2PACX-1vSL4SJun4GptQWQqkKoTxc1RhiDZcdjz7E8Gkk1bL-pldPu8L0jYC1z2UlrwW-pvE-oH3TTKaQDKS-x/pub?w=963&amp;h=513">

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
