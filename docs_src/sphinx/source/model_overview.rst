.. # with overline, for parts
   * with overline, for chapters
   =, for sections
   -, for subsections
   ^, for subsubsections
   ", for paragraphs


##############
Model Overview
##############

.. raw:: html

   <!-- From Tobey Carman's google drawing "dvmdostem-general-idea-science"-->
   <img src="https://docs.google.com/drawings/d/17AWgyjGv3fWRLhEPX7ayJKSZt3AXcBILXN2S-FGQHeY/pub?w=960&amp;h=720">
    
*********
Structure
*********

`dvmdostem` is multi-dimensional. It operates across spatial and temporal 
dimensions, soil layers, and plant functional types.

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
* Scenario (sc)

The primary difference between the run stages is the nature of the input climate
dataset, and specifically whether there is annual variability in the driving 
climate data that the model uses. A complete, future-projecting, simulation is 
usually only made after advancing the model through several of the previous run 
stages to stabilize the system. Typically the ending state from each stage is 
used as the beginning state for each subsequent stage.

A complete run utilizes all 5 stages. It is possible to work with any subset of 
the stages.

------------
pre-run (pr)
------------

The pre-run is an equilibrium run for the physical variables of the model. It is
typically 100 years, uses constant climate (typically monthly average computed
from the [1901-1930] period). 


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

.. note:: Automatic equilibrium detection.
   TEM does not have an internal test for whether or not equilibrium has
   been reached. In other words, if you specify ``--max-eq=20000``, the model 
   will run for 20,000 years no matter what internal state it reached. It 
   appears that some of the variable and constant names and the command 
   line flag ``--max-eq`` are vestigial remains of an attempt at "automatic 
   equilibrium detection".

-----------
spinup (sp)
-----------
In the spinup stage, the climate is not fixed. In the sp stage, the driving 
climate is used from the first 30 years of the historic climate dataset. Should 
the spstage be set to run longer than 30 years, the 30 year climate period is 
re-used. Another difference between eq and sp stages is that the sp stage is set 
to run for a fixed number of years, regardless of the internal state that the 
model reaches. In the sp stage the fire date is fixed, occuring at an interval 
equal to the Fire Recurrence Interval (FRI).

--------------
transient (tr)
--------------
In the transient stage, the climate varies from year to year. The tr stage is 
used to run the model over the period of historical record. The input climate 
data for the tr stage should be the historic climate. This is typically the 
climate data for the 20th century, so roughly 1901-2009.

--------------
scenario (sc)
--------------
In the scenario stage, the climate also varies from year to year, but rather
than observed variability, a predicted climate scenario is used.

A complete run utilizes all 5 stages. It is possible to work with any subset of
the stages


=======================
Community Types (CMTs)
=======================
Each TEM grid cell can be assigned one “community type” (CMT). A community 
type is essentially a parameterization that specifies many properties for 
vegetation, and soil.

=======================
Vegetation Types (PFTs)
=======================
    WRITE THIS...

.. raw:: html

   <!-- From Tobey Carman's google drawing "dvmdostem-general-idea-pft"-->
   <img src="https://docs.google.com/drawings/d/14vNsPCuorCy3PuE6ucgAmerAks42SxZCtWr4vV5p4Pg/pub?w=960&amp;h=720">

=======================
Soil (Layers)
=======================
    WRITE THIS...

.. raw:: html

   <!-- From Tobey Carman's google drawing "dvmdostem-general-idea-soil"-->
   <img src="https://docs.google.com/drawings/d/1cGr4b90CHsh98TxpB5_ymMaft1wJ62t1gsWGdBVy6QM/pub?w=820&amp;h=884">

   <!-- From Tobey Carman's google drawing "dvmdostem-soil-detail" -->
   <img src="https://docs.google.com/drawings/d/1TPZNC_DazpOpkxSKkTJ3oMQlLvzBjUaY6DmBW9LR9cY/pub?w=1005&amp;h=746">

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


========
Inputs
========

