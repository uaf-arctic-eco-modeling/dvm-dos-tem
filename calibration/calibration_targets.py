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
  ## Updated by EE (April, May, June 2017)
  "shrub tundra": {
    'cmtnumber': 4,
                                 #    pft0     pft1      pft2     pft3     pft4     pft5      pft6      pft7      pft8     pft9   
                                 #  Salix    Betula    Decid.   E.green   Sedges    Forbs   Grasses   Lichens   Feather.    Misc.
    'GPPAllIgnoringNitrogen':    [  143.89,  288.65,   42.33,    9.03,    19.39,   28.44,    11.29,    16.45,     37.38,    0.00 ], # ingpp     (gC/m2/year)   GPP without N limitation
    'NPPAllIgnoringNitrogen':    [  107.92,  216.49,   39.57,    8.44,    18.13,   26.59,    10.56,    15.38,     34.95,    0.00 ], # innpp     (gC/m2/year)   NPP without N limitation 
    'NPPAll':                    [   71.95,  144.33,   21.16,    4.51,     9.69,   14.22,     5.65,     8.23,     18.69,    0.00 ], # npp       (gC/m2/year)   NPP with N limitation
    'Nuptake':                   [    0.81,    1.55,    0.29,    0.06,     0.14,    0.21,     0.08,     0.01,      0.54,    0.00 ], # nuptake   (gN/m2/year)
    'VegCarbon': {
      'Leaf':                    [   23.85,    38.1,   14.85,    1.30,     3.64,    5.33,     2.12,     18.7,     89.00,    0.00 ], # vegcl     (gC/m2)
      'Stem':                    [  194.07,  502.07,   30.67,    9.47,      0.0,     0.0,      0.0,      0.0,       0.0,     0.0 ], # vegcw     (gC/m2)
      'Root':                    [    6.10,   38.35,    2.25,    0.66,     6.06,    8.89,     3.53,      0.0,       0.0,     0.0 ], # vegcr     (gC/m2)
    },
    'VegStructuralNitrogen': {
      'Leaf':                    [    1.16,    1.84,    0.73,    0.03,     0.17,    0.25,     0.09,     0.67,      2.59,     0.0 ], # vegnl     (gN/m2)
      'Stem':                    [    1.94,    5.73,    0.66,    0.18,      0.0,     0.0,      0.0,      0.0,       0.0,     0.0 ], # vegnw     (gN/m2)
      'Root':                    [    0.08,    0.56,    0.04,    0.01,     0.12,    0.17,     0.07,      0.0,       0.0,     0.0 ], # vegnr     (gN/m2)
    },
    'MossDeathC':              178.00,    #  dmossc
    'CarbonShallow':          2340.00,    #  shlwc
    'CarbonDeep':            5853.00,    #  deepc
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
                                 #  betula    decid     egreen    sedge    forb     lichen   feather   sphag    blank   blank
    'GPPAllIgnoringNitrogen':    [   106.2,   54.13,    208.5,    390.4,   7.016,   286.8,   191.8,    172.6,   0.00,   0.00 ], # ingpp     (gC/m2/year)   GPP without N limitation
    'NPPAllIgnoringNitrogen':    [   59.00,   27.06,    104.2,    195.2,   3.508,   136.6,   94.97,    85.42,   0.00,   0.00 ], # innpp     (gC/m2/year)   NPP without N limitation 
    'NPPAll':                    [   34.71,   14.47,    55.74,    104.4,   1.876,   68.29,   48.70,    43.81,   0.00,   0.00 ], # npp       (gC/m2/year)   NPP with N limitation
    'Nuptake':                   [   0.197,   0.082,    0.418,    0.731,   0.009,   0.074,   0.487,    0.376,   0.00,   0.00 ], # nuptake   (gN/m2/year)
    'VegCarbon': {
      'Leaf':                    [    4.14,   15.01,    74.61,   105.25,    0.85,    42.70,   37.22,   86.84,   0.00,   0.00 ], # vegcl     (gC/m2)
      'Stem':                    [   69.78,   30.42,   127.74,     0.00,    0.00,     0.00,    0.00,    0.00,   0.00,   0.00 ], # vegcw     (gC/m2)
      'Root':                    [    4.54,    5.41,    11.84,   166.51,   11.71,     0.00,    0.00,    0.00,   0.00,   0.00 ], # vegcr     (gC/m2)
    },
    'VegStructuralNitrogen': {
      'Leaf':                    [    0.13,    0.47,     1.58,     4.72,    0.03,     0.69,    0.56,    1.49,   0.00,   0.00 ], # vegnl     (gN/m2)
      'Stem':                    [    1.13,    0.49,     2.06,    0.000,   0.000,     0.00,    0.00,    0.00,   0.00,   0.00 ], # vegnw     (gN/m2)
      'Root':                    [    1.02,    1.21,     1.77,     7.48,    1.81,     0.00,    0.00,    0.00,   0.00,   0.00 ], # vegnr     (gN/m2)
    },
    'MossDeathC':              178.00,    #  dmossc
    'CarbonShallow':          3079.00,    #  shlwc
    'CarbonDeep':             7703.00,    #  deepc
    'CarbonMineralSum':      43404.00,    #  minec
    'OrganicNitrogenSum':     2206.00,    #  soln
    'AvailableNitrogenSum':     8.958,    #  avln
  },
  ## WARNING: JUNK, PLACEHOLDER VALUES! USE AT YOUR OWN RISK!
  "wet sedge tundra": {
    'cmtnumber': 6,
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
  "heath tundra": {
    'cmtnumber': 7,
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
  "maritime forest": {
    'cmtnumber': 8,
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






