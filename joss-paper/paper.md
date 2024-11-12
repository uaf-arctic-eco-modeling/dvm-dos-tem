---
title: 'DVMDOSTEM: a terrestrial ecosystem model designed to represent arctic, boreal and permafrost ecosystem dynamics'
tags:
  - C++
  - Python
  - ecology
  - cryosphere
  - biogeochemistry
  - permafrost
  - vegetation dynamics
  - soil thermal dynamics
  - soil hydrological dynamics
  - Arctic
  - Boreal
  - terrestrial carbon cycle

authors:
  - name: Tobey B Carman
    email: tcarman2@alaska.edu
    affiliation: '1'
    orcid: 0000-0003-4617-4674
    corresponding: true
    equal-contrib: true

  - name: Hélène Genet
    email: hgenet@alaska.edu
    affiliation: '1'
    oricid: 0000-0003-4537-9563
    equal-contrib: true
  
  - name: Ruth A Rutter
    email: rarutter@alaska.edu
    affiliation: '1'
    oricid: 0009-0009-7043-6081
  
  - name: Elchin Jafarov
    email: ejafarov@woodwellclimate.org
    affiliation: '2'
    oricid: 0000-0002-8310-3261
  
  - name: Eugénie Euskirchen
    email: seeuskirchen@alaska.edu
    affiliation: '1'
    oricid: 0000-0002-0848-4295
  
  - name: Ben Maglio
    email: bmaglio@alaska.edu
    affiliation: '1'
    oricid: 0000-0002-1948-0177 
  
  - name: Joy Clein
    email: jsclein@alaska.edu
    affiliation: '1'
    oricid: 0000-0002-2816-5312
  
  - name: Valeria Briones
    email: vbriones@woodwellclimate.org
    affiliation: '2'
    oricid: 0000-0002-5649-851X
  
  - name: Andrew L Mullen
    email: amullen@woodwellclimate.org
    affiliation: '2'
    oricid: 0000-0002-9127-9996
  
  - name: Heather Greaves
    email: hegreaves@alaska.edu
    affiliation: '1'
    oricid: 0000-0002-8800-019X
  
  - name: A. D. McGuire
    email: admcguire@alaska.edu
    affiliation: '1'
    oricid: 0000-0003-4646-0750
  
  - name: Fengming Yuan
    email: yuanf@ornl.gov
    affiliation: '3'
    oricid: 0000-0003-0910-5231
  
  - name: Chu-Chun Chang
    email: cchang@woodwellclimate.org
    affiliation: '2'
    oricid: 0000-0002-2971-2349
  
  - name: Joshua M. Rady
    email: jrady@woodwellclimate.org
    affiliation: '2'
    oricid: 0000-0002-7806-136X
  
  - name: Doğukan Teber
    email: dteber@woodwellclimate.org
    affiliation: '2'
    oricid: 
  
  - name: Brendan M Rogers
    email: brogers@woodwellclimate.org
    affiliation: '2'
    oricid: 0000-0001-6711-8466
  
  - name: Trevor Smith
    email: tsmith@woodwellclimate.org
    affiliation: '2'
    oricid: 
  
  - name: Hannah Mevenkamp
    email: hkmevenkamp@alaska.edu
    affiliation: '1'
    oricid: 0000-0002-7241-5374
  
  - name: Mark J Lara
    email: mjlara@illinois.edu
    affiliation: '6'
    oricid: 0000-0002-4670-7031
  
  - name: Qianlai Zhuang
    email: qzhuang@purdue.edu
    affiliation: '4'
    oricid: 0000-0002-4536-9851
  
  - name: Shuhua Yi
    email: yis@lzb.ac.cn
    affiliation: '5'
    oricid: 