Generally TEM requires several types of inputs:

* Spatially explicit - varies over spatial dimensions.
    Examples are the topography variables, slope, aspect and elevation, which 
    change for geographic location, but are fixed through time.

* Temporally explicit - varies over time dimension.
    An example (and in fact the only such input for TEM) is atmospheric CO2 
    concentration, which is roughly the same across the globe, but varies 
    over time.

* Temporally and spatially explicit - varies over time and spatial dimensions.
    Examples are climate variables like air temperature and precipitation.

.. raw:: html

    <!-- From Shared Drives/DVM-DOS-TEM Documentation/drawings/input -->
    <img src="https://docs.google.com/drawings/d/e/2PACX-1vRErkgxPAPvzMTDOM-sOOQ3fPjmU4itFQvmklp1Q3-qcdFUnrYkl1B3pqSAtMT2Ze57yKq_IYXy9hTN/pub?w=960&amp;h=720">
 
The ``dvmdostem`` code is neither particularly smart nor picky about the input
files. There is minimal built-in error or validity checking and the program will
happily run with garbage input data or fail to run because of an invalid
attribute or missing input data value. It is up to the user to properly prepare
and validate their input data. There is a :ref:`helper
program<Running_dvmdostem:From ERA5>` specifically for generating inputs from
data provided by `SNAP <http://snap.uaf.edu>`_. This data was prepared as part
of the `Alaska IEM <https://akcasc.org/project/iem-project/>`_ project (more
info `here
<https://uaf-snap.org/project/iem-an-integrated-ecosystem-model-for-alaska-and-northwest-canada/>`_).
It remains an open project to generate input data from another source, e.g.
`ERA5 <https://www.ecmwf.int/en/forecasts/datasets/reanalysis-datasets/era5>`_
or a different soil database, etc. 

Here some things that are generally **assumed** (program will likely run; results will 
likely be invalid) or **expected** (program unlikely to run if condition not met) of 
dvmdostem input files:

* The model **assumes** the dimension order to be (time, Y, X), as per CF Conventions.
* The time axes of the files are **assumed** to align exactly.
* Input file spatial extents are **assumed** to align exactly.
* The model **expects** inputs in NetCDF format.
* The variables names are **expected** to exactly match the names as shown in the 
  table below.

While there is full support for geo-referenced files, this is not a requirement. 
Internally, the model requires the latitude for only a single calculation. 
The geo-referencing information is simply passed along to the output files. It 
is not used internally and is primarily for provenance and to enable pre and post 
processing steps. In the event that the file(s) are projected and or geo-referenced, 
they should contain extra variables and attributes for projection coordinate data, 
unprojected coordinate data, and grid mapping strings.

The complete list of required TEM input variables is shown below.

