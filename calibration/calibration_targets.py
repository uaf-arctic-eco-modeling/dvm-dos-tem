#!/usr/bin/env python

# could add code here to load up calibration_targets variable from the
# contents of an excel file...? or just plain csv?

calibration_targets = {
  # Added this data structure to support comments, units, references etc that
  # can be handled in the fixed width text parameter files as well as the csv
  # parameter files.
  "meta": {
    'GPPAllIgnoringNitrogen': {'units': 'g/m2/year', 'desc': 'GPP without N limitation', 'comment': 'ingpp', 'ref': '', 'ncname': 'INGPP'},
    'NPPAllIgnoringNitrogen': {'units': 'g/m2/year', 'desc': 'NPP without N limitation', 'comment': 'innpp', 'ref': '', 'ncname': 'INNPP'},
    'NPPAll': {'units': 'g/m2/year', 'desc': 'NPP with N limitation', 'comment': 'npp', 'ref': '', 'ncname': 'NPP'},
    'Nuptake': {'units': 'g/m2/year', 'desc': '', 'comment': 'nuptake', 'ref': '','ncname': '?'},
    'VegCarbon': {
      'Leaf': {'units': 'g/m2', 'desc': '', 'comment': 'vegcl', 'ref': '', 'ncname': 'VEGC'},
      'Stem': {'units': 'g/m2', 'desc': '', 'comment': 'vegcw', 'ref': '', 'ncname': 'VEGC'},
      'Root': {'units': 'g/m2', 'desc': '', 'comment': 'vegcr', 'ref': '', 'ncname': 'VEGC'},
    },
    'VegStructuralNitrogen': {
      'Leaf': {'units': 'g/m2', 'desc': '', 'comment': 'vegnl', 'ref': '', 'ncname': 'VEGN'},
      'Stem': {'units': 'g/m2', 'desc': '', 'comment': 'vegnw', 'ref': '', 'ncname': 'VEGN'},
      'Root': {'units': 'g/m2', 'desc': '', 'comment': 'vegnr', 'ref': '', 'ncname': 'VEGN'},
    },
    'MossDeathC': {'units': 'g/m2', 'desc': '', 'comment': 'dmossc', 'ref': '', 'ncname': 'MOSSDEATHC'},
    'CarbonShallow': {'units': 'g/m2', 'desc': '', 'comment': 'shlwc', 'ref': '', 'ncname': 'SHLWC'},
    'CarbonDeep': {'units': 'g/m2', 'desc': '', 'comment': 'deep', 'ref': '', 'ncname': 'DEEPC'},
    'CarbonMineralSum': {'units': 'g/m2', 'desc': '', 'comment': 'minec', 'ref': '', 'ncname': 'MINEC'},
    'OrganicNitrogenSum': {'units': '', 'desc': '', 'comment': 'soln', 'ref': '', 'ncname': 'ORGN'},
    'AvailableNitrogenSum': {'units': '', 'desc': '', 'comment': 'avln', 'ref': '', 'ncname': 'AVLN'},
  },

  ## WARNING: JUNK, PLACEHOLDER VALUES! USE AT YOUR OWN RISK!
  "BLANK": {
    'cmtnumber': 0,
    'PFTNames':                  [  'PFT0',  'PFT1',   'PFT2',   'PFT3',  'PFT4',  'PFT5',  'PFT6',  'PFT7',  'PFT0', 'PFT9'],
    'GPPAllIgnoringNitrogen':    [     0.0,     0.0,      0.0,      0.0,     0.0,     0.0,     0.0,     0.0,     0.0,    0.0 ], # ingpp     (gC/m2/year)   GPP without N limitation
    'NPPAllIgnoringNitrogen':    [     0.0,     0.0,      0.0,      0.0,     0.0,     0.0,     0.0,     0.0,     0.0,    0.0 ], # innpp     (gC/m2/year)   NPP without N limitation 
    'NPPAll':                    [     0.0,     0.0,      0.0,      0.0,     0.0,     0.0,     0.0,     0.0,     0.0,    0.0 ], # npp       (gC/m2/year)   NPP with N limitation
    'Nuptake':                   [     0.0,     0.0,      0.0,      0.0,     0.0,     0.0,     0.0,     0.0,     0.0,    0.0 ], # nuptake   (gN/m2/year)
    'VegCarbon': {
      'Leaf':                    [     0.0,     0.0,      0.0,      0.0,     0.0,     0.0,     0.0,     0.0,     0.0,    0.0 ], # vegcl     (gC/m2)
      'Stem':                    [     0.0,     0.0,      0.0,      0.0,     0.0,     0.0,     0.0,     0.0,     0.0,    0.0 ], # vegcw     (gC/m2)
      'Root':                    [     0.0,     0.0,      0.0,      0.0,     0.0,     0.0,     0.0,     0.0,     0.0,    0.0 ], # vegcr     (gC/m2)
    },
    'VegStructuralNitrogen': {
      'Leaf':                    [     0.0,     0.0,      0.0,      0.0,     0.0,     0.0,     0.0,     0.0,     0.0,    0.0 ], # vegnl     (gN/m2)
      'Stem':                    [     0.0,     0.0,      0.0,      0.0,     0.0,     0.0,     0.0,     0.0,     0.0,    0.0 ], # vegnw     (gN/m2)
      'Root':                    [     0.0,     0.0,      0.0,      0.0,     0.0,     0.0,     0.0,     0.0,     0.0,    0.0 ], # vegnr     (gN/m2)
    },
    'MossDeathC':                0.00,    #  dmossc
    'CarbonShallow':             0.00,    #  shlwc
    'CarbonDeep':                0.00,    #  deepc
    'CarbonMineralSum':          0.00,    #  minec
    'OrganicNitrogenSum':        0.00,    #  soln
    'AvailableNitrogenSum':      0.00,    #  avln
  },
  ## CMT01 - Black Spruce Forest, calibration for Murphy Dome climate.
  "black spruce forest": {
    'cmtnumber': 1,
                                 #    pft0     pft1      pft2      pft3     pft4     pft5     pft6     pft7     pft8    pft9   
    'PFTNames':                  ['BlackSpr', 'DecidShrub', 'Decid', 'Moss', '', '', '', '', '', ''],
    'GPPAllIgnoringNitrogen':    [  306.07,   24.53,    46.53,    54.23,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # ingpp     (gC/m2/year)   GPP without N limitation
    'NPPAllIgnoringNitrogen':    [  229.56,   18.40,    34.90,    40.65,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # innpp     (gC/m2/year)   NPP without N limitation
    'NPPAll':                    [  153.04,   12.27,    17.36,    27.10,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # npp       (gC/m2/year)   NPP with N limitation
    'Nuptake':                   [    1.26,    0.07,     0.23,     0.03,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # nuptake   (gN/m2/year)
    'VegCarbon': {
      'Leaf':                    [  293.76,   15.13,     9.06,   180.85,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegcl     (gC/m2)
      'Stem':                    [ 1796.32,  100.16,   333.75,     0.00,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegcw     (gC/m2)
      'Root':                    [  404.48,   15.07,    44.80,     0.00,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegcr     (gC/m2)
    },
    'VegStructuralNitrogen': {
      'Leaf':                    [    6.35,    0.72,     0.70,     1.61,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegnl     (gN/m2)
      'Stem':                    [   24.34,    2.48,     9.45,     0.00,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegnw     (gN/m2)
      'Root':                    [    0.17,    0.01,     0.03,     0.00,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegnr     (gN/m2)
    },
    'MossDeathC':              178.00,    #  dmossc
    'CarbonShallow':           782.73,    #  shlwc
    'CarbonDeep':             3448.46,    #  deepc
    'CarbonMineralSum':      41665.00,    #  minec
    'OrganicNitrogenSum':     2145.87,    #  soln
    'AvailableNitrogenSum':      0.76,    #  avln
  },
  ## CMT02 - White Spruce Forest, calibration for Murphy Dome climate.
  "white spruce forest": {
    'cmtnumber': 2,
                                 #    pft0     pft1      pft2      pft3     pft4     pft5     pft6     pft7     pft8    pft9   
    'PFTNames':                  ['WhiteSpr', 'DecidShrub', 'Decid', 'Moss', '', '', '', '', '', ''],
    'GPPAllIgnoringNitrogen':    [  491.81,   10.73,   189.32,    54.20,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # ingpp     (gC/m2/year)   GPP without N limitation
    'NPPAllIgnoringNitrogen':    [  368.96,    8.04,   141.99,    40.65,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # innpp     (gC/m2/year)   NPP without N limitation
    'NPPAll':                    [  245.90,    5.36,    94.66,    27.10,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # npp       (gC/m2/year)   NPP with N limitation
    'Nuptake':                   [    1.36,    0.05,     0.92,     0.03,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # nuptake   (gN/m2/year)
    'VegCarbon': {
      'Leaf':                    [  417.34,    2.26,    26.99,   180.85,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegcl     (gC/m2)
      'Stem':                    [ 5359.60,   76.76,  1367.66,     0.00,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegcw     (gC/m2)
      'Root':                    [  401.63,   10.33,   182.27,     0.00,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegcr     (gC/m2)
    },
    'VegStructuralNitrogen': {
      'Leaf':                    [    9.03,    0.11,     2.10,     1.61,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegnl     (gN/m2)
      'Stem':                    [   72.61,    1.90,    38.72,     0.00,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegnw     (gN/m2)
      'Root':                    [    9.20,    0.20,     3.57,     0.00,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegnr     (gN/m2)
    },
    'MossDeathC':              178.00,    #  dmossc
    'CarbonShallow':          1156.00,    #  shlwc
    'CarbonDeep':             4254.00,    #  deepc
    'CarbonMineralSum':      11005.00,    #  minec
    'OrganicNitrogenSum':      699.81,    #  soln
    'AvailableNitrogenSum':      1.69,    #  avln
  },
  ## CMT03 - Deciduous Forest, calibration for Murphy Dome climate.
  "deciduous forest": {
    'cmtnumber': 3,
                                 #    pft0     pft1      pft2      pft3     pft4     pft5     pft6     pft7     pft8    pft9   
    'PFTNames':                  ['SprTree', 'DecidShrub', 'DecidTree', 'Moss', '', '', '', '', '', ''],
    'GPPAllIgnoringNitrogen':    [    1.81,   61.75,   997.38,     0.82,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # ingpp     (gC/m2/year)   GPP without N limitation
    'NPPAllIgnoringNitrogen':    [    1.36,   46.31,   748.03,     0.62,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # innpp     (gC/m2/year)   NPP without N limitation
    'NPPAll':                    [    0.91,   30.87,   498.69,     0.41,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # npp       (gC/m2/year)   NPP with N limitation
    'Nuptake':                   [    1.69,    0.07,     3.68,     0.01,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # nuptake   (gN/m2/year)
    'VegCarbon': {
      'Leaf':                    [    2.47,    8.33,   131.74,     5.60,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegcl     (gC/m2)
      'Stem':                    [   11.82,   93.25,  5469.13,     0.00,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegcw     (gC/m2)
      'Root':                    [    0.99,   13.28,   731.99,     0.00,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegcr     (gC/m2)
    },
    'VegStructuralNitrogen': {
      'Leaf':                    [    0.05,    0.41,     7.04,     0.10,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegnl     (gN/m2)
      'Stem':                    [    0.16,    2.37,   107.98,     0.00,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegnw     (gN/m2)
      'Root':                    [    0.01,    0.11,     1.08,     0.00,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegnr     (gN/m2)
    },
    'MossDeathC':              178.19,    #  dmossc
    'CarbonShallow':           528.17,    #  shlwc
    'CarbonDeep':             1653.50,    #  deepc
    'CarbonMineralSum':      25915.00,    #  minec
    'OrganicNitrogenSum':     1513.10,    #  soln
    'AvailableNitrogenSum':       3.5,    #  avln
  },
  ## CMT04 - Shrub Tundra, calibration for Toolik climate.
  "shrub tundra": {
    'cmtnumber': 4,
                                 #    pft0     pft1      pft2     pft3     pft4     pft5      pft6      pft7      pft8     pft9   
                  'PFTNames':    ['Salix', 'Betula', 'Decid', 'EGreen', 'Sedges', 'Forbs', 'Grasses', 'Lichens', 'Feather', 'PFT9'],
    'GPPAllIgnoringNitrogen':    [  143.89,  288.65,   42.33,    9.03,    19.39,   28.44,    11.29,    16.45,     37.38,    0.00 ], # ingpp     (gC/m2/year)   GPP without N limitation
    'NPPAllIgnoringNitrogen':    [  107.92,  216.49,   39.57,    8.44,    18.13,   26.59,    10.56,     8.23,     18.69,    0.00 ], # innpp     (gC/m2/year)   NPP without N limitation 
    'NPPAll':                    [   71.95,  144.33,   21.16,    4.51,     9.69,   14.22,     5.65,     8.23,     18.69,    0.00 ], # npp       (gC/m2/year)   NPP with N limitation
    'Nuptake':                   [    0.81,    1.55,    0.29,    0.06,     0.14,    0.21,     0.08,     0.01,      0.54,    0.00 ], # nuptake   (gN/m2/year)
    'VegCarbon': {
      'Leaf':                    [   23.85,   38.01,   14.85,    1.30,     3.64,    5.33,     2.12,     18.7,     89.00,    0.00 ], # vegcl     (gC/m2)
      'Stem':                    [  194.07,  502.07,   30.67,    9.47,     0.00,    0.00,     0.00,      0.0,      0.00,    0.00 ], # vegcw     (gC/m2)
      'Root':                    [    6.10,   38.35,    2.25,    0.66,     6.06,    8.89,     3.53,      0.0,      0.00,    0.00 ], # vegcr     (gC/m2)
    },
    'VegStructuralNitrogen': {
      'Leaf':                    [    1.16,    1.84,    0.73,    0.03,     0.17,    0.25,     0.09,     0.67,      2.59,    0.00 ], # vegnl     (gN/m2)
      'Stem':                    [    1.94,    5.73,    0.66,    0.18,     0.00,    0.00,     0.00,     0.00,      0.00,    0.00 ], # vegnw     (gN/m2)
      'Root':                    [    0.08,    0.56,    0.04,    0.01,     0.12,    0.17,     0.07,     0.00,      0.00,    0.00 ], # vegnr     (gN/m2)
    },
    'MossDeathC':              178.00,    #  dmossc
    'CarbonShallow':          2240.00,    #  shlwc
    'CarbonDeep':             5853.00,    #  deepc
    'CarbonMineralSum':      37022.00,    #  minec
    'OrganicNitrogenSum':     1843.00,    #  soln
    'AvailableNitrogenSum':      3.93,    #  avln
  },
  ## CMT05 Tussock Tundra (updated 2/23/2016, JDC: GPPain, NPPain, NPPall, Nuptake, Veg from Shaver & Chapin 1991; 
  ## Assume Toolik C:N same as Council; then Veg N = Shaver & Chapin Veg C * (Council N / Council C); MossDeathC from CTucker data;
  ## Soils data from H. Genet Tussock.xls and Nat. Soil Carbon Database (averages for Tussock from few profiles around and at Toolik)
  "tussock tundra": {
    'cmtnumber': 5,
                                 #    pft0     pft1      pft2      pft3     pft4     pft5     pft6     pft7     pft8    pft9   
                  'PFTNames':    ['Betula', 'Decid', 'EGreen', 'Sedges', 'Forbs', 'Lichens', 'Feather', 'Sphag', 'PFT8', 'PFT9'],
    'GPPAllIgnoringNitrogen':    [   46.08,   1.333,   113.44,   201.06,   1.029,    8.88,   28.18,    15.01,    0.00,   0.00 ], # ingpp     (gC/m2/year)   GPP without N limitation
    'NPPAllIgnoringNitrogen':    [   23.04,   0.666,    56.72,   100.53,   0.515,    4.44,   14.09,     7.50,   0.00,   0.00 ], # innpp     (gC/m2/year)   NPP without N limitation
    'NPPAll':                    [   15.36,   0.444,    37.81,    67.02,   0.343,    2.96,    9.39,     5.00,   0.00,   0.00 ], # npp       (gC/m2/year)   NPP with N limitation
    'Nuptake':                   [   0.197,   0.082,    0.418,    0.731,   0.009,   0.074,   0.487,    0.376,   0.00,   0.00 ], # nuptake   (gN/m2/year)
    'VegCarbon': {
      'Leaf':                    [   12.02,   0.349,    42.42,    32.17,   0.165,    32.93,   57.26,   80.55,   0.00,   0.00 ], # vegcl     (gC/m2)
      'Stem':                    [  462.96,   3.716,   224.49,     0.00,   0.000,     0.00,    0.00,    0.00,   0.00,   0.00 ], # vegcw     (gC/m2)
      'Root':                    [  147.94,   1.188,   143.47,   147.65,   2.599,     0.00,    0.00,    0.00,   0.00,   0.00 ], # vegcr     (gC/m2)
    },
    'VegStructuralNitrogen': {
      'Leaf':                    [    0.36,   0.0069,    1.01,     0.82,    0.0058,    0.69,    1.33,    1.22,   0.00,   0.00 ], # vegnl     (gN/m2)
      'Stem':                    [    7.75,   0.0559,    2.57,     0.00,    0.0000,    0.00,    0.00,    0.00,   0.00,   0.00 ], # vegnw     (gN/m2)
      'Root':                    [    3.07,   0.0221,    2.01,     3.03,    0.0921,    0.00,    0.00,    0.00,   0.00,   0.00 ], # vegnr     (gN/m2)
    },
    'RE':                       25.00,    #  Respiration_ecosystem  ** JUNK VALUE FOR TESTING! **
    'NEE':                      10.00,     #  Net Ecosystem Exchange ** JUNK VALUE FOR TESTING! **
    'MossDeathC':              178.00,    #  dmossc
    'CarbonShallow':          3079.00,    #  shlwc
    'CarbonDeep':             7703.00,    #  deepc
    'CarbonMineralSum':      43404.00,    #  minec
    'OrganicNitrogenSum':     2206.00,    #  soln
    'AvailableNitrogenSum':      8.958,   #  avln
  },
  ## CMT06 - WETSEDGE TUNDRA - CALIBRATION WITH toolik climate (also barrow climate)  Lichen gpp was 0.375, npp 0.187, feather 8.4 sphg 2.9, 1.45
  "wet sedge tundra": {
    'cmtnumber': 6,
                                 #    pft0     pft1      pft2      pft3     pft4     pft5     pft6     pft7     pft8    pft9   
                  'PFTNames':    ['Decid', 'Sedges', 'Grasses', 'Forbs', 'Lichens', 'Feather', 'Sphag', 'PFT7', 'PFT8', 'PFT9'],
    'GPPAllIgnoringNitrogen':    [  11.833,  197.867,   42.987,   10.667,   3.375,  16.000,   6.000,    0.00,   0.00,   0.00 ], # ingpp     (gC/m2/year)   GPP without N limitation
    'NPPAllIgnoringNitrogen':    [  11.064,  187.005,   40.193,    9.973,   2.187,   8.000,   3.000,    0.00,   0.00,   0.00 ], # innpp     (gC/m2/year)   NPP without N limitation 
    'NPPAll':                    [   5.916,   98.933,   21.493,    5.333,   2.187,   8.000,   3.000,    0.00,   0.00,   0.00 ], # npp       (gC/m2/year)   NPP with N limitation
    'Nuptake':                   [   0.041,    1.758,    0.382,    0.089,    0.01,   0.033,   0.012,    0.00,   0.00,   0.00 ], # nuptake   (gN/m2/year)
    'VegCarbon': {
      'Leaf':                    [   2.000,   37.100,     8.06,    2.000,    2.00,   22.00,   23.00,    0.00,   0.00,   0.00 ], # vegcl     (gC/m2)
      'Stem':                    [   4.000,    0.000,     0.00,    0.000,    0.00,    0.00,    0.00,    0.00,   0.00,   0.00 ], # vegcw     (gC/m2)
      'Root':                    [   0.297,  161.280,    11.04,    3.200,    0.00,    0.00,    0.00,    0.00,   0.00,   0.00 ], # vegcr     (gC/m2)
    },
    'VegStructuralNitrogen': {
      'Leaf':                    [   0.006,    0.740,    0.161,    0.048,    0.12,    0.66,   0.012,    0.00,   0.00,   0.00 ], # vegnl     (gN/m2)
      'Stem':                    [   0.207,    0.000,    0.000,    0.000,    0.00,    0.00,   0.000,    0.00,   0.00,   0.00 ], # vegnw     (gN/m2)
      'Root':                    [   0.069,    2.776,    0.603,    0.130,    0.00,    0.00,   0.000,    0.00,   0.00,   0.00 ], # vegnr     (gN/m2)
    },
    'MossDeathC':              178.00,    #  dmossc
    'CarbonShallow':          3358.00,    #  shlwc
    'CarbonDeep':             8401.00,    #  deepc
    'CarbonMineralSum':      44252.00,    #  minec
    'OrganicNitrogenSum':     2698.00,    #  soln
    'AvailableNitrogenSum':      0.48,    #  avln
  },
  ## CMT07 - HEATH TUNDRA - CALIBRATION TOOLIK CLIMATE   New Values from Helene, input by Joy 8 16 2019, except Nuptake and soilC numbers and forb
  "heath tundra": {
    'cmtnumber': 7,
                                 #    pft0     pft1      pft2      pft3       pft4    pft5      pft6    pft7     pft8    pft9   
                  'PFTNames':    ['Decid',  'EGreen',  'Forbs',  'Lichens','Grasses','Moss',   'PFT6', 'PFT7',  'PFT8',  'PFT9'],
    'GPPAllIgnoringNitrogen':    [  37.204,   69.055,    2.667,    72.760,   0.100,   0.744,    0.00,    0.00,    0.00,   0.00 ], # ingpp (gC/m2/year) GPP Wout N limitation
    'NPPAllIgnoringNitrogen':    [  18.602,   34.528,    2.493,    36.380,   0.050,   0.372,    0.00,    0.00,    0.00,   0.00 ], # innpp (gC/m2/year) NPP Wout N limitation 
    'NPPAll':                    [  12.401,   23.018,    1.333,    24.253,   0.033,   0.248,    0.00,    0.00,    0.00,   0.00 ], # npp   (gC/m2/year) NPP with N limitation
    'Nuptake':                   [    0.09,    0.215,    0.165,     0.010,   0.080,   0.051,    0.00,    0.00,    0.00,   0.00 ], # nuptake   (gN/m2/year)
    'VegCarbon': {
      'Leaf':                    [   6.908,   28.501,    1.100,    80.844,   1.029,   0.827,    0.00,    0.00,    0.00,   0.00 ], # vegcl     (gC/m2)
      'Stem':                    [  30.483,   67.635,    0.000,     0.000,   0.000,   0.000,    0.00,    0.00,    0.00,   0.00 ], # vegcw     (gC/m2)
      'Root':                    [  21.405,   43.189,    0.833,     0.000,   0.921,   0.000,    0.00,    0.00,    0.00,   0.00 ], # vegcr     (gC/m2)
    },
    'VegStructuralNitrogen': {
      'Leaf':                    [   0.274,    0.736,    0.300,     1.708,   0.018,   0.028,    0.00,    0.00,    0.00,   0.00 ], # vegnl     (gN/m2)
      'Stem':                    [   0.807,    1.414,    0.000,     0.000,   0.000,   0.000,    0.00,    0.00,    0.00,   0.00 ], # vegnw     (gN/m2)
      'Root':                    [   0.362,    0.446,    0.030,     0.000,   0.011,   0.000,    0.00,    0.00,    0.00,   0.00 ], # vegnr     (gN/m2)
    },
    'MossDeathC':              178.00,    #  dmossc
    'CarbonShallow':          1065.00,    #  shlwc
    'CarbonDeep':             1071.00,    #  deepc
    'CarbonMineralSum':      32640.00,    #  minec
    'OrganicNitrogenSum':     1405.00,    #  soln
    'AvailableNitrogenSum':      0.17,    #  avln
  },
  ## Prepared from Vijay Patil work in the Yukon Flats with the mentoring of Eugenie Euskirchen- soil data comes from unknown
  "Shrubland": {
    'cmtnumber': 8,
                                 #      pft0      pft1      pft2      pft3     pft4     pft5     pft6     pft7      pft8    pft9   
                 # 'PFTNames':    ['D.Shrub', 'E.Shrub', 'D.Tree', 'E.Tree', 'Forbs', 'Gram', 'Feather', 'Lichen', 'Equisetum', 'Misc.'],
    'GPPAllIgnoringNitrogen':    [    166.12,     50.78,   319.62,   634.91,  120.25, 1086.39,   44.93,    8.40,    38.93,   0.00 ], # ingpp     (gC/m2/year)   GPP without N limitation
    'NPPAllIgnoringNitrogen':    [     83.06,     25.39,   159.81,   317.45,   60.12,  543.19,   22.46,    4.20,    19.47,   0.00 ], # innpp     (gC/m2/year)   NPP without N limitation 
    'NPPAll':                    [     55.37,     16.93,    85.46,   169.76,   32.15,  290.48,   22.46,    4.20,    10.41,   0.00 ], # npp       (gC/m2/year)   NPP with N limitation
    'Nuptake':                   [      0.92,      0.26,     0.96,     2.08,    0.43,    3.85,    0.41,    0.06,     0.12,   0.00 ], # nuptake   (gN/m2/year)
    'VegCarbon': {
      'Leaf':                    [     50.91,     23.05,    35.94,    27.16,    6.83,  259.09,   67.39,    4.44,     2.38,   0.00 ], # vegcl     (gC/m2)
      'Stem':                    [     87.33,     26.03,  1000.19,   919.68,    0.00,    0.00,    0.00,    0.00,     0.00,   0.00 ], # vegcw     (gC/m2)
      'Root':                    [     40.09,     12.27,   207.23,    85.22,   44.01,  452.05,    0.00,    0.00,     9.50,   0.00 ], # vegcr     (gC/m2)
    },
    'VegStructuralNitrogen': {
      'Leaf':                    [      2.12,      0.76,     1.11,     0.75,    0.49,   10.24,    2.48,    0.12,     0.09,   0.00 ], # vegnl     (gN/m2)
      'Stem':                    [      1.38,      0.49,    15.78,    11.83,    0.00,    0.00,    0.00,    0.00,     0.00,   0.00 ], # vegnw     (gN/m2)
      'Root':                    [      0.84,      0.25,     4.19,     1.69,    0.85,    8.61,    0.00,    0.00,     0.17,   0.00 ], # vegnr     (gN/m2)
    },
    'MossDeathC':              178.00,    #  dmossc
    'CarbonShallow':          3745.51,    #  shlwc
    'CarbonDeep':             7672.62,    #  deepc
    'CarbonMineralSum':      24235.14,    #  minec
    'OrganicNitrogenSum':     2177.91,    #  soln
    'AvailableNitrogenSum':       0.8,    #  avln
  },
 ## Prepared from EML??
  "Shrub tundra EML": {
    'cmtnumber': 9,
                                 #      pft0       pft1      pft2      pft3     pft4     pft5     pft6     pft7      pft8    pft9   
                  #'PFTNames':    ['Betnan', 'Carex', 'Ericoid', 'Feather', 'Lichen', 'Othmoss', 'Rubcha', 'Misc.', 'Misc.', 'Misc.'],
    'GPPAllIgnoringNitrogen':    [   1112.72,    200.06,   725.94,   364.58,   52.96,   55.43,  129.52,    0.00,    0.00,   0.00 ], # ingpp     (gC/m2/year)   GPP without N limitation
    'NPPAllIgnoringNitrogen':    [    834.54,    150.04,   544.46,   273.44,   39.72,   41.57,   97.14,    0.00,    0.00,   0.00 ], # innpp     (gC/m2/year)   NPP without N limitation 
    'NPPAll':                    [    556.36,    100.03,   362.97,   182.29,   26.48,   27.71,   64.76,    0.00,    0.00,   0.00 ], # npp       (gC/m2/year)   NPP with N limitation
    'Nuptake':                   [      6.68,      1.20,     4.36,     2.19,    0.32,    0.33,    0.78,    0.00,    0.00,   0.00 ], # nuptake   (gN/m2/year)
    'VegCarbon': {
      'Leaf':                    [    397.15,     19.63,   269.81,   588.10,  139.99,   89.41,    1.33,    0.00,    0.00,   0.00 ], # vegcl     (gC/m2)
      'Stem':                    [   1767.96,    171.73,  1362.49,     0.00,    0.00,    0.00,   82.22,    0.00,    0.00,   0.00 ], # vegcw     (gC/m2)
      'Root':                    [    203.43,     80.40,   245.86,     0.00,    0.00,    0.00,   63.43,    0.00,    0.00,   0.00 ], # vegcr     (gC/m2)
    },
    'VegStructuralNitrogen': {
      'Leaf':                    [      6.95,      0.57,     5.52,     8.75,    2.30,    0.50,   0.044,    0.00,    0.00,   0.00 ], # vegnl     (gN/m2)
      'Stem':                    [     26.05,      2.30,    13.91,     0.00,    0.00,    0.00,    1.30,    0.00,    0.00,   0.00 ], # vegnw     (gN/m2)
      'Root':                    [      3.33,      0.92,     2.47,     0.00,    0.00,    0.00,    1.27,    0.00,    0.00,   0.00 ], # vegnr     (gN/m2)
    },
    'MossDeathC':                0.00,    #  dmossc928.0
    'CarbonShallow':          4365.66,    #  shlwc
    'CarbonDeep':            12814.11,    #  deepc
    'CarbonMineralSum':      36329.49,    #  minec
    'OrganicNitrogenSum':     1904.10,    #  soln
    'AvailableNitrogenSum':      4.00,    #  avln
  },
  ## Prepared from EML??  Need Nuptake   created from excel file sent by Helene August 2022
  "Tussock tundra EML": {
    'cmtnumber': 21,
                                 #   pft0       pft1      pft2     pft3     pft4     pft5     pft6     pft7      pft8    pft9
                  'PFTNames':    ['Decidsh','Egreensh', 'Sedge', 'Forbs', 'Lichen', 'Omoss', 'Sphag',  'PFT7', 'PFT8', 'PFT9'],
    'GPPAllIgnoringNitrogen':    [  21.831,  132.247,   301.40,    1.792,  15.469,  49.072,   26.139,    0.00,   0.00,   0.00 ], # ingpp    (gC/m2/year)  GPP without N limitation
    'NPPAllIgnoringNitrogen':    [  10.915,   66.124,   150.70,    0.896,   7.735,  24.536,   13.070,    0.00,   0.00,   0.00 ], # innpp    (gC/m2/year)  NPP without N limitation
    'NPPAll':                    [   7.277,   44.082,   100.47,    0.598,   5.156,  16.357,    8.713,    0.00,   0.00,   0.00 ], # npp       (gC/m2/year)  NPP with N limitation
    'Nuptake':                   [   0.043,    0.429,    0.930,    0.011,   0.040,   0.126,    0.086,    0.00,   0.00,   0.00 ], # nuptake   (gN/m2/year)
    'VegCarbon': {
      'Leaf':                    [   2.464,   33.925,   118.20,    0.165,   24.75,  133.78,    7.088,    0.00,   0.00,   0.00 ], # vegcl     (gC/m2)
      'Stem':                    [  71.674,  230.388,     0.00,    0.000,    0.00,    0.00,     0.00,    0.00,   0.00,   0.00 ], # vegcw     (gC/m2)
      'Root':                    [ 105.495,  169.930,   205.57,    2.599,    0.00,    0.00,     0.00,    0.00,   0.00,   0.00 ], # vegcr     (gC/m2)
    },
    'VegStructuralNitrogen': {
      'Leaf':                    [   0.044,    0.660,    2.189,    0.006,    0.19,   2.065,    0.139,    0.00,   0.00,   0.00 ], # vegnl     (gN/m2)
      'Stem':                    [   0.892,    1.861,    0.000,    0.000,    0.00,    0.00,    0.000,    0.00,   0.00,   0.00 ], # vegnw     (gN/m2)
      'Root':                    [   1.271,    1.609,    3.180,    0.092,    0.00,    0.00,    0.000,    0.00,   0.00,   0.00 ], # vegnr     (gN/m2)
    },
    'MossDeathC':                0.00,    #  dmossc
    'CarbonShallow':          4365.66,    #  shlwc
    'CarbonDeep':            12814.11,    #  deepc
    'CarbonMineralSum':      43416.95,    #  minec
    'OrganicNitrogenSum':     1998.37,    #  soln
    'AvailableNitrogenSum':      1.70,    #  avln
  },
  ## CMT 31 - BOREAL BOG - CALIBRATION BONANZA CREEK THERMOKARST BOG - EUSKIRCHEN TOWER BZB - B. MAGLIO
   "Boreal Bog": {
     'cmtnumber': 31,
                                #   pft0          pft1           pft2           pft3          pft4  pft5  pft6  pft7  pft8  pft9   
                                #   Sphag         Eshrub         Sedge          Dshrub        Misc. Misc. Misc. Misc. Misc. Misc.
     'GPPAllIgnoringNitrogen':    [   479.2101837,   92.14549605,    118.8998794,     30.18051452,  0,    0,   0,      0,      0,      0 ], # ingpp     (gC/m2/year)   GPP without N limitation 
     'NPPAllIgnoringNitrogen':    [   239.6050919,   46.07274803,    59.4499397,    15.09025726,  0,   0,    0,    0,      0,      0 ], # innpp     (gC/m2/year)   NPP without N limitation
     'NPPAll':                    [   191.6840735,   36.85819842,    47.55995176,     12.07220581,    0,   0,      0,      0,      0,      0 ], # npp       (gC/m2/year)   NPP with N limitation
     'Nuptake':                   [   4.259646078,     0.9450820108, 1.219485943,     0.3095437387, 0,     0,      0,      0,      0,      0 ], # nuptake   (gN/m2/year)
     'VegCarbon': {
       'Leaf':                    [   293.995652,      8.9926087,    8.859734807,     6.406304385,    0,   0,      0,    0,      0,    0 ], # vegcl     (gC/m2) 
       'Stem':                    [   0,             41.63577828,    0,               11.01434789,  0,    0,     0,      0,      0,      0 ], # vegcw     (gC/m2)
       'Root':                    [   0,             39.29770002,    38.51852619,     5.057608725,    0,     0,      0,      0,      0,      0 ], # vegcr     (gC/m2)
     },
     'VegStructuralNitrogen': {
       'Leaf':                    [   3.665087447,   0.3034250666,    0.3543893923,    0.2350333634,0,     0,      0,    0,      0,      0 ], # vegnl     (gN/m2)
       'Stem':                    [   0,             0.7083564987,    0,               0.1911383582, 0,   0,      0,      0,      0,      0 ], # vegnw     (gN/m2)
       'Root':                    [   0,             0.9767043623,    1.041604278,     0.1257017205, 0,   0,      0,      0,      0,      0 ], # vegnr     (gN/m2)
    },
    'MossDeathC':                    0.00,    #  dmossc ## IGNORE
    'CarbonShallow':                 8732,    #  shlwc 
    'CarbonDeep':                    24092,    #  deepc 
    'CarbonMineralSum':              61545,    #  minec 
    'OrganicNitrogenSum':            4138,    #  soln  
    'AvailableNitrogenSum':          7.134,     #  avln 
    # 'EcosystemRespiration':          596,
    },
  ## CMT44 - SHRUB TUNDRA - CALIBRATION SEWARD PENINSULA CLIMATE (COUNCIL)   JOY Aug 17 2019 changed BETULA for Kougarok
  "shrub tundra kougarok": {
    'cmtnumber': 44,
                                 #    pft0     pft1      pft2     pft3     pft4     pft5      pft6      pft7      pft8     pft9   
                  'PFTNames':    [ 'Salix', 'Betula', 'Decid.', 'E.green','Sedges','Forbs','Grasses','Lichens','Feather.', 'Misc.'],
    'GPPAllIgnoringNitrogen':    [  143.89,  167.82,   42.33,    9.03,    19.39,   28.44,    11.29,    16.45,     37.38,    0.00 ], # ingpp     (gC/m2/year)   GPP without N limitation
    'NPPAllIgnoringNitrogen':    [  107.92,  125.87,   39.57,    8.44,    18.13,   26.59,    10.56,     8.23,     18.69,    0.00 ], # innpp     (gC/m2/year)   NPP without N limitation 
    'NPPAll':                    [   71.95,   83.91,   21.16,    4.51,     9.69,   14.22,     5.65,     8.23,     18.69,    0.00 ], # npp       (gC/m2/year)   NPP with N limitation
    'Nuptake':                   [    0.81,    0.90,    0.29,    0.06,     0.14,    0.21,     0.08,     0.01,      0.54,    0.00 ], # nuptake   (gN/m2/year)
    'VegCarbon': {
      'Leaf':                    [   23.85,   22.10,   14.85,    1.30,     3.64,    5.33,     2.12,     18.7,     89.00,    0.00 ], # vegcl     (gC/m2)
      'Stem':                    [  194.07,  291.90,   30.67,    9.47,     0.00,    0.00,     0.00,      0.0,      0.00,    0.00 ], # vegcw     (gC/m2)
      'Root':                    [    6.10,   22.30,    2.25,    0.66,     6.06,    8.89,     3.53,      0.0,      0.00,    0.00 ], # vegcr     (gC/m2)
    },
    'VegStructuralNitrogen': {
      'Leaf':                    [    1.16,    1.07,    0.73,    0.03,     0.17,    0.25,     0.09,     0.67,      2.59,    0.00 ], # vegnl     (gN/m2)
      'Stem':                    [    1.94,    3.33,    0.66,    0.18,     0.00,    0.00,     0.00,     0.00,      0.00,    0.00 ], # vegnw     (gN/m2)
      'Root':                    [    0.08,    0.33,    0.04,    0.01,     0.12,    0.17,     0.07,     0.00,      0.00,    0.00 ], # vegnr     (gN/m2)
    },
    'MossDeathC':              178.00,    #  dmossc
    'CarbonShallow':          2240.00,    #  shlwc
    'CarbonDeep':             5853.00,    #  deepc
    'CarbonMineralSum':      37022.00,    #  minec
    'OrganicNitrogenSum':     1843.00,    #  soln
    'AvailableNitrogenSum':      3.93,    #  avln
  },

}

def cmtbynumber(cmtnum):
  '''
  Find target values for a single CMT based on the number only.

  Parameters
  ----------
  cmtnumber : int
    The integer value for the CMT to return data for.

  Returns
  -------
  data : dict
    A multi-level dict structure with calibration target data for a single CMT.

  Raises
  ------
  RuntimeError if the cmtnum is not found anywhere in the calibration_targets
  data structure.
  '''
  for k, v in calibration_targets.items():
    if 'cmtnumber' in v.keys():
      if v['cmtnumber'] == cmtnum:
        return {k:v}
  raise RuntimeError("Can't find cmtnumber: {}".format(cmtnum))


def cmtnames():
  '''returns a list of community names'''
  return [key for key in list(calibration_targets.keys())]

def cmtnumbers():
  '''returns the cmt number for each known commnunity'''
  return [data['cmtnumber'] for k, data in calibration_targets.items()]

def caltargets2prettystring():
  '''returns a formatted string with one cmt name/number pair per line'''
  s = ''
  for key, value in calibration_targets.items():
    s += "{1:02d} {0:}\n".format(key, value['cmtnumber'])
  s = s[0:-1] # trim the last new line
  return s

def caltargets2prettystring2():
  '''returns sorted (by number) formatted string with '# - name' per line'''
  l = [
      '%s - %s' % (data['cmtnumber'], k)
      for k, data in
        calibration_targets.items()
  ]

  sl = sorted(l)
  return '\n'.join(sl)

def caltargets2prettystring3():
  '''returns a space separated list of (#)name pairs, sorted by number'''
  l = [
      '(%s)%s' % (data['cmtnumber'], k)
      for k, data in
        calibration_targets.items()
  ]

  sl = sorted(l)
  return ' '.join(sl)


def toxl():
  ''' A total hack attempt at writing out an excel workbook from the values
  that are hardcoded above in the calibraiton_targets dict. Actually kinda 
  works though...'''

  import xlwt

  font0 = xlwt.Font()
  font0.name = 'Times New Roman'
  font0.colour_index = 2
  font0.bold = True

  style0 = xlwt.XFStyle()
  style0.font = font0

  wb = xlwt.Workbook()

  nzr = 5
  nzc = 5


  for community, cmtdata in calibration_targets.items():
    ws = wb.add_sheet(community)

    #        r  c
    ws.write(0, 0, 'community number:', style0)
    ws.write(0, 1, cmtdata['cmtnumber'])

    r = nzr
    for key, data in cmtdata.items():
      print("OPERATING ON: %s" % key)
      if key == 'cmtnumber':
        pass
      else:
        ws.write(r, 1, key) # col 1, the main key
        print("row: %s col: %s key: %s" % (r, 1, key))
        if type(data) == list:
          for col, pftvalue in enumerate(data):
            ws.write(r, col + nzc, pftvalue)
            print("row: %s col: %s pftvalue: %s" % (r, col + nzc, pftvalue))

          r = r + 1
            
        elif type(data) == dict:
          for compartment, pftvals in data.items():
            ws.write(r, 2, compartment)
            print("row: %s col: %s compartment: %s" % (r, 2, compartment))

            for col, pftvalue in enumerate(pftvals):
              ws.write(r, col + nzc, pftvalue)
              print("row: %s col: %s pftvalue: %s" % (r, col + nzc, pftvalue))

            r = r + 1
        elif type(data) == int or type(data) == float:
          print("WTF")
          ws.write(r, nzc, data)
          print("row: %s col: %s data: %s" % (r, nzc, data))
          r = r + 1



  wb.save('example.xls')




def frmxl():
  print("NOT IMPLEMENTED")

if __name__ == '__main__':
  print("Nothing happening here yet...")

  # for testing:
  toxl()