affiliations:
  - name: Institute of Arctic Biology, University of Alaska Fairbanks, Fairbanks 99775, Alaska, USA
    index: 1
  - name: Woodwell Climate Research Center, Falmouth 02540, Massachusetts, USA
    index: 2
  - name: Environmental Science Division and Climate Change Science Institute, Oak Ridge National Laboratory, Oak Ridge, TN 37831
    index: 3
  - name: Department of Earth, Atmospheric, and Planetary Science, Purdue University, West Lafayette IN 47907 USA
    index: 4
  - name: School of Geographic Sciences, Nantong University, Nantong Jiangsu, 226019 P.R. China
    index: 5
  - name: Department(s) of Plant Biology and Geography, University of Illinois Urbana-Champaign, Urbana, IL 61801
    index: 6

date: 19 August 2024
bibliography: joss-paper.bib
---

![Logo for `DVMDOSTEM`\label{fig:logo}](ddt_logo_910x705_alpha.png){width="20%"} 

# Summary

The impacts of climate change on natural ecosystems are the result of complex
physical and ecological processes operating and interacting at a variety of
spatio-temporal scales, that can be represented in process-based ecosystem models.

`DVMDOSTEM` is an advanced process-based terrestrial ecosystem model (TEM)
designed to study ecosystem responses to climate changes and disturbances. It
has a particular focus on permafrost regions (i.e. regions characterized by
soils that stay partially frozen all year round for at least two consecutive
years), encompassing boreal, arctic, and alpine landscapes. The model couples a
dynamic vegetation module (DVM) and a dynamic organic soil (DOS) module to
simulate processes at yearly and monthly scales, with some physical processes
operating at an even finer temporal resolution. Its versatility allows for
site-specific to regional simulations, making it valuable for predicting shifts
in permafrost, vegetation, and carbon (C) and nitrogen (N) dynamics.

# Statement of need

Arctic and boreal regions underlain by permafrost store nearly half of the
world’s soil organic C - approximately 1,440-1,600 Pg [@Hugelius2014;
@Schuur2022]. These regions are warming four times faster than
the rest of the globe, driving widespread and rapid permafrost thaw
[@Rantanen2022; @Smith2022]. As permafrost thaws, soil organic C becomes
available for decomposition and release as greenhouse gasses (GHGs) to the
atmosphere. Climate-driven permafrost thaw and the associated release of GHGs
can influence the global climate system, a phenomenon called the permafrost
carbon-climate feedback or PCCF [@Koven2011; @Schuur2015]. The PCCF has been
identified as one of the largest sources of uncertainty in future climate
projections and therefore needs to be accurately represented in global earth 
system models [@Schadel2024].

# Model Design

`DVMDOSTEM` is designed to simulate the key
biophysical and biogeochemical processes between the soil, the vegetation and
the atmosphere. The evolution and refinement of `DVMDOSTEM` have been shaped by
extensive research programs and applications both in permafrost and
non-permafrost regions [@Genet2013; @Genet2018; @Jafarov2013; @Yi2010;
@Yi2009; @Euskirchen2022; @Briones2024]. The model is spatially explicit and
represents ecosystem response to climate and disturbances at seasonal (i.e.
monthly) to centennial scales. The snow and soil columns are split into a
dynamic number of layers to represent their impact on thermal and hydrological
dynamics and the consequences for soil C and N dynamics. Vegetation composition
is modeled using community types (CMTs), each of which consists of multiple
plant functional types (PFTs - groups of species sharing similar ecological
traits). This structure allows the model to represent the effect of competition
for light, water and nutrients on vegetation composition [@Euskirchen2009], as well
as the role of nutrient limitation on permafrost ecosystem dynamics, with
coupling between C and N cycles [@McGuire1992; @Euskirchen2009]. Finally,
the model represents the effects of wildfire in order to evaluate the role of
climate-driven fire intensification on ecosystem structure and function
[@Yi2010; @Genet2013]. The structure of `DVMDOSTEM` is represented visually in
\autoref{fig:modeloverview}.

