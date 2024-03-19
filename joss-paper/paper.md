---
title: 'DVMDOSTEM: A terrestrial biosphere model focused on Arctic vegetation and soil dynamics'
tags:
  - C++
  - Python
  - ecology
  - permafrost
  - vegetation dynamics
  - soil thermal dynamics
  - Arctic
  - carbon cycle

authors:
  - name: Tobey B Carman
    corresponding: true
    equal-contrib: true
    affiliation: 1
  - name: Ruth A Rutter
    equal-contrib: true
    affiliation: 1
  - name: Helene Genet
    equal-contrib: true
    affiliation: 1
  - name: Eugenie Euskirchen
    equal-contrib: true
    affiliation: 1
  - name: Elchin Jafarov
    equal-contrib: true
    affiliation: 2
  - name: Ben Maglio
    affiliation: 1
  - name: Joy Clein
    affiliation: 1
  - name: Valeria Briones
    affiliation: 2
  - name: Andrew Mullen
    affiliation: 1
  - name: Aiza Kaber
    affiliation: 2

affiliations:
  - name: Institute of Arctic Biology, University of Alaska Fairbanks
    index: 1
  - name: Woodwell Climate Research Center
    index: 2
date: 13 September 2023
bibliography: paper.bib
---

# Summary

Questions about the evolution of ecosystems under a changing climate are
pressing in many fields. Terrestrial Biosphere Models (TBMs) seek to answer
questions about changing ecosystems at a scale between the Global
Circulation Models and smaller point or process specific models. The ``DVMDOSTEM``
model is a TBM focused on C and N cycling through vegetation and soil as well as
soil thermal dynamics. 

``DVMDOSTEM`` is an advanced ecological process model tailored to capture the intricacies of vegetation and soil thermal dynamics for multiple vegeation types and multiple soil layers. Designed to study ecosystem responses to climate changes and disturbances, it has a particular focus on boreal, arctic, and alpine landscapes. The model integrates vegetation dynamics (DVM) and soil biogeochemistry (DOS) to simulate processes on monthly and yearly scales, with some components operating at an even finer granularity. Its versatility allows for site-specific to regional simulations, making it valuable for predicting shifts in permafrost, vegetation, and carbon dynamics.

The ``DVMDOSTEM`` model has thus far been primarlily used for high latitude ecosystems, but with work put into the parameterizations, it could be used elsewhere.

# Statement of need

The permafrost regions, repositories of a colossal 1,440-1,600 Pg of organic carbon in soils, embody nearly half of the world’s soil organic carbon pool, underpinning the global climate system (Hugelius et al., 2014; Schuur et al., 2022). Arctic warming is catalyzing permafrost thaw and leading to the accelerated decomposition and release of a substantial portion of the soil-stored carbon as greenhouse gases which will exert formidable pressure on global climate dynamics (Schuur et al., 2022; Natali et al., 2021; Treharne et al., 2022). 

An imperative demand exists to utilize models that integrate cryo-hydrological processes with ecosystem carbon cycling and to explore the uncertainties of modeling the permafrost carbon feedback.

The evolution and refinement of ``DVMDOSTEM`` (Dynamic Vegetation, Dynamic Organic Soil Terrestrial Ecosystem Model) has been shaped by extensive research and application, marked by a strong focus on simulating biophysical and biogeochemical interactions amongst the soil, vegetation, and atmosphere, particularly in high-latitude ecosystems. Developed to encapsulate carbon and nitrogen cycles, as influenced by a myriad of factors ranging from climatic variables and disturbances, to varied biophysical processes, the model's trajectory of development has offered nuanced insights into these complex interplays across both seasonal and centennial scales (Genet et al., 2013, 2018). This model is designed to incorporate the necessary physics to study carbon cycling in frozen ground.

The model has a long history of application in both Arctic and Boreal ecosystems across permafrost and non-permafrost regions, reinforcing its capability and reliability in studying and simulating complex ecosystem dynamics (Genet et al., 2013; Jafarov et al., 2013; Yi et al., 2010, 2009; Euskirchen et al., 2022). 


# Model Design

``DVMDOSTEM`` is a process-based biosphere model designed to simulate biophysical and biogeochemical processes between the soil, the vegetation and the atmosphere. The model is spatially explicit and focuses on representing carbon and nitrogen cycles in high latitude ecosystems and how they are affected at seasonal (i.e. monthly) to centennial scales by climate, disturbances and biophysical processes such as permafrost, soil thermal and hydrological regimes, snow cover or canopy development.

Conceptually there are four core groups of processes in ``DVMDOSTEM`` that act upon the structure of the model:  

 - vegetation growth (and death), 
 - soil thermal and hydrologic changes, 
 - soil C and N fluxes, and 
 - alteration of the vegetation and or soil structure (disturbance). 

