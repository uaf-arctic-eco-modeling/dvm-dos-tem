.. # with overline, for parts
   * with overline, for chapters
   =, for sections
   -, for subsections
   ^, for subsubsections
   ", for paragraphs

#######
Running
#######

This chapter is split into two sections, one covering the practical aspects of 
running the model and the other covering the more conceptual aspects.

*************
Practical
*************

The following sections will outline the steps you need to take and commands
will need to run the software and associated pre and post processing tools.

================
Getting Started
================

-------------
Download
-------------

Download the source code from Github:
https://github.com/uaf-arctic-eco-modeling/dvm-dos-tem.git or clone the code
using git:

.. code::

    git clone git@github.com:uaf-arctic-eco-modeling/dvm-dos-tem.git

It is also possible to download just the code for a specific release from the 
`Releases`_ page on Github.


-------------
Dependencies
-------------

To see the list of libraries that must be installed for ``dvmdostem`` to compile
and run, look at the install commands in the project's ``Dockerfile`` s.

While the supporting scripts don't need compilation, they require a bunch of
supporting libraries and software to be installed. Again looking at the install
commands and comments in the ``Dockerfile`` s will show the dependencies.

---------
Compile
---------

The ``dvmdostem`` program must be compiled from C++ source code. If you have the
dependencies installed and accessible on your ``PATH``, then you can install
using ``make``, executed from the root of the project. There is also a
`SCons`_ file and the command ``scons`` can be used to compile.

The majority, if not all, of the supporting scripts and tools are written in
interpreted languages and don't need compilation.


-----------
Install
-----------

There is not an explicit installation step for ``dvmdostem``. You can add the
directory where you keep the code (named ``dvm-dos-tem`` by default when you
clone the repository), to your ``$PATH`` variable, or you can reference the 
scripts and other programs by their absolute path.

While the ``$PATH`` variable is setup in the development docker container:

.. code:: 

    develop@d146768bfaac:/data/workflows$ runmask.py -h
    usage: runmask.py [-h] [--verbose] [--reset] [--all-on] ...
                        [FILE]


many of the examples still show things using the absolute path:

.. code::

    develop@d146768bfaac:/data/workflows$ /work/scripts/runmask.py --help
    usage: runmask.py [-h] [--verbose] [--reset] [--all-on] ...
                        [FILE]



==================
Control Options
==================

There are generally three ways you can control how ``dvmdostem`` runs:

 - Command Line Options
 - Configuration Files
 - Parameter Files

If setting are present in both the configuration files and the command line 
options, precedence is given to the command line.

--------------
Command line
--------------

The best way to see the command line options for ``dvmdostem`` is by using the 
``--help`` flag. 

--------------
Configuration
--------------

The ``dvmdostem`` program will look for a file, ``config/config.js`` when
starting. The file is ``.json`` formatted, and should have the following top
level keys:

.. code::

    {
    "general": { },
    "IO": { },
    "calibration-IO": { },
    "stage_settings": { },
    "model_settings": { },
    }

Of note is that under the "stage_settings" entry it is now possible to control
which modules of the model are enabled at different stages. Previously this was
not possible to modify after compilation unless you were using the calibration
mode and the calibration directives file.

--------------
Parameters
--------------

``dvmdostem`` is designed to be highly configurable with regards to parameters.
This means that many parameters have been factored out so that their values can
be set in text files which allows the operation of the model to be changed
without re-compiling. But this flexibility results in **lots** of parameters,
and managing them can be cumbersome.

``dvmdostem`` ingests parameters that are stored in a custom, space delimited,
fixed width text format. The format is a compromise that allows:
 
 * Storing parameters for multiple Community Types (CMTs) in one file.
 * Human readable text format (space delimted columns).
 * Easily editable on a small scale (adjusting a couple parameters).

at the expense of:

 * Easy editing on a large scale.
 * Standardizaton/portability to other tools (e.g. spreadsheet, or database).
 * Easy handling of metadata such as CMT names, PFT names, parameter names, 
   units, comments, and references

The ``util/param.py`` script has many functions to help manipulate ``dvmdostem``
parameter files. Included in ``util/param.py`` are functions that can help
convert from the custom fixed width text (FWT) format to command separated value
(CSV) and back. Certain edits (such as adding and updating metadata) are much
easier to accomplish in a spreadhsheet program. The metadata in the existing FWT
files is incomplete and the assumption is that this will improve over time as
users convert to CSV, work on the files, updating values (i.e. through
calibration, new observations or further literature review), and updating
metadata and then convert the files back to FWT before comitting to the
repository. This is described in the following diagram.

.. raw:: html

   <!-- From Shared Drive, Documentation Embed Images folder google drawing "working_with_parameters"-->
   <img src="https://docs.google.com/drawings/d/e/2PACX-1vTla1Wpo09y9OO1vSdcoHo_o4drkumHU1gET-P1Uz31QBk3Fgepp11NFvZi88LQ8HdPSLTdS1f9joUu/pub?w=960&amp;h=720">

More information about the csv format can be found with the ``param.py
--csv-v1-spec`` command line option. Rather than circulating a template file,
the intention is that the user creates template files from the FWT files using
the tools in ``param.py``.


``util/param.py`` also has facilities for converting from FWT to json and back.
These functions had thus far been most useful in integrating ``dvmdostem`` with 
other software such as `PEcAn`_


