---
title: 'DVMDOSTEM: A terrestrial biosphere model focused on arctic vegetation and soil dynamics'
tags:
  - C++
  - Python
  - ecology
  - permafrost
  - vegetation dynamics
  - soil thermal dynamics
  - arctic
  - carbon cycle

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
Circulation Models and smaller point or process specific models. The ``DVMDOSTEM``
model is a TBM focused on C and N cycling through vegetation and soil as well as
soil thermal dynamics. The ``DVMDOSTEM`` model has been primarlily used thus
far for high latitude ecosystems, but with work put into the parameterizations,
it could be used elsewhere.

DVM-DOS-TEM is an advanced ecological process model tailored to capture the intricacies of vegetation and soil thermal dynamics for multiple vegeation types and multiple soil layers. Designed to study ecosystem responses to climate changes and disturbances, it has a particular focus on boreal, arctic, and alpine landscapes. The model integrates vegetation dynamics (DVM) and soil biogeochemistry (DOS-TEM) to simulate processes on monthly and yearly scales, with some components operating at an even finer granularity. Its versatility allows for site-specific to regional simulations, making it valuable for predicting shifts in permafrost, vegetation, and carbon dynamics.

Key Features:

* Vegetation Dynamics: Simulates the lifecycle of various plant functional types, influenced by climatic conditions and including competition between plant functional types.
* Carbon and Nitrogen Cycling: Captures ecosystem carbon and nitrogen fluxes and pools, incorporating processes such as photosynthesis, respiration, and decomposition.
* Soil Thermal Dynamics: Provides detailed insights into soil thermal conditions, including permafrost dynamics and active layer thickness, influenced by external factors like snow cover and vegetation.
* Disturbance Modules: Accounts for ecological disturbances, including wildfires and permafrost thaw.

# Statement of need

The permafrost regions, repositories of a colossal 1,440-1,600 Pg of organic carbon in soils, embody nearly half of the world’s soil organic carbon pool, underpinning the global climate system (Hugelius et al., 2014; Schuur et al., 2022). Accelerated Arctic warming is catalyzing permafrost thaw and introduces a potent threat in the form of accelerated  decomposition and release of a substantial portion of this stored carbon as greenhouse gases, thereby exerting formidable pressures on global climate dynamics (Schuur et al., 2022; Natali et al., 2021; Treharne et al., 2022). An imperative demand exists to utilize models that integrate cryo-hydrological processes with ecosystem carbon cycling and to explore the uncertainties of modeling the permafrost carbon feedback.

The evolution and refinement of the DVM-DOS-TEM (Terrestrial Ecosystem Model with Dynamic Vegetation and Dynamic Organic Soil Layers) model has been shaped by extensive research and application, marked by a strong focus on simulating biophysical and biogeochemical interactions amongst the soil, vegetation, and atmosphere, particularly in high-latitude ecosystems. Developed to encapsulate carbon and nitrogen cycles, and influenced by a myriad of factors ranging from climatic variables, disturbances, to varied biophysical processes, the model's trajectory has aimed to offer nuanced insights into these complex interplays across both seasonal and centennial scales (Genet et al., 2013, 2018). This model is designed to be computationally efficient while incorporating the necessary physics to study carbon cycling in frozen ground.

The DVM-DOS-TEM uses coupled soil thermal and hydrological dynamics, including snow cover and canopy development (Zhuang et al., 2002; Euskirchen et al., 2006, 2014; Yi et al., 2009; McGuire et al., 2018). Detailed structuring of vegetation into multiple plant functional types and compartmentalization, alongside soil stratification into various horizons and layers, have enabled meticulous simulations of carbon, nitrogen, temperature, and water content across diverse sub-components of the ecosystem.

The model leverages the two-directional Stefan Algorithm and the Richards equation, ensuring precise predictions of freezing/thawing fronts and calculating soil moisture changes in the unfrozen layers respectively (Yi et al., 2009, 2010; Zhuang et al., 2002). The intrinsic links between thermal and hydraulic properties of soil layers and their water content further shaped the DVM-DOS-TEM’s functionality and application, ensuring a holistic representation of underlying ecological processes, including carbon and nitrogen dynamics across the vegetation community and each layer of the soil column, driven by climate, atmospheric chemistry, soil and canopy environment, and wildfire occurrences. The model has a vast history of application in both Arctic and Boreal ecosystems across permafrost and non-permafrost regions, reinforcing its capability and reliability in studying and simulating complex ecosystem dynamics (Genet et al., 2013; Jafarov et al., 2013; Yi et al., 2010, 2009; Euskirchen et al., 2022). 


# Mathematics

The fundamental equation includes carbon cycling, surface and subsurface energy balance, and hydrology. In addition to these equations, the model includes the dynamics of the organic layer and fire disturbance processes. 

### Carbon Cycling:

1. **Net Primary Production (NPP):**
   $$NPP = GPP - R_a$$
   where $GPP$ is Gross Primary Production, and $R_a$ is autotrophic respiration.

2. **Net Ecosystem Exchange (NEE):**
   $$NEE = NPP - R_h$$
   where $R_h$ is heterotrophic respiration.

3. **Carbon Stock Change:**
   $$\Delta C = \text{Input} - (\text{Decomposition} + \text{Leaching})$$

### Permafrost Energy Balance:

1. **Conductive Heat Flux:**
   $$Q = -k \cdot \frac{\Delta T}{\Delta z}$$
   where $k$ is thermal conductivity, $\Delta T$ is the temperature gradient, and $\Delta z$ is the thickness of the soil layer.

2. **Ground Heat Flux:**
   $$G = (1 - \alpha) \cdot SW_{\downarrow} + LW_{\downarrow} - LW_{\uparrow} - H - LE$$
   where $\alpha$ is albedo, $SW_{\downarrow}$ is downward shortwave radiation, $LW_{\downarrow}$ is downward longwave radiation, $LW_{\uparrow}$ is upward longwave radiation, $H$ is sensible heat flux, and $LE$ is latent heat flux.

### Hydrology:

1. **Water Balance Equation:**
   $$P = Q + ET + \Delta S$$
   where $P$ is precipitation, $Q$ is runoff, $ET$ is evapotranspiration, and $\Delta S$ is change in storage.

2. **Darcy’s Law (Water Flow):**
   $$Q = -k \cdot A \cdot \frac{\Delta h}{\Delta l}$$
   where $Q$ is the flow rate, $k$ is the hydraulic conductivity, $A$ is the cross-sectional area, $\Delta h$ is the head loss, and $\Delta l$ is the length of the pathway.

3. **Richards Equation (Unsaturated Water Flow):**
   $$\frac{\partial \theta}{\partial t} = \nabla \cdot [K(\theta) \cdot \nabla h] + S(\theta)$$
   where $\theta$ is the volumetric water content, $t$ is time, $K(\theta)$ is the hydraulic conductivity as a function of $\theta$, $h$ is the matric potential, and $S(\theta)$ is a source/sink term.


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

# Model Architecture

# Input Data

# Demo

# Conclusion

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