+--------------------+--------------------+--------------------+--------------------+
| file               | variable name      | dimensions         | units              |
+--------------------+--------------------+--------------------+--------------------+
| run-mask.nc        |                    |                    |                    |
+--------------------+--------------------+--------------------+--------------------+
|                    | run                | Y X                |                    |
+--------------------+--------------------+--------------------+--------------------+
| drainage.nc        |                    |                    |                    |
+--------------------+--------------------+--------------------+--------------------+
|                    | drainage\_class    | Y X                |                    |
+--------------------+--------------------+--------------------+--------------------+
| vegetation.nc      |                    |                    |                    |
+--------------------+--------------------+--------------------+--------------------+
|                    | veg\_class         | Y X                |                    |
+--------------------+--------------------+--------------------+--------------------+
| topo.nc            |                    |                    |                    |
+--------------------+--------------------+--------------------+--------------------+
|                    | slope              | Y X                |                    |
+--------------------+--------------------+--------------------+--------------------+
|                    | aspect             | Y X                |                    |
+--------------------+--------------------+--------------------+--------------------+
|                    | elevation          | Y X                |                    |
+--------------------+--------------------+--------------------+--------------------+
| soil-texture.nc    |                    |                    |                    |
+--------------------+--------------------+--------------------+--------------------+
|                    | pct\_sand          | Y X                |                    |
+--------------------+--------------------+--------------------+--------------------+
|                    | pct\_silt          | Y X                |                    |
+--------------------+--------------------+--------------------+--------------------+
|                    | pct\_clay          | Y X                |                    |
+--------------------+--------------------+--------------------+--------------------+
| co2.nc             |                    |                    |                    |
|                    |                    |                    |                    |
| projected-co2.nc   |                    |                    |                    |
+--------------------+--------------------+--------------------+--------------------+
|                    | co2                | year               |                    |
+--------------------+--------------------+--------------------+--------------------+
| historic-climate.n |                    |                    |                    |
| c                  |                    |                    |                    |
|                    |                    |                    |                    |
| projected-climate. |                    |                    |                    |
| nc                 |                    |                    |                    |
+--------------------+--------------------+--------------------+--------------------+
|                    | tair               | time Y X           | celcius            |
+--------------------+--------------------+--------------------+--------------------+
|                    | precip             | time Y X           | mm month-1         |
+--------------------+--------------------+--------------------+--------------------+
|                    | nirr               | time Y X           | W m-2              |
+--------------------+--------------------+--------------------+--------------------+
|                    | vapor\_press       | time Y X           | hPa                |
+--------------------+--------------------+--------------------+--------------------+
|                    | time               | time               | days since         |
|                    |                    |                    | YYYY-MM-DD         |
|                    |                    |                    | HH:MM:SS           |
+--------------------+--------------------+--------------------+--------------------+
| fri-fire.nc        |                    |                    |                    |
+--------------------+--------------------+--------------------+--------------------+
|                    | fri                | Y X                |                    |
+--------------------+--------------------+--------------------+--------------------+
|                    | fri\_severity      | Y X                |                    |
+--------------------+--------------------+--------------------+--------------------+
|                    | fri\_jday\_of\_bur | Y X                |                    |
|                    | n                  |                    |                    |
+--------------------+--------------------+--------------------+--------------------+
|                    | fri\_area\_of\_bur | Y X                |                    |
|                    | n                  |                    |                    |
+--------------------+--------------------+--------------------+--------------------+
| historic-explicit- |                    |                    |                    |
| fire.nc            |                    |                    |                    |
|                    |                    |                    |                    |
| projected-explicit |                    |                    |                    |
| -fire.nc           |                    |                    |                    |
+--------------------+--------------------+--------------------+--------------------+
|                    | exp\_burn\_mask    |                    |                    |
+--------------------+--------------------+--------------------+--------------------+
|                    | exp\_jday\_of\_bur |                    |                    |
|                    | n                  |                    |                    |
+--------------------+--------------------+--------------------+--------------------+
|                    | exp\_fire\_severit |                    |                    |
|                    | y                  |                    |                    |
+--------------------+--------------------+--------------------+--------------------+
|                    | exp\_area\_of\_bur |                    |                    |
|                    | n                  |                    |                    |
+--------------------+--------------------+--------------------+--------------------+
|                    | time               | time               | days since         |
|                    |                    |                    | YYYY-MM-DD         |
|                    |                    |                    | HH:MM:SS           |
+--------------------+--------------------+--------------------+--------------------+

.. note:: Example code to generate the above table.

    .. code-block:: python
       
        import os; import netCDF4 as nc
        indir_path = "demo-data/cru-ts40_ar5_rcp85_ncar-ccsm4_toolik_field_station_10x10"
        for f in filter(lambda x: '.nc' in x, os.listdir(indir_path)):
            ds = nc.Dataset(os.path.join(indir_path, f))
            print(f)
            for vname, info  in ds.variables.items():
                if 'units' in info.ncattrs():
                    us = info.units
                else:
                    us = ''
                print("  {:25s},{:15s},{:25s}".format( vname, ' '.join(info.dimensions),us))



==========
Outputs
==========
    WRITE THIS...

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

