---
title: 'DVMDOSTEM v0.8.2: a terrestrial ecosystem model designed to represent arctic, boreal and permafrost ecosystem dynamics'
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
    orcid: 0000-0003-4537-9563
    equal-contrib: true
  
  - name: Ruth A Rutter
    email: rarutter@alaska.edu
    affiliation: '1'
    orcid: 0009-0009-7043-6081
  
  - name: Elchin Jafarov
    email: ejafarov@woodwellclimate.org
    affiliation: '2'
    orcid: 0000-0002-8310-3261
  
  - name: Eugénie Euskirchen
    email: seeuskirchen@alaska.edu
    affiliation: '1'
    orcid: 0000-0002-0848-4295
  
  - name: Ben Maglio
    email: bmaglio@alaska.edu
    affiliation: '1'
    orcid: 0000-0002-1948-0177 
  
  - name: Joy Clein
    email: jsclein@alaska.edu
    affiliation: '1'
    orcid: 0000-0002-2816-5312
  
  - name: Valeria Briones
    email: vbriones@woodwellclimate.org
    affiliation: '2'
    orcid: 0000-0002-5649-851X
  
  - name: Andrew L Mullen
    email: amullen@woodwellclimate.org
    affiliation: '2'
    orcid: 0000-0002-9127-9996
  
  - name: Heather Greaves
    email: hegreaves@alaska.edu
    affiliation: '1'
    orcid: 0000-0002-8800-019X
  
  - name: A. D. McGuire
    email: admcguire@alaska.edu
    affiliation: '1'
    orcid: 0000-0003-4646-0750
  
  - name: Fengming Yuan
    email: yuanf@ornl.gov
    affiliation: '3'
    orcid: 0000-0003-0910-5231
  
  - name: Chu-Chun Chang
    email: cchang@woodwellclimate.org
    affiliation: '2'
    orcid: 0000-0002-2971-2349
  
  - name: Joshua M. Rady
    email: jrady@woodwellclimate.org
    affiliation: '2'
    orcid: 0000-0002-7806-136X
  
  - name: Doğukan Teber
    email: dteber@woodwellclimate.org
    affiliation: '2'
    orcid: 0009-0000-1547-950X
  
  - name: Brendan M Rogers
    email: brogers@woodwellclimate.org
    affiliation: '2'
    orcid: 0000-0001-6711-8466
  
  - name: Trevor Smith
    email: tsmith@woodwellclimate.org
    affiliation: '2'
    orcid: 
  
  - name: Hannah Mevenkamp
    email: hkmevenkamp@alaska.edu
    affiliation: '1'
    orcid: 0000-0002-7241-5374
  
  - name: Mark J Lara
    email: mjlara@illinois.edu
    affiliation: '6'
    orcid: 0000-0002-4670-7031
  
  - name: Qianlai Zhuang
    email: qzhuang@purdue.edu
    affiliation: '4'
    orcid: 0000-0002-4536-9851
  
  - name: Shuhua Yi
    email: yis@lzb.ac.cn
    affiliation: '5'
    orcid: 0000-0003-4932-8237

affiliations:
  - name: Institute of Arctic Biology, University of Alaska Fairbanks, Fairbanks 99775, Alaska, USA
    index: 1
  - name: Woodwell Climate Research Center, Falmouth 02540, Massachusetts, USA
    index: 2
  - name: Environmental Science Division and Climate Change Science Institute, Oak Ridge National Laboratory, Oak Ridge, TN 37831
    index: 3
  - name: Department of Earth, Atmospheric, and Planetary Science, Purdue University, West Lafayette IN 47907 USA
    index: 4
  - name: Laboratory of Herbage Improvement And Agro-ecosystem, Lanzhou University, Lanzhou 730000, Gansu Province, P.R. China
    index: 5
  - name: Department(s) of Plant Biology and Geography, University of Illinois Urbana-Champaign, Urbana, IL 61801
    index: 6

date: 06 March 2025
bibliography: joss-paper.bib
---

# Summary

The impacts of climate change on natural ecosystems are the result of complex
physical and ecological processes operating and interacting at a variety of
spatio-temporal scales, that can be represented in process-based ecosystem models.