![Overview of `DVMDOSTEM` soil and vegetation structure. On the left is the soil
structure showing the layers and different properties that are tracked (purple
bubble: carbon (C), nitrogen (N), temperature (T), volumetric water content
(VWC), ice). Each of the layers with properties described above is also
categorized as organic (fibric or humic) or mineral. Additionally, the model
simulates snow layers and the removal of soil organic layers due to fire. On the
right is the vegetation structure showing plant functional types (PFTs)
within a community type (CMT) and the associated pools and fluxes of C and
N. Each PFT is split into compartments (leaf, stem and root) which track their
own C and N content and associated fluxes. The fluxes are represented with red
text while the pools are black. In addition, there is competition among the PFTs
for light, water, and available N, shown with the purple arrow in the top
center.\label{fig:modeloverview}](dvmdostem-overview-export_2024-08-19.jpg)


## Inputs and outputs

NetCDF files [@Rew1990] are used as model inputs and outputs, conforming
to the CF Conventions v1.11 [@Eaton2011] where possible. The input variables
used to drive `DVMDOSTEM` include: drainage classification (upland or lowland), CMT
classification, topography (slope, aspect, elevation), soil texture (percent
sand, silt, and clay), climate (air temperature, precipitation, vapor pressure,
incoming shortwave radiation), atmospheric $CO_2$ concentration, and fire
occurrence (date and severity). All input datasets are spatially explicit,
except the time series of atmospheric $CO_2$. 

There are approximately 110 different variables available for output from
`DVMDOSTEM`. One file will be produced per requested output variable. Users can
specify the temporal and structural resolutions at which model outputs are
produced. This functionality allows users to consider their
computational resources and information needs when setting up a model run.


# Parameterization

`DVMDOSTEM` parameterization sets are developed for each CMT. Each CMT is defined
by more than 200 parameters. Parameter values are
estimated directly from field, lab or remote sensing observations, literature
review or site-specific calibration. Calibration is required when (1) parameter
values cannot be determined directly from available data or published
information, and (2) model sensitivity to the parameter is substantial. The
calibration process consists of adjusting parameter values until there is
acceptable agreement between measured field data and model prediction on the
state variables most influenced by the parameter to be calibrated. Due to the
large number of parameters requiring calibration, and the non-linear nature of
the relationships between parameters and state variables, model calibration can
be labor-intensive. We are actively developing a calibration process
that allows automation [@JafarovINPREP2024].


# Software Design

The `DVMDOSTEM` software repository is a combination of tightly coupled
sub-components: 

 - the `DVMDOSTEM` model,
 - supporting tools, and
 - development environment specifications.

The core `DVMDOSTEM` model is written in C++ and uses some object-oriented concepts.
The model exposes a command line interface that allows users to start simulations 
manually or use a scripting language to drive the command line interface.

Surrounding the core model is a large body of supporting tools to assist the
user with preparing inputs, setting up and monitoring model runs and analyzing
model outputs. This collection of tools is primarily written in Python and shell
scripts, with some of the demonstration and exploratory analysis using Jupyter
Notebooks. The supporting tooling is partially exposed via command line
interfaces and a Python API which are documented in the User Guide. 

The model and tools target a UNIX-like operating system environment. The
combination of the core `DVMDOSTEM` model and the supporting tools result in the
need for a complex computing environment with many dependencies. Docker images
are used to manage this complexity, providing consistent environments
for development and production, [@Merkel2014]. 

Software updates are ongoing, stemming from the organic growth spanning 30+ years 
of development by research scientists, graduate students and programmers. Recent
years have seen an increased effort to apply professional software development 
practices such as version control, automated documentation, containerization, 
and testing.

# Acknowledgements

The current version of `DVMDOSTEM` is the result of decades of model
developments from the original TEM code developed at the Marine Biological
Laboratory [@Raich1991]. Following is the list of recent and current
programs and projects that supported model developments over the past ten years:
(1) the Integrated Ecosystem Model for Alaska and Northwest Canada project
supported by the US Geological Survey and the Arctic, Western Alaska, and
Northwest Boreal Landscape Conservation Cooperatives in Alaska, (2) the Bonanza
Creek Long Term Ecological Research Program funded by the National Science
Foundation and the USDA Forest Service, (3) the Permafrost Pathways project
through the TED Audacious Project and the Quadrature Climate Foundation, (4) the
Next Generation Ecosystem Experiment program for the Arctic region supported by
the Department of Energy. 	


# References