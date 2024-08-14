.. # with overline, for parts
   * with overline, for chapters
   =, for sections
   -, for subsections
   ^, for subsubsections
   ", for paragraphs

####################
Manual Calibration
####################

***************************************
What is calibration for ``dvmdostem``?
***************************************

    Calibration is defined as the estimation and adjustment of model parameters
    and constants to improve the agreement between model output and a data set.
    [Rykiel_1996]_

Being originally a biogeochemical model, ``dvmdostem`` calibration is mainly
focused on the carbon (C) and nitrogen (N) cycle. Rate-limiting parameters for
various processes are adjusted until model values of C and N fluxes and stocks
match field-based estimates or observations, which we refer to as "target
values". Below is a table of variables or processes and their corresponding rate
limiting parameters:

=================================  ==============================================
Gross Primary Productivity (GPP)   Cmax
Autotrophic Respiration (Ra)       Kr
Heterotrophic Respiration (Rh)     Kd
maximum plant N uptake             Nmax
C and N litter production          Cfall, Nfall
soil C and N immobilization        micbnup, kdcrawc, kdscoma, kdcsomapr, kdcsomcr
=================================  ==============================================

For this reason, calibrations are conducted at the site level, using sentinel 
sites representing typical mature ecosystems, well characterized and monitored
over long periods of time.

The selection of parameters for calibration is based on:

  1. The sensitivity of the model carbon and nitrogen stocks and fluxes to these
     parameters. 
  2. The uncertainty of the parameter values.

.. raw:: html

   <!-- From google drawing: TEM UAF Only Records > Documentation Embed Images > calibration_schematic -->
   <img src="https://docs.google.com/drawings/d/e/2PACX-1vRSmEzkC53GiG8p7xrtPbvFnjOxkKcDaIJjiWb4d9JSi3Oqz9dfGDf5G4rJyTkWrVcVoW0uD8imkJJQ/pub?w=449&amp;h=249">


******************************
When to conduct a calibration?
******************************
Calibrations are typically conducted for every vegetation community type the
model is parameterized for. However, recent studies have shown that parameter
uncertainty may not only vary between community type, but also in space within
the same community type [Euskirchen_2021]_. Therefore, multiple
calibrations can be developed for the same community type but different
eco-climatic regions.

*****************************
How to conduct a calibration?
*****************************
The comparison between model outputs and target values are done at equilibrium,
i.e. a simulation under constant environment (climate, atmospheric CO2, and
vegetation), when all fluxes and stocks have reach a steady state.

Calibration targets
===================
As mentioned above, target values are based on field observations for the main
carbon and nitrogen fluxes and stocks targeted for the calibration. Target
values are representing the “typical” state of a mature ecosystem for the
vegetation community for which the calibration is developed.

For this reason, as often as possible, target values are computed from
observations collected across multiple years, at the sentinel site where the
calibration is developed. In this case, a target value will be computed as the
mean of a multi-year time series. The standard deviation is also important to
compute and store as it can inform a subsequent uncertainty analysis at the
sentinel site.

Target values are stored in the text file named `calibration_targets.py` in the
calibration directory.

Vegetation Targets
------------------

**INGPP, INNPP** are target values for gross and net primary productivity
reached by vegetation not limited by nutrient availability. These target values
are typically assessed from fertilization experiments. When fertilization
experiment is not available at the sentinel site where calibration is developed,
fertilization factor can be calculated from literature review of fertilization
experiment in similar ecosystem. This fertilization factor is computed as the
ratio between GPP or NPP in control and fertilized plots. These two variables
should have target values for every PFT.

**GPP, NPP** are target values for gross and net primary productivity reached by
mature vegetation under natural conditions. When data is available, these target
values are averaged across multi-year observations. These two variables should
have target values for every PFT. Partitioning between PFT can be done based on
aboveground NPP estimated from biomass quantification.

**NUPTAKE** is the rate of nitrogen uptake by the vegetation. As for the
carbon fluxes, this flux should be partitioned by plant functional type. This
target value is usually set from literature review.

**VEGC** is the target value for vegetation carbon pools. VEGC should be
indicated for every compartment (i.e. leaf, stem, and root) of every plant
functional type. Target values are based on biomass estimations. If biomass
estimates are not available for all compartments (e.g. root) or all PFT (e.g.
green mosses), partitioning information should be estimated from literature
review.

**VEGN** is the target value for vegetation nitrogen pools. VEGN should be
indicated for every compartment (i.e. leaf, stem, and root) of every plant
functional type. Target values are based on biomass estimations and C:N ratios.
If biomass or C:N estimates are not available for all compartments (e.g. root)
or all PFT (e.g. green mosses), partitioning information should be estimated
from literature review.

Soil Targets
------------

**SOILC** is the target value for soil carbon pools. It is estimated separately
for the fibric layer, the humic layer and the top 1 meter of the mineral layer.

**ORGN** is the target value of the soil nitrogen pool. In contract to SOILC,
ORGN is estimated for the organic layer *and* the top 1 meter mineral soil. It 
is usually estimated from the soil carbons pools and estimated C:N ratios.

**AVLN** is the target value for soil available nitrogen. By definition, this
pool is estimated across the rooting depth only (indicated in the parameter file
cmt\_dimvegetation.txt).


Calibration parameters 
======================

Calibrated parameters are stored in the text file named `cmt\_calparbgc.txt` in
the parameter directory.

Vegetation parameters
---------------------

