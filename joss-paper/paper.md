---
title: 'DVMDOSTEM: A terrestrial biosphere model focused on arctic vegetation and soil dynamics'
tags:
  - C++
  - Python
  - ecology
  - permafrost
  - dynamics

authors:
  - name: Tobey B Carman
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
    corresponding: true
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
questions about changing ecosystems at a scale somewhere between the Global
Circulation Models smaller point or process specific models. The ``DVMDOSTEM``
model is a TBM focused on C and N cycling through vegetation and soil as well as
soil thermal dynamics. The ``DVMDOSTEM`` model has been primarlily used thus
far for high latitude ecosystems, but with work put into the parameterizations,
it could be used elsewhere.

DVM-DOS-TEM is an advanced ecological mechanistic model tailored to capture the intricacies of vegetation and soil thermal dynamics in cold regions. Designed to study ecosystem responses to climate changes and disturbances, it has a particular focus on boreal, arctic, and alpine landscapes. The model integrates vegetation dynamics (DVM) and soil biogeochemistry (DOS-TEM) to simulate processes on monthly and yearly scales, with some components operating at an even finer granularity. Its versatility allows for site-specific to regional simulations, making it valuable for predicting shifts in permafrost, vegetation, and carbon dynamics.

Key Features:

* Vegetation Dynamics: Simulates the lifecycle of various plant functional types, influenced by climatic conditions.
* Carbon and Nitrogen Cycling: Captures ecosystem carbon and nitrogen fluxes and reservoirs, incorporating processes such as photosynthesis, respiration, and decomposition.
* Soil Thermal Dynamics: Provides detailed insights into soil thermal conditions, including permafrost dynamics and active layer thickness, influenced by external factors like snow cover.
* Disturbance Modules: Accounts for ecological disturbances, including wildfires, insect infestations, and anthropogenic activities.

# Statement of need

TBMs are needed because...

# Mathematics

The fundamental equation governing the vegetation side of ``DVMDOSTEM`` is the
equation for GPP as a function of...

$$\Theta(x) = 0$$

The fundamental equations for the dynamic soil side of ``DVMDOSTEM`` are...

$$`\Pi(x) = 1$$

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

# Figures

<!-- Exported from Tobey Carman's Google Drawing "dvmdostem-general-idea-science"-->
![Overview of DVMDOSTEM spatial structure. DVMDOSTEM is a process based spatially explicit model.\label{fig:structural_overview}](figures/dvmdostem-general-idea-science-export_2023-10-09.jpg)

<!-- Exported from UAF Shared Drive > Documentation Embed Images > "dvmdostem-overview" Google Drawing -->
![Overview of DVMDOSTEM soil and vegetation structure. On the left is the soil structure showing the layers, different properties that are tracked (purple bubble; Carbon, Nitrogen, Temperature, Volumetric Water Content, Ice). Each of the layers with properties described above, is also categorized as Organic (fibric or humic) or Mineral (shallow or deep). Additionally the model simulates snow layers and the removal to layers due to processes such as fire.  On the right is the vegetation structure showing the Plant Functional Types (PFTs) and the associated pools and fluxes of Carbon and Nitrogen. Each PFT is split into compartments (Leaf, Stem and Root) which track their own C and N content and associated fluxes. The fluxes are represented with red text while the pools are black. In addition there is competition among the PFTs shown with the purple arrow in the top center.\label{fig:soil_veg_structure}](figures/dvmdostem-overview-export_2023-10-09.jpg)


<!-- Figures can be included like this:
![Caption for example figure.\label{fig:example}](figure.png)

and referenced from text using \autoref{fig:example}.




Figure sizes can be customized by adding an optional second parameter:
![Caption for example figure.](figure.png){ width=20% } -->

# Acknowledgements


# References
