#!/usr/bin/env python
# coding: utf-8

import sys
import os
# setting path
sys.path.append('/work/scripts/drivers')
sys.path.append('/work/scripts/util')
import pandas as pd
import seaborn as sns
import Sensitivity_LOCAL_750 as sa
import output as ou


work_dir='/data/workflows/BONA_black_spruce_SWC_SA'
#work_dir='/data/workflows/BONA_birch_SWC_SA'

opt_run_setup='--tr-yrs=122 --sp-yrs=300 --eq-yrs=500 '

driver = sa.SensitivityDriver(work_dir = work_dir, clean=True)
driver.site = '/data/input-catalog/cpcrw_towers_downscaled/'
driver.opt_run_setup = opt_run_setup

#US-Prr
#driver.PXx ='1'
#driver.PXy='0'
#
#BONA
#driver.PXx ='0'
#driver.PXy='3'
#
#BONA downscaled
driver.PXx ='0'
driver.PXy='0'
#

params = ['hksat(m)','hksat(f)','hksat(h)',
          'tcsolid(m)', 'tcsolid(f)', 'tcsolid(h)',
          'porosity(m)', 'porosity(f)', 'porosity(h)',
          'nfactor(s)', 'nfactor(w)',
          'rhq10']#, 'rhq10_w']
#hksat-m .12-.15
#.25-.35
#.01-0.33
#BONA-Black-Spruce # produces good match
bounds = [[0.101, 0.2], [0.1, 0.2], [0.005, 0.05], #[0.000040, ]
          [0.1, 0.4], [0.1, 0.4], [0.1, .5],
          [0.8, 0.95], [0.8, 0.95], [0.5, 0.8],
          [1.8, 2.0], [0.2, 0.4],
          [2.38, 2.4]]

#bounds = [[0.13, 0.15], [0.12, 0.14], [0.02, 0.04], #[0.000040, ]
#          [0.26, 0.3], [0.38, 0.41], [0.35, .39],
#          [0.83, 0.87], [0.89, 0.93], [0.5, 0.55],
#          [1.8, 2.0], [0.2, 0.3],
#          [2.3, 2.4]]

#BONA-Birch
#bounds = [[0.01, 0.103], [0.01, 0.163], [0.0005, 0.012], #[0.000040, ]
#          [0.005, 0.1], [0.005, 0.1], [0.02, .2],
#          [0.83, 0.98], [0.8, 0.83], [0.5, 0.7],
#          [2.0, 2.1], [0.23, .28],
#          [2.3, 2.7]]#, [1.6, 2.4]]


driver.logparams = [1, 1, 1,
                    1, 1, 1,
                    0, 0, 0,
                    0, 0,
                    0]#, 0]

driver.outputs = [
      { 'name': 'GPP', 'type': 'flux'},
      { 'name': 'RH','type': 'flux'},
      { 'name': 'ALD','type': 'flux'},
      { 'name': 'LWCLAYER','type': 'layer'},
      { 'name': 'VWCLAYER','type': 'layer'},
      { 'name': 'TLAYER','type': 'layer'},
      { 'name': 'LAYERDEPTH','type': 'layer'},
      { 'name': 'LAYERDZ','type': 'layer'},
      { 'name': 'LAYERTYPE','type': 'layer'},
    ]

driver.design_experiment(Nsamples = 50, cmtnum = 15, params = params,
                         bounds=bounds, pftnums = [None]*len(params), sampling_method='uniform')


driver.clean()
driver.setup_multi()
driver.run_all_samples()


driver.sample_matrix