The processes are linked because the C and N pools of the vegetation exist both on top of and in the soil column. Properties of the soil thermal environment are used to govern the C and N fluxes associated with vegetation growth (and death), thereby changing the C and N pools that exist in, and on top of the soil column. Properties of the vegetation are used to influence the soil thermal and hydrologic regeimes. 

Each site, (grid cell, or pixel) that the model simulates is represented by the soil and vegetation structure described here. Running a simulation consists of stepping this structure through the processes for a series of timesteps.

## Soil structure and processes

The soil column is modeled as a series of layers. The number, and type of layers may change throughout the simulation based on vegeation, thermal, and hydrologic properties that are calculated at each time step (Zhuang et al., 2002; Euskirchen et al., 2006, 2014; Yi et al., 2009; McGuire et al., 2018). The model uses the two-directional Stefan Algorithm and the Richards equation, to predict freezing/thawing fronts, and soil moisture changes in the unfrozen layers respectively (Yi et al., 2009, 2010; Zhuang et al., 2002). The intrinsic links between thermal and hydraulic properties of soil layers and their water content further shaped ``DVMDOSTEM``’s functionality and application, ensuring a holistic representation of underlying ecological processes, including carbon and nitrogen dynamics across the vegetation community and each layer of the soil column, driven by climate, atmospheric chemistry, soil and canopy environment, and wildfire occurrences. 

## Vegetation structure and processes

The vegetation is modeled using a detailed structure that can consider up to ten distinct vegetation types (plant functional types or PFTs), each of which may have up to three compartments: leaf, stem, and root. Vegetation C and N fluxes are calcluated at each time step based on environmental factors, and soil properties.

<!-- Exported from UAF Shared Drive > Documentation Embed Images > "dvmdostem-overview" Google Drawing -->
![Overview of ``DVMDOSTEM`` soil and vegetation structure. On the left is the soil structure showing the layers, and different properties that are tracked (purple bubble; Carbon, Nitrogen, Temperature, Volumetric Water Content, Ice). Each of the layers with properties described above, is also categorized as Organic (fibric or humic) or Mineral (shallow or deep). Additionally the model simulates snow layers and the removal of layers due to processes such as fire.  On the right is the vegetation structure showing the Plant Functional Types (PFTs) and the associated pools and fluxes of Carbon and Nitrogen. Each PFT is split into compartments (Leaf, Stem and Root) which track their own C and N content and associated fluxes. The fluxes are represented with red text while the pools are black. In addition there is competition among the PFTs shown with the purple arrow in the top center.\label{fig:soil_veg_structure}](figures/dvmdostem-overview-export_2023-12-20.png)


## Run stages

``DVMDOSTEM`` is a temporal model in the sense that a run operates processes at consecutive time-steps. In addition, with ``DVMDOSTEM``, the concept of a “run stage” is used to run the model over different climatic periods of generally increasing complexity. There are 5 possible “run stages”:

 * Pre-run (pr)
 * Equilibrium (eq)
 * Spinup (sp)
 * Transient (tr)
 * Scenario (sc)

The primary difference between the run stages is the nature of the input climate dataset, and specifically whether there is annual variability in the driving climate data that the model uses. A complete, future-projecting, simulation is usually only made after advancing the model through several of the previous run stages to stabilize the system. Typically the ending state from each stage is used as the beginning state for each subsequent stage. A complete run utilizes all 5 stages. It is possible to work with any subset of the stages.


## Spatial considerations

When considered regionally, ``DVMDOSTEM`` uses the concept of a grid cell. The spatial domain is broken into grid cells, each of which contains the model structure for that point. Each grid cell is driven to a different state as a result of the input values that are used for that grid cell. A land cover map is used to classify each grid cell, and the classifications have different assembleages of PFTs and different soil properties as well as different driving climates, soil parameterizations, disturbance charachteristics, and topography. There is not communication between grid cells and the grid cell classification is currently fixed throughout the simulation although there is active reserarch interest in being able to modifiy the land cover classification during a simulation {ref?}.

<!-- Exported from Tobey Carman's Google Drawing "dvmdostem-general-idea-science"-->
![Overview of ``DVMDOSTEM`` spatial structure. ``DVMDOSTEM`` is a process based spatially explicit model.\label{fig:structural_overview}](figures/dvmdostem-general-idea-science-export_2023-10-09.jpg)

## Inputs and outputs

``DVMDOSTEM`` uses NetCDF files for both inputs and outputs. The input variables that are used to drive ``DVMDOSTEM`` are: drainage classification, vegetation classification, topographic (slope, aspect, elevation), soil texture, atmospheric co2 concentration, four climate variables (air temperature, precipitation, vapor pressure, and incoming shortwave radiation), atmospheric $CO_2$ concentration, and fire classification.