**Cmax** is the maximum rate of carbon assimilation. It is defined by plant
functional type. Maximum assimilation is reached when plants are exposed to no
significant limitation in nutrient availability. For this reason, Cmax is
calibrated with nitrogen feedback off. Cmax is adjusted so that model GPP is
equal to observed GPP estimates from fertilization experiments. When
fertilization experiments are not available for the community/region of
interest, it is estimated by applying a multiplicative factor to observed GPP in
control (not manipulated) plots. Based on literature, this fertilization factor
can vary from 1.25 to 1.5.

**Kr** is the limiting rate of maintenance respiration (Rm) at :math:`0^oC`:

.. math:: Rm = Kr * VEGC 
  
where VEGC is vegetation carbon pool. Kr is itself a function of vegetation
carbon pool: 

.. math:: Kr = e^{(Kr_a * VEGC) + Kr_b}

.. Alternate formulation...
.. .. math:: Kr = \exp{([Kr_a * VEGC] + Kr_b)}

:math:`Kr_a` is usually set to :math:`-8.06e10^5`, and :math:`Kr_b` is
calibrated for every vegetation compartment: leaf, stem and root. Because the
relationship between biomass and maintenance respiration is not linear and
decreases as biomass increases, :math:`Kr_b` should be negative.

**Cfall** is the limiting rate of carbon litterfall (Cltr): 

.. math:: Cltr = Cfall * VEGC 
  
where VEGC is the vegetation carbon pool. Cfall is calibrated for every
vegetation compartment: leaf, stem and root.

**Nmax** is the maximum rate of plant nitrogen uptake. Maximum vegetation
nitrogen uptake is reached when plants productivity is at its maximum, and there
are no significant limitation from low temperature.

**Nfall** is the limiting rate of nitrogen litterfall (Nltr):

.. math:: Nltr = Nfall * VEGN

where VEGN is the vegetation nitrogen pool. Nfall is calibrated for every
vegetation compartment: leaf, stem and root.

Soil parameters
---------------

.. **:math:`Nup_{mic}`** reStructuredText can't do super/sub inside bold.

:math:`Nup_{mic}` is the limiting rate of microbial nitrogen uptake per unit of
detrital carbon respired (g/g). :math:`Nup_{mic}` directly influences nitrogen
immobilization by decomposers, and net mineralization which is the amount of
inorganic nitrogen produced during the decomposition of the soil organic matter
minus that immobilized by decomposers.

**Kdc** is the limiting rate of soil carbon decomposition. Kdc is calibrated for
the four soil carbon pools: litter/raw pool, active, physically and chemically
resistant pools. The higher the value of this rate is, the faster the turnover
is. Therefore:

.. math:: Kdc_{raw} > Kdc_{active} > Kdc_{pr} > Kdc_{cr} 

**********************
Calibration Process
**********************

Calibration is done in equilibrium simulation and in calibration mode. Because
biogeochemical turn-overs in the vegetation are faster than in the soil,
vegetation-related variables reach equilibrium sooner than soil-related
variables. Therefore, the length of the equilibrium run can be set to shorter
time when vegetation-related parameters are calibrated (e.g. 200 to 500 years),
whereas soil calibration typically requires several thousand years to reach
equilibrium.

Calibrate vegetation parameters **without** N limitation
========================================================
#. Set ``NFEED=OFF`` and ``AVLN=OFF``.

#. Adjust Cmax until INGPP (GPP without N limitation) matches target for every
   plant functional type. Increasing Cmax increases GPP.

Calibrate vegetation parameters **with** N limitation
=====================================================

#. Set ``NFEED=ON`` and ``AVLN=ON``.

#. Set the level of N limitation with Nmax and Nup\ :sub:`mic` so that actual
   GPP, and AVLN match the target values. Increasing Nmax should increase GPP,
   and increasing Nup\ :sub:`mic` should decrease both GPP and AVLN.

#. Set the ratio between GPP and NPP with Krb. Krb influences maintenance
   respiration, and it will also affect the ratio between GPP and NPP.
   Increasing Krb will increase respiration and decrease NPP. Krb should 
   therefore be calibrated targeting NPP.

#. Calibrate Cfall targeting VEGC. Change in vegetation is a result of NPP
   (input) and Litterfall (output). Therefore, VEGC pools will be influenced
   both by Krb and Cfall parameters. Because Krb has been adjusted in step 3,
   the focus here should be on adjusting Cfall with minimal adjustment to Krb.

#. Calibrate Nfall targeting VEGN. Vegetation nitrogen pool is a result of
   vegetation nitrogen uptake (input) and litterfall (output).

Calibrate soil parameters
=========================

#. Calibrate decomposition rate limiting parameters targeting soil carbon
   stocks. The fibric layer is dominated by raw and active carbon pools. The
   humic layer is dominated by active and physically resistant pools. Finally,
   the mineral layer is dominated by pools of slower turnover. Therefore, Kdc 
   for the raw material should be adjusted targeting soil C stock in the fibric
   layer. Kdc for the active organic matter will affect primarily fibric and
   humic carbon pools. Kdc for the physically resistant pool will affect
   primarily the humic and mineral pools.

***********
Reference
***********

.. [Euskirchen_2021] Euskirchen, Eugénie S. et al. 2021 Assessing dynamic
 vegetation model parameter uncertainty across Alaskan arctic tundra plant
 communities. *Ecological Applications* 32 : n. pag.

.. [Rykiel_1996] Rykiel, E. J., Jr. 1996. Testing ecological models: the meaning
 of validation. *Ecological Modeling*, 90: 229–244. https://doi.org/10.1016/0304-3800(95)00152-2