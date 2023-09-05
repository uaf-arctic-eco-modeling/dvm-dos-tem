#!/usr/bin/env python
# coding: utf-8

import sys
import os
# setting path
sys.path.append('/work/scripts')
import pandas as pd
import seaborn as sns


import Sensitivity as sa
import output_utils as ou


# # parameters influencing soil hydro/thermal state
# ### cmt_envground.txt
# --------------------------------------------------------
# #### tcsolid(m): Soil thermal conductivity for moss (W/mK)
# current value: 0.25, range: 0.005-0.5
# 
# *Ekici et al. 2015,Jiang et al. 2015, O’Donnell et al. 2009*
# 
# #### tcsolid(f): Soil thermal conductivity for fibric (W/mK)
# current value: 0.25, range: 0.005-0.5
# 
# *Ekici et al. 2015,Jiang et al. 2015, O’Donnell et al. 2009*
# 
# #### tcsolid(h): Soil thermal conductivity for humic (W/mK)
# current value: 0.25, range: 0.02-2.0
# 
# *Ekici et al. 2015,Jiang et al. 2015, O’Donnell et al. 2009*
# 
# ---------------------------------------------------------
# #### porosity(m): porosity for moss layers (m3/m3)
# current value: 0.98, range: 0.85-0.99
# 
# *O’Donnell et al. 2009*
# 
# #### porosity(f): porosity for fibric layers  (m3/m3)
# current value: 0.95, range: 0.85-0.99
# 
# *O’Donnell et al. 2009*
# 
# #### porosity(h): porosity for humic layers  (m3/m3)
# current value: 0.8, range: 0.7-0.9
# 
# *O’Donnell et al. 2009*
# 
# --------------------------------------------------------
# #### bulkden(m): bulk density for moss (g/m3)
# current value: 25,000, range: 10,000 - 80,000
# 
# *Tuomi et al. 2020, Rodionov et al. 2007, O’Donnell et al. 2009*
# 
# #### bulkden(f): bulk density for fibric (g/m3)
# current value: 51,000, range: 20,000 - 200,000
# 
# *Tuomi et al. 2020, Rodionov et al. 2007, O’Donnell et al. 2009*
# 
# #### bulkden(h): bulk density for humic (g/m3)
# current value: 176,000, range: 100,000 - 800,000
# 
# *Tuomi et al. 2020, Rodionov et al. 2007, O’Donnell et al. 2009*
# 
# --------------------------------------------------------
# #### hksat(m): hydraulic conductivity at saturation for moss (mm/s)
# current value: 0.15, range: 0.0002 - 30
# 
# *Ekici et al. 2015, Letts et al. 2000, Liu et al. 2019*
# 
# #### hksat(f): hydraulic conductivity at saturation for fibric (mm/s)
# current value: 0.28, range: 0.0002 - 30
# 
# *Ekici et al. 2015, Letts et al. 2000, Liu et al. 2019*
# 
# #### hksat(h): hydraulic conductivity at saturation for humic (mm/s)
# current value: 0.002, range: 0.00004 - 2.01
# 
# *Ekici et al. 2015, Letts et al. 2000, Liu et al. 2019*
# 
# ---------------------------------------------------------
# #### nfactor(s): Summer nfactor
# current value: 1.5, range: 0.2-2.0
# 
# *Kade et al. 2006, Klene et al. 2001*
# 
# #### nfactor(w): Winter nfactor
# current value: 1.0, range: 0.4-1.0
# 
# *Kade et al. 2006, Klene et al. 2001*
# 
# ---------------------------------------------------------
# #### snwalbmax
# current value: 0.8, range: 0.7-0.85
# 
# *Te Beest et al. 2016, Petzold et al. 1975, Loranty et al. 2011*
# 
# #### snwalbmin
# current value: 0.4, range: 0.4-0.6
# 
# *Te Beest et al. 2016, Petzold et al. 1975, Loranty et al. 2011*
# 
# ---------------------------------------------------------
# ### cmt_dimground.txt
# ---------------------------------------------------------
# #### snwdenmax (kg/m3)
# current value: 250, range: 100-800
# 
# *Domine et al. 2016, Gerland et al. 1999, Muskett 2012*
# 
# #### snwdennew (kg/m3)
# current value: 50, range: 10-250
# 
# *Domine et al. 2016, Gerland et al. 1999, Muskett 2012*
# 
# 
# ### cmt_bgcsoil.txt
# ---------------------------------------------------------
# #### rhq10
# current value: 2, range: 1.6-2.4
# #### rhq10_w
# current value: 2, range: 0.85-0.99

work_dir='/data/workflows/US-Prr_SWC_SA'
opt_run_setup='--tr-yrs=121 --sp-yrs=300 --eq-yrs=500 '

driver = sa.SensitivityDriver(work_dir = work_dir, clean=True)
driver.site = '/data/input-catalog/caribou-poker_merged/'
driver.opt_run_setup = opt_run_setup
driver.PXx ='1'
driver.PXy='0'

params = ['hksat(m)','hksat(f)','hksat(h)',
          'tcsolid(m)', 'tcsolid(f)', 'tcsolid(h)',
          'porosity(m)', 'porosity(f)', 'porosity(h)',
          'nfactor(s)', 'nfactor(w)',
          'rhq10']#, 'rhq10_w']
percent_diffs = [0.1, 0.1, 0.1,
                 0.1, 0.1, 0.1,
                 0.1, 0.1, 0.1,
                 0.1, 0.1,
                 0.1]#, 0.1]
bounds = [[0.001, 0.005], [1e-4, 0.05], [1e-4, 8e-4],
          [0.005, 0.5], [0.005, 0.5], [0.02, 2.0],
          [0.85, 0.99], [0.85, 0.99], [0.7, 0.9],
          [0.2, 2.0], [0.4, 1.0],
          [1.6, 2.4]]#, [1.6, 2.4]]
driver.logparams = [1, 1, 1,
                    1, 1, 1,
                    0, 0, 0,
                    0, 0,
                    0]#, 0]

driver.outputs = [
      { 'name': 'GPP', 'type': 'flux'},
      { 'name': 'RH','type': 'flux'},
      { 'name': 'LWCLAYER','type': 'layer'},
      { 'name': 'VWCLAYER','type': 'layer'},
      { 'name': 'TLAYER','type': 'layer'},
      { 'name': 'LAYERDEPTH','type': 'layer'},
      { 'name': 'LAYERDZ','type': 'layer'},
      { 'name': 'LAYERTYPE','type': 'layer'},
    ]

driver.design_experiment(Nsamples = 50, cmtnum = 13, params = params, percent_diffs = percent_diffs,
                         bounds=bounds, pftnums = [None]*len(params), sampling_method='uniform')


driver.setup_multi()


driver.sample_matrix


driver.run_all_samples()