Example parameter files can be found in the ``parameters/`` directory. The 
general structural constraints are enumerated here:

 * The parameters are grouped into different files by rough theme.
 * Each file can have 1 or more "blocks" of CMT data, (CMT blocks).
 * Within one file the CMT blocks must contain identical lists of parameters (by
   name).
 * Comments in the file are accomplished with ``//``.
 * Each CMT block starts with a line containing the CMT code, e.g. an 
   alpha numeric code consisting of the letters ``CMT`` followed by two 
   digits, for example ``CMT05``
 * There may be any number of comment lines (beginning with ``//``) present
   between the beginning of block and the data as long as they do not contain
   the string ``CMT``
 * Each parameter will be stored on a line. The value of the parameter will be
   followed by a comment containing the parameter name and optionally units, 
   description, comments and references, formatted like so:

   .. code:: text
       
       1.0 // param_name: units // description // comment // refs

   The parameter name (followed by ``:`` ) is required, all other fields are
   optional.
 * For PFT specific data, the data block will have space delimited columns, with
   one column for each PFT. 
 * For PFT specific data, the last comment line before the data begins will hold
   the PFT names, i.e. "BlackSpruce" or "Moss".
 * For CMTs that don't define all 10 PFTs, the undefined PFTs will have a name 
   like 'Misc' or 'PFT' or 'pft'
 * The CMT and PFT names are not used in the C++ code but many of the pre- and
   post-processing Python tools expect the CMT and PFT names to be present.

An abbreviated example of non-PFT data from ``cmt_bgcsoil.txt``:

 .. code:: text

    //===========================================================
    // CMT04 // Shrub Tundra // Calibrated for Toolik area.
    2.0               // rhq10:
    ....
    0.2               // propftos:
    0.0               // fnloss:  fraction N leaching (0 - 1) when drainage occurs
    .....
    3.93              // initavln:  was 0.68

An abbreviated demonstration example of PFT specific data from
``cmt_envcanopy.txt``:

  .. code:: text

    //===========================================================
    // CMT89 // Demo Example // more comments...
    // extra comment line...
    //Spruce    Decid       PFT2    ...    PFT9   // names: comments                  
    0.10        0.10        0.10    ...    0.10   // albvisnir: canopy albedo
    ...
    0.003       0.003       0.003   ...    0.003  // glmax: m/2 // max. canopy conductance
    ...
    0.0         0.0         0.0     ...    0.0    // initvegsnow: initial intercepted snow water in canopy





=================
Running the Model
=================

----------------
Setting up a run
----------------
Each run should take place in its own workign directory. This directory should
have a variety of configuration files, parameter files, and output directory and
optionally calibration and input files. See the script
``setup_working_directory.py`` which is a helper tool for intitializing a run
directory.

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

    WRITE THIS....

------------------
Output Selection
------------------
    WRITE THIS...

.. note:: draft thoughts: 
    NetCDF outputs are specified in a csv file named in config/config.js. The 
    csv file specifies a variable name (for identification only - it does not 
    correspond to the variable name in the code), a short description, units, 
    and what level of detail to output on (timestep and variable part).
    [Link to default file after PR merge] Variable name, Description, 
    Units, Yearly, Monthly, Daily, PFT, Compartment, Layer,
    Example entry: VEGC,Total veg. biomass C,gC/m2,y,m,,p,c,,
    This will output VegC every month, and provide both PFT and PFT 
    compartment values.
    The file is more user-friendly when viewed in a spreadsheet.
    [example]
    A complete list of output combinations is below
    The initial list of outputs can be found at Issue #252
    LAYERDEPTH, LAYERDZ, and LAYERTYPE should be automatically output if 
    the user specifies any by-layer output. They are not currently, so ensure
    that they are specified on the same timestep as the desired output.
    HKLAYER, LAYERDEPTH, LAYERDZ, LAYERTYPE, TCLAYER, TLAYER, and VWCLAYER 
    must have the layer option specified or they will generate NetCDF 
    dimension bound errors.


-------------
Process
-------------
    WRITE THIS...

.. note:: draft thoughts:
    A single output file will be produced for each entry in the specifying file, 
    based on variable name, timestep, and run stage.
    VEGC_monthly_eq.nc
    At the beginning of the model run, an output file will be constructed for each 
    variable specified, for each run stage where NetCDF output is indicated and that 
    has more than 0 years of run time.
    Currently the model tracks the variables specified for each timestep as separate 
    sets (i.e. monthly separate from yearly, etc). This reduces the number of map 
    lookups every time the output function is called, but increases the number of 
    monthly vs. yearly string comparisons.

------------------------------
Variable Output Combinations
------------------------------
    WRITE THIS...

.. note:: draft thoughts:
    '-' indicates that the combination is not an option 'x' indicates that the
    combination has been implemented in the code '?' indicates that it is undecided 
    if the combination should be made available, or that structure in the code needs 
    to be modified to make data available for output.
    Three variables should be automatically written out if any by-layer variable is 
    specified: Layer type Layer depth Layer thickness Currently they are written out 
    like standard variables. Automation will need to be added in the future.


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

****************************************
Conceptural Modeling Method and Workflow
****************************************
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

.. links 
.. _PEcAn: https://pecanproject.github.io
.. _Releases: https://github.com/uaf-arctic-eco-modeling/dvm-dos-tem/releases
.. _SCons: https://scons.org