`DVMDOSTEM` is an advanced process-based terrestrial ecosystem model (TEM)
designed to study ecosystem responses to climate changes and disturbances. It
has a particular focus on permafrost regions (i.e. regions characterized by
soils that stay partially frozen all year round for at least two consecutive
years), encompassing boreal, arctic, and alpine landscapes. The model couples
two previous versions of the Terrestrial Ecosystem Model (TEM), [@McGuire1992]:
DVMTEM that includes a dynamic vegetation module (DVM) [@Euskirchen2009], and
DOSTEM that includes a dynamic organic soil module (DOS) [@Yi2010; @Genet2013].
`DVMDOSTEM` simulates processes at yearly and monthly scales, with some physical
processes operating at an even finer temporal resolution. Its versatility allows
for site-specific to regional simulations, making it valuable for predicting
shifts in permafrost, vegetation, and carbon (C) and nitrogen (N) dynamics.
While `DVMDOSTEM` has been described in the methods sections of many
manuscripts, this paper is the first stand alone description of `DVMDOSTEM`,
independent of a particular scientific investigation.

![Logo for `DVMDOSTEM`\label{fig:logo}](ddt_logo_910x705_alpha.png){width="20%"} 


# Statement of need

Arctic and boreal regions underlain by permafrost store nearly half of the
world’s soil organic C - approximately 1,440-1,600 Pg [@Hugelius2014;
@Schuur2022]. These regions are warming four times faster than the rest of the
globe, driving widespread and rapid permafrost thaw [@Rantanen2022; @Smith2022].
As permafrost thaws, soil organic C becomes available for decomposition and
release as greenhouse gasses (GHGs) to the atmosphere. Climate-driven permafrost
thaw and the associated release of GHGs can influence the global climate system,
a phenomenon called the permafrost carbon-climate feedback or PCCF [@Koven2011;
@Schuur2015]. The PCCF has been identified as one of the largest sources of
uncertainty in future climate projections and therefore needs to be accurately
represented in global earth system models [@Schadel2024]. `DVMDOSTEM` has been
developed with special emphasis on physical and biological processes driving
permafrost and carbon cycling in high latitude ecosystems. `DVMDOSTEM` is
therefore well suited to assessing and informing our understanding of the PCCF.

# Model Design

`DVMDOSTEM` is designed to simulate the key
biophysical and biogeochemical processes between the soil, the vegetation and
the atmosphere. The evolution and refinement of `DVMDOSTEM` have been shaped by
extensive research programs and applications both in permafrost and
non-permafrost regions [@Genet2013; @Genet2018; @Jafarov2013; @Yi2010;
@Yi2009; @Euskirchen2022; @Briones2024]. The model is spatially explicit and
represents ecosystem response to climate and disturbances at seasonal (i.e.
monthly) to centennial scales. 

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
center.\label{fig:modeloverview}](dvmdostem-overview-export_2025-03-06.jpg)


The snow and soil columns are split into a dynamic number of layers to represent
their impact on thermal and hydrological dynamics and the consequences for soil
C and N dynamics. Vegetation composition is modeled using community types
(CMTs), each of which consists of multiple plant functional types (PFTs - groups
of species sharing similar ecological traits). This structure allows the model
to represent the effect of competition for light, water and nutrients on
vegetation composition [@Euskirchen2009], as well as the role of nutrient
limitation on permafrost ecosystem dynamics, with coupling between C and N
cycles [@McGuire1992; @Euskirchen2009]. Finally, the model represents the
effects of wildfire in order to evaluate the role of climate-driven fire
intensification on ecosystem structure and function [@Yi2010; @Genet2013]. The
structure of `DVMDOSTEM` is represented visually in \autoref{fig:modeloverview}.

# State of the Field

In the field of ecosystem models, several prominent models such as CLM5
[@Lawrence2019], ELM-FATES [@Fisher2015], LANDIS [@Scheller2007], and iLand
[@Seidl2012] have been developed to simulate ecological processes at various
scales, resolutions and ecotypes. Like `DVMDOSTEM`, ELM-FATES, and early
versions of CLM, are "offline" land models that do not include feedback with
atmospheric or oceanic models, focusing instead on land surface processes.
LANDIS and iLand emphasize forest dynamics with some interaction between grid
cells, while `DVMDOSTEM` does not model interaction between grid cells. While
`DVMDOSTEM` contains detailed representations of vegetation - multiple Plant
Functional Types (PFTs) and individual compartments within PFTs - it also has 
the concept of community types (collections of PFTs and
soil properties) and is designed to run at the landscape scale by representing
more than a single stand of trees or a single forest type. `DVMDOSTEM` is unique
in its detailed representation of high latitude processes, particularly the
dynamic organic soils in regions with frozen ground coupled with dynamic
vegetation and high latitude specific parameterizations. This focus allows
`DVMDOSTEM` to simulate the complex interactions between soil, vegetation, and
climate in permafrost ecosystems, providing valuable insights into the PCCF. For
a more detailed assessment and comparison of high latitude vegetation modeling,
see [@Heffernan2024].

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