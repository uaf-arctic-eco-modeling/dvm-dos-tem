#!/usr/bin/env python
# coding: utf-8

import netCDF4 as nc
import numpy as np
from matplotlib import pyplot as plt


run_name='poker_flats_test'


get_ipython().run_line_magic('cd', '/work')


# Cleanup:
get_ipython().system('rm -r /data/workflows/single_run')


#set working directory
get_ipython().system('scripts/setup_working_directory.py  --input-data-path /data/input-catalog/caribou-poker/  /data/workflows/poker_flats_test/')


get_ipython().system('ls ../data/input-catalog/caribou-poker/')


get_ipython().system('ls ../data/workflows/poker_flats_test/')


# setup runmask
# caribou creek (y x) = 3 0
# poker flats (y x) = 0 1
get_ipython().system('runmask-util.py --reset  --yx 0 1  --show  /data/workflows/poker_flats_test/run-mask.nc')


get_ipython().system('dvmdostem --help')


path_to_drainage_input='../data/input-catalog/caribou-poker/drainage.nc'


drainage = nc.Dataset(path_to_drainage_input)
print(drainage)


# poorly drained: 1, or well drained: 0
drainage['drainage_class'][:]


#force input data to site obs: --force-cmt {#}  black spruce = 1, deciduous = 3
    



#also force drainage (poorly drained: 1, or well drained: 0), 