The $CO_2$, climate and fire include a temporal dimension, while the others do not. The $CO_2$ driving input must be yearly resolution, and the climate and fire must be monthly resolution.

The output files that ``DVMDOSTEM`` produces are also NetCDF format and attempt to conform with the CF Conventions {verison?} {ref?}. There is one output file per variable and various resolutions available depending on the variable. Many soil output can be requested by layer, and many vegetation outputs can be requested by PFT and even compartment.

# Summary of Mathematics

The fundamental equations include carbon cycling, surface and subsurface energy balance, and hydrology. In addition to these equations, the model includes the dynamics of the organic layer and fire disturbance processes. 

## Carbon Cycling:

1. **Net Primary Production (NPP):**
   $$NPP = GPP - R_a$$
   where $GPP$ is Gross Primary Production, and $R_a$ is autotrophic respiration.

2. **Net Ecosystem Exchange (NEE):**
   $$NEE = NPP - R_h$$
   where $R_h$ is heterotrophic respiration.

3. **Carbon Stock Change:**
   $$\Delta C = \text{Input} - (\text{Decomposition} + \text{Leaching})$$

## Permafrost Energy Balance:

1. **Conductive Heat Flux:**
   $$Q = -k \cdot \frac{\Delta T}{\Delta z}$$
   where $k$ is thermal conductivity, $\Delta T$ is the temperature gradient, and $\Delta z$ is the thickness of the soil layer.

2. **Ground Heat Flux:**
   $$G = (1 - \alpha) \cdot SW_{\downarrow} + LW_{\downarrow} - LW_{\uparrow} - H - LE$$
   where $\alpha$ is albedo, $SW_{\downarrow}$ is downward shortwave radiation, $LW_{\downarrow}$ is downward longwave radiation, $LW_{\uparrow}$ is upward longwave radiation, $H$ is sensible heat flux, and $LE$ is latent heat flux.

## Hydrology:

1. **Water Balance Equation:**
   $$P = Q + ET + \Delta S$$
   where $P$ is precipitation, $Q$ is runoff, $ET$ is evapotranspiration, and $\Delta S$ is change in storage.

2. **Darcy’s Law (Water Flow):**
   $$Q = -k \cdot A \cdot \frac{\Delta h}{\Delta l}$$
   where $Q$ is the flow rate, $k$ is the hydraulic conductivity, $A$ is the cross-sectional area, $\Delta h$ is the head loss, and $\Delta l$ is the length of the pathway.

3. **Richards Equation (Unsaturated Water Flow):**
   $$\frac{\partial \theta}{\partial t} = \nabla \cdot [K(\theta) \cdot \nabla h] + S(\theta)$$
   where $\theta$ is the volumetric water content, $t$ is time, $K(\theta)$ is the hydraulic conductivity as a function of $\theta$, $h$ is the matric potential, and $S(\theta)$ is a source/sink term.

.. note::

  NEED TO ADD Stephan equation? referenced in soil structure section above...

<!-- Single dollars ($) are required for inline mathematics e.g. $f(x) = e^{\pi/x}$

Double dollars make self-standing equations:

$$\Theta(x) = \left\{\begin{array}{l}
0\textrm{ if } x < 0\cr
1\textrm{ else}
\end{array}\right.$$

You can also use plain \LaTeX for equations
\begin{equation}\label{eq:fourier}
\hat f(\omega) = \int_{-\infty}^{\infty} f(x) e^{i\omega x} dx
\end{equation}
and refer to \autoref{eq:fourier} from text. -->

# Software Design

While the core ``DVMDOSTEM`` executable is a stand alone compiled C++ program, the ``dvm-dos-tem`` Git repository includes the source code for the main model executable and a wide variety of supporting tooling including various scripts that help with analyses, input/output processing, the documentation system, and the container system.

The ``DVMDOSTEM`` C++ core stands by itself as the embodiment of the model described in \autoref{heading:Model Design},  but it would be difficult to use ``DVMDOSTEM`` without the surrounding tooling that ships with the repository.

## Target User

``DVMDOSTEM`` is designed primarly for a "developer user". In other words there is not (currently) a meaningful way to use most of the tools in the repository without familiarity with the basics of a software development workflow centered around using the Git version control system, and to a lesser extent the Docker {ref?} container system.

Following is a description of the major pieces of the ``dvm-dos-tem`` repostitory. More complete and up-to-date documentation for the project can be found here: http://uaf-arctic-eco-modeling.github.io/dvm-dos-tem/.


## C++ model core

The C++ code is kept in the ``src/`` directory, and headers are in the ``include/`` directory. There is a Makefile with the project. The final executable is linked against dependencies for NetCDF {ref?}, several Boost {ref?} libraries, a json parsing library and the lapacke linear algebra solver {ref?}. Parallelism is achievd using a combination of MPI, a parallel file system, the parallel NetCDF library and scripts that can split and merge a single larger run into batches. The C++ code employs some object oriented concepts but encapsulation and compartmentalization could be improved.

## Documentation

The public facing documentation (published on the web) is maintained using the Python Sphinx {ref?} tool. The project's narrative documentaton is managed with Sphinx as well as the auto-generated documentaton for the Python tooling. Some documentation for the C++ model core can be auto-generated using the Doxygen {ref?} tool. The Doxygen outputs are not published.

## Container system

The project is using Docker {ref?} containers to compartmentalize build and running environments. This is achieved using Docker's volume mounts which enable sharing host system folders with guest containers. Each user is then free to organize files as they wish on their host system, but paths and software within the containers are standarized. The project's Docker files specify containers for building, running and supporing ``dvmdostem`` as well as a Docker Compose {ref?} file that can start containers using standard volume mounts for the project.
 
## Auxiliary scripts

The project ``scripts`` directory is a catch all for the various interperted language tools that researchers have built over the project history. The majority of the auxiliary scripts are written in Python. There are scripts for the following major tasks:

 - diagnostics (assesing "closure" of the C balance),
 - input and output processing,
 - calibration,
   - manual, and 
   - MADS assisted,

with the MADS assisted calibration being the most developed.

### Diagnostics

Write this...


### I/O

Write this...

### Calibration

Calibration is the process of adjusting model parameters such that there is acceptable agreement between measured field data and model predicitons (outputs). Due to the large number and non-linear nature of parameters available with ``DVMDOSTEM`` calibration is a significant hurdle.

#### Manual Calibration

The manual calibration process relies on an expert user to run ``DVMDOSTEM`` with special settings that allow for control and adjustment of the model during run-time in response to the user's assessment of the model outputs and behavior. In this mode ``DVMDOSTEM`` produces additional outputs in ``.json`` format that shadow the NetCDF outputs. The ``.json`` outputs are used by a dynamic plotting program that updates as new data becomes available. The user then stops the model, turns settings on/off, and adjustst parameters until they achieve the desired agreement between model outputs and target values. The graphical plotting program is named ``calibration_viewer.py`` and uses ``matplotlib`` {ref?} to build and display the interactive plot.

#### MADS Assisted Calibration

The MADS assisted calibration uses numerical methods to help find optimum parameter values. The proccess is not fully automated and requires a skilled operator to carry out the steps and interpert the results. However using the numerical methods provides a much more organized and repeatable way to explore the parameter space.

The MADS assisted calibration begins with a sensitivity analysis to find the most important parameters and is followed by an optimization step which used the MADS {ref?} library to optimize parameters. 

The sensitivity analysis samples from the parameter space and carries out many runs with modifications to the parameters from across the parameter space. Then outputs are analyzed to look for parameters that have the most impact on model outputs. The user is then able to choose a more appropriate range for the parameter space that is fed to the optimiaiton step.

The optimizaitn step, with the MADS library, is using levenberg marquart gradient descent {ref?} to find parameters that result in model outputs most closely agreeing with the target values.

Due to the number of parameters and the entangled nature of the processes implemented in ``DVMDOSTEM``, we have had the most luck with interatively engaging in the calibration process (sensitivity analysis followed by optimizaiton) for different combination of variables.

Tools to assist this process exist in the ``scripts/drivers``, ``scripts/util``, and ``mads_calibration`` directories.

# Demonstration

Assuming you have downloaded/cloned the repo and you have built docker images, then you should be able to run the following:

    $ dvmdostem --log-level err -p 10 -e 100 -s 200 -t 115 -n 85

And end up with the following files in your output directory:

    $ ls output/

From which you should be able to make the following plot (basic timeseries of GPP):


![Timeseries of historic and projected GPP for a single pixel of the demonstration data shipped with the codebase. Toolik Lake Alaska. \label{fig:some image}](figures/create_this_image.jpg)


# Acknowledgements
 * WCRC
 * UAF
 * NGEE?
 * DOE project

# Citations

<!-- Citations to entries in paper.bib should be in
[rMarkdown](http://rmarkdown.rstudio.com/authoring_bibliographies_and_citations.html)
format.

If you want to cite a software repository URL (e.g. something on GitHub without a preferred
citation) then you can do it with the example BibTeX entry below for @fidgit.

For a quick reference, the following citation commands can be used:
- `@author:2001`  ->  "Author et al. (2001)"
- `[@author:2001]` -> "(Author et al., 2001)"
- `[@author1:2001; @author2:2001]` -> "(Author1 et al., 2001; Author2 et al., 2002)" -->



<!-- Figures can be included like this:
![Caption for example figure.\label{fig:example}](figure.png)

and referenced from text using \autoref{fig:example}.

Figure sizes can be customized by adding an optional second parameter:
![Caption for example figure.](figure.png){ width=20% } -->


