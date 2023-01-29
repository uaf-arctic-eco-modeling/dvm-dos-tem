.. # with overline, for parts
   * with overline, for chapters
   =, for sections
   -, for subsections
   ^, for subsubsections
   ", for paragraphs


#######################################
EE 0 - Single Site Run
#######################################

Example Experiment 0: We want to conduct a full single-site simulation, explore
the output data and produce preliminary plots.

The examples assume that you are running on the ``dvmdostem`` Docker stack.

***********************
Design Specification
***********************

Here we have designed a small experiment with answers to the unknowns posed in
:ref:`setting up a run <examples_and_tutorials/basic_model_run:setting up a dvmdostem run>`

#. Decide where on your computer you want to store your model run(s).

    - ``/data/workflows/exp0_jan26_test``

#. Decide what spatial (geographic) area you want to run.

    - Toolik, use ??? dataset pixels: (0,0), (1,1), (2,2)

#. Decide what variables you want to have output.

   - GPP: monthly, by PFT
   - RH, RA, RG, RM: monthly
   - TLAYER: monthly by layer
   - VEGC: yearly
   - ALD: yearly
   - SOMA: yearly
   - CMTNUM: yearly

#. Decide on all other run settings/parameters:

   * Which stages to run and for how many years.

      - all stages, pr 100, eq 1000, sp 250, tr 115, sc 85

   * Is the community type (CMT) fixed or driven by input vegetation.nc map?

      - no, forcing to 5

   * For which stages should the output files be generated and saved?

      - sp, tr, sc

   * Calibration settings if necessary (``--cal-mode``).

      - no

   * Any other command line options or environment settings.

      - no

.. collapse:: solution other

   .. code:: 

      $ ./scripts/setup_working_directory.py --input-data-path /data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_TOOLIK_FIELD_STATION_10x10 /data/workflows/exp0_jan26_test
      $ cd /data/workflows/exp0_jan26_test/
      $ outspec_utils.py config/output_spec.csv --on RH m
      $ outspec_utils.py config/output_spec.csv --on RA m
      $ outspec_utils.py config/output_spec.csv --on RG m
      $ outspec_utils.py config/output_spec.csv --on RM m
      $ outspec_utils.py config/output_spec.csv --on TLAYER l m
      $ outspec_utils.py config/output_spec.csv --on GPP m p
      $ outspec_utils.py config/output_spec.csv --on VEGC y
      $ outspec_utils.py config/output_spec.csv --on ALD y
      $ outspec_utils.py config/output_spec.csv --on SOMA y
      $ outspec_utils.py config/output_spec.csv --on CMTNUM y
      $ runmask-util.py --reset run-mask.nc 
      $ runmask-util.py --on 0 0  run-mask.nc 
      $ runmask-util.py --yx 0 0  run-mask.nc 
      $ runmask-util.py --yx 1 1  run-mask.nc 
      $ runmask-util.py --yx 2 2  run-mask.nc 
      $ dvmdostem --force-cmt 5 -p 100 -s 250 -e 1000 -t 115 -n 85




**************************
Explore inputs 
**************************

Exploring the input dataset, determine the start year of the historical, and the
projected climate time series. From the length of the time dimension, compute
the end year and the total number of years of the time series. Note that this
information is used to set the number of transient and scenario years to run.

.. collapse:: solution

   .. code:: 

      $ ncdump -h /data/input-catalog/cru-ts40_ar5_rcp85_ncar-ccsm4_TOOLIK_FIELD_STATION_10x10/historic-climate.nc  | grep time:units

**************************
Computing Means
**************************

Compute the mean vegetation and soil carbon stocks for the following decades:
[1990-2010], [2040-2050], [2090-2100].

   a. What are the units of these stocks?

.. collapse:: solution

   .. code:: 

      Find these...
      Stocks                 [1990-2010] [2040-2050] [2090-2100]
              Vegetation
      
                  Fibric
         Soil      Humic
                 Mineral

                   Total


****************************
Computing Monthly NEE
****************************

Compute monthly Net Ecosystem Exchange (NEE) for the historical and scenario
simulations. Indicate how you formulated NEE.



****************************
Computing mean GPP
****************************

Compute the mean GPP, autotrophic and heterotrophic respirations and NEE for the
following decades: [1990-2010], [2040-2050], [2090-2100].

   a. What are the units of these fluxes?

.. collapse:: solution 

   .. code::

      Fluxes                         [1990-2010]    [2040-2050]    [2090-2100]

      GPP
      Autotrophic respiration
      Heterotrophic respiration
      Net Ecosystem Exchange


*******************************************
Plot Active Later Depth
*******************************************

Plot the active layer depth from 1950 to 2100.

.. collapse:: solution

   Write this...

******************************
Plot seasonal dynamic
******************************

Plot the seasonal dynamic of GPP for the same three decades: [1990-2010],
[2040-2050], [2090-2100]. The plot should show the mean monthly GPP computed
across each decade as lines, and the standard deviation across the mean as
envelopes.

.. collapse:: solution

   Write this...

*****************************
Plot soil temperatures
*****************************

Plot the soil temperature profile for [June-July-August] period for the same
three years: 1990, 2040, 2090. The plot should show the mean summer temperature
computed across each decade as lines, and the standard deviation across the mean
as envelops.

.. collapse:: solution

   Write this...
