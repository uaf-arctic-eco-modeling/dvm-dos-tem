#!/usr/bin/env python

# could add code here to load up calibration_targets variable from the
# contents of an excel file...? or just plain csv?

calibration_targets = {
  ## WARNING: JUNK, PLACEHOLDER VALUES! USE AT YOUR OWN RISK!
  "BLANK": {
    'cmtnumber': 0,
                                 #    pft0     pft1      pft2      pft3     pft4     pft5     pft6     pft7     pft8    pft9   
                                 #    Misc.    Misc.     Misc.     Misc.    Misc.    Misc.    Misc.    Misc.    Misc.   Misc.
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
  ## WARNING: JUNK, PLACEHOLDER VALUES! USE AT YOUR OWN RISK!
  "black spruce forest": {
    'cmtnumber': 1,
                                 #    pft0     pft1      pft2      pft3     pft4     pft5     pft6     pft7     pft8    pft9   
                  'PFTNames':    ['BlackSpr', 'Decid', 'DecidShrub', 'EGreen', 'Sphag', 'Feather', 'Moss', 'Lichen', 'Forbs', 'Sedge'],
    'GPPAllIgnoringNitrogen':    [  468.74,   81.73,    27.51,    22.23,   29.85,   28.44,   11.29,    7.75,   42.18,   0.00 ], # ingpp     (gC/m2/year)   GPP without N limitation
    'NPPAllIgnoringNitrogen':    [  200.39,   61.30,    25.73,    20.79,   27.91,   26.59,   10.56,    7.25,   39.44,   0.00 ], # innpp     (gC/m2/year)   NPP without N limitation 
    'NPPAll':                    [  133.59,   40.87,    13.76,    11.12,   14.92,   14.22,    5.65,    3.87,   21.09,   0.00 ], # npp       (gC/m2/year)   NPP with N limitation
    'Nuptake':                   [    0.67,    0.42,     0.17,     0.17,    0.22,    0.21,    0.08,    0.01,    0.24,   0.00 ], # nuptake   (gN/m2/year)
    'VegCarbon': {
      'Leaf':                    [  121.92,   13.17,     8.85,     6.03,    5.60,    5.33,    2.12,   35.22,  100.35,   0.00 ], # vegcl     (gC/m2)
      'Stem':                    [ 1519.45,  129.81,    76.07,    13.10,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegcw     (gC/m2)
      'Root':                    [  410.34,    4.00,     4.20,     1.17,    9.33,    8.89,    3.53,    0.00,    0.00,   0.00 ], # vegcr     (gC/m2)
    },
    'VegStructuralNitrogen': {
      'Leaf':                    [    1.05,    0.53,     0.38,     0.15,    0.26,    0.25,    0.09,    0.99,    2.31,   0.00 ], # vegnl     (gN/m2)
      'Stem':                    [    2.74,    3.05,     3.10,     0.23,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegnw     (gN/m2)
      'Root':                    [    3.52,    0.06,     0.06,     0.01,    0.19,    0.17,    0.07,    0.00,    0.00,   0.00 ], # vegnr     (gN/m2)
    },
    'MossDeathC':              178.00,    #  dmossc
    'CarbonShallow':          1783.00,    #  shlwc
    'CarbonDeep':             5021.00,    #  deepc
    'CarbonMineralSum':       9000.00,    #  minec
    'OrganicNitrogenSum':      363.00,    #  soln
    'AvailableNitrogenSum':      0.76,    #  avln
  },
  ## WARNING: JUNK, PLACEHOLDER VALUES! USE AT YOUR OWN RISK!
  "white spruce forest": {
    'cmtnumber': 2,
                                 #    pft0     pft1      pft2      pft3     pft4     pft5     pft6     pft7     pft8    pft9   
                                 #  Spruce    Salix    Decid.   E.green   Sedges    Forbs  Grasses  Lichens  Feather.   Misc.
    'GPPAllIgnoringNitrogen':    [  468.74,   81.73,    27.51,    22.23,   29.85,   28.44,   11.29,    7.75,   42.18,   0.00 ], # ingpp     (gC/m2/year)   GPP without N limitation
    'NPPAllIgnoringNitrogen':    [  200.39,   61.30,    25.73,    20.79,   27.91,   26.59,   10.56,    7.25,   39.44,   0.00 ], # innpp     (gC/m2/year)   NPP without N limitation 
    'NPPAll':                    [  133.59,   40.87,    13.76,    11.12,   14.92,   14.22,    5.65,    3.87,   21.09,   0.00 ], # npp       (gC/m2/year)   NPP with N limitation
    'Nuptake':                   [    0.67,    0.42,     0.17,     0.17,    0.22,    0.21,    0.08,    0.01,    0.24,   0.00 ], # nuptake   (gN/m2/year)
    'VegCarbon': {
      'Leaf':                    [  121.92,   13.17,     8.85,     6.03,    5.60,    5.33,    2.12,   35.22,  100.35,   0.00 ], # vegcl     (gC/m2)
      'Stem':                    [ 1519.45,  129.81,    76.07,    13.10,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegcw     (gC/m2)
      'Root':                    [  410.34,    4.00,     4.20,     1.17,    9.33,    8.89,    3.53,    0.00,    0.00,   0.00 ], # vegcr     (gC/m2)
    },
    'VegStructuralNitrogen': {
      'Leaf':                    [    1.05,    0.53,     0.38,     0.15,    0.26,    0.25,    0.09,    0.99,    2.31,   0.00 ], # vegnl     (gN/m2)
      'Stem':                    [    2.74,    3.05,     3.10,     0.23,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegnw     (gN/m2)
      'Root':                    [    3.52,    0.06,     0.06,     0.01,    0.19,    0.17,    0.07,    0.00,    0.00,   0.00 ], # vegnr     (gN/m2)
    },
    'MossDeathC':              178.00,    #  dmossc
    'CarbonShallow':          1783.00,    #  shlwc
    'CarbonDeep':             5021.00,    #  deepc
    'CarbonMineralSum':       9000.00,    #  minec
    'OrganicNitrogenSum':      363.00,    #  soln
    'AvailableNitrogenSum':      0.76,    #  avln
  },
  ## WARNING: JUNK, PLACEHOLDER VALUES! USE AT YOUR OWN RISK!
  "deciduous forest": {
    'cmtnumber': 3,
                                 #    pft0     pft1      pft2      pft3     pft4     pft5     pft6     pft7     pft8    pft9   
                                 #  Spruce    Salix    Decid.   E.green   Sedges    Forbs  Grasses  Lichens  Feather.   Misc.
    'GPPAllIgnoringNitrogen':    [  468.74,   81.73,    27.51,    22.23,   29.85,   28.44,   11.29,    7.75,   42.18,   0.00 ], # ingpp     (gC/m2/year)   GPP without N limitation
    'NPPAllIgnoringNitrogen':    [  200.39,   61.30,    25.73,    20.79,   27.91,   26.59,   10.56,    7.25,   39.44,   0.00 ], # innpp     (gC/m2/year)   NPP without N limitation 
    'NPPAll':                    [  133.59,   40.87,    13.76,    11.12,   14.92,   14.22,    5.65,    3.87,   21.09,   0.00 ], # npp       (gC/m2/year)   NPP with N limitation
    'Nuptake':                   [    0.67,    0.42,     0.17,     0.17,    0.22,    0.21,    0.08,    0.01,    0.24,   0.00 ], # nuptake   (gN/m2/year)
    'VegCarbon': {
      'Leaf':                    [  121.92,   13.17,     8.85,     6.03,    5.60,    5.33,    2.12,   35.22,  100.35,   0.00 ], # vegcl     (gC/m2)
      'Stem':                    [ 1519.45,  129.81,    76.07,    13.10,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegcw     (gC/m2)
      'Root':                    [  410.34,    4.00,     4.20,     1.17,    9.33,    8.89,    3.53,    0.00,    0.00,   0.00 ], # vegcr     (gC/m2)
    },
    'VegStructuralNitrogen': {
      'Leaf':                    [    1.05,    0.53,     0.38,     0.15,    0.26,    0.25,    0.09,    0.99,    2.31,   0.00 ], # vegnl     (gN/m2)
      'Stem':                    [    2.74,    3.05,     3.10,     0.23,    0.00,    0.00,    0.00,    0.00,    0.00,   0.00 ], # vegnw     (gN/m2)
      'Root':                    [    3.52,    0.06,     0.06,     0.01,    0.19,    0.17,    0.07,    0.00,    0.00,   0.00 ], # vegnr     (gN/m2)
    },
    'MossDeathC':              178.00,    #  dmossc
    'CarbonShallow':          1783.00,    #  shlwc
    'CarbonDeep':             5021.00,    #  deepc
    'CarbonMineralSum':       9000.00,    #  minec
    'OrganicNitrogenSum':      363.00,    #  soln
    'AvailableNitrogenSum':      0.76,    #  avln
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
    'GPPAllIgnoringNitrogen':    [  106.20,   54.13,   208.50,   390.40,   7.016,  286.80,  191.80,   172.60,   0.00,   0.00 ], # ingpp     (gC/m2/year)   GPP without N limitation
    'NPPAllIgnoringNitrogen':    [   59.00,   27.06,   104.20,   195.20,   3.508,  136.60,   94.97,    85.42,   0.00,   0.00 ], # innpp     (gC/m2/year)   NPP without N limitation 
    'NPPAll':                    [   34.71,   14.47,    55.74,   104.40,   1.876,   68.29,   48.70,    43.81,   0.00,   0.00 ], # npp       (gC/m2/year)   NPP with N limitation
    'Nuptake':                   [   0.197,   0.082,    0.418,    0.731,   0.009,   0.074,   0.487,    0.376,   0.00,   0.00 ], # nuptake   (gN/m2/year)
    'VegCarbon': {
      'Leaf':                    [    4.14,   15.01,    74.61,   105.25,    0.85,    42.70,   37.22,   86.84,   0.00,   0.00 ], # vegcl     (gC/m2)
      'Stem':                    [   69.78,   30.42,   127.74,     0.00,    0.00,     0.00,    0.00,    0.00,   0.00,   0.00 ], # vegcw     (gC/m2)
      'Root':                    [    4.54,    5.41,    11.84,   166.51,   11.71,     0.00,    0.00,    0.00,   0.00,   0.00 ], # vegcr     (gC/m2)
    },
    'VegStructuralNitrogen': {
      'Leaf':                    [    0.13,    0.47,     1.58,     4.72,    0.03,     0.69,    0.56,    1.49,   0.00,   0.00 ], # vegnl     (gN/m2)
      'Stem':                    [    1.13,    0.49,     2.06,     0.00,    0.00,     0.00,    0.00,    0.00,   0.00,   0.00 ], # vegnw     (gN/m2)
      'Root':                    [    1.02,    1.21,     1.77,     7.48,    1.81,     0.00,    0.00,    0.00,   0.00,   0.00 ], # vegnr     (gN/m2)
    },
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
 ## Prepared from EML??
  "Tussock tundra EML": {
    'cmtnumber': 10,
                                 #      pft0       pft1      pft2      pft3     pft4     pft5     pft6     pft7      pft8    pft9   
                  #'PFTNames':    ['Betnan', 'Carex', 'Ericoid', 'Erivag', 'Feather', 'Lichen', 'Othmoss', 'Rubcha', 'Sphag.', 'Misc.'],
    'GPPAllIgnoringNitrogen':    [     80.64,    300.26,   572.29,   657.57,   0.133,   46.58,  415.07,  154.58,    9.03,   0.00 ], # ingpp     (gC/m2/year)   GPP without N limitation
    'NPPAllIgnoringNitrogen':    [     60.48,    225.19,   429.22,   493.18,   0.100,   34.94,  311.31,  115.93,    6.77,   0.00 ], # innpp     (gC/m2/year)   NPP without N limitation 
    'NPPAll':                    [     40.32,    150.13,   286.14,   328.79,   0.066,   23.29,  207.54,   77.29,    4.51,   0.00 ], # npp       (gC/m2/year)   NPP with N limitation
    'Nuptake':                   [      0.48,      1.80,     3.43,     3.95,  0.0008,    0.28,    2.49,    0.93,    0.05,   0.00 ], # nuptake   (gN/m2/year)
    'VegCarbon': {
      'Leaf':                    [      8.71,     18.65,   228.12,   269.81,   0.214,  123.12,  669.55,    0.71,   35.44,   0.00 ], # vegcl     (gC/m2)
      'Stem':                    [     11.64,    243.40,  1089.93,   226.60,   0.000,    0.00,    0.00,   22.40,    0.00,   0.00 ], # vegcw     (gC/m2)
      'Root':                    [     31.60,    140.91,   187.16,    58.98,   0.000,    0.00,    0.00,   76.58,    0.00,   0.00 ], # vegcr     (gC/m2)
    },
    'VegStructuralNitrogen': {
      'Leaf':                    [      0.15,      0.52,     4.46,     6.98,  0.0043,    0.95,   10.34,   0.027,    0.70,   0.00 ], # vegnl     (gN/m2)
      'Stem':                    [      0.11,      3.01,     9.77,     6.67,   0.000,    0.00,    0.00,    0.42,    0.00,   0.00 ], # vegnw     (gN/m2)
      'Root':                    [      0.34,      1.52,     1.77,     0.65,   0.000,    0.00,    0.00,    1.08,    0.00,   0.00 ], # vegnr     (gN/m2)
    },
    'MossDeathC':                0.00,    #  dmossc
    'CarbonShallow':          4365.66,    #  shlwc
    'CarbonDeep':            12814.11,    #  deepc
    'CarbonMineralSum':      43416.95,    #  minec
    'OrganicNitrogenSum':     1998.37,    #  soln
    'AvailableNitrogenSum':      1.70,    #  avln
  },
  ## CMT44 - SHRUB TUNDRA - CALIBRATION SEWARD PENINSULA CLIMATE (COUNCIL)   JOY Aug 17 2019 changed BETULA for Kougaruk  
  "shrub tundra": {
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

def cmtnames():
  '''returns a list of community names'''
  return [key for key in calibration_targets.keys()]

def cmtnumbers():
  '''returns the cmt number for each known commnunity'''
  return [data['cmtnumber'] for k, data in calibration_targets.iteritems()]

def caltargets2prettystring():
  '''returns a formatted string with one cmt name/number pair per line'''
  s = ''
  for key, value in calibration_targets.iteritems():
    s += "{1:02d} {0:}\n".format(key, value['cmtnumber'])
  s = s[0:-1] # trim the last new line
  return s

def caltargets2prettystring2():
  '''returns sorted (by number) formatted string with '# - name' per line'''
  l = [
      '%s - %s' % (data['cmtnumber'], k)
      for k, data in
        calibration_targets.iteritems()
  ]

  sl = sorted(l)
  return '\n'.join(sl)

def caltargets2prettystring3():
  '''returns a space separated list of (#)name pairs, sorted by number'''
  l = [
      '(%s)%s' % (data['cmtnumber'], k)
      for k, data in
        calibration_targets.iteritems()
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


  for community, cmtdata in calibration_targets.iteritems():
    ws = wb.add_sheet(community)

    #        r  c
    ws.write(0, 0, 'community number:', style0)
    ws.write(0, 1, cmtdata['cmtnumber'])

    r = nzr
    for key, data in cmtdata.iteritems():
      print "OPERATING ON: %s" % key
      if key == 'cmtnumber':
        pass
      else:
        ws.write(r, 1, key) # col 1, the main key
        print "row: %s col: %s key: %s" % (r, 1, key)
        if type(data) == list:
          for col, pftvalue in enumerate(data):
            ws.write(r, col + nzc, pftvalue)
            print "row: %s col: %s pftvalue: %s" % (r, col + nzc, pftvalue)

          r = r + 1
            
        elif type(data) == dict:
          for compartment, pftvals in data.iteritems():
            ws.write(r, 2, compartment)
            print "row: %s col: %s compartment: %s" % (r, 2, compartment)

            for col, pftvalue in enumerate(pftvals):
              ws.write(r, col + nzc, pftvalue)
              print "row: %s col: %s pftvalue: %s" % (r, col + nzc, pftvalue)

            r = r + 1
        elif type(data) == int or type(data) == float:
          print "WTF"
          ws.write(r, nzc, data)
          print "row: %s col: %s data: %s" % (r, nzc, data)
          r = r + 1



  wb.save('example.xls')




def frmxl():
  print "NOT IMPLEMENTED"

if __name__ == '__main__':
  print "Nothing happening here yet..."

  # for testing:
  toxl()






